"""Download the three input files at pinned upstream revisions and check their SHA-256.

    python fetch_data.py   # writes data/bipia/ and data/llmail-inject/

The datasets are not redistributed here; see each upstream licence.
"""

import hashlib
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent

FILES = [
    ("bipia/email_test.jsonl",
     "https://raw.githubusercontent.com/microsoft/BIPIA/a004b69ec0dd446e0afd461d98cb5e96e120a5d0/benchmark/email/test.jsonl",
     "217b403faaa1d0cb12c24892bea39f4a0b9e2819919ac7e2b902006e28278cdb"),
    ("llmail-inject/emails_for_fp_tests.json",
     "https://huggingface.co/datasets/microsoft/llmail-inject-challenge/resolve/"
     "1063bdf01ec8762b812d5e06ee768a06faa5a6f7/data/emails_for_fp_tests.json",
     "4ddd950b5dbaa8548f5597c886d8e09a051ba07f80a9291fdcca9c2397d22abe"),
    ("llmail-inject/labelled_unique_submissions_phase2.json",
     "https://huggingface.co/datasets/microsoft/llmail-inject-challenge/resolve/"
     "1063bdf01ec8762b812d5e06ee768a06faa5a6f7/data/labelled_unique_submissions_phase2.json",
     "f89af984e345430c3b357903890e30867bf4676f4ef10c138cc7bad218e890b8"),
]


def main() -> int:
    ok = True
    for rel, url, sha in FILES:
        out = HERE / "data" / rel
        if not out.exists():
            out.parent.mkdir(parents=True, exist_ok=True)
            print(f"downloading {rel}", file=sys.stderr)
            with urllib.request.urlopen(url, timeout=120) as r:
                out.write_bytes(r.read())
        got = hashlib.sha256(out.read_bytes()).hexdigest()
        status = "ok" if got == sha else f"MISMATCH (got {got})"
        ok &= got == sha
        print(f"{rel}: {status}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
