#!/usr/bin/env python3
"""
Tower Communication Protocol — Standardized inter-tower messaging via pipeline.db.

Per CLAUDE.md: towers do NOT import from each other directly.
Instead, they communicate through:
  1. pipeline.db shared tables (deals, activities, proposals, call_briefs)
  2. This protocol module (shared utility in execution/)

Usage:
    from execution.tower_protocol import request_action, check_pending, complete_action

    # Tower A requests Tower B to do something
    request_action("lead-generation", "fitness-influencer", "generate_coaching_content",
                   {"deal_id": 42, "client_name": "Naples Gym"})

    # Tower B checks for pending requests
    pending = check_pending("fitness-influencer")

    # Tower B completes the request
    complete_action(request_id, result={"pdf_path": "/path/to/program.pdf"})

Protocol:
    All requests are rows in the `tower_requests` table:
      - from_tower, to_tower, action, payload (JSON), status, result (JSON)
      - status: pending → processing → completed | failed
    Towers poll for their pending requests (or are triggered by launchd).
"""

import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tower_protocol")


def _get_db() -> sqlite3.Connection:
    """Get the pipeline database connection (shared coordination layer)."""
    import importlib.util
    root = Path(__file__).parent.parent
    spec = importlib.util.spec_from_file_location(
        "pipeline_db", root / "execution" / "pipeline_db.py"
    )
    pdb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pdb)
    conn = pdb.get_db()
    _ensure_table(conn)
    return conn


def _ensure_table(conn: sqlite3.Connection):
    """Create the tower_requests table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tower_requests (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            from_tower  TEXT NOT NULL,
            to_tower    TEXT NOT NULL,
            action      TEXT NOT NULL,
            payload     TEXT DEFAULT '{}',
            status      TEXT DEFAULT 'pending'
                        CHECK(status IN ('pending','processing','completed','failed')),
            result      TEXT DEFAULT NULL,
            created_at  TEXT DEFAULT (datetime('now')),
            updated_at  TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


def request_action(from_tower: str, to_tower: str, action: str,
                   payload: Dict[str, Any] = None) -> int:
    """Request another tower to perform an action.

    Returns the request ID.
    """
    conn = _get_db()
    cursor = conn.execute(
        "INSERT INTO tower_requests (from_tower, to_tower, action, payload) VALUES (?, ?, ?, ?)",
        (from_tower, to_tower, action, json.dumps(payload or {}))
    )
    request_id = cursor.lastrowid
    conn.commit()
    conn.close()
    logger.info(f"Tower request #{request_id}: {from_tower} → {to_tower} [{action}]")
    return request_id


def check_pending(tower: str) -> List[Dict[str, Any]]:
    """Check for pending requests addressed to this tower."""
    conn = _get_db()
    rows = conn.execute(
        "SELECT * FROM tower_requests WHERE to_tower = ? AND status = 'pending' "
        "ORDER BY created_at ASC",
        (tower,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def claim_request(request_id: int) -> bool:
    """Mark a request as 'processing' (claimed by the target tower)."""
    conn = _get_db()
    conn.execute(
        "UPDATE tower_requests SET status = 'processing', updated_at = datetime('now') "
        "WHERE id = ? AND status = 'pending'",
        (request_id,)
    )
    conn.commit()
    changed = conn.total_changes > 0
    conn.close()
    return changed


def complete_action(request_id: int, result: Dict[str, Any] = None) -> bool:
    """Mark a request as completed with optional result data."""
    conn = _get_db()
    conn.execute(
        "UPDATE tower_requests SET status = 'completed', result = ?, updated_at = datetime('now') "
        "WHERE id = ?",
        (json.dumps(result or {}), request_id)
    )
    conn.commit()
    conn.close()
    logger.info(f"Tower request #{request_id}: completed")
    return True


def fail_action(request_id: int, error: str) -> bool:
    """Mark a request as failed with error detail."""
    conn = _get_db()
    conn.execute(
        "UPDATE tower_requests SET status = 'failed', result = ?, updated_at = datetime('now') "
        "WHERE id = ?",
        (json.dumps({"error": error}), request_id)
    )
    conn.commit()
    conn.close()
    logger.warning(f"Tower request #{request_id}: failed — {error}")
    return True


# ---------------------------------------------------------------------------
# Convenience: Common cross-tower actions
# ---------------------------------------------------------------------------

def request_coaching_content(deal_id: int, client_name: str, tower: str = "fitness-influencer") -> int:
    """Lead-gen → Fitness: Generate coaching content for a won deal."""
    return request_action(
        "lead-generation", tower, "generate_coaching_content",
        {"deal_id": deal_id, "client_name": client_name}
    )


def request_calendly_email(deal_id: int, contact_email: str, company: str) -> int:
    """Lead-gen → Personal-assistant: Send Calendly link to prospect."""
    return request_action(
        "lead-generation", "personal-assistant", "send_calendly_email",
        {"deal_id": deal_id, "contact_email": contact_email, "company": company}
    )


def request_meeting_prep(deal_id: int, company: str) -> int:
    """Personal-assistant → AI-systems: Generate meeting prep packet."""
    return request_action(
        "personal-assistant", "ai-systems", "generate_meeting_prep",
        {"deal_id": deal_id, "company": company}
    )


def request_notification_email(from_tower: str, to_email: str,
                               subject: str, body: str) -> int:
    """Any tower → Personal-assistant: Send a notification email via Gmail."""
    return request_action(
        from_tower, "personal-assistant", "send_notification_email",
        {"to": to_email, "subject": subject, "body": body}
    )


def request_goal_progress_update(from_tower: str = "system") -> int:
    """Any tower → Personal-assistant: Trigger goal progress recalculation."""
    return request_action(
        from_tower, "personal-assistant", "update_goal_progress", {}
    )


# ---------------------------------------------------------------------------
# Tower status queries (read-only, no request creation)
# ---------------------------------------------------------------------------

def get_tower_health(tower: str) -> Dict[str, Any]:
    """Check request health for a specific tower — pending, failed, recent completions."""
    conn = _get_db()
    pending = conn.execute(
        "SELECT COUNT(*) FROM tower_requests WHERE to_tower = ? AND status = 'pending'",
        (tower,)
    ).fetchone()[0]
    failed_recent = conn.execute(
        "SELECT COUNT(*) FROM tower_requests WHERE to_tower = ? AND status = 'failed' "
        "AND created_at > datetime('now', '-1 day')",
        (tower,)
    ).fetchone()[0]
    completed_recent = conn.execute(
        "SELECT COUNT(*) FROM tower_requests WHERE to_tower = ? AND status = 'completed' "
        "AND created_at > datetime('now', '-1 day')",
        (tower,)
    ).fetchone()[0]
    conn.close()
    return {
        "tower": tower,
        "pending": pending,
        "failed_24h": failed_recent,
        "completed_24h": completed_recent,
        "healthy": failed_recent == 0 and pending < 10,
    }
