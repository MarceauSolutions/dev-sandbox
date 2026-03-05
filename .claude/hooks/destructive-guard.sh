#!/bin/bash
# Claude Code PreToolUse Hook: Destructive Command Guard
#
# Detects destructive patterns (rm -rf, xargs rm, git checkout --, git clean, etc.)
# and automatically creates a backup of uncommitted work BEFORE the command runs.
#
# BLOCKING: If the command would delete inside dev-sandbox root, it blocks entirely.
# NON-BLOCKING: Otherwise it auto-backs up and allows the command.

INPUT=$(cat)

COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

if [[ -z "$COMMAND" ]]; then
    exit 0
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "")"
BACKUP_SCRIPT="$REPO_ROOT/scripts/backup-untracked.sh"

# ============================================================
# Pattern 1: BLOCK — rm/xargs targeting dev-sandbox root
# ============================================================
if echo "$COMMAND" | grep -qE '(xargs\s+rm|rm\s+-rf\s+\*)' 2>/dev/null; then
    if echo "$COMMAND" | grep -qE "(cd\s+[\"']?($REPO_ROOT|\\\$REPO_ROOT|\\\$\(git rev-parse)" 2>/dev/null; then
        echo "" >&2
        echo "=== DESTRUCTIVE GUARD: BLOCKED ===" >&2
        echo "Command appears to delete files in dev-sandbox root." >&2
        echo "If deploying, use: ./scripts/deploy_website.sh <client>" >&2
        echo "" >&2
        exit 1
    fi
fi

# ============================================================
# Pattern 2: WARN + AUTO-BACKUP — Any destructive command
# ============================================================
DESTRUCTIVE=false

if echo "$COMMAND" | grep -qE 'rm\s+-r[f ]' 2>/dev/null; then
    # Skip temp dirs — those are fine
    if echo "$COMMAND" | grep -qE 'rm\s+-rf\s+(/tmp/|/var/folders/|\$TMPDIR|\$DEPLOY_TMPDIR)' 2>/dev/null; then
        exit 0
    fi
    DESTRUCTIVE=true
fi

echo "$COMMAND" | grep -qE 'xargs\s+rm' 2>/dev/null && DESTRUCTIVE=true
echo "$COMMAND" | grep -qE 'git\s+checkout\s+--\s+\.' 2>/dev/null && DESTRUCTIVE=true
echo "$COMMAND" | grep -qE 'git\s+clean\s+-[fd]' 2>/dev/null && DESTRUCTIVE=true
echo "$COMMAND" | grep -qE 'git\s+reset\s+--hard' 2>/dev/null && DESTRUCTIVE=true

if [[ "$DESTRUCTIVE" == "true" ]]; then
    echo "" >&2
    echo "--- Destructive Guard: Auto-backup triggered ---" >&2
    if [[ -x "$BACKUP_SCRIPT" ]]; then
        "$BACKUP_SCRIPT" "pre-destructive" 2>&1 | while read -r line; do echo "  $line" >&2; done
    else
        echo "  WARNING: backup-untracked.sh not found" >&2
    fi
    echo "  Allowing command to proceed." >&2
    echo "" >&2
fi

exit 0
