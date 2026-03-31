#!/usr/bin/env python3
"""
daily_priorities_cron.py — Send Daily Priority List to Telegram

Runs via cron to send the top 5 prioritized follow-ups each morning.

Usage:
    python execution/daily_priorities_cron.py           # Send to Telegram
    python execution/daily_priorities_cron.py --preview # Preview without sending
    python execution/daily_priorities_cron.py --learn   # Update learnings then send

Crontab entry (8am ET = 12:00 UTC):
    0 12 * * * cd /home/clawdbot/dev-sandbox && /usr/bin/python3 execution/daily_priorities_cron.py >> /home/clawdbot/logs/priorities.log 2>&1
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Setup paths
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "execution"))

from dotenv import load_dotenv
load_dotenv(REPO_ROOT / ".env")


def send_telegram(message: str) -> bool:
    """Send message to Telegram."""
    import urllib.request
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "5692454753")
    if not bot_token:
        print(f"[NO TELEGRAM] {message}")
        return False
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = json.dumps({
            "chat_id": chat_id, 
            "text": message[:4096], 
            "parse_mode": "Markdown"
        }).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        print(f"Telegram error: {e}")
        return False


def run_daily_priorities(learn: bool = False, preview: bool = False) -> bool:
    """Generate and send daily priority list."""
    from followup_prioritizer import FollowupPrioritizer
    
    print(f"\n{'='*50}")
    print(f"Daily Priorities — {datetime.now().isoformat()}")
    print(f"{'='*50}")
    
    prioritizer = FollowupPrioritizer()
    
    # Optional: update learnings from outcomes first
    if learn:
        print("Updating learnings from outcomes...")
        learnings = prioritizer.learn_from_outcomes()
        if learnings.get("learning_log"):
            for entry in learnings["learning_log"]:
                print(f"  Updated {entry['industry']}: {entry['old_rate']:.1%} → {entry['new_rate']:.1%}")
    
    # Get prioritized list
    leads = prioritizer.get_top_5()
    
    if not leads:
        message = "✅ No high-priority follow-ups today.\n\nAll leads contacted or no phone numbers available."
    else:
        message = prioritizer.format_daily_list(leads)
    
    # Add header
    now = datetime.now()
    header = f"☀️ *Good morning!*\n\n"
    message = header + message
    
    # Add footer with next action hint
    if leads:
        message += f"\n\nReply *next* for detailed call prep on #{1}."
    
    if preview:
        print("\n[PREVIEW MODE - Not sending]\n")
        print(message)
        return True
    
    # Send to Telegram
    if send_telegram(message):
        print("✅ Daily priorities sent to Telegram")
        return True
    else:
        print("❌ Failed to send to Telegram")
        print(message)
        return False


def main():
    parser = argparse.ArgumentParser(description="Send daily priority list to Telegram")
    parser.add_argument("--preview", action="store_true", help="Preview without sending")
    parser.add_argument("--learn", action="store_true", help="Update learnings first")
    
    args = parser.parse_args()
    
    success = run_daily_priorities(learn=args.learn, preview=args.preview)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
