#!/usr/bin/env python3
"""
twilio_inbox_monitor.py - Poll Twilio for Incoming SMS Messages

PURPOSE: Check for SMS replies without running a webhook server.
SOLVES: User can't see responses to cold outreach sent via Twilio number.

FEATURES:
1. Poll Twilio API for incoming messages
2. Match replies to outreach campaigns
3. Forward HOT LEADS to personal phone via SMS
4. Send email notifications for HOT/WARM leads only (NOT opt-outs)
5. Log all replies to sms_replies.json

USAGE:
    # Check for new messages
    python twilio_inbox_monitor.py check

    # Check and forward to personal phone
    python twilio_inbox_monitor.py check --forward-to "+12395551234"

    # Run as daemon (checks every 5 minutes)
    python twilio_inbox_monitor.py daemon --forward-to "+12395551234"

DEPENDENCIES: twilio, python-dotenv
"""

import os
import sys
import json
import argparse
import smtplib
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv

# Load environment from dev-sandbox root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
except ImportError:
    print("ERROR: twilio package not installed")
    print("Install with: pip install twilio")
    sys.exit(1)


@dataclass
class IncomingSMS:
    """Represents an incoming SMS message."""
    message_sid: str
    from_phone: str
    to_phone: str
    body: str
    date_sent: str
    status: str

    # Enriched data (after matching to outreach)
    business_name: str = ""
    category: str = ""  # hot_lead, warm_lead, opt_out, unknown
    matched_to_outreach: bool = False
    processed: bool = False
    forwarded: bool = False
    notification_sent: bool = False


class TwilioInboxMonitor:
    """
    Monitor Twilio inbox for incoming SMS replies.

    Uses polling instead of webhooks - no server required.
    """

    # Response categorization keywords
    HOT_KEYWORDS = [
        "yes", "interested", "call me", "call back", "website", "how much",
        "price", "cost", "let's talk", "schedule", "available", "sounds good",
        "tell me more", "more info", "what's included", "sign me up"
    ]

    WARM_KEYWORDS = [
        "maybe", "thinking", "consider", "question", "?", "what", "how",
        "when", "where", "who are you", "more details", "busy"
    ]

    OPT_OUT_KEYWORDS = [
        "stop", "unsubscribe", "remove", "opt out", "opt-out", "cancel", "no"
    ]

    def __init__(self):
        """Initialize Twilio client."""
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_number = os.getenv('TWILIO_PHONE_NUMBER')

        if not all([self.account_sid, self.auth_token, self.twilio_number]):
            raise ValueError(
                "Missing Twilio credentials. Set TWILIO_ACCOUNT_SID, "
                "TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER in .env"
            )

        self.client = Client(self.account_sid, self.auth_token)

        # SMTP for notifications
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USERNAME", "")
        self.smtp_pass = os.getenv("SMTP_PASSWORD", "")
        self.notification_email = os.getenv("NOTIFICATION_EMAIL", "")
        self.sender_email = os.getenv("SENDER_EMAIL", self.smtp_user)

        # Data directories
        self.project_root = Path(__file__).parent.parent
        self.lead_scraper_output = self.project_root / "projects" / "lead-scraper" / "output"
        self.replies_file = self.lead_scraper_output / "sms_replies.json"
        self.campaigns_file = self.lead_scraper_output / "sms_campaigns.json"

        # Load existing replies and campaigns
        self.processed_sids: set = set()
        self.phone_to_business: Dict[str, str] = {}
        self._load_existing_data()

    def _load_existing_data(self) -> None:
        """Load processed message SIDs and campaign data."""
        # Load already processed replies
        if self.replies_file.exists():
            try:
                with open(self.replies_file) as f:
                    data = json.load(f)
                    for reply in data.get("replies", []):
                        self.processed_sids.add(reply.get("message_sid", ""))
            except Exception as e:
                print(f"Warning: Could not load replies file: {e}")

        # Load campaign data to match phone numbers to businesses
        if self.campaigns_file.exists():
            try:
                with open(self.campaigns_file) as f:
                    data = json.load(f)
                    for record in data.get("records", []):
                        phone = self._normalize_phone(record.get("phone", ""))
                        business = record.get("business_name", "")
                        if phone and business:
                            self.phone_to_business[phone] = business
            except Exception as e:
                print(f"Warning: Could not load campaigns file: {e}")

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number to E.164 format."""
        digits = ''.join(c for c in phone if c.isdigit())
        if len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) == 11 and digits.startswith('1'):
            return f"+{digits}"
        return phone

    def _categorize_message(self, body: str) -> str:
        """Categorize a message based on content."""
        body_lower = body.lower().strip()

        # Opt-out check first (legal requirement)
        if any(kw in body_lower for kw in self.OPT_OUT_KEYWORDS):
            return "opt_out"

        # Hot lead
        if any(kw in body_lower for kw in self.HOT_KEYWORDS):
            return "hot_lead"

        # Warm lead
        if any(kw in body_lower for kw in self.WARM_KEYWORDS):
            return "warm_lead"

        return "unknown"

    def fetch_incoming_messages(
        self,
        hours_back: int = 48,
        limit: int = 100
    ) -> List[IncomingSMS]:
        """
        Fetch incoming messages from Twilio.

        Args:
            hours_back: How many hours back to look
            limit: Maximum number of messages to fetch

        Returns:
            List of IncomingSMS objects
        """
        messages = []
        date_sent_after = datetime.utcnow() - timedelta(hours=hours_back)

        try:
            # Fetch incoming messages TO our Twilio number
            twilio_messages = self.client.messages.list(
                to=self.twilio_number,
                date_sent_after=date_sent_after,
                limit=limit
            )

            for msg in twilio_messages:
                # Skip if already processed
                if msg.sid in self.processed_sids:
                    continue

                # Create IncomingSMS object
                incoming = IncomingSMS(
                    message_sid=msg.sid,
                    from_phone=msg.from_,
                    to_phone=msg.to,
                    body=msg.body,
                    date_sent=str(msg.date_sent),
                    status=msg.status
                )

                # Match to business
                normalized_from = self._normalize_phone(msg.from_)
                if normalized_from in self.phone_to_business:
                    incoming.business_name = self.phone_to_business[normalized_from]
                    incoming.matched_to_outreach = True

                # Categorize
                incoming.category = self._categorize_message(msg.body)

                messages.append(incoming)

        except TwilioRestException as e:
            print(f"Twilio API error: {e}")

        return messages

    def forward_to_phone(self, message: IncomingSMS, forward_to: str) -> bool:
        """
        Forward a message to personal phone via SMS.

        Args:
            message: The incoming SMS to forward
            forward_to: Phone number to forward to

        Returns:
            True if forwarded successfully
        """
        try:
            category_emoji = {
                "hot_lead": "🔥 HOT LEAD",
                "warm_lead": "☀️ WARM LEAD",
                "opt_out": "🚫 OPT-OUT",
                "unknown": "📱 NEW SMS"
            }

            category_text = category_emoji.get(message.category, "📱 NEW SMS")
            business = message.business_name or "Unknown business"

            forward_text = (
                f"{category_text}\n"
                f"From: {message.from_phone}\n"
                f"Business: {business}\n"
                f"Message: {message.body}\n"
                f"---\n"
                f"Reply directly to: {message.from_phone}"
            )

            # Send via Twilio
            self.client.messages.create(
                body=forward_text,
                from_=self.twilio_number,
                to=forward_to
            )

            print(f"  ✓ Forwarded to {forward_to}")
            return True

        except TwilioRestException as e:
            print(f"  ✗ Forward failed: {e}")
            return False

    def send_email_notification(self, message: IncomingSMS) -> bool:
        """Send email notification for HOT/WARM leads only (skip opt-outs)."""
        if not all([self.smtp_user, self.smtp_pass, self.notification_email]):
            return False

        # SKIP email notifications for opt-outs and unknown - no need to clutter inbox
        if message.category in ["opt_out", "unknown"]:
            return False  # Silently skip - these are logged but don't need email

        category_emoji = {
            "hot_lead": "🔥",
            "warm_lead": "☀️",
            "opt_out": "🚫",
            "unknown": "📱"
        }

        emoji = category_emoji.get(message.category, "📱")
        business = message.business_name or "Unknown"

        # Make hot leads VERY visible in email subject
        priority = "🚨 URGENT" if message.category == "hot_lead" else ""
        subject = f"{priority} {emoji} SMS Reply from {business} ({message.category.upper().replace('_', ' ')})"

        body = f"""
New SMS Reply Received!

CATEGORY: {message.category.upper().replace('_', ' ')}
FROM: {message.from_phone}
BUSINESS: {business}
TIME: {message.date_sent}

MESSAGE:
{message.body}

---
Quick Actions:
- Reply directly: {message.from_phone}
- View all replies: Check output/sms_replies.json

This message was sent to your Twilio number: {message.to_phone}
"""

        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = self.notification_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)

            return True

        except Exception as e:
            print(f"  ✗ Email notification failed: {e}")
            return False

    def save_reply(self, message: IncomingSMS) -> None:
        """Save a reply to the replies file."""
        # Load existing
        data = {"replies": [], "summary": {}, "last_updated": ""}
        if self.replies_file.exists():
            try:
                with open(self.replies_file) as f:
                    data = json.load(f)
            except:
                pass

        # Add new reply
        data["replies"].append(asdict(message))

        # Update summary
        data["summary"] = {
            "total": len(data["replies"]),
            "hot_leads": sum(1 for r in data["replies"] if r.get("category") == "hot_lead"),
            "warm_leads": sum(1 for r in data["replies"] if r.get("category") == "warm_lead"),
            "opt_outs": sum(1 for r in data["replies"] if r.get("category") == "opt_out"),
            "unknown": sum(1 for r in data["replies"] if r.get("category") == "unknown"),
        }
        data["last_updated"] = datetime.now().isoformat()

        # Save
        self.replies_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.replies_file, 'w') as f:
            json.dump(data, f, indent=2)

        # Track as processed
        self.processed_sids.add(message.message_sid)

    def check_inbox(
        self,
        hours_back: int = 48,
        forward_to: Optional[str] = None,
        send_email: bool = True
    ) -> Dict[str, Any]:
        """
        Check inbox for new messages and process them.

        Args:
            hours_back: How many hours back to look
            forward_to: Phone number to forward hot/warm leads to
            send_email: Whether to send email notifications

        Returns:
            Summary of processed messages
        """
        print(f"\n{'='*60}")
        print(f"TWILIO INBOX CHECK")
        print(f"{'='*60}")
        print(f"Twilio Number: {self.twilio_number}")
        print(f"Looking back: {hours_back} hours")
        print(f"Forward to: {forward_to or 'Not configured'}")
        print()

        # Fetch messages
        messages = self.fetch_incoming_messages(hours_back=hours_back)

        if not messages:
            print("No new messages found.")
            return {"total": 0, "hot_leads": 0, "warm_leads": 0, "opt_outs": 0}

        print(f"Found {len(messages)} new message(s):\n")

        results = {
            "total": len(messages),
            "hot_leads": 0,
            "warm_leads": 0,
            "opt_outs": 0,
            "unknown": 0,
            "messages": []
        }

        for msg in messages:
            # Count by category
            if msg.category == "hot_lead":
                results["hot_leads"] += 1
            elif msg.category == "warm_lead":
                results["warm_leads"] += 1
            elif msg.category == "opt_out":
                results["opt_outs"] += 1
            else:
                results["unknown"] += 1

            # Print message
            category_emoji = {
                "hot_lead": "🔥 HOT LEAD",
                "warm_lead": "☀️ WARM LEAD",
                "opt_out": "🚫 OPT-OUT",
                "unknown": "📱 UNKNOWN"
            }

            print(f"[{category_emoji.get(msg.category, '📱')}]")
            print(f"  From: {msg.from_phone}")
            print(f"  Business: {msg.business_name or 'Unknown (not matched to campaign)'}")
            print(f"  Time: {msg.date_sent}")
            print(f"  Message: {msg.body}")

            # Forward hot/warm leads to personal phone
            if forward_to and msg.category in ["hot_lead", "warm_lead"]:
                msg.forwarded = self.forward_to_phone(msg, forward_to)

            # Send email notification
            if send_email:
                msg.notification_sent = self.send_email_notification(msg)
                if msg.notification_sent:
                    print(f"  ✓ Email notification sent")

            # Save to file
            msg.processed = True
            self.save_reply(msg)
            print(f"  ✓ Saved to sms_replies.json")
            print()

            results["messages"].append(asdict(msg))

        # Summary
        print(f"{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"Total new messages: {results['total']}")
        print(f"  🔥 Hot Leads: {results['hot_leads']}")
        print(f"  ☀️  Warm Leads: {results['warm_leads']}")
        print(f"  🚫 Opt-outs: {results['opt_outs']}")
        print(f"  📱 Unknown: {results['unknown']}")

        if results["hot_leads"] > 0:
            print("\n⚡ ACTION REQUIRED: You have hot leads waiting!")

        return results

    def run_daemon(
        self,
        forward_to: str,
        check_interval_minutes: int = 5
    ) -> None:
        """
        Run as a daemon, checking for messages periodically.

        Args:
            forward_to: Phone number to forward hot/warm leads to
            check_interval_minutes: How often to check (default 5 min)
        """
        print(f"\n{'='*60}")
        print("TWILIO INBOX MONITOR - DAEMON MODE")
        print(f"{'='*60}")
        print(f"Checking every {check_interval_minutes} minutes")
        print(f"Forwarding hot/warm leads to: {forward_to}")
        print("Press Ctrl+C to stop")
        print()

        while True:
            try:
                self.check_inbox(
                    hours_back=check_interval_minutes + 5,  # Small overlap
                    forward_to=forward_to,
                    send_email=True
                )
                print(f"\nNext check in {check_interval_minutes} minutes...")
                time.sleep(check_interval_minutes * 60)

            except KeyboardInterrupt:
                print("\nDaemon stopped.")
                break
            except Exception as e:
                print(f"\nError: {e}")
                print(f"Retrying in {check_interval_minutes} minutes...")
                time.sleep(check_interval_minutes * 60)


def main():
    """CLI for Twilio inbox monitor."""
    parser = argparse.ArgumentParser(
        description="Monitor Twilio inbox for SMS replies"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Check command
    check_parser = subparsers.add_parser("check", help="Check for new messages")
    check_parser.add_argument(
        "--hours", type=int, default=48,
        help="Hours to look back (default: 48)"
    )
    check_parser.add_argument(
        "--forward-to",
        help="Phone number to forward hot/warm leads to"
    )
    check_parser.add_argument(
        "--no-email", action="store_true",
        help="Don't send email notifications"
    )

    # Daemon command
    daemon_parser = subparsers.add_parser("daemon", help="Run as daemon")
    daemon_parser.add_argument(
        "--forward-to", required=True,
        help="Phone number to forward hot/warm leads to"
    )
    daemon_parser.add_argument(
        "--interval", type=int, default=5,
        help="Check interval in minutes (default: 5)"
    )

    # Summary command
    summary_parser = subparsers.add_parser("summary", help="Show reply summary")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        monitor = TwilioInboxMonitor()
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    if args.command == "check":
        results = monitor.check_inbox(
            hours_back=args.hours,
            forward_to=args.forward_to,
            send_email=not args.no_email
        )
        return 0 if results else 1

    elif args.command == "daemon":
        monitor.run_daemon(
            forward_to=args.forward_to,
            check_interval_minutes=args.interval
        )
        return 0

    elif args.command == "summary":
        replies_file = monitor.replies_file
        if not replies_file.exists():
            print("No replies file found. Run 'check' first.")
            return 1

        with open(replies_file) as f:
            data = json.load(f)

        summary = data.get("summary", {})
        print(f"\n{'='*60}")
        print("SMS REPLY SUMMARY")
        print(f"{'='*60}")
        print(f"Total Replies: {summary.get('total', 0)}")
        print(f"  🔥 Hot Leads: {summary.get('hot_leads', 0)}")
        print(f"  ☀️  Warm Leads: {summary.get('warm_leads', 0)}")
        print(f"  🚫 Opt-outs: {summary.get('opt_outs', 0)}")
        print(f"  📱 Unknown: {summary.get('unknown', 0)}")
        print(f"\nLast Updated: {data.get('last_updated', 'Never')}")

        # Show recent replies
        replies = data.get("replies", [])
        if replies:
            print(f"\nRecent Replies:")
            for reply in replies[-5:]:
                print(f"  - {reply.get('business_name', 'Unknown')}: {reply.get('body', '')[:50]}...")

        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
