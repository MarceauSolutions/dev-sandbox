#!/bin/bash
# Setup cron jobs for 9x daily posting: 6 AM - 10 PM (for marceau-solutions 25 posts/day)
#
# Usage: bash setup_posting_schedule.sh

PROJECT_PATH="/Users/williammarceaujr./dev-sandbox/projects/social-media-automation"
PYTHON_PATH="/opt/anaconda3/bin/python"

echo "Setting up social media posting schedule..."
echo ""
echo "Schedule: 6 AM, 8 AM, 10 AM, 12 PM, 2 PM, 4 PM, 6 PM, 8 PM, 10 PM EST"
echo "Posts per run: Varies by business (marceau-solutions: 25/day, others: 2/day)"
echo ""

# Remove any existing social media cron jobs
if crontab -l 2>/dev/null | grep -q "business_scheduler\|social-media"; then
    echo "Removing existing social media cron jobs..."
    crontab -l | grep -v "business_scheduler\|social-media\|Social Media" | crontab -
fi

# Add header
(crontab -l 2>/dev/null; echo "") | crontab -
(crontab -l 2>/dev/null; echo "# Social Media Automation - Multi-Business Posting") | crontab -
(crontab -l 2>/dev/null; echo "# Posts 9x daily: 6 AM, 8 AM, 10 AM, 12 PM, 2 PM, 4 PM, 6 PM, 8 PM, 10 PM EST") | crontab -
(crontab -l 2>/dev/null; echo "# marceau-solutions: 25 posts/day (all 9 slots)") | crontab -
(crontab -l 2>/dev/null; echo "# squarefoot-shipping, swflorida-hvac: 2 posts/day (9 AM, 3 PM)") | crontab -
(crontab -l 2>/dev/null; echo "") | crontab -

# 6 AM - Daily run (schedule posts for next 3 days + process queue)
(crontab -l 2>/dev/null; echo "0 6 * * * cd $PROJECT_PATH && $PYTHON_PATH -m src.business_scheduler daily-run >> $PROJECT_PATH/output/posting.log 2>&1") | crontab -

# 8 AM - Process queue
(crontab -l 2>/dev/null; echo "0 8 * * * cd $PROJECT_PATH && $PYTHON_PATH -m src.business_scheduler process >> $PROJECT_PATH/output/posting.log 2>&1") | crontab -

# 10 AM - Process queue
(crontab -l 2>/dev/null; echo "0 10 * * * cd $PROJECT_PATH && $PYTHON_PATH -m src.business_scheduler process >> $PROJECT_PATH/output/posting.log 2>&1") | crontab -

# 12 PM - Process queue
(crontab -l 2>/dev/null; echo "0 12 * * * cd $PROJECT_PATH && $PYTHON_PATH -m src.business_scheduler process >> $PROJECT_PATH/output/posting.log 2>&1") | crontab -

# 2 PM - Process queue
(crontab -l 2>/dev/null; echo "0 14 * * * cd $PROJECT_PATH && $PYTHON_PATH -m src.business_scheduler process >> $PROJECT_PATH/output/posting.log 2>&1") | crontab -

# 4 PM - Process queue
(crontab -l 2>/dev/null; echo "0 16 * * * cd $PROJECT_PATH && $PYTHON_PATH -m src.business_scheduler process >> $PROJECT_PATH/output/posting.log 2>&1") | crontab -

# 6 PM - Process queue
(crontab -l 2>/dev/null; echo "0 18 * * * cd $PROJECT_PATH && $PYTHON_PATH -m src.business_scheduler process >> $PROJECT_PATH/output/posting.log 2>&1") | crontab -

# 8 PM - Process queue
(crontab -l 2>/dev/null; echo "0 20 * * * cd $PROJECT_PATH && $PYTHON_PATH -m src.business_scheduler process >> $PROJECT_PATH/output/posting.log 2>&1") | crontab -

# 10 PM - Process queue
(crontab -l 2>/dev/null; echo "0 22 * * * cd $PROJECT_PATH && $PYTHON_PATH -m src.business_scheduler process >> $PROJECT_PATH/output/posting.log 2>&1") | crontab -

echo "✅ Cron jobs created!"
echo ""
echo "Posting schedule (9 times daily):"
echo "  - 6:00 AM EST: Schedule posts + send queued posts"
echo "  - 8:00 AM EST: Send queued posts"
echo "  - 10:00 AM EST: Send queued posts"
echo "  - 12:00 PM EST: Send queued posts"
echo "  - 2:00 PM EST: Send queued posts"
echo "  - 4:00 PM EST: Send queued posts"
echo "  - 6:00 PM EST: Send queued posts"
echo "  - 8:00 PM EST: Send queued posts"
echo "  - 10:00 PM EST: Send queued posts"
echo ""
echo "Business posting rates:"
echo "  - marceau-solutions: 25 posts/day (aggressive growth)"
echo "  - squarefoot-shipping: 2 posts/day"
echo "  - swflorida-hvac: 2 posts/day"
echo ""
echo "Logs: $PROJECT_PATH/output/posting.log"
echo ""
echo "To verify:"
echo "  crontab -l | grep business_scheduler"
echo ""
echo "To test manually:"
echo "  cd $PROJECT_PATH"
echo "  python -m src.business_scheduler process --max 5"
echo ""
