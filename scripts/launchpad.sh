#!/bin/bash
# LaunchPad — Direct launch. No CLI navigation needed.
# Usage: ./scripts/launchpad.sh [product-name]
# Default product: dumbphone-lock

PRODUCT="${1:-dumbphone-lock}"
PORT=8765
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/projects/marceau-solutions/labs/launch-platform/src/app.py"

# Open browser after server starts
(sleep 1.5 && open "http://127.0.0.1:$PORT") &

python "$APP" --product "$PRODUCT" --port $PORT
