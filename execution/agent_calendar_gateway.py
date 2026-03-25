#!/usr/bin/env python3
"""
Agent Calendar Gateway — Single entry point for all agent calendar operations.

All agents (Claude Code, Panacea, Ralph) MUST route calendar changes through this
gateway. It validates against conflicts, enforces Time Blocks rules, and logs
every action for cross-agent awareness.

Usage:
    # Start the gateway (runs on port 5015)
    python execution/agent_calendar_gateway.py

    # Create an event (with validation)
    curl -X POST http://localhost:5015/calendar/create \
        -H "Content-Type: application/json" \
        -d '{"agent": "panacea", "calendar": "time_blocks", "summary": "Training", ...}'

    # Check for conflicts on a date
    curl -X POST http://localhost:5015/calendar/check \
        -d '{"date": "2026-03-25"}'

    # View action log
    curl http://localhost:5015/calendar/log

Author: William Marceau Jr. / Claude Code
Created: 2026-03-25
"""

import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request
from flask_cors import CORS

# Google Calendar API
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

app = Flask(__name__)
CORS(app)

# --- Configuration ---

PORT = 5015
DB_PATH = Path(__file__).parent.parent / "data" / "agent_calendar.db"
RULES_PATH = Path(__file__).parent.parent / "rules" / "tools" / "calendar-management.md"

# Calendar IDs
PRIMARY_CAL = "primary"
TIME_BLOCKS_CAL = "c_710cb4eceeac036e44157b8626fe6447b430ce3fd0100020d4b32fc44af1f164@group.calendar.google.com"

CAL_MAP = {
    "primary": PRIMARY_CAL,
    "time_blocks": TIME_BLOCKS_CAL,
}

# Token paths (try multiple locations)
TOKEN_PATHS = [
    Path("/home/clawdbot/dev-sandbox/token_marceausolutions.json"),  # EC2
    Path.home() / "dev-sandbox" / "token_marceausolutions.json",     # Mac
    Path(__file__).parent.parent / "token_marceausolutions.json",    # Relative
]

CREDENTIALS_PATHS = [
    Path("/home/clawdbot/dev-sandbox/credentials.json"),
    Path.home() / "dev-sandbox" / "credentials.json",
    Path(__file__).parent.parent / "credentials.json",
]

# Items that belong on each calendar
TIME_BLOCKS_KEYWORDS = [
    "dog walk", "morning routine", "dashboard review", "outreach blitz",
    "rule of 100", "break", "hand therapy", "lunch", "training",
    "defy the odds", "spanish study", "dog training", "follow-up",
    "quick follow-ups", "proposals", "cold email", "cold call",
    "lead nurturing", "content batch", "sales readiness",
    "discovery calls", "proposal writing",
]

PRIMARY_KEYWORDS = [
    "stop 1", "stop 2", "stop 3", "stop 4", "stop 5",
    "meeting with", "call with", "discovery call —",
    "drive to", "milestone",
]


# --- Database ---

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS action_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            agent TEXT NOT NULL,
            action TEXT NOT NULL,
            calendar TEXT NOT NULL,
            event_summary TEXT,
            event_start TEXT,
            event_end TEXT,
            status TEXT NOT NULL,
            details TEXT
        )
    """)
    conn.commit()
    conn.close()


def log_action(agent: str, action: str, calendar: str, summary: str = "",
               start: str = "", end: str = "", status: str = "success", details: str = ""):
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        INSERT INTO action_log (timestamp, agent, action, calendar, event_summary,
                                event_start, event_end, status, details)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (datetime.now().isoformat(), agent, action, calendar, summary, start, end, status, details))
    conn.commit()
    conn.close()


# --- Google Calendar Service ---

def get_calendar_service():
    """Build Google Calendar API service."""
    token_path = None
    for p in TOKEN_PATHS:
        if p.exists():
            token_path = p
            break

    if not token_path:
        raise RuntimeError(f"No calendar token found. Checked: {TOKEN_PATHS}")

    creds = Credentials.from_authorized_user_file(str(token_path))

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(str(token_path), "w") as f:
            f.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def list_events_for_date(service, calendar_id: str, date_str: str):
    """List all events on a calendar for a given date."""
    time_min = f"{date_str}T00:00:00-04:00"
    time_max = f"{date_str}T23:59:59-04:00"

    result = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    return result.get("items", [])


def check_overlap(existing_events: list, new_start: str, new_end: str) -> list:
    """Check if a proposed event overlaps with existing events."""
    from dateutil import parser as dp

    new_s = dp.parse(new_start)
    new_e = dp.parse(new_end)
    conflicts = []

    for ev in existing_events:
        ev_start = ev.get("start", {}).get("dateTime")
        ev_end = ev.get("end", {}).get("dateTime")
        if not ev_start or not ev_end:
            continue

        ev_s = dp.parse(ev_start)
        ev_e = dp.parse(ev_end)

        # Overlap: new starts before existing ends AND new ends after existing starts
        if new_s < ev_e and new_e > ev_s:
            conflicts.append({
                "summary": ev.get("summary", "Untitled"),
                "start": ev_start,
                "end": ev_end,
                "id": ev.get("id"),
            })

    return conflicts


def validate_calendar_choice(summary: str, requested_calendar: str) -> dict:
    """Validate that the event is going to the right calendar."""
    summary_lower = summary.lower()

    # Check if it looks like a Time Blocks event
    is_routine = any(kw in summary_lower for kw in TIME_BLOCKS_KEYWORDS)
    is_specific = any(kw in summary_lower for kw in PRIMARY_KEYWORDS)

    if is_routine and requested_calendar == "primary":
        return {
            "valid": False,
            "reason": f"'{summary}' looks like a routine block — should go on Time Blocks, not Primary.",
            "suggested_calendar": "time_blocks",
        }

    if is_specific and requested_calendar == "time_blocks":
        return {
            "valid": False,
            "reason": f"'{summary}' looks like a specific event — should go on Primary, not Time Blocks.",
            "suggested_calendar": "primary",
        }

    return {"valid": True}


def validate_training_time(summary: str, start: str) -> dict:
    """Ensure training is never scheduled before noon."""
    if "training" in summary.lower() or "defy the odds" in summary.lower():
        from dateutil import parser as dp
        start_dt = dp.parse(start)
        if start_dt.hour < 12:
            return {
                "valid": False,
                "reason": f"Training scheduled at {start_dt.strftime('%I:%M %p')} — "
                          f"Training is NEVER before noon. Default to 6:00-8:00pm.",
            }
    return {"valid": True}


# --- API Routes ---

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "agent-calendar-gateway", "port": PORT})


@app.route("/calendar/check", methods=["POST"])
def check_conflicts():
    """Check for conflicts on a given date across both calendars."""
    data = request.json or {}
    date_str = data.get("date")
    if not date_str:
        return jsonify({"error": "date required (YYYY-MM-DD)"}), 400

    try:
        service = get_calendar_service()
        primary_events = list_events_for_date(service, PRIMARY_CAL, date_str)
        tb_events = list_events_for_date(service, TIME_BLOCKS_CAL, date_str)
        all_events = primary_events + tb_events

        # Check for overlaps between ALL events
        overlaps = []
        for i, ev1 in enumerate(all_events):
            for ev2 in all_events[i + 1:]:
                s1 = ev1.get("start", {}).get("dateTime")
                e1 = ev1.get("end", {}).get("dateTime")
                s2 = ev2.get("start", {}).get("dateTime")
                e2 = ev2.get("end", {}).get("dateTime")
                if not all([s1, e1, s2, e2]):
                    continue

                from dateutil import parser as dp
                if dp.parse(s1) < dp.parse(e2) and dp.parse(s2) < dp.parse(e1):
                    overlaps.append({
                        "event_1": ev1.get("summary"),
                        "event_1_time": f"{s1} - {e1}",
                        "event_2": ev2.get("summary"),
                        "event_2_time": f"{s2} - {e2}",
                    })

        return jsonify({
            "date": date_str,
            "primary_count": len(primary_events),
            "time_blocks_count": len(tb_events),
            "conflicts": overlaps,
            "conflict_count": len(overlaps),
            "primary_events": [{"summary": e.get("summary"), "start": e.get("start", {}).get("dateTime"), "end": e.get("end", {}).get("dateTime")} for e in primary_events],
            "time_blocks_events": [{"summary": e.get("summary"), "start": e.get("start", {}).get("dateTime"), "end": e.get("end", {}).get("dateTime")} for e in tb_events],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/calendar/create", methods=["POST"])
def create_event():
    """Create a calendar event with full validation."""
    data = request.json or {}

    # Required fields
    agent = data.get("agent", "unknown")
    calendar = data.get("calendar")  # "primary" or "time_blocks"
    summary = data.get("summary")
    start = data.get("start")  # ISO 8601
    end = data.get("end")      # ISO 8601
    description = data.get("description", "")
    location = data.get("location", "")
    force = data.get("force", False)  # Skip validation

    if not all([calendar, summary, start, end]):
        return jsonify({"error": "Required: calendar, summary, start, end"}), 400

    if calendar not in CAL_MAP:
        return jsonify({"error": f"calendar must be 'primary' or 'time_blocks', got '{calendar}'"}), 400

    cal_id = CAL_MAP[calendar]
    errors = []

    if not force:
        # Validation 1: Right calendar?
        cal_check = validate_calendar_choice(summary, calendar)
        if not cal_check["valid"]:
            errors.append(cal_check["reason"])

        # Validation 2: Training time?
        train_check = validate_training_time(summary, start)
        if not train_check["valid"]:
            errors.append(train_check["reason"])

        # Validation 3: Conflicts?
        try:
            service = get_calendar_service()
            date_str = start[:10]

            # Check BOTH calendars
            primary_events = list_events_for_date(service, PRIMARY_CAL, date_str)
            tb_events = list_events_for_date(service, TIME_BLOCKS_CAL, date_str)
            all_events = primary_events + tb_events

            conflicts = check_overlap(all_events, start, end)
            if conflicts:
                conflict_names = [c["summary"] for c in conflicts]
                errors.append(f"Overlaps with: {', '.join(conflict_names)}")

        except Exception as e:
            errors.append(f"Could not check conflicts: {e}")

    if errors:
        log_action(agent, "create_blocked", calendar, summary, start, end,
                    "blocked", json.dumps(errors))
        return jsonify({
            "status": "blocked",
            "errors": errors,
            "message": "Event NOT created. Fix the issues or use force=true to override.",
        }), 409

    # Create the event
    try:
        service = get_calendar_service()
        event_body = {
            "summary": summary,
            "start": {"dateTime": start, "timeZone": "America/New_York"},
            "end": {"dateTime": end, "timeZone": "America/New_York"},
        }
        if description:
            event_body["description"] = description
        if location:
            event_body["location"] = location

        created = service.events().insert(calendarId=cal_id, body=event_body).execute()

        log_action(agent, "create", calendar, summary, start, end, "success",
                    json.dumps({"event_id": created.get("id")}))

        return jsonify({
            "status": "created",
            "event_id": created.get("id"),
            "summary": summary,
            "calendar": calendar,
            "start": start,
            "end": end,
        })

    except Exception as e:
        log_action(agent, "create_failed", calendar, summary, start, end, "error", str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/calendar/delete", methods=["POST"])
def delete_event():
    """Delete a calendar event (with logging)."""
    data = request.json or {}
    agent = data.get("agent", "unknown")
    calendar = data.get("calendar")
    event_id = data.get("event_id")

    if not all([calendar, event_id]):
        return jsonify({"error": "Required: calendar, event_id"}), 400

    cal_id = CAL_MAP.get(calendar)
    if not cal_id:
        return jsonify({"error": f"calendar must be 'primary' or 'time_blocks'"}), 400

    try:
        service = get_calendar_service()

        # Get event details before deleting (for logging)
        try:
            ev = service.events().get(calendarId=cal_id, eventId=event_id).execute()
            summary = ev.get("summary", "Unknown")
        except Exception:
            summary = "Unknown"

        service.events().delete(calendarId=cal_id, eventId=event_id).execute()

        log_action(agent, "delete", calendar, summary, "", "", "success",
                    json.dumps({"event_id": event_id}))

        return jsonify({"status": "deleted", "event_id": event_id, "summary": summary})

    except Exception as e:
        log_action(agent, "delete_failed", calendar, "", "", "", "error", str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/calendar/log", methods=["GET"])
def get_log():
    """View recent action log."""
    limit = request.args.get("limit", 50, type=int)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM action_log ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/calendar/day", methods=["POST"])
def get_day():
    """Get full day view across both calendars (for agent pre-flight)."""
    data = request.json or {}
    date_str = data.get("date")
    if not date_str:
        return jsonify({"error": "date required (YYYY-MM-DD)"}), 400

    try:
        service = get_calendar_service()
        primary = list_events_for_date(service, PRIMARY_CAL, date_str)
        time_blocks = list_events_for_date(service, TIME_BLOCKS_CAL, date_str)

        def simplify(events):
            return [{
                "summary": e.get("summary"),
                "start": e.get("start", {}).get("dateTime"),
                "end": e.get("end", {}).get("dateTime"),
                "id": e.get("id"),
            } for e in events]

        return jsonify({
            "date": date_str,
            "primary": simplify(primary),
            "time_blocks": simplify(time_blocks),
            "total": len(primary) + len(time_blocks),
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/calendar/rules", methods=["GET"])
def get_rules():
    """Return the calendar management rules (so agents can read them via API)."""
    if RULES_PATH.exists():
        return RULES_PATH.read_text(), 200, {"Content-Type": "text/markdown"}
    return jsonify({"error": "Rules file not found"}), 404


# --- Telegram Alert (optional) ---

def send_telegram_alert(message: str):
    """Send alert to William via Telegram."""
    import requests
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "5692454753")
    if not bot_token:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=10,
        )
    except Exception:
        pass


# --- Main ---

if __name__ == "__main__":
    init_db()
    print(f"Agent Calendar Gateway running on port {PORT}")
    print(f"Rules: {RULES_PATH}")
    print(f"DB: {DB_PATH}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
