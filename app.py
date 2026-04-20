import io
import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus
from xml.etree import ElementTree as ET

import requests
import streamlit as st
from pypdf import PdfReader

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "papers.db"
OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "gemma3:4b"
ARXIV_API = "http://export.arxiv.org/api/query"
ARXIV_NS = {"a": "http://www.w3.org/2005/Atom"}


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            authors TEXT,
            source TEXT,
            url TEXT,
            abstract TEXT,
            analysis TEXT,
            saved_at TEXT
        )"""
    )
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
        authors = [
            (a.findtext("a:name", default="", namespaces=ARXIV_NS) or "").strip()
            for a in entry.findall("a:author", ARXIV_NS)
        ]
        page_url = ""
        pdf_url = ""
        for link in entry.findall("a:link", ARXIV_NS):
            if link.get("type") == "application/pdf":
                pdf_url = link.get("href", "")
            elif link.get("rel") == "alternate":
                page_url = link.get("href", "")
        out.append(
            {
                "title": title,
                "authors": authors,
                "abstract": summary,
                "published": published[:10],
                "url": page_url,
                "pdf_url": pdf_url,
            }
        )
    return out


def extract_pdf_text(file_bytes: bytes, max_chars: int = 60_000) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    parts = []
    total = 0
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        parts.append(text)
        total += len(text)
        if total >= max_chars:
            break
    return "\n".join(parts)[:max_chars]


def fetch_pdf_bytes(url: str) -> bytes:
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.content


def ollama_generate(prompt: str, model: str, stream_placeholder=None) -> str:
    payload = {"model": model, "prompt": prompt, "stream": True}
    try:
        r = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=600)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f"[Ollama error: {e}. Is `ollama serve` running and `{model}` pulled?]"

    full = []
    for line in r.iter_lines():
        if not line:
            continue
        try:
            chunk = json.loads(line.decode("utf-8"))
        except json.JSONDecodeError:
            continue
        token = chunk.get("response", "")
        if token:
            full.append(token)
            if stream_placeholder is not None:
                stream_placeholder.markdown("".join(full))
        if chunk.get("done"):
            break
    return "".join(full)


def list_ollama_models() -> list[str]:
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return []


ANALYSIS_PROMPT = """You are an expert academic research assistant. Analyze the paper below and produce a structured report in Markdown with these sections:

## TL;DR
Two sentences capturing the core contribution.

## Problem & Motivation
What problem does this paper solve and why it matters.

## Key Contributions
Bulleted list of the main contributions.

## Methodology
How the authors approach the problem — datasets, models, techniques, experiments.

## Results
Headline numbers and findings, with comparisons where stated.

## Limitations & Open Questions
Weaknesses, scope limits, or unanswered questions.

## Why It Matters
Who should care about this work and what it enables next.

Be precise. Quote numbers only if they appear in the text. Do not invent citations.

---
PAPER TITLE: {title}

PAPER CONTENT:
{content}
"""

QA_PROMPT = """You are an expert research assistant answering a question about an academic paper.
Use ONLY the paper content below. If the answer is not in the paper, say so.

PAPER TITLE: {title}

PAPER CONTENT:
{content}

QUESTION: {question}

Answer in Markdown. Be concise and cite section names when possible."""


st.set_page_config(page_title="Academic Paper Analyzer", page_icon="📚", layout="wide")

if "paper" not in st.session_state:
    st.session_state.paper = None
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "search_results" not in st.session_state:
    st.session_state.search_results = []

st.title("📚 Academic Paper Analyzer")
st.caption("Search arXiv, upload PDFs, analyze with local Gemma via Ollama — part of SmartStudy AI.")

with st.sidebar:
    st.header("⚙️ Settings")
    available = list_ollama_models()
    if available:
        default_idx = 0
        for i, m in enumerate(available):
            if m.startswith("gemma"):
                default_idx = i
                break
        model = st.selectbox("Model", available, index=default_idx)
    else:
        model = st.text_input("Model", value=DEFAULT_MODEL)
        st.warning("Ollama not reachable at localhost:11434. Start it with `ollama serve` and pull a Gemma model, e.g. `ollama pull gemma3:4b`.")

    st.divider()
    st.subheader("💾 Saved Papers")
    conn = db()
    saved = conn.execute(
        "SELECT id, title, saved_at FROM papers ORDER BY id DESC"
    ).fetchall()
    conn.close()
    if not saved:
        st.caption("No papers saved yet.")
    for pid, title, saved_at in saved:
        with st.expander(f"{title[:60]}"):
            st.caption(saved_at)
            cols = st.columns(2)
            if cols[0].button("Load", key=f"load_{pid}"):
                conn = db()
                row = conn.execute(
                    "SELECT title, authors, source, url, abstract, analysis FROM papers WHERE id=?",
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
                        "content": row[4],
                    }
                    st.session_state.analysis = row[5]
                    st.rerun()
            if cols[1].button("Delete", key=f"del_{pid}"):
                conn = db()
                conn.execute("DELETE FROM papers WHERE id=?", (pid,))
                conn.commit()
                conn.close()
                st.rerun()

tab_search, tab_upload, tab_analyze = st.tabs(["🔍 Search arXiv", "📄 Upload PDF", "🧠 Analyze & Chat"])

with tab_search:
    query = st.text_input("Search query", placeholder="e.g. retrieval augmented generation for medical QA")
    max_results = st.slider("Results", 5, 25, 10)
    if st.button("Search", type="primary") and query.strip():
        with st.spinner("Searching arXiv..."):
            try:
                st.session_state.search_results = arxiv_search(query, max_results)
            except Exception as e:
                st.error(f"arXiv error: {e}")

    for i, p in enumerate(st.session_state.search_results):
        with st.container(border=True):
            st.markdown(f"### {p['title']}")
            st.caption(f"{', '.join(p['authors'][:5])}{' et al.' if len(p['authors']) > 5 else ''} • {p['published']}")
            st.write(p["abstract"][:400] + ("..." if len(p["abstract"]) > 400 else ""))
            cols = st.columns(3)
            if p["url"]:
                cols[0].link_button("arXiv page", p["url"])
            if p["pdf_url"]:
                cols[1].link_button("PDF", p["pdf_url"])
            if cols[2].button("Load for analysis", key=f"load_search_{i}"):
                with st.spinner("Fetching PDF..."):
                    try:
                        pdf_bytes = fetch_pdf_bytes(p["pdf_url"])
                        content = extract_pdf_text(pdf_bytes)
                        st.session_state.paper = {
                            "title": p["title"],
                            "authors": p["authors"],
                            "source": "arXiv",
                            "url": p["url"],
                            "abstract": p["abstract"],
                            "content": content,
                        }
                        st.session_state.analysis = None
                        st.success("Loaded. Open the Analyze tab.")
                    except Exception as e:
                        st.error(f"Failed to fetch PDF: {e}")

with tab_upload:
    uploaded = st.file_uploader("Upload a PDF", type=["pdf"])
    title_override = st.text_input("Title (optional)")
    if uploaded and st.button("Load PDF", type="primary"):
        with st.spinner("Extracting text..."):
            try:
                content = extract_pdf_text(uploaded.read())
                st.session_state.paper = {
                    "title": title_override or uploaded.name,
                    "authors": [],
                    "source": "Upload",
                    "url": "",
                    "abstract": content[:1000],
                    "content": content,
                }
                st.session_state.analysis = None
                st.success("Loaded. Open the Analyze tab.")
            except Exception as e:
                st.error(f"PDF error: {e}")

with tab_analyze:
    paper = st.session_state.paper
    if not paper:
        st.info("Load a paper from Search or Upload first.")
    else:
        st.markdown(f"## {paper['title']}")
        if paper["authors"]:
            st.caption(", ".join(paper["authors"]))
        meta_cols = st.columns(3)
        meta_cols[0].metric("Source", paper["source"])
        meta_cols[1].metric("Characters", f"{len(paper['content']):,}")
        meta_cols[2].metric("Approx. words", f"{len(paper['content'].split()):,}")

        with st.expander("Raw extracted text"):
            st.text(paper["content"][:5000] + ("..." if len(paper["content"]) > 5000 else ""))

        st.divider()
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("🧠 Structured Analysis")
            if st.button("Run analysis", type="primary"):
                placeholder = st.empty()
                prompt = ANALYSIS_PROMPT.format(
                    title=paper["title"], content=paper["content"][:40_000]
                )
                with st.spinner(f"Analyzing with {model}..."):
                    result = ollama_generate(prompt, model, placeholder)
                st.session_state.analysis = result

            if st.session_state.analysis:
                st.markdown(st.session_state.analysis)
                save_cols = st.columns(2)
                if save_cols[0].button("💾 Save paper"):
                    conn = db()
                    conn.execute(
                        "INSERT INTO papers (title, authors, source, url, abstract, analysis, saved_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            paper["title"],
                            ", ".join(paper["authors"]),
                            paper["source"],
                            paper["url"],
                            paper["abstract"],
                            st.session_state.analysis,
                            datetime.utcnow().isoformat(timespec="seconds"),
                        ),
                    )
                    conn.commit()
                    conn.close()
                    st.success("Saved.")
                save_cols[1].download_button(
                    "⬇️ Download .md",
                    data=f"# {paper['title']}\n\n{st.session_state.analysis}",
                    file_name=f"{paper['title'][:60].replace('/', '_')}.md",
                    mime="text/markdown",
                )

        with col2:
            st.subheader("💬 Ask a question")
            question = st.text_area("Your question", height=100)
            if st.button("Ask") and question.strip():
                placeholder = st.empty()
                prompt = QA_PROMPT.format(
                    title=paper["title"],
                    content=paper["content"][:40_000],
                    question=question,
                )
                with st.spinner("Thinking..."):
                    ollama_generate(prompt, model, placeholder)
