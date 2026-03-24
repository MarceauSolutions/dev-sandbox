#!/bin/bash
# Launch the Marceau Solutions client signing portal.
# Usage: ./scripts/signing-portal.sh
set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT/projects/shared/signing-portal"

export PYTHONPATH="$REPO_ROOT:$PYTHONPATH"
if [ -f "$REPO_ROOT/.env" ]; then
  set -o allexport
  source "$REPO_ROOT/.env"
  set +o allexport
fi

echo ""
echo "  Marceau Signing Portal"
echo "  Local:  http://localhost:8797/{token}"
echo "  Prod:   https://sign.marceausolutions.com/{token}"
echo "  Health: http://localhost:8797/health"
echo ""

python app.py
