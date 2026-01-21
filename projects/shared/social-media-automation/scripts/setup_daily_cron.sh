#!/bin/bash
# Setup cron job for daily social media automation
#
# Runs once per day at 8 AM to schedule and post content for all businesses
#
# Usage: bash setup_daily_cron.sh

PROJECT_PATH="/Users/williammarceaujr./dev-sandbox/projects/social-media-automation"
PYTHON_PATH="/opt/anaconda3/bin/python"

echo "Setting up daily social media automation..."
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "business_scheduler daily-run"; then
    echo "⚠️  Cron job already exists for daily automation"
    echo ""
    crontab -l | grep "business_scheduler daily-run"
    echo ""
    read -p "Replace it? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
    crontab -l | grep -v "business_scheduler daily-run" | crontab -
fi

# Add cron job (runs at 8 AM daily)
(crontab -l 2>/dev/null; echo "# Social Media Daily Automation") | crontab -
(crontab -l 2>/dev/null; echo "0 8 * * * cd $PROJECT_PATH && $PYTHON_PATH -m src.business_scheduler daily-run >> $PROJECT_PATH/output/daily_cron.log 2>&1") | crontab -

echo "✅ Cron job created!"
echo ""
echo "Schedule: 8:00 AM daily"
echo "Action: Schedules posts + processes queue for all businesses"
echo "Logs: $PROJECT_PATH/output/daily_cron.log"
echo ""
echo "To verify: crontab -l"
echo "To test now: cd $PROJECT_PATH && python -m src.business_scheduler daily-run"
echo ""
