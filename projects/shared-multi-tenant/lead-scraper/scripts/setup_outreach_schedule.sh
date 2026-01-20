#!/bin/bash
# Setup cron jobs for automated outreach (similar to social media automation)
#
# Usage: bash setup_outreach_schedule.sh

PROJECT_PATH="/Users/williammarceaujr./dev-sandbox/projects/lead-scraper"
PYTHON_PATH="/opt/anaconda3/bin/python"

echo "Setting up automated outreach schedule..."
echo ""
echo "Schedule: 8 AM, 9 AM, 10 AM, 11 AM, 1 PM, 2 PM, 3 PM, 4 PM EST"
echo ""
echo "Businesses:"
echo "  - marceau-solutions: 20 emails/day + 10 SMS/day"
echo "  - swflorida-hvac: 15 emails/day + 10 SMS/day"
echo ""

# Remove any existing outreach cron jobs
if crontab -l 2>/dev/null | grep -q "outreach_scheduler"; then
    echo "Removing existing outreach cron jobs..."
    crontab -l | grep -v "outreach_scheduler\|Outreach Automation" | crontab -
fi

# Add header
(crontab -l 2>/dev/null; echo "") | crontab -
(crontab -l 2>/dev/null; echo "# Outreach Automation - Multi-Business Email/SMS") | crontab -
(crontab -l 2>/dev/null; echo "# Runs 8x daily: 8 AM, 9 AM, 10 AM, 11 AM, 1 PM, 2 PM, 3 PM, 4 PM EST") | crontab -
(crontab -l 2>/dev/null; echo "") | crontab -

# 6 AM - Daily run (schedule today's outreach for both businesses)
(crontab -l 2>/dev/null; echo "0 6 * * * cd $PROJECT_PATH && $PYTHON_PATH -m src.outreach_scheduler daily-run --business marceau-solutions >> $PROJECT_PATH/output/outreach.log 2>&1") | crontab -
(crontab -l 2>/dev/null; echo "5 6 * * * cd $PROJECT_PATH && $PYTHON_PATH -m src.outreach_scheduler daily-run --business swflorida-hvac >> $PROJECT_PATH/output/outreach.log 2>&1") | crontab -

# 8 AM - Process queue
(crontab -l 2>/dev/null; echo "0 8 * * * cd $PROJECT_PATH && $PYTHON_PATH -m src.outreach_scheduler process >> $PROJECT_PATH/output/outreach.log 2>&1") | crontab -

# 9 AM - Process queue (includes SMS batches)
(crontab -l 2>/dev/null; echo "0 9 * * * cd $PROJECT_PATH && $PYTHON_PATH -m src.outreach_scheduler process >> $PROJECT_PATH/output/outreach.log 2>&1") | crontab -

# 10 AM - Process queue
(crontab -l 2>/dev/null; echo "0 10 * * * cd $PROJECT_PATH && $PYTHON_PATH -m src.outreach_scheduler process >> $PROJECT_PATH/output/outreach.log 2>&1") | crontab -

# 11 AM - Process queue
(crontab -l 2>/dev/null; echo "0 11 * * * cd $PROJECT_PATH && $PYTHON_PATH -m src.outreach_scheduler process >> $PROJECT_PATH/output/outreach.log 2>&1") | crontab -

# 1 PM - Process queue
(crontab -l 2>/dev/null; echo "0 13 * * * cd $PROJECT_PATH && $PYTHON_PATH -m src.outreach_scheduler process >> $PROJECT_PATH/output/outreach.log 2>&1") | crontab -

# 2 PM - Process queue
(crontab -l 2>/dev/null; echo "0 14 * * * cd $PROJECT_PATH && $PYTHON_PATH -m src.outreach_scheduler process >> $PROJECT_PATH/output/outreach.log 2>&1") | crontab -

# 3 PM - Process queue (includes SMS batches)
(crontab -l 2>/dev/null; echo "0 15 * * * cd $PROJECT_PATH && $PYTHON_PATH -m src.outreach_scheduler process >> $PROJECT_PATH/output/outreach.log 2>&1") | crontab -

# 4 PM - Process queue
(crontab -l 2>/dev/null; echo "0 16 * * * cd $PROJECT_PATH && $PYTHON_PATH -m src.outreach_scheduler process >> $PROJECT_PATH/output/outreach.log 2>&1") | crontab -

echo "✅ Cron jobs created!"
echo ""
echo "Outreach schedule (8 times daily):"
echo "  - 6:00 AM EST: Schedule today's outreach for both businesses"
echo "  - 8:00 AM EST: Process queue (emails)"
echo "  - 9:00 AM EST: Process queue (emails + SMS)"
echo "  - 10:00 AM EST: Process queue (emails)"
echo "  - 11:00 AM EST: Process queue (emails)"
echo "  - 1:00 PM EST: Process queue (emails)"
echo "  - 2:00 PM EST: Process queue (emails)"
echo "  - 3:00 PM EST: Process queue (emails + SMS)"
echo "  - 4:00 PM EST: Process queue (emails)"
echo ""
echo "Daily outreach limits:"
echo "  - marceau-solutions: 20 emails + 10 SMS (Rule of 100 weekly)"
echo "  - swflorida-hvac: 15 emails + 10 SMS"
echo ""
echo "Logs: $PROJECT_PATH/output/outreach.log"
echo ""
echo "To verify:"
echo "  crontab -l | grep outreach_scheduler"
echo ""
echo "To test manually:"
echo "  cd $PROJECT_PATH"
echo "  python -m src.outreach_scheduler status"
echo "  python -m src.outreach_scheduler daily-run --business marceau-solutions"
echo ""
