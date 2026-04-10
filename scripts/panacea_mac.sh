#!/usr/bin/env bash
# Panacea Mac — Autonomous claude -p with Grok pre-consultation
#
# Same architecture as EC2 Panacea: Grok consulted first, direction injected
# via --append-system-prompt into claude -p. Uses the same grok_strategic_layer.py module.
#
# Usage:
#   ./scripts/panacea_mac.sh "refactor the PDF engine to use tower structure"
#   ./scripts/panacea_mac.sh "run the morning digest and send it to my phone"

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# Load env
if [ -f "$REPO_ROOT/.env" ]; then
    set -a
    source "$REPO_ROOT/.env"
    set +a
fi

if [ $# -eq 0 ]; then
    echo "Usage: panacea_mac.sh 'your task here'"
    exit 1
fi

PROMPT="$*"

SYSTEM_PROMPT="You are Panacea, William's autonomous AI agent running on his Mac. \
Execute the task fully — edit files, run commands, deploy, test. \
Be concise in output. William is not watching — just do the work and report the result. \
You have full access to the dev-sandbox repo, bash, git, and all tools."

# Consult Grok (same module as EC2 Panacea)
echo "[Panacea] Consulting Grok..."
GROK_DIRECTION=$(python3 "$REPO_ROOT/projects/personal-assistant/src/grok_strategic_layer.py" "$PROMPT" 2>/dev/null | tail -n +2 || echo "Grok unreachable — proceeding with best judgment.")
echo "[Panacea] Grok says: $GROK_DIRECTION"
echo ""

# Run Claude with Grok's direction via --append-system-prompt (same as EC2 Panacea)
echo "[Panacea] Executing with Claude Code..."
echo "---"
claude -p "$PROMPT" \
    --output-format text \
    --system-prompt "$SYSTEM_PROMPT" \
    --append-system-prompt "Strategic directive from Grok: $GROK_DIRECTION"
