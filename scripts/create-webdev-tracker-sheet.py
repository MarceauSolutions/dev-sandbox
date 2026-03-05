#!/usr/bin/env python3
"""
create-webdev-tracker-sheet.py - Create Web Dev Client Tracker Google Sheet

WHAT: Creates a Google Sheets spreadsheet with 3 tabs for tracking web dev clients
WHY: Central hub for client data, project status, billing, and cross-referrals
INPUT: Google OAuth credentials (credentials.json + token_sheets.json)
OUTPUT: New Google Sheet with formatted tabs

QUICK USAGE:
  python scripts/create-webdev-tracker-sheet.py

DEPENDENCIES: google-auth, google-auth-oauthlib, google-api-python-client
API_KEYS: Google OAuth credentials (credentials.json at project root)
"""

import os
import sys
from pathlib import Path

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

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
]

PROJECT_ROOT = Path(__file__).parent.parent
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token_sheets.json"

SPREADSHEET_NAME = "Web Dev Client Tracker"

SHEETS = {
    "Web Dev Clients": [
        "Client Name", "Email", "Phone", "Domain", "GitHub Repo",
        "Project Slug", "Amount Paid", "Date", "Status", "DNS Status",
        "HTTPS Enabled", "Last Deploy", "Monthly Hosting", "Notes"
    ],
    "Project Log": [
        "Date", "Client Name", "Action", "Details", "Deploy Commit",
        "Notified Client"
    ],
    "Cross-Referrals": [
        "Date", "Client Name", "Phone", "Email", "From Business",
        "To Business", "Need", "Status", "Outcome", "Notes"
    ],
}

# Brand colors
GOLD = {"red": 0.788, "green": 0.588, "blue": 0.235}  # #C9963C
DARK = {"red": 0.102, "green": 0.102, "blue": 0.102}   # #1a1a1a
WHITE = {"red": 1.0, "green": 1.0, "blue": 1.0}


def get_credentials():
    """Get or refresh Google OAuth credentials."""
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print(f"ERROR: {CREDENTIALS_FILE} not found")
                print("Download from Google Cloud Console > APIs & Services > Credentials")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())

    return creds


def create_spreadsheet(service):
    """Create the spreadsheet with all tabs."""
    sheet_properties = []
    for i, (name, _) in enumerate(SHEETS.items()):
        sheet_properties.append({
            "properties": {
                "title": name,
                "index": i,
                "gridProperties": {"frozenRowCount": 1},
                "tabColorStyle": {"rgbColor": GOLD}
            }
        })

    spreadsheet = service.spreadsheets().create(body={
        "properties": {"title": SPREADSHEET_NAME},
        "sheets": sheet_properties
    }).execute()

    spreadsheet_id = spreadsheet["spreadsheetId"]
    print(f"Created: {SPREADSHEET_NAME}")
    print(f"ID: {spreadsheet_id}")
    print(f"URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")

    return spreadsheet_id


def populate_headers(service, spreadsheet_id):
    """Add headers to each tab."""
    data = []
    for sheet_name, headers in SHEETS.items():
        data.append({
            "range": f"'{sheet_name}'!A1:{chr(64 + len(headers))}1",
            "values": [headers]
        })

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"valueInputOption": "RAW", "data": data}
    ).execute()
    print("Headers populated.")


def format_headers(service, spreadsheet_id):
    """Apply dark+gold formatting to header rows."""
    sheets_meta = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id
    ).execute()

    requests = []
    for sheet in sheets_meta["sheets"]:
        sheet_id = sheet["properties"]["sheetId"]
        col_count = len(SHEETS[sheet["properties"]["title"]])

        # Header row: gold background, dark text, bold
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0, "endRowIndex": 1,
                    "startColumnIndex": 0, "endColumnIndex": col_count
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": GOLD,
                        "textFormat": {
                            "foregroundColorStyle": {"rgbColor": DARK},
                            "bold": True,
                            "fontSize": 10
                        },
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        })

        # Auto-resize columns
        requests.append({
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": 0, "endIndex": col_count
                }
            }
        })

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests}
    ).execute()
    print("Formatting applied (dark+gold headers).")


def seed_existing_clients(service, spreadsheet_id):
    """Pre-populate with existing web dev clients."""
    clients = [
        ["SW Florida Comfort HVAC", "", "", "swfloridacomfort.com",
         "MarceauSolutions/swflorida-comfort-hvac", "hvac", "",
         "", "Active", "Complete", "Yes", "", "No", ""],
        ["BoabFit", "", "", "TBD",
         "MarceauSolutions/boabfit-website", "boabfit", "",
         "", "Active", "N/A", "No", "", "No", ""],
        ["Flames of Passion", "", "(239) 784-6792",
         "flamesofpassionentertainment.com",
         "MarceauSolutions/flames-of-passion-website", "flames", "",
         "", "Active", "Pending", "No", "", "No",
         "DNS managed via Google Workspace Admin Console"],
    ]

    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="'Web Dev Clients'!A2",
        valueInputOption="RAW",
        body={"values": clients}
    ).execute()
    print(f"Seeded {len(clients)} existing clients.")


def main():
    print("=" * 60)
    print("WEB DEV CLIENT TRACKER — SETUP")
    print("=" * 60)

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    spreadsheet_id = create_spreadsheet(service)
    populate_headers(service, spreadsheet_id)
    format_headers(service, spreadsheet_id)
    seed_existing_clients(service, spreadsheet_id)

    print("\n" + "=" * 60)
    print("DONE! Web Dev Client Tracker is ready.")
    print(f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
    print("=" * 60)

    # Save the ID for reference
    config_path = PROJECT_ROOT / "projects/marceau-solutions/web-dev/data/sheet-config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump({
            "spreadsheet_id": spreadsheet_id,
            "spreadsheet_name": SPREADSHEET_NAME,
            "created": "auto",
            "tabs": list(SHEETS.keys())
        }, f, indent=2)
    print(f"Sheet ID saved to {config_path}")


if __name__ == "__main__":
    main()
