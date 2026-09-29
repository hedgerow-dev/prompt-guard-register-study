# When customer notices look like attacks

Data and code for a study of 12 open prompt-injection detectors on benign transactional email, synthetic benign email, and prompt-injection attacks from LLMail-Inject that triggered the target assistant's tool call.

- Paper: [`paper/main.tex`](paper/main.tex) (*When Customer Notices Look Like Attacks: Register Sensitivity and Threshold Transfer in Open Prompt-Injection Classifiers*)
- Blog post: *Your bank writes like an attacker* (Hedgerow Security Research)

## Main results

- `protectai/deberta-v3-base-prompt-injection-v2` flags 29 of 44 BIPIA transactional emails and 0 of 203 LLMail synthetic emails at 0.5.
- On 60 matched benign events it flags 52% of customer-notice phrasings and 2% of conversational phrasings (30 vs 0 discordant pairs).
- Against transactional mail it ranks tool-triggering attacks below benign messages (AUC 0.28).
- For 9 of 12 detectors, attacks separate less well from transactional than from synthetic benign mail; thresholds tuned on the synthetic set flag 80% to 98% of transactional mail for 6 of 12.
- Rewriting canonical imperative injections as polite requests lowers detector recall for 11 of 12 detectors on a 40-pair confirmation set frozen before scoring.

Every number is in [`results/tables.md`](results/tables.md) and [`results/summary.json`](results/summary.json).

## Layout

| path | what |
|---|---|
| `probes.py` | hand-written probe sets; SHA-256 in `probes.sha256`, recorded 2026-09-29 05:06 UTC before any scoring |
| `probes_replication.py` | 40 confirmation attack pairs, written after the first 20 were scored; SHA-256 in `probes_replication.sha256`, recorded 2026-09-29 07:12 UTC before they were scored |
| `fetch_data.py` | downloads BIPIA and LLMail-Inject files at pinned revisions and checks SHA-256 |
| `score.py` | scores every text with every detector, caches to `results/scores/` and `results/scores-replication/` |
| `analyze.py` | builds `results/tables.md` and `results/summary.json` from the cached scores |
| `trace.py` | word-deletion (`occlusion body|native`) and proxy training-corpus check (`association`) for protectai v2 |
| `figure.py` | Figure 1 (`paper/fig-thresholds.pdf`) |
| `results/manifest.json` | model revisions, label maps, dataset hashes, hardware, scoring settings, dated download counts |
| `results/requirements.lock` | full package versions of the environment that produced the results |

Per-item scores are keyed by item ID only; no dataset text is redistributed.

## Reproduce

Tested with Python 3.14. Needs, about 70 MB of data, and a Hugging Face login with Meta's Prompt Guard licence accepted (both Prompt Guard models are gated).

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python fetch_data.py
python analyze.py > results/tables.md          # tables from the committed scores, seconds
python score.py                                  # re-score everything, about 1.5 h on an Apple M5
python score.py replication
python trace.py association > results/association.md
python trace.py occlusion body > results/occlusion-body.md
python figure.py
```

Scoring ran in fp32 on Apple MPS with batches of 16. On 120 random items, batched GPU scores matched unbatched CPU scores to within 1e-5 with no verdict changes, so re-scoring on other hardware should reproduce the tables.

## Licence

Code, probes and results: MIT. BIPIA, LLMail-Inject and the proxy corpus are fetched from upstream under their own licences.
