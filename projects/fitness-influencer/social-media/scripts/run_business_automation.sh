#!/bin/bash
#
# run_business_automation.sh - Daily automation runner for multi-business posting
#
# Run this script daily via cron to:
# 1. Generate content for upcoming days
# 2. Schedule posts at optimal times
# 3. Process the posting queue
#
# Cron example (run at 8am EST daily):
#   0 8 * * * /Users/williammarceaujr./dev-sandbox/projects/social-media-automation/scripts/run_business_automation.sh >> /tmp/business_automation.log 2>&1
#

# Configuration
PROJECT_DIR="/Users/williammarceaujr./dev-sandbox/projects/social-media-automation"
LOG_FILE="/tmp/business_automation_$(date +%Y%m%d).log"

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Load environment variables
source /Users/williammarceaujr./dev-sandbox/.env 2>/dev/null || true

echo "=========================================="
echo "Business Automation Run: $(date)"
echo "=========================================="

# Run the daily automation
python -m src.business_scheduler daily-run --days 3

# Log completion
echo ""
echo "Automation complete at $(date)"
echo "=========================================="
