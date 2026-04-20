"""CodeFlow — code to flowcharts with Gemma."""

import streamlit as st
import streamlit.components.v1 as components

from core import gemma_engine
from core.mermaid_utils import build_mermaid_html, extract_mermaid_code
from core.obsidian_export import export_mind_map
from core.page_state import ensure_state, set_result
from core.sidebar import render_sidebar
from core.ui_components import inject_global_css, page_header

st.set_page_config(page_title="CodeFlow", page_icon="🔀", layout="wide")
inject_global_css()
model_config = render_sidebar("codeflow")

page_header("🔀", "CodeFlow — Code to Flowcharts", "Paste code and get Mermaid.js flowcharts with local Gemma. Part of the CodeLens suite.", badge="Flow")

ensure_state(codeflow_code="", codeflow_model="")

code_input = st.text_area("Paste your code", height=300, placeholder="Paste a function, class, or module...")
diagram_type = st.selectbox("Diagram type", [
    "flowchart TD",
    "flowchart LR",
    "sequenceDiagram",
    "classDiagram",
    "stateDiagram-v2",
])

focus = st.selectbox("Focus on", [
    "Execution flow",
    "Function call relationships",
    "Data flow",
    "Error handling paths",
    "State transitions",
])

if st.button("Generate Flowchart", type="primary") and code_input.strip():
    prompt = f"""Analyze this code and generate a Mermaid.js {diagram_type} diagram showing: {focus}.

STRICT SYNTAX RULES:
- First line must be exactly: {diagram_type}
- Node IDs: simple alphanumeric only (e.g. A, step1, funcX) — NO spaces or special chars
- Node labels in square brackets: A[Parse Input]
- Decision nodes use curly braces: D{{Is Valid?}}
- Edge labels with pipes: A -->|yes| B
- Do NOT put parentheses, colons, or quotes inside labels
- Do NOT use markdown formatting
- Keep under 25 nodes
- Output ONLY the Mermaid code. No explanation, no fences.

Code:
```
{code_input[:15000]}
```"""

    placeholder = st.empty()
    with st.spinner("Analyzing code with Gemma..."):
        config = gemma_engine.GemmaConfig(model=model_config.model, temperature=0.2, max_tokens=3500)
        result = gemma_engine.generate(prompt, config, stream_callback=lambda t: placeholder.markdown(f"```mermaid\n{t}\n```"))
    if result.startswith("[") and "error" in result.lower():
        st.error(result)
    else:
        set_result("codeflow_code", extract_mermaid_code(result, fallback_prefix=diagram_type))
        set_result("codeflow_model", model_config.model)

if st.session_state.codeflow_code:
    st.code(st.session_state.codeflow_code, language="mermaid")
    components.html(build_mermaid_html(st.session_state.codeflow_code), height=600, scrolling=True)
    if st.button("Export to Obsidian"):
        path = export_mind_map("CodeFlow Diagram", st.session_state.codeflow_code, tags=["codeflow", "codelens"])
        st.success(f"Exported: {path}")
