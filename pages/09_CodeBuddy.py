"""CodeBuddy — AI Code Explainer & Debugger (Gemma 4)."""

import streamlit as st

from core import gemma_engine
from core.obsidian_export import export_study_guide
from core.page_state import ensure_state, set_result
from core.sidebar import render_sidebar
from core.ui_components import inject_global_css, page_header

st.set_page_config(page_title="CodeBuddy", page_icon="🐛", layout="wide")
inject_global_css()
model_config = render_sidebar("codebuddy")

page_header("🐛", "CodeBuddy — Code Explainer & Debugger", "Paste code — get explanations, find bugs, optimize, or convert between languages with Gemma 4.", badge="Code")

ensure_state(
    codebuddy_explain_result="",
    codebuddy_debug_result="",
    codebuddy_convert_result="",
    codebuddy_review_result="",
)

# --- Tabs ---
tab_explain, tab_debug, tab_convert, tab_review = st.tabs(
    ["Explain Code", "Debug / Fix", "Convert Language", "Code Review"]
)


with tab_explain:
    code_explain = st.text_area("Paste code to explain", height=250, key="explain_code")
    col1, col2 = st.columns(2)
    with col1:
        language = st.text_input("Language", "Python", key="explain_lang")
    with col2:
        detail_level = st.selectbox("Detail level", ["Beginner-friendly", "Intermediate", "Expert"], key="explain_detail")

    if st.button("Explain", type="primary", key="btn_explain") and code_explain.strip():
        prompt = f"""Explain the following {language} code at a {detail_level.lower()} level.

```{language.lower()}
{code_explain}
```

Include:
1. **Overview** — what the code does in 1-2 sentences
2. **Step-by-step walkthrough** — explain each significant block
3. **Key concepts** — programming concepts used (with brief explanations if beginner level)
4. **Time/space complexity** — if algorithmic code"""

        config = gemma_engine.GemmaConfig(model=model_config.model, temperature=0.3, max_tokens=3000)
        config.system_prompt = "You are a patient programming tutor. Explain code clearly with examples."

        placeholder = st.empty()
        with st.spinner("Analyzing code..."):
            result = gemma_engine.generate(prompt, config, stream_callback=lambda t: placeholder.markdown(t))
        placeholder.markdown(result)
        set_result("codebuddy_explain_result", result)

    if st.session_state.codebuddy_explain_result:
        st.markdown(st.session_state.codebuddy_explain_result)

with tab_debug:
    code_debug = st.text_area("Paste buggy code", height=200, key="debug_code")
    error_msg = st.text_area("Error message (if any)", height=80, key="debug_error",
                              placeholder="Paste the error traceback or describe the unexpected behavior")

    if st.button("Find & Fix Bugs", type="primary", key="btn_debug") and code_debug.strip():
        prompt = f"""Debug the following code.

```
{code_debug}
```

{f'**Error message:** {error_msg}' if error_msg else '**No error message provided — analyze for logical bugs, edge cases, and potential issues.**'}

Provide:
1. **Bugs Found** — list each bug with the problematic line
2. **Root Cause** — explain why each bug occurs
3. **Fixed Code** — the complete corrected code
4. **Prevention Tips** — how to avoid these bugs in the future"""

        config = gemma_engine.GemmaConfig(model=model_config.model, temperature=0.2, max_tokens=4000)
        config.system_prompt = "You are a senior software engineer debugging code. Be precise and thorough."

        placeholder = st.empty()
        with st.spinner("Debugging..."):
            result = gemma_engine.generate(prompt, config, stream_callback=lambda t: placeholder.markdown(t))
        placeholder.markdown(result)
        set_result("codebuddy_debug_result", result)

    if st.session_state.codebuddy_debug_result:
        st.markdown(st.session_state.codebuddy_debug_result)

with tab_convert:
    code_convert = st.text_area("Paste code to convert", height=200, key="convert_code")
    col1, col2 = st.columns(2)
    with col1:
        from_lang = st.text_input("From language", "Python", key="from_lang")
    with col2:
        to_lang = st.text_input("To language", "JavaScript", key="to_lang")

    if st.button("Convert", type="primary", key="btn_convert") and code_convert.strip():
        prompt = f"""Convert the following {from_lang} code to {to_lang}.

```{from_lang.lower()}
{code_convert}
```

Requirements:
- Idiomatic {to_lang} (use language-specific conventions and best practices)
- Preserve the logic and functionality exactly
- Add comments noting any important differences between the languages
- Include any necessary imports"""

        config = gemma_engine.GemmaConfig(model=model_config.model, temperature=0.2, max_tokens=4000)
        config.system_prompt = f"You are an expert in both {from_lang} and {to_lang}. Convert code idiomatically."

        placeholder = st.empty()
        with st.spinner(f"Converting {from_lang} → {to_lang}..."):
            result = gemma_engine.generate(prompt, config, stream_callback=lambda t: placeholder.markdown(t))
        placeholder.markdown(result)
        set_result("codebuddy_convert_result", result)

    if st.session_state.codebuddy_convert_result:
        st.markdown(st.session_state.codebuddy_convert_result)

with tab_review:
    code_review = st.text_area("Paste code for review", height=250, key="review_code")
    review_focus = st.multiselect("Review focus", [
        "Performance", "Security", "Readability", "Best practices",
        "Error handling", "Testing suggestions",
    ], default=["Readability", "Best practices"])

    if st.button("Review Code", type="primary", key="btn_review") and code_review.strip():
        prompt = f"""Review the following code. Focus on: {', '.join(review_focus)}.

```
{code_review}
```

Provide:
1. **Overall Quality** — rating out of 10
2. **Strengths** — what's done well
3. **Issues Found** — ordered by severity (critical → minor)
4. **Refactored Version** — improved code with changes highlighted
5. **Suggestions** — additional improvements for production-readiness"""

        config = gemma_engine.GemmaConfig(model=model_config.model, temperature=0.3, max_tokens=4000)
        config.system_prompt = "You are a senior code reviewer. Be constructive, specific, and prioritize by impact."

        placeholder = st.empty()
        with st.spinner("Reviewing code..."):
            result = gemma_engine.generate(prompt, config, stream_callback=lambda t: placeholder.markdown(t))
        placeholder.markdown(result)
        set_result("codebuddy_review_result", result)

    if st.session_state.codebuddy_review_result:
        st.markdown(st.session_state.codebuddy_review_result)
        if st.button("Export Review to Obsidian"):
            path = export_study_guide(
                "CodeBuddy Review",
                st.session_state.codebuddy_review_result,
                tags=["codebuddy", "code-review"],
            )
            st.success(f"Exported to: {path}")
