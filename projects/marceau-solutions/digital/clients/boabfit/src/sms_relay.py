#!/usr/bin/env python3
"""
BoabFit SMS Relay — Two-way SMS proxy between Julia and her clients.

Clients text the 855 number → forwarded to Julia with context.
Julia replies → forwarded to the client she's responding to.

How it works:
  - Polls Twilio inbox every 30 seconds for new inbound messages
  - If sender is a BoabFit client → forward to Julia with their name
  - If sender is Julia → forward her reply to the last client who texted
  - Julia can text "TO [name]: message" to pick a specific client
  - All conversations are logged

Usage:
  python projects/boabfit/src/sms_relay.py              # Run relay (polls every 30s)
  python projects/boabfit/src/sms_relay.py --check       # One-time inbox check
  python projects/boabfit/src/sms_relay.py --status      # Show relay state
"""

import os
import sys
import json
import time as time_mod
import re
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta

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


# Config
JULIA_PHONE = "+12393985197"
WILLIAM_PHONE = "+12393985676"
FROM_NUMBER = "+18552399364"
POLL_INTERVAL = 30  # seconds

# State file for tracking conversations
STATE_DIR = ROOT / "projects" / "boabfit" / "clients"
STATE_FILE = STATE_DIR / "relay_state.json"
CONVO_LOG = STATE_DIR / "conversations.jsonl"


def load_roster() -> dict:
    """Load client roster and build phone→name lookup."""
    roster_path = ROOT / "projects" / "boabfit" / "clients" / "roster.json"
    with open(roster_path) as f:
        clients = json.load(f)

    lookup = {}
    for c in clients:
        phone = format_phone(c['phone'])
        if phone:
            lookup[phone] = c['name']
    return lookup


def format_phone(phone: str) -> str:
    """Format phone number to E.164."""
    cleaned = ''.join(c for c in phone if c.isdigit())
    if len(cleaned) == 10:
        return f"+1{cleaned}"
    elif len(cleaned) == 11 and cleaned.startswith('1'):
        return f"+{cleaned}"
    return None


def load_state() -> dict:
    """Load relay state (last processed message, active conversation)."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "last_processed_sid": None,
        "last_processed_time": None,
        "active_client_phone": None,
        "active_client_name": None
    }


def save_state(state: dict):
    """Persist relay state."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def log_conversation(direction: str, from_name: str, to_name: str, message: str):
    """Append to conversation log."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "direction": direction,
        "from": from_name,
        "to": to_name,
        "message": message
    }
    with open(CONVO_LOG, 'a') as f:
        f.write(json.dumps(entry) + '\n')


def send_sms(client, to: str, message: str) -> dict:
    """Send SMS via Twilio."""
    try:
        sms = client.messages.create(
            body=message,
            from_=FROM_NUMBER,
            to=to
        )
        return {"success": True, "sid": sms.sid, "status": sms.status}
    except TwilioRestException as e:
        return {"success": False, "error": e.msg}
    except Exception as e:
        return {"success": False, "error": str(e)}


def find_client_by_name(name_query: str, client_lookup: dict) -> tuple:
    """Find a client by partial name match. Returns (phone, name) or (None, None)."""
    name_query = name_query.strip().lower()
    matches = []
    for phone, name in client_lookup.items():
        if name_query in name.lower():
            matches.append((phone, name))

    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        # Return first match but could be ambiguous
        return matches[0]
    return (None, None)


def process_inbound(twilio_client, client_lookup: dict, state: dict):
    """Check for new inbound messages and relay them."""
    # Fetch recent inbound messages to the 855 number
    since = datetime.now(timezone.utc) - timedelta(minutes=5)
    messages = twilio_client.messages.list(
        to=FROM_NUMBER,
        date_sent_after=since,
        limit=20
    )

    if not messages:
        return

    # Process newest first, skip already-processed
    last_sid = state.get("last_processed_sid")
    new_messages = []

    for msg in messages:
        if msg.sid == last_sid:
            break
        new_messages.append(msg)

    # Process oldest-first
    new_messages.reverse()

    for msg in new_messages:
        sender = msg.from_
        body = msg.body.strip()
        timestamp = datetime.now().strftime('%I:%M %p')

        # Handle STOP/opt-out (let Twilio handle natively, just log)
        if body.upper() in ['STOP', 'STOPALL', 'UNSUBSCRIBE', 'CANCEL', 'END', 'QUIT']:
            print(f"  ⛔ OPT-OUT from {sender}: {body}")
            log_conversation("opt_out", sender, "system", body)
            state["last_processed_sid"] = msg.sid
            save_state(state)
            # Notify Julia about opt-out
            client_name = client_lookup.get(sender, "Unknown")
            send_sms(twilio_client, JULIA_PHONE,
                     f"⛔ {client_name} ({sender}) opted out of texts.")
            continue

        if sender == JULIA_PHONE:
            # Julia is replying — route to a client
            target_phone = None
            target_name = None
            relay_message = body

            # Check for "TO [name]: message" format
            to_match = re.match(r'^TO\s+(.+?):\s*(.+)$', body, re.IGNORECASE | re.DOTALL)
            if to_match:
                name_query = to_match.group(1)
                relay_message = to_match.group(2)
                target_phone, target_name = find_client_by_name(name_query, client_lookup)
                if not target_phone:
                    send_sms(twilio_client, JULIA_PHONE,
                             f"❌ No client found matching \"{name_query}\". "
                             f"Try: TO [first name]: [message]")
                    state["last_processed_sid"] = msg.sid
                    save_state(state)
                    continue
            else:
                # Reply to the last active client
                target_phone = state.get("active_client_phone")
                target_name = state.get("active_client_name")

            if not target_phone:
                send_sms(twilio_client, JULIA_PHONE,
                         "❌ No active conversation. Use: TO [name]: [your message]")
                state["last_processed_sid"] = msg.sid
                save_state(state)
                continue

            # Forward Julia's reply to the client
            result = send_sms(twilio_client, target_phone, relay_message)
            if result['success']:
                print(f"  → Julia → {target_name} ({target_phone}): {relay_message[:60]}...")
                log_conversation("julia_to_client", "Julia", target_name, relay_message)
            else:
                print(f"  ✗ Failed to relay to {target_name}: {result['error']}")
                send_sms(twilio_client, JULIA_PHONE,
                         f"❌ Failed to send to {target_name}: {result['error']}")

        elif sender in client_lookup:
            # A BoabFit client is texting in — forward to Julia
            client_name = client_lookup[sender]

            # Set this client as Julia's active conversation
            state["active_client_phone"] = sender
            state["active_client_name"] = client_name

            # Forward to Julia with context
            forward_msg = f"📩 {client_name} ({sender}):\n{body}"
            result = send_sms(twilio_client, JULIA_PHONE, forward_msg)
            if result['success']:
                print(f"  ← {client_name} → Julia: {body[:60]}...")
                log_conversation("client_to_julia", client_name, "Julia", body)
            else:
                print(f"  ✗ Failed to forward to Julia: {result['error']}")

        else:
            # Unknown number — notify William (might be non-BoabFit)
            print(f"  ? Unknown sender {sender}: {body[:60]}...")
            log_conversation("unknown", sender, "system", body)

        state["last_processed_sid"] = msg.sid
        state["last_processed_time"] = datetime.now().isoformat()
        save_state(state)


def show_status(state: dict, client_lookup: dict):
    """Show current relay status."""
    print(f"\n{'='*50}")
    print(f"BOABFIT SMS RELAY STATUS")
    print(f"{'='*50}")
    print(f"From number: {FROM_NUMBER}")
    print(f"Julia: {JULIA_PHONE}")
    print(f"Clients tracked: {len(client_lookup)}")
    print(f"Active conversation: {state.get('active_client_name', 'None')} "
          f"({state.get('active_client_phone', 'N/A')})")
    print(f"Last processed: {state.get('last_processed_time', 'Never')}")

    if CONVO_LOG.exists():
        with open(CONVO_LOG) as f:
            lines = f.readlines()
        print(f"Total conversations logged: {len(lines)}")
    print(f"{'='*50}")


def main():
    parser = argparse.ArgumentParser(description="BoabFit SMS Relay")
    parser.add_argument('--check', action='store_true', help='One-time inbox check')
    parser.add_argument('--status', action='store_true', help='Show relay state')
    args = parser.parse_args()

    client_lookup = load_roster()
    state = load_state()

    if args.status:
        show_status(state, client_lookup)
        return

    # Initialize Twilio
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    if not account_sid or not auth_token:
        print("ERROR: Missing Twilio credentials in .env")
        sys.exit(1)
    twilio_client = Client(account_sid, auth_token)

    if args.check:
        print(f"[{datetime.now().strftime('%I:%M %p')}] Checking inbox...")
        process_inbound(twilio_client, client_lookup, state)
        print("Done.")
        return

    # Continuous relay mode
    print(f"\n{'='*50}")
    print(f"BOABFIT SMS RELAY — LIVE")
    print(f"{'='*50}")
    print(f"Monitoring {FROM_NUMBER} for BoabFit client replies")
    print(f"Relaying to Julia at {JULIA_PHONE}")
    print(f"Tracking {len(client_lookup)} clients")
    print(f"Poll interval: {POLL_INTERVAL}s")
    print(f"")
    print(f"Julia can reply directly (goes to last client who texted)")
    print(f"Or use: TO [name]: [message]")
    print(f"")
    print(f"Ctrl+C to stop")
    print(f"{'='*50}\n")

    try:
        while True:
            try:
                process_inbound(twilio_client, client_lookup, state)
            except Exception as e:
                print(f"  ⚠ Error during poll: {e}")
            time_mod.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print(f"\n\nRelay stopped. State saved to {STATE_FILE}")


if __name__ == "__main__":
    main()
