"""Two follow-ups on protectai-v2 only: which words carry the alarm, and where could it learn them.

    python trace.py occlusion native > results/occlusion-native.md
    python trace.py occlusion body   > results/occlusion-body.md
    python trace.py association  > results/association.md

occlusion    For each real BIPIA email the model flags, delete one word at a time
             and rescore. A word is load-bearing in an email if deleting it alone
             drops the score below 0.5.

association  In a public prompt-injection training corpus (xTRam1/safe-guard-
             prompt-injection, train+test), how often does each slot-test word
             appear in attack rows compared with the base rate? Then: does that
             lift predict how the model scores the word in the slot test?
             This is a proxy corpus. Protect AI has not published v2's training set.
"""

from __future__ import annotations

import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

import probes
from score import study_items

HERE = Path(__file__).resolve().parent
MODEL = "protectai/deberta-v3-base-prompt-injection-v2"
PROXY_REPO = "xTRam1/safe-guard-prompt-injection"
PROXY_REVISION = "a3a877d608f37b7d20d9945671902df895ecdb46"


def occlusion(view: str) -> None:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL).eval()

    def score(texts: list[str]) -> list[float]:
        out = []
        for i in range(0, len(texts), 16):
            enc = tok(texts[i:i + 16], truncation=True, max_length=512, padding=True, return_tensors="pt")
            with torch.no_grad():
                out += torch.softmax(model(**enc).logits, dim=-1)[:, 1].tolist()
        return out

    # Words are whitespace-split and rejoined with single spaces, and the base
    # score is taken on that rejoined text, so a deletion is the only change.
    emails = {k: " ".join(v.split()) for k, v in study_items().items()
              if k.startswith(f"bipia/{view}/")}
    base = dict(zip(emails, score(list(emails.values()))))
    flagged = [k for k in emails if base[k] >= 0.5]

    drops: dict[str, list[float]] = defaultdict(list)
    bearing: dict[str, set[str]] = defaultdict(set)
    for n, k in enumerate(flagged):
        words = emails[k].split(" ")  # already single-spaced
        variants = [" ".join(words[:i] + words[i + 1:]) for i in range(len(words))]
        new = score(variants)
        for w, s in zip(words, new):
            norm = re.sub(r"[^a-z0-9]", "", w.lower())
            if not norm:
                continue
            drops[norm].append(base[k] - s)
            if s < 0.5:
                bearing[norm].add(k)
        print(f"\r{n + 1}/{len(flagged)}", end="", file=sys.stderr)
    print(file=sys.stderr)

    print(f"# Occlusion, {MODEL}\n")
    print(f"View: {view}. {len(flagged)} of {len(emails)} distinct BIPIA emails flagged at 0.5.\n")
    print("## Words whose deletion alone clears an email\n")
    print("| word | emails it clears | mean score drop when deleted |")
    print("|---|---:|---:|")
    for w in sorted(bearing, key=lambda w: (-len(bearing[w]), w)):
        print(f"| `{w}` | {len(bearing[w])} | {sum(drops[w]) / len(drops[w]):.3f} |")
    cleared = set().union(*bearing.values()) if bearing else set()
    print(f"\n{len(cleared)} of {len(flagged)} flagged emails can be cleared by deleting one word. "
          f"The rest need more than one deletion.\n")
    print("## Largest mean drop (words deleted at least 3 times)\n")
    print("| word | times deleted | mean drop |")
    print("|---|---:|---:|")
    ranked = sorted((w for w in drops if len(drops[w]) >= 3), key=lambda w: -sum(drops[w]) / len(drops[w]))
    for w in ranked[:25]:
        print(f"| `{w}` | {len(drops[w])} | {sum(drops[w]) / len(drops[w]):.3f} |")


def spearman(x: list[float], y: list[float]) -> float:
    def ranks(v: list[float]) -> list[float]:
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(v):
            j = i
            while j < len(v) and v[order[j]] == v[order[i]]:
                j += 1
            for t in range(i, j):
                r[order[t]] = (i + j - 1) / 2
            i = j
        return r
    rx, ry = ranks(x), ranks(y)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    return cov / math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))


def association() -> None:
    import pyarrow.parquet as pq

    from huggingface_hub import hf_hub_download

    rows = []
    for f in ("train-00000-of-00001.parquet", "test-00000-of-00001.parquet"):
        path = hf_hub_download(PROXY_REPO, f"data/{f}", repo_type="dataset", revision=PROXY_REVISION)
        t = pq.read_table(path).to_pydict()
        rows += list(zip(t["text"], t["label"]))
    base = sum(lab for _, lab in rows) / len(rows)

    s = json.loads((HERE / "results" / "scores" / "protectai-v2.json").read_text())["scores"]
    nf = len(probes.SLOT_FRAMES)

    print(f"# Label association in xTRam1/safe-guard-prompt-injection\n")
    print(f"{len(rows)} rows, attack base rate {100 * base:.1f}%. Whole-word, case-insensitive.\n")
    print("| word | kind | rows containing it | share attack | lift | model median score in slot test |")
    print("|---|---|---:|---:|---:|---:|")
    xs, ys = [], []
    for kind, words in probes.SLOT_WORDS.items():
        for w in words:
            pat = re.compile(rf"\b{w}\b", re.I)
            hits = [lab for text, lab in rows if pat.search(text)]
            med = sorted(s[f"slot/{kind}/{w}/{f}"] for f in range(nf))[nf // 2]
            if hits:
                share = sum(hits) / len(hits)
                lift = share / base
                print(f"| `{w}` | {kind} | {len(hits)} | {100 * share:.0f}% | {lift:.2f}x | {med:.3f} |")
                if len(hits) >= 5:
                    xs.append(lift)
                    ys.append(med)
            else:
                print(f"| `{w}` | {kind} | 0 | - | - | {med:.3f} |")
    # Exact-enough p-value by permutation, interval by bootstrap over words.
    import random
    rng = random.Random(0)
    rho = spearman(xs, ys)
    perm = sum(abs(spearman(xs, rng.sample(ys, len(ys)))) >= abs(rho) for _ in range(10000))
    boots = []
    while len(boots) < 2000:
        idx = [rng.randrange(len(xs)) for _ in xs]
        bx, by = [xs[i] for i in idx], [ys[i] for i in idx]
        if len(set(bx)) > 1 and len(set(by)) > 1:
            boots.append(spearman(bx, by))
    boots.sort()
    print(f"\nSpearman correlation between lift and the model's MEDIAN score over the five frames, "
          f"words with at least 5 rows: rho = {rho:.2f} (n = {len(xs)} words), "
          f"permutation p = {(perm + 1) / 10001:.4f} (two-sided, 10,000 permutations), "
          f"bootstrap 95% interval [{boots[50]:.2f}, {boots[1949]:.2f}]")


if __name__ == "__main__":
    if sys.argv[1] == "occlusion":
        occlusion(sys.argv[2])
    else:
        association()
