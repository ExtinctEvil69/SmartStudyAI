"""ArchViz — Architecture Diagram Generator (Gemma 4 → Mermaid.js)."""

import streamlit as st
import streamlit.components.v1 as components

from core import gemma_engine
from core.mermaid_utils import build_mermaid_html, extract_mermaid_code
from core.obsidian_export import export_mind_map
from core.page_state import ensure_state, set_result
from core.sidebar import render_sidebar
from core.ui_components import inject_global_css, page_header

st.set_page_config(page_title="ArchViz", page_icon="🏗️", layout="wide")
inject_global_css()
model_config = render_sidebar("archviz")

page_header("🏗️", "ArchViz — Architecture Diagram Generator", "Describe a system — get architecture diagrams rendered as Mermaid.js, powered by Gemma 4.", badge="Diagrams")

ensure_state(archviz_code="", archviz_description="", archviz_title="")
ensure_state(archviz_diagram_type="")

# --- Input ---
col1, col2 = st.columns([2, 1])

with col1:
    system_desc = st.text_area(
        "Describe the system architecture",
        height=180,
        placeholder="e.g. A microservices e-commerce platform with user service, product catalog, order processing, payment gateway, and notification service. Uses RabbitMQ for async messaging and Redis for caching.",
    )

with col2:
    diagram_type = st.selectbox("Diagram type", [
        "System Architecture (C4 style)",
        "Sequence Diagram",
        "Class Diagram",
        "Entity Relationship",
        "Flowchart",
        "State Diagram",
        "Deployment Diagram",
    ])
    detail_level = st.selectbox("Detail level", ["High-level overview", "Detailed", "Implementation-level"])

mermaid_type_map = {
    "System Architecture (C4 style)": "graph TD",
    "Sequence Diagram": "sequenceDiagram",
    "Class Diagram": "classDiagram",
    "Entity Relationship": "erDiagram",
    "Flowchart": "flowchart TD",
    "State Diagram": "stateDiagram-v2",
    "Deployment Diagram": "graph LR",
}

if st.button("Generate Diagram", type="primary") and system_desc.strip():
    mermaid_syntax = mermaid_type_map[diagram_type]

    prompt = f"""Generate a Mermaid.js {diagram_type.lower()} for the following system:

**System:** {system_desc}
**Detail level:** {detail_level}
**Mermaid type:** {mermaid_syntax}

STRICT SYNTAX RULES — follow these exactly:
- First line must be exactly: {mermaid_syntax}
- Node IDs must be simple alphanumeric (e.g. A, userSvc, db1) — NO spaces, NO special chars
- Node labels go inside square brackets: A[User Service]
- Edge labels use pipe syntax: A -->|sends request| B
- Do NOT put parentheses () inside square bracket labels
- Do NOT use colons : in node labels
- Do NOT use markdown formatting (no **, no #, no _)
- Use subgraph/end for grouping
- Keep it under 25 nodes for readability
- Output ONLY the Mermaid code. No explanation, no fences, no commentary.

{mermaid_syntax}
..."""

    config = gemma_engine.GemmaConfig(model=model_config.model, temperature=0.2, max_tokens=3000)
    config.system_prompt = "You are a software architect. Output ONLY valid Mermaid.js diagram code. No markdown fences, no explanation. Just the diagram starting with the diagram type declaration."

    with st.spinner("Generating architecture diagram..."):
        result = gemma_engine.generate(prompt, config)

    if result.startswith("[") and "error" in result.lower():
        st.error(result)
    else:
        set_result("archviz_code", extract_mermaid_code(result, fallback_prefix=mermaid_syntax))
        set_result("archviz_title", f"ArchViz - {system_desc[:40]}")
        set_result("archviz_diagram_type", diagram_type)

if st.session_state.archviz_code:
    st.subheader("Architecture Diagram")
    components.html(build_mermaid_html(st.session_state.archviz_code), height=600, scrolling=True)

    with st.expander("Mermaid Source Code"):
        st.code(st.session_state.archviz_code, language="mermaid")

    col_e1, col_e2 = st.columns(2)
    if col_e1.button("Export to Obsidian"):
        path = export_mind_map(
            st.session_state.archviz_title,
            st.session_state.archviz_code,
            tags=["archviz", (st.session_state.archviz_diagram_type or diagram_type).lower().replace(" ", "-")],
        )
        st.success(f"Exported to: {path}")

    if col_e2.button("Add Description"):
        desc_prompt = f"""Based on this architecture diagram:

```mermaid
{st.session_state.archviz_code}
```

Write a concise architecture description:
1. **Overview** — what the system does
2. **Components** — key components and their roles
3. **Data Flow** — how data moves through the system
4. **Key Decisions** — important architectural choices and trade-offs"""

        desc_config = gemma_engine.GemmaConfig(model=model_config.model, temperature=0.4, max_tokens=2000)
        desc_placeholder = st.empty()
        with st.spinner("Generating description..."):
            desc = gemma_engine.generate(desc_prompt, desc_config, stream_callback=lambda t: desc_placeholder.markdown(t))
        desc_placeholder.markdown(desc)
        set_result("archviz_description", desc)

    if st.session_state.archviz_description:
        st.markdown(st.session_state.archviz_description)
