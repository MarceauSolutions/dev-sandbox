#!/usr/bin/env python3
"""
Auto Follow-up Engine — sends SMS/email follow-ups when next_action_date arrives.

Called by n8n daily at 8:00 AM. Checks pipeline for deals due today,
sends the appropriate follow-up based on outcome/stage, logs it back.

Usage:
    python -m src.auto_followup check        # Preview what would send (dry run)
    python -m src.auto_followup send         # Actually send follow-ups
    python -m src.auto_followup send --sms-only   # Only SMS, skip email
"""

import os
import sys
import json
import sqlite3
import smtplib
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(str(_PROJECT_ROOT / ".env"))

DB_PATH = str(Path(__file__).parent.parent / "data" / "pipeline.db")

# Twilio config
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_PHONE_NUMBER", "+18552399364")

# SMTP config
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USERNAME")
SMTP_PASS = os.getenv("SMTP_PASSWORD")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "wmarceau@marceausolutions.com")

# William's phone for notifications
WILLIAM_PHONE = "+12393985676"


# --- Follow-up templates by outcome/next_action ---

SMS_TEMPLATES = {
    # From call outcomes → next_action values set by app.py log-call routing
    # NOTE: No "AI" language — frame as business automation / results
    "Re-call": (
        "Hey {first_name}, this is William from Marceau Solutions. "
        "I tried reaching you the other day about helping {company} make sure no leads slip "
        "through the cracks. Still open to a quick chat? Just reply with a good time."
    ),
    "Call back — callback requested": (
        "Hey {first_name}, it's William from Marceau Solutions -- following up as promised. "
        "Still a good time to chat about streamlining how {company} handles calls and follow-ups? "
        "I can do a quick 10-min call whenever works for you."
    ),
    "Book meeting — qualified lead": (
        "Hey {first_name}, great chatting the other day! Here's my calendar link to grab 15 min "
        "this week: calendly.com/wmarceau/ai-services-discovery -- looking forward to showing you "
        "how the system works for {company}."
    ),
    "In-person visit": (
        "Hey {first_name}, this is William from Marceau Solutions. "
        "I'd love to stop by {company} and show you a quick demo of the system -- "
        "takes about 5 minutes. What day works best this week?"
    ),
    "Try direct line/email": (
        "Hi {first_name}, this is William with Marceau Solutions. "
        "I help businesses like {company} connect their calls, texts, and web leads into one "
        "system so nothing falls through the cracks. Quick 10-min call this week? No pressure."
    ),
    "Check back — verify system works": (
        "Hey {first_name}, William from Marceau Solutions. "
        "Just checking in on {company} -- how's everything running? "
        "If you ever want a second opinion on your setup, I'm here. No pitch, just a resource."
    ),
    "voicemail_followup": (
        "Hey {first_name}, this is William from Marceau Solutions. "
        "I left you a voicemail about helping {company} capture more leads automatically. "
        "Would a quick 5-minute call work sometime this week?"
    ),
    "no_answer_followup": (
        "Hey {first_name}, William from Marceau Solutions here. "
        "I tried calling {company} but couldn't get through. I help local businesses make sure "
        "every call and inquiry gets answered and followed up with -- worth a quick chat?"
    ),
    "Re-email with value-add": None,  # Email only, no SMS
    "Update phone number": None,  # Skip - needs manual action
}

EMAIL_TEMPLATES = {
    "Re-email with value-add": {
        "subject": "Quick thought for {company}",
        "body": (
            "Hi {first_name},\n\n"
            "I reached out recently about helping {company} streamline how you handle leads and follow-ups. "
            "I know it might not have been the right time, so I wanted to share something useful either way.\n\n"
            "I took a quick look at how {company} handles inbound calls and inquiries and noticed a few "
            "things that could save your team hours every week. Happy to share if you're curious.\n\n"
            "Either way, no pressure. Just wanted to be helpful.\n\n"
            "Best,\nWilliam Marceau\nMarceau Solutions\n(239) 398-5676\nmarceausolutions.com"
        ),
    },
}


def get_followups_due(conn):
    """Get deals with follow-ups due today or overdue."""
    today = datetime.now().strftime("%Y-%m-%d")
    rows = conn.execute("""
        SELECT d.id, d.company, d.contact_name, d.contact_email, d.contact_phone,
               d.stage, d.next_action, d.next_action_date, d.notes, d.outreach_method
        FROM deals d
        WHERE d.next_action_date <= ?
        AND d.next_action_date IS NOT NULL
        AND d.next_action_date != ''
        AND d.stage NOT IN ('Closed Won', 'Closed Lost')
        ORDER BY d.next_action_date ASC
    """, (today,)).fetchall()
    return [dict(r) for r in rows]


def send_sms(to, message, dry_run=False):
    """Send SMS via Twilio."""
    if not to or not to.strip():
        return {"success": False, "error": "No phone number"}

    # Normalize phone number
    phone = to.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not phone.startswith("+"):
        phone = "+1" + phone.lstrip("1")

    if dry_run:
        return {"success": True, "dry_run": True, "to": phone, "message": message[:80] + "..."}

    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        msg = client.messages.create(body=message, from_=TWILIO_FROM, to=phone)
        return {"success": True, "sid": msg.sid, "to": phone}
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_email(to_email, subject, body, dry_run=False):
    """Send email via SMTP."""
    if not to_email or not to_email.strip():
        return {"success": False, "error": "No email address"}

    if dry_run:
        return {"success": True, "dry_run": True, "to": to_email, "subject": subject}

    try:
        msg = MIMEMultipart()
        msg["From"] = f"William Marceau <{SENDER_EMAIL}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        return {"success": True, "to": to_email}
    except Exception as e:
        return {"success": False, "error": str(e)}


def log_followup(conn, deal_id, company, contact, channel, message_summary, template_name=""):
    """Log the follow-up to outreach_log (does NOT advance next_action_date)."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO outreach_log (deal_id, company, contact, channel, message_summary, created_at, tower, template_used) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (deal_id, company, contact, channel, message_summary, now, "digital-ai-services", template_name)
    )
    conn.commit()


def advance_next_action_date(conn, deal_id, days=3):
    """Push next_action_date forward — only call after a successful send."""
    next_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    conn.execute(
        "UPDATE deals SET next_action_date = ? WHERE id = ?",
        (next_date, deal_id)
    )
    conn.commit()


def process_followups(dry_run=True, sms_only=False):
    """Process all due follow-ups."""
    # Validate Twilio credentials before attempting to send
    if not dry_run:
        if not TWILIO_SID or not TWILIO_TOKEN:
            print("ERROR: TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in .env")
            return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    due = get_followups_due(conn)

    if not due:
        print("No follow-ups due today.")
        conn.close()
        return []

    results = []
    for deal in due:
        action = deal["next_action"] or ""
        name_parts = (deal["contact_name"] or "").split()
        first_name = name_parts[0] if name_parts else "there"
        company = deal["company"] or "your business"
        phone = deal["contact_phone"] or ""
        email = deal["contact_email"] or ""

        fmt = {"first_name": first_name, "company": company}

        sent_something = False

        # Resolve template — check explicit action first, then fall back by pattern
        sms_template = SMS_TEMPLATES.get(action)
        if not sms_template and action:
            # Fuzzy match: "Re-call" might be stored as "Re-call" or lowercase
            for key, tmpl in SMS_TEMPLATES.items():
                if key and action.lower().strip() in key.lower():
                    sms_template = tmpl
                    break

        # Try SMS first
        if sms_template and phone:
            message = sms_template.format(**fmt)
            result = send_sms(phone, message, dry_run=dry_run)
            result["deal_id"] = deal["id"]
            result["company"] = company
            result["channel"] = "SMS"
            result["action"] = action
            results.append(result)

            if not dry_run and result["success"]:
                log_followup(conn, deal["id"], company, deal["contact_name"] or "",
                            "SMS", f"Auto follow-up ({action}): {message[:100]}...",
                            template_name=action)
                sent_something = True
            elif not dry_run and not result["success"]:
                print(f"  [FAIL] SMS to {company}: {result.get('error')}")

            print(f"  {'[DRY]' if dry_run else '[SENT]' if result.get('success') else '[FAIL]'} SMS to {company} ({phone}): {action}")

        # Try email if we have it and it's not sms_only
        email_template = EMAIL_TEMPLATES.get(action)
        if email_template and email and not sms_only:
            subject = email_template["subject"].format(**fmt)
            body = email_template["body"].format(**fmt)
            result = send_email(email, subject, body, dry_run=dry_run)
            result["deal_id"] = deal["id"]
            result["company"] = company
            result["channel"] = "Email"
            result["action"] = action
            results.append(result)

            if not dry_run and result["success"]:
                log_followup(conn, deal["id"], company, deal["contact_name"] or "",
                            "Email", f"Auto follow-up ({action}): {subject}",
                            template_name=action)
                sent_something = True

            print(f"  {'[DRY]' if dry_run else '[SENT]' if result.get('success') else '[FAIL]'} Email to {company} ({email}): {subject}")

        # If no template matched but there's a phone, send generic
        if not sms_template and not email_template and phone:
            generic = (
                f"Hey {first_name}, this is William from Marceau Solutions. "
                f"Following up on our conversation about {company}. "
                f"Still open to chatting? Just reply with a good time."
            )
            result = send_sms(phone, generic, dry_run=dry_run)
            result["deal_id"] = deal["id"]
            result["company"] = company
            result["channel"] = "SMS"
            result["action"] = "generic_followup"
            results.append(result)

            if not dry_run and result["success"]:
                log_followup(conn, deal["id"], company, deal["contact_name"] or "",
                            "SMS", f"Auto follow-up (generic): {generic[:100]}...",
                            template_name="generic_followup")
                sent_something = True

            print(f"  {'[DRY]' if dry_run else '[SENT]' if result.get('success') else '[FAIL]'} SMS generic to {company} ({phone})")

        # Only advance next_action_date if at least one message actually sent
        if sent_something and not dry_run:
            advance_next_action_date(conn, deal["id"], days=3)

        if not phone and not email:
            print(f"  [SKIP] {company} — no phone or email on file")
            results.append({
                "deal_id": deal["id"], "company": company,
                "channel": "NONE", "action": action,
                "success": False, "error": "No contact info"
            })

    conn.close()
    return results


def format_summary(results):
    """Format results for notification."""
    sent = [r for r in results if r.get("success") and not r.get("dry_run")]
    failed = [r for r in results if not r.get("success")]
    skipped = [r for r in results if r.get("dry_run")]

    lines = [f"Auto Follow-up Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}"]
    if sent:
        lines.append(f"\nSent ({len(sent)}):")
        for r in sent:
            lines.append(f"  {r['channel']} → {r['company']} ({r['action']})")
    if failed:
        lines.append(f"\nFailed ({len(failed)}):")
        for r in failed:
            lines.append(f"  {r['company']}: {r.get('error', 'unknown')}")
    if skipped:
        lines.append(f"\nWould send ({len(skipped)}):")
        for r in skipped:
            lines.append(f"  {r['channel']} → {r['company']} ({r['action']})")

    return "\n".join(lines)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    sms_only = "--sms-only" in sys.argv

    if cmd == "check":
        print("DRY RUN — previewing follow-ups due today:\n")
        results = process_followups(dry_run=True, sms_only=sms_only)
        print(f"\n{format_summary(results)}")
    elif cmd == "send":
        print("SENDING follow-ups:\n")
        results = process_followups(dry_run=False, sms_only=sms_only)
        summary = format_summary(results)
        print(f"\n{summary}")

        # Notify William via SMS
        sent_count = sum(1 for r in results if r.get("success") and not r.get("dry_run"))
        if sent_count > 0:
            notify_msg = f"Auto follow-ups sent: {sent_count} messages. Check pipeline for details."
            _send_telegram_notification(notify_msg)
    else:
        print("Usage: python -m src.auto_followup [check|send] [--sms-only]")


# --- Telegram notification (replaces SMS to William) ---
def _send_telegram_notification(message: str) -> bool:
    """Send notification to William via Telegram instead of SMS."""
    import urllib.request
    import json
    import os
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "5692454753")  # William's Telegram ID
    
    if not bot_token:
        print("TELEGRAM_BOT_TOKEN not set - skipping notification")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = json.dumps({
            "chat_id": chat_id,
            "text": f"📱 Auto Follow-up Report\n\n{message}",
            "parse_mode": "HTML"
        }).encode()
        
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"Telegram notification failed: {e}")
        return False
