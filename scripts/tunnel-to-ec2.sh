#!/bin/bash
# SSH Reverse Tunnel — Exposes Mac's PA API (port 5011) to EC2
#
# Run this on Mac. It creates a tunnel so EC2's localhost:5011
# reaches your Mac's Personal Assistant Flask app.
#
# Prerequisites:
#   1. PA Flask app running: cd projects/personal-assistant && python -m src.app
#   2. SSH key at ~/.ssh/marceau-ec2-key.pem
#
# Usage:
#   bash scripts/tunnel-to-ec2.sh          # Start tunnel (runs in foreground)
#   bash scripts/tunnel-to-ec2.sh &        # Start in background
#   ssh -O exit ec2-user@34.193.98.97      # Stop tunnel
#
# After tunnel is running, Clawdbot on EC2 can call:
#   curl http://localhost:5011/scheduler/today
#   curl http://localhost:5011/health

EC2_HOST="ec2-user@34.193.98.97"
EC2_KEY="$HOME/.ssh/marceau-ec2-key.pem"
LOCAL_PORT=5011

echo "Starting SSH reverse tunnel: EC2:${LOCAL_PORT} → Mac:${LOCAL_PORT}"
echo "Clawdbot will be able to reach PA API at localhost:${LOCAL_PORT}"
echo "Press Ctrl+C to stop."
echo ""

ssh -i "$EC2_KEY" \
    -R ${LOCAL_PORT}:localhost:${LOCAL_PORT} \
    -N -o ServerAliveInterval=60 -o ServerAliveCountMax=3 \
    "$EC2_HOST"
