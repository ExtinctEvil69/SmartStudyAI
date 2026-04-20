"""IdeaSpark — AI Brainstorming & Idea Generator (Gemma 4)."""

import streamlit as st

from core import gemma_engine
from core.obsidian_export import export_study_guide
from core.page_state import ensure_state, set_result
from core.sidebar import render_sidebar
from core.ui_components import inject_global_css, page_header

st.set_page_config(page_title="IdeaSpark", page_icon="💡", layout="wide")
inject_global_css()
model_config = render_sidebar("ideaspark")

page_header("💡", "IdeaSpark — AI Brainstorming Assistant", "Generate ideas for projects, research, essays, startups, and more — powered by Gemma 4.", badge="Ideas")

ensure_state(ideaspark_result="", ideaspark_topic="", ideaspark_type="", expand_ideas="", ideaspark_expand_result="")

# --- Input ---
col1, col2 = st.columns([2, 1])

with col1:
    topic = st.text_input("What do you need ideas for?",
                           placeholder="e.g. Machine learning project ideas for a healthcare dataset")
    constraints = st.text_area("Constraints or requirements (optional)", height=80,
                                placeholder="e.g. Must use Python, suitable for a 2-week timeline, beginner-friendly")

with col2:
    idea_type = st.selectbox("Idea type", [
        "Research project", "Software project", "Essay/paper topic",
        "Startup / business", "Creative project", "Experiment design",
        "Presentation topic", "Hackathon project", "Study approach",
    ])
    num_ideas = st.slider("Number of ideas", 3, 15, 7)
    creativity = st.select_slider("Creativity level", ["Conservative", "Balanced", "Creative", "Wild"])

creativity_temp = {"Conservative": 0.3, "Balanced": 0.6, "Creative": 0.8, "Wild": 1.0}

if st.button("Generate Ideas", type="primary") and topic.strip():
    prompt = f"""Generate {num_ideas} {idea_type.lower()} ideas about: {topic}

{f'**Constraints:** {constraints}' if constraints else ''}
**Creativity level:** {creativity}

For each idea provide:
1. **Title** — catchy, descriptive name
2. **Description** — 2-3 sentences explaining the idea
3. **Why it's interesting** — what makes this worth pursuing
4. **Feasibility** — difficulty level (Easy/Medium/Hard) and key challenges
5. **First steps** — 3 concrete actions to get started
6. **Potential impact** — who benefits and how

{'Push boundaries — include at least 2 unconventional or surprising ideas.' if creativity in ('Creative', 'Wild') else ''}
Order from most practical to most ambitious."""

    config = gemma_engine.GemmaConfig(
        model=model_config.model,
        temperature=creativity_temp[creativity],
        max_tokens=num_ideas * 500,
    )
    config.system_prompt = "You are a creative innovation consultant. Generate diverse, actionable ideas that range from practical to visionary."

    placeholder = st.empty()
    with st.spinner("Brainstorming..."):
        result = gemma_engine.generate(prompt, config, stream_callback=lambda t: placeholder.markdown(t))
    placeholder.markdown(result)
    set_result("ideaspark_result", result)
    set_result("ideaspark_topic", topic)
    set_result("ideaspark_type", idea_type)

if st.session_state.ideaspark_result:
    col_e1, col_e2 = st.columns(2)
    if col_e1.button("Export to Obsidian"):
        path = export_study_guide(
            f"IdeaSpark - {st.session_state.ideaspark_topic[:50]}",
            f"## Topic\n{st.session_state.ideaspark_topic}\n\n{st.session_state.ideaspark_result}",
            tags=["ideaspark", st.session_state.ideaspark_type.lower().replace(" ", "-")],
        )
        st.success(f"Exported to: {path}")

    if col_e2.button("Expand Best Idea"):
        st.session_state["expand_ideas"] = st.session_state.ideaspark_result

# --- Expand an idea ---
if st.session_state.get("expand_ideas"):
    st.divider()
    st.subheader("Expand an Idea")
    idea_to_expand = st.text_input("Which idea number or name to expand?", placeholder="e.g. Idea 3 or the project name")

    if st.button("Expand", type="primary", key="btn_expand") and idea_to_expand:
        prompt = f"""Based on these brainstormed ideas:

{st.session_state['expand_ideas']}

Expand on: {idea_to_expand}

Provide a detailed plan:
1. **Full Description** — detailed explanation of the idea
2. **Implementation Plan** — step-by-step roadmap with milestones
3. **Resources Needed** — tools, data, skills, team
4. **Timeline** — realistic week-by-week plan
5. **Success Metrics** — how to measure if it's working
6. **Risks & Mitigations** — potential problems and solutions
7. **Similar Projects** — existing work to learn from"""

        config = gemma_engine.GemmaConfig(model=model_config.model, temperature=0.5, max_tokens=4000)
        placeholder2 = st.empty()
        with st.spinner("Expanding idea..."):
            result = gemma_engine.generate(prompt, config, stream_callback=lambda t: placeholder2.markdown(t))
        placeholder2.markdown(result)
        set_result("ideaspark_expand_result", result)

if st.session_state.ideaspark_expand_result:
    st.markdown(st.session_state.ideaspark_expand_result)
