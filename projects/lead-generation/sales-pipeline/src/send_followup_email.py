#!/usr/bin/env python3
"""
Send follow-up email after a call is logged.
This should be triggered automatically when a positive call outcome is logged.
"""

import smtplib
import os
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv('/home/clawdbot/dev-sandbox/.env')

SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_USER = os.getenv('SMTP_USERNAME')
SMTP_PASS = os.getenv('SMTP_PASSWORD')
SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'wmarceau@marceausolutions.com')
SENDER_NAME = os.getenv('SENDER_NAME', 'William Marceau')

DB_PATH = '/home/clawdbot/dev-sandbox/projects/shared/sales-pipeline/data/pipeline.db'

def get_email_template(company_name: str, contact_name: str, industry: str = "business") -> tuple[str, str]:
    """Generate subject and HTML body for follow-up email."""
    
    first_name = contact_name.split()[0] if contact_name else "there"
    
    subject = f"Following up — {company_name}"
    
    html_body = f"""
<p>Hi {first_name},</p>

<p>Great speaking with you earlier! As promised, I wanted to send over a bit more info about what I do.</p>

<p>I help local businesses like {company_name} automate the stuff that eats up your day — missed calls, appointment scheduling, follow-ups, after-hours inquiries. The AI handles the admin so your team can focus on actual work.</p>

<p><strong>Here's what that looks like:</strong></p>
<ul>
    <li>Every call answered — even at 2am or when you're on a job</li>
    <li>Appointments booked automatically into your calendar</li>
    <li>Follow-up texts/emails sent without lifting a finger</li>
    <li>No more leads slipping through the cracks</li>
</ul>

<p>You can even try it right now — call <strong>(855) 239-9364</strong> and talk to my AI assistant. See if it feels like a robot or a real person.</p>

<p>Would you be open to a quick 15-minute call this week to see if it's a fit?</p>

<p>Best,<br>
<strong>William Marceau</strong><br>
Marceau Solutions<br>
(239) 331-0576<br>
wmarceau@marceausolutions.com<br>
<a href="https://marceausolutions.com/ai-automation">marceausolutions.com/ai-automation</a></p>
"""
    return subject, html_body


def send_followup_email(
    to_email: str,
    company_name: str,
    contact_name: str = "",
    industry: str = "business"
) -> dict:
    """Send a follow-up email and log it to the database."""
    
    if not to_email:
        return {"ok": False, "error": "No email address provided"}
    
    subject, html_body = get_email_template(company_name, contact_name, industry)
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg['To'] = to_email
    msg.attach(MIMEText(html_body, 'html'))
    
    try:
        with smtplib.SMTP(SMTP_HOST, 587) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SENDER_EMAIL, [to_email], msg.as_string())
        
        # Log to database
        log_email_sent(company_name, contact_name, to_email, subject)
        
        return {"ok": True, "message": f"Email sent to {to_email}"}
    
    except Exception as e:
        return {"ok": False, "error": str(e)}


def log_email_sent(company_name: str, contact_name: str, email: str, subject: str):
    """Log the sent email to outreach_log."""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Find deal_id
    cursor.execute("SELECT id FROM deals WHERE company = ?", (company_name,))
    row = cursor.fetchone()
    deal_id = row[0] if row else None
    
    cursor.execute("""
        INSERT INTO outreach_log (deal_id, company, contact, channel, message_summary, created_at, tower)
        VALUES (?, ?, ?, 'Email', ?, datetime('now'), 'digital-ai-services')
    """, (deal_id, company_name, contact_name, f"Follow-up email sent: {subject}"))
    
    # Update deal stage to "Contacted" if still at Intake
    if deal_id:
        cursor.execute("""
            UPDATE deals SET stage = 'Contacted', updated_at = datetime('now')
            WHERE id = ? AND stage = 'Intake'
        """, (deal_id,))
    
    conn.commit()
    conn.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 4:
        email = sys.argv[1]
        company = sys.argv[2]
        contact = sys.argv[3] if len(sys.argv) > 3 else ""
        result = send_followup_email(email, company, contact)
        print(result)
    else:
        print("Usage: python send_followup_email.py <email> <company_name> [contact_name]")
