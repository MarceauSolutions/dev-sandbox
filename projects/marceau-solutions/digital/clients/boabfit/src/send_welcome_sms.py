#!/usr/bin/env python3
"""
BoabFit 6-Week Program Welcome SMS — Batch sender using Twilio.

Sends Julia's welcome message to all clients who signed up via TikTok form,
then sends Julia a summary of who received the message.

Usage:
  python projects/boabfit/src/send_welcome_sms.py --dry-run     # Preview only
  python projects/boabfit/src/send_welcome_sms.py --test         # Send to William only
  python projects/boabfit/src/send_welcome_sms.py --send         # Send to all clients + notify Julia
"""

import os
import sys
import json
import time as time_mod
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
except ImportError:
    print("ERROR: twilio package not installed. pip install twilio")
    sys.exit(1)


# Julia's welcome message (with TCPA opt-out appended)
WELCOME_MESSAGE = (
    "Hey girl! \U0001f496  You filled out my TikTok form about the BOABFIT 6-week "
    "workout program, so I wanted to make sure you saw that we start TODAY! \u2728\n\n"
    "If you've been wanting to get back into a routine, feel stronger, and start "
    "seeing your body change, this is your sign to jump in and do it with me \U0001f4aa\u2728\U0001f496\n\n"
    "The next 6 weeks are going to be so good and I'm so excited to get summer "
    "body ready with you \u2600\ufe0f\u2728\n\n"
    "Grab your spot here:\n"
    "www.boabfit.com/6week\n\n"
    "Let's do this!! \U0001f495\n\n"
    "Reply STOP to opt out."
)

# Phone numbers
WILLIAM_PHONE = "+12393985676"
JULIA_PHONE = "+12393985197"  # Julz m — Julia Marceau herself
FROM_NUMBER = "+18552399364"  # William's 855 toll-free


def load_roster():
    """Load client roster from JSON."""
    roster_path = ROOT / "projects" / "boabfit" / "clients" / "roster.json"
    with open(roster_path) as f:
        return json.load(f)


def format_phone(phone: str) -> str:
    """Format phone number to E.164."""
    cleaned = ''.join(c for c in phone if c.isdigit())
    if len(cleaned) == 10:
        return f"+1{cleaned}"
    elif len(cleaned) == 11 and cleaned.startswith('1'):
        return f"+{cleaned}"
    return None


def send_sms(client, to: str, message: str, from_number: str) -> dict:
    """Send a single SMS and return result."""
    try:
        sms = client.messages.create(
            body=message,
            from_=from_number,
            to=to
        )
        return {
            "success": True,
            "sid": sms.sid,
            "status": sms.status,
            "to": to
        }
    except TwilioRestException as e:
        return {
            "success": False,
            "error": e.msg,
            "code": e.code,
            "to": to
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "to": to
        }


def build_julia_summary(roster, sent_names, failed_entries):
    """Build a summary text to send to Julia after the campaign."""
    now = datetime.now().strftime('%I:%M %p')
    lines = [
        f"Hey Julia! Your BOABFIT 6-week welcome text was sent this morning at {now} ET.",
        f"",
        f"Successfully sent to {len(sent_names)} clients:",
    ]
    for name in sent_names:
        lines.append(f"  - {name}")

    if failed_entries:
        lines.append(f"")
        lines.append(f"Failed ({len(failed_entries)}):")
        for e in failed_entries:
            lines.append(f"  - {e['name']}: {e['error']}")

    lines.append(f"")
    lines.append(f"Total: {len(sent_names)}/{len(roster)} delivered.")
    lines.append(f"Let me know if you need anything else!")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="BoabFit 6-Week Welcome SMS")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true', help='Preview messages without sending')
    group.add_argument('--test', action='store_true', help='Send test to William only')
    group.add_argument('--send', action='store_true', help='Send to all clients + notify Julia')
    args = parser.parse_args()

    roster = load_roster()
    print(f"\n{'='*60}")
    print(f"BOABFIT 6-WEEK WELCOME SMS")
    print(f"{'='*60}")
    print(f"Clients in roster: {len(roster)}")
    print(f"From number: {FROM_NUMBER}")
    print(f"Message length: {len(WELCOME_MESSAGE)} chars")
    print(f"Time: {datetime.now().strftime('%I:%M %p ET')}")

    if args.dry_run:
        print(f"\n--- DRY RUN (no messages sent) ---\n")
        print(f"MESSAGE:\n{WELCOME_MESSAGE}\n")
        print(f"RECIPIENTS:")
        for i, c in enumerate(roster, 1):
            phone = format_phone(c['phone'])
            status = "VALID" if phone else "INVALID"
            print(f"  {i:2d}. {c['name']:<25s} {phone or c['phone']:<16s} [{status}]")
        valid = sum(1 for c in roster if format_phone(c['phone']))
        print(f"\nValid numbers: {valid}/{len(roster)}")
        print(f"Estimated cost: ${valid * 0.0079:.2f} (clients) + $0.0079 (Julia summary) = ${(valid + 1) * 0.0079:.2f}")
        print(f"\nJulia ({JULIA_PHONE}) will receive a summary text after send.")
        return

    # Initialize Twilio
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    if not account_sid or not auth_token:
        print("ERROR: Missing TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN in .env")
        sys.exit(1)
    client = Client(account_sid, auth_token)

    if args.test:
        print(f"\n--- TEST MODE: Sending to William ({WILLIAM_PHONE}) ---\n")
        result = send_sms(client, WILLIAM_PHONE, WELCOME_MESSAGE, FROM_NUMBER)
        if result['success']:
            print(f"  ✓ Test sent! SID: {result['sid']} Status: {result['status']}")
        else:
            print(f"  ✗ Failed: {result['error']}")
        return

    if args.send:
        print(f"\n--- SENDING TO ALL {len(roster)} CLIENTS ---\n")
        sent_names = []
        failed_entries = []

        for i, c in enumerate(roster, 1):
            phone = format_phone(c['phone'])
            if not phone:
                print(f"  [{i:2d}/{len(roster)}] SKIP {c['name']} — invalid number: {c['phone']}")
                failed_entries.append({"name": c['name'], "error": "invalid number"})
                continue

            print(f"  [{i:2d}/{len(roster)}] Sending to {c['name']} ({phone})...", end=" ")
            result = send_sms(client, phone, WELCOME_MESSAGE, FROM_NUMBER)

            if result['success']:
                print(f"✓ {result['status']}")
                sent_names.append(c['name'])
            else:
                print(f"✗ {result['error']}")
                failed_entries.append({"name": c['name'], "error": result['error']})

            # Rate limit: 1 second between messages
            if i < len(roster):
                time_mod.sleep(1)

        # Send Julia her summary
        print(f"\n--- SENDING SUMMARY TO JULIA ({JULIA_PHONE}) ---")
        summary = build_julia_summary(roster, sent_names, failed_entries)
        result = send_sms(client, JULIA_PHONE, summary, FROM_NUMBER)
        if result['success']:
            print(f"  ✓ Julia notified! SID: {result['sid']}")
        else:
            print(f"  ✗ Failed to notify Julia: {result['error']}")

        print(f"\n{'='*60}")
        print(f"COMPLETE: {len(sent_names)}/{len(roster)} sent, {len(failed_entries)} failed")
        print(f"Cost: ~${(len(sent_names) + 1) * 0.0079:.2f}")
        if failed_entries:
            print(f"\nFailed:")
            for e in failed_entries:
                print(f"  - {e['name']}: {e['error']}")
        print(f"{'='*60}")

        # Save send log
        log_path = ROOT / "projects" / "boabfit" / "clients" / "welcome_sms_log.json"
        with open(log_path, 'w') as f:
            json.dump({
                "campaign": "boabfit-6week-welcome",
                "sent_at": datetime.now().isoformat(),
                "from_number": FROM_NUMBER,
                "sent_to": sent_names,
                "failed": failed_entries,
                "julia_notified": result.get('success', False)
            }, f, indent=2)
        print(f"\nLog saved: {log_path}")


if __name__ == "__main__":
    main()
