#!/bin/bash
###############################################################################
# auto_save.sh - Automatic Session Progress Saver
#
# PURPOSE: Save development progress every 30 minutes to prevent data loss
# USAGE: ./auto_save.sh (run once, then repeats every 30 min)
# SETUP: chmod +x auto_save.sh && ./auto_save.sh &
#
# WHAT IT DOES:
# - Checks for uncommitted changes
# - Auto-commits with timestamp
# - Updates session log
# - Runs in background continuously
#
# NOTE: Review auto-commits and amend/squash before pushing to main
###############################################################################

# Configuration
INTERVAL=1800  # 30 minutes in seconds
REPO_DIR="/Users/williammarceaujr./dev-sandbox"
SESSION_LOG=".claude/SESSION_LOG.md"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to perform auto-save
auto_save() {
    cd "$REPO_DIR" || exit 1
    
    timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    date_only=$(date +"%Y-%m-%d")
    time_only=$(date +"%I:%M %p")
    
    # Check if there are changes
    if [[ -n $(git status -s) ]]; then
        echo -e "${YELLOW}[${timestamp}] Changes detected, auto-saving...${NC}"
        
        # Stage all changes
        git add -A
        
        # Create commit message
        commit_msg="auto-save: Progress checkpoint at ${timestamp}

Files modified:
$(git status -s | head -10)

Auto-saved by session monitoring script.
Review and amend this commit message before pushing to remote."
        
        # Commit
        if git commit -m "$commit_msg"; then
            echo -e "${GREEN}✓ Auto-saved successfully at ${timestamp}${NC}"
            
            # Update session log with timestamp
            if [ -f "$SESSION_LOG" ]; then
                echo "" >> "$SESSION_LOG"
                echo "**Auto-save checkpoint:** ${time_only} - Working on fitness influencer AI optimizations" >> "$SESSION_LOG"
            fi
            
            # Show summary
            echo "  Files changed: $(git diff HEAD~1 --stat | tail -1)"
        else
            echo "⚠ No changes to commit (possibly already committed)"
        fi
    else
        echo "[${timestamp}] No changes detected, skipping auto-save"
    fi
    
    echo ""
}

# Function to run continuously
run_continuous() {
    echo "=========================================="
    echo "Auto-Save Monitor Started"
    echo "=========================================="
    echo "Repository: $REPO_DIR"
    echo "Interval: Every 30 minutes"
    echo "Press Ctrl+C to stop"
    echo "=========================================="
    echo ""
    
    while true; do
        auto_save
        
        # Wait for next interval
        echo "Next auto-save in 30 minutes..."
        sleep $INTERVAL
    done
}

# Main execution
case "${1:-continuous}" in
    once)
        # Run once and exit
        auto_save
        ;;
    continuous)
        # Run continuously in loop
        run_continuous
        ;;
    test)
        # Test mode - 1 minute interval
        INTERVAL=60
        echo "TEST MODE: Auto-saving every 60 seconds"
        run_continuous
        ;;
    *)
        echo "Usage: $0 {once|continuous|test}"
        echo "  once       - Save once and exit"
        echo "  continuous - Keep running (default)"
        echo "  test       - Test mode (1 min intervals)"
        exit 1
        ;;
esac