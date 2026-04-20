"""MindMapper — Mind map generation API router."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from core.gemma_engine import GemmaConfig, generate
from core.cag_engine import generate_from_context
from brahmavidya.memory import log_event

router = APIRouter()


class MindMapRequest(BaseModel):
    content: str
    topic: str = ""
    style: str = "hierarchical"


class MindMapResponse(BaseModel):
    mermaid_code: str
    summary: str


@router.post("/generate", response_model=MindMapResponse)
async def gen_mindmap(req: MindMapRequest):
    topic_label = req.topic or "Topic"

    instruction = f"""Analyze the following content and create a mind map in Mermaid.js syntax.

Topic: {topic_label}
Style: {req.style}

Generate a Mermaid mindmap diagram. Output ONLY the Mermaid code block, nothing else.
Use this format:

mindmap
  root(({topic_label}))
    Branch 1
      Sub-topic A
      Sub-topic B
    Branch 2
      Sub-topic C
        Detail 1
        Detail 2
    Branch 3
      Sub-topic D

Make branches meaningful and cover all key concepts from the content.
Also provide a one-paragraph summary of the mind map structure after the mermaid code, separated by ---SUMMARY---"""

    config = GemmaConfig(temperature=0.4)
    result = generate_from_context(
        req.content, instruction,
        system_prompt="You are an expert at creating clear, well-organized mind maps for studying. Generate valid Mermaid.js mindmap syntax.",
        config=config,
    )

    # Split mermaid code from summary
    parts = result.split("---SUMMARY---")
    mermaid_code = parts[0].strip()
    summary = parts[1].strip() if len(parts) > 1 else "Mind map generated successfully."

    # Clean up mermaid code - remove markdown fences if present
    if "```mermaid" in mermaid_code:
        mermaid_code = mermaid_code.split("```mermaid")[1].split("```")[0].strip()
    elif "```" in mermaid_code:
        mermaid_code = mermaid_code.split("```")[1].split("```")[0].strip()

    log_event("MindMapper", "mindmap_generated", topic_label, style=req.style)
    return MindMapResponse(mermaid_code=mermaid_code, summary=summary)
