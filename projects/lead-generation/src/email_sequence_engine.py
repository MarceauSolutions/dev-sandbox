#!/usr/bin/env python3
"""
Email Sequence Engine — Autonomous cold email outreach via Gmail API.

Replaces manual Apollo.io sequence uploads with fully automated email sending.
Integrates with existing tiering system (Tier 1 deep personalized, Tier 2 batch).

Features:
- Gmail API sending (from wmarceau26@gmail.com)
- Template personalization (first_name, company_name, pain_points)
- Multi-step sequences (Day 0, Day 3, Day 7)
- Reply detection → auto-stop sequence
- Open tracking via tracking pixel
- Rate limiting (50 emails/day max)
- Full integration with pipeline.db

Usage:
    # Enroll a lead in sequence
    python execution/email_sequence_engine.py enroll --deal-id 123 --sequence general_ai
    
    # Process due emails (run via cron)
    python execution/email_sequence_engine.py process
    
    # Check for replies and stop sequences
    python execution/email_sequence_engine.py check-replies
    
    # View sequence status
    python execution/email_sequence_engine.py status

Cron setup:
    # Send due emails at 9am ET
    0 13 * * 1-5 cd /home/clawdbot/dev-sandbox && python3 execution/email_sequence_engine.py process
    
    # Check replies every 30 min during business hours
    */30 13-22 * * 1-5 cd /home/clawdbot/dev-sandbox && python3 execution/email_sequence_engine.py check-replies
"""

import os
import sys
import json
import base64
import sqlite3
import logging
import argparse
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, asdict
import hashlib

# Google API imports
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Setup paths
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv
load_dotenv(REPO_ROOT / ".env")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
GMAIL_TOKEN_PATH = REPO_ROOT / "token.json"
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify"
]
PIPELINE_DB = Path("/home/clawdbot/data/pipeline.db")
SEQUENCE_DB = REPO_ROOT / "data" / "email_sequences.db"
TEMPLATES_FILE = REPO_ROOT / "docs" / "apollo-sequence-templates.txt"

# Rate limits
MAX_EMAILS_PER_DAY = 50
SEND_DELAY_SECONDS = 30  # Between emails to avoid spam flags

# Sender info
SENDER_EMAIL = "wmarceau26@gmail.com"
SENDER_NAME = "William Marceau"
CALENDLY_LINK = "https://calendly.com/wmarceau/ai-services-discovery-call"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class EmailTemplate:
    """Single email template in a sequence."""
    step: int
    day: int
    subject: str
    body: str


@dataclass
class EmailSequence:
    """Full email sequence definition."""
    name: str
    description: str
    templates: List[EmailTemplate]


@dataclass
class SequenceEnrollment:
    """A lead enrolled in an email sequence."""
    id: int
    deal_id: int
    sequence_name: str
    current_step: int
    status: str  # active, completed, replied, unsubscribed, bounced
    enrolled_at: str
    next_send_at: str
    last_sent_at: Optional[str]
    emails_sent: int
    emails_opened: int


# =============================================================================
# DATABASE SETUP
# =============================================================================

def init_sequence_db():
    """Initialize the email sequences database."""
    SEQUENCE_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(SEQUENCE_DB))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id INTEGER NOT NULL,
            sequence_name TEXT NOT NULL,
            current_step INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            enrolled_at TEXT NOT NULL,
            next_send_at TEXT NOT NULL,
            last_sent_at TEXT,
            emails_sent INTEGER DEFAULT 0,
            emails_opened INTEGER DEFAULT 0,
            contact_email TEXT,
            contact_name TEXT,
            company_name TEXT,
            personalization JSON,
            UNIQUE(deal_id, sequence_name)
        );
        
        CREATE TABLE IF NOT EXISTS sent_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enrollment_id INTEGER NOT NULL,
            step INTEGER NOT NULL,
            message_id TEXT,
            thread_id TEXT,
            subject TEXT,
            sent_at TEXT NOT NULL,
            opened_at TEXT,
            replied_at TEXT,
            tracking_id TEXT UNIQUE,
            FOREIGN KEY (enrollment_id) REFERENCES enrollments(id)
        );
        
        CREATE TABLE IF NOT EXISTS daily_stats (
            date TEXT PRIMARY KEY,
            emails_sent INTEGER DEFAULT 0,
            emails_opened INTEGER DEFAULT 0,
            replies_received INTEGER DEFAULT 0
        );
        
        CREATE INDEX IF NOT EXISTS idx_enrollments_status ON enrollments(status);
        CREATE INDEX IF NOT EXISTS idx_enrollments_next_send ON enrollments(next_send_at);
        CREATE INDEX IF NOT EXISTS idx_sent_emails_thread ON sent_emails(thread_id);
    """)
    conn.commit()
    conn.close()
    logger.info(f"Sequence database initialized: {SEQUENCE_DB}")


def get_sequence_db():
    """Get sequence database connection."""
    init_sequence_db()
    conn = sqlite3.connect(str(SEQUENCE_DB))
    conn.row_factory = sqlite3.Row
    return conn


def get_pipeline_db():
    """Get pipeline database connection."""
    conn = sqlite3.connect(str(PIPELINE_DB))
    conn.row_factory = sqlite3.Row
    return conn


# =============================================================================
# GMAIL API
# =============================================================================

class GmailClient:
    """Gmail API client for sending and reading emails."""
    
    def __init__(self):
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Gmail API."""
        creds = None
        
        if GMAIL_TOKEN_PATH.exists():
            creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN_PATH), GMAIL_SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Save refreshed token
                GMAIL_TOKEN_PATH.write_text(creds.to_json())
            else:
                raise Exception("Gmail credentials not found or invalid. Run OAuth flow first.")
        
        self.service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail API authenticated")
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        reply_to_message_id: str = None,
        thread_id: str = None,
        tracking_id: str = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Send an email via Gmail API.
        
        Returns:
            Tuple of (message_id, thread_id) or (None, None) on failure
        """
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['To'] = to
            message['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
            message['Subject'] = subject
            
            # Add reply headers if this is a follow-up
            if reply_to_message_id:
                message['In-Reply-To'] = reply_to_message_id
                message['References'] = reply_to_message_id
            
            # Add tracking pixel if tracking_id provided
            if tracking_id:
                tracking_pixel = f'<img src="https://track.marceausolutions.com/pixel/{tracking_id}" width="1" height="1" />'
                body_with_tracking = body + f"\n\n{tracking_pixel}"
            else:
                body_with_tracking = body
            
            # Plain text version
            text_part = MIMEText(body, 'plain')
            message.attach(text_part)
            
            # HTML version (for tracking)
            html_body = body.replace('\n', '<br>')
            if tracking_id:
                html_body += f'<img src="https://track.marceausolutions.com/pixel/{tracking_id}" width="1" height="1" style="display:none" />'
            html_part = MIMEText(html_body, 'html')
            message.attach(html_part)
            
            # Encode
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send
            body_data = {'raw': raw}
            if thread_id:
                body_data['threadId'] = thread_id
            
            result = self.service.users().messages().send(
                userId='me',
                body=body_data
            ).execute()
            
            msg_id = result.get('id')
            thrd_id = result.get('threadId')
            
            logger.info(f"Email sent to {to}: {subject[:50]}... (msg_id: {msg_id})")
            return msg_id, thrd_id
            
        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            return None, None
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return None, None
    
    def check_for_replies(self, since_hours: int = 24) -> List[Dict]:
        """
        Check for replies to our sent emails.
        
        Returns list of replies with thread_id, from_email, subject, snippet
        """
        try:
            # Search for emails in threads we started
            query = f"is:inbox newer_than:{since_hours}h"
            
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=50
            ).execute()
            
            messages = results.get('messages', [])
            replies = []
            
            for msg in messages:
                # Get full message
                full_msg = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'In-Reply-To']
                ).execute()
                
                headers = {h['name']: h['value'] for h in full_msg.get('payload', {}).get('headers', [])}
                
                # Check if it's a reply (has In-Reply-To header) and not from us
                from_email = headers.get('From', '')
                if 'In-Reply-To' in headers and SENDER_EMAIL not in from_email:
                    replies.append({
                        'message_id': msg['id'],
                        'thread_id': full_msg.get('threadId'),
                        'from': from_email,
                        'subject': headers.get('Subject', ''),
                        'snippet': full_msg.get('snippet', '')[:200]
                    })
            
            logger.info(f"Found {len(replies)} replies in last {since_hours} hours")
            return replies
            
        except HttpError as e:
            logger.error(f"Gmail API error checking replies: {e}")
            return []


# =============================================================================
# TEMPLATE PARSING
# =============================================================================

def parse_templates() -> Dict[str, EmailSequence]:
    """Parse email templates from apollo-sequence-templates.txt."""
    sequences = {}
    
    if not TEMPLATES_FILE.exists():
        logger.warning(f"Templates file not found: {TEMPLATES_FILE}")
        return sequences
    
    content = TEMPLATES_FILE.read_text()
    
    # Split by sequence headers (lines starting with "SEQUENCE")
    sequence_blocks = re.split(r'\n─+\nSEQUENCE\s+([A-Z]):\s*(.+?)\n', content)
    
    # First block is header, skip it
    i = 1
    while i < len(sequence_blocks) - 2:
        seq_letter = sequence_blocks[i]
        seq_name = sequence_blocks[i + 1].strip()
        seq_content = sequence_blocks[i + 2]
        
        # Parse individual steps
        templates = []
        step_blocks = re.split(r'\n\s+Step\s+(\d+)\s+—\s+Day\s+(\d+)', seq_content)
        
        j = 1
        while j < len(step_blocks) - 2:
            step_num = int(step_blocks[j])
            day_num = int(step_blocks[j + 1])
            step_content = step_blocks[j + 2]
            
            # Extract subject
            subject_match = re.search(r'Subject:\s*(.+?)\n', step_content)
            subject = subject_match.group(1).strip() if subject_match else f"Following up - Step {step_num}"
            
            # Extract body (everything after the dots line)
            body_match = re.search(r'\.{10,}\n(.+?)(?=\n\s+Step|\n─|$)', step_content, re.DOTALL)
            body = body_match.group(1).strip() if body_match else ""
            
            if body:
                templates.append(EmailTemplate(
                    step=step_num,
                    day=day_num,
                    subject=subject,
                    body=body
                ))
            
            j += 3
        
        if templates:
            # Create sequence name from letter and description
            seq_key = f"sequence_{seq_letter.lower()}"
            sequences[seq_key] = EmailSequence(
                name=seq_key,
                description=seq_name,
                templates=sorted(templates, key=lambda t: t.step)
            )
        
        i += 3
    
    # Add default general AI sequence if not parsed
    if not sequences:
        sequences['general_ai'] = EmailSequence(
            name='general_ai',
            description='General AI Services',
            templates=[
                EmailTemplate(
                    step=1, day=0,
                    subject="{{first_name}} — built something for businesses like yours",
                    body="""Hi {{first_name}},

I came across {{company_name}} and I've already built systems for businesses just like yours here in Naples — so I wanted to reach out directly.

What I do: I build AI-powered intake systems that capture every lead, follow up automatically, and book appointments 24/7 — without adding headcount. The businesses I work with typically stop losing 30-40% of their inbound leads within the first 30 days.

Not sure if it's the right fit for you, but worth a 15-minute conversation to find out.

William Marceau
Marceau Solutions | (239) 398-5676
""" + CALENDLY_LINK
                ),
                EmailTemplate(
                    step=2, day=3,
                    subject="{{first_name}} — what this looks like for {{company_name}}",
                    body="""{{first_name}},

I put together a quick look at what the system would actually do for {{company_name}} specifically — not a generic demo, but the exact automations that make sense for your type of business.

The short version: every inquiry that comes in after hours, on weekends, or when your team is heads-down gets answered, qualified, and either booked or followed up with automatically. Nothing falls through the cracks.

We build the whole thing during a free 2-week onboarding — no cost until you've seen it working.

If you want to see it: """ + CALENDLY_LINK + """

William"""
                ),
                EmailTemplate(
                    step=3, day=7,
                    subject="{{first_name}} — last one from me",
                    body="""{{first_name}},

I'll keep this short — I only take 5 clients per quarter because I build every system personally. I have 2 spots left for Q2.

If you're not interested, no worries — I won't keep following up. But if you want to see what this could do for {{company_name}}, here's my calendar: """ + CALENDLY_LINK + """

Either way, good luck with the business.

William"""
                )
            ]
        )
    
    logger.info(f"Parsed {len(sequences)} email sequences")
    return sequences


def personalize_template(template: EmailTemplate, personalization: Dict) -> Tuple[str, str]:
    """
    Apply personalization to email template.
    
    Handles: {{first_name}}, {{company_name}}, {{pain_points}}, etc.
    """
    subject = template.subject
    body = template.body
    
    # Default values
    defaults = {
        'first_name': 'there',
        'company_name': 'your company',
        'pain_points': '',
        'industry': '',
    }
    
    # Merge with provided personalization
    data = {**defaults, **personalization}
    
    # Handle Jinja-style defaults: {{first_name | default: "Hey"}}
    def replace_with_default(match):
        var_name = match.group(1).strip()
        default_val = match.group(2).strip().strip('"\'') if match.group(2) else ''
        return data.get(var_name, default_val) or default_val
    
    pattern = r'\{\{(\w+)(?:\s*\|\s*default:\s*([^}]+))?\}\}'
    
    subject = re.sub(pattern, replace_with_default, subject)
    body = re.sub(pattern, replace_with_default, body)
    
    # Simple replacements for any remaining
    for key, value in data.items():
        subject = subject.replace(f'{{{{{key}}}}}', str(value))
        body = body.replace(f'{{{{{key}}}}}', str(value))
    
    return subject, body


# =============================================================================
# SEQUENCE MANAGEMENT
# =============================================================================

def enroll_lead(
    deal_id: int,
    sequence_name: str = 'general_ai',
    personalization: Dict = None
) -> Optional[int]:
    """
    Enroll a lead in an email sequence.
    
    Returns enrollment_id or None if failed.
    """
    # Get lead info from pipeline DB
    pipeline = get_pipeline_db()
    deal = pipeline.execute(
        "SELECT * FROM deals WHERE id = ?", (deal_id,)
    ).fetchone()
    pipeline.close()
    
    if not deal:
        logger.error(f"Deal {deal_id} not found in pipeline")
        return None
    
    contact_email = deal['contact_email']
    if not contact_email:
        logger.error(f"Deal {deal_id} has no email address")
        return None
    
    # Prepare personalization
    pers = personalization or {}
    pers.setdefault('first_name', deal['contact_name'].split()[0] if deal['contact_name'] else 'there')
    pers.setdefault('company_name', deal['company'] or 'your company')
    pers.setdefault('industry', deal['industry'] or '')
    pers.setdefault('pain_points', deal['pain_points'] or '')
    
    # Calculate first send time (next business day 9am ET if after 5pm)
    now = datetime.now()
    if now.hour >= 17 or now.weekday() >= 5:  # After 5pm or weekend
        # Next business day
        days_ahead = 1
        next_day = now + timedelta(days=days_ahead)
        while next_day.weekday() >= 5:  # Skip weekends
            days_ahead += 1
            next_day = now + timedelta(days=days_ahead)
        next_send = next_day.replace(hour=9, minute=0, second=0, microsecond=0)
    else:
        next_send = now
    
    # Insert enrollment
    seq_db = get_sequence_db()
    try:
        cursor = seq_db.execute("""
            INSERT INTO enrollments (
                deal_id, sequence_name, current_step, status,
                enrolled_at, next_send_at, contact_email, contact_name,
                company_name, personalization
            ) VALUES (?, ?, 1, 'active', ?, ?, ?, ?, ?, ?)
        """, (
            deal_id, sequence_name, 
            now.isoformat(), next_send.isoformat(),
            contact_email, deal['contact_name'], deal['company'],
            json.dumps(pers)
        ))
        seq_db.commit()
        enrollment_id = cursor.lastrowid
        
        logger.info(f"Enrolled deal {deal_id} ({contact_email}) in {sequence_name}, first send: {next_send}")
        
        # Update pipeline stage
        pipeline = get_pipeline_db()
        pipeline.execute(
            "UPDATE deals SET stage = 'Outreached', updated_at = datetime('now') WHERE id = ?",
            (deal_id,)
        )
        pipeline.commit()
        pipeline.close()
        
        return enrollment_id
        
    except sqlite3.IntegrityError:
        logger.warning(f"Deal {deal_id} already enrolled in {sequence_name}")
        return None
    finally:
        seq_db.close()


def process_due_emails(dry_run: bool = False) -> Dict[str, int]:
    """
    Process all emails due to be sent.
    
    Returns stats dict with counts.
    """
    stats = {'processed': 0, 'sent': 0, 'skipped': 0, 'errors': 0}
    
    # Check daily limit
    today = datetime.now().strftime('%Y-%m-%d')
    seq_db = get_sequence_db()
    
    daily_row = seq_db.execute(
        "SELECT emails_sent FROM daily_stats WHERE date = ?", (today,)
    ).fetchone()
    daily_sent = daily_row['emails_sent'] if daily_row else 0
    
    if daily_sent >= MAX_EMAILS_PER_DAY:
        logger.warning(f"Daily limit reached ({MAX_EMAILS_PER_DAY}). Skipping.")
        seq_db.close()
        return stats
    
    remaining_today = MAX_EMAILS_PER_DAY - daily_sent
    
    # Get active enrollments due for sending
    now = datetime.now().isoformat()
    enrollments = seq_db.execute("""
        SELECT * FROM enrollments 
        WHERE status = 'active' AND next_send_at <= ?
        ORDER BY next_send_at
        LIMIT ?
    """, (now, remaining_today)).fetchall()
    
    if not enrollments:
        logger.info("No emails due to send")
        seq_db.close()
        return stats
    
    # Load sequences
    sequences = parse_templates()
    
    # Initialize Gmail client
    gmail = None
    if not dry_run:
        gmail = GmailClient()
    
    import time
    
    for enrollment in enrollments:
        stats['processed'] += 1
        
        sequence = sequences.get(enrollment['sequence_name'])
        if not sequence:
            logger.error(f"Sequence {enrollment['sequence_name']} not found")
            stats['errors'] += 1
            continue
        
        # Get current step template
        current_step = enrollment['current_step']
        template = None
        for t in sequence.templates:
            if t.step == current_step:
                template = t
                break
        
        if not template:
            # Sequence completed
            seq_db.execute(
                "UPDATE enrollments SET status = 'completed' WHERE id = ?",
                (enrollment['id'],)
            )
            logger.info(f"Enrollment {enrollment['id']} completed all steps")
            continue
        
        # Personalize
        pers = json.loads(enrollment['personalization'] or '{}')
        subject, body = personalize_template(template, pers)
        
        # Generate tracking ID
        tracking_id = hashlib.md5(
            f"{enrollment['id']}-{current_step}-{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        if dry_run:
            logger.info(f"[DRY RUN] Would send to {enrollment['contact_email']}: {subject}")
            stats['sent'] += 1
        else:
            # Get previous thread_id if follow-up
            thread_id = None
            prev_email = seq_db.execute(
                "SELECT thread_id FROM sent_emails WHERE enrollment_id = ? ORDER BY step DESC LIMIT 1",
                (enrollment['id'],)
            ).fetchone()
            if prev_email:
                thread_id = prev_email['thread_id']
            
            # Send email
            msg_id, thrd_id = gmail.send_email(
                to=enrollment['contact_email'],
                subject=subject,
                body=body,
                thread_id=thread_id,
                tracking_id=tracking_id
            )
            
            if msg_id:
                # Record sent email
                seq_db.execute("""
                    INSERT INTO sent_emails (
                        enrollment_id, step, message_id, thread_id,
                        subject, sent_at, tracking_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    enrollment['id'], current_step, msg_id, thrd_id,
                    subject, datetime.now().isoformat(), tracking_id
                ))
                
                # Calculate next send time
                next_step = current_step + 1
                next_template = None
                for t in sequence.templates:
                    if t.step == next_step:
                        next_template = t
                        break
                
                if next_template:
                    days_until_next = next_template.day - template.day
                    next_send = datetime.now() + timedelta(days=days_until_next)
                    # Ensure business hours
                    if next_send.weekday() >= 5:
                        next_send += timedelta(days=(7 - next_send.weekday()))
                    next_send = next_send.replace(hour=9, minute=0, second=0)
                    
                    seq_db.execute("""
                        UPDATE enrollments SET 
                            current_step = ?, 
                            next_send_at = ?,
                            last_sent_at = ?,
                            emails_sent = emails_sent + 1
                        WHERE id = ?
                    """, (next_step, next_send.isoformat(), datetime.now().isoformat(), enrollment['id']))
                else:
                    # Last step sent, mark pending completion
                    seq_db.execute("""
                        UPDATE enrollments SET 
                            status = 'completed',
                            last_sent_at = ?,
                            emails_sent = emails_sent + 1
                        WHERE id = ?
                    """, (datetime.now().isoformat(), enrollment['id']))
                
                stats['sent'] += 1
                
                # Rate limiting
                time.sleep(SEND_DELAY_SECONDS)
            else:
                stats['errors'] += 1
    
    # Update daily stats
    seq_db.execute("""
        INSERT INTO daily_stats (date, emails_sent) VALUES (?, ?)
        ON CONFLICT(date) DO UPDATE SET emails_sent = emails_sent + ?
    """, (today, stats['sent'], stats['sent']))
    
    seq_db.commit()
    seq_db.close()
    
    logger.info(f"Processed {stats['processed']} enrollments, sent {stats['sent']} emails")
    return stats


def check_replies() -> int:
    """
    Check for replies and stop sequences accordingly.
    
    Returns count of replies processed.
    """
    gmail = GmailClient()
    replies = gmail.check_for_replies(since_hours=12)
    
    if not replies:
        return 0
    
    seq_db = get_sequence_db()
    processed = 0
    
    for reply in replies:
        # Find matching enrollment by thread_id
        sent_email = seq_db.execute(
            "SELECT enrollment_id FROM sent_emails WHERE thread_id = ?",
            (reply['thread_id'],)
        ).fetchone()
        
        if sent_email:
            # Stop the sequence
            seq_db.execute("""
                UPDATE enrollments SET status = 'replied' WHERE id = ?
            """, (sent_email['enrollment_id'],))
            
            # Update sent_email record
            seq_db.execute("""
                UPDATE sent_emails SET replied_at = ? WHERE thread_id = ?
            """, (datetime.now().isoformat(), reply['thread_id']))
            
            # Get enrollment details for notification
            enrollment = seq_db.execute(
                "SELECT * FROM enrollments WHERE id = ?",
                (sent_email['enrollment_id'],)
            ).fetchone()
            
            if enrollment:
                # Update pipeline deal
                pipeline = get_pipeline_db()
                pipeline.execute("""
                    UPDATE deals SET stage = 'Replied', updated_at = datetime('now')
                    WHERE id = ?
                """, (enrollment['deal_id'],))
                pipeline.commit()
                pipeline.close()
                
                # Queue notification
                try:
                    from execution.notification_policy import notify
                    notify(
                        "client_reply",
                        f"📧 Reply from {enrollment['contact_name']}",
                        f"Company: {enrollment['company_name']}\n\n\"{reply['snippet']}\"",
                        metadata={"deal_id": enrollment['deal_id']},
                        force_immediate=True
                    )
                except ImportError:
                    logger.warning("Could not import notification_policy")
                
                logger.info(f"Stopped sequence for {enrollment['contact_email']} - got reply")
                processed += 1
    
    seq_db.commit()
    seq_db.close()
    
    return processed


def get_status() -> Dict[str, Any]:
    """Get current sequence engine status."""
    seq_db = get_sequence_db()
    
    # Count by status
    status_counts = {}
    for row in seq_db.execute(
        "SELECT status, COUNT(*) as count FROM enrollments GROUP BY status"
    ).fetchall():
        status_counts[row['status']] = row['count']
    
    # Today's stats
    today = datetime.now().strftime('%Y-%m-%d')
    daily = seq_db.execute(
        "SELECT * FROM daily_stats WHERE date = ?", (today,)
    ).fetchone()
    
    # Pending sends
    now = datetime.now().isoformat()
    pending = seq_db.execute(
        "SELECT COUNT(*) as count FROM enrollments WHERE status = 'active' AND next_send_at <= ?",
        (now,)
    ).fetchone()['count']
    
    # Upcoming (next 24h)
    tomorrow = (datetime.now() + timedelta(days=1)).isoformat()
    upcoming = seq_db.execute(
        "SELECT COUNT(*) as count FROM enrollments WHERE status = 'active' AND next_send_at <= ?",
        (tomorrow,)
    ).fetchone()['count']
    
    seq_db.close()
    
    return {
        'enrollments': status_counts,
        'pending_now': pending,
        'upcoming_24h': upcoming,
        'today': {
            'sent': daily['emails_sent'] if daily else 0,
            'opened': daily['emails_opened'] if daily else 0,
            'replies': daily['replies_received'] if daily else 0,
            'limit': MAX_EMAILS_PER_DAY
        }
    }


# =============================================================================
# INTEGRATION WITH DAILY LOOP
# =============================================================================

def enroll_from_pipeline(
    min_score: int = 50,
    max_enrollments: int = 20,
    sequence_name: str = 'general_ai',
    dry_run: bool = False
) -> List[int]:
    """
    Auto-enroll qualified leads from pipeline into email sequence.
    
    Called by daily_loop.py orchestrator.
    """
    pipeline = get_pipeline_db()
    seq_db = get_sequence_db()
    
    # Get already enrolled deal IDs
    enrolled_ids = {row['deal_id'] for row in seq_db.execute(
        "SELECT deal_id FROM enrollments"
    ).fetchall()}
    
    # Get qualified leads not yet enrolled
    leads = pipeline.execute("""
        SELECT * FROM deals 
        WHERE contact_email IS NOT NULL 
          AND contact_email != ''
          AND stage IN ('New Lead', 'Qualified', 'Discovery')
          AND id NOT IN ({})
        ORDER BY created_at DESC
        LIMIT ?
    """.format(','.join(map(str, enrolled_ids)) if enrolled_ids else '0'), 
        (max_enrollments,)
    ).fetchall()
    
    pipeline.close()
    seq_db.close()
    
    enrolled = []
    for lead in leads:
        if dry_run:
            logger.info(f"[DRY RUN] Would enroll: {lead['company']} ({lead['contact_email']})")
            enrolled.append(lead['id'])
        else:
            enrollment_id = enroll_lead(lead['id'], sequence_name)
            if enrollment_id:
                enrolled.append(lead['id'])
    
    logger.info(f"Enrolled {len(enrolled)} leads from pipeline")
    return enrolled


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Email Sequence Engine")
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # Enroll command
    enroll_parser = subparsers.add_parser('enroll', help='Enroll a lead in sequence')
    enroll_parser.add_argument('--deal-id', type=int, required=True)
    enroll_parser.add_argument('--sequence', default='general_ai')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Send due emails')
    process_parser.add_argument('--dry-run', action='store_true')
    
    # Check replies command
    subparsers.add_parser('check-replies', help='Check for replies')
    
    # Auto-enroll command
    auto_parser = subparsers.add_parser('auto-enroll', help='Enroll from pipeline')
    auto_parser.add_argument('--max', type=int, default=20)
    auto_parser.add_argument('--sequence', default='general_ai')
    auto_parser.add_argument('--dry-run', action='store_true')
    
    # Status command
    subparsers.add_parser('status', help='Show status')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test email sending')
    test_parser.add_argument('--to', required=True, help='Test recipient email')
    
    args = parser.parse_args()
    
    if args.command == 'enroll':
        result = enroll_lead(args.deal_id, args.sequence)
        if result:
            print(f"✅ Enrolled deal {args.deal_id} in {args.sequence} (enrollment #{result})")
        else:
            print(f"❌ Failed to enroll deal {args.deal_id}")
            sys.exit(1)
    
    elif args.command == 'process':
        stats = process_due_emails(dry_run=args.dry_run)
        print(f"📧 Processed: {stats['processed']}, Sent: {stats['sent']}, Errors: {stats['errors']}")
    
    elif args.command == 'check-replies':
        count = check_replies()
        print(f"📬 Processed {count} replies")
    
    elif args.command == 'auto-enroll':
        enrolled = enroll_from_pipeline(
            max_enrollments=args.max,
            sequence_name=args.sequence,
            dry_run=args.dry_run
        )
        print(f"✅ Enrolled {len(enrolled)} leads")
    
    elif args.command == 'status':
        status = get_status()
        print("\n📊 Email Sequence Engine Status")
        print("=" * 40)
        print(f"\nEnrollments by status:")
        for s, count in status['enrollments'].items():
            print(f"  {s}: {count}")
        print(f"\nPending now: {status['pending_now']}")
        print(f"Upcoming 24h: {status['upcoming_24h']}")
        print(f"\nToday's activity:")
        print(f"  Sent: {status['today']['sent']}/{status['today']['limit']}")
        print(f"  Opened: {status['today']['opened']}")
        print(f"  Replies: {status['today']['replies']}")
    
    elif args.command == 'test':
        print(f"Sending test email to {args.to}...")
        gmail = GmailClient()
        msg_id, thread_id = gmail.send_email(
            to=args.to,
            subject="Test from Email Sequence Engine",
            body="This is a test email from the Marceau Solutions Email Sequence Engine.\n\nIf you received this, the system is working correctly.\n\nWilliam"
        )
        if msg_id:
            print(f"✅ Test email sent! Message ID: {msg_id}")
        else:
            print("❌ Failed to send test email")
            sys.exit(1)


if __name__ == "__main__":
    main()
