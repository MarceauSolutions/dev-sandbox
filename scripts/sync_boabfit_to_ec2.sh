#!/bin/bash
# sync_boabfit_to_ec2.sh — Sync BoabFit + shared execution files to EC2
#
# Run this after modifying any BoabFit scripts or shared execution utilities
# that the n8n workflows depend on.
#
# Usage: ./scripts/sync_boabfit_to_ec2.sh

set -euo pipefail

SSH_KEY=~/.ssh/marceau-ec2-key.pem
EC2=ec2-user@34.193.98.97
BASE=/home/ec2-user/dev-sandbox
LOCAL_BASE=$(cd "$(dirname "$0")/.." && pwd)

echo "Syncing BoabFit files to EC2..."
echo "  Local: $LOCAL_BASE"
echo "  Remote: $EC2:$BASE"
echo ""

# Ensure directories exist
ssh -i $SSH_KEY $EC2 "mkdir -p $BASE/execution $BASE/projects/boabfit/src $BASE/projects/boabfit/clients $BASE/.tmp/questionnaires"

# Shared execution scripts (used by n8n workflows)
echo "Syncing execution scripts..."
for f in twilio_sms.py client_questionnaire.py questionnaire_response_watcher.py n8n_workflow_verifier.py twilio_inbox_monitor.py; do
    if [ -f "$LOCAL_BASE/execution/$f" ]; then
        scp -i $SSH_KEY "$LOCAL_BASE/execution/$f" "$EC2:$BASE/execution/"
        echo "  ✓ execution/$f"
    fi
done

# BoabFit project files
echo "Syncing BoabFit project files..."
for f in daily_checkin_sms.py sms_relay.py send_welcome_sms.py workout_plan.json drip_checker.py abandon_checker.py register_signup.py drip_mark_sent.py; do
    if [ -f "$LOCAL_BASE/projects/boabfit/src/$f" ]; then
        scp -i $SSH_KEY "$LOCAL_BASE/projects/boabfit/src/$f" "$EC2:$BASE/projects/boabfit/src/"
        echo "  ✓ projects/boabfit/src/$f"
    fi
done

scp -i $SSH_KEY "$LOCAL_BASE/projects/boabfit/clients/roster.json" "$EC2:$BASE/projects/boabfit/clients/"
echo "  ✓ projects/boabfit/clients/roster.json"

# .env (credentials)
scp -i $SSH_KEY "$LOCAL_BASE/.env" "$EC2:$BASE/.env"
echo "  ✓ .env"

# Questionnaire session data
if ls "$LOCAL_BASE/.tmp/questionnaires/"*.json &>/dev/null; then
    scp -i $SSH_KEY "$LOCAL_BASE/.tmp/questionnaires/"*.json "$EC2:$BASE/.tmp/questionnaires/"
    echo "  ✓ questionnaire sessions"
fi

echo ""
echo "Sync complete! Verifying..."

# Quick verification — dry run on EC2
ssh -i $SSH_KEY $EC2 "cd $BASE && python3 projects/boabfit/src/daily_checkin_sms.py --dry-run --day monday 2>&1 | head -5"
echo ""
echo "✅ EC2 sync verified."
