"""
Marceau Solutions — Canonical Pipeline Database

EC2-aware SQLite for the multi-tower sales pipeline.
One source of truth, readable by Claude Code (Mac), Clawdbot (EC2), and the Pipeline dashboard.

DATA LOCATION:
  - EC2 (primary): /home/clawdbot/data/pipeline.db
  - Mac (dev):     ~/dev-sandbox/projects/lead-generation/sales-pipeline/data/pipeline.db
  - Auto-detected: on EC2 → uses EC2 path; on Mac → uses local path

TOWERS:
  - digital-ai-services   AI automation (missed call text-back, chatbots)
  - digital-web-dev       Website builds and redesigns
  - fitness-coaching      1:1 PT coaching ($197/mo)
  - fitness-influencer    Brand partnership deals for influencer clients
  - labs                  R&D / new product experiments

MULTI-TOWER SCHEMA:
  All tables have a `tower` column (DEFAULT 'digital-ai-services' for backward compat).
  Dashboards filter by tower; Clawdbot queries default to all towers unless specified.

USAGE:
  from execution.pipeline_db import get_db, create_deal, get_pipeline_stats
  conn = get_db()  # auto-detects environment
  conn = get_db(tower='fitness-coaching')  # pre-filtered convenience wrapper

SYNC:
  Mac → EC2: python execution/pipeline_db.py --sync
  EC2 → Mac: python execution/pipeline_db.py --pull
"""

import os
import sys
import json
import sqlite3
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Path Resolution ─────────────────────────────────────────────────────────

EC2_HOST = "ec2-user@34.193.98.97"
EC2_KEY = Path.home() / ".ssh" / "marceau-ec2-key.pem"
EC2_DB_PATH = "/home/clawdbot/data/pipeline.db"
MAC_DB_PATH = Path(__file__).parents[1] / "projects/lead-generation/sales-pipeline/data/pipeline.db"


def _is_ec2() -> bool:
    """Detect if running on EC2 (clawdbot environment)."""
    return (
        os.path.exists("/home/clawdbot") or
        os.getenv("CLAWDBOT_ENV") == "ec2" or
        Path("/home/clawdbot/data").exists()
    )


def get_db_path() -> Path:
    if _is_ec2():
        p = Path(EC2_DB_PATH)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    else:
        MAC_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        return MAC_DB_PATH


# ── Towers ───────────────────────────────────────────────────────────────────

TOWERS = {
    "digital-ai-services":  {"label": "AI Services",        "icon": "🤖", "color": "#C9963C"},
    "digital-web-dev":      {"label": "Web Development",    "icon": "🌐", "color": "#58a6ff"},
    "fitness-coaching":     {"label": "Fitness Coaching",   "icon": "💪", "color": "#3fb950"},
    "fitness-influencer":   {"label": "Influencer Deals",   "icon": "📸", "color": "#bc8cff"},
    "labs":                 {"label": "Labs / R&D",         "icon": "🔬", "color": "#d29922"},
}

STAGES = ["Prospect", "Outreached", "Replied", "Meeting Booked",
          "Proposal Sent", "Trial Active", "Closed Won", "Closed Lost"]

STAGE_COLORS = {
    "Prospect": "#8b949e", "Outreached": "#58a6ff", "Replied": "#d29922",
    "Meeting Booked": "#C9963C", "Proposal Sent": "#bc8cff",
    "Trial Active": "#3fb950", "Closed Won": "#3fb950", "Closed Lost": "#f85149"
}

CHANNELS = ["Email", "Cold Email", "SMS", "Call", "LinkedIn", "Instagram DM",
            "In-Person", "Referral", "YouTube", "Google"]


# ── Schema ───────────────────────────────────────────────────────────────────

def get_db(tower: Optional[str] = None) -> sqlite3.Connection:
    """
    Get database connection. Auto-detects EC2 vs Mac.
    If tower is specified, returned connection has tower pre-filtered via a view.
    """
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _create_tables(conn)
    if tower:
        conn.execute(f"CREATE TEMP VIEW IF NOT EXISTS active_deals AS "
                     f"SELECT * FROM deals WHERE tower = '{tower}'")
    return conn


def _create_tables(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS deals (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            tower           TEXT    NOT NULL DEFAULT 'digital-ai-services',
            company         TEXT    NOT NULL,
            contact_name    TEXT,
            contact_phone   TEXT,
            contact_email   TEXT,
            email_source    TEXT,           -- crawl | hunter_domain | hunter_finder | snov_domain | snov_name_finder | phone-only
            email_confidence INTEGER DEFAULT 0,
            industry        TEXT    DEFAULT 'Other',
            city            TEXT    DEFAULT 'Naples',
            state           TEXT    DEFAULT 'FL',
            website         TEXT,
            pain_points     TEXT,           -- JSON array
            lead_source     TEXT,           -- apollo | google_places | yelp | referral | inbound | manual
            stage           TEXT    DEFAULT 'Prospect',
            next_action     TEXT,
            next_action_date TEXT,
            trial_start_date TEXT,
            trial_end_date   TEXT,
            proposal_amount  REAL   DEFAULT 0,
            setup_fee        REAL   DEFAULT 0,
            monthly_fee      REAL   DEFAULT 0,
            close_date       TEXT,
            notes            TEXT,
            created_at       TEXT   DEFAULT (datetime('now')),
            updated_at       TEXT   DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS outreach_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id         INTEGER REFERENCES deals(id) ON DELETE CASCADE,
            tower           TEXT    DEFAULT 'digital-ai-services',
            company         TEXT,
            contact         TEXT,
            channel         TEXT    DEFAULT 'Email',
            message_summary TEXT,
            response        TEXT,
            follow_up_date  TEXT,
            follow_up_count INTEGER DEFAULT 0,
            lead_source     TEXT,
            created_at      TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS trial_metrics (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id         INTEGER NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
            log_date        TEXT    NOT NULL DEFAULT (date('now')),
            missed_calls    INTEGER DEFAULT 0,
            texts_sent      INTEGER DEFAULT 0,
            replies         INTEGER DEFAULT 0,
            calls_recovered INTEGER DEFAULT 0,
            revenue_recovered REAL  DEFAULT 0,
            notes           TEXT,
            created_at      TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS proposals (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id         INTEGER NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
            title           TEXT    NOT NULL,
            setup_fee       REAL    DEFAULT 0,
            monthly_fee     REAL    DEFAULT 0,
            scope_summary   TEXT,
            deliverables    TEXT,
            timeline        TEXT,
            pdf_path        TEXT,
            sent_at         TEXT,
            status          TEXT    DEFAULT 'draft'
                                    CHECK(status IN ('draft','sent','viewed','accepted','rejected')),
            created_at      TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS call_briefs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id         INTEGER NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
            company_research TEXT,
            pain_points     TEXT,
            talking_points  TEXT,
            questions_to_ask TEXT,
            competitive_landscape TEXT,
            recommended_solution  TEXT,
            pdf_path        TEXT,
            created_at      TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS activities (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id         INTEGER REFERENCES deals(id) ON DELETE CASCADE,
            tower           TEXT    DEFAULT 'digital-ai-services',
            activity_type   TEXT    NOT NULL,
            description     TEXT,
            created_at      TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS referrals (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            from_deal_id    INTEGER REFERENCES deals(id),
            referred_company TEXT   NOT NULL,
            referred_contact TEXT,
            referred_email  TEXT,
            tower           TEXT    DEFAULT 'digital-ai-services',
            status          TEXT    DEFAULT 'pending'
                                    CHECK(status IN ('pending','contacted','converted','lost')),
            notes           TEXT,
            created_at      TEXT    DEFAULT (datetime('now'))
        );

    """)
    conn.commit()
    # Indexes created separately to handle cases where columns may not exist yet
    _create_indexes_safe(conn)


def _create_indexes_safe(conn: sqlite3.Connection):
    """Create indexes — each attempted individually so missing columns don't block others."""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_deals_stage ON deals(stage)",
        "CREATE INDEX IF NOT EXISTS idx_outreach_deal ON outreach_log(deal_id)",
        "CREATE INDEX IF NOT EXISTS idx_trial_metrics_deal ON trial_metrics(deal_id)",
        "CREATE INDEX IF NOT EXISTS idx_activities_deal ON activities(deal_id)",
        # Tower indexes only work after migration adds the tower column:
        "CREATE INDEX IF NOT EXISTS idx_deals_tower ON deals(tower)",
        "CREATE INDEX IF NOT EXISTS idx_outreach_tower ON outreach_log(tower)",
        "CREATE INDEX IF NOT EXISTS idx_activities_tower ON activities(tower)",
    ]
    for sql in indexes:
        try:
            conn.execute(sql)
        except sqlite3.OperationalError:
            pass  # Column doesn't exist yet — will be added by migrate_existing_db()
    conn.commit()


# ── Deal CRUD ────────────────────────────────────────────────────────────────

def create_deal(conn: sqlite3.Connection, company: str,
                tower: str = "digital-ai-services", **kwargs) -> int:
    kwargs["tower"] = tower
    cols = ["company"] + list(kwargs.keys())
    vals = [company] + list(kwargs.values())
    placeholders = ", ".join(["?"] * len(cols))
    cur = conn.execute(
        f"INSERT INTO deals ({', '.join(cols)}) VALUES ({placeholders})", vals
    )
    conn.commit()
    log_activity(conn, cur.lastrowid, "deal_created", f"New deal: {company}", tower=tower)
    return cur.lastrowid


def update_deal(conn: sqlite3.Connection, deal_id: int, **kwargs):
    if not kwargs:
        return
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    conn.execute(
        f"UPDATE deals SET {fields}, updated_at = datetime('now') WHERE id = ?",
        (*kwargs.values(), deal_id)
    )
    conn.commit()
    if "stage" in kwargs:
        deal = get_deal(conn, deal_id)
        tower = dict(deal).get("tower", "digital-ai-services") if deal else "digital-ai-services"
        log_activity(conn, deal_id, "stage_changed", f"Moved to: {kwargs['stage']}", tower=tower)


def get_deal(conn: sqlite3.Connection, deal_id: int) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM deals WHERE id = ?", (deal_id,)).fetchone()


def get_deals_by_stage(conn: sqlite3.Connection,
                       tower: Optional[str] = None) -> dict:
    q = "SELECT * FROM deals WHERE stage != 'Closed Lost'"
    params = []
    if tower:
        q += " AND tower = ?"
        params.append(tower)
    q += " ORDER BY updated_at DESC"
    deals = conn.execute(q, params).fetchall()
    grouped = {s: [] for s in STAGES}
    for d in deals:
        s = d["stage"] if d["stage"] in grouped else "Prospect"
        grouped[s].append(d)
    return grouped


# ── Outreach ─────────────────────────────────────────────────────────────────

def log_outreach(conn: sqlite3.Connection, company: str, channel: str = "Email",
                 message: str = "", response: str = "", follow_up_date: Optional[str] = None,
                 deal_id: Optional[int] = None, tower: str = "digital-ai-services",
                 lead_source: str = "") -> int:
    cur = conn.execute("""
        INSERT INTO outreach_log
            (deal_id, tower, company, channel, message_summary, response, follow_up_date, lead_source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (deal_id, tower, company, channel, message, response, follow_up_date, lead_source))
    conn.commit()
    if deal_id:
        log_activity(conn, deal_id, "outreach", f"{channel}: {message[:80]}", tower=tower)
    return cur.lastrowid


# ── Trial Metrics ─────────────────────────────────────────────────────────────

def log_trial_day(conn: sqlite3.Connection, deal_id: int, missed_calls: int = 0,
                  texts_sent: int = 0, replies: int = 0, calls_recovered: int = 0,
                  revenue_recovered: float = 0.0, notes: str = "") -> int:
    """Log one day of trial client performance metrics."""
    cur = conn.execute("""
        INSERT INTO trial_metrics
            (deal_id, missed_calls, texts_sent, replies, calls_recovered, revenue_recovered, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (deal_id, missed_calls, texts_sent, replies, calls_recovered, revenue_recovered, notes))
    conn.commit()
    return cur.lastrowid


def get_trial_summary(conn: sqlite3.Connection, deal_id: int) -> dict:
    """Aggregate trial metrics for a client — used for Day 10/14 check-in reports."""
    row = conn.execute("""
        SELECT
            COUNT(*) as days_logged,
            SUM(missed_calls) as total_missed,
            SUM(texts_sent) as total_texts,
            SUM(replies) as total_replies,
            SUM(calls_recovered) as total_recovered,
            SUM(revenue_recovered) as total_revenue
        FROM trial_metrics WHERE deal_id = ?
    """, (deal_id,)).fetchone()
    if not row:
        return {}
    d = dict(row)
    d["recovery_rate"] = round(d["total_recovered"] / max(d["total_missed"], 1) * 100)
    d["reply_rate"] = round(d["total_replies"] / max(d["total_texts"], 1) * 100)
    return d


# ── Pipeline Stats (multi-tower) ──────────────────────────────────────────────

def get_pipeline_stats(conn: sqlite3.Connection,
                       tower: Optional[str] = None) -> dict:
    """Full pipeline stats, optionally filtered by tower."""
    def _count(q, params=()):
        return conn.execute(q, params).fetchone()[0]

    tower_filter = "AND tower = ?" if tower else ""
    p = (tower,) if tower else ()

    total    = _count(f"SELECT COUNT(*) FROM deals WHERE stage NOT IN ('Closed Lost') {tower_filter}", p)
    won      = _count(f"SELECT COUNT(*) FROM deals WHERE stage = 'Closed Won' {tower_filter}", p)
    lost     = _count(f"SELECT COUNT(*) FROM deals WHERE stage = 'Closed Lost' {tower_filter}", p)
    trials   = _count(f"SELECT COUNT(*) FROM deals WHERE stage = 'Trial Active' {tower_filter}", p)
    meetings = _count(f"SELECT COUNT(*) FROM deals WHERE stage = 'Meeting Booked' AND updated_at > datetime('now', '-7 days') {tower_filter}", p)
    proposals = _count(f"SELECT COUNT(*) FROM deals WHERE stage = 'Proposal Sent' {tower_filter}", p)
    outreach_today = _count(f"SELECT COUNT(*) FROM outreach_log WHERE date(created_at) = date('now') {tower_filter}", p)
    outreach_week  = _count(f"SELECT COUNT(*) FROM outreach_log WHERE created_at > datetime('now', '-7 days') {tower_filter}", p)
    followups_due  = _count(f"SELECT COUNT(*) FROM outreach_log WHERE follow_up_date <= date('now') AND (response IS NULL OR response = '') {tower_filter}", p)

    mrr_row = conn.execute(
        f"SELECT COALESCE(SUM(monthly_fee), 0) FROM deals WHERE stage = 'Closed Won' {tower_filter}", p
    ).fetchone()
    mrr = mrr_row[0] if mrr_row else 0

    pipeline_value = conn.execute(
        f"SELECT COALESCE(SUM(setup_fee + monthly_fee * 12), 0) FROM deals WHERE stage NOT IN ('Closed Won','Closed Lost') {tower_filter}", p
    ).fetchone()[0]

    stage_counts = {}
    for row in conn.execute(
        f"SELECT stage, COUNT(*) as c FROM deals {('WHERE tower = ?' if tower else '')} GROUP BY stage",
        p
    ):
        stage_counts[row["stage"]] = row["c"]

    return {
        "total_active": total, "deals_won": won, "deals_lost": lost,
        "trials_active": trials, "meetings_this_week": meetings,
        "proposals_out": proposals, "outreach_today": outreach_today,
        "outreach_week": outreach_week, "followups_due": followups_due,
        "mrr": mrr, "pipeline_value": pipeline_value,
        "stage_counts": stage_counts,
        "win_rate": round(won / max(won + lost, 1) * 100),
        "tower": tower or "all",
    }


def get_tower_summary(conn: sqlite3.Connection) -> list[dict]:
    """Quick summary for all towers — used by the top-level dashboard."""
    summaries = []
    for tower_id, meta in TOWERS.items():
        stats = get_pipeline_stats(conn, tower=tower_id)
        summaries.append({
            "id": tower_id,
            "label": meta["label"],
            "icon": meta["icon"],
            "color": meta["color"],
            "deals_won": stats["deals_won"],
            "trials_active": stats["trials_active"],
            "outreach_week": stats["outreach_week"],
            "mrr": stats["mrr"],
            "followups_due": stats["followups_due"],
        })
    return summaries


# ── Activity Log ──────────────────────────────────────────────────────────────

def log_activity(conn: sqlite3.Connection, deal_id: int, activity_type: str,
                 description: str = "", tower: str = "digital-ai-services"):
    conn.execute(
        "INSERT INTO activities (deal_id, tower, activity_type, description) VALUES (?, ?, ?, ?)",
        (deal_id, tower, activity_type, description)
    )
    conn.commit()


# ── Referrals ─────────────────────────────────────────────────────────────────

def create_referral(conn: sqlite3.Connection, from_deal_id: int,
                    referred_company: str, tower: str = "digital-ai-services",
                    **kwargs) -> int:
    """Record a referral from a won/trial client."""
    cur = conn.execute("""
        INSERT INTO referrals (from_deal_id, referred_company, tower)
        VALUES (?, ?, ?)
    """, (from_deal_id, referred_company, tower))
    conn.commit()
    log_activity(conn, from_deal_id, "referral_given",
                 f"Referred: {referred_company}", tower=tower)
    return cur.lastrowid


# ── EC2 Sync ──────────────────────────────────────────────────────────────────

def sync_to_ec2() -> bool:
    """Push local pipeline.db to EC2. Run on Mac after local changes."""
    if _is_ec2():
        logger.info("Already on EC2 — no sync needed")
        return True
    if not EC2_KEY.exists():
        logger.error(f"EC2 key not found: {EC2_KEY}")
        return False
    local_db = str(MAC_DB_PATH)
    if not Path(local_db).exists():
        logger.error("Local pipeline.db not found — nothing to sync")
        return False
    cmd = [
        "scp", "-i", str(EC2_KEY), "-o", "StrictHostKeyChecking=no",
        local_db,
        f"{EC2_HOST}:{EC2_DB_PATH}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        logger.info("pipeline.db synced to EC2")
        return True
    logger.error(f"Sync failed: {result.stderr}")
    return False


def pull_from_ec2() -> bool:
    """Pull EC2 pipeline.db to local Mac. Run to get latest data."""
    if _is_ec2():
        logger.info("Already on EC2 — no pull needed")
        return True
    if not EC2_KEY.exists():
        logger.error(f"EC2 key not found: {EC2_KEY}")
        return False
    MAC_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "scp", "-i", str(EC2_KEY), "-o", "StrictHostKeyChecking=no",
        f"{EC2_HOST}:{EC2_DB_PATH}",
        str(MAC_DB_PATH)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        logger.info("pipeline.db pulled from EC2")
        return True
    logger.error(f"Pull failed: {result.stderr}")
    return False


# ── Migrate existing pipeline.db → new schema ─────────────────────────────────

def migrate_existing_db():
    """
    Add new multi-tower columns to an existing pipeline.db that was built
    with the old sales-pipeline schema (no tower/email_source/trial_metrics).
    Safe to run multiple times (uses ADD COLUMN IF NOT EXISTS via try/except).
    """
    conn = get_db()
    migrations = [
        "ALTER TABLE deals ADD COLUMN tower TEXT NOT NULL DEFAULT 'digital-ai-services'",
        "ALTER TABLE deals ADD COLUMN email_source TEXT",
        "ALTER TABLE deals ADD COLUMN email_confidence INTEGER DEFAULT 0",
        "ALTER TABLE deals ADD COLUMN city TEXT DEFAULT 'Naples'",
        "ALTER TABLE deals ADD COLUMN state TEXT DEFAULT 'FL'",
        "ALTER TABLE deals ADD COLUMN website TEXT",
        "ALTER TABLE deals ADD COLUMN trial_start_date TEXT",
        "ALTER TABLE deals ADD COLUMN trial_end_date TEXT",
        "ALTER TABLE outreach_log ADD COLUMN tower TEXT DEFAULT 'digital-ai-services'",
        "ALTER TABLE outreach_log ADD COLUMN follow_up_count INTEGER DEFAULT 0",
        "ALTER TABLE activities ADD COLUMN tower TEXT DEFAULT 'digital-ai-services'",
    ]
    applied = 0
    for sql in migrations:
        try:
            conn.execute(sql)
            conn.commit()
            applied += 1
        except sqlite3.OperationalError:
            pass  # Column already exists
    print(f"Migration complete: {applied} new columns added")
    conn.close()


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Marceau Pipeline DB utilities")
    parser.add_argument("--sync", action="store_true", help="Push local DB to EC2")
    parser.add_argument("--pull", action="store_true", help="Pull EC2 DB to local")
    parser.add_argument("--migrate", action="store_true", help="Add multi-tower columns to existing DB")
    parser.add_argument("--stats", action="store_true", help="Print pipeline stats")
    parser.add_argument("--tower", default=None, help="Filter by tower ID")
    args = parser.parse_args()

    if args.sync:
        ok = sync_to_ec2()
        print("✅ Synced to EC2" if ok else "❌ Sync failed")
    elif args.pull:
        ok = pull_from_ec2()
        print("✅ Pulled from EC2" if ok else "❌ Pull failed")
    elif args.migrate:
        migrate_existing_db()
    elif args.stats:
        conn = get_db()
        if args.tower:
            stats = get_pipeline_stats(conn, tower=args.tower)
            print(json.dumps(stats, indent=2))
        else:
            summaries = get_tower_summary(conn)
            for s in summaries:
                print(f"{s['icon']} {s['label']}: {s['deals_won']} won | "
                      f"{s['trials_active']} trials | "
                      f"${s['mrr']:,.0f} MRR | "
                      f"{s['outreach_week']} outreach this week")
        conn.close()
    else:
        parser.print_help()
