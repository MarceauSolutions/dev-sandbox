#!/bin/bash
# verify_clawdbot_retired.sh — One-shot check that the 2026-05-16 cleanup held.
#
# Runs ON the EC2 instance. Checks:
#   1. clawdbot.service and ralph-webhook.service are inactive
#   2. No clawdbot/app or ralph processes are running
#   3. Panacea logs have no 401 / third-party / getUpdates-conflict errors
#   4. No EOD/Accountability workflows reappeared in n8n
#
# Sends a summary to William's Telegram either way (success or failure).
# Designed to be scheduled in ec2-user's crontab.

set +e  # we want to collect all results, not exit early
cd "${REPO_ROOT:-/home/clawdbot/dev-sandbox}"

FAIL=0
LINES=("Clawdbot retirement check — $(date -u '+%Y-%m-%d %H:%M UTC')")
LINES+=("")

# Check 1 — services inactive
CLAW=$(sudo systemctl is-active clawdbot 2>&1)
RALPH=$(sudo systemctl is-active ralph-webhook 2>&1)
if [ "$CLAW" = "inactive" ] && [ "$RALPH" = "inactive" ]; then
    LINES+=("✓ clawdbot.service: $CLAW")
    LINES+=("✓ ralph-webhook.service: $RALPH")
else
    LINES+=("✗ clawdbot.service: $CLAW (expected: inactive)")
    LINES+=("✗ ralph-webhook.service: $RALPH (expected: inactive)")
    FAIL=1
fi

# Check 2 — no clawdbot or ralph processes
ZOMBIE=$(ps aux | grep -E 'clawdbot/app|/scripts/webhook_server.py' | grep -v grep | head -3)
if [ -z "$ZOMBIE" ]; then
    LINES+=("✓ no clawdbot/ralph processes running")
else
    LINES+=("✗ found stowaway processes:")
    LINES+=("$ZOMBIE")
    FAIL=1
fi

# Check 3 — Panacea logs clean for 7 days (specific error patterns, not millisecond timestamps)
ERR_COUNT=$(sudo journalctl -u panacea --since '7 days ago' 2>/dev/null \
    | grep -iE 'Failed to authenticate|Invalid authentication|authentication_error|third-party|getUpdates conflict' \
    | wc -l | tr -d ' ')
if [ "$ERR_COUNT" = "0" ]; then
    LINES+=("✓ Panacea logs clean (no 401 / third-party / conflict errors in 7 days)")
else
    LINES+=("✗ Panacea logs show $ERR_COUNT suspicious lines in 7 days")
    FAIL=1
fi

# Check 4 — accountability workflows still deleted
GHOST=$(sqlite3 /home/ec2-user/.n8n/database.sqlite "SELECT name FROM workflow_entity WHERE name LIKE '%Accountab%' OR name LIKE '%EOD%';" 2>/dev/null)
if [ -z "$GHOST" ]; then
    LINES+=("✓ EOD/Accountability workflows still deleted")
else
    LINES+=("✗ accountability workflows reappeared:")
    LINES+=("$GHOST")
    FAIL=1
fi

LINES+=("")
if [ "$FAIL" = "0" ]; then
    LINES+=("All clear. Cleanup held.")
else
    LINES+=("FAILED checks. See HANDOFF.md for recovery (memory: reference_ec2_services.md).")
fi

SUMMARY=$(printf "%s\n" "${LINES[@]}")
echo "$SUMMARY"

# Send to Telegram (always send so William sees the heartbeat, not just on failure)
TG_TOKEN=$(grep '^TELEGRAM_BOT_TOKEN=' /home/clawdbot/dev-sandbox/.env | cut -d= -f2-)
CHAT_ID="${TELEGRAM_CHAT_ID:-5692454753}"
curl -sS -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${CHAT_ID}" \
    --data-urlencode "text=${SUMMARY}" \
    > /dev/null
