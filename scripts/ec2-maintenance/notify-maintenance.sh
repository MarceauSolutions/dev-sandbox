#!/bin/bash
###############################################################################
# notify-maintenance.sh - Maintenance Notification System
#
# Sends SMS/Email notifications before scheduled maintenance
#
# USAGE:
#   ./notify-maintenance.sh --now "EBS Encryption starting"
#   ./notify-maintenance.sh --schedule "2026-01-30 02:00" "EBS Encryption"
#   ./notify-maintenance.sh --complete "EBS Encryption complete. New IP: X.X.X.X"
#
# REQUIRES:
#   - TWILIO_* environment variables (from .env)
#   - SMTP_* environment variables (from .env)
#
# Created: 2026-01-29
###############################################################################

set -e

# Load environment variables
if [ -f "/Users/williammarceaujr./dev-sandbox/.env" ]; then
    export $(grep -E '^(TWILIO_|SMTP_|NOTIFICATION_)' /Users/williammarceaujr./dev-sandbox/.env | xargs)
fi

# Configuration
ADMIN_PHONE="${NOTIFICATION_PHONE:-+12393985676}"
ADMIN_EMAIL="${NOTIFICATION_EMAIL:-wmarceau@marceausolutions.com}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

send_sms() {
    local message="$1"

    if [ -z "$TWILIO_ACCOUNT_SID" ] || [ -z "$TWILIO_AUTH_TOKEN" ] || [ -z "$TWILIO_PHONE_NUMBER" ]; then
        echo -e "${YELLOW}WARNING: Twilio not configured, skipping SMS${NC}"
        return 0
    fi

    curl -s -X POST "https://api.twilio.com/2010-04-01/Accounts/${TWILIO_ACCOUNT_SID}/Messages.json" \
        --data-urlencode "To=${ADMIN_PHONE}" \
        --data-urlencode "From=${TWILIO_PHONE_NUMBER}" \
        --data-urlencode "Body=${message}" \
        -u "${TWILIO_ACCOUNT_SID}:${TWILIO_AUTH_TOKEN}" > /dev/null

    echo -e "${GREEN}✓ SMS sent to ${ADMIN_PHONE}${NC}"
}

send_email() {
    local subject="$1"
    local body="$2"

    # Use Python for SMTP (more reliable than bash solutions)
    python3 << EOF
import smtplib
from email.mime.text import MIMEText
import os

smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
smtp_port = int(os.getenv('SMTP_PORT', '587'))
smtp_user = os.getenv('SMTP_USERNAME', '')
smtp_pass = os.getenv('SMTP_PASSWORD', '')
recipient = os.getenv('NOTIFICATION_EMAIL', '${ADMIN_EMAIL}')

if not smtp_user or not smtp_pass:
    print("WARNING: SMTP not configured, skipping email")
    exit(0)

msg = MIMEText("""${body}

---
Sent by EC2 Maintenance System
""")
msg['Subject'] = "${subject}"
msg['From'] = smtp_user
msg['To'] = recipient

try:
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
    print("✓ Email sent to", recipient)
except Exception as e:
    print(f"Email failed: {e}")
EOF
}

show_usage() {
    echo "Usage: $0 [option] [arguments]"
    echo ""
    echo "Options:"
    echo "  --now MESSAGE           Send immediate notification"
    echo "  --schedule TIME DESC    Schedule maintenance reminder"
    echo "  --starting DESC         Notify maintenance is starting"
    echo "  --complete MESSAGE      Notify maintenance is complete"
    echo "  --test                  Test notification delivery"
    echo ""
    echo "Examples:"
    echo "  $0 --test"
    echo "  $0 --starting 'EBS Encryption'"
    echo "  $0 --complete 'EBS Encryption done. New IP: 34.193.98.97'"
}

case "${1:-}" in
    --now)
        MESSAGE="${2:-Maintenance notification}"
        echo "Sending immediate notification..."
        send_sms "[EC2] $MESSAGE"
        send_email "[EC2 Maintenance] Notification" "$MESSAGE"
        ;;

    --starting)
        DESC="${2:-Scheduled maintenance}"
        MESSAGE="🔧 MAINTENANCE STARTING: $DESC

Instance: i-01752306f94897d7d
Expected downtime: 10-15 minutes
Services affected: Clawdbot, Ralph, Voice AI

You will receive notification when complete."

        echo "Sending maintenance start notification..."
        send_sms "[EC2] 🔧 STARTING: $DESC - ~15 min downtime"
        send_email "[EC2] Maintenance Starting: $DESC" "$MESSAGE"
        ;;

    --complete)
        MESSAGE="${2:-Maintenance complete}"
        FULL_MESSAGE="✅ MAINTENANCE COMPLETE

$MESSAGE

Instance: i-01752306f94897d7d
Time: $(date '+%Y-%m-%d %H:%M:%S')

Please verify:
- SSH access works
- Clawdbot responds on Telegram
- Voice AI lines operational"

        echo "Sending completion notification..."
        send_sms "[EC2] ✅ COMPLETE: $MESSAGE"
        send_email "[EC2] Maintenance Complete" "$FULL_MESSAGE"
        ;;

    --schedule)
        TIME="${2:-tomorrow 02:00}"
        DESC="${3:-Scheduled maintenance}"

        echo "Scheduling maintenance reminder for: $TIME"
        echo ""
        echo "Add to crontab or calendar:"
        echo "  Maintenance: $DESC"
        echo "  Time: $TIME"
        echo ""

        # Create reminder file
        REMINDER_FILE="/tmp/maintenance-reminder-$(date +%Y%m%d).txt"
        cat > "$REMINDER_FILE" << REMINDER
SCHEDULED MAINTENANCE REMINDER

Description: $DESC
Scheduled: $TIME
Instance: i-01752306f94897d7d

Before starting:
1. Run dry-run: ./encrypt-ebs.sh --dry-run
2. Check no active tasks on EC2
3. Review MAINTENANCE-RUNBOOK.md

Commands:
  ./notify-maintenance.sh --starting "$DESC"
  ./encrypt-ebs.sh
  ./notify-maintenance.sh --complete "$DESC complete"
REMINDER

        echo "Reminder saved to: $REMINDER_FILE"
        cat "$REMINDER_FILE"
        ;;

    --test)
        echo "Testing notification delivery..."
        echo ""
        send_sms "[EC2 TEST] This is a test notification from maintenance system"
        send_email "[EC2 TEST] Notification Test" "This is a test of the EC2 maintenance notification system.\n\nIf you received this, notifications are working correctly."
        echo ""
        echo "Test complete. Check your phone and email."
        ;;

    --help|-h|"")
        show_usage
        ;;

    *)
        echo "Unknown option: $1"
        show_usage
        exit 1
        ;;
esac
