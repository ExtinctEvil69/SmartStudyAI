"""QuizForge — Adaptive quiz generation API router."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from core.cag_engine import generate_quiz
from core.gemma_engine import GemmaConfig
from brahmavidya.memory import log_event, update_mastery

router = APIRouter()


class QuizRequest(BaseModel):
    content: str
    subject: str = ""
    topic: str = ""
    num_questions: int = 5
    difficulty: str = "mixed"
    question_types: str = "mcq"


class QuizResponse(BaseModel):
    quiz: dict | None
    error: str = ""


class ScoreRequest(BaseModel):
    topic: str
    score: float
    total: int
    correct: int


class ScoreResponse(BaseModel):
    mastery: dict
    message: str


@router.post("/generate", response_model=QuizResponse)
async def gen_quiz(req: QuizRequest):
    config = GemmaConfig(temperature=0.3)
    quiz = generate_quiz(
        context=req.content,
        subject=req.subject,
        topic=req.topic,
        num_questions=req.num_questions,
        difficulty=req.difficulty,
        question_types=req.question_types,
        config=config,
    )
    if quiz:
        log_event("QuizForge", "quiz_generated", req.topic or req.subject or "General",
                  num_questions=req.num_questions, difficulty=req.difficulty)
        return QuizResponse(quiz=quiz)
    return QuizResponse(quiz=None, error="Failed to generate quiz. Try again.")


@router.post("/score", response_model=ScoreResponse)
async def score_quiz(req: ScoreRequest):
    mastery = update_mastery(req.topic, req.score, "QuizForge")
    log_event("QuizForge", "quiz_completed", req.topic,
              score=req.score, correct=req.correct, total=req.total)
    msg = "Great job!" if req.score >= 80 else "Keep practicing!" if req.score >= 50 else "Review this topic and try again."
    return ScoreResponse(mastery={"topic": mastery.topic, "score": mastery.score, "attempts": mastery.attempts}, message=msg)
