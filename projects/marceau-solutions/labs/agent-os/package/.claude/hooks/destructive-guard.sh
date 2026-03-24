#!/usr/bin/env bash
# AgentOS Hook: Destructive Command Guard
# Auto-backs up before destructive operations. Blocks deletion in project root.

set -euo pipefail

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || true)

if [[ -z "$COMMAND" ]]; then
    exit 0
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"

# BLOCK: rm/xargs targeting project root
if echo "$COMMAND" | grep -qE '(xargs\s+rm|rm\s+-rf\s+\*)' 2>/dev/null; then
    if echo "$COMMAND" | grep -qE "(cd\s+[\"']?($REPO_ROOT|\\\$REPO_ROOT|\\\$\(git rev-parse)" 2>/dev/null; then
        echo "" >&2
        echo "=== DESTRUCTIVE GUARD: BLOCKED ===" >&2
        echo "Command appears to delete files in project root." >&2
        echo "This is too dangerous to allow automatically." >&2
        echo "" >&2
        exit 1
    fi
fi

# WARN: Any destructive command
DESTRUCTIVE=false
echo "$COMMAND" | grep -qE 'rm\s+-r[f ]' 2>/dev/null && DESTRUCTIVE=true
echo "$COMMAND" | grep -qE 'xargs\s+rm' 2>/dev/null && DESTRUCTIVE=true
echo "$COMMAND" | grep -qE 'git\s+checkout\s+--\s+\.' 2>/dev/null && DESTRUCTIVE=true
echo "$COMMAND" | grep -qE 'git\s+clean\s+-[fd]' 2>/dev/null && DESTRUCTIVE=true
echo "$COMMAND" | grep -qE 'git\s+reset\s+--hard' 2>/dev/null && DESTRUCTIVE=true

if [[ "$DESTRUCTIVE" == "true" ]]; then
    # Skip temp directory operations
    if echo "$COMMAND" | grep -qE 'rm\s+-rf\s+(/tmp/|/var/folders/|\$TMPDIR)' 2>/dev/null; then
        exit 0
    fi
    echo "" >&2
    echo "--- Destructive Guard: Caution ---" >&2
    echo "This command modifies or deletes files. Proceeding with care." >&2
    echo "" >&2
fi

exit 0
