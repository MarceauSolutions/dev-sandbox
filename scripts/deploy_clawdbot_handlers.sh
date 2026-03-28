#!/bin/bash
# Deploy PA Clawdbot handlers to EC2 as a microservice
# Run this from dev-sandbox root: bash scripts/deploy_clawdbot_handlers.sh
#
# Creates a FastAPI microservice on EC2 port 8786 that wraps clawdbot_handlers.py.
# The Clawdbot binary can call this endpoint to route Telegram messages.
#
# Prerequisites:
#   - SSH access to EC2 (marceau-ec2-key.pem)
#   - pipeline.db must be synced to EC2 (or the service calls Mac via SSH tunnel)

set -e

EC2_HOST="ec2-user@34.193.98.97"
EC2_KEY="$HOME/.ssh/marceau-ec2-key.pem"
REMOTE_DIR="/home/clawdbot/pa-handlers"

echo "=== Deploying PA Clawdbot Handlers to EC2 ==="

# 1. Create remote directory
ssh -i "$EC2_KEY" "$EC2_HOST" "sudo mkdir -p $REMOTE_DIR && sudo chown clawdbot:clawdbot $REMOTE_DIR"

# 2. Copy handler files
echo "Copying handler files..."
scp -i "$EC2_KEY" \
    projects/personal-assistant/src/clawdbot_handlers.py \
    projects/personal-assistant/src/goal_manager.py \
    projects/personal-assistant/src/goal_progress.py \
    "$EC2_HOST:/tmp/pa-handlers/"

ssh -i "$EC2_KEY" "$EC2_HOST" "sudo mv /tmp/pa-handlers/* $REMOTE_DIR/ && sudo chown clawdbot:clawdbot $REMOTE_DIR/*"

# 3. Copy pipeline.db for local access
echo "Syncing pipeline.db..."
scp -i "$EC2_KEY" \
    execution/pipeline.db \
    "$EC2_HOST:/tmp/pipeline.db"
ssh -i "$EC2_KEY" "$EC2_HOST" "sudo mv /tmp/pipeline.db $REMOTE_DIR/ && sudo chown clawdbot:clawdbot $REMOTE_DIR/pipeline.db"

# 4. Create the FastAPI wrapper
echo "Creating FastAPI service..."
ssh -i "$EC2_KEY" "$EC2_HOST" "sudo -u clawdbot cat > $REMOTE_DIR/service.py << 'PYEOF'
#!/usr/bin/env python3
\"\"\"PA Handler Service — wraps clawdbot_handlers.py as a FastAPI endpoint.\"\"\"
import sys
sys.path.insert(0, '/home/clawdbot/pa-handlers')
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title='PA Handlers')

class Message(BaseModel):
    text: str

@app.post('/route')
async def route(msg: Message):
    from clawdbot_handlers import route_message
    result = route_message(msg.text)
    return {'handled': result is not None, 'response': result or ''}

@app.get('/health')
async def health():
    return {'status': 'healthy', 'service': 'pa-handlers'}
PYEOF
"

echo ""
echo "=== Deploy complete ==="
echo "Start the service on EC2:"
echo "  ssh -i $EC2_KEY $EC2_HOST"
echo "  sudo -u clawdbot uvicorn service:app --host 127.0.0.1 --port 8786 --app-dir $REMOTE_DIR"
echo ""
echo "Test:"
echo "  curl -X POST http://localhost:8786/route -H 'Content-Type: application/json' -d '{\"text\": \"next\"}'"
