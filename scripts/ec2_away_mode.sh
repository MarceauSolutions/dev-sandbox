#!/bin/bash
# EC2 Away-Mode Automation — Runs critical business functions on EC2
# when William's Mac is off (hospital stay, travel, etc.)
#
# Install on EC2:
#   scp -i ~/.ssh/marceau-ec2-key.pem scripts/ec2_away_mode.sh ec2-user@34.193.98.97:/tmp/
#   ssh ec2-user@34.193.98.97 "sudo cp /tmp/ec2_away_mode.sh /home/clawdbot/scripts/ && sudo chmod +x /home/clawdbot/scripts/ec2_away_mode.sh && sudo chown clawdbot:clawdbot /home/clawdbot/scripts/ec2_away_mode.sh"
#
# Add to clawdbot crontab:
#   # Morning digest + decisions at 6:30am
#   30 6 * * * /home/clawdbot/scripts/ec2_away_mode.sh morning
#   # Deal monitoring every 30 min during business hours
#   */30 9-17 * * 1-5 /home/clawdbot/scripts/ec2_away_mode.sh monitor
#   # EOD summary at 5pm
#   0 17 * * 1-5 /home/clawdbot/scripts/ec2_away_mode.sh eod

PA_URL="http://127.0.0.1:8786"
TELEGRAM_TOKEN=$(grep TELEGRAM_BOT_TOKEN /home/clawdbot/.clawdbot/.env 2>/dev/null | cut -d= -f2)
CHAT_ID="5692454753"
LOG="/home/clawdbot/logs/away_mode.log"

send_telegram() {
    local msg="$1"
    if [ -n "$TELEGRAM_TOKEN" ] && [ -n "$msg" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
            -H "Content-Type: application/json" \
            -d "{\"chat_id\": \"${CHAT_ID}\", \"text\": \"${msg}\"}" > /dev/null 2>&1
    fi
}

call_pa() {
    local text="$1"
    curl -s -X POST "$PA_URL/route" \
        -H "Content-Type: application/json" \
        -d "{\"text\": \"$text\"}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('response',''))" 2>/dev/null
}

case "$1" in
    morning)
        echo "$(date): Running morning sequence" >> "$LOG"
        # Get goal progress
        goals=$(call_pa "goal progress")
        # Get decisions
        decisions=$(call_pa "decisions")
        # Get next action
        next=$(call_pa "next")

        msg="MORNING (EC2 away-mode)

${goals}

${decisions}

TOP PRIORITY:
$(echo "$next" | head -5)"

        send_telegram "$msg"
        echo "$(date): Morning sent" >> "$LOG"
        ;;

    monitor)
        echo "$(date): Running deal monitor" >> "$LOG"
        # Check for new responses
        responses=$(call_pa "did anyone respond to my emails today")
        if echo "$responses" | grep -qv "No new"; then
            send_telegram "NEW RESPONSES:
$responses"
            echo "$(date): New responses found" >> "$LOG"
        fi
        ;;

    eod)
        echo "$(date): Running EOD" >> "$LOG"
        goals=$(call_pa "goal progress")
        learned=$(call_pa "learned")

        msg="END OF DAY (EC2 away-mode)

${goals}

${learned}

Reply 'next' for tomorrow's top priority."

        send_telegram "$msg"
        echo "$(date): EOD sent" >> "$LOG"
        ;;

    *)
        echo "Usage: $0 {morning|monitor|eod}"
        echo "  morning - Send morning digest + decisions + next action"
        echo "  monitor - Check for new responses (every 30 min)"
        echo "  eod     - Send end-of-day summary"
        exit 1
        ;;
esac
