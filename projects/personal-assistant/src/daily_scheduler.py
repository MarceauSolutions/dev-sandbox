#!/usr/bin/env python3
"""
Daily Scheduler — Personal assistant that turns pipeline leads into a prioritized day.

Reads pipeline.db, ranks by ROI, proposes time blocks in the morning digest,
and creates Google Calendar events when William approves via "yes schedule".

ROI Priority (Hormozi framework — revenue impact first):
  Tier 1: HOT leads → In-person visit or call (closest to cash)
  Tier 2: Qualified leads → Walk-in visit or cold call
  Tier 3: Warm responses → Follow-up call
  Tier 4: Scheduled calls → Prep + attend
  Meta:   Build Learning System → triggers when outcome data reaches threshold
  Auto:   Follow-ups, discovery, scoring → daily_loop handles it

Approval flow:
  Morning digest shows proposed blocks → William replies "yes schedule"
  → Twilio webhook → create_approved_blocks() → Calendar gateway creates events

Usage:
    # Generate schedule (used by morning digest)
    python -m src.daily_scheduler preview

    # Create approved blocks on calendar
    python -m src.daily_scheduler create

    # Show what's pending approval
    python -m src.daily_scheduler pending

    # Check learning system readiness
    python -m src.daily_scheduler learning-status
"""

import argparse
import json
import logging
import os
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("daily_scheduler")

SCHEDULE_FILE = REPO_ROOT / "projects" / "personal-assistant" / "logs" / "pending_schedule.json"

# Post-April 6: available blocks around 7am-3pm job
WEEKDAY_BLOCKS = [
    {"id": "pre_work",   "start": "06:15", "end": "06:45", "label": "Pre-work prep",       "type": "prep"},
    {"id": "lunch",      "start": "12:00", "end": "12:45", "label": "Lunch outreach",       "type": "outreach"},
    {"id": "post_work",  "start": "15:15", "end": "17:15", "label": "Post-work visits/calls","type": "outreach"},
    {"id": "evening",    "start": "20:15", "end": "21:00", "label": "Evening admin",        "type": "admin"},
]

# Pre-April 6: full days available
SPRINT_BLOCKS = [
    {"id": "high_agency","start": "07:30", "end": "09:00", "label": "Strategy + education",  "type": "prep"},
    {"id": "outreach_am","start": "09:00", "end": "11:00", "label": "Morning outreach",      "type": "outreach"},
    {"id": "content",    "start": "11:00", "end": "12:00", "label": "Content creation",      "type": "content"},
    {"id": "deep_work",  "start": "13:00", "end": "15:00", "label": "Deep work + visits",    "type": "outreach"},
    {"id": "afternoon",  "start": "15:00", "end": "17:00", "label": "Follow-ups + admin",    "type": "admin"},
]

# Training block — NEVER schedule over this
TRAINING_BLOCK = ("18:00", "20:00")


def _get_pipeline_db():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "pipeline_db", REPO_ROOT / "execution" / "pipeline_db.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Lead analysis
# ---------------------------------------------------------------------------

def _get_best_outreach_method() -> str:
    """Check research gate data to determine best outreach method.

    Returns 'call' or 'visit' based on actual response rate data.
    If calls convert significantly better than in-person, prefer calls.
    Falls back to 'visit' if no data available.
    """
    try:
        import importlib.util as _ilu
        _rg_spec = _ilu.spec_from_file_location(
            "research_gate", REPO_ROOT / "execution" / "research_gate.py"
        )
        _rg = _ilu.module_from_spec(_rg_spec)
        _rg_spec.loader.exec_module(_rg)
        ctx = _rg.gather_context()
        channels = ctx.get("outreach", {}).get("by_channel", {})

        call_rate = channels.get("Call", {}).get("response_rate", 0)
        visit_rate = channels.get("In-Person", {}).get("response_rate", 0)

        # If calls have meaningfully better response rate, prefer calls
        if call_rate > visit_rate + 10:
            logger.info(f"Research gate: Calls ({call_rate}%) beat visits ({visit_rate}%), preferring calls")
            return "call"
        elif visit_rate > call_rate + 10:
            logger.info(f"Research gate: Visits ({visit_rate}%) beat calls ({call_rate}%), preferring visits")
            return "visit"
        else:
            return "visit_or_call"
    except Exception:
        return "visit_or_call"


def get_actionable_leads() -> List[Dict[str, Any]]:
    """Get leads that need manual action today, ranked by ROI.

    Uses research gate data to determine whether to propose calls or visits
    for Tier 1-2 leads, instead of hardcoding action types.
    """
    try:
        pdb = _get_pipeline_db()
        conn = pdb.get_db()
        leads = []

        # Check research data for best outreach method
        best_method = _get_best_outreach_method()

        # Tier 1: HOT (closest to cash — one conversation away from a deal)
        for r in conn.execute(
            "SELECT id, company, contact_name, contact_phone, contact_email, "
            "industry, stage, next_action, city "
            "FROM deals WHERE stage = 'Hot Response' "
            "ORDER BY updated_at DESC LIMIT 5"
        ).fetchall():
            d = dict(r)
            if best_method == "call":
                d.update(roi_tier=1, roi_reason="Replied interested + calls convert best (data-driven)",
                         action_type="call", time_needed=15)
            else:
                d.update(roi_tier=1, roi_reason="Replied interested — one call from a deal",
                         action_type="visit_or_call", time_needed=30)
            leads.append(d)

        # Tier 2: Qualified (data-driven: calls vs visits)
        for r in conn.execute(
            "SELECT id, company, contact_name, contact_phone, industry, city "
            "FROM deals WHERE stage = 'Qualified' "
            "ORDER BY updated_at DESC LIMIT 5"
        ).fetchall():
            d = dict(r)
            if best_method == "call":
                d.update(roi_tier=2, roi_reason="Qualified lead + calls outperform visits (data-driven)",
                         action_type="call", time_needed=15)
            elif best_method == "visit":
                d.update(roi_tier=2, roi_reason="Qualified lead + in-person converts best (data-driven)",
                         action_type="visit", time_needed=45)
            else:
                d.update(roi_tier=2, roi_reason="High-score lead — walk-in or call converts best",
                         action_type="visit_or_call", time_needed=30)
            leads.append(d)

        # Tier 3: Warm responses (always calls — nurturing is phone-based)
        for r in conn.execute(
            "SELECT id, company, contact_name, contact_phone, industry "
            "FROM deals WHERE stage = 'Warm Response' "
            "ORDER BY updated_at DESC LIMIT 3"
        ).fetchall():
            d = dict(r)
            d.update(roi_tier=3, roi_reason="Engaged but undecided — a call tips the balance",
                     action_type="call", time_needed=15)
            leads.append(d)

        # Tier 4: Proposals sent (always calls — follow-through)
        for r in conn.execute(
            "SELECT id, company, contact_name, contact_phone "
            "FROM deals WHERE stage = 'Proposal Sent' "
            "ORDER BY updated_at DESC LIMIT 2"
        ).fetchall():
            d = dict(r)
            d.update(roi_tier=4, roi_reason="Proposal out — follow-up closes or kills",
                     action_type="call", time_needed=15)
            leads.append(d)

        conn.close()
        return leads

    except Exception as e:
        logger.warning(f"Failed to get leads: {e}")
        return []


# ---------------------------------------------------------------------------
# Learning system readiness
# ---------------------------------------------------------------------------

# Thresholds: only propose the learning system block when we have real data
LEARNING_SYSTEM_MIN_OUTCOMES = 5        # at least 5 tasks with recorded outcomes
LEARNING_SYSTEM_MIN_DAYS_RUNNING = 7    # scheduler must have been running 7+ days
LEARNING_SYSTEM_BLOCK_HOURS = 2.5       # 2.5 hour deep work block


def check_learning_system_readiness() -> Dict[str, Any]:
    """Check if we have enough outcome data to justify building the learning system.

    Reads scheduled_outcomes from pipeline.db. Only triggers when:
      1. At least LEARNING_SYSTEM_MIN_OUTCOMES completed tasks with outcomes, AND
      2. Scheduler has been generating schedules for 7+ days, AND
      3. At least 1 client landed (Closed Won) OR 10+ outcomes exist (sufficient data either way)

    Returns dict with ready: bool, stats, and reasoning.
    """
    try:
        pdb = _get_pipeline_db()
        conn = pdb.get_db()

        # Count completed outcomes
        outcome_count = conn.execute(
            "SELECT COUNT(*) FROM scheduled_outcomes WHERE completed = 1 AND outcome IS NOT NULL"
        ).fetchone()[0]

        # Count distinct days with outcomes (proxy for "days running")
        days_with_outcomes = conn.execute(
            "SELECT COUNT(DISTINCT scheduled_date) FROM scheduled_outcomes WHERE scheduled_date IS NOT NULL"
        ).fetchone()[0]

        # Check for closed-won deals (strongest signal)
        closed_won = conn.execute(
            "SELECT COUNT(*) FROM deals WHERE stage = 'Closed Won'"
        ).fetchone()[0]

        # Check for positive outcomes (responses, meetings, wins)
        positive_outcomes = conn.execute(
            "SELECT COUNT(*) FROM scheduled_outcomes "
            "WHERE completed = 1 AND resulted_in IN ('response', 'meeting_booked', 'closed_won', 'callback', 'interested')"
        ).fetchone()[0]

        # First outcome date (how long we've been tracking)
        first_outcome = conn.execute(
            "SELECT MIN(created_at) FROM scheduled_outcomes WHERE completed = 1"
        ).fetchone()[0]

        conn.close()

        days_since_first = 0
        if first_outcome:
            first_dt = datetime.fromisoformat(first_outcome.replace("Z", "+00:00")) if "T" in first_outcome else datetime.strptime(first_outcome, "%Y-%m-%d %H:%M:%S")
            days_since_first = (datetime.now() - first_dt.replace(tzinfo=None)).days

        has_enough_outcomes = outcome_count >= LEARNING_SYSTEM_MIN_OUTCOMES
        has_enough_days = days_since_first >= LEARNING_SYSTEM_MIN_DAYS_RUNNING
        has_client_or_data = closed_won >= 1 or outcome_count >= 10

        ready = has_enough_outcomes and has_enough_days and has_client_or_data

        reason = []
        if not has_enough_outcomes:
            reason.append(f"Need {LEARNING_SYSTEM_MIN_OUTCOMES} outcomes, have {outcome_count}")
        if not has_enough_days:
            reason.append(f"Need {LEARNING_SYSTEM_MIN_DAYS_RUNNING} days of data, have {days_since_first}")
        if not has_client_or_data:
            reason.append(f"Need 1 closed-won or 10+ outcomes (have {closed_won} won, {outcome_count} outcomes)")

        return {
            "ready": ready,
            "outcome_count": outcome_count,
            "positive_outcomes": positive_outcomes,
            "closed_won": closed_won,
            "days_tracking": days_since_first,
            "days_with_outcomes": days_with_outcomes,
            "reason": " | ".join(reason) if reason else "Data threshold met — learning system build is justified",
        }

    except Exception as e:
        logger.warning(f"Learning system readiness check failed: {e}")
        return {"ready": False, "reason": f"Check failed: {e}", "outcome_count": 0}


# ---------------------------------------------------------------------------
# Schedule generation
# ---------------------------------------------------------------------------

def generate_proposed_schedule(post_april_6: bool = None) -> Dict[str, Any]:
    """Generate ROI-prioritized daily schedule from pipeline leads.

    Returns schedule with proposed time blocks and delegation list.
    """
    if post_april_6 is None:
        post_april_6 = datetime.now() >= datetime(2026, 4, 6)

    leads = get_actionable_leads()
    available_blocks = WEEKDAY_BLOCKS if post_april_6 else SPRINT_BLOCKS
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")

    # Split leads by type
    visits = [l for l in leads if l["action_type"] in ("visit", "visit_or_call") and l["roi_tier"] <= 2]
    calls = [l for l in leads if l["action_type"] == "call" or (l["action_type"] == "visit_or_call" and l["roi_tier"] > 2)]

    proposed_blocks = []

    # Assign visits to outreach blocks
    outreach_blocks = [b for b in available_blocks if b["type"] == "outreach"]
    if visits and outreach_blocks:
        block = outreach_blocks[0]
        names = [f"{l['company']}" + (f" ({l.get('city', '')})" if l.get("city") else "") for l in visits[:3]]
        total_min = sum(l["time_needed"] for l in visits[:3])
        proposed_blocks.append({
            "calendar_summary": f"🎯 Walk-in visits: {', '.join(n.split(' (')[0] for n in names[:2])}",
            "start": f"{today_str}T{block['start']}:00",
            "end": f"{today_str}T{block['end']}:00",
            "description": f"ROI Priority: Walk-in visits convert at highest rate.\n\nLeads:\n" +
                           "\n".join(f"• {n} — {visits[i]['roi_reason']}" for i, n in enumerate(names[:3])),
            "location": ", ".join(names[:2]),
            "priority": "critical" if any(l["roi_tier"] == 1 for l in visits[:3]) else "high",
            "leads": names,
            "minutes": total_min,
            "roi_reasoning": "In-person visits have 5-10x conversion vs email. These leads are qualified or HOT.",
        })

    # Assign calls to lunch or second outreach block
    call_blocks = [b for b in available_blocks if b["type"] in ("outreach", "admin")]
    used_block_ids = {pb.get("block_id") for pb in proposed_blocks}
    call_block = next((b for b in call_blocks if b["id"] not in used_block_ids), None)
    if calls and call_block:
        names = [l["company"] for l in calls[:3]]
        total_min = sum(l["time_needed"] for l in calls[:3])
        proposed_blocks.append({
            "calendar_summary": f"📞 Calls: {', '.join(names[:2])}",
            "start": f"{today_str}T{call_block['start']}:00",
            "end": f"{today_str}T{call_block['end']}:00",
            "description": f"Follow-up calls for warm/proposal leads.\n\nLeads:\n" +
                           "\n".join(f"• {calls[i]['company']} — {calls[i]['roi_reason']}" for i in range(min(3, len(calls)))),
            "priority": "medium",
            "leads": names,
            "minutes": total_min,
            "roi_reasoning": "Phone calls advance warm leads faster than email. These replied or received proposals.",
        })

    # Meta-task: Build Learning System (only when data threshold met)
    learning_status = check_learning_system_readiness()
    if learning_status["ready"]:
        # Schedule on weekends or in the evening admin block (post-April 6)
        # Pre-April 6: use deep_work block; Post-April 6: use Saturday/Sunday or evening
        is_weekend = today.weekday() >= 5
        learning_minutes = int(LEARNING_SYSTEM_BLOCK_HOURS * 60)

        if not post_april_6:
            # Sprint mode: use deep_work slot
            ls_start, ls_end = "13:00", "15:30"
        elif is_weekend:
            # Weekends: morning deep work
            ls_start, ls_end = "09:00", "11:30"
        else:
            # Weekday post-job: evening slot (after training)
            ls_start, ls_end = "20:15", "21:00"
            learning_minutes = 45  # shorter on weekday evenings

        proposed_blocks.append({
            "calendar_summary": "🧠 Build Learning System — adaptive ROI ranking",
            "start": f"{today_str}T{ls_start}:00",
            "end": f"{today_str}T{ls_end}:00",
            "description": (
                "HIGH-ROI META-TASK: Analyze which scheduled tasks led to responses/wins "
                "and implement adaptive ROI ranking.\n\n"
                f"Data available: {learning_status['outcome_count']} task outcomes, "
                f"{learning_status['positive_outcomes']} positive, "
                f"{learning_status['closed_won']} closed-won deals.\n\n"
                "Deliverables:\n"
                "• Outcome tracking dashboard (which tasks → which wins)\n"
                "• Adaptive ROI weights (auto-adjust tier priorities based on real conversion data)\n"
                "• Continuous improvement loop (scheduler learns from what actually works)"
            ),
            "priority": "high",
            "leads": [],
            "minutes": learning_minutes,
            "roi_reasoning": (
                "Meta-task: Makes every future scheduled task more effective. "
                f"Based on {learning_status['outcome_count']} real outcomes over "
                f"{learning_status['days_tracking']} days."
            ),
            "meta_task": True,
        })

    # Delegated to automation
    delegated = [
        {"task": "Follow-up email sequences", "handler": "daily_loop (auto)", "saves": "2+ hours"},
        {"task": "Lead discovery + scoring", "handler": "daily_loop Stage 1-3 (auto)", "saves": "1 hour"},
        {"task": "Response monitoring", "handler": "check-responses every 15min (auto)", "saves": "continuous"},
        {"task": "Pipeline analytics", "handler": "5:30pm digest (auto)", "saves": "30min"},
    ]

    # Research gate: capture outreach effectiveness data for informed scheduling
    research_snapshot = {}
    try:
        import importlib.util as _ilu
        _rg_spec = _ilu.spec_from_file_location(
            "research_gate", REPO_ROOT / "execution" / "research_gate.py"
        )
        _rg = _ilu.module_from_spec(_rg_spec)
        _rg_spec.loader.exec_module(_rg)
        ctx = _rg.gather_context()
        research_snapshot = {
            "outreach_by_channel": ctx.get("outreach", {}).get("by_channel", {}),
            "recent_7d": ctx.get("outreach", {}).get("recent_7d", 0),
            "goal_progress_pct": ctx.get("goals", {}).get("short_term", {}).get("overall_pct", 0),
        }
    except Exception:
        pass

    schedule = {
        "date": today.strftime("%A, %B %d"),
        "date_iso": today_str,
        "proposed_blocks": proposed_blocks,
        "delegated": delegated,
        "lead_counts": {
            "hot": len([l for l in leads if l["roi_tier"] == 1]),
            "qualified": len([l for l in leads if l["roi_tier"] == 2]),
            "warm": len([l for l in leads if l["roi_tier"] == 3]),
            "proposals": len([l for l in leads if l["roi_tier"] == 4]),
        },
        "learning_system": learning_status,
        "research_snapshot": research_snapshot,
        "total_manual_minutes": sum(b["minutes"] for b in proposed_blocks),
        "post_april_6": post_april_6,
    }

    # Save for approval
    SCHEDULE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(schedule, f, indent=2, default=str)

    return schedule


# ---------------------------------------------------------------------------
# Calendar write (with approval gate)
# ---------------------------------------------------------------------------

def create_approved_blocks() -> Dict[str, Any]:
    """Create calendar events for the approved schedule.

    Called when William replies "yes schedule" via SMS/Telegram.
    Uses the calendar gateway (port 5015) for conflict checking.
    """
    if not SCHEDULE_FILE.exists():
        return {"success": False, "error": "No pending schedule to approve"}

    with open(SCHEDULE_FILE) as f:
        schedule = json.load(f)

    created = []
    errors = []

    for block in schedule.get("proposed_blocks", []):
        result = _create_calendar_event(
            summary=block["calendar_summary"],
            start=block["start"],
            end=block["end"],
            description=block.get("description", ""),
            location=block.get("location", ""),
        )
        if result.get("success"):
            created.append(block["calendar_summary"])
        else:
            errors.append(f"{block['calendar_summary']}: {result.get('error', 'unknown')}")

    # Clear pending schedule after processing
    SCHEDULE_FILE.unlink(missing_ok=True)

    logger.info(f"Calendar blocks created: {len(created)}, errors: {len(errors)}")
    return {"created": created, "errors": errors, "total": len(created)}


def _create_calendar_event(summary: str, start: str, end: str,
                           description: str = "", location: str = "") -> Dict:
    """Create a calendar event via the gateway or directly via Google API."""
    # Try calendar gateway first (has conflict checking)
    try:
        data = json.dumps({
            "agent": "daily_scheduler",
            "calendar": "time_blocks",
            "summary": summary,
            "start": start,
            "end": end,
            "description": description,
            "location": location,
        }).encode()
        req = urllib.request.Request(
            "http://localhost:5015/calendar/create",
            data=data, headers={"Content-Type": "application/json"}, method="POST",
        )
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        return {"success": True, **result}
    except Exception as gw_err:
        logger.info(f"Gateway unavailable ({gw_err}), using direct Google API")

    # Fallback: direct Google Calendar API
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        token_path = REPO_ROOT / "token.json"
        creds = Credentials.from_authorized_user_file(str(token_path))
        service = build("calendar", "v3", credentials=creds)

        event_body = {
            "summary": summary,
            "start": {"dateTime": start, "timeZone": "America/New_York"},
            "end": {"dateTime": end, "timeZone": "America/New_York"},
        }
        if description:
            event_body["description"] = description
        if location:
            event_body["location"] = location

        created = service.events().insert(calendarId="primary", body=event_body).execute()
        return {"success": True, "event_id": created.get("id")}

    except Exception as e:
        return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Digest formatting
# ---------------------------------------------------------------------------

def format_for_digest(schedule: Dict[str, Any]) -> str:
    """Format schedule for the morning Telegram digest."""
    blocks = schedule.get("proposed_blocks", [])
    if not blocks:
        return ""

    lines = ["📋 *TODAY'S PLAN*"]

    for b in blocks:
        icon = {"critical": "‼️", "high": "❗", "medium": "▪️"}.get(b["priority"], "")
        time_range = b["start"].split("T")[1][:5] + "–" + b["end"].split("T")[1][:5]
        lines.append(f"  {icon} {time_range}: {b['calendar_summary']}")
        lines.append(f"    _Why: {b['roi_reasoning'][:70]}_")

    total = schedule.get("total_manual_minutes", 0)
    lines.append(f"  ⏱️ Total manual time: ~{total}min")

    delegated = schedule.get("delegated", [])
    if delegated:
        lines.append(f"  🤖 Automated: {len(delegated)} tasks delegated to daily_loop")

    counts = schedule.get("lead_counts", {})
    if counts:
        parts = []
        if counts.get("hot"): parts.append(f"🔥{counts['hot']} hot")
        if counts.get("qualified"): parts.append(f"🎯{counts['qualified']} qualified")
        if counts.get("warm"): parts.append(f"📞{counts['warm']} warm")
        if counts.get("proposals"): parts.append(f"📋{counts['proposals']} proposals")
        if parts:
            lines.append(f"  Pipeline: {', '.join(parts)}")

    # Expected ROI summary
    hot = counts.get("hot", 0)
    qualified = counts.get("qualified", 0)
    proposals = counts.get("proposals", 0)
    if hot > 0:
        lines.append(f"  💰 Expected ROI: HIGH — {hot} hot lead(s) = 1 call from a deal")
    elif qualified > 0 or proposals > 0:
        lines.append(f"  💰 Expected ROI: MEDIUM — {qualified} visit targets + {proposals} proposals to close")
    else:
        lines.append(f"  💰 Expected ROI: Building pipeline — outreach generating future opportunities")

    # Learning system status
    ls = schedule.get("learning_system", {})
    if ls.get("ready"):
        lines.append(f"  🧠 Learning system: READY ({ls['outcome_count']} outcomes tracked)")
    elif ls.get("outcome_count", 0) > 0:
        lines.append(f"  🧠 Learning system: {ls['outcome_count']}/{LEARNING_SYSTEM_MIN_OUTCOMES} outcomes — {ls.get('reason', 'gathering data')}")

    lines.append(f"  _Reply 'yes schedule' to add these blocks to your calendar_")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Daily Scheduler")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("preview", help="Preview proposed schedule")
    sub.add_parser("create", help="Create approved blocks on calendar")
    sub.add_parser("pending", help="Show pending schedule")
    sub.add_parser("learning-status", help="Check learning system readiness")
    args = parser.parse_args()

    if args.command == "preview":
        schedule = generate_proposed_schedule()
        print(format_for_digest(schedule))
    elif args.command == "create":
        result = create_approved_blocks()
        print(json.dumps(result, indent=2))
    elif args.command == "pending":
        if SCHEDULE_FILE.exists():
            with open(SCHEDULE_FILE) as f:
                print(json.dumps(json.load(f), indent=2))
        else:
            print("No pending schedule.")
    elif args.command == "learning-status":
        status = check_learning_system_readiness()
        ready_icon = "🟢" if status["ready"] else "🔴"
        print(f"{ready_icon} Learning System Readiness")
        print(f"  Outcomes tracked: {status.get('outcome_count', 0)}")
        print(f"  Positive outcomes: {status.get('positive_outcomes', 0)}")
        print(f"  Closed-won deals: {status.get('closed_won', 0)}")
        print(f"  Days tracking: {status.get('days_tracking', 0)}")
        print(f"  Status: {status.get('reason', 'unknown')}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
