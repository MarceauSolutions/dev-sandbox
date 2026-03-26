#!/usr/bin/env python3
"""Validate and refresh Google OAuth token. Outputs one of: VALID, REFRESHED, NO_REFRESH, ERROR:<msg>"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
token_path = ROOT / "token.json"

if not token_path.exists():
    print("NO_TOKEN")
    sys.exit(1)

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    creds = Credentials.from_authorized_user_file(str(token_path))

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_path, "w") as f:
            f.write(creds.to_json())
        print("REFRESHED")
    elif not creds.expired:
        print("VALID")
    elif not creds.refresh_token:
        print("NO_REFRESH")
    else:
        print("UNKNOWN")
except Exception as e:
    err = str(e).replace("\n", " ")[:120]
    print(f"ERROR:{err}")
    sys.exit(1)
