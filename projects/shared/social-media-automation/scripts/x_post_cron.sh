#!/bin/bash
#
# X Platform Post Processing Script
# Run via cron every hour to process scheduled posts
#
# This script processes any posts that are due from the queue

cd /Users/williammarceaujr./dev-sandbox/projects/shared/social-media-automation || exit 1

echo "====================================================="
echo "X Post Processing - $(date)"
echo "====================================================="

# Process up to 5 ready posts
/opt/anaconda3/bin/python -m src.x_scheduler process --max 5 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ X posts processed successfully"
else
    echo "⚠️ X post processing had issues"
fi

echo ""
echo "Queue stats:"
/opt/anaconda3/bin/python -m src.x_scheduler stats 2>/dev/null

echo ""
echo "====================================================="
echo "X post processing complete - $(date)"
echo "====================================================="
