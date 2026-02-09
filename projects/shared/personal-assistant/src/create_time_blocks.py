#!/usr/bin/env python3
"""
Create time blocks for the week based on business priorities.
Uses Google Calendar API.

Philosophy: Volume > Perfection for content. Daily habits compound.
"""

import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']

# Time blocks for week of Feb 10, 2026
# Based on: Content velocity + Personal development + Business priorities
TIME_BLOCKS = [
    # ========================================
    # DAILY HABITS (Mon-Fri) - Non-negotiable
    # ========================================

    # MONDAY Feb 10 - Daily Habits
    {
        "summary": "💪 Workout",
        "description": "Non-negotiable. Fitness influencer = practice what you preach.\nLog workout for potential content.",
        "start": "2026-02-10T06:00:00",
        "end": "2026-02-10T07:00:00",
        "colorId": "10"  # Green
    },
    {
        "summary": "🇪🇸 Spanish Practice",
        "description": "15-30 min Duolingo or Pimsleur.\n60M+ Hispanic Americans = 2x audience if bilingual.",
        "start": "2026-02-10T07:00:00",
        "end": "2026-02-10T07:30:00",
        "colorId": "2"  # Green
    },
    {
        "summary": "📚 Reading",
        "description": "Business, fitness, or personal development.\nIdeas for content come from inputs.",
        "start": "2026-02-10T07:30:00",
        "end": "2026-02-10T08:00:00",
        "colorId": "2"  # Green
    },
    {
        "summary": "🐕 Dog Training",
        "description": "Evening session. Discipline transfer + potential content angle.",
        "start": "2026-02-10T17:00:00",
        "end": "2026-02-10T17:30:00",
        "colorId": "2"  # Green
    },
    {
        "summary": "📱 Daily Content Post",
        "description": "Post 1 short-form piece (TikTok/Reels/Shorts).\nRaw > Perfect. Volume negates luck.\n\nIdeas: workout clip, tip, form check, peptide fact.",
        "start": "2026-02-10T20:00:00",
        "end": "2026-02-10T20:30:00",
        "colorId": "9"  # Blue
    },

    # TUESDAY Feb 11 - Daily Habits
    {
        "summary": "💪 Workout",
        "description": "Non-negotiable. Fitness influencer = practice what you preach.\nLog workout for potential content.",
        "start": "2026-02-11T06:00:00",
        "end": "2026-02-11T07:00:00",
        "colorId": "10"  # Green
    },
    {
        "summary": "🇪🇸 Spanish Practice",
        "description": "15-30 min Duolingo or Pimsleur.\n60M+ Hispanic Americans = 2x audience if bilingual.",
        "start": "2026-02-11T07:00:00",
        "end": "2026-02-11T07:30:00",
        "colorId": "2"  # Green
    },
    {
        "summary": "📚 Reading",
        "description": "Business, fitness, or personal development.\nIdeas for content come from inputs.",
        "start": "2026-02-11T07:30:00",
        "end": "2026-02-11T08:00:00",
        "colorId": "2"  # Green
    },
    {
        "summary": "🐕 Dog Training",
        "description": "Evening session. Discipline transfer + potential content angle.",
        "start": "2026-02-11T17:00:00",
        "end": "2026-02-11T17:30:00",
        "colorId": "2"  # Green
    },
    {
        "summary": "📱 Daily Content Post",
        "description": "Post 1 short-form piece (TikTok/Reels/Shorts).\nRaw > Perfect. Volume negates luck.\n\nIdeas: workout clip, tip, form check, peptide fact.",
        "start": "2026-02-11T20:00:00",
        "end": "2026-02-11T20:30:00",
        "colorId": "9"  # Blue
    },

    # WEDNESDAY Feb 12 - Daily Habits
    {
        "summary": "💪 Workout",
        "description": "Non-negotiable. Fitness influencer = practice what you preach.\nLog workout for potential content.",
        "start": "2026-02-12T06:00:00",
        "end": "2026-02-12T07:00:00",
        "colorId": "10"  # Green
    },
    {
        "summary": "🇪🇸 Spanish Practice",
        "description": "15-30 min Duolingo or Pimsleur.\n60M+ Hispanic Americans = 2x audience if bilingual.",
        "start": "2026-02-12T07:00:00",
        "end": "2026-02-12T07:30:00",
        "colorId": "2"  # Green
    },
    {
        "summary": "📚 Reading",
        "description": "Business, fitness, or personal development.\nIdeas for content come from inputs.",
        "start": "2026-02-12T07:30:00",
        "end": "2026-02-12T08:00:00",
        "colorId": "2"  # Green
    },
    {
        "summary": "🐕 Dog Training",
        "description": "Evening session. Discipline transfer + potential content angle.",
        "start": "2026-02-12T17:00:00",
        "end": "2026-02-12T17:30:00",
        "colorId": "2"  # Green
    },
    {
        "summary": "📱 Daily Content Post",
        "description": "Post 1 short-form piece (TikTok/Reels/Shorts).\nRaw > Perfect. Volume negates luck.\n\nIdeas: workout clip, tip, form check, peptide fact.",
        "start": "2026-02-12T20:00:00",
        "end": "2026-02-12T20:30:00",
        "colorId": "9"  # Blue
    },

    # THURSDAY Feb 13 - Daily Habits
    {
        "summary": "💪 Workout",
        "description": "Non-negotiable. Fitness influencer = practice what you preach.\nLog workout for potential content.",
        "start": "2026-02-13T06:00:00",
        "end": "2026-02-13T07:00:00",
        "colorId": "10"  # Green
    },
    {
        "summary": "🇪🇸 Spanish Practice",
        "description": "15-30 min Duolingo or Pimsleur.\n60M+ Hispanic Americans = 2x audience if bilingual.",
        "start": "2026-02-13T07:00:00",
        "end": "2026-02-13T07:30:00",
        "colorId": "2"  # Green
    },
    {
        "summary": "📚 Reading",
        "description": "Business, fitness, or personal development.\nIdeas for content come from inputs.",
        "start": "2026-02-13T07:30:00",
        "end": "2026-02-13T08:00:00",
        "colorId": "2"  # Green
    },
    {
        "summary": "🐕 Dog Training",
        "description": "Evening session. Discipline transfer + potential content angle.",
        "start": "2026-02-13T17:00:00",
        "end": "2026-02-13T17:30:00",
        "colorId": "2"  # Green
    },
    {
        "summary": "📱 Daily Content Post",
        "description": "Post 1 short-form piece (TikTok/Reels/Shorts).\nRaw > Perfect. Volume negates luck.\n\nIdeas: workout clip, tip, form check, peptide fact.",
        "start": "2026-02-13T20:00:00",
        "end": "2026-02-13T20:30:00",
        "colorId": "9"  # Blue
    },

    # FRIDAY Feb 14 - Daily Habits
    {
        "summary": "💪 Workout",
        "description": "Non-negotiable. Fitness influencer = practice what you preach.\nLog workout for potential content.",
        "start": "2026-02-14T06:00:00",
        "end": "2026-02-14T07:00:00",
        "colorId": "10"  # Green
    },
    {
        "summary": "🇪🇸 Spanish Practice",
        "description": "15-30 min Duolingo or Pimsleur.\n60M+ Hispanic Americans = 2x audience if bilingual.",
        "start": "2026-02-14T07:00:00",
        "end": "2026-02-14T07:30:00",
        "colorId": "2"  # Green
    },
    {
        "summary": "📚 Reading",
        "description": "Business, fitness, or personal development.\nIdeas for content come from inputs.",
        "start": "2026-02-14T07:30:00",
        "end": "2026-02-14T08:00:00",
        "colorId": "2"  # Green
    },
    {
        "summary": "🐕 Dog Training",
        "description": "Evening session. Discipline transfer + potential content angle.",
        "start": "2026-02-14T17:00:00",
        "end": "2026-02-14T17:30:00",
        "colorId": "2"  # Green
    },
    {
        "summary": "📱 Daily Content Post",
        "description": "Post 1 short-form piece (TikTok/Reels/Shorts).\nRaw > Perfect. Volume negates luck.\n\nIdeas: workout clip, tip, form check, peptide fact.",
        "start": "2026-02-14T20:00:00",
        "end": "2026-02-14T20:30:00",
        "colorId": "9"  # Blue
    },

    # SATURDAY Feb 15 - Rest Day Habits (lighter)
    {
        "summary": "💪 Active Recovery / Light Workout",
        "description": "Walk, stretch, yoga, or light activity.\nRest is part of training.",
        "start": "2026-02-15T08:00:00",
        "end": "2026-02-15T09:00:00",
        "colorId": "10"  # Green
    },
    {
        "summary": "🐕 Dog Training + Walk",
        "description": "Longer weekend session. Good for both of you.",
        "start": "2026-02-15T10:00:00",
        "end": "2026-02-15T11:00:00",
        "colorId": "2"  # Green
    },

    # SUNDAY Feb 16 - Rest + Prep
    {
        "summary": "📚 Deep Reading / Learning",
        "description": "Longer learning session. Peptide research, business books, etc.",
        "start": "2026-02-16T09:00:00",
        "end": "2026-02-16T10:30:00",
        "colorId": "2"  # Green
    },
    {
        "summary": "📅 Week Prep: Content Batching",
        "description": "Plan and batch content for the week.\n- Write 5-7 short-form hooks\n- Outline 1 long-form video\n- Schedule posts if possible",
        "start": "2026-02-16T14:00:00",
        "end": "2026-02-16T16:00:00",
        "colorId": "9"  # Blue
    },

    # ========================================
    # BUSINESS BLOCKS (Strategic work)
    # ========================================

    # Monday Feb 10
    {
        "summary": "🔴 CRITICAL: Review Fitness Influencer v2.0 OVERHAUL-PLAN",
        "description": """Decision point: Approve for Ralph execution OR scope down.

Action items:
1. Read /projects/marceau-solutions/fitness-influencer/OVERHAUL-PLAN.md
2. Review the 40+ story scope
3. Decide: GO (4-6 weeks Ralph) or adjust scope
4. If GO: Launch Ralph PRD

Business Impact: $60K-120K Year 1 revenue potential""",
        "start": "2026-02-10T09:00:00",
        "end": "2026-02-10T10:30:00",
        "colorId": "11"  # Red
    },
    {
        "summary": "🎬 Content Creation: Film 2-3 Short Clips",
        "description": """Batch film content while energy is high.

Ideas:
- Post-workout tip
- Form demonstration
- Quick peptide fact
- Motivation/mindset

Raw footage is fine - edit later or post raw.""",
        "start": "2026-02-10T11:00:00",
        "end": "2026-02-10T12:00:00",
        "colorId": "9"  # Blue
    },

    # Tuesday Feb 11
    {
        "summary": "🟠 HIGH: Lead Scraper Campaign Analysis",
        "description": """Optimize SMS campaign performance.

Action items:
1. Review CAMPAIGN-PERFORMANCE-BASELINE.md
2. Analyze 9,128 enrolled leads performance
3. Identify winning message templates
4. Plan next segment (HVAC or fitness studios)

SOP: SOP 22 (Campaign Analytics), SOP 23 (Strategy Development)
Potential: $3-5K/month revenue""",
        "start": "2026-02-11T09:00:00",
        "end": "2026-02-11T11:00:00",
        "colorId": "6"  # Orange
    },
    {
        "summary": "🟠 HIGH: TikTok Integration Testing",
        "description": """Test the new TikTok modules implemented Feb 8.

Action items:
1. Test TikTok OAuth flow with real account
2. Upload test video via API
3. Verify scheduling works (TikTokScheduler)
4. Document any issues for Fitness Influencer product

Files: projects/shared/social-media-automation/src/tiktok_*.py
Impact: 10X reach if cross-posting works""",
        "start": "2026-02-11T14:00:00",
        "end": "2026-02-11T16:00:00",
        "colorId": "6"  # Orange
    },

    # Wednesday Feb 12
    {
        "summary": "🟠 HIGH: Personal Training Business Validation",
        "description": """Start validation for peptide-focused personal training.

Action items:
1. Create 5-7 social posts for fitness niche
2. Set up basic website (use website-builder)
3. Draft fitness content strategy
4. Reach out to 3 potential clients

Business model: $50-75/session + Peptide referral $500-1000/client""",
        "start": "2026-02-12T09:00:00",
        "end": "2026-02-12T11:30:00",
        "colorId": "6"  # Orange
    },
    {
        "summary": "🎬 Content Creation: Medium-Form Content",
        "description": """Create 1-2 longer pieces (3-5 min).

Ideas:
- Full workout walkthrough
- Peptide basics explainer
- Client transformation story
- Q&A from DMs

Can be YouTube Short or full video.""",
        "start": "2026-02-12T14:00:00",
        "end": "2026-02-12T15:30:00",
        "colorId": "9"  # Blue
    },

    # Thursday Feb 13 - BATCH CONTENT DAY
    {
        "summary": "🎬 BATCH DAY: Long-Form YouTube Production",
        "description": """Dedicated content production block.

Create 1 polished YouTube video OR batch multiple shorts.

Structure:
1. Script/outline (30 min)
2. Film (1 hr)
3. Edit (1.5 hr)

Topic ideas:
- Peptide deep-dive
- Weekly workout routine
- Nutrition protocol
- "Day in the life" fitness""",
        "start": "2026-02-13T09:00:00",
        "end": "2026-02-13T12:00:00",
        "colorId": "9"  # Blue
    },
    {
        "summary": "📊 Lead Scraper: Execute Follow-up Sequence",
        "description": """Run follow-up sequence on best performers.

Action items:
1. Identify leads that responded positively
2. Run SOP 19 (Multi-Touch Follow-Up)
3. Move hot leads to ClickUp CRM
4. Schedule callbacks

Tools: python -m src.follow_up_sequence process-due""",
        "start": "2026-02-13T14:00:00",
        "end": "2026-02-13T15:30:00",
        "colorId": "7"  # Cyan
    },

    # Friday Feb 14
    {
        "summary": "📋 Fitness Influencer: Ralph Progress Checkpoint",
        "description": """If Ralph running, review progress.

Action items:
1. Check completed stories in Ralph execution
2. Review any checkpoint approvals needed
3. Adjust scope if blockers found
4. Plan next week's execution

If not running: Launch Ralph today""",
        "start": "2026-02-14T09:00:00",
        "end": "2026-02-14T10:00:00",
        "colorId": "7"  # Cyan
    },
    {
        "summary": "🎬 Content Review: Publish Best of Week",
        "description": """Review week's content and publish best pieces.

Actions:
1. Review all filmed content
2. Quick edits on top 2-3 pieces
3. Schedule for optimal posting times
4. Cross-post to all platforms

Friday afternoon = high engagement time.""",
        "start": "2026-02-14T10:30:00",
        "end": "2026-02-14T12:00:00",
        "colorId": "9"  # Blue
    },
    {
        "summary": "📅 Weekly Planning: Review & Adjust",
        "description": """End of week planning session.

Action items:
1. Review content performance (what got engagement?)
2. Document wins and learnings
3. Update docs/session-history.md
4. Plan next week's content themes
5. Adjust strategy based on data

Prepare for: Week 2 with more data""",
        "start": "2026-02-14T14:00:00",
        "end": "2026-02-14T15:00:00",
        "colorId": "3"  # Purple
    },
]


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
    print("Creating time blocks for week of Feb 10, 2026...")
    print("Philosophy: Volume > Perfection | Daily habits compound")
    print("=" * 60)

    service = get_calendar_service()
    if not service:
        print("Failed to authenticate with Google Calendar")
        return

    created_count = 0
    for block in TIME_BLOCKS:
        try:
            event = create_time_block(service, block)
            print(f"✅ Created: {block['summary'][:50]}...")
            print(f"   Time: {block['start']} - {block['end'].split('T')[1]}")
            created_count += 1
        except Exception as e:
            print(f"❌ Failed: {block['summary'][:50]}...")
            print(f"   Error: {e}")

    print("=" * 60)
    print(f"Created {created_count}/{len(TIME_BLOCKS)} time blocks")
    print("\n📊 WEEKLY SUMMARY:")
    print("\nDAILY HABITS (Mon-Fri):")
    print("  6:00-7:00  💪 Workout")
    print("  7:00-7:30  🇪🇸 Spanish")
    print("  7:30-8:00  📚 Reading")
    print("  5:00-5:30  🐕 Dog Training")
    print("  8:00-8:30  📱 Daily Content Post")
    print("\nCONTENT BLOCKS:")
    print("  Mon 11-12  🎬 Film 2-3 clips")
    print("  Wed 2-3:30 🎬 Medium-form content")
    print("  Thu 9-12   🎬 BATCH DAY: Long-form YouTube")
    print("  Fri 10:30  🎬 Publish best of week")
    print("  Sun 2-4    📅 Week prep + batch planning")
    print("\nBUSINESS BLOCKS:")
    print("  Mon 9-10:30  🔴 Fitness v2.0 Decision")
    print("  Tue 9-11     🟠 Lead Scraper Analysis")
    print("  Tue 2-4      🟠 TikTok Testing")
    print("  Wed 9-11:30  🟠 PT Validation")
    print("  Thu 2-3:30   📊 Follow-up Sequence")
    print("  Fri 9-10     📋 Ralph Checkpoint")
    print("  Fri 2-3      📅 Weekly Planning")


if __name__ == '__main__':
    main()
