#!/usr/bin/env python3
"""
BOABFIT Client Database — Single source of truth for all client data.

Replaces scattered JSON files (roster.json, drip_state.json, abandon_sent.json)
with a SQLite database tracking the full client lifecycle.

Usage:
    from client_db import BoabfitDB
    db = BoabfitDB()
    db.add_client(email="...", name="...", phone="...", program="barbie-body-6wk", source="stripe")
    db.log_email(email="...", email_type="welcome", subject="...")
    db.update_program_status(email="...", week=3, status="active")
"""

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Database location
DB_PATHS = [
    Path("/home/ec2-user/data/boabfit/clients.db"),
    Path("/home/clawdbot/dev-sandbox/projects/boabfit/data/clients.db"),
    Path(os.environ.get("BOABFIT_DB", "")),
]

def _get_db_path() -> Path:
    for p in DB_PATHS:
        if str(p) and p.parent.exists():
            return p
    return Path("projects/boabfit/data/clients.db")


class BoabfitDB:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path) if db_path else _get_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        self.conn.executescript("""
            -- Core client record
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                phone TEXT,
                instagram TEXT,
                source TEXT DEFAULT 'website',          -- stripe, manual, instagram, referral
                signup_date TEXT NOT NULL,
                status TEXT DEFAULT 'active',            -- lead, onboarding, active, at_risk, completed, churned, paused, alumni
                stripe_customer_id TEXT,                 -- Stripe customer ID (links to all payments)
                last_workout_logged_at TEXT,             -- most predictive churn indicator
                days_since_last_activity INTEGER,        -- computed: >7 = risk, >14 = critical
                workout_completion_rate REAL,            -- 0.0-1.0, primary compliance metric
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            -- Program enrollments (a client can buy multiple programs)
            CREATE TABLE IF NOT EXISTS enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                program TEXT NOT NULL,                   -- barbie-body-6wk, custom-coaching, etc.
                start_date TEXT NOT NULL,
                end_date TEXT,                           -- calculated from program length
                current_week INTEGER DEFAULT 1,
                total_weeks INTEGER DEFAULT 6,
                status TEXT DEFAULT 'active',            -- active, completed, paused, refunded
                program_completed INTEGER DEFAULT 0,     -- explicit boolean: 1 = finished all weeks
                stripe_payment_id TEXT,                  -- Stripe charge/subscription ID
                amount_paid REAL DEFAULT 0,
                currency TEXT DEFAULT 'USD',
                enrolled_by TEXT DEFAULT 'self',         -- self, julia, admin
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (client_id) REFERENCES clients(id)
            );

            -- Communication log (every email, SMS, notification)
            CREATE TABLE IF NOT EXISTS communications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                channel TEXT NOT NULL,                   -- email, sms, instagram_dm, push
                comm_type TEXT NOT NULL,                 -- welcome, drip_day3, drip_day7, drip_day14, checkin, promo, manual
                subject TEXT,
                status TEXT DEFAULT 'sent',              -- sent, delivered, opened, clicked, bounced, failed
                sent_at TEXT DEFAULT (datetime('now')),
                metadata TEXT,                           -- JSON blob for extra data
                FOREIGN KEY (client_id) REFERENCES clients(id)
            );

            -- Engagement tracking (check-ins, app usage, social interactions)
            CREATE TABLE IF NOT EXISTS engagement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,                -- checkin, workout_completed, app_login, instagram_comment, photo_shared
                event_date TEXT DEFAULT (datetime('now')),
                details TEXT,                            -- JSON blob
                FOREIGN KEY (client_id) REFERENCES clients(id)
            );

            -- Indexes for common queries
            CREATE INDEX IF NOT EXISTS idx_clients_email ON clients(email);
            CREATE INDEX IF NOT EXISTS idx_clients_status ON clients(status);
            CREATE INDEX IF NOT EXISTS idx_enrollments_client ON enrollments(client_id);
            CREATE INDEX IF NOT EXISTS idx_enrollments_status ON enrollments(status);
            CREATE INDEX IF NOT EXISTS idx_comms_client ON communications(client_id);
            CREATE INDEX IF NOT EXISTS idx_engagement_client ON engagement(client_id);
        """)
        self.conn.commit()
        self._migrate()

    def _migrate(self):
        """Add columns that may not exist in older databases."""
        existing = {row[1] for row in self.conn.execute("PRAGMA table_info(clients)").fetchall()}
        migrations = {
            "stripe_customer_id": "ALTER TABLE clients ADD COLUMN stripe_customer_id TEXT",
            "last_workout_logged_at": "ALTER TABLE clients ADD COLUMN last_workout_logged_at TEXT",
            "days_since_last_activity": "ALTER TABLE clients ADD COLUMN days_since_last_activity INTEGER",
            "workout_completion_rate": "ALTER TABLE clients ADD COLUMN workout_completion_rate REAL",
        }
        for col, sql in migrations.items():
            if col not in existing:
                self.conn.execute(sql)

        existing_enroll = {row[1] for row in self.conn.execute("PRAGMA table_info(enrollments)").fetchall()}
        if "program_completed" not in existing_enroll:
            self.conn.execute("ALTER TABLE enrollments ADD COLUMN program_completed INTEGER DEFAULT 0")

        self.conn.commit()

    # ── Client Operations ──────────────────────────────────────────────

    def add_client(self, email: str, name: str, phone: str = "",
                   instagram: str = "", source: str = "website",
                   signup_date: Optional[str] = None, status: str = "active",
                   stripe_customer_id: str = "", notes: str = "") -> int:
        """Add or update a client. Returns client ID."""
        email = email.strip().lower()
        now = signup_date or datetime.now(timezone.utc).isoformat()

        existing = self.conn.execute("SELECT id FROM clients WHERE email = ?", (email,)).fetchone()
        if existing:
            self.conn.execute("""
                UPDATE clients SET name=?, phone=?, instagram=?, source=?, status=?,
                stripe_customer_id=COALESCE(NULLIF(?, ''), stripe_customer_id),
                notes=?, updated_at=datetime('now') WHERE id=?
            """, (name, phone, instagram, source, status, stripe_customer_id, notes, existing['id']))
            self.conn.commit()
            return existing['id']

        cur = self.conn.execute("""
            INSERT INTO clients (email, name, phone, instagram, source, signup_date, status,
                stripe_customer_id, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (email, name, phone, instagram, source, now, status, stripe_customer_id, notes))
        self.conn.commit()
        return cur.lastrowid

    def get_client(self, email: str) -> Optional[Dict]:
        """Get client by email."""
        row = self.conn.execute("SELECT * FROM clients WHERE email = ?", (email.lower(),)).fetchone()
        return dict(row) if row else None

    def get_all_clients(self, status: Optional[str] = None) -> List[Dict]:
        """Get all clients, optionally filtered by status."""
        if status:
            rows = self.conn.execute("SELECT * FROM clients WHERE status = ? ORDER BY signup_date DESC", (status,)).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM clients ORDER BY signup_date DESC").fetchall()
        return [dict(r) for r in rows]

    # ── Enrollment Operations ──────────────────────────────────────────

    def enroll(self, email: str, program: str, amount: float = 0,
               stripe_id: str = "", enrolled_by: str = "self",
               total_weeks: int = 6, start_date: Optional[str] = None) -> int:
        """Enroll a client in a program. Returns enrollment ID."""
        client = self.get_client(email)
        if not client:
            raise ValueError(f"Client not found: {email}")

        start = start_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cur = self.conn.execute("""
            INSERT INTO enrollments (client_id, program, start_date, total_weeks,
                stripe_payment_id, amount_paid, enrolled_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (client['id'], program, start, total_weeks, stripe_id, amount, enrolled_by))
        self.conn.commit()
        return cur.lastrowid

    def update_program_status(self, email: str, week: Optional[int] = None,
                              status: Optional[str] = None) -> bool:
        """Update a client's active enrollment progress."""
        client = self.get_client(email)
        if not client:
            return False

        enrollment = self.conn.execute("""
            SELECT id FROM enrollments WHERE client_id = ? AND status = 'active'
            ORDER BY created_at DESC LIMIT 1
        """, (client['id'],)).fetchone()
        if not enrollment:
            return False

        updates = []
        values = []
        if week is not None:
            updates.append("current_week = ?")
            values.append(week)
        if status:
            updates.append("status = ?")
            values.append(status)
        values.append(enrollment['id'])

        self.conn.execute(f"UPDATE enrollments SET {', '.join(updates)} WHERE id = ?", values)
        self.conn.commit()
        return True

    def get_enrollments(self, email: str) -> List[Dict]:
        """Get all enrollments for a client."""
        client = self.get_client(email)
        if not client:
            return []
        rows = self.conn.execute(
            "SELECT * FROM enrollments WHERE client_id = ? ORDER BY created_at DESC",
            (client['id'],)
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Workout Tracking ────────────────────────────────────────────────

    def log_workout(self, email: str, details: Optional[Dict] = None) -> bool:
        """Log a workout completion. Updates client fitness metrics."""
        client = self.get_client(email)
        if not client:
            return False

        now = datetime.now(timezone.utc).isoformat()

        # Log the engagement event
        self.log_engagement(email, "workout_completed", details)

        # Update client-level tracking fields
        self.conn.execute("""
            UPDATE clients SET last_workout_logged_at = ?, days_since_last_activity = 0,
            updated_at = datetime('now') WHERE id = ?
        """, (now, client['id']))

        # Update workout completion rate on active enrollment
        enrollment = self.conn.execute("""
            SELECT id, total_weeks FROM enrollments
            WHERE client_id = ? AND status = 'active'
            ORDER BY created_at DESC LIMIT 1
        """, (client['id'],)).fetchone()

        if enrollment:
            total_workouts = self.conn.execute("""
                SELECT COUNT(*) FROM engagement
                WHERE client_id = ? AND event_type = 'workout_completed'
            """, (client['id'],)).fetchone()[0]
            # Assume ~5 workouts per week as target
            expected = enrollment['total_weeks'] * 5
            rate = min(total_workouts / max(expected, 1), 1.0)
            self.conn.execute(
                "UPDATE clients SET workout_completion_rate = ? WHERE id = ?",
                (round(rate, 2), client['id'])
            )

        self.conn.commit()
        return True

    def mark_program_completed(self, email: str) -> bool:
        """Mark a client's active enrollment as completed."""
        client = self.get_client(email)
        if not client:
            return False

        self.conn.execute("""
            UPDATE enrollments SET status = 'completed', program_completed = 1
            WHERE client_id = ? AND status = 'active'
        """, (client['id'],))
        self.conn.execute(
            "UPDATE clients SET status = 'alumni', updated_at = datetime('now') WHERE id = ?",
            (client['id'],)
        )
        self.conn.commit()
        return True

    def get_at_risk_clients(self, days_threshold: int = 7) -> List[Dict]:
        """Get clients who haven't logged a workout in N+ days."""
        rows = self.conn.execute("""
            SELECT * FROM clients
            WHERE status = 'active'
            AND (last_workout_logged_at IS NULL
                 OR julianday('now') - julianday(last_workout_logged_at) > ?)
        """, (days_threshold,)).fetchall()
        return [dict(r) for r in rows]

    # ── Communication Operations ──────────────────────────────────────

    def log_email(self, email: str, comm_type: str, subject: str = "",
                  channel: str = "email", status: str = "sent",
                  metadata: Optional[Dict] = None) -> bool:
        """Log a communication sent to a client."""
        client = self.get_client(email)
        if not client:
            return False

        self.conn.execute("""
            INSERT INTO communications (client_id, channel, comm_type, subject, status, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (client['id'], channel, comm_type, subject, status,
              json.dumps(metadata) if metadata else None))
        self.conn.commit()
        return True

    def has_received(self, email: str, comm_type: str) -> bool:
        """Check if client has already received a specific communication type."""
        client = self.get_client(email)
        if not client:
            return False
        row = self.conn.execute("""
            SELECT COUNT(*) as cnt FROM communications
            WHERE client_id = ? AND comm_type = ? AND status != 'failed'
        """, (client['id'], comm_type)).fetchone()
        return row['cnt'] > 0

    def get_communications(self, email: str) -> List[Dict]:
        """Get all communications for a client."""
        client = self.get_client(email)
        if not client:
            return []
        rows = self.conn.execute(
            "SELECT * FROM communications WHERE client_id = ? ORDER BY sent_at DESC",
            (client['id'],)
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Engagement Operations ─────────────────────────────────────────

    def log_engagement(self, email: str, event_type: str,
                       details: Optional[Dict] = None) -> bool:
        """Log a client engagement event."""
        client = self.get_client(email)
        if not client:
            return False

        self.conn.execute("""
            INSERT INTO engagement (client_id, event_type, details)
            VALUES (?, ?, ?)
        """, (client['id'], event_type, json.dumps(details) if details else None))
        self.conn.commit()
        return True

    # ── Analytics ─────────────────────────────────────────────────────

    def get_dashboard(self) -> Dict[str, Any]:
        """Get overview stats for Julia's dashboard."""
        total = self.conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
        active = self.conn.execute("SELECT COUNT(*) FROM clients WHERE status = 'active'").fetchone()[0]
        active_enrollments = self.conn.execute("SELECT COUNT(*) FROM enrollments WHERE status = 'active'").fetchone()[0]
        total_revenue = self.conn.execute("SELECT COALESCE(SUM(amount_paid), 0) FROM enrollments").fetchone()[0]
        comms_sent = self.conn.execute("SELECT COUNT(*) FROM communications").fetchone()[0]

        return {
            "total_clients": total,
            "active_clients": active,
            "active_enrollments": active_enrollments,
            "total_revenue": total_revenue,
            "communications_sent": comms_sent,
        }

    # ── Migration ─────────────────────────────────────────────────────

    def migrate_from_json(self, roster_path: str, drip_state_path: str):
        """Import existing clients from roster.json and drip_state.json."""
        imported = 0

        # Import roster (old clients)
        if os.path.exists(roster_path):
            with open(roster_path) as f:
                roster = json.load(f)
            for client in roster:
                self.add_client(
                    email=client.get("email", ""),
                    name=client.get("name", ""),
                    phone=client.get("phone", ""),
                    signup_date=client.get("signup_date", ""),
                    source="legacy_roster",
                    status="completed",
                )
                imported += 1

        # Import drip state (new clients)
        if os.path.exists(drip_state_path):
            with open(drip_state_path) as f:
                state = json.load(f)
            for email, data in state.get("signups", {}).items():
                if not email:
                    continue
                client_id = self.add_client(
                    email=email,
                    name=data.get("name", ""),
                    phone=data.get("phone", ""),
                    signup_date=data.get("signed_up_at", ""),
                    source="website",
                    status="active",
                )
                # Log emails that were already sent
                for day in data.get("emails_sent", []):
                    comm_type = {0: "welcome", 3: "drip_day3", 7: "drip_day7", 14: "drip_day14"}.get(day, f"drip_day{day}")
                    self.log_email(email, comm_type, channel="email", status="sent")
                imported += 1

        return imported

    def close(self):
        self.conn.close()


if __name__ == "__main__":
    import sys

    db = BoabfitDB("projects/boabfit/data/clients.db")

    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        count = db.migrate_from_json(
            "projects/boabfit/clients/roster.json",
            "projects/boabfit/data/drip_state.json"
        )
        print(f"Migrated {count} clients")
        print(json.dumps(db.get_dashboard(), indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "dashboard":
        print(json.dumps(db.get_dashboard(), indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "list":
        for c in db.get_all_clients():
            enrollments = db.get_enrollments(c["email"])
            comms = db.get_communications(c["email"])
            print(f"{c['name']} ({c['email']}) — status={c['status']}, enrollments={len(enrollments)}, comms={len(comms)}")
    else:
        print("Usage: python client_db.py [migrate|dashboard|list]")

    db.close()
