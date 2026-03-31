#!/usr/bin/env python3
"""
Tower Triggers — Automatic cross-tower actions based on deal stage changes.

Trigger Rules:
  - Deal → "Won"       → Fire cross-sell requests to other towers
  - Deal → "Qualified" → Auto-generate content/proposals
  - Response received  → Escalate priority of related requests

Usage:
    from execution.tower_triggers import check_stage_triggers, fire_trigger

    # Check all recent stage changes and fire appropriate triggers
    fired = check_stage_triggers()

    # Manually fire a trigger for a specific deal
    fire_trigger(deal_id, "won", deal_data)
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tower_triggers")

REPO_ROOT = Path(__file__).resolve().parent.parent


def _get_db():
    """Get pipeline database connection."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "pipeline_db", REPO_ROOT / "execution" / "pipeline_db.py"
    )
    pdb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pdb)
    return pdb.get_db()


def _get_protocol():
    """Get tower protocol module."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "tower_protocol", REPO_ROOT / "execution" / "tower_protocol.py"
    )
    tp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tp)
    return tp


# ── Cross-Sell Rules ─────────────────────────────────────────────────────────
# When a deal is won in one tower, what should we offer in other towers?

CROSS_SELL_RULES = {
    "digital-ai-services": [
        # AI Services client → suggest web dev, fitness coaching
        {"to": "digital-web-dev", "action": "cross_sell_web_redesign",
         "condition": lambda d: not d.get("website") or "outdated" in (d.get("notes") or "").lower()},
        {"to": "fitness-coaching", "action": "cross_sell_coaching",
         "condition": lambda d: True},  # Always offer
    ],
    "digital-web-dev": [
        # Web dev client → suggest AI automation
        {"to": "digital-ai-services", "action": "cross_sell_ai_automation",
         "condition": lambda d: True},
    ],
    "fitness-coaching": [
        # Coaching client → suggest AI (for their business) or influencer (if big following)
        {"to": "digital-ai-services", "action": "cross_sell_ai_automation",
         "condition": lambda d: d.get("industry") and d["industry"] != "Individual"},
        {"to": "fitness-influencer", "action": "cross_sell_brand_deals",
         "condition": lambda d: "influencer" in (d.get("notes") or "").lower() or
                                "followers" in (d.get("notes") or "").lower()},
    ],
    "fitness-influencer": [
        # Influencer client → suggest coaching or AI
        {"to": "fitness-coaching", "action": "cross_sell_coaching",
         "condition": lambda d: True},
        {"to": "digital-ai-services", "action": "cross_sell_ai_automation",
         "condition": lambda d: "business" in (d.get("notes") or "").lower()},
    ],
}

# ── Content Generation Rules ─────────────────────────────────────────────────
# When deal reaches "Qualified", auto-generate relevant content

CONTENT_RULES = {
    "digital-ai-services": [
        {"action": "generate_ai_proposal", "to": "digital-ai-services"},
        {"action": "generate_roi_calculator", "to": "digital-ai-services"},
    ],
    "digital-web-dev": [
        {"action": "generate_web_proposal", "to": "digital-web-dev"},
    ],
    "fitness-coaching": [
        {"action": "generate_coaching_program", "to": "fitness-influencer"},
        {"action": "generate_coaching_proposal", "to": "fitness-coaching"},
    ],
    "fitness-influencer": [
        {"action": "generate_media_kit", "to": "fitness-influencer"},
        {"action": "generate_brand_proposal", "to": "fitness-influencer"},
    ],
}


def _ensure_trigger_log_table(conn: sqlite3.Connection):
    """Create trigger log table to track which triggers have fired."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tower_trigger_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id         INTEGER NOT NULL,
            trigger_type    TEXT NOT NULL,
            from_stage      TEXT,
            to_stage        TEXT,
            requests_fired  TEXT DEFAULT '[]',
            created_at      TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_trigger_log_deal 
        ON tower_trigger_log(deal_id, trigger_type)
    """)
    conn.commit()


def _has_trigger_fired(conn: sqlite3.Connection, deal_id: int,
                       trigger_type: str, to_stage: str) -> bool:
    """Check if this trigger already fired for this deal/stage."""
    row = conn.execute("""
        SELECT 1 FROM tower_trigger_log 
        WHERE deal_id = ? AND trigger_type = ? AND to_stage = ?
        AND created_at > datetime('now', '-24 hours')
    """, (deal_id, trigger_type, to_stage)).fetchone()
    return row is not None


def _log_trigger(conn: sqlite3.Connection, deal_id: int, trigger_type: str,
                 from_stage: str, to_stage: str, requests_fired: List[int]):
    """Log that a trigger fired."""
    conn.execute("""
        INSERT INTO tower_trigger_log 
        (deal_id, trigger_type, from_stage, to_stage, requests_fired)
        VALUES (?, ?, ?, ?, ?)
    """, (deal_id, trigger_type, from_stage, to_stage, json.dumps(requests_fired)))
    conn.commit()


def fire_won_trigger(deal: Dict[str, Any]) -> List[int]:
    """Fire cross-sell requests when a deal is won.
    
    Returns list of created request IDs.
    """
    tp = _get_protocol()
    deal_id = deal["id"]
    tower = deal.get("tower", "digital-ai-services")
    company = deal.get("company", "Unknown")
    
    rules = CROSS_SELL_RULES.get(tower, [])
    request_ids = []
    
    for rule in rules:
        # Check condition
        if not rule["condition"](deal):
            continue
            
        # Calculate priority based on deal value
        deal_value = (deal.get("setup_fee") or 0) + (deal.get("monthly_fee") or 0) * 12
        priority = _calculate_priority_score(deal_value, 0.3, 0.8)  # High urgency for cross-sell
        
        payload = {
            "deal_id": deal_id,
            "source_deal_company": company,
            "source_tower": tower,
            "contact_name": deal.get("contact_name"),
            "contact_email": deal.get("contact_email"),
            "contact_phone": deal.get("contact_phone"),
            "industry": deal.get("industry"),
            "notes": deal.get("notes"),
            "cross_sell_context": f"Won deal in {tower}: {company}",
            "priority_score": priority,
        }
        
        req_id = tp.request_action(
            from_tower=tower,
            to_tower=rule["to"],
            action=rule["action"],
            payload=payload
        )
        
        # Update priority in the request
        _update_request_priority(req_id, priority)
        
        request_ids.append(req_id)
        logger.info(f"Cross-sell trigger: {tower} → {rule['to']} [{rule['action']}] "
                   f"for {company} (priority: {priority:.2f})")
    
    return request_ids


def fire_qualified_trigger(deal: Dict[str, Any]) -> List[int]:
    """Fire content generation requests when a deal becomes qualified.
    
    Returns list of created request IDs.
    """
    tp = _get_protocol()
    deal_id = deal["id"]
    tower = deal.get("tower", "digital-ai-services")
    company = deal.get("company", "Unknown")
    
    rules = CONTENT_RULES.get(tower, [])
    request_ids = []
    
    for rule in rules:
        # Calculate priority based on deal value
        deal_value = (deal.get("proposal_amount") or 0) or \
                     (deal.get("setup_fee") or 0) + (deal.get("monthly_fee") or 0) * 12
        priority = _calculate_priority_score(deal_value, 0.5, 0.6)  # Medium urgency
        
        payload = {
            "deal_id": deal_id,
            "company": company,
            "tower": tower,
            "contact_name": deal.get("contact_name"),
            "contact_email": deal.get("contact_email"),
            "industry": deal.get("industry"),
            "pain_points": deal.get("pain_points"),
            "notes": deal.get("notes"),
            "priority_score": priority,
        }
        
        req_id = tp.request_action(
            from_tower=tower,
            to_tower=rule["to"],
            action=rule["action"],
            payload=payload
        )
        
        _update_request_priority(req_id, priority)
        
        request_ids.append(req_id)
        logger.info(f"Content trigger: {tower} → {rule['to']} [{rule['action']}] "
                   f"for {company} (priority: {priority:.2f})")
    
    return request_ids


def fire_response_escalation(deal: Dict[str, Any]) -> List[int]:
    """When a prospect responds, escalate priority of all pending requests for this deal."""
    conn = _get_db()
    deal_id = deal["id"]
    company = deal.get("company", "Unknown")
    
    # Find pending requests related to this deal
    rows = conn.execute("""
        SELECT id, priority_score FROM tower_requests 
        WHERE status IN ('pending', 'processing')
        AND (
            payload LIKE ? OR payload LIKE ?
        )
    """, (f'%"deal_id": {deal_id}%', f'%"deal_id":{deal_id}%')).fetchall()
    
    escalated_ids = []
    for row in rows:
        req_id = row["id"]
        old_priority = row["priority_score"] or 0.5
        new_priority = min(1.0, old_priority * 1.5)  # 50% boost
        
        conn.execute("""
            UPDATE tower_requests 
            SET priority_score = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (new_priority, req_id))
        
        escalated_ids.append(req_id)
        logger.info(f"Priority escalated: request #{req_id} for {company} "
                   f"({old_priority:.2f} → {new_priority:.2f})")
    
    conn.commit()
    conn.close()
    return escalated_ids


def _calculate_priority_score(deal_value: float, 
                               conversion_prob: float = 0.5,
                               urgency: float = 0.5) -> float:
    """Calculate ROI priority score.
    
    Score = normalized_deal_value × conversion_probability × urgency_factor
    
    Returns value between 0 and 1.
    """
    # Normalize deal value (assume max deal is $50k/year)
    max_deal = 50000
    normalized_value = min(deal_value / max_deal, 1.0)
    
    # Composite score
    score = normalized_value * conversion_prob * urgency
    
    # Apply sigmoid-like scaling to spread scores
    # This ensures we don't cluster all scores at extremes
    import math
    scaled = 1 / (1 + math.exp(-10 * (score - 0.3)))
    
    return round(scaled, 4)


def _update_request_priority(request_id: int, priority_score: float):
    """Update the priority score on a tower request."""
    conn = _get_db()
    
    # Ensure priority_score column exists
    try:
        conn.execute("SELECT priority_score FROM tower_requests LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE tower_requests ADD COLUMN priority_score REAL DEFAULT 0.5")
        conn.commit()
    
    conn.execute("""
        UPDATE tower_requests 
        SET priority_score = ?, updated_at = datetime('now')
        WHERE id = ?
    """, (priority_score, request_id))
    conn.commit()
    conn.close()


def check_stage_triggers(since_minutes: int = 15) -> Dict[str, List[int]]:
    """Check for recent stage changes and fire appropriate triggers.
    
    Called by cross_tower_sync to process deal stage transitions.
    
    Returns dict of trigger_type → list of request IDs fired.
    """
    conn = _get_db()
    _ensure_trigger_log_table(conn)
    
    results = {
        "won_triggers": [],
        "qualified_triggers": [],
        "response_escalations": [],
    }
    
    # Find stage_changed activities in the last N minutes
    activities = conn.execute(f"""
        SELECT a.deal_id, a.description, d.*
        FROM activities a
        JOIN deals d ON a.deal_id = d.id
        WHERE a.activity_type = 'stage_changed'
        AND a.created_at > datetime('now', '-{since_minutes} minutes')
        ORDER BY a.created_at DESC
    """).fetchall()
    
    for row in activities:
        deal = dict(row)
        deal_id = deal["deal_id"]
        description = deal.get("description", "")
        
        # Parse stage from description like "Moved to: Closed Won"
        if "Closed Won" in description:
            if not _has_trigger_fired(conn, deal_id, "won", "Closed Won"):
                req_ids = fire_won_trigger(deal)
                _log_trigger(conn, deal_id, "won", None, "Closed Won", req_ids)
                results["won_triggers"].extend(req_ids)
                
        elif "Qualified" in description:
            if not _has_trigger_fired(conn, deal_id, "qualified", "Qualified"):
                req_ids = fire_qualified_trigger(deal)
                _log_trigger(conn, deal_id, "qualified", None, "Qualified", req_ids)
                results["qualified_triggers"].extend(req_ids)
    
    # Check for recent responses (Replied stage or response in outreach_log)
    responses = conn.execute(f"""
        SELECT DISTINCT d.*
        FROM deals d
        WHERE d.stage IN ('Replied', 'Hot Response', 'Warm Response')
        AND d.updated_at > datetime('now', '-{since_minutes} minutes')
    """).fetchall()
    
    for row in responses:
        deal = dict(row)
        deal_id = deal["id"]
        if not _has_trigger_fired(conn, deal_id, "response", deal["stage"]):
            escalated = fire_response_escalation(deal)
            _log_trigger(conn, deal_id, "response", None, deal["stage"], escalated)
            results["response_escalations"].extend(escalated)
    
    conn.close()
    
    total = sum(len(v) for v in results.values())
    if total:
        logger.info(f"Stage triggers fired: {total} total "
                   f"(won={len(results['won_triggers'])}, "
                   f"qualified={len(results['qualified_triggers'])}, "
                   f"escalations={len(results['response_escalations'])})")
    
    return results


def fire_trigger(deal_id: int, trigger_type: str, 
                 deal_data: Optional[Dict[str, Any]] = None) -> List[int]:
    """Manually fire a specific trigger for a deal.
    
    Args:
        deal_id: The deal to trigger on
        trigger_type: "won", "qualified", or "response"
        deal_data: Optional deal data (will be fetched if not provided)
    
    Returns list of created request IDs.
    """
    conn = _get_db()
    
    if deal_data is None:
        row = conn.execute("SELECT * FROM deals WHERE id = ?", (deal_id,)).fetchone()
        if not row:
            logger.error(f"Deal {deal_id} not found")
            return []
        deal_data = dict(row)
    
    conn.close()
    
    if trigger_type == "won":
        return fire_won_trigger(deal_data)
    elif trigger_type == "qualified":
        return fire_qualified_trigger(deal_data)
    elif trigger_type == "response":
        return fire_response_escalation(deal_data)
    else:
        logger.error(f"Unknown trigger type: {trigger_type}")
        return []


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Tower Triggers")
    parser.add_argument("--check", action="store_true", 
                       help="Check for recent stage changes and fire triggers")
    parser.add_argument("--since", type=int, default=15,
                       help="Check activities from the last N minutes")
    parser.add_argument("--fire", type=str,
                       help="Manually fire a trigger (format: deal_id:type)")
    parser.add_argument("--status", action="store_true",
                       help="Show recent trigger log")
    args = parser.parse_args()
    
    if args.check:
        results = check_stage_triggers(since_minutes=args.since)
        print(json.dumps(results, indent=2))
    elif args.fire:
        try:
            deal_id, trigger_type = args.fire.split(":")
            req_ids = fire_trigger(int(deal_id), trigger_type)
            print(f"Fired {len(req_ids)} requests: {req_ids}")
        except ValueError:
            print("Format: --fire deal_id:type (e.g., --fire 42:won)")
    elif args.status:
        conn = _get_db()
        _ensure_trigger_log_table(conn)
        rows = conn.execute("""
            SELECT * FROM tower_trigger_log 
            ORDER BY created_at DESC LIMIT 20
        """).fetchall()
        for r in rows:
            d = dict(r)
            print(f"[{d['created_at']}] Deal #{d['deal_id']} | {d['trigger_type']} | "
                  f"{d['from_stage']} → {d['to_stage']} | {d['requests_fired']}")
        conn.close()
    else:
        parser.print_help()
