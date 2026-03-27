#!/usr/bin/env python3
"""
Reply Monitor — Check Gmail for responses to outreach emails.

Connects via IMAP to check for replies in the last 24h.
Classifies replies: interested / not_interested / out_of_office / auto_reply.
Updates deal stages based on reply content.
Alerts William via SMS for hot replies (interested).
"""

import imaplib
import email
import re
import sqlite3
from datetime import datetime, timedelta
from email.header import decode_header

from .config import (
    DB_PATH, IMAP_HOST, IMAP_PORT, SMTP_USERNAME, SMTP_PASSWORD,
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER,
    WILLIAM_PHONE,
)


# Reply classification keywords
INTERESTED_KEYWORDS = [
    "interested", "yes", "tell me more", "sounds good", "let's talk",
    "schedule", "set up a time", "demo", "when can we",
    "that could work", "send me info", "i'd like to", "want to learn",
    "how does it work", "what's the cost", "pricing",
]

NOT_INTERESTED_KEYWORDS = [
    "not interested", "no thanks", "no thank you", "remove me",
    "unsubscribe", "stop", "don't contact", "not looking",
    "already have", "not a good fit", "pass",
]

OUT_OF_OFFICE_KEYWORDS = [
    "out of office", "ooo", "away from", "on vacation",
    "will return", "auto-reply", "automatic reply",
    "limited access to email",
]

AUTO_REPLY_KEYWORDS = [
    "auto-reply", "automatic reply", "do not reply",
    "this is an automated", "noreply", "no-reply",
    "mailer-daemon", "delivery status notification",
]


def classify_reply(subject: str, body: str, sender: str) -> str:
    """
    Classify an email reply into a category.

    Args:
        subject: Email subject line
        body: Email body text
        sender: Sender email address

    Returns:
        One of: "interested", "not_interested", "out_of_office", "auto_reply", "unknown"
    """
    combined = f"{subject} {body}".lower()
    sender_lower = sender.lower()

    # Check auto-reply first (most specific)
    if any(kw in sender_lower for kw in ["noreply", "no-reply", "mailer-daemon"]):
        return "auto_reply"
    if any(kw in combined for kw in AUTO_REPLY_KEYWORDS):
        return "auto_reply"

    # Out of office
    if any(kw in combined for kw in OUT_OF_OFFICE_KEYWORDS):
        return "out_of_office"

    # Not interested (check before interested to avoid false positives)
    if any(kw in combined for kw in NOT_INTERESTED_KEYWORDS):
        return "not_interested"

    # Interested
    if any(kw in combined for kw in INTERESTED_KEYWORDS):
        return "interested"

    return "unknown"


def find_matching_deal(conn: sqlite3.Connection, sender_email: str) -> dict:
    """Find a deal that matches the sender's email address."""
    row = conn.execute(
        "SELECT * FROM deals WHERE LOWER(contact_email) = LOWER(?)", (sender_email,)
    ).fetchone()
    if row:
        return dict(row)

    # Try partial match on domain
    domain = sender_email.split("@")[-1] if "@" in sender_email else ""
    if domain and domain not in ("gmail.com", "yahoo.com", "hotmail.com", "outlook.com"):
        row = conn.execute(
            "SELECT * FROM deals WHERE LOWER(contact_email) LIKE ?", (f"%@{domain.lower()}",)
        ).fetchone()
        if row:
            return dict(row)

    return None


def check_replies(hours: int = 24, dry_run: bool = False) -> list:
    """
    Check Gmail for replies to outreach emails.

    Args:
        hours: Look back this many hours
        dry_run: Don't update database or send alerts

    Returns:
        List of reply dicts with classification
    """
    print("\n=== REPLY MONITOR ===")

    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("  [WARN] SMTP credentials not set — skipping reply check")
        return []

    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(SMTP_USERNAME, SMTP_PASSWORD)
        mail.select("INBOX")
    except Exception as e:
        print(f"  [ERROR] IMAP connection failed: {e}")
        return []

    # Search for emails in the last N hours
    since_date = (datetime.now() - timedelta(hours=hours)).strftime("%d-%b-%Y")
    try:
        _, message_numbers = mail.search(None, f'(SINCE "{since_date}")')
    except Exception as e:
        print(f"  [ERROR] IMAP search failed: {e}")
        mail.logout()
        return []

    msg_nums = message_numbers[0].split()
    print(f"  Found {len(msg_nums)} emails in last {hours}h")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    replies = []
    hot_replies = []

    for num in msg_nums:
        try:
            _, data = mail.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])

            # Get sender
            sender = msg["From"] or ""
            sender_email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', sender)
            sender_email = sender_email_match.group(0) if sender_email_match else sender

            # Skip our own emails
            if sender_email.lower() == SMTP_USERNAME.lower():
                continue

            # Get subject
            subject = msg["Subject"] or ""
            if isinstance(subject, bytes):
                subject = subject.decode("utf-8", errors="ignore")
            decoded = decode_header(subject)
            if decoded:
                subject = str(decoded[0][0]) if isinstance(decoded[0][0], str) else decoded[0][0].decode(decoded[0][1] or "utf-8", errors="ignore")

            # Get body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore") if msg.get_payload(decode=True) else ""

            # Check if this is a reply to our outreach
            is_reply = (
                subject.lower().startswith("re:") and
                ("marceau" in body.lower() or "marceau" in subject.lower() or
                 "lead" in body.lower() or "system" in body.lower())
            )

            # Also match if sender is one of our leads
            deal = find_matching_deal(conn, sender_email)

            if not is_reply and not deal:
                continue

            # Classify
            classification = classify_reply(subject, body, sender_email)

            reply = {
                "sender_email": sender_email,
                "subject": subject,
                "body_preview": body[:200],
                "classification": classification,
                "deal": deal,
                "timestamp": msg["Date"] or datetime.now().isoformat(),
            }
            replies.append(reply)

            print(f"  [{classification.upper()}] From: {sender_email}")
            print(f"    Subject: {subject[:60]}")
            if deal:
                print(f"    Matched deal: {deal['company']} (ID: {deal['id']})")

            # Update pipeline
            if deal and not dry_run:
                deal_id = deal["id"]

                if classification == "interested":
                    conn.execute("""
                        UPDATE deals SET stage = 'Qualified',
                            next_action = 'Call back — replied interested',
                            next_action_date = ?,
                            updated_at = datetime('now')
                        WHERE id = ? AND stage NOT IN ('Closed Won', 'Meeting Booked')
                    """, (datetime.now().strftime("%Y-%m-%d"), deal_id))

                    # Log to outreach
                    conn.execute("""
                        INSERT INTO outreach_log (deal_id, company, contact, channel,
                            message_summary, response, created_at, tower)
                        VALUES (?, ?, ?, 'Email', ?, 'Interested — replied to cold email',
                            datetime('now'), 'digital-ai-services')
                    """, (deal_id, deal["company"], deal.get("contact_name", ""),
                          f"Reply: {subject[:80]}"))

                    hot_replies.append(reply)

                elif classification == "not_interested":
                    conn.execute("""
                        UPDATE deals SET stage = 'Closed Lost',
                            next_action = NULL,
                            next_action_date = NULL,
                            updated_at = datetime('now')
                        WHERE id = ?
                    """, (deal_id,))

                    conn.execute("""
                        INSERT INTO outreach_log (deal_id, company, contact, channel,
                            message_summary, response, created_at, tower)
                        VALUES (?, ?, ?, 'Email', ?, 'Not interested — replied to cold email',
                            datetime('now'), 'digital-ai-services')
                    """, (deal_id, deal["company"], deal.get("contact_name", ""),
                          f"Reply (declined): {subject[:80]}"))

                elif classification == "out_of_office":
                    # Push follow-up back 5 days
                    conn.execute("""
                        UPDATE deals SET next_action_date = ?,
                            next_action = 'Re-email after OOO',
                            updated_at = datetime('now')
                        WHERE id = ?
                    """, ((datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"), deal_id))

                conn.commit()

        except Exception as e:
            print(f"  [ERROR] Processing email: {e}")
            continue

    mail.logout()

    # Alert William for hot replies
    if hot_replies and not dry_run:
        _alert_hot_replies(hot_replies)

    conn.close()

    print(f"\n  Total replies: {len(replies)}")
    print(f"  Hot (interested): {len(hot_replies)}")
    return replies


def _alert_hot_replies(hot_replies: list):
    """Send SMS to William for interested replies."""
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        print("  [WARN] Twilio not configured — can't alert for hot replies")
        return

    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        for reply in hot_replies:
            deal = reply.get("deal", {})
            company = deal.get("company", "Unknown")
            contact = deal.get("contact_name", "")
            phone = deal.get("contact_phone", "")

            msg = (
                f"HOT LEAD REPLY: {company}\n"
                f"Contact: {contact}\n"
                f"Phone: {phone}\n"
                f"Said: {reply['body_preview'][:100]}\n"
                f"Call them NOW!"
            )

            client.messages.create(
                body=msg, from_=TWILIO_PHONE_NUMBER, to=WILLIAM_PHONE
            )
            print(f"  [ALERT] SMS sent to William for {company}")
    except Exception as e:
        print(f"  [ERROR] Alert SMS failed: {e}")


if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    hours = 24
    for arg in sys.argv[1:]:
        if arg.startswith("--hours="):
            hours = int(arg.split("=")[1])
    check_replies(hours=hours, dry_run=dry)
