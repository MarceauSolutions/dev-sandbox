#!/bin/bash
# MailAssist — AI Email Assistant
# Launch: ./scripts/email-assistant.sh → http://127.0.0.1:8791

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$SCRIPT_DIR/.."
PROJECT_DIR="$ROOT_DIR/projects/marceau-solutions/labs/email-assistant"
PORT=8791

echo "═══════════════════════════════════════════"
echo "  MailAssist — AI Email Assistant"
echo "  http://127.0.0.1:$PORT"
echo "═══════════════════════════════════════════"

# Check for credentials.json
CREDS="${GOOGLE_OAUTH_CREDENTIALS:-$ROOT_DIR/credentials.json}"
if [ ! -f "$CREDS" ]; then
    echo ""
    echo "WARNING: credentials.json not found at $CREDS"
    echo "Download OAuth credentials from Google Cloud Console:"
    echo "  1. Go to https://console.cloud.google.com"
    echo "  2. APIs & Services → Credentials → Create OAuth Client ID"
    echo "  3. Application type: Web application"
    echo "  4. Add redirect URI: http://127.0.0.1:$PORT/auth/callback"
    echo "  5. Download JSON → save as credentials.json in dev-sandbox root"
    echo ""
fi

# Install deps if needed
cd "$PROJECT_DIR"
if ! python3 -c "import fastapi, uvicorn, anthropic" 2>/dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt -q
fi

# Kill any existing instance on this port
lsof -ti:$PORT 2>/dev/null | xargs kill -9 2>/dev/null || true

echo ""
echo "Starting MailAssist on port $PORT..."
echo "Press Ctrl+C to stop"
echo ""

# Open browser after short delay
(sleep 2 && open "http://127.0.0.1:$PORT") &

# Run from project dir so relative paths work, add to PYTHONPATH
cd "$PROJECT_DIR"
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
