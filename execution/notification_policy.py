#!/usr/bin/env python3
"""
Notification Policy — Controls what gets sent to Telegram and when.

POLICY:
- Morning digest: 6:30am ET — everything from overnight
- Evening digest: 9:00pm ET — everything from the day
- Immediate notifications ONLY for:
  * Hot leads requiring callback within 1 hour
  * Critical system failures
  * Meetings starting within 30 minutes

All other notifications are BATCHED into the digests.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Paths
QUEUE_FILE = Path("/home/clawdbot/logs/notification_queue.json")
POLICY_FILE = Path(__file__).parent / "notification_policy_config.json"

# Notification priorities
class Priority:
    IMMEDIATE = "immediate"  # Hot leads, critical failures, imminent meetings
    DIGEST = "digest"        # Everything else

# Default policy
DEFAULT_POLICY = {
    "immediate_allowed": [
        "hot_lead",           # Lead quality = hot, needs callback
        "critical_failure",   # System down, API broken
        "meeting_reminder",   # Meeting in < 30 min
        "client_reply",       # Direct reply from active client
    ],
    "digest_only": [
        "voice_call_report",  # Regular call reports
        "lead_update",        # Pipeline stage changes
        "system_health",      # Non-critical health checks
        "tower_sync",         # Cross-tower sync updates
        "fitness_update",     # Fitness tower updates
        "coaching_update",    # Coaching tower updates
    ],
    "quiet_hours": {
        "start": "22:00",     # 10pm
        "end": "07:00",       # 7am
        "timezone": "America/New_York"
    },
    "digest_times": {
        "morning": "06:30",
        "evening": "21:00",
        "timezone": "America/New_York"
    }
}


def load_policy() -> dict:
    """Load notification policy."""
    if POLICY_FILE.exists():
        try:
            return json.loads(POLICY_FILE.read_text())
        except Exception:
            pass
    return DEFAULT_POLICY


def save_policy(policy: dict):
    """Save notification policy."""
    POLICY_FILE.write_text(json.dumps(policy, indent=2))


def should_send_immediately(notification_type: str, metadata: dict = None) -> bool:
    """
    Determine if a notification should be sent immediately or queued for digest.
    
    Returns True only for truly urgent notifications.
    """
    policy = load_policy()
    
    # Check if it's an immediate-allowed type
    if notification_type in policy.get("immediate_allowed", []):
        # Additional checks for specific types
        if notification_type == "hot_lead":
            # Only if lead quality is actually "hot"
            return metadata and metadata.get("lead_quality") == "hot"
        if notification_type == "meeting_reminder":
            # Only if meeting is within 30 minutes
            return metadata and metadata.get("minutes_until", 999) <= 30
        return True
    
    # Everything else goes to digest
    return False


def queue_for_digest(notification_type: str, title: str, body: str, metadata: dict = None):
    """
    Queue a notification for the next digest instead of sending immediately.
    """
    queue = load_queue()
    
    entry = {
        "type": notification_type,
        "title": title,
        "body": body,
        "metadata": metadata or {},
        "timestamp": datetime.now().isoformat(),
    }
    
    queue.append(entry)
    save_queue(queue)
    logger.info(f"Queued notification for digest: {notification_type} - {title}")


def load_queue() -> list:
    """Load notification queue."""
    if QUEUE_FILE.exists():
        try:
            return json.loads(QUEUE_FILE.read_text())
        except Exception:
            pass
    return []


def save_queue(queue: list):
    """Save notification queue."""
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_FILE.write_text(json.dumps(queue, indent=2))


def clear_queue():
    """Clear the notification queue after sending digest."""
    save_queue([])


def get_queued_notifications(since_hours: int = 24) -> list:
    """Get notifications queued in the last N hours."""
    queue = load_queue()
    cutoff = datetime.now() - timedelta(hours=since_hours)
    
    return [
        n for n in queue 
        if datetime.fromisoformat(n["timestamp"]) > cutoff
    ]


def format_digest(notifications: list, digest_type: str = "evening") -> str:
    """
    Format queued notifications into a readable digest.
    
    Groups by type and summarizes.
    """
    if not notifications:
        return None  # No digest needed
    
    # Group by type
    by_type = {}
    for n in notifications:
        t = n["type"]
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(n)
    
    # Format
    lines = []
    
    if digest_type == "morning":
        lines.append("☀️ <b>MORNING DIGEST</b>")
        lines.append(f"📅 {datetime.now().strftime('%A, %B %d')}")
    else:
        lines.append("🌙 <b>EVENING DIGEST</b>")
        lines.append(f"📅 {datetime.now().strftime('%A, %B %d')}")
    
    lines.append("")
    
    # Voice calls
    if "voice_call_report" in by_type:
        calls = by_type["voice_call_report"]
        hot = sum(1 for c in calls if c.get("metadata", {}).get("lead_quality") == "hot")
        warm = sum(1 for c in calls if c.get("metadata", {}).get("lead_quality") == "warm")
        lines.append(f"📞 <b>Voice AI Calls:</b> {len(calls)} total")
        if hot:
            lines.append(f"   🔥 {hot} hot lead(s) - review needed!")
        if warm:
            lines.append(f"   🟡 {warm} warm lead(s)")
        lines.append("")
    
    # Lead updates
    if "lead_update" in by_type:
        updates = by_type["lead_update"]
        lines.append(f"📊 <b>Pipeline Updates:</b> {len(updates)}")
        for u in updates[:5]:  # Show top 5
            lines.append(f"   • {u['title']}")
        if len(updates) > 5:
            lines.append(f"   ... and {len(updates) - 5} more")
        lines.append("")
    
    # Client replies
    if "client_reply" in by_type:
        replies = by_type["client_reply"]
        lines.append(f"💬 <b>Client Replies:</b> {len(replies)}")
        for r in replies:
            lines.append(f"   • {r['title']}")
        lines.append("")
    
    # System health
    if "system_health" in by_type:
        health = by_type["system_health"]
        issues = [h for h in health if h.get("metadata", {}).get("status") != "ok"]
        if issues:
            lines.append(f"⚠️ <b>System Issues:</b> {len(issues)}")
            for h in issues:
                lines.append(f"   • {h['title']}")
            lines.append("")
    
    # Other
    other_types = set(by_type.keys()) - {"voice_call_report", "lead_update", "client_reply", "system_health"}
    if other_types:
        other_count = sum(len(by_type[t]) for t in other_types)
        lines.append(f"📌 <b>Other Updates:</b> {other_count}")
        for t in other_types:
            lines.append(f"   • {t}: {len(by_type[t])}")
    
    return "\n".join(lines)


# Convenience function for scripts to use
def notify(
    notification_type: str,
    title: str,
    body: str,
    metadata: dict = None,
    force_immediate: bool = False
) -> bool:
    """
    Smart notification function.
    
    - If urgent, sends immediately
    - Otherwise queues for digest
    
    Returns True if sent immediately, False if queued.
    """
    if force_immediate or should_send_immediately(notification_type, metadata):
        # Send immediately
        return _send_telegram(f"<b>{title}</b>\n\n{body}")
    else:
        # Queue for digest
        queue_for_digest(notification_type, title, body, metadata)
        return False


def _send_telegram(message: str) -> bool:
    """Send message to Telegram."""
    import urllib.request
    
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = "5692454753"
    
    if not token:
        logger.error("No TELEGRAM_BOT_TOKEN")
        return False
    
    try:
        data = json.dumps({
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }).encode()
        
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Notification Policy Manager")
    parser.add_argument("action", choices=["status", "queue", "digest", "clear", "test"])
    parser.add_argument("--type", default="evening", help="Digest type (morning/evening)")
    args = parser.parse_args()
    
    if args.action == "status":
        policy = load_policy()
        queue = load_queue()
        print(f"Queued notifications: {len(queue)}")
        print(f"Immediate allowed: {policy.get('immediate_allowed', [])}")
        
    elif args.action == "queue":
        queue = load_queue()
        for n in queue[-10:]:
            print(f"[{n['timestamp']}] {n['type']}: {n['title']}")
            
    elif args.action == "digest":
        notifications = get_queued_notifications(since_hours=12)
        digest = format_digest(notifications, args.type)
        if digest:
            print(digest)
            print("\n--- Would send above to Telegram ---")
        else:
            print("No notifications to digest")
            
    elif args.action == "clear":
        clear_queue()
        print("Queue cleared")
        
    elif args.action == "test":
        # Test queue a notification
        queue_for_digest("voice_call_report", "Test Call", "This is a test", {"lead_quality": "cold"})
        print("Test notification queued")
