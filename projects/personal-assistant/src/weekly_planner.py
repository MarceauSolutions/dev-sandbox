#!/usr/bin/env python3
"""
Weekly Planner — Generate all time blocks for the upcoming week.

Runs Sunday evening or Monday morning to plan the entire week ahead.
Uses show_as (transparency) evaluation for each block type.

This replaces the daily_scheduler's role in proposing blocks.
Morning digest now just SHOWS what's scheduled, doesn't propose.

Usage:
    python -m src.weekly_planner                   # Plan this week
    python -m src.weekly_planner --next-week       # Plan next week
    python -m src.weekly_planner --preview         # Preview without creating
    python -m src.weekly_planner --start 2026-03-30  # Start from specific date
"""

import argparse
import json
import logging
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("weekly_planner")

GATEWAY_URL = "http://localhost:5016/calendar/create"

# =============================================================================
# BLOCK TEMPLATES
# =============================================================================

# Sprint mode (pre-April 6): Full days available
SPRINT_WEEKDAY_BLOCKS = [
    {
        "start": "07:30", "end": "09:00",
        "label": "🧠 HIGH-AGENCY: Strategy + Education",
        "type": "deep_work", "show_as": "busy",
        "description": "Peak willpower — strategic thinking, learning, research.\nNo email, no social. Protect the morning."
    },
    {
        "start": "09:00", "end": "11:00",
        "label": "🎯 Outreach Blitz",
        "type": "outreach", "show_as": "busy",
        "description": "Phone calls or walk-in visits to qualified leads.\nROI priority: In-person > calls > email."
    },
    {
        "start": "11:00", "end": "12:00",
        "label": "🎬 Content Creation",
        "type": "content", "show_as": "free",
        "description": "Record or edit content. Flexible — can be moved if needed."
    },
    {
        "start": "12:00", "end": "13:00",
        "label": "🍽️ Lunch",
        "type": "break", "show_as": "free",
        "description": "Meal break."
    },
    {
        "start": "13:00", "end": "15:00",
        "label": "🏃 Deep Work + Visits",
        "type": "outreach", "show_as": "busy",
        "description": "Afternoon outreach or deep project work."
    },
    {
        "start": "15:00", "end": "17:00",
        "label": "📊 Follow-ups + Admin",
        "type": "admin", "show_as": "free",
        "description": "Follow-up calls, proposals, email review.\nReactive tasks go in the afternoon."
    },
    {
        "start": "18:00", "end": "20:00",
        "label": "💪 Training: Defy the Odds",
        "type": "training", "show_as": "busy",
        "description": "NEVER schedule over this. Training is sacred."
    },
    {
        "start": "20:00", "end": "21:00",
        "label": "📚 Wind Down + Reading",
        "type": "personal", "show_as": "free",
        "description": "Evening reading, Spanish, or relaxation."
    },
]

# Post-April 6: Job 7am-3pm, blocks around it
POST_JOB_WEEKDAY_BLOCKS = [
    {
        "start": "05:30", "end": "06:15",
        "label": "🌅 Pre-Work Prep",
        "type": "prep", "show_as": "free",
        "description": "Morning routine, review day's priorities."
    },
    {
        "start": "12:00", "end": "12:45",
        "label": "🍽️ Lunch Outreach",
        "type": "outreach", "show_as": "free",
        "description": "Quick calls or follow-ups during lunch."
    },
    {
        "start": "15:30", "end": "17:30",
        "label": "🎯 Post-Work Outreach",
        "type": "outreach", "show_as": "busy",
        "description": "Visits or calls after the day job."
    },
    {
        "start": "18:00", "end": "20:00",
        "label": "💪 Training",
        "type": "training", "show_as": "busy",
        "description": "Training block — non-negotiable."
    },
    {
        "start": "20:15", "end": "21:00",
        "label": "📊 Evening Admin",
        "type": "admin", "show_as": "free",
        "description": "Proposals, follow-ups, planning."
    },
]

# Weekend blocks (lighter)
WEEKEND_BLOCKS = [
    {
        "start": "09:00", "end": "10:30",
        "label": "📚 Deep Reading + Learning",
        "type": "learning", "show_as": "free",
        "description": "Longer learning session. Books, research, interests."
    },
    {
        "start": "10:30", "end": "12:00",
        "label": "🐕 Active Time + Dog",
        "type": "personal", "show_as": "free",
        "description": "Dog training, outdoor activity."
    },
    {
        "start": "14:00", "end": "16:00",
        "label": "🎬 Weekend Content Batch",
        "type": "content", "show_as": "free",
        "description": "Batch content for the week."
    },
    {
        "start": "18:00", "end": "19:30",
        "label": "💪 Training",
        "type": "training", "show_as": "busy",
        "description": "Weekend training session."
    },
]


# =============================================================================
# PLANNER LOGIC
# =============================================================================

def get_blocks_for_date(date: datetime, post_april_6: bool = None) -> List[Dict]:
    """Get the appropriate blocks for a given date."""
    if post_april_6 is None:
        post_april_6 = date >= datetime(2026, 4, 6)
    
    is_weekend = date.weekday() >= 5
    
    if is_weekend:
        return WEEKEND_BLOCKS
    elif post_april_6:
        return POST_JOB_WEEKDAY_BLOCKS
    else:
        return SPRINT_WEEKDAY_BLOCKS


def create_calendar_event(summary: str, start: str, end: str, 
                          description: str, show_as: str) -> Dict:
    """Create a calendar event via the gateway."""
    transparency = "opaque" if show_as == "busy" else "transparent"
    
    payload = {
        "agent": "weekly_planner",
        "calendar": "time_blocks",
        "summary": summary,
        "start": start,
        "end": end,
        "description": description,
        "transparency": transparency,
        "force": True,
    }
    
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            GATEWAY_URL, data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        return {"success": True, **result}
    except Exception as e:
        logger.warning(f"Gateway error: {e}")
        return {"success": False, "error": str(e)}


def plan_week(start_date: datetime = None, preview: bool = False, 
              post_april_6: bool = None) -> Dict[str, Any]:
    """Plan the entire week starting from start_date."""
    if start_date is None:
        today = datetime.now()
        # Default: start from Monday of this week
        start_date = today - timedelta(days=today.weekday())
    
    results = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "days": [],
        "created": 0,
        "failed": 0,
        "busy_count": 0,
        "free_count": 0,
    }
    
    for day_offset in range(7):
        current_date = start_date + timedelta(days=day_offset)
        date_str = current_date.strftime("%Y-%m-%d")
        day_name = current_date.strftime("%A")
        
        blocks = get_blocks_for_date(current_date, post_april_6)
        day_result = {
            "date": date_str,
            "day": day_name,
            "blocks": [],
        }
        
        for block in blocks:
            start_dt = f"{date_str}T{block['start']}:00"
            end_dt = f"{date_str}T{block['end']}:00"
            
            if preview:
                result = {"success": True, "preview": True}
            else:
                result = create_calendar_event(
                    summary=block["label"],
                    start=start_dt,
                    end=end_dt,
                    description=block["description"],
                    show_as=block["show_as"],
                )
            
            if result.get("success"):
                results["created"] += 1
            else:
                results["failed"] += 1
            
            if block["show_as"] == "busy":
                results["busy_count"] += 1
            else:
                results["free_count"] += 1
            
            day_result["blocks"].append({
                "label": block["label"],
                "time": f"{block['start']}-{block['end']}",
                "show_as": block["show_as"],
                "success": result.get("success", False),
            })
        
        results["days"].append(day_result)
    
    return results


def format_summary(results: Dict) -> str:
    """Format planning results for display."""
    lines = [
        "🗓️ WEEKLY PLAN CREATED",
        f"Week of {results['start_date']}",
        "=" * 40,
    ]
    
    for day in results["days"]:
        lines.append(f"\n📅 {day['day']} ({day['date']})")
        for block in day["blocks"]:
            icon = "🔒" if block["show_as"] == "busy" else "📖"
            status = "✅" if block["success"] else "❌"
            lines.append(f"  {status} {block['time']} {block['label']} {icon}")
    
    lines.append("")
    lines.append("=" * 40)
    lines.append(f"📊 SUMMARY")
    lines.append(f"  Created: {results['created']} blocks")
    lines.append(f"  🔒 Busy: {results['busy_count']} | 📖 Free: {results['free_count']}")
    
    return "\n".join(lines)


def send_telegram_notification(text: str) -> bool:
    """Send planning notification to Telegram."""
    import os
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "5692454753")
    
    if not token:
        return False
    
    try:
        payload = json.dumps({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception:
        return False


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Weekly Planner")
    parser.add_argument("--preview", action="store_true", help="Preview without creating")
    parser.add_argument("--next-week", action="store_true", help="Plan next week instead")
    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--notify", action="store_true", help="Send Telegram notification")
    parser.add_argument("--post-april-6", action="store_true", help="Use post-job schedule")
    args = parser.parse_args()
    
    # Determine start date
    if args.start:
        start_date = datetime.strptime(args.start, "%Y-%m-%d")
    elif args.next_week:
        today = datetime.now()
        next_monday = today + timedelta(days=(7 - today.weekday()))
        start_date = next_monday
    else:
        today = datetime.now()
        start_date = today - timedelta(days=today.weekday())
    
    print(f"🗓️ Planning week starting {start_date.strftime('%Y-%m-%d')}")
    if args.preview:
        print("📋 PREVIEW MODE — no events will be created\n")
    
    results = plan_week(
        start_date=start_date,
        preview=args.preview,
        post_april_6=args.post_april_6 if args.post_april_6 else None,
    )
    
    summary = format_summary(results)
    print(summary)
    
    if args.notify and not args.preview:
        short_msg = (
            f"🗓️ *Week Planned*\n"
            f"Week of {results['start_date']}\n"
            f"✅ {results['created']} blocks created\n"
            f"🔒 {results['busy_count']} busy | 📖 {results['free_count']} free"
        )
        if send_telegram_notification(short_msg):
            print("\n✅ Telegram notification sent")
        else:
            print("\n⚠️ Telegram notification failed")


if __name__ == "__main__":
    main()
