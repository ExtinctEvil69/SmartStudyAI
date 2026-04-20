#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

mkdir -p assets/screenshots data/demo_outputs

cat <<'EOF'
Demo asset checklist prepared.

Take and save these screenshots:
  assets/screenshots/homepage.png
  assets/screenshots/netseek.png
  assets/screenshots/neuroread.png
  assets/screenshots/quizverse.png
  assets/screenshots/audiooverview.png
  assets/screenshots/logictrace.png

Docs already prepared:
  DEMO_SCRIPT.md
  DEMO_SCRIPT_3_MIN_WORD_FOR_WORD.md
  JUDGE_CHECKLIST.md
  PITCH_60_SECONDS.md
  DEVPOST_SUBMISSION.md

Current running services to capture:
  App: http://localhost:8524
  LightRAG: http://localhost:9621
EOF
