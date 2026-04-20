"""Academic Paper Analyzer — arXiv search + LightRAG + Gemma 4 analysis."""

import io
import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus
from xml.etree import ElementTree as ET

import requests
import streamlit as st
from pypdf import PdfReader

from core import gemma_engine, lightrag_engine, vision_engine
from core.session_context import get_session_workspace
from core.obsidian_export import export_study_guide
from core.page_state import ensure_state, set_result
from core.sidebar import render_sidebar
from core.ui_components import inject_global_css, page_header

APP_DIR = Path(__file__).parent.parent
DB_PATH = APP_DIR / "data" / "papers.db"
ARXIV_API = "https://export.arxiv.org/api/query"
ARXIV_NS = {"a": "http://www.w3.org/2005/Atom"}

st.set_page_config(page_title="Paper Analyzer", page_icon="📄", layout="wide")
inject_global_css()
model_config = render_sidebar("paperanalyzer")

page_header("📄", "Academic Paper Analyzer", "Search arXiv, analyze papers with LightRAG knowledge graph + Gemma 4.", badge="Research")


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL, authors TEXT, source TEXT,
            url TEXT, abstract TEXT, analysis TEXT, saved_at TEXT, content TEXT
        )"""
    )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(papers)").fetchall()}
    if "content" not in columns:
        conn.execute("ALTER TABLE papers ADD COLUMN content TEXT")
    return conn


def arxiv_search(query: str, max_results: int = 10):
    params = f"search_query=all:{quote_plus(query)}&start=0&max_results={max_results}&sortBy=relevance"
    r = requests.get(f"{ARXIV_API}?{params}", timeout=30)
    r.raise_for_status()
    root = ET.fromstring(r.text)
    out = []
    for entry in root.findall("a:entry", ARXIV_NS):
        title = (entry.findtext("a:title", default="", namespaces=ARXIV_NS) or "").strip()
        summary = (entry.findtext("a:summary", default="", namespaces=ARXIV_NS) or "").strip()
        published = entry.findtext("a:published", default="", namespaces=ARXIV_NS) or ""
        authors = [(a.findtext("a:name", default="", namespaces=ARXIV_NS) or "").strip()
                    for a in entry.findall("a:author", ARXIV_NS)]
        page_url, pdf_url = "", ""
        for link in entry.findall("a:link", ARXIV_NS):
            if link.get("type") == "application/pdf":
                pdf_url = link.get("href", "")
            elif link.get("rel") == "alternate":
                page_url = link.get("href", "")
        out.append({"title": title, "authors": authors, "abstract": summary,
                     "published": published[:10], "url": page_url, "pdf_url": pdf_url})
    return out


def extract_pdf_text(file_bytes: bytes, max_chars: int = 60000) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    parts, total = [], 0
    for page in reader.pages:
        text = page.extract_text() or ""
        parts.append(text)
        total += len(text)
        if total >= max_chars:
            break
    return "\n".join(parts)[:max_chars]


ensure_state(
    paper=None,
    analysis=None,
    search_results=[],
    paper_answer="",
    paper_question="",
    paper_references=[],
    paper_chat_history=[],
    paper_bytes=None,
    paper_vision_result="",
    paper_vision_structured=None,
)
workspace = get_session_workspace("paper_analyzer_workspace", "paperanalyzer")

# Sidebar — saved papers
with st.sidebar:
    st.subheader("Saved Papers")
    conn = db()
    saved = conn.execute("SELECT id, title, saved_at FROM papers ORDER BY id DESC").fetchall()
    conn.close()
    if not saved:
        st.caption("No papers saved yet.")
    for pid, title, saved_at in saved:
        with st.expander(f"{title[:60]}"):
            st.caption(saved_at)
            if st.button("Load", key=f"load_{pid}"):
                conn = db()
                row = conn.execute(
                    "SELECT title, authors, source, url, abstract, analysis, content FROM papers WHERE id=?",
                    (pid,),
                ).fetchone()
                conn.close()
                if row:
                    st.session_state.paper = {
                        "title": row[0],
                        "authors": row[1].split(", ") if row[1] else [],
                        "source": row[2],
                        "url": row[3],
                        "abstract": row[4],
                        "content": row[6] or row[4],
                    }
                    st.session_state.analysis = row[5]
                    st.session_state.paper_answer = ""
                    st.session_state.paper_references = []
                    st.session_state.paper_chat_history = []
                    st.rerun()

# Tabs
tab_search, tab_upload, tab_analyze = st.tabs(["🔍 Search arXiv", "📄 Upload PDF", "🧠 Analyze"])

with tab_search:
    query = st.text_input("Search query", placeholder="e.g. retrieval augmented generation for medical QA")
    max_results = st.slider("Results", 5, 25, 10)
    if st.button("Search", type="primary") and query.strip():
        with st.spinner("Searching arXiv..."):
            st.session_state.search_results = arxiv_search(query, max_results)
    for i, p in enumerate(st.session_state.search_results):
        with st.container(border=True):
            st.markdown(f"### {p['title']}")
            st.caption(f"{', '.join(p['authors'][:5])} | {p['published']}")
            st.write(p["abstract"][:400] + ("..." if len(p["abstract"]) > 400 else ""))
            cols = st.columns(3)
            if p["url"]:
                cols[0].link_button("arXiv page", p["url"])
            if cols[2].button("Load for analysis", key=f"load_search_{i}"):
                with st.spinner("Fetching PDF..."):
                    pdf_bytes = requests.get(p["pdf_url"], timeout=60).content
                    content = extract_pdf_text(pdf_bytes)
                    st.session_state.paper = {**p, "source": "arXiv", "content": content}
                    st.session_state.paper_bytes = pdf_bytes
                    st.session_state.analysis = None
                    st.session_state.paper_answer = ""
                    st.session_state.paper_references = []
                    st.session_state.paper_chat_history = []
                    # Also index in LightRAG
                    if lightrag_engine.is_available(workspace=workspace):
                        lightrag_engine.insert_text(content[:50000], f"Paper: {p['title']}", workspace=workspace)
                    st.success("Loaded. Go to Analyze tab.")

with tab_upload:
    uploaded = st.file_uploader("Upload a PDF", type=["pdf"])
    title_override = st.text_input("Title (optional)")
    if uploaded and st.button("Load PDF", type="primary"):
        with st.spinner("Extracting text..."):
            file_bytes = uploaded.read()
            content = extract_pdf_text(file_bytes)
            st.session_state.paper = {"title": title_override or uploaded.name, "authors": [],
                                       "source": "Upload", "url": "", "abstract": content[:1000], "content": content}
            st.session_state.paper_bytes = file_bytes
            st.session_state.analysis = None
            st.session_state.paper_answer = ""
            st.session_state.paper_references = []
            st.session_state.paper_chat_history = []
            if lightrag_engine.is_available(workspace=workspace):
                lightrag_engine.insert_text(content[:50000], f"Paper: {title_override or uploaded.name}", workspace=workspace)
            st.success("Loaded. Go to Analyze tab.")

with tab_analyze:
    paper = st.session_state.paper
    if not paper:
        st.info("Load a paper from Search or Upload first.")
    else:
        st.markdown(f"## {paper['title']}")
        if paper.get("authors"):
            st.caption(", ".join(paper["authors"]))

        available_models = gemma_engine.list_models() or ["gemma4:e2b"]
        docread_model = st.selectbox(
            "DocRead vision model",
            available_models,
            index=0,
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("Structured Analysis")
            if st.button("Run Analysis", type="primary"):
                prompt = f"""Analyze this academic paper and produce a structured report:

## TL;DR
## Problem & Motivation
## Key Contributions
## Methodology
## Results
## Limitations
## Why It Matters

PAPER: {paper['content'][:40000]}"""
                placeholder = st.empty()
                config = gemma_engine.GemmaConfig(model=model_config.model, max_tokens=4096)
                with st.spinner("Analyzing..."):
                    result = gemma_engine.generate(prompt, config, stream_callback=lambda t: placeholder.markdown(t))
                st.session_state.analysis = result

            if st.session_state.analysis:
                st.markdown(st.session_state.analysis)
                if st.button("Save paper"):
                    conn = db()
                    conn.execute("INSERT INTO papers (title,authors,source,url,abstract,analysis,saved_at,content) VALUES (?,?,?,?,?,?,?,?)",
                                 (paper["title"], ", ".join(paper.get("authors", [])), paper.get("source", ""),
                                   paper.get("url", ""), paper.get("abstract", ""), st.session_state.analysis,
                                   datetime.utcnow().isoformat(timespec="seconds"), paper.get("content", "")))
                    conn.commit()
                    conn.close()
                    st.success("Saved!")
                if st.button("Export to Obsidian"):
                    path = export_study_guide(paper["title"], st.session_state.analysis, tags=["paper-analyzer", "academic"])
                    st.success(f"Exported: {path}")

            if st.session_state.paper_bytes is not None:
                st.divider()
                st.subheader("Visual Page Analysis")
                vision_instruction = st.text_area(
                    "Vision prompt",
                    value="Summarize the visible academic content, identify key figures/tables/formulas, and explain what stands out on the inspected pages.",
                    height=100,
                    key="paper_vision_prompt",
                )
                fields = st.text_input(
                    "Structured fields",
                    value="title, key_figures, formulas, table_summary, methodology_clues",
                    key="paper_vision_fields",
                )
                max_pages = st.slider("Pages to inspect visually", 1, 5, 2, key="paper_vision_pages")
                vision_col1, vision_col2, vision_col3 = st.columns(3)
                if vision_col1.button("Run Visual Summary"):
                    try:
                        config = vision_engine.VisionConfig(model=docread_model, temperature=0.2, max_tokens=2500)
                        with st.spinner("Analyzing paper pages visually..."):
                            result = vision_engine.analyze_pdf_pages(st.session_state.paper_bytes, vision_instruction, config=config, max_pages=max_pages)
                        set_result("paper_vision_result", result)
                    except Exception as exc:
                        st.error(f"Vision analysis failed: {exc}")
                if vision_col2.button("Extract Structured Fields"):
                    try:
                        config = vision_engine.VisionConfig(model=docread_model, temperature=0.1, max_tokens=1200)
                        structured = vision_engine.extract_structured_document_info(
                            st.session_state.paper_bytes,
                            [field.strip() for field in fields.split(",") if field.strip()],
                            config=config,
                        )
                        set_result("paper_vision_structured", structured)
                    except Exception as exc:
                        st.error(f"Structured extraction failed: {exc}")
                if vision_col3.button("Add Visual Findings To RAG Context"):
                    combined = []
                    if st.session_state.paper_vision_result:
                        combined.append(st.session_state.paper_vision_result)
                    if st.session_state.paper_vision_structured:
                        combined.append(str(st.session_state.paper_vision_structured))
                    if not combined:
                        st.warning("Run visual analysis first.")
                    else:
                        extra_context = "\n\n".join(combined)
                        try:
                            if lightrag_engine.is_available(workspace=workspace):
                                lightrag_engine.insert_text(extra_context[:50000], f"Vision notes: {paper['title']}", workspace=workspace)
                            st.session_state.paper["content"] += "\n\n" + extra_context
                            st.success("Visual findings added to the current paper context.")
                        except Exception as exc:
                            st.error(f"Failed to enrich paper context: {exc}")

                if st.session_state.paper_vision_result:
                    st.markdown(st.session_state.paper_vision_result)
                if st.session_state.paper_vision_structured:
                    st.json(st.session_state.paper_vision_structured)

        with col2:
            st.subheader("Ask about this paper")
            st.caption(f"Session workspace: `{workspace}`")
            reset_col, clear_col = st.columns(2)
            if reset_col.button("Reset Session Answers"):
                st.session_state.paper_answer = ""
                st.session_state.paper_question = ""
                st.session_state.paper_references = []
                st.session_state.paper_chat_history = []
            if clear_col.button("Clear Session Workspace"):
                try:
                    docs = lightrag_engine.get_documents(workspace=workspace)
                    for doc in docs:
                        doc_id = doc.get("id") or doc.get("doc_id")
                        if doc_id:
                            lightrag_engine.delete_document(doc_id, workspace=workspace)
                    st.session_state.paper_answer = ""
                    st.session_state.paper_question = ""
                    st.session_state.paper_references = []
                    st.session_state.paper_chat_history = []
                    st.success("Cleared the Paper Analyzer workspace.")
                except Exception as exc:
                    st.error(f"Failed to clear workspace: {exc}")
            if st.session_state.paper_chat_history:
                with st.expander("Conversation Memory", expanded=False):
                    for message in st.session_state.paper_chat_history:
                        speaker = "You" if message["role"] == "user" else "SmartStudy AI"
                        st.markdown(f"**{speaker}:** {message['content']}")
            question = st.text_area("Your question", height=100)
            use_lightrag = st.checkbox("Use LightRAG knowledge graph", value=lightrag_engine.is_available(workspace=workspace))

            if st.button("Ask") and question.strip():
                placeholder = st.empty()
                if use_lightrag and lightrag_engine.is_available(workspace=workspace):
                    with st.spinner("Querying knowledge graph..."):
                        result = lightrag_engine.query_with_references(
                            question,
                            mode="hybrid",
                            workspace=workspace,
                            conversation_history=st.session_state.paper_chat_history[-6:],
                        )
                        answer = result.get("response", "")
                        set_result("paper_references", result.get("references", []))
                else:
                    history_text = "\n".join(
                        f"{message['role']}: {message['content']}" for message in st.session_state.paper_chat_history[-6:]
                    )
                    prompt = f"""Answer this question about the paper. Use ONLY the paper content.

Conversation history:
{history_text or 'None'}

PAPER: {paper['content'][:40000]}

QUESTION: {question}"""
                    config = gemma_engine.GemmaConfig(model=model_config.model)
                    with st.spinner("Thinking..."):
                        answer = gemma_engine.generate(prompt, config, stream_callback=lambda t: placeholder.markdown(t))
                    set_result("paper_references", [])

                placeholder.markdown(answer)
                set_result("paper_answer", answer)
                set_result("paper_question", question)
                st.session_state.paper_chat_history.extend(
                    [
                        {"role": "user", "content": question},
                        {"role": "assistant", "content": answer},
                    ]
                )

            if st.session_state.paper_answer:
                st.markdown(st.session_state.paper_answer)
                if st.session_state.paper_question:
                    st.caption(f"Question: {st.session_state.paper_question}")
                if st.session_state.paper_references:
                    with st.expander("Sources", expanded=True):
                        for ref in st.session_state.paper_references:
                            st.markdown(f"- `{ref.get('reference_id', '?')}` {ref.get('file_path', 'Unknown source')}")
