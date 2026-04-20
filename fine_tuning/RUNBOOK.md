# Fine-Tuning Runbook

This is the shortest practical path from the current repo to a fine-tuned local model.

## Goal

Train the highest-value adapters first:

1. QuizVerse
2. Studio
3. NeuroRead / PaperAnalyzer follow-up QA behavior
4. DSA Sage

## Step 1: Prepare datasets locally

Run:

```bash
python fine_tuning/prepare_context_qa_dataset.py
python fine_tuning/prepare_dataset.py
python fine_tuning/build_training_corpus.py
```

If you only want to prepare what is already available locally:

```bash
python fine_tuning/prepare_all_datasets.py
```

## Step 2: Run Stage 1 on Kaggle / GPU

Run:

```bash
python fine_tuning/train_stage1_sft.py
```

This now defaults to the merged corpus:

- `fine_tuning/datasets/smartstudy_train.jsonl`
- `fine_tuning/datasets/smartstudy_eval.jsonl`

## Step 3: Run Stage 2 GRPO

```bash
python fine_tuning/train_stage2_grpo.py
```

## Step 4: Run Stage 3 SimPO

```bash
python fine_tuning/train_stage3_simpo.py
```

## Step 5: Evaluate

```bash
python fine_tuning/evaluate.py
```

## Step 6: Export to GGUF

```bash
python fine_tuning/export_gguf.py
```

## Step 7: Create a local Ollama model

Create a `Modelfile` like:

```text
FROM ./smartstudy-gemma4-edu-unsloth.Q4_K_M.gguf
PARAMETER temperature 0.3
```

Then run:

```bash
ollama create smartstudy-edu -f Modelfile
```

## Step 8: Point the app to the fine-tuned model

Add to `.env`:

```env
SMARTSTUDY_MODEL_QUIZVERSE=smartstudy-edu
SMARTSTUDY_MODEL_STUDIO=smartstudy-edu
SMARTSTUDY_MODEL_DSASAGE=smartstudy-edu
SMARTSTUDY_MODEL_PREPMASTER=smartstudy-edu
```

Then restart Streamlit.

## Optional Vision Adapter Path

After you prepare a multimodal dataset:

```bash
python fine_tuning/train_docread_vision.py
```

Use the resulting model for:

- NeuroRead
- PaperAnalyzer

## Practical Note

The repo is now wired so the app can keep working on base Gemma today and switch to your fine-tuned model later just by changing `.env` model names.
