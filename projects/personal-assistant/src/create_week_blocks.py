#!/usr/bin/env python3
"""
Create time blocks for the current week with show_as status evaluation.
Tests the full flow: generate blocks → evaluate show_as → create on calendar.
"""

import json
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Sprint blocks (pre-April 6)
SPRINT_BLOCKS = [
    {
        "id": "high_agency",
        "start": "07:30",
        "end": "09:00",
        "label": "🧠 HIGH-AGENCY: Strategy + Education",
        "type": "deep_work",
        "show_as": "busy",  # Protected time
        "description": "Peak willpower — strategic thinking, learning, peptide research.\nNo email, no social media. Protect the morning."
    },
    {
        "id": "outreach_am",
        "start": "09:00",
        "end": "11:00",
        "label": "🎯 Outreach Blitz",
        "type": "outreach",
        "show_as": "busy",  # Active calls/visits
        "description": "Phone calls or walk-in visits to qualified leads.\nROI priority: In-person > calls > email."
    },
    {
        "id": "content",
        "start": "11:00",
        "end": "12:00",
        "label": "🎬 Content Creation",
        "type": "content",
        "show_as": "free",  # Flexible
        "description": "Record or edit content. Can be moved if needed."
    },
    {
        "id": "lunch",
        "start": "12:00",
        "end": "13:00",
        "label": "🍽️ Lunch",
        "type": "break",
        "show_as": "free",  # Flexible
        "description": "Meal break."
    },
    {
        "id": "deep_work",
        "start": "13:00",
        "end": "15:00",
        "label": "🏃 Deep Work + Visits",
        "type": "outreach",
        "show_as": "busy",  # External commitments
        "description": "Afternoon outreach or deep work on projects."
    },
    {
        "id": "afternoon",
        "start": "15:00",
        "end": "17:00",
        "label": "📊 Follow-ups + Admin",
        "type": "admin",
        "show_as": "free",  # Flexible
        "description": "Follow-up calls, proposals, email review.\nReactive tasks go in the afternoon."
    },
    {
        "id": "training",
        "start": "18:00",
        "end": "20:00",
        "label": "💪 Training: Defy the Odds",
        "type": "training",
        "show_as": "busy",  # Non-negotiable
        "description": "NEVER schedule over this. Training is sacred."
    },
    {
        "id": "wind_down",
        "start": "20:00",
        "end": "21:00",
        "label": "📚 Wind Down + Reading",
        "type": "personal",
        "show_as": "free",  # Personal time
        "description": "Evening reading, Spanish study, or relaxation."
    },
]

# Weekend blocks (lighter)
WEEKEND_BLOCKS = [
    {
        "id": "morning",
        "start": "09:00",
        "end": "10:30",
        "label": "📚 Deep Reading + Learning",
        "type": "learning",
        "show_as": "free",
        "description": "Longer learning session. Books, research, personal interests."
    },
    {
        "id": "active",
        "start": "10:30",
        "end": "12:00",
        "label": "🐕 Active Time + Dog",
        "type": "personal",
        "show_as": "free",
        "description": "Dog training, outdoor activity, light exercise."
    },
    {
        "id": "content",
        "start": "14:00",
        "end": "16:00",
        "label": "🎬 Weekend Content",
        "type": "content",
        "show_as": "free",
        "description": "Batch content for the week or relaxed filming."
    },
    {
        "id": "training",
        "start": "18:00",
        "end": "19:30",
        "label": "💪 Training",
        "type": "training",
        "show_as": "busy",
        "description": "Weekend training session."
    },
]


def create_calendar_event(summary, start, end, description, show_as):
    """Create a calendar event via the gateway."""
    transparency = "opaque" if show_as == "busy" else "transparent"
    
    payload = {
        "agent": "create_week_blocks",
        "calendar": "time_blocks",
        "summary": summary,
        "start": start,
        "end": end,
        "description": description,
        "transparency": transparency,
        "force": True,  # Skip conflict validation for bulk creation
    }
    
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            "http://localhost:5015/calendar/create",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        return result
    except Exception as e:
        return {"error": str(e)}


def generate_week_blocks():
    """Generate time blocks for the current week."""
    today = datetime.now()
    # Start from Monday of this week
    monday = today - timedelta(days=today.weekday())
    
    all_results = []
    
    for day_offset in range(7):
        current_date = monday + timedelta(days=day_offset)
        date_str = current_date.strftime("%Y-%m-%d")
        day_name = current_date.strftime("%A")
        is_weekend = current_date.weekday() >= 5
        
        blocks = WEEKEND_BLOCKS if is_weekend else SPRINT_BLOCKS
        
        print(f"\n📅 {day_name} ({date_str})")
        print("-" * 40)
        
        for block in blocks:
            start_dt = f"{date_str}T{block['start']}:00"
            end_dt = f"{date_str}T{block['end']}:00"
            
            result = create_calendar_event(
                summary=block["label"],
                start=start_dt,
                end=end_dt,
                description=block["description"],
                show_as=block["show_as"],
            )
            
            status_icon = "✅" if result.get("status") == "created" else "❌"
            show_as_icon = "🔒" if block["show_as"] == "busy" else "📖"
            
            print(f"  {status_icon} {block['start']}-{block['end']} {block['label']}")
            print(f"     {show_as_icon} Show as: {block['show_as']}")
            
            all_results.append({
                "date": date_str,
                "block": block["label"],
                "show_as": block["show_as"],
                "result": result,
            })
    
    # Summary
    created = sum(1 for r in all_results if r["result"].get("status") == "created")
    busy_count = sum(1 for r in all_results if r["show_as"] == "busy")
    free_count = sum(1 for r in all_results if r["show_as"] == "free")
    
    print(f"\n{'=' * 40}")
    print(f"📊 SUMMARY")
    print(f"  Created: {created}/{len(all_results)} blocks")
    print(f"  🔒 Busy (opaque): {busy_count} blocks")
    print(f"  📖 Free (transparent): {free_count} blocks")
    
    return all_results


if __name__ == "__main__":
    print("🗓️  CREATING WEEK TIME BLOCKS")
    print("=" * 40)
    print("Testing show_as (transparency) evaluation for each block")
    
    results = generate_week_blocks()
    
    print("\n✅ Week blocks created with show_as status evaluated!")
