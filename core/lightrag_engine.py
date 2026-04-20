"""LightRAG integration — graph-based RAG via the running LightRAG server.

Replaces the FAISS-based rag_engine from the original plan with LightRAG's
knowledge graph approach: entity extraction, relationship mapping, and
multi-mode retrieval (local, global, hybrid, mix, naive).
"""

import time

import requests

from core.settings import get_lightrag_base

QUERY_MODES = ("local", "global", "hybrid", "mix", "naive")


def _workspace_headers(workspace: str | None = None) -> dict[str, str]:
    if not workspace:
        return {}
    return {"LIGHTRAG-WORKSPACE": workspace}


def health_check(workspace: str | None = None) -> dict | None:
    try:
        r = requests.get(f"{get_lightrag_base()}/health", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def is_available(workspace: str | None = None) -> bool:
    h = health_check()
    return h is not None and h.get("status") == "healthy"


def insert_text(text: str, description: str = "", workspace: str | None = None) -> dict:
    """Insert text into the LightRAG knowledge graph."""
    payload = {"text": text}
    if description:
        payload["description"] = description
    r = requests.post(
        f"{get_lightrag_base()}/documents/text",
        json=payload,
        timeout=30,
        headers=_workspace_headers(workspace),
    )
    r.raise_for_status()
    return r.json()


def insert_file(file_path: str, workspace: str | None = None) -> dict:
    """Upload a file (PDF, DOCX, TXT, etc.) to LightRAG."""
    with open(file_path, "rb") as f:
        r = requests.post(
            f"{get_lightrag_base()}/documents/file",
            files={"file": f},
            timeout=60,
            headers=_workspace_headers(workspace),
        )
    r.raise_for_status()
    return r.json()


def insert_file_bytes(filename: str, file_bytes: bytes, content_type: str = "application/pdf", workspace: str | None = None) -> dict:
    """Upload file bytes to LightRAG."""
    r = requests.post(
        f"{get_lightrag_base()}/documents/file",
        files={"file": (filename, file_bytes, content_type)},
        timeout=60,
        headers=_workspace_headers(workspace),
    )
    r.raise_for_status()
    return r.json()


def pipeline_status(workspace: str | None = None) -> dict:
    """Check document processing pipeline status."""
    r = requests.get(
        f"{get_lightrag_base()}/documents/pipeline_status",
        timeout=10,
        headers=_workspace_headers(workspace),
    )
    r.raise_for_status()
    return r.json()


def wait_for_pipeline(timeout: int = 300, poll_interval: int = 3, workspace: str | None = None) -> bool:
    """Block until the pipeline is idle. Returns True if completed, False on timeout."""
    start = time.time()
    while time.time() - start < timeout:
        status = pipeline_status(workspace)
        if not status.get("busy", True):
            return True
        time.sleep(poll_interval)
    return False


def query(question: str, mode: str = "hybrid", top_k: int = 40, stream: bool = False, workspace: str | None = None) -> str:
    """Query the LightRAG knowledge graph."""
    if mode not in QUERY_MODES:
        raise ValueError(f"mode must be one of {QUERY_MODES}")
    payload = {
        "query": question,
        "mode": mode,
        "top_k": top_k,
        "stream": stream,
    }
    r = requests.post(
        f"{get_lightrag_base()}/query",
        json=payload,
        timeout=300,
        headers=_workspace_headers(workspace),
    )
    r.raise_for_status()
    data = r.json()
    return data.get("response", "")


def query_with_references(
    question: str,
    mode: str = "hybrid",
    top_k: int = 40,
    workspace: str | None = None,
    include_chunk_content: bool = False,
    conversation_history: list[dict[str, str]] | None = None,
) -> dict:
    """Query LightRAG and return the full response with references."""
    if mode not in QUERY_MODES:
        raise ValueError(f"mode must be one of {QUERY_MODES}")
    payload = {
        "query": question,
        "mode": mode,
        "top_k": top_k,
        "stream": False,
        "include_references": True,
        "include_chunk_content": include_chunk_content,
    }
    if conversation_history:
        payload["conversation_history"] = conversation_history
    r = requests.post(
        f"{get_lightrag_base()}/query",
        json=payload,
        timeout=300,
        headers=_workspace_headers(workspace),
    )
    r.raise_for_status()
    return r.json()


def get_graph(max_nodes: int = 500, workspace: str | None = None) -> dict:
    """Retrieve the knowledge graph for visualization."""
    r = requests.get(
        f"{get_lightrag_base()}/graph",
        params={"limit": max_nodes},
        timeout=30,
        headers=_workspace_headers(workspace),
    )
    r.raise_for_status()
    return r.json()


def get_documents(workspace: str | None = None) -> list[dict]:
    """List all indexed documents."""
    r = requests.get(f"{get_lightrag_base()}/documents", timeout=10, headers=_workspace_headers(workspace))
    r.raise_for_status()
    return r.json()


def delete_document(doc_id: str, workspace: str | None = None) -> dict:
    """Delete a document from the index."""
    r = requests.delete(
        f"{get_lightrag_base()}/documents/{doc_id}",
        timeout=10,
        headers=_workspace_headers(workspace),
    )
    r.raise_for_status()
    return r.json()
