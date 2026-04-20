"""Export fine-tuned model to GGUF for Ollama deployment.

Run after Stage 3 on Kaggle:
    python export_gguf.py

Then copy the GGUF file to your local machine and:
    ollama create smartstudy-edu -f Modelfile
"""

from unsloth import FastLanguageModel

# === Config ===
STAGE3_MODEL = "./stage3_simpo/final"
EXPORT_NAME = "smartstudy-gemma4-edu"
QUANT_METHOD = "q4_k_m"  # Best quality/size tradeoff for M3 Pro

# === Load final model ===
print(f"Loading final model from {STAGE3_MODEL}...")
model, tokenizer = FastLanguageModel.from_pretrained(
    STAGE3_MODEL,
    max_seq_length=2048,
    load_in_4bit=True,
)

# === Export to GGUF ===
print(f"Exporting to GGUF ({QUANT_METHOD})...")
model.save_pretrained_gguf(
    EXPORT_NAME,
    tokenizer,
    quantization_method=QUANT_METHOD,
)

print(f"\nGGUF export complete: {EXPORT_NAME}/")
print(f"\nTo deploy locally with Ollama:")
print(f"  1. Copy the GGUF file to your machine")
print(f"  2. Create a Modelfile:")
print(f"     FROM ./{EXPORT_NAME}-unsloth.{QUANT_METHOD.upper()}.gguf")
print(f"  3. Run: ollama create smartstudy-edu -f Modelfile")
print(f"  4. Test: ollama run smartstudy-edu 'Generate 3 MCQ questions about biology'")

# === Also push to HuggingFace Hub (for Unsloth $10K prize) ===
print("\nTo push to HuggingFace Hub:")
print("  model.push_to_hub_gguf('YOUR_USERNAME/smartstudy-gemma4-edu',")
print("                         tokenizer, quantization_method='q4_k_m',")
print("                         token='YOUR_HF_TOKEN')")
