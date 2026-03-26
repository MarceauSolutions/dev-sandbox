#!/usr/bin/env python3
"""
Email Follow-Up Scheduler - Automated email sequence management.

Similar to social media post scheduler, this manages scheduled email follow-ups
stored in scheduled_emails.json and sends them at the appropriate times.

Based on Alex Hormozi's $100M Leads follow-up framework:
- Day 0: Initial outreach (already sent)
- Day 2: Still looking? (9-word reactivation)
- Day 5: Direct question (makes them think)
- Day 10: Soft ask (worth 15 minutes?)
- Day 15: Breakup (closing the loop)

Usage:
    python -m src.email_scheduler status
    python -m src.email_scheduler process --dry-run
    python -m src.email_scheduler process --for-real
    python -m src.email_scheduler add --recipient "email@example.com" --campaign "campaign_name"
"""

import os
import json
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Any
import uuid

from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path)

logger = logging.getLogger(__name__)


class EmailScheduler:
    """
    Manages scheduled email follow-up sequences.

    Storage format mirrors social media scheduler:
    - scheduled_emails.json stores all scheduled emails
    - Each email has: id, recipient, subject, body, scheduled_date, status
    - Statuses: scheduled, sent, failed, cancelled
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.emails_file = self.output_dir / "scheduled_emails.json"
        self.emails: List[Dict[str, Any]] = []
        self._load_emails()

        # SMTP config from env
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")

    def _load_emails(self) -> None:
        """Load scheduled emails from JSON."""
        if self.emails_file.exists():
            with open(self.emails_file, 'r') as f:
                data = json.load(f)
                self.emails = data.get("scheduled_emails", [])

    def _save_emails(self) -> None:
        """Save scheduled emails to JSON."""
        data = {
            "scheduled_emails": self.emails,
            "metadata": {
                "created_at": self.emails[0].get("created_at") if self.emails else datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "version": "1.0.0"
            }
        }
        with open(self.emails_file, 'w') as f:
            json.dump(data, f, indent=2)

    def get_due_emails(self, as_of: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        Get emails that are due to be sent.

        Args:
            as_of: Check against this date (default: today)

        Returns:
            List of email dicts that are scheduled for today or earlier
        """
        if as_of is None:
            as_of = date.today()

        due = []
        for email in self.emails:
            if email.get("status") != "scheduled":
                continue

            scheduled_date = datetime.strptime(email["scheduled_date"], "%Y-%m-%d").date()
            if scheduled_date <= as_of:
                due.append(email)

        return due

    def send_email(self, email: Dict[str, Any], dry_run: bool = True) -> Dict[str, Any]:
        """
        Send a single email.

        Args:
            email: Email dict with recipient, subject, body
            dry_run: If True, don't actually send

        Returns:
            Result dict with status
        """
        recipient = email.get("recipient_email")
        subject = email.get("subject")
        body = email.get("body")

        if dry_run:
            logger.info(f"[DRY RUN] Would send to {recipient}: {subject}")
            return {
                "status": "dry_run",
                "recipient": recipient,
                "subject": subject
            }

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_username
            msg['To'] = recipient

            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.smtp_username, recipient, msg.as_string())

            # Update email record
            email["status"] = "sent"
            email["sent_at"] = datetime.now().isoformat()
            self._save_emails()

            logger.info(f"Sent email to {recipient}: {subject}")
            return {
                "status": "sent",
                "recipient": recipient,
                "subject": subject
            }

        except Exception as e:
            logger.error(f"Failed to send to {recipient}: {e}")
            email["status"] = "failed"
            email["error"] = str(e)
            self._save_emails()
            return {
                "status": "failed",
                "recipient": recipient,
                "error": str(e)
            }

    def process_due_emails(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Process all emails that are due.

        Args:
            dry_run: If True, don't actually send

        Returns:
            Processing statistics
        """
        stats = {
            "total_due": 0,
            "processed": 0,
            "sent": 0,
            "failed": 0,
            "dry_run": dry_run
        }

        due_emails = self.get_due_emails()
        stats["total_due"] = len(due_emails)

        for email in due_emails:
            result = self.send_email(email, dry_run=dry_run)
            stats["processed"] += 1

            if result["status"] in ["sent", "dry_run"]:
                stats["sent"] += 1
            else:
                stats["failed"] += 1

        return stats

    def add_email(
        self,
        recipient_email: str,
        recipient_name: str,
        recipient_company: str,
        subject: str,
        body: str,
        scheduled_date: str,
        scheduled_time: str = "08:30",
        campaign: str = "",
        business_id: str = "marceau-solutions",
        touch_number: int = 1,
        template_type: str = "custom",
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        Add a new scheduled email.

        Args:
            recipient_email: Email address
            recipient_name: Recipient's name
            recipient_company: Company name
            subject: Email subject
            body: Email body
            scheduled_date: YYYY-MM-DD format
            scheduled_time: HH:MM format (default 08:30)
            campaign: Campaign identifier
            business_id: Which business is sending
            touch_number: Position in sequence
            template_type: Template category
            notes: Additional notes

        Returns:
            Created email dict
        """
        email_id = uuid.uuid4().hex[:12]

        email = {
            "id": email_id,
            "campaign": campaign,
            "business_id": business_id,
            "recipient_email": recipient_email,
            "recipient_name": recipient_name,
            "recipient_company": recipient_company,
            "subject": subject,
            "body": body,
            "status": "scheduled",
            "touch_number": touch_number,
            "scheduled_date": scheduled_date,
            "scheduled_time": scheduled_time,
            "timezone": "America/New_York",
            "created_at": datetime.now().isoformat(),
            "sent_at": None,
            "template_type": template_type,
            "notes": notes
        }

        self.emails.append(email)
        self._save_emails()

        logger.info(f"Added email for {recipient_email} scheduled {scheduled_date}")
        return email

    def get_status(self) -> Dict[str, Any]:
        """Get overall email scheduler status."""
        stats = {
            "total": len(self.emails),
            "by_status": {},
            "by_campaign": {},
            "by_business": {},
            "due_today": 0
        }

        today = date.today()

        for email in self.emails:
            # By status
            status = email.get("status", "unknown")
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

            # By campaign
            campaign = email.get("campaign", "unknown")
            stats["by_campaign"][campaign] = stats["by_campaign"].get(campaign, 0) + 1

            # By business
            business = email.get("business_id", "unknown")
            stats["by_business"][business] = stats["by_business"].get(business, 0) + 1

            # Due today
            if email.get("status") == "scheduled":
                scheduled_date = datetime.strptime(email["scheduled_date"], "%Y-%m-%d").date()
                if scheduled_date <= today:
                    stats["due_today"] += 1

        return stats

    def cancel_email(self, email_id: str) -> bool:
        """Cancel a scheduled email."""
        for email in self.emails:
            if email.get("id") == email_id:
                email["status"] = "cancelled"
                self._save_emails()
                return True
        return False

    def mark_responded(self, recipient_email: str, campaign: str = "") -> int:
        """
        Mark all pending emails for a recipient as cancelled (they responded).

        Args:
            recipient_email: Email address that responded
            campaign: Optional campaign to filter

        Returns:
            Number of emails cancelled
        """
        cancelled = 0
        for email in self.emails:
            if email.get("recipient_email") == recipient_email:
                if campaign and email.get("campaign") != campaign:
                    continue
                if email.get("status") == "scheduled":
                    email["status"] = "cancelled"
                    email["notes"] = f"Cancelled - recipient responded. {email.get('notes', '')}"
                    cancelled += 1

        if cancelled:
            self._save_emails()

        return cancelled


def main():
    """CLI entry point."""
    import argparse

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description="Email Follow-Up Scheduler")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show scheduler status")
    status_parser.add_argument("--output-dir", "-o", default="output", help="Output directory")

    # Process command
    process_parser = subparsers.add_parser("process", help="Process due emails")
    process_parser.add_argument("--dry-run", action="store_true", default=True, help="Preview without sending")
    process_parser.add_argument("--for-real", action="store_true", help="Actually send emails")
    process_parser.add_argument("--output-dir", "-o", default="output", help="Output directory")

    # Queue command
    queue_parser = subparsers.add_parser("queue", help="Show upcoming emails")
    queue_parser.add_argument("--days", "-d", type=int, default=7, help="Days to look ahead")
    queue_parser.add_argument("--output-dir", "-o", default="output", help="Output directory")

    # Response command
    response_parser = subparsers.add_parser("response", help="Mark recipient as responded")
    response_parser.add_argument("email", help="Email address that responded")
    response_parser.add_argument("--campaign", "-c", default="", help="Campaign filter")
    response_parser.add_argument("--output-dir", "-o", default="output", help="Output directory")

    args = parser.parse_args()

    if args.command == "status":
        scheduler = EmailScheduler(output_dir=args.output_dir)
        stats = scheduler.get_status()

        print("\n=== Email Scheduler Status ===")
        print(f"Total Emails: {stats['total']}")
        print(f"Due Today: {stats['due_today']}")
        print("\nBy Status:")
        for status, count in stats["by_status"].items():
            print(f"  {status}: {count}")
        print("\nBy Campaign:")
        for campaign, count in stats["by_campaign"].items():
            print(f"  {campaign}: {count}")
        print("\nBy Business:")
        for business, count in stats["by_business"].items():
            print(f"  {business}: {count}")

    elif args.command == "process":
        scheduler = EmailScheduler(output_dir=args.output_dir)
        dry_run = not args.for_real

        stats = scheduler.process_due_emails(dry_run=dry_run)

        print("\n=== Processing Results ===")
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print(f"Total Due: {stats['total_due']}")
        print(f"Processed: {stats['processed']}")
        print(f"Sent: {stats['sent']}")
        if stats['failed']:
            print(f"Failed: {stats['failed']}")

    elif args.command == "queue":
        from datetime import timedelta

        scheduler = EmailScheduler(output_dir=args.output_dir)
        cutoff = date.today() + timedelta(days=args.days)

        print(f"\n=== Emails Scheduled (Next {args.days} Days) ===\n")

        by_date = {}
        for email in scheduler.emails:
            if email.get("status") != "scheduled":
                continue
            sched_date = email["scheduled_date"]
            if datetime.strptime(sched_date, "%Y-%m-%d").date() <= cutoff:
                if sched_date not in by_date:
                    by_date[sched_date] = []
                by_date[sched_date].append(email)

        for sched_date in sorted(by_date.keys()):
            print(f"{sched_date}:")
            for email in by_date[sched_date]:
                print(f"  - {email['recipient_name']} ({email['recipient_company']}): {email['subject']}")

        if not by_date:
            print("No emails scheduled.")

    elif args.command == "response":
        scheduler = EmailScheduler(output_dir=args.output_dir)
        cancelled = scheduler.mark_responded(args.email, args.campaign)
        print(f"Cancelled {cancelled} scheduled emails for {args.email}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
