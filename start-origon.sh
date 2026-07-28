#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cleanup(){ kill ${API_PID:-0} ${WEB_PID:-0} 2>/dev/null || true; }
trap cleanup EXIT INT TERM
cd "$ROOT/backend"; source .venv/bin/activate
ORIGON_STORAGE="$ROOT/storage" uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 & API_PID=$!
cd "$ROOT/frontend"; npm run dev -- --hostname 0.0.0.0 --port 3000 & WEB_PID=$!
echo "Origon Studio AI: http://localhost:3000 | API: http://localhost:8000/docs"
wait
