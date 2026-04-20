# Fine-Tuning Notes

This directory contains the open-source training path for SmartStudy AI.

## Base Model

The training scripts are already configured around an open-source Gemma checkpoint:

- `unsloth/gemma-4-E4B-it`

That is the base model used in the Stage 1 SFT script.

## What Exists Already

- `prepare_dataset.py`
  builds quiz-oriented instruction data from public datasets
- `build_training_corpus.py`
  merges quiz data with grounded follow-up QA data for Stage 1
- `prepare_all_datasets.py`
  convenience runner for local dataset preparation
- `train_stage1_sft.py`
  supervised fine-tuning with rsLoRA
- `train_stage2_grpo.py`
  reward-based tuning for quiz quality
- `train_stage3_simpo.py`
  preference optimization stage
- `train_docread_vision.py`
  multimodal DocRead vision adapter training scaffold
- `evaluate.py`
  evaluation entrypoint
- `export_gguf.py`
  export path for local deployment
- `Modelfile.smartstudy-edu.template`
  Ollama template for the exported GGUF model
- `RUNBOOK.md`
  exact order of execution from datasets to local Ollama usage

## New Context QA Dataset

To improve context-following and follow-up question handling, this repo now also includes:

- `prepare_context_qa_dataset.py`

This generates training examples focused on:

- answering only from provided context
- handling follow-up questions with conversation history
- refusing to invent answers when the context does not contain them

Run it with:

```bash
python fine_tuning/prepare_context_qa_dataset.py
```

It writes:

- `fine_tuning/datasets/context_qa_train.jsonl`

## Important Constraint

The repository can prepare and run the open-source training pipeline, but it does not magically create or ship trained custom weights by itself.

To produce a stronger local model for your demo, you still need to:

1. generate the datasets
2. run the SFT / GRPO / SimPO stages on a GPU machine
3. export the final checkpoint for local use

## Recommended Demo Story

For the hackathon, the strongest honest story is:

- the product already runs on a local open-source Gemma setup
- the repo includes a real path to specialize that model further for education and grounded context-following
