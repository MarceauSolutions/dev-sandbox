"""
KeyVault SaaS — Database models and operations.

Multi-tenant API key management platform with encryption, auth, and billing.
"""

import sqlite3
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import bcrypt
import jwt
from cryptography.fernet import Fernet

DB_PATH = Path(__file__).parent.parent / "data" / "keyvault.db"

# JWT config — persisted to file so tokens survive restarts
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 72

_JWT_SECRET_PATH = Path(__file__).parent.parent / "data" / ".jwt_secret"


def _get_jwt_secret() -> str:
    _JWT_SECRET_PATH.parent.mkdir(parents=True, exist_ok=True)
    if _JWT_SECRET_PATH.exists():
        return _JWT_SECRET_PATH.read_text().strip()
    secret = secrets.token_hex(32)
    _JWT_SECRET_PATH.write_text(secret)
    os.chmod(str(_JWT_SECRET_PATH), 0o600)
    return secret


JWT_SECRET = os.getenv("KEYVAULT_JWT_SECRET") or _get_jwt_secret()

# Encryption key for stored key values — MUST be persisted
_ENCRYPTION_KEY_PATH = Path(__file__).parent.parent / "data" / ".encryption_key"


def _get_encryption_key() -> bytes:
    _ENCRYPTION_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if _ENCRYPTION_KEY_PATH.exists():
        return _ENCRYPTION_KEY_PATH.read_bytes()
    key = Fernet.generate_key()
    _ENCRYPTION_KEY_PATH.write_bytes(key)
    os.chmod(str(_ENCRYPTION_KEY_PATH), 0o600)
    return key


_fernet = Fernet(_get_encryption_key())


def encrypt_value(plaintext: str) -> str:
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    return _fernet.decrypt(ciphertext.encode()).decode()


def mask_value(plaintext: str) -> str:
    if len(plaintext) <= 8:
        return "••••••••"
    return plaintext[:4] + "•" * (len(plaintext) - 8) + plaintext[-4:]


# ─── Database ────────────────────────────────────────────────

def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _create_tables(conn)
    return conn


def _create_tables(conn: sqlite3.Connection):
    conn.executescript("""
        -- Organizations (tenants)
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            plan TEXT DEFAULT 'free' CHECK(plan IN ('free', 'pro', 'enterprise')),
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT,
            max_keys INTEGER DEFAULT 25,
            max_environments INTEGER DEFAULT 2,
            max_members INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        -- Users
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            org_id INTEGER REFERENCES organizations(id),
            role TEXT DEFAULT 'member' CHECK(role IN ('owner', 'admin', 'member', 'viewer')),
            is_active INTEGER DEFAULT 1,
            last_login_at TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        -- API tokens for programmatic access
        CREATE TABLE IF NOT EXISTS api_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            org_id INTEGER NOT NULL REFERENCES organizations(id),
            name TEXT NOT NULL,
            token_hash TEXT UNIQUE NOT NULL,
            token_prefix TEXT NOT NULL,
            scopes TEXT DEFAULT 'read',
            last_used_at TEXT,
            expires_at TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now'))
        );

        -- Services (per org)
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER NOT NULL REFERENCES organizations(id),
            name TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'other',
            website_url TEXT,
            dashboard_url TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(org_id, name)
        );

        -- API keys (per org, linked to service)
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER NOT NULL REFERENCES organizations(id),
            service_id INTEGER NOT NULL REFERENCES services(id),
            label TEXT NOT NULL,
            env_var_name TEXT NOT NULL,
            encrypted_value TEXT,
            key_type TEXT NOT NULL DEFAULT 'api_key',
            auth_protocol TEXT DEFAULT 'api_key',
            expires_at TEXT,
            renew_by TEXT,
            auto_renews INTEGER DEFAULT 0,
            renewal_url TEXT,
            renewal_notes TEXT,
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'expired', 'revoked', 'retired', 'empty', 'warning')),
            last_verified_at TEXT,
            last_verified_ok INTEGER,
            monthly_cost REAL DEFAULT 0,
            tier TEXT,
            rate_limit TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(org_id, env_var_name)
        );

        -- Environments (per org)
        CREATE TABLE IF NOT EXISTS environments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER NOT NULL REFERENCES organizations(id),
            name TEXT NOT NULL,
            env_file_path TEXT,
            ssh_command TEXT,
            last_synced_at TEXT,
            notes TEXT,
            UNIQUE(org_id, name)
        );

        -- Key-to-environment sync status
        CREATE TABLE IF NOT EXISTS env_sync_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key_id INTEGER NOT NULL REFERENCES api_keys(id),
            environment_id INTEGER NOT NULL REFERENCES environments(id),
            in_sync INTEGER DEFAULT 0,
            last_checked_at TEXT,
            notes TEXT,
            UNIQUE(api_key_id, environment_id)
        );

        -- Consumers (what uses each key)
        CREATE TABLE IF NOT EXISTS key_consumers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key_id INTEGER NOT NULL REFERENCES api_keys(id),
            consumer_type TEXT NOT NULL CHECK(consumer_type IN ('script', 'workflow', 'bot', 'agent', 'mcp', 'client_system', 'webhook', 'other')),
            consumer_name TEXT NOT NULL,
            consumer_path TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        -- Deprecation notices
        CREATE TABLE IF NOT EXISTS deprecation_notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER NOT NULL REFERENCES organizations(id),
            service_id INTEGER NOT NULL REFERENCES services(id),
            notice_date TEXT NOT NULL,
            effective_date TEXT,
            description TEXT NOT NULL,
            migration_notes TEXT,
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'resolved', 'ignored')),
            resolved_at TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        -- Reminders
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER NOT NULL REFERENCES organizations(id),
            api_key_id INTEGER REFERENCES api_keys(id),
            service_id INTEGER REFERENCES services(id),
            reminder_type TEXT NOT NULL CHECK(reminder_type IN ('expiration', 'renewal', 'deprecation', 'cost_review', 'health_check', 'custom')),
            remind_at TEXT NOT NULL,
            message TEXT NOT NULL,
            sent INTEGER DEFAULT 0,
            sent_at TEXT,
            channel TEXT DEFAULT 'email' CHECK(channel IN ('sms', 'email', 'telegram', 'webhook', 'dashboard')),
            created_at TEXT DEFAULT (datetime('now'))
        );

        -- Audit log
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER NOT NULL REFERENCES organizations(id),
            user_id INTEGER,
            entity_type TEXT NOT NULL,
            entity_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        -- Health check results
        CREATE TABLE IF NOT EXISTS health_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key_id INTEGER NOT NULL REFERENCES api_keys(id),
            check_type TEXT NOT NULL,
            is_healthy INTEGER NOT NULL,
            response_ms INTEGER,
            error_message TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        -- Notification preferences
        CREATE TABLE IF NOT EXISTS notification_prefs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER NOT NULL REFERENCES organizations(id),
            channel TEXT NOT NULL CHECK(channel IN ('email', 'sms', 'telegram', 'webhook')),
            destination TEXT NOT NULL,
            notify_on_expiry INTEGER DEFAULT 1,
            notify_on_health_fail INTEGER DEFAULT 1,
            notify_on_deprecation INTEGER DEFAULT 1,
            notify_on_sync_drift INTEGER DEFAULT 1,
            expiry_warn_days INTEGER DEFAULT 14,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(org_id, channel, destination)
        );
    """)
    conn.commit()


# ─── Auth helpers ────────────────────────────────────────────

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_jwt(user_id: int, org_id: int, role: str, email: str) -> str:
    payload = {
        "user_id": user_id,
        "org_id": org_id,
        "role": role,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def generate_api_token() -> tuple[str, str, str]:
    """Returns (full_token, token_hash, prefix) for API token auth."""
    token = f"kv_{secrets.token_urlsafe(32)}"
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    prefix = token[:10]
    return token, token_hash, prefix


# ─── Org + User CRUD ────────────────────────────────────────

def create_org(conn, name: str, slug: str, plan: str = "free") -> int:
    cur = conn.execute(
        "INSERT INTO organizations (name, slug, plan) VALUES (?, ?, ?)",
        (name, slug, plan)
    )
    conn.commit()
    return cur.lastrowid


def create_user(conn, email: str, password: str, name: str, org_id: int, role: str = "owner") -> int:
    cur = conn.execute(
        "INSERT INTO users (email, password_hash, name, org_id, role) VALUES (?, ?, ?, ?, ?)",
        (email, hash_password(password), name, org_id, role)
    )
    conn.commit()
    return cur.lastrowid


def authenticate_user(conn, email: str, password: str) -> Optional[dict]:
    user = conn.execute("SELECT * FROM users WHERE email = ? AND is_active = 1", (email,)).fetchone()
    if user and verify_password(password, user["password_hash"]):
        conn.execute("UPDATE users SET last_login_at = datetime('now') WHERE id = ?", (user["id"],))
        conn.commit()
        return dict(user)
    return None


# ─── Service + Key CRUD ─────────────────────────────────────

def upsert_service(conn, org_id: int, name: str, category: str = "other", **kwargs) -> int:
    existing = conn.execute("SELECT id FROM services WHERE org_id = ? AND name = ?", (org_id, name)).fetchone()
    if existing:
        fields = ", ".join(f"{k} = ?" for k in kwargs)
        if fields:
            conn.execute(
                f"UPDATE services SET category = ?, {fields}, updated_at = datetime('now') WHERE id = ?",
                (category, *kwargs.values(), existing["id"])
            )
        conn.commit()
        return existing["id"]
    cols = ["org_id", "name", "category"] + list(kwargs.keys())
    placeholders = ", ".join(["?"] * len(cols))
    cur = conn.execute(
        f"INSERT INTO services ({', '.join(cols)}) VALUES ({placeholders})",
        (org_id, name, category, *kwargs.values())
    )
    conn.commit()
    return cur.lastrowid


def upsert_api_key(conn, org_id: int, service_id: int, env_var_name: str, label: str = None, value: str = None, **kwargs) -> int:
    if not label:
        label = env_var_name
    existing = conn.execute(
        "SELECT id FROM api_keys WHERE org_id = ? AND env_var_name = ?",
        (org_id, env_var_name)
    ).fetchone()

    encrypted = encrypt_value(value) if value else None

    if existing:
        updates = {**kwargs}
        if encrypted:
            updates["encrypted_value"] = encrypted
        if updates:
            fields = ", ".join(f"{k} = ?" for k in updates)
            conn.execute(
                f"UPDATE api_keys SET {fields}, updated_at = datetime('now') WHERE id = ?",
                (*updates.values(), existing["id"])
            )
        conn.commit()
        return existing["id"]

    cols = ["org_id", "service_id", "env_var_name", "label"] + list(kwargs.keys())
    vals = [org_id, service_id, env_var_name, label] + list(kwargs.values())
    if encrypted:
        cols.append("encrypted_value")
        vals.append(encrypted)
    placeholders = ", ".join(["?"] * len(cols))
    cur = conn.execute(
        f"INSERT INTO api_keys ({', '.join(cols)}) VALUES ({placeholders})", vals
    )
    conn.commit()
    return cur.lastrowid


def add_consumer(conn, api_key_id: int, consumer_type: str, consumer_name: str, consumer_path: str = None, notes: str = None):
    existing = conn.execute(
        "SELECT id FROM key_consumers WHERE api_key_id = ? AND consumer_type = ? AND consumer_name = ?",
        (api_key_id, consumer_type, consumer_name)
    ).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO key_consumers (api_key_id, consumer_type, consumer_name, consumer_path, notes) VALUES (?, ?, ?, ?, ?)",
            (api_key_id, consumer_type, consumer_name, consumer_path, notes)
        )
        conn.commit()


def add_deprecation_notice(conn, org_id: int, service_id: int, description: str, notice_date: str = None, effective_date: str = None, migration_notes: str = None):
    conn.execute(
        "INSERT INTO deprecation_notices (org_id, service_id, notice_date, effective_date, description, migration_notes) VALUES (?, ?, ?, ?, ?, ?)",
        (org_id, service_id, notice_date or datetime.now().strftime("%Y-%m-%d"), effective_date, description, migration_notes)
    )
    conn.commit()


def add_reminder(conn, org_id: int, message: str, remind_at: str, reminder_type: str = "custom", api_key_id: int = None, service_id: int = None, channel: str = "email"):
    conn.execute(
        "INSERT INTO reminders (org_id, api_key_id, service_id, reminder_type, remind_at, message, channel) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (org_id, api_key_id, service_id, reminder_type, remind_at, message, channel)
    )
    conn.commit()


def log_audit(conn, org_id: int, action: str, entity_type: str = "", entity_id: int = None, details: str = None, user_id: int = None, ip: str = None):
    conn.execute(
        "INSERT INTO audit_log (org_id, user_id, entity_type, entity_id, action, details, ip_address) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (org_id, user_id, entity_type, entity_id, action, details, ip)
    )
    conn.commit()


# ─── Query helpers ───────────────────────────────────────────

def get_expiring_keys(conn, org_id: int, within_days: int = 30) -> list:
    return conn.execute("""
        SELECT ak.*, s.name as service_name, s.category
        FROM api_keys ak JOIN services s ON ak.service_id = s.id
        WHERE ak.org_id = ? AND ak.expires_at IS NOT NULL AND ak.status = 'active'
        AND date(ak.expires_at) <= date('now', ? || ' days')
        ORDER BY ak.expires_at ASC
    """, (org_id, str(within_days))).fetchall()


def get_all_keys_with_details(conn, org_id: int) -> list:
    return conn.execute("""
        SELECT ak.*, s.name as service_name, s.category, s.dashboard_url,
            (SELECT COUNT(*) FROM key_consumers kc WHERE kc.api_key_id = ak.id) as consumer_count,
            (SELECT GROUP_CONCAT(kc.consumer_name, ', ') FROM key_consumers kc WHERE kc.api_key_id = ak.id) as consumers
        FROM api_keys ak JOIN services s ON ak.service_id = s.id
        WHERE ak.org_id = ?
        ORDER BY s.category, s.name, ak.env_var_name
    """, (org_id,)).fetchall()


def get_dashboard_summary(conn, org_id: int) -> dict:
    def _count(query, params=()):
        return conn.execute(query, params).fetchone()[0]

    total = _count("SELECT COUNT(*) FROM api_keys WHERE org_id = ? AND status = 'active'", (org_id,))
    expiring = len(get_expiring_keys(conn, org_id, 30))
    expired = _count("SELECT COUNT(*) FROM api_keys WHERE org_id = ? AND status = 'expired'", (org_id,))
    retired = _count("SELECT COUNT(*) FROM api_keys WHERE org_id = ? AND status = 'retired'", (org_id,))
    empty = _count("SELECT COUNT(*) FROM api_keys WHERE org_id = ? AND status = 'empty'", (org_id,))
    deprecations = _count("""SELECT COUNT(*) FROM deprecation_notices WHERE org_id = ? AND status = 'active'""", (org_id,))
    monthly_cost = conn.execute("SELECT COALESCE(SUM(monthly_cost), 0) FROM api_keys WHERE org_id = ? AND status = 'active'", (org_id,)).fetchone()[0]
    services = _count("SELECT COUNT(*) FROM services WHERE org_id = ?", (org_id,))
    consumers = _count("SELECT COUNT(DISTINCT kc.consumer_name) FROM key_consumers kc JOIN api_keys ak ON kc.api_key_id = ak.id WHERE ak.org_id = ?", (org_id,))
    out_of_sync = _count("""SELECT COUNT(*) FROM env_sync_status ess JOIN api_keys ak ON ess.api_key_id = ak.id WHERE ak.org_id = ? AND ess.in_sync = 0""", (org_id,))
    healthy = _count("SELECT COUNT(*) FROM api_keys WHERE org_id = ? AND last_verified_ok = 1", (org_id,))
    unhealthy = _count("SELECT COUNT(*) FROM api_keys WHERE org_id = ? AND last_verified_ok = 0", (org_id,))

    return {
        "total_active_keys": total,
        "expiring_within_30d": expiring,
        "expired_keys": expired,
        "retired_keys": retired,
        "empty_keys": empty,
        "active_deprecations": deprecations,
        "monthly_cost": monthly_cost,
        "total_services": services,
        "total_consumers": consumers,
        "out_of_sync_envs": out_of_sync,
        "healthy_keys": healthy,
        "unhealthy_keys": unhealthy,
    }


def get_sync_status(conn, org_id: int) -> list:
    return conn.execute("""
        SELECT ess.*, ak.env_var_name, s.name as service_name, e.name as env_name
        FROM env_sync_status ess
        JOIN api_keys ak ON ess.api_key_id = ak.id
        JOIN services s ON ak.service_id = s.id
        JOIN environments e ON ess.environment_id = e.id
        WHERE ak.org_id = ?
        ORDER BY ess.in_sync ASC, s.name
    """, (org_id,)).fetchall()


def get_active_deprecations(conn, org_id: int) -> list:
    return conn.execute("""
        SELECT dn.*, s.name as service_name
        FROM deprecation_notices dn JOIN services s ON dn.service_id = s.id
        WHERE dn.org_id = ? AND dn.status = 'active'
        ORDER BY dn.effective_date ASC
    """, (org_id,)).fetchall()


def get_recent_audit_log(conn, org_id: int, limit: int = 50) -> list:
    return conn.execute("""
        SELECT al.*, u.name as user_name, u.email as user_email
        FROM audit_log al LEFT JOIN users u ON al.user_id = u.id
        WHERE al.org_id = ?
        ORDER BY al.created_at DESC LIMIT ?
    """, (org_id, limit)).fetchall()


def get_health_history(conn, api_key_id: int, limit: int = 20) -> list:
    return conn.execute("""
        SELECT * FROM health_checks WHERE api_key_id = ? ORDER BY created_at DESC LIMIT ?
    """, (api_key_id, limit)).fetchall()


def get_plan_limits(conn, org_id: int) -> dict:
    org = conn.execute("SELECT * FROM organizations WHERE id = ?", (org_id,)).fetchone()
    if not org:
        return {"max_keys": 25, "max_environments": 2, "max_members": 1, "plan": "free"}
    current_keys = conn.execute("SELECT COUNT(*) FROM api_keys WHERE org_id = ?", (org_id,)).fetchone()[0]
    current_envs = conn.execute("SELECT COUNT(*) FROM environments WHERE org_id = ?", (org_id,)).fetchone()[0]
    current_members = conn.execute("SELECT COUNT(*) FROM users WHERE org_id = ?", (org_id,)).fetchone()[0]
    return {
        "plan": org["plan"],
        "max_keys": org["max_keys"],
        "max_environments": org["max_environments"],
        "max_members": org["max_members"],
        "current_keys": current_keys,
        "current_envs": current_envs,
        "current_members": current_members,
    }
