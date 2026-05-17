"""
SQLite persistence for the AI phone agent.

Replaces in-process dicts and JSON files so state survives:
  - gunicorn worker recycles
  - EC2 reboots
  - systemd restarts
  - concurrent calls hitting different workers

Tables
------
active_calls    in-flight call state, keyed by Twilio CallSid
leads           completed-call lead records (formerly leads.json)
cell_reliability transfer attempt history (formerly cell_reliability.json)
tenants         per-client config for multi-tenancy (keyed by Twilio number)

The CallStore class exposes a dict-like API so the existing app.py call
sites (active_calls[call_sid] = {...}, .get, .pop) work unchanged.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

DB_PATH = Path(os.environ.get(
    "PHONE_AGENT_DB",
    str(Path(__file__).parent.parent / "data" / "phone_agent.db"),
))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

_lock = threading.Lock()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=10.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Create tables if they don't exist. Safe to call repeatedly."""
    with _lock, _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS active_calls (
                call_sid          TEXT PRIMARY KEY,
                conversation_id   TEXT,
                caller            TEXT,
                tenant_id         TEXT,
                started_at        TEXT NOT NULL,
                status            TEXT,
                origin            TEXT,
                transcript        TEXT,
                collected_data    TEXT,
                transfer_reason   TEXT,
                caller_name       TEXT,
                urgency           TEXT,
                updated_at        TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_active_calls_conv
                ON active_calls(conversation_id);

            CREATE TABLE IF NOT EXISTS leads (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id       TEXT,
                phone           TEXT,
                name            TEXT,
                email           TEXT,
                source          TEXT,
                status          TEXT,
                business_type   TEXT,
                pain_points     TEXT,
                timeline        TEXT,
                notes           TEXT,
                call_sid        TEXT,
                conversation_id TEXT,
                recording_url   TEXT,
                transcript      TEXT,
                collected_data  TEXT,
                created_at      TEXT NOT NULL,
                updated_at      TEXT NOT NULL,
                follow_up_at    TEXT,
                contacted       INTEGER DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_leads_call_sid
                ON leads(call_sid);
            CREATE INDEX IF NOT EXISTS idx_leads_conv
                ON leads(conversation_id);

            CREATE TABLE IF NOT EXISTS cell_reliability (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id   TEXT,
                timestamp   TEXT NOT NULL,
                call_sid    TEXT,
                caller      TEXT,
                answered    INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tenants (
                tenant_id              TEXT PRIMARY KEY,
                twilio_number          TEXT UNIQUE NOT NULL,
                business_name          TEXT,
                persona_name           TEXT,
                telegram_chat_id       TEXT,
                elevenlabs_agent_id    TEXT,
                transfer_target_cell   TEXT,
                config                 TEXT,
                active                 INTEGER DEFAULT 1,
                created_at             TEXT NOT NULL
            );
            """
        )


# =============================================================================
# Active calls — dict-like wrapper so app.py call sites are unchanged
# =============================================================================

def _now() -> str:
    return datetime.now().isoformat()


def _row_to_call(row: sqlite3.Row) -> dict[str, Any]:
    """Hydrate a sqlite row into the dict shape app.py expects."""
    if row is None:
        return {}
    d = dict(row)
    for json_field in ("origin", "transcript", "collected_data"):
        if d.get(json_field):
            try:
                d[json_field] = json.loads(d[json_field])
            except (json.JSONDecodeError, TypeError):
                d[json_field] = [] if json_field == "transcript" else {}
        else:
            d[json_field] = [] if json_field == "transcript" else {}
    return d


_CALL_COLUMNS = {
    "call_sid", "conversation_id", "caller", "tenant_id",
    "started_at", "status", "origin", "transcript", "collected_data",
    "transfer_reason", "caller_name", "urgency",
}
_JSON_COLUMNS = {"origin", "transcript", "collected_data"}


class CallStore:
    """SQLite-backed replacement for the old `active_calls = {}` dict."""

    def __init__(self) -> None:
        init_db()

    def _serialize(self, value: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for k, v in value.items():
            if k not in _CALL_COLUMNS:
                continue
            if k in _JSON_COLUMNS:
                out[k] = json.dumps(v) if v is not None else None
            else:
                out[k] = v
        return out

    def __setitem__(self, call_sid: str, data: dict[str, Any]) -> None:
        """Insert-or-replace a call row. Matches `active_calls[sid] = {...}`."""
        merged = dict(data)
        merged["call_sid"] = call_sid
        merged.setdefault("started_at", _now())
        merged["updated_at"] = _now()
        cols = self._serialize(merged)
        cols["updated_at"] = merged["updated_at"]
        keys = ", ".join(cols.keys())
        placeholders = ", ".join(f":{k}" for k in cols.keys())
        with _lock, _connect() as conn:
            conn.execute(
                f"INSERT OR REPLACE INTO active_calls ({keys}) VALUES ({placeholders})",
                cols,
            )

    def __getitem__(self, call_sid: str) -> dict[str, Any]:
        row = self._fetch(call_sid)
        if not row:
            raise KeyError(call_sid)
        return row

    def __contains__(self, call_sid: str) -> bool:
        return bool(self._fetch(call_sid))

    def get(self, call_sid: str, default: Any = None) -> Any:
        row = self._fetch(call_sid)
        return row if row else (default if default is not None else {})

    def pop(self, call_sid: str, default: Any = None) -> Any:
        row = self._fetch(call_sid)
        with _lock, _connect() as conn:
            conn.execute("DELETE FROM active_calls WHERE call_sid=?", (call_sid,))
        return row if row else default

    def update_fields(self, call_sid: str, **fields: Any) -> None:
        """Patch specific fields on an existing call. Use instead of mutating the dict in place."""
        if not fields:
            return
        cols = self._serialize(fields)
        cols["updated_at"] = _now()
        sets = ", ".join(f"{k}=:{k}" for k in cols.keys())
        cols["call_sid"] = call_sid
        with _lock, _connect() as conn:
            conn.execute(
                f"UPDATE active_calls SET {sets} WHERE call_sid=:call_sid",
                cols,
            )

    def _fetch(self, call_sid: str) -> dict[str, Any]:
        with _lock, _connect() as conn:
            cur = conn.execute(
                "SELECT * FROM active_calls WHERE call_sid=?",
                (call_sid,),
            )
            row = cur.fetchone()
        return _row_to_call(row)


# =============================================================================
# Leads (replaces dashboard's leads.json)
# =============================================================================

def list_leads(status: Optional[str] = None, source: Optional[str] = None) -> list[dict[str, Any]]:
    sql = "SELECT * FROM leads WHERE 1=1"
    params: list[Any] = []
    if status:
        sql += " AND status=?"
        params.append(status)
    if source:
        sql += " AND source=?"
        params.append(source)
    sql += " ORDER BY created_at DESC"
    with _lock, _connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_lead_row_to_dict(r) for r in rows]


def _lead_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    for json_field in ("transcript", "collected_data"):
        if d.get(json_field):
            try:
                d[json_field] = json.loads(d[json_field])
            except (json.JSONDecodeError, TypeError):
                d[json_field] = [] if json_field == "transcript" else {}
        else:
            d[json_field] = [] if json_field == "transcript" else {}
    d["contacted"] = bool(d.get("contacted", 0))
    return d


def insert_lead(data: dict[str, Any]) -> dict[str, Any]:
    """Insert a new lead from a webhook payload. Returns the inserted row."""
    collected = data.get("collected_data") or {}
    now = _now()
    row = {
        "tenant_id": data.get("tenant_id"),
        "phone": data.get("phone", "Unknown"),
        "name": data.get("name", ""),
        "email": data.get("email", ""),
        "source": data.get("source", "unknown"),
        "status": data.get("status", "new"),
        "business_type": collected.get("business_type", ""),
        "pain_points": collected.get("pain_points", ""),
        "timeline": collected.get("timeline", ""),
        "notes": data.get("notes", ""),
        "call_sid": data.get("call_sid", ""),
        "conversation_id": data.get("conversation_id", ""),
        "recording_url": data.get("recording_url", ""),
        "transcript": json.dumps(data.get("transcript", [])),
        "collected_data": json.dumps(collected),
        "created_at": now,
        "updated_at": now,
        "follow_up_at": None,
        "contacted": 0,
    }
    keys = ", ".join(row.keys())
    placeholders = ", ".join(f":{k}" for k in row.keys())
    with _lock, _connect() as conn:
        cur = conn.execute(
            f"INSERT INTO leads ({keys}) VALUES ({placeholders})",
            row,
        )
        lead_id = cur.lastrowid
    return get_lead(lead_id)


def upsert_lead_by_conversation(conversation_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """
    Used by the ElevenLabs poller: PATCH an existing lead by conversation_id,
    or INSERT one if the call_sid path didn't already create it.
    """
    existing = find_lead_by_conversation(conversation_id)
    if existing:
        update_lead(existing["id"], data | {"conversation_id": conversation_id})
        return get_lead(existing["id"])

    # No existing row — also try call_sid match (Flask side might have inserted
    # before the poller knew the conversation_id).
    call_sid = data.get("call_sid")
    if call_sid:
        with _lock, _connect() as conn:
            row = conn.execute(
                "SELECT id FROM leads WHERE call_sid=? ORDER BY id DESC LIMIT 1",
                (call_sid,),
            ).fetchone()
        if row:
            update_lead(row["id"], data | {"conversation_id": conversation_id})
            return get_lead(row["id"])

    return insert_lead(data | {"conversation_id": conversation_id})


def find_lead_by_conversation(conversation_id: str) -> Optional[dict[str, Any]]:
    with _lock, _connect() as conn:
        row = conn.execute(
            "SELECT * FROM leads WHERE conversation_id=? ORDER BY id DESC LIMIT 1",
            (conversation_id,),
        ).fetchone()
    return _lead_row_to_dict(row) if row else None


def get_lead(lead_id: int) -> Optional[dict[str, Any]]:
    with _lock, _connect() as conn:
        row = conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
    return _lead_row_to_dict(row) if row else None


_LEAD_UPDATABLE = {
    "phone", "name", "email", "source", "status", "business_type",
    "pain_points", "timeline", "notes", "call_sid", "conversation_id",
    "recording_url", "transcript", "collected_data", "follow_up_at", "contacted",
}


def update_lead(lead_id: int, patch: dict[str, Any]) -> Optional[dict[str, Any]]:
    cols: dict[str, Any] = {}
    for k, v in patch.items():
        if k not in _LEAD_UPDATABLE:
            continue
        if k in ("transcript", "collected_data") and not isinstance(v, str):
            cols[k] = json.dumps(v)
        elif k == "contacted":
            cols[k] = 1 if v else 0
        else:
            cols[k] = v
    if not cols:
        return get_lead(lead_id)
    cols["updated_at"] = _now()
    sets = ", ".join(f"{k}=:{k}" for k in cols.keys())
    cols["id"] = lead_id
    with _lock, _connect() as conn:
        conn.execute(f"UPDATE leads SET {sets} WHERE id=:id", cols)
    return get_lead(lead_id)


# =============================================================================
# Cell reliability (replaces cell_reliability.json)
# =============================================================================

def record_transfer(call_sid: str, caller: str, answered: bool, tenant_id: Optional[str] = None) -> None:
    with _lock, _connect() as conn:
        conn.execute(
            "INSERT INTO cell_reliability (tenant_id, timestamp, call_sid, caller, answered) "
            "VALUES (?, ?, ?, ?, ?)",
            (tenant_id, _now(), call_sid, caller, 1 if answered else 0),
        )


def recent_transfers(window: int = 10, tenant_id: Optional[str] = None) -> list[dict[str, Any]]:
    sql = "SELECT * FROM cell_reliability"
    params: list[Any] = []
    if tenant_id:
        sql += " WHERE tenant_id=?"
        params.append(tenant_id)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(window)
    with _lock, _connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in reversed(rows)]


def transfer_totals(tenant_id: Optional[str] = None) -> tuple[int, int]:
    sql = "SELECT COUNT(*) AS total, SUM(answered) AS answered FROM cell_reliability"
    params: list[Any] = []
    if tenant_id:
        sql += " WHERE tenant_id=?"
        params.append(tenant_id)
    with _lock, _connect() as conn:
        row = conn.execute(sql, params).fetchone()
    return (row["total"] or 0, row["answered"] or 0)


# =============================================================================
# Tenants (for client_setup.py and the multi-tenant path)
# =============================================================================

def upsert_tenant(tenant: dict[str, Any]) -> dict[str, Any]:
    required = {"tenant_id", "twilio_number"}
    missing = required - tenant.keys()
    if missing:
        raise ValueError(f"tenant missing required fields: {missing}")
    row = {
        "tenant_id": tenant["tenant_id"],
        "twilio_number": tenant["twilio_number"],
        "business_name": tenant.get("business_name", ""),
        "persona_name": tenant.get("persona_name", ""),
        "telegram_chat_id": tenant.get("telegram_chat_id", ""),
        "elevenlabs_agent_id": tenant.get("elevenlabs_agent_id", ""),
        "transfer_target_cell": tenant.get("transfer_target_cell", ""),
        "config": json.dumps(tenant.get("config", {})),
        "active": 1 if tenant.get("active", True) else 0,
        "created_at": _now(),
    }
    with _lock, _connect() as conn:
        conn.execute(
            """
            INSERT INTO tenants
                (tenant_id, twilio_number, business_name, persona_name,
                 telegram_chat_id, elevenlabs_agent_id, transfer_target_cell,
                 config, active, created_at)
            VALUES (:tenant_id, :twilio_number, :business_name, :persona_name,
                    :telegram_chat_id, :elevenlabs_agent_id, :transfer_target_cell,
                    :config, :active, :created_at)
            ON CONFLICT(tenant_id) DO UPDATE SET
                twilio_number=excluded.twilio_number,
                business_name=excluded.business_name,
                persona_name=excluded.persona_name,
                telegram_chat_id=excluded.telegram_chat_id,
                elevenlabs_agent_id=excluded.elevenlabs_agent_id,
                transfer_target_cell=excluded.transfer_target_cell,
                config=excluded.config,
                active=excluded.active
            """,
            row,
        )
    return get_tenant(tenant["tenant_id"])


def get_tenant(tenant_id: str) -> Optional[dict[str, Any]]:
    with _lock, _connect() as conn:
        row = conn.execute("SELECT * FROM tenants WHERE tenant_id=?", (tenant_id,)).fetchone()
    return _tenant_to_dict(row) if row else None


def tenant_for_number(twilio_number: str) -> Optional[dict[str, Any]]:
    """Look up a tenant by the dialed Twilio number. None falls back to env defaults."""
    with _lock, _connect() as conn:
        row = conn.execute(
            "SELECT * FROM tenants WHERE twilio_number=? AND active=1",
            (twilio_number,),
        ).fetchone()
    return _tenant_to_dict(row) if row else None


def list_tenants() -> list[dict[str, Any]]:
    with _lock, _connect() as conn:
        rows = conn.execute("SELECT * FROM tenants ORDER BY created_at DESC").fetchall()
    return [_tenant_to_dict(r) for r in rows]


def _tenant_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    if d.get("config"):
        try:
            d["config"] = json.loads(d["config"])
        except (json.JSONDecodeError, TypeError):
            d["config"] = {}
    else:
        d["config"] = {}
    d["active"] = bool(d.get("active", 0))
    return d


# =============================================================================
# One-shot migration from the old JSON files (idempotent — safe to re-run)
# =============================================================================

def migrate_legacy_json(data_dir: Optional[Path] = None) -> dict[str, int]:
    """
    Pull leads.json and cell_reliability.json into SQLite if they exist.
    Returns counts of records imported. Safe to run multiple times.
    """
    data_dir = data_dir or (Path(__file__).parent.parent / "data")
    counts = {"leads": 0, "cell_attempts": 0}

    leads_file = data_dir / "leads.json"
    if leads_file.exists():
        with open(leads_file) as f:
            try:
                old_leads = json.load(f)
            except json.JSONDecodeError:
                old_leads = []
        with _lock, _connect() as conn:
            existing = {
                r["call_sid"] for r in conn.execute(
                    "SELECT call_sid FROM leads WHERE call_sid IS NOT NULL AND call_sid != ''"
                )
            }
        for ld in old_leads:
            if ld.get("call_sid") and ld["call_sid"] in existing:
                continue
            insert_lead({
                "phone": ld.get("phone", "Unknown"),
                "name": ld.get("name", ""),
                "email": ld.get("email", ""),
                "source": ld.get("source", "legacy"),
                "status": ld.get("status", "new"),
                "collected_data": {
                    "business_type": ld.get("business_type", ""),
                    "pain_points": ld.get("pain_points", ""),
                    "timeline": ld.get("timeline", ""),
                },
                "notes": ld.get("notes", ""),
                "call_sid": ld.get("call_sid", ""),
                "recording_url": ld.get("recording_url", ""),
            })
            counts["leads"] += 1

    cell_file = data_dir / "cell_reliability.json"
    if cell_file.exists():
        with open(cell_file) as f:
            try:
                old = json.load(f)
            except json.JSONDecodeError:
                old = {}
        with _lock, _connect() as conn:
            existing_ts = {
                r["timestamp"] for r in conn.execute("SELECT timestamp FROM cell_reliability")
            }
        for a in (old.get("attempts") or []):
            if a.get("timestamp") in existing_ts:
                continue
            with _lock, _connect() as conn:
                conn.execute(
                    "INSERT INTO cell_reliability (timestamp, call_sid, caller, answered) "
                    "VALUES (?, ?, ?, ?)",
                    (a.get("timestamp"), a.get("call_sid"), a.get("caller"),
                     1 if a.get("answered") else 0),
                )
            counts["cell_attempts"] += 1

    return counts
