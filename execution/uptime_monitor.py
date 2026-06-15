#!/usr/bin/env python3
"""
uptime_monitor.py — Checks all live Marceau URLs from data/live-urls.json and
Telegrams William when one changes state (up->down or down->up). Stateful so it
alerts ONCE on transition, not every run (no spam).

Designed to run from a systemd timer / cron on EC2 every 5 min, independent of
n8n so it survives n8n going down.

Env required: TELEGRAM_BOT_TOKEN (from repo .env). Chat defaults to TELEGRAM_CHAT_ID.

Usage:
    python3 execution/uptime_monitor.py            # check + alert on changes
    python3 execution/uptime_monitor.py --dry-run  # check + print, never send/persist
    python3 execution/uptime_monitor.py --test      # send a test Telegram, then exit
"""
import argparse
import json
import os
import ssl
import sys
import time
from pathlib import Path
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

# Build an SSL context with a real CA bundle (certifi if present, else system
# default). Verification stays ON: an expired/invalid cert is a real outage a
# client would also hit, so we WANT it reported as down.
try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    SSL_CTX = ssl.create_default_context()

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "data" / "live-urls.json"
STATE_FILE = ROOT / "data" / ".uptime_state.json"

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "5692454753")
TIMEOUT = 12
RETRIES = 2          # a single timeout != down; require RETRIES consecutive fails
RETRY_GAP = 3        # seconds between retries


def send_telegram(text: str) -> bool:
    if not BOT_TOKEN:
        print("WARN: TELEGRAM_BOT_TOKEN not set; cannot alert", file=sys.stderr)
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = json.dumps({
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode()
    req = urlrequest.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urlrequest.urlopen(req, timeout=15, context=SSL_CTX) as r:
            return json.loads(r.read()).get("ok", False)
    except Exception as e:
        print(f"ERROR sending telegram: {e}", file=sys.stderr)
        return False


def check(site: dict) -> dict:
    """Return {up: bool, code: int|None, detail: str}. Retries before declaring down."""
    url = site["url"]
    expect = site.get("expect")  # list of acceptable codes, or None = any HTTP response is 'up'
    last = {"up": False, "code": None, "detail": ""}
    for attempt in range(1, RETRIES + 1):
        code = None
        try:
            req = urlrequest.Request(url, method="GET", headers={"User-Agent": "MarceauUptime/1.0"})
            with urlrequest.urlopen(req, timeout=TIMEOUT, context=SSL_CTX) as r:
                code = r.getcode()
        except HTTPError as e:
            code = e.code  # an HTTP error code still means the server answered = reachable
        except (URLError, TimeoutError, OSError) as e:
            last = {"up": False, "code": None, "detail": f"no response ({type(e).__name__})"}
            if attempt < RETRIES:
                time.sleep(RETRY_GAP)
            continue
        # got an HTTP code
        if expect:
            up = code in expect
            detail = "" if up else f"unexpected HTTP {code} (want {expect})"
        else:
            up = True
            detail = ""
        last = {"up": up, "code": code, "detail": detail}
        if up:
            return last
        if attempt < RETRIES:
            time.sleep(RETRY_GAP)
    return last


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return {}
    return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="check + print, never send or persist state")
    ap.add_argument("--test", action="store_true", help="send a test Telegram and exit")
    args = ap.parse_args()

    if args.test:
        ok = send_telegram("✅ <b>Marceau Uptime Monitor</b> — test alert. If you see this, alerting works.")
        print("test sent" if ok else "test FAILED")
        sys.exit(0 if ok else 1)

    registry = json.loads(REGISTRY.read_text())
    sites = [s for s in registry.get("sites", []) if s.get("monitor", True)]
    prev = load_state()
    new_state = {}
    transitions = []

    for site in sites:
        res = check(site)
        url = site["url"]
        was_up = prev.get(url, {}).get("up", True)  # assume up first run -> only alert on real drop
        new_state[url] = {"up": res["up"], "code": res["code"]}
        status = "UP" if res["up"] else "DOWN"
        print(f"[{status}] {site['name']} ({url}) code={res['code']} {res['detail']}")
        if res["up"] != was_up:
            transitions.append((site, res, was_up))

    if args.dry_run:
        print("\n--dry-run: no alerts sent, state not persisted")
        print(f"would-alert transitions: {len(transitions)}")
        return

    for site, res, was_up in transitions:
        if not res["up"]:
            msg = (
                f"🔴 <b>SITE DOWN</b>\n"
                f"<b>{site['name']}</b>\n"
                f"{site['url']}\n"
                f"Reason: {res['detail'] or 'no response / timeout'}\n"
                f"Host: {site.get('host','?')}"
            )
        else:
            msg = (
                f"🟢 <b>RECOVERED</b>\n"
                f"<b>{site['name']}</b>\n"
                f"{site['url']} is back up (HTTP {res['code']})"
            )
        send_telegram(msg)

    STATE_FILE.write_text(json.dumps(new_state, indent=2))
    print(f"\nchecked {len(sites)} sites, {len(transitions)} state change(s) alerted")


if __name__ == "__main__":
    main()
