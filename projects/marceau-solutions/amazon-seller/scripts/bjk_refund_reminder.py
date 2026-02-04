#!/usr/bin/env python3
"""
BJK University Refund Follow-Up Reminder

Sends email reminders at 7 and 10 days after refund request.
Refund requested: 01/31/2026
- Day 7 reminder: 02/07/2026
- Day 10 reminder: 02/10/2026
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent.parent.parent / ".env")

# Email configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
TO_EMAIL = "wmarceau@marceausolutions.com"

# Refund details
REFUND_REQUEST_DATE = datetime(2026, 1, 31)
CONTRACT_REF = "ZOBYK-5KYKJ-5ZQJB-U4VKN"
TRANSACTION_ID = "11650944065"
AMOUNT_PAID = 5000.00
EXPECTED_REFUND_MIN = 4900.00
EXPECTED_REFUND_MAX = 4950.00
DEADLINE = datetime(2026, 3, 2)  # 30-day window ends

FOLLOWUP_EMAIL = """Subject: Refund Request Follow-Up - Contract ZOBYK-5KYKJ-5ZQJB-U4VKN

To Whom It May Concern,

I am writing to follow up on my refund request submitted on January 31, 2026, the same day I signed the Certified AI Amazon Seller VIP Program Agreement.

Per Section 2.3.1 of the agreement, I am exercising my right to the unconditional 30-day money-back guarantee.

Regarding the transaction fee: During my conversation with Aaron Civitarese, it was verbally agreed that the transaction fee would be 1-2%, not the 5% stated in the written contract. I am requesting that BJK University honor the terms discussed with your representative.

Refund Details:
- Contract Reference: ZOBYK-5KYKJ-5ZQJB-U4VKN
- Transaction ID: 11650944065
- Amount Paid: $5,000.00
- Expected Refund: $4,900.00 - $4,950.00 (per verbal agreement of 1-2% fee)

Please provide an update on the expected timeline for processing this refund.

Regards,
William Marceau
wmarceau@marceausolutions.com
(239) 398-5676"""


def send_email(subject: str, body: str):
    """Send an email reminder."""
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print(f"SMTP not configured. Would send email:")
        print(f"Subject: {subject}")
        print(f"Body:\n{body}")
        return False

    msg = MIMEMultipart()
    msg["From"] = SMTP_USERNAME
    msg["To"] = TO_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_USERNAME, TO_EMAIL, msg.as_string())
        print(f"Email sent: {subject}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def check_and_send_reminder():
    """Check if it's time to send a reminder and send it."""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    days_since_request = (today - REFUND_REQUEST_DATE).days

    print(f"Days since refund request: {days_since_request}")
    print(f"30-day deadline: {DEADLINE.strftime('%B %d, %Y')}")

    if days_since_request == 7:
        subject = "REMINDER: Check BJK University Refund Status (Day 7)"
        body = f"""Hi William,

It's been 7 days since your BJK University refund request on 01/31/2026.

ACTION REQUIRED:
1. Check your bank statement for a refund from BJK Institutions Inc.
2. Expected amount: ${EXPECTED_REFUND_MIN:,.2f} - ${EXPECTED_REFUND_MAX:,.2f} (after 1-2% fee per Aaron's verbal agreement)

If NOT received yet, don't worry - give it a few more days.

Key Details:
- Contract Reference: {CONTRACT_REF}
- Transaction ID: {TRANSACTION_ID}
- 30-day deadline: {DEADLINE.strftime('%B %d, %Y')}

- Your AI Assistant
"""
        send_email(subject, body)

    elif days_since_request == 10:
        subject = "URGENT: BJK Refund Not Received? Send Follow-Up NOW (Day 10)"
        body = f"""Hi William,

It's been 10 DAYS since your BJK University refund request.

IF YOU HAVE NOT RECEIVED YOUR REFUND, send this email NOW to billing@bjkuniversity.com:

---
{FOLLOWUP_EMAIL}
---

30-day deadline: {DEADLINE.strftime('%B %d, %Y')}

- Your AI Assistant
"""
        send_email(subject, body)

    elif days_since_request < 7:
        print(f"Too early for reminder. Next reminder in {7 - days_since_request} days.")
    elif days_since_request > 10:
        print("Past reminder window. Check if refund was received.")
    else:
        print(f"Day {days_since_request} - between reminders. Day 10 reminder in {10 - days_since_request} days.")


def send_reminder_now(day: int):
    """Manually send a specific day's reminder."""
    if day == 7:
        subject = "REMINDER: Check BJK University Refund Status (Day 7)"
        body = f"""Hi William,

It's been 7 days since your BJK University refund request on 01/31/2026.

ACTION REQUIRED:
1. Check your bank statement for a refund from BJK Institutions Inc.
2. Expected amount: ${EXPECTED_REFUND_MIN:,.2f} - ${EXPECTED_REFUND_MAX:,.2f} (after 1-2% fee per Aaron's verbal agreement)

If NOT received yet, don't worry - give it a few more days.

Key Details:
- Contract Reference: {CONTRACT_REF}
- Transaction ID: {TRANSACTION_ID}
- 30-day deadline: {DEADLINE.strftime('%B %d, %Y')}

- Your AI Assistant
"""
        send_email(subject, body)

    elif day == 10:
        subject = "URGENT: BJK Refund Not Received? Send Follow-Up NOW (Day 10)"
        body = f"""Hi William,

It's been 10 DAYS since your BJK University refund request.

IF YOU HAVE NOT RECEIVED YOUR REFUND, send this email NOW to billing@bjkuniversity.com:

---
{FOLLOWUP_EMAIL}
---

30-day deadline: {DEADLINE.strftime('%B %d, %Y')}

- Your AI Assistant
"""
        send_email(subject, body)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--day7":
            send_reminder_now(7)
        elif sys.argv[1] == "--day10":
            send_reminder_now(10)
        elif sys.argv[1] == "--status":
            today = datetime.now()
            days_since = (today - REFUND_REQUEST_DATE).days
            print(f"Refund requested: {REFUND_REQUEST_DATE.strftime('%B %d, %Y')}")
            print(f"Days elapsed: {days_since}")
            print(f"Day 7 reminder: {(REFUND_REQUEST_DATE + timedelta(days=7)).strftime('%B %d, %Y')}")
            print(f"Day 10 reminder: {(REFUND_REQUEST_DATE + timedelta(days=10)).strftime('%B %d, %Y')}")
            print(f"30-day deadline: {DEADLINE.strftime('%B %d, %Y')}")
        else:
            print("Usage: python bjk_refund_reminder.py [--day7|--day10|--status]")
    else:
        check_and_send_reminder()
