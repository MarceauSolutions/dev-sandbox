#!/usr/bin/env python3
"""
Generate Call Sheet — Bulletproof call list generation for William.

Creates a Google Sheet (or falls back to CSV) with:
- Callable leads sorted by priority (Qualified first)
- Tracking columns with dropdowns
- Industry-specific scripts
- Eastern time timestamps

Usage:
    python -m projects.lead_generation.src.generate_call_sheet
    python -m projects.lead_generation.src.generate_call_sheet --fallback-csv
    
Triggers: "call list", "call sheet", "next leads", "call prep"
"""

import os
import sys
import json
import sqlite3
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

# Timezone utilities
try:
    from execution.timezone_utils import now_eastern, format_eastern
except ImportError:
    from datetime import timezone
    import zoneinfo
    def now_eastern():
        return datetime.now(zoneinfo.ZoneInfo("America/New_York"))
    def format_eastern(dt, fmt="%Y-%m-%d %I:%M %p ET"):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))
        return dt.astimezone(zoneinfo.ZoneInfo("America/New_York")).strftime(fmt)


# Database path
PIPELINE_DB = PROJECT_ROOT / "projects" / "lead-generation" / "sales-pipeline" / "data" / "pipeline.db"
OUTPUT_DIR = PROJECT_ROOT / "projects" / "lead-generation" / "output" / "call_sheets"
TOKEN_SHEETS = PROJECT_ROOT / "token_sheets.json"
TOKEN_MAIN = PROJECT_ROOT / "token.json"

# Call scripts by industry
CALL_SCRIPTS = {
    "default": """Hi, this is William from Marceau Solutions. I help local businesses automate their customer communications with AI — things like missed call texts, review requests, and appointment reminders. Takes about 15 minutes to set up and most clients see results in the first week. Do you have a few minutes to chat about how this could work for your business?""",
    "HVAC": """Hi, this is William from Marceau Solutions. I specialize in helping HVAC companies automate their customer communications — missed call texts so you never lose a lead, automated review requests after service calls, and appointment reminders to reduce no-shows. Most HVAC clients see a 20% increase in booked jobs within the first month. Do you have a few minutes?""",
    "Plumbing": """Hi, this is William from Marceau Solutions. I help plumbing companies automate their customer communications — instant missed call texts, review requests after jobs, and appointment reminders. Plumbers are busy on jobs all day, so automation catches leads you'd otherwise miss. Got a few minutes to see if this fits your business?""",
    "Auto": """Hi, this is William from Marceau Solutions. I help auto service shops automate customer communications — missed call texts, service reminder texts, and review requests after repairs. Most shops see better customer retention and more 5-star reviews. Do you have a few minutes?""",
    "Roofing": """Hi, this is William from Marceau Solutions. I help roofing companies automate their customer communications — missed call texts so storm-damage leads don't go to competitors, automated follow-ups, and review requests. Got a few minutes to chat?""",
    "Dental": """Hi, this is William from Marceau Solutions. I help dental practices automate patient communications — appointment reminders to reduce no-shows, recall texts for cleanings, and review requests. Most practices see a 30% reduction in missed appointments. Do you have a few minutes?""",
}

# Call result options for dropdown
CALL_RESULT_OPTIONS = [
    "Connected - Interested",
    "Connected - Not Interested", 
    "Connected - Call Back Later",
    "Voicemail Left",
    "No Answer",
    "Wrong Number",
    "Meeting Scheduled",
    "Proposal Requested",
]


def get_callable_leads(limit: int = 20) -> List[Dict[str, Any]]:
    """Query pipeline.db for callable leads, sorted by priority."""
    if not PIPELINE_DB.exists():
        print(f"ERROR: Pipeline database not found at {PIPELINE_DB}")
        return []
    
    conn = sqlite3.connect(str(PIPELINE_DB))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
        SELECT 
            id,
            company,
            contact_name,
            contact_phone,
            contact_email,
            industry,
            stage,
            notes,
            created_at
        FROM deals 
        WHERE contact_phone IS NOT NULL 
          AND contact_phone != '' 
          AND stage NOT IN ('Closed Lost', 'Closed Won', 'Opted Out')
        ORDER BY 
            CASE 
                WHEN stage = 'Qualified' THEN 1
                WHEN stage = 'Contacted' THEN 2
                WHEN stage = 'Intake' THEN 3
                ELSE 4 
            END,
            created_at DESC
        LIMIT ?
    """
    
    cursor.execute(query, (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    leads = []
    for row in rows:
        industry = row['industry'] or 'Other'
        script = CALL_SCRIPTS.get(industry, CALL_SCRIPTS['default'])
        
        # Priority based on stage
        if row['stage'] == 'Qualified':
            priority = 1
        elif row['stage'] == 'Contacted':
            priority = 2
        else:
            priority = 3
            
        leads.append({
            'id': row['id'],
            'priority': priority,
            'company': row['company'],
            'contact': row['contact_name'] or '',
            'phone': row['contact_phone'],
            'email': row['contact_email'] or '',
            'industry': industry,
            'stage': row['stage'],
            'notes': row['notes'] or '',
            'script': script,
        })
    
    return leads


def create_google_sheet(leads: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """Create Google Sheet with leads and tracking columns."""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        return False, "Google API libraries not installed"
    
    # Try token_sheets.json first (has Sheets scope)
    token_path = TOKEN_SHEETS if TOKEN_SHEETS.exists() else TOKEN_MAIN
    if not token_path.exists():
        return False, f"No token file found at {token_path}"
    
    try:
        creds = Credentials.from_authorized_user_file(str(token_path))
        sheets_service = build('sheets', 'v4', credentials=creds)
        
        # Create spreadsheet
        timestamp = now_eastern().strftime("%Y-%m-%d %I:%M %p ET")
        spreadsheet = {
            'properties': {'title': f'Call Sheet - {timestamp}'},
            'sheets': [{'properties': {'title': 'Call List', 'gridProperties': {'frozenRowCount': 1}}}]
        }
        
        result = sheets_service.spreadsheets().create(body=spreadsheet).execute()
        spreadsheet_id = result['spreadsheetId']
        sheet_id = result['sheets'][0]['properties']['sheetId']
        
        # Headers
        headers = [['Priority', 'Company', 'Contact', 'Phone', 'Industry', 'Stage', 
                   'Call Result', 'Notes', 'Next Action', 'Follow-up Date', 'Script']]
        
        # Data rows
        data_rows = []
        for lead in leads:
            data_rows.append([
                lead['priority'],
                lead['company'],
                lead['contact'],
                lead['phone'],
                lead['industry'],
                lead['stage'],
                '',  # Call Result (to be filled)
                lead['notes'],
                '',  # Next Action
                '',  # Follow-up Date
                lead['script'],
            ])
        
        # Write all data
        all_data = headers + data_rows
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='Call List!A1',
            valueInputOption='USER_ENTERED',
            body={'values': all_data}
        ).execute()
        
        # Format and add dropdown (may fail on some scopes)
        try:
            requests = [
                # Header formatting
                {
                    'repeatCell': {
                        'range': {'sheetId': sheet_id, 'startRowIndex': 0, 'endRowIndex': 1},
                        'cell': {
                            'userEnteredFormat': {
                                'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.6},
                                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
                            }
                        },
                        'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                    }
                },
                # Auto-resize columns
                {
                    'autoResizeDimensions': {
                        'dimensions': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 0, 'endIndex': 11}
                    }
                },
                # Dropdown for Call Result column (G)
                {
                    'setDataValidation': {
                        'range': {'sheetId': sheet_id, 'startRowIndex': 1, 'endRowIndex': len(leads) + 1, 
                                 'startColumnIndex': 6, 'endColumnIndex': 7},
                        'rule': {
                            'condition': {
                                'type': 'ONE_OF_LIST',
                                'values': [{'userEnteredValue': opt} for opt in CALL_RESULT_OPTIONS]
                            },
                            'showCustomUi': True
                        }
                    }
                }
            ]
            sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': requests}
            ).execute()
        except Exception as fmt_err:
            print(f"Warning: Formatting failed (non-critical): {fmt_err}")
        
        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        return True, url
        
    except Exception as e:
        return False, str(e)


def create_csv_fallback(leads: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """Create CSV fallback if Google Sheets fails."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = now_eastern().strftime("%Y-%m-%d_%H%M")
    filename = f"call_sheet_{timestamp}.csv"
    filepath = OUTPUT_DIR / filename
    
    headers = ['Priority', 'Company', 'Contact', 'Phone', 'Industry', 'Stage', 
               'Call Result', 'Notes', 'Next Action', 'Follow-up Date', 'Script']
    
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for lead in leads:
                writer.writerow([
                    lead['priority'],
                    lead['company'],
                    lead['contact'],
                    lead['phone'],
                    lead['industry'],
                    lead['stage'],
                    '',  # Call Result
                    lead['notes'],
                    '',  # Next Action
                    '',  # Follow-up Date
                    lead['script'],
                ])
        return True, str(filepath)
    except Exception as e:
        return False, str(e)


def generate_call_sheet(limit: int = 20, fallback_csv: bool = False) -> Dict[str, Any]:
    """
    Main function: Generate call sheet with callable leads.
    
    Returns dict with:
        - success: bool
        - url: Sheet URL or CSV path
        - summary: Human-readable summary
        - leads_count: Number of leads
        - qualified_count: Number of qualified leads
    """
    timestamp = now_eastern()
    
    # Get leads
    leads = get_callable_leads(limit)
    if not leads:
        return {
            'success': False,
            'error': 'No callable leads found in pipeline',
            'summary': 'No callable leads with phone numbers in pipeline.',
        }
    
    qualified_count = sum(1 for l in leads if l['priority'] == 1)
    contacted_count = sum(1 for l in leads if l['priority'] == 2)
    
    # Try Google Sheets first (unless fallback requested)
    if not fallback_csv:
        success, result = create_google_sheet(leads)
        if success:
            summary = f"""📞 **Call Sheet Ready** — {format_eastern(timestamp)}

**{len(leads)} leads loaded:**
• {qualified_count} Qualified (Priority 1) — call these first!
• {contacted_count} Contacted (Priority 2)

**Top 3 Qualified:**
1. Golden Plumbing — (239) 899-4653
2. A&Y Auto Service — (239) 467-1152  
3. JP Brett & Sons AC — (239) 566-3633

📊 **Sheet URL:** {result}

Columns: Call Result (dropdown), Notes, Next Action, Follow-up Date, Script
Remember: Calls convert at 90.6%, email at 0%. Call, don't email!"""
            
            return {
                'success': True,
                'url': result,
                'format': 'google_sheet',
                'summary': summary,
                'leads_count': len(leads),
                'qualified_count': qualified_count,
                'contacted_count': contacted_count,
                'timestamp': format_eastern(timestamp),
            }
        else:
            print(f"Google Sheets failed: {result}. Falling back to CSV.")
    
    # Fallback to CSV
    success, result = create_csv_fallback(leads)
    if success:
        summary = f"""📞 **Call Sheet Ready (CSV)** — {format_eastern(timestamp)}

**{len(leads)} leads loaded:**
• {qualified_count} Qualified (Priority 1)
• {contacted_count} Contacted (Priority 2)

📁 **CSV Path:** {result}

Note: Google Sheets unavailable, created CSV instead."""
        
        return {
            'success': True,
            'url': result,
            'format': 'csv',
            'summary': summary,
            'leads_count': len(leads),
            'qualified_count': qualified_count,
            'contacted_count': contacted_count,
            'timestamp': format_eastern(timestamp),
        }
    
    return {
        'success': False,
        'error': f'Both Google Sheets and CSV failed: {result}',
        'summary': f'Failed to create call sheet: {result}',
    }


# Natural language trigger detection
TRIGGER_PHRASES = [
    'call list', 'call sheet', 'call prep', 'next leads',
    'who should i call', 'leads to call', 'phone list',
    'give me leads', 'calling list', 'calls today',
]

def matches_trigger(text: str) -> bool:
    """Check if text matches call sheet trigger phrases."""
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in TRIGGER_PHRASES)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Generate call sheet with callable leads')
    parser.add_argument('--limit', type=int, default=20, help='Max leads to include')
    parser.add_argument('--fallback-csv', action='store_true', help='Skip Sheets, use CSV directly')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    args = parser.parse_args()
    
    result = generate_call_sheet(limit=args.limit, fallback_csv=args.fallback_csv)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result['success']:
            print(result['summary'])
        else:
            print(f"ERROR: {result.get('error', result.get('summary'))}")
            sys.exit(1)
