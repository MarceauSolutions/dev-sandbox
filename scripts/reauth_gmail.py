#!/usr/bin/env python3
"""
Re-authenticate Gmail with full scopes (readonly + send + modify).

Run this ONCE from the Mac (requires browser):
    python3 scripts/reauth_gmail.py

This upgrades the token from gmail.readonly to full access,
enabling Gmail API sending (instead of SMTP fallback) and
draft creation for the hot lead → Calendly handoff.

After running, the token.json will have all required scopes
and both reading and sending will work via Gmail API.
"""

import os
import json
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

REPO_ROOT = Path(__file__).resolve().parent.parent
TOKEN_PATH = REPO_ROOT / "token.json"
CREDS_PATH = REPO_ROOT / "credentials.json"

FULL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
]


def main():
    print("=" * 60)
    print("Gmail Re-Authentication — Full Scopes")
    print("=" * 60)

    # Show current scopes
    if TOKEN_PATH.exists():
        with open(TOKEN_PATH) as f:
            current = json.load(f)
        print(f"\nCurrent scopes: {current.get('scopes', [])}")
        missing = [s for s in FULL_SCOPES if s not in current.get("scopes", [])]
        if not missing:
            print("\n✓ Token already has all required scopes. No action needed.")
            return
        print(f"Missing scopes: {missing}")
    else:
        print("\nNo token.json found — will create new one.")

    if not CREDS_PATH.exists():
        print(f"\nERROR: {CREDS_PATH} not found.")
        print("Download from Google Cloud Console → APIs & Services → Credentials")
        return

    print("\nA browser window will open. Sign in with wmarceau@marceausolutions.com")
    print("and grant all requested permissions.\n")

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_PATH), FULL_SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())

    # Verify
    with open(TOKEN_PATH) as f:
        new_token = json.load(f)

    print("\n" + "=" * 60)
    print("✓ Token updated successfully!")
    print(f"Scopes: {new_token.get('scopes', [])}")
    print(f"Saved to: {TOKEN_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
