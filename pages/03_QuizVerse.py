"""QuizVerse — Interactive AI Quiz Generator (fine-tuned Gemma 4 + CAG)."""

import streamlit as st

from core import cag_engine, gemma_engine
from core.page_state import ensure_state
from core.utils import extract_pdf_text, truncate_text
from core.obsidian_export import export_quiz_results
from core.sidebar import render_sidebar
from core.ui_components import inject_global_css, page_header
from core.vidya_smriti import log_event, update_mastery

st.set_page_config(page_title="QuizVerse", page_icon="🧠", layout="wide")
inject_global_css()
model_config = render_sidebar("quizverse")

page_header("🧠", "QuizVerse — Interactive Quiz Generator", "Generate adaptive quizzes from your documents using fine-tuned Gemma 4 + CAG.", badge="Quiz")

ensure_state(
    quiz_data=None,
    quiz_answers={},
    quiz_submitted=False,
    quiz_context="",
    quiz_subject="",
)

# --- Input ---
col_input, col_config = st.columns([2, 1])

with col_input:
    input_method = st.radio("Content source", ["Paste text", "Upload PDF"], horizontal=True)

    if input_method == "Paste text":
        context = st.text_area("Paste your study material", height=200)
        if context:
            st.session_state.quiz_context = context
    else:
        uploaded = st.file_uploader("Upload PDF", type=["pdf"])
        if uploaded:
            with st.spinner("Extracting text..."):
                st.session_state.quiz_context = extract_pdf_text(uploaded.read())
            st.success(f"Extracted {len(st.session_state.quiz_context):,} characters")

with col_config:
    st.subheader("Quiz Settings")
    subject = st.text_input("Subject", placeholder="e.g. Biology")
    topic = st.text_input("Topic", placeholder="e.g. Cell Division")
    num_questions = st.slider("Number of questions", 3, 20, 5)
    difficulty = st.selectbox("Difficulty", ["mixed", "easy", "medium", "hard"])
    question_types = st.selectbox("Question types", ["mcq", "true_false", "fill_blank", "mixed"])
    grade_level = st.text_input("Grade level (optional)", placeholder="e.g. Grade 10, Undergraduate")


# --- Generate quiz ---
if st.button("Generate Quiz", type="primary") and st.session_state.quiz_context:
    st.session_state.quiz_submitted = False
    st.session_state.quiz_answers = {}

    config = gemma_engine.GemmaConfig(model=model_config.model)
    context_text = truncate_text(st.session_state.quiz_context, 25000)

    with st.spinner(f"Generating {num_questions} questions with Gemma 4..."):
        quiz = cag_engine.generate_quiz(
            context=context_text,
            subject=subject,
            topic=topic,
            num_questions=num_questions,
            difficulty=difficulty,
            question_types=question_types,
            grade_level=grade_level,
            config=config,
        )

    if quiz and "questions" in quiz:
        st.session_state.quiz_data = quiz
        st.session_state.quiz_subject = subject
        st.success(f"Generated {len(quiz['questions'])} questions!")
    else:
        st.error("Failed to generate valid quiz JSON. Try again or use a different model.")

# --- Display quiz ---
if st.session_state.quiz_data and not st.session_state.quiz_submitted:
    quiz = st.session_state.quiz_data
    st.markdown(f"## {quiz.get('quiz_title', 'Quiz')}")
    st.divider()

    for i, q in enumerate(quiz["questions"]):
        st.markdown(f"### Q{i+1}. {q['question']}")

        if q.get("difficulty"):
            st.caption(f"Difficulty: {q['difficulty']} | Bloom's: {q.get('bloom_level', 'N/A')}")

        q_type = q.get("type", "mcq")
        options = q.get("options", [])

        if q_type == "mcq" and options:
            st.session_state.quiz_answers[i] = st.radio(
                f"Select answer for Q{i+1}",
                options,
                key=f"q_{i}",
                label_visibility="collapsed",
            )
        elif q_type == "true_false":
            st.session_state.quiz_answers[i] = st.radio(
                f"Q{i+1}", ["True", "False"], key=f"q_{i}", label_visibility="collapsed"
            )
        else:
            st.session_state.quiz_answers[i] = st.text_input(
                f"Your answer for Q{i+1}", key=f"q_{i}", label_visibility="collapsed"
            )
        st.divider()

    if st.button("Submit Quiz", type="primary"):
        st.session_state.quiz_submitted = True
        st.rerun()

# --- Show results ---
if st.session_state.quiz_submitted and st.session_state.quiz_data:
    quiz = st.session_state.quiz_data
    questions = quiz["questions"]
    score = 0
    results = []

    st.markdown("## Results")
    for i, q in enumerate(questions):
        user_ans = st.session_state.quiz_answers.get(i, "")
        correct = q.get("correct_answer", "")
        is_correct = str(user_ans).strip().lower() == str(correct).strip().lower()
        if is_correct:
            score += 1

        emoji = "✅" if is_correct else "❌"
        st.markdown(f"### {emoji} Q{i+1}. {q['question']}")
        st.markdown(f"**Your answer:** {user_ans}")
        st.markdown(f"**Correct answer:** {correct}")
        if q.get("explanation"):
            st.info(q["explanation"])

        results.append({**q, "user_answer": user_ans, "is_correct": is_correct})
        st.divider()

    pct = round(score / len(questions) * 100) if questions else 0
    st.metric("Score", f"{score}/{len(questions)} ({pct}%)")

    # ── Vidya Smriti: log quiz completion + update mastery ──
    quiz_topic = topic or subject or "General"
    log_event("QuizVerse", "quiz_completed", quiz_topic,
              score=pct, num_questions=len(questions), difficulty=difficulty)
    if quiz_topic:
        update_mastery(quiz_topic, pct, "QuizVerse")

    # Export
    col_export1, col_export2 = st.columns(2)
    if col_export1.button("Export to Obsidian"):
        path = export_quiz_results(
            quiz.get("quiz_title", "Quiz"),
            results,
            score=score,
            total=len(questions),
            tags=["quizverse", st.session_state.quiz_subject.lower()] if st.session_state.quiz_subject else ["quizverse"],
        )
        st.success(f"Exported to: {path}")

    if col_export2.button("Generate New Quiz"):
        st.session_state.quiz_data = None
        st.session_state.quiz_submitted = False
        st.session_state.quiz_answers = {}
        st.rerun()
