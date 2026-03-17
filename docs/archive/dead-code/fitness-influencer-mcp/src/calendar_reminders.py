#!/usr/bin/env python3
"""
Google Calendar Integration for Reminders
Manages calendar events and reminders.

Features:
- Create recurring reminders
- List upcoming events
- Send notifications

Usage:
    python calendar_reminders.py create --title "Instagram Post" --days "Mon,Wed,Fri" --time "09:00"
    python calendar_reminders.py list --days 7
"""

import argparse
import sys
import os
from datetime import datetime, timedelta, time
from pathlib import Path

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("ERROR: Google API libraries not installed")
    print("Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)


class CalendarReminders:
    """
    Manage Google Calendar reminders.
    """

    # Google Calendar API scopes
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    def __init__(self, calendar_id='primary', credentials_path='credentials.json', token_path='token.json'):
        """
        Initialize calendar manager.

        Args:
            calendar_id: Calendar ID (default: primary)
            credentials_path: Path to OAuth credentials
            token_path: Path to token file
        """
        self.calendar_id = calendar_id
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None

    def authenticate(self):
        """
        Authenticate with Google Calendar API.

        Returns:
            Calendar service object
        """
        creds = None

        # Load existing token
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)

        # Authenticate if needed
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    print(f"ERROR: Credentials file not found: {self.credentials_path}")
                    return None

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save token
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        self.service = build('calendar', 'v3', credentials=creds)
        return self.service

    def create_reminder(self, title, description, start_date, end_date, recurrence=None):
        """
        Create a calendar event/reminder.

        Args:
            title: Event title
            description: Event description
            start_date: Start datetime
            end_date: End datetime
            recurrence: List of RRULE strings (e.g., ['RRULE:FREQ=WEEKLY;UNTIL=20261231'])

        Returns:
            Event ID
        """
        if not self.service:
            return None

        event = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': start_date.isoformat(),
                'timeZone': 'America/New_York',  # Adjust to your timezone
            },
            'end': {
                'dateTime': end_date.isoformat(),
                'timeZone': 'America/New_York',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 60},  # 1 hour before
                    {'method': 'popup', 'minutes': 10},  # 10 minutes before
                ],
            },
        }

        if recurrence:
            event['recurrence'] = recurrence

        try:
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()

            print(f"  ✓ Created event: {created_event.get('htmlLink')}")
            return created_event.get('id')

        except HttpError as error:
            print(f"ERROR: Calendar API error: {error}")
            return None

    def create_recurring_reminder(self, title, description, days_of_week, time_of_day, duration_minutes=30, until_date=None):
        """
        Create recurring reminder on specific days.

        Args:
            title: Event title
            description: Event description
            days_of_week: List of days (e.g., ['Mon', 'Wed', 'Fri'])
            time_of_day: Time string (e.g., '09:00')
            duration_minutes: Event duration
            until_date: End date for recurrence (default: 1 year from now)

        Returns:
            Event ID
        """
        # Parse time
        try:
            hour, minute = map(int, time_of_day.split(':'))
            start_time = time(hour, minute)
        except ValueError:
            print("ERROR: Invalid time format. Use HH:MM")
            return None

        # Set start date to next occurrence of first day
        today = datetime.now().date()
        day_map = {'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6}
        day_nums = [day_map.get(d[:3], -1) for d in days_of_week]
        day_nums = [d for d in day_nums if d != -1]

        if not day_nums:
            print("ERROR: Invalid days of week")
            return None

        # Find next start date
        current_weekday = today.weekday()
        days_ahead = min((d - current_weekday) % 7 for d in day_nums)
        start_date = today + timedelta(days=days_ahead)
        start_datetime = datetime.combine(start_date, start_time)
        end_datetime = start_datetime + timedelta(minutes=duration_minutes)

        # Set until date
        if not until_date:
            until_date = (datetime.now() + timedelta(days=365)).strftime('%Y%m%d')

        # Create RRULE
        rrule_days = ','.join([['MO','TU','WE','TH','FR','SA','SU'][d] for d in day_nums])
        recurrence = [f'RRULE:FREQ=WEEKLY;UNTIL={until_date};BYDAY={rrule_days}']

        return self.create_reminder(
            title=title,
            description=description,
            start_date=start_datetime,
            end_date=end_datetime,
            recurrence=recurrence
        )

    def list_upcoming_events(self, days_ahead=7, max_results=10):
        """
        List upcoming calendar events.

        Args:
            days_ahead: Number of days to look ahead
            max_results: Maximum events to return

        Returns:
            List of events
        """
        if not self.service:
            return []

        try:
            time_min = datetime.now().isoformat() + 'Z'
            time_max = (datetime.now() + timedelta(days=days_ahead)).isoformat() + 'Z'

            print(f"→ Fetching events for next {days_ahead} days...")

            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            if not events:
                print("  No upcoming events found")
                return []

            print(f"  ✓ Found {len(events)} upcoming events")

            return events

        except HttpError as error:
            print(f"ERROR: Calendar API error: {error}")
            return []


def main():
    """CLI for calendar reminders."""
    parser = argparse.ArgumentParser(
        description='Google Calendar Reminders - Manage events and reminders'
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Create command
    create_parser = subparsers.add_parser('create', help='Create a reminder')
    create_parser.add_argument('--title', required=True, help='Reminder title')
    create_parser.add_argument('--description', help='Reminder description')
    create_parser.add_argument('--days', help='Days of week (comma-separated: Mon,Wed,Fri)')
    create_parser.add_argument('--time', help='Time of day (HH:MM)')
    create_parser.add_argument('--duration', type=int, default=30, help='Duration in minutes')

    # List command
    list_parser = subparsers.add_parser('list', help='List upcoming events')
    list_parser.add_argument('--days', type=int, default=7, help='Days ahead to list')

    args = parser.parse_args()

    # Create manager
    manager = CalendarReminders()

    # Authenticate
    print("→ Authenticating with Google Calendar...")
    service = manager.authenticate()

    if not service:
        print("\\n✗ Authentication failed")
        return 1

    print("  ✓ Authentication successful\\n")

    # Execute command
    try:
        if args.command == 'create':
            if not args.days or not args.time:
                print("ERROR: --days and --time required for recurring reminders")
                return 1

            days = [d.strip() for d in args.days.split(',')]

            event_id = manager.create_recurring_reminder(
                title=args.title,
                description=args.description or '',
                days_of_week=days,
                time_of_day=args.time,
                duration_minutes=args.duration
            )

            if event_id:
                print(f"✅ Reminder created successfully! (ID: {event_id})")
            else:
                print("✗ Failed to create reminder")

        elif args.command == 'list':
            events = manager.list_upcoming_events(days_ahead=args.days)

            if events:
                print(f"📅 UPCOMING EVENTS (Next {args.days} days):\\n")

                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    print(f"  • {event['summary']}")
                    print(f"    {start}")
                    if 'description' in event:
                        print(f"    {event['description'][:100]}...")
                    print()

        return 0

    except Exception as e:
        print(f"\\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())