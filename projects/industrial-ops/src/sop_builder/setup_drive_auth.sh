#!/bin/bash
# setup_drive_auth.sh — One-time Google Drive OAuth setup for the SOP builder.
#
# Run this ONCE on the Mac. It will:
#   1. Trigger the Drive OAuth browser flow (you approve in browser)
#   2. Save the refresh token locally as token_drive_readonly.json
#   3. SCP that token to the EC2 instance so Panacea can use it from Telegram
#
# After this completes, you can ask Panacea via Telegram to build SOPs
# from any Drive folder, hands-free.

set -e

REPO_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
TOKEN_FILE="$REPO_ROOT/token_drive_readonly.json"
EC2_HOST="ec2-user@34.193.98.97"
EC2_KEY="$HOME/.ssh/marceau-ec2-key.pem"
EC2_PATH="/home/clawdbot/dev-sandbox/token_drive_readonly.json"

echo "→ Triggering Drive OAuth flow (a browser tab will open)..."
cd "$REPO_ROOT"
python3 -c "
import sys
sys.path.insert(0, 'projects/industrial-ops/src/sop_builder')
from drive_collector import get_drive_service
service = get_drive_service()
about = service.about().get(fields='user(emailAddress)').execute()
print(f'✓ Authorized as: {about[\"user\"][\"emailAddress\"]}')
"

if [ ! -f "$TOKEN_FILE" ]; then
    echo "ERROR: $TOKEN_FILE was not created. Auth may have failed."
    exit 1
fi

echo
echo "→ Token saved at $TOKEN_FILE"
echo "→ Copying token to EC2 ($EC2_HOST:$EC2_PATH)..."
scp -i "$EC2_KEY" "$TOKEN_FILE" "$EC2_HOST:$EC2_PATH"

echo
echo "✓ Setup complete. From now on you can:"
echo "  - Scan documents into a Drive folder via the Drive app on your phone"
echo "  - Tell Panacea on Telegram: 'Make me an SOP from <folder>, number WW-SOP-XXX, title <title>'"
echo "  - The PDF will arrive in your Telegram chat in 1-2 minutes"
