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
    python3 execution/accountability_handler.py --type morning_briefing
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import stripe as stripe_lib
    stripe_lib.api_key = os.getenv("STRIPE_SECRET_KEY", "")
    HAS_STRIPE = bool(stripe_lib.api_key)
except ImportError:
    HAS_STRIPE = False

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

# Find token files
PROJECT_ROOT = Path(__file__).parent.parent
TOKEN_CANDIDATES = [
    PROJECT_ROOT / "token_sheets.json",
    Path.home() / "dev-sandbox" / "token_sheets.json",
    Path("/home/clawdbot/dev-sandbox/token_sheets.json"),
]

CALENDAR_TOKEN_CANDIDATES = [
    PROJECT_ROOT / "token_marceausolutions.json",
    Path.home() / "dev-sandbox" / "token_marceausolutions.json",
    Path("/home/clawdbot/dev-sandbox/token_marceausolutions.json"),
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


def get_calendar_service():
    """Get Google Calendar API service."""
    token_file = None
    for candidate in CALENDAR_TOKEN_CANDIDATES:
        if candidate.exists():
            token_file = candidate
            break
    if not token_file:
        return None

    try:
        creds = Credentials.from_authorized_user_file(
            str(token_file), ["https://www.googleapis.com/auth/calendar"]
        )
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_file, "w") as f:
                f.write(creds.to_json())
        return build("calendar", "v3", credentials=creds)
    except Exception:
        return None


def get_todays_events():
    """Fetch today's calendar events. Returns formatted string or empty string."""
    cal_service = get_calendar_service()
    if not cal_service:
        return ""

    try:
        now = datetime.utcnow()
        start = now.replace(hour=9, minute=0, second=0).isoformat() + "Z"  # 5am ET = 9 UTC
        end = (now.replace(hour=9, minute=0, second=0) + timedelta(hours=19)).isoformat() + "Z"  # through midnight ET

        events = cal_service.events().list(
            calendarId="primary",
            timeMin=start,
            timeMax=end,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        items = events.get("items", [])

        if not items:
            return ""

        lines = []
        for e in items:
            start_raw = e["start"].get("dateTime", e["start"].get("date", ""))
            summary = e.get("summary", "(no title)")
            location = e.get("location", "")
            description = e.get("description", "")

            # Format time
            if "T" in start_raw:
                try:
                    dt = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
                    time_str = dt.strftime("%-I:%M%p").lower()
                except Exception:
                    time_str = start_raw.split("T")[1][:5]
            else:
                time_str = "all day"

            line = f"  {time_str}: {summary}"
            if location:
                line += f" ({location})"
            lines.append(line)

            # Flag important items
            lower_summary = summary.lower()
            if any(w in lower_summary for w in ["meeting", "call", "interview", "doctor", "appointment", "treatment"]):
                lines.append(f"    ^ IMPORTANT — be prepared for this")

        return "\n".join(lines)
    except Exception:
        return ""


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
        .get(spreadsheetId=SCORECARD_SHEET_ID, range=f"{tab_name}!A:O")
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
        range=f"{tab_name}!A:O",
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
# Columns L-O are new integrations added 2026-03-21
COL_MAP = {
    "Date": "A", "Day_Number": "B", "Week_Number": "C", "Day_of_Week": "D",
    "Morning_Energy": "E", "Outreach_Count": "F", "Meetings_Booked": "G",
    "Videos_Filmed": "H", "Content_Posted": "I", "Training_Session": "J", "Notes": "K",
    "Pain_Level": "L", "Sleep_Quality": "M", "Training_Details": "N", "MRR_Snapshot": "O",
}


def get_stripe_mrr():
    """Fetch current MRR from active Stripe subscriptions."""
    if not HAS_STRIPE:
        return None
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent.parent / ".env")
        stripe_lib.api_key = os.getenv("STRIPE_SECRET_KEY", "")
        if not stripe_lib.api_key:
            return None

        subs = stripe_lib.Subscription.list(status="active", limit=100)
        mrr_cents = 0
        for sub in subs.auto_paging_iter():
            for item in sub["items"]["data"]:
                amount = item["price"]["unit_amount"] or 0
                interval = item["price"]["recurring"]["interval"]
                if interval == "year":
                    mrr_cents += amount / 12
                elif interval == "month":
                    mrr_cents += amount
                elif interval == "week":
                    mrr_cents += amount * 4.33
        return round(mrr_cents / 100, 2)
    except Exception:
        return None


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
            ctx["day_of_week"], args.value, "", "", "", "", "", "",
            "", "", "", ""
        ])

    energy = args.value
    # Check if pain was already logged today — make response health-aware
    pain_today = None
    if existing:
        pain_today = existing.get("Pain_Level", "")
        if pain_today:
            try:
                pain_today = int(pain_today)
            except (ValueError, TypeError):
                pain_today = None

    if pain_today and pain_today >= 7:
        # High pain day — adjust expectations
        if energy >= 5:
            return (f"Energy {energy} with pain at {pain_today} — you're pushing through. "
                    f"Focus on what you can control. Even 30 outreach is a win today.")
        else:
            return (f"Energy {energy}, pain {pain_today}. Rough day. "
                    f"Do what you can without making it worse. Rest is productive too.")
    elif energy >= 8:
        return "High energy day. Channel it into outreach volume."
    elif energy >= 5:
        return "Solid. Execute the fundamentals today."
    elif energy >= 3:
        return "Low energy. Do the minimum: 50 outreach, 1 video. Rest is legit."
    else:
        return "Rough day. Do what you can. Even 10 outreach messages is forward progress."


def handle_pain(args):
    """Log pain level (1-10) for dystonia tracking."""
    ctx = get_context()
    service = get_sheets_service()
    rows = read_tab(service, "Daily Log")
    existing, row_idx = find_today_row(rows, ctx["today"])

    pain = args.pain_value

    if existing:
        update_cell(service, "Daily Log", row_idx, COL_MAP["Pain_Level"], pain)
    else:
        append_row(service, "Daily Log", [
            ctx["today"], ctx["day_number"], ctx["week_number"],
            ctx["day_of_week"], "", "", "", "", "", "", "",
            pain, "", "", ""
        ])

    # Calculate recent pain trend
    recent = rows[-7:] if len(rows) >= 7 else rows
    recent_pain = [int(r.get("Pain_Level", 0)) for r in recent if r.get("Pain_Level")]
    avg_pain = round(sum(recent_pain) / len(recent_pain), 1) if recent_pain else None

    if pain >= 8:
        response = (f"Pain {pain}/10. Bad day. Prioritize rest and pain management. "
                    f"Outreach can wait — your health can't.")
    elif pain >= 6:
        response = (f"Pain {pain}/10. Moderate-high. Lighter day — "
                    f"do what you can without pushing through pain that'll compound tomorrow.")
    elif pain >= 4:
        response = f"Pain {pain}/10. Manageable. Execute the plan."
    else:
        response = f"Pain {pain}/10. Good day — take advantage of it."

    if avg_pain is not None:
        trend = "↑" if pain > avg_pain else "↓" if pain < avg_pain else "→"
        response += f"\n7-day avg: {avg_pain} {trend}"

    return response


def handle_sleep(args):
    """Log sleep quality (1-10)."""
    ctx = get_context()
    service = get_sheets_service()
    rows = read_tab(service, "Daily Log")
    existing, row_idx = find_today_row(rows, ctx["today"])

    sleep = args.sleep_value

    if existing:
        update_cell(service, "Daily Log", row_idx, COL_MAP["Sleep_Quality"], sleep)
    else:
        append_row(service, "Daily Log", [
            ctx["today"], ctx["day_number"], ctx["week_number"],
            ctx["day_of_week"], "", "", "", "", "", "", "",
            "", sleep, "", ""
        ])

    if sleep >= 8:
        return f"Sleep {sleep}/10. Well rested — make it count."
    elif sleep >= 5:
        return f"Sleep {sleep}/10. Decent. Execute."
    else:
        return f"Sleep {sleep}/10. Rough night. Caffeine, light exposure, keep it simple today."


def handle_eod(args):
    ctx = get_context()
    service = get_sheets_service()
    rows = read_tab(service, "Daily Log")
    existing, row_idx = find_today_row(rows, ctx["today"])

    outreach = args.outreach
    meetings = args.meetings
    videos = args.videos
    content = args.content

    # Handle trained field if provided
    trained = getattr(args, 'trained', None)
    
    if existing:
        update_cell(service, "Daily Log", row_idx, COL_MAP["Outreach_Count"], outreach)
        update_cell(service, "Daily Log", row_idx, COL_MAP["Meetings_Booked"], meetings)
        update_cell(service, "Daily Log", row_idx, COL_MAP["Videos_Filmed"], videos)
        update_cell(service, "Daily Log", row_idx, COL_MAP["Content_Posted"], content)
        if trained is not None:
            update_cell(service, "Daily Log", row_idx, COL_MAP["Training_Session"], "TRUE" if trained else "FALSE")
    else:
        append_row(service, "Daily Log", [
            ctx["today"], ctx["day_number"], ctx["week_number"],
            ctx["day_of_week"], "", outreach, meetings, videos, content, "", ""
        ])

    # Calculate weekly total
    this_week = [r for r in rows if r.get("Week_Number") == str(ctx["week_number"])]
    weekly_outreach = sum(int(r.get("Outreach_Count") or 0) for r in this_week) + outreach

    # Check milestones
    milestone_msg = check_milestones(service, rows, outreach, meetings)

    # Calculate conversion rate
    total_outreach = sum(int(r.get("Outreach_Count") or 0) for r in rows) + outreach
    total_meetings = sum(int(r.get("Meetings_Booked") or 0) for r in rows) + meetings
    conversion_pct = round((total_meetings / total_outreach * 100), 2) if total_outreach > 0 else 0

    # Check today's pain level for health-aware response
    existing_row, _ = find_today_row(rows, ctx["today"])
    pain_today = None
    if existing_row:
        try:
            pain_today = int(existing_row.get("Pain_Level") or 0)
        except (ValueError, TypeError):
            pain_today = None

    # Training status line
    train_line = ""
    if trained is not None:
        train_line = "\n💪 Trained today." if trained else "\n⏸️ Rest day (no training)."
    
    if pain_today and pain_today >= 7 and outreach > 0:
        # High pain day — celebrate whatever they did
        response = (
            f"Pain day and you still put in {outreach} outreach. That's discipline.\n"
            f"{meetings} meeting(s), {videos} video(s), {content} content.\n"
            f"Weekly total: {weekly_outreach}/500.\n"
            f"Conversion rate: {conversion_pct}% ({total_meetings} meetings / {total_outreach} outreach)"
            f"{train_line}"
        )
    elif outreach >= 120:
        response = (
            f"{outreach} outreach — ABOVE TARGET.\n"
            f"This is how you build momentum.\n"
            f'"Simple scales. Fancy fails." — Hormozi\n'
            f"Weekly total: {weekly_outreach}/500.\n"
            f"Conversion rate: {conversion_pct}% ({total_meetings}/{total_outreach})"
            f"{train_line}"
        )
    elif outreach >= 100:
        response = (
            f"Logged. {outreach} outreach (target: 100) — solid.\n"
            f"{meetings} meeting(s) booked. {videos} video(s) filmed.\n"
            f"Running total this week: {weekly_outreach}/500.\n"
            f"Conversion rate: {conversion_pct}%"
            f"{train_line}"
        )
    elif outreach > 0:
        shortfall = 100 - outreach
        response = (
            f"Logged. {outreach} outreach (target: 100) — {shortfall} short.\n"
            f"Volume solves all problems. Tomorrow: make up the gap.\n"
            f"Weekly total: {weekly_outreach}/500.\n"
            f"Conversion rate: {conversion_pct}%"
            f"{train_line}"
        )
    else:
        response = (
            f"Logged. 0 outreach today.\n"
            f"{meetings} meeting(s), {videos} video(s), {content} content.\n"
            f"Everyone has off days. Reset tonight, attack tomorrow."
            f"{train_line}"
        )

    if milestone_msg:
        response += f"\n\n{milestone_msg}"
    return response


def check_milestones(service, rows, new_outreach, new_meetings):
    """Check if any milestones were just crossed. Returns celebration message or empty string."""
    milestones = read_tab(service, "Milestones")
    achieved = {m.get("Milestone_ID"): m.get("Achieved") == "TRUE" for m in milestones}

    cumulative_outreach = sum(int(r.get("Outreach_Count") or 0) for r in rows) + new_outreach
    cumulative_meetings = sum(int(r.get("Meetings_Booked") or 0) for r in rows) + new_meetings

    celebrations = []

    # Milestone 1: First Discovery Call
    if cumulative_meetings >= 1 and not achieved.get("1"):
        celebrations.append(
            "FIRST CALL BOOKED. This is where it starts. "
            "Every empire began with one conversation. Go crush it."
        )
        mark_milestone(service, "1")

    # Milestone 6: 500 Outreach Messages
    if cumulative_outreach >= 500 and not achieved.get("6"):
        celebrations.append(
            "500 MESSAGES SENT. Your pitch is 10x better than message #1. "
            "Your fear of rejection is gone. That's 500 reps of the most important "
            "skill in business: ASKING. Next stop: 1,000."
        )
        mark_milestone(service, "6")

    if celebrations:
        return "\n\n".join(celebrations)
    return ""


def mark_milestone(service, milestone_id):
    """Mark a milestone as achieved in the Milestones tab."""
    milestones = read_tab(service, "Milestones")
    for i, m in enumerate(milestones):
        if m.get("Milestone_ID") == milestone_id:
            row_idx = i + 2  # +2 for header + 0-index
            update_cell(service, "Milestones", row_idx, "D", "TRUE")  # Achieved
            update_cell(service, "Milestones", row_idx, "E", datetime.now().strftime("%Y-%m-%d"))  # Achieved_Date
            update_cell(service, "Milestones", row_idx, "F", "TRUE")  # Celebration_Sent
            break


def handle_status(args):
    ctx = get_context()
    service = get_sheets_service()
    rows = read_tab(service, "Daily Log")
    goals = read_tab(service, "90-Day Goals")

    this_week = [r for r in rows if r.get("Week_Number") == str(ctx["week_number"])]
    wo = sum(int(r.get("Outreach_Count") or 0) for r in this_week)
    wm = sum(int(r.get("Meetings_Booked") or 0) for r in this_week)
    wv = sum(int(r.get("Videos_Filmed") or 0) for r in this_week)

    # New metrics
    wt = sum(1 for r in this_week if r.get("Training_Session") == "TRUE")
    total_outreach = sum(int(r.get("Outreach_Count") or 0) for r in rows)
    total_meetings = sum(int(r.get("Meetings_Booked") or 0) for r in rows)
    conversion = round((total_meetings / total_outreach * 100), 2) if total_outreach > 0 else 0

    # Pain/sleep averages
    recent = rows[-7:] if len(rows) >= 7 else rows
    recent_pain = [int(r.get("Pain_Level", 0)) for r in recent if r.get("Pain_Level")]
    avg_pain = round(sum(recent_pain) / len(recent_pain), 1) if recent_pain else "—"
    recent_sleep = [int(r.get("Sleep_Quality", 0)) for r in recent if r.get("Sleep_Quality")]
    avg_sleep = round(sum(recent_sleep) / len(recent_sleep), 1) if recent_sleep else "—"

    # MRR
    mrr = get_stripe_mrr()
    mrr_str = f"${mrr:,.0f}" if mrr else "—"

    return (
        f"Day {ctx['day_number']}/90 | Week {ctx['week_number']}/12\n\n"
        f"REVENUE: {mrr_str} / $3,000 MRR\n\n"
        f"This week:\n"
        f"  Outreach: {wo} / 500\n"
        f"  Meetings: {wm} / 3-5\n"
        f"  Videos: {wv} / 2\n"
        f"  Training: {wt} / 5\n\n"
        f"All-time:\n"
        f"  Conversion: {conversion}% ({total_meetings} meetings / {total_outreach} outreach)\n\n"
        f"Health (7-day avg):\n"
        f"  Pain: {avg_pain}/10\n"
        f"  Sleep: {avg_sleep}/10\n\n"
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

    # Check for training details (e.g., "trained — push day, bench 225 3x5")
    details = getattr(args, "training_details", "") or ""

    if existing:
        update_cell(service, "Daily Log", row_idx, COL_MAP["Training_Session"], "TRUE")
        if details:
            update_cell(service, "Daily Log", row_idx, COL_MAP["Training_Details"], details)
    else:
        append_row(service, "Daily Log", [
            ctx["today"], ctx["day_number"], ctx["week_number"],
            ctx["day_of_week"], "", "", "", "", "", "TRUE", "",
            "", "", details, ""
        ])

    this_week = [r for r in rows if r.get("Week_Number") == str(ctx["week_number"])]
    train_count = sum(1 for r in this_week if r.get("Training_Session") == "TRUE") + 1

    response = f"Training logged. {train_count}/5 this week."
    if details:
        response += f"\nDetails: {details}"

    # Show weekly training summary
    week_details = [r.get("Training_Details", "") for r in this_week if r.get("Training_Session") == "TRUE" and r.get("Training_Details")]
    if week_details:
        response += f"\nThis week's sessions: {', '.join(week_details)}"

    return response


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
        "pain": "Pain_Level",
        "sleep": "Sleep_Quality",
    }

    col_name = field_map.get(args.field)
    if not col_name:
        return f"Unknown field: {args.field}. Use: outreach, meetings, videos, content, energy, pain, sleep."

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

    # EOD (4 or 5 comma-separated numbers - 5th is trained 0/1)
    m = re.match(r"^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d+))?\s*$", text)
    if m:
        args.type = "eod"
        args.outreach = int(m.group(1))
        args.meetings = int(m.group(2))
        args.videos = int(m.group(3))
        args.content = int(m.group(4))
        args.trained = int(m.group(5)) if m.group(5) else None
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

    # Pain level: "pain 7" or "pain: 7" or "pain level 7"
    m = re.match(r"^\s*pain\s*:?\s*(?:level\s*:?\s*)?([1-9]|10)\s*$", text, re.I)
    if m:
        args.pain_value = int(m.group(1))
        return handle_pain(args)

    # Sleep quality: "sleep 7" or "sleep: 8" or "slept 6"
    m = re.match(r"^\s*(?:sleep|slept)\s*:?\s*(?:quality\s*:?\s*)?([1-9]|10)\s*$", text, re.I)
    if m:
        args.sleep_value = int(m.group(1))
        return handle_sleep(args)

    # Training with details: "trained — push day, bench 225 3x5" or "gym done — legs"
    m = re.match(r"^\s*(trained|trained today|workout done|gym done|session done)\s*[-—:]\s*(.+)$", text, re.I)
    if m:
        args.training_details = m.group(2).strip()
        return handle_training(args)

    # Training (simple)
    m = re.match(r"^\s*(trained|trained today|workout done|gym done|session done)\s*$", text, re.I)
    if m:
        args.training_details = ""
        return handle_training(args)

    # Fix/correct
    m = re.match(r"^\s*(fix|correct|update)\s+(outreach|meetings|videos|content|energy)\s+(\d+)\s*$", text, re.I)
    if m:
        args.field = m.group(2).lower()
        args.fix_value = int(m.group(3))
        return handle_fix(args)

    # Todo commands
    m = re.match(r"^\s*todo\s+add\s+(.+)$", text, re.I)
    if m:
        args.task = m.group(1).strip()
        args.priority = 0
        # Check for priority prefix like "p1:" or "#1"
        pm = re.match(r"^(?:p|#)(\d)\s*:?\s*(.+)$", args.task, re.I)
        if pm:
            args.priority = int(pm.group(1))
            args.task = pm.group(2).strip()
        return handle_todo_add(args)

    if re.match(r"^\s*(todo|tasks|my tasks|todo list|task list)\s*$", text, re.I):
        return handle_todo_list(args)

    m = re.match(r"^\s*(?:todo\s+)?done\s+#?(\d+)\s*$", text, re.I)
    if m:
        args.task_id = int(m.group(1))
        return handle_todo_done(args)

    m = re.match(r"^\s*(?:todo\s+)?remove\s+#?(\d+)\s*$", text, re.I)
    if m:
        args.task_id = int(m.group(1))
        return handle_todo_remove(args)

    return None  # Not an accountability message


def handle_morning_briefing(args):
    """Generate a complete morning briefing: calendar + accountability metrics."""
    ctx = get_context()
    service = get_sheets_service()
    rows = read_tab(service, "Daily Log")
    goals = read_tab(service, "90-Day Goals")
    content = read_tab(service, "Content Calendar")

    day_of_week = ctx["day_of_week"]

    # Weekly totals
    this_week = [r for r in rows if r.get("Week_Number") == str(ctx["week_number"])]
    weekly_outreach = sum(int(r.get("Outreach_Count") or 0) for r in this_week)
    weekly_meetings = sum(int(r.get("Meetings_Booked") or 0) for r in this_week)
    weekly_videos = sum(int(r.get("Videos_Filmed") or 0) for r in this_week)

    # Goal data
    client_goal = next((g for g in goals if "AI services" in g.get("Goal", "")), {})
    current_clients = client_goal.get("Current", "0 clients")

    # Next video topic
    next_video = next(
        (c for c in content if c.get("Published") != "TRUE" and c.get("Video_Type") == "Long-form"),
        {},
    )
    next_video_topic = next_video.get("Video_Topic", "Check content calendar")

    total_meetings = sum(int(r.get("Meetings_Booked") or 0) for r in rows)

    # Stripe MRR
    mrr = get_stripe_mrr()
    mrr_str = f"${mrr:,.0f}" if mrr else "—"

    # Yesterday's pain (for trend awareness)
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday_row, _ = find_today_row(rows, yesterday)
    yesterday_pain = None
    if yesterday_row:
        try:
            yesterday_pain = int(yesterday_row.get("Pain_Level") or 0)
        except (ValueError, TypeError):
            yesterday_pain = None

    # Recent pain average (7 days)
    recent = rows[-7:] if len(rows) >= 7 else rows
    recent_pain = [int(r.get("Pain_Level", 0)) for r in recent if r.get("Pain_Level")]
    avg_pain = round(sum(recent_pain) / len(recent_pain), 1) if recent_pain else None

    # Recent sleep average
    recent_sleep = [int(r.get("Sleep_Quality", 0)) for r in recent if r.get("Sleep_Quality")]
    avg_sleep = round(sum(recent_sleep) / len(recent_sleep), 1) if recent_sleep else None

    # Training this week
    training_this_week = sum(1 for r in this_week if r.get("Training_Session") == "TRUE")

    # Cumulative conversion rate
    all_outreach = sum(int(r.get("Outreach_Count") or 0) for r in rows)
    all_meetings_total = sum(int(r.get("Meetings_Booked") or 0) for r in rows)
    conversion = round((all_meetings_total / all_outreach * 100), 2) if all_outreach > 0 else 0

    # Build header
    header = f"Day {ctx['day_number']}/90 · Week {ctx['week_number']}/12 · MRR: {mrr_str}/$3,000"
    parts = [header]

    # Log MRR snapshot
    if mrr is not None:
        existing_today, today_row_idx = find_today_row(rows, ctx["today"])
        if existing_today and today_row_idx:
            try:
                update_cell(service, "Daily Log", today_row_idx, COL_MAP["MRR_Snapshot"], mrr)
            except Exception:
                pass

    # Calendar section
    calendar_text = get_todays_events()
    if calendar_text:
        parts.append(f"\nTODAY'S CALENDAR:\n{calendar_text}")
    else:
        parts.append(f"\nNo calendar events today.")

    # Day-specific focus
    if day_of_week == "Monday":
        parts.append(
            f"\nAI Services: {current_clients} (goal: 3)\n"
            f"TODAY: Outreach blitz + offer assets.\n"
            f"100 outreach minimum. This is the Rule of 100."
        )
    elif day_of_week == "Tuesday":
        parts.append(
            f"\nContent day.\n"
            f"Film topic: {next_video_topic}\n"
            f"Outreach blitz first — 100 minimum."
        )
    elif day_of_week == "Wednesday":
        parts.append(
            f"\nNaples day.\n"
            f"5 businesses in person.\n"
            f"Pipeline: {total_meetings} total meetings booked."
        )
    elif day_of_week == "Thursday":
        parts.append(
            f"\nOutreach + Film Day #2.\n"
            f"{weekly_meetings} meetings booked this week (target: 3-5).\n"
            f"{ctx['days_remaining']} days left in the plan."
        )
    elif day_of_week == "Friday":
        parts.append(
            f"\nLighter day — 50 outreach.\n"
            f"This week:\n"
            f"  Outreach: {weekly_outreach}\n"
            f"  Meetings: {weekly_meetings}\n"
            f"  Videos: {weekly_videos}"
        )
    elif day_of_week == "Saturday":
        parts.append(
            f"\nSaturday — content catch-up + recovery.\n"
            f"This week so far:\n"
            f"  Outreach: {weekly_outreach}/500\n"
            f"  Meetings: {weekly_meetings}/3-5\n"
            f"  Videos: {weekly_videos}/2"
        )

    # Health metrics section
    health_parts = []
    if avg_pain is not None:
        health_parts.append(f"Pain avg (7d): {avg_pain}/10")
        if yesterday_pain and yesterday_pain >= 7:
            health_parts.append(f"Yesterday's pain was {yesterday_pain} — take it easy if needed")
    if avg_sleep is not None:
        health_parts.append(f"Sleep avg (7d): {avg_sleep}/10")
    if training_this_week > 0:
        health_parts.append(f"Training: {training_this_week}/5 this week")
    if conversion > 0:
        health_parts.append(f"Conversion rate: {conversion}% ({all_meetings_total} meetings / {all_outreach} outreach)")

    if health_parts:
        parts.append(f"\nMETRICS:\n  " + "\n  ".join(health_parts))

    # Tasks section
    tasks_summary = get_pending_todos_summary()
    if tasks_summary:
        parts.append(f"\nTASKS:\n{tasks_summary}")

    parts.append(f"\nPain level? (1-10)  ·  Sleep quality? (1-10)  ·  Energy? (1-10)")

    return "\n".join(parts)


# =============================================================================
# TODO LIST SYSTEM
# =============================================================================

# Uses the FitAI task system as single source of truth (no duplicate systems)
TASKS_FILE_CANDIDATES = [
    PROJECT_ROOT / "projects" / "marceau-solutions" / "fitness" / "tools" / "fitness-influencer" / "data" / "tenants" / "wmarceau" / "tasks.json",
    Path.home() / "dev-sandbox" / "projects" / "marceau-solutions" / "fitness" / "tools" / "fitness-influencer" / "data" / "tenants" / "wmarceau" / "tasks.json",
    Path("/home/clawdbot/dev-sandbox/projects/marceau-solutions/fitness/tools/fitness-influencer/data/tenants/wmarceau/tasks.json"),
]


def get_todo_file():
    """Find the FitAI tasks.json file."""
    for candidate in TASKS_FILE_CANDIDATES:
        if candidate.exists():
            return candidate
    # Create with compatible format if none exists
    for candidate in TASKS_FILE_CANDIDATES:
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            candidate.write_text(json.dumps({"tenant_id": "wmarceau", "tasks": []}))
            return candidate
        except OSError:
            continue
    raise FileNotFoundError("Cannot find or create tasks.json")


def load_todos():
    todo_file = get_todo_file()
    with open(todo_file) as f:
        data = json.load(f)
    # Normalize: FitAI format uses "tasks" list, ensure next_id exists
    if "next_id" not in data:
        # Calculate next ID from existing tasks
        max_id = 0
        for t in data.get("tasks", []):
            tid = t.get("id", "")
            if isinstance(tid, str) and tid.startswith("task_"):
                try:
                    max_id = max(max_id, int(tid.split("_")[-1]))
                except ValueError:
                    pass
            elif isinstance(tid, int):
                max_id = max(max_id, tid)
        data["next_id"] = max_id + 1
    return data


def save_todos(data):
    todo_file = get_todo_file()
    # Remove next_id before saving (not part of FitAI format)
    save_data = {k: v for k, v in data.items() if k != "next_id"}
    with open(todo_file, "w") as f:
        json.dump(save_data, f, indent=2)


def handle_todo_add(args):
    """Add a task to the todo list (FitAI-compatible format)."""
    if not args.task:
        return "No task provided. Usage: todo add Buy groceries"

    data = load_todos()
    task_id = data["next_id"]

    # Priority mapping: 1-2=critical, 3=high, 4-5=medium, 6+=low
    priority_str = "high"
    section = "today"
    if args.priority > 0:
        if args.priority <= 2:
            priority_str = "critical"
            section = "today"
        elif args.priority <= 3:
            priority_str = "high"
            section = "today"
        elif args.priority <= 5:
            priority_str = "medium"
            section = "this_week"
        else:
            priority_str = "low"
            section = "circle_back"

    task = {
        "id": f"task_acc_{task_id:03d}",
        "title": args.task,
        "description": "",
        "section": section,
        "priority": priority_str,
        "status": "pending",
        "due_date": None,
        "trigger_condition": None,
        "tags": ["accountability"],
        "project": "accountability",
        "progress": 0,
        "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "completed_at": None,
    }
    data["tasks"].append(task)
    data["next_id"] = task_id + 1
    save_todos(data)
    return f"Added: {args.task} [{priority_str}, {section}]"


def handle_todo_list(args):
    """List all pending tasks, sorted by priority."""
    data = load_todos()
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "deferred": 4}
    pending = [t for t in data["tasks"] if t.get("status") not in ("complete", "cancelled")]

    if not pending:
        return "No tasks on your list. Nice work, or time to add some."

    # Group by section
    sections = {"today": [], "this_week": [], "circle_back": []}
    for t in sorted(pending, key=lambda t: priority_order.get(t.get("priority", "medium"), 2)):
        sec = t.get("section", "this_week")
        sections.setdefault(sec, []).append(t)

    lines = ["YOUR TASKS:\n"]
    for sec_name, sec_label in [("today", "TODAY"), ("this_week", "THIS WEEK"), ("circle_back", "CIRCLE BACK")]:
        tasks = sections.get(sec_name, [])
        if tasks:
            lines.append(f"{sec_label}:")
            for t in tasks:
                tid = t.get("id", "?")
                # Show short ID for readability
                short_id = tid.replace("task_acc_", "#").replace("task_", "#")
                title = t.get("title", t.get("text", "?"))
                pri = t.get("priority", "")
                lines.append(f"  {short_id} [{pri}] {title}")
            lines.append("")

    completed = [t for t in data["tasks"] if t.get("status") == "complete"]
    if completed:
        lines.append(f"Completed total: {len(completed)}")

    return "\n".join(lines)


def handle_todo_done(args):
    """Mark a task as done."""
    data = load_todos()
    target_id = args.task_id
    # Support both numeric and string IDs
    search_ids = [
        str(target_id),
        f"task_acc_{target_id:03d}" if isinstance(target_id, int) else str(target_id),
    ]

    for t in data["tasks"]:
        if t.get("id") in search_ids or str(t.get("id", "")).endswith(f"_{target_id:03d}" if isinstance(target_id, int) else str(target_id)):
            if t.get("status") != "complete":
                t["status"] = "complete"
                t["section"] = "recently_done"
                t["completed_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                t["progress"] = 100
                save_todos(data)
                remaining = len([x for x in data["tasks"] if x.get("status") not in ("complete", "cancelled")])
                title = t.get("title", t.get("text", "?"))
                return f"Done: {title}\n{remaining} task(s) remaining."
    return f"Task #{target_id} not found or already done."


def handle_todo_remove(args):
    """Remove a task entirely."""
    data = load_todos()
    target_id = args.task_id
    original_len = len(data["tasks"])

    data["tasks"] = [
        t for t in data["tasks"]
        if not (str(t.get("id", "")).endswith(f"_{target_id:03d}" if isinstance(target_id, int) else str(target_id))
                or str(t.get("id")) == str(target_id))
    ]

    if len(data["tasks"]) < original_len:
        save_todos(data)
        return f"Removed task #{target_id}."
    return f"Task #{target_id} not found."


def get_pending_todos_summary():
    """Get a brief summary of pending tasks for the morning briefing."""
    try:
        data = load_todos()
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "deferred": 4}
        pending = sorted(
            [t for t in data["tasks"] if t.get("status") not in ("complete", "cancelled")],
            key=lambda t: priority_order.get(t.get("priority", "medium"), 2),
        )
        if not pending:
            return ""

        # Show today's tasks first, then this_week
        today_tasks = [t for t in pending if t.get("section") == "today"]
        week_tasks = [t for t in pending if t.get("section") == "this_week"]

        lines = []
        show_tasks = today_tasks[:5] if today_tasks else week_tasks[:5]
        for t in show_tasks:
            title = t.get("title", t.get("text", "?"))
            pri = t.get("priority", "")
            lines.append(f"  [{pri}] {title}")

        total_pending = len(pending)
        if total_pending > 5:
            lines.append(f"  ...and {total_pending - 5} more")
        return "\n".join(lines)
    except Exception:
        return ""


def main():
    parser = argparse.ArgumentParser(description="Accountability system handler")
    parser.add_argument("--type", required=True,
                        choices=["energy", "eod", "status", "goals", "training",
                                 "note", "outreach_only", "fix", "parse",
                                 "morning_briefing", "pain", "sleep",
                                 "todo_add", "todo_list", "todo_done", "todo_remove"])
    parser.add_argument("--value", type=int, help="Energy level 1-10")
    parser.add_argument("--outreach", type=int, default=0)
    parser.add_argument("--meetings", type=int, default=0)
    parser.add_argument("--videos", type=int, default=0)
    parser.add_argument("--content", type=int, default=0)
    parser.add_argument("--note", type=str, default="")
    parser.add_argument("--field", type=str, default="")
    parser.add_argument("--fix-value", type=int, default=0)
    parser.add_argument("--text", type=str, default="", help="Raw message text for parse mode")
    parser.add_argument("--task", type=str, default="", help="Task description for todo")
    parser.add_argument("--task-id", type=int, default=0, help="Task number for done/remove")
    parser.add_argument("--pain-value", type=int, default=0, help="Pain level 1-10")
    parser.add_argument("--sleep-value", type=int, default=0, help="Sleep quality 1-10")
    parser.add_argument("--training-details", type=str, default="", help="Training session details")
    parser.add_argument("--priority", type=int, default=0, help="Priority (1=highest)")

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
        "morning_briefing": handle_morning_briefing,
        "pain": handle_pain,
        "sleep": handle_sleep,
        "todo_add": handle_todo_add,
        "todo_list": handle_todo_list,
        "todo_done": handle_todo_done,
        "todo_remove": handle_todo_remove,
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
