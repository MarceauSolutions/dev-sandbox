#!/usr/bin/env python3
"""
Sync Call Outcomes — pulls William's call results from Google Sheet
and updates pipeline.db with correct stages, outreach logs, and follow-ups.

Usage:
    python -m src.sync_call_outcomes              # Sync and update pipeline
    python -m src.sync_call_outcomes --dry-run    # Preview changes only
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent.parent.parent / ".env")
except ImportError:
    pass

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

DB_PATH = str(Path(__file__).parent.parent / "data" / "pipeline.db")
SPREADSHEET_ID = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')

# Map call outcomes to pipeline stages and actions
OUTCOME_MAP = {
    'Interested': {
        'stage': 'Qualified',
        'next_action': 'Send proposal/info email',
        'days_until_followup': 2,
    },
    'Not Interested': {
        'stage': 'Closed Lost',
        'next_action': None,
        'days_until_followup': None,
    },
    'Voicemail': {
        'stage': 'Contacted',
        'next_action': 'Follow-up call (left voicemail)',
        'days_until_followup': 3,
    },
    'No Answer': {
        'stage': 'Contacted',
        'next_action': 'Try calling again',
        'days_until_followup': 2,
    },
    'Callback Requested': {
        'stage': 'Qualified',
        'next_action': 'Call back as requested',
        'days_until_followup': 1,
    },
    'Meeting Booked': {
        'stage': 'Meeting Booked',
        'next_action': 'Prepare for meeting',
        'days_until_followup': 0,
    },
    'Wrong Number': {
        'stage': 'Closed Lost',
        'next_action': None,
        'days_until_followup': None,
    },
    'Gatekeeper': {
        'stage': 'Contacted',
        'next_action': 'Try again — get past gatekeeper',
        'days_until_followup': 2,
    },
    'Already Has Solution': {
        'stage': 'Closed Lost',
        'next_action': None,
        'days_until_followup': None,
    },
}


def get_sheet_data(sheet_name: str = None) -> list:
    """Pull call outcomes from Google Sheet."""
    creds = Credentials.from_authorized_user_file(
        str(Path(__file__).parent.parent.parent.parent.parent / "token.json")
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    sheets = build('sheets', 'v4', credentials=creds)

    if not sheet_name:
        sheet_name = f"Call List {datetime.now().strftime('%Y-%m-%d')}"

    result = sheets.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"'{sheet_name}'!A2:Q100"
    ).execute()

    rows = result.get('values', [])
    outcomes = []
    for row in rows:
        if len(row) < 13:
            continue
        outcome = (row[12] if len(row) > 12 else '').strip()
        if not outcome:
            continue

        outcomes.append({
            'row_num': row[0] if row else '',
            'company': row[2] if len(row) > 2 else '',
            'contact_name': row[3] if len(row) > 3 else '',
            'phone': row[4] if len(row) > 4 else '',
            'outcome': outcome,
            'spoke_with': row[13] if len(row) > 13 else '',
            'notes': row[14] if len(row) > 14 else '',
            'next_step': row[15] if len(row) > 15 else '',
            'followup_date': row[16] if len(row) > 16 else '',
        })

    return outcomes


def sync_outcomes(dry_run: bool = False, sheet_name: str = None):
    """Pull outcomes from sheet and update pipeline."""
    outcomes = get_sheet_data(sheet_name)

    if not outcomes:
        print("No call outcomes found in sheet. Fill in column M (Call Outcome) and re-run.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')

    print(f"Found {len(outcomes)} call outcomes to process:")
    updated = 0
    logged = 0

    for o in outcomes:
        company = o['company']
        outcome = o['outcome']
        mapping = OUTCOME_MAP.get(outcome)

        if not mapping:
            print(f"  SKIP: {company} — unknown outcome '{outcome}'")
            continue

        # Find deal
        deal = conn.execute(
            "SELECT id, stage FROM deals WHERE company = ?", (company,)
        ).fetchone()
        if not deal:
            deal = conn.execute(
                "SELECT id, stage FROM deals WHERE company LIKE ?", (f"%{company}%",)
            ).fetchone()
        if not deal:
            print(f"  SKIP: {company} — not found in pipeline")
            continue

        deal_id = deal['id']
        new_stage = mapping['stage']
        next_action = o['next_step'] if o['next_step'] else mapping['next_action']

        # Calculate follow-up date
        followup_date = None
        if o['followup_date']:
            followup_date = o['followup_date']
        elif mapping['days_until_followup'] is not None:
            followup_date = (now + timedelta(days=mapping['days_until_followup'])).strftime('%Y-%m-%d')

        # Build outreach log entry
        summary = f"Cold call"
        if o['spoke_with']:
            summary += f" — spoke with {o['spoke_with']}"
        if o['notes']:
            summary += f". {o['notes'][:100]}"

        print(f"  {'DRY ' if dry_run else ''}{company}:")
        print(f"    Outcome: {outcome} -> Stage: {new_stage}")
        if next_action:
            print(f"    Next: {next_action} (due {followup_date})")
        if o['notes']:
            print(f"    Notes: {o['notes'][:60]}")

        if not dry_run:
            # Update deal stage and next action
            conn.execute("""
                UPDATE deals SET stage = ?, next_action = ?, next_action_date = ?,
                    contact_name = CASE WHEN ? != '' THEN ? ELSE contact_name END
                WHERE id = ?
            """, (new_stage, next_action, followup_date,
                  o['spoke_with'], o['spoke_with'], deal_id))
            updated += 1

            # Log to outreach_log
            conn.execute("""
                INSERT INTO outreach_log (deal_id, company, contact, channel, message_summary, response, follow_up_date, created_at, tower)
                VALUES (?, ?, ?, 'Call', ?, ?, ?, ?, 'digital-ai-services')
            """, (deal_id, company, o['spoke_with'] or o['contact_name'],
                  summary, outcome, followup_date, f"{today} {now.strftime('%H:%M:%S')}"))
            logged += 1

    if not dry_run:
        conn.commit()

    conn.close()
    print(f"\nDone: {updated} deals updated, {logged} outreach records logged")

    # Auto-log accountability outcomes
    if not dry_run and logged > 0:
        try:
            from .accountability_tracker import auto_log_call_outcomes
            auto_log_call_outcomes()
        except Exception as e:
            print(f"Warning: Failed to auto-log accountability: {e}")


if __name__ == "__main__":
    import sys
    dry = '--dry-run' in sys.argv
    sheet = None
    for arg in sys.argv[1:]:
        if arg.startswith('--sheet='):
            sheet = arg.split('=', 1)[1]

    sync_outcomes(dry_run=dry, sheet_name=sheet)
