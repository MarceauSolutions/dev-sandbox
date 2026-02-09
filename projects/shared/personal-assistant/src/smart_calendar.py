#!/usr/bin/env python3
"""
Smart Calendar: AI-Powered Time Block Scheduling

Integrates with three-agent protocol (SOP-29):
- Claude Code (Mac): Interactive planning, complex scheduling
- Clawdbot (EC2): Quick mobile requests ("block tomorrow for content")
- Ralph (EC2): Complex multi-week schedule generation via PRD

Philosophy:
- Hormozi-style prioritization: Revenue impact → Operations → Admin
- Energy management: Hard tasks in morning, admin in afternoon
- Habit stacking: Consistent daily routines compound
- Content velocity: Daily posts > weekly polished content
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
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
    print("Warning: Google Calendar API not available. Install google-api-python-client")

SCOPES = ['https://www.googleapis.com/auth/calendar']

# Default transition time between blocks (minutes)
DEFAULT_TRANSITION_MINUTES = 15


class Priority(Enum):
    """Hormozi-style priority levels"""
    CRITICAL = 1      # Revenue-generating, time-sensitive decisions
    HIGH = 2          # Important business activities
    MEDIUM = 3        # Operations and maintenance
    LOW = 4           # Admin and nice-to-haves
    HABIT = 5         # Daily habits (workout, reading, etc.)


class EnergyLevel(Enum):
    """Time-of-day energy optimization"""
    PEAK = "peak"           # 6-10 AM: Deep work, decisions, creative
    HIGH = "high"           # 10 AM-12 PM: Collaborative, meetings
    MODERATE = "moderate"   # 1-4 PM: Operations, follow-ups
    LOW = "low"             # 4-6 PM: Admin, routine tasks
    EVENING = "evening"     # 6-9 PM: Light work, content, personal


class BlockType(Enum):
    """Types of time blocks"""
    HABIT = "habit"             # Daily recurring (workout, reading)
    CONTENT = "content"         # Content creation/posting
    BUSINESS = "business"       # Business/revenue work
    LEARNING = "learning"       # Personal development (Spanish, reading)
    PERSONAL = "personal"       # Dog training, appointments
    PLANNING = "planning"       # Weekly review, planning


# Google Calendar color IDs
COLORS = {
    Priority.CRITICAL: "11",    # Red
    Priority.HIGH: "6",         # Orange
    Priority.MEDIUM: "5",       # Yellow
    Priority.LOW: "7",          # Cyan
    Priority.HABIT: "10",       # Green
    BlockType.CONTENT: "9",     # Blue
    BlockType.LEARNING: "2",    # Green (sage)
    BlockType.PLANNING: "3",    # Purple
}


@dataclass
class TimeBlock:
    """A scheduled time block"""
    summary: str
    description: str
    start: datetime
    end: datetime
    priority: Priority = Priority.MEDIUM
    block_type: BlockType = BlockType.BUSINESS
    color_id: str = "1"

    def to_calendar_event(self, timezone: str = "America/New_York") -> Dict[str, Any]:
        """Convert to Google Calendar event format"""
        return {
            'summary': self.summary,
            'description': self.description,
            'start': {
                'dateTime': self.start.isoformat(),
                'timeZone': timezone,
            },
            'end': {
                'dateTime': self.end.isoformat(),
                'timeZone': timezone,
            },
            'colorId': self.color_id,
            'reminders': {
                'useDefault': False,
                'overrides': [{'method': 'popup', 'minutes': 15}],
            },
        }


@dataclass
class ScheduleContext:
    """Context for AI-powered scheduling decisions"""
    # Business priorities
    revenue_goals: List[str] = field(default_factory=list)
    active_projects: List[str] = field(default_factory=list)
    pending_decisions: List[str] = field(default_factory=list)

    # Content strategy
    content_frequency: str = "daily"  # daily, 3x_week, weekly
    content_types: List[str] = field(default_factory=lambda: ["short_form", "long_form"])
    batch_content_day: str = "thursday"

    # Personal development
    habits: List[str] = field(default_factory=lambda: ["workout", "spanish", "reading", "dog_training"])
    learning_goals: List[str] = field(default_factory=list)

    # Energy preferences
    peak_hours: tuple = (6, 10)      # 6 AM - 10 AM
    low_energy_start: int = 16       # 4 PM

    # Working hours
    work_start: int = 6              # 6 AM
    work_end: int = 21               # 9 PM

    def to_dict(self) -> Dict[str, Any]:
        return {
            "revenue_goals": self.revenue_goals,
            "active_projects": self.active_projects,
            "pending_decisions": self.pending_decisions,
            "content_frequency": self.content_frequency,
            "content_types": self.content_types,
            "batch_content_day": self.batch_content_day,
            "habits": self.habits,
            "learning_goals": self.learning_goals,
            "peak_hours": self.peak_hours,
            "work_start": self.work_start,
            "work_end": self.work_end,
        }


class SmartCalendar:
    """AI-powered calendar scheduling system"""

    def __init__(self, context: Optional[ScheduleContext] = None):
        self.context = context or ScheduleContext()
        self.service = None
        self._load_calendar_service()

    def _load_calendar_service(self):
        """Load Google Calendar service"""
        if not GOOGLE_AVAILABLE:
            return

        creds = None
        token_path = Path('/Users/williammarceaujr./dev-sandbox/token.json')
        creds_path = Path('/Users/williammarceaujr./dev-sandbox/credentials.json')

        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not creds_path.exists():
                    print(f"Warning: credentials.json not found at {creds_path}")
                    return
                flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
                creds = flow.run_local_server(port=0)

            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        self.service = build('calendar', 'v3', credentials=creds)

    def get_existing_events(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch existing calendar events for a date range"""
        if not self.service:
            return []

        try:
            # Fetch events from Google Calendar
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_date.isoformat() + 'Z' if start_date.tzinfo is None else start_date.isoformat(),
                timeMax=end_date.isoformat() + 'Z' if end_date.tzinfo is None else end_date.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            # Parse events into a consistent format
            parsed_events = []
            for event in events:
                start = event.get('start', {})
                end = event.get('end', {})

                # Handle all-day events vs timed events
                if 'dateTime' in start:
                    start_dt = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end['dateTime'].replace('Z', '+00:00'))
                else:
                    # All-day event - skip for conflict detection
                    continue

                parsed_events.append({
                    'id': event.get('id'),
                    'summary': event.get('summary', 'Untitled'),
                    'start': start_dt,
                    'end': end_dt,
                    'description': event.get('description', '')
                })

            return parsed_events
        except Exception as e:
            print(f"Warning: Could not fetch existing events: {e}")
            return []

    def check_conflicts(self, new_block: TimeBlock, existing_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check if a new block conflicts with existing events"""
        conflicts = []

        for event in existing_events:
            event_start = event['start']
            event_end = event['end']

            # Remove timezone info for comparison if needed
            if new_block.start.tzinfo is None and event_start.tzinfo is not None:
                event_start = event_start.replace(tzinfo=None)
                event_end = event_end.replace(tzinfo=None)

            # Check for overlap: A overlaps B if A.start < B.end AND A.end > B.start
            if new_block.start < event_end and new_block.end > event_start:
                conflicts.append(event)

        return conflicts

    def check_duplicate(self, new_block: TimeBlock, existing_events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Check if a new block is a duplicate of an existing event"""
        for event in existing_events:
            event_start = event['start']

            # Remove timezone info for comparison if needed
            if new_block.start.tzinfo is None and event_start.tzinfo is not None:
                event_start = event_start.replace(tzinfo=None)

            # Check for duplicate: same summary and same start time (within 5 min)
            time_diff = abs((new_block.start - event_start).total_seconds())

            # Normalize summaries for comparison (remove emojis and extra spaces)
            new_summary = ''.join(c for c in new_block.summary if c.isalnum() or c.isspace()).lower().strip()
            existing_summary = ''.join(c for c in event['summary'] if c.isalnum() or c.isspace()).lower().strip()

            if time_diff < 300 and (new_summary in existing_summary or existing_summary in new_summary):
                return event

        return None

    def add_transition_time(self, blocks: List[TimeBlock], transition_minutes: int = DEFAULT_TRANSITION_MINUTES) -> List[TimeBlock]:
        """Add transition time between blocks by ending each block earlier"""
        if not blocks:
            return blocks

        # Sort blocks by start time
        sorted_blocks = sorted(blocks, key=lambda b: b.start)

        # Adjust end times to leave transition buffer
        for i, block in enumerate(sorted_blocks):
            # Check if there's a next block on the same day
            if i < len(sorted_blocks) - 1:
                next_block = sorted_blocks[i + 1]

                # Only adjust if blocks are on the same day and adjacent
                if block.start.date() == next_block.start.date():
                    gap = (next_block.start - block.end).total_seconds() / 60

                    # If gap is less than transition time, shorten current block
                    if gap < transition_minutes:
                        new_end = block.end - timedelta(minutes=transition_minutes - int(gap))
                        # Don't make blocks shorter than 15 minutes
                        if (new_end - block.start).total_seconds() >= 900:
                            block.end = new_end

        return sorted_blocks

    def generate_daily_habits(self, date: datetime) -> List[TimeBlock]:
        """Generate daily habit blocks based on context"""
        blocks = []
        day_name = date.strftime("%A").lower()
        is_weekend = day_name in ["saturday", "sunday"]

        # Workout - adjusted for weekends
        if "workout" in self.context.habits:
            if is_weekend:
                blocks.append(TimeBlock(
                    summary="💪 Active Recovery / Light Workout",
                    description="Walk, stretch, yoga, or light activity.\nRest is part of training.",
                    start=date.replace(hour=8, minute=0),
                    end=date.replace(hour=9, minute=0),
                    priority=Priority.HABIT,
                    block_type=BlockType.HABIT,
                    color_id=COLORS[Priority.HABIT]
                ))
            else:
                blocks.append(TimeBlock(
                    summary="💪 Workout",
                    description="Non-negotiable. Fitness influencer = practice what you preach.\nLog workout for potential content.",
                    start=date.replace(hour=6, minute=0),
                    end=date.replace(hour=7, minute=0),
                    priority=Priority.HABIT,
                    block_type=BlockType.HABIT,
                    color_id=COLORS[Priority.HABIT]
                ))

        # Spanish - weekdays only
        if "spanish" in self.context.habits and not is_weekend:
            blocks.append(TimeBlock(
                summary="🇪🇸 Spanish Practice",
                description="15-30 min Duolingo or Pimsleur.\n60M+ Hispanic Americans = 2x audience if bilingual.",
                start=date.replace(hour=7, minute=0),
                end=date.replace(hour=7, minute=30),
                priority=Priority.HABIT,
                block_type=BlockType.LEARNING,
                color_id=COLORS[BlockType.LEARNING]
            ))

        # Reading - daily but longer on weekends
        if "reading" in self.context.habits:
            if is_weekend and day_name == "sunday":
                blocks.append(TimeBlock(
                    summary="📚 Deep Reading / Learning",
                    description="Longer learning session. Peptide research, business books, etc.",
                    start=date.replace(hour=9, minute=0),
                    end=date.replace(hour=10, minute=30),
                    priority=Priority.HABIT,
                    block_type=BlockType.LEARNING,
                    color_id=COLORS[BlockType.LEARNING]
                ))
            elif not is_weekend:
                blocks.append(TimeBlock(
                    summary="📚 Reading",
                    description="Business, fitness, or personal development.\nIdeas for content come from inputs.",
                    start=date.replace(hour=7, minute=30),
                    end=date.replace(hour=8, minute=0),
                    priority=Priority.HABIT,
                    block_type=BlockType.LEARNING,
                    color_id=COLORS[BlockType.LEARNING]
                ))

        # Dog training - daily
        if "dog_training" in self.context.habits:
            if is_weekend:
                blocks.append(TimeBlock(
                    summary="🐕 Dog Training + Walk",
                    description="Longer weekend session. Good for both of you.",
                    start=date.replace(hour=10, minute=0),
                    end=date.replace(hour=11, minute=0),
                    priority=Priority.HABIT,
                    block_type=BlockType.PERSONAL,
                    color_id=COLORS[BlockType.LEARNING]
                ))
            else:
                blocks.append(TimeBlock(
                    summary="🐕 Dog Training",
                    description="Evening session. Discipline transfer + potential content angle.",
                    start=date.replace(hour=17, minute=0),
                    end=date.replace(hour=17, minute=30),
                    priority=Priority.HABIT,
                    block_type=BlockType.PERSONAL,
                    color_id=COLORS[BlockType.LEARNING]
                ))

        return blocks

    def generate_content_blocks(self, date: datetime) -> List[TimeBlock]:
        """Generate content creation/posting blocks based on strategy"""
        blocks = []
        day_name = date.strftime("%A").lower()
        is_weekend = day_name in ["saturday", "sunday"]

        # Daily content post (weekdays)
        if not is_weekend and self.context.content_frequency == "daily":
            blocks.append(TimeBlock(
                summary="📱 Daily Content Post",
                description="Post 1 short-form piece (TikTok/Reels/Shorts).\nRaw > Perfect. Volume negates luck.\n\nIdeas: workout clip, tip, form check, peptide fact.",
                start=date.replace(hour=20, minute=0),
                end=date.replace(hour=20, minute=30),
                priority=Priority.HIGH,
                block_type=BlockType.CONTENT,
                color_id=COLORS[BlockType.CONTENT]
            ))

        # Day-specific content blocks
        if day_name == "monday" and not is_weekend:
            blocks.append(TimeBlock(
                summary="🎬 Content Creation: Film 2-3 Short Clips",
                description="Batch film content while energy is high.\n\nIdeas:\n- Post-workout tip\n- Form demonstration\n- Quick peptide fact\n- Motivation/mindset\n\nRaw footage is fine - edit later or post raw.",
                start=date.replace(hour=11, minute=0),
                end=date.replace(hour=12, minute=0),
                priority=Priority.HIGH,
                block_type=BlockType.CONTENT,
                color_id=COLORS[BlockType.CONTENT]
            ))

        elif day_name == "wednesday" and not is_weekend:
            blocks.append(TimeBlock(
                summary="🎬 Content Creation: Medium-Form Content",
                description="Create 1-2 longer pieces (3-5 min).\n\nIdeas:\n- Full workout walkthrough\n- Peptide basics explainer\n- Client transformation story\n- Q&A from DMs\n\nCan be YouTube Short or full video.",
                start=date.replace(hour=14, minute=0),
                end=date.replace(hour=15, minute=30),
                priority=Priority.HIGH,
                block_type=BlockType.CONTENT,
                color_id=COLORS[BlockType.CONTENT]
            ))

        elif day_name == self.context.batch_content_day and not is_weekend:
            blocks.append(TimeBlock(
                summary="🎬 BATCH DAY: Long-Form YouTube Production",
                description="Dedicated content production block.\n\nCreate 1 polished YouTube video OR batch multiple shorts.\n\nStructure:\n1. Script/outline (30 min)\n2. Film (1 hr)\n3. Edit (1.5 hr)\n\nTopic ideas:\n- Peptide deep-dive\n- Weekly workout routine\n- Nutrition protocol\n- 'Day in the life' fitness",
                start=date.replace(hour=9, minute=0),
                end=date.replace(hour=12, minute=0),
                priority=Priority.HIGH,
                block_type=BlockType.CONTENT,
                color_id=COLORS[BlockType.CONTENT]
            ))

        elif day_name == "friday" and not is_weekend:
            blocks.append(TimeBlock(
                summary="🎬 Content Review: Publish Best of Week",
                description="Review week's content and publish best pieces.\n\nActions:\n1. Review all filmed content\n2. Quick edits on top 2-3 pieces\n3. Schedule for optimal posting times\n4. Cross-post to all platforms\n\nFriday afternoon = high engagement time.",
                start=date.replace(hour=10, minute=30),
                end=date.replace(hour=12, minute=0),
                priority=Priority.HIGH,
                block_type=BlockType.CONTENT,
                color_id=COLORS[BlockType.CONTENT]
            ))

        elif day_name == "sunday":
            blocks.append(TimeBlock(
                summary="📅 Week Prep: Content Batching",
                description="Plan and batch content for the week.\n- Write 5-7 short-form hooks\n- Outline 1 long-form video\n- Schedule posts if possible",
                start=date.replace(hour=14, minute=0),
                end=date.replace(hour=16, minute=0),
                priority=Priority.MEDIUM,
                block_type=BlockType.PLANNING,
                color_id=COLORS[BlockType.CONTENT]
            ))

        return blocks

    def generate_business_blocks(self, date: datetime, priorities: List[Dict[str, Any]]) -> List[TimeBlock]:
        """Generate business blocks based on priorities"""
        blocks = []
        day_name = date.strftime("%A").lower()
        is_weekend = day_name in ["saturday", "sunday"]

        if is_weekend:
            return blocks  # No business blocks on weekends

        # Critical/High priority items go in peak hours (9-11 AM)
        peak_start = 9
        for i, priority in enumerate(priorities[:2]):  # Max 2 critical items per day
            if priority.get("level") in ["critical", "high"]:
                duration = priority.get("duration", 90)  # Default 90 min
                blocks.append(TimeBlock(
                    summary=priority.get("emoji", "🔴") + " " + priority.get("title", "Business Task"),
                    description=priority.get("description", ""),
                    start=date.replace(hour=peak_start + (i * 2), minute=0 if i == 0 else 30),
                    end=date.replace(hour=peak_start + (i * 2) + (duration // 60), minute=duration % 60),
                    priority=Priority.CRITICAL if priority.get("level") == "critical" else Priority.HIGH,
                    block_type=BlockType.BUSINESS,
                    color_id=COLORS[Priority.CRITICAL] if priority.get("level") == "critical" else COLORS[Priority.HIGH]
                ))

        # Medium priority items in afternoon
        afternoon_start = 14
        for i, priority in enumerate(priorities[2:4]):  # Max 2 medium items per day
            if priority.get("level") in ["medium", "low"]:
                duration = priority.get("duration", 60)
                blocks.append(TimeBlock(
                    summary=priority.get("emoji", "🟡") + " " + priority.get("title", "Business Task"),
                    description=priority.get("description", ""),
                    start=date.replace(hour=afternoon_start + (i * 2), minute=0),
                    end=date.replace(hour=afternoon_start + (i * 2) + (duration // 60), minute=duration % 60),
                    priority=Priority.MEDIUM if priority.get("level") == "medium" else Priority.LOW,
                    block_type=BlockType.BUSINESS,
                    color_id=COLORS[Priority.MEDIUM] if priority.get("level") == "medium" else COLORS[Priority.LOW]
                ))

        return blocks

    def add_planning_blocks(self, date: datetime) -> List[TimeBlock]:
        """Add weekly planning/review blocks"""
        blocks = []
        day_name = date.strftime("%A").lower()

        if day_name == "friday":
            blocks.append(TimeBlock(
                summary="📅 Weekly Planning: Review & Adjust",
                description="End of week planning session.\n\nAction items:\n1. Review content performance (what got engagement?)\n2. Document wins and learnings\n3. Update docs/session-history.md\n4. Plan next week's content themes\n5. Adjust strategy based on data\n\nPrepare for: Week 2 with more data",
                start=date.replace(hour=14, minute=0),
                end=date.replace(hour=15, minute=0),
                priority=Priority.MEDIUM,
                block_type=BlockType.PLANNING,
                color_id=COLORS[BlockType.PLANNING]
            ))

        return blocks

    def generate_week(
        self,
        start_date: datetime,
        priorities: Optional[List[Dict[str, Any]]] = None
    ) -> List[TimeBlock]:
        """Generate a full week of time blocks"""
        all_blocks = []
        priorities = priorities or []

        for day_offset in range(7):
            current_date = start_date + timedelta(days=day_offset)
            day_name = current_date.strftime("%A").lower()

            # Daily habits
            all_blocks.extend(self.generate_daily_habits(current_date))

            # Content blocks
            all_blocks.extend(self.generate_content_blocks(current_date))

            # Business blocks (distribute priorities across week)
            day_priorities = [p for p in priorities if p.get("day", "").lower() == day_name]
            all_blocks.extend(self.generate_business_blocks(current_date, day_priorities))

            # Planning blocks
            all_blocks.extend(self.add_planning_blocks(current_date))

        return all_blocks

    def create_blocks(
        self,
        blocks: List[TimeBlock],
        dry_run: bool = False,
        skip_conflict_check: bool = False,
        add_transitions: bool = True
    ) -> Dict[str, Any]:
        """Create time blocks in Google Calendar with conflict/duplicate detection"""
        if not self.service:
            return {"success": False, "error": "Google Calendar not available"}

        results = {
            "created": 0,
            "failed": 0,
            "skipped_duplicates": 0,
            "conflicts": [],
            "blocks": []
        }

        # Add transition time between blocks
        if add_transitions:
            blocks = self.add_transition_time(blocks)

        # Get date range for existing events
        if blocks:
            min_date = min(b.start for b in blocks)
            max_date = max(b.end for b in blocks) + timedelta(days=1)
            existing_events = self.get_existing_events(min_date, max_date)
        else:
            existing_events = []

        for block in blocks:
            # Check for duplicates
            duplicate = self.check_duplicate(block, existing_events)
            if duplicate:
                results["blocks"].append({
                    "summary": block.summary,
                    "start": block.start.isoformat(),
                    "end": block.end.isoformat(),
                    "status": "skipped_duplicate",
                    "existing_event": duplicate['summary']
                })
                results["skipped_duplicates"] += 1
                continue

            # Check for conflicts
            if not skip_conflict_check:
                conflicts = self.check_conflicts(block, existing_events)
                if conflicts:
                    conflict_info = {
                        "new_block": {
                            "summary": block.summary,
                            "start": block.start.isoformat(),
                            "end": block.end.isoformat()
                        },
                        "conflicting_events": [
                            {
                                "summary": c['summary'],
                                "start": c['start'].isoformat(),
                                "end": c['end'].isoformat()
                            }
                            for c in conflicts
                        ]
                    }
                    results["conflicts"].append(conflict_info)
                    results["blocks"].append({
                        "summary": block.summary,
                        "start": block.start.isoformat(),
                        "end": block.end.isoformat(),
                        "status": "conflict",
                        "conflicts_with": [c['summary'] for c in conflicts]
                    })
                    continue

            try:
                if dry_run:
                    results["blocks"].append({
                        "summary": block.summary,
                        "start": block.start.isoformat(),
                        "end": block.end.isoformat(),
                        "status": "dry_run"
                    })
                    results["created"] += 1
                else:
                    event = self.service.events().insert(
                        calendarId='primary',
                        body=block.to_calendar_event()
                    ).execute()
                    results["blocks"].append({
                        "summary": block.summary,
                        "start": block.start.isoformat(),
                        "end": block.end.isoformat(),
                        "status": "created",
                        "id": event.get("id")
                    })
                    results["created"] += 1

                    # Add to existing events for subsequent conflict checks
                    existing_events.append({
                        'id': event.get("id"),
                        'summary': block.summary,
                        'start': block.start,
                        'end': block.end
                    })
            except Exception as e:
                results["blocks"].append({
                    "summary": block.summary,
                    "error": str(e),
                    "status": "failed"
                })
                results["failed"] += 1

        results["success"] = results["failed"] == 0 and len(results["conflicts"]) == 0
        return results

    def delete_events(
        self,
        events: List[Dict[str, Any]],
        dry_run: bool = True,
        require_confirmation: bool = True
    ) -> Dict[str, Any]:
        """
        Delete events from Google Calendar with safety checks.

        CAUTION: This is a destructive operation!
        - Always shows preview first
        - Requires explicit confirmation
        - Cannot be undone
        """
        if not self.service:
            return {"success": False, "error": "Google Calendar not available"}

        results = {
            "deleted": 0,
            "failed": 0,
            "events": []
        }

        if not events:
            return {"success": True, "deleted": 0, "events": [], "message": "No events to delete"}

        # Show what will be deleted
        print("\n🗑️  EVENTS TO DELETE:")
        print("=" * 60)
        for i, event in enumerate(events, 1):
            start_time = event['start'].strftime('%Y-%m-%d %H:%M') if hasattr(event['start'], 'strftime') else str(event['start'])
            end_time = event['end'].strftime('%H:%M') if hasattr(event['end'], 'strftime') else str(event['end'])
            print(f"  {i}. {event['summary']}")
            print(f"     Time: {start_time} - {end_time}")
            print(f"     ID: {event.get('id', 'N/A')}")
        print("=" * 60)

        if dry_run:
            print("\n📋 Dry run - no events deleted. Use --delete --confirm to actually delete.")
            for event in events:
                results["events"].append({
                    "summary": event['summary'],
                    "status": "dry_run",
                    "id": event.get('id')
                })
            results["success"] = True
            return results

        # Double confirmation for safety
        if require_confirmation:
            print("\n⚠️  WARNING: This action CANNOT be undone!")
            confirm1 = input(f"Are you sure you want to delete {len(events)} event(s)? (yes/no): ")
            if confirm1.lower() != 'yes':
                print("Cancelled.")
                return {"success": False, "deleted": 0, "events": [], "message": "Cancelled by user"}

            confirm2 = input("Type 'DELETE' to confirm: ")
            if confirm2 != 'DELETE':
                print("Cancelled - confirmation not matched.")
                return {"success": False, "deleted": 0, "events": [], "message": "Confirmation not matched"}

        # Actually delete
        for event in events:
            event_id = event.get('id')
            if not event_id:
                results["events"].append({
                    "summary": event['summary'],
                    "status": "failed",
                    "error": "No event ID"
                })
                results["failed"] += 1
                continue

            try:
                self.service.events().delete(
                    calendarId='primary',
                    eventId=event_id
                ).execute()
                results["events"].append({
                    "summary": event['summary'],
                    "status": "deleted",
                    "id": event_id
                })
                results["deleted"] += 1
                print(f"   🗑️  Deleted: {event['summary']}")
            except Exception as e:
                results["events"].append({
                    "summary": event['summary'],
                    "status": "failed",
                    "error": str(e)
                })
                results["failed"] += 1
                print(f"   ❌ Failed to delete {event['summary']}: {e}")

        results["success"] = results["failed"] == 0
        return results

    def find_events_by_summary(self, search_term: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Find events matching a search term"""
        existing = self.get_existing_events(start_date, end_date)
        search_lower = search_term.lower()

        matches = [
            e for e in existing
            if search_lower in e['summary'].lower()
        ]

        return matches

    def schedule_from_natural_language(self, request: str, start_date: Optional[datetime] = None) -> List[TimeBlock]:
        """
        Parse natural language request and generate appropriate blocks.

        This is the main entry point for AI-powered scheduling.
        Can be called by:
        - Claude Code: Interactive session
        - Clawdbot: Quick mobile requests
        - Ralph: Complex schedule generation

        Examples:
        - "Block tomorrow for content creation"
        - "Schedule next week with focus on lead scraper and content"
        - "Add morning habits and Spanish practice for the week"
        """
        start_date = start_date or datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        request_lower = request.lower()

        # Detect time range
        if "tomorrow" in request_lower:
            start_date = start_date + timedelta(days=1)
            days = 1
        elif "week" in request_lower:
            # Start from next Monday if not already Monday
            days_until_monday = (7 - start_date.weekday()) % 7
            if days_until_monday == 0 and start_date.weekday() != 0:
                days_until_monday = 7
            start_date = start_date + timedelta(days=days_until_monday if days_until_monday else 0)
            days = 7
        else:
            days = 1

        # Detect focus areas
        blocks = []

        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)

            # Always include habits unless explicitly excluded
            if "no habits" not in request_lower:
                blocks.extend(self.generate_daily_habits(current_date))

            # Content focus
            if any(word in request_lower for word in ["content", "video", "post", "tiktok", "youtube"]):
                blocks.extend(self.generate_content_blocks(current_date))

            # Business focus
            if any(word in request_lower for word in ["business", "lead", "scraper", "campaign", "revenue"]):
                # Generate generic business blocks
                priorities = [
                    {"level": "high", "title": "Business Focus Block", "duration": 120, "day": current_date.strftime("%A").lower()}
                ]
                blocks.extend(self.generate_business_blocks(current_date, priorities))

            # Planning
            if "planning" in request_lower or "review" in request_lower:
                blocks.extend(self.add_planning_blocks(current_date))

        return blocks


def main():
    """CLI interface for smart calendar"""
    parser = argparse.ArgumentParser(description="Smart Calendar - AI-Powered Scheduling")
    parser.add_argument("--schedule", type=str, help="Natural language schedule request")
    parser.add_argument("--week", action="store_true", help="Generate full week starting from next Monday")
    parser.add_argument("--tomorrow", action="store_true", help="Generate tomorrow's schedule")
    parser.add_argument("--date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without creating events")
    parser.add_argument("--context", type=str, help="Path to context JSON file")
    parser.add_argument("--force", action="store_true", help="Skip conflict confirmation (create anyway)")
    parser.add_argument("--no-transitions", action="store_true", help="Don't add transition time between blocks")
    parser.add_argument("--show-existing", action="store_true", help="Show existing events for the date range")
    parser.add_argument("--delete", type=str, metavar="SEARCH", help="Delete events matching search term (DANGEROUS)")
    parser.add_argument("--confirm", action="store_true", help="Confirm deletion (required with --delete)")

    args = parser.parse_args()

    # Load context if provided
    context = ScheduleContext()
    if args.context:
        with open(args.context) as f:
            ctx_data = json.load(f)
            context = ScheduleContext(**ctx_data)

    # Default context for William
    context.habits = ["workout", "spanish", "reading", "dog_training"]
    context.content_frequency = "daily"
    context.batch_content_day = "thursday"

    calendar = SmartCalendar(context=context)

    # Determine start date
    if args.date:
        start_date = datetime.strptime(args.date, "%Y-%m-%d")
    elif args.tomorrow:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    elif args.week:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        # Start from next Monday
        days_until_monday = (7 - start_date.weekday()) % 7
        if days_until_monday == 0 and start_date.weekday() != 0:
            days_until_monday = 7
        start_date = start_date + timedelta(days=days_until_monday if days_until_monday else 0)
    else:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Determine end date for existing events check
    if args.week:
        end_date = start_date + timedelta(days=7)
    else:
        end_date = start_date + timedelta(days=1)

    # Show existing events if requested or always show for awareness
    existing_events = calendar.get_existing_events(start_date, end_date)
    if existing_events:
        print(f"\n📅 Existing events ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}):")
        print("-" * 60)
        for event in existing_events:
            start_time = event['start'].strftime('%H:%M') if hasattr(event['start'], 'strftime') else str(event['start'])
            end_time = event['end'].strftime('%H:%M') if hasattr(event['end'], 'strftime') else str(event['end'])
            date_str = event['start'].strftime('%a %m/%d') if hasattr(event['start'], 'strftime') else ''
            print(f"  • {date_str} {start_time}-{end_time}: {event['summary']}")
        print("-" * 60)
        print()

    if args.show_existing:
        return  # Only show existing events, don't generate new ones

    # Handle delete operation
    if args.delete:
        print(f"\n🔍 Searching for events matching: '{args.delete}'")
        matches = calendar.find_events_by_summary(args.delete, start_date, end_date)

        if not matches:
            print(f"❌ No events found matching '{args.delete}'")
            return

        print(f"Found {len(matches)} matching event(s)")

        # Delete with appropriate confirmation level
        delete_results = calendar.delete_events(
            matches,
            dry_run=not args.confirm,
            require_confirmation=True
        )

        if delete_results.get("deleted", 0) > 0:
            print(f"\n✅ Deleted {delete_results['deleted']} event(s)")
        return

    # Generate blocks
    if args.schedule:
        blocks = calendar.schedule_from_natural_language(args.schedule, start_date)
    elif args.week:
        blocks = calendar.generate_week(start_date)
    else:
        # Default: tomorrow with habits + content
        blocks = calendar.generate_daily_habits(start_date)
        blocks.extend(calendar.generate_content_blocks(start_date))

    # First pass: check for conflicts and duplicates (always dry run first)
    print(f"🔍 Checking {len(blocks)} proposed time blocks for conflicts...")
    print("=" * 60)

    check_results = calendar.create_blocks(
        blocks,
        dry_run=True,
        skip_conflict_check=False,
        add_transitions=not args.no_transitions
    )

    # Display results by category
    duplicates = [b for b in check_results["blocks"] if b["status"] == "skipped_duplicate"]
    conflicts = [b for b in check_results["blocks"] if b["status"] == "conflict"]
    ready = [b for b in check_results["blocks"] if b["status"] == "dry_run"]

    if duplicates:
        print(f"\n⚠️  {len(duplicates)} DUPLICATES (will skip):")
        for dup in duplicates:
            print(f"   ⏭️  {dup['summary']}")
            print(f"      Already exists: {dup.get('existing_event', 'similar event')}")

    if conflicts:
        print(f"\n🚨 {len(conflicts)} CONFLICTS DETECTED:")
        for conf in conflicts:
            print(f"   ⚠️  {conf['summary']}")
            print(f"      Time: {conf['start'].split('T')[1][:5]} - {conf['end'].split('T')[1][:5]}")
            print(f"      Conflicts with: {', '.join(conf.get('conflicts_with', []))}")

    if ready:
        print(f"\n✅ {len(ready)} events ready to create:")
        for blk in ready[:10]:  # Show first 10
            print(f"   • {blk['summary']}")
            print(f"     {blk['start'].split('T')[1][:5]} - {blk['end'].split('T')[1][:5]}")
        if len(ready) > 10:
            print(f"   ... and {len(ready) - 10} more")

    print("\n" + "=" * 60)
    print(f"Summary: {len(ready)} ready | {len(duplicates)} duplicates | {len(conflicts)} conflicts")

    # Handle conflicts
    if conflicts and not args.force and not args.dry_run:
        print("\n⚠️  There are conflicts! Options:")
        print("   1. Add --force to create anyway (will overlap)")
        print("   2. Resolve conflicts manually in Google Calendar first")
        print("   3. Use --dry-run to preview without creating")
        return

    # Create events if not dry run
    if args.dry_run:
        print("\n📋 Dry run - no events created. Remove --dry-run to create events.")
    else:
        if not ready:
            print("\n❌ No events to create (all duplicates or conflicts)")
            return

        # Confirm before creating
        if not args.force:
            confirm = input(f"\nCreate {len(ready)} events? (y/N): ")
            if confirm.lower() != 'y':
                print("Cancelled.")
                return

        # Actually create the events (skip duplicates, handle conflicts based on --force)
        print(f"\n🚀 Creating {len(ready)} events...")
        final_results = calendar.create_blocks(
            blocks,
            dry_run=False,
            skip_conflict_check=args.force,
            add_transitions=not args.no_transitions
        )

        created = [b for b in final_results["blocks"] if b["status"] == "created"]
        print(f"\n✅ Created {len(created)} events successfully!")

        for event in created:
            print(f"   ✅ {event['summary']}")


if __name__ == "__main__":
    main()
