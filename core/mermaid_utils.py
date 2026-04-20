"""Helpers for extracting, sanitizing, and rendering Mermaid diagrams."""

from __future__ import annotations

import base64
import json
import re


MERMAID_PREFIXES = (
    "flowchart",
    "graph",
    "mindmap",
    "sequenceDiagram",
    "classDiagram",
    "erDiagram",
    "stateDiagram-v2",
    "journey",
    "timeline",
)


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def extract_mermaid_code(raw_text: str, fallback_prefix: str = "flowchart TD") -> str:
    """Pull Mermaid code out of LLM output (may be wrapped in fences)."""
    text = raw_text.strip()
    match = re.search(r"```(?:mermaid)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    code = match.group(1).strip() if match else text
    code = re.sub(r"^```\w*\n?", "", code)
    code = re.sub(r"\n?```$", "", code).strip()

    code = sanitize_mermaid(code)

    if not code.startswith(MERMAID_PREFIXES):
        code = f"{fallback_prefix}\n{code}"

    return code


# ---------------------------------------------------------------------------
# Sanitisation — fix the most common LLM Mermaid mistakes
# ---------------------------------------------------------------------------

def sanitize_mermaid(code: str) -> str:
    """Best-effort repair of broken Mermaid emitted by an LLM."""
    code = code.replace("\t", "    ")
    code = code.replace("\r\n", "\n").replace("\r", "\n")
    # smart quotes → ascii
    code = code.replace("\u201c", '"').replace("\u201d", '"')
    code = code.replace("\u2018", "'").replace("\u2019", "'")
    # em/en dashes → --
    code = code.replace("\u2014", "--").replace("\u2013", "--")

    lines = code.split("\n")
    cleaned: list[str] = []
    for line in lines:
        stripped = line.strip()
        # drop blank markdown-like headers LLMs sometimes inject
        if stripped.startswith("#"):
            continue
        # drop stray markdown bold/italic wrapping
        if stripped in ("**", "***", "__", "___"):
            continue
        # remove inline bold/italic markers that break mermaid labels
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
        line = re.sub(r"\*(.+?)\*", r"\1", line)

        cleaned.append(line)

    code = "\n".join(cleaned)

    # --- Fix arrows with colons (Gemma likes A -->: text: B) --------------
    code = re.sub(r"(-->)\s*:\s*", r"\1|", code)
    # close unclosed pipe labels:  -->|text\n  →  -->|text|\n
    code = re.sub(r"(-->\|[^|\n]+)\n", r"\1|\n", code)

    # --- Remove duplicate direction lines ---------------------------------
    first_line = code.split("\n", 1)[0].strip()
    if first_line.startswith(MERMAID_PREFIXES):
        rest_lines = code.split("\n")[1:]
        rest_lines = [
            ln for ln in rest_lines
            if not ln.strip().startswith(MERMAID_PREFIXES)
        ]
        code = first_line + "\n" + "\n".join(rest_lines)

    # collapse 3+ blank lines to 1
    code = re.sub(r"\n{3,}", "\n\n", code)

    return code.strip()


# ---------------------------------------------------------------------------
# mermaid.ink URL — renders Mermaid server-side, returns an image
# ---------------------------------------------------------------------------

def _mermaid_ink_url(mermaid_code: str, theme: str = "dark") -> str:
    """Build a mermaid.ink image URL using plain base64 encoding."""
    payload = json.dumps({"code": mermaid_code, "mermaid": {"theme": theme}})
    encoded = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")
    return f"https://mermaid.ink/svg/{encoded}"


# ---------------------------------------------------------------------------
# HTML renderer — uses mermaid.ink <img> (no client-side JS needed)
# ---------------------------------------------------------------------------

def build_mermaid_html(mermaid_code: str, theme: str = "dark") -> str:
    """Return an HTML snippet that renders a Mermaid diagram via mermaid.ink.

    Uses a server-rendered SVG image — no client-side Mermaid JS required,
    so it works reliably inside Streamlit iframes without CDN/sandbox issues.
    """
    img_url = _mermaid_ink_url(mermaid_code, theme)

    return f"""
    <style>
      body {{ margin: 0; padding: 0; background: #0a0a0f; }}
      #diagram-container {{
        width: 100%;
        min-height: 200px;
        display: flex;
        justify-content: center;
        align-items: flex-start;
        overflow: auto;
        background: #0a0a0f;
        padding: 16px;
        border-radius: 8px;
      }}
      #diagram-container img {{
        max-width: 100%;
        height: auto;
      }}
      #diagram-error {{
        display: none;
        padding: 12px 16px;
        margin-top: 8px;
        background: #1a1a2e;
        border-left: 3px solid #6C5CE7;
        color: #ccc;
        font-size: 13px;
        border-radius: 4px;
      }}
    </style>
    <div id="diagram-container">
      <img src="{img_url}"
           alt="Diagram"
           onerror="
             this.style.display='none';
             var code = {json.dumps(mermaid_code)};
             var pre = document.createElement('pre');
             pre.style.cssText = 'text-align:left;padding:16px;background:#13131a;border-radius:8px;color:#a0a0c0;font-size:13px;overflow:auto;white-space:pre-wrap;width:100%';
             pre.textContent = code;
             this.parentNode.appendChild(pre);
             document.getElementById('diagram-error').style.display = 'block';
           " />
    </div>
    <div id="diagram-error">Diagram image could not be loaded. The Mermaid source is shown above.</div>
    """
