# SmartStudy AI — Advanced Fine-Tuning Strategy
## Beyond Ordinary LoRA: A 3-Stage Training Pipeline

---

## Why ordinary LoRA isn't enough

Standard LoRA + SFT teaches the model *what* to say by showing it examples. But it doesn't teach the model *how to think* — it can't develop strategies, self-correct, or learn from its own mistakes. This is why frontier models like Claude aren't just fine-tuned once — they go through multiple optimization stages, each targeting a different capability.

Your SmartStudy AI model needs to:
1. Generate structured educational content consistently (format compliance)
2. Reason about difficulty levels and adapt to students (judgment)
3. Prefer high-quality explanations over mediocre ones (taste)
4. Self-correct when it produces wrong quiz answers (reliability)

No single training method handles all four. Here's the pipeline that does.

---

## The 3-Stage Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  STAGE 1: SFT + LoRA                                       │
│  "Teach it the format and domain"                           │
│  Method: Supervised Fine-Tuning with Unsloth QLoRA          │
│  Data: 5,000 curated educational Q&A pairs                  │
│  Output: Model that reliably outputs structured JSON        │
│                                                             │
│  ──────────────────────── ▼ ────────────────────────        │
│                                                             │
│  STAGE 2: GRPO (Reinforcement Learning)                     │
│  "Teach it to reason and self-correct"                      │
│  Method: Group Relative Policy Optimization                 │
│  Data: 500-1000 prompts with reward functions               │
│  Output: Model that develops strategies for quiz quality    │
│                                                             │
│  ──────────────────────── ▼ ────────────────────────        │
│                                                             │
│  STAGE 3: SimPO (Preference Optimization)                   │
│  "Teach it taste — prefer excellent over merely correct"    │
│  Method: Simple Preference Optimization (reference-free)    │
│  Data: 2,000 preference pairs (good quiz vs bad quiz)       │
│  Output: Model that consistently generates high-quality     │
│          educational content with clear explanations         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## STAGE 1: SFT + QLoRA (Foundation)

### What it does
Teaches Gemma 4 E4B the format, domain vocabulary, and basic task structure. After this stage, the model reliably outputs structured JSON for quizzes, flashcards, and study guides.

### Why SFT first
SFT is the right choice when you need the model to learn counterintuitive, rule-based behaviors — like always outputting valid JSON with exactly 4 options per MCQ, including Bloom's taxonomy levels, and maintaining grade-appropriate language. Research shows SFT achieves 88% accuracy on rule-based tasks where GRPO alone plateaus at 43%.

### Training code
```python
from unsloth import FastLanguageModel
import torch
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig

# Load Gemma 4 E4B with 4-bit quantization
model, tokenizer = FastLanguageModel.from_pretrained(
    "unsloth/gemma-4-E4B-it",
    max_seq_length=2048,
    load_in_4bit=True,
    use_gradient_checkpointing="unsloth",
)

# Attach LoRA adapters
model = FastLanguageModel.get_peft_model(
    model,
    r=32,                    # Higher rank than standard (16) for richer adaptation
    lora_alpha=64,           # 2x rank is the sweet spot
    lora_dropout=0.05,
    target_modules=[         # Target ALL linear layers, not just attention
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    use_rslora=True,         # Rank-Stabilized LoRA — better than vanilla LoRA
                             # Scales adapter learning rate by 1/sqrt(r)
                             # Prevents training instability at higher ranks
)

# Load curated dataset
dataset = load_dataset("json", data_files="fine_tuning/datasets/eduquiz_train.jsonl")

# Training config — conservative to prevent catastrophic forgetting
training_args = SFTConfig(
    output_dir="./stage1_sft",
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,    # Effective batch size = 8
    learning_rate=2e-4,
    num_train_epochs=3,               # Stop at 3 — more degrades generalization
    warmup_ratio=0.1,                 # 10% warmup for stability
    lr_scheduler_type="cosine",       # Cosine decay > linear for fine-tuning
    bf16=True,
    max_seq_length=2048,
    logging_steps=25,
    eval_strategy="steps",
    eval_steps=100,
    save_strategy="steps",
    save_steps=200,
    optim="adamw_8bit",               # 8-bit Adam for memory efficiency
    weight_decay=0.01,
)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
    tokenizer=tokenizer,
)

trainer.train()
model.save_pretrained("./stage1_sft/final")
```

### Key upgrades over standard LoRA:
- **rsLoRA (Rank-Stabilized LoRA)**: Scales learning rate by 1/√r, preventing instability at higher ranks. This lets you use r=32 instead of r=16 for richer adaptation without training collapse.
- **r=32 instead of r=16**: More parameters trained = better domain adaptation for structured output tasks.
- **Cosine learning rate schedule**: Decays smoothly instead of linearly, better for fine-tuning.
- **All linear layers targeted**: Not just attention — gate, up, and down projections too.

---

## STAGE 2: GRPO (Reinforcement Learning)

### What it does
Teaches the model to *reason* about quiz quality. Instead of just mimicking training examples, GRPO lets the model develop its own strategies for generating good quizzes. It samples multiple outputs, scores them with reward functions, and learns to produce more of the high-scoring ones.

### Why GRPO instead of PPO
- GRPO eliminates the need for a separate value/critic model — saves 50% memory
- Works with as few as 100 training prompts (you don't need a massive dataset)
- Unsloth has native GRPO support for Gemma 4
- This is the same method DeepSeek-R1 used to develop reasoning capabilities

### Reward functions

This is where the magic happens. You design reward functions that score quiz quality on multiple dimensions:

```python
def quiz_reward_function(prompt, completion):
    """
    Multi-dimensional reward for educational quiz generation.
    Returns a score between 0 and 1.
    """
    reward = 0.0
    
    # --- Reward 1: Valid JSON structure (0.3 weight) ---
    try:
        parsed = json.loads(completion)
        reward += 0.15  # Valid JSON
        if "questions" in parsed and isinstance(parsed["questions"], list):
            reward += 0.15  # Correct schema
    except json.JSONDecodeError:
        return 0.0  # Invalid JSON = zero reward, hard penalty
    
    # --- Reward 2: Answer correctness (0.3 weight) ---
    # Use a verifier model or knowledge base to check answers
    questions = parsed.get("questions", [])
    correct_count = 0
    for q in questions:
        if verify_answer(q["question"], q["correct_answer"]):
            correct_count += 1
    if questions:
        reward += 0.3 * (correct_count / len(questions))
    
    # --- Reward 3: Explanation quality (0.2 weight) ---
    for q in questions:
        explanation = q.get("explanation", "")
        if len(explanation) > 50:  # Non-trivial explanation
            reward += 0.05
        if any(keyword in explanation.lower() for keyword in 
               ["because", "this is", "the reason", "for example"]):
            reward += 0.05  # Causal reasoning present
    reward = min(reward, 0.8)  # Cap explanation reward
    
    # --- Reward 4: Difficulty distribution (0.1 weight) ---
    difficulties = [q.get("difficulty", "") for q in questions]
    unique_diffs = set(difficulties)
    if len(unique_diffs) >= 2:  # Mix of difficulties
        reward += 0.05
    if len(unique_diffs) >= 3:  # All three levels present
        reward += 0.05
    
    # --- Reward 5: Bloom's taxonomy coverage (0.1 weight) ---
    blooms = [q.get("bloom_level", "") for q in questions]
    unique_blooms = set(blooms)
    if len(unique_blooms) >= 2:
        reward += 0.1
    
    # --- Penalty: Repetitive questions ---
    question_texts = [q["question"].lower() for q in questions]
    if len(question_texts) != len(set(question_texts)):
        reward -= 0.2  # Deduct for duplicate questions
    
    return max(0.0, min(1.0, reward))


def document_comprehension_reward(prompt, completion):
    """
    Reward function for document Q&A accuracy and citation quality.
    """
    reward = 0.0
    
    # Does the answer cite specific source locations?
    if re.search(r'\[Source \d+|page \d+|paragraph \d+', completion):
        reward += 0.3
    
    # Is the answer grounded (doesn't introduce external knowledge)?
    # Compare against source documents in prompt
    source_text = extract_source_from_prompt(prompt)
    answer_claims = extract_claims(completion)
    grounded_claims = sum(1 for c in answer_claims 
                         if is_grounded(c, source_text))
    if answer_claims:
        reward += 0.4 * (grounded_claims / len(answer_claims))
    
    # Is it concise but complete?
    word_count = len(completion.split())
    if 50 <= word_count <= 300:
        reward += 0.2  # Sweet spot
    elif word_count > 500:
        reward -= 0.1  # Too verbose
    
    # Does it directly answer the question?
    if not completion.startswith(("I don't", "I cannot", "Unfortunately")):
        reward += 0.1
    
    return max(0.0, min(1.0, reward))
```

### GRPO training code
```python
from unsloth import FastLanguageModel
from trl import GRPOConfig, GRPOTrainer

# Load Stage 1 SFT model (not base model!)
model, tokenizer = FastLanguageModel.from_pretrained(
    "./stage1_sft/final",
    max_seq_length=2048,
    load_in_4bit=True,
)

# GRPO config
grpo_config = GRPOConfig(
    output_dir="./stage2_grpo",
    learning_rate=5e-6,           # Much lower than SFT — careful updates
    num_train_epochs=1,           # Single epoch for RL
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    num_generations=8,            # Sample 8 responses per prompt
                                  # Research shows G=8 is optimal
    max_completion_length=1024,
    bf16=True,
    logging_steps=10,
    
    # KL penalty to prevent drift from SFT model
    kl_coef=0.05,                 # Start conservative
)

trainer = GRPOTrainer(
    model=model,
    args=grpo_config,
    train_dataset=grpo_prompts,   # 500-1000 prompts, no labels needed
    reward_funcs=[
        quiz_reward_function,       # For quiz generation prompts  
        document_comprehension_reward,  # For document Q&A prompts
    ],
    tokenizer=tokenizer,
)

trainer.train()
model.save_pretrained("./stage2_grpo/final")
```

### What makes this better than just SFT:
- The model learns to self-correct: if it generates invalid JSON, it gets zero reward and learns to avoid that
- It develops strategies for covering multiple Bloom's taxonomy levels
- It learns to balance difficulty distribution without being explicitly shown how
- It works with only 500-1000 prompts — no need for thousands of labeled examples
- The reward functions encode YOUR educational philosophy about what makes a good quiz

---

## STAGE 3: SimPO (Preference Optimization)

### What it does
Teaches the model *taste* — given two quiz outputs for the same prompt, which one is better? SimPO makes the model consistently prefer excellent educational content over merely correct content.

### Why SimPO instead of DPO
- **SimPO outperforms DPO by 6.4 points on AlpacaEval 2 and 7.5 points on Arena-Hard**
- **Reference-free**: No need to keep a copy of the reference model in memory — uses average log probability as the implicit reward instead
- **Length-normalized**: Doesn't bias toward longer responses (DPO does)
- **Simpler**: One model instead of two, less compute, less memory
- **AlphaPO (the latest variant) boosts SimPO by another 7-10%** — but SimPO is the practical choice for Kaggle GPU constraints

### Creating preference data
You need pairs: (preferred response, rejected response) for the same prompt.

**Method 1: Self-play generation**
```python
# Generate 5 responses per prompt from your Stage 2 model
# Score them with the same reward functions
# Best scoring = preferred, worst scoring = rejected

def create_preference_pairs(model, prompts, reward_fn, n_samples=5):
    pairs = []
    for prompt in prompts:
        responses = [model.generate(prompt) for _ in range(n_samples)]
        scores = [reward_fn(prompt, r) for r in responses]
        
        best_idx = scores.index(max(scores))
        worst_idx = scores.index(min(scores))
        
        if scores[best_idx] - scores[worst_idx] > 0.2:  # Meaningful gap
            pairs.append({
                "prompt": prompt,
                "chosen": responses[best_idx],
                "rejected": responses[worst_idx],
            })
    return pairs
```

**Method 2: LLM-as-Judge**
Use Claude API or Gemma 4 26B as a judge to evaluate pairs:
```python
judge_prompt = """
You are evaluating two educational quiz outputs. Score each on:
1. Accuracy of answers (0-10)
2. Quality of explanations (0-10)  
3. Appropriate difficulty for the target grade (0-10)
4. Diversity of question types (0-10)
5. Pedagogical value — does it actually help learning? (0-10)

Output JSON: {"response_a_score": X, "response_b_score": Y, "reasoning": "..."}
"""
```

### SimPO training code
```python
from trl import SimPOConfig, SimPOTrainer

# Load Stage 2 GRPO model
model, tokenizer = FastLanguageModel.from_pretrained(
    "./stage2_grpo/final",
    max_seq_length=2048,
    load_in_4bit=True,
)

simpo_config = SimPOConfig(
    output_dir="./stage3_simpo",
    learning_rate=5e-7,           # Very low — fine adjustments only
    num_train_epochs=1,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    beta=2.0,                     # SimPO-specific: controls preference strength
    gamma=1.0,                    # Target reward margin (0.5-1.5 optimal)
    bf16=True,
    max_length=2048,
    max_prompt_length=512,
    logging_steps=10,
)

trainer = SimPOTrainer(
    model=model,
    args=simpo_config,
    train_dataset=preference_dataset,  # 2,000 (chosen, rejected) pairs
    tokenizer=tokenizer,
)

trainer.train()

# Final export
model.save_pretrained("./stage3_simpo/final")

# Export to GGUF for Ollama
model.save_pretrained_gguf(
    "smartstudy-gemma4-edu",
    tokenizer,
    quantization_method="q4_k_m",  # Best quality/size tradeoff
)
```

---

## Vision Fine-Tuning (DocRead Adapter)

For the document comprehension LoRA, use Unsloth's vision fine-tuning:

```python
from unsloth import FastVisionModel

model, processor = FastVisionModel.from_pretrained(
    "unsloth/gemma-4-E4B-it",
    load_in_4bit=True,
    use_gradient_checkpointing="unsloth",
)

model = FastVisionModel.get_peft_model(
    model,
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    finetune_vision_layers=True,    # Fine-tune the ViT encoder
    finetune_language_layers=True,  # AND the language decoder
    finetune_attention_modules=True,
    finetune_mlp_modules=True,
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
)

# Vision dataset format:
# Each example has an image + question + answer
# Images: photographed textbook pages, handwritten notes, diagrams
# Questions: "What concepts are covered?", "Summarize the key points"
# Answers: Structured extracted content
```

This goes through the same 3-stage pipeline but with vision data mixed in.

---

## Evaluation Framework

### Before/after comparison metrics:

| Metric | What it measures | How to compute |
|--------|-----------------|----------------|
| JSON compliance rate | % of outputs that parse as valid JSON | `try: json.loads(output)` |
| Answer accuracy | % of quiz answers that are factually correct | Cross-reference with source material |
| Bloom's coverage | % of outputs spanning 2+ taxonomy levels | Check `bloom_level` field distribution |
| Difficulty distribution | Evenness of easy/medium/hard split | Chi-square test on difficulty counts |
| Explanation BLEU | Quality of explanations vs references | `sacrebleu` library |
| Citation groundedness | % of claims traceable to source documents | Manual annotation on 100 samples |
| Format consistency | Whether output matches schema every time | Schema validation |
| Preference win rate | How often fine-tuned beats base model | LLM-as-judge (Claude or GPT-4o) |

### Run evaluation:
```python
# Test on 200 held-out examples
# Compare: base Gemma 4 E4B vs Stage 1 vs Stage 2 vs Stage 3

results = {
    "base": evaluate(base_model, test_set),
    "stage1_sft": evaluate(sft_model, test_set),
    "stage2_grpo": evaluate(grpo_model, test_set),
    "stage3_simpo": evaluate(simpo_model, test_set),
}

# Expected improvement trajectory:
# Base:   ~40% JSON compliance, ~55% accuracy
# SFT:    ~92% JSON compliance, ~75% accuracy  
# GRPO:   ~95% JSON compliance, ~82% accuracy, better reasoning
# SimPO:  ~97% JSON compliance, ~85% accuracy, consistently excellent
```

---

## What makes this pipeline special for the hackathon

1. **No one else will do 3-stage training.** Most submissions will do basic SFT or zero-shot prompting. A multi-stage pipeline (SFT → GRPO → SimPO) shows deep technical understanding.

2. **Custom reward functions for education.** The reward functions encode Bloom's taxonomy, difficulty distribution, and explanation quality — concepts specific to educational AI. This shows the judges you understand both ML and education.

3. **Eligible for the $10K Unsloth prize.** Using Unsloth for all three stages, with rsLoRA, GRPO, and GGUF export, demonstrates advanced usage of their framework.

4. **Measurable improvement at each stage.** The evaluation framework shows clear gains from base → SFT → GRPO → SimPO, which makes for a compelling technical write-up.

5. **Inspired by frontier model training.** Claude, GPT-4, and Gemini all use multi-stage post-training (SFT → RL → preference optimization). You're applying the same methodology to an open model for education.

---

## Hardware Requirements

| Stage | GPU | VRAM | Time (5K examples) |
|-------|-----|------|---------------------|
| Stage 1: SFT | Kaggle T4 (free) | 15GB | ~2-3 hours |
| Stage 2: GRPO | Kaggle T4 (free) | 15GB | ~3-4 hours |
| Stage 3: SimPO | Kaggle T4 (free) | 12GB | ~1-2 hours |
| Vision fine-tuning | Kaggle T4 (free) | 15GB | ~2-3 hours |

**Total training time: ~10-12 hours on free Kaggle GPUs**
**Total cost: $0** (all on Kaggle free tier)

---

*This pipeline transforms a general-purpose Gemma 4 E4B into a specialized educational AI that doesn't just answer questions — it teaches.*
