"""Build merged training corpora for the SmartStudy AI fine-tuning pipeline.

This script merges the quiz-structure dataset with the grounded follow-up QA
dataset so Stage 1 can learn both structured educational outputs and stronger
context-following behavior.
"""

from __future__ import annotations

import json
import random
from pathlib import Path


DATA_DIR = Path(__file__).parent / "datasets"
EDUQUIZ_TRAIN = DATA_DIR / "eduquiz_train.jsonl"
EDUQUIZ_EVAL = DATA_DIR / "eduquiz_eval.jsonl"
CONTEXT_QA_TRAIN = DATA_DIR / "context_qa_train.jsonl"

MERGED_TRAIN = DATA_DIR / "smartstudy_train.jsonl"
MERGED_EVAL = DATA_DIR / "smartstudy_eval.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    random.seed(42)

    eduquiz_train = read_jsonl(EDUQUIZ_TRAIN)
    eduquiz_eval = read_jsonl(EDUQUIZ_EVAL)
    context_train = read_jsonl(CONTEXT_QA_TRAIN)

    if not eduquiz_train:
        raise FileNotFoundError(
            f"Missing {EDUQUIZ_TRAIN}. Run fine_tuning/prepare_dataset.py first."
        )

    context_eval = []
    context_train_split = context_train
    if len(context_train) >= 2:
        split_idx = max(1, int(len(context_train) * 0.75))
        context_train_split = context_train[:split_idx]
        context_eval = context_train[split_idx:]

    merged_train = eduquiz_train + context_train_split
    merged_eval = eduquiz_eval + context_eval
    random.shuffle(merged_train)
    random.shuffle(merged_eval)

    write_jsonl(MERGED_TRAIN, merged_train)
    write_jsonl(MERGED_EVAL, merged_eval)

    print(f"Wrote merged train set: {MERGED_TRAIN} ({len(merged_train)} rows)")
    print(f"Wrote merged eval set:  {MERGED_EVAL} ({len(merged_eval)} rows)")


if __name__ == "__main__":
    main()
