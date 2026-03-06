#!/usr/bin/env python3
"""
create-client-lead-sheets.py - Create Google Sheets for HVAC and Square Foot lead tracking

Creates individual lead tracking sheets for:
- SW Florida Comfort HVAC
- Square Foot Shipping & Storage

Then prints the sheet IDs to wire into form_handler/business_config.py.

Usage:
    python scripts/create-client-lead-sheets.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file']
PROJECT_ROOT = Path(__file__).parent.parent
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token_sheets.json"


def get_credentials():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
    return creds


def create_lead_sheet(service, business_name, columns):
    columns_with_meta = ["Date", "Name", "Email", "Phone", "Service Type", "Message", "Source"] + columns + ["Status", "Follow-Up Date", "Notes"]

    body = {
        'properties': {'title': f'{business_name} — Leads'},
        'sheets': [
            {
                'properties': {'title': 'Leads', 'sheetId': 0},
                'data': [{'rowData': [{'values': [{'userEnteredValue': {'stringValue': col}, 'userEnteredFormat': {'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2}, 'textFormat': {'bold': True, 'foregroundColor': {'red': 0.85, 'green': 0.6, 'blue': 0.23}}}} for col in columns_with_meta]}]}]
            }
        ]
    }

    result = service.spreadsheets().create(body=body).execute()
    sheet_id = result['spreadsheetId']
    print(f"  Created: {business_name} — Leads")
    print(f"  Sheet ID: {sheet_id}")
    print(f"  URL: https://docs.google.com/spreadsheets/d/{sheet_id}")
    return sheet_id


def main():
    print("Creating client lead tracking sheets...\n")
    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    print("1. SW Florida Comfort HVAC")
    hvac_id = create_lead_sheet(service, "SW Florida Comfort HVAC", ["AC Type", "Emergency"])
    print()

    print("2. Square Foot Shipping & Storage")
    sqft_id = create_lead_sheet(service, "Square Foot Shipping & Storage", ["Shipment Type", "Origin", "Destination"])
    print()

    print("=" * 60)
    print("WIRE THESE INTO form_handler/business_config.py:")
    print(f'  HVAC google_sheet_id="{hvac_id}"')
    print(f'  SquareFoot google_sheet_id="{sqft_id}"')
    print()
    print("Add to .env:")
    print(f'  HVAC_LEADS_SHEET_ID={hvac_id}')
    print(f'  SQUAREFOOT_LEADS_SHEET_ID={sqft_id}')

    return hvac_id, sqft_id


if __name__ == "__main__":
    main()
