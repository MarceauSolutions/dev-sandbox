#!/bin/bash
# backup-to-github.sh — Safe automated backup of EC2 workspace to GitHub
# Runs hourly via cron. Uses git add -A (stages new + modified, respects .gitignore).
# .gitignore covers: .env, credentials.json, token_*.json, __pycache__, .tmp/

set -e
cd /home/clawdbot/dev-sandbox

# Stage all changes (respects .gitignore — safe for sensitive files)
git add -A

# Only proceed if there are staged changes
if git diff --cached --quiet; then
    exit 0
fi

# Commit with timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
git commit -m "backup: auto-save ${TIMESTAMP}"

# Push to GitHub
git push origin main

echo "$(date): Backup complete"
