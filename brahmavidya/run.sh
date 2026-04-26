#!/usr/bin/env bash
# BrahmaVidya — start the FastAPI app locally.
# Usage: ./brahmavidya/run.sh [port]

set -e
cd "$(dirname "$0")/.."

PORT="${1:-8000}"
VENV=".venv/bin/python3"

# Pick venv python if it has fastapi, otherwise fall back to system python.
if [[ -x "$VENV" ]] && "$VENV" -c "import fastapi" 2>/dev/null; then
    PY="$VENV"
elif command -v /Library/Frameworks/Python.framework/Versions/3.14/bin/python3 &>/dev/null; then
    PY="/Library/Frameworks/Python.framework/Versions/3.14/bin/python3"
else
    PY="$(command -v python3)"
fi

echo "▶ Using Python: $PY"
echo "▶ Open: http://localhost:$PORT"
echo ""

# Health check — Ollama must be running for Gemma generation
if curl -s -o /dev/null -w "%{http_code}" http://localhost:11434 | grep -q 200; then
    echo "✓ Ollama detected at http://localhost:11434"
else
    echo "⚠ Ollama not running — start it with: ollama serve"
fi

exec "$PY" -m uvicorn brahmavidya.app:app --reload --host 0.0.0.0 --port "$PORT"
