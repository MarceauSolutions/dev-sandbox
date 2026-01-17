#!/usr/bin/env python3
"""
calendar_client.py - Google Calendar Integration for Elder Tech Concierge

WHAT: Read calendar events and provide schedule summaries
WHY: Help seniors keep track of appointments and daily activities
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("WARNING: Google API libraries not installed")
    print("Install with: pip install google-auth google-auth-oauthlib google-api-python-client")
    Request = None
    Credentials = None
    InstalledAppFlow = None
    HttpError = Exception

from config import config


class CalendarClient:
    """
    Google Calendar client for viewing schedules.

    Features:
    - Fetch today's events
    - Fetch upcoming events
    - Senior-friendly time formatting
    - Spoken schedule summaries
    """

    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

    def __init__(
        self,
        credentials_path: str = None,
        token_path: str = None,
        calendar_id: str = 'primary'
    ):
        """
        Initialize Calendar client.

        Args:
            credentials_path: Path to OAuth credentials (defaults to config)
            token_path: Path to token file (defaults to config)
            calendar_id: Calendar to use (default: primary)
        """
        self.credentials_path = credentials_path or config.google_credentials_path
        self.token_path = token_path or config.google_token_path
        self.calendar_id = calendar_id
        self.service = None

    def is_available(self) -> bool:
        """Check if Calendar API is available."""
        return Credentials is not None and os.path.exists(self.credentials_path)

    def authenticate(self) -> bool:
        """
        Authenticate with Google Calendar API.

        Returns:
            True if authentication successful
        """
        if not self.is_available():
            return False

        creds = None

        # Load existing token
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
            except Exception:
                pass

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = None

            if not creds:
                if not os.path.exists(self.credentials_path):
                    return False

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                except Exception:
                    return False

            # Save token
            try:
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
            except Exception:
                pass

        try:
            self.service = build('calendar', 'v3', credentials=creds)
            return True
        except Exception:
            return False

    def get_todays_events(self) -> Dict[str, Any]:
        """
        Get all events for today.

        Returns:
            Dict with events list and spoken summary
        """
        now = datetime.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        return self._get_events(start_of_day, end_of_day, "today")

    def get_upcoming_events(self, days: int = 7, max_results: int = 10) -> Dict[str, Any]:
        """
        Get upcoming events.

        Args:
            days: Number of days to look ahead
            max_results: Maximum events to return

        Returns:
            Dict with events list and spoken summary
        """
        now = datetime.now()
        end_date = now + timedelta(days=days)

        return self._get_events(now, end_date, f"the next {days} days", max_results)

    def _get_events(
        self,
        start: datetime,
        end: datetime,
        period_description: str,
        max_results: int = 50
    ) -> Dict[str, Any]:
        """
        Fetch events for a time period.

        Args:
            start: Start datetime
            end: End datetime
            period_description: Description for spoken response
            max_results: Maximum events to fetch

        Returns:
            Dict with events and spoken summary
        """
        if not self.service:
            if not self.authenticate():
                return {
                    'success': False,
                    'events': [],
                    'error': 'Calendar not connected',
                    'spoken_response': "I can't access your calendar right now. The calendar service isn't set up yet."
                }

        try:
            # Fetch events
            time_min = start.isoformat() + 'Z' if start.tzinfo is None else start.isoformat()
            time_max = end.isoformat() + 'Z' if end.tzinfo is None else end.isoformat()

            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            raw_events = events_result.get('items', [])

            # Parse events
            events = []
            for event in raw_events:
                parsed = self._parse_event(event)
                if parsed:
                    events.append(parsed)

            return {
                'success': True,
                'events': events,
                'count': len(events),
                'period': period_description,
                'spoken_response': self._format_events_spoken(events, period_description)
            }

        except HttpError as error:
            return {
                'success': False,
                'events': [],
                'error': str(error),
                'spoken_response': "I had trouble checking your calendar. Let's try again in a moment."
            }
        except Exception as e:
            return {
                'success': False,
                'events': [],
                'error': str(e),
                'spoken_response': "Something went wrong checking your calendar. Would you like to try again?"
            }

    def _parse_event(self, event: Dict) -> Optional[Dict]:
        """
        Parse a calendar event into senior-friendly format.

        Args:
            event: Raw Google Calendar event

        Returns:
            Parsed event dict
        """
        try:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))

            # Parse datetime
            if 'T' in start:
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                is_all_day = False
            else:
                start_dt = datetime.strptime(start, '%Y-%m-%d')
                is_all_day = True

            if 'T' in end:
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
            else:
                end_dt = datetime.strptime(end, '%Y-%m-%d')

            return {
                'id': event['id'],
                'summary': event.get('summary', 'Untitled Event'),
                'location': event.get('location', ''),
                'description': event.get('description', ''),
                'start': start,
                'end': end,
                'start_datetime': start_dt,
                'end_datetime': end_dt,
                'is_all_day': is_all_day,
                'time_formatted': self._format_time_spoken(start_dt, is_all_day)
            }

        except Exception:
            return None

    def _format_time_spoken(self, dt: datetime, is_all_day: bool) -> str:
        """Format time for voice output."""
        if is_all_day:
            return "all day"

        hour = dt.hour
        minute = dt.minute

        # Convert to 12-hour format
        if hour == 0:
            hour_str = "12"
            period = "in the morning"
        elif hour < 12:
            hour_str = str(hour)
            period = "in the morning"
        elif hour == 12:
            hour_str = "12"
            period = "in the afternoon"
        else:
            hour_str = str(hour - 12)
            period = "in the afternoon" if hour < 17 else "in the evening"

        if minute == 0:
            return f"{hour_str} o'clock {period}"
        elif minute == 30:
            return f"half past {hour_str} {period}"
        elif minute == 15:
            return f"quarter past {hour_str} {period}"
        elif minute == 45:
            next_hour = int(hour_str) + 1
            if next_hour > 12:
                next_hour = 1
            return f"quarter to {next_hour} {period}"
        else:
            return f"{hour_str}:{minute:02d} {period}"

    def _format_events_spoken(self, events: List[Dict], period: str) -> str:
        """Format events list for voice output."""
        if not events:
            return f"You have no appointments scheduled for {period}. It's a free day!"

        count = len(events)

        if period == "today":
            intro = f"You have {count} thing{'s' if count > 1 else ''} on your calendar today."
        else:
            intro = f"You have {count} upcoming appointment{'s' if count > 1 else ''} for {period}."

        parts = [intro]

        # List first 3 events
        for i, event in enumerate(events[:3], 1):
            time_str = event['time_formatted']
            summary = event['summary']

            if event['is_all_day']:
                parts.append(f"{summary}, all day.")
            else:
                parts.append(f"At {time_str}: {summary}.")

            # Add location if available
            if event['location']:
                parts.append(f"That's at {event['location']}.")

        if count > 3:
            parts.append(f"And {count - 3} more later.")

        return ' '.join(parts)

    def get_next_event(self) -> Dict[str, Any]:
        """
        Get the next upcoming event.

        Returns:
            Dict with next event info
        """
        result = self.get_upcoming_events(days=7, max_results=1)

        if not result['success']:
            return result

        if not result['events']:
            return {
                'success': True,
                'event': None,
                'spoken_response': "You don't have any upcoming appointments scheduled."
            }

        event = result['events'][0]
        time_str = event['time_formatted']
        summary = event['summary']

        # Calculate how soon
        now = datetime.now()
        if hasattr(event['start_datetime'], 'date'):
            event_date = event['start_datetime'].date() if hasattr(event['start_datetime'], 'date') else event['start_datetime']
            today = now.date()

            if event_date == today:
                when = "today"
            elif event_date == today + timedelta(days=1):
                when = "tomorrow"
            else:
                day_name = event['start_datetime'].strftime('%A')
                when = f"on {day_name}"
        else:
            when = "soon"

        spoken = f"Your next appointment is {summary}, {when} at {time_str}."
        if event['location']:
            spoken += f" It's at {event['location']}."

        return {
            'success': True,
            'event': event,
            'spoken_response': spoken
        }


# CLI testing
if __name__ == "__main__":
    client = CalendarClient()

    print("\n" + "=" * 60)
    print("ELDER TECH CONCIERGE - Calendar Client Test")
    print("=" * 60 + "\n")

    if not client.is_available():
        print("Calendar API not available. Check credentials.json")
        sys.exit(1)

    print("Authenticating with Google Calendar...")
    if not client.authenticate():
        print("Authentication failed.")
        sys.exit(1)

    print("Connected to Google Calendar!\n")

    # Test today's events
    print("Checking today's schedule...")
    result = client.get_todays_events()

    if result['success']:
        print(f"\nFound {result['count']} events today")
        print(f"\nSpoken response:")
        print(f"  {result['spoken_response']}")
    else:
        print(f"\nError: {result.get('error')}")

    # Test next event
    print("\n" + "-" * 40)
    print("\nChecking next event...")
    result = client.get_next_event()

    if result['success']:
        print(f"\nSpoken response:")
        print(f"  {result['spoken_response']}")
