"""Master dataset builder — runs all recipes and writes per-source + merged JSONLs.

Pipeline per recipe:
    1. fetch documents via the chosen source module
    2. for each document, chunk and run 5 base generators:
         qa | quiz | study_notes | summary | agent_plan
    3. ALSO run the recipe's exam_styles generators
    4. write to fine_tuning/datasets/<recipe>_sft.jsonl
    5. final step: merge all into fine_tuning/datasets/master_sft.jsonl

Usage:
    # build everything in the catalog
    python3 fine_tuning/build_master_dataset.py

    # only certain recipes
    python3 fine_tuning/build_master_dataset.py --recipes mit_801_physics 3b1b_calculus

    # with a custom Ollama model
    python3 fine_tuning/build_master_dataset.py --model gemma3:latest

    # smaller / faster run for testing
    python3 fine_tuning/build_master_dataset.py --max-docs-per-recipe 1 --max-chunks 1
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.gemma_engine import GemmaConfig, generate_json
from core.cag_engine import generate_from_context, generate_quiz

from fine_tuning.dataset_recipes import RECIPES
from fine_tuning.sources import exam_styles


# ── Base generators (same shape as in build_walter_lewin_dataset.py) ────────

def _gen_qa(chunk: str, topic: str, cfg: GemmaConfig) -> dict | None:
    prompt = f"""Read this material and write ONE high-quality study question that
tests understanding (not trivia), then answer it grounded in the text.

Topic: {topic}

Source:
{chunk}

Output JSON: {{"question": "...", "answer": "..."}}"""
    r = generate_json(prompt, cfg)
    if not r or "question" not in r or "answer" not in r:
        return None
    return {"messages": [
        {"role": "user", "content": f"Use only the source below.\n\n{r['question']}\n\nSource:\n{chunk}"},
        {"role": "model", "content": r["answer"]},
    ]}


def _gen_quiz(chunk: str, topic: str, cfg: GemmaConfig) -> dict | None:
    quiz = generate_quiz(chunk, topic=topic, num_questions=3, difficulty="mixed", config=cfg)
    if not quiz or not quiz.get("questions"):
        return None
    return {"messages": [
        {"role": "user", "content": f"Generate a 3-question quiz from this source.\nTopic: {topic}\n\n{chunk}"},
        {"role": "model", "content": json.dumps(quiz, indent=2)},
    ]}


def _gen_notes(chunk: str, topic: str, cfg: GemmaConfig) -> dict | None:
    instr = ("Create rigorous study notes. Sections: ## Key Concepts, "
             "## Detailed Notes (bulleted, **bold** key terms), ## Worked Examples, "
             "## Review Questions.")
    notes = generate_from_context(
        chunk, instr,
        system_prompt="You are an expert educator creating university-level study materials.",
        config=cfg,
    )
    if not notes or len(notes) < 200:
        return None
    return {"messages": [
        {"role": "user", "content": f"Create study notes for this source.\nTopic: {topic}\n\n{chunk}"},
        {"role": "model", "content": notes},
    ]}


def _gen_summary(chunk: str, topic: str, cfg: GemmaConfig) -> dict | None:
    instr = "Write one-paragraph overview, then 5 key bullet points covering the main ideas."
    s = generate_from_context(chunk, instr, config=cfg)
    if not s or len(s) < 100:
        return None
    return {"messages": [
        {"role": "user", "content": f"Summarize this source concisely.\nTopic: {topic}\n\n{chunk}"},
        {"role": "model", "content": s},
    ]}


def _gen_agent_plan(topic: str, subject: str, cfg: GemmaConfig) -> dict | None:
    user_msg = f"""You are a study coach. Create a concise learning plan.

Goal: Master {topic} ({subject}) for a college-level exam
Topic: {topic}
User has no prior study history on '{topic}'.

Available actions: research, study_notes, key_concepts, summarize, quiz

Output valid JSON only:
{{
  "rationale": "1-2 sentences",
  "plan": [{{"action": "<action>", "goal": "<1-sentence goal>"}}]
}}

Rules: first step MUST be research, last step MUST be quiz, 3-5 steps total."""
    r = generate_json(user_msg, cfg)
    if not r or "plan" not in r:
        return None
    return {"messages": [
        {"role": "user", "content": user_msg},
        {"role": "model", "content": json.dumps(r, indent=2)},
    ]}


BASE_GENERATORS = [
    ("qa", _gen_qa),
    ("quiz", _gen_quiz),
    ("notes", _gen_notes),
    ("summary", _gen_summary),
]


# ── Chunker ─────────────────────────────────────────────────────────────────

def chunk_text(text: str, size: int = 6000, overlap: int = 400) -> list[str]:
    text = (text or "").strip()
    if len(text) <= size:
        return [text] if text else []
    out, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        out.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return out


# ── Per-recipe runner ───────────────────────────────────────────────────────

def run_recipe(recipe_id: str, recipe: dict, cfg: GemmaConfig,
               max_docs: int | None, max_chunks_override: int | None,
               output_dir: Path) -> Path:
    print(f"\n{'='*70}\n▶ RECIPE: {recipe_id}  (subject={recipe['subject']})\n{'='*70}")

    src_module_name = recipe["source_module"]
    src = importlib.import_module(f"fine_tuning.sources.{src_module_name}")
    docs = src.fetch(recipe["spec"])
    if not docs:
        print(f"  ✗ no documents fetched for {recipe_id}")
        return None

    if max_docs is not None:
        docs = docs[:max_docs]
    print(f"  ✓ {len(docs)} document(s) fetched")

    max_chunks = max_chunks_override if max_chunks_override is not None else recipe.get("max_chunks", 2)
    examples: list[dict] = []
    subject = recipe["subject"]
    exam_ids = recipe.get("exam_styles", [])

    for di, doc in enumerate(docs, 1):
        topic = doc["title"]
        print(f"\n  [{di}/{len(docs)}] {topic}")

        # 1 agent_plan per document (input doesn't depend on chunks)
        plan = _gen_agent_plan(topic, subject, cfg)
        if plan:
            examples.append(plan)
            print(f"    ✓ agent_plan")

        chunks = chunk_text(doc["text"])[:max_chunks]
        for ci, chunk in enumerate(chunks, 1):
            for kind, fn in BASE_GENERATORS:
                t0 = time.time()
                try:
                    ex = fn(chunk, topic, cfg)
                except Exception as exc:
                    print(f"    ✗ chunk {ci} {kind}: {exc}")
                    continue
                if ex:
                    examples.append(ex)
                    print(f"    ✓ chunk {ci} {kind} ({time.time()-t0:.0f}s)")

            # Exam-style generators (use first chunk only — exam q's don't need full doc)
            if ci == 1:
                for exam_id in exam_ids:
                    t0 = time.time()
                    try:
                        ex = exam_styles.make_exam_pair(chunk, topic, exam_id, cfg)
                    except Exception as exc:
                        print(f"    ✗ exam {exam_id}: {exc}")
                        continue
                    if ex:
                        examples.append(ex)
                        print(f"    ✓ exam_{exam_id} ({time.time()-t0:.0f}s)")

    out_path = output_dir / f"{recipe_id}_sft.jsonl"
    with open(out_path, "w") as f:
        for ex in examples:
            f.write(json.dumps(ex) + "\n")
    print(f"\n  ✓ wrote {len(examples)} examples to {out_path}")
    return out_path


# ── Master merge ────────────────────────────────────────────────────────────

def merge_jsonls(paths: list[Path], merged: Path) -> int:
    total = 0
    with open(merged, "w") as out:
        for p in paths:
            if not p or not p.exists():
                continue
            with open(p) as f:
                for line in f:
                    if line.strip():
                        out.write(line)
                        total += 1
    return total


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--recipes", nargs="*", help="Subset of recipe IDs to run")
    parser.add_argument("--max-docs-per-recipe", type=int, default=None,
                        help="Cap documents per recipe (useful for testing)")
    parser.add_argument("--max-chunks", type=int, default=None,
                        help="Override per-recipe chunk cap")
    parser.add_argument("--model", default="", help="Ollama model override")
    parser.add_argument("--output-dir", default="fine_tuning/datasets")
    args = parser.parse_args()

    cfg = GemmaConfig(temperature=0.4, max_tokens=2000)
    if args.model:
        cfg.model = args.model

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    recipe_ids = args.recipes or list(RECIPES.keys())
    print(f"Building {len(recipe_ids)} recipe(s): {recipe_ids}")

    written: list[Path] = []
    t0 = time.time()
    for rid in recipe_ids:
        if rid not in RECIPES:
            print(f"  ⚠ unknown recipe: {rid}")
            continue
        path = run_recipe(rid, RECIPES[rid], cfg,
                          args.max_docs_per_recipe, args.max_chunks, output_dir)
        if path:
            written.append(path)

    # Merge into master_sft.jsonl
    merged = output_dir / "master_sft.jsonl"
    total = merge_jsonls(written, merged)
    elapsed = time.time() - t0

    print(f"\n{'='*70}")
    print(f"DONE in {elapsed/60:.1f} min")
    print(f"Per-recipe files: {len(written)}")
    print(f"Master file: {merged} ({total} examples, {merged.stat().st_size/1024:.1f} KB)")
    print(f"\nNext: train on Kaggle T4 — see fine_tuning/RUNBOOK_TRAINING.md")


if __name__ == "__main__":
    main()
