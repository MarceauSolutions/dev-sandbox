"""
FormHandler - Main handler for processing form submissions.

Orchestrates:
1. JSON file storage
2. ClickUp CRM integration
3. Google Sheets logging
4. Email/SMS notifications
5. Workflow triggers
"""

import os
import json
import smtplib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import requests
from dotenv import load_dotenv

from .models import FormSubmission, LeadSource

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")


class FormHandler:
    """
    Unified form submission handler.

    Processes form submissions from all website pages and:
    1. Saves to local JSON file (backup/audit trail)
    2. Creates lead in ClickUp CRM
    3. Appends row to Google Sheets
    4. Sends notification email
    5. Optionally sends SMS notification
    6. Triggers follow-up workflows based on source
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize handler with configuration from environment."""
        # Output directory for JSON files
        self.output_dir = output_dir or Path(__file__).parent.parent.parent / "output" / "form_submissions"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # ClickUp configuration
        self.clickup_token = os.getenv("CLICKUP_API_TOKEN", "")
        self.clickup_list_id = os.getenv("CLICKUP_LIST_ID", "")

        # Google Sheets configuration
        self.sheets_spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")

        # Notification configuration
        self.notification_email = os.getenv("NOTIFICATION_EMAIL", "")
        self.notification_phone = os.getenv("NOTIFICATION_PHONE", "")
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.sender_name = os.getenv("SENDER_NAME", "Form Handler")
        self.sender_email = os.getenv("SENDER_EMAIL", self.smtp_username)

        # Twilio configuration (for SMS)
        self.twilio_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.twilio_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.twilio_phone = os.getenv("TWILIO_PHONE_NUMBER", "")

    def process_submission(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a form submission through all integrations.

        Args:
            data: Raw form data dictionary

        Returns:
            Result dictionary with status and IDs
        """
        result = {
            "success": False,
            "submission_id": "",
            "clickup_task_id": "",
            "google_sheet_row": 0,
            "notifications_sent": [],
            "errors": []
        }

        try:
            # Parse form data into submission object
            submission = FormSubmission.from_dict(data)
            result["submission_id"] = submission.submission_id

            # Step 1: Save to JSON (always succeeds, acts as backup)
            self._save_to_json(submission)

            # Step 2: Create ClickUp task
            try:
                task_id = self._create_clickup_task(submission)
                submission.clickup_task_id = task_id
                result["clickup_task_id"] = task_id
            except Exception as e:
                submission.errors.append(f"ClickUp error: {str(e)}")
                result["errors"].append(f"ClickUp: {str(e)}")

            # Step 3: Append to Google Sheets
            try:
                row_num = self._append_to_sheets(submission)
                submission.google_sheet_row = row_num
                result["google_sheet_row"] = row_num
            except Exception as e:
                submission.errors.append(f"Google Sheets error: {str(e)}")
                result["errors"].append(f"Google Sheets: {str(e)}")

            # Step 4: Send email notification
            try:
                self._send_email_notification(submission)
                result["notifications_sent"].append("email")
            except Exception as e:
                submission.errors.append(f"Email notification error: {str(e)}")
                result["errors"].append(f"Email: {str(e)}")

            # Step 5: Send SMS notification (if configured)
            if self.notification_phone and self.twilio_sid:
                try:
                    self._send_sms_notification(submission)
                    result["notifications_sent"].append("sms")
                except Exception as e:
                    submission.errors.append(f"SMS notification error: {str(e)}")
                    result["errors"].append(f"SMS: {str(e)}")

            # Step 6: Trigger source-specific workflows
            try:
                self._trigger_workflows(submission)
            except Exception as e:
                submission.errors.append(f"Workflow trigger error: {str(e)}")
                result["errors"].append(f"Workflows: {str(e)}")

            # Mark as processed if critical steps succeeded
            submission.processed = bool(submission.clickup_task_id or submission.google_sheet_row)

            # Update JSON file with final status
            self._save_to_json(submission)

            result["success"] = submission.processed

        except Exception as e:
            result["errors"].append(f"Processing error: {str(e)}")

        return result

    def _save_to_json(self, submission: FormSubmission) -> Path:
        """
        Save submission to JSON file.

        Files are organized by date: output/form_submissions/YYYY-MM-DD/
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        date_dir = self.output_dir / date_str
        date_dir.mkdir(exist_ok=True)

        filename = f"{submission.submission_id}.json"
        filepath = date_dir / filename

        with open(filepath, 'w') as f:
            f.write(submission.to_json())

        # Also update the master submissions file
        master_file = self.output_dir / "all_submissions.json"
        submissions = []
        if master_file.exists():
            with open(master_file, 'r') as f:
                try:
                    submissions = json.load(f)
                except:
                    submissions = []

        # Update or append
        updated = False
        for i, s in enumerate(submissions):
            if s.get("submission_id") == submission.submission_id:
                submissions[i] = submission.to_dict()
                updated = True
                break
        if not updated:
            submissions.append(submission.to_dict())

        with open(master_file, 'w') as f:
            json.dump(submissions, f, indent=2)

        return filepath

    def _create_clickup_task(self, submission: FormSubmission) -> str:
        """
        Create a task in ClickUp CRM.

        Returns:
            Task ID string
        """
        if not self.clickup_token or not self.clickup_list_id:
            raise ValueError("ClickUp not configured (missing token or list ID)")

        url = f"https://api.clickup.com/api/v2/list/{self.clickup_list_id}/task"

        headers = {
            "Authorization": self.clickup_token,
            "Content-Type": "application/json"
        }

        # Determine priority based on source
        priority_map = {
            "fitness_influencer_landing": 2,  # High
            "interview_prep_landing": 2,
            "contact-page": 3,  # Normal
            "home-page": 3,
        }
        priority = priority_map.get(submission.source, 3)

        # Create task name
        task_name = f"Lead: {submission.get_display_name()}"
        if submission.interest:
            task_name += f" - {submission.interest}"

        payload = {
            "name": task_name,
            "description": submission.to_clickup_description(),
            "priority": priority,
            "tags": [
                submission.source.replace("_", "-"),
                "website-lead",
                "auto-created"
            ],
            "custom_fields": []  # Can be extended with custom field IDs
        }

        # Add due date (follow up within 24 hours)
        # ClickUp uses milliseconds
        import time
        due_date = int((time.time() + 86400) * 1000)  # 24 hours from now
        payload["due_date"] = due_date

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        task_data = response.json()
        return task_data.get("id", "")

    def _append_to_sheets(self, submission: FormSubmission) -> int:
        """
        Append submission to Google Sheets.

        Returns:
            Row number where data was appended
        """
        if not self.sheets_spreadsheet_id:
            raise ValueError("Google Sheets not configured (missing spreadsheet ID)")

        # Use Google Sheets API via service account or OAuth
        # For now, we'll use a simple append via the Sheets API

        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            import pickle

            SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
            creds = None
            token_path = Path(__file__).parent.parent.parent / "token.json"
            creds_path = Path(__file__).parent.parent.parent / "credentials.json"

            if token_path.exists():
                with open(token_path, 'rb') as token:
                    creds = pickle.load(token)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                elif creds_path.exists():
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(creds_path), SCOPES)
                    creds = flow.run_local_server(port=0)
                else:
                    raise ValueError("No credentials found for Google Sheets")

                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)

            service = build('sheets', 'v4', credentials=creds)
            sheet = service.spreadsheets()

            # Append row to Form Submissions sheet
            range_name = "Form Submissions!A:Q"
            values = [submission.to_sheet_row()]

            body = {'values': values}
            result = sheet.values().append(
                spreadsheetId=self.sheets_spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()

            # Parse the updated range to get row number
            updated_range = result.get('updates', {}).get('updatedRange', '')
            # Format: "Form Submissions!A123:Q123"
            if ':' in updated_range:
                row_part = updated_range.split('!')[1].split(':')[0]
                row_num = int(''.join(filter(str.isdigit, row_part)))
                return row_num

            return 0

        except ImportError:
            # Google API not installed, log the submission data
            print(f"Google Sheets API not available. Submission logged to JSON.")
            return 0

    def _send_email_notification(self, submission: FormSubmission) -> None:
        """Send email notification about new submission."""
        if not self.notification_email or not self.smtp_username:
            return

        subject = f"New Lead: {submission.get_display_name()}"
        if submission.source:
            subject += f" [{submission.get_source_label()}]"

        body = f"""
New form submission received!

Source: {submission.get_source_label()}
Time: {submission.timestamp}

CONTACT INFO:
- Name: {submission.name or 'Not provided'}
- Email: {submission.email}
- Phone: {submission.phone or 'Not provided'}

"""
        if submission.interest:
            body += f"INTEREST: {submission.interest}\n\n"

        if submission.social_handle or submission.followers:
            body += f"""SOCIAL MEDIA:
- Handle: {submission.social_handle or 'Not provided'}
- Followers: {submission.followers or 'Not provided'}

"""

        if submission.message:
            body += f"""MESSAGE:
{submission.message}

"""

        body += f"""CONSENT:
- Email marketing: {'Yes' if submission.email_opt_in else 'No'}
- SMS marketing: {'Yes' if submission.sms_opt_in else 'No'}

---
Submission ID: {submission.submission_id}
"""
        if submission.clickup_task_id:
            body += f"ClickUp Task: https://app.clickup.com/t/{submission.clickup_task_id}\n"

        msg = MIMEMultipart()
        msg['From'] = f"{self.sender_name} <{self.sender_email}>"
        msg['To'] = self.notification_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)

    def _send_sms_notification(self, submission: FormSubmission) -> None:
        """Send SMS notification about new submission."""
        if not all([self.twilio_sid, self.twilio_token, self.twilio_phone, self.notification_phone]):
            return

        from twilio.rest import Client

        client = Client(self.twilio_sid, self.twilio_token)

        message_body = f"New lead: {submission.get_display_name()}"
        if submission.interest:
            message_body += f" - {submission.interest}"
        message_body += f"\nFrom: {submission.get_source_label()}"
        message_body += f"\nEmail: {submission.email}"

        client.messages.create(
            body=message_body,
            from_=self.twilio_phone,
            to=self.notification_phone
        )

    def _trigger_workflows(self, submission: FormSubmission) -> None:
        """
        Trigger source-specific workflows.

        Based on the source page, different follow-up actions may be needed.
        """
        source = submission.source

        # Fitness Influencer leads - schedule for follow-up sequence
        if source == "fitness_influencer_landing":
            self._add_to_follow_up_sequence(submission, "fitness_influencer")

        # High-value leads from contact page with specific interest
        elif source == "contact-page" and submission.interest in ["Custom AI Solution", "MedTech Solutions"]:
            self._flag_for_immediate_follow_up(submission)

        # All leads with phone and SMS opt-in - add to SMS sequence
        if submission.phone and submission.sms_opt_in:
            self._add_to_sms_sequence(submission)

    def _add_to_follow_up_sequence(self, submission: FormSubmission, sequence_type: str) -> None:
        """Add lead to automated follow-up sequence."""
        # This would integrate with the lead-scraper follow-up system
        # For now, we log the intent
        sequence_file = self.output_dir / "follow_up_queue.json"
        queue = []
        if sequence_file.exists():
            with open(sequence_file, 'r') as f:
                try:
                    queue = json.load(f)
                except:
                    queue = []

        queue.append({
            "submission_id": submission.submission_id,
            "email": submission.email,
            "phone": submission.phone,
            "sequence_type": sequence_type,
            "added_at": datetime.now().isoformat(),
            "status": "pending"
        })

        with open(sequence_file, 'w') as f:
            json.dump(queue, f, indent=2)

    def _flag_for_immediate_follow_up(self, submission: FormSubmission) -> None:
        """Flag high-priority leads for immediate follow-up."""
        priority_file = self.output_dir / "priority_leads.json"
        leads = []
        if priority_file.exists():
            with open(priority_file, 'r') as f:
                try:
                    leads = json.load(f)
                except:
                    leads = []

        leads.append({
            "submission_id": submission.submission_id,
            "name": submission.name,
            "email": submission.email,
            "phone": submission.phone,
            "interest": submission.interest,
            "flagged_at": datetime.now().isoformat(),
            "reason": "High-value inquiry"
        })

        with open(priority_file, 'w') as f:
            json.dump(leads, f, indent=2)

    def _add_to_sms_sequence(self, submission: FormSubmission) -> None:
        """Add lead to SMS follow-up sequence."""
        sms_file = self.output_dir / "sms_queue.json"
        queue = []
        if sms_file.exists():
            with open(sms_file, 'r') as f:
                try:
                    queue = json.load(f)
                except:
                    queue = []

        queue.append({
            "submission_id": submission.submission_id,
            "phone": submission.phone,
            "name": submission.name,
            "source": submission.source,
            "added_at": datetime.now().isoformat(),
            "status": "pending"
        })

        with open(sms_file, 'w') as f:
            json.dump(queue, f, indent=2)

    def get_submissions_by_date(self, date: str) -> List[FormSubmission]:
        """Get all submissions for a specific date (YYYY-MM-DD)."""
        date_dir = self.output_dir / date
        submissions = []

        if date_dir.exists():
            for filepath in date_dir.glob("*.json"):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    submissions.append(FormSubmission.from_dict(data))

        return submissions

    def get_all_submissions(self) -> List[FormSubmission]:
        """Get all submissions from master file."""
        master_file = self.output_dir / "all_submissions.json"
        if not master_file.exists():
            return []

        with open(master_file, 'r') as f:
            data = json.load(f)

        return [FormSubmission.from_dict(s) for s in data]
