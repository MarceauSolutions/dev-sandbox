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
            priority_score REAL DEFAULT 0.5,
            created_at  TEXT DEFAULT (datetime('now')),
            updated_at  TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    
    # Add priority_score column if missing (for existing tables)
    try:
        conn.execute("SELECT priority_score FROM tower_requests LIMIT 1")
    except:
        try:
            conn.execute("ALTER TABLE tower_requests ADD COLUMN priority_score REAL DEFAULT 0.5")
            conn.commit()
        except:
            pass  # Column may already exist


def request_action(from_tower: str, to_tower: str, action: str,
                   payload: Dict[str, Any] = None,
                   priority_score: float = None) -> int:
    """Request another tower to perform an action.

    Args:
        from_tower: Requesting tower ID
        to_tower: Target tower ID
        action: Action name to perform
        payload: Optional dict with action parameters
        priority_score: Optional priority (0-1). If not provided, calculated from payload.

    Returns the request ID.
    """
    conn = _get_db()
    
    # Calculate priority if not provided
    if priority_score is None:
        priority_score = calculate_priority(payload or {})
    
    cursor = conn.execute(
        "INSERT INTO tower_requests (from_tower, to_tower, action, payload, priority_score) "
        "VALUES (?, ?, ?, ?, ?)",
        (from_tower, to_tower, action, json.dumps(payload or {}), priority_score)
    )
    request_id = cursor.lastrowid
    conn.commit()
    conn.close()
    logger.info(f"Tower request #{request_id}: {from_tower} → {to_tower} [{action}] "
                f"(priority: {priority_score:.3f})")
    return request_id


def calculate_priority(payload: Dict[str, Any],
                      conversion_prob: float = None,
                      urgency_factor: float = None) -> float:
    """Calculate ROI-based priority score.
    
    Score = normalized_deal_value × conversion_probability × urgency_factor
    
    Args:
        payload: Request payload (may contain deal_value, priority_score, etc.)
        conversion_prob: Override conversion probability (0-1)
        urgency_factor: Override urgency factor (0-1)
    
    Returns: Priority score between 0 and 1
    """
    import math
    
    # Extract deal value from payload
    deal_value = payload.get("deal_value", 0)
    if not deal_value:
        # Try to calculate from fees
        setup = payload.get("setup_fee", 0) or 0
        monthly = payload.get("monthly_fee", 0) or 0
        deal_value = setup + (monthly * 12)
    
    # If payload already has a priority_score, use it as base
    if "priority_score" in payload:
        return float(payload["priority_score"])
    
    # Normalize deal value (assume max deal is $50k/year)
    max_deal = 50000
    normalized_value = min(deal_value / max_deal, 1.0) if deal_value > 0 else 0.2
    
    # Default conversion probability based on action type
    if conversion_prob is None:
        action_probs = {
            "cross_sell": 0.3,
            "generate_proposal": 0.6,
            "send_email": 0.4,
            "generate_content": 0.5,
        }
        # Check if any action keyword matches
        action = payload.get("action", "").lower()
        conversion_prob = 0.5
        for key, prob in action_probs.items():
            if key in action:
                conversion_prob = prob
                break
    
    # Default urgency based on context
    if urgency_factor is None:
        urgency_factor = 0.5
        # Hot responses get higher urgency
        if payload.get("stage") in ("Hot Response", "Trial Active"):
            urgency_factor = 0.9
        elif payload.get("cross_sell_context"):
            urgency_factor = 0.7
    
    # Composite score
    raw_score = normalized_value * conversion_prob * urgency_factor
    
    # Apply sigmoid scaling to spread scores between 0.1 and 0.9
    scaled = 1 / (1 + math.exp(-8 * (raw_score - 0.25)))
    scaled = 0.1 + (scaled * 0.8)  # Clamp to 0.1-0.9 range
    
    return round(scaled, 4)


def update_priority(request_id: int, priority_score: float) -> bool:
    """Update the priority score of an existing request."""
    conn = _get_db()
    conn.execute(
        "UPDATE tower_requests SET priority_score = ?, updated_at = datetime('now') "
        "WHERE id = ?",
        (priority_score, request_id)
    )
    changed = conn.total_changes > 0
    conn.commit()
    conn.close()
    return changed


def boost_priority(request_id: int, multiplier: float = 1.5) -> float:
    """Boost the priority of a request (e.g., when response received).
    
    Returns the new priority score.
    """
    conn = _get_db()
    row = conn.execute(
        "SELECT priority_score FROM tower_requests WHERE id = ?", (request_id,)
    ).fetchone()
    
    if not row:
        conn.close()
        return 0.0
    
    old_priority = row[0] or 0.5
    new_priority = min(1.0, old_priority * multiplier)
    
    conn.execute(
        "UPDATE tower_requests SET priority_score = ?, updated_at = datetime('now') "
        "WHERE id = ?",
        (new_priority, request_id)
    )
    conn.commit()
    conn.close()
    
    logger.info(f"Priority boosted: request #{request_id} ({old_priority:.3f} → {new_priority:.3f})")
    return new_priority


def check_pending(tower: str, order_by_priority: bool = True) -> List[Dict[str, Any]]:
    """Check for pending requests addressed to this tower.
    
    Args:
        tower: Tower ID to check
        order_by_priority: If True, return high-priority requests first.
                          If False, return in FIFO order (created_at ASC).
    
    Returns: List of pending request dicts with priority_score included.
    """
    conn = _get_db()
    
    if order_by_priority:
        # High priority first, then by age (older first within same priority)
        order_clause = "ORDER BY priority_score DESC, created_at ASC"
    else:
        order_clause = "ORDER BY created_at ASC"
    
    rows = conn.execute(
        f"SELECT * FROM tower_requests WHERE to_tower = ? AND status = 'pending' "
        f"{order_clause}",
        (tower,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_high_priority_requests(min_priority: float = 0.7) -> List[Dict[str, Any]]:
    """Get all high-priority pending requests across all towers.
    
    Used for urgent processing or alerts.
    """
    conn = _get_db()
    rows = conn.execute(
        "SELECT * FROM tower_requests WHERE status = 'pending' "
        "AND priority_score >= ? ORDER BY priority_score DESC",
        (min_priority,)
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
