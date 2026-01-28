#!/bin/bash
#
# Daily Follow-Up Automation Script
# Run via cron at 9 AM daily
#
# This script:
# 1. Checks lead inventory and sends alerts if low
# 2. Enrolls new Apollo B2B leads into follow-up sequence
# 3. Processes due follow-up touchpoints for all sequences
# 4. Updates campaign analytics

cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper || exit 1

echo "====================================================="
echo "Daily Follow-Up Automation - $(date)"
echo "====================================================="

# Step 0: Check lead inventory and alert if low
echo ""
echo "Step 0: Checking lead inventory..."
/opt/anaconda3/bin/python -m src.lead_monitor check --alert 2>/dev/null || echo "Lead monitor check skipped"

# Save inventory snapshot for trend tracking
/opt/anaconda3/bin/python -m src.lead_monitor snapshot 2>/dev/null || echo "Snapshot skipped"

# Step 1: Enroll new Apollo leads (limit to batch size)
APOLLO_BATCH_SIZE=${APOLLO_BATCH_SIZE:-20}  # Default 20 new leads per day (increased)
echo ""
echo "Step 1: Enrolling new Apollo B2B leads (limit: $APOLLO_BATCH_SIZE)..."
/opt/anaconda3/bin/python -m src.apollo_leads_loader enroll --limit "$APOLLO_BATCH_SIZE" --for-real 2>/dev/null || echo "Apollo enrollment skipped"

# Step 2: Process due follow-up touchpoints
echo ""
echo "Step 2: Processing due follow-up messages..."
/opt/anaconda3/bin/python -m src.follow_up_sequence process --for-real 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Follow-up processing complete"
else
    echo "⚠️ Follow-up processing had issues"
fi

# Step 3: Sync responses to templates and update analytics
echo ""
echo "Step 3: Syncing responses and updating analytics..."
/opt/anaconda3/bin/python -m src.response_tracker sync 2>/dev/null || echo "Response sync skipped"
/opt/anaconda3/bin/python -m src.campaign_analytics update 2>/dev/null || echo "Analytics update skipped"

# Check for concerning metrics
echo ""
echo "Checking for alerts..."
/opt/anaconda3/bin/python -m src.response_tracker alert 2>/dev/null || echo "Alert check skipped"

# Step 4: Show current status
echo ""
echo "Step 4: Current sequence status:"
/opt/anaconda3/bin/python -m src.follow_up_sequence status 2>/dev/null || echo "Status check failed"

# Step 5: Show lead inventory forecast
echo ""
echo "Step 5: Lead inventory status:"
/opt/anaconda3/bin/python -m src.lead_monitor status 2>/dev/null || echo "Lead status skipped"

echo ""
echo "====================================================="
echo "Daily automation complete - $(date)"
echo "====================================================="
