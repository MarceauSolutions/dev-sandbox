#!/bin/bash
#
# Daily Follow-Up Automation Script
#
# This script runs the automated follow-up sequences for SMS campaigns.
# It should be run once per day via cron to send scheduled follow-up messages.
#
# Cron setup:
#   0 9 * * * /path/to/daily_followup_cron.sh >> /path/to/logs/followup.log 2>&1
#
# This runs at 9 AM every day and logs output.

# Set working directory
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper || exit 1

# Activate virtual environment if needed
# source venv/bin/activate

echo "====================================================="
echo "Daily Follow-Up Automation - $(date)"
echo "====================================================="

# Process due follow-up touchpoints
echo ""
echo "Processing due follow-up messages..."
python -m src.follow_up_sequence process --for-real

if [ $? -eq 0 ]; then
    echo "✅ Follow-up processing complete"
else
    echo "❌ Follow-up processing failed"
    exit 1
fi

# Check status
echo ""
echo "Current sequence status:"
python -m src.follow_up_sequence status

# Optional: Scan Voice AI logs for new leads
echo ""
echo "Scanning Voice AI for new leads..."
cd /Users/williammarceaujr./dev-sandbox/projects/ai-customer-service || exit 1
python -m src.auto_lead_detector scan --create-tasks --recent 24

echo ""
echo "====================================================="
echo "Daily automation complete - $(date)"
echo "====================================================="
