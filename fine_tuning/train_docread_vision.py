"""DocRead vision adapter training scaffold for NeuroRead and PaperAnalyzer.

Run on Kaggle or another GPU machine after curating the multimodal dataset.
"""

from unsloth import FastVisionModel
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig


MODEL_NAME = "unsloth/gemma-3-4b-it"
OUTPUT_DIR = "./docread_vision"
DATASET_PATH = "fine_tuning/datasets/docread_vision.jsonl"


def format_example(example, tokenizer):
    messages = example["messages"]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    return {"text": text, "images": example.get("images", [])}


print("Loading multimodal base model...")
model, tokenizer = FastVisionModel.from_pretrained(
    MODEL_NAME,
    load_in_4bit=True,
)

print("Attaching multimodal LoRA adapters...")
model = FastVisionModel.get_peft_model(
    model,
    r=16,
    lora_alpha=32,
    finetune_vision_layers=True,
    finetune_language_layers=True,
    finetune_attention_modules=True,
    finetune_mlp_modules=True,
)

print(f"Loading dataset from {DATASET_PATH}...")
dataset = load_dataset("json", data_files={"train": DATASET_PATH})
train_dataset = dataset["train"].map(lambda ex: format_example(ex, tokenizer))

training_args = SFTConfig(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    learning_rate=1e-4,
    num_train_epochs=2,
    bf16=True,
    logging_steps=10,
    save_steps=100,
    save_total_limit=2,
    optim="adamw_8bit",
    dataset_text_field="text",
    report_to="none",
)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    tokenizer=tokenizer,
)

trainer.train()
model.save_pretrained(f"{OUTPUT_DIR}/final")
tokenizer.save_pretrained(f"{OUTPUT_DIR}/final")
print("DocRead vision adapter training complete.")
