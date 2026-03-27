#!/usr/bin/env python3
"""
COMPLETE CALL LOGGING - Does everything in ONE action:
1. Logs call to outreach_log
2. Updates deal stage
3. Sends follow-up email (if positive outcome + email provided)
4. Sets follow-up reminder date
5. Returns confirmation with all IDs

NO MORE "logged!" without execution.
"""

import sqlite3
import smtplib
import os
import sys
import json
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv('/home/clawdbot/dev-sandbox/.env')

DB_PATH = '/home/clawdbot/dev-sandbox/projects/lead-generation/sales-pipeline/data/pipeline.db'
SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_USER = os.getenv('SMTP_USERNAME')
SMTP_PASS = os.getenv('SMTP_PASSWORD')
SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'wmarceau@marceausolutions.com')
SENDER_NAME = os.getenv('SENDER_NAME', 'William Marceau')

POSITIVE_OUTCOMES = ['interested', 'callback', 'email_requested', 'demo_scheduled', 'send_info']
STAGE_MAP = {
    'interested': 'Qualified',
    'callback': 'Contacted',
    'email_requested': 'Contacted',
    'demo_scheduled': 'Demo Scheduled',
    'send_info': 'Contacted',
    'not_interested': 'Closed Lost',
    'voicemail': 'Contacted',
    'no_answer': 'Intake',
    'wrong_number': 'Closed Lost',
    'language_barrier': 'Contacted',
}


def log_call_complete(
    company: str,
    contact_name: str = "",
    contact_email: str = "",
    contact_phone: str = "",
    outcome: str = "contacted",
    notes: str = "",
    send_email: bool = True
) -> dict:
    """
    Complete call logging - logs, updates stage, sends email, sets reminder.
    Returns dict with all confirmation IDs.
    """
    
    result = {
        "company": company,
        "contact_name": contact_name,
        "outcome": outcome,
        "actions_taken": [],
        "errors": []
    }
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # 1. Find or create deal
        cursor.execute("SELECT id, stage FROM deals WHERE company = ?", (company,))
        deal_row = cursor.fetchone()
        
        if deal_row:
            deal_id = deal_row['id']
            result["deal_id"] = deal_id
            result["actions_taken"].append(f"Found existing deal #{deal_id}")
        else:
            cursor.execute("""
                INSERT INTO deals (company, contact_name, contact_email, contact_phone, stage, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'Intake', datetime('now'), datetime('now'))
            """, (company, contact_name, contact_email, contact_phone))
            deal_id = cursor.lastrowid
            result["deal_id"] = deal_id
            result["actions_taken"].append(f"Created new deal #{deal_id}")
        
        # 2. Update contact info if provided
        if contact_name or contact_email or contact_phone:
            updates = []
            params = []
            if contact_name:
                updates.append("contact_name = ?")
                params.append(contact_name)
            if contact_email:
                updates.append("contact_email = ?")
                params.append(contact_email)
            if contact_phone:
                updates.append("contact_phone = ?")
                params.append(contact_phone)
            updates.append("updated_at = datetime('now')")
            params.append(deal_id)
            
            cursor.execute(f"UPDATE deals SET {', '.join(updates)} WHERE id = ?", params)
            result["actions_taken"].append("Updated contact info")
        
        # 3. Update stage based on outcome
        new_stage = STAGE_MAP.get(outcome, 'Contacted')
        cursor.execute("UPDATE deals SET stage = ?, updated_at = datetime('now') WHERE id = ?", (new_stage, deal_id))
        result["new_stage"] = new_stage
        result["actions_taken"].append(f"Updated stage to '{new_stage}'")
        
        # 4. Set follow-up date (3 days for positive, 7 days for neutral)
        if outcome in POSITIVE_OUTCOMES:
            follow_up_days = 3
        else:
            follow_up_days = 7
        follow_up_date = (datetime.now() + timedelta(days=follow_up_days)).strftime('%Y-%m-%d')
        cursor.execute("UPDATE deals SET next_action_date = ?, next_action = ? WHERE id = ?", 
                      (follow_up_date, f"Follow up - {outcome}", deal_id))
        result["follow_up_date"] = follow_up_date
        result["actions_taken"].append(f"Set follow-up for {follow_up_date}")
        
        # 5. Log to outreach_log
        cursor.execute("""
            INSERT INTO outreach_log (deal_id, company, contact, channel, message_summary, response, follow_up_date, created_at, tower)
            VALUES (?, ?, ?, 'Call', ?, ?, ?, datetime('now'), 'digital-ai-services')
        """, (deal_id, company, contact_name, notes or f"Call outcome: {outcome}", outcome, follow_up_date))
        outreach_id = cursor.lastrowid
        result["outreach_log_id"] = outreach_id
        result["actions_taken"].append(f"Logged to outreach_log #{outreach_id}")
        
        conn.commit()
        
        # 6. Send follow-up email if positive outcome and email provided
        if send_email and outcome in POSITIVE_OUTCOMES and contact_email:
            email_result = send_followup_email(contact_email, company, contact_name)
            if email_result["ok"]:
                result["email_sent"] = True
                result["email_to"] = contact_email
                result["actions_taken"].append(f"Sent follow-up email to {contact_email}")
                
                # Log email to outreach_log
                cursor.execute("""
                    INSERT INTO outreach_log (deal_id, company, contact, channel, message_summary, created_at, tower)
                    VALUES (?, ?, ?, 'Email', 'Follow-up email sent', datetime('now'), 'digital-ai-services')
                """, (deal_id, company, contact_name))
                conn.commit()
                result["actions_taken"].append("Logged email to outreach_log")
            else:
                result["email_sent"] = False
                result["errors"].append(f"Email failed: {email_result.get('error')}")
        else:
            if not contact_email:
                result["email_sent"] = False
                result["actions_taken"].append("No email sent (no email address)")
            elif outcome not in POSITIVE_OUTCOMES:
                result["email_sent"] = False  
                result["actions_taken"].append(f"No email sent (outcome '{outcome}' not positive)")
        
        result["success"] = True
        
    except Exception as e:
        result["success"] = False
        result["errors"].append(str(e))
        conn.rollback()
    
    finally:
        conn.close()
    
    return result


def send_followup_email(to_email: str, company_name: str, contact_name: str = "") -> dict:
    """Send follow-up email."""
    
    first_name = contact_name.split()[0] if contact_name else "there"
    
    subject = f"Following up — {company_name}"
    
    html_body = f"""
<p>Hi {first_name},</p>

<p>Great speaking with you! As promised, here's more info about what I do.</p>

<p>I help local businesses like {company_name} automate the stuff that eats up your day — missed calls, scheduling, follow-ups. The AI handles admin so your team can focus on real work.</p>

<p><strong>What that looks like:</strong></p>
<ul>
    <li>Every call answered — even at 2am</li>
    <li>Appointments booked automatically</li>
    <li>Follow-up texts/emails without lifting a finger</li>
</ul>

<p>Try it now — call <strong>(855) 239-9364</strong> and talk to my AI assistant.</p>

<p>Open to a quick 15-min call this week?</p>

<p>Best,<br>
<strong>William Marceau</strong><br>
Marceau Solutions<br>
(239) 331-0576<br>
<a href="https://marceausolutions.com/ai-automation">marceausolutions.com/ai-automation</a></p>
"""
    
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
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def verify_contact_history(company: str) -> dict:
    """
    Check ACTUAL contact history for a company.
    Use this before generating "warm" scripts.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    result = {
        "company": company,
        "in_database": False,
        "calls": [],
        "emails": [],
        "is_warm": False
    }
    
    # Check deals
    cursor.execute("SELECT * FROM deals WHERE company LIKE ?", (f"%{company}%",))
    deal = cursor.fetchone()
    
    if deal:
        result["in_database"] = True
        result["deal_id"] = deal['id']
        result["stage"] = deal['stage']
        result["contact_name"] = deal['contact_name']
        result["contact_email"] = deal['contact_email']
        
        # Get outreach history
        cursor.execute("""
            SELECT channel, message_summary, response, created_at 
            FROM outreach_log 
            WHERE deal_id = ? 
            ORDER BY created_at DESC
        """, (deal['id'],))
        
        for row in cursor.fetchall():
            entry = {
                "channel": row['channel'],
                "summary": row['message_summary'],
                "response": row['response'],
                "date": row['created_at']
            }
            if row['channel'] == 'Call':
                result["calls"].append(entry)
            elif row['channel'] == 'Email':
                result["emails"].append(entry)
        
        # Determine if warm
        result["is_warm"] = len(result["calls"]) > 0 or len(result["emails"]) > 0
    
    conn.close()
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Log call: python log_call_complete.py log <company> <contact_name> <email> <outcome> [notes]")
        print("  Verify:   python log_call_complete.py verify <company>")
        print("")
        print("Outcomes: interested, callback, email_requested, demo_scheduled, send_info, not_interested, voicemail, no_answer, wrong_number, language_barrier")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "log" and len(sys.argv) >= 5:
        company = sys.argv[2]
        contact = sys.argv[3]
        email = sys.argv[4] if len(sys.argv) > 4 else ""
        outcome = sys.argv[5] if len(sys.argv) > 5 else "contacted"
        notes = sys.argv[6] if len(sys.argv) > 6 else ""
        
        result = log_call_complete(company, contact, email, "", outcome, notes)
        print(json.dumps(result, indent=2))
        
    elif action == "verify" and len(sys.argv) >= 3:
        company = sys.argv[2]
        result = verify_contact_history(company)
        print(json.dumps(result, indent=2))
        
    else:
        print("Invalid arguments. Run without args for usage.")
