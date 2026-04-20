"""Cache-Augmented Generation (CAG) engine.

For tools where speed matters and the full document is already in context:
QuizVerse, Studio, PrepMaster, DSA Sage.

No retrieval step — preloads full document text into Gemma 4's context window
and generates structured output directly.
"""

from core import gemma_engine
from core.gemma_engine import GemmaConfig


def generate_from_context(
    context: str,
    instruction: str,
    system_prompt: str = "",
    config: GemmaConfig | None = None,
    stream_callback=None,
) -> str:
    """Generate content with full document context preloaded (CAG pattern).

    Args:
        context: Full document text preloaded into context
        instruction: What to generate (e.g. "Create 5 quiz questions")
        system_prompt: Optional system-level instructions
        config: Gemma configuration overrides
    """
    cfg = config or GemmaConfig()
    cfg.system_prompt = system_prompt or cfg.system_prompt

    prompt = f"""<context>
{context}
</context>

<instruction>
{instruction}
</instruction>"""

    return gemma_engine.generate(prompt, cfg, stream_callback=stream_callback)


def generate_json_from_context(
    context: str,
    instruction: str,
    system_prompt: str = "",
    config: GemmaConfig | None = None,
) -> dict | None:
    """Generate structured JSON from full document context (CAG pattern)."""
    cfg = config or GemmaConfig()
    cfg.temperature = 0.3

    json_instruction = f"""{instruction}

Output ONLY valid JSON. No explanation, no markdown code blocks — just the raw JSON object."""

    full_system = (system_prompt + "\n" if system_prompt else "") + "You always respond with valid JSON only."
    cfg.system_prompt = full_system

    prompt = f"""<context>
{context}
</context>

<instruction>
{json_instruction}
</instruction>"""

    return gemma_engine.generate_json(prompt, cfg)


def generate_quiz(
    context: str,
    subject: str = "",
    topic: str = "",
    num_questions: int = 5,
    difficulty: str = "mixed",
    question_types: str = "mcq",
    grade_level: str = "",
    config: GemmaConfig | None = None,
) -> dict | None:
    """Generate a structured quiz from document context using CAG."""
    instruction = f"""Generate exactly {num_questions} quiz questions based on the provided context.

Subject: {subject or 'infer from context'}
Topic: {topic or 'infer from context'}
Difficulty: {difficulty}
Question types: {question_types}
{f'Grade level: {grade_level}' if grade_level else ''}

Output valid JSON with this exact schema:
{{
  "quiz_title": "string",
  "questions": [
    {{
      "question": "string",
      "type": "mcq" | "true_false" | "fill_blank",
      "options": ["A", "B", "C", "D"],
      "correct_answer": "string",
      "explanation": "string (2-3 sentences explaining why)",
      "difficulty": "easy" | "medium" | "hard",
      "bloom_level": "remember" | "understand" | "apply" | "analyze" | "evaluate" | "create"
    }}
  ]
}}"""

    system = "You are an expert educational quiz generator. Generate pedagogically sound questions that test genuine understanding, not just recall. Include clear explanations for each answer."

    return generate_json_from_context(context, instruction, system, config)


def generate_flashcards(
    context: str,
    num_cards: int = 10,
    config: GemmaConfig | None = None,
) -> dict | None:
    """Generate Obsidian-compatible flashcards from document context."""
    instruction = f"""Create {num_cards} flashcards from the provided context.

Output valid JSON:
{{
  "title": "string",
  "cards": [
    {{
      "front": "string (question or term)",
      "back": "string (answer or definition)",
      "tags": ["string"]
    }}
  ]
}}"""

    system = "You are an expert study materials creator. Make flashcards that promote active recall and spaced repetition."
    return generate_json_from_context(context, instruction, system, config)


def generate_study_guide(
    context: str,
    format: str = "markdown",
    config: GemmaConfig | None = None,
    stream_callback=None,
) -> str:
    """Generate a comprehensive study guide from document context."""
    instruction = """Create a detailed study guide from the provided context. Include:
1. Key Concepts (with definitions)
2. Important Relationships between concepts
3. Summary of main arguments/findings
4. Key terms glossary
5. Review questions

Format as clean Markdown with headers, bullet points, and bold key terms."""

    system = "You are an expert educator creating study materials. Be thorough but concise."
    return generate_from_context(context, instruction, system, config, stream_callback)


def generate_study_plan(
    context: str,
    goal: str = "",
    duration_weeks: int = 4,
    hours_per_week: int = 10,
    config: GemmaConfig | None = None,
    stream_callback=None,
) -> str:
    """Generate a personalized study plan from document context."""
    instruction = f"""Create a detailed week-by-week study plan.

Goal: {goal or 'Master the content in the provided context'}
Duration: {duration_weeks} weeks
Available study time: {hours_per_week} hours per week

For each week include:
- Focus topics
- Specific study activities with time allocations
- Practice exercises
- Self-assessment checkpoints
- Resources to review

Format as clean Markdown."""

    system = "You are an expert academic coach. Create realistic, actionable study plans that optimize learning through spaced repetition and active recall."
    return generate_from_context(context, instruction, system, config, stream_callback)
