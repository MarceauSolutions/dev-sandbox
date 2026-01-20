#!/bin/bash

# Update cron jobs to use correct path
# From: /Users/williammarceaujr./dev-sandbox/projects/social-media-automation
# To: /Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/social-media-automation

echo "Backing up current crontab..."
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt

echo "Updating cron jobs with correct path..."

# Export current crontab, update paths, and reinstall
crontab -l | sed 's|/Users/williammarceaujr./dev-sandbox/projects/social-media-automation|/Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/social-media-automation|g' | crontab -

echo "Cron jobs updated successfully!"
echo ""
echo "New cron schedule:"
crontab -l | grep "social-media"
