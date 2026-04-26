"""Build SFT training data from Walter Lewin's MIT 8.01 physics lectures.

Pipeline (mirrors the BrahmaVidya StudyAgent pattern):
  for each lecture:
    1. fetch YouTube transcript
    2. chunk into 8K-char windows (Gemma can handle full lectures, but chunking
       gives more diverse training examples)
    3. for each chunk, generate 5 training pairs using local Gemma:
         - Q&A         (grounded answering)
         - quiz_json   (structured quiz output)
         - study_notes (structured notes)
         - summary     (compression)
         - agent_plan  (the agentic Plan-Mode output)
    4. write all examples to one consolidated JSONL in chat-message format

Output: fine_tuning/datasets/walter_lewin_sft.jsonl
        (compatible with fine_tuning/train_stage1_sft.py)

Usage:
    python3 fine_tuning/build_walter_lewin_dataset.py
    python3 fine_tuning/build_walter_lewin_dataset.py --videos id1 id2 id3
    python3 fine_tuning/build_walter_lewin_dataset.py --max-per-lecture 3
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.gemma_engine import GemmaConfig, generate, generate_json
from core.cag_engine import generate_from_context, generate_quiz
from core.youtube_engine import fetch_transcript


# ── MIT 8.01 Walter Lewin lecture catalog ───────────────────────────────────
# Title strings are used as `topic` metadata for the StudyAgent-style examples.
# Add or remove entries to control the dataset size.

LECTURES: list[tuple[str, str]] = [
    ("GtOGurrUPmQ", "Powers of Ten — Units, Dimensions, Measurements"),
    ("9JmQ8YNeoBs", "1D Kinematics — Speed, Velocity, Acceleration"),
    ("0BIFFCwgwxs", "Vectors — Dot Products and Cross Products"),
    ("dnRwoVsBV1k", "3D Kinematics — Free Falling Reference Frames"),
    ("g8KZRA2flyo", "Circular Motion — Centripetal Acceleration"),
    ("h7DBKHzJiOg", "Newton's Laws — Tension and Friction"),
    ("HPvrLOnaxfw", "Friction — Static vs Kinetic"),
    ("3Hr-58yLXh4", "Hooke's Law — Springs and Pendulums"),
    ("v_OTU8DfA1g", "Pulleys, Tension and Apparent Weight"),
    ("7yDk2j5fLNQ", "Work, Energy, Conservation"),
]


# ── Generators — each returns a (system, user, assistant) tuple ─────────────

def make_qa_example(transcript_chunk: str, topic: str, cfg: GemmaConfig) -> dict | None:
    """Generate a grounded Q&A pair from a transcript chunk."""
    user_prompt = f"""Read this lecture transcript and write ONE high-quality study question
that tests understanding (not trivia), then answer it grounded in the text.

Topic: {topic}

Transcript:
{transcript_chunk}

Output JSON:
{{
  "question": "<the question>",
  "answer": "<grounded answer, 2-4 sentences, cite specifics from the transcript>"
}}"""
    result = generate_json(user_prompt, cfg)
    if not result or "question" not in result or "answer" not in result:
        return None
    return {
        "messages": [
            {"role": "user", "content": f"Use only the transcript below.\n\n{result['question']}\n\nTranscript:\n{transcript_chunk}"},
            {"role": "model", "content": result["answer"]},
        ]
    }


def make_quiz_example(transcript_chunk: str, topic: str, cfg: GemmaConfig) -> dict | None:
    """Generate a quiz-output training pair (matches QuizForge format)."""
    quiz = generate_quiz(
        context=transcript_chunk,
        subject="Physics",
        topic=topic,
        num_questions=3,
        difficulty="mixed",
        config=cfg,
    )
    if not quiz or not quiz.get("questions"):
        return None
    user_msg = f"Generate a 3-question quiz from this physics lecture transcript.\n\nTopic: {topic}\n\nTranscript:\n{transcript_chunk}"
    return {
        "messages": [
            {"role": "user", "content": user_msg},
            {"role": "model", "content": json.dumps(quiz, indent=2)},
        ]
    }


def make_notes_example(transcript_chunk: str, topic: str, cfg: GemmaConfig) -> dict | None:
    """Generate a structured study-notes training pair."""
    instruction = (
        "Create rigorous study notes. Sections: ## Key Concepts, ## Detailed Notes "
        "(bulleted, **bold** key terms), ## Worked Examples, ## Review Questions."
    )
    notes = generate_from_context(
        transcript_chunk, instruction,
        system_prompt="You are an expert physics educator creating MIT-style study materials.",
        config=cfg,
    )
    if not notes or len(notes) < 200:
        return None
    user_msg = f"Create study notes for this physics lecture transcript.\n\nTopic: {topic}\n\nTranscript:\n{transcript_chunk}"
    return {
        "messages": [
            {"role": "user", "content": user_msg},
            {"role": "model", "content": notes},
        ]
    }


def make_summary_example(transcript_chunk: str, topic: str, cfg: GemmaConfig) -> dict | None:
    """Generate a one-paragraph summary + bullets."""
    instruction = "Write one-paragraph overview, then 5 key bullet points covering the main ideas."
    summary = generate_from_context(transcript_chunk, instruction, config=cfg)
    if not summary or len(summary) < 100:
        return None
    user_msg = f"Summarize this physics lecture transcript concisely.\n\nTopic: {topic}\n\nTranscript:\n{transcript_chunk}"
    return {
        "messages": [
            {"role": "user", "content": user_msg},
            {"role": "model", "content": summary},
        ]
    }


def make_agent_plan_example(topic: str, cfg: GemmaConfig) -> dict | None:
    """Generate an agentic Plan-Mode training pair (input: goal+topic, output: JSON plan).

    This is what teaches Gemma the StudyAgent format.
    """
    user_msg = f"""You are a study coach. Create a concise learning plan.

Goal: Master {topic} for an introductory physics exam
Topic: {topic}
User has no prior study history on '{topic}'.

Available actions: research, study_notes, key_concepts, summarize, quiz

Output valid JSON only:
{{
  "rationale": "1-2 sentences",
  "plan": [
    {{"action": "<action>", "goal": "<1-sentence goal>"}}
  ]
}}

Rules: first step MUST be research, last step MUST be quiz, 3-5 steps total."""
    result = generate_json(user_msg, cfg)
    if not result or "plan" not in result:
        return None
    return {
        "messages": [
            {"role": "user", "content": user_msg},
            {"role": "model", "content": json.dumps(result, indent=2)},
        ]
    }


# ── Chunker ─────────────────────────────────────────────────────────────────

def chunk_transcript(text: str, chunk_chars: int = 6000, overlap: int = 400) -> list[str]:
    """Split a long transcript into windows for diverse training examples."""
    text = text.strip()
    if len(text) <= chunk_chars:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_chars, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return chunks


# ── Main pipeline ───────────────────────────────────────────────────────────

GENERATORS = [
    ("qa", make_qa_example),
    ("quiz", make_quiz_example),
    ("notes", make_notes_example),
    ("summary", make_summary_example),
]


def process_lecture(video_id: str, topic: str, cfg: GemmaConfig, max_per_lecture: int) -> list[dict]:
    """Fetch one lecture, run all generators on its chunks, return training examples."""
    print(f"\n▶ {topic} ({video_id})")
    try:
        transcript = fetch_transcript(video_id)
    except Exception as exc:
        print(f"  ✗ transcript fetch failed: {exc}")
        return []
    print(f"  ✓ transcript: {len(transcript):,} chars")

    chunks = chunk_transcript(transcript)
    print(f"  ✓ chunked into {len(chunks)} window(s)")

    examples: list[dict] = []

    # 1 agentic-plan example per lecture (input doesn't depend on chunk)
    plan = make_agent_plan_example(topic, cfg)
    if plan:
        examples.append({"_kind": "agent_plan", **plan})
        print(f"    ✓ agent_plan")

    # Per-chunk examples — round-robin across generators, capped per lecture
    for i, chunk in enumerate(chunks[:max_per_lecture]):
        for kind, fn in GENERATORS:
            t0 = time.time()
            try:
                ex = fn(chunk, topic, cfg)
            except Exception as exc:
                print(f"    ✗ chunk {i+1} {kind}: {exc}")
                continue
            if ex:
                examples.append({"_kind": kind, **ex})
                print(f"    ✓ chunk {i+1} {kind} ({time.time()-t0:.0f}s)")
    return examples


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--videos", nargs="*", help="Override video ID list")
    parser.add_argument("--max-per-lecture", type=int, default=2,
                        help="Max chunks per lecture (each chunk → 4 examples)")
    parser.add_argument("--output", default="fine_tuning/datasets/walter_lewin_sft.jsonl")
    parser.add_argument("--model", default="", help="Ollama model override")
    args = parser.parse_args()

    cfg = GemmaConfig(temperature=0.4, max_tokens=2000)
    if args.model:
        cfg.model = args.model

    # Resolve lecture list
    if args.videos:
        lectures = [(v, f"Lecture {v}") for v in args.videos]
    else:
        lectures = LECTURES

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    all_examples: list[dict] = []
    for video_id, topic in lectures:
        examples = process_lecture(video_id, topic, cfg, args.max_per_lecture)
        all_examples.extend(examples)

    # Write JSONL — strip the _kind metadata field (training ignores it)
    with open(out_path, "w") as f:
        for ex in all_examples:
            ex.pop("_kind", None)
            f.write(json.dumps(ex) + "\n")

    # Stats
    print(f"\n{'='*60}")
    print(f"✓ Wrote {len(all_examples)} training examples to {out_path}")
    print(f"  File size: {out_path.stat().st_size / 1024:.1f} KB")
    if all_examples:
        kinds: dict[str, int] = {}
        for ex in all_examples:
            for k in ["qa", "quiz", "notes", "summary", "agent_plan"]:
                if k in str(ex):
                    pass
        # Re-count from raw written file
        print(f"  Lectures processed: {len(lectures)}")


if __name__ == "__main__":
    main()
