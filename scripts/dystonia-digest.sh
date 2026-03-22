#!/bin/bash
# Dystonia Research Digest — Web Dashboard
# Launch: ./scripts/dystonia-digest.sh → http://127.0.0.1:8792
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$SCRIPT_DIR/.."
PROJECT_DIR="$ROOT_DIR/projects/marceau-solutions/labs/dystonia-digest"
PORT=8792

echo "═══════════════════════════════════════════"
echo "  Dystonia Research Digest"
echo "  http://127.0.0.1:$PORT"
echo "═══════════════════════════════════════════"

cd "$PROJECT_DIR"
if ! python3 -c "import fastapi, uvicorn, jinja2, aiofiles" 2>/dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt -q
fi

# Kill any existing process on this port
lsof -ti:$PORT 2>/dev/null | xargs kill -9 2>/dev/null || true

# Open browser after 2 second delay
(sleep 2 && open "http://127.0.0.1:$PORT") &

# Run with auto-reload
PYTHONPATH="$PROJECT_DIR:$ROOT_DIR:$PYTHONPATH" \
    python3 -c "
import uvicorn
uvicorn.run(
    'src.app:app',
    host='127.0.0.1',
    port=$PORT,
    reload=True,
    reload_dirs=['$PROJECT_DIR/src', '$PROJECT_DIR/templates', '$PROJECT_DIR/static']
)
"
