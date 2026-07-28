#!/usr/bin/env bash
set -euo pipefail
git pull --ff-only
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
cd frontend && npm install
