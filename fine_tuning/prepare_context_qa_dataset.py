"""Prepare grounded context-followup QA data for open-source Gemma training.

This script creates chat-style JSONL examples aimed at improving:
- grounded answers from provided context
- follow-up question handling
- refusal when the answer is not in context

Run:
    pip install datasets
    python fine_tuning/prepare_context_qa_dataset.py
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT_DIR = Path(__file__).parent.parent
INPUT_DIR = ROOT_DIR / "assets" / "demo_inputs"
OUT_DIR = Path(__file__).parent / "datasets"
OUT_DIR.mkdir(exist_ok=True)


def build_examples() -> list[dict]:
    examples: list[dict] = []

    rag_context = (INPUT_DIR / "rag_vs_cag_study_packet.txt").read_text()
    audio_context = (INPUT_DIR / "audio_overview_transcript.txt").read_text()

    examples.append(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Use the provided context only. Explain the difference between RAG and CAG in education.\n\n"
                        f"Context:\n{rag_context}"
                    ),
                },
                {
                    "role": "model",
                    "content": (
                        "RAG answers questions by retrieving relevant external material at question time and grounding the response in those retrieved passages. "
                        "CAG instead loads the source material directly into the model context and generates from that full context without a separate retrieval step. "
                        "In education, RAG is stronger for grounded Q&A across multiple documents, while CAG is stronger for transforming a single known source into summaries, study guides, quizzes, and flashcards."
                    ),
                },
            ]
        }
    )

    examples.append(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Answer using only the context below.\n\n"
                        f"Context:\n{rag_context}"
                    ),
                },
                {
                    "role": "assistant",
                    "content": "RAG is stronger for grounded Q&A over many documents, while CAG is faster when the entire source already fits in context.",
                },
                {
                    "role": "user",
                    "content": "Follow up: why does session memory matter for learners?",
                },
                {
                    "role": "model",
                    "content": (
                        "Session memory matters because learners usually ask a sequence of follow-up questions rather than one isolated question. "
                        "The context says that preserving conversational context makes the system feel more helpful because it can carry forward earlier points while staying grounded in the source material."
                    ),
                },
            ]
        }
    )

    examples.append(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Use only this transcript. What is the difference between rereading and active recall?\n\n"
                        f"Transcript:\n{audio_context}"
                    ),
                },
                {
                    "role": "model",
                    "content": (
                        "Rereading mainly creates familiarity, which can feel like understanding even when the learner cannot recall the idea independently. "
                        "Active recall forces the learner to retrieve the information from memory through flashcards, summaries, explanations, or practice problems, which strengthens memory and exposes gaps more clearly."
                    ),
                },
            ]
        }
    )

    examples.append(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Answer only from the context. If the answer is missing, say so clearly.\n\n"
                        f"Context:\n{audio_context}"
                    ),
                },
                {
                    "role": "user",
                    "content": "What database engine does the podcast recommend for flashcards?",
                },
                {
                    "role": "model",
                    "content": "The transcript does not mention any database engine for flashcards.",
                },
            ]
        }
    )

    return examples


def main() -> None:
    examples = build_examples()
    out_path = OUT_DIR / "context_qa_train.jsonl"
    with out_path.open("w") as handle:
        for example in examples:
            handle.write(json.dumps(example, ensure_ascii=False) + "\n")
    print(f"Wrote {len(examples)} examples to {out_path}")


if __name__ == "__main__":
    main()
