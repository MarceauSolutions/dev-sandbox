#!/usr/bin/env python3
"""
Twilio Webhook Handler for SMS Replies

This module handles incoming SMS replies from Twilio and:
1. Logs responses to Google Sheets
2. Sends email notifications for hot leads
3. Updates campaign tracking
4. Triggers follow-up sequences

Webhook URL: https://your-domain.com/sms/reply
Configure in Twilio Console: Phone Numbers > Your Number > Messaging > Webhook

Usage:
    # Start webhook server locally (for testing with ngrok)
    python -m src.twilio_webhook serve --port 5001

    # Process a test reply
    python -m src.twilio_webhook test --from "+12395551234" --body "Yes interested"
"""

import os
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum

from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import opt-out manager for centralized handling
try:
    from .opt_out_manager import OptOutManager, OptOutReason, detect_opt_out
    OPT_OUT_MANAGER_AVAILABLE = True
except ImportError:
    OPT_OUT_MANAGER_AVAILABLE = False
    logger.warning("OptOutManager not available, using basic opt-out handling")


# =============================================================================
# Configuration
# =============================================================================

class ResponseCategory(Enum):
    """Categories for SMS responses."""
    HOT_LEAD = "hot_lead"           # Interested, wants call
    WARM_LEAD = "warm_lead"         # Asks questions, needs info
    COLD_LEAD = "cold_lead"         # Not now, maybe later
    OPT_OUT = "opt_out"             # STOP, unsubscribe
    UNKNOWN = "unknown"             # Can't categorize


@dataclass
class SMSReply:
    """Represents an incoming SMS reply."""
    from_phone: str
    to_phone: str
    body: str
    received_at: str
    message_sid: str = ""

    # Enrichment (filled after matching to lead)
    lead_id: str = ""
    business_name: str = ""
    category: str = ""

    # Processing
    processed: bool = False
    notification_sent: bool = False
    added_to_sheets: bool = False

    def __post_init__(self):
        if not self.received_at:
            self.received_at = datetime.now().isoformat()


# =============================================================================
# Response Categorization
# =============================================================================

def categorize_response(body: str) -> ResponseCategory:
    """
    Categorize SMS response using keyword matching.

    Hot lead indicators: yes, interested, call me, website, how much, price
    Warm lead indicators: questions, more info, tell me more
    Cold lead indicators: not now, later, busy, no thanks
    Opt-out: stop, unsubscribe, remove, opt out
    """
    body_lower = body.lower().strip()

    # Opt-out (highest priority - legal requirement)
    opt_out_keywords = ["stop", "unsubscribe", "remove", "opt out", "opt-out", "cancel"]
    if any(keyword in body_lower for keyword in opt_out_keywords):
        return ResponseCategory.OPT_OUT

    # Hot lead signals
    hot_keywords = [
        "yes", "interested", "call me", "call back", "website", "how much",
        "price", "cost", "let's talk", "schedule", "available", "sounds good",
        "tell me more", "more info", "what's included"
    ]
    if any(keyword in body_lower for keyword in hot_keywords):
        return ResponseCategory.HOT_LEAD

    # Warm lead signals
    warm_keywords = [
        "maybe", "thinking", "consider", "question", "?", "what", "how",
        "when", "where", "who are you", "more details"
    ]
    if any(keyword in body_lower for keyword in warm_keywords):
        return ResponseCategory.WARM_LEAD

    # Cold lead signals
    cold_keywords = [
        "not now", "later", "busy", "no thanks", "not interested",
        "no", "nope", "pass", "already have"
    ]
    if any(keyword in body_lower for keyword in cold_keywords):
        return ResponseCategory.COLD_LEAD

    return ResponseCategory.UNKNOWN


# =============================================================================
# Notification System
# =============================================================================

class NotificationManager:
    """Send notifications for important responses."""

    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USERNAME", "")
        self.smtp_pass = os.getenv("SMTP_PASSWORD", "")
        self.sender_email = os.getenv("SENDER_EMAIL", "")
        self.notification_email = os.getenv("NOTIFICATION_EMAIL", "")

    def send_email_notification(self, reply: SMSReply) -> bool:
        """Send email notification for a hot or warm lead."""
        if not all([self.smtp_user, self.smtp_pass, self.notification_email]):
            logger.warning("Email not configured - skipping notification")
            return False

        subject = f"[{reply.category.upper()}] SMS Reply from {reply.business_name or reply.from_phone}"

        body = f"""
New SMS Reply Received!

Category: {reply.category.upper()}
From: {reply.from_phone}
Business: {reply.business_name or 'Unknown'}
Time: {reply.received_at}

Message:
{reply.body}

---
Quick Actions:
- Call back: {reply.from_phone}
- Add to ClickUp: Run `python -m src.form_webhook process --data '{{"name": "{reply.business_name}", "phone": "{reply.from_phone}", "source": "sms_reply"}}'`

---
Campaign Dashboard: Check output/campaign_state.json
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

            logger.info(f"Email notification sent to {self.notification_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False


# =============================================================================
# Google Sheets Integration
# =============================================================================

class SheetsTracker:
    """Track responses in Google Sheets."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.replies_file = self.output_dir / "sms_replies.json"
        self.replies: List[SMSReply] = []
        self._load_replies()

    def _load_replies(self) -> None:
        """Load existing replies from file."""
        if self.replies_file.exists():
            with open(self.replies_file) as f:
                data = json.load(f)
                self.replies = [SMSReply(**r) for r in data.get("replies", [])]

    def _save_replies(self) -> None:
        """Save replies to file."""
        data = {
            "replies": [asdict(r) for r in self.replies],
            "last_updated": datetime.now().isoformat(),
            "summary": {
                "total": len(self.replies),
                "hot_leads": sum(1 for r in self.replies if r.category == "hot_lead"),
                "warm_leads": sum(1 for r in self.replies if r.category == "warm_lead"),
                "opt_outs": sum(1 for r in self.replies if r.category == "opt_out")
            }
        }
        with open(self.replies_file, "w") as f:
            json.dump(data, f, indent=2)

    def add_reply(self, reply: SMSReply) -> None:
        """Add a new reply to tracking."""
        self.replies.append(reply)
        self._save_replies()

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all replies."""
        return {
            "total": len(self.replies),
            "by_category": {
                "hot_lead": sum(1 for r in self.replies if r.category == "hot_lead"),
                "warm_lead": sum(1 for r in self.replies if r.category == "warm_lead"),
                "cold_lead": sum(1 for r in self.replies if r.category == "cold_lead"),
                "opt_out": sum(1 for r in self.replies if r.category == "opt_out"),
                "unknown": sum(1 for r in self.replies if r.category == "unknown")
            },
            "recent": [asdict(r) for r in self.replies[-5:]]
        }

    def export_to_csv(self, filename: str = "sms_replies.csv") -> str:
        """Export replies to CSV for Google Sheets import."""
        import csv
        filepath = self.output_dir / filename

        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Received At", "From Phone", "Business Name", "Category",
                "Message", "Processed", "Notification Sent"
            ])
            for reply in self.replies:
                writer.writerow([
                    reply.received_at, reply.from_phone, reply.business_name,
                    reply.category, reply.body, reply.processed, reply.notification_sent
                ])

        return str(filepath)


# =============================================================================
# Webhook Handler
# =============================================================================

class TwilioWebhookHandler:
    """Handle incoming Twilio webhooks."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.notification_manager = NotificationManager()
        self.sheets_tracker = SheetsTracker(output_dir)

        # Initialize centralized opt-out manager
        if OPT_OUT_MANAGER_AVAILABLE:
            self.opt_out_manager = OptOutManager(output_dir=output_dir)
        else:
            self.opt_out_manager = None

        # Load leads for matching
        self.leads_by_phone: Dict[str, Dict] = {}
        self._load_leads()

    def _load_leads(self) -> None:
        """Load leads to match replies to businesses."""
        leads_file = self.output_dir / "leads.json"
        if leads_file.exists():
            with open(leads_file) as f:
                data = json.load(f)
                for lead in data.get("leads", []):
                    phone = self._normalize_phone(lead.get("phone", ""))
                    if phone:
                        self.leads_by_phone[phone] = lead

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number for matching."""
        # Remove all non-digits
        digits = "".join(c for c in phone if c.isdigit())
        # Add country code if missing
        if len(digits) == 10:
            digits = "1" + digits
        return digits

    def _match_lead(self, from_phone: str) -> Optional[Dict]:
        """Match incoming phone to a lead."""
        normalized = self._normalize_phone(from_phone)
        return self.leads_by_phone.get(normalized)

    def process_reply(self, from_phone: str, to_phone: str, body: str, message_sid: str = "") -> Dict[str, Any]:
        """
        Process an incoming SMS reply.

        Steps:
        1. Categorize the response
        2. Match to lead (if possible)
        3. Handle opt-outs
        4. Send notifications for hot/warm leads
        5. Log to tracking
        """
        # Create reply object
        reply = SMSReply(
            from_phone=from_phone,
            to_phone=to_phone,
            body=body,
            message_sid=message_sid,
            received_at=datetime.now().isoformat()
        )

        # Categorize
        category = categorize_response(body)
        reply.category = category.value

        # Match to lead
        lead = self._match_lead(from_phone)
        if lead:
            reply.lead_id = lead.get("id", "")
            reply.business_name = lead.get("business_name", "")

        logger.info(f"Processing reply from {from_phone}: {category.value}")

        result = {
            "success": True,
            "category": category.value,
            "business_name": reply.business_name,
            "actions_taken": []
        }

        # Handle opt-out
        if category == ResponseCategory.OPT_OUT:
            self._handle_optout(from_phone, reply.business_name, message_body=body, message_sid=message_sid)
            result["actions_taken"].append("added_to_optout_list")

        # Send notification for hot/warm leads
        if category in [ResponseCategory.HOT_LEAD, ResponseCategory.WARM_LEAD]:
            if self.notification_manager.send_email_notification(reply):
                reply.notification_sent = True
                result["actions_taken"].append("email_notification_sent")

        # Log to tracking
        reply.processed = True
        self.sheets_tracker.add_reply(reply)
        result["actions_taken"].append("logged_to_tracking")

        return result

    def _handle_optout(self, phone: str, business_name: str, message_body: str = "", message_sid: str = "") -> None:
        """Add phone to opt-out list using centralized OptOutManager."""
        if self.opt_out_manager:
            # Use centralized opt-out manager for better tracking
            self.opt_out_manager.process_sms_reply(
                from_phone=phone,
                message_body=message_body,
                business_name=business_name,
                message_sid=message_sid
            )
        else:
            # Fallback to basic file-based opt-out (legacy)
            optout_file = self.output_dir / "optout_list.json"

            optouts = []
            if optout_file.exists():
                with open(optout_file) as f:
                    optouts = json.load(f)

            # Add normalized phone
            normalized = self._normalize_phone(phone)
            if normalized not in optouts:
                optouts.append(normalized)

            # Also add business name if available
            if business_name and business_name.lower() not in [o.lower() for o in optouts if isinstance(o, str)]:
                optouts.append(business_name.lower())

            with open(optout_file, "w") as f:
                json.dump(optouts, f, indent=2)

        logger.info(f"Added to opt-out list: {phone} ({business_name})")


# =============================================================================
# Flask Webhook Server
# =============================================================================

def create_webhook_app(handler: TwilioWebhookHandler):
    """Create Flask app for Twilio webhooks."""
    try:
        from flask import Flask, request, Response
    except ImportError:
        logger.error("Flask not installed. Run: pip install flask")
        return None

    app = Flask(__name__)

    @app.route("/sms/reply", methods=["POST"])
    def handle_sms_reply():
        """
        Twilio webhook endpoint for incoming SMS.

        Twilio sends:
        - From: Sender phone number
        - To: Your Twilio number
        - Body: Message content
        - MessageSid: Unique message ID
        """
        from_phone = request.form.get("From", "")
        to_phone = request.form.get("To", "")
        body = request.form.get("Body", "")
        message_sid = request.form.get("MessageSid", "")

        logger.info(f"Received SMS from {from_phone}: {body[:50]}...")

        # Check if this is William replying
        if from_phone.endswith("2393985676"):
            stripped = body.strip().lower()

            # HOT lead reply (1/2/3)
            if stripped in ("1", "2", "3"):
                try:
                    from .hot_lead_handler import handle_william_reply
                    result = handle_william_reply(stripped)
                    logger.info(f"William HOT lead reply handled: {result}")
                except Exception as e:
                    logger.error(f"Hot lead handler failed: {e}")
                    result = {"success": False, "error": str(e)}

            # Schedule approval ("yes schedule")
            elif stripped == "yes schedule":
                try:
                    import sys
                    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "projects" / "personal-assistant" / "src"))
                    from daily_scheduler import create_approved_blocks
                    result = create_approved_blocks()
                    logger.info(f"Schedule approval handled: {result}")
                except Exception as e:
                    logger.error(f"Schedule approval failed: {e}")
                    result = {"success": False, "error": str(e)}

            # Goal update ("goal short: Land 2 clients by April 15")
            elif stripped.startswith("goal "):
                try:
                    import sys
                    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "projects" / "personal-assistant" / "src"))
                    from goal_manager import quick_set
                    result_msg = quick_set(body.strip())
                    logger.info(f"Goal update: {result_msg}")
                    result = {"success": True, "message": result_msg}
                except Exception as e:
                    logger.error(f"Goal update failed: {e}")
                    result = {"success": False, "error": str(e)}

            # Tower/project approval ("yes real-estate")
            elif stripped.startswith("yes "):
                try:
                    import sys
                    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "execution"))
                    from autonomous_tower_manager import handle_approval
                    name = stripped[4:].strip()
                    result = handle_approval(name)
                    logger.info(f"Tower approval handled: {result}")
                except Exception as e:
                    logger.error(f"Tower approval failed: {e}")
                    result = {"success": False, "error": str(e)}
            else:
                result = handler.process_reply(from_phone, to_phone, body, message_sid)
        else:
            result = handler.process_reply(from_phone, to_phone, body, message_sid)

        # Return TwiML response (empty = no auto-reply)
        twiml = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
        return Response(twiml, mimetype="text/xml")

    @app.route("/sms/status", methods=["POST"])
    def handle_status_callback():
        """Handle delivery status callbacks from Twilio."""
        message_sid = request.form.get("MessageSid", "")
        status = request.form.get("MessageStatus", "")

        logger.info(f"Status update for {message_sid}: {status}")

        # Could update campaign tracking here
        return Response("OK", status=200)

    @app.route("/health", methods=["GET"])
    def health_check():
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}

    @app.route("/summary", methods=["GET"])
    def get_summary():
        return handler.sheets_tracker.get_summary()

    return app


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Twilio Webhook Handler")
    subparsers = parser.add_subparsers(dest="command")

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start webhook server")
    serve_parser.add_argument("--port", type=int, default=5001, help="Port to listen on")
    serve_parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind")
    serve_parser.add_argument("--output-dir", type=str, default="output", help="Output directory")

    # Test command
    test_parser = subparsers.add_parser("test", help="Test processing a reply")
    test_parser.add_argument("--from", dest="from_phone", required=True, help="From phone number")
    test_parser.add_argument("--body", required=True, help="Message body")
    test_parser.add_argument("--output-dir", type=str, default="output", help="Output directory")

    # Summary command
    summary_parser = subparsers.add_parser("summary", help="Show reply summary")
    summary_parser.add_argument("--output-dir", type=str, default="output", help="Output directory")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export replies to CSV")
    export_parser.add_argument("--output-dir", type=str, default="output", help="Output directory")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    output_dir = getattr(args, "output_dir", "output")
    handler = TwilioWebhookHandler(output_dir=output_dir)

    if args.command == "serve":
        app = create_webhook_app(handler)
        if app:
            print(f"\nStarting Twilio webhook server on {args.host}:{args.port}")
            print(f"\nEndpoints:")
            print(f"  POST /sms/reply  - Twilio incoming SMS webhook")
            print(f"  POST /sms/status - Twilio delivery status callback")
            print(f"  GET  /summary    - Reply statistics")
            print(f"  GET  /health     - Health check")
            print(f"\nTo expose publicly, use ngrok:")
            print(f"  ngrok http {args.port}")
            print(f"\nThen configure Twilio webhook URL:")
            print(f"  https://your-ngrok-url.ngrok.io/sms/reply\n")
            app.run(host=args.host, port=args.port, debug=True)
        else:
            return 1

    elif args.command == "test":
        result = handler.process_reply(
            from_phone=args.from_phone,
            to_phone=os.getenv("TWILIO_PHONE_NUMBER", ""),
            body=args.body
        )
        print(json.dumps(result, indent=2))

    elif args.command == "summary":
        summary = handler.sheets_tracker.get_summary()
        print(json.dumps(summary, indent=2))

    elif args.command == "export":
        filepath = handler.sheets_tracker.export_to_csv()
        print(f"Exported to: {filepath}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
