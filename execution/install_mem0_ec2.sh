#!/bin/bash
#
# Install Mem0 API on EC2
#
# This script installs and configures the Mem0 REST API as a systemd service
# on the EC2 instance. It's optimized for low-memory environments.
#
# Usage:
#   # On your local machine:
#   scp execution/install_mem0_ec2.sh ec2:/home/ubuntu/
#   ssh ec2 'bash /home/ubuntu/install_mem0_ec2.sh'
#
# Author: William Marceau Jr.
# Created: 2026-02-15

set -e  # Exit on error

echo "=========================================="
echo "Installing Mem0 API on EC2"
echo "=========================================="
echo ""

# Check if running on EC2
if [[ ! -f /home/ubuntu/dev-sandbox/.env ]]; then
    echo "ERROR: /home/ubuntu/dev-sandbox/.env not found"
    echo "Are you running this on the EC2 instance?"
    exit 1
fi

# Check for OPENAI_API_KEY
if ! grep -q "OPENAI_API_KEY" /home/ubuntu/dev-sandbox/.env; then
    echo "ERROR: OPENAI_API_KEY not found in .env"
    echo "Please add it to /home/ubuntu/dev-sandbox/.env"
    exit 1
fi

echo "[1/6] Installing Python dependencies..."
cd /home/ubuntu/dev-sandbox

# Install dependencies (use --user to avoid permission issues)
/usr/bin/python3 -m pip install --user --upgrade pip
/usr/bin/python3 -m pip install --user fastapi uvicorn mem0ai python-dotenv

echo ""
echo "[2/6] Creating Mem0 database directory..."
mkdir -p ~/.mem0/chroma_db
echo "  Created: ~/.mem0/chroma_db"

echo ""
echo "[3/6] Testing Mem0 API locally..."
# Quick test to ensure it starts
timeout 5 /usr/bin/python3 -m execution.mem0_api --port 5020 &
TEST_PID=$!
sleep 3

if kill -0 $TEST_PID 2>/dev/null; then
    echo "  Mem0 API started successfully (PID: $TEST_PID)"
    kill $TEST_PID
    wait $TEST_PID 2>/dev/null || true
else
    echo "  ERROR: Mem0 API failed to start"
    exit 1
fi

echo ""
echo "[4/6] Installing systemd service..."
sudo cp /home/ubuntu/dev-sandbox/execution/mem0-api.service /etc/systemd/system/
sudo systemctl daemon-reload

echo ""
echo "[5/6] Enabling and starting service..."
sudo systemctl enable mem0-api
sudo systemctl start mem0-api

echo ""
echo "[6/6] Checking service status..."
sleep 2
sudo systemctl status mem0-api --no-pager || true

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Service Commands:"
echo "  sudo systemctl status mem0-api    # Check status"
echo "  sudo systemctl restart mem0-api   # Restart service"
echo "  sudo systemctl stop mem0-api      # Stop service"
echo "  sudo journalctl -u mem0-api -f    # View logs"
echo ""
echo "API Endpoints:"
echo "  http://localhost:5020/health      # Health check"
echo "  http://localhost:5020/docs        # Interactive docs"
echo ""
echo "Test Commands:"
echo "  # Health check"
echo "  curl http://localhost:5020/health"
echo ""
echo "  # Add a memory"
echo "  curl -X POST http://localhost:5020/memory \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"agent_id\": \"claude-code\", \"content\": \"Test memory\", \"metadata\": {}}'"
echo ""
echo "  # Search memories"
echo "  curl 'http://localhost:5020/memory/search?q=test&agent_id=claude-code'"
echo ""
echo "=========================================="
