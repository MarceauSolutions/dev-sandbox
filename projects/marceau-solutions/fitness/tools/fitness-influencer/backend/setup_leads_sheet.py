#!/usr/bin/env python3
"""
Setup Google Sheets for Lead Storage
Creates a new sheet with proper headers for the lead capture form.
"""

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from pathlib import Path
import json

def create_leads_sheet():
    """Create a Google Sheet for storing leads with proper formatting."""

    # Load credentials
    token_path = Path(__file__).parent / "token.json"

    if not token_path.exists():
        print("❌ Error: token.json not found. Please run calendar_reminders.py first to authenticate.")
        return None

    creds = Credentials.from_authorized_user_file(str(token_path))

    # Build services
    sheets_service = build('sheets', 'v4', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    # Create new spreadsheet
    spreadsheet = {
        'properties': {
            'title': 'Marceau Solutions - Lead Captures'
        },
        'sheets': [
            {
                'properties': {
                    'title': 'Leads',
                    'gridProperties': {
                        'frozenRowCount': 1
                    }
                }
            }
        ]
    }

    result = sheets_service.spreadsheets().create(body=spreadsheet).execute()
    spreadsheet_id = result['spreadsheetId']

    print(f"✅ Created Google Sheet: {result['properties']['title']}")
    print(f"   Sheet ID: {spreadsheet_id}")
    print(f"   URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")

    # Add headers
    headers = [
        'Timestamp',
        'First Name',
        'Last Name',
        'Business Name',
        'Email',
        'Phone',
        'Project Description',
        'SMS Opt-In',
        'Email Opt-In',
        'Source',
        'Status',
        'Notes'
    ]

    # Format header row
    requests = [
        # Set header values
        {
            'updateCells': {
                'rows': [
                    {
                        'values': [
                            {
                                'userEnteredValue': {'stringValue': header},
                                'userEnteredFormat': {
                                    'backgroundColor': {'red': 1.0, 'green': 0.84, 'blue': 0.0},  # Gold
                                    'textFormat': {
                                        'bold': True,
                                        'fontSize': 11
                                    },
                                    'horizontalAlignment': 'CENTER'
                                }
                            } for header in headers
                        ]
                    }
                ],
                'fields': 'userEnteredValue,userEnteredFormat',
                'start': {'sheetId': 0, 'rowIndex': 0, 'columnIndex': 0}
            }
        },
        # Auto-resize columns
        {
            'autoResizeDimensions': {
                'dimensions': {
                    'sheetId': 0,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': len(headers)
                }
            }
        },
        # Set column widths
        {
            'updateDimensionProperties': {
                'range': {
                    'sheetId': 0,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': 1
                },
                'properties': {
                    'pixelSize': 180  # Timestamp column
                },
                'fields': 'pixelSize'
            }
        },
        {
            'updateDimensionProperties': {
                'range': {
                    'sheetId': 0,
                    'dimension': 'COLUMNS',
                    'startIndex': 6,
                    'endIndex': 7
                },
                'properties': {
                    'pixelSize': 300  # Project Description column
                },
                'fields': 'pixelSize'
            }
        }
    ]

    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()

    print("✅ Formatted header row with gold background")

    # Share with yourself (make sure you have access)
    # This ensures the sheet is accessible
    print("\n📊 Google Sheet Setup Complete!")
    print(f"\n🔑 Add this to Railway environment variables:")
    print(f"   LEADS_SHEET_ID={spreadsheet_id}")

    # Save to a local file for easy reference
    config_file = Path(__file__).parent / "sheet_config.json"
    with open(config_file, 'w') as f:
        json.dump({
            'spreadsheet_id': spreadsheet_id,
            'spreadsheet_url': f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}",
            'sheet_name': 'Leads'
        }, f, indent=2)

    print(f"\n💾 Configuration saved to: {config_file}")

    return spreadsheet_id

if __name__ == "__main__":
    print("="*70)
    print("MARCEAU SOLUTIONS - LEAD STORAGE SETUP")
    print("="*70)
    print("\nCreating Google Sheet for lead capture...\n")

    sheet_id = create_leads_sheet()

    if sheet_id:
        print("\n" + "="*70)
        print("✅ SUCCESS - Your lead storage is ready!")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("❌ FAILED - Please check errors above")
        print("="*70)
