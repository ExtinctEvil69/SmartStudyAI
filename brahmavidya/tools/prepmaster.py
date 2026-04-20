"""PrepMaster — Study plan generation API router."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from core.cag_engine import generate_study_plan, generate_study_guide
from core.gemma_engine import GemmaConfig
from brahmavidya.memory import log_event

router = APIRouter()


class StudyPlanRequest(BaseModel):
    content: str
    goal: str = ""
    duration_weeks: int = 4
    hours_per_week: int = 10


class StudyPlanResponse(BaseModel):
    plan: str


class StudyGuideRequest(BaseModel):
    content: str


class StudyGuideResponse(BaseModel):
    guide: str


@router.post("/plan", response_model=StudyPlanResponse)
async def gen_plan(req: StudyPlanRequest):
    config = GemmaConfig(temperature=0.4)
    plan = generate_study_plan(
        context=req.content,
        goal=req.goal,
        duration_weeks=req.duration_weeks,
        hours_per_week=req.hours_per_week,
        config=config,
    )
    log_event("PrepMaster", "study_plan_generated", req.goal or "Study plan",
              duration_weeks=req.duration_weeks, hours_per_week=req.hours_per_week)
    return StudyPlanResponse(plan=plan)


@router.post("/guide", response_model=StudyGuideResponse)
async def gen_guide(req: StudyGuideRequest):
    config = GemmaConfig(temperature=0.4)
    guide = generate_study_guide(req.content, config=config)
    log_event("PrepMaster", "study_guide_generated", "Study guide")
    return StudyGuideResponse(guide=guide)
