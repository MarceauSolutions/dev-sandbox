#!/usr/bin/env python3
"""
Multi-Account Gmail Search

Search across multiple Gmail accounts from a single command.
Each account gets its own token file. Uses the shared OAuth client (credentials.json).

Setup (one-time per account):
    python execution/multi_gmail_search.py --add-account personal
    # Browser opens → sign in with wmarceau26@gmail.com → token saved

Usage:
    python execution/multi_gmail_search.py --query "insurance quote ranger"
    python execution/multi_gmail_search.py --query "invoice" --accounts business
    python execution/multi_gmail_search.py --query "order confirmation" --accounts personal
    python execution/multi_gmail_search.py --query "from:someone@example.com" --accounts all
    python execution/multi_gmail_search.py --list-accounts

Accounts are stored in ~/.gmail-tokens/ with a registry file.
"""

import argparse
import json
import os
import sys
import base64
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKENS_DIR = Path.home() / ".gmail-tokens"
REGISTRY_FILE = TOKENS_DIR / "accounts.json"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"


def load_registry() -> dict:
    """Load the account registry."""
    if REGISTRY_FILE.exists():
        with open(REGISTRY_FILE) as f:
            return json.load(f)
    return {"accounts": {}}


def save_registry(registry: dict):
    """Save the account registry."""
    TOKENS_DIR.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, indent=2)


def get_token_path(alias: str) -> Path:
    """Get token file path for an account alias."""
    return TOKENS_DIR / f"token_{alias}.json"


def add_account(alias: str):
    """Add a new Gmail account via OAuth browser flow."""
    TOKENS_DIR.mkdir(parents=True, exist_ok=True)

    if not CREDENTIALS_FILE.exists():
        print(f"ERROR: OAuth credentials not found at {CREDENTIALS_FILE}")
        print("Download from Google Cloud Console → APIs & Services → Credentials")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"Adding Gmail account: '{alias}'")
    print(f"{'='*60}")
    print(f"\nA browser window will open. Sign in with the Google account")
    print(f"you want to associate with the alias '{alias}'.\n")

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=0)

    # Save token
    token_path = get_token_path(alias)
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else SCOPES,
    }
    with open(token_path, "w") as f:
        json.dump(token_data, f, indent=2)

    # Get the email address for this account
    service = build("gmail", "v1", credentials=creds)
    profile = service.users().getProfile(userId="me").execute()
    email = profile.get("emailAddress", "unknown")

    # Update registry
    registry = load_registry()
    registry["accounts"][alias] = {
        "email": email,
        "token_file": str(token_path),
        "added": datetime.now().isoformat(),
    }
    save_registry(registry)

    print(f"\n✅ Account '{alias}' added: {email}")
    print(f"   Token saved to: {token_path}")


def get_service(alias: str):
    """Get an authenticated Gmail service for an account alias."""
    registry = load_registry()

    if alias not in registry.get("accounts", {}):
        # Check if it's the default business account
        if alias == "business":
            token_path = PROJECT_ROOT / "token.json"
        else:
            print(f"ERROR: Account '{alias}' not found. Run: --add-account {alias}")
            return None, None
    else:
        token_path = Path(registry["accounts"][alias]["token_file"])

    if not token_path.exists():
        print(f"ERROR: Token file not found: {token_path}")
        return None, None

    with open(token_path) as f:
        token_data = json.load(f)

    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes", SCOPES),
    )

    # Refresh if expired
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Save refreshed token
            token_data["token"] = creds.token
            if hasattr(creds, "expiry") and creds.expiry:
                token_data["expiry"] = creds.expiry.isoformat() + "Z"
            with open(token_path, "w") as f:
                json.dump(token_data, f, indent=2)
        except Exception as e:
            print(f"ERROR: Token refresh failed for '{alias}': {e}")
            return None, None

    service = build("gmail", "v1", credentials=creds)

    # Get email address
    email = registry.get("accounts", {}).get(alias, {}).get("email", "")
    if not email:
        try:
            profile = service.users().getProfile(userId="me").execute()
            email = profile.get("emailAddress", alias)
        except Exception:
            email = alias

    return service, email


def decode_body(payload: dict) -> str:
    """Extract plain text body from Gmail message payload."""
    body = ""

    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
    elif payload.get("parts"):
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                break
            elif part.get("parts"):
                body = decode_body(part)
                if body:
                    break

    return body.strip()


def search_account(service, email: str, query: str, max_results: int = 10) -> list:
    """Search a single Gmail account and return results."""
    results = []

    try:
        response = service.users().messages().list(
            userId="me", q=query, maxResults=max_results
        ).execute()

        messages = response.get("messages", [])
        if not messages:
            return results

        for msg_info in messages:
            msg = service.users().messages().get(
                userId="me", id=msg_info["id"], format="full"
            ).execute()

            headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
            body = decode_body(msg.get("payload", {}))

            # Parse date
            date_str = headers.get("date", "")
            try:
                # Handle various date formats
                clean_date = re.sub(r"\s*\(.*?\)\s*$", "", date_str)
                for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S"]:
                    try:
                        parsed_date = datetime.strptime(clean_date, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    parsed_date = None
            except Exception:
                parsed_date = None

            results.append({
                "account": email,
                "id": msg_info["id"],
                "date": date_str,
                "parsed_date": parsed_date,
                "from": headers.get("from", ""),
                "to": headers.get("to", ""),
                "subject": headers.get("subject", "(no subject)"),
                "snippet": msg.get("snippet", ""),
                "body": body[:2000] if body else "",
                "has_attachments": any(
                    p.get("filename") for p in msg.get("payload", {}).get("parts", [])
                ),
            })

    except Exception as e:
        print(f"  ERROR searching {email}: {e}")

    return results


def list_accounts():
    """List all registered accounts."""
    registry = load_registry()

    # Always show business account
    print(f"\n{'='*60}")
    print("Registered Gmail Accounts")
    print(f"{'='*60}\n")

    # Check for default business token
    biz_token = PROJECT_ROOT / "token.json"
    if biz_token.exists():
        print(f"  business  →  wmarceau@marceausolutions.com  (default, token.json)")

    for alias, info in registry.get("accounts", {}).items():
        token_exists = "✅" if Path(info["token_file"]).exists() else "❌"
        print(f"  {alias:10s}  →  {info['email']}  {token_exists}")

    if not registry.get("accounts") and not biz_token.exists():
        print("  (no accounts registered)")

    print(f"\n  Add account: python execution/multi_gmail_search.py --add-account <alias>")
    print()


def main():
    parser = argparse.ArgumentParser(description="Search multiple Gmail accounts")
    parser.add_argument("--query", "-q", help="Gmail search query")
    parser.add_argument("--accounts", "-a", default="all",
                        help="Comma-separated account aliases or 'all' (default: all)")
    parser.add_argument("--max-results", "-n", type=int, default=10,
                        help="Max results per account (default: 10)")
    parser.add_argument("--add-account", metavar="ALIAS",
                        help="Add a new Gmail account with this alias")
    parser.add_argument("--list-accounts", action="store_true",
                        help="List all registered accounts")
    parser.add_argument("--body", action="store_true",
                        help="Show email body text (default: subject + snippet only)")
    parser.add_argument("--json-output", action="store_true",
                        help="Output results as JSON")

    args = parser.parse_args()

    if args.list_accounts:
        list_accounts()
        return

    if args.add_account:
        add_account(args.add_account)
        return

    if not args.query:
        parser.print_help()
        print("\nExamples:")
        print('  python execution/multi_gmail_search.py -q "insurance quote ranger"')
        print('  python execution/multi_gmail_search.py -q "from:geico.com" -a personal')
        print('  python execution/multi_gmail_search.py --add-account personal')
        return

    # Determine which accounts to search
    registry = load_registry()

    if args.accounts == "all":
        account_aliases = ["business"]  # Always include business
        account_aliases.extend(registry.get("accounts", {}).keys())
        # Deduplicate
        account_aliases = list(dict.fromkeys(account_aliases))
    else:
        account_aliases = [a.strip() for a in args.accounts.split(",")]

    print(f"\n{'='*60}")
    print(f"Multi-Gmail Search: \"{args.query}\"")
    print(f"Accounts: {', '.join(account_aliases)}")
    print(f"{'='*60}\n")

    all_results = []

    for alias in account_aliases:
        service, email = get_service(alias)
        if not service:
            continue

        print(f"  Searching {email}...")
        results = search_account(service, email, args.query, args.max_results)
        print(f"    → {len(results)} results")
        all_results.extend(results)

    # Sort all results by date (newest first)
    all_results.sort(
        key=lambda r: r["parsed_date"] or datetime.min.replace(tzinfo=None),
        reverse=True,
    )

    if args.json_output:
        output = []
        for r in all_results:
            r_copy = dict(r)
            r_copy.pop("parsed_date", None)
            output.append(r_copy)
        print(json.dumps(output, indent=2))
        return

    if not all_results:
        print("\nNo results found across any account.")
        return

    print(f"\n{'='*60}")
    print(f"Results ({len(all_results)} total)")
    print(f"{'='*60}\n")

    for i, r in enumerate(all_results, 1):
        acct_label = r["account"].split("@")[0]
        print(f"  [{i}] ({acct_label}) {r['subject']}")
        print(f"      From: {r['from']}")
        print(f"      Date: {r['date']}")
        if r["has_attachments"]:
            print(f"      📎 Has attachments")
        print(f"      {r['snippet'][:120]}")
        if args.body and r["body"]:
            print(f"\n      --- Body ---")
            for line in r["body"][:1000].split("\n"):
                print(f"      {line}")
            print(f"      --- End ---")
        print()


if __name__ == "__main__":
    main()
