#!/usr/bin/env python3
"""
Lead Nurture Scheduler - Time-Based Drip Sequences

PURPOSE: Automatically follow up with leads at specific intervals
SOLVES: Leads going cold because follow-ups weren't sent at the right time

SEQUENCE EXAMPLE (Website Builder):
- Day 0: Auto-response with Calendly link (immediate)
- Day 1: "Just checking in" email (9 AM)
- Day 3: Social proof email with case study (9 AM)
- Day 7: "Still interested?" with special offer (9 AM)
- Day 14: Final "breaking up" email (9 AM)

USAGE:
    # Check what follow-ups are due today
    python -m src.lead_nurture_scheduler check

    # Send all due follow-ups
    python -m src.lead_nurture_scheduler send

    # Preview what would be sent (dry run)
    python -m src.lead_nurture_scheduler send --dry-run

    # Add a lead to a nurture sequence
    python -m src.lead_nurture_scheduler enroll --email jane@fitgym.com --sequence website_builder

    # List all sequences
    python -m src.lead_nurture_scheduler sequences

RUN DAILY: Set up a cron job or launchd to run at 9 AM daily:
    0 9 * * * cd /path/to/lead-scraper && python -m src.lead_nurture_scheduler send
"""

import os
import json
import smtplib
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# =============================================================================
# Nurture Sequence Definitions
# =============================================================================

NURTURE_SEQUENCES = {
    "website_builder": {
        "name": "Website Builder Lead Nurture",
        "description": "Follow-up sequence for leads who submitted a website inquiry",
        "steps": [
            {
                "day": 0,
                "time": "immediate",  # Handled by form_webhook auto-response
                "channel": "email",
                "template": "welcome",
                "subject": "Thanks for reaching out! 🎉",
                "skip_if_booked": True  # Skip if they already booked a meeting
            },
            {
                "day": 1,
                "time": "09:00",
                "channel": "email",
                "template": "day1_checkin",
                "subject": "Quick question about your website project",
                "skip_if_booked": True
            },
            {
                "day": 3,
                "time": "09:00",
                "channel": "email",
                "template": "day3_social_proof",
                "subject": "How [similar business] got 40% more customers",
                "skip_if_booked": True
            },
            {
                "day": 7,
                "time": "09:00",
                "channel": "email",
                "template": "day7_value",
                "subject": "3 things your competitors are doing online",
                "skip_if_booked": True
            },
            {
                "day": 14,
                "time": "09:00",
                "channel": "email",
                "template": "day14_breakup",
                "subject": "Should I close your file?",
                "skip_if_booked": True
            }
        ]
    },
    "gym_website": {
        "name": "Gym/Fitness Website Nurture",
        "description": "Specialized sequence for gym and fitness businesses",
        "steps": [
            {
                "day": 0,
                "time": "immediate",
                "channel": "email",
                "template": "welcome",
                "subject": "Thanks for reaching out! 🎉",
                "skip_if_booked": True
            },
            {
                "day": 1,
                "time": "09:00",
                "channel": "sms",
                "template": "day1_sms_checkin",
                "skip_if_booked": True
            },
            {
                "day": 2,
                "time": "09:00",
                "channel": "email",
                "template": "day2_gym_case_study",
                "subject": "How FitLife Gym doubled their membership signups",
                "skip_if_booked": True
            },
            {
                "day": 5,
                "time": "09:00",
                "channel": "email",
                "template": "day5_member_acquisition",
                "subject": "The #1 thing stopping potential members from joining",
                "skip_if_booked": True
            },
            {
                "day": 7,
                "time": "09:00",
                "channel": "sms",
                "template": "day7_sms_final",
                "skip_if_booked": True
            }
        ]
    }
}

# =============================================================================
# Email Templates
# =============================================================================

EMAIL_TEMPLATES = {
    "day1_checkin": {
        "plain": """Hi {first_name},

Just wanted to follow up on your website inquiry from yesterday.

I know you're busy running {company}, so I'll keep this short - is there a specific challenge you're facing with getting more customers online?

I'd love to help, even if it's just pointing you in the right direction.

Book a quick 15-min call if it's easier to chat: {calendly_link}

Best,
{owner_name}
{business_name}""",
        "html": """
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; line-height: 1.6;">
    <p>Hi {first_name},</p>

    <p>Just wanted to follow up on your website inquiry from yesterday.</p>

    <p>I know you're busy running <strong>{company}</strong>, so I'll keep this short - is there a specific challenge you're facing with getting more customers online?</p>

    <p>I'd love to help, even if it's just pointing you in the right direction.</p>

    <div style="text-align: center; margin: 25px 0;">
        <a href="{calendly_link}" style="background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">Book a Quick Call</a>
    </div>

    <p>Best,<br>
    <strong>{owner_name}</strong><br>
    {business_name}</p>
</body>
</html>"""
    },

    "day3_social_proof": {
        "plain": """Hi {first_name},

Quick story I thought you'd find interesting...

Last month I helped a {industry} business similar to {company} get their first website up. Within 30 days, they saw:
- 40% increase in customer inquiries
- 3x more phone calls
- First page Google ranking for "{industry} near me"

The owner told me "I wish I had done this years ago."

Would you like to see what I could create for {company}? I can put together a free mockup - no strings attached.

Just reply "yes" or book a call: {calendly_link}

{owner_name}""",
        "html": """
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; line-height: 1.6;">
    <p>Hi {first_name},</p>

    <p>Quick story I thought you'd find interesting...</p>

    <p>Last month I helped a <strong>{industry}</strong> business similar to {company} get their first website up. Within 30 days, they saw:</p>

    <ul style="background: #f5f5f5; padding: 20px 20px 20px 40px; border-radius: 5px;">
        <li>40% increase in customer inquiries</li>
        <li>3x more phone calls</li>
        <li>First page Google ranking for "{industry} near me"</li>
    </ul>

    <p>The owner told me <em>"I wish I had done this years ago."</em></p>

    <p>Would you like to see what I could create for <strong>{company}</strong>? I can put together a free mockup - no strings attached.</p>

    <p>Just reply "yes" or <a href="{calendly_link}" style="color: #667eea;">book a call here</a>.</p>

    <p>{owner_name}</p>
</body>
</html>"""
    },

    "day7_value": {
        "plain": """Hi {first_name},

Been thinking about {company} and wanted to share 3 things I've noticed your competitors are doing online:

1. They show up when people search "{industry} near me"
2. They have customer reviews visible on their website
3. They make it easy to contact them or book online

The good news? These are all fixable, and faster than you might think.

I have a few slots open this week if you'd like to chat about getting {company} online. No pressure, just a friendly conversation about your options.

{calendly_link}

{owner_name}
{business_name}""",
        "html": """
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; line-height: 1.6;">
    <p>Hi {first_name},</p>

    <p>Been thinking about <strong>{company}</strong> and wanted to share 3 things I've noticed your competitors are doing online:</p>

    <ol style="background: #fff3cd; padding: 20px 20px 20px 40px; border-radius: 5px; border-left: 4px solid #ffc107;">
        <li>They show up when people search "{industry} near me"</li>
        <li>They have customer reviews visible on their website</li>
        <li>They make it easy to contact them or book online</li>
    </ol>

    <p>The good news? These are all fixable, and faster than you might think.</p>

    <p>I have a few slots open this week if you'd like to chat about getting {company} online. No pressure, just a friendly conversation about your options.</p>

    <div style="text-align: center; margin: 25px 0;">
        <a href="{calendly_link}" style="background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">Schedule a Chat</a>
    </div>

    <p>{owner_name}<br>{business_name}</p>
</body>
</html>"""
    },

    "day14_breakup": {
        "plain": """Hi {first_name},

I've reached out a few times about helping {company} with a website, but haven't heard back.

No worries at all - I know timing isn't always right.

I'm going to close your file for now, but if you ever want to revisit this in the future, just reply to this email and I'll be happy to help.

Wishing you and {company} all the best!

{owner_name}
{business_name}

P.S. If I completely missed the mark on what you were looking for, I'd genuinely appreciate knowing so I can do better. Just hit reply.""",
        "html": """
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; line-height: 1.6;">
    <p>Hi {first_name},</p>

    <p>I've reached out a few times about helping <strong>{company}</strong> with a website, but haven't heard back.</p>

    <p>No worries at all - I know timing isn't always right.</p>

    <p>I'm going to close your file for now, but if you ever want to revisit this in the future, just reply to this email and I'll be happy to help.</p>

    <p>Wishing you and {company} all the best!</p>

    <p>{owner_name}<br>{business_name}</p>

    <p style="color: #666; font-size: 14px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
        <strong>P.S.</strong> If I completely missed the mark on what you were looking for, I'd genuinely appreciate knowing so I can do better. Just hit reply.
    </p>
</body>
</html>"""
    },

    # Gym-specific templates
    "day2_gym_case_study": {
        "plain": """Hi {first_name},

I wanted to share something that might help {company}...

A gym owner I worked with was struggling to get new members. They relied on word-of-mouth and a Facebook page, but leads were slow.

After launching their website:
- 67 new member inquiries in the first month
- Class bookings went up 45%
- They finally showed up when people searched "gym near me"

The best part? Members could sign up for classes online 24/7, which meant the front desk wasn't constantly answering phones.

Want to see what this could look like for {company}? I'd love to show you.

{calendly_link}

{owner_name}""",
        "html": """
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; line-height: 1.6;">
    <p>Hi {first_name},</p>

    <p>I wanted to share something that might help <strong>{company}</strong>...</p>

    <p>A gym owner I worked with was struggling to get new members. They relied on word-of-mouth and a Facebook page, but leads were slow.</p>

    <p><strong>After launching their website:</strong></p>
    <ul style="background: #d4edda; padding: 20px 20px 20px 40px; border-radius: 5px;">
        <li>67 new member inquiries in the first month</li>
        <li>Class bookings went up 45%</li>
        <li>They finally showed up when people searched "gym near me"</li>
    </ul>

    <p>The best part? Members could sign up for classes online 24/7, which meant the front desk wasn't constantly answering phones.</p>

    <p>Want to see what this could look like for {company}? I'd love to show you.</p>

    <div style="text-align: center; margin: 25px 0;">
        <a href="{calendly_link}" style="background: #28a745; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">See What's Possible</a>
    </div>

    <p>{owner_name}</p>
</body>
</html>"""
    },

    "day5_member_acquisition": {
        "plain": """Hi {first_name},

Quick question for you...

When someone in your area searches "gym near me" or "{industry} in [your city]", does {company} show up?

If not, you're invisible to the 80% of people who search online before choosing a gym.

Here's the thing - your competitors ARE showing up. And every day without a website is potential members walking into their doors instead of yours.

I can help fix that. Let's chat for 15 minutes about getting {company} visible online.

{calendly_link}

{owner_name}""",
        "html": """
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; line-height: 1.6;">
    <p>Hi {first_name},</p>

    <p>Quick question for you...</p>

    <p style="background: #f8f9fa; padding: 15px; border-radius: 5px; font-size: 18px;">
        When someone in your area searches <strong>"gym near me"</strong> or <strong>"{industry} in [your city]"</strong>, does {company} show up?
    </p>

    <p>If not, you're invisible to the <strong>80% of people</strong> who search online before choosing a gym.</p>

    <p>Here's the thing - your competitors ARE showing up. And every day without a website is potential members walking into their doors instead of yours.</p>

    <p>I can help fix that. Let's chat for 15 minutes about getting {company} visible online.</p>

    <div style="text-align: center; margin: 25px 0;">
        <a href="{calendly_link}" style="background: #dc3545; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">Let's Fix This</a>
    </div>

    <p>{owner_name}</p>
</body>
</html>"""
    }
}

SMS_TEMPLATES = {
    "day1_sms_checkin": "Hi {first_name}! William here - just following up on your website inquiry. Any questions I can answer? Or book a quick call: {calendly_link}",
    "day7_sms_final": "Hi {first_name}, last check-in about your {company} website project. Would love to help if timing works. Let me know! - William"
}


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class NurtureEnrollment:
    """A lead enrolled in a nurture sequence."""
    lead_id: str
    email: str
    name: str
    phone: str = ""
    company: str = ""
    industry: str = ""
    sequence_id: str = "website_builder"
    enrolled_at: str = ""
    current_step: int = 0  # 0 = welcome already sent
    steps_completed: List[int] = field(default_factory=list)
    meeting_booked: bool = False
    opted_out: bool = False
    converted: bool = False
    last_touch_at: str = ""
    notes: str = ""

    def __post_init__(self):
        if not self.enrolled_at:
            self.enrolled_at = datetime.now().isoformat()
        if not self.lead_id:
            self.lead_id = f"lead_{datetime.now().strftime('%Y%m%d%H%M%S')}"


# =============================================================================
# Lead Nurture Scheduler
# =============================================================================

class LeadNurtureScheduler:
    """Manages time-based lead nurture sequences."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.enrollments_file = self.output_dir / "nurture_enrollments.json"
        self.enrollments: List[NurtureEnrollment] = []

        # Email settings
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.sender_name = os.getenv("SENDER_NAME", "Marceau Solutions")
        self.sender_email = os.getenv("SENDER_EMAIL", self.smtp_username)

        # Business settings
        self.calendly_link = os.getenv("CALENDLY_URL") or os.getenv("CALENDLY_LINK", "https://calendly.com/marceausolutions/discovery")
        self.business_name = os.getenv("BUSINESS_NAME", "Marceau Solutions")
        self.owner_name = os.getenv("OWNER_NAME", "William")

        # Twilio settings
        self.twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

        self._load_enrollments()

    def _load_enrollments(self):
        """Load existing enrollments."""
        if self.enrollments_file.exists():
            with open(self.enrollments_file) as f:
                data = json.load(f)
                self.enrollments = [
                    NurtureEnrollment(**e) for e in data.get("enrollments", [])
                ]

    def _save_enrollments(self):
        """Save enrollments to file."""
        data = {
            "enrollments": [asdict(e) for e in self.enrollments],
            "last_updated": datetime.now().isoformat()
        }
        with open(self.enrollments_file, "w") as f:
            json.dump(data, f, indent=2)

    def enroll_lead(
        self,
        email: str,
        name: str,
        phone: str = "",
        company: str = "",
        industry: str = "",
        sequence_id: str = "website_builder"
    ) -> NurtureEnrollment:
        """Enroll a lead in a nurture sequence."""
        # Check if already enrolled
        existing = next((e for e in self.enrollments if e.email.lower() == email.lower()), None)
        if existing:
            logger.info(f"Lead {email} already enrolled in sequence {existing.sequence_id}")
            return existing

        enrollment = NurtureEnrollment(
            lead_id=f"lead_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            email=email,
            name=name,
            phone=phone,
            company=company or "your business",
            industry=industry or "business",
            sequence_id=sequence_id,
            current_step=0,  # Start after welcome (Day 0 handled by auto-response)
            steps_completed=[0]  # Mark Day 0 as done
        )

        self.enrollments.append(enrollment)
        self._save_enrollments()

        logger.info(f"✅ Enrolled {name} ({email}) in sequence: {sequence_id}")
        return enrollment

    def get_due_followups(self) -> List[Dict]:
        """Get all follow-ups that are due today."""
        due = []
        now = datetime.now()
        today = now.date()
        current_time = now.strftime("%H:%M")

        for enrollment in self.enrollments:
            # Skip if opted out, converted, or meeting booked
            if enrollment.opted_out or enrollment.converted or enrollment.meeting_booked:
                continue

            sequence = NURTURE_SEQUENCES.get(enrollment.sequence_id)
            if not sequence:
                continue

            enrolled_date = datetime.fromisoformat(enrollment.enrolled_at).date()
            days_since_enrollment = (today - enrolled_date).days

            for i, step in enumerate(sequence["steps"]):
                # Skip if already completed
                if i in enrollment.steps_completed:
                    continue

                # Skip immediate (Day 0) - handled by auto-response
                if step["time"] == "immediate":
                    continue

                # Check if this step is due
                if step["day"] == days_since_enrollment:
                    # Check if it's time (or past time) to send
                    step_time = step["time"]
                    if current_time >= step_time:
                        due.append({
                            "enrollment": enrollment,
                            "step_index": i,
                            "step": step,
                            "sequence": sequence
                        })
                        break  # Only one step per lead per day

                # Don't send steps in the future
                elif step["day"] > days_since_enrollment:
                    break

        return due

    def _format_template(self, template: str, enrollment: NurtureEnrollment) -> str:
        """Replace template variables with lead data."""
        first_name = enrollment.name.split()[0] if enrollment.name else "there"

        return template.format(
            first_name=first_name,
            name=enrollment.name,
            company=enrollment.company or "your business",
            industry=enrollment.industry or "business",
            calendly_link=self.calendly_link,
            owner_name=self.owner_name,
            business_name=self.business_name
        )

    def send_email(self, enrollment: NurtureEnrollment, step: Dict) -> bool:
        """Send a nurture email."""
        template_id = step["template"]
        template = EMAIL_TEMPLATES.get(template_id)

        if not template:
            logger.error(f"Template not found: {template_id}")
            return False

        if not self.smtp_username or not self.smtp_password:
            logger.error("SMTP credentials not configured")
            return False

        try:
            # Format templates
            plain_body = self._format_template(template["plain"], enrollment)
            html_body = self._format_template(template["html"], enrollment)
            subject = self._format_template(step["subject"], enrollment)

            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.sender_name} <{self.sender_email}>"
            msg["To"] = enrollment.email

            msg.attach(MIMEText(plain_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            # Send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.sender_email, enrollment.email, msg.as_string())

            logger.info(f"✅ Sent email to {enrollment.email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {enrollment.email}: {e}")
            return False

    def send_sms(self, enrollment: NurtureEnrollment, step: Dict) -> bool:
        """Send a nurture SMS."""
        template_id = step["template"]
        template = SMS_TEMPLATES.get(template_id)

        if not template:
            logger.error(f"SMS template not found: {template_id}")
            return False

        if not enrollment.phone:
            logger.warning(f"No phone for {enrollment.email} - skipping SMS")
            return False

        if not all([self.twilio_sid, self.twilio_token, self.twilio_number]):
            logger.error("Twilio not configured")
            return False

        try:
            from twilio.rest import Client

            client = Client(self.twilio_sid, self.twilio_token)
            message_body = self._format_template(template, enrollment)

            # Normalize phone
            phone = enrollment.phone
            if not phone.startswith('+'):
                digits = ''.join(c for c in phone if c.isdigit())
                phone = f"+1{digits}" if len(digits) == 10 else f"+{digits}"

            message = client.messages.create(
                body=message_body,
                from_=self.twilio_number,
                to=phone
            )

            logger.info(f"✅ Sent SMS to {phone}: {message.sid}")
            return True

        except Exception as e:
            logger.error(f"Failed to send SMS to {enrollment.phone}: {e}")
            return False

    def process_due_followups(self, dry_run: bool = False) -> Dict[str, int]:
        """Process all due follow-ups."""
        due = self.get_due_followups()

        results = {"sent": 0, "failed": 0, "skipped": 0}

        if not due:
            logger.info("No follow-ups due right now")
            return results

        logger.info(f"Found {len(due)} follow-ups due")

        for item in due:
            enrollment = item["enrollment"]
            step = item["step"]
            step_index = item["step_index"]

            channel = step["channel"]
            template = step["template"]

            logger.info(f"\n--- {enrollment.name} ({enrollment.email}) ---")
            logger.info(f"    Sequence: {item['sequence']['name']}")
            logger.info(f"    Step: Day {step['day']} - {template} ({channel})")

            if dry_run:
                logger.info(f"    [DRY RUN] Would send {channel}")
                results["skipped"] += 1
                continue

            # Send based on channel
            success = False
            if channel == "email":
                success = self.send_email(enrollment, step)
            elif channel == "sms":
                success = self.send_sms(enrollment, step)

            if success:
                # Mark step complete
                enrollment.steps_completed.append(step_index)
                enrollment.current_step = step_index
                enrollment.last_touch_at = datetime.now().isoformat()
                self._save_enrollments()
                results["sent"] += 1
            else:
                results["failed"] += 1

        return results

    def mark_meeting_booked(self, email: str):
        """Mark a lead as having booked a meeting (stops sequence)."""
        enrollment = next((e for e in self.enrollments if e.email.lower() == email.lower()), None)
        if enrollment:
            enrollment.meeting_booked = True
            self._save_enrollments()
            logger.info(f"✅ Marked {email} as meeting booked - stopping sequence")

    def mark_opted_out(self, email: str):
        """Mark a lead as opted out."""
        enrollment = next((e for e in self.enrollments if e.email.lower() == email.lower()), None)
        if enrollment:
            enrollment.opted_out = True
            self._save_enrollments()
            logger.info(f"✅ Marked {email} as opted out")

    def get_status_report(self) -> Dict:
        """Get status of all enrollments."""
        active = [e for e in self.enrollments if not e.opted_out and not e.converted and not e.meeting_booked]
        booked = [e for e in self.enrollments if e.meeting_booked]
        opted_out = [e for e in self.enrollments if e.opted_out]
        converted = [e for e in self.enrollments if e.converted]

        return {
            "total": len(self.enrollments),
            "active": len(active),
            "meeting_booked": len(booked),
            "opted_out": len(opted_out),
            "converted": len(converted),
            "active_leads": [
                {
                    "name": e.name,
                    "email": e.email,
                    "sequence": e.sequence_id,
                    "current_step": e.current_step,
                    "enrolled": e.enrolled_at
                }
                for e in active
            ]
        }


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Lead Nurture Scheduler")
    subparsers = parser.add_subparsers(dest="command")

    # Check command
    check_parser = subparsers.add_parser("check", help="Check what follow-ups are due")
    check_parser.add_argument("--output-dir", default="output")

    # Send command
    send_parser = subparsers.add_parser("send", help="Send all due follow-ups")
    send_parser.add_argument("--dry-run", action="store_true", help="Preview without sending")
    send_parser.add_argument("--output-dir", default="output")

    # Enroll command
    enroll_parser = subparsers.add_parser("enroll", help="Enroll a lead in a sequence")
    enroll_parser.add_argument("--email", required=True)
    enroll_parser.add_argument("--name", required=True)
    enroll_parser.add_argument("--phone", default="")
    enroll_parser.add_argument("--company", default="")
    enroll_parser.add_argument("--industry", default="")
    enroll_parser.add_argument("--sequence", default="website_builder")
    enroll_parser.add_argument("--output-dir", default="output")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show enrollment status")
    status_parser.add_argument("--output-dir", default="output")

    # Sequences command
    sequences_parser = subparsers.add_parser("sequences", help="List available sequences")

    # Mark booked command
    booked_parser = subparsers.add_parser("mark-booked", help="Mark lead as meeting booked")
    booked_parser.add_argument("--email", required=True)
    booked_parser.add_argument("--output-dir", default="output")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "sequences":
        print("\n=== Available Nurture Sequences ===\n")
        for seq_id, seq in NURTURE_SEQUENCES.items():
            print(f"📧 {seq_id}: {seq['name']}")
            print(f"   {seq['description']}")
            print(f"   Steps:")
            for i, step in enumerate(seq["steps"]):
                time_str = step["time"] if step["time"] != "immediate" else "immediately"
                print(f"     Day {step['day']} ({time_str}): {step['template']} [{step['channel']}]")
            print()
        return

    output_dir = getattr(args, "output_dir", "output")
    scheduler = LeadNurtureScheduler(output_dir=output_dir)

    if args.command == "check":
        due = scheduler.get_due_followups()
        print(f"\n=== Follow-ups Due Now ===\n")
        if not due:
            print("No follow-ups due right now.")
        else:
            for item in due:
                e = item["enrollment"]
                step = item["step"]
                print(f"📧 {e.name} ({e.email})")
                print(f"   Day {step['day']}: {step['template']} [{step['channel']}]")
                print()

    elif args.command == "send":
        results = scheduler.process_due_followups(dry_run=args.dry_run)
        print(f"\n=== Results ===")
        print(f"Sent: {results['sent']}")
        print(f"Failed: {results['failed']}")
        print(f"Skipped: {results['skipped']}")

    elif args.command == "enroll":
        scheduler.enroll_lead(
            email=args.email,
            name=args.name,
            phone=args.phone,
            company=args.company,
            industry=args.industry,
            sequence_id=args.sequence
        )

    elif args.command == "status":
        report = scheduler.get_status_report()
        print(f"\n=== Nurture Status ===")
        print(f"Total enrolled: {report['total']}")
        print(f"Active: {report['active']}")
        print(f"Meeting booked: {report['meeting_booked']}")
        print(f"Opted out: {report['opted_out']}")
        print(f"Converted: {report['converted']}")

        if report['active_leads']:
            print(f"\n--- Active Leads ---")
            for lead in report['active_leads']:
                print(f"  {lead['name']} ({lead['email']})")
                print(f"    Sequence: {lead['sequence']}, Step: {lead['current_step']}")

    elif args.command == "mark-booked":
        scheduler.mark_meeting_booked(args.email)


if __name__ == "__main__":
    main()
