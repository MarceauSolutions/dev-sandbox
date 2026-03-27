#!/bin/bash
# Safe Git Save — one command to commit and push tracked changes
#
# Usage:
#   ./scripts/save.sh "Added daily loop and hot lead handler"
#   ./scripts/save.sh                    # Default timestamp message
#   ./scripts/save.sh --dry-run          # Preview only
#   ./scripts/save.sh --include-new "Added new tower files"

cd "$(dirname "$0")/.."
python3 execution/safe_git_save.py "$@"
