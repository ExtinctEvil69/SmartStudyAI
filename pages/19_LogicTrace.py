"""LogicTrace — debugging, root-cause analysis, and execution tracing."""

import streamlit as st
import streamlit.components.v1 as components

from core import gemma_engine
from core.mermaid_utils import build_mermaid_html, extract_mermaid_code
from core.obsidian_export import export_mind_map, export_study_guide
from core.page_state import ensure_state, set_result
from core.sidebar import render_sidebar
from core.ui_components import inject_global_css, page_header

st.set_page_config(page_title="LogicTrace", page_icon="🐛", layout="wide")
inject_global_css()
model_config = render_sidebar("logictrace")

page_header("🐛", "LogicTrace — Debug Visualizer", "Paste errors, logs, or code and get a root-cause analysis, execution trace, and next-step debugging plan.", badge="Debug")

ensure_state(
    logictrace_debug_result="",
    logictrace_flow_result="",
    logictrace_flow_mermaid="",
    logictrace_triage_result="",
)


tab_debug, tab_flow, tab_triage = st.tabs(["Trace an Error", "Execution Flow", "Bug Triage"])

with tab_debug:
    error_trace = st.text_area(
        "Error traceback or failure output",
        height=180,
        placeholder="Paste the traceback, compiler error, failing test output, or runtime exception here.",
    )
    code_snippet = st.text_area(
        "Relevant code",
        height=220,
        placeholder="Paste the function, class, or surrounding code that appears to be involved.",
    )
    expected_behavior = st.text_area(
        "Expected behavior",
        height=80,
        placeholder="What should have happened instead?",
    )

    if st.button("Analyze Failure", type="primary", key="logictrace_debug") and (error_trace.strip() or code_snippet.strip()):
        prompt = f"""Analyze this software failure.

Expected behavior:
{expected_behavior or 'Not provided'}

Failure output:
{error_trace or 'Not provided'}

Relevant code:
```
{code_snippet[:16000]}
```

Return these sections:
## Likely Root Cause
## What The Program Is Doing
## Most Suspicious Lines / Regions
## Verification Steps
## Fix Options
## Regression Tests To Add
"""
        config = gemma_engine.GemmaConfig(model=model_config.model, temperature=0.2, max_tokens=4000)
        config.system_prompt = "You are a senior debugging assistant. Prioritize concrete root causes over generic advice."

        placeholder = st.empty()
        with st.spinner("Tracing the failure..."):
            result = gemma_engine.generate(prompt, config, stream_callback=lambda text: placeholder.markdown(text))
        placeholder.markdown(result)
        set_result("logictrace_debug_result", result)

    if st.session_state.logictrace_debug_result:
        st.markdown(st.session_state.logictrace_debug_result)
        if st.button("Export Failure Analysis"):
            path = export_study_guide("LogicTrace Failure Analysis", st.session_state.logictrace_debug_result, tags=["logictrace", "debugging"])
            st.success(f"Exported to: {path}")

with tab_flow:
    flow_code = st.text_area(
        "Code to trace",
        height=260,
        placeholder="Paste a function or module to visualize its execution path.",
    )
    flow_input = st.text_input("Input / scenario", placeholder="e.g. POST /login with invalid password")
    flow_focus = st.selectbox("Focus", ["Full execution path", "State changes", "Branching decisions", "Data flow"])

    if st.button("Generate Execution Trace", type="primary", key="logictrace_flow") and flow_code.strip():
        prompt = f"""Analyze this code path.

Scenario: {flow_input or 'Generic execution'}
Focus: {flow_focus}

Code:
```
{flow_code[:16000]}
```

Return:
1. A short overview.
2. A numbered step-by-step execution trace.
3. A variable/state checkpoint list.
4. A Mermaid flowchart in a fenced ```mermaid block. STRICT MERMAID RULES: first line "flowchart TD", node IDs alphanumeric only (A, step1), labels in square brackets A[Parse Input], decision nodes D{{Is Valid?}}, edge labels A -->|yes| B, NO parentheses/colons/quotes/markdown inside labels, under 25 nodes.
5. The highest-risk failure points.
"""
        config = gemma_engine.GemmaConfig(model=model_config.model, temperature=0.2, max_tokens=4500)
        config.system_prompt = "You are a software engineer who explains execution flow clearly and produces valid Mermaid when asked."

        placeholder = st.empty()
        with st.spinner("Building execution trace..."):
            result = gemma_engine.generate(prompt, config, stream_callback=lambda text: placeholder.markdown(text))
        placeholder.markdown(result)
        set_result("logictrace_flow_result", result)
        set_result("logictrace_flow_mermaid", extract_mermaid_code(result, fallback_prefix="flowchart TD"))

    if st.session_state.logictrace_flow_result:
        st.markdown(st.session_state.logictrace_flow_result)
        if st.session_state.logictrace_flow_mermaid:
            st.subheader("Flowchart")
            components.html(build_mermaid_html(st.session_state.logictrace_flow_mermaid), height=550, scrolling=True)
            export_col, code_col = st.columns(2)
            if export_col.button("Export Flowchart"):
                path = export_mind_map("LogicTrace Flow", st.session_state.logictrace_flow_mermaid, tags=["logictrace", "flow"])
                st.success(f"Exported to: {path}")
            code_col.code(st.session_state.logictrace_flow_mermaid, language="mermaid")

with tab_triage:
    bug_report = st.text_area(
        "Bug report or symptom summary",
        height=150,
        placeholder="Describe the bug as reported by the user or QA.",
    )
    logs = st.text_area("Relevant logs", height=180, placeholder="Paste logs, request IDs, or monitoring output.")
    recent_changes = st.text_area(
        "Recent changes / deploy context",
        height=100,
        placeholder="e.g. Switched cache backend, added auth middleware, changed DB schema",
    )

    if st.button("Build Triage Plan", type="primary", key="logictrace_triage") and bug_report.strip():
        prompt = f"""Triage this production bug.

Bug report:
{bug_report}

Logs:
{logs or 'Not provided'}

Recent changes:
{recent_changes or 'Not provided'}

Return these sections:
## Initial Assessment
## Top Hypotheses Ranked
## Fastest Reproduction Path
## Debugging Checklist
## Instrumentation / Logging To Add
## Minimal Safe Fix
## Rollback Criteria
"""
        config = gemma_engine.GemmaConfig(model=model_config.model, temperature=0.25, max_tokens=3500)
        config.system_prompt = "You are an incident responder and software engineer. Be specific and operationally practical."

        placeholder = st.empty()
        with st.spinner("Preparing triage plan..."):
            result = gemma_engine.generate(prompt, config, stream_callback=lambda text: placeholder.markdown(text))
        placeholder.markdown(result)
        set_result("logictrace_triage_result", result)

    if st.session_state.logictrace_triage_result:
        st.markdown(st.session_state.logictrace_triage_result)
        if st.button("Export Triage Plan"):
            path = export_study_guide("LogicTrace Triage Plan", st.session_state.logictrace_triage_result, tags=["logictrace", "triage"])
            st.success(f"Exported to: {path}")
