#!/usr/bin/env python3
"""
accountability_handler.py — Parse accountability messages and log to Google Sheets.

Called by Clawdbot when it detects accountability-pattern messages from William.
Returns structured response text for Clawdbot to relay via Telegram.

Usage:
    python3 execution/accountability_handler.py --type energy --value 7
    python3 execution/accountability_handler.py --type eod --outreach 87 --meetings 1 --videos 2 --content 3
    python3 execution/accountability_handler.py --type status
    python3 execution/accountability_handler.py --type goals
    python3 execution/accountability_handler.py --type training
    python3 execution/accountability_handler.py --type note --note "Had a great meeting with HVAC prospect"
    python3 execution/accountability_handler.py --type outreach_only --outreach 47
    python3 execution/accountability_handler.py --type fix --field outreach --fix-value 95
    python3 execution/accountability_handler.py --type parse --text "87, 1, 2, 3"
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError:
    print("ERROR: google-api-python-client not installed. Run: pip install google-auth google-auth-oauthlib google-api-python-client")
    sys.exit(1)

# Constants
PLAN_START = datetime(2026, 3, 17)
PLAN_END = datetime(2026, 6, 7)
SCORECARD_SHEET_ID = "1Y5PwloUBbHM8AeiL032_zWy9jjo9vwhyRZkl7qaKw5o"
DAILY_LOG_GID = 1874200900
WEEKLY_SUMMARY_GID = 311738664
GOALS_GID = 1782644948
MILESTONES_GID = 725518367

# Find token file
PROJECT_ROOT = Path(__file__).parent.parent
TOKEN_CANDIDATES = [
    PROJECT_ROOT / "token_sheets.json",
    Path.home() / "dev-sandbox" / "token_sheets.json",
    Path("/home/clawdbot/dev-sandbox/token_sheets.json"),
]


def get_sheets_service():
    token_file = None
    for candidate in TOKEN_CANDIDATES:
        if candidate.exists():
            token_file = candidate
            break
    if not token_file:
        raise FileNotFoundError("No token_sheets.json found")

    creds = Credentials.from_authorized_user_file(
        str(token_file), ["https://www.googleapis.com/auth/spreadsheets"]
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_file, "w") as f:
            f.write(creds.to_json())

    return build("sheets", "v4", credentials=creds)


def get_context():
    """Calculate day/week numbers from plan start."""
    now = datetime.now()
    days_since = (now - PLAN_START).days
    day_number = max(1, days_since + 1)
    week_number = min(12, max(1, (day_number + 6) // 7))
    days_remaining = max(0, 84 - days_since)
    today = now.strftime("%Y-%m-%d")
    day_of_week = now.strftime("%A")
    return {
        "day_number": day_number,
        "week_number": week_number,
        "days_remaining": days_remaining,
        "today": today,
        "day_of_week": day_of_week,
    }


def read_tab(service, tab_name):
    """Read all rows from a tab."""
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=SCORECARD_SHEET_ID, range=f"{tab_name}!A:K")
        .execute()
    )
    rows = result.get("values", [])
    if not rows:
        return []
    headers = rows[0]
    return [dict(zip(headers, row + [""] * (len(headers) - len(row)))) for row in rows[1:]]


def append_row(service, tab_name, values):
    """Append a row to a tab."""
    service.spreadsheets().values().append(
        spreadsheetId=SCORECARD_SHEET_ID,
        range=f"{tab_name}!A:K",
        valueInputOption="USER_ENTERED",
        body={"values": [values]},
    ).execute()


def update_cell(service, tab_name, row_index, col_letter, value):
    """Update a specific cell (row_index is 1-based including header)."""
    service.spreadsheets().values().update(
        spreadsheetId=SCORECARD_SHEET_ID,
        range=f"{tab_name}!{col_letter}{row_index}",
        valueInputOption="USER_ENTERED",
        body={"values": [[value]]},
    ).execute()


def find_today_row(rows, today):
    """Find row for today's date. Returns (row_dict, 1-based_row_index) or (None, None)."""
    for i, row in enumerate(rows):
        if row.get("Date") == today:
            return row, i + 2  # +2 because header is row 1, data starts row 2
    return None, None


# Column letter mapping for Daily Log
COL_MAP = {
    "Date": "A", "Day_Number": "B", "Week_Number": "C", "Day_of_Week": "D",
    "Morning_Energy": "E", "Outreach_Count": "F", "Meetings_Booked": "G",
    "Videos_Filmed": "H", "Content_Posted": "I", "Training_Session": "J", "Notes": "K",
}


def handle_energy(args):
    ctx = get_context()
    service = get_sheets_service()
    rows = read_tab(service, "Daily Log")
    existing, row_idx = find_today_row(rows, ctx["today"])

    if existing:
        update_cell(service, "Daily Log", row_idx, COL_MAP["Morning_Energy"], args.value)
    else:
        append_row(service, "Daily Log", [
            ctx["today"], ctx["day_number"], ctx["week_number"],
            ctx["day_of_week"], args.value, "", "", "", "", "", ""
        ])

    energy = args.value
    if energy >= 8:
        return "High energy day. Channel it into outreach volume."
    elif energy >= 5:
        return "Solid. Execute the fundamentals today."
    elif energy >= 3:
        return "Low energy. Do the minimum: 50 outreach, 1 video. Rest is legit."
    else:
        return "Rough day. Do what you can. Even 10 outreach messages is forward progress."


def handle_eod(args):
    ctx = get_context()
    service = get_sheets_service()
    rows = read_tab(service, "Daily Log")
    existing, row_idx = find_today_row(rows, ctx["today"])

    outreach = args.outreach
    meetings = args.meetings
    videos = args.videos
    content = args.content

    if existing:
        update_cell(service, "Daily Log", row_idx, COL_MAP["Outreach_Count"], outreach)
        update_cell(service, "Daily Log", row_idx, COL_MAP["Meetings_Booked"], meetings)
        update_cell(service, "Daily Log", row_idx, COL_MAP["Videos_Filmed"], videos)
        update_cell(service, "Daily Log", row_idx, COL_MAP["Content_Posted"], content)
    else:
        append_row(service, "Daily Log", [
            ctx["today"], ctx["day_number"], ctx["week_number"],
            ctx["day_of_week"], "", outreach, meetings, videos, content, "", ""
        ])

    # Calculate weekly total
    this_week = [r for r in rows if r.get("Week_Number") == str(ctx["week_number"])]
    weekly_outreach = sum(int(r.get("Outreach_Count") or 0) for r in this_week) + outreach

    if outreach >= 120:
        return (
            f"{outreach} outreach — ABOVE TARGET.\n"
            f"This is how you build momentum.\n"
            f'"Simple scales. Fancy fails." — Hormozi\n'
            f"Weekly total: {weekly_outreach}/500."
        )
    elif outreach >= 100:
        return (
            f"Logged. {outreach} outreach (target: 100) — solid.\n"
            f"{meetings} meeting(s) booked. {videos} video(s) filmed.\n"
            f"Running total this week: {weekly_outreach}/500.\n"
            f"Keep going."
        )
    elif outreach > 0:
        shortfall = 100 - outreach
        return (
            f"Logged. {outreach} outreach (target: 100) — {shortfall} short.\n"
            f"Volume solves all problems. Tomorrow: make up the gap.\n"
            f"Weekly total: {weekly_outreach}/500."
        )
    else:
        return (
            f"Logged. 0 outreach today.\n"
            f"{meetings} meeting(s), {videos} video(s), {content} content.\n"
            f"Everyone has off days. Reset tonight, attack tomorrow."
        )


def handle_status(args):
    ctx = get_context()
    service = get_sheets_service()
    rows = read_tab(service, "Daily Log")
    goals = read_tab(service, "90-Day Goals")

    this_week = [r for r in rows if r.get("Week_Number") == str(ctx["week_number"])]
    wo = sum(int(r.get("Outreach_Count") or 0) for r in this_week)
    wm = sum(int(r.get("Meetings_Booked") or 0) for r in this_week)
    wv = sum(int(r.get("Videos_Filmed") or 0) for r in this_week)

    return (
        f"Day {ctx['day_number']}/90 | Week {ctx['week_number']}/12\n\n"
        f"This week so far:\n"
        f"  Outreach: {wo} / 500\n"
        f"  Meetings: {wm} / 3-5\n"
        f"  Videos: {wv} / 2\n\n"
        f"90-day progress:\n"
        f"  Clients: {goals[0].get('Current', '0') if goals else '0'} / {goals[0].get('Target', '3') if goals else '3'}\n"
        f"  YouTube: {goals[1].get('Current', '0') if goals else '0'} / {goals[1].get('Target', '500') if goals else '500'}\n\n"
        f"Days remaining: {ctx['days_remaining']}"
    )


def handle_goals(args):
    ctx = get_context()
    service = get_sheets_service()
    goals = read_tab(service, "90-Day Goals")

    msg = f"90-DAY GOALS (Day {ctx['day_number']}/84)\n\n"
    for i, g in enumerate(goals):
        msg += f"{i+1}. {g.get('Goal', '?')}\n   {g.get('Current', 'Not started')} / {g.get('Target', '?')}\n\n"
    msg += f"Days remaining: {ctx['days_remaining']}"
    return msg


def handle_training(args):
    ctx = get_context()
    service = get_sheets_service()
    rows = read_tab(service, "Daily Log")
    existing, row_idx = find_today_row(rows, ctx["today"])

    if existing:
        update_cell(service, "Daily Log", row_idx, COL_MAP["Training_Session"], "TRUE")
    else:
        append_row(service, "Daily Log", [
            ctx["today"], ctx["day_number"], ctx["week_number"],
            ctx["day_of_week"], "", "", "", "", "", "TRUE", ""
        ])

    this_week = [r for r in rows if r.get("Week_Number") == str(ctx["week_number"])]
    train_count = sum(1 for r in this_week if r.get("Training_Session") == "TRUE") + 1
    return f"Training logged. {train_count}/5 this week."


def handle_note(args):
    ctx = get_context()
    service = get_sheets_service()
    rows = read_tab(service, "Daily Log")
    existing, row_idx = find_today_row(rows, ctx["today"])

    if existing:
        old_note = existing.get("Notes", "")
        new_note = f"{old_note}; {args.note}" if old_note else args.note
        update_cell(service, "Daily Log", row_idx, COL_MAP["Notes"], new_note)
    else:
        append_row(service, "Daily Log", [
            ctx["today"], ctx["day_number"], ctx["week_number"],
            ctx["day_of_week"], "", "", "", "", "", "", args.note
        ])
    return "Noted."


def handle_outreach_only(args):
    ctx = get_context()
    service = get_sheets_service()
    rows = read_tab(service, "Daily Log")
    existing, row_idx = find_today_row(rows, ctx["today"])

    if existing:
        update_cell(service, "Daily Log", row_idx, COL_MAP["Outreach_Count"], args.outreach)
    else:
        append_row(service, "Daily Log", [
            ctx["today"], ctx["day_number"], ctx["week_number"],
            ctx["day_of_week"], "", args.outreach, 0, 0, 0, "", ""
        ])
    return f"Logged {args.outreach} outreach. Send meetings, videos, content numbers if you have them — or I'll keep zeros."


def handle_fix(args):
    ctx = get_context()
    service = get_sheets_service()
    rows = read_tab(service, "Daily Log")
    existing, row_idx = find_today_row(rows, ctx["today"])

    field_map = {
        "outreach": "Outreach_Count",
        "meetings": "Meetings_Booked",
        "videos": "Videos_Filmed",
        "content": "Content_Posted",
        "energy": "Morning_Energy",
    }

    col_name = field_map.get(args.field)
    if not col_name:
        return f"Unknown field: {args.field}. Use: outreach, meetings, videos, content, energy."

    if existing:
        update_cell(service, "Daily Log", row_idx, COL_MAP[col_name], args.fix_value)
        return f"Updated {args.field} to {args.fix_value} for today."
    else:
        return "No entry for today yet. Log your numbers first."


def handle_parse(args):
    """Auto-detect message type from raw text and handle accordingly."""
    text = args.text.strip()

    # Energy (1-10)
    m = re.match(r"^\s*([1-9]|10)\s*$", text)
    if m:
        args.type = "energy"
        args.value = int(m.group(1))
        return handle_energy(args)

    # EOD (4 comma-separated numbers)
    m = re.match(r"^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*$", text)
    if m:
        args.type = "eod"
        args.outreach = int(m.group(1))
        args.meetings = int(m.group(2))
        args.videos = int(m.group(3))
        args.content = int(m.group(4))
        return handle_eod(args)

    # Status commands
    m = re.match(r"^\s*(status|dashboard|how am i doing|numbers|scorecard|goals)\s*[?]?\s*$", text, re.I)
    if m:
        cmd = m.group(1).lower()
        if cmd == "goals":
            return handle_goals(args)
        return handle_status(args)

    # Single large number (outreach)
    m = re.match(r"^\s*(\d+)\s*$", text)
    if m and int(m.group(1)) > 10:
        args.outreach = int(m.group(1))
        return handle_outreach_only(args)

    # Note
    m = re.match(r"^\s*notes?:\s*(.+)$", text, re.I | re.S)
    if m:
        args.note = m.group(1).strip()
        return handle_note(args)

    # Training
    m = re.match(r"^\s*(trained|trained today|workout done|gym done|session done)\s*$", text, re.I)
    if m:
        return handle_training(args)

    # Fix/correct
    m = re.match(r"^\s*(fix|correct|update)\s+(outreach|meetings|videos|content|energy)\s+(\d+)\s*$", text, re.I)
    if m:
        args.field = m.group(2).lower()
        args.fix_value = int(m.group(3))
        return handle_fix(args)

    return None  # Not an accountability message


def main():
    parser = argparse.ArgumentParser(description="Accountability system handler")
    parser.add_argument("--type", required=True,
                        choices=["energy", "eod", "status", "goals", "training",
                                 "note", "outreach_only", "fix", "parse"])
    parser.add_argument("--value", type=int, help="Energy level 1-10")
    parser.add_argument("--outreach", type=int, default=0)
    parser.add_argument("--meetings", type=int, default=0)
    parser.add_argument("--videos", type=int, default=0)
    parser.add_argument("--content", type=int, default=0)
    parser.add_argument("--note", type=str, default="")
    parser.add_argument("--field", type=str, default="")
    parser.add_argument("--fix-value", type=int, default=0)
    parser.add_argument("--text", type=str, default="", help="Raw message text for parse mode")

    args = parser.parse_args()

    handlers = {
        "energy": handle_energy,
        "eod": handle_eod,
        "status": handle_status,
        "goals": handle_goals,
        "training": handle_training,
        "note": handle_note,
        "outreach_only": handle_outreach_only,
        "fix": handle_fix,
        "parse": handle_parse,
    }

    try:
        result = handlers[args.type](args)
        if result is None:
            print("NOT_ACCOUNTABILITY")
        else:
            print(result)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
