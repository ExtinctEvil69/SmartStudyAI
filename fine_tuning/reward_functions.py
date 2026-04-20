"""Reward functions for GRPO Stage 2 training.

Multi-dimensional scoring for educational content quality:
- JSON structure validity
- Answer correctness
- Explanation quality
- Difficulty distribution
- Bloom's taxonomy coverage
"""

import json
import re


def quiz_reward_function(completions: list[str], prompts: list[str] | None = None, **kwargs) -> list[float]:
    """Score quiz generation outputs on multiple quality dimensions.

    Returns list of rewards between 0.0 and 1.0.

    Signature is compatible with both old TRL (prompts, completions)
    and new TRL (completions, prompts=None).
    """
    rewards = []
    for completion in completions:
        # Handle completions that may be dicts from the trainer
        text = completion if isinstance(completion, str) else str(completion)
        reward = _score_quiz(text)
        rewards.append(reward)
    return rewards


def _score_quiz(text: str) -> float:
    """Score a single quiz completion."""
    reward = 0.0

    # --- Reward 1: Valid JSON structure (0.3 weight) ---
    parsed = _try_parse_json(text)
    if parsed is None:
        return 0.0  # Hard penalty: invalid JSON = zero reward

    reward += 0.15  # Valid JSON
    questions = parsed.get("questions", [])
    if isinstance(questions, list) and len(questions) > 0:
        reward += 0.15  # Correct schema with questions array

    if not questions:
        return reward  # No questions to evaluate further

    # --- Reward 2: Schema completeness (0.15 weight) ---
    required_fields = {"question", "correct_answer", "options"}
    for q in questions:
        if isinstance(q, dict) and required_fields.issubset(q.keys()):
            reward += 0.15 / len(questions)

    # --- Reward 2b: Answer validity (0.05 weight) ---
    # correct_answer should appear in options
    for q in questions:
        if isinstance(q, dict):
            opts = q.get("options", [])
            correct = q.get("correct_answer", "")
            if isinstance(opts, list) and correct and correct in opts:
                reward += 0.05 / len(questions)

    # --- Reward 3: Explanation quality (0.2 weight) ---
    explanation_score = 0.0
    for q in questions:
        if not isinstance(q, dict):
            continue
        explanation = q.get("explanation", "")
        if len(explanation) > 50:
            explanation_score += 0.5
        if len(explanation) > 100:
            explanation_score += 0.25
        causal_words = ["because", "this is", "the reason", "for example", "since", "therefore", "due to"]
        if any(w in explanation.lower() for w in causal_words):
            explanation_score += 0.25
    if questions:
        reward += 0.2 * min(1.0, explanation_score / len(questions))

    # --- Reward 4: Difficulty distribution (0.1 weight) ---
    difficulties = [q.get("difficulty", "") for q in questions if isinstance(q, dict)]
    unique_diffs = set(d for d in difficulties if d in ("easy", "medium", "hard"))
    if len(unique_diffs) >= 2:
        reward += 0.05
    if len(unique_diffs) >= 3:
        reward += 0.05

    # --- Reward 5: Bloom's taxonomy coverage (0.1 weight) ---
    valid_blooms = {"remember", "understand", "apply", "analyze", "evaluate", "create"}
    blooms = [q.get("bloom_level", "") for q in questions if isinstance(q, dict)]
    unique_blooms = set(b for b in blooms if b in valid_blooms)
    if len(unique_blooms) >= 2:
        reward += 0.05
    if len(unique_blooms) >= 3:
        reward += 0.05

    # --- Reward 6: Option count correctness (0.1 weight) ---
    for q in questions:
        if isinstance(q, dict):
            opts = q.get("options", [])
            if isinstance(opts, list) and len(opts) == 4:
                reward += 0.1 / len(questions)

    # --- Penalty: Repetitive questions ---
    if questions:
        q_texts = [q.get("question", "").lower().strip() for q in questions if isinstance(q, dict)]
        if len(q_texts) != len(set(q_texts)):
            reward -= 0.2

    return max(0.0, min(1.0, reward))


def document_comprehension_reward(completions: list[str], prompts: list[str] | None = None, **kwargs) -> list[float]:
    """Score document Q&A outputs for accuracy and citation quality."""
    rewards = []
    for completion in completions:
        text = completion if isinstance(completion, str) else str(completion)
        reward = _score_doc_qa(text)
        rewards.append(reward)
    return rewards


def _score_doc_qa(text: str) -> float:
    """Score a single document Q&A completion."""
    reward = 0.0

    # Citation quality
    if re.search(r'\[Source \d+|page \d+|paragraph \d+|section|chapter', text, re.IGNORECASE):
        reward += 0.3

    # Conciseness (sweet spot: 50-300 words)
    word_count = len(text.split())
    if 50 <= word_count <= 300:
        reward += 0.2
    elif 30 <= word_count <= 500:
        reward += 0.1
    elif word_count > 500:
        reward -= 0.1

    # Doesn't start with refusal
    refusal_starts = ("i don't", "i cannot", "unfortunately", "i'm sorry", "as an ai")
    if not text.lower().strip().startswith(refusal_starts):
        reward += 0.15

    # Has structure (bullet points, bold, headers)
    if any(marker in text for marker in ["- ", "* ", "**", "##", "1."]):
        reward += 0.1

    # Reasonable length (not empty, not absurdly long)
    if 10 < word_count < 1000:
        reward += 0.15

    # Groundedness signal (quotes or specific references)
    if '"' in text or "'" in text or "according to" in text.lower():
        reward += 0.1

    return max(0.0, min(1.0, reward))


def _try_parse_json(text: str) -> dict | None:
    """Try to parse JSON from text, handling markdown code blocks."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try extracting from code blocks
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return None


if __name__ == "__main__":
    # Quick test
    good_quiz = json.dumps({
        "questions": [
            {
                "question": "What is photosynthesis?",
                "type": "mcq",
                "options": ["Light conversion", "Cell division", "DNA replication", "Protein synthesis"],
                "correct_answer": "Light conversion",
                "explanation": "Photosynthesis is the process by which plants convert light energy into chemical energy because they need glucose for growth.",
                "difficulty": "easy",
                "bloom_level": "remember",
            },
            {
                "question": "Which organelle performs photosynthesis?",
                "type": "mcq",
                "options": ["Chloroplast", "Mitochondria", "Nucleus", "Ribosome"],
                "correct_answer": "Chloroplast",
                "explanation": "Chloroplasts contain chlorophyll, the pigment that absorbs light. This is because the thylakoid membranes are where the light reactions occur.",
                "difficulty": "medium",
                "bloom_level": "understand",
            },
        ]
    })

    bad_quiz = "This is not JSON at all"
    mediocre_quiz = json.dumps({"questions": [{"question": "Q?", "correct_answer": "A"}]})

    print(f"Good quiz score:     {_score_quiz(good_quiz):.2f}")
    print(f"Bad quiz score:      {_score_quiz(bad_quiz):.2f}")
    print(f"Mediocre quiz score: {_score_quiz(mediocre_quiz):.2f}")
