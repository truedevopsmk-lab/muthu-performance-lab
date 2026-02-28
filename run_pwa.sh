#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment (.venv)..."
  python3 -m venv .venv
fi

source .venv/bin/activate

python -m pip install --upgrade pip >/dev/null
python -m pip install -r requirements.txt >/dev/null

GARMIN_PATH="${1:-}"
if [ -n "$GARMIN_PATH" ]; then
  python export_pwa_data.py --garmin-path "$GARMIN_PATH"
else
  python export_pwa_data.py
fi

echo ""
echo "PWA running at: http://localhost:8765/pwa/"
echo "Press Ctrl+C to stop."
python -m http.server 8765
