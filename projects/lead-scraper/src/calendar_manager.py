"""
Google Calendar Manager for Fitness Influencer Weekly Routine

Manages calendar events using the Google Calendar API.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


class CalendarManager:
    """Manage Google Calendar events for fitness influencer routine."""

    SCOPES = ['https://www.googleapis.com/auth/calendar']

    def __init__(self, token_path: str):
        """Initialize with Google OAuth token."""
        self.token_path = Path(token_path)
        self.creds = self._load_credentials()
        self.service = build('calendar', 'v3', credentials=self.creds)

    def _load_credentials(self) -> Credentials:
        """Load and refresh credentials from token file."""
        if not self.token_path.exists():
            raise FileNotFoundError(f"Token file not found: {self.token_path}")

        with open(self.token_path) as f:
            token_data = json.load(f)

        creds = Credentials(
            token=token_data.get('token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data.get('token_uri'),
            client_id=token_data.get('client_id'),
            client_secret=token_data.get('client_secret'),
            scopes=token_data.get('scopes', self.SCOPES)
        )

        # Refresh if expired
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed token
            token_data['token'] = creds.token
            token_data['expiry'] = creds.expiry.isoformat() if creds.expiry else None
            with open(self.token_path, 'w') as f:
                json.dump(token_data, f, indent=2)

        return creds

    def get_events(self, days_ahead: int = 7, calendar_id: str = 'primary') -> list:
        """Get events for the next N days."""
        now = datetime.utcnow()
        time_min = now.isoformat() + 'Z'
        time_max = (now + timedelta(days=days_ahead)).isoformat() + 'Z'

        events_result = self.service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=250,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        return events_result.get('items', [])

    def delete_event(self, event_id: str, calendar_id: str = 'primary') -> bool:
        """Delete an event by ID."""
        try:
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            return True
        except Exception as e:
            print(f"Error deleting event {event_id}: {e}")
            return False

    def delete_events_by_title(self, title_contains: str, days_ahead: int = 7, calendar_id: str = 'primary') -> list:
        """Delete all events containing the specified text in the title."""
        events = self.get_events(days_ahead=days_ahead, calendar_id=calendar_id)
        deleted = []

        for event in events:
            summary = event.get('summary', '')
            if title_contains.lower() in summary.lower():
                if self.delete_event(event['id'], calendar_id):
                    deleted.append(summary)

        return deleted

    def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: str = '',
        calendar_id: str = 'primary',
        color_id: Optional[str] = None,
        recurrence: Optional[list] = None
    ) -> dict:
        """Create a calendar event."""
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'America/New_York',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'America/New_York',
            },
        }

        if color_id:
            event['colorId'] = color_id

        if recurrence:
            event['recurrence'] = recurrence

        return self.service.events().insert(
            calendarId=calendar_id,
            body=event
        ).execute()

    def event_exists(self, summary: str, start_date: datetime, calendar_id: str = 'primary') -> bool:
        """Check if an event with the same summary already exists on the given date."""
        # Get events for that specific day
        time_min = start_date.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
        time_max = start_date.replace(hour=23, minute=59, second=59).isoformat() + 'Z'

        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=100,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        for event in events:
            if event.get('summary', '').lower() == summary.lower():
                return True
        return False


def get_next_weekday(target_weekday: int, from_date: Optional[datetime] = None) -> datetime:
    """Get the next occurrence of a weekday (0=Monday, 6=Sunday)."""
    if from_date is None:
        from_date = datetime.now()

    days_ahead = target_weekday - from_date.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return from_date + timedelta(days=days_ahead)


def create_fitness_influencer_schedule(manager: CalendarManager) -> list:
    """
    Create the fitness influencer weekly routine schedule.

    Schedule (Monday-Saturday, Sundays free):
    - Morning SMS Outreach: 9-11 AM (Tue-Fri)
    - Content Creation: Various blocks
    - Email Checking: Morning and afternoon
    - Fitness/Workout: Daily
    - Planning and Strategy sessions
    """

    created_events = []

    # Get dates for next week (Monday through Saturday)
    today = datetime.now()

    # Find next Monday
    days_until_monday = (0 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7  # Start from next Monday if today is Monday
    next_monday = today + timedelta(days=days_until_monday)
    next_monday = next_monday.replace(hour=0, minute=0, second=0, microsecond=0)

    # Event color IDs (Google Calendar colors):
    # 1=Lavender, 2=Sage, 3=Grape, 4=Flamingo, 5=Banana, 6=Tangerine, 7=Peacock, 8=Graphite, 9=Blueberry, 10=Basil, 11=Tomato
    COLOR_OUTREACH = '6'      # Tangerine - Outreach
    COLOR_CONTENT = '9'       # Blueberry - Content Creation
    COLOR_EMAIL = '8'         # Graphite - Email
    COLOR_FITNESS = '11'      # Tomato - Fitness
    COLOR_PLANNING = '7'      # Peacock - Planning
    COLOR_ANALYTICS = '5'     # Banana - Analytics

    # Weekly Schedule Template
    weekly_schedule = {
        # Monday - Planning & Content Day
        0: [
            {'summary': 'Weekly Planning & Strategy', 'start_hour': 8, 'start_min': 0, 'duration': 60, 'color': COLOR_PLANNING, 'desc': 'Review weekly goals, plan content calendar, set priorities'},
            {'summary': 'Email Check & Response', 'start_hour': 9, 'start_min': 0, 'duration': 30, 'color': COLOR_EMAIL, 'desc': 'Process inbox, respond to urgent emails'},
            {'summary': 'Content Creation - Video Editing', 'start_hour': 10, 'start_min': 0, 'duration': 120, 'color': COLOR_CONTENT, 'desc': 'Edit workout videos, create jump cuts, add branding'},
            {'summary': 'Lunch Break', 'start_hour': 12, 'start_min': 0, 'duration': 60, 'color': '8', 'desc': ''},
            {'summary': 'Fitness Workout', 'start_hour': 13, 'start_min': 0, 'duration': 90, 'color': COLOR_FITNESS, 'desc': 'Training session - upper body focus'},
            {'summary': 'Content Creation - Social Posts', 'start_hour': 15, 'start_min': 0, 'duration': 90, 'color': COLOR_CONTENT, 'desc': 'Create posts for TikTok and Instagram'},
            {'summary': 'Email Check (Afternoon)', 'start_hour': 17, 'start_min': 0, 'duration': 30, 'color': COLOR_EMAIL, 'desc': 'End-of-day inbox review'},
        ],
        # Tuesday - Outreach & Content Day
        1: [
            {'summary': 'Email Check & Response', 'start_hour': 8, 'start_min': 0, 'duration': 30, 'color': COLOR_EMAIL, 'desc': 'Morning inbox review'},
            {'summary': 'SMS Outreach Block', 'start_hour': 9, 'start_min': 0, 'duration': 120, 'color': COLOR_OUTREACH, 'desc': 'Lead outreach - Rule of 100 (50 contacts)'},
            {'summary': 'Content Creation - Workout Plans', 'start_hour': 11, 'start_min': 30, 'duration': 60, 'color': COLOR_CONTENT, 'desc': 'Create workout plans for followers'},
            {'summary': 'Lunch Break', 'start_hour': 12, 'start_min': 30, 'duration': 60, 'color': '8', 'desc': ''},
            {'summary': 'Fitness Workout', 'start_hour': 13, 'start_min': 30, 'duration': 90, 'color': COLOR_FITNESS, 'desc': 'Training session - lower body focus'},
            {'summary': 'Content Creation - AI Images', 'start_hour': 15, 'start_min': 30, 'duration': 90, 'color': COLOR_CONTENT, 'desc': 'Generate AI fitness images, create graphics'},
            {'summary': 'Email Check (Afternoon)', 'start_hour': 17, 'start_min': 30, 'duration': 30, 'color': COLOR_EMAIL, 'desc': 'End-of-day inbox review'},
        ],
        # Wednesday - Outreach & Analytics Day
        2: [
            {'summary': 'Email Check & Response', 'start_hour': 8, 'start_min': 0, 'duration': 30, 'color': COLOR_EMAIL, 'desc': 'Morning inbox review'},
            {'summary': 'SMS Outreach Block', 'start_hour': 9, 'start_min': 0, 'duration': 120, 'color': COLOR_OUTREACH, 'desc': 'Lead outreach - Rule of 100 (50 contacts)'},
            {'summary': 'Revenue Analytics Review', 'start_hour': 11, 'start_min': 30, 'duration': 60, 'color': COLOR_ANALYTICS, 'desc': 'Review revenue reports, track COGS, analyze performance'},
            {'summary': 'Lunch Break', 'start_hour': 12, 'start_min': 30, 'duration': 60, 'color': '8', 'desc': ''},
            {'summary': 'Fitness Workout', 'start_hour': 13, 'start_min': 30, 'duration': 90, 'color': COLOR_FITNESS, 'desc': 'Training session - push day'},
            {'summary': 'Content Creation - Video Filming', 'start_hour': 15, 'start_min': 30, 'duration': 120, 'color': COLOR_CONTENT, 'desc': 'Film new workout content'},
            {'summary': 'Email Check (Afternoon)', 'start_hour': 17, 'start_min': 30, 'duration': 30, 'color': COLOR_EMAIL, 'desc': 'End-of-day inbox review'},
        ],
        # Thursday - Outreach & Content Day
        3: [
            {'summary': 'Email Check & Response', 'start_hour': 8, 'start_min': 0, 'duration': 30, 'color': COLOR_EMAIL, 'desc': 'Morning inbox review'},
            {'summary': 'SMS Outreach Block', 'start_hour': 9, 'start_min': 0, 'duration': 120, 'color': COLOR_OUTREACH, 'desc': 'Lead outreach - Rule of 100 (50 contacts)'},
            {'summary': 'Content Creation - Blog/Newsletter', 'start_hour': 11, 'start_min': 30, 'duration': 60, 'color': COLOR_CONTENT, 'desc': 'Write newsletter content, blog posts'},
            {'summary': 'Lunch Break', 'start_hour': 12, 'start_min': 30, 'duration': 60, 'color': '8', 'desc': ''},
            {'summary': 'Fitness Workout', 'start_hour': 13, 'start_min': 30, 'duration': 90, 'color': COLOR_FITNESS, 'desc': 'Training session - pull day'},
            {'summary': 'Content Creation - Video Editing', 'start_hour': 15, 'start_min': 30, 'duration': 90, 'color': COLOR_CONTENT, 'desc': 'Edit filmed content from Wednesday'},
            {'summary': 'Email Check (Afternoon)', 'start_hour': 17, 'start_min': 30, 'duration': 30, 'color': COLOR_EMAIL, 'desc': 'End-of-day inbox review'},
        ],
        # Friday - Outreach & Wrap-up Day
        4: [
            {'summary': 'Email Check & Response', 'start_hour': 8, 'start_min': 0, 'duration': 30, 'color': COLOR_EMAIL, 'desc': 'Morning inbox review'},
            {'summary': 'SMS Outreach Block', 'start_hour': 9, 'start_min': 0, 'duration': 120, 'color': COLOR_OUTREACH, 'desc': 'Lead outreach - Rule of 100 (50 contacts)'},
            {'summary': 'Content Scheduling & Planning', 'start_hour': 11, 'start_min': 30, 'duration': 60, 'color': COLOR_PLANNING, 'desc': 'Schedule posts for next week'},
            {'summary': 'Lunch Break', 'start_hour': 12, 'start_min': 30, 'duration': 60, 'color': '8', 'desc': ''},
            {'summary': 'Fitness Workout', 'start_hour': 13, 'start_min': 30, 'duration': 90, 'color': COLOR_FITNESS, 'desc': 'Training session - leg day'},
            {'summary': 'Weekly Review & Metrics', 'start_hour': 15, 'start_min': 30, 'duration': 60, 'color': COLOR_ANALYTICS, 'desc': 'Review week performance, update metrics'},
            {'summary': 'Email Check (Afternoon)', 'start_hour': 16, 'start_min': 30, 'duration': 30, 'color': COLOR_EMAIL, 'desc': 'End-of-week inbox cleanup'},
        ],
        # Saturday - Light Content Day
        5: [
            {'summary': 'Email Check (Quick)', 'start_hour': 9, 'start_min': 0, 'duration': 30, 'color': COLOR_EMAIL, 'desc': 'Quick inbox scan - urgent only'},
            {'summary': 'Fitness Workout', 'start_hour': 10, 'start_min': 0, 'duration': 90, 'color': COLOR_FITNESS, 'desc': 'Training session - cardio/active recovery'},
            {'summary': 'Content Batch - Light Work', 'start_hour': 12, 'start_min': 0, 'duration': 120, 'color': COLOR_CONTENT, 'desc': 'Optional: batch create stories, quick content'},
        ],
        # Sunday - REST DAY (No events)
        6: []
    }

    # Create events for the week
    for day_offset in range(7):
        current_date = next_monday + timedelta(days=day_offset)
        weekday = current_date.weekday()

        day_events = weekly_schedule.get(weekday, [])

        for event_info in day_events:
            start_time = current_date.replace(
                hour=event_info['start_hour'],
                minute=event_info['start_min'],
                second=0,
                microsecond=0
            )
            end_time = start_time + timedelta(minutes=event_info['duration'])

            # Check if event already exists
            if manager.event_exists(event_info['summary'], start_time):
                print(f"  Skipping (exists): {event_info['summary']} on {current_date.strftime('%A, %b %d')}")
                continue

            try:
                event = manager.create_event(
                    summary=event_info['summary'],
                    start_time=start_time,
                    end_time=end_time,
                    description=event_info.get('desc', ''),
                    color_id=event_info.get('color')
                )
                created_events.append({
                    'summary': event_info['summary'],
                    'date': current_date.strftime('%A, %b %d'),
                    'time': f"{start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}",
                    'id': event.get('id')
                })
                print(f"  Created: {event_info['summary']} on {current_date.strftime('%A, %b %d')} at {start_time.strftime('%I:%M %p')}")
            except Exception as e:
                print(f"  Error creating {event_info['summary']}: {e}")

    return created_events


def main():
    """Main function to run calendar management."""
    token_path = "/Users/williammarceaujr./dev-sandbox/projects/lead-scraper/output/google_token.json"

    print("=" * 60)
    print("FITNESS INFLUENCER CALENDAR MANAGER")
    print("=" * 60)

    # Initialize manager
    print("\n[1] Initializing Google Calendar connection...")
    manager = CalendarManager(token_path)
    print("    Connected successfully!")

    # Get existing events
    print("\n[2] Retrieving existing events for next 7 days...")
    events = manager.get_events(days_ahead=7)
    print(f"    Found {len(events)} existing events:")
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(f"      - {event.get('summary', 'No title')} ({start})")

    # Delete Instagram events
    print("\n[3] Deleting events with 'Instagram' in title...")
    deleted = manager.delete_events_by_title('Instagram', days_ahead=7)
    if deleted:
        print(f"    Deleted {len(deleted)} events:")
        for title in deleted:
            print(f"      - {title}")
    else:
        print("    No Instagram events found to delete.")

    # Create fitness influencer schedule
    print("\n[4] Creating fitness influencer weekly routine...")
    print("    Schedule: Monday-Saturday (Sundays free)")
    print("    - SMS Outreach: 9-11 AM (Tue-Fri)")
    print("    - Content Creation blocks")
    print("    - Email checking (morning & afternoon)")
    print("    - Fitness/Workout daily")
    print()

    created = create_fitness_influencer_schedule(manager)

    # Summary
    print("\n" + "=" * 60)
    print("CALENDAR UPDATE COMPLETE")
    print("=" * 60)
    print(f"\nCreated {len(created)} new events:")

    # Group by day for summary
    events_by_day = {}
    for event in created:
        day = event['date']
        if day not in events_by_day:
            events_by_day[day] = []
        events_by_day[day].append(event)

    for day, day_events in events_by_day.items():
        print(f"\n{day}:")
        for event in day_events:
            print(f"  {event['time']} - {event['summary']}")

    # Sunday note
    print("\nSunday: REST DAY (No scheduled events)")

    return created


if __name__ == "__main__":
    main()
