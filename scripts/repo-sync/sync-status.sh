#!/bin/bash
###############################################################################
# sync-status.sh - Check sync status between local and EC2 repositories
#
# Shows whether local, EC2, and remote (GitHub) are in sync
#
# USAGE:
#   ./sync-status.sh              # Check dev-sandbox
#   ./sync-status.sh --all        # Check all tracked repos
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
SSH_OPTS="-i $EC2_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=5"
# Need sudo -u clawdbot to access clawdbot's repo
SSH_GIT_CMD="sudo -u clawdbot bash -c"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Get current EC2 IP from AWS if not set
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
}

check_repo_sync() {
    local repo_name="$1"
    local local_path="$2"
    local ec2_path="$3"

    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  Repository: ${repo_name}${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"

    # Check if local repo exists
    if [ ! -d "$local_path/.git" ]; then
        echo -e "${RED}✗ Local repo not found: $local_path${NC}"
        return 1
    fi

    cd "$local_path"

    # Get local commit info
    LOCAL_COMMIT=$(git rev-parse HEAD 2>/dev/null)
    LOCAL_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
    LOCAL_SHORT="${LOCAL_COMMIT:0:7}"

    echo -e "\n${BLUE}Local ($(hostname)):${NC}"
    echo -e "  Branch: $LOCAL_BRANCH"
    echo -e "  Commit: $LOCAL_SHORT"
    echo -e "  Status: $(git status -s | wc -l | tr -d ' ') uncommitted changes"

    # Check if there are uncommitted changes
    if [ -n "$(git status -s)" ]; then
        echo -e "  ${YELLOW}⚠ Has uncommitted changes:${NC}"
        git status -s | head -5 | sed 's/^/    /'
        [ $(git status -s | wc -l) -gt 5 ] && echo "    ... and more"
    fi

    # Fetch from origin (quietly)
    git fetch origin "$LOCAL_BRANCH" 2>/dev/null || true

    # Get remote commit
    REMOTE_COMMIT=$(git rev-parse "origin/$LOCAL_BRANCH" 2>/dev/null || echo "unknown")
    REMOTE_SHORT="${REMOTE_COMMIT:0:7}"

    echo -e "\n${BLUE}GitHub (origin/$LOCAL_BRANCH):${NC}"
    echo -e "  Commit: $REMOTE_SHORT"

    # Check local vs remote
    if [ "$LOCAL_COMMIT" == "$REMOTE_COMMIT" ]; then
        echo -e "  ${GREEN}✓ In sync with local${NC}"
    else
        BEHIND=$(git rev-list --count HEAD..origin/$LOCAL_BRANCH 2>/dev/null || echo "?")
        AHEAD=$(git rev-list --count origin/$LOCAL_BRANCH..HEAD 2>/dev/null || echo "?")
        echo -e "  ${YELLOW}⚠ Local is $AHEAD ahead, $BEHIND behind${NC}"
    fi

    # Check EC2
    echo -e "\n${BLUE}EC2 ($EC2_HOST):${NC}"
    EC2_COMMIT=$(ssh $SSH_OPTS "$EC2_USER@$EC2_HOST" \
        "$SSH_GIT_CMD 'cd $ec2_path && git rev-parse HEAD'" 2>/dev/null || echo "unreachable")

    if [ "$EC2_COMMIT" == "unreachable" ]; then
        echo -e "  ${RED}✗ Cannot connect to EC2${NC}"
    else
        EC2_SHORT="${EC2_COMMIT:0:7}"
        echo -e "  Commit: $EC2_SHORT"

        # Check EC2 uncommitted changes
        EC2_STATUS=$(ssh $SSH_OPTS "$EC2_USER@$EC2_HOST" \
            "$SSH_GIT_CMD 'cd $ec2_path && git status -s | wc -l'" 2>/dev/null || echo "?")
        echo -e "  Status: $EC2_STATUS uncommitted changes"

        # Compare all three
        if [ "$LOCAL_COMMIT" == "$EC2_COMMIT" ] && [ "$EC2_COMMIT" == "$REMOTE_COMMIT" ]; then
            echo -e "\n${GREEN}✓ ALL IN SYNC: Local = EC2 = GitHub${NC}"
        elif [ "$LOCAL_COMMIT" == "$EC2_COMMIT" ]; then
            echo -e "\n${YELLOW}⚠ Local = EC2, but GitHub differs${NC}"
            echo -e "  Run: git push origin $LOCAL_BRANCH"
        elif [ "$EC2_COMMIT" == "$REMOTE_COMMIT" ]; then
            echo -e "\n${YELLOW}⚠ EC2 = GitHub, but Local differs${NC}"
            echo -e "  Run: ./sync-repos.sh --pull"
        elif [ "$LOCAL_COMMIT" == "$REMOTE_COMMIT" ]; then
            echo -e "\n${YELLOW}⚠ Local = GitHub, but EC2 differs${NC}"
            echo -e "  EC2 has unpushed changes. Run on EC2: git push"
        else
            echo -e "\n${RED}✗ ALL THREE DIFFER - Manual review needed${NC}"
            echo -e "  Local:  $LOCAL_SHORT"
            echo -e "  EC2:    $EC2_SHORT"
            echo -e "  GitHub: $REMOTE_SHORT"
        fi
    fi
}

show_summary() {
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}                    SYNC STATUS SUMMARY${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "  Checked at: $(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "  EC2 Host: $EC2_HOST"
    echo ""
    echo -e "${BLUE}Quick Commands:${NC}"
    echo "  ./sync-repos.sh --push     # Push local changes to EC2 + GitHub"
    echo "  ./sync-repos.sh --pull     # Pull EC2/GitHub changes to local"
    echo "  ./sync-repos.sh --force-local  # Force EC2 to match local"
    echo ""
}

# Main
get_ec2_ip

case "${1:-}" in
    --all)
        check_repo_sync "dev-sandbox" "$LOCAL_REPO" "$EC2_REPO"
        # Add other repos here as needed
        show_summary
        ;;
    --help|-h)
        echo "Usage: $0 [--all]"
        echo ""
        echo "Options:"
        echo "  (none)   Check dev-sandbox sync status"
        echo "  --all    Check all tracked repositories"
        ;;
    *)
        check_repo_sync "dev-sandbox" "$LOCAL_REPO" "$EC2_REPO"
        show_summary
        ;;
esac
