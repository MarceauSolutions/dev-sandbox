#!/usr/bin/env python3
"""
routine_scheduler.py - Create Recurring Calendar Reminders

Sets up recurring calendar events for routine tasks:
- Daily: Morning digest review, SMS check, form submissions
- Weekly: Campaign review, ClickUp pipeline, product opportunities
- Bi-weekly: Revenue analytics, Amazon inventory
- Monthly: Revenue comparison, ROI analysis

Usage:
    python -m src.routine_scheduler setup        # Create all reminders
    python -m src.routine_scheduler list         # List existing reminders
    python -m src.routine_scheduler delete       # Remove all routine reminders
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    print("Warning: Google API libraries not installed")


# Routine reminders configuration
ROUTINE_REMINDERS = {
    "daily": [
        {
            "summary": "📧 Review Morning Digest",
            "description": "Check morning digest email for:\n- Urgent emails\n- SMS replies (hot leads, callbacks)\n- New form submissions\n- Today's calendar\n- Action items",
            "time": "08:00",
            "duration_minutes": 15,
            "color_id": "9",  # Blue
        },
        {
            "summary": "📱 Check SMS Replies",
            "description": "Run: python -m src.twilio_webhook stats\n\nRespond to:\n- Hot leads (call within 1 hour)\n- Questions\n- Callback requests",
            "time": "10:00",
            "duration_minutes": 15,
            "color_id": "6",  # Orange
        },
        {
            "summary": "📝 Check Form Submissions",
            "description": "Check Google Sheet: Lead Submissions\n\nReview new inquiries and create ClickUp tasks for qualified leads.",
            "time": "10:15",
            "duration_minutes": 10,
            "color_id": "10",  # Green
        },
    ],
    "weekly_monday": [
        {
            "summary": "📊 Weekly Campaign Performance Review",
            "description": "Run:\n- python -m src.campaign_analytics report\n- python -m src.campaign_analytics templates\n- python -m src.campaign_analytics funnel\n\nAnalyze:\n- Response rates by template\n- Conversion funnel\n- A/B test results",
            "time": "09:00",
            "duration_minutes": 30,
            "color_id": "11",  # Red
        },
        {
            "summary": "📋 ClickUp CRM Pipeline Review",
            "description": "Review ClickUp pipeline:\n- Leads in each stage\n- Stale deals (>7 days no activity)\n- Follow-up required\n- Close predictions",
            "time": "09:30",
            "duration_minutes": 20,
            "color_id": "7",  # Cyan
        },
        {
            "summary": "📅 Week Preview",
            "description": "Run: python calendar_reminders.py list --days 7\n\nReview upcoming:\n- Client calls\n- Deadlines\n- Content blocks\n- Review sessions",
            "time": "10:00",
            "duration_minutes": 15,
            "color_id": "9",  # Blue
        },
    ],
    "weekly_friday": [
        {
            "summary": "💡 Product Opportunity Review",
            "description": "Open: methods/product-opportunities/OPPORTUNITY-LOG.md\n\nReview pending opportunities:\n- Score viability (SOP 17)\n- Archive low-potential\n- Kickoff high-potential (SOP 0)",
            "time": "16:00",
            "duration_minutes": 30,
            "color_id": "3",  # Purple
        },
        {
            "summary": "📝 Weekly Session Documentation",
            "description": "Update docs/session-history.md:\n- Key accomplishments\n- Learnings\n- New patterns discovered\n\nCommit documentation updates.",
            "time": "16:30",
            "duration_minutes": 15,
            "color_id": "8",  # Gray
        },
    ],
    "biweekly": [
        {
            "summary": "💰 Revenue Analytics Review",
            "description": "Run: python revenue_analytics.py report\n\nReview:\n- Revenue by source\n- MoM growth\n- API costs (COGS)\n- Profit margin (target: 60%+)",
            "time": "10:00",
            "duration_minutes": 30,
            "color_id": "5",  # Yellow
        },
        {
            "summary": "📦 Amazon Inventory Check",
            "description": "Check:\n- Low stock alerts (<14 days)\n- Aged inventory (storage fees)\n- Buy box status\n- Review monitoring",
            "time": "10:30",
            "duration_minutes": 20,
            "color_id": "6",  # Orange
        },
        {
            "summary": "🧪 A/B Test Results Review",
            "description": "Run: python -m src.campaign_analytics ab-test results\n\nCheck if tests reached:\n- 100+ contacts per variant\n- 85% confidence threshold\n- 7+ day runtime\n\nDeclare winners and update templates.",
            "time": "11:00",
            "duration_minutes": 20,
            "color_id": "11",  # Red
        },
    ],
    "monthly": [
        {
            "summary": "📊 Monthly Revenue Comparison",
            "description": "Generate month-over-month report:\n- Total revenue vs last month\n- Revenue by source breakdown\n- Cost analysis\n- Profit trends\n\nSet goals for next month.",
            "time": "09:00",
            "duration_minutes": 45,
            "color_id": "5",  # Yellow
        },
        {
            "summary": "📈 Campaign ROI Analysis",
            "description": "Calculate:\n- Cost per lead (SMS costs / contacts)\n- Cost per conversion\n- ROI per campaign\n- Template performance trends\n\nDecide: Scale winners, retire losers.",
            "time": "10:00",
            "duration_minutes": 30,
            "color_id": "11",  # Red
        },
        {
            "summary": "🗂️ Repository Cleanup",
            "description": "Run: find . -name '.git' -type d\n\nCheck for:\n- Nested repos (fix immediately)\n- Stale branches\n- Uncommitted changes\n- Deploy vs dev version mismatches",
            "time": "11:00",
            "duration_minutes": 20,
            "color_id": "8",  # Gray
        },
    ],
}


class RoutineScheduler:
    """
    Creates recurring calendar events for routine tasks.
    """

    SCOPES = ['https://www.googleapis.com/auth/calendar']
    REMINDER_TAG = "[ROUTINE]"  # Tag to identify our reminders

    def __init__(self, credentials_path: str = 'credentials.json', token_path: str = 'token.json'):
        """Initialize scheduler."""
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None

    def authenticate(self) -> bool:
        """Authenticate with Google Calendar API."""
        if not GOOGLE_AVAILABLE:
            print("Google libraries not available")
            return False

        creds = None

        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    print(f"ERROR: Credentials file not found: {self.credentials_path}")
                    return False

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        try:
            self.service = build('calendar', 'v3', credentials=creds)
            return True
        except Exception as e:
            print(f"ERROR building Calendar service: {e}")
            return False

    def _get_next_day(self, weekday: int) -> datetime:
        """Get the next occurrence of a weekday (0=Monday, 6=Sunday)."""
        today = datetime.now()
        days_ahead = weekday - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return today + timedelta(days=days_ahead)

    def _create_rrule(self, frequency: str) -> str:
        """Create RRULE string for recurrence."""
        if frequency == "daily":
            return "RRULE:FREQ=DAILY"
        elif frequency == "weekly_monday":
            return "RRULE:FREQ=WEEKLY;BYDAY=MO"
        elif frequency == "weekly_friday":
            return "RRULE:FREQ=WEEKLY;BYDAY=FR"
        elif frequency == "biweekly":
            return "RRULE:FREQ=WEEKLY;INTERVAL=2"
        elif frequency == "monthly":
            return "RRULE:FREQ=MONTHLY;BYMONTHDAY=1"
        else:
            return "RRULE:FREQ=DAILY"

    def _get_start_date(self, frequency: str, time_str: str) -> datetime:
        """Calculate start date for event based on frequency."""
        hour, minute = map(int, time_str.split(':'))
        today = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)

        if frequency == "daily":
            # Start tomorrow
            return today + timedelta(days=1)
        elif frequency == "weekly_monday":
            return self._get_next_day(0).replace(hour=hour, minute=minute)
        elif frequency == "weekly_friday":
            return self._get_next_day(4).replace(hour=hour, minute=minute)
        elif frequency == "biweekly":
            # Start next week
            return self._get_next_day(0).replace(hour=hour, minute=minute)
        elif frequency == "monthly":
            # Start next month 1st
            next_month = today.replace(day=1) + timedelta(days=32)
            return next_month.replace(day=1, hour=hour, minute=minute)
        else:
            return today + timedelta(days=1)

    def create_reminder(self, reminder: Dict, frequency: str) -> Optional[str]:
        """
        Create a recurring calendar event.

        Args:
            reminder: Reminder configuration dict
            frequency: Recurrence frequency (daily, weekly_monday, etc.)

        Returns:
            Event ID if created, None otherwise
        """
        if not self.service:
            print("ERROR: Not authenticated")
            return None

        # Calculate start time
        start_dt = self._get_start_date(frequency, reminder['time'])
        end_dt = start_dt + timedelta(minutes=reminder['duration_minutes'])

        # Format for API
        start_str = start_dt.isoformat()
        end_str = end_dt.isoformat()

        # Build event
        event = {
            'summary': f"{self.REMINDER_TAG} {reminder['summary']}",
            'description': reminder['description'],
            'start': {
                'dateTime': start_str,
                'timeZone': 'America/New_York',
            },
            'end': {
                'dateTime': end_str,
                'timeZone': 'America/New_York',
            },
            'recurrence': [self._create_rrule(frequency)],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 10},
                    {'method': 'email', 'minutes': 30},
                ],
            },
            'colorId': reminder.get('color_id', '9'),
        }

        try:
            created = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()

            print(f"  ✓ Created: {reminder['summary']}")
            return created.get('id')

        except HttpError as e:
            print(f"  ✗ Failed to create {reminder['summary']}: {e}")
            return None

    def setup_all_reminders(self) -> Dict[str, List[str]]:
        """
        Create all routine reminders.

        Returns:
            Dict mapping frequency to list of event IDs
        """
        if not self.service:
            print("ERROR: Not authenticated")
            return {}

        print("\nSetting up routine reminders...")
        print("=" * 50)

        created_ids = {}

        for frequency, reminders in ROUTINE_REMINDERS.items():
            print(f"\n{frequency.upper()} Reminders:")
            print("-" * 30)

            created_ids[frequency] = []
            for reminder in reminders:
                event_id = self.create_reminder(reminder, frequency)
                if event_id:
                    created_ids[frequency].append(event_id)

        # Summary
        total = sum(len(ids) for ids in created_ids.values())
        print(f"\n{'=' * 50}")
        print(f"✓ Created {total} recurring reminders")

        return created_ids

    def list_routine_reminders(self) -> List[Dict]:
        """
        List all routine reminders (events with our tag).

        Returns:
            List of event dicts
        """
        if not self.service:
            print("ERROR: Not authenticated")
            return []

        try:
            # Get events with our tag
            now = datetime.utcnow().isoformat() + 'Z'
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=100,
                singleEvents=False,
                q=self.REMINDER_TAG
            ).execute()

            events = events_result.get('items', [])
            return events

        except HttpError as e:
            print(f"ERROR listing events: {e}")
            return []

    def delete_all_routine_reminders(self) -> int:
        """
        Delete all routine reminders.

        Returns:
            Number of events deleted
        """
        if not self.service:
            print("ERROR: Not authenticated")
            return 0

        events = self.list_routine_reminders()
        deleted = 0

        print(f"\nDeleting {len(events)} routine reminders...")

        for event in events:
            try:
                self.service.events().delete(
                    calendarId='primary',
                    eventId=event['id']
                ).execute()
                print(f"  ✓ Deleted: {event.get('summary', 'Unknown')}")
                deleted += 1
            except HttpError as e:
                print(f"  ✗ Failed to delete {event.get('summary', 'Unknown')}: {e}")

        print(f"\n✓ Deleted {deleted} reminders")
        return deleted


def main():
    """CLI for routine scheduler."""
    parser = argparse.ArgumentParser(description='Manage routine calendar reminders')
    parser.add_argument('command', choices=['setup', 'list', 'delete'],
                        help='Command: setup (create), list (show), delete (remove all)')
    parser.add_argument('--credentials', default='credentials.json', help='Google credentials file')
    parser.add_argument('--token', default='token.json', help='Google token file')

    args = parser.parse_args()

    scheduler = RoutineScheduler(
        credentials_path=args.credentials,
        token_path=args.token
    )

    print("Authenticating with Google Calendar...")
    if not scheduler.authenticate():
        print("\n✗ Authentication failed")
        return 1

    print("✓ Authenticated\n")

    if args.command == 'setup':
        scheduler.setup_all_reminders()

    elif args.command == 'list':
        events = scheduler.list_routine_reminders()
        print(f"Found {len(events)} routine reminders:\n")
        for event in events:
            summary = event.get('summary', 'No Title')
            recurrence = event.get('recurrence', ['No recurrence'])
            print(f"  • {summary}")
            print(f"    Recurrence: {recurrence[0] if recurrence else 'None'}")

    elif args.command == 'delete':
        confirm = input("Delete ALL routine reminders? (yes/no): ")
        if confirm.lower() == 'yes':
            scheduler.delete_all_routine_reminders()
        else:
            print("Cancelled")

    return 0


if __name__ == '__main__':
    sys.exit(main())
