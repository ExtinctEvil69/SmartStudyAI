"""DSA Sage — Data Structures & Algorithms Tutor (Gemma 4 + CAG)."""

import streamlit as st

from core import gemma_engine, cag_engine
from core.obsidian_export import export_study_guide
from core.page_state import ensure_state, set_result
from core.sidebar import render_sidebar
from core.ui_components import inject_global_css, page_header

st.set_page_config(page_title="DSA Sage", page_icon="🌳", layout="wide")
inject_global_css()
model_config = render_sidebar("dsasage")

page_header("🌳", "DSA Sage — Algorithm & Data Structure Tutor", "Solve problems, visualize algorithms, and learn DSA concepts step-by-step with Gemma 4.", badge="DSA")

ensure_state(
    dsasage_solve_result="",
    dsasage_solve_title="",
    dsasage_learn_result="",
    dsasage_learn_title="",
    dsasage_compare_result="",
    dsasage_practice_result="",
    dsasage_practice_title="",
)

tab_solve, tab_learn, tab_compare, tab_practice = st.tabs(
    ["Solve Problem", "Learn Concept", "Compare Approaches", "Practice Problems"]
)


with tab_solve:
    problem = st.text_area("Describe the problem", height=150,
                            placeholder="e.g. Given an array of integers, find two numbers that add up to a target sum.")
    col1, col2 = st.columns(2)
    with col1:
        lang = st.selectbox("Language", ["Python", "Java", "C++", "JavaScript", "Go"], key="solve_lang")
    with col2:
        approach = st.selectbox("Approach", ["Optimal solution", "Brute force first, then optimize", "Multiple approaches"])

    if st.button("Solve", type="primary", key="btn_solve") and problem.strip():
        prompt = f"""Solve the following DSA problem.

**Problem:** {problem}
**Language:** {lang}
**Approach:** {approach}

Provide:
1. **Understanding** — Restate the problem, identify input/output, and edge cases
2. **Approach** — Explain the algorithm strategy before writing code
3. **Solution** — Clean, well-commented {lang} code
4. **Dry Run** — Walk through an example step-by-step
5. **Complexity Analysis** — Time and space complexity with justification
6. **Follow-up** — How would the solution change if constraints changed?"""

        config = gemma_engine.GemmaConfig(model=model_config.model, temperature=0.3, max_tokens=5000)
        config.system_prompt = "You are a DSA expert and competitive programming coach. Explain solutions clearly with intuition first, then code."

        placeholder = st.empty()
        with st.spinner("Solving..."):
            result = gemma_engine.generate(prompt, config, stream_callback=lambda t: placeholder.markdown(t))
        placeholder.markdown(result)
        set_result("dsasage_solve_result", result)
        set_result("dsasage_solve_title", problem)

    if st.session_state.dsasage_solve_result:
        st.markdown(st.session_state.dsasage_solve_result)
        if st.button("Export to Obsidian", key="export_solve"):
            path = export_study_guide(
                f"DSA - {st.session_state.dsasage_solve_title[:50]}",
                st.session_state.dsasage_solve_result,
                tags=["dsa-sage", "algorithms"],
            )
            st.success(f"Exported to: {path}")

with tab_learn:
    concept = st.selectbox("Data Structure / Algorithm", [
        "Arrays & Hashing", "Two Pointers", "Sliding Window", "Stack & Queue",
        "Linked List", "Binary Tree", "BST", "Heap / Priority Queue",
        "Graph — BFS/DFS", "Graph — Dijkstra/Bellman-Ford", "Dynamic Programming",
        "Backtracking", "Trie", "Union Find", "Segment Tree",
        "Sorting Algorithms", "Binary Search", "Greedy Algorithms",
    ])
    depth = st.selectbox("Depth", ["Beginner intro", "Intermediate with patterns", "Advanced with proofs"])

    if st.button("Learn", type="primary", key="btn_learn"):
        prompt = f"""Teach me about **{concept}** at a {depth.lower()} level.

Include:
1. **What it is** — intuitive explanation with real-world analogy
2. **When to use it** — problem patterns that signal this approach
3. **How it works** — step-by-step with visual representation (use ASCII diagrams)
4. **Template code** — reusable Python template
5. **Common variations** — important variants and their use cases
6. **Classic problems** — 5 LeetCode-style problems that use this concept
7. **Common mistakes** — pitfalls to avoid"""

        config = gemma_engine.GemmaConfig(model=model_config.model, temperature=0.4, max_tokens=5000)
        config.system_prompt = "You are a world-class DSA educator. Use intuitive explanations, ASCII visualizations, and practical patterns."

        placeholder = st.empty()
        with st.spinner(f"Preparing lesson on {concept}..."):
            result = gemma_engine.generate(prompt, config, stream_callback=lambda t: placeholder.markdown(t))
        placeholder.markdown(result)
        set_result("dsasage_learn_result", result)
        set_result("dsasage_learn_title", concept)

    if st.session_state.dsasage_learn_result:
        st.markdown(st.session_state.dsasage_learn_result)
        if st.button("Export to Obsidian", key="export_learn"):
            path = export_study_guide(
                f"DSA - {st.session_state.dsasage_learn_title}",
                st.session_state.dsasage_learn_result,
                tags=["dsa-sage", "learning"],
            )
            st.success(f"Exported to: {path}")

with tab_compare:
    st.markdown("Compare different algorithmic approaches to the same problem.")
    compare_problem = st.text_area("Problem to compare approaches for", height=100,
                                    placeholder="e.g. Find the kth largest element in an array")

    if st.button("Compare Approaches", type="primary", key="btn_compare") and compare_problem.strip():
        prompt = f"""Compare different algorithmic approaches for:

**Problem:** {compare_problem}

For each viable approach, provide:
| Approach | Time | Space | Pros | Cons |
|----------|------|-------|------|------|

Then for each approach:
1. Brief explanation of the strategy
2. Python implementation
3. When this approach is preferred

End with a **recommendation** for which approach to use in an interview vs. production."""

        config = gemma_engine.GemmaConfig(model=model_config.model, temperature=0.3, max_tokens=5000)
        placeholder = st.empty()
        with st.spinner("Comparing approaches..."):
            result = gemma_engine.generate(prompt, config, stream_callback=lambda t: placeholder.markdown(t))
        placeholder.markdown(result)
        set_result("dsasage_compare_result", result)

    if st.session_state.dsasage_compare_result:
        st.markdown(st.session_state.dsasage_compare_result)

with tab_practice:
    st.markdown("Generate practice problems for a specific topic.")
    practice_topic = st.selectbox("Topic", [
        "Arrays", "Strings", "Linked Lists", "Trees", "Graphs",
        "Dynamic Programming", "Sorting & Searching", "Stack & Queue",
        "Greedy", "Backtracking", "Bit Manipulation",
    ], key="practice_topic")
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard", "Progressive (easy → hard)"])
    num_problems = st.slider("Number of problems", 3, 10, 5)

    if st.button("Generate Problems", type="primary", key="btn_practice"):
        prompt = f"""Generate {num_problems} {difficulty.lower()} practice problems about {practice_topic}.

For each problem:
1. **Problem statement** — clear, LeetCode-style description
2. **Examples** — 2-3 input/output examples
3. **Constraints** — input size and value constraints
4. **Hint** (hidden) — one-sentence hint
5. **Approach tag** — the key technique needed (e.g., "two pointers", "memoization")

Make problems progressively build on each other when possible."""

        config = gemma_engine.GemmaConfig(model=model_config.model, temperature=0.6, max_tokens=5000)
        placeholder = st.empty()
        with st.spinner("Generating practice problems..."):
            result = gemma_engine.generate(prompt, config, stream_callback=lambda t: placeholder.markdown(t))
        placeholder.markdown(result)
        set_result("dsasage_practice_result", result)
        set_result("dsasage_practice_title", practice_topic)

    if st.session_state.dsasage_practice_result:
        st.markdown(st.session_state.dsasage_practice_result)
        if st.button("Export to Obsidian", key="export_practice"):
            path = export_study_guide(
                f"DSA Practice - {st.session_state.dsasage_practice_title}",
                st.session_state.dsasage_practice_result,
                tags=["dsa-sage", "practice"],
            )
            st.success(f"Exported to: {path}")
