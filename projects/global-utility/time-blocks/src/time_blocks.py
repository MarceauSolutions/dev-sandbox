#!/usr/bin/env python3
"""
Time Blocks - Personal productivity tool for scheduling focused work periods.

Creates time blocks in your calendar so you know exactly what you're doing
at any given time. Time between blocks is "free time" for whatever.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Google Calendar imports
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False


# ============================================================================
# Configuration
# ============================================================================

SCOPES = ['https://www.googleapis.com/auth/calendar']
TOKEN_PATH = Path.home() / '.time-blocks' / 'token.json'
CREDENTIALS_PATH = Path.home() / '.time-blocks' / 'credentials.json'
DATA_PATH = Path.home() / '.time-blocks' / 'blocks.json'
USER_PREFS_PATH = Path(__file__).parent.parent / 'config' / 'user_preferences.json'

# Default working hours (can be overridden by user_preferences.json)
DEFAULT_WORKING_HOURS = {
    "start": "06:00",
    "end": "21:00"
}


def load_user_preferences() -> Dict[str, Any]:
    """Load user preferences from config file."""
    if USER_PREFS_PATH.exists():
        with open(USER_PREFS_PATH, 'r') as f:
            return json.load(f)
    return {}


def get_working_hours() -> Dict[str, str]:
    """Get working hours from user preferences or defaults."""
    prefs = load_user_preferences()
    return prefs.get('working_hours', DEFAULT_WORKING_HOURS)


def validate_block_within_working_hours(block: 'TimeBlock') -> tuple[bool, str]:
    """Validate that a block falls within working hours.

    Returns:
        tuple: (is_valid, error_message)
    """
    working_hours = get_working_hours()
    start_limit = datetime.strptime(working_hours['start'], '%H:%M')
    end_limit = datetime.strptime(working_hours['end'], '%H:%M')

    block_start = datetime.strptime(block.start, '%H:%M')
    block_end = datetime.strptime(block.end, '%H:%M')

    if block_start < start_limit:
        return False, f"Block starts at {block.start}, before working hours start ({working_hours['start']})"

    if block_end > end_limit:
        return False, f"Block ends at {block.end}, after working hours end ({working_hours['end']})"

    return True, ""

# Category colors for Google Calendar (color IDs)
# https://developers.google.com/calendar/api/v3/reference/colors/get
CATEGORY_COLORS = {
    'work': '9',        # Blue
    'exercise': '11',   # Red
    'personal': '5',    # Yellow
    'rest': '2',        # Green
    'admin': '7',       # Cyan
    'meal': '6',        # Orange
    'learning': '3',    # Purple
    'social': '10',     # Dark green
}


# ============================================================================
# Data Classes
# ============================================================================

class Category(str, Enum):
    WORK = 'work'
    EXERCISE = 'exercise'
    PERSONAL = 'personal'
    REST = 'rest'
    ADMIN = 'admin'
    MEAL = 'meal'
    LEARNING = 'learning'
    SOCIAL = 'social'


class Priority(str, Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


@dataclass
class TimeBlock:
    """A single time block representing a focused activity period."""
    start: str          # HH:MM format
    end: str            # HH:MM format
    activity: str
    category: str
    priority: str = 'medium'
    notes: str = ''
    recurring: bool = False
    days: List[str] = None  # ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

    def __post_init__(self):
        if self.days is None:
            self.days = []

    @property
    def duration_minutes(self) -> int:
        """Calculate duration in minutes."""
        start_dt = datetime.strptime(self.start, '%H:%M')
        end_dt = datetime.strptime(self.end, '%H:%M')
        diff = end_dt - start_dt
        return int(diff.total_seconds() / 60)

    @classmethod
    def from_duration(cls, start: str, duration: int, activity: str,
                      category: str, **kwargs) -> 'TimeBlock':
        """Create a block from start time and duration (minutes)."""
        start_dt = datetime.strptime(start, '%H:%M')
        end_dt = start_dt + timedelta(minutes=duration)
        return cls(
            start=start,
            end=end_dt.strftime('%H:%M'),
            activity=activity,
            category=category,
            **kwargs
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimeBlock':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class DaySchedule:
    """A collection of time blocks for a specific date."""
    date: str  # YYYY-MM-DD format
    blocks: List[TimeBlock]

    def add_block(self, block: TimeBlock) -> None:
        """Add a block and sort by start time."""
        self.blocks.append(block)
        self.blocks.sort(key=lambda b: b.start)

    def remove_block(self, index: int) -> None:
        """Remove a block by index."""
        if 0 <= index < len(self.blocks):
            self.blocks.pop(index)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'date': self.date,
            'blocks': [b.to_dict() for b in self.blocks]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DaySchedule':
        """Create from dictionary."""
        return cls(
            date=data['date'],
            blocks=[TimeBlock.from_dict(b) for b in data['blocks']]
        )


# ============================================================================
# Storage
# ============================================================================

class BlockStorage:
    """Handles persistence of time blocks."""

    def __init__(self, path: Path = DATA_PATH):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, DaySchedule] = {}
        self._load()

    def _load(self) -> None:
        """Load blocks from disk."""
        if self.path.exists():
            with open(self.path, 'r') as f:
                raw = json.load(f)
                self._data = {
                    k: DaySchedule.from_dict(v)
                    for k, v in raw.items()
                }

    def _save(self) -> None:
        """Save blocks to disk."""
        with open(self.path, 'w') as f:
            json.dump(
                {k: v.to_dict() for k, v in self._data.items()},
                f,
                indent=2
            )

    def get_schedule(self, date_str: str) -> DaySchedule:
        """Get schedule for a date, creating if needed."""
        if date_str not in self._data:
            self._data[date_str] = DaySchedule(date=date_str, blocks=[])
        return self._data[date_str]

    def add_block(self, date_str: str, block: TimeBlock) -> None:
        """Add a block to a date."""
        schedule = self.get_schedule(date_str)
        schedule.add_block(block)
        self._save()

    def remove_block(self, date_str: str, index: int) -> bool:
        """Remove a block by index."""
        if date_str in self._data:
            schedule = self._data[date_str]
            if 0 <= index < len(schedule.blocks):
                schedule.remove_block(index)
                self._save()
                return True
        return False

    def clear_date(self, date_str: str) -> None:
        """Clear all blocks for a date."""
        if date_str in self._data:
            del self._data[date_str]
            self._save()


# ============================================================================
# Google Calendar Integration
# ============================================================================

class GoogleCalendarSync:
    """Handles syncing time blocks to Google Calendar."""

    def __init__(self):
        self.service = None
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Ensure config directories exist."""
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)

    def authenticate(self) -> bool:
        """Authenticate with Google Calendar API."""
        if not GOOGLE_AVAILABLE:
            print("Error: Google Calendar libraries not installed.")
            print("Run: pip install google-auth-oauthlib google-api-python-client")
            return False

        creds = None

        # Load existing token
        if TOKEN_PATH.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not CREDENTIALS_PATH.exists():
                    print(f"Error: No credentials file found at {CREDENTIALS_PATH}")
                    print("\nTo set up Google Calendar integration:")
                    print("1. Go to https://console.cloud.google.com/")
                    print("2. Create a project and enable Google Calendar API")
                    print("3. Create OAuth 2.0 credentials (Desktop app)")
                    print(f"4. Download and save as {CREDENTIALS_PATH}")
                    return False

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(CREDENTIALS_PATH), SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save token
            with open(TOKEN_PATH, 'w') as f:
                f.write(creds.to_json())

        self.service = build('calendar', 'v3', credentials=creds)
        return True

    def list_calendars(self) -> List[Dict[str, str]]:
        """List available calendars."""
        if not self.service:
            return []

        result = self.service.calendarList().list().execute()
        return [
            {'id': cal['id'], 'name': cal['summary']}
            for cal in result.get('items', [])
        ]

    def find_or_create_calendar(self, name: str) -> Optional[str]:
        """Find a calendar by name, or create it."""
        if not self.service:
            return None

        # Search existing
        calendars = self.list_calendars()
        for cal in calendars:
            if cal['name'].lower() == name.lower():
                return cal['id']

        # Create new
        calendar = {
            'summary': name,
            'description': 'Time blocks for focused work periods',
            'timeZone': 'America/New_York'  # TODO: Make configurable
        }
        created = self.service.calendars().insert(body=calendar).execute()
        return created['id']

    def create_event(self, calendar_id: str, block: TimeBlock,
                     date_str: str) -> Optional[str]:
        """Create a calendar event from a time block."""
        if not self.service:
            return None

        # Parse date and times
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(block.start, '%H:%M').time()
        end_time = datetime.strptime(block.end, '%H:%M').time()

        start_dt = datetime.combine(date_obj, start_time)
        end_dt = datetime.combine(date_obj, end_time)

        # Build event
        event = {
            'summary': block.activity,
            'description': f"Category: {block.category}\nPriority: {block.priority}\n\n{block.notes}",
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'America/New_York',
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'America/New_York',
            },
            'colorId': CATEGORY_COLORS.get(block.category, '1'),
        }

        # Handle recurring events
        if block.recurring and block.days:
            days_map = {
                'mon': 'MO', 'tue': 'TU', 'wed': 'WE',
                'thu': 'TH', 'fri': 'FR', 'sat': 'SA', 'sun': 'SU'
            }
            rrule_days = ','.join(days_map[d] for d in block.days if d in days_map)
            if rrule_days:
                event['recurrence'] = [f'RRULE:FREQ=WEEKLY;BYDAY={rrule_days}']

        result = self.service.events().insert(
            calendarId=calendar_id, body=event
        ).execute()
        return result.get('id')

    def get_existing_events(self, calendar_id: str, date_str: str) -> List[Dict]:
        """Get existing events for a date."""
        if not self.service:
            return []

        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        start = datetime.combine(date_obj, datetime.min.time()).isoformat() + 'Z'
        end = datetime.combine(date_obj, datetime.max.time()).isoformat() + 'Z'

        result = self.service.events().list(
            calendarId=calendar_id,
            timeMin=start,
            timeMax=end,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        return result.get('items', [])

    def sync_schedule(self, schedule: DaySchedule, calendar_name: str,
                      skip_existing: bool = True) -> Dict[str, Any]:
        """Sync a day's schedule to Google Calendar."""
        if not self.authenticate():
            return {'success': False, 'error': 'Authentication failed'}

        calendar_id = self.find_or_create_calendar(calendar_name)
        if not calendar_id:
            return {'success': False, 'error': 'Could not find/create calendar'}

        results = {
            'success': True,
            'created': [],
            'skipped': [],
            'errors': []
        }

        # Get existing events to avoid duplicates
        existing = []
        if skip_existing:
            existing = self.get_existing_events(calendar_id, schedule.date)
            existing_titles = {e['summary'].lower() for e in existing}

        for block in schedule.blocks:
            # Skip if already exists
            if skip_existing and block.activity.lower() in existing_titles:
                results['skipped'].append(block.activity)
                continue

            try:
                event_id = self.create_event(calendar_id, block, schedule.date)
                if event_id:
                    results['created'].append(block.activity)
                else:
                    results['errors'].append(f"Failed to create: {block.activity}")
            except Exception as e:
                results['errors'].append(f"{block.activity}: {str(e)}")

        return results


# ============================================================================
# Template System
# ============================================================================

class TemplateManager:
    """Manages reusable schedule templates."""

    def __init__(self, templates_dir: Optional[Path] = None):
        if templates_dir is None:
            # Default to templates folder in project
            self.templates_dir = Path(__file__).parent.parent / 'templates'
        else:
            self.templates_dir = templates_dir
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def list_templates(self) -> List[str]:
        """List available templates."""
        return [f.stem for f in self.templates_dir.glob('*.json')]

    def load_template(self, name: str) -> Optional[Dict[str, Any]]:
        """Load a template by name."""
        path = self.templates_dir / f"{name}.json"
        if not path.exists():
            return None

        with open(path, 'r') as f:
            return json.load(f)

    def save_template(self, name: str, data: Dict[str, Any]) -> None:
        """Save a template."""
        path = self.templates_dir / f"{name}.json"
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def apply_template(self, name: str, date_str: str,
                       storage: BlockStorage) -> List[TimeBlock]:
        """Apply a template to a date."""
        template = self.load_template(name)
        if not template:
            return []

        blocks = []
        for block_data in template.get('blocks', []):
            # Support both end time and duration
            if 'end' in block_data:
                block = TimeBlock(
                    start=block_data['start'],
                    end=block_data['end'],
                    activity=block_data['activity'],
                    category=block_data.get('category', 'work'),
                    priority=block_data.get('priority', 'medium'),
                    notes=block_data.get('notes', ''),
                    recurring=block_data.get('recurring', False),
                    days=block_data.get('days', [])
                )
            else:
                block = TimeBlock.from_duration(
                    start=block_data['start'],
                    duration=block_data.get('duration', 60),
                    activity=block_data['activity'],
                    category=block_data.get('category', 'work'),
                    priority=block_data.get('priority', 'medium'),
                    notes=block_data.get('notes', ''),
                    recurring=block_data.get('recurring', False),
                    days=block_data.get('days', [])
                )

            storage.add_block(date_str, block)
            blocks.append(block)

        return blocks

    def create_from_schedule(self, name: str, schedule: DaySchedule) -> None:
        """Create a template from an existing schedule."""
        template = {
            'name': name,
            'description': f'Template created from {schedule.date}',
            'blocks': [b.to_dict() for b in schedule.blocks]
        }
        self.save_template(name, template)


# ============================================================================
# Visual Display
# ============================================================================

class ScheduleDisplay:
    """Handles visual representation of schedules."""

    # Category symbols for visual display
    CATEGORY_SYMBOLS = {
        'work': '\u2588',      # Full block
        'exercise': '\u2591',  # Light shade
        'personal': '\u2592',  # Medium shade
        'rest': '\u2593',      # Dark shade
        'admin': '\u2502',     # Vertical line
        'meal': '\u25cf',      # Circle
        'learning': '\u25a0',  # Square
        'social': '\u25c6',    # Diamond
    }

    # ANSI colors
    COLORS = {
        'work': '\033[94m',      # Blue
        'exercise': '\033[91m',  # Red
        'personal': '\033[93m',  # Yellow
        'rest': '\033[92m',      # Green
        'admin': '\033[96m',     # Cyan
        'meal': '\033[33m',      # Orange
        'learning': '\033[95m',  # Purple
        'social': '\033[32m',    # Dark green
        'reset': '\033[0m',
        'bold': '\033[1m',
        'dim': '\033[2m',
    }

    @classmethod
    def print_schedule(cls, schedule: DaySchedule, show_free: bool = False) -> None:
        """Print a visual representation of the day's schedule."""
        c = cls.COLORS

        # Header
        print(f"\n{c['bold']}{'=' * 60}")
        print(f"  TIME BLOCKS - {schedule.date}")
        print(f"{'=' * 60}{c['reset']}\n")

        if not schedule.blocks:
            print(f"  {c['dim']}No blocks scheduled for this day.{c['reset']}\n")
            return

        # Print each block
        for i, block in enumerate(schedule.blocks):
            cat_color = c.get(block.category, c['reset'])
            symbol = cls.CATEGORY_SYMBOLS.get(block.category, '\u25aa')

            # Time line
            print(f"  {cat_color}{symbol}{c['reset']} ", end='')
            print(f"{c['bold']}{block.start} - {block.end}{c['reset']}", end='')
            print(f"  ({block.duration_minutes} min)")

            # Activity
            print(f"    {cat_color}{block.activity}{c['reset']}")

            # Details
            print(f"    {c['dim']}Category: {block.category.upper()} | Priority: {block.priority}{c['reset']}")

            if block.notes:
                print(f"    {c['dim']}Notes: {block.notes}{c['reset']}")

            if block.recurring:
                days_str = ', '.join(d.upper() for d in block.days)
                print(f"    {c['dim']}Recurring: {days_str}{c['reset']}")

            print()

        # Summary
        total_minutes = sum(b.duration_minutes for b in schedule.blocks)
        hours = total_minutes // 60
        minutes = total_minutes % 60

        print(f"{c['dim']}{'─' * 60}")
        print(f"  Total scheduled: {hours}h {minutes}m across {len(schedule.blocks)} blocks")
        print(f"{'─' * 60}{c['reset']}\n")

        # Category legend
        print(f"  {c['bold']}Categories:{c['reset']}")
        for cat, color in cls.COLORS.items():
            if cat not in ['reset', 'bold', 'dim']:
                symbol = cls.CATEGORY_SYMBOLS.get(cat, '\u25aa')
                print(f"    {color}{symbol} {cat.upper()}{c['reset']}", end='  ')
        print('\n')

    @classmethod
    def print_timeline(cls, schedule: DaySchedule, start_hour: int = None,
                       end_hour: int = None) -> None:
        """Print a timeline view of the day.

        Uses working hours from config if start_hour/end_hour not specified.
        """
        c = cls.COLORS

        # Use configured working hours if not specified
        if start_hour is None or end_hour is None:
            working_hours = get_working_hours()
            if start_hour is None:
                start_hour = int(working_hours['start'].split(':')[0])
            if end_hour is None:
                end_hour = int(working_hours['end'].split(':')[0]) + 1  # +1 to include the last hour

        print(f"\n{c['bold']}TIMELINE VIEW - {schedule.date}{c['reset']}")
        print(f"{c['dim']}Working hours: {start_hour:02d}:00 - {end_hour-1:02d}:00{c['reset']}\n")

        # Create hour slots
        for hour in range(start_hour, end_hour):
            hour_str = f"{hour:02d}:00"

            # Check if any block starts in this hour
            blocks_in_hour = [
                b for b in schedule.blocks
                if int(b.start.split(':')[0]) == hour
            ]

            if blocks_in_hour:
                for block in blocks_in_hour:
                    cat_color = c.get(block.category, c['reset'])
                    bar_len = min(block.duration_minutes // 2, 40)  # Scale bar
                    bar = '\u2588' * bar_len
                    print(f"  {hour_str} {cat_color}{bar}{c['reset']} {block.activity}")
            else:
                print(f"  {c['dim']}{hour_str} {'·' * 20}{c['reset']}")

        print()


# ============================================================================
# CLI Interface
# ============================================================================

def parse_date(date_str: str) -> str:
    """Parse flexible date input to YYYY-MM-DD format."""
    if date_str.lower() == 'today':
        return date.today().strftime('%Y-%m-%d')
    elif date_str.lower() == 'tomorrow':
        return (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        # Try to parse various formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%d/%m/%Y']:
            try:
                return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        return date_str  # Return as-is, will fail later if invalid


def main():
    parser = argparse.ArgumentParser(
        description='Time Blocks - Schedule focused work periods',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s add --start 6:00 --end 7:00 --activity "Workout" --category exercise
  %(prog)s add --start 19:00 --duration 180 --activity "Project Building" --category work
  %(prog)s apply-template productive_day --date today
  %(prog)s view --date today
  %(prog)s sync --calendar "Work Blocks" --date today
  %(prog)s templates
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Add block
    add_parser = subparsers.add_parser('add', help='Add a time block')
    add_parser.add_argument('--start', required=True, help='Start time (HH:MM)')
    add_parser.add_argument('--end', help='End time (HH:MM)')
    add_parser.add_argument('--duration', type=int, help='Duration in minutes')
    add_parser.add_argument('--activity', required=True, help='Activity name')
    add_parser.add_argument('--category', default='work',
                           choices=['work', 'exercise', 'personal', 'rest',
                                   'admin', 'meal', 'learning', 'social'],
                           help='Activity category')
    add_parser.add_argument('--priority', default='medium',
                           choices=['low', 'medium', 'high', 'critical'],
                           help='Priority level')
    add_parser.add_argument('--notes', default='', help='Additional notes')
    add_parser.add_argument('--date', default='today', help='Date (YYYY-MM-DD or "today")')
    add_parser.add_argument('--recurring', action='store_true', help='Make recurring')
    add_parser.add_argument('--days', nargs='+',
                           help='Days for recurring (mon tue wed thu fri sat sun)')

    # Remove block
    remove_parser = subparsers.add_parser('remove', help='Remove a time block')
    remove_parser.add_argument('index', type=int, help='Block index (0-based)')
    remove_parser.add_argument('--date', default='today', help='Date')

    # Clear day
    clear_parser = subparsers.add_parser('clear', help='Clear all blocks for a day')
    clear_parser.add_argument('--date', default='today', help='Date')

    # View schedule
    view_parser = subparsers.add_parser('view', help='View schedule')
    view_parser.add_argument('--date', default='today', help='Date')
    view_parser.add_argument('--timeline', action='store_true', help='Show timeline view')

    # Apply template
    template_parser = subparsers.add_parser('apply-template', help='Apply a template')
    template_parser.add_argument('template', help='Template name')
    template_parser.add_argument('--date', default='today', help='Date')

    # Save as template
    save_template_parser = subparsers.add_parser('save-template', help='Save current schedule as template')
    save_template_parser.add_argument('name', help='Template name')
    save_template_parser.add_argument('--date', default='today', help='Date to save')

    # List templates
    subparsers.add_parser('templates', help='List available templates')

    # Sync to Google Calendar
    sync_parser = subparsers.add_parser('sync', help='Sync to Google Calendar')
    sync_parser.add_argument('--calendar', default='Time Blocks', help='Calendar name')
    sync_parser.add_argument('--date', default='today', help='Date')
    sync_parser.add_argument('--force', action='store_true',
                            help='Create events even if similar exists')

    # List calendars
    subparsers.add_parser('calendars', help='List Google Calendar calendars')

    # Auth (for initial setup)
    subparsers.add_parser('auth', help='Authenticate with Google Calendar')

    # Show config/preferences
    subparsers.add_parser('config', help='Show current configuration and working hours')

    args = parser.parse_args()

    # Initialize components
    storage = BlockStorage()
    templates = TemplateManager()
    gcal = GoogleCalendarSync()

    if args.command == 'add':
        date_str = parse_date(args.date)

        if args.end:
            block = TimeBlock(
                start=args.start,
                end=args.end,
                activity=args.activity,
                category=args.category,
                priority=args.priority,
                notes=args.notes,
                recurring=args.recurring,
                days=args.days or []
            )
        elif args.duration:
            block = TimeBlock.from_duration(
                start=args.start,
                duration=args.duration,
                activity=args.activity,
                category=args.category,
                priority=args.priority,
                notes=args.notes,
                recurring=args.recurring,
                days=args.days or []
            )
        else:
            print("Error: Must specify either --end or --duration")
            sys.exit(1)

        # Validate block is within working hours
        is_valid, error_msg = validate_block_within_working_hours(block)
        if not is_valid:
            working_hours = get_working_hours()
            print(f"Warning: {error_msg}")
            print(f"Working hours are set to {working_hours['start']} - {working_hours['end']}")
            response = input("Add anyway? (y/N): ").strip().lower()
            if response != 'y':
                print("Block not added.")
                sys.exit(0)

        storage.add_block(date_str, block)
        print(f"Added: {block.activity} ({block.start} - {block.end})")

        # Show updated schedule
        schedule = storage.get_schedule(date_str)
        ScheduleDisplay.print_schedule(schedule)

    elif args.command == 'remove':
        date_str = parse_date(args.date)
        if storage.remove_block(date_str, args.index):
            print(f"Removed block at index {args.index}")
        else:
            print(f"Error: No block found at index {args.index}")
            sys.exit(1)

    elif args.command == 'clear':
        date_str = parse_date(args.date)
        storage.clear_date(date_str)
        print(f"Cleared all blocks for {date_str}")

    elif args.command == 'view':
        date_str = parse_date(args.date)
        schedule = storage.get_schedule(date_str)

        if args.timeline:
            ScheduleDisplay.print_timeline(schedule)
        else:
            ScheduleDisplay.print_schedule(schedule)

    elif args.command == 'apply-template':
        date_str = parse_date(args.date)
        blocks = templates.apply_template(args.template, date_str, storage)

        if blocks:
            print(f"Applied template '{args.template}' to {date_str}")
            print(f"Created {len(blocks)} blocks")

            schedule = storage.get_schedule(date_str)
            ScheduleDisplay.print_schedule(schedule)
        else:
            print(f"Error: Template '{args.template}' not found")
            print(f"Available templates: {', '.join(templates.list_templates())}")
            sys.exit(1)

    elif args.command == 'save-template':
        date_str = parse_date(args.date)
        schedule = storage.get_schedule(date_str)

        if schedule.blocks:
            templates.create_from_schedule(args.name, schedule)
            print(f"Saved schedule as template '{args.name}'")
        else:
            print(f"Error: No blocks found for {date_str}")
            sys.exit(1)

    elif args.command == 'templates':
        template_list = templates.list_templates()
        if template_list:
            print("\nAvailable templates:")
            for t in template_list:
                data = templates.load_template(t)
                # Count blocks - handle both flat blocks and day-specific structure
                block_count = len(data.get('blocks', []))
                recurring_count = len(data.get('recurring_blocks', []))
                day_specific = data.get('day_specific', {})

                if day_specific:
                    # Count total blocks across all days
                    day_block_count = sum(
                        len(day_data.get('blocks', []))
                        for day_data in day_specific.values()
                    )
                    print(f"  - {t} (weekly: {recurring_count} recurring + {day_block_count} day-specific)")
                else:
                    print(f"  - {t} ({block_count} blocks)")
        else:
            print("No templates found")

    elif args.command == 'sync':
        date_str = parse_date(args.date)
        schedule = storage.get_schedule(date_str)

        if not schedule.blocks:
            print(f"No blocks to sync for {date_str}")
            sys.exit(0)

        print(f"Syncing {len(schedule.blocks)} blocks to Google Calendar...")
        result = gcal.sync_schedule(
            schedule,
            args.calendar,
            skip_existing=not args.force
        )

        if result['success']:
            if result['created']:
                print(f"Created: {', '.join(result['created'])}")
            if result['skipped']:
                print(f"Skipped (already exists): {', '.join(result['skipped'])}")
            if result['errors']:
                print(f"Errors: {', '.join(result['errors'])}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            sys.exit(1)

    elif args.command == 'calendars':
        if gcal.authenticate():
            calendars = gcal.list_calendars()
            print("\nAvailable calendars:")
            for cal in calendars:
                print(f"  - {cal['name']}")
        else:
            sys.exit(1)

    elif args.command == 'auth':
        if gcal.authenticate():
            print("Successfully authenticated with Google Calendar!")
            print(f"Token saved to: {TOKEN_PATH}")
        else:
            sys.exit(1)

    elif args.command == 'config':
        prefs = load_user_preferences()
        working_hours = get_working_hours()

        print("\n" + "=" * 50)
        print("  TIME BLOCKS CONFIGURATION")
        print("=" * 50 + "\n")

        print(f"Config file: {USER_PREFS_PATH}")
        print(f"Config exists: {USER_PREFS_PATH.exists()}\n")

        print("WORKING HOURS:")
        print(f"  Start: {working_hours['start']} (6 AM)")
        print(f"  End:   {working_hours['end']} (9 PM)")
        print(f"  Note:  All blocks must fall within these hours\n")

        if prefs.get('recurring_blocks'):
            print("RECURRING BLOCKS:")
            for name, block in prefs['recurring_blocks'].items():
                days = ', '.join(d.upper() for d in block.get('days', []))
                time_start = block.get('time', {}).get('start', 'N/A')
                time_end = block.get('time', {}).get('end', 'N/A')
                print(f"  {name.upper()}:")
                print(f"    Time: {time_start} - {time_end}")
                print(f"    Days: {days}")
                print(f"    Category: {block.get('category', 'N/A')}")
                print()

        print("DATA PATHS:")
        print(f"  Blocks storage: {DATA_PATH}")
        print(f"  Token path: {TOKEN_PATH}")
        print(f"  Credentials: {CREDENTIALS_PATH}")
        print()

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
