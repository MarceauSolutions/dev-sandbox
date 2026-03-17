#!/usr/bin/env python3
"""
create-scorecard-sheet.py - Create Marceau Execution Scorecard Google Sheet

WHAT: Creates a Google Sheets spreadsheet with 5 tabs for the 90-day accountability system
WHY: Central scorecard for Clawdbot auto-logging, weekly reports, and milestone tracking
INPUT: Google OAuth credentials (credentials.json + token_sheets.json)
OUTPUT: New Google Sheet with formatted tabs, pre-populated data, and conditional formatting

QUICK USAGE:
  python scripts/create-scorecard-sheet.py

DEPENDENCIES: google-auth, google-auth-oauthlib, google-api-python-client
API_KEYS: Google OAuth credentials (credentials.json at project root)
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
SPREADSHEET_NAME = "Marceau Execution Scorecard"

# Brand colors
GOLD = {"red": 201/255, "green": 150/255, "blue": 60/255}   # #C9963C
CHARCOAL = {"red": 51/255, "green": 51/255, "blue": 51/255}  # #333333
WHITE = {"red": 1.0, "green": 1.0, "blue": 1.0}

TAB_DEFINITIONS = [
    {
        "name": "Daily Log",
        "headers": [
            "Date", "Day_Number", "Week_Number", "Day_of_Week", "Morning_Energy",
            "Outreach_Count", "Meetings_Booked", "Videos_Filmed", "Content_Posted",
            "Training_Session", "Notes"
        ],
        "col_widths": [110, 90, 100, 100, 120, 120, 120, 110, 120, 120, 300],
        "frozen_rows": 1,
        "frozen_cols": 2,
    },
    {
        "name": "Weekly Summary",
        "headers": [
            "Week_Number", "Week_Starting", "Total_Outreach", "Total_Meetings",
            "Total_Proposals", "Clients_Closed", "Videos_Published", "Shorts_Published",
            "Training_Sessions", "Avg_Energy", "Revenue_Setup", "Revenue_MRR",
            "On_Track_Score", "Win_of_Week", "Focus_Area"
        ],
        "col_widths": [100, 120, 120, 120, 120, 120, 130, 130, 130, 100, 120, 110, 120, 200, 200],
        "frozen_rows": 1,
        "frozen_cols": 1,
    },
    {
        "name": "90-Day Goals",
        "headers": ["Goal", "Target", "Current", "Pct_Complete", "Days_Remaining", "Status"],
        "col_widths": [300, 150, 150, 120, 120, 120],
        "frozen_rows": 1,
        "frozen_cols": 0,
    },
    {
        "name": "Milestones",
        "headers": [
            "Milestone_ID", "Milestone_Name", "Target_Condition", "Achieved",
            "Achieved_Date", "Celebration_Sent", "Data_Snapshot"
        ],
        "col_widths": [100, 250, 300, 90, 120, 130, 300],
        "frozen_rows": 1,
        "frozen_cols": 0,
    },
    {
        "name": "Content Calendar",
        "headers": [
            "Week_Number", "Video_Topic", "Video_Type", "Published",
            "Published_Date", "Notes"
        ],
        "col_widths": [100, 350, 120, 90, 120, 250],
        "frozen_rows": 1,
        "frozen_cols": 0,
    },
]

# Pre-populated data
WEEKLY_SUMMARY_ROWS = [
    [1, "2026-03-17", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    [2, "2026-03-24", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    [3, "2026-03-31", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    [4, "2026-04-07", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    [5, "2026-04-14", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    [6, "2026-04-21", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    [7, "2026-04-28", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    [8, "2026-05-05", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    [9, "2026-05-12", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    [10, "2026-05-19", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    [11, "2026-05-26", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    [12, "2026-06-02", "", "", "", "", "", "", "", "", "", "", "", "", ""],
]

GOALS_ROWS = [
    ["3 paying AI services clients ($1,500-3,000/mo each)", "3 clients", "0 clients", "", "", "Not Started"],
    ["500+ YouTube subscribers", "500 subscribers", "0 subscribers", "", "", "Not Started"],
    ["1 digital fitness product live ($19.99)", "1 product", "0 products", "", "", "Not Started"],
    ["First group coaching cohort forming", "5 waitlist signups", "0 signups", "", "", "Not Started"],
    ["$3,000/mo total revenue", "$3,000", "$0", "", "", "Not Started"],
]

MILESTONES_ROWS = [
    [1, "First Discovery Call Booked", "Cumulative Meetings_Booked >= 1", False, "", False, ""],
    [2, "First Free Client Signed", "Cumulative Clients_Closed >= 1", False, "", False, ""],
    [3, "First Paid Client", "First non-zero AI services Stripe payment", False, "", False, ""],
    [4, "$1,000 MRR", "Stripe active subscription sum >= $1,000/mo", False, "", False, ""],
    [5, "100 YouTube Subscribers", "YouTube subscriber count >= 100", False, "", False, ""],
    [6, "500 Outreach Messages Sent", "Cumulative SUM(Outreach_Count) >= 500", False, "", False, ""],
    [7, "500 YouTube Subscribers", "YouTube subscriber count >= 500", False, "", False, ""],
    [8, "First Digital Product Sale", "Stripe payment for digital product price ID", False, "", False, ""],
    [9, "$3,000/mo Revenue", "Monthly total revenue >= $3,000", False, "", False, ""],
    [10, "90-Day Plan Complete", "Calendar date: Sunday June 7, 2026", False, "", False, ""],
]

CONTENT_CALENDAR_ROWS = [
    [1, "Brain cancer, dystonia, and why I still train", "Long-form", False, "", ""],
    [1, "My morning routine with a brain tumor", "Short", False, "", ""],
    [2, "The peptide protocol that changed everything", "Long-form", False, "", ""],
    [2, "3 exercises everyone with dystonia should try", "Short", False, "", ""],
    [3, "How I built an AI business from a hospital bed", "Long-form", False, "", ""],
    [3, "Tesamorelin explained in 60 seconds", "Short", False, "", ""],
    [4, "Evidence-based training with neurological conditions", "Long-form", False, "", ""],
    [4, "What I eat in a day (brain cancer edition)", "Short", False, "", ""],
]

# Validation rules (dropdowns)
VALIDATION_RULES = {
    "90-Day Goals": {
        "Status": ["Not Started", "In Progress", "At Risk", "On Track", "Achieved"],
    },
    "Content Calendar": {
        "Video_Type": ["Long-form", "Short", "Reel", "Behind-the-scenes"],
    },
}


def get_credentials():
    """Get or refresh OAuth credentials."""
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

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

        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        print(f"Credentials saved to {TOKEN_FILE}")

    return creds


def col_letter(index):
    """Convert 0-based column index to letter (0=A, 25=Z, 26=AA, etc.)."""
    result = ""
    while index >= 0:
        result = chr(65 + (index % 26)) + result
        index = index // 26 - 1
    return result


def hex_to_rgb(hex_color):
    """Convert hex color string to RGB dict for Sheets API."""
    hex_color = hex_color.lstrip('#')
    return {
        "red": int(hex_color[0:2], 16) / 255,
        "green": int(hex_color[2:4], 16) / 255,
        "blue": int(hex_color[4:6], 16) / 255,
    }


def create_spreadsheet(sheets_service, drive_service):
    """Create the spreadsheet with all tabs, headers, formatting, data, and validations."""

    # Build sheet properties
    sheet_props = []
    for idx, tab in enumerate(TAB_DEFINITIONS):
        sheet_props.append({
            'properties': {
                'title': tab["name"],
                'index': idx,
            }
        })

    spreadsheet_body = {
        'properties': {'title': SPREADSHEET_NAME},
        'sheets': sheet_props,
    }

    print(f"\nCreating spreadsheet: {SPREADSHEET_NAME}")
    spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet_body).execute()
    spreadsheet_id = spreadsheet['spreadsheetId']
    print(f"Spreadsheet ID: {spreadsheet_id}")

    # Share with William
    drive_service.permissions().create(
        fileId=spreadsheet_id,
        body={
            'type': 'user',
            'role': 'writer',
            'emailAddress': 'wmarceau@marceausolutions.com',
        },
        sendNotificationEmail=False,
    ).execute()
    print("Shared with wmarceau@marceausolutions.com (editor)")

    # ---- Write headers and pre-populated data ----
    batch_data = []

    for tab in TAB_DEFINITIONS:
        name = tab["name"]
        headers = tab["headers"]
        end_col = col_letter(len(headers) - 1)
        batch_data.append({
            'range': f"'{name}'!A1:{end_col}1",
            'values': [headers]
        })

    # Weekly Summary data (rows 2-13)
    batch_data.append({
        'range': "'Weekly Summary'!A2:O13",
        'values': WEEKLY_SUMMARY_ROWS,
    })

    # 90-Day Goals data (rows 2-6)
    batch_data.append({
        'range': "'90-Day Goals'!A2:F6",
        'values': GOALS_ROWS,
    })

    # Milestones data (rows 2-11)
    batch_data.append({
        'range': "'Milestones'!A2:G11",
        'values': MILESTONES_ROWS,
    })

    # Content Calendar data (rows 2-9)
    batch_data.append({
        'range': "'Content Calendar'!A2:F9",
        'values': CONTENT_CALENDAR_ROWS,
    })

    sheets_service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'valueInputOption': 'USER_ENTERED', 'data': batch_data}
    ).execute()
    print("Added headers and pre-populated data to all sheets")

    # ---- Build formatting requests ----
    requests = []

    for idx, tab in enumerate(TAB_DEFINITIONS):
        sheet_id = spreadsheet['sheets'][idx]['properties']['sheetId']
        headers = tab["headers"]
        num_cols = len(headers)

        # Header formatting: charcoal background, gold text, bold
        requests.append({
            'repeatCell': {
                'range': {'sheetId': sheet_id, 'startRowIndex': 0, 'endRowIndex': 1},
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {
                            'bold': True,
                            'fontSize': 11,
                            'foregroundColor': GOLD,
                        },
                        'backgroundColor': CHARCOAL,
                        'horizontalAlignment': 'CENTER',
                    }
                },
                'fields': 'userEnteredFormat(textFormat,backgroundColor,horizontalAlignment)'
            }
        })

        # Freeze rows
        frozen_rows = tab.get("frozen_rows", 1)
        frozen_cols = tab.get("frozen_cols", 0)
        grid_props = {'frozenRowCount': frozen_rows}
        fields = 'gridProperties.frozenRowCount'
        if frozen_cols > 0:
            grid_props['frozenColumnCount'] = frozen_cols
            fields = 'gridProperties(frozenRowCount,frozenColumnCount)'

        requests.append({
            'updateSheetProperties': {
                'properties': {
                    'sheetId': sheet_id,
                    'gridProperties': grid_props,
                },
                'fields': fields,
            }
        })

        # Column widths
        col_widths = tab.get("col_widths", [])
        for col_idx, width in enumerate(col_widths):
            requests.append({
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': sheet_id,
                        'dimension': 'COLUMNS',
                        'startIndex': col_idx,
                        'endIndex': col_idx + 1,
                    },
                    'properties': {'pixelSize': width},
                    'fields': 'pixelSize',
                }
            })

        # Data validation for dropdowns
        name = tab["name"]
        if name in VALIDATION_RULES:
            for col_name, values in VALIDATION_RULES[name].items():
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

    # ---- Conditional formatting for On_Track_Score (Weekly Summary) ----
    ws_sheet_id = spreadsheet['sheets'][1]['properties']['sheetId']
    ots_col = TAB_DEFINITIONS[1]["headers"].index("On_Track_Score")  # column index

    # Gold for >= 80
    requests.append({
        'addConditionalFormatRule': {
            'rule': {
                'ranges': [{
                    'sheetId': ws_sheet_id,
                    'startRowIndex': 1, 'endRowIndex': 100,
                    'startColumnIndex': ots_col, 'endColumnIndex': ots_col + 1,
                }],
                'booleanRule': {
                    'condition': {
                        'type': 'NUMBER_GREATER_THAN_EQ',
                        'values': [{'userEnteredValue': '80'}]
                    },
                    'format': {
                        'backgroundColor': GOLD,
                        'textFormat': {'foregroundColor': WHITE},
                    }
                }
            },
            'index': 0,
        }
    })

    # Amber for >= 60 (and < 80, applied after gold rule takes priority)
    requests.append({
        'addConditionalFormatRule': {
            'rule': {
                'ranges': [{
                    'sheetId': ws_sheet_id,
                    'startRowIndex': 1, 'endRowIndex': 100,
                    'startColumnIndex': ots_col, 'endColumnIndex': ots_col + 1,
                }],
                'booleanRule': {
                    'condition': {
                        'type': 'NUMBER_GREATER_THAN_EQ',
                        'values': [{'userEnteredValue': '60'}]
                    },
                    'format': {
                        'backgroundColor': hex_to_rgb('#f59e0b'),
                        'textFormat': {'foregroundColor': CHARCOAL},
                    }
                }
            },
            'index': 1,
        }
    })

    # Red for < 60
    requests.append({
        'addConditionalFormatRule': {
            'rule': {
                'ranges': [{
                    'sheetId': ws_sheet_id,
                    'startRowIndex': 1, 'endRowIndex': 100,
                    'startColumnIndex': ots_col, 'endColumnIndex': ots_col + 1,
                }],
                'booleanRule': {
                    'condition': {
                        'type': 'NUMBER_LESS',
                        'values': [{'userEnteredValue': '60'}]
                    },
                    'format': {
                        'backgroundColor': hex_to_rgb('#ef4444'),
                        'textFormat': {'foregroundColor': WHITE},
                    }
                }
            },
            'index': 2,
        }
    })

    # ---- Conditional formatting for 90-Day Goals Status column ----
    goals_sheet_id = spreadsheet['sheets'][2]['properties']['sheetId']
    status_col = TAB_DEFINITIONS[2]["headers"].index("Status")

    status_colors = [
        ("Achieved", "#C9963C", "#FFFFFF"),
        ("On Track", "#3b82f6", "#FFFFFF"),
        ("In Progress", "#6b7280", "#FFFFFF"),
        ("At Risk", "#f59e0b", "#333333"),
        ("Not Started", "#e5e7eb", "#333333"),
    ]

    for i, (text, bg, fg) in enumerate(status_colors):
        requests.append({
            'addConditionalFormatRule': {
                'rule': {
                    'ranges': [{
                        'sheetId': goals_sheet_id,
                        'startRowIndex': 1, 'endRowIndex': 100,
                        'startColumnIndex': status_col, 'endColumnIndex': status_col + 1,
                    }],
                    'booleanRule': {
                        'condition': {
                            'type': 'TEXT_EQ',
                            'values': [{'userEnteredValue': text}]
                        },
                        'format': {
                            'backgroundColor': hex_to_rgb(bg),
                            'textFormat': {'foregroundColor': hex_to_rgb(fg)},
                        }
                    }
                },
                'index': i,
            }
        })

    # Execute all formatting requests
    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()
    print("Applied formatting: headers, column widths, freezes, dropdowns, conditional formatting")

    # Print tab GIDs for memory/sheets-gids.md
    print("\n--- Tab GIDs (for memory/sheets-gids.md) ---")
    for sheet in spreadsheet['sheets']:
        props = sheet['properties']
        print(f"  {props['title']}: {props['sheetId']}")

    return spreadsheet_id


def main():
    print("=" * 60)
    print("Creating Marceau Execution Scorecard")
    print("=" * 60)

    creds = get_credentials()

    sheets_service = build('sheets', 'v4', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    spreadsheet_id = create_spreadsheet(sheets_service, drive_service)

    url = "https://docs.google.com/spreadsheets/d/" + spreadsheet_id + "/edit"

    print("\n" + "=" * 60)
    print("SUCCESS!")
    print("=" * 60)
    print(f"\nSpreadsheet ID: {spreadsheet_id}")
    print(f"URL: {url}")
    print(f"\nTabs created:")
    for tab in TAB_DEFINITIONS:
        print(f"  - {tab['name']} ({len(tab['headers'])} columns)")

    print(f"\nPre-populated data:")
    print(f"  - Weekly Summary: 12 week rows")
    print(f"  - 90-Day Goals: 5 goals")
    print(f"  - Milestones: 10 milestones")
    print(f"  - Content Calendar: 8 video topics (weeks 1-4)")

    print(f"\nDropdown validations:")
    for sheet_name, rules in VALIDATION_RULES.items():
        for col_name, values in rules.items():
            print(f"  - {sheet_name} > {col_name}: {', '.join(values)}")

    print(f"\nConditional formatting:")
    print(f"  - Weekly Summary > On_Track_Score: Gold (>=80), Amber (>=60), Red (<60)")
    print(f"  - 90-Day Goals > Status: Color-coded by status value")

    print("\n" + "=" * 60)
    print("NEXT STEP")
    print("=" * 60)
    print(f"\nAdd to .env:")
    print(f"  SCORECARD_SPREADSHEET_ID={spreadsheet_id}")
    print(f"\nOpen the sheet:")
    print(f"  {url}")

    return spreadsheet_id


if __name__ == "__main__":
    main()
