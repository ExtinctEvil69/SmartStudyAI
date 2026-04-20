"""Stage 1: SFT + rsLoRA — Teach Gemma 4 E4B format and domain.

Run on Kaggle T4 GPU:
    pip install unsloth trl peft datasets
    python train_stage1_sft.py

After training: model outputs consistent structured JSON for quizzes,
flashcards, and study guides.
"""

from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig

# === Config ===
MODEL_NAME = "unsloth/gemma-4-E4B-it"
MAX_SEQ_LENGTH = 2048
LOAD_IN_4BIT = True
OUTPUT_DIR = "./stage1_sft"
DATASET_PATH = "fine_tuning/datasets/eduquiz_train.jsonl"
EVAL_PATH = "fine_tuning/datasets/eduquiz_eval.jsonl"

# === Load model ===
print("Loading Gemma 4 E4B...")
model, tokenizer = FastLanguageModel.from_pretrained(
    MODEL_NAME,
    max_seq_length=MAX_SEQ_LENGTH,
    load_in_4bit=LOAD_IN_4BIT,
    use_gradient_checkpointing="unsloth",
)

# === Attach rsLoRA adapters ===
# Key upgrades over standard LoRA:
# - rsLoRA: scales LR by 1/sqrt(r), stable at high ranks
# - r=32: richer adaptation for structured output tasks
# - All linear layers: not just attention
print("Attaching rsLoRA adapters (r=32, all linear layers)...")
model = FastLanguageModel.get_peft_model(
    model,
    r=32,
    lora_alpha=64,              # 2x rank sweet spot
    lora_dropout=0.05,
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    use_rslora=True,            # Rank-Stabilized LoRA
)

# === Load dataset ===
print(f"Loading dataset from {DATASET_PATH}...")
dataset = load_dataset("json", data_files={
    "train": DATASET_PATH,
    "eval": EVAL_PATH,
})

# === Format for chat template ===
def format_chat(example):
    """Format messages into Gemma chat template."""
    messages = example["messages"]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    return {"text": text}

train_dataset = dataset["train"].map(format_chat)
eval_dataset = dataset["eval"].map(format_chat)

# === Training ===
print("Starting Stage 1 SFT training...")
training_args = SFTConfig(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,      # Effective batch size = 8
    learning_rate=2e-4,
    num_train_epochs=3,
    warmup_ratio=0.1,
    lr_scheduler_type="cosine",
    bf16=True,
    max_seq_length=MAX_SEQ_LENGTH,
    logging_steps=25,
    eval_strategy="steps",
    eval_steps=100,
    save_strategy="steps",
    save_steps=200,
    save_total_limit=3,
    optim="adamw_8bit",
    weight_decay=0.01,
    dataset_text_field="text",
    report_to="none",
)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    tokenizer=tokenizer,
)

stats = trainer.train()
print(f"\nTraining complete!")
print(f"  Total steps: {stats.global_step}")
print(f"  Train loss: {stats.training_loss:.4f}")

# === Save ===
print(f"Saving model to {OUTPUT_DIR}/final...")
model.save_pretrained(f"{OUTPUT_DIR}/final")
tokenizer.save_pretrained(f"{OUTPUT_DIR}/final")
print("Stage 1 SFT complete! Proceed to Stage 2 (GRPO).")
