#!/usr/bin/env bash
# AgentOS Hook: No Asking Guard
# Blocks the AI from asking permission for obvious next steps.
# "Just do it" — E1 enforcement.

set -euo pipefail

INPUT=$(cat)
MESSAGE=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
msg = d.get('tool_input', {}).get('content', '')
if not msg:
    msg = d.get('tool_input', {}).get('message', '')
print(msg.lower() if msg else '')
" 2>/dev/null || true)

if [[ -z "$MESSAGE" ]]; then
    exit 0
fi

# Permission-seeking patterns
if echo "$MESSAGE" | grep -qE "(would you like me to|want me to|should i|shall i|do you want me to|would you prefer)" 2>/dev/null; then
    # Exception: genuinely ambiguous decisions
    if echo "$MESSAGE" | grep -qE "(option|either|alternatively|which approach|two ways|multiple)" 2>/dev/null; then
        exit 0
    fi
    echo "" >&2
    echo "=== NO ASKING GUARD ===" >&2
    echo "Rule E1: Just do it." >&2
    echo "If it's an obvious next step, do it. Don't ask." >&2
    echo "Only ask when there are genuinely multiple valid paths." >&2
    echo "" >&2
    exit 1
fi

# "Let me know if..." deferral
if echo "$MESSAGE" | grep -qE "let me know if (you('d| would) like|you want|i should)" 2>/dev/null; then
    echo "" >&2
    echo "=== NO ASKING GUARD ===" >&2
    echo "Rule E1: Just do it. Don't defer obvious tasks." >&2
    echo "" >&2
    exit 1
fi

exit 0
