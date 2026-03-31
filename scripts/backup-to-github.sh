#!/bin/bash
# backup-to-github.sh — Safe automated backup of EC2 workspace to GitHub
# Runs hourly via cron. Only stages TRACKED files (never git add -A).
# Respects .gitignore — will never stage .env, token.json, *.db, etc.

set -e
cd /home/clawdbot/dev-sandbox

# Only stage tracked files that have changes (safe — never adds new files)
git add -u

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
