"""
Best-effort notifications. Every function swallows its own errors and returns a
bool — a notification failure must NEVER block or roll back a purchase.

- Buyer 'you won' alert  -> SMS via shared execution.twilio_sms.TwilioSMS
- Admin event ping       -> Telegram Bot API (sendMessage) direct, using
                            TELEGRAM_BOT_TOKEN + chat id from env.
"""
import os
import sys
import json
import ssl
import urllib.request
import urllib.parse
from pathlib import Path

import config

# allow importing shared execution utilities
_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def notify_buyer_won(contractor, appt: dict) -> bool:
    """SMS the winning buyer the revealed appointment details (transactional).
    Disabled until Twilio is reactivated (config.NOTIFY_SMS) — the buyer also sees the
    contact on-screen immediately and William gets a Telegram alert regardless."""
    if not config.NOTIFY_ENABLED or not config.NOTIFY_SMS or not contractor["phone"]:
        return False
    body = (
        f"{config.BRAND['name']}: you won an appointment!\n"
        f"{appt['service_type']} — {appt['scheduled_time']}\n"
        f"{appt['homeowner_name']}, {appt['address_full']}\n"
        f"Phone: {appt['homeowner_phone']}\n"
        f"Notes: {appt.get('private_notes') or appt['job_summary']}"
    )
    try:
        from execution.twilio_sms import TwilioSMS  # type: ignore
        res = TwilioSMS().send_message(to=contractor["phone"], message=body, force_send=True)
        return bool(res and res.get("status") not in ("failed", "error", None))
    except Exception as e:
        print(f"[notify] buyer SMS failed: {e}", file=sys.stderr)
        return False


def notify_admin(text: str) -> bool:
    """Telegram ping to William on marketplace events (direct Bot API)."""
    if not config.NOTIFY_ENABLED:
        return False
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = config.NOTIFY_TELEGRAM_CHAT_ID
    if not token or not chat_id:
        return False
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()
    try:
        data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage", data=data)
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            return json.load(r).get("ok", False)
    except Exception as e:
        print(f"[notify] admin telegram failed: {e}", file=sys.stderr)
        return False
