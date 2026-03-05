#!/bin/bash
# Claude Code PreToolUse Hook: No Asking Guard
#
# HARD RULE #1: Just do it — Never ask "want me to do X?" when X is obvious.
#
# Detects hedging/permission-seeking patterns in Claude's output text.
# Blocks phrases like "Would you like me to...", "Should I...", "Want me to..."
# when they're about obvious next steps.

INPUT=$(cat)

# This hook only applies if it's somehow triggered on text output
# In practice, we'll add this to the PostToolUse or as a behavioral check
MESSAGE=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
msg = d.get('tool_input', {}).get('content', '')
if not msg:
    msg = d.get('tool_input', {}).get('message', '')
print(msg.lower() if msg else '')
" 2>/dev/null)

if [[ -z "$MESSAGE" ]]; then
    exit 0
fi

# Permission-seeking patterns
VIOLATIONS=()

# "Would you like me to..." / "Want me to..." / "Should I..."
if echo "$MESSAGE" | grep -qE "(would you like me to|want me to|should i|shall i|do you want me to|would you prefer)" 2>/dev/null; then
    # Exception: genuinely ambiguous decisions (multiple valid options)
    # Allow if the message also contains "option" or "either"
    if echo "$MESSAGE" | grep -qE "(option|either|alternatively|which approach|two ways)" 2>/dev/null; then
        exit 0
    fi
    VIOLATIONS+=("Permission-seeking for obvious next step")
fi

# "Let me know if..." when the answer is obviously yes
if echo "$MESSAGE" | grep -qE "let me know if (you('d| would) like|you want|i should)" 2>/dev/null; then
    VIOLATIONS+=("Deferring action on obvious task")
fi

if [[ ${#VIOLATIONS[@]} -gt 0 ]]; then
    echo "" >&2
    echo "=== NO ASKING GUARD ===" >&2
    echo "HARD RULE #1: Just do it." >&2
    echo "" >&2
    for v in "${VIOLATIONS[@]}"; do
        echo "  VIOLATION: $v" >&2
    done
    echo "" >&2
    echo "If it's an obvious next step, do it. Don't ask." >&2
    echo "Only ask when there are genuinely multiple valid paths." >&2
    echo "" >&2
    exit 1
fi

exit 0
