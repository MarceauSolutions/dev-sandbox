#!/bin/bash
###############################################################################
# ec2-sync-agent.sh - EC2 Repository Sync Agent
#
# DEPLOY TO EC2: /home/clawdbot/scripts/sync-agent.sh
#
# This script runs on EC2 and handles:
# - Automatic pulls before any agent work
# - Safe commits with conflict prevention
# - Sync status reporting
#
# USAGE (on EC2):
#   ./sync-agent.sh --pull           # Pull latest before starting work
#   ./sync-agent.sh --push "msg"     # Commit and push changes
#   ./sync-agent.sh --status         # Check sync status
#   ./sync-agent.sh --auto-sync      # Run by cron every 30 min
#
# Created: 2026-01-29
###############################################################################

set -e

# Configuration
REPO_DIR="/home/clawdbot/dev-sandbox"
BRANCH="main"
LOG_FILE="/home/clawdbot/.clawdbot/sync-agent.log"
LOCK_FILE="/tmp/ec2-sync.lock"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg" | tee -a "$LOG_FILE"
}

# Prevent concurrent runs
acquire_lock() {
    if [ -f "$LOCK_FILE" ]; then
        LOCK_PID=$(cat "$LOCK_FILE")
        if kill -0 "$LOCK_PID" 2>/dev/null; then
            log "ERROR: Another sync is running (PID $LOCK_PID)"
            exit 1
        fi
    fi
    echo $$ > "$LOCK_FILE"
}

release_lock() {
    rm -f "$LOCK_FILE"
}

trap release_lock EXIT

# Pull latest from origin (safe, creates backup)
do_pull() {
    log "=== PULL: Updating from origin ==="
    cd "$REPO_DIR"

    # Create backup
    BACKUP_BRANCH="backup-before-pull-$(date +%Y%m%d-%H%M%S)"
    git branch "$BACKUP_BRANCH" 2>/dev/null || true
    log "Backup: $BACKUP_BRANCH"

    # Stash any uncommitted changes
    if [ -n "$(git status -s)" ]; then
        git stash push -m "auto-stash $(date +%Y%m%d-%H%M%S)"
        log "Stashed uncommitted changes"
    fi

    # Fetch and pull
    git fetch origin "$BRANCH"

    LOCAL_COMMIT=$(git rev-parse HEAD)
    REMOTE_COMMIT=$(git rev-parse "origin/$BRANCH")

    if [ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]; then
        BEHIND=$(git rev-list --count HEAD.."origin/$BRANCH")
        log "Pulling $BEHIND commits..."
        git pull origin "$BRANCH" --rebase
        log "✓ Updated to $(git rev-parse --short HEAD)"
    else
        log "✓ Already up to date"
    fi
}

# Push changes to origin (with full conflict prevention)
do_push() {
    local commit_msg="${1:-Auto-commit from EC2 $(date +%Y%m%d-%H%M%S)}"
    local commit_dir="${2:-.}"

    log "=== PUSH: Committing and pushing ==="
    cd "$REPO_DIR"

    # Check for changes
    if [ -z "$(git status -s)" ]; then
        log "No changes to commit"
        return 0
    fi

    # 1. Fetch latest
    log "Fetching latest..."
    git fetch origin "$BRANCH"

    # 2. Check for incoming changes
    INCOMING=$(git log HEAD.."origin/$BRANCH" --oneline)
    if [ -n "$INCOMING" ]; then
        log "Incoming changes detected:"
        echo "$INCOMING" | head -5
        log "Pulling before commit..."
        git pull origin "$BRANCH" --rebase
    fi

    # 3. Create backup
    BACKUP_BRANCH="backup-before-push-$(date +%Y%m%d-%H%M%S)"
    git branch "$BACKUP_BRANCH"
    log "Backup: $BACKUP_BRANCH"

    # 4. Stage and commit
    git add "$commit_dir"
    git commit -m "$commit_msg

Co-Authored-By: Clawdbot <clawdbot@ec2>"
    log "Committed: $(git rev-parse --short HEAD)"

    # 5. Dry run
    log "Dry run push..."
    if ! git push --dry-run origin "$BRANCH" 2>&1; then
        log "ERROR: Dry run failed"
        return 1
    fi

    # 6. Actual push
    log "Pushing to origin..."
    git push origin "$BRANCH"
    log "✓ Pushed successfully"
}

# Check sync status
do_status() {
    cd "$REPO_DIR"

    git fetch origin "$BRANCH" 2>/dev/null

    LOCAL_COMMIT=$(git rev-parse HEAD)
    LOCAL_SHORT="${LOCAL_COMMIT:0:7}"
    REMOTE_COMMIT=$(git rev-parse "origin/$BRANCH" 2>/dev/null || echo "unknown")
    REMOTE_SHORT="${REMOTE_COMMIT:0:7}"

    echo "═══════════════════════════════════════════════════════════════"
    echo "  EC2 SYNC STATUS - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "Repository: $REPO_DIR"
    echo "Branch:     $BRANCH"
    echo ""
    echo "EC2 Commit:    $LOCAL_SHORT"
    echo "GitHub Commit: $REMOTE_SHORT"
    echo ""

    UNCOMMITTED=$(git status -s | wc -l | tr -d ' ')
    echo "Uncommitted changes: $UNCOMMITTED"

    if [ "$LOCAL_COMMIT" == "$REMOTE_COMMIT" ]; then
        echo ""
        echo "✓ EC2 is in sync with GitHub"
    else
        BEHIND=$(git rev-list --count HEAD.."origin/$BRANCH" 2>/dev/null || echo "?")
        AHEAD=$(git rev-list --count "origin/$BRANCH"..HEAD 2>/dev/null || echo "?")
        echo ""
        echo "⚠ EC2 is $AHEAD ahead, $BEHIND behind GitHub"

        if [ "$BEHIND" -gt 0 ]; then
            echo ""
            echo "Run: ./sync-agent.sh --pull"
        fi
        if [ "$AHEAD" -gt 0 ]; then
            echo ""
            echo "Run: ./sync-agent.sh --push 'message'"
        fi
    fi
    echo ""
}

# Auto-sync (for cron job - pull only, push requires explicit action)
do_auto_sync() {
    log "=== AUTO-SYNC ==="

    # Only pull automatically (pushing requires explicit commit message)
    do_pull

    # Report status
    cd "$REPO_DIR"
    UNCOMMITTED=$(git status -s | wc -l)
    if [ "$UNCOMMITTED" -gt 0 ]; then
        log "⚠ EC2 has $UNCOMMITTED uncommitted changes"
    fi
}

show_usage() {
    echo "EC2 Sync Agent - Repository synchronization for Clawdbot/Ralph"
    echo ""
    echo "Usage: $0 [option]"
    echo ""
    echo "Options:"
    echo "  --pull              Pull latest from GitHub"
    echo "  --push 'message'    Commit and push changes"
    echo "  --status            Show sync status"
    echo "  --auto-sync         Auto-pull (for cron)"
    echo ""
    echo "Cron setup (every 30 min):"
    echo "  */30 * * * * /home/clawdbot/scripts/sync-agent.sh --auto-sync"
}

# Main
acquire_lock

case "${1:-}" in
    --pull)
        do_pull
        ;;
    --push)
        do_push "${2:-}"
        ;;
    --status)
        do_status
        ;;
    --auto-sync)
        do_auto_sync
        ;;
    --help|-h|"")
        show_usage
        ;;
    *)
        echo "Unknown option: $1"
        show_usage
        exit 1
        ;;
esac
