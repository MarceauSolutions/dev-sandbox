"""
Accountability Tracker — Keeps you on track for April 6, 2026 goal.
Integrates with pipeline, calendar, call_logger, and Telegram.
Auto-logs activity completion and sends smart reminders.
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
import requests
from .models import get_db

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Configurable targets — adjust as needed
GOAL_TARGETS = {
    'calls_made': 25,      # calls per day
    'meetings_booked': 3,
    'proposals_sent': 2,
    'closed_won': 1,       # ultimate goal by April 6
}

def log_daily_activity(activity_type: str, completed: bool = False, notes: str = ""):
    """Log completion of a daily activity block."""
    conn = get_db()
    today = datetime.now().strftime("%Y-%m-%d")

    existing = conn.execute(
        "SELECT id FROM accountability_logs WHERE date = ? AND activity_type = ?",
        (today, activity_type)
    ).fetchone()

    if existing:
        conn.execute(
            "UPDATE accountability_logs SET completed = ?, notes = ?, updated_at = datetime('now') WHERE id = ?",
            (completed, notes, existing['id'])
        )
    else:
        conn.execute(
            "INSERT INTO accountability_logs (date, activity_type, completed, notes, created_at) "
            "VALUES (?, ?, ?, ?, datetime('now'))",
            (today, activity_type, completed, notes)
        )

    conn.commit()
    conn.close()

def auto_log_from_pipeline():
    """Automatically detect and log completed blocks from pipeline data."""
    conn = get_db()
    today = datetime.now().strftime("%Y-%m-%d")

    # Calls
    calls_today = conn.execute(
        "SELECT COUNT(*) FROM outreach_log WHERE date(created_at) = ? AND channel = 'Call'",
        (today,)
    ).fetchone()[0]

    if calls_today >= GOAL_TARGETS['calls_made'] // 2:
        log_daily_activity("call_block", completed=True, notes=f"Completed {calls_today} calls today")

    # Visits (in-person)
    visits_today = conn.execute(
        "SELECT COUNT(*) FROM outreach_log WHERE date(created_at) = ? AND channel = 'In-Person'",
        (today,)
    ).fetchone()[0]

    if visits_today > 0:
        log_daily_activity("visit_block", completed=True, notes=f"Completed {visits_today} in-person visits")

    # Emails
    emails_today = conn.execute(
        "SELECT COUNT(*) FROM outreach_log WHERE date(created_at) = ? AND channel = 'Email'",
        (today,)
    ).fetchone()[0]

    if emails_today >= 8:
        log_daily_activity("email_block", completed=True, notes=f"Sent {emails_today} emails")

    conn.close()

def check_missed_activities():
    """Check yesterday's activities and send reminders if missed."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    conn = get_db()
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    missed = conn.execute("""
        SELECT activity_type 
        FROM accountability_logs 
        WHERE date = ? AND completed = FALSE
    """, (yesterday,)).fetchall()

    conn.close()

    if missed:
        message = "🚨 ACCOUNTABILITY ALERT 🚨\n\nYou missed these blocks yesterday:\n"
        for m in missed:
            message += f"• {m['activity_type'].replace('_', ' ').title()}\n"
        message += "\nLet's get back on track today for the April 6 goal!"

        send_telegram_message(message)

def send_reminder(activity_type: str):
    """Send proactive reminder for a specific block."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    messages = {
        "call_block": "⏰ CALL BLOCK STARTING SOON — Time to make your calls! Use the Daily Command Center for scripts.",
        "visit_block": "🚗 VISIT BLOCK — In-person visits scheduled. Check addresses and talking points.",
        "email_block": "📧 EMAIL BLOCK — Personalized emails ready in the Command Center.",
        "pipeline_run": "📊 PIPELINE RUN REMINDER — Run the orchestrator to stay current."
    }

    message = messages.get(activity_type, f"⏰ Reminder: {activity_type.replace('_', ' ').title()}")
    send_telegram_message(message)

def send_telegram_message(text: str):
    """Send message via Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception:
        pass

def get_accountability_status():
    """Get today's accountability status for dashboards."""
    conn = get_db()
    today = datetime.now().strftime("%Y-%m-%d")

    activities = conn.execute(
        "SELECT activity_type, completed, notes FROM accountability_logs WHERE date = ?",
        (today,)
    ).fetchall()

    conn.close()

    status = {}
    default_activities = ['call_block', 'visit_block', 'email_block', 'pipeline_run']

    for activity in default_activities:
        status[activity] = {'completed': False, 'notes': ''}

    for act in activities:
        status[act['activity_type']] = {
            'completed': bool(act['completed']),
            'notes': act['notes'] or ''
        }

    return status

def update_goal_progress():
    """Update daily + cumulative progress toward April 6 goal."""
    conn = get_db()
    today = datetime.now().strftime("%Y-%m-%d")

    calls_made = conn.execute(
        "SELECT COUNT(*) FROM outreach_log WHERE date(created_at) = ? AND channel = 'Call'",
        (today,)
    ).fetchone()[0]

    meetings_booked = conn.execute(
        "SELECT COUNT(*) FROM deals WHERE stage = 'Meeting Booked' AND date(updated_at) = ?",
        (today,)
    ).fetchone()[0]

    proposals_sent = conn.execute(
        "SELECT COUNT(*) FROM deals WHERE stage = 'Proposal Sent' AND date(updated_at) = ?",
        (today,)
    ).fetchone()[0]

    closed_won = conn.execute(
        "SELECT COUNT(*) FROM deals WHERE stage = 'Closed Won' AND date(close_date) = ?",
        (today,)
    ).fetchone()[0]

    for metric, value in [('calls_made', calls_made), ('meetings_booked', meetings_booked),
                          ('proposals_sent', proposals_sent), ('closed_won', closed_won)]:
        conn.execute("""
            INSERT OR REPLACE INTO goal_progress (date, metric, value, target)
            VALUES (?, ?, ?, ?)
        """, (today, metric, value, GOAL_TARGETS[metric]))

    conn.commit()
    conn.close()

    return {
        'calls_made': calls_made,
        'meetings_booked': meetings_booked,
        'proposals_sent': proposals_sent,
        'closed_won': closed_won
    }

# Auto-run when imported by orchestrator
if __name__ == "__main__":
    auto_log_from_pipeline()
    check_missed_activities()