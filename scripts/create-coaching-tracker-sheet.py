#!/usr/bin/env python3
"""
create-coaching-tracker-sheet.py - Create Coaching Client Tracker Google Sheet

Creates a "Coaching Client Tracker" spreadsheet with 5 tabs:
  1. Client Roster
  2. Weekly Check-Ins
  3. Progress Tracking
  4. Billing
  5. Program History

Uses existing OAuth credentials (same auth pattern as create-social-media-sheet.py).

USAGE:
    python scripts/create-coaching-tracker-sheet.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError:
    print("Installing required packages...")
    os.system("pip install google-auth google-auth-oauthlib google-api-python-client")
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

import json

# Scopes needed
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
]

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token_sheets.json"

# Sheet definitions
SPREADSHEET_NAME = "Coaching Client Tracker"

SHEETS = {
    "Client Roster": [
        "Client_ID", "Full_Name", "Email", "Phone", "Time_Zone",
        "Start_Date", "Status", "Stripe_Customer_ID", "Drive_Folder_ID", "Notes"
    ],
    "Weekly Check-Ins": [
        "Check_In_Date", "Client_ID", "Client_Name", "Rating_1_10", "Notes",
        "Sleep_Hours", "Stress_Level", "Compliance_Pct", "Coach_Response", "Responded"
    ],
    "Progress Tracking": [
        "Date", "Client_ID", "Client_Name", "Weight", "Body_Fat_Pct",
        "Waist_In", "Chest_In", "Arms_In", "Thighs_In", "Photo_Link", "Notes"
    ],
    "Billing": [
        "Date", "Client_ID", "Client_Name", "Amount", "Status",
        "Stripe_Payment_ID", "Notes"
    ],
    "Program History": [
        "Date", "Client_ID", "Client_Name", "Program_Name", "Drive_File_Link",
        "Training_Days", "Focus", "Notes"
    ],
}

# Data validation rules for dropdown columns
VALIDATION_RULES = {
    "Client Roster": {
        "Status": ["Active", "Paused", "Cancelled"],
    },
    "Weekly Check-Ins": {
        "Responded": ["Yes", "No"],
    },
    "Billing": {
        "Status": ["Paid", "Failed", "Refunded"],
    },
}


def get_credentials():
    """Get or refresh OAuth credentials."""
    creds = None

    # Check for existing token
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # If no valid credentials, need to authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print(f"ERROR: credentials.json not found at {CREDENTIALS_FILE}")
                sys.exit(1)

            print("Opening browser for authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save credentials for next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        print(f"Credentials saved to {TOKEN_FILE}")

    return creds


def find_or_create_folder(drive_service, folder_name="Coaching Clients"):
    """Find or create a folder in Google Drive."""
    query = "name='" + folder_name + "' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    folders = results.get('files', [])

    if folders:
        print(f"Found existing folder: {folder_name} (ID: {folders[0]['id']})")
        return folders[0]['id']

    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
    print(f"Created folder: {folder_name} (ID: {folder['id']})")
    return folder['id']


def col_letter(index):
    """Convert 0-based column index to letter (0=A, 25=Z, 26=AA, etc.)."""
    result = ""
    while index >= 0:
        result = chr(65 + (index % 26)) + result
        index = index // 26 - 1
    return result


def create_spreadsheet(sheets_service, drive_service, folder_id):
    """Create the spreadsheet with all tabs, headers, formatting, and validations."""

    spreadsheet_body = {
        'properties': {
            'title': SPREADSHEET_NAME
        },
        'sheets': [
            {
                'properties': {
                    'title': sheet_name,
                    'index': idx,
                }
            }
            for idx, sheet_name in enumerate(SHEETS.keys())
        ]
    }

    print(f"\nCreating spreadsheet: {SPREADSHEET_NAME}")
    spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet_body).execute()
    spreadsheet_id = spreadsheet['spreadsheetId']
    print(f"Spreadsheet ID: {spreadsheet_id}")

    # Move to folder
    if folder_id and drive_service:
        file = drive_service.files().get(fileId=spreadsheet_id, fields='parents').execute()
        previous_parents = ",".join(file.get('parents', []))

        drive_service.files().update(
            fileId=spreadsheet_id,
            addParents=folder_id,
            removeParents=previous_parents,
            fields='id, parents'
        ).execute()
        print("Moved to Coaching Clients folder")

    # Add headers to each sheet
    batch_data = []
    for sheet_name, headers in SHEETS.items():
        end_col = col_letter(len(headers) - 1)
        batch_data.append({
            'range': "'" + sheet_name + "'!A1:" + end_col + "1",
            'values': [headers]
        })

    sheets_service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'valueInputOption': 'RAW', 'data': batch_data}
    ).execute()
    print("Added headers to all sheets")

    # Build formatting + validation requests
    requests = []
    for idx, sheet_name in enumerate(SHEETS.keys()):
        sheet_id = spreadsheet['sheets'][idx]['properties']['sheetId']
        headers = SHEETS[sheet_name]
        num_cols = len(headers)

        # Bold headers with light gray background
        requests.append({
            'repeatCell': {
                'range': {'sheetId': sheet_id, 'startRowIndex': 0, 'endRowIndex': 1},
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {'bold': True},
                        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
                    }
                },
                'fields': 'userEnteredFormat(textFormat,backgroundColor)'
            }
        })

        # Freeze header row
        requests.append({
            'updateSheetProperties': {
                'properties': {
                    'sheetId': sheet_id,
                    'gridProperties': {'frozenRowCount': 1}
                },
                'fields': 'gridProperties.frozenRowCount'
            }
        })

        # Auto-resize columns
        requests.append({
            'autoResizeDimensions': {
                'dimensions': {
                    'sheetId': sheet_id,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': num_cols
                }
            }
        })

        # Add data validation for dropdown columns
        if sheet_name in VALIDATION_RULES:
            for col_name, values in VALIDATION_RULES[sheet_name].items():
                col_idx = headers.index(col_name)
                requests.append({
                    'setDataValidation': {
                        'range': {
                            'sheetId': sheet_id,
                            'startRowIndex': 1,
                            'endRowIndex': 1000,
                            'startColumnIndex': col_idx,
                            'endColumnIndex': col_idx + 1,
                        },
                        'rule': {
                            'condition': {
                                'type': 'ONE_OF_LIST',
                                'values': [{'userEnteredValue': v} for v in values]
                            },
                            'showCustomUi': True,
                            'strict': True,
                        }
                    }
                })

    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()
    print("Formatted headers (bold, frozen, auto-resized)")
    print("Added data validation dropdowns for Status and Responded columns")

    return spreadsheet_id


def main():
    print("=" * 60)
    print("Creating Coaching Client Tracker Google Sheet")
    print("=" * 60)

    # Get credentials
    creds = get_credentials()

    # Build services
    sheets_service = build('sheets', 'v4', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    # Find or create Coaching Clients folder
    folder_id = find_or_create_folder(drive_service, "Coaching Clients")

    # Create spreadsheet
    spreadsheet_id = create_spreadsheet(sheets_service, drive_service, folder_id)

    # Print results
    print("\n" + "=" * 60)
    print("SUCCESS!")
    print("=" * 60)
    print(f"\nSpreadsheet ID: {spreadsheet_id}")
    url = "https://docs.google.com/spreadsheets/d/" + spreadsheet_id + "/edit"
    print(f"\nURL: {url}")
    print("\nSheets created:")
    for sheet_name, headers in SHEETS.items():
        print(f"  - {sheet_name} ({len(headers)} columns)")

    print("\nData validation dropdowns:")
    for sheet_name, rules in VALIDATION_RULES.items():
        for col_name, values in rules.items():
            vals_str = ", ".join(values)
            print(f"  - {sheet_name} > {col_name}: {vals_str}")

    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("")
    print("1. Add to .env:")
    print(f"   COACHING_TRACKER_SPREADSHEET_ID={spreadsheet_id}")
    print("")
    print("2. Open the sheet:")
    print(f"   {url}")
    print("")
    print("3. Start adding clients to the Client Roster tab!")
    print("")

    # Save the ID to a file for easy reference
    id_file = PROJECT_ROOT / "COACHING_TRACKER_SHEET_ID.txt"
    with open(id_file, 'w') as f:
        f.write(spreadsheet_id)
    print(f"Spreadsheet ID saved to {id_file.name}")


if __name__ == "__main__":
    main()
