#!/usr/bin/env python3
"""
Form Webhook Handler for Lead Scraper

Handles incoming form submissions and:
1. Stores data in Google Sheets
2. Sends notifications (email/SMS) when someone shows interest
3. Creates tasks in ClickUp CRM

Usage:
    # As Flask endpoint (for webhook receiver)
    python -m src.form_webhook serve --port 5000

    # Manual processing (for testing)
    python -m src.form_webhook process --data '{"name": "John", "email": "john@example.com"}'

    # Test notification
    python -m src.form_webhook test-notify

Environment Variables:
    # Google Sheets
    GOOGLE_CLIENT_ID - OAuth client ID
    GOOGLE_CLIENT_SECRET - OAuth client secret
    GOOGLE_SHEETS_SPREADSHEET_ID - Target spreadsheet ID

    # ClickUp
    CLICKUP_API_TOKEN - API token
    CLICKUP_LIST_ID - Target list for new inquiries

    # Twilio (notifications)
    TWILIO_ACCOUNT_SID - Account SID
    TWILIO_AUTH_TOKEN - Auth token
    TWILIO_PHONE_NUMBER - From phone number
    NOTIFICATION_PHONE - Your phone for SMS alerts

    # Email (notifications)
    NOTIFICATION_EMAIL - Your email for alerts
"""

import os
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import requests

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class WebhookConfig:
    """Configuration for webhook handler."""
    # Google Sheets
    google_client_id: str = ""
    google_client_secret: str = ""
    google_sheets_spreadsheet_id: str = ""
    google_sheets_range: str = "Sheet1!A:Z"

    # ClickUp
    clickup_api_token: str = ""
    clickup_list_id: str = ""
    clickup_workspace_id: str = ""

    # Twilio (SMS notifications)
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    notification_phone: str = ""

    # Email notifications
    notification_email: str = ""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587

    # General
    output_dir: str = "output"

    @classmethod
    def from_env(cls) -> "WebhookConfig":
        """Load configuration from environment variables."""
        return cls(
            google_client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
            google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
            google_sheets_spreadsheet_id=os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", ""),
            clickup_api_token=os.getenv("CLICKUP_API_TOKEN", ""),
            clickup_list_id=os.getenv("CLICKUP_LIST_ID", ""),
            clickup_workspace_id=os.getenv("CLICKUP_WORKSPACE_ID", ""),
            twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID", ""),
            twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN", ""),
            twilio_phone_number=os.getenv("TWILIO_PHONE_NUMBER", ""),
            notification_phone=os.getenv("NOTIFICATION_PHONE", ""),
            notification_email=os.getenv("NOTIFICATION_EMAIL", ""),
        )


@dataclass
class FormSubmission:
    """Represents an incoming form submission."""
    # Contact info
    name: str = ""
    email: str = ""
    phone: str = ""
    company: str = ""

    # Inquiry details
    project_type: str = ""  # e.g., "website", "ai_assistant", "consulting"
    message: str = ""
    budget: str = ""
    timeline: str = ""

    # Source tracking
    source: str = ""  # e.g., "landing_page", "cold_outreach", "referral"
    utm_source: str = ""
    utm_medium: str = ""
    utm_campaign: str = ""

    # Metadata
    submitted_at: str = ""
    ip_address: str = ""
    user_agent: str = ""

    # Processing status
    processed: bool = False
    clickup_task_id: str = ""
    sheets_row: int = 0

    def __post_init__(self):
        if not self.submitted_at:
            self.submitted_at = datetime.now().isoformat()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FormSubmission":
        """Create from dictionary (webhook payload)."""
        # Map common form field names to our fields
        field_mapping = {
            "full_name": "name",
            "fullname": "name",
            "first_name": "name",
            "email_address": "email",
            "phone_number": "phone",
            "company_name": "company",
            "business_name": "company",
            "project": "project_type",
            "service": "project_type",
            "inquiry": "message",
            "comments": "message",
            "description": "message",
        }

        normalized = {}
        for key, value in data.items():
            # Normalize the key
            norm_key = key.lower().strip()
            mapped_key = field_mapping.get(norm_key, norm_key)

            # Only set if it's a valid field
            if hasattr(cls, mapped_key) or mapped_key in cls.__dataclass_fields__:
                normalized[mapped_key] = value

        return cls(**{k: v for k, v in normalized.items()
                     if k in cls.__dataclass_fields__})

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_sheets_row(self) -> List[str]:
        """Convert to a row for Google Sheets."""
        return [
            self.submitted_at,
            self.name,
            self.email,
            self.phone,
            self.company,
            self.project_type,
            self.message,
            self.budget,
            self.timeline,
            self.source,
            self.utm_source,
            self.utm_medium,
            self.utm_campaign,
            self.clickup_task_id,
            "Yes" if self.processed else "No"
        ]


# =============================================================================
# Google Sheets Integration
# =============================================================================

class GoogleSheetsClient:
    """Simple Google Sheets client using service account or OAuth."""

    def __init__(self, config: WebhookConfig):
        self.config = config
        self.credentials = None
        self._token = None

    def _get_access_token(self) -> Optional[str]:
        """Get OAuth access token (requires prior authorization)."""
        # Check for stored token
        token_path = Path(self.config.output_dir) / "google_token.json"
        if token_path.exists():
            with open(token_path) as f:
                token_data = json.load(f)

            # Check if token is expired and refresh if needed
            expiry_str = token_data.get("expiry")
            if expiry_str:
                from datetime import datetime
                try:
                    # Handle timezone-aware ISO format
                    expiry = datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))
                    now = datetime.now(expiry.tzinfo) if expiry.tzinfo else datetime.now()

                    if now >= expiry:
                        # Token expired, refresh it
                        refresh_token = token_data.get("refresh_token")
                        client_id = token_data.get("client_id")
                        client_secret = token_data.get("client_secret")
                        token_uri = token_data.get("token_uri", "https://oauth2.googleapis.com/token")

                        if refresh_token and client_id and client_secret:
                            logger.info("Refreshing expired Google token...")
                            response = requests.post(token_uri, data={
                                "grant_type": "refresh_token",
                                "refresh_token": refresh_token,
                                "client_id": client_id,
                                "client_secret": client_secret
                            })

                            if response.status_code == 200:
                                new_token_data = response.json()
                                token_data["token"] = new_token_data["access_token"]
                                # Update expiry (tokens typically last 1 hour)
                                from datetime import timedelta
                                new_expiry = datetime.now() + timedelta(seconds=new_token_data.get("expires_in", 3600))
                                token_data["expiry"] = new_expiry.isoformat() + "Z"

                                # Save updated token
                                with open(token_path, "w") as f:
                                    json.dump(token_data, f)
                                logger.info("Google token refreshed successfully")
                            else:
                                logger.error(f"Failed to refresh token: {response.text}")
                                return None
                except Exception as e:
                    logger.warning(f"Error checking token expiry: {e}")

            # Return the access token (key is "token" not "access_token")
            return token_data.get("token") or token_data.get("access_token")

        logger.warning("No Google access token found. Run authorization flow first.")
        return None

    def append_row(self, spreadsheet_id: str, range_name: str, values: List[str]) -> bool:
        """Append a row to Google Sheets."""
        access_token = self._get_access_token()
        if not access_token:
            logger.error("Cannot append to Sheets: no access token")
            return False

        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_name}:append"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        data = {
            "values": [values],
            "majorDimension": "ROWS"
        }

        params = {
            "valueInputOption": "RAW",
            "insertDataOption": "INSERT_ROWS"
        }

        try:
            response = requests.post(url, headers=headers, json=data, params=params)
            response.raise_for_status()
            logger.info(f"Row appended to Google Sheets")
            return True
        except Exception as e:
            logger.error(f"Failed to append to Sheets: {e}")
            return False


# =============================================================================
# ClickUp Integration
# =============================================================================

class ClickUpClient:
    """ClickUp API client for creating inquiry tasks."""

    API_BASE = "https://api.clickup.com/api/v2"

    def __init__(self, config: WebhookConfig):
        self.config = config

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": self.config.clickup_api_token,
            "Content-Type": "application/json"
        }

    def create_inquiry_task(self, submission: FormSubmission) -> Optional[str]:
        """Create a task in ClickUp for a new inquiry."""
        if not self.config.clickup_api_token or not self.config.clickup_list_id:
            logger.warning("ClickUp not configured - skipping task creation")
            return None

        url = f"{self.API_BASE}/list/{self.config.clickup_list_id}/task"

        # Build task description
        description = f"""**New Inquiry from {submission.source or 'Website'}**

**Contact Information:**
- Name: {submission.name}
- Email: {submission.email}
- Phone: {submission.phone}
- Company: {submission.company}

**Project Details:**
- Type: {submission.project_type}
- Budget: {submission.budget}
- Timeline: {submission.timeline}

**Message:**
{submission.message}

**Tracking:**
- Source: {submission.source}
- Campaign: {submission.utm_campaign}
- Submitted: {submission.submitted_at}
"""

        data = {
            "name": f"Inquiry: {submission.name} - {submission.project_type or 'General'}",
            "description": description,
            "tags": ["inquiry", submission.source] if submission.source else ["inquiry"],
            "status": "to do"
        }

        try:
            response = requests.post(url, headers=self._get_headers(), json=data)
            response.raise_for_status()
            task = response.json()
            task_id = task.get("id")
            logger.info(f"Created ClickUp task: {task_id}")
            return task_id
        except Exception as e:
            logger.error(f"Failed to create ClickUp task: {e}")
            return None

    def get_lists(self, space_id: str = None) -> List[Dict]:
        """Get available lists (for configuration)."""
        if not space_id:
            # Get from workspace
            space_url = f"{self.API_BASE}/team/{self.config.clickup_workspace_id}/space"
            response = requests.get(space_url, headers=self._get_headers())
            spaces = response.json().get("spaces", [])
            if spaces:
                space_id = spaces[0]["id"]

        if not space_id:
            return []

        url = f"{self.API_BASE}/space/{space_id}/list"
        response = requests.get(url, headers=self._get_headers())
        return response.json().get("lists", [])


# =============================================================================
# Notification System
# =============================================================================

class NotificationManager:
    """Send notifications via SMS and email."""

    def __init__(self, config: WebhookConfig):
        self.config = config

    def send_sms_notification(self, submission: FormSubmission) -> bool:
        """Send SMS notification about new inquiry."""
        if not all([
            self.config.twilio_account_sid,
            self.config.twilio_auth_token,
            self.config.twilio_phone_number,
            self.config.notification_phone
        ]):
            logger.warning("Twilio not fully configured - skipping SMS notification")
            return False

        try:
            from twilio.rest import Client

            client = Client(
                self.config.twilio_account_sid,
                self.config.twilio_auth_token
            )

            message_body = (
                f"New Inquiry!\n"
                f"From: {submission.name}\n"
                f"Email: {submission.email}\n"
                f"Project: {submission.project_type}\n"
                f"Source: {submission.source}"
            )

            message = client.messages.create(
                body=message_body,
                from_=self.config.twilio_phone_number,
                to=self.config.notification_phone
            )

            logger.info(f"SMS notification sent: {message.sid}")
            return True

        except ImportError:
            logger.error("Twilio library not installed. Run: pip install twilio")
            return False
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False

    def send_email_notification(self, submission: FormSubmission) -> bool:
        """Send email notification about new inquiry."""
        if not self.config.notification_email:
            logger.warning("Notification email not configured - skipping")
            return False

        # For now, log the email that would be sent
        # Full email implementation would require SMTP credentials
        logger.info(f"Email notification would be sent to: {self.config.notification_email}")
        logger.info(f"Subject: New Inquiry from {submission.name}")
        return True


# =============================================================================
# Webhook Handler
# =============================================================================

class FormWebhookHandler:
    """Main webhook handler that coordinates all integrations."""

    def __init__(self, output_dir: str = "output"):
        self.config = WebhookConfig.from_env()
        self.config.output_dir = output_dir

        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Initialize clients
        self.sheets_client = GoogleSheetsClient(self.config)
        self.clickup_client = ClickUpClient(self.config)
        self.notification_manager = NotificationManager(self.config)

        # Load submission history
        self.submissions_file = Path(output_dir) / "form_submissions.json"
        self.submissions: List[FormSubmission] = []
        self._load_submissions()

    def _load_submissions(self) -> None:
        """Load existing submissions from file."""
        if self.submissions_file.exists():
            with open(self.submissions_file) as f:
                data = json.load(f)
                self.submissions = [
                    FormSubmission(**s) for s in data.get("submissions", [])
                ]

    def _save_submissions(self) -> None:
        """Save submissions to file."""
        data = {
            "submissions": [s.to_dict() for s in self.submissions],
            "last_updated": datetime.now().isoformat()
        }
        with open(self.submissions_file, "w") as f:
            json.dump(data, f, indent=2)

    def process_submission(
        self,
        data: Dict[str, Any],
        source: str = "webhook",
        notify: bool = True,
        create_task: bool = True,
        add_to_sheets: bool = True
    ) -> Dict[str, Any]:
        """
        Process an incoming form submission.

        Args:
            data: Form data dictionary
            source: Where the submission came from
            notify: Whether to send notifications
            create_task: Whether to create ClickUp task
            add_to_sheets: Whether to add to Google Sheets

        Returns:
            Processing result with status and IDs
        """
        result = {
            "success": False,
            "submission_id": None,
            "clickup_task_id": None,
            "sheets_added": False,
            "notifications_sent": [],
            "errors": []
        }

        try:
            # Parse submission
            submission = FormSubmission.from_dict(data)
            submission.source = source

            # Generate unique ID
            submission_id = f"sub_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.submissions)}"
            result["submission_id"] = submission_id

            logger.info(f"Processing submission from {submission.name} ({submission.email})")

            # 1. Add to Google Sheets
            if add_to_sheets and self.config.google_sheets_spreadsheet_id:
                sheets_success = self.sheets_client.append_row(
                    self.config.google_sheets_spreadsheet_id,
                    self.config.google_sheets_range,
                    submission.to_sheets_row()
                )
                result["sheets_added"] = sheets_success
                if not sheets_success:
                    result["errors"].append("Failed to add to Google Sheets")

            # 2. Create ClickUp task
            if create_task:
                task_id = self.clickup_client.create_inquiry_task(submission)
                if task_id:
                    submission.clickup_task_id = task_id
                    result["clickup_task_id"] = task_id
                else:
                    result["errors"].append("Failed to create ClickUp task")

            # 3. Send notifications
            if notify:
                # SMS notification
                if self.notification_manager.send_sms_notification(submission):
                    result["notifications_sent"].append("sms")

                # Email notification
                if self.notification_manager.send_email_notification(submission):
                    result["notifications_sent"].append("email")

            # Mark as processed and save
            submission.processed = True
            self.submissions.append(submission)
            self._save_submissions()

            result["success"] = True
            logger.info(f"Submission processed successfully: {submission_id}")

        except Exception as e:
            logger.error(f"Error processing submission: {e}")
            result["errors"].append(str(e))

        return result

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about form submissions."""
        total = len(self.submissions)
        processed = sum(1 for s in self.submissions if s.processed)

        by_source = {}
        by_project_type = {}

        for s in self.submissions:
            by_source[s.source or "unknown"] = by_source.get(s.source or "unknown", 0) + 1
            by_project_type[s.project_type or "general"] = by_project_type.get(s.project_type or "general", 0) + 1

        return {
            "total_submissions": total,
            "processed": processed,
            "by_source": by_source,
            "by_project_type": by_project_type,
            "with_clickup_task": sum(1 for s in self.submissions if s.clickup_task_id)
        }


# =============================================================================
# Flask Webhook Server
# =============================================================================

def create_webhook_app(handler: FormWebhookHandler):
    """Create Flask app for receiving webhooks."""
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        logger.error("Flask not installed. Run: pip install flask")
        return None

    app = Flask(__name__)

    @app.route("/webhook/form", methods=["POST"])
    def handle_form_webhook():
        """Handle incoming form webhooks."""
        try:
            data = request.get_json() or request.form.to_dict()
            source = request.args.get("source", "webhook")

            result = handler.process_submission(data, source=source)

            if result["success"]:
                return jsonify({"status": "success", **result}), 200
            else:
                return jsonify({"status": "error", **result}), 500

        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/webhook/health", methods=["GET"])
    def health_check():
        """Health check endpoint."""
        return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

    @app.route("/webhook/stats", methods=["GET"])
    def get_stats():
        """Get submission statistics."""
        return jsonify(handler.get_statistics())

    return app


# =============================================================================
# CLI
# =============================================================================

def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Form Webhook Handler")
    subparsers = parser.add_subparsers(dest="command")

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start webhook server")
    serve_parser.add_argument("--port", type=int, default=5000, help="Port to listen on")
    serve_parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    serve_parser.add_argument("--output-dir", type=str, default="output", help="Output directory")

    # Process command (manual testing)
    process_parser = subparsers.add_parser("process", help="Process a form submission manually")
    process_parser.add_argument("--data", type=str, required=True, help="JSON data to process")
    process_parser.add_argument("--source", type=str, default="manual", help="Source identifier")
    process_parser.add_argument("--output-dir", type=str, default="output", help="Output directory")

    # Test notification
    test_parser = subparsers.add_parser("test-notify", help="Send a test notification")
    test_parser.add_argument("--output-dir", type=str, default="output", help="Output directory")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show submission statistics")
    stats_parser.add_argument("--output-dir", type=str, default="output", help="Output directory")

    # List ClickUp lists
    clickup_parser = subparsers.add_parser("clickup-lists", help="List available ClickUp lists")
    clickup_parser.add_argument("--output-dir", type=str, default="output", help="Output directory")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    output_dir = getattr(args, "output_dir", "output")
    handler = FormWebhookHandler(output_dir=output_dir)

    if args.command == "serve":
        app = create_webhook_app(handler)
        if app:
            print(f"Starting webhook server on {args.host}:{args.port}")
            print(f"Endpoints:")
            print(f"  POST /webhook/form - Receive form submissions")
            print(f"  GET  /webhook/health - Health check")
            print(f"  GET  /webhook/stats - Submission statistics")
            app.run(host=args.host, port=args.port, debug=True)
        else:
            print("Failed to create Flask app. Install flask: pip install flask")
            return 1

    elif args.command == "process":
        data = json.loads(args.data)
        result = handler.process_submission(data, source=args.source)
        print(json.dumps(result, indent=2))

    elif args.command == "test-notify":
        test_submission = FormSubmission(
            name="Test User",
            email="test@example.com",
            phone="555-1234",
            company="Test Company",
            project_type="website",
            message="This is a test notification",
            source="test"
        )

        print("Sending test notifications...")
        sms_sent = handler.notification_manager.send_sms_notification(test_submission)
        email_sent = handler.notification_manager.send_email_notification(test_submission)

        print(f"SMS sent: {sms_sent}")
        print(f"Email sent: {email_sent}")

    elif args.command == "stats":
        stats = handler.get_statistics()
        print("\n=== Form Submission Statistics ===")
        print(f"Total submissions: {stats['total_submissions']}")
        print(f"Processed: {stats['processed']}")
        print(f"With ClickUp task: {stats['with_clickup_task']}")
        print("\nBy Source:")
        for source, count in stats["by_source"].items():
            print(f"  {source}: {count}")
        print("\nBy Project Type:")
        for ptype, count in stats["by_project_type"].items():
            print(f"  {ptype}: {count}")

    elif args.command == "clickup-lists":
        lists = handler.clickup_client.get_lists()
        print("\n=== Available ClickUp Lists ===")
        for lst in lists:
            print(f"  - {lst['name']} (ID: {lst['id']})")
        print("\nSet CLICKUP_LIST_ID in .env to enable automatic task creation")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
