#!/usr/bin/env python3
"""
KeyVault — Scheduled Tasks

Run by n8n or cron to:
1. Check key health
2. Scan for expiring keys and send reminders
3. Check environment sync drift

Run: python -m projects.shared.api-key-manager.src.scheduled_tasks [--health] [--expiry] [--sync] [--all]
"""

import sys
import os
import json
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

from .models import get_db, get_expiring_keys, log_audit
from .health_checker import run_health_checks


def check_expiry_and_notify(org_id: int = None):
    """Scan for expiring keys and send notifications."""
    conn = get_db()

    if org_id:
        orgs = [{"id": org_id}]
    else:
        orgs = conn.execute("SELECT id FROM organizations").fetchall()

    total_notifications = 0

    for org in orgs:
        oid = org["id"]

        # Get notification preferences
        prefs = conn.execute(
            "SELECT * FROM notification_prefs WHERE org_id = ? AND is_active = 1 AND notify_on_expiry = 1",
            (oid,)
        ).fetchall()

        if not prefs:
            continue

        # Check for keys expiring within each pref's warn window
        for pref in prefs:
            warn_days = pref["expiry_warn_days"]
            expiring = get_expiring_keys(conn, oid, warn_days)

            for key in expiring:
                # Check if we already sent a reminder for this
                existing = conn.execute("""
                    SELECT id FROM reminders
                    WHERE api_key_id = ? AND reminder_type = 'expiration' AND sent = 1
                    AND created_at > datetime('now', '-7 days')
                """, (key["id"],)).fetchone()

                if existing:
                    continue  # Already notified recently

                # Build message
                days_left = (datetime.fromisoformat(key["expires_at"]) - datetime.now()).days
                msg = f"⚠️ KeyVault: {key['service_name']} key ({key['env_var_name']}) expires in {days_left} days ({key['expires_at'][:10]})"

                # Send notification
                sent = _send_notification(pref["channel"], pref["destination"], msg)

                if sent:
                    # Record reminder
                    conn.execute("""
                        INSERT INTO reminders (org_id, api_key_id, service_id, reminder_type, remind_at, message, sent, sent_at, channel)
                        VALUES (?, ?, ?, 'expiration', datetime('now'), ?, 1, datetime('now'), ?)
                    """, (oid, key["id"], key["service_id"], msg, pref["channel"]))
                    total_notifications += 1

        conn.commit()

    print(f"Expiry check: sent {total_notifications} notifications")
    conn.close()
    return total_notifications


def check_health_and_notify(org_id: int = None):
    """Run health checks and notify on failures."""
    total, healthy, failed = run_health_checks(org_id)

    if failed == 0:
        return

    conn = get_db()
    if org_id:
        orgs = [{"id": org_id}]
    else:
        orgs = conn.execute("SELECT id FROM organizations").fetchall()

    for org in orgs:
        oid = org["id"]
        prefs = conn.execute(
            "SELECT * FROM notification_prefs WHERE org_id = ? AND is_active = 1 AND notify_on_health_fail = 1",
            (oid,)
        ).fetchall()

        if not prefs:
            continue

        # Get failed keys
        failed_keys = conn.execute("""
            SELECT ak.env_var_name, s.name as service_name, hc.error_message
            FROM health_checks hc
            JOIN api_keys ak ON hc.api_key_id = ak.id
            JOIN services s ON ak.service_id = s.id
            WHERE ak.org_id = ? AND hc.is_healthy = 0
            AND hc.created_at > datetime('now', '-1 hour')
        """, (oid,)).fetchall()

        if not failed_keys:
            continue

        names = ", ".join(f"{k['service_name']}" for k in failed_keys)
        msg = f"🔴 KeyVault: {len(failed_keys)} key(s) failed health check: {names}"

        for pref in prefs:
            _send_notification(pref["channel"], pref["destination"], msg)

    conn.close()


def _send_notification(channel: str, destination: str, message: str) -> bool:
    """Send a notification via the specified channel."""
    try:
        if channel == "email":
            return _send_email(destination, "KeyVault Alert", message)
        elif channel == "sms":
            return _send_sms(destination, message)
        elif channel == "telegram":
            return _send_telegram(destination, message)
        elif channel == "webhook":
            return _send_webhook(destination, message)
        return False
    except Exception as e:
        print(f"  Notification failed ({channel}): {e}")
        return False


def _send_email(to: str, subject: str, body: str) -> bool:
    """Send email via SMTP."""
    import smtplib
    from email.mime.text import MIMEText

    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    if not smtp_user or not smtp_pass:
        print("  SMTP not configured")
        return False

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to

    with smtplib.SMTP(smtp_host, 587) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
    print(f"  Email sent to {to}")
    return True


def _send_sms(to: str, body: str) -> bool:
    """Send SMS via Twilio."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")
    if not all([account_sid, auth_token, from_number]):
        print("  Twilio not configured")
        return False

    import base64
    auth = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
    data = urllib.parse.urlencode({"To": to, "From": from_number, "Body": body}).encode()
    req = urllib.request.Request(
        f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
        data=data,
        headers={"Authorization": f"Basic {auth}"},
        method="POST"
    )
    urllib.request.urlopen(req, timeout=10)
    print(f"  SMS sent to {to}")
    return True


def _send_telegram(chat_id: str, message: str) -> bool:
    """Send Telegram message."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("  Telegram not configured")
        return False

    data = json.dumps({"chat_id": chat_id, "text": message, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    urllib.request.urlopen(req, timeout=10)
    print(f"  Telegram sent to {chat_id}")
    return True


def _send_webhook(url: str, message: str) -> bool:
    """Send webhook POST."""
    data = json.dumps({"text": message, "source": "keyvault"}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    urllib.request.urlopen(req, timeout=10)
    print(f"  Webhook sent to {url}")
    return True


if __name__ == "__main__":
    args = sys.argv[1:]
    run_all = "--all" in args or not args

    org = None
    if "--org-id" in args:
        org = int(args[args.index("--org-id") + 1])

    if run_all or "--health" in args:
        print("=== Health Checks ===")
        check_health_and_notify(org)

    if run_all or "--expiry" in args:
        print("\n=== Expiry Scanner ===")
        check_expiry_and_notify(org)

    print("\nScheduled tasks complete.")
