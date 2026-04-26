"""Generic tool runner — drives any registry-defined tool from tool_configs.TOOLS."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.gemma_engine import GemmaConfig, generate
from brahmavidya.memory import log_event
from brahmavidya.tool_configs import all_tools, get_tool

router = APIRouter()


class RunRequest(BaseModel):
    input: str
    options: dict = Field(default_factory=dict)


@router.get("/list")
async def list_tools():
    """Return the public registry — frontend uses this to render sidebar + pages."""
    return {"tools": all_tools()}


@router.get("/{tool_id}")
async def get_config(tool_id: str):
    cfg = get_tool(tool_id)
    if not cfg:
        raise HTTPException(404, f"unknown tool: {tool_id}")
    return cfg


@router.post("/{tool_id}/run")
async def run(tool_id: str, req: RunRequest):
    cfg = get_tool(tool_id)
    if not cfg:
        raise HTTPException(404, f"unknown tool: {tool_id}")
    if not req.input.strip():
        raise HTTPException(400, "input is empty")

    # Fill in any {placeholder} in the prompt template using options + input.
    fmt = {"input": req.input}
    for opt in cfg.get("options", []):
        opt_id = opt["id"]
        fmt[opt_id] = req.options.get(opt_id, "") or _default_for(opt)

    try:
        prompt = cfg["prompt"].format(**fmt)
    except KeyError as e:
        raise HTTPException(400, f"missing option: {e}")

    gem_cfg = GemmaConfig(temperature=0.4, max_tokens=3000)
    gem_cfg.system_prompt = cfg.get("system", "")
    result = generate(prompt, gem_cfg)

    # Strip mermaid fences if the tool expects raw mermaid output
    kind = cfg.get("output_kind", "markdown")
    if kind == "mermaid":
        result = _strip_mermaid_fences(result)

    log_event(cfg["name"], "ran", req.input[:80], **req.options)

    return {
        "tool_id": tool_id,
        "kind": kind,
        "result": result,
    }


def _default_for(opt: dict) -> str:
    if opt.get("type") == "select":
        vals = opt.get("values") or []
        return vals[0] if vals else ""
    return ""


def _strip_mermaid_fences(text: str) -> str:
    """Pull pure mermaid out of a possibly-fenced response."""
    t = (text or "").strip()
    if "```mermaid" in t:
        t = t.split("```mermaid", 1)[1].split("```", 1)[0].strip()
    elif t.startswith("```"):
        t = t.split("```", 2)[1].strip() if t.count("```") >= 2 else t.strip("`")
    return t
