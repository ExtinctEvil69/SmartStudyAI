"""Evaluation: compare Base vs Stage1 vs Stage2 vs Stage3.

Run on Kaggle after each stage to measure improvement.
Produces a results table for the hackathon writeup.
"""

import json
import time
from pathlib import Path

from unsloth import FastLanguageModel
from datasets import load_dataset

from reward_functions import _score_quiz, _try_parse_json

EVAL_DATASET = "fine_tuning/datasets/eduquiz_eval.jsonl"
NUM_EVAL = 200
MODELS = {
    "base": "unsloth/gemma-4-E4B-it",
    "stage1_sft": "./stage1_sft/final",
    "stage2_grpo": "./stage2_grpo/final",
    "stage3_simpo": "./stage3_simpo/final",
}


def evaluate_model(model_path: str, tokenizer_or_model=None, num_samples: int = 200) -> dict:
    """Evaluate a model on quiz generation quality."""
    print(f"\nEvaluating: {model_path}")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_path, max_seq_length=2048, load_in_4bit=True,
    )
    FastLanguageModel.for_inference(model)

    # Load eval prompts
    eval_data = load_dataset("json", data_files=EVAL_DATASET, split="train")
    eval_data = eval_data.select(range(min(num_samples, len(eval_data))))

    metrics = {
        "json_valid": 0,
        "schema_valid": 0,
        "has_explanation": 0,
        "has_bloom": 0,
        "has_difficulty": 0,
        "multi_difficulty": 0,
        "multi_bloom": 0,
        "avg_reward": 0.0,
        "total": 0,
    }

    for i, example in enumerate(eval_data):
        prompt = example["messages"][0]["content"]
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        output = model.generate(
            **inputs, max_new_tokens=1024, temperature=0.3, do_sample=True,
        )
        response = tokenizer.decode(output[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

        metrics["total"] += 1

        # JSON validity
        parsed = _try_parse_json(response)
        if parsed is not None:
            metrics["json_valid"] += 1

            questions = parsed.get("questions", [])
            if isinstance(questions, list) and len(questions) > 0:
                metrics["schema_valid"] += 1

                # Check fields
                for q in questions:
                    if q.get("explanation") and len(q["explanation"]) > 20:
                        metrics["has_explanation"] += 1
                        break
                for q in questions:
                    if q.get("bloom_level"):
                        metrics["has_bloom"] += 1
                        break
                for q in questions:
                    if q.get("difficulty"):
                        metrics["has_difficulty"] += 1
                        break

                diffs = set(q.get("difficulty", "") for q in questions)
                if len(diffs - {""}) >= 2:
                    metrics["multi_difficulty"] += 1

                blooms = set(q.get("bloom_level", "") for q in questions)
                if len(blooms - {""}) >= 2:
                    metrics["multi_bloom"] += 1

        # Reward score
        metrics["avg_reward"] += _score_quiz(response)

        if (i + 1) % 50 == 0:
            print(f"  Evaluated {i+1}/{num_samples}")

    total = metrics["total"]
    if total > 0:
        metrics["avg_reward"] /= total

    results = {
        "model": model_path,
        "json_compliance": f"{metrics['json_valid']/total*100:.1f}%",
        "schema_compliance": f"{metrics['schema_valid']/total*100:.1f}%",
        "has_explanations": f"{metrics['has_explanation']/total*100:.1f}%",
        "bloom_coverage": f"{metrics['has_bloom']/total*100:.1f}%",
        "difficulty_tags": f"{metrics['has_difficulty']/total*100:.1f}%",
        "multi_difficulty": f"{metrics['multi_difficulty']/total*100:.1f}%",
        "multi_bloom": f"{metrics['multi_bloom']/total*100:.1f}%",
        "avg_reward_score": f"{metrics['avg_reward']:.3f}",
        "samples": total,
    }

    print(f"  Results: {json.dumps(results, indent=2)}")
    return results


def main():
    all_results = []

    for name, path in MODELS.items():
        if not Path(path).exists() and not path.startswith("unsloth/"):
            print(f"Skipping {name}: {path} not found")
            continue
        try:
            results = evaluate_model(path, num_samples=NUM_EVAL)
            results["stage"] = name
            all_results.append(results)
        except Exception as e:
            print(f"Error evaluating {name}: {e}")

    # Print comparison table
    print("\n" + "=" * 80)
    print("EVALUATION RESULTS — SmartStudy AI Fine-Tuning Pipeline")
    print("=" * 80)
    header = f"{'Stage':<15} {'JSON%':<10} {'Schema%':<10} {'Explain%':<10} {'Bloom%':<10} {'Reward':<10}"
    print(header)
    print("-" * 65)
    for r in all_results:
        row = f"{r['stage']:<15} {r['json_compliance']:<10} {r['schema_compliance']:<10} {r['has_explanations']:<10} {r['bloom_coverage']:<10} {r['avg_reward_score']:<10}"
        print(row)

    # Save results
    out_path = Path("fine_tuning/eval_results.json")
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
