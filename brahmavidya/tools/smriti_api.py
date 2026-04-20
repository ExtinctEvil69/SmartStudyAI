"""Vidya Smriti — Memory dashboard API router."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from brahmavidya.memory import (
    get_dashboard_data,
    get_events,
    get_mastery,
    get_recommendations,
    LearnerProfile,
)

router = APIRouter()


class ProfileUpdate(BaseModel):
    name: str = ""
    goals: list[str] = []
    strengths: list[str] = []
    preferred_style: str = "visual"


@router.get("/dashboard")
async def dashboard():
    return get_dashboard_data()


@router.get("/events")
async def events(tool: str | None = None, limit: int = 50):
    return get_events(tool=tool, limit=limit)


@router.get("/mastery")
async def mastery(topic: str | None = None):
    return get_mastery(topic=topic)


@router.get("/recommendations")
async def recommendations():
    return get_recommendations()


@router.post("/profile")
async def update_profile(req: ProfileUpdate):
    profile = LearnerProfile.load()
    if req.name:
        profile.name = req.name
    if req.goals:
        profile.goals = req.goals
    if req.strengths:
        profile.strengths = req.strengths
    if req.preferred_style:
        profile.preferred_style = req.preferred_style
    profile.save()
    return {"status": "ok", "profile": {"name": profile.name, "goals": profile.goals}}


@router.get("/profile")
async def get_profile():
    profile = LearnerProfile.load()
    from dataclasses import asdict
    return asdict(profile)
