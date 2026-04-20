"""FeatureForge — Feature Specification Generator (Gemma 4)."""

import streamlit as st

from core import gemma_engine
from core.obsidian_export import export_study_guide
from core.page_state import ensure_state, set_result
from core.sidebar import render_sidebar
from core.ui_components import inject_global_css, page_header

st.set_page_config(page_title="FeatureForge", page_icon="🔧", layout="wide")
inject_global_css()
model_config = render_sidebar("featureforge")

page_header("🔧", "FeatureForge — Feature Spec Generator", "Describe a feature idea — get a complete specification document with user stories, acceptance criteria, and technical design.", badge="Specs")

ensure_state(
    featureforge_spec_result="",
    featureforge_spec_title="",
    featureforge_stories_result="",
    featureforge_api_result="",
    featureforge_api_title="",
)

tab_spec, tab_user_stories, tab_api = st.tabs(["Feature Spec", "User Stories", "API Design"])


with tab_spec:
    feature_name = st.text_input("Feature name", placeholder="e.g. User notification preferences")
    feature_desc = st.text_area("Describe the feature", height=150,
                                 placeholder="Users should be able to set their notification preferences — choose which events trigger emails, push notifications, or in-app alerts.")
    col1, col2 = st.columns(2)
    with col1:
        project_type = st.selectbox("Project type", ["Web app", "Mobile app", "API/Backend", "CLI tool", "Library/SDK"])
    with col2:
        tech_stack = st.text_input("Tech stack (optional)", placeholder="e.g. React, FastAPI, PostgreSQL")

    if st.button("Generate Spec", type="primary", key="btn_spec") and feature_desc.strip():
        prompt = f"""Write a complete feature specification document.

**Feature:** {feature_name or 'See description'}
**Description:** {feature_desc}
**Project type:** {project_type}
{f'**Tech stack:** {tech_stack}' if tech_stack else ''}

Include these sections:
## 1. Overview
- Problem statement, goals, non-goals

## 2. User Stories
- As a [role], I want [action] so that [benefit]
- Include 5-8 user stories covering main flows and edge cases

## 3. Acceptance Criteria
- Testable criteria for each user story (Given/When/Then format)

## 4. Technical Design
- High-level architecture, data models, API endpoints
- Key technical decisions and trade-offs

## 5. UI/UX Considerations
- Key screens/flows, accessibility requirements

## 6. Edge Cases & Error Handling
- What could go wrong and how to handle it

## 7. Dependencies & Risks
- External dependencies, technical risks, open questions

## 8. Success Metrics
- How to measure if the feature is successful"""

        config = gemma_engine.GemmaConfig(model=model_config.model, temperature=0.4, max_tokens=6000)
        config.system_prompt = "You are a senior product manager writing detailed feature specifications. Be thorough but practical."

        placeholder = st.empty()
        with st.spinner("Generating feature spec..."):
            result = gemma_engine.generate(prompt, config, stream_callback=lambda t: placeholder.markdown(t))
        placeholder.markdown(result)
        set_result("featureforge_spec_result", result)
        set_result("featureforge_spec_title", feature_name or "Feature")

    if st.session_state.featureforge_spec_result:
        st.markdown(st.session_state.featureforge_spec_result)
        if st.button("Export to Obsidian", key="export_spec"):
            path = export_study_guide(
                f"Feature Spec - {st.session_state.featureforge_spec_title}",
                st.session_state.featureforge_spec_result, tags=["featureforge", "spec"],
            )
            st.success(f"Exported to: {path}")

with tab_user_stories:
    epic = st.text_area("Describe the epic or feature area", height=120,
                         placeholder="e.g. E-commerce checkout flow — users need to review cart, enter shipping, select payment, and confirm order")
    num_stories = st.slider("Number of user stories", 5, 20, 10)

    if st.button("Generate User Stories", type="primary", key="btn_stories") and epic.strip():
        prompt = f"""Generate {num_stories} user stories for:

{epic}

For each story:
- **Title** — short descriptive name
- **Story** — As a [role], I want [action], so that [benefit]
- **Acceptance Criteria** — 3-5 testable criteria in Given/When/Then format
- **Priority** — Must-have / Should-have / Nice-to-have
- **Estimate** — Story points (1, 2, 3, 5, 8, 13)

Include happy path, error cases, and edge cases. Order by priority."""

        config = gemma_engine.GemmaConfig(model=model_config.model, temperature=0.4, max_tokens=5000)
        placeholder = st.empty()
        with st.spinner("Writing user stories..."):
            result = gemma_engine.generate(prompt, config, stream_callback=lambda t: placeholder.markdown(t))
        placeholder.markdown(result)
        set_result("featureforge_stories_result", result)

    if st.session_state.featureforge_stories_result:
        st.markdown(st.session_state.featureforge_stories_result)

with tab_api:
    api_desc = st.text_area("Describe the API you need", height=120,
                              placeholder="e.g. REST API for a todo list app — CRUD operations for tasks, lists, and user authentication")
    api_style = st.selectbox("API style", ["REST", "GraphQL", "gRPC"])

    if st.button("Design API", type="primary", key="btn_api") and api_desc.strip():
        prompt = f"""Design a {api_style} API for:

{api_desc}

Include:
1. **Endpoints/Operations** — full list with methods, paths, descriptions
2. **Request/Response Schemas** — JSON examples for each endpoint
3. **Authentication** — how auth works
4. **Error Handling** — standard error response format
5. **Rate Limiting** — suggested limits
6. **Example Requests** — curl or code examples for key operations

Use {api_style} best practices and conventions."""

        config = gemma_engine.GemmaConfig(model=model_config.model, temperature=0.3, max_tokens=5000)
        config.system_prompt = f"You are a senior backend engineer designing {api_style} APIs. Follow industry best practices."

        placeholder = st.empty()
        with st.spinner(f"Designing {api_style} API..."):
            result = gemma_engine.generate(prompt, config, stream_callback=lambda t: placeholder.markdown(t))
        placeholder.markdown(result)
        set_result("featureforge_api_result", result)
        set_result("featureforge_api_title", api_desc[:40])

    if st.session_state.featureforge_api_result:
        st.markdown(st.session_state.featureforge_api_result)
        if st.button("Export to Obsidian", key="export_api"):
            path = export_study_guide(
                f"API Design - {st.session_state.featureforge_api_title}",
                st.session_state.featureforge_api_result,
                tags=["featureforge", "api"],
            )
            st.success(f"Exported to: {path}")
