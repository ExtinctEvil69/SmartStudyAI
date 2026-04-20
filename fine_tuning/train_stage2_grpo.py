"""Stage 2: GRPO — Teach Gemma 4 to reason about quiz quality.

Run on Kaggle T4 GPU after Stage 1:
    python train_stage2_grpo.py

Group Relative Policy Optimization:
- Samples 8 responses per prompt
- Scores with multi-dimensional reward functions
- Updates model to produce more high-scoring outputs
- Same method DeepSeek-R1 used for reasoning
"""

import json
from pathlib import Path

from unsloth import FastLanguageModel
from datasets import Dataset
from trl import GRPOConfig, GRPOTrainer

from reward_functions import quiz_reward_function

# === Config ===
STAGE1_MODEL = "./stage1_sft/final"
OUTPUT_DIR = "./stage2_grpo"
NUM_PROMPTS = 500  # GRPO works with few prompts + many generations


def create_grpo_prompts(num_prompts: int = 500) -> Dataset:
    """Create diverse quiz generation prompts for GRPO training."""
    subjects = [
        "Biology", "Chemistry", "Physics", "Mathematics", "History",
        "Geography", "Psychology", "Computer Science", "Literature",
        "Economics", "Environmental Science", "Sociology",
    ]
    difficulties = ["easy", "medium", "hard", "mixed"]
    grade_levels = ["Grade 8", "Grade 10", "Grade 12", "Undergraduate", "Graduate"]
    num_questions_options = [3, 5, 7, 10]
    topics_by_subject = {
        "Biology": ["Cell Division", "Genetics", "Evolution", "Ecology", "Human Anatomy"],
        "Chemistry": ["Atomic Structure", "Chemical Bonding", "Organic Chemistry", "Acids and Bases"],
        "Physics": ["Newton's Laws", "Thermodynamics", "Electromagnetism", "Optics", "Quantum Mechanics"],
        "Mathematics": ["Algebra", "Calculus", "Statistics", "Geometry", "Linear Algebra"],
        "History": ["World War II", "Industrial Revolution", "Renaissance", "Cold War"],
        "Computer Science": ["Data Structures", "Algorithms", "Databases", "Operating Systems"],
    }

    prompts = []
    import random
    random.seed(42)

    for i in range(num_prompts):
        subject = random.choice(subjects)
        difficulty = random.choice(difficulties)
        grade = random.choice(grade_levels)
        num_q = random.choice(num_questions_options)
        topics = topics_by_subject.get(subject, [subject])
        topic = random.choice(topics)

        prompt = (
            f"Generate {num_q} {difficulty} MCQ questions about {topic} ({subject}) "
            f"for {grade} students. Output valid JSON with the schema: "
            f'{{\"questions\": [{{\"question\", \"type\": \"mcq\", \"options\": [4], '
            f'\"correct_answer\", \"explanation\", \"difficulty\", \"bloom_level\"}}]}}'
        )
        prompts.append({"prompt": prompt})

    return Dataset.from_list(prompts)


# === Load Stage 1 model ===
print(f"Loading Stage 1 SFT model from {STAGE1_MODEL}...")
model, tokenizer = FastLanguageModel.from_pretrained(
    STAGE1_MODEL,
    max_seq_length=2048,
    load_in_4bit=True,
)

# === Create prompts ===
print(f"Creating {NUM_PROMPTS} GRPO prompts...")
train_dataset = create_grpo_prompts(NUM_PROMPTS)

# === GRPO Training ===
print("Starting Stage 2 GRPO training...")
grpo_config = GRPOConfig(
    output_dir=OUTPUT_DIR,
    learning_rate=5e-6,             # Much lower than SFT
    num_train_epochs=1,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    num_generations=8,              # Sample 8 responses per prompt (G=8 optimal)
    max_completion_length=1024,
    bf16=True,
    logging_steps=10,
    save_steps=100,
    save_total_limit=2,
    report_to="none",
    kl_coef=0.05,                   # Conservative KL penalty
)

trainer = GRPOTrainer(
    model=model,
    args=grpo_config,
    train_dataset=train_dataset,
    reward_funcs=[quiz_reward_function],
    tokenizer=tokenizer,
)

stats = trainer.train()
print(f"\nGRPO Training complete!")
print(f"  Total steps: {stats.global_step}")

# === Save ===
print(f"Saving model to {OUTPUT_DIR}/final...")
model.save_pretrained(f"{OUTPUT_DIR}/final")
tokenizer.save_pretrained(f"{OUTPUT_DIR}/final")
print("Stage 2 GRPO complete! Proceed to Stage 3 (SimPO).")
