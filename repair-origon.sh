#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$ROOT"/storage/{database,media,music,voice,compositions,renders,exports,backups,trash,products,batches}
find "$ROOT/backend" -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
rm -rf "$ROOT/frontend/.next"
echo "Pastas e caches reparados. Dados SQLite preservados."
