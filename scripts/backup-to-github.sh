#!/bin/bash
# backup-to-github.sh — Automated backup of EC2 workspace to GitHub
# Runs on schedule, commits any changes, pushes to GitHub

set -e
cd /home/clawdbot/dev-sandbox

# Only proceed if there are changes
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
    echo "$(date): No changes to backup"
    exit 0
fi

# Add all changes (respecting .gitignore)
git add -A

# Commit with timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
git commit -m "backup: auto-save ${TIMESTAMP}" || exit 0

# Push to GitHub
git push origin main

echo "$(date): Backup complete"
