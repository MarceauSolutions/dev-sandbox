#!/usr/bin/env python3
"""
fitness_calendar.py - Fitness-Integrated Calendar Management

Integrates Fitness Influencer workout generator with Google Calendar to:
- Create 6 AM daily workout events with actual generated workouts
- Add evening reading time
- Manage workout/wellness schedule
- Smart reminders for workout prep

Usage:
    python -m src.fitness_calendar setup        # Create workout + reading schedule
    python -m src.fitness_calendar list         # List current fitness events
    python -m src.fitness_calendar delete       # Remove all fitness events
    python -m src.fitness_calendar generate     # Just generate workout plan (no calendar)
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

# Add fitness influencer to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "fitness-influencer" / "src"))

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

try:
    from fitness_influencer_mcp.workout_plan_generator import WorkoutPlanGenerator
    WORKOUT_GENERATOR_AVAILABLE = True
except ImportError:
    WORKOUT_GENERATOR_AVAILABLE = False
    print("Warning: Workout generator not available")


class FitnessCalendarManager:
    """
    Manages fitness events on Google Calendar with integrated workout generation.
    """

    SCOPES = ['https://www.googleapis.com/auth/calendar']
    FITNESS_TAG = "[FITNESS]"
    READING_TAG = "[READING]"

    # Default configuration
    DEFAULT_CONFIG = {
        "workout_time": "06:00",
        "workout_duration_minutes": 60,
        "reading_time": "21:00",
        "reading_duration_minutes": 30,
        "workout_goal": "muscle_gain",
        "workout_experience": "intermediate",
        "workout_days_per_week": 5,
        "workout_equipment": "full_gym",
        "timezone": "America/New_York"
    }

    # Day mapping for workout schedule
    WORKOUT_DAYS = {
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
        5: "Saturday",
        6: "Sunday"
    }

    def __init__(self, credentials_path: str = None, token_path: str = None, config: Dict = None):
        """Initialize manager."""
        # Use root dev-sandbox credentials (has calendar scope)
        # Path: projects/personal-assistant/src/fitness_calendar.py -> dev-sandbox
        base_path = Path(__file__).parent.parent.parent.parent  # up to dev-sandbox
        self.credentials_path = credentials_path or str(base_path / "credentials.json")
        self.token_path = token_path or str(base_path / "token.json")

        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self.service = None
        self.workout_generator = WorkoutPlanGenerator() if WORKOUT_GENERATOR_AVAILABLE else None

    def authenticate(self) -> bool:
        """Authenticate with Google Calendar API."""
        if not GOOGLE_AVAILABLE:
            print("Google libraries not available")
            return False

        creds = None
        scopes = ['https://www.googleapis.com/auth/calendar']

        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    print(f"ERROR: Credentials file not found: {self.credentials_path}")
                    return False

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, scopes
                )
                creds = flow.run_local_server(port=0)

            # Save token
            token_dir = Path(self.token_path).parent
            token_dir.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        try:
            self.service = build('calendar', 'v3', credentials=creds)
            return True
        except Exception as e:
            print(f"ERROR building Calendar service: {e}")
            return False

    def generate_workout_plan(self) -> Dict:
        """Generate a weekly workout plan using Fitness Influencer."""
        if not self.workout_generator:
            print("Workout generator not available, using default plan")
            return self._default_workout_plan()

        plan = self.workout_generator.generate_plan(
            goal=self.config["workout_goal"],
            experience=self.config["workout_experience"],
            days_per_week=self.config["workout_days_per_week"],
            equipment=self.config["workout_equipment"]
        )

        print(f"\nGenerated {plan['goal']} workout plan:")
        print(f"  Experience: {plan['experience']}")
        print(f"  Days/week: {plan['days_per_week']}")
        print(f"  Equipment: {plan['equipment']}")

        return plan

    def _default_workout_plan(self) -> Dict:
        """Fallback workout plan if generator not available."""
        return {
            "goal": "General Fitness",
            "experience": "Intermediate",
            "days_per_week": 5,
            "equipment": "Full Gym",
            "weekly_schedule": [
                {"day": 1, "focus": "Push Day", "exercises": []},
                {"day": 2, "focus": "Pull Day", "exercises": []},
                {"day": 3, "focus": "Legs", "exercises": []},
                {"day": 4, "focus": "Upper Body", "exercises": []},
                {"day": 5, "focus": "Lower Body", "exercises": []},
            ],
            "notes": {
                "warm_up": "5-10 minutes light cardio + dynamic stretching",
                "progression": "Add weight progressively"
            }
        }

    def _format_workout_description(self, day_workout: Dict, notes: Dict) -> str:
        """Format workout details for calendar event description."""
        desc = []

        # Add focus
        desc.append(f"FOCUS: {day_workout['focus']}")
        desc.append("")

        # Add exercises
        if day_workout.get('exercises'):
            desc.append("EXERCISES:")
            for i, ex in enumerate(day_workout['exercises'], 1):
                desc.append(f"  {i}. {ex['exercise']}")
                desc.append(f"     {ex['sets']} sets x {ex['reps']} reps")
                desc.append(f"     Rest: {ex['rest']}")
                desc.append("")

        # Add notes
        if notes:
            desc.append("NOTES:")
            if notes.get('warm_up'):
                desc.append(f"  Warm-up: {notes['warm_up']}")
            if notes.get('progression'):
                desc.append(f"  Progression: {notes['progression']}")

        return "\n".join(desc)

    def _get_next_weekday(self, target_weekday: int, after_date: datetime = None) -> datetime:
        """Get next occurrence of a weekday (0=Monday)."""
        if after_date is None:
            after_date = datetime.now()

        days_ahead = target_weekday - after_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return after_date + timedelta(days=days_ahead)

    def create_workout_events(self, workout_plan: Dict) -> List[str]:
        """Create recurring workout events on calendar."""
        if not self.service:
            print("ERROR: Not authenticated")
            return []

        created_ids = []
        workout_time = self.config["workout_time"]
        duration = self.config["workout_duration_minutes"]

        # Map workout days to weekdays
        # For a 5-day program: Mon, Tue, Wed, Thu, Fri
        # For a 6-day program: Mon, Tue, Wed, Thu, Fri, Sat
        workout_weekdays = list(range(self.config["workout_days_per_week"]))

        print(f"\nCreating workout events at {workout_time}...")

        for i, day_workout in enumerate(workout_plan['weekly_schedule']):
            weekday = workout_weekdays[i] if i < len(workout_weekdays) else i

            # Calculate start date (next occurrence of this weekday)
            hour, minute = map(int, workout_time.split(':'))
            start_date = self._get_next_weekday(weekday)
            start_dt = start_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            end_dt = start_dt + timedelta(minutes=duration)

            # Build event
            event = {
                'summary': f"{self.FITNESS_TAG} {day_workout['focus']}",
                'description': self._format_workout_description(
                    day_workout,
                    workout_plan.get('notes', {})
                ),
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': self.config['timezone'],
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': self.config['timezone'],
                },
                'recurrence': [f"RRULE:FREQ=WEEKLY;BYDAY={self._weekday_to_rrule(weekday)}"],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 15},  # 15 min to prep
                        {'method': 'popup', 'minutes': 5},   # 5 min final alert
                    ],
                },
                'colorId': '11',  # Red for workouts
            }

            try:
                created = self.service.events().insert(
                    calendarId='primary',
                    body=event
                ).execute()

                day_name = self.WORKOUT_DAYS[weekday]
                print(f"  ✓ {day_name} {workout_time}: {day_workout['focus']}")
                created_ids.append(created.get('id'))

            except HttpError as e:
                print(f"  ✗ Failed to create {day_workout['focus']}: {e}")

        return created_ids

    def create_reading_event(self) -> Optional[str]:
        """Create recurring evening reading event."""
        if not self.service:
            print("ERROR: Not authenticated")
            return None

        reading_time = self.config["reading_time"]
        duration = self.config["reading_duration_minutes"]

        hour, minute = map(int, reading_time.split(':'))
        start_dt = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        if start_dt <= datetime.now():
            start_dt += timedelta(days=1)
        end_dt = start_dt + timedelta(minutes=duration)

        event = {
            'summary': f"{self.READING_TAG} Evening Reading",
            'description': "Daily reading time for learning and growth.\n\nSuggested:\n- Industry books\n- Technical articles\n- Personal development\n- Fiction for relaxation",
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': self.config['timezone'],
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': self.config['timezone'],
            },
            'recurrence': ["RRULE:FREQ=DAILY"],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 10},
                ],
            },
            'colorId': '9',  # Blue for reading
        }

        try:
            created = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()

            print(f"  ✓ Daily {reading_time}: Evening Reading")
            return created.get('id')

        except HttpError as e:
            print(f"  ✗ Failed to create reading event: {e}")
            return None

    def _weekday_to_rrule(self, weekday: int) -> str:
        """Convert weekday number to RRULE day code."""
        codes = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
        return codes[weekday]

    def list_fitness_events(self) -> List[Dict]:
        """List all fitness-related events."""
        if not self.service:
            print("ERROR: Not authenticated")
            return []

        events = []

        try:
            # Search for fitness events
            now = datetime.utcnow().isoformat() + 'Z'
            for tag in [self.FITNESS_TAG, self.READING_TAG]:
                results = self.service.events().list(
                    calendarId='primary',
                    timeMin=now,
                    maxResults=50,
                    singleEvents=False,
                    q=tag
                ).execute()

                events.extend(results.get('items', []))

            return events

        except HttpError as e:
            print(f"ERROR listing events: {e}")
            return []

    def delete_fitness_events(self) -> int:
        """Delete all fitness-related events."""
        if not self.service:
            print("ERROR: Not authenticated")
            return 0

        events = self.list_fitness_events()
        deleted = 0

        print(f"\nDeleting {len(events)} fitness events...")

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

        print(f"\n✓ Deleted {deleted} events")
        return deleted

    def setup_fitness_schedule(self) -> Dict:
        """
        Full setup: delete old events, generate workout, create new schedule.

        Returns:
            Dict with created event IDs and workout plan
        """
        print("\n" + "=" * 60)
        print("SETTING UP FITNESS SCHEDULE")
        print("=" * 60)

        # Step 1: Delete existing fitness events
        print("\n1. Removing existing fitness events...")
        self.delete_fitness_events()

        # Step 2: Generate workout plan
        print("\n2. Generating workout plan...")
        workout_plan = self.generate_workout_plan()

        # Step 3: Create workout events
        print("\n3. Creating workout events (6:00 AM)...")
        workout_ids = self.create_workout_events(workout_plan)

        # Step 4: Create reading event
        print("\n4. Creating reading event (9:00 PM)...")
        reading_id = self.create_reading_event()

        # Summary
        print("\n" + "=" * 60)
        print("SCHEDULE CREATED")
        print("=" * 60)
        print(f"\nWorkout events created: {len(workout_ids)}")
        print(f"Reading event created: {'Yes' if reading_id else 'No'}")

        print("\nWeekly Schedule:")
        for day in workout_plan['weekly_schedule']:
            day_num = day['day']
            # Map to weekday name
            if day_num <= len(workout_plan['weekly_schedule']):
                weekday_idx = day_num - 1
                day_name = self.WORKOUT_DAYS.get(weekday_idx, f"Day {day_num}")
            else:
                day_name = f"Day {day_num}"
            print(f"  {day_name}: {day['focus']}")

        print(f"\nReminders:")
        print(f"  Workouts: 15 min + 5 min before")
        print(f"  Reading: 10 min before")

        return {
            "workout_ids": workout_ids,
            "reading_id": reading_id,
            "workout_plan": workout_plan
        }


def main():
    """CLI for fitness calendar management."""
    parser = argparse.ArgumentParser(description='Fitness Calendar Manager')
    parser.add_argument('command', choices=['setup', 'list', 'delete', 'generate'],
                        help='Command: setup, list, delete, generate (plan only)')

    # Config options
    parser.add_argument('--workout-time', default='06:00', help='Workout time (HH:MM)')
    parser.add_argument('--reading-time', default='21:00', help='Reading time (HH:MM)')
    parser.add_argument('--goal', default='muscle_gain',
                        choices=['muscle_gain', 'strength', 'endurance'],
                        help='Workout goal')
    parser.add_argument('--experience', default='intermediate',
                        choices=['beginner', 'intermediate', 'advanced'],
                        help='Experience level')
    parser.add_argument('--days', type=int, default=5, help='Workout days per week')
    parser.add_argument('--equipment', default='full_gym',
                        choices=['full_gym', 'home_gym', 'minimal'],
                        help='Available equipment')

    args = parser.parse_args()

    # Build config from args
    config = {
        "workout_time": args.workout_time,
        "reading_time": args.reading_time,
        "workout_goal": args.goal,
        "workout_experience": args.experience,
        "workout_days_per_week": args.days,
        "workout_equipment": args.equipment,
    }

    manager = FitnessCalendarManager(config=config)

    if args.command == 'generate':
        # Just generate plan, no calendar interaction
        plan = manager.generate_workout_plan()
        print("\nWorkout Plan:")
        for day in plan['weekly_schedule']:
            print(f"\nDay {day['day']}: {day['focus']}")
            for ex in day.get('exercises', []):
                print(f"  - {ex['exercise']}: {ex['sets']}x{ex['reps']}")
        return 0

    # All other commands need authentication
    print("Authenticating with Google Calendar...")
    if not manager.authenticate():
        print("\n✗ Authentication failed")
        return 1
    print("✓ Authenticated")

    if args.command == 'setup':
        manager.setup_fitness_schedule()

    elif args.command == 'list':
        events = manager.list_fitness_events()
        if not events:
            print("\nNo fitness events found")
        else:
            print(f"\nFound {len(events)} fitness events:")
            for event in events:
                summary = event.get('summary', 'No Title')
                recurrence = event.get('recurrence', ['No recurrence'])
                print(f"  • {summary}")
                print(f"    {recurrence[0] if recurrence else 'No recurrence'}")

    elif args.command == 'delete':
        confirm = input("Delete ALL fitness events? (yes/no): ")
        if confirm.lower() == 'yes':
            manager.delete_fitness_events()
        else:
            print("Cancelled")

    return 0


if __name__ == '__main__':
    sys.exit(main())
