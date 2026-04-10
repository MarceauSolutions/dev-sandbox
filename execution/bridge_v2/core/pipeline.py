"""Pipeline operations blueprint — deal management, pipeline queries."""

import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import Blueprint, jsonify, request
from execution.bridge_v2.app import (
    ErrorCode, make_error, make_success, track_request,
)

pipeline_bp = Blueprint('pipeline', __name__)

# Pipeline database path
DB_PATHS = [
    Path("/home/clawdbot/dev-sandbox/data/pipeline.db"),
    Path("/home/ec2-user/dev-sandbox/data/pipeline.db"),
    Path("/Users/williammarceaujr./dev-sandbox/data/pipeline.db"),
    Path("/home/clawdbot/dev-sandbox/execution/pipeline.db"),
    Path("/home/ec2-user/dev-sandbox/execution/pipeline.db"),
]


def _get_db() -> Optional[sqlite3.Connection]:
    """Get pipeline database connection."""
    for db_path in DB_PATHS:
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            return conn
    return None


def _ensure_deals_table(conn: sqlite3.Connection):
    """Create deals table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            stage TEXT DEFAULT 'New',
            source TEXT DEFAULT 'manual',
            industry TEXT,
            notes TEXT,
            value REAL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


@pipeline_bp.route('/pipeline/deal/add', methods=['POST'])
def deal_add():
    """Add or update a deal in the pipeline."""
    track_request('pipeline/deal/add')
    data = request.get_json() or {}

    business_name = data.get('business_name')
    if not business_name:
        return make_error(ErrorCode.MISSING_PARAMETER, "Missing 'business_name'")

    conn = _get_db()
    if not conn:
        return make_error(ErrorCode.INTERNAL_ERROR, "Pipeline database not found", 500)

    try:
        _ensure_deals_table(conn)

        # Check if deal already exists (upsert by business_name)
        existing = conn.execute(
            "SELECT id FROM deals WHERE business_name = ?", (business_name,)
        ).fetchone()

        if existing:
            # Update
            fields = []
            values = []
            for key in ('email', 'phone', 'stage', 'source', 'industry', 'notes', 'value'):
                if key in data:
                    fields.append(f"{key} = ?")
                    values.append(data[key])
            fields.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(existing['id'])

            conn.execute(f"UPDATE deals SET {', '.join(fields)} WHERE id = ?", values)
            conn.commit()
            conn.close()
            return make_success({"deal_id": existing['id'], "action": "updated", "business_name": business_name})
        else:
            # Insert
            conn.execute(
                """INSERT INTO deals (business_name, email, phone, stage, source, industry, notes, value)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    business_name,
                    data.get('email', ''),
                    data.get('phone', ''),
                    data.get('stage', 'New'),
                    data.get('source', 'manual'),
                    data.get('industry', ''),
                    data.get('notes', ''),
                    data.get('value', 0),
                )
            )
            deal_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.commit()
            conn.close()
            return make_success({"deal_id": deal_id, "action": "created", "business_name": business_name})

    except Exception as e:
        conn.close()
        return make_error(ErrorCode.INTERNAL_ERROR, f"Pipeline error: {e}", 500)


@pipeline_bp.route('/pipeline/stats', methods=['GET'])
def pipeline_stats():
    """Get pipeline summary stats."""
    track_request('pipeline/stats')
    conn = _get_db()
    if not conn:
        return make_error(ErrorCode.INTERNAL_ERROR, "Pipeline database not found", 500)

    try:
        _ensure_deals_table(conn)
        stages = conn.execute(
            "SELECT stage, COUNT(*) as count FROM deals GROUP BY stage ORDER BY count DESC"
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM deals").fetchone()[0]
        total_value = conn.execute("SELECT COALESCE(SUM(value), 0) FROM deals").fetchone()[0]
        conn.close()

        return make_success({
            "total_deals": total,
            "total_value": total_value,
            "by_stage": {r['stage']: r['count'] for r in stages},
        })
    except Exception as e:
        conn.close()
        return make_error(ErrorCode.INTERNAL_ERROR, f"Pipeline error: {e}", 500)


@pipeline_bp.route('/pipeline/summary', methods=['GET'])
def pipeline_summary():
    """Get pipeline summary for Grok/strategic layer."""
    track_request('pipeline/summary')
    conn = _get_db()
    if not conn:
        return make_error(ErrorCode.INTERNAL_ERROR, "Pipeline database not found", 500)

    try:
        _ensure_deals_table(conn)
        total = conn.execute("SELECT COUNT(*) FROM deals").fetchone()[0]
        hot = conn.execute("SELECT COUNT(*) FROM deals WHERE stage = 'Hot Response'").fetchone()[0]
        stages = conn.execute(
            "SELECT stage, COUNT(*) as count FROM deals GROUP BY stage"
        ).fetchall()
        recent = conn.execute(
            "SELECT business_name, stage, updated_at FROM deals ORDER BY updated_at DESC LIMIT 5"
        ).fetchall()
        conn.close()

        return make_success({
            "total_deals": total,
            "hot_leads": hot,
            "by_stage": {r['stage']: r['count'] for r in stages},
            "recent": [{"name": r['business_name'], "stage": r['stage'], "updated": r['updated_at']} for r in recent],
        })
    except Exception as e:
        conn.close()
        return make_error(ErrorCode.INTERNAL_ERROR, f"Pipeline error: {e}", 500)


@pipeline_bp.route('/pipeline/deals', methods=['GET'])
def pipeline_deals():
    """List all deals."""
    track_request('pipeline/deals')
    conn = _get_db()
    if not conn:
        return make_error(ErrorCode.INTERNAL_ERROR, "Pipeline database not found", 500)

    try:
        _ensure_deals_table(conn)
        deals = conn.execute("SELECT * FROM deals ORDER BY updated_at DESC").fetchall()
        conn.close()
        return make_success({"deals": [dict(d) for d in deals]})
    except Exception as e:
        conn.close()
        return make_error(ErrorCode.INTERNAL_ERROR, f"Pipeline error: {e}", 500)


@pipeline_bp.route('/pipeline/followups', methods=['GET'])
def pipeline_followups():
    """Get deals needing follow-up."""
    track_request('pipeline/followups')
    conn = _get_db()
    if not conn:
        return make_error(ErrorCode.INTERNAL_ERROR, "Pipeline database not found", 500)

    try:
        _ensure_deals_table(conn)
        deals = conn.execute(
            "SELECT * FROM deals WHERE stage NOT IN ('Won', 'Lost', 'Dead') ORDER BY updated_at ASC"
        ).fetchall()
        conn.close()
        return make_success({"followups": [dict(d) for d in deals]})
    except Exception as e:
        conn.close()
        return make_error(ErrorCode.INTERNAL_ERROR, f"Pipeline error: {e}", 500)
