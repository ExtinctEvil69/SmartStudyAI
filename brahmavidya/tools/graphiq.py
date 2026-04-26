"""GraphiQ — 2D equation graphing via Desmos.

The actual rendering happens client-side via the Desmos API. This endpoint
asks Gemma to translate a natural-language description into a list of
Desmos-friendly equation strings.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from core.gemma_engine import GemmaConfig, generate_json
from brahmavidya.memory import log_event

router = APIRouter()


class GraphRequest(BaseModel):
    description: str
    style: str = "standard"   # standard | physics | calculus | implicit


PHYSICS_TEMPLATES = {
    "projectile": ["y=v_0\\sin(\\theta)x - 0.5g x^2/(v_0\\cos(\\theta))^2"],
    "pendulum":   ["y=A\\cos(\\sqrt{g/L} x)"],
    "spring":     ["y=A\\cos(\\sqrt{k/m} x + \\phi)"],
}


@router.post("/equations")
async def equations(req: GraphRequest):
    """Translate a description → list of Desmos equation strings + window."""
    prompt = f"""Convert this description into Desmos-compatible equations.
Style: {req.style}

Description: {req.description}

Output JSON only:
{{
  "equations": ["y=...", "y=...", ...],
  "window": {{"xmin": -10, "xmax": 10, "ymin": -10, "ymax": 10}},
  "explanation": "1-2 sentences on what these equations represent"
}}

Notes:
- Use Desmos syntax: y= or x= or implicit (e.g. x^2+y^2=25 for a circle)
- For physics, use realistic constants
- For implicit shapes (heart, lemniscate), use forms like (x^2+y^2-1)^3=x^2y^3"""

    cfg = GemmaConfig(temperature=0.3, max_tokens=1500)
    cfg.system_prompt = "You are a precise math/physics assistant who outputs valid Desmos equations only."
    result = generate_json(prompt, cfg) or {}

    if "equations" not in result:
        result = {
            "equations": ["y=x^2"],
            "window": {"xmin": -10, "xmax": 10, "ymin": -10, "ymax": 10},
            "explanation": "Default parabola — couldn't parse description.",
        }

    log_event("GraphiQ", "graph_created", req.description[:80], style=req.style)
    return result
