#!/bin/bash
# Setup cron job for automated social media posting (3 times daily)
#
# Schedule: 9 AM, 12 PM, 3 PM (EST)
# Posts to: Marceau Solutions X/Twitter account
#
# Usage: bash setup_cron_posting.sh

# Path to the project
PROJECT_PATH="/Users/williammarceaujr./dev-sandbox/projects/social-media-automation"

# Path to Python (use which python to find your Python path)
PYTHON_PATH="/opt/anaconda3/bin/python"

# Cron schedule:
# - 9 AM EST: 0 9 * * *
# - 12 PM EST: 0 12 * * *
# - 3 PM EST: 0 15 * * *

echo "Setting up automated social media posting..."
echo ""

# Check if cron jobs already exist
if crontab -l 2>/dev/null | grep -q "business_scheduler"; then
    echo "⚠️  Cron jobs already exist for social media posting"
    echo ""
    echo "Current cron jobs:"
    crontab -l | grep "business_scheduler"
    echo ""
    read -p "Do you want to replace them? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted. No changes made."
        exit 0
    fi

    # Remove existing jobs
    crontab -l | grep -v "business_scheduler" | crontab -
    echo "✅ Removed existing cron jobs"
fi

# Create new cron jobs
(crontab -l 2>/dev/null; echo "# Marceau Solutions Social Media Automation") | crontab -
(crontab -l 2>/dev/null; echo "# Post 3 times daily: 9 AM, 12 PM, 3 PM EST") | crontab -
(crontab -l 2>/dev/null; echo "") | crontab -

# 9 AM post
(crontab -l 2>/dev/null; echo "0 9 * * * cd $PROJECT_PATH && $PYTHON_PATH -m src.business_scheduler post --business marceausolutions --time 09:00 >> $PROJECT_PATH/output/cron.log 2>&1") | crontab -

# 12 PM post
(crontab -l 2>/dev/null; echo "0 12 * * * cd $PROJECT_PATH && $PYTHON_PATH -m src.business_scheduler post --business marceausolutions --time 12:00 >> $PROJECT_PATH/output/cron.log 2>&1") | crontab -

# 3 PM post
(crontab -l 2>/dev/null; echo "0 15 * * * cd $PROJECT_PATH && $PYTHON_PATH -m src.business_scheduler post --business marceausolutions --time 15:00 >> $PROJECT_PATH/output/cron.log 2>&1") | crontab -

echo ""
echo "✅ Cron jobs created successfully!"
echo ""
echo "Scheduled posts:"
echo "  - 9:00 AM EST (every day)"
echo "  - 12:00 PM EST (every day)"
echo "  - 3:00 PM EST (every day)"
echo ""
echo "Logs: $PROJECT_PATH/output/cron.log"
echo ""
echo "To verify:"
echo "  crontab -l"
echo ""
echo "To remove:"
echo "  crontab -l | grep -v 'business_scheduler' | crontab -"
echo ""
