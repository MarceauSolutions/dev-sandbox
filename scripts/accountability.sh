#!/bin/bash
# Marceau Accountability Engine — Launch dashboard
# Usage: ./scripts/accountability.sh

cd "$(dirname "$0")/.."

# Check if already running
if lsof -i :8780 > /dev/null 2>&1; then
    echo "Accountability Engine already running"
    open "http://127.0.0.1:8780"
    exit 0
fi

echo "Starting Accountability Engine → http://127.0.0.1:8780"
python -m projects.shared.command-center.src.app &
sleep 2
open "http://127.0.0.1:8780"
