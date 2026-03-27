#!/usr/bin/env python3
"""
Create time blocks for the week based on Hormozi high-agency framework.
Uses Google Calendar API.

Philosophy:
- High-agency tasks (study, reading, strategic thinking) → MORNING peak willpower
- Workout → 9-11 AM non-negotiable 2hr block
- Creative work (recording) → post-workout energy
- Reactive tasks (editing, admin, email, social) → AFTERNOON
- Never waste peak morning hours on email or social media
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']

# =============================================================================
# HORMOZI FRAMEWORK: Time blocks for week of Feb 10, 2026
# Morning = HIGH-AGENCY (study, reading, strategic thinking)
# Afternoon = REACTIVE (editing, admin, email, social)
# =============================================================================

# Reading rotation by day
READING_TOPICS = {
    "Mon": "Business/Entrepreneurship + Weekly planning",
    "Tue": "Fitness/Exercise Science + Peptide deep-dive",
    "Wed": "Business/Entrepreneurship + Analytics review",
    "Thu": "Fitness/Exercise Science + Lead follow-up",
    "Fri": "Psychology/Productivity + Business review",
}

# Content themes by day
CONTENT_THEMES = {
    "Mon": ("Quick workout tip / gym hack", "30-60s short"),
    "Tue": ("Full exercise tutorial", "2-3 min"),
    "Wed": ("Peptide education / science content", "medium-form"),
    "Thu": ("Client transformation / before-after", "short"),
    "Fri": ("Week recap + motivation", "short"),
    "Sat": ("Longer-form workout follow-along", "long-form"),
    "Sun": ("Lifestyle / nutrition / dog content", "rest day"),
}

# Workout rotation by day
WORKOUT_FOCUS = {
    "Mon": "Push (Chest/Shoulders/Tri)",
    "Tue": "Pull (Back/Biceps)",
    "Wed": "Legs (Quads/Hams/Glutes)",
    "Thu": "Push variation",
    "Fri": "Pull variation",
    "Sat": "Full body / Active recovery",
    "Sun": "Rest / Light cardio",
}


def generate_weekday_blocks(date):
    """Generate all blocks for a single weekday using Hormozi framework."""
    day_abbr = date.strftime("%a")
    day_str = date.strftime("%Y-%m-%d")
    reading_topic = READING_TOPICS.get(day_abbr, "Business")
    content_theme, content_format = CONTENT_THEMES.get(day_abbr, ("General content", "short"))
    workout_focus = WORKOUT_FOCUS.get(day_abbr, "General training")

    blocks = []

    # === 7:00-7:30 MORNING STARTUP ===
    blocks.append({
        "summary": "🌅 Morning Startup",
        "description": "Wake + hydrate (water, electrolytes, peptide protocol) + short dog walk.\n\nNo screens, no email, no social media. Protect the morning.",
        "start": f"{day_str}T07:00:00",
        "end": f"{day_str}T07:30:00",
        "colorId": "10"  # Green
    })

    # === 7:30-9:00 HIGH-AGENCY BLOCK (PEAK WILLPOWER) ===
    blocks.append({
        "summary": "🧠 HIGH-AGENCY: Study + Reading",
        "description": f"PEAK WILLPOWER — highest cognitive load tasks FIRST.\n\n"
                      f"7:30-8:15: Peptide Research (protocols, mechanisms, compounds)\n"
                      f"8:15-8:45: Business Education — {reading_topic}\n"
                      f"8:45-9:00: Pre-workout nutrition\n\n"
                      f"Hormozi rule: Do the thing that makes everything else easier or unnecessary FIRST.",
        "start": f"{day_str}T07:30:00",
        "end": f"{day_str}T09:00:00",
        "colorId": "11"  # Red (critical priority)
    })

    # === 9:00-11:00 WORKOUT (2hr NON-NEGOTIABLE) ===
    blocks.append({
        "summary": f"💪 WORKOUT: {workout_focus}",
        "description": f"NON-NEGOTIABLE 2-hour block.\n\n"
                      f"Focus: {workout_focus}\n\n"
                      f"9:00-9:15: Warmup (dynamic stretching, mobility)\n"
                      f"9:15-10:30: Training session\n"
                      f"10:30-10:45: Cooldown + stretch\n"
                      f"10:45-11:00: Post-workout nutrition\n\n"
                      f"If filming: set up camera BEFORE warmup, film 2-3 key sets.",
        "start": f"{day_str}T09:00:00",
        "end": f"{day_str}T11:00:00",
        "colorId": "10"  # Green
    })

    # === 11:00-1:00 VIDEO RECORDING (CREATIVE/PROACTIVE) ===
    blocks.append({
        "summary": f"🎬 Record: {content_theme}",
        "description": f"Creative block — still proactive, uses post-workout energy.\n\n"
                      f"Theme: {content_theme}\n"
                      f"Format: {content_format}\n\n"
                      f"11:00-11:15: Review content calendar\n"
                      f"11:15-12:15: Record video content\n"
                      f"12:15-12:45: Quick edit pass (import to pipeline)\n"
                      f"12:45-1:00: Publish/schedule to TikTok, YouTube, IG",
        "start": f"{day_str}T11:00:00",
        "end": f"{day_str}T13:00:00",
        "colorId": "9"  # Blue
    })

    # === 1:00-1:30 LUNCH ===
    blocks.append({
        "summary": "🍽️ Lunch",
        "description": "Meal prep or cook.",
        "start": f"{day_str}T13:00:00",
        "end": f"{day_str}T13:30:00",
        "colorId": "2"  # Green (sage)
    })

    # === 1:30-3:30 VIDEO EDITING (REACTIVE/MECHANICAL) ===
    blocks.append({
        "summary": "✂️ Video Editing & Post-Production",
        "description": "REACTIVE — doesn't require peak willpower.\n\n"
                      "1:30-2:00: Review pipeline output\n"
                      "2:00-3:00: Fine-tune edits, B-roll, captions\n"
                      "3:00-3:30: Export & package for platforms",
        "start": f"{day_str}T13:30:00",
        "end": f"{day_str}T15:30:00",
        "colorId": "9"  # Blue
    })

    # === 3:30-5:00 BUSINESS OPS & ADMIN (REACTIVE) ===
    blocks.append({
        "summary": "📊 Business Ops & Admin",
        "description": "REACTIVE — lowest leverage tasks go last in the workday.\n\n"
                      "3:30-3:45: Check SMS/lead replies\n"
                      "3:45-4:00: Review morning digest (NOT in morning!)\n"
                      "4:00-4:30: Review analytics, campaign performance\n"
                      "4:30-5:00: Social engagement, comments, DMs\n\n"
                      "Rule: NO email or social media before 3:30 PM.",
        "start": f"{day_str}T15:30:00",
        "end": f"{day_str}T17:00:00",
        "colorId": "7"  # Cyan
    })

    # === 5:00-6:00 PLAN TOMORROW + DOG TRAINING ===
    blocks.append({
        "summary": "🐕 Plan Tomorrow + Dog Training",
        "description": "5:00-5:15: Plan tomorrow (content topic, workout, calendar)\n"
                      "5:15-6:00: Dog training + evening walk\n\n"
                      "Obedience drills, socialization, mental stimulation on return.",
        "start": f"{day_str}T17:00:00",
        "end": f"{day_str}T18:00:00",
        "colorId": "2"  # Green (sage)
    })

    # === 6:00-7:00 DINNER + WIND DOWN ===
    blocks.append({
        "summary": "🍽️ Dinner + Wind Down",
        "description": "6:00-6:30: Dinner\n6:30-7:00: Light stretching, prep for next day.",
        "start": f"{day_str}T18:00:00",
        "end": f"{day_str}T19:00:00",
        "colorId": "2"  # Green (sage)
    })

    return blocks


def generate_weekend_blocks(date):
    """Generate weekend blocks (lighter schedule)."""
    day_abbr = date.strftime("%a")
    day_str = date.strftime("%Y-%m-%d")
    workout_focus = WORKOUT_FOCUS.get(day_abbr, "Active recovery")
    content_theme, content_format = CONTENT_THEMES.get(day_abbr, ("Lifestyle content", "short"))

    blocks = []

    if day_abbr == "Sat":
        blocks.append({
            "summary": f"💪 {workout_focus}",
            "description": "Lighter weekend session. Walk, stretch, yoga, or light activity.\nRest is part of training.",
            "start": f"{day_str}T09:00:00",
            "end": f"{day_str}T10:00:00",
            "colorId": "10"
        })
        blocks.append({
            "summary": "🐕 Dog Training + Walk",
            "description": "Longer weekend session. Good for both of you.",
            "start": f"{day_str}T10:00:00",
            "end": f"{day_str}T11:00:00",
            "colorId": "2"
        })
        blocks.append({
            "summary": f"🎬 {content_theme}",
            "description": f"Weekend content: {content_theme}\nFormat: {content_format}\n\nMore relaxed pace — film when inspiration strikes.",
            "start": f"{day_str}T14:00:00",
            "end": f"{day_str}T16:00:00",
            "colorId": "9"
        })

    elif day_abbr == "Sun":
        blocks.append({
            "summary": "📚 Deep Reading / Learning",
            "description": "Longer learning session. Peptide research, business books, biohacking.\nPersonal interest / fiction allowed on Sundays.",
            "start": f"{day_str}T09:00:00",
            "end": f"{day_str}T10:30:00",
            "colorId": "2"
        })
        blocks.append({
            "summary": "🐕 Dog Training + Walk",
            "description": "Longer weekend session.",
            "start": f"{day_str}T10:30:00",
            "end": f"{day_str}T11:30:00",
            "colorId": "2"
        })
        blocks.append({
            "summary": "📅 Week Prep: Content Batching",
            "description": "Plan and batch content for the week.\n- Write 5-7 short-form hooks\n- Outline 1 long-form video\n- Schedule posts if possible\n- Meal prep for the week",
            "start": f"{day_str}T14:00:00",
            "end": f"{day_str}T16:00:00",
            "colorId": "3"
        })

    return blocks


def get_calendar_service():
    """Authenticate and return Google Calendar service."""
    creds = None
    token_path = Path(__file__).parent.parent / 'token.json'
    creds_path = Path(__file__).parent.parent / 'credentials.json'

    # Try root dev-sandbox paths as fallback
    if not creds_path.exists():
        creds_path = Path('/Users/williammarceaujr./dev-sandbox/credentials.json')
    if not token_path.exists():
        token_path = Path('/Users/williammarceaujr./dev-sandbox/token.json')

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                print(f"Error: credentials.json not found at {creds_path}")
                print("Please ensure Google OAuth credentials are set up.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)


def create_time_block(service, block):
    """Create a single calendar event."""
    event = {
        'summary': block['summary'],
        'description': block['description'],
        'start': {
            'dateTime': block['start'],
            'timeZone': 'America/New_York',
        },
        'end': {
            'dateTime': block['end'],
            'timeZone': 'America/New_York',
        },
        'colorId': block.get('colorId', '1'),
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 15},
            ],
        },
    }

    created = service.events().insert(calendarId='primary', body=event).execute()
    return created


def main():
    """Create all time blocks for the week."""
    # Generate blocks for week of Feb 10, 2026
    start_date = datetime(2026, 2, 10)  # Monday

    all_blocks = []
    for day_offset in range(7):
        current_date = start_date + timedelta(days=day_offset)
        day_name = current_date.strftime("%A")
        day_abbr = current_date.strftime("%a")

        if day_abbr in ("Sat", "Sun"):
            all_blocks.extend(generate_weekend_blocks(current_date))
        else:
            all_blocks.extend(generate_weekday_blocks(current_date))

    print("Creating time blocks for week of Feb 10, 2026...")
    print("Framework: Alex Hormozi High-Agency (study/reading FIRST, reactive tasks LAST)")
    print("=" * 70)

    service = get_calendar_service()
    if not service:
        print("Failed to authenticate with Google Calendar")
        return

    created_count = 0
    for block in all_blocks:
        try:
            event = create_time_block(service, block)
            print(f"  {block['summary'][:55]}")
            print(f"    {block['start'].split('T')[0]} {block['start'].split('T')[1][:5]} - {block['end'].split('T')[1][:5]}")
            created_count += 1
        except Exception as e:
            print(f"  FAILED: {block['summary'][:55]}")
            print(f"    Error: {e}")

    print("=" * 70)
    print(f"Created {created_count}/{len(all_blocks)} time blocks")
    print()
    print("HORMOZI DAILY FRAMEWORK:")
    print("  7:00-7:30   🌅 Morning Startup (wake, hydrate, dog walk)")
    print("  7:30-9:00   🧠 HIGH-AGENCY: Peptide Study + Business Education + Reading")
    print("  9:00-11:00  💪 WORKOUT (2hr non-negotiable)")
    print("  11:00-1:00  🎬 Video Recording (creative/proactive)")
    print("  1:00-1:30   🍽️  Lunch")
    print("  1:30-3:30   ✂️  Video Editing (reactive/mechanical)")
    print("  3:30-5:00   📊 Business Ops & Admin (reactive)")
    print("  5:00-6:00   🐕 Plan Tomorrow + Dog Training")
    print("  6:00-7:00   🍽️  Dinner + Wind Down")
    print()
    print("Rule: NO email or social media before 3:30 PM.")


if __name__ == '__main__':
    main()
