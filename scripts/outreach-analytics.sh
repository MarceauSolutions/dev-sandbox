#!/bin/bash
# Outreach Analytics Dashboard — AI Client Sprint
# Launches at http://127.0.0.1:8794
cd "$(dirname "$0")/.."

if lsof -i :8794 > /dev/null 2>&1; then
    echo "Outreach Analytics already running → http://127.0.0.1:8794"
    open "http://127.0.0.1:8794"
    exit 0
fi

echo "Starting Outreach Analytics → http://127.0.0.1:8794"
python projects/shared/outreach-analytics/app.py &
sleep 2
open "http://127.0.0.1:8794"
