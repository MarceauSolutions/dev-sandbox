#!/usr/bin/env python3
"""
setup-ai-pipeline-sheet.py — Create the AI Services Pipeline Google Sheet.

Creates a sheet with 3 tabs: Deals, Outreach_Log, Weekly_Metrics.
Uses token_sheets.json (or token.json fallback) for auth.

Usage:
    python scripts/setup-ai-pipeline-sheet.py
"""

import json
import sys
from pathlib import Path

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError:
    print("ERROR: google-api-python-client not installed.")
    print("Run: pip install google-auth google-auth-oauthlib google-api-python-client")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

TOKEN_CANDIDATES = [
    PROJECT_ROOT / "token_sheets.json",
    PROJECT_ROOT / "token.json",
]

# Tab definitions
DEALS_COLUMNS = [
    "Deal_ID", "Company", "Contact_Name", "Contact_Phone", "Contact_Email",
    "Industry", "Pain_Points", "Lead_Source",
    "Stage",  # Intake/Qualified/Meeting_Booked/Proposal_Sent/Negotiation/Closed_Won/Closed_Lost
    "Next_Action", "Next_Action_Date", "Proposal_Amount", "Setup_Fee",
    "Monthly_Fee", "Close_Date", "Notes", "Created_Date"
]

OUTREACH_COLUMNS = [
    "Date", "Company", "Contact", "Channel",  # SMS/Email/Call/LinkedIn
    "Message_Summary", "Response", "Follow_Up_Date", "Lead_Source"
]

METRICS_COLUMNS = [
    "Week_Number", "Week_Starting", "Total_Outreach", "New_Leads",
    "Meetings_Booked", "Proposals_Sent", "Pipeline_Value",
    "Deals_Closed", "Revenue_Won"
]

# Brand colors
GOLD = {"red": 0.788, "green": 0.588, "blue": 0.235}  # #C9963C
CHARCOAL = {"red": 0.2, "green": 0.2, "blue": 0.2}  # #333333
WHITE = {"red": 1.0, "green": 1.0, "blue": 1.0}


def get_sheets_service():
    token_file = None
    for candidate in TOKEN_CANDIDATES:
        if candidate.exists():
            token_file = candidate
            break
    if not token_file:
        print("ERROR: No token file found. Need token_sheets.json or token.json")
        sys.exit(1)

    print(f"Using token: {token_file}")
    creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_file, "w") as f:
            f.write(creds.to_json())

    return build("sheets", "v4", credentials=creds)


def create_sheet_properties(title, index, columns):
    """Create sheet properties with frozen header row."""
    return {
        "properties": {
            "title": title,
            "index": index,
            "gridProperties": {
                "rowCount": 1000,
                "columnCount": len(columns),
                "frozenRowCount": 1,
            },
        }
    }


def main():
    service = get_sheets_service()

    # Create spreadsheet with 3 tabs
    spreadsheet_body = {
        "properties": {
            "title": "AI Services Pipeline",
        },
        "sheets": [
            create_sheet_properties("Deals", 0, DEALS_COLUMNS),
            create_sheet_properties("Outreach_Log", 1, OUTREACH_COLUMNS),
            create_sheet_properties("Weekly_Metrics", 2, METRICS_COLUMNS),
        ],
    }

    result = service.spreadsheets().create(body=spreadsheet_body).execute()
    sheet_id = result["spreadsheetId"]
    sheet_url = result["spreadsheetUrl"]

    print(f"Created sheet: {sheet_id}")
    print(f"URL: {sheet_url}")

    # Get sheet IDs for formatting
    sheets_meta = {s["properties"]["title"]: s["properties"]["sheetId"] for s in result["sheets"]}

    # Write headers and format all tabs
    batch_data = [
        {"range": "Deals!A1", "values": [DEALS_COLUMNS]},
        {"range": "Outreach_Log!A1", "values": [OUTREACH_COLUMNS]},
        {"range": "Weekly_Metrics!A1", "values": [METRICS_COLUMNS]},
    ]

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=sheet_id,
        body={"valueInputOption": "RAW", "data": batch_data},
    ).execute()

    # Format headers — gold background, white bold text
    format_requests = []
    for tab_name, tab_columns in [("Deals", DEALS_COLUMNS), ("Outreach_Log", OUTREACH_COLUMNS), ("Weekly_Metrics", METRICS_COLUMNS)]:
        sid = sheets_meta[tab_name]
        # Header formatting
        format_requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sid,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": len(tab_columns),
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": GOLD,
                        "textFormat": {
                            "foregroundColor": WHITE,
                            "bold": True,
                            "fontSize": 11,
                        },
                        "horizontalAlignment": "CENTER",
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
            }
        })
        # Auto-resize columns
        format_requests.append({
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": sid,
                    "dimension": "COLUMNS",
                    "startIndex": 0,
                    "endIndex": len(tab_columns),
                }
            }
        })

    # Add data validation for Stage column in Deals (column index 8)
    format_requests.append({
        "setDataValidation": {
            "range": {
                "sheetId": sheets_meta["Deals"],
                "startRowIndex": 1,
                "endRowIndex": 1000,
                "startColumnIndex": 8,
                "endColumnIndex": 9,
            },
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [
                        {"userEnteredValue": "Intake"},
                        {"userEnteredValue": "Qualified"},
                        {"userEnteredValue": "Meeting_Booked"},
                        {"userEnteredValue": "Proposal_Sent"},
                        {"userEnteredValue": "Negotiation"},
                        {"userEnteredValue": "Closed_Won"},
                        {"userEnteredValue": "Closed_Lost"},
                    ],
                },
                "showCustomUi": True,
                "strict": False,
            },
        }
    })

    # Add data validation for Channel column in Outreach_Log (column index 3)
    format_requests.append({
        "setDataValidation": {
            "range": {
                "sheetId": sheets_meta["Outreach_Log"],
                "startRowIndex": 1,
                "endRowIndex": 1000,
                "startColumnIndex": 3,
                "endColumnIndex": 4,
            },
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [
                        {"userEnteredValue": "SMS"},
                        {"userEnteredValue": "Email"},
                        {"userEnteredValue": "Call"},
                        {"userEnteredValue": "LinkedIn"},
                    ],
                },
                "showCustomUi": True,
                "strict": False,
            },
        }
    })

    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": format_requests},
    ).execute()

    print("\n--- AI Services Pipeline Sheet ---")
    print(f"Sheet ID: {sheet_id}")
    print(f"URL: {sheet_url}")
    print(f"Tabs: Deals (GID={sheets_meta['Deals']}), Outreach_Log (GID={sheets_meta['Outreach_Log']}), Weekly_Metrics (GID={sheets_meta['Weekly_Metrics']})")
    print("Done!")


if __name__ == "__main__":
    main()
