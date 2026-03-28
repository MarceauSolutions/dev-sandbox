#!/usr/bin/env python3
"""
Hot Lead Handler — Twilio webhook for William's reply-to-action on HOT lead SMS.

When William replies 1/2/3 to a HOT lead SMS, this handler:
  1 = Send Calendly link to the prospect (hands off to personal-assistant)
  2 = Send William the prospect's phone number to call directly
  3 = Mark deal as "Passed" and close

Runs as part of the Twilio webhook (twilio_webhook.py) or standalone.

Inter-Tower Protocol:
  Lead-gen writes: deals.next_action = "send_calendly" | "manual_call" | "passed"
  Personal-assistant reads: deals WHERE next_action = "send_calendly"
                            → sends Calendly link via Gmail API
                            → creates call_brief for meeting prep

Usage:
    # Process a reply from William
    python -m src.hot_lead_handler process --reply "1" --deal-id 42

    # Check for pending handoffs
    python -m src.hot_lead_handler pending
"""

import argparse
import json
import logging
import os
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

PROJECT_ROOT = Path(__file__).parent.parent
REPO_ROOT = PROJECT_ROOT.parent.parent

sys.path.insert(0, str(REPO_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hot_lead_handler")

CALENDLY_LINK = "https://calendly.com/wmarceau/ai-services-discovery"
WILLIAM_PHONE = "+12393985676"


def get_pipeline_db():
    """Import pipeline_db from execution/."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "pipeline_db", REPO_ROOT / "execution" / "pipeline_db.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def handle_william_reply(reply_text: str, deal_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Process William's reply to a HOT lead SMS.

    Args:
        reply_text: "1", "2", or "3"
        deal_id: Pipeline deal ID (if known; otherwise uses most recent hot lead)

    Returns:
        Dict with action taken
    """
    pdb = get_pipeline_db()
    conn = pdb.get_db()

    # Find the deal
    if deal_id:
        deal = pdb.get_deal(conn, deal_id)
    else:
        # Get most recent hot lead
        deal_row = conn.execute(
            "SELECT * FROM deals WHERE stage = 'Hot Response' "
            "ORDER BY updated_at DESC LIMIT 1"
        ).fetchone()
        deal = dict(deal_row) if deal_row else None

    if not deal:
        conn.close()
        return {"success": False, "error": "No hot lead found"}

    reply = reply_text.strip()

    if reply == "1":
        # Schedule via Calendly — hand off to personal-assistant tower
        pdb.update_deal(conn, deal["id"],
                        next_action="send_calendly",
                        stage="Scheduling")
        pdb.log_activity(conn, deal["id"], "human_decision",
                         "William chose: Send Calendly link")

        # Also directly send the Calendly link email if we have the contact email
        email_sent = _send_calendly_email(deal)

        conn.close()
        logger.info(f"Deal {deal['id']} ({deal['company']}): Calendly handoff triggered")
        return {
            "success": True,
            "action": "send_calendly",
            "deal_id": deal["id"],
            "company": deal["company"],
            "email_sent": email_sent,
        }

    elif reply == "2":
        # Manual call — send William the contact's phone
        pdb.update_deal(conn, deal["id"],
                        next_action="manual_call",
                        stage="Call Scheduled")
        pdb.log_activity(conn, deal["id"], "human_decision",
                         "William chose: Call directly")

        # SMS William the contact details
        _send_contact_details_sms(deal)

        conn.close()
        logger.info(f"Deal {deal['id']} ({deal['company']}): Manual call initiated")
        return {
            "success": True,
            "action": "manual_call",
            "deal_id": deal["id"],
            "company": deal["company"],
            "contact_phone": deal.get("contact_phone", ""),
        }

    elif reply == "3":
        # Pass
        pdb.update_deal(conn, deal["id"],
                        next_action=None,
                        stage="Lost")
        pdb.log_activity(conn, deal["id"], "human_decision",
                         "William chose: Pass")
        conn.close()
        logger.info(f"Deal {deal['id']} ({deal['company']}): Passed")
        return {
            "success": True,
            "action": "passed",
            "deal_id": deal["id"],
            "company": deal["company"],
        }

    else:
        conn.close()
        return {"success": False, "error": f"Unknown reply: {reply}"}


def _send_calendly_email(deal: dict) -> bool:
    """Request personal-assistant tower to send Calendly link via tower_protocol.

    Per CLAUDE.md: towers do NOT import from each other directly.
    Lead-gen requests PA to send the email via the protocol layer.
    """
    contact_email = deal.get("contact_email")
    if not contact_email:
        logger.warning(f"No email for deal {deal['id']} -- can't send Calendly link")
        return False

    try:
        sys.path.insert(0, str(REPO_ROOT / "execution"))
        from tower_protocol import request_calendly_email

        request_id = request_calendly_email(
            deal_id=deal["id"],
            contact_email=contact_email,
            company=deal.get("company", ""),
        )
        logger.info(f"Calendly email requested via tower_protocol (request #{request_id}) "
                     f"for deal {deal['id']} -> {contact_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to request Calendly email via protocol: {e}")
        return False


def _send_contact_details_sms(deal: dict) -> bool:
    """Send the prospect's contact details to William's phone."""
    try:
        from twilio.rest import Client
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_PHONE_NUMBER")

        if not all([account_sid, auth_token, from_number]):
            return False

        company = deal.get("company", "")
        contact = deal.get("contact_name", "N/A")
        phone = deal.get("contact_phone", "N/A")
        email = deal.get("contact_email", "N/A")

        body = (
            f"📞 Call now:\n\n"
            f"{company}\n"
            f"Contact: {contact}\n"
            f"Phone: {phone}\n"
            f"Email: {email}"
        )

        client = Client(account_sid, auth_token)
        client.messages.create(body=body, from_=from_number, to=WILLIAM_PHONE)
        return True
    except Exception as e:
        logger.error(f"Contact details SMS failed: {e}")
        return False


def check_pending_handoffs():
    """Show deals waiting for personal-assistant tower to act."""
    pdb = get_pipeline_db()
    conn = pdb.get_db()
    rows = conn.execute(
        "SELECT id, company, contact_name, contact_email, next_action, stage "
        "FROM deals WHERE next_action IS NOT NULL "
        "ORDER BY updated_at DESC"
    ).fetchall()
    conn.close()

    if not rows:
        print("No pending handoffs.")
        return

    print(f"\n📋 Pending Handoffs ({len(rows)}):\n")
    for r in rows:
        print(f"  Deal #{r['id']}: {r['company']}")
        print(f"    Contact: {r['contact_name'] or 'N/A'} | {r['contact_email'] or 'N/A'}")
        print(f"    Action: {r['next_action']} | Stage: {r['stage']}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Hot Lead Handler")
    sub = parser.add_subparsers(dest="command")

    proc = sub.add_parser("process", help="Process William's reply")
    proc.add_argument("--reply", required=True, help="1, 2, or 3")
    proc.add_argument("--deal-id", type=int, help="Deal ID (optional)")

    sub.add_parser("pending", help="Show pending handoffs")

    args = parser.parse_args()

    if args.command == "process":
        result = handle_william_reply(args.reply, args.deal_id)
        print(json.dumps(result, indent=2))
    elif args.command == "pending":
        check_pending_handoffs()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
