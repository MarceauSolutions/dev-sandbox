#!/usr/bin/env python3
"""
Daily Decision Email — Hospital-stay mode fallback.

Sends William a daily email with everything needing his yes/no decision.
Works when Telegram isn't accessible (hospital, travel, no phone).

Combines: decisions queue + goal progress + learning insights + hot leads
into one email at wmarceau@marceausolutions.com.

Called by: cross_tower_sync (once per day at first run after 6am)
          or manually: python -m src.daily_decision_email

Usage:
    python -m src.daily_decision_email              # Send the email
    python -m src.daily_decision_email --preview     # Preview without sending
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

_os_env = os.environ.get("REPO_ROOT")
REPO_ROOT = Path(_os_env) if _os_env else Path(__file__).resolve().parent.parent.parent.parent

sys.path.insert(0, str(REPO_ROOT / "execution"))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("decision_email")

SENT_FILE = REPO_ROOT / "projects" / "personal-assistant" / "logs" / ".last_decision_email"


def should_send_today() -> bool:
    """Check if we've already sent the decision email today."""
    if not SENT_FILE.exists():
        return True
    try:
        last = SENT_FILE.read_text().strip()
        last_date = last[:10]  # YYYY-MM-DD
        return last_date != datetime.now().strftime("%Y-%m-%d")
    except (ValueError, OSError):
        return True


def generate_decision_email() -> dict:
    """Generate the decision email content from pipeline data.

    Returns: {"subject": str, "body": str, "decisions_count": int}
    """
    import importlib.util

    lines = []
    decisions = 0

    lines.append(f"DAILY DECISIONS — {datetime.now().strftime('%A, %B %d')}")
    lines.append(f"{'=' * 50}")
    lines.append("")

    try:
        # Goal progress
        spec = importlib.util.spec_from_file_location(
            "goal_progress", REPO_ROOT / "projects" / "personal-assistant" / "src" / "goal_progress.py"
        )
        gp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gp)
        progress = gp.calculate_goal_progress()
        short = progress.get("short_term", {})
        if short:
            lines.append(f"GOAL: {short.get('goal', '?')}")
            lines.append(f"  Progress: {short.get('overall_pct', 0)}% | {short.get('days_left', '?')} days left")
            lines.append("")
    except Exception as e:
        logger.debug(f"Goal progress failed: {e}")

    try:
        # Pipeline decisions
        spec = importlib.util.spec_from_file_location(
            "pipeline_db", REPO_ROOT / "execution" / "pipeline_db.py"
        )
        pdb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdb)
        conn = pdb.get_db()

        # Trials needing conversion
        trials = conn.execute(
            "SELECT company, contact_name, contact_phone FROM deals "
            "WHERE stage = 'Trial Active'"
        ).fetchall()
        if trials:
            lines.append("CONVERT TRIALS:")
            for r in trials:
                d = dict(r)
                decisions += 1
                lines.append(f"  {decisions}. {d['company']} — {d.get('contact_name', '?')} {d.get('contact_phone', '')}")
                lines.append(f"     Reply: onboard {d['company']}  OR  result {d['company']}: not_interested")
            lines.append("")

        # Stale proposals
        stale = conn.execute(
            "SELECT company, contact_phone, updated_at FROM deals "
            "WHERE stage = 'Proposal Sent' AND updated_at < datetime('now', '-3 days')"
        ).fetchall()
        if stale:
            lines.append("FOLLOW UP PROPOSALS (>3 days):")
            for r in stale:
                d = dict(r)
                decisions += 1
                lines.append(f"  {decisions}. {d['company']} — sent {d['updated_at'][:10]}")
                lines.append(f"     Call {d.get('contact_phone', 'no phone')} to ask for decision")
            lines.append("")

        # Qualified leads to call
        qualified = conn.execute(
            "SELECT company, contact_name, contact_phone FROM deals "
            "WHERE stage = 'Qualified' AND contact_phone IS NOT NULL "
            "ORDER BY updated_at DESC LIMIT 5"
        ).fetchall()
        if qualified:
            decisions += 1
            lines.append(f"  {decisions}. CALL {len(qualified)} QUALIFIED LEADS:")
            for r in qualified:
                d = dict(r)
                lines.append(f"     {d['company']} — {d.get('contact_name', '?')} {d['contact_phone']}")
            lines.append(f"     Use Telegram: 'next' for call prep")
            lines.append("")

        # Recent auto-actions
        recent_outreach = conn.execute(
            "SELECT COUNT(*) FROM outreach_log WHERE created_at > datetime('now', '-1 day')"
        ).fetchone()[0]
        recent_followups = conn.execute(
            "SELECT COUNT(*) FROM outreach_log WHERE created_at > datetime('now', '-1 day') AND channel = 'Email'"
        ).fetchone()[0]

        conn.close()

        lines.append("SYSTEM AUTO-ACTIONS (last 24h):")
        lines.append(f"  Outreach sent: {recent_outreach}")
        lines.append(f"  Follow-up emails: {recent_followups}")
        lines.append("")

    except Exception as e:
        logger.error(f"Pipeline data failed: {e}")
        lines.append(f"Pipeline data unavailable: {e}")

    # Learning insights
    try:
        spec = importlib.util.spec_from_file_location(
            "outcome_learner", REPO_ROOT / "projects" / "personal-assistant" / "src" / "outcome_learner.py"
        )
        ol = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ol)
        insights = ol.get_insights()
        if insights.get("insights"):
            lines.append("LEARNED:")
            for i in insights["insights"][:3]:
                lines.append(f"  {i}")
            lines.append("")
    except Exception:
        pass

    lines.append(f"Total decisions: {decisions}")
    lines.append(f"\nReply to this email with decisions, or use Telegram commands.")
    lines.append(f"Telegram: next | decisions | leads | goal progress")
    lines.append(f"\n— Marceau Solutions Personal Assistant")

    subject = f"[{decisions} decisions] Daily Business Decisions — {datetime.now().strftime('%b %d')}"
    body = "\n".join(lines)

    return {"subject": subject, "body": body, "decisions_count": decisions}


def send_decision_email(preview: bool = False) -> dict:
    """Generate and send the daily decision email."""
    import importlib.util

    email_data = generate_decision_email()

    if preview:
        print(email_data["body"])
        return {"sent": False, "preview": True, **email_data}

    if email_data["decisions_count"] == 0:
        logger.info("No decisions needed today. Skipping email.")
        return {"sent": False, "reason": "no decisions", **email_data}

    try:
        spec = importlib.util.spec_from_file_location(
            "gmail_api", REPO_ROOT / "projects" / "personal-assistant" / "src" / "gmail_api.py"
        )
        gm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gm)

        result = gm.send_email(
            to="wmarceau@marceausolutions.com",
            subject=email_data["subject"],
            body=email_data["body"],
        )

        if result.get("success"):
            SENT_FILE.parent.mkdir(parents=True, exist_ok=True)
            SENT_FILE.write_text(datetime.now().isoformat())
            logger.info(f"Decision email sent: {email_data['decisions_count']} decisions")
            return {"sent": True, **email_data}
        else:
            return {"sent": False, "error": result.get("error"), **email_data}

    except Exception as e:
        return {"sent": False, "error": str(e), **email_data}


def main():
    parser = argparse.ArgumentParser(description="Daily Decision Email")
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    result = send_decision_email(preview=args.preview)
    if not args.preview:
        print(json.dumps({k: v for k, v in result.items() if k != "body"}, indent=2))


if __name__ == "__main__":
    main()
