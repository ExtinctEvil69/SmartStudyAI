"""Exam-style training pair generators.

These don't fetch content — they take a topic + transcript/notes from another
source and ask Gemma to generate problems in the EXACT format of major exams.

The point: Gemma learns the SIGNATURE FORMAT of each exam:
  - JEE Advanced: multi-step physics/math, MCQ + numerical, calc-heavy
  - GATE CS:      1-mark and 2-mark questions, formal definitions
  - SAT Math:     no calculus, problem-solving, 4 options
  - Putnam:       proof-style, A1/B1 numbering, very hard
  - IMO:          proof-style, geometry/algebra/number theory/combinatorics
  - USAMO:        Olympiad proofs, US-style
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.gemma_engine import GemmaConfig, generate_json

name = "exam_styles"


# ── Per-exam prompt templates ───────────────────────────────────────────────

EXAM_TEMPLATES = {
    "jee_advanced": {
        "subject_match": ["physics", "math", "chemistry"],
        "format": "JEE Advanced (Indian engineering entrance)",
        "instruction": """Create a JEE Advanced-style problem on this topic.

Format:
- ONE multi-part problem (parts a, b, c if applicable)
- Heavy use of calculus, vectors, and physical reasoning
- 4 MCQ options (multiple may be correct) OR a numerical answer
- Step-by-step solution showing every algebraic manipulation
- Difficulty: top 1% of high school students

Output JSON:
{
  "exam": "JEE Advanced",
  "topic": "<from input>",
  "problem": "<the problem statement, formal language>",
  "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
  "correct": ["A", "C"],
  "solution_steps": ["Step 1: ...", "Step 2: ...", ...],
  "final_answer": "...",
  "concepts_tested": ["..."]
}""",
    },

    "gate_cs": {
        "subject_match": ["computer science", "algorithms", "ml", "cs"],
        "format": "GATE Computer Science (Indian graduate aptitude)",
        "instruction": """Create a GATE CS-style question on this topic.

Format:
- Either a 1-mark conceptual question OR a 2-mark numerical/applied problem
- Formal definitions, precise wording
- 4 MCQ options OR numerical answer
- Concise solution (3-5 lines)

Output JSON:
{
  "exam": "GATE CS",
  "marks": 1 | 2,
  "topic": "<from input>",
  "problem": "<formal question>",
  "options": ["A) ...", "B) ...", "C) ...", "D) ..."] | null,
  "correct": "A" | "<numerical>",
  "solution": "<concise explanation>",
  "concepts_tested": ["..."]
}""",
    },

    "sat_math": {
        "subject_match": ["math", "algebra", "geometry"],
        "format": "SAT Math (US college admission)",
        "instruction": """Create an SAT Math-style problem on this topic.

Format:
- NO calculus (algebra, geometry, basic statistics, problem-solving only)
- 4 MCQ options OR student-produced response
- Realistic context (word problems welcome)
- Solution in 2-4 short steps

Output JSON:
{
  "exam": "SAT Math",
  "topic": "<from input>",
  "problem": "<the problem>",
  "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
  "correct": "B",
  "solution_steps": ["...", "..."],
  "concepts_tested": ["..."]
}""",
    },

    "putnam": {
        "subject_match": ["math", "calculus", "algebra", "analysis", "combinatorics"],
        "format": "Putnam Mathematical Competition (US undergraduate)",
        "instruction": """Create a Putnam-style problem on this topic.

Format:
- Numbered as A1-A6 (morning) or B1-B6 (afternoon), pick a difficulty
- Pure math, no calculator, proof-based
- Problem statement is short but the solution requires creativity
- Full proof with justification at every step

Output JSON:
{
  "exam": "Putnam",
  "problem_number": "A3",
  "topic": "<from input>",
  "problem": "<short formal statement>",
  "proof": "<rigorous solution / proof, 5-15 lines>",
  "key_insight": "<the trick that unlocks it>",
  "concepts_tested": ["..."]
}""",
    },

    "imo": {
        "subject_match": ["math", "geometry", "number theory", "combinatorics", "algebra"],
        "format": "International Mathematical Olympiad (high school)",
        "instruction": """Create an IMO-style problem on this topic.

Format:
- Single elegant problem statement
- Pure math, classified as: geometry / algebra / number theory / combinatorics
- Difficulty: high (top 6 students per country level)
- Full rigorous proof in formal mathematical language

Output JSON:
{
  "exam": "IMO",
  "category": "geometry" | "algebra" | "number_theory" | "combinatorics",
  "topic": "<from input>",
  "problem": "<elegant formal statement>",
  "proof": "<complete proof, formal, multi-paragraph>",
  "key_lemma": "<the auxiliary result needed>",
  "concepts_tested": ["..."]
}""",
    },

    "usamo": {
        "subject_match": ["math", "olympiad"],
        "format": "USAMO / USAJMO (US Olympiad)",
        "instruction": """Create a USAMO-style proof problem on this topic.

Format:
- Numbered Problem 1-6, indicate difficulty
- Proof-based, no MCQ
- US-style notation
- Complete rigorous solution

Output JSON:
{
  "exam": "USAMO",
  "problem_number": 3,
  "topic": "<from input>",
  "problem": "<formal statement>",
  "solution": "<complete proof>",
  "concepts_tested": ["..."]
}""",
    },
}


def make_exam_pair(transcript_chunk: str, topic: str, exam_id: str, cfg: GemmaConfig) -> dict | None:
    """Generate one exam-style training pair from source content + topic."""
    template = EXAM_TEMPLATES.get(exam_id)
    if not template:
        return None

    user_prompt = f"""Topic: {topic}
Source material excerpt (use as inspiration, do not copy):
{transcript_chunk[:2500]}

{template["instruction"]}"""

    # Exam outputs (especially Putnam/IMO proofs and JEE multi-step solutions)
    # routinely exceed 2K tokens — bump the budget locally without mutating cfg.
    big_cfg = GemmaConfig(
        model=cfg.model, temperature=cfg.temperature, max_tokens=4000,
        system_prompt=cfg.system_prompt,
    )

    result = generate_json(user_prompt, big_cfg)
    if not result or "problem" not in result:
        return None

    return {
        "messages": [
            {"role": "user", "content": f"Create a {template['format']}-style problem on the topic: {topic}"},
            {"role": "model", "content": json.dumps(result, indent=2)},
        ]
    }


def supported_exams_for_subject(subject: str) -> list[str]:
    """Pick the exam styles that fit a given subject."""
    s = subject.lower()
    return [
        eid for eid, tpl in EXAM_TEMPLATES.items()
        if any(m in s for m in tpl["subject_match"])
    ]
