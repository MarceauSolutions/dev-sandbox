#!/bin/bash
# Marceau Command Center — Launch Script
# Usage: ./scripts/command-center.sh
# Opens the business dashboard at http://127.0.0.1:8780

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
APP="$PROJECT_ROOT/projects/shared/command-center/app.py"
PORT=8780
URL="http://127.0.0.1:$PORT"

# Check if already running
if lsof -i :$PORT -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Command Center already running at $URL"
    open "$URL"
    exit 0
fi

echo ""
echo "============================================"
echo "  MARCEAU COMMAND CENTER"
echo "  Starting on $URL"
echo "============================================"
echo ""

# Open browser after a short delay
(sleep 2 && open "$URL") &

# Run the Flask app
cd "$PROJECT_ROOT"
python3 "$APP"
