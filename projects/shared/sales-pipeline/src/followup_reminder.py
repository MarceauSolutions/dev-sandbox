#!/usr/bin/env python3
"""
Follow-up Reminder System
Checks for deals with follow-ups due today and returns them.
Should be called by Clawdbot heartbeat or cron.
"""

import sqlite3
from datetime import datetime, timedelta

DB_PATH = '/home/clawdbot/dev-sandbox/projects/shared/sales-pipeline/data/pipeline.db'


def get_followups_due(days_range: int = 0) -> list:
    """
    Get deals with follow-ups due today (or within days_range).
    Returns list of dicts with deal info.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    if days_range > 0:
        end_date = (datetime.now() + timedelta(days=days_range)).strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT d.id, d.company, d.contact_name, d.contact_email, d.contact_phone,
                   d.stage, d.next_action, d.next_action_date, d.notes
            FROM deals d
            WHERE d.next_action_date >= ? AND d.next_action_date <= ?
            AND d.stage NOT IN ('Closed Won', 'Closed Lost')
            ORDER BY d.next_action_date ASC
        """, (today, end_date))
    else:
        cursor.execute("""
            SELECT d.id, d.company, d.contact_name, d.contact_email, d.contact_phone,
                   d.stage, d.next_action, d.next_action_date, d.notes
            FROM deals d
            WHERE d.next_action_date = ?
            AND d.stage NOT IN ('Closed Won', 'Closed Lost')
        """, (today,))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "deal_id": row['id'],
            "company": row['company'],
            "contact_name": row['contact_name'],
            "contact_email": row['contact_email'],
            "contact_phone": row['contact_phone'],
            "stage": row['stage'],
            "next_action": row['next_action'],
            "due_date": row['next_action_date'],
            "notes": row['notes']
        })
    
    conn.close()
    return results


def get_overdue_followups() -> list:
    """Get deals with follow-ups that are overdue (past due date)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    cursor.execute("""
        SELECT d.id, d.company, d.contact_name, d.contact_email, d.contact_phone,
               d.stage, d.next_action, d.next_action_date
        FROM deals d
        WHERE d.next_action_date < ?
        AND d.next_action_date IS NOT NULL
        AND d.next_action_date != ''
        AND d.stage NOT IN ('Closed Won', 'Closed Lost', 'Intake')
        ORDER BY d.next_action_date ASC
    """, (today,))
    
    results = []
    for row in cursor.fetchall():
        days_overdue = (datetime.now() - datetime.strptime(row['next_action_date'], '%Y-%m-%d')).days
        results.append({
            "deal_id": row['id'],
            "company": row['company'],
            "contact_name": row['contact_name'],
            "contact_email": row['contact_email'],
            "contact_phone": row['contact_phone'],
            "stage": row['stage'],
            "next_action": row['next_action'],
            "due_date": row['next_action_date'],
            "days_overdue": days_overdue
        })
    
    conn.close()
    return results


def format_reminder_message(followups: list, overdue: list = None) -> str:
    """Format follow-ups into a Telegram-friendly message."""
    
    lines = []
    
    if overdue:
        lines.append("🚨 **OVERDUE FOLLOW-UPS:**")
        for f in overdue[:5]:  # Limit to 5
            lines.append(f"• {f['company']} — {f['days_overdue']} days overdue")
            if f['contact_name']:
                lines.append(f"  Contact: {f['contact_name']}")
            if f['contact_phone']:
                lines.append(f"  📞 {f['contact_phone']}")
        lines.append("")
    
    if followups:
        lines.append("📅 **TODAY'S FOLLOW-UPS:**")
        for f in followups[:10]:  # Limit to 10
            lines.append(f"• {f['company']} ({f['stage']})")
            if f['contact_name']:
                lines.append(f"  Contact: {f['contact_name']}")
            if f['contact_phone']:
                lines.append(f"  📞 {f['contact_phone']}")
            if f['next_action']:
                lines.append(f"  Action: {f['next_action']}")
        lines.append("")
    
    if not followups and not overdue:
        lines.append("✅ No follow-ups due today.")
    
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        due_today = get_followups_due()
        overdue = get_overdue_followups()
        print(format_reminder_message(due_today, overdue))
    else:
        print("Usage: python followup_reminder.py check")
