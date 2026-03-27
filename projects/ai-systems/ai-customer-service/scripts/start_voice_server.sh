#!/bin/bash
# Voice AI Server - Quick Startup Script
#
# This is a simple wrapper around start_server.py for quick access.
# The Python script handles all the logic (health checks, ngrok, etc.)
#
# Usage:
#   ./scripts/start_voice_server.sh          # Start (or verify already running)
#   ./scripts/start_voice_server.sh restart  # Kill and restart

cd /Users/williammarceaujr./dev-sandbox/projects/ai-customer-service

if [ "$1" == "restart" ]; then
    python scripts/start_server.py --restart
else
    python scripts/start_server.py
fi
