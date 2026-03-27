#!/usr/bin/env python3
"""
Daily Report — Generate the daily Google Sheet call list + SMS summary.

Creates a NEW sheet tab "Calls YYYY-MM-DD" (never overwrites existing tabs).
Each lead gets:
  - Priority, Company, Contact, Phone, Email, Industry, Score, Stage
  - OPENER, HOOK, ASK THIS, CLOSE (from pitch_briefer)
  - IF VOICEMAIL script
  - Objection handlers
  - Prior outreach summary
  - YOUR INPUT columns: Call Outcome (dropdown), Spoke With, Notes
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path

from .config import DB_PATH, SPREADSHEET_ID, TOKEN_PATH, WILLIAM_PHONE, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER


def _get_sheets_service():
    """Get authenticated Google Sheets API service."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    if not os.path.exists(TOKEN_PATH):
        raise FileNotFoundError(f"Google token not found at {TOKEN_PATH}. Run OAuth flow first.")

    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return build("sheets", "v4", credentials=creds)


def _format_outreach_history(deal_id: int, conn: sqlite3.Connection) -> str:
    """Summarize prior outreach for this lead."""
    rows = conn.execute("""
        SELECT channel, message_summary, response, created_at
        FROM outreach_log WHERE deal_id = ?
        ORDER BY created_at DESC LIMIT 5
    """, (deal_id,)).fetchall()

    if not rows:
        return "No prior outreach"

    lines = []
    for r in rows:
        date = r["created_at"][:10] if r["created_at"] else "?"
        resp = f" -> {r['response']}" if r["response"] else ""
        lines.append(f"{date} {r['channel']}: {(r['message_summary'] or '')[:50]}{resp}")
    return "\n".join(lines)


def generate_call_sheet(tasks: list, dry_run: bool = False) -> str:
    """
    Generate a Google Sheet tab with today's call list.

    Args:
        tasks: Task dicts from follow_up_router (with pitch scripts)
        dry_run: If True, print but don't create sheet

    Returns:
        Sheet URL or empty string on failure
    """
    print("\n=== DAILY CALL SHEET ===")

    today = datetime.now().strftime("%Y-%m-%d")
    tab_name = f"Calls {today}"

    # Filter to tasks with phone numbers
    call_tasks = [t for t in tasks if t.get("phone")]

    if not call_tasks:
        print("  No leads with phone numbers for today's call list")
        return ""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Build header row
    headers = [
        "#", "Priority", "Company", "Contact", "Phone", "Email",
        "Industry", "Score", "Stage", "Tier",
        "OPENER", "HOOK", "ASK THIS", "CLOSE",
        "IF VOICEMAIL",
        "If 'Already Have AI'", "If 'Not Interested'", "If 'Too Busy'",
        "Prior Outreach",
        "CALL OUTCOME", "SPOKE WITH", "NOTES",
    ]

    rows = [headers]

    for i, task in enumerate(call_tasks, 1):
        pitch = task.get("pitch", {})
        objections = task.get("objection_handlers", {})

        # Outreach history
        history = _format_outreach_history(task["deal_id"], conn)

        row = [
            i,
            f"{'FOLLOW-UP' if task.get('is_followup') else 'NEW'} | {'HIGH' if task['priority'] == 'high' else task['priority'].upper()}",
            task["company"],
            task.get("contact", ""),
            task.get("phone", ""),
            task.get("email", ""),
            task.get("industry", ""),
            task.get("score", 0),
            task.get("stage", ""),
            f"T{task.get('tier', 3)}",
            pitch.get("opener", ""),
            pitch.get("hook", ""),
            pitch.get("discovery_question", ""),
            pitch.get("close", ""),
            task.get("voicemail", ""),
            objections.get("already_have_ai", ""),
            objections.get("not_interested", ""),
            objections.get("too_busy", ""),
            history,
            "",  # CALL OUTCOME — William fills this in
            "",  # SPOKE WITH
            "",  # NOTES
        ]
        rows.append(row)

    conn.close()

    print(f"  Prepared {len(call_tasks)} leads for call sheet")

    if dry_run:
        for row in rows[:3]:
            print(f"  Row: {row[:5]}...")
        print(f"  ... ({len(rows) - 1} total leads)")
        return f"[DRY RUN] Would create tab: {tab_name}"

    # Create Google Sheet tab
    try:
        service = _get_sheets_service()

        # Create new tab (never overwrite existing)
        try:
            service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={
                    "requests": [{
                        "addSheet": {
                            "properties": {
                                "title": tab_name,
                                "gridProperties": {
                                    "rowCount": max(len(rows) + 5, 100),
                                    "columnCount": len(headers),
                                },
                            }
                        }
                    }]
                },
            ).execute()
            print(f"  Created new tab: {tab_name}")
        except Exception as e:
            if "already exists" in str(e).lower():
                # Tab exists — use a versioned name
                tab_name = f"Calls {today} v2"
                service.spreadsheets().batchUpdate(
                    spreadsheetId=SPREADSHEET_ID,
                    body={
                        "requests": [{
                            "addSheet": {
                                "properties": {"title": tab_name}
                            }
                        }]
                    },
                ).execute()
                print(f"  Tab existed, created: {tab_name}")
            else:
                raise

        # Write data
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{tab_name}'!A1",
            valueInputOption="RAW",
            body={"values": rows},
        ).execute()

        # Add data validation for CALL OUTCOME column (column T = index 19)
        # Get the sheet ID for the new tab
        sheet_metadata = service.spreadsheets().get(
            spreadsheetId=SPREADSHEET_ID
        ).execute()
        sheet_id = None
        for sheet in sheet_metadata.get("sheets", []):
            if sheet["properties"]["title"] == tab_name:
                sheet_id = sheet["properties"]["sheetId"]
                break

        if sheet_id is not None:
            outcome_col_index = headers.index("CALL OUTCOME")
            service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={
                    "requests": [{
                        "setDataValidation": {
                            "range": {
                                "sheetId": sheet_id,
                                "startRowIndex": 1,
                                "endRowIndex": len(rows) + 1,
                                "startColumnIndex": outcome_col_index,
                                "endColumnIndex": outcome_col_index + 1,
                            },
                            "rule": {
                                "condition": {
                                    "type": "ONE_OF_LIST",
                                    "values": [
                                        {"userEnteredValue": v} for v in [
                                            "Interested", "Not Interested", "Voicemail",
                                            "Callback Requested", "Meeting Booked",
                                            "No Answer", "Gatekeeper", "Send Info",
                                            "Wrong Number", "Already Has Solution",
                                        ]
                                    ],
                                },
                                "showCustomUi": True,
                                "strict": False,
                            },
                        }
                    }]
                },
            ).execute()

            # Freeze header row and bold it
            service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={
                    "requests": [
                        {
                            "updateSheetProperties": {
                                "properties": {
                                    "sheetId": sheet_id,
                                    "gridProperties": {"frozenRowCount": 1},
                                },
                                "fields": "gridProperties.frozenRowCount",
                            }
                        },
                        {
                            "repeatCell": {
                                "range": {
                                    "sheetId": sheet_id,
                                    "startRowIndex": 0,
                                    "endRowIndex": 1,
                                },
                                "cell": {
                                    "userEnteredFormat": {
                                        "textFormat": {"bold": True},
                                        "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2},
                                        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                                    }
                                },
                                "fields": "userEnteredFormat(textFormat,backgroundColor)",
                            }
                        },
                    ]
                },
            ).execute()

        sheet_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={sheet_id}"
        print(f"  Sheet URL: {sheet_url}")
        return sheet_url

    except Exception as e:
        print(f"  [ERROR] Failed to create Google Sheet: {e}")
        return ""


def send_summary_sms(task_count: int, sheet_url: str, dry_run: bool = False):
    """Send SMS summary to William with call count and sheet link."""
    if not task_count:
        return

    message = (
        f"{task_count} calls ready for today.\n"
        f"Sheet: {sheet_url}" if sheet_url else f"{task_count} calls ready for today. Check Google Sheets."
    )

    if dry_run:
        print(f"  [DRY] Would SMS William: {message[:80]}")
        return

    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        print("  [WARN] Twilio not configured — can't send SMS summary")
        return

    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message, from_=TWILIO_PHONE_NUMBER, to=WILLIAM_PHONE
        )
        print(f"  [SENT] SMS summary to William: {task_count} calls ready")
    except Exception as e:
        print(f"  [ERROR] SMS summary failed: {e}")


def run_daily_report(tasks: list, dry_run: bool = False) -> str:
    """
    Generate daily call sheet and notify William.

    Args:
        tasks: Task dicts from follow_up_router
        dry_run: Preview only

    Returns:
        Sheet URL
    """
    sheet_url = generate_call_sheet(tasks, dry_run=dry_run)

    call_count = sum(1 for t in tasks if t.get("phone"))
    send_summary_sms(call_count, sheet_url, dry_run=dry_run)

    return sheet_url


if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    from .follow_up_router import run_routing
    tasks = run_routing(dry_run=True)
    run_daily_report(tasks, dry_run=dry)
