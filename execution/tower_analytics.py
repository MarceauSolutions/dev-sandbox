#!/usr/bin/env python3
"""
Tower Analytics — Conversion tracking for cross-tower requests.

Tracks: request → action → outcome → revenue

Feeds learning into priority scoring system.

Usage:
    from execution.tower_analytics import (
        log_conversion, get_conversion_stats, 
        calculate_tower_roi, update_conversion_probabilities
    )

    # Log when a cross-tower request leads to revenue
    log_conversion(request_id, outcome="client_won", revenue=5964)

    # Get stats for a specific tower
    stats = get_conversion_stats("digital-ai-services")

    # Update conversion probabilities based on historical data
    update_conversion_probabilities()
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tower_analytics")

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


def _ensure_analytics_tables(conn: sqlite3.Connection):
    """Create analytics tables if they don't exist."""
    conn.executescript("""
        -- Track conversion outcomes for tower requests
        CREATE TABLE IF NOT EXISTS tower_conversions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id      INTEGER NOT NULL,
            from_tower      TEXT NOT NULL,
            to_tower        TEXT NOT NULL,
            action          TEXT NOT NULL,
            outcome         TEXT DEFAULT 'pending'
                            CHECK(outcome IN ('pending', 'no_action', 'action_taken', 
                                             'lead_generated', 'meeting_booked', 
                                             'proposal_sent', 'trial_started', 
                                             'client_won', 'client_lost')),
            revenue         REAL DEFAULT 0,
            cost            REAL DEFAULT 0,
            deal_id         INTEGER,
            notes           TEXT,
            created_at      TEXT DEFAULT (datetime('now')),
            converted_at    TEXT
        );

        -- Aggregated conversion rates by tower pair and action
        CREATE TABLE IF NOT EXISTS tower_conversion_rates (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            from_tower      TEXT NOT NULL,
            to_tower        TEXT NOT NULL,
            action          TEXT NOT NULL,
            total_requests  INTEGER DEFAULT 0,
            conversions     INTEGER DEFAULT 0,
            total_revenue   REAL DEFAULT 0,
            avg_revenue     REAL DEFAULT 0,
            conversion_rate REAL DEFAULT 0,
            roi             REAL DEFAULT 0,
            last_updated    TEXT DEFAULT (datetime('now')),
            UNIQUE(from_tower, to_tower, action)
        );

        -- Learning coefficients for priority calculation
        CREATE TABLE IF NOT EXISTS tower_learning (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            tower_pair      TEXT NOT NULL,
            action          TEXT NOT NULL,
            learned_prob    REAL DEFAULT 0.5,
            sample_size     INTEGER DEFAULT 0,
            confidence      REAL DEFAULT 0,
            last_updated    TEXT DEFAULT (datetime('now')),
            UNIQUE(tower_pair, action)
        );

        CREATE INDEX IF NOT EXISTS idx_conversions_request 
            ON tower_conversions(request_id);
        CREATE INDEX IF NOT EXISTS idx_conversions_outcome 
            ON tower_conversions(outcome);
        CREATE INDEX IF NOT EXISTS idx_learning_pair 
            ON tower_learning(tower_pair);
    """)
    conn.commit()


def log_conversion(request_id: int, outcome: str,
                   revenue: float = 0, cost: float = 0,
                   deal_id: int = None, notes: str = "") -> int:
    """Log a conversion outcome for a tower request.
    
    Args:
        request_id: The tower_requests.id that led to this outcome
        outcome: One of: no_action, action_taken, lead_generated, 
                 meeting_booked, proposal_sent, trial_started, 
                 client_won, client_lost
        revenue: Revenue generated (if any)
        cost: Cost incurred (if any)
        deal_id: Related deal ID (if applicable)
        notes: Additional context
    
    Returns: Conversion log ID
    """
    conn = _get_db()
    _ensure_analytics_tables(conn)
    
    # Get request details
    req = conn.execute(
        "SELECT from_tower, to_tower, action FROM tower_requests WHERE id = ?",
        (request_id,)
    ).fetchone()
    
    if not req:
        logger.error(f"Request #{request_id} not found")
        conn.close()
        return 0
    
    req = dict(req)
    
    cursor = conn.execute("""
        INSERT INTO tower_conversions 
        (request_id, from_tower, to_tower, action, outcome, revenue, cost, deal_id, notes, converted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (request_id, req["from_tower"], req["to_tower"], req["action"],
          outcome, revenue, cost, deal_id, notes))
    
    conversion_id = cursor.lastrowid
    conn.commit()
    
    logger.info(f"Conversion logged: request #{request_id} → {outcome} "
               f"(${revenue:,.0f} revenue)")
    
    # Trigger rate update
    _update_conversion_rate(conn, req["from_tower"], req["to_tower"], req["action"])
    
    conn.close()
    return conversion_id


def _update_conversion_rate(conn: sqlite3.Connection,
                            from_tower: str, to_tower: str, action: str):
    """Update aggregated conversion rates for a tower pair + action."""
    
    # Calculate fresh stats
    stats = conn.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN outcome IN ('meeting_booked', 'proposal_sent', 
                                       'trial_started', 'client_won') THEN 1 ELSE 0 END) as conversions,
            SUM(revenue) as total_revenue,
            AVG(CASE WHEN revenue > 0 THEN revenue ELSE NULL END) as avg_revenue
        FROM tower_conversions
        WHERE from_tower = ? AND to_tower = ? AND action = ?
        AND outcome != 'pending'
    """, (from_tower, to_tower, action)).fetchone()
    
    stats = dict(stats)
    total = stats["total"] or 0
    conversions = stats["conversions"] or 0
    total_revenue = stats["total_revenue"] or 0
    avg_revenue = stats["avg_revenue"] or 0
    
    # Calculate rates
    conversion_rate = conversions / max(total, 1)
    roi = total_revenue / max(total * 10, 1)  # Assume $10 cost per request
    
    # Upsert
    conn.execute("""
        INSERT INTO tower_conversion_rates 
        (from_tower, to_tower, action, total_requests, conversions, 
         total_revenue, avg_revenue, conversion_rate, roi, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(from_tower, to_tower, action) DO UPDATE SET
            total_requests = excluded.total_requests,
            conversions = excluded.conversions,
            total_revenue = excluded.total_revenue,
            avg_revenue = excluded.avg_revenue,
            conversion_rate = excluded.conversion_rate,
            roi = excluded.roi,
            last_updated = excluded.last_updated
    """, (from_tower, to_tower, action, total, conversions,
          total_revenue, avg_revenue, conversion_rate, roi))
    
    conn.commit()


def get_conversion_stats(tower: str = None) -> Dict[str, Any]:
    """Get conversion statistics for a tower (or all towers).
    
    Returns:
        {
            "total_requests": int,
            "total_conversions": int,
            "total_revenue": float,
            "conversion_rate": float,
            "avg_revenue_per_conversion": float,
            "top_actions": [...],
            "by_outcome": {...}
        }
    """
    conn = _get_db()
    _ensure_analytics_tables(conn)
    
    where = ""
    params = ()
    if tower:
        where = "WHERE to_tower = ?"
        params = (tower,)
    
    # Overall stats
    row = conn.execute(f"""
        SELECT 
            COUNT(*) as total_requests,
            SUM(CASE WHEN outcome IN ('meeting_booked', 'proposal_sent', 
                                       'trial_started', 'client_won') THEN 1 ELSE 0 END) as conversions,
            SUM(revenue) as total_revenue
        FROM tower_conversions
        {where}
    """, params).fetchone()
    
    row = dict(row)
    total_requests = row["total_requests"] or 0
    conversions = row["conversions"] or 0
    total_revenue = row["total_revenue"] or 0
    
    # By outcome
    outcomes = {}
    for r in conn.execute(f"""
        SELECT outcome, COUNT(*) as count, SUM(revenue) as revenue
        FROM tower_conversions
        {where}
        GROUP BY outcome
    """, params):
        d = dict(r)
        outcomes[d["outcome"]] = {
            "count": d["count"],
            "revenue": d["revenue"] or 0
        }
    
    # Top actions by conversion rate
    top_actions = []
    for r in conn.execute(f"""
        SELECT action, total_requests, conversions, conversion_rate, avg_revenue
        FROM tower_conversion_rates
        {("WHERE to_tower = ?" if tower else "")}
        ORDER BY conversion_rate DESC
        LIMIT 10
    """, params if tower else ()):
        top_actions.append(dict(r))
    
    conn.close()
    
    return {
        "tower": tower or "all",
        "total_requests": total_requests,
        "total_conversions": conversions,
        "total_revenue": total_revenue,
        "conversion_rate": round(conversions / max(total_requests, 1), 4),
        "avg_revenue_per_conversion": round(total_revenue / max(conversions, 1), 2),
        "by_outcome": outcomes,
        "top_actions": top_actions,
    }


def calculate_tower_roi(from_tower: str, to_tower: str) -> Dict[str, Any]:
    """Calculate ROI for requests from one tower to another.
    
    Returns:
        {
            "from_tower": str,
            "to_tower": str,
            "total_requests": int,
            "total_revenue": float,
            "estimated_cost": float,
            "roi_percent": float,
            "best_action": str,
            "worst_action": str
        }
    """
    conn = _get_db()
    _ensure_analytics_tables(conn)
    
    row = conn.execute("""
        SELECT 
            COUNT(*) as total_requests,
            SUM(revenue) as total_revenue,
            SUM(cost) as total_cost
        FROM tower_conversions
        WHERE from_tower = ? AND to_tower = ?
    """, (from_tower, to_tower)).fetchone()
    
    row = dict(row)
    total_requests = row["total_requests"] or 0
    total_revenue = row["total_revenue"] or 0
    total_cost = row["total_cost"] or (total_requests * 10)  # Default $10/request
    
    # Best and worst actions
    actions = conn.execute("""
        SELECT action, conversion_rate, roi
        FROM tower_conversion_rates
        WHERE from_tower = ? AND to_tower = ?
        ORDER BY roi DESC
    """, (from_tower, to_tower)).fetchall()
    
    conn.close()
    
    best_action = actions[0]["action"] if actions else None
    worst_action = actions[-1]["action"] if len(actions) > 1 else None
    
    roi_percent = ((total_revenue - total_cost) / max(total_cost, 1)) * 100
    
    return {
        "from_tower": from_tower,
        "to_tower": to_tower,
        "total_requests": total_requests,
        "total_revenue": total_revenue,
        "estimated_cost": total_cost,
        "roi_percent": round(roi_percent, 1),
        "best_action": best_action,
        "worst_action": worst_action,
    }


def get_learned_probability(from_tower: str, to_tower: str, action: str) -> float:
    """Get the learned conversion probability for a specific tower action.
    
    Falls back to default 0.5 if no data exists.
    """
    conn = _get_db()
    _ensure_analytics_tables(conn)
    
    tower_pair = f"{from_tower}:{to_tower}"
    
    row = conn.execute("""
        SELECT learned_prob, sample_size, confidence
        FROM tower_learning
        WHERE tower_pair = ? AND action = ?
    """, (tower_pair, action)).fetchone()
    
    conn.close()
    
    if not row:
        return 0.5
    
    row = dict(row)
    
    # If sample size is small, blend with prior (0.5)
    sample_size = row["sample_size"] or 0
    learned = row["learned_prob"]
    
    if sample_size < 5:
        # Bayesian-ish: weight prior more heavily with small samples
        prior_weight = (5 - sample_size) / 5
        return (prior_weight * 0.5) + ((1 - prior_weight) * learned)
    
    return learned


def update_conversion_probabilities():
    """Update learned conversion probabilities from historical data.
    
    Called periodically to feed learning into priority scoring.
    """
    conn = _get_db()
    _ensure_analytics_tables(conn)
    
    # Get all tower pair + action combinations with conversions
    rates = conn.execute("""
        SELECT from_tower, to_tower, action, total_requests, 
               conversions, conversion_rate
        FROM tower_conversion_rates
        WHERE total_requests >= 1
    """).fetchall()
    
    updated = 0
    for r in rates:
        r = dict(r)
        tower_pair = f"{r['from_tower']}:{r['to_tower']}"
        action = r["action"]
        sample_size = r["total_requests"]
        conversion_rate = r["conversion_rate"]
        
        # Calculate confidence based on sample size
        # More samples = higher confidence in the learned rate
        import math
        confidence = 1 - math.exp(-sample_size / 10)  # Asymptotes to 1
        
        # Upsert learning record
        conn.execute("""
            INSERT INTO tower_learning 
            (tower_pair, action, learned_prob, sample_size, confidence, last_updated)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(tower_pair, action) DO UPDATE SET
                learned_prob = excluded.learned_prob,
                sample_size = excluded.sample_size,
                confidence = excluded.confidence,
                last_updated = excluded.last_updated
        """, (tower_pair, action, conversion_rate, sample_size, confidence))
        
        updated += 1
    
    conn.commit()
    conn.close()
    
    logger.info(f"Updated {updated} conversion probabilities")
    return updated


def auto_log_completed_request(request_id: int) -> Optional[int]:
    """Automatically log a conversion when a tower request is completed.
    
    Called by cross_tower_sync when processing completed requests.
    Determines outcome based on result data.
    """
    conn = _get_db()
    _ensure_analytics_tables(conn)
    
    # Check if already logged
    existing = conn.execute(
        "SELECT id FROM tower_conversions WHERE request_id = ?", (request_id,)
    ).fetchone()
    
    if existing:
        conn.close()
        return existing[0]
    
    # Get request details
    req = conn.execute(
        "SELECT * FROM tower_requests WHERE id = ?", (request_id,)
    ).fetchone()
    
    if not req:
        conn.close()
        return None
    
    req = dict(req)
    status = req["status"]
    result = json.loads(req.get("result") or "{}")
    payload = json.loads(req.get("payload") or "{}")
    
    # Determine outcome
    if status == "failed":
        outcome = "no_action"
    elif status == "completed":
        # Check result for clues about outcome
        if result.get("deal_created") or result.get("lead_generated"):
            outcome = "lead_generated"
        elif result.get("meeting_booked"):
            outcome = "meeting_booked"
        elif result.get("proposal_sent") or result.get("proposal_path"):
            outcome = "proposal_sent"
        elif result.get("revenue") or result.get("client_won"):
            outcome = "client_won"
        else:
            outcome = "action_taken"
    else:
        outcome = "pending"
    
    revenue = result.get("revenue", 0) or payload.get("deal_value", 0)
    deal_id = result.get("deal_id") or payload.get("deal_id")
    
    cursor = conn.execute("""
        INSERT INTO tower_conversions 
        (request_id, from_tower, to_tower, action, outcome, revenue, deal_id, converted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (request_id, req["from_tower"], req["to_tower"], req["action"],
          outcome, revenue, deal_id))
    
    conversion_id = cursor.lastrowid
    conn.commit()
    
    # Update rates
    _update_conversion_rate(conn, req["from_tower"], req["to_tower"], req["action"])
    
    conn.close()
    return conversion_id


def get_tower_dashboard() -> Dict[str, Any]:
    """Get a complete dashboard view of cross-tower analytics.
    
    Returns summary stats, top performers, and learning status.
    """
    conn = _get_db()
    _ensure_analytics_tables(conn)
    
    # Overall stats
    overall = conn.execute("""
        SELECT 
            COUNT(*) as total_requests,
            SUM(CASE WHEN outcome = 'client_won' THEN 1 ELSE 0 END) as clients_won,
            SUM(revenue) as total_revenue,
            AVG(CASE WHEN revenue > 0 THEN revenue ELSE NULL END) as avg_deal_size
        FROM tower_conversions
    """).fetchone()
    overall = dict(overall)
    
    # By tower pair
    tower_pairs = []
    for r in conn.execute("""
        SELECT from_tower, to_tower, 
               SUM(total_requests) as requests,
               SUM(conversions) as conversions,
               SUM(total_revenue) as revenue
        FROM tower_conversion_rates
        GROUP BY from_tower, to_tower
        ORDER BY revenue DESC
    """):
        tower_pairs.append(dict(r))
    
    # Learning status
    learning = []
    for r in conn.execute("""
        SELECT tower_pair, action, learned_prob, sample_size, confidence
        FROM tower_learning
        WHERE sample_size >= 3
        ORDER BY confidence DESC
        LIMIT 10
    """):
        learning.append(dict(r))
    
    # Recent conversions
    recent = []
    for r in conn.execute("""
        SELECT request_id, from_tower, to_tower, action, outcome, revenue, converted_at
        FROM tower_conversions
        WHERE outcome != 'pending'
        ORDER BY converted_at DESC
        LIMIT 10
    """):
        recent.append(dict(r))
    
    conn.close()
    
    return {
        "overall": {
            "total_requests": overall["total_requests"] or 0,
            "clients_won": overall["clients_won"] or 0,
            "total_revenue": overall["total_revenue"] or 0,
            "avg_deal_size": round(overall["avg_deal_size"] or 0, 2),
        },
        "tower_pairs": tower_pairs,
        "learning": learning,
        "recent_conversions": recent,
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Tower Analytics")
    parser.add_argument("--stats", type=str, nargs="?", const="all",
                       help="Show conversion stats (optionally for a specific tower)")
    parser.add_argument("--roi", type=str, nargs=2, metavar=("FROM", "TO"),
                       help="Calculate ROI for a tower pair")
    parser.add_argument("--update", action="store_true",
                       help="Update conversion probabilities from historical data")
    parser.add_argument("--dashboard", action="store_true",
                       help="Show full analytics dashboard")
    parser.add_argument("--log", type=int, metavar="REQUEST_ID",
                       help="Auto-log conversion for a completed request")
    args = parser.parse_args()
    
    if args.stats:
        tower = None if args.stats == "all" else args.stats
        stats = get_conversion_stats(tower)
        print(json.dumps(stats, indent=2))
    elif args.roi:
        roi = calculate_tower_roi(args.roi[0], args.roi[1])
        print(json.dumps(roi, indent=2))
    elif args.update:
        count = update_conversion_probabilities()
        print(f"Updated {count} conversion probabilities")
    elif args.dashboard:
        dash = get_tower_dashboard()
        print(json.dumps(dash, indent=2))
    elif args.log:
        conv_id = auto_log_completed_request(args.log)
        print(f"Conversion ID: {conv_id}")
    else:
        parser.print_help()
