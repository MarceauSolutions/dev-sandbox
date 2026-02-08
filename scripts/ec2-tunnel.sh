#!/bin/bash
# EC2 n8n Tunnel Script
# Creates SSH tunnel to access n8n at http://localhost:5679

EC2_HOST="ec2"
LOCAL_PORT="5679"
REMOTE_PORT="5678"

# Check if tunnel already exists
if lsof -i :$LOCAL_PORT > /dev/null 2>&1; then
    echo "Tunnel already running on port $LOCAL_PORT"
    echo "Access n8n at: http://localhost:$LOCAL_PORT"
    exit 0
fi

# Start tunnel in background
echo "Starting SSH tunnel to EC2 n8n..."
ssh -f -N -L $LOCAL_PORT:localhost:$REMOTE_PORT $EC2_HOST

if [ $? -eq 0 ]; then
    echo "Tunnel established!"
    echo "Access n8n at: http://localhost:$LOCAL_PORT"
    echo ""
    echo "To stop tunnel: kill \$(lsof -t -i:$LOCAL_PORT)"
else
    echo "Failed to establish tunnel"
    exit 1
fi
