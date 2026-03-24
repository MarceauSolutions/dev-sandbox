#!/bin/bash
# Marceau Hub — One URL, all your tools.
# Always at http://127.0.0.1:8760
# Usage: ./scripts/hub.sh

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/projects/marceau-solutions/labs/hub/app.py"
PORT=8760

# Check if already running
if lsof -i :$PORT -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Hub already running → http://127.0.0.1:$PORT"
    open "http://127.0.0.1:$PORT"
    exit 0
fi

# Check for Flask
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Installing Flask..."
    pip3 install flask --quiet
fi

echo ""
echo "  ╔═══════════════════════════════════════╗"
echo "  ║   MARCEAU HUB                         ║"
echo "  ║   http://127.0.0.1:${PORT}              ║"
echo "  ║   One URL. All your tools.            ║"
echo "  ╚═══════════════════════════════════════╝"
echo ""

# Open browser
(sleep 1.5 && open "http://127.0.0.1:$PORT") &

# Start server
cd "$ROOT"
HUB_PORT=$PORT python3 "$APP"
