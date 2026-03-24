#!/usr/bin/env bash
# AgentOS Hook: Duplicate Code Guard
# Blocks creating a .py file when a canonical version exists in execution/.
# Enforces: "Import from execution/, don't duplicate."

set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || true)

if [[ ! "$FILE_PATH" =~ \.py$ ]]; then
    exit 0
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"
BASENAME=$(basename "$FILE_PATH")
CANONICAL="$REPO_ROOT/execution/$BASENAME"

# Allow if canonical doesn't exist
if [[ ! -f "$CANONICAL" ]]; then
    exit 0
fi

# Allow if writing to canonical location itself
if [[ "$FILE_PATH" == "$CANONICAL" ]]; then
    exit 0
fi

echo "" >&2
echo "=== DUPLICATE CODE GUARD ===" >&2
echo "A canonical version exists: execution/$BASENAME" >&2
echo "Import from execution/ instead of creating a copy." >&2
echo "" >&2
exit 1
