#!/bin/bash
###############################################################################
# ec2-sync-agent.sh - EC2 Repository Sync Agent (v2 - 2026-04-02)
#
# DEPLOY TO EC2: /home/clawdbot/scripts/sync-agent.sh
#
# Handles bidirectional sync between EC2 and GitHub:
# - Pulls from GitHub (stash + rebase, no backup branches)
# - Commits and pushes EC2 changes (respects .gitignore)
# - Auto-sync mode for cron (pull, commit if needed, push)
#
# USAGE:
#   ./sync-agent.sh --pull           # Pull latest
#   ./sync-agent.sh --push "msg"     # Commit and push
#   ./sync-agent.sh --status         # Check sync status
#   ./sync-agent.sh --auto-sync      # Cron: pull + commit + push
###############################################################################

set -e

REPO_DIR="/home/clawdbot/dev-sandbox"
BRANCH="main"
LOG_FILE="/home/clawdbot/.clawdbot/sync-agent.log"
LOCK_FILE="/tmp/ec2-sync.lock"

mkdir -p "$(dirname "$LOG_FILE")"

log() {
    local ts
    ts=$(date "+%Y-%m-%d %H:%M:%S")
    echo "[$ts] $1" | tee -a "$LOG_FILE"
}

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

do_pull() {
    log "=== PULL: Updating from origin ==="
    cd "$REPO_DIR"

    # Stash uncommitted changes (safe — no backup branches)
    STASHED=false
    if [ -n "$(git status -s)" ]; then
        git stash push -m "auto-stash $(date +%Y%m%d-%H%M%S)" -q
        STASHED=true
        log "Stashed uncommitted changes"
    fi

    git fetch origin "$BRANCH"

    LOCAL_COMMIT=$(git rev-parse HEAD)
    REMOTE_COMMIT=$(git rev-parse "origin/$BRANCH")

    if [ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]; then
        BEHIND=$(git rev-list --count HEAD.."origin/$BRANCH")
        log "Pulling $BEHIND commits..."
        if git pull origin "$BRANCH" --rebase 2>&1; then
            log "Updated to $(git rev-parse --short HEAD)"
        else
            log "ERROR: Rebase failed, aborting rebase and using merge"
            git rebase --abort 2>/dev/null || true
            git pull origin "$BRANCH" --no-rebase 2>&1
            log "Merged to $(git rev-parse --short HEAD)"
        fi
    else
        log "Already up to date"
    fi

    # Restore stashed changes
    if [ "$STASHED" = true ]; then
        if git stash pop -q 2>/dev/null; then
            log "Restored stashed changes"
        else
            log "WARNING: Stash pop had conflicts, kept in stash"
        fi
    fi
}

do_push() {
    local commit_msg
    local ts
    ts=$(date "+%Y-%m-%d %H:%M")
    commit_msg="${1:-auto-sync: EC2 changes $ts}"

    log "=== PUSH: Committing and pushing ==="
    cd "$REPO_DIR"

    if [ -z "$(git status -s)" ]; then
        log "No changes to commit"
        return 0
    fi

    # Pull first to minimize conflicts
    git fetch origin "$BRANCH"
    BEHIND=$(git rev-list --count HEAD.."origin/$BRANCH" 2>/dev/null || echo "0")
    if [ "$BEHIND" -gt 0 ]; then
        log "Pulling $BEHIND incoming commits first..."
        git stash push -m "pre-push-stash" -q 2>/dev/null || true
        git pull origin "$BRANCH" --rebase 2>&1
        git stash pop -q 2>/dev/null || true
    fi

    # Stage changes (git add -A respects .gitignore)
    git add -A

    # Commit
    git commit -m "$commit_msg

Co-Authored-By: Clawdbot <clawdbot@ec2>" 2>/dev/null || {
        log "Nothing to commit after staging"
        return 0
    }
    log "Committed: $(git rev-parse --short HEAD)"

    # Push
    if git push origin "$BRANCH" 2>&1; then
        log "Pushed successfully"
    else
        log "ERROR: Push failed — likely needs manual conflict resolution"
        return 1
    fi
}

do_status() {
    cd "$REPO_DIR"
    git fetch origin "$BRANCH" 2>/dev/null

    LOCAL=$(git rev-parse --short HEAD)
    REMOTE=$(git rev-parse --short "origin/$BRANCH" 2>/dev/null || echo "???")
    UNCOMMITTED=$(git status -s | wc -l | xargs)
    BEHIND=$(git rev-list --count HEAD.."origin/$BRANCH" 2>/dev/null || echo "0")
    AHEAD=$(git rev-list --count "origin/$BRANCH"..HEAD 2>/dev/null || echo "0")

    local ts
    ts=$(date "+%Y-%m-%d %H:%M")
    echo "EC2 Sync Status — $ts"
    echo "  EC2:    $LOCAL | GitHub: $REMOTE"
    echo "  Ahead:  $AHEAD | Behind: $BEHIND | Uncommitted: $UNCOMMITTED"
    if [ "$LOCAL" = "$REMOTE" ] && [ "$UNCOMMITTED" -eq 0 ]; then
        echo "  Status: IN SYNC"
    else
        echo "  Status: DRIFT DETECTED"
    fi
}

do_auto_sync() {
    log "=== AUTO-SYNC ==="

    # Pull first
    do_pull

    # Check for uncommitted changes
    cd "$REPO_DIR"
    if [ -n "$(git status -s)" ]; then
        UNCOMMITTED=$(git status -s | wc -l | xargs)
        log "Found $UNCOMMITTED uncommitted changes, auto-committing..."
        do_push
    fi
}

acquire_lock

case "${1:-}" in
    --pull)      do_pull ;;
    --push)      do_push "${2:-}" ;;
    --status)    do_status ;;
    --auto-sync) do_auto_sync ;;
    *)
        echo "Usage: $0 [--pull|--push 'msg'|--status|--auto-sync]"
        exit 1
        ;;
esac
