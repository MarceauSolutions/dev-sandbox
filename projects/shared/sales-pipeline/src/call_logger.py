#!/usr/bin/env python3
"""
Call Logger - Writes DIRECTLY to pipeline.db (not JSON files).

Commands via Telegram:
- "called [business]: [outcome]" - Log a call
- "called [business]: [outcome], [notes]" - Log with notes
- "calls" or "call history" - View recent calls
- "calls [business]" - View calls for specific business
"""

import os
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any

DB_PATH = str(Path(__file__).parent.parent / "data" / "pipeline.db")

OUTCOME_ALIASES = {
    "interested": "interested", "int": "interested", "positive": "interested",
    "pos": "interested", "good": "interested", "hot": "interested",
    "not interested": "not_interested", "not_interested": "not_interested",
    "no": "not_interested", "negative": "not_interested", "neg": "not_interested",
    "pass": "not_interested",
    "voicemail": "voicemail", "vm": "voicemail", "left message": "voicemail",
    "no answer": "no_answer", "no_answer": "no_answer", "na": "no_answer",
    "callback": "callback", "call back": "callback", "cb": "callback",
    "spanish": "spanish_speaker", "spanish speaker": "spanish_speaker",
    "gatekeeper": "gatekeeper", "gk": "gatekeeper", "secretary": "gatekeeper",
    "wrong number": "wrong_number", "wrong": "wrong_number",
    "busy": "busy",
    "meeting booked": "meeting_booked", "booked": "meeting_booked",
    "has ai": "has_ai_already", "has_ai_already": "has_ai_already",
    "email requested": "email_requested", "gave email": "email_requested",
}

POSITIVE = ["interested", "callback", "meeting_booked", "email_requested"]
NEUTRAL = ["voicemail", "no_answer", "busy", "gatekeeper", "spanish_speaker"]
NEGATIVE = ["not_interested", "wrong_number", "has_ai_already"]

STAGE_MAP = {
    "interested": "Qualified",
    "callback": "Qualified",
    "meeting_booked": "Meeting Booked",
    "email_requested": "Qualified",
    "voicemail": "Intake",
    "no_answer": "Intake",
    "gatekeeper": "Intake",
    "not_interested": "Closed Lost",
    "wrong_number": "Closed Lost",
    "has_ai_already": "Closed Lost",
    "spanish_speaker": "Intake",
    "busy": "Intake",
}


def normalize_outcome(text):
    return OUTCOME_ALIASES.get(text.lower().strip(), text.lower().strip())


def log_call(business, outcome, notes="", contact_name="", phone="", email="", deal_id=None):
    """Log call directly to pipeline.db.

    Args:
        deal_id: If provided, update by deal ID (exact). Otherwise match by company name (exact).
    """
    conn = sqlite3.connect(DB_PATH)
    normalized = normalize_outcome(outcome)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stage = STAGE_MAP.get(normalized, "Intake")

    # Update deal
    updates = ["stage = ?"]
    params = [stage]
    if contact_name:
        updates.append("contact_name = ?")
        params.append(contact_name)
    if email:
        updates.append("contact_email = ?")
        params.append(email)
    if normalized in POSITIVE + NEUTRAL:
        updates.append("next_action_date = ?")
        params.append((datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"))

    if deal_id:
        conn.execute("UPDATE deals SET " + ", ".join(updates) + " WHERE id = ?", params + [deal_id])
    else:
        conn.execute("UPDATE deals SET " + ", ".join(updates) + " WHERE company = ?", params + [business])

    # Resolve deal_id for outreach_log foreign key if not provided
    resolved_deal_id = deal_id
    if not resolved_deal_id:
        row = conn.execute("SELECT id FROM deals WHERE company = ? LIMIT 1", (business,)).fetchone()
        if row:
            resolved_deal_id = row[0]

    # Log to outreach_log
    conn.execute(
        "INSERT INTO outreach_log (deal_id, company, contact, channel, message_summary, response, created_at, tower) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (resolved_deal_id, business, contact_name, "Call", notes or normalized, normalized, now, "digital-ai-services")
    )

    conn.commit()
    
    signal = "+" if normalized in POSITIVE else ("-" if normalized in NEGATIVE else "~")
    result = {"business": business, "outcome": normalized, "signal": signal, "stage": stage}
    conn.close()
    return result


def get_recent_calls(limit=20):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT company, contact, message_summary, response, created_at FROM outreach_log WHERE channel = 'Call' ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_calls_for_business(business=None, deal_id=None):
    """Get outreach history for a business by exact name or deal_id."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if deal_id:
        rows = conn.execute(
            "SELECT company, contact, channel, message_summary, response, created_at FROM outreach_log WHERE deal_id = ? ORDER BY id",
            (deal_id,)
        ).fetchall()
    elif business:
        rows = conn.execute(
            "SELECT company, contact, channel, message_summary, response, created_at FROM outreach_log WHERE company = ? ORDER BY id",
            (business,)
        ).fetchall()
    else:
        rows = []
    conn.close()
    return [dict(r) for r in rows]


def parse_call_command(text):
    pattern = r"^called\s+(.+?):\s*([^,]+)(?:,\s*(.*))?$"
    match = re.match(pattern, text.strip(), re.IGNORECASE)
    if match:
        return {"business": match.group(1).strip(), "outcome": match.group(2).strip(), "notes": (match.group(3) or "").strip()}
    return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python call_logger.py log Company outcome notes")
        print("  python call_logger.py recent")
        print("  python call_logger.py business Company")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "log" and len(sys.argv) >= 4:
        r = log_call(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
        print("Logged: " + r["business"] + " -> " + r["outcome"] + " (" + r["stage"] + ")")
    elif cmd == "recent":
        for c in get_recent_calls():
            print("  " + str(c["created_at"]) + " | " + str(c["company"]) + " | " + str(c.get("response","")))
    elif cmd == "business" and len(sys.argv) >= 3:
        for c in get_calls_for_business(sys.argv[2]):
            print("  " + str(c["created_at"]) + " | " + str(c["channel"]) + " | " + str(c.get("message_summary",""))[:60])
