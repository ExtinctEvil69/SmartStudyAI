"""EduTube — YouTube transcript summarizer and study notes."""

import streamlit as st

from core import gemma_engine, cag_engine
from core.obsidian_export import export_study_guide, export_flashcards
from core.page_state import ensure_state, set_result
from core.youtube_engine import fetch_transcript
from core.sidebar import render_sidebar
from core.ui_components import inject_global_css, page_header
from core.vidya_smriti import log_event

st.set_page_config(page_title="EduTube", page_icon="🎬", layout="wide")
inject_global_css()
model_config = render_sidebar("edutube")

page_header("🎬", "EduTube — YouTube Study Notes Generator", "Load a YouTube transcript automatically or paste your own notes, then turn it into study material.", badge="Video")

ensure_state(
    edutube_transcript="",
    edutube_source_label="",
    edutube_result=None,
    edutube_result_type="",
    edutube_result_subject="",
    edutube_error="",
)

# --- Input ---
input_method = st.radio(
    "Input method",
    ["YouTube URL", "Paste transcript", "Paste video description / notes"],
    horizontal=True,
)

if input_method == "YouTube URL":
    youtube_url = st.text_input("YouTube URL or video ID", placeholder="https://www.youtube.com/watch?v=...")
    if st.button("Fetch Transcript", key="edutube_fetch") and youtube_url.strip():
        try:
            with st.spinner("Fetching transcript..."):
                transcript = fetch_transcript(youtube_url)
            set_result("edutube_transcript", transcript)
            set_result("edutube_source_label", youtube_url)
            set_result("edutube_error", "")
            st.success(f"Loaded transcript with {len(transcript):,} characters")
        except Exception as exc:
            set_result("edutube_error", str(exc))
elif input_method == "Paste transcript":
    transcript = st.text_area(
        "Paste the YouTube transcript here",
        height=250,
        placeholder="Copy the transcript from YouTube (click '...' → 'Show transcript' on any video)",
    )
    if transcript:
        set_result("edutube_transcript", transcript)
        set_result("edutube_source_label", "Manual transcript")
        set_result("edutube_error", "")
else:
    notes = st.text_area(
        "Paste video description or your notes",
        height=250,
        placeholder="Paste the video description, chapter markers, or your own notes about the video",
    )
    if notes:
        set_result("edutube_transcript", notes)
        set_result("edutube_source_label", "Manual notes")
        set_result("edutube_error", "")

if st.session_state.edutube_error:
    st.error(st.session_state.edutube_error)

if st.session_state.edutube_transcript:
    st.info(f"Loaded {len(st.session_state.edutube_transcript):,} characters")
    if st.session_state.edutube_source_label:
        st.caption(f"Source: {st.session_state.edutube_source_label}")

# --- Config ---
col1, col2 = st.columns(2)
with col1:
    output_type = st.selectbox("Generate", ["Study Notes", "Summary", "Flashcards", "Key Concepts", "Quiz Prep Notes"])
with col2:
    subject = st.text_input("Subject (optional)", placeholder="e.g. Machine Learning")

# --- Generate ---
if st.button("Generate", type="primary") and st.session_state.edutube_transcript:
    config = gemma_engine.GemmaConfig(model=model_config.model, temperature=0.4)
    context = st.session_state.edutube_transcript

    if output_type == "Flashcards":
        with st.spinner("Generating flashcards..."):
            result = cag_engine.generate_flashcards(context, num_cards=15, config=config)
        set_result("edutube_result", result)
        set_result("edutube_result_type", output_type)
        set_result("edutube_result_subject", subject)
        # ── Vidya Smriti: log flashcard generation ──
        log_event("EduTube", "flashcards_created", subject or "Video content",
                  num_cards=len(result.get("cards", [])), source=st.session_state.edutube_source_label)
    else:
        instructions = {
            "Study Notes": """Create comprehensive study notes from this video transcript. Include:
## Key Topics
- List main topics covered with timestamps if available

## Detailed Notes
- Organized by topic with bullet points
- Bold key terms and concepts
- Include examples mentioned

## Key Takeaways
- 5-7 main takeaways from the video

## Questions to Review
- 3-5 self-test questions based on the content""",

            "Summary": """Write a concise summary of this video transcript:
1. One-paragraph overview
2. Main points (bullet list)
3. Key conclusions
4. Who this is most useful for""",

            "Key Concepts": """Extract and explain all key concepts from this transcript:
For each concept:
- **Concept name** in bold
- Brief definition (1-2 sentences)
- How it relates to other concepts mentioned
- Example from the video if available

Organize from foundational to advanced concepts.""",

            "Quiz Prep Notes": """Create quiz preparation notes from this transcript:
## Must-Know Facts
- Key facts, dates, formulas, definitions

## Common Exam Questions
- Likely exam questions with brief model answers

## Concept Connections
- How different topics connect to each other

## Potential Trick Questions
- Areas where misunderstanding is common""",
        }

        instruction = instructions.get(output_type, instructions["Study Notes"])
        if subject:
            instruction = f"Subject: {subject}\n\n{instruction}"

        placeholder = st.empty()
        with st.spinner(f"Generating {output_type.lower()}..."):
            result = cag_engine.generate_from_context(
                context, instruction,
                system_prompt="You are an expert educator creating study materials from video content.",
                config=config,
                stream_callback=lambda t: placeholder.markdown(t),
            )
        placeholder.markdown(result)
        set_result("edutube_result", result)
        set_result("edutube_result_type", output_type)
        set_result("edutube_result_subject", subject)
        # ── Vidya Smriti: log notes generation ──
        log_event("EduTube", "notes_generated", subject or "Video content",
                  output_type=output_type, source=st.session_state.edutube_source_label)

edutube_result = st.session_state.edutube_result
if edutube_result:
    st.divider()
    if st.session_state.edutube_result_type == "Flashcards" and isinstance(edutube_result, dict) and "cards" in edutube_result:
        st.success(f"Generated {len(edutube_result['cards'])} flashcards!")
        for i, card in enumerate(edutube_result["cards"], 1):
            with st.expander(f"Card {i}: {card['front'][:60]}"):
                st.markdown(f"**Q:** {card['front']}")
                st.markdown(f"**A:** {card['back']}")
                if card.get("tags"):
                    st.caption(f"Tags: {', '.join(card['tags'])}")
        if st.button("Export Flashcards to Obsidian"):
            title = f"EduTube Flashcards - {st.session_state.edutube_result_subject or 'Video Notes'}"
            path = export_flashcards(title, edutube_result["cards"], tags=["edutube", "flashcards"])
            st.success(f"Exported to: {path}")
    elif isinstance(edutube_result, str):
        st.markdown(edutube_result)
        if st.button("Export to Obsidian"):
            path = export_study_guide(
                f"EduTube - {st.session_state.edutube_result_subject or st.session_state.edutube_result_type}",
                edutube_result,
                tags=["edutube", st.session_state.edutube_result_type.lower().replace(" ", "-")],
            )
            st.success(f"Exported to: {path}")
        st.download_button(
            "Download Markdown",
            data=edutube_result,
            file_name="edutube_notes.md",
            mime="text/markdown",
        )
