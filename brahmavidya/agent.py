"""StudyAgent — Claude Code-style agent loop for learning tasks.

Pattern: Explore → Plan → Execute → Verify → Record
- Explore: query Vidya Smriti for prior mastery + context
- Plan:    Gemma produces a multi-step study plan (user approves)
- Execute: dispatch each step to a BrahmaVidya tool
- Verify:  quiz generation scores understanding
- Record:  log events + update mastery in Vidya Smriti

Each step is a (action, tool, args) tuple. Observations accumulate into
session.artifacts, which later steps can read. This mirrors the
H_{t+1} = H_t ∪ {action_t, observation_t} formulation from the report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.gemma_engine import GemmaConfig, generate, generate_json
from core.cag_engine import generate_from_context, generate_quiz
from core.web_research import search_web, build_research_context
from brahmavidya.memory import (
    get_mastery,
    log_event,
    update_mastery,
    register_content,
)


# ── Tool registry — available actions the planner can schedule ──────────────

TOOL_CATALOG = {
    "research":     "Search the web and synthesize sources into a factual brief.",
    "study_notes":  "Produce detailed study notes from prior research artifacts.",
    "key_concepts": "Extract concepts with definitions and relationships.",
    "summarize":    "One-paragraph summary plus 5 key bullet points.",
    "quiz":         "Generate a 5-question mixed-difficulty quiz for verification.",
}


# ── Data classes ────────────────────────────────────────────────────────────

@dataclass
class AgentStep:
    action: str               # one of TOOL_CATALOG keys
    goal: str                 # 1-sentence description of what the step accomplishes
    args: dict = field(default_factory=dict)
    result: str = ""          # short text observation (preview)
    status: str = "pending"   # pending | running | done | failed

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "goal": self.goal,
            "args": self.args,
            "result": self.result,
            "status": self.status,
        }


@dataclass
class AgentSession:
    goal: str
    topic: str
    plan: list[AgentStep] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)
    rationale: str = ""
    final_summary: str = ""
    mastery_before: float = 0.0
    mastery_after: float = 0.0

    def to_dict(self) -> dict:
        return {
            "goal": self.goal,
            "topic": self.topic,
            "plan": [s.to_dict() for s in self.plan],
            "artifacts": {k: (v if isinstance(v, (str, dict, list)) else str(v)) for k, v in self.artifacts.items()},
            "rationale": self.rationale,
            "final_summary": self.final_summary,
            "mastery_before": self.mastery_before,
            "mastery_after": self.mastery_after,
        }


# ── Phase 1 + 2: Explore + Plan ─────────────────────────────────────────────

def plan_session(goal: str, topic: str) -> AgentSession:
    """Build a plan without executing. Returns the session with plan populated."""
    prior = get_mastery(topic)
    prior_line = (
        f"User's current mastery on '{topic}': {prior.get('score', 0):.0f}% "
        f"over {prior.get('attempts', 0)} prior attempts."
        if isinstance(prior, dict) and prior
        else f"User has no prior study history on '{topic}'."
    )

    prompt = f"""You are a study coach. Create a concise learning plan.

Goal: {goal}
Topic: {topic}
{prior_line}

Available actions (use action names exactly): {", ".join(TOOL_CATALOG.keys())}

Output valid JSON only with this shape:
{{
  "rationale": "1-2 sentences on why this plan fits the goal",
  "plan": [
    {{"action": "research",     "goal": "what this step accomplishes"}},
    {{"action": "study_notes",  "goal": "..."}},
    {{"action": "key_concepts", "goal": "..."}},
    {{"action": "quiz",         "goal": "..."}}
  ]
}}

Hard rules:
- FIRST step MUST be "research" (gathers the source material).
- LAST step MUST be "quiz" (verification).
- 3-5 steps total.
- Each action must be from the available list."""

    cfg = GemmaConfig(temperature=0.5)
    result = generate_json(prompt, cfg) or {}

    raw_plan = result.get("plan", [])
    rationale = result.get("rationale", "")

    session = AgentSession(goal=goal, topic=topic, rationale=rationale)
    if isinstance(prior, dict) and prior:
        session.mastery_before = float(prior.get("score", 0))

    # Sanitize + enforce invariants
    plan_steps: list[AgentStep] = []
    for p in raw_plan:
        action = str(p.get("action", "")).strip().lower()
        if action in TOOL_CATALOG:
            plan_steps.append(AgentStep(action=action, goal=p.get("goal", ""), args=p.get("args", {})))

    if not plan_steps or plan_steps[0].action != "research":
        plan_steps.insert(0, AgentStep(action="research", goal=f"Gather source material on {topic}"))
    if plan_steps[-1].action != "quiz":
        plan_steps.append(AgentStep(action="quiz", goal="Verify understanding with a short quiz"))

    session.plan = plan_steps
    log_event("StudyAgent", "plan_created", topic, goal=goal, num_steps=len(plan_steps))
    return session


# ── Phase 3: Execute ────────────────────────────────────────────────────────

def _execute_step(step: AgentStep, session: AgentSession) -> None:
    """Dispatch one step. Updates step.result + step.status in place."""
    step.status = "running"
    cfg = GemmaConfig(temperature=0.4)
    topic = session.topic

    try:
        if step.action == "research":
            raw = search_web(topic, max_results=4)
            if not raw:
                step.result = "No web results found."
                step.status = "failed"
                return
            ctx, sources = build_research_context(raw)
            prompt = (
                f"Summarize the key findings on '{topic}' using only the sources below.\n"
                f"Cite claims inline as [Source X]. Be factual.\n\nSources:\n{ctx}"
            )
            research = generate(prompt, cfg)
            session.artifacts["research"] = research
            session.artifacts["sources"] = [
                {"title": s["title"], "url": s["url"], "source_id": s["source_id"]}
                for s in sources
            ]
            register_content("research_brief", topic, "StudyAgent", num_sources=len(sources))
            step.result = _preview(research)

        elif step.action == "study_notes":
            context = session.artifacts.get("research") or session.goal
            instruction = (
                "Create detailed study notes. Sections: Key Topics, Detailed Notes "
                "(bulleted, bold key terms), Key Takeaways, Review Questions."
            )
            notes = generate_from_context(
                context, instruction,
                system_prompt="You are an expert educator creating rigorous study materials.",
                config=cfg,
            )
            session.artifacts["notes"] = notes
            step.result = _preview(notes)

        elif step.action == "key_concepts":
            context = session.artifacts.get("notes") or session.artifacts.get("research") or session.goal
            instruction = (
                "Extract all key concepts. For each: **Name**, 1-2 sentence definition, "
                "how it relates to other concepts. Order foundational → advanced."
            )
            concepts = generate_from_context(context, instruction, config=cfg)
            session.artifacts["concepts"] = concepts
            step.result = _preview(concepts)

        elif step.action == "summarize":
            context = (
                session.artifacts.get("notes")
                or session.artifacts.get("research")
                or session.goal
            )
            instruction = "Write one-paragraph overview, then 5 key bullet points, then 'Who this helps'."
            summary = generate_from_context(context, instruction, config=cfg)
            session.artifacts["summary"] = summary
            step.result = _preview(summary)

        elif step.action == "quiz":
            context = (
                session.artifacts.get("notes")
                or session.artifacts.get("research")
                or session.goal
            )
            quiz = generate_quiz(
                context,
                topic=topic,
                num_questions=5,
                difficulty="mixed",
                config=cfg,
            )
            session.artifacts["quiz"] = quiz or {"questions": []}
            n = len(quiz.get("questions", [])) if quiz else 0
            step.result = f"Generated {n} quiz questions — take the quiz to verify understanding."

        else:
            step.result = f"Unknown action: {step.action}"
            step.status = "failed"
            return

        step.status = "done"
        log_event("StudyAgent", f"step_{step.action}", topic, step_goal=step.goal)

    except Exception as exc:
        step.result = f"Error: {exc}"
        step.status = "failed"
        log_event("StudyAgent", "step_failed", topic, action=step.action, error=str(exc))


def execute_session(session: AgentSession) -> AgentSession:
    """Run every step in the plan and produce the final summary."""
    for step in session.plan:
        _execute_step(step, session)

    # Phase 5: Record — stateful final report (Claude Code pattern)
    artifact_names = [k for k in session.artifacts.keys() if k != "sources"]
    summary_prompt = f"""Write a concise stateful session report in this exact format:

Changed:
- (list artifacts produced and what each contributes)

Verified:
- (list verification signals e.g. quiz generated with N questions)

Remaining risk:
- (what the learner should still practice)

Next step:
- (single concrete next action for the learner)

Session data:
Topic: {session.topic}
Goal: {session.goal}
Rationale: {session.rationale}
Artifacts: {artifact_names}
Quiz questions generated: {len(session.artifacts.get('quiz', {}).get('questions', []))}
Mastery before: {session.mastery_before:.0f}%"""

    cfg = GemmaConfig(temperature=0.3)
    session.final_summary = generate(summary_prompt, cfg)

    log_event(
        "StudyAgent",
        "session_completed",
        session.topic,
        goal=session.goal,
        artifacts=len(session.artifacts),
        steps_done=sum(1 for s in session.plan if s.status == "done"),
    )
    return session


# ── Phase 4: Verify (quiz scoring — called from UI after user takes quiz) ───

def record_quiz_result(topic: str, score: float, correct: int, total: int) -> dict:
    """Update mastery after the user takes the agent-generated quiz."""
    mastery = update_mastery(topic, score, "StudyAgent")
    log_event(
        "StudyAgent",
        "quiz_verified",
        topic,
        score=score,
        correct=correct,
        total=total,
    )
    return {
        "topic": mastery.topic,
        "score": mastery.score,
        "attempts": mastery.attempts,
    }


# ── Helpers ─────────────────────────────────────────────────────────────────

def _preview(text: str, limit: int = 280) -> str:
    text = (text or "").strip()
    return text if len(text) <= limit else text[:limit].rstrip() + "…"
