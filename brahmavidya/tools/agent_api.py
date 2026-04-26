"""StudyAgent API — Plan Mode + Execute pattern."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from brahmavidya.agent import (
    AgentSession,
    AgentStep,
    TOOL_CATALOG,
    execute_session,
    plan_session,
    record_quiz_result,
)
from brahmavidya.memory import get_mastery

router = APIRouter()


class PlanRequest(BaseModel):
    goal: str
    topic: str


class PlanStep(BaseModel):
    action: str
    goal: str
    args: dict = Field(default_factory=dict)


class ExecuteRequest(BaseModel):
    goal: str
    topic: str
    plan: list[PlanStep]
    rationale: str = ""


class QuizVerifyRequest(BaseModel):
    topic: str
    score: float
    correct: int
    total: int


@router.get("/tools")
async def list_tools():
    return {"tools": TOOL_CATALOG}


@router.post("/plan")
async def plan(req: PlanRequest):
    """Phase 1+2: Explore prior mastery + Plan (user-approvable)."""
    session = plan_session(req.goal, req.topic)
    return session.to_dict()


@router.post("/execute")
async def execute(req: ExecuteRequest):
    """Phase 3+5: Execute an approved plan and record the session."""
    session = AgentSession(goal=req.goal, topic=req.topic, rationale=req.rationale)
    prior = get_mastery(req.topic)
    if isinstance(prior, dict) and prior:
        session.mastery_before = float(prior.get("score", 0))
    session.plan = [AgentStep(action=p.action, goal=p.goal, args=p.args) for p in req.plan]
    execute_session(session)
    return session.to_dict()


@router.post("/verify")
async def verify(req: QuizVerifyRequest):
    """Phase 4: record quiz result after user takes the agent-generated quiz."""
    mastery = record_quiz_result(req.topic, req.score, req.correct, req.total)
    return {"mastery": mastery, "message": _verdict(req.score)}


def _verdict(pct: float) -> str:
    if pct >= 85:
        return "Excellent — mastery above target."
    if pct >= 65:
        return "Solid understanding. One more round would cement it."
    if pct >= 40:
        return "Partial grasp. Revisit study notes and retry."
    return "Needs another study cycle. Re-run the agent with a narrower goal."
