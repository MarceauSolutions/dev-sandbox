#!/usr/bin/env bash
# AgentOS Hook: Stack Guard
# Blocks attempts to use unapproved tools/services.
# Add services to BLOCKED_TOOLS to enforce your approved stack.

set -euo pipefail

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || true)

if [[ -z "$COMMAND" ]]; then
    exit 0
fi

COMMAND_LOWER=$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]')

# --- CONFIGURE YOUR BLOCKED TOOLS ---
# Add services/tools you explicitly do NOT want used.
# These will be HARD BLOCKED — the AI cannot use them.
# Example entries: "ngrok" "heroku" "netlify"
BLOCKED_TOOLS=(
    # Add your blocked tools here during setup
)

for tool in "${BLOCKED_TOOLS[@]}"; do
    if [[ "$COMMAND_LOWER" == *"$tool"* ]]; then
        echo "" >&2
        echo "=== STACK GUARD: BLOCKED ===" >&2
        echo "Attempted to use: $tool" >&2
        echo "This is NOT in your approved stack." >&2
        echo "" >&2
        echo "Check your approved stack in CLAUDE.md or update this hook" >&2
        echo "to allow this tool: .claude/hooks/stack-guard.sh" >&2
        echo "" >&2
        exit 1
    fi
done

exit 0
