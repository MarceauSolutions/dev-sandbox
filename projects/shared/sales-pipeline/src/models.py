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


def _migrate(conn):
    """Safely add new columns to existing tables."""
    # Deals table migrations
    deals_cols = {row[1] for row in conn.execute("PRAGMA table_info(deals)").fetchall()}
    deals_migrations = [
        ("tier",             "INTEGER DEFAULT 0"),
        ("research_verdict", "TEXT"),
        ("email_template",   "TEXT"),
        ("website",          "TEXT"),
        ("outreach_method",  "TEXT DEFAULT 'email'"),
        ("phone_dependency", "TEXT"),
        ("email_confidence", "TEXT"),
        ("lead_score",       "INTEGER DEFAULT 0"),
        ("outreach_day",     "TEXT"),
    ]
    for col, col_def in deals_migrations:
        if col not in deals_cols:
            conn.execute(f"ALTER TABLE deals ADD COLUMN {col} {col_def}")

    # Outreach_log table migrations (tower, template tracking, A/B testing)
    outreach_cols = {row[1] for row in conn.execute("PRAGMA table_info(outreach_log)").fetchall()}
    outreach_migrations = [
        ("tower",          "TEXT"),
        ("template_used",  "TEXT"),
        ("variant_group",  "TEXT"),
    ]
    for col, col_def in outreach_migrations:
        if col not in outreach_cols:
            conn.execute(f"ALTER TABLE outreach_log ADD COLUMN {col} {col_def}")

    conn.commit()


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
            tower TEXT,
            template_used TEXT,
            variant_group TEXT,
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
    _migrate(conn)


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
    return conn.execute("""
        SELECT * FROM deals
        ORDER BY CASE WHEN tier=1 THEN 0 WHEN tier=2 THEN 1 ELSE 2 END, company ASC
    """).fetchall()


def get_call_queue(conn):
    """Deals for call day — T1 first, with call stats and last email date."""
    return conn.execute("""
        SELECT d.*,
               COUNT(DISTINCT CASE WHEN o.channel='Call' THEN o.id END) AS call_count,
               MAX(CASE WHEN o.channel='Call' THEN o.created_at END)    AS last_called,
               MAX(CASE WHEN o.channel='Email' THEN o.created_at END)   AS last_emailed,
               MAX(CASE WHEN o.channel='Email' THEN o.message_summary END) AS last_email_subject
        FROM deals d
        LEFT JOIN outreach_log o ON o.deal_id = d.id
        WHERE d.stage NOT IN ('Closed Won','Closed Lost')
        GROUP BY d.id
        ORDER BY CASE WHEN d.tier=1 THEN 0 WHEN d.tier=2 THEN 1 ELSE 2 END,
                 d.company ASC
    """).fetchall()


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
    # Only count real outreach interactions (exclude bulk imports like 'Phone Blitz' channel)
    _real_channels = "channel IN ('Call','Email','In-Person','SMS','LinkedIn','DM','Referral')"
    outreach_today = _count(f"SELECT COUNT(*) FROM outreach_log WHERE date(created_at) = date('now') AND {_real_channels}")
    calls_today = _count(f"SELECT COUNT(*) FROM outreach_log WHERE date(created_at) = date('now') AND channel = 'Call'")
    outreach_week = _count(f"SELECT COUNT(*) FROM outreach_log WHERE created_at > datetime('now', '-7 days') AND {_real_channels}")
    followups_due = _count("SELECT COUNT(*) FROM outreach_log WHERE follow_up_date <= date('now') AND (response IS NULL OR response = '') AND follow_up_date IS NOT NULL")

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
        "calls_today": calls_today,
        "outreach_week": outreach_week,
        "followups_due": followups_due,
        "stage_counts": stage_counts,
        "win_rate": round(won / max(won + lost, 1) * 100) if won + lost > 0 else 0,
    }


def assign_outreach_method(conn):
    """
    Intelligently assign outreach_method to all deals based on their profile.

    Routing logic:
    - PHONE (call day): phone_dependency=high OR (no email AND has phone) OR tier=1 with no email
    - IN-PERSON: tier=1 AND phone_dependency=high AND has website AND no email AND in Naples
    - EMAIL: has valid email (personal or generic) AND phone_dependency != high
    - Default: phone if has phone, email if has email, in-person if neither

    Day allocation:
    - Monday: Email batch (T2 industry templates)
    - Tuesday: In-person visits (T1 local Naples)
    - Wednesday: Phone calls (T1 high-priority)
    - Thursday: Email follow-ups + new T2 batch
    - Friday: Phone calls (T2 + callback follow-ups)
    - Saturday: Email nurture + social
    """
    deals = conn.execute(
        "SELECT id, tier, contact_email, contact_phone, phone_dependency, "
        "email_confidence, website, city FROM deals "
        "WHERE stage NOT IN ('Closed Won', 'Closed Lost')"
    ).fetchall()

    for deal in deals:
        d = dict(deal)
        has_email = bool(d.get('contact_email') and '@' in str(d.get('contact_email', '')))
        has_phone = bool(d.get('contact_phone'))
        phone_dep = d.get('phone_dependency') or 'medium'
        email_conf = d.get('email_confidence') or ''
        tier = d.get('tier') or 2
        is_naples = 'naples' in str(d.get('city') or '').lower()

        # Determine method
        if phone_dep == 'high' and not has_email:
            if tier == 1 and is_naples:
                method = 'in-person'
                day = 'tue'
            else:
                method = 'phone'
                day = 'wed' if tier == 1 else 'fri'
        elif phone_dep == 'high' and has_email:
            method = 'phone'
            day = 'wed' if tier == 1 else 'fri'
        elif has_email and email_conf == 'personal_owner':
            method = 'email'
            day = 'mon' if tier == 2 else 'thu'
        elif has_email:
            method = 'email'
            day = 'mon' if tier == 2 else 'thu'
        elif has_phone:
            method = 'phone'
            day = 'wed' if tier == 1 else 'fri'
        else:
            if tier == 1 and is_naples:
                method = 'in-person'
                day = 'tue'
            else:
                method = 'phone'
                day = 'fri'

        conn.execute("UPDATE deals SET outreach_method=?, outreach_day=? WHERE id=?",
                     (method, day, d['id']))

    conn.commit()


def get_email_queue(conn):
    """Deals assigned to email outreach, T1 first."""
    return conn.execute("""
        SELECT d.*,
               COUNT(DISTINCT CASE WHEN o.channel='Email' THEN o.id END) AS email_count,
               MAX(CASE WHEN o.channel='Email' THEN o.created_at END) AS last_emailed
        FROM deals d
        LEFT JOIN outreach_log o ON o.deal_id = d.id
        WHERE d.outreach_method = 'email' AND d.stage NOT IN ('Closed Won','Closed Lost')
        GROUP BY d.id
        ORDER BY CASE WHEN d.tier=1 THEN 0 WHEN d.tier=2 THEN 1 ELSE 2 END, d.company ASC
    """).fetchall()


def get_phone_queue(conn):
    """Deals assigned to phone outreach, T1 first."""
    return conn.execute("""
        SELECT d.*,
               COUNT(DISTINCT CASE WHEN o.channel='Call' THEN o.id END) AS call_count,
               MAX(CASE WHEN o.channel='Call' THEN o.created_at END) AS last_called,
               MAX(CASE WHEN o.channel='Email' THEN o.created_at END) AS last_emailed
        FROM deals d
        LEFT JOIN outreach_log o ON o.deal_id = d.id
        WHERE d.outreach_method = 'phone' AND d.stage NOT IN ('Closed Won','Closed Lost')
        GROUP BY d.id
        ORDER BY CASE WHEN d.tier=1 THEN 0 WHEN d.tier=2 THEN 1 ELSE 2 END, d.company ASC
    """).fetchall()


def get_inperson_queue(conn):
    """Deals flagged for in-person visits — outreach_method='in-person' OR next_action contains 'in-person'."""
    return conn.execute("""
        SELECT d.*,
               COUNT(DISTINCT CASE WHEN o.channel='In-Person' THEN o.id END) AS visit_count,
               MAX(CASE WHEN o.channel='In-Person' THEN o.created_at END) AS last_visited,
               COUNT(DISTINCT CASE WHEN o.channel='Call' THEN o.id END) AS call_count,
               MAX(CASE WHEN o.channel='Call' THEN o.created_at END) AS last_called,
               MAX(CASE WHEN o.channel='Email' THEN o.created_at END) AS last_emailed
        FROM deals d
        LEFT JOIN outreach_log o ON o.deal_id = d.id
        WHERE (d.outreach_method = 'in-person' OR LOWER(d.next_action) LIKE '%in-person%')
          AND d.stage NOT IN ('Closed Won','Closed Lost')
        GROUP BY d.id
        ORDER BY d.next_action_date ASC,
                 CASE WHEN d.tier=1 THEN 0 WHEN d.tier=2 THEN 1 ELSE 2 END, d.company ASC
    """).fetchall()


def get_outreach_stats(conn):
    """Stats broken down by outreach method."""
    stats = {}
    for method in ['email', 'phone', 'in-person']:
        row = conn.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN tier=1 THEN 1 ELSE 0 END) as t1,
                   SUM(CASE WHEN tier=2 THEN 1 ELSE 0 END) as t2
            FROM deals
            WHERE outreach_method=? AND stage NOT IN ('Closed Won','Closed Lost')
        """, (method,)).fetchone()
        stats[method] = dict(row)
    return stats


def get_daily_outreach_counts(conn):
    """Get today's outreach counts by channel for progress rings."""
    today = datetime.now().strftime("%Y-%m-%d")
    row = conn.execute("""
        SELECT
            COALESCE(SUM(CASE WHEN channel='Call' THEN 1 ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN channel='Email' THEN 1 ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN channel='In-Person' THEN 1 ELSE 0 END), 0)
        FROM outreach_log WHERE date(created_at) = ?
    """, (today,)).fetchone()
    return {"calls": row[0], "emails": row[1], "visits": row[2]}


def get_leads_by_tier_and_method(conn):
    """Get active leads grouped by (tier, outreach_method) for the dashboard matrix."""
    deals = conn.execute("""
        SELECT d.*,
               MAX(CASE WHEN o.channel='Call' THEN o.created_at END) AS last_called,
               MAX(CASE WHEN o.channel='Email' THEN o.created_at END) AS last_emailed,
               MAX(CASE WHEN o.channel='In-Person' THEN o.created_at END) AS last_visited,
               COUNT(DISTINCT CASE WHEN o.channel='Call' THEN o.id END) AS call_count,
               COUNT(DISTINCT CASE WHEN o.channel='Email' THEN o.id END) AS email_count
        FROM deals d
        LEFT JOIN outreach_log o ON o.deal_id = d.id
        WHERE d.stage NOT IN ('Closed Won', 'Closed Lost')
        GROUP BY d.id
        ORDER BY CASE WHEN d.tier=1 THEN 0 WHEN d.tier=2 THEN 1 ELSE 2 END, d.company ASC
    """).fetchall()

    grouped = {}
    for d in deals:
        d_dict = dict(d)
        tier = d_dict.get("tier") or 0
        method = d_dict.get("outreach_method") or "email"
        key = f"{tier}_{method}"
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(d_dict)
    return grouped, [dict(d) for d in deals]


def get_tier1_queue(conn):
    """Return up to 10 Tier 1 deals not Closed, sorted by stage priority."""
    return conn.execute("""
        SELECT * FROM deals
        WHERE tier = 1 AND stage NOT IN ('Closed Won', 'Closed Lost')
        ORDER BY CASE stage
            WHEN 'Qualified'      THEN 1
            WHEN 'Meeting Booked' THEN 2
            WHEN 'Proposal Sent'  THEN 3
            WHEN 'Negotiation'    THEN 4
            ELSE 5
        END
        LIMIT 10
    """).fetchall()
