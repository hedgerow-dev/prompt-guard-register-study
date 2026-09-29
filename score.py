"""Score every study text with every detector and cache the raw scores.

    python score.py                 # all models
    python score.py protectai-v2    # one model

Writes results/scores/<short>.json: {item_id: score}. The score is the
probability of the attack class (for Prompt Guard v1, 1 - P(BENIGN), which is
Meta's recommended score for untrusted third-party data). Inputs are truncated
to 512 tokens, as every one of these models does in deployment.

analyze.py turns the cached scores into tables. Scoring is slow; analysis is not.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

import probes

HERE = Path(__file__).resolve().parent
DATA = Path(os.environ.get("STUDY_DATA", HERE / "data"))  # filled by fetch_data.py
OUT = HERE / "results" / "scores"

# short name -> (hf id, how to read the attack probability)
MODELS = {
    "protectai-v2": ("protectai/deberta-v3-base-prompt-injection-v2", "label1"),
    "protectai-v1": ("protectai/deberta-v3-base-prompt-injection", "label1"),
    "deepset": ("deepset/deberta-v3-base-injection", "label1"),
    "prompt-guard-2": ("meta-llama/Llama-Prompt-Guard-2-86M", "label1"),
    "prompt-guard-1": ("meta-llama/Prompt-Guard-86M", "not_benign"),
    "testsavant-base-v0": ("testsavantai/prompt-injection-defender-base-v0", "label1"),
    "testsavant-base-v1": ("testsavantai/prompt-injection-defender-base-v1", "label1"),
    "testsavant-large-v0": ("testsavantai/prompt-injection-defender-large-v0", "label1"),
    "fmops-distilbert": ("fmops/distilbert-prompt-injection", "label1"),
    "devndeploy-bert": ("devndeploy/bert-prompt-injection-detector", "label1"),
    "proventra-mdeberta": ("proventra/mdeberta-v3-base-prompt-injection", "label1"),
    "tihilya-modernbert": ("tihilya/modernbert-base-prompt-injection-detection", "label1"),
}


def parse_bipia(record: str) -> str:
    """Body of a pipe-delimited BIPIA record, headers dropped."""
    body = []
    for seg in record.split("|"):
        m = re.match(r"\s*([A-Z_ ]{2,20})\s*:", seg)
        key = m.group(1).strip() if m else None
        if key == "CONTENT":
            body.append(seg.split(":", 1)[1])
        elif key not in ("SUBJECT", "EMAIL_FROM", "RECEIVED DATE", "FROM", "TO", "CC", "DATE"):
            body.append(seg)
    return "\n".join(body).strip()


def parse_llmail(record: str) -> str:
    m = re.match(r"^Subject of the email:\s*(.*?)\.?\s+Body:\s*(.*)$", record, re.S)
    return m.group(2).strip() if m else record.strip()


def study_items() -> dict[str, str]:
    """Every text the study scores, keyed by a stable id."""
    items: dict[str, str] = {}

    # BIPIA ships 50 email records; several are the same email asked about
    # twice. Score each distinct email once.
    seen = []
    for line in (DATA / "bipia" / "email_test.jsonl").read_text().splitlines():
        if line.strip():
            ctx = json.loads(line)["context"]
            if ctx not in seen:
                seen.append(ctx)
    for i, ctx in enumerate(seen):
        items[f"bipia/native/{i}"] = ctx
        items[f"bipia/body/{i}"] = parse_bipia(ctx)

    benign = json.loads((DATA / "llmail-inject" / "emails_for_fp_tests.json").read_text())
    for i, text in enumerate(benign):
        items[f"llmail/native/{i}"] = text
        items[f"llmail/body/{i}"] = parse_llmail(text)

    # Real attacks from phase 2 whose tool call actually fired in the
    # challenge: ground truth from the environment, not a judge's label.
    subs = json.loads((DATA / "llmail-inject" / "labelled_unique_submissions_phase2.json").read_text())
    fired = sorted(t for t, lab in subs.items() if lab["reason"] == "api_triggered")
    for i, text in enumerate(fired):
        items[f"attack/{i}"] = text

    for i, (_, notice, impersonal, chat) in enumerate(probes.REGISTER):
        items[f"register/notice/{i}"] = notice
        items[f"register/impersonal/{i}"] = impersonal
        items[f"register/chat/{i}"] = chat

    for kind, words in probes.SLOT_WORDS.items():
        for w in words:
            for f, frame in enumerate(probes.SLOT_FRAMES):
                items[f"slot/{kind}/{w}/{f}"] = frame.format(w)

    for i, (imperative, chatty) in enumerate(probes.ATTACKS):
        items[f"probe-attack/imperative/{i}"] = imperative
        items[f"probe-attack/chatty/{i}"] = chatty

    return items


def score_model(short: str, items: dict[str, str]) -> None:
    hf_id, mode = MODELS[short]
    tok = AutoTokenizer.from_pretrained(hf_id)
    model = AutoModelForSequenceClassification.from_pretrained(hf_id).eval()
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    try:
        model.to(device)
    except Exception:
        device = "cpu"
    benign_idx = next(i for i, lab in model.config.id2label.items() if lab.upper() == "BENIGN") \
        if mode == "not_benign" else None

    # Length-sorted batches keep padding, and so runtime, down.
    ids = sorted(items, key=lambda k: len(items[k]))
    lengths = {}
    scores = {}
    batch = 16
    for start in range(0, len(ids), batch):
        chunk = ids[start:start + batch]
        texts = [items[k] for k in chunk]
        enc = tok(texts, truncation=True, max_length=512, padding=True, return_tensors="pt")
        full = tok(texts, truncation=False)["input_ids"]
        with torch.no_grad():
            probs = torch.softmax(model(**enc.to(device)).logits.float(), dim=-1).cpu()
        for k, p, f in zip(chunk, probs, full):
            scores[k] = float(1 - p[benign_idx]) if benign_idx is not None else float(p[1])
            lengths[k] = len(f)
        print(f"\r{short}: {start + len(chunk)}/{len(ids)}", end="", file=sys.stderr)
    print(file=sys.stderr)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{short}.json").write_text(json.dumps({
        "model": hf_id,
        "device": device,
        "probes_sha256": hashlib.sha256((HERE / "probes.py").read_bytes()).hexdigest(),
        "replication_sha256": hashlib.sha256((HERE / "probes_replication.py").read_bytes()).hexdigest(),
        "scores": scores,
        "tokens": lengths,
    }, indent=0))


def replication_items() -> dict[str, str]:
    import probes_replication
    items = {}
    for i, (imperative, friendly) in enumerate(probes_replication.ATTACKS):
        items[f"rep-attack/imperative/{i}"] = imperative
        items[f"rep-attack/chatty/{i}"] = friendly
    return items


def main() -> None:
    args = sys.argv[1:]
    global OUT
    if args[:1] == ["replication"]:
        # python score.py replication [models...]: the frozen 40-pair replication set
        args = args[1:]
        items = replication_items()
        OUT = HERE / "results" / "scores-replication"
    else:
        items = study_items()
    print(f"{len(items)} texts", file=sys.stderr)
    for short in args or list(MODELS):
        score_model(short, items)


if __name__ == "__main__":
    main()
