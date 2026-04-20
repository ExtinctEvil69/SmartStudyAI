"""NeuroRead — AI Document Assistant (RAG + LightRAG)."""

import json

import streamlit as st

from core import gemma_engine, lightrag_engine, rag_engine, vision_engine
from core.obsidian_export import export_study_guide
from core.page_state import ensure_state, set_result
from core.session_context import get_session_workspace
from core.utils import extract_pdf_text
from core.sidebar import render_sidebar
from core.ui_components import inject_global_css, page_header
from core.vidya_smriti import log_event

st.set_page_config(page_title="NeuroRead", page_icon="📖", layout="wide")
inject_global_css()
model_config = render_sidebar("neuroread")

page_header("📖", "NeuroRead — AI Document Assistant", "Upload PDFs, ask questions, get citation-grounded answers via LightRAG knowledge graph.", badge="RAG")

ensure_state(
    neuroread_docs=[],
    neuroread_answer="",
    neuroread_question="",
    neuroread_references=[],
    neuroread_chat_history=[],
    neuroread_local_index=None,
    neuroread_vision_result="",
    neuroread_vision_structured=None,
)
workspace = get_session_workspace("neuroread_workspace", "neuroread")
rag_available = lightrag_engine.is_available(workspace=workspace)

if not rag_available:
    st.warning(
        "LightRAG is unavailable. NeuroRead will use the local `rag_engine.py` fallback instead of the graph-backed server."
    )

tab_upload, tab_chat, tab_vision = st.tabs(["📄 Upload Documents", "💬 Ask Questions", "👁️ Vision Analysis"])

with tab_upload:
    st.caption(f"Session workspace: `{workspace}`")
    uploaded_files = st.file_uploader("Upload documents", type=["pdf", "txt"], accept_multiple_files=True)

    if uploaded_files and st.button("Index Documents", type="primary"):
        local_sources: list[str] = []
        for f in uploaded_files:
            with st.spinner(f"Indexing {f.name}..."):
                try:
                    file_bytes = f.read()
                    if f.name.endswith(".pdf"):
                        local_sources.append(extract_pdf_text(file_bytes))
                        content_type = "application/pdf"
                    else:
                        local_sources.append(file_bytes.decode("utf-8", errors="replace"))
                        content_type = "text/plain"

                    if rag_available:
                        result = lightrag_engine.insert_file_bytes(f.name, file_bytes, content_type, workspace=workspace)
                        st.success(f"Indexed: {f.name} — {result.get('message', 'processing')}")
                    else:
                        st.success(f"Prepared local index input: {f.name}")
                    if f.name not in st.session_state.neuroread_docs:
                        st.session_state.neuroread_docs.append(f.name)
                except Exception as e:
                    st.error(f"Failed to index {f.name}: {e}")

        if local_sources:
            combined_text = "\n\n".join(local_sources)
            st.session_state.neuroread_local_index = rag_engine.build_index_from_text(combined_text, source="uploaded_documents")

        if rag_available:
            with st.spinner("Building knowledge graph (this may take a few minutes with Gemma 4)..."):
                lightrag_engine.wait_for_pipeline(timeout=600, workspace=workspace)
            st.success("All documents indexed and knowledge graph built.")
        elif st.session_state.neuroread_local_index is not None:
            st.success("Local RAG index built successfully.")

        # ── Vidya Smriti: log document ingestion ──
        for f in uploaded_files:
            log_event("NeuroRead", "content_ingested", f.name, source="document_upload")

    clear_col, refresh_col = st.columns(2)
    if clear_col.button("Clear Session Index"):
        try:
            if rag_available:
                docs = lightrag_engine.get_documents(workspace=workspace)
                for doc in docs:
                    doc_id = doc.get("id") or doc.get("doc_id")
                    if doc_id:
                        lightrag_engine.delete_document(doc_id, workspace=workspace)
            st.session_state.neuroread_docs = []
            st.session_state.neuroread_answer = ""
            st.session_state.neuroread_question = ""
            st.session_state.neuroread_references = []
            st.session_state.neuroread_chat_history = []
            st.session_state.neuroread_local_index = None
            st.success("Cleared the current session workspace.")
        except Exception as e:
            st.error(f"Failed to clear session workspace: {e}")
    if refresh_col.button("Refresh Workspace Docs"):
        try:
            if rag_available:
                docs = lightrag_engine.get_documents(workspace=workspace)
                st.session_state.neuroread_docs = [doc.get("file_path") or doc.get("file_source") or doc.get("id", "unknown") for doc in docs]
                st.success("Workspace document list refreshed.")
            else:
                st.info("Local fallback mode does not have a remote workspace to refresh.")
        except Exception as e:
            st.error(f"Failed to refresh documents: {e}")

    if st.session_state.neuroread_docs:
        st.markdown("**Indexed documents:**")
        for doc in st.session_state.neuroread_docs:
            st.markdown(f"- {doc}")

with tab_vision:
    st.subheader("Visual Document Analysis")
    st.caption("Analyze photographed notes, textbook pages, charts, or PDFs with the multimodal document path.")

    available_models = gemma_engine.list_models() or ["gemma4:e2b"]
    vision_model = st.selectbox("Vision model", available_models, index=0)
    uploaded_visual = st.file_uploader("Upload image or PDF", type=["png", "jpg", "jpeg", "webp", "pdf"], key="neuroread_visual_upload")
    instruction = st.text_area(
        "Vision prompt",
        height=100,
        value="Summarize the educational content on this page, identify important concepts, and note any formulas, diagrams, or charts.",
    )
    structured_fields = st.text_input(
        "Structured fields (comma-separated)",
        value="title, main_topic, key_concepts, formulas, chart_or_diagram_summary",
    )
    max_pages = st.slider("PDF pages to inspect", 1, 5, 2, key="neuroread_vision_pages")

    if uploaded_visual is not None:
        file_bytes = uploaded_visual.read()
        if uploaded_visual.type.startswith("image/"):
            st.image(file_bytes, caption=uploaded_visual.name, use_container_width=True)

        analyze_col, extract_col, add_col = st.columns(3)
        if analyze_col.button("Run Visual Summary", type="primary"):
            try:
                config = vision_engine.VisionConfig(model=vision_model, temperature=0.2, max_tokens=2500)
                with st.spinner("Analyzing visual content..."):
                    if uploaded_visual.name.lower().endswith(".pdf"):
                        result = vision_engine.analyze_pdf_pages(file_bytes, instruction, config=config, max_pages=max_pages)
                    else:
                        result = vision_engine.analyze_image_bytes(instruction, file_bytes, config=config)
                set_result("neuroread_vision_result", result)
                st.markdown(result)
            except Exception as exc:
                st.error(f"Vision analysis failed: {exc}")

        if extract_col.button("Run Structured Extraction"):
            try:
                config = vision_engine.VisionConfig(model=vision_model, temperature=0.1, max_tokens=1200)
                fields = [field.strip() for field in structured_fields.split(",") if field.strip()]
                with st.spinner("Extracting structured fields..."):
                    if uploaded_visual.name.lower().endswith(".pdf"):
                        structured = vision_engine.extract_structured_document_info(file_bytes, fields, config=config)
                    else:
                        raw = vision_engine.analyze_image_bytes(
                            "Extract the following fields and return valid JSON only: " + ", ".join(fields),
                            file_bytes,
                            config=config,
                        )
                        structured = json.loads(raw)
                set_result("neuroread_vision_structured", structured)
                st.json(structured)
            except Exception as exc:
                st.error(f"Structured extraction failed: {exc}")

        if add_col.button("Add Vision Findings To Current Session"):
            combined = []
            if st.session_state.neuroread_vision_result:
                combined.append(st.session_state.neuroread_vision_result)
            if st.session_state.neuroread_vision_structured:
                combined.append(str(st.session_state.neuroread_vision_structured))
            if not combined:
                st.warning("Run a visual summary or structured extraction first.")
            else:
                combined_text = "\n\n".join(combined)
                try:
                    if rag_available:
                        lightrag_engine.insert_text(combined_text[:50000], f"Vision notes: {uploaded_visual.name}", workspace=workspace)
                    local_index = st.session_state.neuroread_local_index
                    if local_index is None:
                        st.session_state.neuroread_local_index = rag_engine.build_index_from_text(combined_text, source=f"vision:{uploaded_visual.name}")
                    else:
                        merged_text = "\n\n".join(local_index.chunks) + "\n\n" + combined_text
                        st.session_state.neuroread_local_index = rag_engine.build_index_from_text(merged_text, source="uploaded_documents")
                    if uploaded_visual.name not in st.session_state.neuroread_docs:
                        st.session_state.neuroread_docs.append(f"vision:{uploaded_visual.name}")
                    st.success("Added visual findings to the current NeuroRead session.")
                except Exception as exc:
                    st.error(f"Failed to add vision findings: {exc}")

    if st.session_state.neuroread_vision_result:
        st.divider()
        st.markdown(st.session_state.neuroread_vision_result)
    if st.session_state.neuroread_vision_structured:
        st.json(st.session_state.neuroread_vision_structured)

with tab_chat:
    mode = st.selectbox("Retrieval mode", ["hybrid", "local", "global", "mix", "naive"], index=0)
    st.caption("hybrid = entity-focused + community-based | local = entities only | global = communities only | naive = vector only")

    if st.session_state.neuroread_chat_history:
        with st.expander("Conversation Memory", expanded=False):
            for message in st.session_state.neuroread_chat_history:
                speaker = "You" if message["role"] == "user" else "SmartStudy AI"
                st.markdown(f"**{speaker}:** {message['content']}")

    if st.button("Reset Conversation"):
        st.session_state.neuroread_answer = ""
        st.session_state.neuroread_question = ""
        st.session_state.neuroread_references = []
        st.session_state.neuroread_chat_history = []

    question = st.text_area("Ask a question about your documents", height=100)

    if st.button("Ask", type="primary") and question.strip():
        placeholder = st.empty()
        with st.spinner(f"Querying {'knowledge graph' if rag_available else 'local RAG index'} ({mode} mode)..."):
            try:
                if rag_available:
                    result = lightrag_engine.query_with_references(
                        question,
                        mode=mode,
                        workspace=workspace,
                        conversation_history=st.session_state.neuroread_chat_history[-6:],
                    )
                    answer = result.get("response", "")
                    references = result.get("references", [])
                else:
                    if st.session_state.neuroread_local_index is None:
                        raise ValueError("No local documents indexed yet. Upload documents first.")
                    result = rag_engine.answer_from_index(st.session_state.neuroread_local_index, question)
                    answer = result.get("response", "")
                    references = result.get("sources", [])
                placeholder.markdown(answer)
                set_result("neuroread_answer", answer)
                set_result("neuroread_question", question)
                set_result("neuroread_references", references)
                st.session_state.neuroread_chat_history.extend(
                    [
                        {"role": "user", "content": question},
                        {"role": "assistant", "content": answer},
                    ]
                )
                # ── Vidya Smriti: log Q&A ──
                log_event("NeuroRead", "search_performed", question[:80], mode=mode)

            except Exception as e:
                st.error(f"Query failed: {e}")

    if st.session_state.neuroread_answer:
        if st.session_state.neuroread_question:
            st.caption(f"Question: {st.session_state.neuroread_question}")
        st.markdown(st.session_state.neuroread_answer)
        if st.session_state.neuroread_references:
            with st.expander("Sources", expanded=True):
                for ref in st.session_state.neuroread_references:
                    if rag_available:
                        st.markdown(f"- `{ref.get('reference_id', '?')}` {ref.get('file_path', 'Unknown source')}")
                    else:
                        st.markdown(
                            f"- chunk `{ref.get('chunk_id', '?')}` from `{ref.get('source', 'uploaded_documents')}` "
                            f"(score={ref.get('score', 0)})"
                        )
        if st.button("Export to Obsidian"):
            source_lines = []
            for ref in st.session_state.neuroread_references:
                if rag_available:
                    source_lines.append(f"- {ref.get('reference_id', '?')}: {ref.get('file_path', 'Unknown source')}")
                else:
                    source_lines.append(
                        f"- chunk {ref.get('chunk_id', '?')} from {ref.get('source', 'uploaded_documents')} "
                        f"(score={ref.get('score', 0)})"
                    )
            path = export_study_guide(
                f"NeuroRead - {st.session_state.neuroread_question[:50] if st.session_state.neuroread_question else 'Answer'}",
                "## Question\n"
                f"{st.session_state.neuroread_question}\n\n"
                "## Answer\n"
                f"{st.session_state.neuroread_answer}\n\n"
                "## Sources\n"
                + "\n".join(source_lines),
                tags=["neuroread", "document-qa"],
            )
            st.success(f"Exported to: {path}")
