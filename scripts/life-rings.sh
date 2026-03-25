#!/bin/bash
# Life Rings — Gamified life progress tracker
# Usage: ./scripts/life-rings.sh

PORT=8797
DIR="$(cd "$(dirname "$0")/../projects/marceau-solutions/labs/life-rings" && pwd)"

# Kill existing
lsof -ti :$PORT 2>/dev/null | xargs kill 2>/dev/null

cd "$DIR"
python3 -m http.server $PORT &>/dev/null &
sleep 0.5
open "http://127.0.0.1:$PORT"
echo "Life Rings running at http://127.0.0.1:$PORT"
