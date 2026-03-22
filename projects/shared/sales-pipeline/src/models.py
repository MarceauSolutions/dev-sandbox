"""
Sales Pipeline — Database models and operations.

SQLite-backed CRM for AI services sales pipeline with deal tracking,
outreach logging, proposal generation, and pre-call briefs.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "pipeline.db"

STAGES = ["Intake", "Qualified", "Meeting Booked", "Proposal Sent", "Negotiation", "Closed Won", "Closed Lost"]
STAGE_COLORS = {
    "Intake": "#8b949e", "Qualified": "#58a6ff", "Meeting Booked": "#d29922",
    "Proposal Sent": "#bc8cff", "Negotiation": "#C9963C", "Closed Won": "#3fb950", "Closed Lost": "#f85149"
}
CHANNELS = ["SMS", "Email", "Call", "LinkedIn", "DM", "In-Person", "Referral"]
INDUSTRIES = ["HVAC", "Med Spa", "Restaurant", "Salon", "Insurance", "Real Estate", "Legal", "Dental", "Auto", "Retail", "Other"]


def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _create_tables(conn)
    return conn


def _create_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            contact_name TEXT,
            contact_phone TEXT,
            contact_email TEXT,
            industry TEXT DEFAULT 'Other',
            pain_points TEXT,
            lead_source TEXT,
            stage TEXT DEFAULT 'Intake',
            next_action TEXT,
            next_action_date TEXT,
            proposal_amount REAL DEFAULT 0,
            setup_fee REAL DEFAULT 0,
            monthly_fee REAL DEFAULT 0,
            close_date TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS outreach_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id INTEGER REFERENCES deals(id),
            company TEXT,
            contact TEXT,
            channel TEXT DEFAULT 'Email',
            message_summary TEXT,
            response TEXT,
            follow_up_date TEXT,
            lead_source TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id INTEGER NOT NULL REFERENCES deals(id),
            title TEXT NOT NULL,
            setup_fee REAL DEFAULT 0,
            monthly_fee REAL DEFAULT 0,
            scope_summary TEXT,
            deliverables TEXT,
            timeline TEXT,
            pdf_path TEXT,
            sent_at TEXT,
            status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'sent', 'viewed', 'accepted', 'rejected')),
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS call_briefs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id INTEGER NOT NULL REFERENCES deals(id),
            company_research TEXT,
            pain_points TEXT,
            talking_points TEXT,
            questions_to_ask TEXT,
            competitive_landscape TEXT,
            recommended_solution TEXT,
            pdf_path TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id INTEGER REFERENCES deals(id),
            activity_type TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()


# ─── Deal CRUD ───────────────────────────────────────────────

def create_deal(conn, company, **kwargs):
    cols = ["company"] + list(kwargs.keys())
    vals = [company] + list(kwargs.values())
    placeholders = ", ".join(["?"] * len(cols))
    cur = conn.execute(f"INSERT INTO deals ({', '.join(cols)}) VALUES ({placeholders})", vals)
    conn.commit()
    log_activity(conn, cur.lastrowid, "deal_created", f"New deal: {company}")
    return cur.lastrowid


def update_deal(conn, deal_id, **kwargs):
    if not kwargs:
        return
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    conn.execute(f"UPDATE deals SET {fields}, updated_at = datetime('now') WHERE id = ?",
                 (*kwargs.values(), deal_id))
    conn.commit()
    if "stage" in kwargs:
        log_activity(conn, deal_id, "stage_changed", f"Moved to: {kwargs['stage']}")


def get_deal(conn, deal_id):
    return conn.execute("SELECT * FROM deals WHERE id = ?", (deal_id,)).fetchone()


def get_all_deals(conn):
    return conn.execute("SELECT * FROM deals ORDER BY updated_at DESC").fetchall()


def get_deals_by_stage(conn):
    """Group deals by stage for kanban view."""
    deals = conn.execute("SELECT * FROM deals WHERE stage != 'Closed Lost' ORDER BY updated_at DESC").fetchall()
    grouped = {s: [] for s in STAGES}
    for d in deals:
        stage = d["stage"] if d["stage"] in grouped else "Intake"
        grouped[stage].append(d)
    return grouped


def delete_deal(conn, deal_id):
    conn.execute("DELETE FROM outreach_log WHERE deal_id = ?", (deal_id,))
    conn.execute("DELETE FROM proposals WHERE deal_id = ?", (deal_id,))
    conn.execute("DELETE FROM call_briefs WHERE deal_id = ?", (deal_id,))
    conn.execute("DELETE FROM activities WHERE deal_id = ?", (deal_id,))
    conn.execute("DELETE FROM deals WHERE id = ?", (deal_id,))
    conn.commit()


# ─── Outreach ────────────────────────────────────────────────

def log_outreach(conn, deal_id=None, company="", contact="", channel="Email", message="", response="", follow_up_date=None, lead_source=""):
    conn.execute("""
        INSERT INTO outreach_log (deal_id, company, contact, channel, message_summary, response, follow_up_date, lead_source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (deal_id, company, contact, channel, message, response, follow_up_date, lead_source))
    conn.commit()
    if deal_id:
        log_activity(conn, deal_id, "outreach", f"{channel}: {message[:80]}")


def get_outreach_log(conn, deal_id=None, limit=50):
    if deal_id:
        return conn.execute("SELECT * FROM outreach_log WHERE deal_id = ? ORDER BY created_at DESC LIMIT ?", (deal_id, limit)).fetchall()
    return conn.execute("SELECT * FROM outreach_log ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()


def get_todays_followups(conn):
    today = datetime.now().strftime("%Y-%m-%d")
    return conn.execute("""
        SELECT o.*, d.company as deal_company, d.stage
        FROM outreach_log o LEFT JOIN deals d ON o.deal_id = d.id
        WHERE o.follow_up_date <= ? AND (o.response IS NULL OR o.response = '')
        ORDER BY o.follow_up_date ASC
    """, (today,)).fetchall()


# ─── Proposals ───────────────────────────────────────────────

def create_proposal(conn, deal_id, title, setup_fee=0, monthly_fee=0, scope="", deliverables="", timeline=""):
    cur = conn.execute("""
        INSERT INTO proposals (deal_id, title, setup_fee, monthly_fee, scope_summary, deliverables, timeline)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (deal_id, title, setup_fee, monthly_fee, scope, deliverables, timeline))
    conn.commit()
    log_activity(conn, deal_id, "proposal_created", f"Proposal: {title}")
    return cur.lastrowid


def get_proposals(conn, deal_id):
    return conn.execute("SELECT * FROM proposals WHERE deal_id = ? ORDER BY created_at DESC", (deal_id,)).fetchall()


# ─── Call Briefs ─────────────────────────────────────────────

def save_call_brief(conn, deal_id, **kwargs):
    cols = ["deal_id"] + list(kwargs.keys())
    vals = [deal_id] + list(kwargs.values())
    placeholders = ", ".join(["?"] * len(cols))
    cur = conn.execute(f"INSERT INTO call_briefs ({', '.join(cols)}) VALUES ({placeholders})", vals)
    conn.commit()
    log_activity(conn, deal_id, "brief_generated", "Pre-call intelligence brief created")
    return cur.lastrowid


def get_call_briefs(conn, deal_id):
    return conn.execute("SELECT * FROM call_briefs WHERE deal_id = ? ORDER BY created_at DESC", (deal_id,)).fetchall()


# ─── Activity Log ────────────────────────────────────────────

def log_activity(conn, deal_id, activity_type, description=""):
    conn.execute("INSERT INTO activities (deal_id, activity_type, description) VALUES (?, ?, ?)",
                 (deal_id, activity_type, description))
    conn.commit()


def get_activities(conn, deal_id=None, limit=30):
    if deal_id:
        return conn.execute("SELECT * FROM activities WHERE deal_id = ? ORDER BY created_at DESC LIMIT ?", (deal_id, limit)).fetchall()
    return conn.execute("SELECT * FROM activities ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()


# ─── Dashboard Stats ────────────────────────────────────────

def get_pipeline_stats(conn):
    def _count(q, params=()):
        return conn.execute(q, params).fetchone()[0]

    total = _count("SELECT COUNT(*) FROM deals WHERE stage != 'Closed Lost'")
    won = _count("SELECT COUNT(*) FROM deals WHERE stage = 'Closed Won'")
    lost = _count("SELECT COUNT(*) FROM deals WHERE stage = 'Closed Lost'")
    pipeline_value = conn.execute("SELECT COALESCE(SUM(setup_fee + monthly_fee * 12), 0) FROM deals WHERE stage NOT IN ('Closed Won', 'Closed Lost')").fetchone()[0]
    won_revenue = conn.execute("SELECT COALESCE(SUM(setup_fee + monthly_fee * 12), 0) FROM deals WHERE stage = 'Closed Won'").fetchone()[0]
    meetings_this_week = _count("SELECT COUNT(*) FROM deals WHERE stage = 'Meeting Booked' AND updated_at > datetime('now', '-7 days')")
    proposals_out = _count("SELECT COUNT(*) FROM deals WHERE stage = 'Proposal Sent'")
    outreach_today = _count("SELECT COUNT(*) FROM outreach_log WHERE date(created_at) = date('now')")
    outreach_week = _count("SELECT COUNT(*) FROM outreach_log WHERE created_at > datetime('now', '-7 days')")
    followups_due = _count("SELECT COUNT(*) FROM outreach_log WHERE follow_up_date <= date('now') AND (response IS NULL OR response = '')")

    # Stage counts
    stage_counts = {}
    for row in conn.execute("SELECT stage, COUNT(*) as c FROM deals GROUP BY stage"):
        stage_counts[row["stage"]] = row["c"]

    return {
        "total_active": total,
        "deals_won": won,
        "deals_lost": lost,
        "pipeline_value": pipeline_value,
        "won_revenue": won_revenue,
        "meetings_this_week": meetings_this_week,
        "proposals_out": proposals_out,
        "outreach_today": outreach_today,
        "outreach_week": outreach_week,
        "followups_due": followups_due,
        "stage_counts": stage_counts,
        "win_rate": round(won / max(won + lost, 1) * 100) if won + lost > 0 else 0,
    }
