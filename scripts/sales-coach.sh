#!/bin/bash
# AI Sales Coach — Mock Call Practice Tool
# Launch: ./scripts/sales-coach.sh → http://127.0.0.1:8796
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$SCRIPT_DIR/.."
PORT=8796

echo "═══════════════════════════════════════════"
echo "  AI Sales Coach — Mock Call Practice"
echo "  http://127.0.0.1:$PORT"
echo "═══════════════════════════════════════════"

# Kill existing
lsof -ti:$PORT 2>/dev/null | xargs kill -9 2>/dev/null || true

# Install deps if needed
python3 -c "import flask, anthropic" 2>/dev/null || pip3 install flask anthropic -q

# Open browser
(sleep 2 && open "http://127.0.0.1:$PORT") &

PYTHONPATH="$ROOT_DIR" python3 "$ROOT_DIR/projects/shared/sales-coach/src/app.py"
