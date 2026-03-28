#!/usr/bin/env python3
"""
Personal-Assistant Tower Handler -- Processes cross-tower requests via tower_protocol.

Polls tower_requests table for pending requests addressed to personal-assistant,
then executes them (e.g., send Calendly email, generate meeting prep).

This gives the PA tower WRITE-BACK capability: other towers can request
the PA to perform actions on their behalf, completing the coordination loop.

Called by: launchd (future), or daily_loop, or app.py endpoint.

Actions handled:
  - send_calendly_email: Send Calendly discovery call link to a prospect
  - generate_meeting_prep: Create call brief for an upcoming meeting
  - send_notification_email: Send a branded notification email
  - update_goal_progress: Refresh goal progress from pipeline data

Usage:
    python -m src.tower_handler process          # Process pending requests
    python -m src.tower_handler process --dry-run # Preview only
    python -m src.tower_handler pending           # Show pending requests
    python -m src.tower_handler status            # Show all tower request stats
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

sys.path.insert(0, str(REPO_ROOT / "execution"))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pa_tower_handler")

CALENDLY_LINK = "https://calendly.com/wmarceau/ai-services-discovery"


def process_pending(dry_run: bool = False) -> Dict[str, Any]:
    """Process all pending tower_requests for personal-assistant."""
    from tower_protocol import check_pending, claim_request, complete_action, fail_action

    pending = check_pending("personal-assistant")
    if not pending:
        logger.info("No pending requests for personal-assistant")
        return {"processed": 0, "total_pending": 0}

    processed = 0
    errors = []
    for req in pending:
        action = req["action"]
        payload = json.loads(req["payload"]) if isinstance(req["payload"], str) else req["payload"]
        req_id = req["id"]

        logger.info(f"Processing request #{req_id}: {action} from {req['from_tower']}")

        if dry_run:
            logger.info(f"  [DRY RUN] Would process: {action} with {payload}")
            processed += 1
            continue

        claim_request(req_id)

        try:
            if action == "send_calendly_email":
                result = _send_calendly_email(payload)
            elif action == "generate_meeting_prep":
                result = _generate_meeting_prep(payload)
            elif action == "send_notification_email":
                result = _send_notification_email(payload)
            elif action == "update_goal_progress":
                result = _update_goal_progress(payload)
            else:
                result = {"error": f"Unknown action: {action}"}

            if "error" in result:
                fail_action(req_id, result["error"])
                errors.append(f"#{req_id}: {result['error']}")
            else:
                complete_action(req_id, result)
                processed += 1

        except Exception as e:
            fail_action(req_id, str(e))
            errors.append(f"#{req_id}: {e}")

    return {"processed": processed, "total_pending": len(pending), "errors": errors}


def _send_calendly_email(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Send Calendly discovery call link to a prospect via Gmail API."""
    contact_email = payload.get("contact_email")
    company = payload.get("company", "")
    deal_id = payload.get("deal_id")

    if not contact_email:
        return {"error": "No contact_email in payload"}

    try:
        from . import gmail_api

        contact_name = payload.get("contact_name", "").split()[0] if payload.get("contact_name") else ""
        greeting = f"Hi {contact_name}" if contact_name else "Hi"

        subject = f"Let's find a time to chat -- {company}" if company else "Let's find a time to chat"
        body = (
            f"{greeting},\n\n"
            f"Thanks for your interest! I'd love to learn more about {company} "
            f"and see if there's a fit.\n\n"
            f"Here's my calendar -- grab any time that works for you:\n"
            f"{CALENDLY_LINK}\n\n"
            f"Looking forward to it.\n\n"
            f"William Marceau\n"
            f"Marceau Solutions\n"
            f"wmarceau@marceausolutions.com"
        )

        result = gmail_api.send_email(to=contact_email, subject=subject, body=body)
        if result.get("success"):
            logger.info(f"Calendly email sent to {contact_email} for deal #{deal_id}")
            return {"deal_id": deal_id, "email_sent": True, "to": contact_email}
        else:
            return {"error": f"Email send failed: {result.get('error')}"}

    except Exception as e:
        return {"error": f"Calendly email failed: {e}"}


def _generate_meeting_prep(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a call brief / meeting prep packet for a deal.

    Writes to pipeline.db call_briefs table so the morning digest can show prep notes.
    """
    deal_id = payload.get("deal_id")
    company = payload.get("company", "")

    if not deal_id:
        return {"error": "No deal_id in payload"}

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "pipeline_db", REPO_ROOT / "execution" / "pipeline_db.py"
        )
        pdb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdb)
        conn = pdb.get_db()

        # Get the deal info
        deal = conn.execute(
            "SELECT * FROM deals WHERE id = ?", (deal_id,)
        ).fetchone()

        if not deal:
            conn.close()
            return {"error": f"Deal #{deal_id} not found"}

        deal = dict(deal)
        industry = deal.get("industry", "general business")
        contact = deal.get("contact_name", "the owner")

        # Build a simple but useful call brief
        talking_points = (
            f"Discovery call with {contact} at {company} ({industry}).\n\n"
            f"Key talking points:\n"
            f"- Ask about their biggest operational pain point\n"
            f"- How they currently handle [customer inquiries / scheduling / follow-ups]\n"
            f"- What does a successful outcome look like for them?\n"
            f"- Budget range and timeline for implementation\n\n"
            f"Marceau Solutions value prop for {industry}:\n"
            f"- AI-powered customer service (24/7 response, no missed calls)\n"
            f"- Automated follow-ups (SMS + email sequences)\n"
            f"- Website + booking optimization\n\n"
            f"Close: Propose a small pilot ($497/mo) with measurable ROI in 30 days."
        )

        # Insert or update call_brief
        conn.execute("""
            INSERT INTO call_briefs (deal_id, company, talking_points, created_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(deal_id) DO UPDATE SET
                talking_points = excluded.talking_points,
                created_at = datetime('now')
        """, (deal_id, company, talking_points))
        conn.commit()
        conn.close()

        logger.info(f"Meeting prep created for deal #{deal_id} ({company})")
        return {"deal_id": deal_id, "company": company, "brief_created": True}

    except Exception as e:
        return {"error": f"Meeting prep failed: {e}"}


def _send_notification_email(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Send a notification email (generic action for any tower)."""
    to = payload.get("to")
    subject = payload.get("subject", "Notification from Marceau Solutions")
    body = payload.get("body", "")

    if not to or not body:
        return {"error": "to and body required in payload"}

    try:
        from . import gmail_api
        result = gmail_api.send_email(to=to, subject=subject, body=body)
        if result.get("success"):
            return {"sent": True, "to": to}
        else:
            return {"error": f"Send failed: {result.get('error')}"}
    except Exception as e:
        return {"error": f"Notification email failed: {e}"}


def _update_goal_progress(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Refresh goal progress by checking pipeline.db for real metrics."""
    try:
        from .goal_progress import calculate_goal_progress
        progress = calculate_goal_progress()
        return {"progress": progress, "updated": True}
    except Exception as e:
        return {"error": f"Goal progress update failed: {e}"}


def get_all_tower_stats() -> Dict[str, Any]:
    """Get request statistics across all towers (for cross-tower visibility)."""
    from tower_protocol import _get_db

    conn = _get_db()
    stats = {}

    # Requests by tower
    for row in conn.execute(
        "SELECT to_tower, status, COUNT(*) as cnt "
        "FROM tower_requests GROUP BY to_tower, status"
    ).fetchall():
        tower = row["to_tower"]
        if tower not in stats:
            stats[tower] = {}
        stats[tower][row["status"]] = row["cnt"]

    # Recent activity (last 24h)
    recent = conn.execute(
        "SELECT COUNT(*) FROM tower_requests "
        "WHERE created_at > datetime('now', '-1 day')"
    ).fetchone()[0]

    # Failed requests needing attention
    failed = conn.execute(
        "SELECT id, from_tower, to_tower, action, result "
        "FROM tower_requests WHERE status = 'failed' "
        "ORDER BY created_at DESC LIMIT 5"
    ).fetchall()

    conn.close()

    return {
        "tower_stats": stats,
        "recent_24h": recent,
        "recent_failures": [dict(r) for r in failed],
    }


def show_pending():
    """Show pending requests for personal-assistant."""
    from tower_protocol import check_pending
    pending = check_pending("personal-assistant")
    if not pending:
        print("No pending requests.")
        return
    print(f"\nPending requests ({len(pending)}):")
    for r in pending:
        payload = json.loads(r["payload"]) if isinstance(r["payload"], str) else r["payload"]
        print(f"  #{r['id']}: {r['action']} from {r['from_tower']} -- {payload}")


def main():
    parser = argparse.ArgumentParser(description="Personal-Assistant Tower Handler")
    sub = parser.add_subparsers(dest="command")
    proc = sub.add_parser("process", help="Process pending requests")
    proc.add_argument("--dry-run", action="store_true")
    sub.add_parser("pending", help="Show pending requests")
    sub.add_parser("status", help="Show all tower request stats")
    args = parser.parse_args()

    if args.command == "process":
        result = process_pending(dry_run=args.dry_run)
        print(json.dumps(result, indent=2))
    elif args.command == "pending":
        show_pending()
    elif args.command == "status":
        stats = get_all_tower_stats()
        print(json.dumps(stats, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
