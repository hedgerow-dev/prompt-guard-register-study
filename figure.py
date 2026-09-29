"""Score distributions for protectai v2 with both tuned cuts.

    python figure.py   # writes paper/fig-thresholds.pdf and paper/fig-thresholds.png

Scores are shown as log-odds, log(p / (1 - p)), because most of them sit
within 1e-4 of 0 or 1 and a linear axis hides that structure.
"""

import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
r = json.loads((HERE / "results" / "scores" / "protectai-v2.json").read_text())["scores"]
a = json.loads((HERE / "results" / "summary.json").read_text())["models"]["protectai-v2"]["attacks"]


def logit(p: float) -> float:
    p = min(max(p, 1e-7), 1 - 1e-7)
    return math.log(p / (1 - p))


groups = [
    ("Transactional benign (BIPIA, n=44)", "bipia/native/", "#c0392b"),
    ("Synthetic benign (LLMail, n=203)", "llmail/native/", "#2e86c1"),
    ("Tool-triggering attacks (n=3,165)", "attack/", "#555555"),
]
bins = [x / 2 for x in range(-34, 35)]
fig, ax = plt.subplots(figsize=(6.5, 3.2))
for label, prefix, colour in groups:
    xs = [logit(v) for k, v in r.items() if k.startswith(prefix)]
    ax.hist(xs, bins=bins, density=True, histtype="step", linewidth=1.6, color=colour, label=label)
for cut, name, style in ((a["cut_llmail"], "cut tuned on synthetic", "--"), (a["cut_bipia"], "cut tuned on transactional", ":")):
    ax.axvline(logit(cut), color="black", linestyle=style, linewidth=1, label=name)
ax.set_xlabel("attack score, log-odds (clipped at $\\pm$16)")
ax.set_ylabel("density")
ax.legend(fontsize=7, frameon=False, loc="upper center")
fig.tight_layout()
fig.savefig(HERE / "paper" / "fig-thresholds.pdf")
fig.savefig(HERE / "paper" / "fig-thresholds.png", dpi=200)
