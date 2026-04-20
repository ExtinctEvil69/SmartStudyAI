#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

export OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
export LIGHTRAG_HOST="${LIGHTRAG_HOST:-http://localhost:9621}"
export LLM_BINDING="ollama"
export EMBEDDING_BINDING="ollama"
export LLM_BINDING_HOST="$OLLAMA_HOST"
export EMBEDDING_BINDING_HOST="$OLLAMA_HOST"
export LLM_MODEL="${LLM_MODEL:-gemma4:e2b}"
export EMBEDDING_MODEL="${EMBEDDING_MODEL:-nomic-embed-text:latest}"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
python3 -m pip install -q -r requirements.txt

if ! command -v lightrag-server >/dev/null 2>&1; then
  python3 -m pip install -q -e "./LightRAG[api]"
fi

lightrag-server --llm-binding ollama --embedding-binding ollama
