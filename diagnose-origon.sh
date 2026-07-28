#!/usr/bin/env bash
set -u
for cmd in python3 node npm ffmpeg ffprobe; do printf '%-10s' "$cmd"; command -v "$cmd" || true; done
curl -fsS http://127.0.0.1:8000/health 2>/dev/null || echo "API offline"
curl -fsS http://127.0.0.1:3000 2>/dev/null >/dev/null && echo "Frontend OK" || echo "Frontend offline"
