#!/usr/bin/env python3
"""
Create time blocks for the week based on business priorities.
Uses Google Calendar API.
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
# Based on business priority research
TIME_BLOCKS = [
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
        "summary": "🔴 CRITICAL: 7-Figure Funding Meeting Follow-up",
        "description": """Follow up from funding meeting.

Action items:
1. Did the meeting happen? Document outcome
2. If approved: Schedule 2-4 week validation timeline
3. If denied: Assess alternatives (bootstrap, revenue-based)
4. Update FINANCIAL-PROJECTION-36-MONTH.md with decisions

Files: 7-FIGURE-FUNDING-MEETING-PREP.md, BUSINESS-VIABILITY-TESTING-PLAN.md""",
        "start": "2026-02-10T11:00:00",
        "end": "2026-02-10T12:00:00",
        "colorId": "11"  # Red
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
3. Research ISSA CPT certification timeline ($948)
4. Draft fitness content strategy

Business model: $50-75/session + Peptide referral $500-1000/client
Startup cost: $1,900 minimal""",
        "start": "2026-02-12T09:00:00",
        "end": "2026-02-12T11:30:00",
        "colorId": "6"  # Orange
    },
    {
        "summary": "🟡 MEDIUM: n8n Agent Orchestrator Health Check",
        "description": """Verify n8n automation infrastructure.

Action items:
1. SSH to EC2: http://34.193.98.97:5678
2. Check Agent Orchestrator v4.8 status
3. Verify webhook handlers working
4. Review Python Bridge API logs

Files: execution/agent_bridge_api.py, n8n-workflows/""",
        "start": "2026-02-12T14:00:00",
        "end": "2026-02-12T15:00:00",
        "colorId": "5"  # Yellow
    },

    # Thursday Feb 13
    {
        "summary": "🟡 MEDIUM: MCP Publishing Pipeline (Top 3)",
        "description": """Publish highest-value MCPs to registry.

Priority order:
1. fitness-influencer-mcp (your main product)
2. Already done: canva, instagram, ticket-discovery, tiktok
3. Consider: trainerize-mcp for fitness business

SOP: SOP 11-14 (MCP Publishing workflow)
Alternative: Launch Ralph with prd-mcp-publishing-all.json""",
        "start": "2026-02-13T09:00:00",
        "end": "2026-02-13T12:00:00",
        "colorId": "5"  # Yellow
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
        "summary": "📱 Personal Training: First Content Publish",
        "description": """Publish Week 1 fitness content.

Content ideas:
- Nutrition tip (protein timing, peptide info)
- Form check video
- Client success story (if available)
- Fitness myth debunk

Monitor early engagement for validation signals.""",
        "start": "2026-02-14T10:30:00",
        "end": "2026-02-14T11:30:00",
        "colorId": "7"  # Cyan
    },
    {
        "summary": "📅 Weekly Planning: Review & Adjust",
        "description": """End of week planning session.

Action items:
1. Document decisions made this week
2. Update docs/session-history.md
3. Review what moved the needle
4. Adjust next week priorities
5. Check DOCKET.md for triggered items

Prepare for: Week 2 execution""",
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
    print("=" * 50)

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

    print("=" * 50)
    print(f"Created {created_count}/{len(TIME_BLOCKS)} time blocks")
    print("\nTime blocks scheduled:")
    print("- Monday: Fitness v2.0 Decision, Funding Follow-up")
    print("- Tuesday: Lead Scraper Analysis, TikTok Testing")
    print("- Wednesday: Personal Training Validation, n8n Health Check")
    print("- Thursday: MCP Publishing, Follow-up Sequence")
    print("- Friday: Ralph Checkpoint, Content Publish, Weekly Planning")


if __name__ == '__main__':
    main()
