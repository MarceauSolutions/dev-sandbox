#!/bin/bash
# Claude Code PreToolUse Hook: Interface-First Guard (E10/E12)
#
# Fires on Write tool calls that create new .py files in projects/ that
# appear to be user-facing features (dashboard, app, bot, etc.)
#
# NON-BLOCKING (exit 0) — prints a warning checklist to stderr.
# The goal is to interrupt the default "just write the script" reflex
# and ensure the interface decision was made consciously.
#
# Does NOT fire for: test files, utilities, helpers, migrations, seeds,
# data processing scripts, or files outside projects/.

INPUT=$(cat)

# Only check Write tool calls
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null)
if [[ "$TOOL_NAME" != "Write" ]]; then
    exit 0
fi

# Get the file path being written
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null)

if [[ -z "$FILE_PATH" ]]; then
    exit 0
fi

# Only check .py files
if [[ "$FILE_PATH" != *.py ]]; then
    exit 0
fi

# Only check files in projects/ (not execution/, scripts/, or other dirs)
if [[ "$FILE_PATH" != */projects/* ]]; then
    exit 0
fi

# Skip output directories — generated artifacts are fine
if [[ "$FILE_PATH" == */output/* || "$FILE_PATH" == */__pycache__/* ]]; then
    exit 0
fi

# Get just the filename (lowercase) for pattern matching
BASENAME=$(basename "$FILE_PATH" .py | tr '[:upper:]' '[:lower:]')

# Skip utility/infrastructure files — these don't need interface checks
UTILITY_PATTERNS="test|util|helper|migration|seed|data|config|settings|model|schema|init|constants|types|exceptions|errors|base|mixin|decorator|middleware|fixture|factory|mock"
if echo "$BASENAME" | grep -qE "($UTILITY_PATTERNS)"; then
    exit 0
fi

# Check if filename suggests a user-facing feature
USER_FACING_PATTERNS="dashboard|app|bot|assistant|tool|manager|tracker|analyzer|generator|api|server|handler|endpoint|service|worker|scheduler|processor"
if ! echo "$BASENAME" | grep -qE "($USER_FACING_PATTERNS)"; then
    exit 0
fi

# File matches — emit interface check warning
echo "" >&2
echo "INTERFACE CHECK (E10/E12): $FILE_PATH" >&2
echo "This filename suggests a user-facing feature. Before proceeding, confirm:" >&2
echo "" >&2
echo "  1. Interface decision:" >&2
echo "     [ ] Clawdbot (Telegram) — conversational, quick lookups, William on phone" >&2
echo "     [ ] n8n workflow — automated, scheduled, triggered" >&2
echo "     [ ] Web app at subdomain — dashboard, interactive, data viz" >&2
echo "     [ ] Branded PDF — document, report, guide" >&2
echo "     [ ] SMS/Email — alert, notification" >&2
echo "     [ ] CLI script — ONLY if this is an internal utility, NOT William-facing" >&2
echo "" >&2
echo "  2. Is CLI being avoided as the final interface for William?" >&2
echo "  3. Can this be a new capability in an existing tool (Clawdbot, n8n, FitAI)?" >&2
echo "" >&2
echo "  Full decision tree: rules/routing/ROUTING.md" >&2
echo "" >&2

# Always exit 0 — this is a warning, not a block
exit 0
