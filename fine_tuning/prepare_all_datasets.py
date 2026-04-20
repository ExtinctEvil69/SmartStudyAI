"""Run all local dataset preparation steps for SmartStudy AI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parent


def run(script_name: str) -> None:
    script_path = ROOT / script_name
    subprocess.run([sys.executable, str(script_path)], check=True)


def main() -> None:
    run("prepare_context_qa_dataset.py")
    if (ROOT / "datasets" / "eduquiz_train.jsonl").exists() and (ROOT / "datasets" / "eduquiz_eval.jsonl").exists():
        run("build_training_corpus.py")
    else:
        print("Skipping merged corpus build: eduquiz_train.jsonl / eduquiz_eval.jsonl not present yet.")


if __name__ == "__main__":
    main()
