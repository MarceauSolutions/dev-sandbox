#!/bin/bash
# run.sh — Start the Marceau Solutions signing portal (port 8797)
set -e
cd "$(dirname "$0")"
REPO_ROOT="$(cd "../../.." && pwd)"
export PYTHONPATH="$REPO_ROOT:$PYTHONPATH"

echo ""
echo "  Marceau Signing Portal"
echo "  http://localhost:8797/health"
echo ""

python app.py
