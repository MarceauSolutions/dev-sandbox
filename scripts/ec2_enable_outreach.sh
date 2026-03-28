#!/bin/bash
# Enable or disable real outreach on EC2
# Usage:
#   bash scripts/ec2_enable_outreach.sh enable   # Start sending real emails
#   bash scripts/ec2_enable_outreach.sh disable   # Switch back to dry-run
#   bash scripts/ec2_enable_outreach.sh status    # Check current mode

EC2_HOST="ec2-user@34.193.98.97"
EC2_KEY="$HOME/.ssh/marceau-ec2-key.pem"

case "$1" in
    enable)
        ssh -i "$EC2_KEY" -o ConnectTimeout=10 "$EC2_HOST" "
            sudo crontab -u clawdbot -l | sed 's/--dry-run/--for-real/' | sudo crontab -u clawdbot -
            echo 'Outreach ENABLED — daily_loop will send real emails'
            sudo crontab -u clawdbot -l | grep daily_loop | grep 'full'
        "
        ;;
    disable)
        ssh -i "$EC2_KEY" -o ConnectTimeout=10 "$EC2_HOST" "
            sudo crontab -u clawdbot -l | sed 's/--for-real/--dry-run/' | sudo crontab -u clawdbot -
            echo 'Outreach DISABLED — daily_loop in dry-run mode'
            sudo crontab -u clawdbot -l | grep daily_loop | grep 'full'
        "
        ;;
    status)
        ssh -i "$EC2_KEY" -o ConnectTimeout=10 "$EC2_HOST" "
            mode=\$(sudo crontab -u clawdbot -l | grep 'daily_loop.*full' | grep -o '\-\-dry-run\|--for-real')
            echo \"Outreach mode: \$mode\"
        "
        ;;
    *)
        echo "Usage: $0 {enable|disable|status}"
        echo "  enable  — Start sending real outreach emails from EC2"
        echo "  disable — Switch to dry-run (no emails sent)"
        echo "  status  — Check current mode"
        ;;
esac
