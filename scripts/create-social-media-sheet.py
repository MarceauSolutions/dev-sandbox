#!/usr/bin/env python3
"""
create-social-media-sheet.py - Create Social Media Automation Google Sheet

Uses existing OAuth credentials to create the spreadsheet programmatically.
Run this script and it will create the sheet in your Google Drive.

USAGE:
    python scripts/create-social-media-sheet.py
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
SPREADSHEET_NAME = "Marceau Solutions - Social Media Automation"

SHEETS = {
    "X_Post_Queue": [
        "Post_ID", "Content", "Media_URL", "Scheduled_Time", "Status",
        "Category", "Created_At", "Posted_At", "Tweet_ID", "Error_Message"
    ],
    "X_Post_Analytics": [
        "Tweet_ID", "Post_ID", "Content", "Posted_At", "Impressions",
        "Engagements", "Likes", "Retweets", "Replies", "Profile_Clicks",
        "Link_Clicks", "Updated_At"
    ],
    "B_Roll_Prompts": [
        "Prompt_ID", "Prompt", "Category", "Status", "Image_URL",
        "Created_At", "Generated_At", "Cost", "Provider"
    ],
    "B_Roll_Generated": [
        "Image_ID", "Prompt_ID", "Prompt", "Image_URL", "Provider",
        "Cost", "Quality_Score", "Used_In", "Created_At"
    ],
}

# Folder ID for "Marceau Solutions" in Google Drive (if known)
# You can find this by opening the folder in Drive and copying from URL
FOLDER_ID = None  # Will be found or created


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
                print("\nTo create credentials.json, run:")
                print("""
python -c "
import os, json
from dotenv import load_dotenv
load_dotenv()
creds = {
    'installed': {
        'client_id': os.getenv('GOOGLE_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
        'project_id': os.getenv('GOOGLE_PROJECT_ID'),
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'redirect_uris': ['http://localhost']
    }
}
with open('credentials.json', 'w') as f:
    json.dump(creds, f, indent=2)
print('Created credentials.json')
"
                """)
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


def find_or_create_folder(drive_service, folder_name="Marceau Solutions"):
    """Find or create a folder in Google Drive."""
    # Search for existing folder
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    folders = results.get('files', [])

    if folders:
        print(f"Found existing folder: {folder_name} (ID: {folders[0]['id']})")
        return folders[0]['id']

    # Create folder if not found
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
    print(f"Created folder: {folder_name} (ID: {folder['id']})")
    return folder['id']


def create_spreadsheet(sheets_service, drive_service, folder_id):
    """Create the spreadsheet with all tabs and headers."""

    # Create spreadsheet with multiple sheets
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

    # Move to folder (if Drive API available)
    if folder_id and drive_service:
        # Get current parents
        file = drive_service.files().get(fileId=spreadsheet_id, fields='parents').execute()
        previous_parents = ",".join(file.get('parents', []))

        # Move to new folder
        drive_service.files().update(
            fileId=spreadsheet_id,
            addParents=folder_id,
            removeParents=previous_parents,
            fields='id, parents'
        ).execute()
        print(f"Moved to Marceau Solutions folder")
    else:
        print("Note: Manually move to Marceau Solutions folder in Google Drive")

    # Add headers to each sheet
    batch_data = []
    for sheet_name, headers in SHEETS.items():
        batch_data.append({
            'range': f"'{sheet_name}'!A1:{chr(65 + len(headers) - 1)}1",
            'values': [headers]
        })

    sheets_service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'valueInputOption': 'RAW', 'data': batch_data}
    ).execute()
    print("Added headers to all sheets")

    # Format headers (bold, freeze row)
    requests = []
    for idx, sheet_name in enumerate(SHEETS.keys()):
        sheet_id = spreadsheet['sheets'][idx]['properties']['sheetId']
        requests.extend([
            # Bold headers
            {
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
            },
            # Freeze header row
            {
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': sheet_id,
                        'gridProperties': {'frozenRowCount': 1}
                    },
                    'fields': 'gridProperties.frozenRowCount'
                }
            }
        ])

    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()
    print("Formatted headers (bold, frozen)")

    return spreadsheet_id


def main():
    print("=" * 60)
    print("Creating Social Media Automation Google Sheet")
    print("=" * 60)

    # Get credentials
    creds = get_credentials()

    # Build services
    sheets_service = build('sheets', 'v4', credentials=creds)

    # Use Drive API to find/create Marceau Solutions folder
    drive_service = build('drive', 'v3', credentials=creds)
    folder_id = find_or_create_folder(drive_service, "Marceau Solutions")

    # Create spreadsheet
    spreadsheet_id = create_spreadsheet(sheets_service, drive_service, folder_id)

    # Print results
    print("\n" + "=" * 60)
    print("SUCCESS!")
    print("=" * 60)
    print(f"\nSpreadsheet ID: {spreadsheet_id}")
    print(f"\nURL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
    print(f"\nSheets created:")
    for sheet_name, headers in SHEETS.items():
        print(f"  - {sheet_name} ({len(headers)} columns)")

    print(f"\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print(f"""
1. Update workflows with new ID:
   python scripts/update-social-media-sheets.py {spreadsheet_id}

2. Add to .env:
   SOCIAL_MEDIA_SPREADSHEET_ID={spreadsheet_id}

3. Deploy updated workflows to n8n
""")

    # Also save the ID to a file for easy reference
    with open(PROJECT_ROOT / "SOCIAL_MEDIA_SHEET_ID.txt", "w") as f:
        f.write(spreadsheet_id)
    print(f"Spreadsheet ID saved to SOCIAL_MEDIA_SHEET_ID.txt")


if __name__ == "__main__":
    main()
