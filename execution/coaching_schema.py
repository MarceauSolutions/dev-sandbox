#!/usr/bin/env python3
"""
Fitness Coaching Schema — Extends pipeline.db with coaching-specific tables.

Creates:
  - coaching_clients: Active coaching clients with subscription info
  - coaching_workouts: Generated workout programs per client
  - coaching_checkins: Monday check-in records
  - coaching_messages: Automated message log

Usage:
    python execution/coaching_schema.py          # Create/migrate tables
    python execution/coaching_schema.py --status # Show client counts
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Import from sibling module
sys.path.insert(0, str(Path(__file__).parent))
from pipeline_db import get_db, get_db_path


def create_coaching_tables(conn: sqlite3.Connection):
    """Create fitness-coaching specific tables."""
    conn.executescript("""
        -- Active coaching clients (linked to deals via deal_id or standalone)
        CREATE TABLE IF NOT EXISTS coaching_clients (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id         INTEGER REFERENCES deals(id),
            
            -- Client info
            name            TEXT NOT NULL,
            email           TEXT,
            phone           TEXT,
            
            -- Subscription
            status          TEXT DEFAULT 'active' 
                            CHECK(status IN ('onboarding', 'active', 'paused', 'cancelled')),
            plan_type       TEXT DEFAULT 'monthly',  -- monthly, quarterly, annual
            monthly_rate    REAL DEFAULT 197.0,
            start_date      TEXT,
            next_billing    TEXT,
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT,
            
            -- Fitness profile
            goal            TEXT DEFAULT 'general fitness',
            experience      TEXT DEFAULT 'intermediate',
            equipment       TEXT DEFAULT 'full gym',
            days_per_week   INTEGER DEFAULT 4,
            injuries_notes  TEXT,
            preferences     TEXT,  -- JSON blob
            
            -- Current program
            current_program_id INTEGER,
            program_week    INTEGER DEFAULT 1,
            
            -- Check-in tracking
            last_checkin_date TEXT,
            checkin_streak  INTEGER DEFAULT 0,
            missed_checkins INTEGER DEFAULT 0,
            
            -- Timestamps
            created_at      TEXT DEFAULT (datetime('now')),
            updated_at      TEXT DEFAULT (datetime('now'))
        );

        -- Generated workout programs
        CREATE TABLE IF NOT EXISTS coaching_workouts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id       INTEGER NOT NULL REFERENCES coaching_clients(id),
            
            program_name    TEXT NOT NULL,
            program_data    TEXT,  -- Full JSON workout spec
            pdf_path        TEXT,
            
            -- Program metadata
            goal            TEXT,
            weeks           INTEGER DEFAULT 4,
            days_per_week   INTEGER DEFAULT 4,
            
            -- Version tracking
            version         INTEGER DEFAULT 1,
            active          INTEGER DEFAULT 1,
            
            created_at      TEXT DEFAULT (datetime('now')),
            sent_at         TEXT
        );

        -- Weekly check-in records
        CREATE TABLE IF NOT EXISTS coaching_checkins (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id       INTEGER NOT NULL REFERENCES coaching_clients(id),
            
            week_of         TEXT NOT NULL,  -- Monday date (YYYY-MM-DD)
            
            -- Submitted data
            workouts_completed INTEGER DEFAULT 0,
            energy_level    INTEGER,  -- 1-5
            soreness_level  INTEGER,  -- 1-5
            weight          REAL,
            notes           TEXT,
            photos_received INTEGER DEFAULT 0,
            
            -- Coach response
            coach_feedback  TEXT,
            program_adjusted INTEGER DEFAULT 0,
            
            -- Timestamps
            requested_at    TEXT DEFAULT (datetime('now')),
            submitted_at    TEXT,
            responded_at    TEXT
        );

        -- Automated message log
        CREATE TABLE IF NOT EXISTS coaching_messages (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id       INTEGER REFERENCES coaching_clients(id),
            
            message_type    TEXT NOT NULL,  -- welcome, checkin_request, checkin_reminder, workout_delivery, etc.
            channel         TEXT DEFAULT 'email',  -- email, sms
            subject         TEXT,
            body_preview    TEXT,
            
            -- n8n workflow info
            n8n_workflow    TEXT,
            n8n_execution_id TEXT,
            
            -- Status
            status          TEXT DEFAULT 'sent' CHECK(status IN ('pending', 'sent', 'failed', 'opened')),
            error           TEXT,
            
            sent_at         TEXT DEFAULT (datetime('now'))
        );

        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_coaching_clients_status ON coaching_clients(status);
        CREATE INDEX IF NOT EXISTS idx_coaching_clients_email ON coaching_clients(email);
        CREATE INDEX IF NOT EXISTS idx_coaching_workouts_client ON coaching_workouts(client_id);
        CREATE INDEX IF NOT EXISTS idx_coaching_checkins_client ON coaching_checkins(client_id);
        CREATE INDEX IF NOT EXISTS idx_coaching_checkins_week ON coaching_checkins(week_of);
        CREATE INDEX IF NOT EXISTS idx_coaching_messages_client ON coaching_messages(client_id);
        CREATE INDEX IF NOT EXISTS idx_coaching_messages_type ON coaching_messages(message_type);
    """)
    conn.commit()
    print("✓ Coaching tables created/verified")


def get_coaching_stats(conn: sqlite3.Connection) -> dict:
    """Get coaching tower statistics."""
    stats = {}
    
    # Client counts by status
    rows = conn.execute(
        "SELECT status, COUNT(*) as cnt FROM coaching_clients GROUP BY status"
    ).fetchall()
    stats["clients_by_status"] = {row["status"]: row["cnt"] for row in rows}
    
    # Total MRR
    mrr = conn.execute(
        "SELECT COALESCE(SUM(monthly_rate), 0) FROM coaching_clients WHERE status = 'active'"
    ).fetchone()[0]
    stats["mrr"] = mrr
    
    # This week's check-ins
    from datetime import date, timedelta
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    monday_str = monday.strftime("%Y-%m-%d")
    
    checkins_due = conn.execute(
        "SELECT COUNT(*) FROM coaching_clients WHERE status = 'active'"
    ).fetchone()[0]
    
    checkins_received = conn.execute(
        "SELECT COUNT(*) FROM coaching_checkins WHERE week_of = ? AND submitted_at IS NOT NULL",
        (monday_str,)
    ).fetchone()[0]
    
    stats["checkins_due"] = checkins_due
    stats["checkins_received"] = checkins_received
    
    # Workouts generated this month
    workouts_month = conn.execute(
        "SELECT COUNT(*) FROM coaching_workouts WHERE created_at > datetime('now', '-30 days')"
    ).fetchone()[0]
    stats["workouts_generated_30d"] = workouts_month
    
    return stats


def show_status():
    """Print coaching tower status."""
    conn = get_db()
    create_coaching_tables(conn)
    stats = get_coaching_stats(conn)
    conn.close()
    
    print("\n💪 Fitness Coaching Tower Status")
    print("=" * 40)
    
    print("\nClients by Status:")
    for status, count in stats.get("clients_by_status", {}).items():
        print(f"  {status}: {count}")
    
    print(f"\nMRR: ${stats['mrr']:,.2f}")
    print(f"Check-ins this week: {stats['checkins_received']}/{stats['checkins_due']}")
    print(f"Workouts generated (30d): {stats['workouts_generated_30d']}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Coaching schema management")
    parser.add_argument("--status", action="store_true", help="Show coaching stats")
    args = parser.parse_args()
    
    conn = get_db()
    create_coaching_tables(conn)
    
    if args.status:
        conn.close()
        show_status()
    else:
        print("Run with --status to see stats")
        conn.close()
