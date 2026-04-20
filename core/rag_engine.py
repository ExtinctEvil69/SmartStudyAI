"""Local FAISS-style RAG fallback for SmartStudy AI.

The current product primarily uses LightRAG, but the project plan explicitly
calls for a standalone `rag_engine.py`. This module provides a lightweight,
local retrieval path that works without the external LightRAG server.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from core import gemma_engine
from core.gemma_engine import GemmaConfig
from core.utils import chunk_text


@dataclass
class RetrievedChunk:
    text: str
    score: float
    source: str
    chunk_id: int


@dataclass
class LocalRAGIndex:
    source: str
    chunks: list[str]
    embeddings: list[list[float]]


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = sqrt(sum(a * a for a in left))
    right_norm = sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def build_index_from_text(
    text: str,
    source: str = "document",
    chunk_size: int = 1200,
    overlap: int = 100,
    embedding_model: str = "nomic-embed-text:latest",
) -> LocalRAGIndex:
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    embeddings = gemma_engine.embed(chunks, model=embedding_model) if chunks else []
    return LocalRAGIndex(source=source, chunks=chunks, embeddings=embeddings)


def retrieve(index: LocalRAGIndex, query: str, top_k: int = 5, embedding_model: str = "nomic-embed-text:latest") -> list[RetrievedChunk]:
    if not index.chunks:
        return []
    query_embedding = gemma_engine.embed([query], model=embedding_model)[0]
    scored = [
        RetrievedChunk(text=chunk, score=_cosine_similarity(query_embedding, embedding), source=index.source, chunk_id=i)
        for i, (chunk, embedding) in enumerate(zip(index.chunks, index.embeddings))
    ]
    return sorted(scored, key=lambda item: item.score, reverse=True)[:top_k]


def answer_from_index(
    index: LocalRAGIndex,
    question: str,
    top_k: int = 5,
    config: GemmaConfig | None = None,
    stream_callback=None,
) -> dict:
    retrieved = retrieve(index, question, top_k=top_k)
    context = "\n\n".join(
        f"[Chunk {chunk.chunk_id} | score={chunk.score:.3f} | source={chunk.source}]\n{chunk.text}"
        for chunk in retrieved
    )
    prompt = f"""Answer the question using only the retrieved context below.

Question: {question}

Retrieved context:
{context}

Return a grounded answer. If the answer is not supported by the context, say so clearly."""
    cfg = config or GemmaConfig(temperature=0.2)
    cfg.system_prompt = "You are a grounded educational assistant. Do not invent unsupported facts."
    response = gemma_engine.generate(prompt, cfg, stream_callback=stream_callback)
    return {
        "response": response,
        "sources": [
            {"chunk_id": chunk.chunk_id, "score": round(chunk.score, 4), "source": chunk.source}
            for chunk in retrieved
        ],
    }
