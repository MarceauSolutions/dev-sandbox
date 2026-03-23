#!/usr/bin/env python3
"""EOD auto-send — fires at 7pm daily.

Posts to /api/sprint-close if no manual session-close was sent today.
Reads the session-close log to avoid double-sending.
"""

import os
import sys
import json
import logging
import requests
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

LOG_FILE = Path(__file__).resolve().parent.parent / "output" / "eod_auto_send.log"
SESSION_CLOSE_LOG = Path(__file__).resolve().parent.parent / "output" / "session_close_log.json"
SPRINT_API = "http://127.0.0.1:8780/api/sprint-close"

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def already_sent_today() -> bool:
    """Check if a session-close was already sent today (manually or auto)."""
    if not SESSION_CLOSE_LOG.exists():
        return False
    try:
        log = json.loads(SESSION_CLOSE_LOG.read_text())
        entries = log.get("entries", [])
        today = str(date.today())
        return any(e.get("date") == today for e in entries)
    except Exception:
        return False


def record_sent():
    """Log that EOD was sent today."""
    SESSION_CLOSE_LOG.parent.mkdir(parents=True, exist_ok=True)
    log = {"entries": []}
    if SESSION_CLOSE_LOG.exists():
        try:
            log = json.loads(SESSION_CLOSE_LOG.read_text())
        except Exception:
            pass
    log["entries"].append({
        "date": str(date.today()),
        "time": datetime.now().strftime("%H:%M"),
        "source": "auto"
    })
    # Keep last 90 days
    log["entries"] = log["entries"][-90:]
    SESSION_CLOSE_LOG.write_text(json.dumps(log, indent=2))


def main():
    logging.info("EOD auto-send check starting")

    if already_sent_today():
        logging.info("Session close already sent today — skipping auto-send")
        print("Already sent today — no action needed")
        return

    logging.info("No manual close found — sending auto EOD summary")

    try:
        resp = requests.post(
            SPRINT_API,
            json={"missed_items": "", "source": "auto_eod"},
            timeout=10
        )
        if resp.status_code == 200:
            logging.info("EOD auto-send SUCCESS")
            record_sent()
            print(f"EOD auto-send: OK ({resp.status_code})")
        else:
            logging.error(f"EOD auto-send FAILED: {resp.status_code} {resp.text}")
            print(f"EOD auto-send FAILED: {resp.status_code}", file=sys.stderr)
    except requests.exceptions.ConnectionError:
        logging.warning("Accountability engine not running — EOD skipped (dashboard not open)")
        print("Dashboard offline — EOD skipped")
    except Exception as e:
        logging.error(f"EOD auto-send error: {e}")
        print(f"Error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
