#!/bin/bash
# Client Performance Tracker — AI Services Trial Dashboard
# Launches at http://127.0.0.1:8795
cd "$(dirname "$0")/.."

if lsof -i :8795 > /dev/null 2>&1; then
    echo "Client Tracker already running → http://127.0.0.1:8795"
    open "http://127.0.0.1:8795"
    exit 0
fi

echo "Starting Client Performance Tracker → http://127.0.0.1:8795"
python projects/shared/client-performance-tracker/app.py &
sleep 2
open "http://127.0.0.1:8795"
