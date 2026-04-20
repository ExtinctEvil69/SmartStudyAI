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

mkdir -p data/demo_outputs

LIGHTRAG_PID=""

cleanup() {
  if [ -n "$LIGHTRAG_PID" ] && kill -0 "$LIGHTRAG_PID" >/dev/null 2>&1; then
    kill "$LIGHTRAG_PID" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

if ! curl -sf "$LIGHTRAG_HOST/health" >/dev/null 2>&1; then
  echo "Starting LightRAG server..."
  lightrag-server --llm-binding ollama --embedding-binding ollama > "data/demo_outputs/lightrag.log" 2>&1 &
  LIGHTRAG_PID="$!"

  for _ in $(seq 1 30); do
    if curl -sf "$LIGHTRAG_HOST/health" >/dev/null 2>&1; then
      break
    fi
    sleep 2
  done
fi

if ! curl -sf "$OLLAMA_HOST/api/tags" >/dev/null 2>&1; then
  echo "Warning: Ollama is not reachable at $OLLAMA_HOST"
  echo "Start it first with: ollama serve"
fi

echo "Launching SmartStudy AI demo..."
streamlit run main.py --browser.gatherUsageStats false
