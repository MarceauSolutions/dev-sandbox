#!/bin/bash
# Claude Code PreToolUse Hook: Tool Reuse Checker
#
# Receives JSON on stdin from Claude Code with tool_input.file_path.
# When creating a new .py file, extracts keywords and searches inventory.
# Informational only — warns but does not block (exit 0).

# Read JSON from stdin
INPUT=$(cat)

# Extract file path from tool input using python
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null)

# Only check .py files
if [[ ! "$FILE_PATH" =~ \.py$ ]]; then
    exit 0
fi

# Extract keywords from filename (split on _ and -)
BASENAME=$(basename "$FILE_PATH" .py)
KEYWORDS=$(echo "$BASENAME" | tr '_-' '\n' | grep -v '^$')

INVENTORY_SCRIPT="/Users/williammarceaujr./dev-sandbox/scripts/inventory.py"
if [[ ! -f "$INVENTORY_SCRIPT" ]]; then
    exit 0
fi

MATCHES=""
for KEYWORD in $KEYWORDS; do
    # Skip very short or common words
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

# Always allow — this is informational only
exit 0
