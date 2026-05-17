#!/bin/bash
# claude_auto.sh — Run `claude -p` autonomously on the Mac without permission prompts.
#
# Use this when you want to start a task and walk away. Permission prompts are
# bypassed so code generation, edits, and bash commands run uninterrupted.
#
# Auth: uses your local Claude login (Max/Pro subscription). No API tokens billed.
#
# Usage:
#   bash scripts/claude_auto.sh "describe the task here"
#   bash scripts/claude_auto.sh "fix the bug in projects/industrial-ops/src/sop_builder/drive_collector.py"
#
# Pipe input:
#   echo "summarize this" | bash scripts/claude_auto.sh
#
# Restrict to a subdirectory:
#   bash scripts/claude_auto.sh --add-dir projects/industrial-ops "<task>"
#
# Output is streamed to stdout AND tee'd to scripts/.claude_auto.last.log for review.

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$REPO_ROOT/scripts/.claude_auto.last.log"

cd "$REPO_ROOT"

echo "==> claude_auto: bypassing permission prompts, using local subscription"
echo "==> repo: $REPO_ROOT"
echo "==> log:  $LOG"
echo "----"

exec claude -p \
    --permission-mode bypassPermissions \
    "$@" 2>&1 | tee "$LOG"
