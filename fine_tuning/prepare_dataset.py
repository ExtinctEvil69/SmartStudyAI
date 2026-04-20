"""Dataset curation script for SmartStudy AI fine-tuning.

Pulls from SciQ, ARC, OpenBookQA, MMLU and formats into chat-style JSONL
for Gemma 4 E4B fine-tuning on Kaggle T4.

Run on Kaggle or locally:
    pip install datasets
    python prepare_dataset.py
"""

import json
import random
from pathlib import Path

from datasets import load_dataset

OUT_DIR = Path(__file__).parent / "datasets"
OUT_DIR.mkdir(exist_ok=True)

BLOOM_LEVELS = ["remember", "understand", "apply", "analyze", "evaluate", "create"]
DIFFICULTIES = ["easy", "medium", "hard"]


def format_mcq(question: str, options: list[str], correct: str, explanation: str,
               difficulty: str = "medium", bloom: str = "understand") -> dict:
    """Format a single MCQ into the target JSON schema."""
    return {
        "question": question,
        "type": "mcq",
        "options": options[:4],
        "correct_answer": correct,
        "explanation": explanation,
        "difficulty": difficulty,
        "bloom_level": bloom,
    }


def process_sciq(max_examples: int = 2000) -> list[dict]:
    """Process SciQ dataset (science exam questions)."""
    print("Loading SciQ...")
    ds = load_dataset("allenai/sciq", split="train")
    examples = []

    for row in ds:
        if len(examples) >= max_examples:
            break
        q = row["question"]
        correct = row["correct_answer"]
        distractors = [row["distractor1"], row["distractor2"], row["distractor3"]]
        options = [correct] + distractors
        random.shuffle(options)
        explanation = row.get("support", "") or f"The correct answer is {correct}."

        mcq = format_mcq(q, options, correct, explanation,
                         random.choice(DIFFICULTIES), random.choice(BLOOM_LEVELS[:3]))

        user_msg = f"Generate 1 MCQ question about science. Output valid JSON with the schema: {{\"questions\": [{{\"question\", \"type\", \"options\": [4], \"correct_answer\", \"explanation\", \"difficulty\", \"bloom_level\"}}]}}"
        model_msg = json.dumps({"questions": [mcq]}, ensure_ascii=False)

        examples.append({
            "messages": [
                {"role": "user", "content": user_msg},
                {"role": "model", "content": model_msg},
            ]
        })

    print(f"  SciQ: {len(examples)} examples")
    return examples


def process_arc(max_examples: int = 1500) -> list[dict]:
    """Process ARC dataset (grade-school science)."""
    print("Loading ARC...")
    examples = []

    for split_name in ["ARC-Easy", "ARC-Challenge"]:
        difficulty = "easy" if "Easy" in split_name else "hard"
        ds = load_dataset("allenai/ai2_arc", split_name, split="train")

        for row in ds:
            if len(examples) >= max_examples:
                break
            q = row["question"]
            choices = row["choices"]
            labels = choices["label"]
            texts = choices["text"]
            answer_key = row["answerKey"]

            options = texts[:4]
            try:
                correct_idx = labels.index(answer_key)
                correct = texts[correct_idx]
            except (ValueError, IndexError):
                continue

            explanation = f"The correct answer is '{correct}'. This is a grade-school science question."
            mcq = format_mcq(q, options, correct, explanation,
                             difficulty, random.choice(BLOOM_LEVELS[:4]))

            user_msg = f"Generate 1 {difficulty} science MCQ for grade school students. Output valid JSON."
            model_msg = json.dumps({"questions": [mcq]}, ensure_ascii=False)

            examples.append({
                "messages": [
                    {"role": "user", "content": user_msg},
                    {"role": "model", "content": model_msg},
                ]
            })

    print(f"  ARC: {len(examples)} examples")
    return examples


def process_openbookqa(max_examples: int = 800) -> list[dict]:
    """Process OpenBookQA dataset."""
    print("Loading OpenBookQA...")
    ds = load_dataset("allenai/openbookqa", "main", split="train")
    examples = []

    for row in ds:
        if len(examples) >= max_examples:
            break
        q = row["question_stem"]
        choices = row["choices"]
        labels = choices["label"]
        texts = choices["text"]
        answer_key = row["answerKey"]

        options = texts[:4]
        try:
            correct_idx = labels.index(answer_key)
            correct = texts[correct_idx]
        except (ValueError, IndexError):
            continue

        fact = row.get("fact1", "")
        explanation = f"The correct answer is '{correct}'." + (f" Key fact: {fact}" if fact else "")
        mcq = format_mcq(q, options, correct, explanation,
                         random.choice(DIFFICULTIES), random.choice(BLOOM_LEVELS))

        user_msg = "Generate 1 MCQ testing conceptual understanding. Output valid JSON."
        model_msg = json.dumps({"questions": [mcq]}, ensure_ascii=False)

        examples.append({
            "messages": [
                {"role": "user", "content": user_msg},
                {"role": "model", "content": model_msg},
            ]
        })

    print(f"  OpenBookQA: {len(examples)} examples")
    return examples


def process_mmlu(max_examples: int = 700, subjects: list[str] | None = None) -> list[dict]:
    """Process MMLU subset (humanities + social sciences)."""
    print("Loading MMLU...")
    target_subjects = subjects or [
        "high_school_biology", "high_school_chemistry", "high_school_physics",
        "high_school_world_history", "high_school_us_history",
        "high_school_geography", "high_school_psychology",
        "college_biology", "college_chemistry",
    ]

    examples = []
    ds = load_dataset("cais/mmlu", "all", split="test")

    for row in ds:
        if len(examples) >= max_examples:
            break
        if row.get("subject") not in target_subjects:
            continue

        q = row["question"]
        choices = row["choices"]
        answer_idx = row["answer"]

        if len(choices) < 4 or answer_idx >= len(choices):
            continue

        options = choices[:4]
        correct = choices[answer_idx]
        subject = row["subject"].replace("_", " ").title()
        explanation = f"The correct answer is '{correct}'. This is a {subject} question."

        mcq = format_mcq(q, options, correct, explanation,
                         "hard", random.choice(BLOOM_LEVELS[2:]))

        user_msg = f"Generate 1 advanced {subject} MCQ. Output valid JSON."
        model_msg = json.dumps({"questions": [mcq]}, ensure_ascii=False)

        examples.append({
            "messages": [
                {"role": "user", "content": user_msg},
                {"role": "model", "content": model_msg},
            ]
        })

    print(f"  MMLU: {len(examples)} examples")
    return examples


def main():
    random.seed(42)

    all_examples = []
    all_examples.extend(process_sciq(2000))
    all_examples.extend(process_arc(1500))
    all_examples.extend(process_openbookqa(800))
    all_examples.extend(process_mmlu(700))

    random.shuffle(all_examples)

    # Split: 90% train, 10% eval
    split_idx = int(len(all_examples) * 0.9)
    train = all_examples[:split_idx]
    eval_set = all_examples[split_idx:]

    # Write JSONL
    train_path = OUT_DIR / "eduquiz_train.jsonl"
    eval_path = OUT_DIR / "eduquiz_eval.jsonl"

    with open(train_path, "w") as f:
        for ex in train:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    with open(eval_path, "w") as f:
        for ex in eval_set:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"\nDataset ready:")
    print(f"  Train: {len(train)} examples -> {train_path}")
    print(f"  Eval:  {len(eval_set)} examples -> {eval_path}")
    print(f"  Total: {len(all_examples)} examples")


if __name__ == "__main__":
    main()
