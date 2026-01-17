#!/usr/bin/env python3
"""
Send follow-up SMS to leads from a previous campaign.

This script reads the sms_campaigns.json file to get phone numbers
that were previously contacted and sends a follow-up message.

Usage:
    # Dry run (preview)
    python -m src.send_followup --message "Your message here" --dry-run

    # Send for real
    python -m src.send_followup --message "Your message here" --for-real

    # Send with custom delay
    python -m src.send_followup --message "Your message" --for-real --delay 3.0
"""

import argparse
import json
import time
import os
from pathlib import Path
from datetime import datetime
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


def load_campaign_phones(campaigns_file: Path) -> list:
    """Load phone numbers from previous campaign."""
    if not campaigns_file.exists():
        print(f"Error: {campaigns_file} not found")
        return []

    with open(campaigns_file) as f:
        data = json.load(f)

    # Extract unique phone numbers and business names
    phones = []
    seen = set()

    for record in data.get("records", []):
        phone = record.get("phone", "")
        if phone and phone not in seen:
            phones.append({
                "phone": phone,
                "business_name": record.get("business_name", ""),
                "lead_id": record.get("lead_id", ""),
                "original_sent_at": record.get("sent_at", "")
            })
            seen.add(phone)

    return phones


def send_followup(
    phones: list,
    message: str,
    dry_run: bool = True,
    delay_seconds: float = 2.0
) -> dict:
    """Send follow-up SMS to all phones."""

    # Initialize Twilio client
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_phone = os.getenv("TWILIO_PHONE_NUMBER")

    if not all([account_sid, auth_token, from_phone]):
        print("Error: Missing Twilio credentials in .env")
        return {"error": "Missing Twilio credentials"}

    client = Client(account_sid, auth_token) if not dry_run else None

    stats = {
        "total": len(phones),
        "sent": 0,
        "failed": 0,
        "dry_run": dry_run,
        "records": []
    }

    print(f"\n{'='*60}")
    print(f"FOLLOW-UP SMS CAMPAIGN")
    print(f"{'='*60}")
    print(f"Total contacts: {len(phones)}")
    print(f"Mode: {'DRY RUN (preview only)' if dry_run else 'LIVE SENDING'}")
    print(f"Message ({len(message)} chars):")
    print(f"  {message}")
    print(f"{'='*60}\n")

    if not dry_run:
        print("Starting in 5 seconds... (Ctrl+C to cancel)")
        time.sleep(5)

    for i, contact in enumerate(phones, 1):
        phone = contact["phone"]
        business = contact["business_name"]

        print(f"[{i}/{len(phones)}] {business} ({phone})")

        if dry_run:
            print(f"  [DRY RUN] Would send: {message[:50]}...")
            stats["sent"] += 1
            stats["records"].append({
                "phone": phone,
                "business_name": business,
                "status": "dry_run"
            })
        else:
            try:
                msg = client.messages.create(
                    body=message,
                    from_=from_phone,
                    to=phone
                )
                print(f"  ✓ Sent: {msg.sid}")
                stats["sent"] += 1
                stats["records"].append({
                    "phone": phone,
                    "business_name": business,
                    "status": "sent",
                    "message_sid": msg.sid,
                    "sent_at": datetime.now().isoformat()
                })
            except TwilioRestException as e:
                print(f"  ✗ Error: {e}")
                stats["failed"] += 1
                stats["records"].append({
                    "phone": phone,
                    "business_name": business,
                    "status": "error",
                    "error": str(e)
                })

            # Delay between messages
            if i < len(phones):
                time.sleep(delay_seconds)

    print(f"\n{'='*60}")
    print(f"CAMPAIGN COMPLETE")
    print(f"{'='*60}")
    print(f"Sent: {stats['sent']}")
    print(f"Failed: {stats['failed']}")
    print(f"{'='*60}\n")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Send follow-up SMS to previous campaign contacts")

    parser.add_argument(
        "--message", "-m",
        required=True,
        help="The follow-up message to send"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview without sending (default)"
    )
    parser.add_argument(
        "--for-real",
        action="store_true",
        help="Actually send the messages"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay between messages in seconds (default: 2.0)"
    )
    parser.add_argument(
        "--campaigns-file",
        default="output/sms_campaigns.json",
        help="Path to campaigns JSON file"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of messages to send"
    )

    args = parser.parse_args()

    # Determine mode
    dry_run = not args.for_real

    # Load phone numbers from previous campaign
    project_root = Path(__file__).parent.parent
    campaigns_file = project_root / args.campaigns_file

    phones = load_campaign_phones(campaigns_file)

    if not phones:
        print("No phone numbers found in campaign file")
        return 1

    # Apply limit if specified
    if args.limit:
        phones = phones[:args.limit]
        print(f"Limited to {len(phones)} contacts")

    # Validate message
    if len(args.message) > 160:
        print(f"Warning: Message is {len(args.message)} chars (over 160 limit)")

    # Ensure TCPA compliance
    if "STOP" not in args.message.upper() and "opt" not in args.message.lower():
        print("\n⚠️  WARNING: Message doesn't include opt-out language!")
        print("TCPA requires opt-out instructions in SMS messages.")
        print("Consider adding: 'Reply STOP to opt out'")
        if not dry_run:
            response = input("\nContinue anyway? (yes/no): ")
            if response.lower() != "yes":
                print("Cancelled.")
                return 1

    # Send follow-up messages
    stats = send_followup(
        phones=phones,
        message=args.message,
        dry_run=dry_run,
        delay_seconds=args.delay
    )

    # Save results
    if not dry_run:
        results_file = project_root / "output" / f"followup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, "w") as f:
            json.dump(stats, f, indent=2)
        print(f"Results saved to: {results_file}")

    return 0


if __name__ == "__main__":
    exit(main())
