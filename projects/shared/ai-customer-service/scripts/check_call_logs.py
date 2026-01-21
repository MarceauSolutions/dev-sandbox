#!/usr/bin/env python3
"""Check Twilio call logs and debug issues."""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../../../.env"))

from twilio.rest import Client
from datetime import datetime, timedelta

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")


def check_recent_calls(limit=10):
    """List recent calls with status."""
    client = Client(ACCOUNT_SID, AUTH_TOKEN)

    print("="*70)
    print("RECENT TWILIO CALLS")
    print("="*70)

    calls = client.calls.list(limit=limit)

    for call in calls:
        status_icon = {
            "completed": "✅",
            "failed": "❌",
            "busy": "📞",
            "no-answer": "📵",
            "canceled": "🚫",
            "in-progress": "🔄"
        }.get(call.status, "❓")

        print(f"\n{status_icon} Call SID: {call.sid}")
        print(f"   To: {call.to}")
        print(f"   Status: {call.status}")
        print(f"   Duration: {call.duration}s")
        print(f"   Started: {call.start_time}")

        # Check for errors
        if call.status == "failed":
            try:
                # Get call details for error info
                details = client.calls(call.sid).fetch()
                if hasattr(details, 'error_code') and details.error_code:
                    print(f"   ⚠️ Error Code: {details.error_code}")
                if hasattr(details, 'error_message') and details.error_message:
                    print(f"   ⚠️ Error: {details.error_message}")
            except Exception as e:
                print(f"   Could not fetch details: {e}")


def check_call_notifications(call_sid):
    """Check notifications/errors for a specific call."""
    client = Client(ACCOUNT_SID, AUTH_TOKEN)

    print(f"\n{'='*70}")
    print(f"NOTIFICATIONS FOR CALL: {call_sid}")
    print(f"{'='*70}")

    try:
        notifications = client.calls(call_sid).notifications.list()
        if notifications:
            for n in notifications:
                print(f"\n  Level: {n.log}")
                print(f"  Code: {n.error_code}")
                print(f"  Message: {n.message_text}")
                print(f"  URL: {n.request_url}")
        else:
            print("  No notifications found")
    except Exception as e:
        print(f"  Error fetching notifications: {e}")


def check_debugger_alerts():
    """Check Twilio Debugger for recent alerts."""
    client = Client(ACCOUNT_SID, AUTH_TOKEN)

    print(f"\n{'='*70}")
    print("RECENT DEBUGGER ALERTS")
    print(f"{'='*70}")

    try:
        alerts = client.monitor.alerts.list(limit=10)
        for alert in alerts:
            print(f"\n  Date: {alert.date_created}")
            print(f"  Error Code: {alert.error_code}")
            print(f"  Log Level: {alert.log_level}")
            print(f"  Message: {alert.alert_text[:200] if alert.alert_text else 'N/A'}...")
    except Exception as e:
        print(f"  Error fetching alerts: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Check Twilio call logs")
    parser.add_argument("--call", "-c", help="Check specific call SID")
    parser.add_argument("--limit", "-l", type=int, default=10, help="Number of calls to list")
    parser.add_argument("--alerts", "-a", action="store_true", help="Show debugger alerts")

    args = parser.parse_args()

    if args.call:
        check_call_notifications(args.call)
    elif args.alerts:
        check_debugger_alerts()
    else:
        check_recent_calls(args.limit)
