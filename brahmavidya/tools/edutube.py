"""EduTube — YouTube transcript study notes API router."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from core.gemma_engine import GemmaConfig, generate
from core.cag_engine import generate_from_context, generate_flashcards
from core.youtube_engine import fetch_transcript
from brahmavidya.memory import log_event, register_content

router = APIRouter()


class FetchRequest(BaseModel):
    url: str


class FetchResponse(BaseModel):
    transcript: str
    char_count: int


class GenerateRequest(BaseModel):
    transcript: str
    output_type: str = "Study Notes"
    subject: str = ""
    source_label: str = ""


class GenerateResponse(BaseModel):
    result: str | dict
    output_type: str


INSTRUCTIONS = {
    "Study Notes": """Create comprehensive study notes from this video transcript. Include:
## Key Topics
- List main topics covered

## Detailed Notes
- Organized by topic with bullet points
- Bold key terms and concepts
- Include examples mentioned

## Key Takeaways
- 5-7 main takeaways from the video

## Questions to Review
- 3-5 self-test questions based on the content""",

    "Summary": """Write a concise summary of this video transcript:
1. One-paragraph overview
2. Main points (bullet list)
3. Key conclusions
4. Who this is most useful for""",

    "Key Concepts": """Extract and explain all key concepts from this transcript:
For each concept:
- **Concept name** in bold
- Brief definition (1-2 sentences)
- How it relates to other concepts mentioned
- Example from the video if available

Organize from foundational to advanced concepts.""",

    "Quiz Prep Notes": """Create quiz preparation notes from this transcript:
## Must-Know Facts
- Key facts, dates, formulas, definitions

## Common Exam Questions
- Likely exam questions with brief model answers

## Concept Connections
- How different topics connect to each other

## Potential Trick Questions
- Areas where misunderstanding is common""",
}


@router.post("/fetch", response_model=FetchResponse)
async def fetch(req: FetchRequest):
    transcript = fetch_transcript(req.url)
    register_content("youtube", req.url, "EduTube", url=req.url)
    return FetchResponse(transcript=transcript, char_count=len(transcript))


@router.post("/generate", response_model=GenerateResponse)
async def gen(req: GenerateRequest):
    config = GemmaConfig(temperature=0.4)

    if req.output_type == "Flashcards":
        result = generate_flashcards(req.transcript, num_cards=15, config=config)
        log_event("EduTube", "flashcards_created", req.subject or "Video content",
                  num_cards=len(result.get("cards", [])) if result else 0, source=req.source_label)
        return GenerateResponse(result=result or {"cards": []}, output_type=req.output_type)

    instruction = INSTRUCTIONS.get(req.output_type, INSTRUCTIONS["Study Notes"])
    if req.subject:
        instruction = f"Subject: {req.subject}\n\n{instruction}"

    result = generate_from_context(
        req.transcript, instruction,
        system_prompt="You are an expert educator creating study materials from video content.",
        config=config,
    )
    log_event("EduTube", "notes_generated", req.subject or "Video content",
              output_type=req.output_type, source=req.source_label)
    return GenerateResponse(result=result, output_type=req.output_type)
