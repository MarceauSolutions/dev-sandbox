#!/bin/bash
# Claude Code PreToolUse Hook: Duplicate Code Guard
#
# When creating a .py file, checks if a canonical version exists in execution/.
# If the filename matches an existing execution/ script, BLOCKS creation.
# Exception: MCP packages that need bundled copies.
# Exit 1 = block, Exit 0 = allow.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null)

# Only check .py files
if [[ ! "$FILE_PATH" =~ \.py$ ]]; then
    exit 0
fi

REPO_ROOT=$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null || echo "/Users/williammarceaujr./dev-sandbox")
BASENAME=$(basename "$FILE_PATH")
CANONICAL="$REPO_ROOT/execution/$BASENAME"

# Allow if not creating a duplicate (canonical doesn't exist)
if [[ ! -f "$CANONICAL" ]]; then
    exit 0
fi

# Allow if writing to the canonical location itself
if [[ "$FILE_PATH" == "$CANONICAL" ]]; then
    exit 0
fi

# Allow MCP packages — they need bundled copies for distribution
if [[ "$FILE_PATH" == *"/mcp/"* || "$FILE_PATH" == *"-mcp/"* ]]; then
    exit 0
fi

# Block — canonical version exists and this isn't an allowed exception
echo "" >&2
echo "=== DUPLICATE CODE GUARD ===" >&2
echo "A canonical version exists: execution/$BASENAME" >&2
echo "Import from execution/ instead of creating a copy." >&2
echo "" >&2
echo "If this is an MCP package that needs its own copy, rename or restructure." >&2
echo "" >&2
exit 1
