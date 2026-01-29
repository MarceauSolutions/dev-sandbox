#!/bin/bash
#
# Weekly Optimization Review Script
# Run via cron on Mondays at 9 AM
#
# This script:
# 1. Generates template performance report
# 2. Identifies winning/losing templates
# 3. Recommends allocation changes

cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper || exit 1

echo "====================================================="
echo "Weekly Optimization Review - $(date)"
echo "====================================================="

# Step 1: Generate optimizer status report
echo ""
echo "Step 1: Template performance analysis..."
/opt/anaconda3/bin/python -m src.outreach_optimizer status 2>/dev/null || echo "Optimizer status failed"

# Step 2: Get recommended allocation for next week
echo ""
echo "Step 2: Recommended allocation for next 100 sends..."
/opt/anaconda3/bin/python -m src.outreach_optimizer recommend --limit 100 --source apollo 2>/dev/null || echo "Apollo recommendation failed"

echo ""
/opt/anaconda3/bin/python -m src.outreach_optimizer recommend --limit 100 --source google_places 2>/dev/null || echo "Google Places recommendation failed"

# Step 3: Show capacity
echo ""
echo "Step 3: Daily outreach capacity:"
/opt/anaconda3/bin/python -m src.outreach_optimizer capacity 2>/dev/null || echo "Capacity check failed"

echo ""
echo "====================================================="
echo "Weekly review complete - $(date)"
echo "====================================================="
