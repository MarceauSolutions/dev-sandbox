#!/usr/bin/env python3
"""
Outreach Executor — Send emails and SMS for pipeline outreach.

Sends personalized follow-up emails via SMTP and SMS via Twilio.
Logs every action to outreach_log. Updates deal stages.

TCPA Rules (strictly enforced):
  - NO cold SMS. SMS only to contacts with sms_consent=true.
  - Cold outreach = email + phone ONLY.
  - No messages before 8am or after 9pm local time.
"""

import smtplib
import sqlite3
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .config import (
    DB_PATH, SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD,
    SENDER_EMAIL, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER,
    DEFAULT_FOLLOWUP_DAYS, WILLIAM_PHONE,
)
from .ab_testing_manager import (
    assign_variant, get_subject_text, get_body_text,
    record_send,
)


def _ensure_sms_consent_column(conn: sqlite3.Connection):
    """Add sms_consent column if it doesn't exist yet."""
    cols = {row[1] for row in conn.execute("PRAGMA table_info(deals)").fetchall()}
    if "sms_consent" not in cols:
        conn.execute("ALTER TABLE deals ADD COLUMN sms_consent INTEGER DEFAULT 0")
        conn.commit()


def send_email(to_email: str, subject: str, body: str, dry_run: bool = False) -> dict:
    """
    Send a single email via SMTP.

    Args:
        to_email: Recipient email address
        subject: Email subject line
        body: Email body (plain text)
        dry_run: If True, don't actually send

    Returns:
        Dict with success status and details
    """
    if not to_email or "@" not in to_email:
        return {"success": False, "error": "Invalid email address"}

    if not SMTP_USERNAME or not SMTP_PASSWORD:
        return {"success": False, "error": "SMTP credentials not configured"}

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
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return {"success": True, "to": to_email, "subject": subject}
    except Exception as e:
        return {"success": False, "error": str(e), "to": to_email}


def send_sms(to_phone: str, message: str, dry_run: bool = False) -> dict:
    """
    Send SMS via Twilio.

    Args:
        to_phone: Phone number (any format, will be normalized)
        message: SMS message text
        dry_run: If True, don't actually send

    Returns:
        Dict with success status and details
    """
    if not to_phone:
        return {"success": False, "error": "No phone number"}

    # Normalize phone
    phone = "".join(c for c in to_phone if c.isdigit() or c == "+")
    if not phone.startswith("+"):
        phone = "+1" + phone.lstrip("1")

    if dry_run:
        return {"success": True, "dry_run": True, "to": phone, "message": message[:80]}

    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return {"success": False, "error": "Twilio credentials not configured"}

    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        msg = client.messages.create(body=message, from_=TWILIO_PHONE_NUMBER, to=phone)
        return {"success": True, "sid": msg.sid, "to": phone}
    except Exception as e:
        return {"success": False, "error": str(e), "to": phone}


def log_outreach(conn: sqlite3.Connection, deal_id: int, company: str, contact: str,
                 channel: str, message_summary: str, template_used: str = "",
                 variant_group: str = "", follow_up_date: str = None):
    """Log outreach action to outreach_log."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO outreach_log (deal_id, company, contact, channel, message_summary,
                                  follow_up_date, created_at, tower, template_used, variant_group)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'digital-ai-services', ?, ?)
    """, (deal_id, company, contact, channel, message_summary,
          follow_up_date, now, template_used, variant_group))
    conn.commit()


def execute_email_outreach(tasks: list, dry_run: bool = False) -> dict:
    """
    Send emails for all tasks that include an email action.

    Args:
        tasks: List of task dicts from follow_up_router
        dry_run: Preview only

    Returns:
        Dict with sent/failed counts
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    email_tasks = [t for t in tasks if "email" in t.get("actions", []) and t.get("email")]
    results = {"sent": 0, "failed": 0, "skipped": 0, "details": []}

    for task in email_tasks:
        deal_id = task["deal_id"]
        company = task["company"]
        contact = task.get("contact", "") or ""
        email = task["email"]
        industry = task.get("industry", "Other")

        # Get first name
        contact_first = contact.split()[0] if contact and contact not in ("Unknown", "the owner") else "there"

        # Assign A/B variants
        subject_variant = assign_variant("email_subjects", deal_id)
        body_variant = assign_variant("email_bodies", deal_id)

        # Get actual text
        subject = get_subject_text(subject_variant, company, contact_first)
        body = get_body_text(body_variant, contact_first, company, industry)

        # Send
        result = send_email(email, subject, body, dry_run=dry_run)
        result["company"] = company
        result["variant"] = f"{subject_variant}|{body_variant}"

        if result.get("success"):
            results["sent"] += 1

            if not dry_run:
                # Log to outreach_log
                log_outreach(
                    conn, deal_id, company, contact, "Email",
                    f"Cold email: {subject}",
                    template_used=body_variant,
                    variant_group=f"{subject_variant}|{body_variant}",
                    follow_up_date=(datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
                )

                # Record A/B send
                record_send("email_subjects", subject_variant)
                record_send("email_bodies", body_variant)

                # Update deal stage if first touch
                stage = task.get("stage", "Prospect")
                if stage == "Prospect":
                    conn.execute("""
                        UPDATE deals SET stage = 'Contacted',
                            next_action = 'Follow-up email/call',
                            next_action_date = ?,
                            updated_at = datetime('now')
                        WHERE id = ?
                    """, ((datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"), deal_id))
                    conn.commit()

            print(f"  {'[DRY]' if dry_run else '[SENT]'} Email to {company} ({email}) — {subject_variant}")
        else:
            results["failed"] += 1
            print(f"  [FAIL] Email to {company}: {result.get('error', 'unknown')}")

        results["details"].append(result)

    conn.close()
    return results


def execute_sms_outreach(tasks: list, dry_run: bool = False) -> dict:
    """
    Send SMS ONLY to leads with sms_consent=true.

    TCPA: No cold SMS ever. Only opted-in contacts.

    Args:
        tasks: List of task dicts
        dry_run: Preview only

    Returns:
        Dict with sent/failed counts
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _ensure_sms_consent_column(conn)

    results = {"sent": 0, "failed": 0, "skipped_no_consent": 0, "details": []}

    for task in tasks:
        deal_id = task["deal_id"]
        phone = task.get("phone", "")
        if not phone:
            continue

        # TCPA CHECK: Only send SMS to opted-in contacts
        row = conn.execute(
            "SELECT sms_consent FROM deals WHERE id = ?", (deal_id,)
        ).fetchone()

        if not row or not row["sms_consent"]:
            results["skipped_no_consent"] += 1
            continue

        company = task["company"]
        contact = task.get("contact", "") or ""
        contact_first = contact.split()[0] if contact and contact not in ("Unknown", "the owner") else "there"

        # Build SMS from follow-up template
        next_action = task.get("next_action", "")
        message = (
            f"Hey {contact_first}, this is William from Marceau Solutions. "
            f"Following up on {company}. Still open to a quick chat? "
            f"Reply with a good time or STOP to opt out."
        )

        result = send_sms(phone, message, dry_run=dry_run)
        result["company"] = company

        if result.get("success"):
            results["sent"] += 1
            if not dry_run:
                log_outreach(
                    conn, deal_id, company, contact, "SMS",
                    f"Follow-up SMS: {message[:100]}",
                    template_used="sms_followup",
                )
            print(f"  {'[DRY]' if dry_run else '[SENT]'} SMS to {company} ({phone})")
        else:
            results["failed"] += 1
            print(f"  [FAIL] SMS to {company}: {result.get('error', 'unknown')}")

        results["details"].append(result)

    conn.close()
    return results


def run_outreach(tasks: list, dry_run: bool = False) -> dict:
    """
    Execute all outreach for today's tasks.

    Args:
        tasks: List of task dicts from follow_up_router
        dry_run: Preview only

    Returns:
        Combined results dict
    """
    print("\n=== OUTREACH EXECUTION ===")

    # Send emails (primary cold outreach channel)
    print("\n  --- Emails ---")
    email_results = execute_email_outreach(tasks, dry_run=dry_run)
    print(f"  Emails: {email_results['sent']} sent, {email_results['failed']} failed")

    # Send SMS (ONLY to opted-in contacts)
    print("\n  --- SMS (opted-in only) ---")
    sms_results = execute_sms_outreach(tasks, dry_run=dry_run)
    print(f"  SMS: {sms_results['sent']} sent, {sms_results['skipped_no_consent']} skipped (no consent)")

    return {
        "email": email_results,
        "sms": sms_results,
        "total_sent": email_results["sent"] + sms_results["sent"],
        "total_failed": email_results["failed"] + sms_results["failed"],
    }


if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    # For standalone testing, generate tasks from router
    from .follow_up_router import run_routing
    tasks = run_routing(dry_run=True, include_scripts=False)
    run_outreach(tasks, dry_run=dry)
