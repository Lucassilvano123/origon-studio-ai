#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
command -v ffmpeg >/dev/null || { echo "Instale FFmpeg: sudo apt-get update && sudo apt-get install -y ffmpeg"; exit 1; }
python3 -m venv "$ROOT/backend/.venv"
source "$ROOT/backend/.venv/bin/activate"
pip install --upgrade pip
pip install -r "$ROOT/backend/requirements.txt"
cd "$ROOT/frontend" && npm install
python -c "from app.main import app" 2>/dev/null || true
echo "Setup concluido. Execute ./start-origon.sh"
