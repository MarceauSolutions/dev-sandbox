#!/usr/bin/env python3
"""
Unified Morning Digest — All towers → one Telegram message at 6:30am

Pulls data from:
  1. Gmail (unread count + priority emails)
  2. Google Calendar (today's events)
  3. Pipeline DB (lead-gen status, hot leads, pending actions)
  4. SMS replies (Twilio inbox)
  5. Calendly (upcoming bookings)

Sends a single formatted Telegram message to William at 6:30am ET.
Designed to be the first thing he reads before his 7am work shift.

Usage:
    python -m src.unified_morning_digest                # Send digest
    python -m src.unified_morning_digest --preview      # Preview without sending
    python -m src.unified_morning_digest --hours 12     # Custom lookback
"""

import argparse
import json
import logging
import os
import sys
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("morning_digest")


# ---------------------------------------------------------------------------
# Data collection functions
# ---------------------------------------------------------------------------

def get_pipeline_summary() -> Dict[str, Any]:
    """Pull lead-gen pipeline status from shared pipeline.db."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "pipeline_db", REPO_ROOT / "execution" / "pipeline_db.py"
        )
        pdb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdb)
        conn = pdb.get_db()

        # Stage distribution
        stages = conn.execute(
            "SELECT stage, COUNT(*) as cnt FROM deals "
            "WHERE stage NOT IN ('Lost', 'Opted Out') "
            "GROUP BY stage ORDER BY cnt DESC"
        ).fetchall()

        # Hot leads needing attention
        hot = conn.execute(
            "SELECT company, contact_name, next_action FROM deals "
            "WHERE stage = 'Hot Response'"
        ).fetchall()

        # Yesterday's activity
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")
        recent_activities = conn.execute(
            "SELECT activity_type, COUNT(*) as cnt FROM activities "
            "WHERE date(created_at) >= ? GROUP BY activity_type",
            (yesterday,)
        ).fetchall()

        # Recent outreach count
        recent_outreach = conn.execute(
            "SELECT COUNT(*) as cnt FROM outreach_log "
            "WHERE date(created_at) >= ?", (yesterday,)
        ).fetchone()

        # Upcoming follow-ups
        followups = conn.execute(
            "SELECT COUNT(*) as cnt FROM outreach_log "
            "WHERE follow_up_date = ? AND (response IS NULL OR response = '')",
            (today,)
        ).fetchone()

        # Pending proposals
        proposals = conn.execute(
            "SELECT d.company, p.status FROM proposals p "
            "JOIN deals d ON p.deal_id = d.id "
            "WHERE p.status IN ('draft', 'sent')"
        ).fetchall()

        conn.close()

        return {
            "stages": {r["stage"]: r["cnt"] for r in stages},
            "hot_leads": [dict(r) for r in hot],
            "activities": {r["activity_type"]: r["cnt"] for r in recent_activities},
            "recent_outreach": recent_outreach["cnt"] if recent_outreach else 0,
            "followups_today": followups["cnt"] if followups else 0,
            "proposals": [dict(r) for r in proposals],
        }
    except Exception as e:
        logger.warning(f"Pipeline data unavailable: {e}")
        return {}


def get_email_summary(hours_back: int = 12) -> Dict[str, Any]:
    """Get email summary from Gmail API."""
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from gmail_api import list_emails

        result = list_emails(max_results=20, query=f"is:unread newer_than:{hours_back}h")
        if not result.get("success"):
            return {"total": 0, "priority": []}

        emails = result.get("emails", [])
        priority = []
        for e in emails:
            subj = e.get("subject", "")
            sender = e.get("from", "")
            # Flag priority emails
            is_priority = any(kw in subj.lower() for kw in [
                "invoice", "payment", "calendly", "booking", "urgent",
                "interested", "proposal", "contract", "stripe",
            ]) or any(kw in sender.lower() for kw in [
                "stripe", "calendly", "client", "customer",
            ])
            if is_priority:
                priority.append({"subject": subj[:60], "from": sender.split("<")[0].strip()})

        return {"total": len(emails), "priority": priority[:5]}
    except Exception as e:
        logger.warning(f"Email summary unavailable: {e}")
        return {"total": 0, "priority": []}


def get_calendar_today() -> List[Dict]:
    """Get today's calendar events."""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        token_path = REPO_ROOT / "token.json"
        if not token_path.exists():
            return []

        creds = Credentials.from_authorized_user_file(str(token_path))
        service = build("calendar", "v3", credentials=creds)

        now = datetime.now(tz=None)
        start = now.replace(hour=0, minute=0, second=0).isoformat() + "Z"
        end = now.replace(hour=23, minute=59, second=59).isoformat() + "Z"

        events_result = service.events().list(
            calendarId="primary", timeMin=start, timeMax=end,
            maxResults=10, singleEvents=True, orderBy="startTime"
        ).execute()

        events = []
        for event in events_result.get("items", []):
            start_time = event.get("start", {}).get("dateTime", event.get("start", {}).get("date", ""))
            time_str = ""
            if "T" in start_time:
                try:
                    dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    time_str = dt.strftime("%I:%M %p")
                except Exception:
                    time_str = start_time
            else:
                time_str = "All day"

            events.append({
                "time": time_str,
                "summary": event.get("summary", "No title"),
                "location": event.get("location", ""),
            })
        return events
    except Exception as e:
        logger.warning(f"Calendar unavailable: {e}")
        return []


def get_sms_replies(hours_back: int = 12) -> Dict[str, Any]:
    """Check Twilio inbox for recent replies."""
    try:
        from twilio.rest import Client
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

        if not all([account_sid, auth_token, twilio_number]):
            return {"total": 0}

        client = Client(account_sid, auth_token)
        cutoff = datetime.now(tz=None) - timedelta(hours=hours_back)
        messages = client.messages.list(
            to=twilio_number, date_sent_after=cutoff, limit=20
        )

        hot = []
        total = len(messages)
        for m in messages:
            body_lower = m.body.lower() if m.body else ""
            if any(kw in body_lower for kw in ["interested", "yes", "tell me more", "let's talk", "schedule"]):
                hot.append({"from": m.from_, "body": m.body[:80]})

        return {"total": total, "hot": hot}
    except Exception as e:
        logger.warning(f"SMS check unavailable: {e}")
        return {"total": 0}


# ---------------------------------------------------------------------------
# Digest formatting
# ---------------------------------------------------------------------------

def format_telegram_digest(
    pipeline: Dict, emails: Dict, calendar: List, sms: Dict, hours_back: int,
    health_line: str = ""
) -> str:
    """Format all data into one clean Telegram message."""
    today = datetime.now().strftime("%A, %B %d")
    lines = [f"☀️ *MORNING DIGEST — {today}*\n"]

    # System health (at top so issues are immediately visible)
    if health_line:
        lines.append(health_line)
        lines.append("")

    # --- Pipeline Status ---
    if pipeline:
        hot = pipeline.get("hot_leads", [])
        stages = pipeline.get("stages", {})
        outreach = pipeline.get("recent_outreach", 0)
        followups = pipeline.get("followups_today", 0)

        lines.append("📊 *PIPELINE*")
        if stages:
            stage_parts = [f"{cnt} {stage}" for stage, cnt in stages.items()]
            lines.append(f"  {' → '.join(stage_parts)}")
        if outreach:
            lines.append(f"  Outreached (24h): {outreach}")
        if followups:
            lines.append(f"  Auto follow-ups today: {followups}")

        if hot:
            lines.append(f"\n🔥 *HOT LEADS ({len(hot)})*")
            for h in hot:
                company = h.get("company", "Unknown")
                contact = h.get("contact_name", "")
                action = h.get("next_action", "")
                lines.append(f"  • {company}"
                             f"{' — ' + contact if contact else ''}"
                             f"{' [' + action + ']' if action else ''}")

        proposals = pipeline.get("proposals", [])
        if proposals:
            lines.append(f"\n📋 *PROPOSALS ({len(proposals)})*")
            for p in proposals:
                lines.append(f"  • {p.get('company', '?')} — {p.get('status', '?')}")

        lines.append("")

    # --- Email ---
    email_total = emails.get("total", 0)
    priority = emails.get("priority", [])
    lines.append(f"📧 *EMAIL* ({email_total} unread)")
    if priority:
        for e in priority[:3]:
            lines.append(f"  ⭐ {e['from']}: {e['subject']}")
    elif email_total == 0:
        lines.append("  No new emails")
    lines.append("")

    # --- Calendar (with Calendly booking detection) ---
    # Flag discovery calls / Calendly bookings
    calls = []
    other_events = []
    for ev in calendar:
        summary = ev.get("summary", "").lower()
        if any(kw in summary for kw in ["discovery", "calendly", "call with", "meeting with", "consultation", "ai services"]):
            calls.append(ev)
        else:
            other_events.append(ev)

    if calls:
        lines.append(f"📞 *CALLS TODAY ({len(calls)})*")
        for c in calls:
            loc = f" 📍{c['location']}" if c.get("location") else ""
            lines.append(f"  • {c['time']}: {c['summary']}{loc}")
            # Look up prep packet in pipeline.db call_briefs
            _add_prep_note(lines, c, pipeline)
        lines.append("")

    lines.append(f"📅 *TODAY* ({len(calendar)} events)")
    if calendar:
        for ev in calendar:
            loc = f" 📍{ev['location']}" if ev.get("location") else ""
            lines.append(f"  • {ev['time']}: {ev['summary']}{loc}")
    else:
        lines.append("  No events scheduled")
    lines.append("")

    # --- SMS ---
    sms_total = sms.get("total", 0)
    sms_hot = sms.get("hot", [])
    if sms_total > 0:
        lines.append(f"📱 *SMS* ({sms_total} replies)")
        for h in sms_hot[:3]:
            lines.append(f"  🔥 {h['from']}: \"{h['body']}\"")
        lines.append("")

    # --- Action Items ---
    actions = _generate_action_items(pipeline, emails, calendar, sms)
    if actions:
        lines.append("✅ *ACTION ITEMS*")
        for a in actions:
            lines.append(f"  {a}")
        lines.append("")

    # Footer
    lines.append(f"_Generated {datetime.now().strftime('%I:%M %p')} | {hours_back}h lookback_")

    return "\n".join(lines)


def _add_prep_note(lines: List[str], event: Dict, pipeline: Dict):
    """Add meeting prep note if we have a call brief for this deal."""
    if not pipeline:
        return
    # Try to match event summary to a deal company name
    summary = event.get("summary", "")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "pipeline_db", REPO_ROOT / "execution" / "pipeline_db.py"
        )
        pdb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdb)
        conn = pdb.get_db()
        # Check for call briefs created in last 7 days
        brief = conn.execute(
            "SELECT cb.talking_points, cb.pain_points, d.company "
            "FROM call_briefs cb JOIN deals d ON cb.deal_id = d.id "
            "WHERE cb.created_at > datetime('now', '-7 days') "
            "ORDER BY cb.created_at DESC LIMIT 1"
        ).fetchone()
        conn.close()
        if brief:
            lines.append(f"    📝 Prep: {brief['talking_points'][:80]}..." if brief['talking_points'] else "")
    except Exception:
        pass


def _generate_action_items(pipeline: Dict, emails: Dict, calendar: List, sms: Dict) -> List[str]:
    """Auto-generate prioritized action items."""
    items = []

    # Hot leads are #1 priority
    hot = pipeline.get("hot_leads", []) if pipeline else []
    if hot:
        items.append(f"🔥 {len(hot)} hot lead(s) awaiting response — check SMS alerts")

    # Proposals pending
    proposals = pipeline.get("proposals", []) if pipeline else []
    drafts = [p for p in proposals if p.get("status") == "draft"]
    if drafts:
        items.append(f"📋 {len(drafts)} proposal draft(s) need pricing review")

    # Priority emails
    priority = emails.get("priority", [])
    if priority:
        items.append(f"📧 {len(priority)} priority email(s) to review")

    # Calls today
    calls = [ev for ev in calendar if any(kw in ev.get("summary", "").lower()
             for kw in ["call", "meeting", "discovery", "chat"])]
    if calls:
        items.append(f"📞 {len(calls)} call(s) today — check prep packets")

    # Follow-ups
    followups = pipeline.get("followups_today", 0) if pipeline else 0
    if followups:
        items.append(f"📤 {followups} auto follow-ups scheduled (no action needed)")

    return items


# ---------------------------------------------------------------------------
# Delivery
# ---------------------------------------------------------------------------

def send_telegram(message: str) -> bool:
    """Send to William via Telegram."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "5692454753")
    if not bot_token:
        logger.warning("No TELEGRAM_BOT_TOKEN — cannot send")
        return False
    try:
        data = json.dumps({
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown",
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data=data, headers={"Content-Type": "application/json"}, method="POST",
        )
        urllib.request.urlopen(req, timeout=15)
        logger.info("Telegram digest sent")
        return True
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_digest(hours_back: int = 12, preview: bool = False) -> str:
    """Generate and optionally send the unified morning digest."""
    logger.info(f"Generating morning digest ({hours_back}h lookback)...")

    # Collect data from all sources
    pipeline = get_pipeline_summary()
    emails = get_email_summary(hours_back)
    calendar = get_calendar_today()
    sms = get_sms_replies(hours_back)

    # System health check
    health_line = ""
    try:
        from .system_health_check import run_all_checks, format_for_digest
        health_result = run_all_checks()
        health_line = format_for_digest(health_result)
    except Exception as e:
        logger.warning(f"Health check failed: {e}")
        health_line = "⚠️ *SYSTEM HEALTH*: check failed"

    # CLAUDE.md compliance check
    compliance_line = ""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "standardization_enforcer", REPO_ROOT / "execution" / "standardization_enforcer.py"
        )
        enforcer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(enforcer)
        enforcer_result = enforcer.run_all_checks()
        compliance_line = enforcer.format_for_digest(enforcer_result)
    except Exception as e:
        logger.warning(f"Compliance check failed: {e}")

    # Format
    combined_health = health_line
    if compliance_line:
        combined_health = (health_line + "\n" + compliance_line).strip() if health_line else compliance_line
    message = format_telegram_digest(pipeline, emails, calendar, sms, hours_back,
                                     health_line=combined_health)

    if preview:
        print("\n" + "=" * 60)
        print("PREVIEW — Telegram message:")
        print("=" * 60)
        print(message)
        print("=" * 60)
        print(f"Length: {len(message)} chars")
        return message

    # Send via Telegram
    sent = send_telegram(message)
    if not sent:
        # Fallback: print to stdout so launchd log captures it
        logger.warning("Telegram failed — printing to stdout")
        print(message)

    return message


def main():
    parser = argparse.ArgumentParser(description="Unified Morning Digest")
    parser.add_argument("--hours", type=int, default=12, help="Hours to look back")
    parser.add_argument("--preview", action="store_true", help="Preview without sending")
    args = parser.parse_args()

    generate_digest(hours_back=args.hours, preview=args.preview)


if __name__ == "__main__":
    main()
