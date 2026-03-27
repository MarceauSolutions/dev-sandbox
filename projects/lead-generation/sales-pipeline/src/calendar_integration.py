"""
Google Calendar Integration for Time-Blocking Daily Tasks

Automatically creates calendar events for today's calls, visits, and email blocks
based on pipeline data. Uses Google Calendar API.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from .models import get_db

SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = 'primary'  # Use primary calendar

def get_calendar_service():
    """Get authenticated Google Calendar service."""
    creds = None
    token_path = Path(__file__).parent.parent / "data" / "calendar_token.json"
    creds_path = Path(__file__).parent.parent / "data" / "calendar_credentials.json"

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                raise FileNotFoundError("calendar_credentials.json not found. Download from Google Cloud Console.")
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)

def create_daily_schedule():
    """Create time-blocked calendar events for today's tasks."""
    from .orchestrator.config import DAILY_SCHEDULE_BLOCKS
    from .generate_lead_lists import get_tier_1_phone_leads, get_tier_2_phone_leads, get_email_leads, get_inperson_leads
    from .pitch_briefer import _generate_call_brief

    today = datetime.now().strftime("%Y-%m-%d")

    # Get today's tasks from generate_lead_lists
    t1_calls = get_tier_1_phone_leads(10)
    t2_calls = get_tier_2_phone_leads(10)
    emails = get_email_leads(10)
    visits = get_inperson_leads(5)

    service = get_calendar_service()

    # Clear existing events for today
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=f"{today}T00:00:00Z",
        timeMax=f"{today}T23:59:59Z",
        singleEvents=True,
        q="AI Sales Pipeline"
    ).execute()

    for event in events_result.get('items', []):
        service.events().delete(calendarId=CALENDAR_ID, eventId=event['id']).execute()

    # Create call block
    call_block = DAILY_SCHEDULE_BLOCKS.get('call_block', {'start': '09:00', 'end': '11:00', 'timezone': 'America/New_York'})
    if t1_calls or t2_calls:
        call_descriptions = []
        all_calls = t1_calls + t2_calls
        for call in all_calls[:8]:  # Top 8
            desc = f"{call['company']} - {call.get('contact_name', 'Unknown')}"
            if call.get('contact_phone'):
                desc += f" ({call['contact_phone']})"
            call_descriptions.append(desc)

        # Generate personalized script for top call
        script = ""
        if all_calls:
            brief = _generate_call_brief(all_calls[0])
            script = f"\n\nSCRIPT FOR {all_calls[0]['company'].upper()}:\n{brief.get('talking_points', '')}\n\nQUESTIONS:\n{brief.get('questions_to_ask', '')}"

        event = {
            'summary': f'AI Sales: Call Block ({len(call_descriptions)} calls)',
            'description': "I help businesses eliminate the lead fragmentation that happens when conversational AI agents and missed-call follow-up tools don't talk to each other. We built the only AI automation platform that integrates everything you already have into one seamless system that captures every lead, routes it properly, follows up automatically, and manages the entire sales process all the way to closing — without jumping between five different tools.\n\n" + "\n".join(call_descriptions) + script,
            'start': {'dateTime': f"{today}T{call_block['start']}:00", 'timeZone': call_block['timezone']},
            'end': {'dateTime': f"{today}T{call_block['end']}:00", 'timeZone': call_block['timezone']},
            'location': 'Phone',
        }
        created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()

        # Log to database
        conn = get_db()
        conn.execute("""
            INSERT INTO calendar_events (event_id, title, start_time, end_time, description)
            VALUES (?, ?, ?, ?, ?)
        """, (created_event['id'], event['summary'], event['start']['dateTime'], event['end']['dateTime'], event['description']))
        conn.commit()
        conn.close()

    # Create visit block
    visit_block = DAILY_SCHEDULE_BLOCKS.get('visit_block', {'start': '11:00', 'end': '13:00', 'timezone': 'America/New_York'})
    if visits:
        visit_descriptions = []
        for visit in visits[:4]:  # Top 4
            desc = f"{visit['company']} - {visit.get('contact_name', 'Unknown')}"
            if visit.get('contact_phone'):
                desc += f" ({visit['contact_phone']})"
            visit_descriptions.append(desc)

        event = {
            'summary': f'AI Sales: In-Person Visits ({len(visit_descriptions)} visits)',
            'description': "I help businesses eliminate the lead fragmentation that happens when conversational AI agents and missed-call follow-up tools don't talk to each other. We built the only AI automation platform that integrates everything you already have into one seamless system that captures every lead, routes it properly, follows up automatically, and manages the entire sales process all the way to closing — without jumping between five different tools.\n\n" + "\n".join(visit_descriptions),
            'start': {'dateTime': f"{today}T{visit_block['start']}:00", 'timeZone': visit_block['timezone']},
            'end': {'dateTime': f"{today}T{visit_block['end']}:00", 'timeZone': visit_block['timezone']},
            'location': 'Naples, FL',
        }
        created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()

        conn = get_db()
        conn.execute("""
            INSERT INTO calendar_events (event_id, title, start_time, end_time, description, location)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (created_event['id'], event['summary'], event['start']['dateTime'], event['end']['dateTime'], event['description'], event['location']))
        conn.commit()
        conn.close()

    # Create email block
    email_block = DAILY_SCHEDULE_BLOCKS.get('email_block', {'start': '13:00', 'end': '14:00', 'timezone': 'America/New_York'})
    if emails:
        email_descriptions = []
        for email in emails[:6]:  # Top 6
            desc = f"{email['company']} - {email.get('contact_email', 'No email')}"
            email_descriptions.append(desc)

        event = {
            'summary': f'AI Sales: Email Block ({len(email_descriptions)} emails)',
            'description': "I help businesses eliminate the lead fragmentation that happens when conversational AI agents and missed-call follow-up tools don't talk to each other. We built the only AI automation platform that integrates everything you already have into one seamless system that captures every lead, routes it properly, follows up automatically, and manages the entire sales process all the way to closing — without jumping between five different tools.\n\n" + "\n".join(email_descriptions),
            'start': {'dateTime': f"{today}T{email_block['start']}:00", 'timeZone': email_block['timezone']},
            'end': {'dateTime': f"{today}T{email_block['end']}:00", 'timeZone': email_block['timezone']},
            'location': 'Email',
        }
        created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()

        conn = get_db()
        conn.execute("""
            INSERT INTO calendar_events (event_id, title, start_time, end_time, description)
            VALUES (?, ?, ?, ?, ?)
        """, (created_event['id'], event['summary'], event['start']['dateTime'], event['end']['dateTime'], event['description']))
        conn.commit()
        conn.close()

def get_todays_schedule():
    """Get today's calendar events for command center."""
    service = get_calendar_service()
    today = datetime.now().strftime("%Y-%m-%d")

    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=f"{today}T00:00:00Z",
        timeMax=f"{today}T23:59:59Z",
        singleEvents=True,
        q="AI Sales Pipeline"
    ).execute()

    return events_result.get('items', [])