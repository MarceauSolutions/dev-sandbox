#!/usr/bin/env python3
"""
EC2 Response Checker — Monitors Twilio SMS for new replies when Mac is off.

Checks Twilio for new inbound messages, classifies them (hot/warm/cold),
updates pipeline.db on EC2, and sends Telegram alerts for hot leads.

This replaces the Mac-side check-responses launchd job during away-mode.
Gmail checking is handled separately by Clawdbot/n8n on EC2.

Designed to run via cron every 15 minutes:
  */15 9-21 * * * /usr/bin/python3 /home/clawdbot/scripts/ec2_check_responses.py

Requires: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER in .env
"""

import json
import logging
import os
import sqlite3
import sys
import urllib.request
import ssl
from datetime import datetime, timedelta
from pathlib import Path

# Setup
REPO_ROOT = Path("/home/clawdbot")
DB_PATH = REPO_ROOT / "data" / "pipeline.db"
LAST_CHECK_FILE = REPO_ROOT / "logs" / ".last_response_check"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(REPO_ROOT / "logs" / "response_checker.log"),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger("ec2_responses")

# Load env
env_paths = [
    REPO_ROOT / ".clawdbot" / ".env",
    REPO_ROOT / "dev-sandbox" / ".env",
]
for ep in env_paths:
    if ep.exists():
        for line in ep.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def check_twilio_replies():
    """Check Twilio for new SMS replies since last check."""
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    phone = os.environ.get("TWILIO_PHONE_NUMBER", "")

    if not all([account_sid, auth_token, phone]):
        logger.warning("Twilio credentials not configured")
        return []

    # Get last check time
    since = datetime.utcnow() - timedelta(minutes=20)
    if LAST_CHECK_FILE.exists():
        try:
            since = datetime.fromisoformat(LAST_CHECK_FILE.read_text().strip())
        except (ValueError, OSError):
            pass

    # Query Twilio API for inbound messages
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = ssl.create_default_context()

    try:
        since_str = since.strftime("%Y-%m-%dT%H:%M:%SZ")
        url = (f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}"
               f"/Messages.json?To={phone}&DateSent%3E={since_str}&PageSize=20")

        import base64
        auth = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
        req = urllib.request.Request(url, headers={"Authorization": f"Basic {auth}"})
        resp = urllib.request.urlopen(req, timeout=15, context=ctx)
        data = json.loads(resp.read())

        messages = data.get("messages", [])
        logger.info(f"Twilio: {len(messages)} messages since {since_str}")

        # Save check time
        LAST_CHECK_FILE.parent.mkdir(parents=True, exist_ok=True)
        LAST_CHECK_FILE.write_text(datetime.utcnow().isoformat())

        return [{"from": m["from"], "body": m["body"], "date": m["date_sent"]}
                for m in messages if m.get("body")]

    except Exception as e:
        logger.error(f"Twilio check failed: {e}")
        return []


def classify_response(body: str) -> str:
    """Classify an SMS response as hot/warm/cold/opt-out."""
    lower = body.lower().strip()

    # Opt-out
    if any(w in lower for w in ["stop", "unsubscribe", "remove", "opt out", "no thanks"]):
        return "opt_out"

    # Hot (strong interest)
    if any(w in lower for w in ["interested", "yes", "tell me more", "let's talk",
                                  "schedule", "when can", "how much", "sign me up",
                                  "sounds good", "i'm in", "let's do it"]):
        return "hot"

    # Warm (some engagement)
    if any(w in lower for w in ["maybe", "not sure", "call me", "send info",
                                  "what do you", "how does", "more info"]):
        return "warm"

    return "cold"


def process_replies(replies: list):
    """Process classified replies — update pipeline, send alerts."""
    if not replies:
        return

    conn = get_db()
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = "5692454753"

    for reply in replies:
        phone = reply["from"]
        body = reply["body"]
        classification = classify_response(body)

        # Find matching deal
        deal = conn.execute(
            "SELECT id, company, contact_name, stage FROM deals "
            "WHERE contact_phone LIKE ? ORDER BY updated_at DESC LIMIT 1",
            (f"%{phone[-10:]}%",)
        ).fetchone()

        if not deal:
            logger.info(f"Reply from unknown number {phone}: {body[:50]}")
            continue

        d = dict(deal)
        logger.info(f"Reply from {d['company']} [{classification}]: {body[:80]}")

        if classification == "hot":
            conn.execute(
                "UPDATE deals SET stage = 'Hot Response', next_action = 'schedule_call', "
                "updated_at = datetime('now') WHERE id = ?", (d["id"],)
            )
            conn.execute(
                "INSERT INTO activities (deal_id, activity_type, description, tower) "
                "VALUES (?, 'hot_response', ?, 'lead-generation')",
                (d["id"], f"SMS reply: {body[:200]}")
            )
            # Alert William
            if telegram_token:
                _send_telegram(telegram_token, chat_id,
                    f"HOT LEAD: {d['company']}\n"
                    f"Reply: \"{body[:150]}\"\n"
                    f"Call {d.get('contact_name', '?')} at {phone}\n"
                    f"-> result {d['company']}: [outcome]")

        elif classification == "warm":
            conn.execute(
                "UPDATE deals SET stage = 'Warm Response', updated_at = datetime('now') WHERE id = ?",
                (d["id"],)
            )
            conn.execute(
                "INSERT INTO activities (deal_id, activity_type, description, tower) "
                "VALUES (?, 'warm_response', ?, 'lead-generation')",
                (d["id"], f"SMS reply: {body[:200]}")
            )

        elif classification == "opt_out":
            conn.execute(
                "UPDATE deals SET stage = 'Closed Lost', sms_consent = 0, "
                "updated_at = datetime('now') WHERE id = ?", (d["id"],)
            )

        conn.execute(
            "INSERT INTO outreach_log (deal_id, company, contact, channel, "
            "message_summary, response, created_at) VALUES (?, ?, ?, 'SMS', ?, ?, datetime('now'))",
            (d["id"], d["company"], phone, f"Inbound reply", body[:200])
        )

    conn.commit()
    conn.close()


def _send_telegram(token: str, chat_id: str, message: str):
    """Send Telegram notification."""
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = ssl.create_default_context()

    try:
        data = json.dumps({"chat_id": chat_id, "text": message}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=data, headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=10, context=ctx)
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")


def main():
    logger.info("EC2 response checker starting")
    replies = check_twilio_replies()
    if replies:
        process_replies(replies)
        logger.info(f"Processed {len(replies)} replies")
    else:
        logger.info("No new replies")


if __name__ == "__main__":
    main()
