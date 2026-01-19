"""
Multi-Business Form Handler

Extends the base FormHandler to support multiple businesses with:
- Business-specific CRM routing (ClickUp lists)
- Business-specific Google Sheets
- Owner notifications to correct person
- Auto-responses to customers
- Business-specific nurturing sequences
"""

import os
import json
import smtplib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv

from .models import FormSubmission
from .handler import FormHandler
from .business_config import BusinessConfig, get_business_config, BUSINESS_CONFIGS

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")


class MultiBusinessFormHandler(FormHandler):
    """
    Form handler that routes submissions to business-specific pipelines.

    Extends FormHandler with:
    - Business detection from form source
    - Per-business CRM routing
    - Owner notifications
    - Customer auto-responses
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize with base handler settings."""
        super().__init__(output_dir)

    def process_submission(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process form submission with business-specific routing.

        Args:
            data: Form data including 'source' or 'business_id' field

        Returns:
            Result dictionary with status and IDs
        """
        result = {
            "success": False,
            "submission_id": "",
            "business_id": "",
            "clickup_task_id": "",
            "google_sheet_row": 0,
            "notifications_sent": [],
            "auto_responses_sent": [],
            "errors": []
        }

        try:
            # Determine which business this form belongs to
            business = self._detect_business(data)
            result["business_id"] = business.business_id if business else "unknown"

            # Parse form data
            submission = FormSubmission.from_dict(data)
            result["submission_id"] = submission.submission_id

            # Step 1: Save to business-specific JSON directory
            self._save_to_business_json(submission, business)

            # Step 2: Create task in business-specific ClickUp list
            if business and business.clickup_list_id:
                try:
                    task_id = self._create_business_clickup_task(submission, business)
                    result["clickup_task_id"] = task_id
                except Exception as e:
                    result["errors"].append(f"ClickUp: {str(e)}")
            elif business:
                # Use default ClickUp list from parent
                try:
                    task_id = self._create_clickup_task(submission)
                    result["clickup_task_id"] = task_id
                except Exception as e:
                    result["errors"].append(f"ClickUp: {str(e)}")

            # Step 3: Append to business-specific Google Sheets
            if business and business.google_sheet_id:
                try:
                    row_num = self._append_to_business_sheets(submission, business)
                    result["google_sheet_row"] = row_num
                except Exception as e:
                    result["errors"].append(f"Google Sheets: {str(e)}")
            else:
                # Use default sheets from parent
                try:
                    row_num = self._append_to_sheets(submission)
                    result["google_sheet_row"] = row_num
                except Exception as e:
                    result["errors"].append(f"Google Sheets: {str(e)}")

            # Step 4: Notify business owner
            if business:
                try:
                    self._notify_business_owner(submission, business)
                    result["notifications_sent"].append(f"owner_email:{business.owner_email}")
                    if business.owner_phone:
                        result["notifications_sent"].append(f"owner_sms:{business.owner_phone}")
                except Exception as e:
                    result["errors"].append(f"Owner notification: {str(e)}")

            # Also notify William (central monitoring)
            try:
                self._send_email_notification(submission)
                result["notifications_sent"].append("central_email")
            except Exception as e:
                result["errors"].append(f"Central notification: {str(e)}")

            # Step 5: Send auto-response to customer
            if business and business.auto_response_enabled:
                try:
                    self._send_customer_auto_response(submission, business)
                    result["auto_responses_sent"].append("email")
                    if submission.phone and submission.sms_opt_in:
                        result["auto_responses_sent"].append("sms")
                except Exception as e:
                    result["errors"].append(f"Auto-response: {str(e)}")

            # Step 6: Add to nurturing sequence
            if business and business.nurturing_enabled:
                try:
                    self._add_to_business_nurturing(submission, business)
                except Exception as e:
                    result["errors"].append(f"Nurturing: {str(e)}")

            result["success"] = True

        except Exception as e:
            result["errors"].append(f"Processing error: {str(e)}")

        return result

    def _detect_business(self, data: Dict[str, Any]) -> Optional[BusinessConfig]:
        """
        Detect which business the form belongs to.

        Checks in order:
        1. Explicit business_id field
        2. Form source field
        3. Referrer/origin header
        4. Default to Marceau Solutions
        """
        # Check explicit business_id
        if data.get("business_id"):
            config = get_business_config(data["business_id"])
            if config:
                return config

        # Check source field
        if data.get("source"):
            config = get_business_config(data["source"])
            if config:
                return config

        # Check referrer
        if data.get("referrer"):
            config = get_business_config(data["referrer"])
            if config:
                return config

        # Check origin header
        if data.get("origin"):
            config = get_business_config(data["origin"])
            if config:
                return config

        # Default
        return get_business_config("marceausolutions")

    def _save_to_business_json(self, submission: FormSubmission, business: Optional[BusinessConfig]) -> Path:
        """Save submission to business-specific directory."""
        business_id = business.business_id if business else "unknown"
        date_str = datetime.now().strftime("%Y-%m-%d")

        # Create business-specific directory
        business_dir = self.output_dir / business_id / date_str
        business_dir.mkdir(parents=True, exist_ok=True)

        # Save submission
        filename = f"{submission.submission_id}.json"
        filepath = business_dir / filename

        with open(filepath, 'w') as f:
            f.write(submission.to_json())

        # Also save to master file
        self._save_to_json(submission)

        return filepath

    def _create_business_clickup_task(
        self,
        submission: FormSubmission,
        business: BusinessConfig
    ) -> str:
        """Create ClickUp task in business-specific list."""
        import requests

        url = f"https://api.clickup.com/api/v2/list/{business.clickup_list_id}/task"

        headers = {
            "Authorization": self.clickup_token,
            "Content-Type": "application/json"
        }

        # Create task with business context
        task_name = f"Lead: {submission.get_display_name()}"

        # Enhanced description with business info
        description = f"**Business:** {business.business_name}\n\n"
        description += submission.to_clickup_description()

        payload = {
            "name": task_name,
            "description": description,
            "priority": 2,  # High priority for all leads
            "tags": [
                f"from-{business.business_id}",
                "website-lead",
                "auto-created"
            ],
        }

        # Add due date (follow up within 2 hours for local businesses)
        import time
        due_date = int((time.time() + 7200) * 1000)  # 2 hours for HVAC urgency
        payload["due_date"] = due_date

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        return response.json().get("id", "")

    def _append_to_business_sheets(
        self,
        submission: FormSubmission,
        business: BusinessConfig
    ) -> int:
        """Append to business-specific Google Sheet."""
        # Override sheets_spreadsheet_id temporarily
        original_sheet_id = self.sheets_spreadsheet_id
        self.sheets_spreadsheet_id = business.google_sheet_id

        try:
            row_num = self._append_to_sheets(submission)
        finally:
            self.sheets_spreadsheet_id = original_sheet_id

        return row_num

    def _notify_business_owner(
        self,
        submission: FormSubmission,
        business: BusinessConfig
    ) -> None:
        """Send notification to business owner."""
        # Email notification
        if business.owner_email:
            self._send_owner_email(submission, business)

        # SMS notification
        if business.owner_phone:
            self._send_owner_sms(submission, business)

    def _send_owner_email(
        self,
        submission: FormSubmission,
        business: BusinessConfig
    ) -> None:
        """Send email notification to business owner."""
        subject = f"🔔 New Lead for {business.business_name}"

        body = f"""
New form submission for {business.business_name}!

CONTACT INFORMATION:
- Name: {submission.name or 'Not provided'}
- Email: {submission.email}
- Phone: {submission.phone or 'Not provided'}

"""
        if submission.interest:
            body += f"SERVICE REQUESTED: {submission.interest}\n\n"

        if submission.message:
            body += f"MESSAGE:\n{submission.message}\n\n"

        body += f"""
---
Submitted: {submission.timestamp}
Source: {submission.source}

Reply to this email or call the customer directly.
"""

        msg = MIMEMultipart()
        msg['From'] = f"Marceau Solutions <{self.sender_email}>"
        msg['To'] = business.owner_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)

    def _send_owner_sms(
        self,
        submission: FormSubmission,
        business: BusinessConfig
    ) -> None:
        """Send SMS notification to business owner."""
        from twilio.rest import Client

        client = Client(self.twilio_sid, self.twilio_token)

        message = f"🔔 New {business.business_name} lead!\n"
        message += f"Name: {submission.name or 'N/A'}\n"
        message += f"Phone: {submission.phone or 'N/A'}\n"
        if submission.interest:
            message += f"Service: {submission.interest}"

        client.messages.create(
            body=message,
            from_=self.twilio_phone,
            to=business.owner_phone
        )

    def _send_customer_auto_response(
        self,
        submission: FormSubmission,
        business: BusinessConfig
    ) -> None:
        """Send auto-response to the customer."""
        # Skip test emails
        test_domains = ["example.com", "test.com", "fake.com"]
        if any(domain in submission.email for domain in test_domains):
            return

        # Send email auto-response
        if business.auto_response_email_template:
            self._send_customer_email(submission, business)

        # Send SMS auto-response if phone provided and opted in
        if submission.phone and submission.sms_opt_in and business.auto_response_sms_template:
            self._send_customer_sms(submission, business)

    def _send_customer_email(
        self,
        submission: FormSubmission,
        business: BusinessConfig
    ) -> None:
        """Send auto-response email to customer."""
        # Format template with submission data
        template_vars = {
            "name": submission.name or "there",
            "interest": submission.interest or "your inquiry",
            "calendly_link": business.calendly_link or "",
            "business_name": business.business_name,
            "service_type": submission.interest or "service",
        }

        body = business.auto_response_email_template.format(**template_vars)
        subject = f"Thanks for contacting {business.business_name}!"

        msg = MIMEMultipart()
        msg['From'] = f"{business.business_name} <{self.sender_email}>"
        msg['To'] = submission.email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)

    def _send_customer_sms(
        self,
        submission: FormSubmission,
        business: BusinessConfig
    ) -> None:
        """Send auto-response SMS to customer."""
        from twilio.rest import Client

        client = Client(self.twilio_sid, self.twilio_token)

        # Format template
        template_vars = {
            "name": submission.name or "there",
            "service_type": submission.interest or "service",
            "business_name": business.business_name,
        }

        message = business.auto_response_sms_template.format(**template_vars)

        client.messages.create(
            body=message,
            from_=self.twilio_phone,
            to=submission.phone
        )

    def _add_to_business_nurturing(
        self,
        submission: FormSubmission,
        business: BusinessConfig
    ) -> None:
        """Add lead to business-specific nurturing sequence."""
        nurture_file = self.output_dir / business.business_id / "nurture_queue.json"
        nurture_file.parent.mkdir(parents=True, exist_ok=True)

        queue = []
        if nurture_file.exists():
            with open(nurture_file, 'r') as f:
                try:
                    queue = json.load(f)
                except:
                    queue = []

        # Add to nurturing queue
        queue.append({
            "submission_id": submission.submission_id,
            "email": submission.email,
            "phone": submission.phone,
            "name": submission.name,
            "business_id": business.business_id,
            "sequence_id": business.nurturing_sequence_id or "default",
            "added_at": datetime.now().isoformat(),
            "status": "pending",
            "touches": 0,
            "next_touch_at": datetime.now().isoformat(),
        })

        with open(nurture_file, 'w') as f:
            json.dump(queue, f, indent=2)


def get_handler() -> MultiBusinessFormHandler:
    """Get singleton handler instance."""
    return MultiBusinessFormHandler()
