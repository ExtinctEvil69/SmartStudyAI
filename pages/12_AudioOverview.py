"""AudioOverview — Audio/Podcast Study Notes Generator (Gemma 4 + CAG)."""

import streamlit as st

from core.audio_engine import synthesize_speech
from core import gemma_engine, cag_engine
from core.obsidian_export import export_study_guide, export_flashcards
from core.page_state import ensure_state, set_result
from core.sidebar import render_sidebar
from core.ui_components import inject_global_css, page_header

st.set_page_config(page_title="AudioOverview", page_icon="🎙️", layout="wide")
inject_global_css()
model_config = render_sidebar("audiooverview")

page_header("🎙️", "AudioOverview — Audio & Podcast Study Notes", "Paste podcast transcripts or lecture notes — get structured summaries, key points, and flashcards.", badge="Audio")

ensure_state(
    audio_transcript="",
    audio_result=None,
    audio_result_type="",
    audio_result_topic="",
    audio_file_path="",
    audio_error="",
)

# --- Input ---
st.subheader("Input")
input_method = st.radio("Source", ["Paste transcript", "Paste show notes / summary", "Upload text file"], horizontal=True)

if input_method == "Paste transcript":
    transcript = st.text_area(
        "Paste the audio transcript",
        height=250,
        placeholder="Paste transcript from Otter.ai, YouTube, podcast transcript services, etc.",
    )
    if transcript:
        set_result("audio_transcript", transcript)
        set_result("audio_error", "")
elif input_method == "Paste show notes / summary":
    notes = st.text_area("Paste show notes or summary", height=250)
    if notes:
        set_result("audio_transcript", notes)
        set_result("audio_error", "")
else:
    uploaded = st.file_uploader("Upload transcript file", type=["txt", "srt", "vtt"])
    if uploaded:
        content = uploaded.read().decode("utf-8", errors="replace")
        set_result("audio_transcript", content)
        set_result("audio_error", "")
        st.success(f"Loaded {len(content):,} characters from {uploaded.name}")

if st.session_state.audio_error:
    st.error(st.session_state.audio_error)

if st.session_state.audio_transcript:
    st.info(f"Transcript loaded: {len(st.session_state.audio_transcript):,} characters")

# --- Output config ---
col1, col2 = st.columns(2)
with col1:
    output_type = st.selectbox("Generate", [
        "Episode Summary", "Study Notes", "Key Takeaways",
        "Flashcards", "Discussion Questions", "Action Items", "Podcast Script",
    ])
with col2:
    podcast_topic = st.text_input("Topic/Subject (optional)", placeholder="e.g. Neuroscience, Business Strategy")

if st.button("Generate", type="primary") and st.session_state.audio_transcript:
    config = gemma_engine.GemmaConfig(model=model_config.model, temperature=0.4)
    context = st.session_state.audio_transcript

    if output_type == "Flashcards":
        with st.spinner("Generating flashcards from audio content..."):
            result = cag_engine.generate_flashcards(context, num_cards=15, config=config)
        set_result("audio_result", result)
        set_result("audio_result_type", output_type)
        set_result("audio_result_topic", podcast_topic)
        set_result("audio_file_path", "")
    else:
        instructions = {
            "Episode Summary": """Summarize this audio transcript:
1. **One-line summary** — single sentence capturing the main point
2. **Overview** — 2-3 paragraph summary
3. **Key Points** — bulleted list of main discussion points
4. **Notable Quotes** — any memorable or important quotes
5. **Speakers** — identify different speakers if apparent""",

            "Study Notes": """Create structured study notes from this audio transcript:
## Main Topics
- Topic-by-topic breakdown with key details

## Key Concepts
- Important terms and ideas with definitions

## Arguments & Evidence
- Main arguments made and evidence cited

## Connections
- Links between topics discussed

## Review Questions
- Self-test questions to check understanding""",

            "Key Takeaways": """Extract the key takeaways from this audio content:
- List 7-10 main takeaways, ordered by importance
- For each: one bold statement + 1-2 sentences of context
- End with "Bottom Line" — the single most important message""",

            "Discussion Questions": """Generate thoughtful discussion questions based on this audio content:
- 5-7 open-ended questions that promote critical thinking
- For each: the question, why it matters, and a brief discussion starter
- Include questions at different Bloom's taxonomy levels""",

            "Action Items": """Extract actionable items from this audio content:
- List specific recommendations, tips, or advice mentioned
- Organize by category (if applicable)
- For each: what to do, why, and how to start
- Prioritize by impact (high/medium/low)""",

            "Podcast Script": """Turn this source material into a short podcast-style explainer script:
- Write for spoken delivery, not for reading.
- Include an engaging opening, 3-5 clear segments, and a concise closing recap.
- Keep it under 900 words.
- Use natural transitions and short sentences.""",
        }

        instruction = instructions.get(output_type, instructions["Study Notes"])
        if podcast_topic:
            instruction = f"Topic: {podcast_topic}\n\n{instruction}"

        placeholder = st.empty()
        with st.spinner(f"Generating {output_type.lower()}..."):
            result = cag_engine.generate_from_context(
                context, instruction,
                system_prompt="You are an expert content analyst specializing in audio/podcast content.",
                config=config,
                stream_callback=lambda t: placeholder.markdown(t),
            )
        placeholder.markdown(result)
        set_result("audio_result", result)
        set_result("audio_result_type", output_type)
        set_result("audio_result_topic", podcast_topic)
        set_result("audio_file_path", "")

audio_result = st.session_state.audio_result
if audio_result:
    st.divider()
    if st.session_state.audio_result_type == "Flashcards" and isinstance(audio_result, dict) and "cards" in audio_result:
        st.success(f"Generated {len(audio_result['cards'])} flashcards!")
        for i, card in enumerate(audio_result["cards"], 1):
            with st.expander(f"Card {i}: {card['front'][:60]}"):
                st.markdown(f"**Q:** {card['front']}")
                st.markdown(f"**A:** {card['back']}")
        if st.button("Export Flashcards to Obsidian"):
            path = export_flashcards(
                f"AudioOverview - {st.session_state.audio_result_topic or 'Podcast'}",
                audio_result["cards"],
                tags=["audio-overview", "flashcards"],
            )
            st.success(f"Exported to: {path}")
    elif isinstance(audio_result, str):
        st.markdown(audio_result)
        if st.button("Export to Obsidian"):
            path = export_study_guide(
                f"AudioOverview - {st.session_state.audio_result_topic or st.session_state.audio_result_type}",
                audio_result,
                tags=["audio-overview", st.session_state.audio_result_type.lower().replace(" ", "-")],
            )
            st.success(f"Exported to: {path}")
        if st.button("Generate Audio Narration"):
            try:
                with st.spinner("Synthesizing audio..."):
                    audio_path = synthesize_speech(audio_result, st.session_state.audio_result_topic or st.session_state.audio_result_type)
                set_result("audio_file_path", str(audio_path))
                set_result("audio_error", "")
            except Exception as exc:
                set_result("audio_error", str(exc))
        if st.session_state.audio_file_path:
            st.audio(st.session_state.audio_file_path)
            with open(st.session_state.audio_file_path, "rb") as audio_file:
                st.download_button(
                    "Download MP3",
                    data=audio_file.read(),
                    file_name="audio_overview.mp3",
                    mime="audio/mpeg",
                )
