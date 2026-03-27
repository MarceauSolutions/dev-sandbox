"""
Lead Generation Sales Pipeline API - Tower-specific pipeline operations.

Extracted from monolithic agent_bridge_api.py to restore tower independence.
Delegates to execution/pipeline_db.py for database operations (shared utility).
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent.parent.parent / ".env")
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_pipeline_db():
    """Import and return pipeline_db module from execution/ (shared utility)."""
    import importlib.util
    root = Path(__file__).resolve().parent.parent.parent.parent / "execution"
    spec = importlib.util.spec_from_file_location("pipeline_db", root / "pipeline_db.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def get_stats(tower: Optional[str] = None) -> Dict[str, Any]:
    """
    Get pipeline stats for a tower or all towers.

    Args:
        tower: Tower name filter (e.g. 'digital-ai-services'), or None for all

    Returns:
        Dict with pipeline statistics
    """
    try:
        pdb = _get_pipeline_db()
        conn = pdb.get_db()
        if tower:
            stats = pdb.get_pipeline_stats(conn, tower=tower)
        else:
            stats = pdb.get_tower_summary(conn)
        conn.close()
        return {"ok": True, "data": stats}
    except Exception as e:
        logger.error(f"Failed to get pipeline stats: {e}")
        return {"ok": False, "error": str(e)}


def list_deals(tower: Optional[str] = None, stage: Optional[str] = None) -> Dict[str, Any]:
    """
    List deals filtered by tower and/or stage.

    Args:
        tower: Tower name filter
        stage: Stage filter (e.g. 'Trial Active')

    Returns:
        Dict with deal list
    """
    try:
        pdb = _get_pipeline_db()
        conn = pdb.get_db()
        q = "SELECT * FROM deals WHERE 1=1"
        params = []
        if tower:
            q += " AND tower = ?"
            params.append(tower)
        if stage:
            q += " AND stage = ?"
            params.append(stage)
        q += " ORDER BY updated_at DESC LIMIT 50"
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return {"ok": True, "deals": [dict(r) for r in rows], "count": len(rows)}
    except Exception as e:
        logger.error(f"Failed to list deals: {e}")
        return {"ok": False, "error": str(e)}


def add_deal(company: str, tower: str = "digital-ai-services", **fields) -> Dict[str, Any]:
    """
    Create a new deal in the pipeline.

    Args:
        company: Company name (required)
        tower: Tower name
        **fields: contact_name, contact_email, contact_phone, industry, stage, lead_source, notes

    Returns:
        Dict with created deal info
    """
    if not company.strip():
        return {"ok": False, "error": "company required"}
    try:
        pdb = _get_pipeline_db()
        conn = pdb.get_db()
        deal_id = pdb.create_deal(conn, company.strip(), tower=tower, **fields)
        conn.close()
        return {"ok": True, "deal_id": deal_id, "company": company.strip(), "tower": tower}
    except Exception as e:
        logger.error(f"Failed to add deal: {e}")
        return {"ok": False, "error": str(e)}


def update_deal(deal_id: int, **fields) -> Dict[str, Any]:
    """
    Update a deal's stage or fields.

    Args:
        deal_id: Deal ID
        **fields: stage, next_action, notes, etc.

    Returns:
        Dict with update status
    """
    try:
        pdb = _get_pipeline_db()
        conn = pdb.get_db()
        pdb.update_deal(conn, int(deal_id), **fields)
        conn.close()
        return {"ok": True, "deal_id": deal_id, "updated": list(fields.keys())}
    except Exception as e:
        logger.error(f"Failed to update deal: {e}")
        return {"ok": False, "error": str(e)}


def log_outreach(company: str = "", channel: str = "Email", message: str = "",
                 response: str = "", follow_up_date: Optional[str] = None,
                 deal_id: Optional[int] = None, tower: str = "digital-ai-services",
                 lead_source: str = "") -> Dict[str, Any]:
    """
    Log an outreach attempt. Auto-moves deal to 'Outreached' if deal_id provided.

    Args:
        company: Company name
        channel: Outreach channel (Email, SMS, Phone, etc.)
        message: Message content
        response: Response received
        follow_up_date: Follow-up date (YYYY-MM-DD)
        deal_id: Associated deal ID
        tower: Tower name
        lead_source: Lead source

    Returns:
        Dict with log status
    """
    try:
        pdb = _get_pipeline_db()
        conn = pdb.get_db()
        log_id = pdb.log_outreach(
            conn, company=company, channel=channel, message=message,
            response=response, follow_up_date=follow_up_date,
            deal_id=deal_id, tower=tower, lead_source=lead_source,
        )
        if deal_id:
            deal = pdb.get_deal(conn, deal_id)
            if deal and deal["stage"] == "Prospect":
                pdb.update_deal(conn, deal_id, stage="Outreached")
        conn.close()
        return {"ok": True, "log_id": log_id}
    except Exception as e:
        logger.error(f"Failed to log outreach: {e}")
        return {"ok": False, "error": str(e)}


def log_trial_day(deal_id: int, missed_calls: int = 0, texts_sent: int = 0,
                  replies: int = 0, calls_recovered: int = 0,
                  revenue_recovered: float = 0.0, notes: str = "") -> Dict[str, Any]:
    """
    Log one day of trial client performance.

    Args:
        deal_id: Deal ID
        missed_calls: Number of missed calls
        texts_sent: Number of texts sent
        replies: Number of replies received
        calls_recovered: Calls recovered
        revenue_recovered: Revenue recovered ($)
        notes: Daily notes

    Returns:
        Dict with metric ID
    """
    try:
        pdb = _get_pipeline_db()
        conn = pdb.get_db()
        metric_id = pdb.log_trial_day(
            conn, int(deal_id),
            missed_calls=missed_calls, texts_sent=texts_sent,
            replies=replies, calls_recovered=calls_recovered,
            revenue_recovered=float(revenue_recovered), notes=notes,
        )
        conn.close()
        return {"ok": True, "metric_id": metric_id}
    except Exception as e:
        logger.error(f"Failed to log trial day: {e}")
        return {"ok": False, "error": str(e)}


def get_trial_summary(deal_id: int) -> Dict[str, Any]:
    """
    Get aggregated trial metrics for Day 10/14 check-in reports.

    Args:
        deal_id: Deal ID

    Returns:
        Dict with trial summary
    """
    try:
        pdb = _get_pipeline_db()
        conn = pdb.get_db()
        summary = pdb.get_trial_summary(conn, int(deal_id))
        conn.close()
        return {"ok": True, "summary": summary}
    except Exception as e:
        logger.error(f"Failed to get trial summary: {e}")
        return {"ok": False, "error": str(e)}


def get_followups_due(tower: Optional[str] = None) -> Dict[str, Any]:
    """
    Get outreach records past follow_up_date with no response.

    Args:
        tower: Tower name filter

    Returns:
        Dict with follow-up list
    """
    try:
        pdb = _get_pipeline_db()
        conn = pdb.get_db()
        q = """
            SELECT o.*, d.company as deal_company, d.stage, d.contact_name
            FROM outreach_log o LEFT JOIN deals d ON o.deal_id = d.id
            WHERE o.follow_up_date <= date('now')
              AND (o.response IS NULL OR o.response = '')
        """
        params = []
        if tower:
            q += " AND o.tower = ?"
            params.append(tower)
        q += " ORDER BY o.follow_up_date ASC LIMIT 30"
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return {"ok": True, "followups": [dict(r) for r in rows], "count": len(rows)}
    except Exception as e:
        logger.error(f"Failed to get followups: {e}")
        return {"ok": False, "error": str(e)}


def get_tower_capabilities() -> Dict[str, Any]:
    """Return tower capabilities for pipeline operations."""
    return {
        "name": "lead-generation-pipeline",
        "description": "Sales pipeline management for lead tracking and outreach",
        "functions": [
            "get_stats", "list_deals", "add_deal", "update_deal",
            "log_outreach", "log_trial_day", "get_trial_summary", "get_followups_due"
        ],
        "protocols": ["direct_import", "api"]
    }
