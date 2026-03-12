#!/bin/bash
# Launch Miko's Lab Interactive Browser
# Usage: ./scripts/mikos-lab.sh

set -e

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)/projects/marceau-solutions/labs/mikos-lab"
PORT="${MIKOS_LAB_PORT:-8766}"

# Check for Flask
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Installing Flask..."
    pip3 install flask --quiet
fi

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║   MIKO'S LAB — AI Influencer Workshop  ║"
echo "  ║   http://127.0.0.1:${PORT}               ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

# Open browser after short delay
(sleep 1.5 && open "http://127.0.0.1:${PORT}") &

# Start server
cd "$APP_DIR"
MIKOS_LAB_PORT=$PORT python3 app.py
