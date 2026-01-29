#!/bin/bash
###############################################################################
# invoke-claude-code.sh - Invoke Claude Code for complex tasks
#
# Allows Clawdbot or other agents to delegate complex coding tasks to Claude Code.
# Uses the claude-code-mcp server for "agent in agent" architecture.
#
# USAGE:
#   ./invoke-claude-code.sh "Fix the bug in server.py"
#   ./invoke-claude-code.sh --file /path/to/file.py "Refactor this file"
#   ./invoke-claude-code.sh --dir /path/to/project "Add tests for all modules"
#
# EXAMPLES:
#   # Simple prompt
#   ./invoke-claude-code.sh "List all Python files in the project"
#
#   # Work on specific file
#   ./invoke-claude-code.sh --file execution/stripe_payments.py "Add input validation"
#
#   # Work on entire directory
#   ./invoke-claude-code.sh --dir projects/shared/lead-scraper "Fix all linting errors"
#
# Created: 2026-01-29
###############################################################################

set -e

# Source environment (for API keys)
if [ -f ~/.bashrc ]; then
    source ~/.bashrc 2>/dev/null || true
fi
if [ -f "$HOME/dev-sandbox/.env" ]; then
    export $(grep -v '^#' "$HOME/dev-sandbox/.env" | xargs) 2>/dev/null || true
fi

# Configuration
CLAUDE_CMD="${CLAUDE_CLI_NAME:-claude}"
WORKING_DIR="${WORKING_DIR:-/home/clawdbot/dev-sandbox}"
LOG_DIR="$WORKING_DIR/.claude-invocations"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

show_usage() {
    echo "Usage: $0 [OPTIONS] \"prompt\""
    echo ""
    echo "Options:"
    echo "  --file FILE     Work on a specific file"
    echo "  --dir DIR       Work in a specific directory"
    echo "  --max-turns N   Maximum conversation turns (default: 5)"
    echo "  --dry-run       Show what would be executed without running"
    echo "  --help          Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 \"Fix the import error in server.py\""
    echo "  $0 --file execution/stripe_payments.py \"Add docstrings\""
    echo "  $0 --dir projects/shared/lead-scraper \"Run tests and fix failures\""
}

# Parse arguments
FILE=""
DIR=""
MAX_TURNS=5
DRY_RUN=false
PROMPT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --file)
            FILE="$2"
            shift 2
            ;;
        --dir)
            DIR="$2"
            shift 2
            ;;
        --max-turns)
            MAX_TURNS="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            PROMPT="$1"
            shift
            ;;
    esac
done

if [ -z "$PROMPT" ]; then
    echo -e "${RED}Error: No prompt provided${NC}"
    show_usage
    exit 1
fi

# Create log directory
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/invocation-$TIMESTAMP.log"

# Build the command
CMD_ARGS=("--print" "--dangerously-skip-permissions" "--max-turns" "$MAX_TURNS")

if [ -n "$FILE" ]; then
    # Ensure file path is absolute
    if [[ ! "$FILE" = /* ]]; then
        FILE="$WORKING_DIR/$FILE"
    fi
    PROMPT="File: $FILE\n\n$PROMPT"
fi

if [ -n "$DIR" ]; then
    # Ensure directory path is absolute
    if [[ ! "$DIR" = /* ]]; then
        DIR="$WORKING_DIR/$DIR"
    fi
    cd "$DIR"
fi

# Log the invocation
log "Invoking Claude Code" | tee -a "$LOG_FILE"
log "Prompt: $PROMPT" | tee -a "$LOG_FILE"
log "Working Directory: $(pwd)" | tee -a "$LOG_FILE"
log "Max Turns: $MAX_TURNS" | tee -a "$LOG_FILE"

if [ "$DRY_RUN" = true ]; then
    echo ""
    echo -e "${YELLOW}DRY RUN - Would execute:${NC}"
    echo "$CLAUDE_CMD ${CMD_ARGS[*]} -p \"$PROMPT\""
    exit 0
fi

# Execute Claude Code
echo ""
log "Starting Claude Code..." | tee -a "$LOG_FILE"

# Run Claude Code with the prompt
$CLAUDE_CMD "${CMD_ARGS[@]}" -p "$PROMPT" 2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    log "${GREEN}Claude Code completed successfully${NC}" | tee -a "$LOG_FILE"
else
    log "${RED}Claude Code exited with code $EXIT_CODE${NC}" | tee -a "$LOG_FILE"
fi

log "Log saved to: $LOG_FILE"
exit $EXIT_CODE
