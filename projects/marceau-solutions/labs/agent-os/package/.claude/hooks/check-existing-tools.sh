#!/usr/bin/env bash
# AgentOS Hook: Tool Reuse Checker
# When creating a new .py file, searches inventory for similar existing tools.
# Informational only — warns but does not block.

set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || true)

# Only check .py files
if [[ ! "$FILE_PATH" =~ \.py$ ]]; then
    exit 0
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"
INVENTORY_SCRIPT="$REPO_ROOT/scripts/inventory.py"

if [[ ! -f "$INVENTORY_SCRIPT" ]]; then
    exit 0
fi

BASENAME=$(basename "$FILE_PATH" .py)
KEYWORDS=$(echo "$BASENAME" | tr '_-' '\n' | grep -v '^$')

MATCHES=""
for KEYWORD in $KEYWORDS; do
    if [[ ${#KEYWORD} -lt 4 ]]; then
        continue
    fi
    RESULT=$(python3 "$INVENTORY_SCRIPT" search "$KEYWORD" 2>/dev/null)
    if [[ -n "$RESULT" && "$RESULT" != *"No matches"* ]]; then
        MATCHES="$MATCHES\n--- Matches for '$KEYWORD' ---\n$RESULT"
    fi
done

if [[ -n "$MATCHES" ]]; then
    echo "Similar tools may already exist:" >&2
    echo -e "$MATCHES" >&2
    echo "" >&2
    echo "Check if you can reuse existing tools before creating new ones." >&2
fi

exit 0
