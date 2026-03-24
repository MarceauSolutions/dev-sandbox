"""
signing-portal/models.py — SQLite models for the client signing portal.

Table: agreements
  token          TEXT PRIMARY KEY  — UUID, used in signing URL
  business_name  TEXT              — Client's business name
  client_name    TEXT              — Client's full name
  client_email   TEXT              — Client's email address
  tier           INTEGER           — 1-4
  monthly_rate   TEXT              — e.g. "$497/month"
  effective_date TEXT              — ISO date string
  status         TEXT              — pending / signed / expired
  signer_name    TEXT              — Typed name on submit
  signer_ip      TEXT              — IP at time of signing
  signed_at      TEXT              — ISO datetime when signed
  created_at     TEXT              — ISO datetime when created
"""

import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "signing_portal.db"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agreements (
            token          TEXT PRIMARY KEY,
            business_name  TEXT NOT NULL,
            client_name    TEXT NOT NULL,
            client_email   TEXT NOT NULL,
            tier           INTEGER NOT NULL DEFAULT 1,
            monthly_rate   TEXT NOT NULL DEFAULT '$497/month',
            effective_date TEXT NOT NULL,
            status         TEXT NOT NULL DEFAULT 'pending',
            signer_name    TEXT,
            signer_ip      TEXT,
            signed_at      TEXT,
            created_at     TEXT NOT NULL
        )
    """)
    conn.commit()


def create_agreement(
    conn: sqlite3.Connection,
    token: str,
    business_name: str,
    client_name: str,
    client_email: str,
    tier: int = 1,
    monthly_rate: str = "$497/month",
    effective_date: str = "",
) -> str:
    """Insert a new pending agreement. Returns the token."""
    if not effective_date:
        effective_date = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().isoformat()
    conn.execute(
        """
        INSERT INTO agreements
            (token, business_name, client_name, client_email, tier, monthly_rate,
             effective_date, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        """,
        (token, business_name, client_name, client_email, tier, monthly_rate,
         effective_date, now),
    )
    conn.commit()
    return token


def get_agreement(conn: sqlite3.Connection, token: str):
    """Return the agreement row for the given token, or None."""
    return conn.execute(
        "SELECT * FROM agreements WHERE token = ?", (token,)
    ).fetchone()


def mark_signed(
    conn: sqlite3.Connection,
    token: str,
    signer_name: str,
    signer_ip: str,
):
    """Mark an agreement as signed and record signer details."""
    now = datetime.now().isoformat()
    conn.execute(
        """
        UPDATE agreements
           SET status = 'signed',
               signer_name = ?,
               signer_ip = ?,
               signed_at = ?
         WHERE token = ?
        """,
        (signer_name, signer_ip, now, token),
    )
    conn.commit()
