#!/usr/bin/env bash
# AgentOS Hook: No Delegation Guard
# Blocks the AI from telling the user to do something manually
# when it could be done programmatically. E5 enforcement.

set -euo pipefail

INPUT=$(cat)
MESSAGE=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
msg = d.get('tool_input', {}).get('content', '')
print(msg.lower())
" 2>/dev/null || true)

if [[ -z "$MESSAGE" ]]; then
    exit 0
fi

VIOLATIONS=()

# "Go to [service] and..." — telling user to visit a service we may have API access to
if echo "$MESSAGE" | grep -qE '(go to|visit|navigate to|log into)\s+(stripe|github|google sheets|twilio|aws console)' 2>/dev/null; then
    VIOLATIONS+=("Telling user to visit a service — check if API access exists first")
fi

# "You'll need to..." for technical tasks
if echo "$MESSAGE" | grep -qE "(you('ll| will) need to|you should|you can then)\s+(add|set|configure|update|change|create|delete|enable|disable)" 2>/dev/null; then
    VIOLATIONS+=("Delegating a technical task to the user")
fi

# "Manually" anything
if echo "$MESSAGE" | grep -qE "manual(ly)?\s+(add|set|configure|update|change|create|run|execute)" 2>/dev/null; then
    VIOLATIONS+=("Suggesting manual action for automatable task")
fi

if [[ ${#VIOLATIONS[@]} -gt 0 ]]; then
    echo "" >&2
    echo "=== NO DELEGATION GUARD ===" >&2
    echo "Rule E5: Use APIs, never delegate to user." >&2
    echo "" >&2
    for v in "${VIOLATIONS[@]}"; do
        echo "  VIOLATION: $v" >&2
    done
    echo "" >&2
    echo "Before telling the user to do something:" >&2
    echo "  1. Check .env for API keys" >&2
    echo "  2. Check execution/ for existing scripts" >&2
    echo "  3. Check available MCP tools" >&2
    echo "  4. If programmatic access exists, USE IT." >&2
    echo "" >&2
    exit 1
fi

exit 0
