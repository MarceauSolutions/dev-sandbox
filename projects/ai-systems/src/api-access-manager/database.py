"""
API Access Manager — Database Layer
SQLite models for tracking platform applications, API keys, and steps.
"""

import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "api_access_manager.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS platforms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'not_started',  -- not_started, in_progress, approved, rejected, suspended
            priority_order INTEGER DEFAULT 0,
            application_url TEXT,
            app_id TEXT,
            app_name TEXT,
            notes TEXT,
            started_at TEXT,
            approved_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS application_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform_id INTEGER NOT NULL,
            step_number INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            step_type TEXT DEFAULT 'manual',  -- manual, automated, info
            is_completed INTEGER DEFAULT 0,
            completed_at TEXT,
            notes TEXT,
            FOREIGN KEY (platform_id) REFERENCES platforms(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform_id INTEGER NOT NULL,
            key_name TEXT NOT NULL,
            key_type TEXT DEFAULT 'api_key',  -- api_key, secret, token, refresh_token, access_token
            key_value_encrypted TEXT,
            env_var_name TEXT,
            issued_at TEXT,
            expires_at TEXT,
            rotation_days INTEGER DEFAULT 90,
            last_rotated TEXT,
            is_active INTEGER DEFAULT 1,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (platform_id) REFERENCES platforms(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform_id INTEGER NOT NULL,
            reminder_type TEXT NOT NULL,  -- follow_up, rotation, review, renewal
            title TEXT NOT NULL,
            description TEXT,
            due_date TEXT NOT NULL,
            calendar_event_id TEXT,
            is_completed INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (platform_id) REFERENCES platforms(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (platform_id) REFERENCES platforms(id) ON DELETE SET NULL
        );
    """)
    conn.commit()
    conn.close()


# --- Platform CRUD ---

def get_all_platforms():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM platforms ORDER BY priority_order, name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_platform(platform_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM platforms WHERE id = ?", (platform_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_platform_by_slug(slug):
    conn = get_db()
    row = conn.execute("SELECT * FROM platforms WHERE slug = ?", (slug,)).fetchone()
    conn.close()
    return dict(row) if row else None


def upsert_platform(name, slug, **kwargs):
    conn = get_db()
    existing = conn.execute("SELECT id FROM platforms WHERE slug = ?", (slug,)).fetchone()
    if existing:
        sets = ", ".join(f"{k} = ?" for k in kwargs)
        if sets:
            conn.execute(
                f"UPDATE platforms SET {sets}, updated_at = datetime('now') WHERE slug = ?",
                (*kwargs.values(), slug)
            )
    else:
        cols = "name, slug" + (", " + ", ".join(kwargs.keys()) if kwargs else "")
        placeholders = "?, ?" + (", " + ", ".join("?" for _ in kwargs) if kwargs else "")
        conn.execute(
            f"INSERT INTO platforms ({cols}) VALUES ({placeholders})",
            (name, slug, *kwargs.values())
        )
    conn.commit()
    row = conn.execute("SELECT * FROM platforms WHERE slug = ?", (slug,)).fetchone()
    conn.close()
    return dict(row)


def update_platform(platform_id, **kwargs):
    conn = get_db()
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    conn.execute(
        f"UPDATE platforms SET {sets}, updated_at = datetime('now') WHERE id = ?",
        (*kwargs.values(), platform_id)
    )
    conn.commit()
    conn.close()


# --- Application Steps ---

def get_steps(platform_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM application_steps WHERE platform_id = ? ORDER BY step_number",
        (platform_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def complete_step(step_id):
    conn = get_db()
    conn.execute(
        "UPDATE application_steps SET is_completed = 1, completed_at = datetime('now') WHERE id = ?",
        (step_id,)
    )
    conn.commit()
    conn.close()


def uncomplete_step(step_id):
    conn = get_db()
    conn.execute(
        "UPDATE application_steps SET is_completed = 0, completed_at = NULL WHERE id = ?",
        (step_id,)
    )
    conn.commit()
    conn.close()


def add_step(platform_id, step_number, title, description="", step_type="manual"):
    conn = get_db()
    conn.execute(
        "INSERT INTO application_steps (platform_id, step_number, title, description, step_type) VALUES (?, ?, ?, ?, ?)",
        (platform_id, step_number, title, description, step_type)
    )
    conn.commit()
    conn.close()


def bulk_insert_steps(platform_id, steps):
    """Insert multiple steps at once. steps = list of (step_number, title, description, step_type)"""
    conn = get_db()
    # Clear existing steps first
    conn.execute("DELETE FROM application_steps WHERE platform_id = ?", (platform_id,))
    conn.executemany(
        "INSERT INTO application_steps (platform_id, step_number, title, description, step_type) VALUES (?, ?, ?, ?, ?)",
        [(platform_id, *s) for s in steps]
    )
    conn.commit()
    conn.close()


# --- API Keys ---

def get_keys(platform_id=None):
    conn = get_db()
    if platform_id:
        rows = conn.execute(
            "SELECT k.*, p.name as platform_name, p.slug as platform_slug FROM api_keys k JOIN platforms p ON k.platform_id = p.id WHERE k.platform_id = ? ORDER BY k.key_name",
            (platform_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT k.*, p.name as platform_name, p.slug as platform_slug FROM api_keys k JOIN platforms p ON k.platform_id = p.id ORDER BY p.name, k.key_name"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_key(platform_id, key_name, key_type="api_key", env_var_name="", rotation_days=90, notes="", expires_at=None):
    conn = get_db()
    now = datetime.now().isoformat()
    if not expires_at and rotation_days:
        expires_at = (datetime.now() + timedelta(days=rotation_days)).isoformat()
    conn.execute(
        """INSERT INTO api_keys (platform_id, key_name, key_type, env_var_name, issued_at, expires_at, rotation_days, last_rotated, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (platform_id, key_name, key_type, env_var_name, now, expires_at, rotation_days, now, notes)
    )
    conn.commit()
    conn.close()


def update_key(key_id, **kwargs):
    conn = get_db()
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    conn.execute(f"UPDATE api_keys SET {sets} WHERE id = ?", (*kwargs.values(), key_id))
    conn.commit()
    conn.close()


def rotate_key(key_id):
    conn = get_db()
    key = conn.execute("SELECT * FROM api_keys WHERE id = ?", (key_id,)).fetchone()
    if key:
        now = datetime.now().isoformat()
        new_expires = (datetime.now() + timedelta(days=key["rotation_days"])).isoformat()
        conn.execute(
            "UPDATE api_keys SET last_rotated = ?, expires_at = ?, issued_at = ? WHERE id = ?",
            (now, new_expires, now, key_id)
        )
        conn.commit()
    conn.close()


def delete_key(key_id):
    conn = get_db()
    conn.execute("DELETE FROM api_keys WHERE id = ?", (key_id,))
    conn.commit()
    conn.close()


# --- Reminders ---

def get_reminders(platform_id=None, include_completed=False):
    conn = get_db()
    query = "SELECT r.*, p.name as platform_name FROM reminders r JOIN platforms p ON r.platform_id = p.id"
    conditions = []
    params = []
    if platform_id:
        conditions.append("r.platform_id = ?")
        params.append(platform_id)
    if not include_completed:
        conditions.append("r.is_completed = 0")
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY r.due_date"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_reminder(platform_id, reminder_type, title, description, due_date, calendar_event_id=None):
    conn = get_db()
    conn.execute(
        "INSERT INTO reminders (platform_id, reminder_type, title, description, due_date, calendar_event_id) VALUES (?, ?, ?, ?, ?, ?)",
        (platform_id, reminder_type, title, description, due_date, calendar_event_id)
    )
    conn.commit()
    conn.close()


def complete_reminder(reminder_id):
    conn = get_db()
    conn.execute("UPDATE reminders SET is_completed = 1 WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()


# --- Activity Log ---

def log_activity(platform_id, action, details=""):
    conn = get_db()
    conn.execute(
        "INSERT INTO activity_log (platform_id, action, details) VALUES (?, ?, ?)",
        (platform_id, action, details)
    )
    conn.commit()
    conn.close()


def get_activity_log(platform_id=None, limit=50):
    conn = get_db()
    if platform_id:
        rows = conn.execute(
            "SELECT a.*, p.name as platform_name FROM activity_log a LEFT JOIN platforms p ON a.platform_id = p.id WHERE a.platform_id = ? ORDER BY a.created_at DESC LIMIT ?",
            (platform_id, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT a.*, p.name as platform_name FROM activity_log a LEFT JOIN platforms p ON a.platform_id = p.id ORDER BY a.created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Dashboard Stats ---

def get_dashboard_stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM platforms").fetchone()[0]
    approved = conn.execute("SELECT COUNT(*) FROM platforms WHERE status = 'approved'").fetchone()[0]
    in_progress = conn.execute("SELECT COUNT(*) FROM platforms WHERE status = 'in_progress'").fetchone()[0]

    # Keys expiring within 30 days
    expiring_soon = conn.execute(
        "SELECT COUNT(*) FROM api_keys WHERE is_active = 1 AND expires_at <= datetime('now', '+30 days')"
    ).fetchone()[0]

    # Pending reminders
    pending_reminders = conn.execute(
        "SELECT COUNT(*) FROM reminders WHERE is_completed = 0 AND due_date <= datetime('now', '+7 days')"
    ).fetchone()[0]

    conn.close()
    return {
        "total_platforms": total,
        "approved": approved,
        "in_progress": in_progress,
        "not_started": total - approved - in_progress,
        "expiring_keys": expiring_soon,
        "pending_reminders": pending_reminders,
    }
