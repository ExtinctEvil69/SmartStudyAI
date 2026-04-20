"""Stage 3: SimPO — Teach Gemma 4 taste (prefer excellent over merely correct).

Run on Kaggle T4 GPU after Stage 2:
    python train_stage3_simpo.py

SimPO advantages over DPO:
- Reference-free (no extra model in memory)
- Length-normalized (no bias toward verbose)
- +6.4 pts AlpacaEval 2, +7.5 pts Arena-Hard vs DPO
"""

import json
import random
from pathlib import Path

from unsloth import FastLanguageModel
from datasets import Dataset
from trl import SimPOConfig, SimPOTrainer

from reward_functions import quiz_reward_function, _score_quiz

# === Config ===
STAGE2_MODEL = "./stage2_grpo/final"
OUTPUT_DIR = "./stage3_simpo"
NUM_PREFERENCE_PAIRS = 2000


def generate_preference_pairs(model, tokenizer, num_pairs: int = 2000,
                               samples_per_prompt: int = 5) -> Dataset:
    """Generate preference pairs via self-play.

    For each prompt:
    1. Generate N responses from Stage 2 model
    2. Score each with reward functions
    3. Best = chosen, worst = rejected (keep only if gap > 0.2)
    """
    from reward_functions import _score_quiz

    subjects = ["Biology", "Chemistry", "Physics", "History", "Computer Science",
                "Mathematics", "Psychology", "Economics", "Literature"]
    difficulties = ["easy", "medium", "hard", "mixed"]
    grade_levels = ["Grade 8", "Grade 10", "Undergraduate"]

    FastLanguageModel.for_inference(model)

    pairs = []
    attempts = 0
    max_attempts = num_pairs * 3  # Allow some failures

    print(f"Generating {num_pairs} preference pairs via self-play...")

    while len(pairs) < num_pairs and attempts < max_attempts:
        attempts += 1
        subject = random.choice(subjects)
        difficulty = random.choice(difficulties)
        grade = random.choice(grade_levels)
        num_q = random.choice([3, 5])

        prompt = (
            f"Generate {num_q} {difficulty} MCQ questions about {subject} "
            f"for {grade} students. Output valid JSON."
        )

        # Generate N samples
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        responses = []
        scores = []

        for _ in range(samples_per_prompt):
            output = model.generate(
                **inputs,
                max_new_tokens=1024,
                temperature=0.8,
                top_p=0.9,
                do_sample=True,
            )
            response_text = tokenizer.decode(output[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
            score = _score_quiz(response_text)
            responses.append(response_text)
            scores.append(score)

        if not scores:
            continue

        best_idx = scores.index(max(scores))
        worst_idx = scores.index(min(scores))

        # Only keep if meaningful quality gap
        if scores[best_idx] - scores[worst_idx] > 0.2:
            pairs.append({
                "prompt": prompt,
                "chosen": responses[best_idx],
                "rejected": responses[worst_idx],
            })

        if len(pairs) % 50 == 0 and len(pairs) > 0:
            print(f"  Generated {len(pairs)}/{num_pairs} pairs ({attempts} attempts)")

    FastLanguageModel.for_training(model)
    print(f"Generated {len(pairs)} preference pairs from {attempts} attempts")
    return Dataset.from_list(pairs)


# === Load Stage 2 model ===
print(f"Loading Stage 2 GRPO model from {STAGE2_MODEL}...")
model, tokenizer = FastLanguageModel.from_pretrained(
    STAGE2_MODEL,
    max_seq_length=2048,
    load_in_4bit=True,
)

# === Generate preference data ===
preference_dataset = generate_preference_pairs(model, tokenizer, NUM_PREFERENCE_PAIRS)

# === SimPO Training ===
print("Starting Stage 3 SimPO training...")
simpo_config = SimPOConfig(
    output_dir=OUTPUT_DIR,
    learning_rate=5e-7,             # Very low — fine adjustments only
    num_train_epochs=1,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    beta=2.0,                       # Preference strength
    gamma=1.0,                      # Target reward margin (0.5-1.5 optimal)
    bf16=True,
    max_length=2048,
    max_prompt_length=512,
    logging_steps=10,
    save_steps=200,
    save_total_limit=2,
    report_to="none",
)

trainer = SimPOTrainer(
    model=model,
    args=simpo_config,
    train_dataset=preference_dataset,
    tokenizer=tokenizer,
)

stats = trainer.train()
print(f"\nSimPO Training complete!")
print(f"  Total steps: {stats.global_step}")

# === Save ===
print(f"Saving final model to {OUTPUT_DIR}/final...")
model.save_pretrained(f"{OUTPUT_DIR}/final")
tokenizer.save_pretrained(f"{OUTPUT_DIR}/final")
print("Stage 3 SimPO complete!")
