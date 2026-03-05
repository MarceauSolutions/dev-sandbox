#!/usr/bin/env python3
"""
Warm Outreach SMS Tool — Send personalized outreach messages via Twilio.

Usage:
    # Send to a single contact
    python execution/warm_outreach_sms.py --name "John" --phone "+12395551234" --template gym_friend

    # Send to a list (CSV: name,phone)
    python execution/warm_outreach_sms.py --csv contacts.csv --template gym_friend

    # Preview without sending
    python execution/warm_outreach_sms.py --name "John" --phone "+12395551234" --template gym_friend --dry-run

    # List available templates
    python execution/warm_outreach_sms.py --list-templates
"""

import argparse
import csv
import os
import sys
import time
from pathlib import Path

# Load .env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip("'\"")
            if key and val and " " not in key:
                os.environ.setdefault(key, val)

TWILIO_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM = os.environ.get("TWILIO_PHONE_NUMBER", "+18552399364")

QUIZ_URL = "https://marceausolutions.com/quiz"
COACHING_URL = "https://marceausolutions.com/coaching.html"
CALENDLY_URL = "https://calendly.com/wmarceau/30min"
STRIPE_URL = "https://buy.stripe.com/14A14n29hdqU48wf5wg3601"

TEMPLATES = {
    "gym_friend": {
        "desc": "For people you know from the gym",
        "message": (
            "Hey {name}! It's William. I just launched my fitness coaching business — "
            "evidence-based training with peptide-informed protocols. "
            "I built a free body recomp calculator that gives you custom macros and a training plan. "
            "Try it out: {quiz_url}\n\n"
            "Would love your feedback. And if you know anyone looking for a coach, send them my way!"
        ),
    },
    "close_friend": {
        "desc": "For close friends/family — casual tone",
        "message": (
            "Hey {name}! You know how I've been deep in the fitness/peptide world? "
            "I officially launched my coaching business. $197/mo, custom programs, "
            "AI-powered tracking, the whole thing.\n\n"
            "Take my free quiz and tell me what you think: {quiz_url}\n\n"
            "And if you know anyone who wants to get serious about training, I'm taking clients!"
        ),
    },
    "acquaintance": {
        "desc": "For casual contacts — professional tone",
        "message": (
            "Hi {name}, it's William Marceau. I recently launched an evidence-based fitness coaching practice "
            "here in Naples. I specialize in body recomp and peptide-informed training protocols.\n\n"
            "I built a free Body Recomp Calculator — takes 2 min and gives you custom macros: {quiz_url}\n\n"
            "If this is something you or anyone you know could use, I'd love to help. "
            "Free 30-min call: {calendly_url}"
        ),
    },
    "local_business": {
        "desc": "For gym owners, med spa owners, chiropractors",
        "message": (
            "Hi {name}, I'm William Marceau — just launched a fitness coaching practice here in Naples. "
            "I specialize in evidence-based training with peptide-informed protocols "
            "(I coordinate with licensed physicians).\n\n"
            "I'd love to explore a referral partnership. I send clients your way, you send fitness-interested clients mine. "
            "Would a quick 15-min call make sense?\n\n"
            "Book here: {calendly_url}"
        ),
    },
    "follow_up": {
        "desc": "Follow-up for anyone who didn't respond to first message",
        "message": (
            "Hey {name}, just following up! I know you're busy. "
            "Quick reminder about my free Body Recomp Calculator: {quiz_url}\n\n"
            "Takes 2 minutes, gives you personalized macros and training recommendations. "
            "No strings attached. Let me know what you think!"
        ),
    },
}


def send_sms(to_phone: str, body: str, dry_run: bool = False) -> dict:
    """Send SMS via Twilio API."""
    if dry_run:
        return {"status": "dry_run", "to": to_phone, "body": body}

    if not TWILIO_SID or not TWILIO_TOKEN:
        print("ERROR: Twilio credentials not found in .env")
        sys.exit(1)

    import urllib.request
    import urllib.parse
    import json
    import base64

    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
    data = urllib.parse.urlencode({
        "To": to_phone,
        "From": TWILIO_FROM,
        "Body": body,
    }).encode()

    auth = base64.b64encode(f"{TWILIO_SID}:{TWILIO_TOKEN}".encode()).decode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Basic {auth}")

    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        return {"status": "sent", "sid": result.get("sid", ""), "to": to_phone}
    except urllib.error.HTTPError as e:
        error = json.loads(e.read())
        return {"status": "error", "to": to_phone, "error": error.get("message", str(e))}


def format_message(template_key: str, name: str) -> str:
    """Format a template with contact name and URLs."""
    tmpl = TEMPLATES[template_key]["message"]
    return tmpl.format(
        name=name,
        quiz_url=QUIZ_URL,
        coaching_url=COACHING_URL,
        calendly_url=CALENDLY_URL,
        stripe_url=STRIPE_URL,
    )


def main():
    parser = argparse.ArgumentParser(description="Warm Outreach SMS Tool")
    parser.add_argument("--name", "-n", help="Contact name")
    parser.add_argument("--phone", "-p", help="Phone number (E.164: +12395551234)")
    parser.add_argument("--template", "-t", help="Message template name")
    parser.add_argument("--csv", help="CSV file with name,phone columns")
    parser.add_argument("--dry-run", action="store_true", help="Preview messages without sending")
    parser.add_argument("--list-templates", action="store_true", help="Show available templates")
    parser.add_argument("--delay", type=float, default=2.0, help="Seconds between messages (default: 2)")
    args = parser.parse_args()

    if args.list_templates:
        print("Available templates:\n")
        for key, tmpl in TEMPLATES.items():
            print(f"  {key:20s} — {tmpl['desc']}")
            preview = format_message(key, "John")
            print(f"  {'':20s}   Preview: {preview[:80]}...")
            print()
        return

    if args.csv:
        if not args.template:
            print("ERROR: --template required with --csv")
            sys.exit(1)
        with open(args.csv) as f:
            reader = csv.DictReader(f)
            contacts = list(reader)
        print(f"Sending {len(contacts)} messages with template '{args.template}'")
        if args.dry_run:
            print("(DRY RUN — no messages will be sent)\n")
        for i, contact in enumerate(contacts):
            name = contact.get("name", contact.get("Name", ""))
            phone = contact.get("phone", contact.get("Phone", ""))
            if not name or not phone:
                print(f"  SKIP row {i+1}: missing name or phone")
                continue
            body = format_message(args.template, name)
            result = send_sms(phone, body, dry_run=args.dry_run)
            status = result["status"]
            print(f"  [{status}] {name} ({phone})")
            if not args.dry_run and i < len(contacts) - 1:
                time.sleep(args.delay)
        return

    if not args.name or not args.phone or not args.template:
        parser.print_help()
        print("\nExample: python execution/warm_outreach_sms.py --name 'John' --phone '+12395551234' --template gym_friend --dry-run")
        return

    if args.template not in TEMPLATES:
        print(f"ERROR: Unknown template '{args.template}'. Available: {', '.join(TEMPLATES.keys())}")
        sys.exit(1)

    body = format_message(args.template, args.name)
    print(f"To: {args.phone}")
    print(f"Template: {args.template}")
    print(f"Message ({len(body)} chars):\n")
    print(body)
    print()

    if args.dry_run:
        print("[DRY RUN — message not sent]")
    else:
        result = send_sms(args.phone, body)
        if result["status"] == "sent":
            print(f"[SENT] SID: {result['sid']}")
        else:
            print(f"[ERROR] {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
