#!/usr/bin/env python3
"""
Clawdbot PA Handlers — Drop-in command handlers for the Telegram bot on EC2.

Ralph deploys this to EC2 and wires it into Clawdbot's existing bot.
Each handler calls the Personal Assistant Flask API on William's Mac
via SSH tunnel (localhost:5011 on EC2 → Mac:5011).

Prerequisites:
  1. SSH tunnel running: ssh -R 5011:localhost:5011 ec2-user@34.193.98.97
  2. PA Flask app running on Mac: cd projects/personal-assistant && python -m src.app
  3. This file copied to EC2 Clawdbot directory

Usage (in Clawdbot's main bot.py):
    from clawdbot_handlers import handle_schedule, handle_approve, handle_digest, handle_health

    # In message handler:
    if "schedule" in text.lower():
        response = handle_schedule()
        bot.send_message(chat_id, response, parse_mode="Markdown")
"""

import json
import logging
import urllib.request
from typing import Optional

logger = logging.getLogger("clawdbot_pa")

# PA API base URL (via SSH tunnel: EC2 localhost:5011 → Mac:5011)
PA_API = "http://localhost:5011"
TIMEOUT = 15


def _call_pa(endpoint: str, method: str = "GET", data: dict = None) -> Optional[dict]:
    """Call the Personal Assistant API."""
    try:
        url = f"{PA_API}{endpoint}"
        if data:
            req = urllib.request.Request(
                url, data=json.dumps(data).encode(),
                headers={"Content-Type": "application/json"}, method=method,
            )
        else:
            req = urllib.request.Request(url, method=method)
        resp = urllib.request.urlopen(req, timeout=TIMEOUT)
        return json.loads(resp.read())
    except Exception as e:
        logger.error(f"PA API call failed ({endpoint}): {e}")
        return None


def handle_schedule() -> str:
    """Handle 'What's my schedule?' / 'schedule' / 'plan'."""
    result = _call_pa("/scheduler/today")
    if not result or not result.get("success"):
        return "⚠️ Could not reach Personal Assistant. Is the Mac awake?"

    formatted = result.get("formatted", "")
    if formatted:
        return formatted

    schedule = result.get("schedule", {})
    blocks = schedule.get("proposed_blocks", [])
    if not blocks:
        return "📋 No scheduled blocks for today. Pipeline is in outreach mode."

    lines = ["📋 *TODAY'S PLAN*"]
    for b in blocks:
        lines.append(f"  • {b.get('calendar_summary', '?')}")
    return "\n".join(lines)


def handle_approve() -> str:
    """Handle 'yes schedule' / 'approve schedule'."""
    result = _call_pa("/scheduler/approve", method="POST")
    if not result or not result.get("success"):
        return "⚠️ Could not approve schedule. Is the Mac awake?"

    created = result.get("created", [])
    errors = result.get("errors", [])

    if created:
        lines = [f"✅ {len(created)} block(s) added to Google Calendar:"]
        for c in created:
            lines.append(f"  • {c}")
        return "\n".join(lines)
    elif errors:
        return f"⚠️ Calendar errors: {'; '.join(errors)}"
    else:
        return "No pending schedule to approve."


def handle_digest() -> str:
    """Handle 'morning briefing' / 'digest' / 'what did I miss?'."""
    result = _call_pa("/scheduler/digest")
    if not result or not result.get("success"):
        return "⚠️ Could not reach Personal Assistant. Is the Mac awake?"
    return result.get("digest", "No digest available.")


def handle_health() -> str:
    """Handle 'system status' / 'health' / 'how's the system?'."""
    result = _call_pa("/scheduler/health-check")
    if not result:
        return "⚠️ Could not reach Personal Assistant. Is the Mac awake?"

    healthy = result.get("healthy", False)
    checks = result.get("checks", {})

    if healthy:
        return "🟢 *SYSTEM HEALTH*: All checks pass"

    lines = ["🔴 *SYSTEM HEALTH*: Issues detected"]
    for name, count in checks.items():
        icon = "✓" if count == 0 else "✗"
        lines.append(f"  {icon} {name}: {count} violations")
    return "\n".join(lines)


def route_message(text: str) -> Optional[str]:
    """Route a Telegram message to the right handler.

    Returns response string, or None if not a PA command.
    Wire this into Clawdbot's main message handler.
    """
    lower = text.lower().strip()

    if lower in ("yes schedule", "approve schedule", "approve"):
        return handle_approve()

    if any(kw in lower for kw in ["schedule", "plan", "what's my", "today's plan", "my day"]):
        return handle_schedule()

    if any(kw in lower for kw in ["digest", "briefing", "morning", "what did i miss"]):
        return handle_digest()

    if any(kw in lower for kw in ["health", "status", "system", "check"]):
        return handle_health()

    return None  # Not a PA command — let Clawdbot handle normally
