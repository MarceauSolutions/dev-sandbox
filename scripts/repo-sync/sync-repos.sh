#!/bin/bash
###############################################################################
# sync-repos.sh - Bidirectional sync between local and EC2 repositories
#
# Safely syncs repositories with conflict detection and resolution
#
# USAGE:
#   ./sync-repos.sh --status       # Check sync status (calls sync-status.sh)
#   ./sync-repos.sh --push         # Push local changes to EC2 + GitHub
#   ./sync-repos.sh --pull         # Pull from GitHub to local + EC2
#   ./sync-repos.sh --force-local  # Force EC2 to match local (after backup)
#   ./sync-repos.sh --force-ec2    # Force local to match EC2 (after backup)
#
# INTEGRATES WITH:
#   - EC2: /home/clawdbot/scripts/commit-and-push.sh (conflict prevention)
#   - docs/MULTI-AGENT-GIT-WORKFLOW.md (workflow documentation)
#
# Created: 2026-01-29
###############################################################################

set -e

# Configuration
EC2_USER="ec2-user"
EC2_HOST="${EC2_HOST:-34.193.98.97}"
EC2_KEY="${EC2_KEY:-$HOME/.ssh/marceau-ec2-key.pem}"
LOCAL_REPO="/Users/williammarceaujr./dev-sandbox"
EC2_REPO="/home/clawdbot/dev-sandbox"
BRANCH="main"
LOG_DIR="$LOCAL_REPO/.sync-logs"
LOG_FILE="$LOG_DIR/sync-$(date +%Y%m%d-%H%M%S).log"
SSH_CMD="ssh -i $EC2_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10"
# Need sudo -u clawdbot to access clawdbot's repo
EC2_GIT_PREFIX="sudo -u clawdbot"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

mkdir -p "$LOG_DIR"

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "$msg" | tee -a "$LOG_FILE"
}

error() {
    log "${RED}ERROR: $1${NC}"
    exit 1
}

success() {
    log "${GREEN}✓ $1${NC}"
}

warn() {
    log "${YELLOW}⚠ $1${NC}"
}

info() {
    log "${BLUE}INFO: $1${NC}"
}

# Get current EC2 IP from AWS
get_ec2_ip() {
    if command -v aws &> /dev/null; then
        IP=$(aws ec2 describe-instances \
            --instance-ids i-01752306f94897d7d \
            --query 'Reservations[0].Instances[0].PublicIpAddress' \
            --output text \
            --profile marceau-admin 2>/dev/null || echo "")
        if [ -n "$IP" ] && [ "$IP" != "None" ]; then
            EC2_HOST="$IP"
        fi
    fi
    info "EC2 Host: $EC2_HOST"
}

# Verify SSH connection to EC2
check_ec2_connection() {
    info "Checking EC2 connection..."
    if ! $SSH_CMD "$EC2_USER@$EC2_HOST" "echo 'connected'" &>/dev/null; then
        error "Cannot connect to EC2 at $EC2_HOST"
    fi
    success "EC2 connection OK"
}

# Create backup branch before any destructive operation
create_backup() {
    local location="$1"  # local or ec2
    local backup_name="backup-sync-$(date +%Y%m%d-%H%M%S)"

    if [ "$location" == "local" ]; then
        cd "$LOCAL_REPO"
        git branch "$backup_name"
        success "Local backup branch: $backup_name"
    else
        $SSH_CMD "$EC2_USER@$EC2_HOST" "$EC2_GIT_PREFIX bash -c 'cd $EC2_REPO && git branch $backup_name'"
        success "EC2 backup branch: $backup_name"
    fi
}

# Check for uncommitted changes
check_uncommitted() {
    local location="$1"

    if [ "$location" == "local" ]; then
        cd "$LOCAL_REPO"
        if [ -n "$(git status -s)" ]; then
            warn "Local has uncommitted changes:"
            git status -s | head -5
            return 1
        fi
    else
        EC2_STATUS=$($SSH_CMD "$EC2_USER@$EC2_HOST" "$EC2_GIT_PREFIX bash -c 'cd $EC2_REPO && git status -s'")
        if [ -n "$EC2_STATUS" ]; then
            warn "EC2 has uncommitted changes:"
            echo "$EC2_STATUS" | head -5
            return 1
        fi
    fi
    return 0
}

# Push local changes to GitHub and EC2
do_push() {
    log ""
    log "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    log "${CYAN}  PUSH: Local → GitHub → EC2${NC}"
    log "${CYAN}═══════════════════════════════════════════════════════════════${NC}"

    cd "$LOCAL_REPO"

    # Check for uncommitted local changes
    if ! check_uncommitted "local"; then
        read -p "Commit local changes first? (y/n): " COMMIT_LOCAL
        if [ "$COMMIT_LOCAL" == "y" ]; then
            git add -A
            read -p "Commit message: " COMMIT_MSG
            git commit -m "$COMMIT_MSG"
            success "Local changes committed"
        else
            error "Cannot push with uncommitted changes. Commit or stash first."
        fi
    fi

    # Create backup
    create_backup "local"

    # Fetch and check for remote changes
    info "Fetching from origin..."
    git fetch origin $BRANCH

    LOCAL_COMMIT=$(git rev-parse HEAD)
    REMOTE_COMMIT=$(git rev-parse origin/$BRANCH)

    if [ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]; then
        BEHIND=$(git rev-list --count HEAD..origin/$BRANCH)
        if [ "$BEHIND" -gt 0 ]; then
            warn "Local is behind origin by $BEHIND commits"
            info "Pulling with rebase..."
            git pull origin $BRANCH --rebase
            success "Rebased on origin/$BRANCH"
        fi
    fi

    # Dry run push
    info "Dry run push to origin..."
    if ! git push --dry-run origin $BRANCH 2>&1 | tee -a "$LOG_FILE"; then
        error "Push dry-run failed"
    fi

    # Actual push
    info "Pushing to origin..."
    git push origin $BRANCH
    success "Pushed to GitHub"

    # Now update EC2
    info "Updating EC2..."
    $SSH_CMD "$EC2_USER@$EC2_HOST" "sudo -u clawdbot bash -c '
        cd /home/clawdbot/dev-sandbox

        # Create backup branch
        git branch backup-sync-\$(date +%Y%m%d-%H%M%S) 2>/dev/null || true

        # Stash any local changes
        git stash push -m \"auto-stash before sync \$(date +%Y%m%d-%H%M%S)\" 2>/dev/null || true

        # Pull latest
        git fetch origin main
        git pull origin main --rebase

        echo \"EC2 updated to: \$(git rev-parse --short HEAD)\"
    '"

    success "EC2 updated"

    log ""
    log "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    log "${GREEN}  SYNC COMPLETE: Local → GitHub → EC2${NC}"
    log "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
}

# Pull from GitHub to local and EC2
do_pull() {
    log ""
    log "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    log "${CYAN}  PULL: GitHub → Local + EC2${NC}"
    log "${CYAN}═══════════════════════════════════════════════════════════════${NC}"

    cd "$LOCAL_REPO"

    # Check for uncommitted local changes
    if ! check_uncommitted "local"; then
        warn "Stashing local changes..."
        git stash push -m "auto-stash before pull $(date +%Y%m%d-%H%M%S)"
    fi

    # Create backup
    create_backup "local"

    # Pull from origin
    info "Pulling from origin..."
    git fetch origin $BRANCH
    git pull origin $BRANCH --rebase
    success "Local updated from GitHub"

    # Update EC2
    info "Updating EC2..."
    $SSH_CMD "$EC2_USER@$EC2_HOST" "sudo -u clawdbot bash -c '
        cd /home/clawdbot/dev-sandbox

        # Backup
        git branch backup-sync-\$(date +%Y%m%d-%H%M%S) 2>/dev/null || true

        # Stash local changes
        git stash push -m \"auto-stash before sync \$(date +%Y%m%d-%H%M%S)\" 2>/dev/null || true

        # Pull
        git fetch origin main
        git pull origin main --rebase

        echo \"EC2 updated to: \$(git rev-parse --short HEAD)\"
    '"

    success "EC2 updated"

    log ""
    log "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    log "${GREEN}  SYNC COMPLETE: GitHub → Local + EC2${NC}"
    log "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
}

# Force EC2 to match local (use with caution)
do_force_local() {
    log ""
    log "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    log "${YELLOW}  FORCE SYNC: EC2 will match Local (destructive)${NC}"
    log "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"

    read -p "This will OVERWRITE EC2 changes. Continue? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        log "Aborted."
        exit 0
    fi

    # Push local to GitHub first
    cd "$LOCAL_REPO"
    git push origin $BRANCH --force-with-lease

    # Create EC2 backup
    info "Creating EC2 backup..."
    $SSH_CMD "$EC2_USER@$EC2_HOST" "sudo -u clawdbot bash -c 'cd $EC2_REPO && git branch backup-before-force-\$(date +%Y%m%d-%H%M%S)'"

    # Force EC2 to match
    info "Forcing EC2 to match origin..."
    $SSH_CMD "$EC2_USER@$EC2_HOST" "sudo -u clawdbot bash -c '
        cd /home/clawdbot/dev-sandbox
        git fetch origin main
        git reset --hard origin/main
        echo \"EC2 reset to: \$(git rev-parse --short HEAD)\"
    '"

    success "EC2 now matches Local/GitHub"
}

# Force local to match EC2 (use with caution)
do_force_ec2() {
    log ""
    log "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    log "${YELLOW}  FORCE SYNC: Local will match EC2 (destructive)${NC}"
    log "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"

    read -p "This will OVERWRITE Local changes. Continue? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        log "Aborted."
        exit 0
    fi

    # First, push EC2 to GitHub
    info "Pushing EC2 changes to GitHub..."
    $SSH_CMD "$EC2_USER@$EC2_HOST" "sudo -u clawdbot bash -c 'cd $EC2_REPO && git push origin main --force-with-lease'"

    # Create local backup
    cd "$LOCAL_REPO"
    create_backup "local"

    # Force local to match
    info "Forcing local to match origin (from EC2)..."
    git fetch origin $BRANCH
    git reset --hard origin/$BRANCH

    success "Local now matches EC2/GitHub"
}

show_usage() {
    echo "Usage: $0 [option]"
    echo ""
    echo "Options:"
    echo "  --status       Check sync status across all locations"
    echo "  --push         Push local changes to GitHub and EC2"
    echo "  --pull         Pull from GitHub to local and EC2"
    echo "  --force-local  Force EC2 to match local (creates backup)"
    echo "  --force-ec2    Force local to match EC2 (creates backup)"
    echo ""
    echo "Examples:"
    echo "  $0 --status    # See what's out of sync"
    echo "  $0 --push      # After local development, sync everywhere"
    echo "  $0 --pull      # Get latest from GitHub/EC2"
    echo ""
    echo "Log files: $LOG_DIR/"
}

# Main
get_ec2_ip
check_ec2_connection

case "${1:-}" in
    --status)
        "$(dirname "$0")/sync-status.sh"
        ;;
    --push)
        do_push
        ;;
    --pull)
        do_pull
        ;;
    --force-local)
        do_force_local
        ;;
    --force-ec2)
        do_force_ec2
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
