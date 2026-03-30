#!/usr/bin/env python3
"""
Consolidated Digest Sender

Combines all queued notifications into a single morning or evening digest.
Runs via cron at 6:30am and 9:00pm ET.

Usage:
    python execution/send_digest.py morning
    python execution/send_digest.py evening
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Setup
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)

from execution.notification_policy import (
    get_queued_notifications, format_digest, clear_queue, _send_telegram
)


def get_pipeline_summary() -> str:
    """Get current pipeline status for digest."""
    try:
        import sqlite3
        db_path = Path("/home/clawdbot/data/pipeline.db")
        if not db_path.exists():
            return ""
        
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        
        # Count by stage
        stages = conn.execute("""
            SELECT stage, COUNT(*) as count 
            FROM deals 
            WHERE stage NOT IN ('Closed Won', 'Closed Lost')
            GROUP BY stage
        """).fetchall()
        
        # Today's follow-ups
        today = datetime.now().strftime("%Y-%m-%d")
        followups = conn.execute("""
            SELECT COUNT(*) FROM deals 
            WHERE next_follow_up_date <= ? AND stage NOT IN ('Closed Won', 'Closed Lost')
        """, (today,)).fetchone()[0]
        
        conn.close()
        
        lines = ["<b>📊 Pipeline Status</b>"]
        for s in stages:
            lines.append(f"   • {s['stage']}: {s['count']}")
        if followups:
            lines.append(f"\n⚡ <b>{followups} follow-up(s) due today</b>")
        
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Pipeline summary failed: {e}")
        return ""


def get_calendar_preview() -> str:
    """Get today's calendar events for digest."""
    try:
        # Use smart_calendar if available
        import subprocess
        result = subprocess.run(
            ["python3", "execution/smart_calendar.py", "--no-transitions", "--no-projects", "--today-only"],
            cwd="/home/clawdbot/dev-sandbox",
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return f"<b>📅 Today's Schedule</b>\n{result.stdout.strip()[:500]}"
    except Exception as e:
        logger.debug(f"Calendar preview failed: {e}")
    return ""


def send_morning_digest():
    """Send consolidated morning digest."""
    logger.info("Preparing morning digest...")
    
    # Get overnight notifications (last 12 hours)
    notifications = get_queued_notifications(since_hours=12)
    
    lines = [
        "☀️ <b>MORNING DIGEST</b>",
        f"📅 {datetime.now().strftime('%A, %B %d, %Y')}",
        ""
    ]
    
    # Calendar preview
    calendar = get_calendar_preview()
    if calendar:
        lines.append(calendar)
        lines.append("")
    
    # Pipeline summary
    pipeline = get_pipeline_summary()
    if pipeline:
        lines.append(pipeline)
        lines.append("")
    
    # Queued notifications summary
    if notifications:
        # Group by type
        by_type = {}
        for n in notifications:
            t = n["type"]
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(n)
        
        lines.append("<b>📬 Overnight Activity</b>")
        
        if "voice_call_report" in by_type:
            calls = by_type["voice_call_report"]
            hot = sum(1 for c in calls if c.get("metadata", {}).get("lead_quality") == "hot")
            lines.append(f"   📞 {len(calls)} Voice AI call(s)")
            if hot:
                lines.append(f"      🔥 {hot} HOT - needs callback!")
        
        if "client_reply" in by_type:
            lines.append(f"   💬 {len(by_type['client_reply'])} client reply/replies")
        
        other = len(notifications) - len(by_type.get("voice_call_report", [])) - len(by_type.get("client_reply", []))
        if other > 0:
            lines.append(f"   📌 {other} other update(s)")
    else:
        lines.append("✨ <i>Quiet overnight - no new activity</i>")
    
    # Send
    message = "\n".join(lines)
    if _send_telegram(message):
        logger.info("Morning digest sent")
        clear_queue()
    else:
        logger.error("Failed to send morning digest")


def send_evening_digest():
    """Send consolidated evening digest."""
    logger.info("Preparing evening digest...")
    
    # Get day's notifications (last 14 hours to catch everything since morning)
    notifications = get_queued_notifications(since_hours=14)
    
    lines = [
        "🌙 <b>EVENING DIGEST</b>",
        f"📅 {datetime.now().strftime('%A, %B %d, %Y')}",
        ""
    ]
    
    # Pipeline summary
    pipeline = get_pipeline_summary()
    if pipeline:
        lines.append(pipeline)
        lines.append("")
    
    # Queued notifications summary
    if notifications:
        by_type = {}
        for n in notifications:
            t = n["type"]
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(n)
        
        lines.append("<b>📬 Today's Activity</b>")
        
        if "voice_call_report" in by_type:
            calls = by_type["voice_call_report"]
            hot = sum(1 for c in calls if c.get("metadata", {}).get("lead_quality") == "hot")
            warm = sum(1 for c in calls if c.get("metadata", {}).get("lead_quality") == "warm")
            total_duration = sum(c.get("metadata", {}).get("duration", 0) for c in calls)
            
            lines.append(f"   📞 {len(calls)} Voice AI call(s) ({total_duration // 60}m total)")
            if hot:
                lines.append(f"      🔥 {hot} hot")
            if warm:
                lines.append(f"      🟡 {warm} warm")
        
        if "lead_update" in by_type:
            lines.append(f"   📊 {len(by_type['lead_update'])} pipeline update(s)")
        
        if "client_reply" in by_type:
            lines.append(f"   💬 {len(by_type['client_reply'])} client reply/replies")
        
        if "tower_sync" in by_type:
            lines.append(f"   🔄 {len(by_type['tower_sync'])} sync update(s)")
        
        # Show any issues
        issues = [n for n in notifications if n.get("metadata", {}).get("status") == "error"]
        if issues:
            lines.append(f"\n⚠️ <b>{len(issues)} issue(s) need attention</b>")
    else:
        lines.append("✨ <i>Quiet day - no significant activity</i>")
    
    lines.append("")
    lines.append("🌟 <i>Tomorrow's a new day!</i>")
    
    # Send
    message = "\n".join(lines)
    if _send_telegram(message):
        logger.info("Evening digest sent")
        clear_queue()
    else:
        logger.error("Failed to send evening digest")


def main():
    if len(sys.argv) < 2:
        print("Usage: python send_digest.py [morning|evening]")
        sys.exit(1)
    
    digest_type = sys.argv[1].lower()
    
    if digest_type == "morning":
        send_morning_digest()
    elif digest_type == "evening":
        send_evening_digest()
    else:
        print(f"Unknown digest type: {digest_type}")
        sys.exit(1)


if __name__ == "__main__":
    main()
