#!/bin/bash
# Shortcut for bidirectional sync
# Usage:
#   bash scripts/sync.sh              # Full sync
#   bash scripts/sync.sh --dry-run    # Preview
#   bash scripts/sync.sh --status     # Check state
cd "$(dirname "$0")/.." && python3 scripts/bidirectional_sync.py "$@"
