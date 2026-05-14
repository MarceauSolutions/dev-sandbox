#!/usr/bin/env python3
"""
telegram_send_file.py — Send a file (PDF, image, doc) to a Telegram chat via the Marceau bot.

Used by:
  - claude -p on EC2 (Panacea) to deliver generated PDFs back to William's phone
  - Any automation that needs to push a document to Telegram

Usage:
    python3 execution/telegram_send_file.py --file output/sop.pdf
    python3 execution/telegram_send_file.py --file image.png --caption "Here's the diagram"
    python3 execution/telegram_send_file.py --file report.pdf --chat-id 5692454753

Env required: TELEGRAM_BOT_TOKEN (in repo .env). Defaults chat to William's TELEGRAM_CHAT_ID.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
DEFAULT_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "5692454753")  # William's chat


def send_file(file_path: str, chat_id: Optional[str] = None, caption: str = "") -> dict:
    """Send a file to Telegram. Returns the API response dict on success or raises."""
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set in environment / .env")

    fp = Path(file_path)
    if not fp.exists():
        raise FileNotFoundError(file_path)

    chat_id = chat_id or DEFAULT_CHAT_ID
    size_mb = fp.stat().st_size / (1024 * 1024)
    if size_mb > 50:
        raise ValueError(f"File too large for Telegram (50 MB limit): {size_mb:.1f} MB")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    with fp.open("rb") as f:
        resp = requests.post(
            url,
            data={"chat_id": chat_id, "caption": caption[:1024]},
            files={"document": (fp.name, f)},
            timeout=120,
        )
    resp.raise_for_status()
    payload = resp.json()
    if not payload.get("ok"):
        raise RuntimeError(f"Telegram API error: {payload}")
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", required=True, help="Path to file to send")
    parser.add_argument("--chat-id", help="Telegram chat ID (default: William)")
    parser.add_argument("--caption", default="", help="Optional caption text")
    args = parser.parse_args()

    try:
        result = send_file(args.file, args.chat_id, args.caption)
    except Exception as e:
        sys.exit(f"ERROR: {e}")

    msg_id = result.get("result", {}).get("message_id")
    print(f"OK — sent {Path(args.file).name} (telegram msg_id={msg_id})")


if __name__ == "__main__":
    main()
