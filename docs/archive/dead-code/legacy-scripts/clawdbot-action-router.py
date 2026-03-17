#!/usr/bin/env python3
"""
Route Clawdbot notifications to appropriate actions.

Usage:
    python clawdbot-action-router.py <notification.json>
    python clawdbot-action-router.py --check  # Check for unprocessed notifications
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

DEV_SANDBOX = Path("/Users/williammarceaujr./dev-sandbox")
NOTIFICATIONS_DIR = DEV_SANDBOX / ".tmp" / "clawdbot-notifications"
NOTIFICATIONS_LOG = NOTIFICATIONS_DIR / "actions.log"
INBOX = DEV_SANDBOX / ".tmp" / "clawdbot-inbox"


def log_action(request_id: str, action: str, details: str = ""):
    """Log action taken."""
    NOTIFICATIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    with open(NOTIFICATIONS_LOG, "a") as f:
        f.write(f"[{timestamp}] {request_id}: {action} - {details}\n")


def notify_terminal(message: str, title: str = "Clawdbot"):
    """Display notification in terminal and macOS notification center."""
    print(f"\n{'='*60}")
    print(f"🤖 {title}")
    print(f"{'='*60}")
    print(message)
    print(f"{'='*60}\n")

    # Also send macOS notification
    try:
        subprocess.run([
            "osascript", "-e",
            f'display notification "{message[:100]}..." with title "{title}"'
        ], capture_output=True)
    except Exception:
        pass


def route_notification(payload: dict):
    """Route notification to appropriate handler."""
    request_id = payload.get("request_id", "unknown")
    notification_type = payload.get("type", "simple_notification")
    summary = payload.get("summary", "No summary")
    suggested_project = payload.get("suggested_project", "")
    files = payload.get("files", [])

    if notification_type == "content_ready":
        # Content generated - route to project
        file_list = "\n".join([f"  - {f.get('name', f)}" for f in files]) if files else "  (no files listed)"
        notify_terminal(
            f"Request: {request_id}\n"
            f"Summary: {summary}\n"
            f"Files:\n{file_list}\n"
            f"Suggested project: {suggested_project}\n"
            f"\nNext steps:\n"
            f"1. ./scripts/sync-clawdbot-outputs.sh\n"
            f"2. python scripts/route-clawdbot-contribution.py route {request_id} {suggested_project}",
            title="Clawdbot Content Ready"
        )
        log_action(request_id, "content_ready", f"Project: {suggested_project}")

    elif notification_type == "complex_dev_request":
        # Complex request - route to Ralph
        notify_terminal(
            f"Request: {request_id}\n"
            f"Summary: {summary}\n"
            f"\n⚠️ This looks like a COMPLEX DEVELOPMENT TASK.\n"
            f"Clawdbot has created a PRD outline.\n"
            f"\nNext steps:\n"
            f"1. ./scripts/sync-clawdbot-outputs.sh\n"
            f"2. Review PRD: .tmp/clawdbot-inbox/{request_id}/prd-outline.json\n"
            f"3. Consider using Ralph for implementation",
            title="Clawdbot → Ralph Handoff"
        )
        log_action(request_id, "complex_dev_request", "Routed to Ralph consideration")

    elif notification_type == "research_complete":
        # Research done - notify and route
        notify_terminal(
            f"Request: {request_id}\n"
            f"Summary: {summary}\n"
            f"Suggested project: {suggested_project}\n"
            f"\nResearch files ready for review.\n"
            f"\nNext steps:\n"
            f"1. ./scripts/sync-clawdbot-outputs.sh\n"
            f"2. Review files in .tmp/clawdbot-inbox/{request_id}/",
            title="Clawdbot Research Complete"
        )
        log_action(request_id, "research_complete", f"Project: {suggested_project}")

    elif notification_type == "error":
        # Error occurred
        error_msg = payload.get("error", "Unknown error")
        notify_terminal(
            f"Request: {request_id}\n"
            f"Error: {error_msg}\n"
            f"\nCheck Clawdbot logs:\n"
            f"ssh clawdbot@44.193.244.59 'journalctl -u clawdbot --since \"1 hour ago\"'",
            title="⚠️ Clawdbot Error"
        )
        log_action(request_id, "error", error_msg)

    else:
        # Simple notification
        notify_terminal(
            f"Request: {request_id}\n"
            f"{summary}",
            title="Clawdbot Notification"
        )
        log_action(request_id, notification_type, summary)


def check_unprocessed():
    """Check for unprocessed notifications in inbox."""
    print("\n🤖 Clawdbot Notification Check")
    print("=" * 40)

    # Check inbox for items without MANIFEST.json (unprocessed)
    unprocessed = []
    if INBOX.exists():
        for item in INBOX.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                notification_file = item / "notification.json"
                if notification_file.exists():
                    try:
                        payload = json.loads(notification_file.read_text())
                        unprocessed.append((item.name, payload))
                    except json.JSONDecodeError:
                        unprocessed.append((item.name, {"summary": "Invalid JSON"}))
                else:
                    unprocessed.append((item.name, {"summary": "No notification.json"}))

    if unprocessed:
        print(f"\n📥 {len(unprocessed)} unprocessed item(s):\n")
        for request_id, payload in unprocessed:
            notification_type = payload.get("type", "unknown")
            summary = payload.get("summary", "No summary")
            print(f"  [{notification_type}] {request_id}")
            print(f"      {summary[:60]}...")
            print()
    else:
        print("\n✅ No unprocessed notifications")

    # Show recent action log
    if NOTIFICATIONS_LOG.exists():
        print("\n📋 Recent actions:")
        lines = NOTIFICATIONS_LOG.read_text().strip().split("\n")
        for line in lines[-5:]:  # Last 5 actions
            print(f"  {line}")

    print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "--check":
        check_unprocessed()
    else:
        # Load notification from file
        notification_file = Path(sys.argv[1])
        if notification_file.exists():
            payload = json.loads(notification_file.read_text())
            route_notification(payload)
        else:
            print(f"File not found: {notification_file}")
            sys.exit(1)


if __name__ == "__main__":
    main()
