#!/usr/bin/env python3
"""
gmail_reply_watcher.py — Gmail Reply Watcher for AI Client Sprint

WHAT: Polls Gmail for replies from cold outreach recipients, updates pipeline DB,
      and sends Telegram notifications when replies are detected.
WHY:  Close the loop on cold outreach — know immediately when a prospect responds.
INPUT: outreach_tracking_*.json files in projects/shared/lead-scraper/output/
OUTPUT: Updated pipeline.db + Telegram notification + processed_replies.json log
COST:  FREE (Gmail API + Telegram Bot API)
TIME:  ~5-10 seconds per run

USAGE:
  python execution/gmail_reply_watcher.py           # run normally
  python execution/gmail_reply_watcher.py --dry-run # test without writing

NOTES:
  - Gmail OAuth token stored at token_gmail_readonly.json (root)
  - Will prompt for OAuth on first run if no valid token exists
  - Tracks processed reply IDs in projects/shared/lead-scraper/output/processed_replies.json
  - Pipeline DB: projects/shared/sales-pipeline/data/pipeline.db
  - Stage mapping: cold_sent -> replied (on reply detection)
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

# ─── Paths ────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

OUTREACH_DIR = ROOT / "projects" / "shared" / "lead-scraper" / "output"
PIPELINE_DB = ROOT / "projects" / "shared" / "sales-pipeline" / "data" / "pipeline.db"
PROCESSED_REPLIES_FILE = OUTREACH_DIR / "processed_replies.json"
TOKEN_FILE = ROOT / "token.json"          # shared token with full Gmail scopes
CREDENTIALS_FILE = ROOT / "credentials.json"

# Scopes already granted in token.json (gmail.readonly is a subset of gmail.modify)
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Telegram config
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = "5692454753"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# Pipeline stage constants
STAGE_COLD_SENT = "Intake"       # maps to existing pipeline "Intake" stage
STAGE_REPLIED = "Qualified"      # reply = qualified lead in the pipeline


# ─── Gmail Auth ───────────────────────────────────────────────────────────────

def get_gmail_service():
    """
    Authenticate with Gmail API using OAuth 2.0.
    Uses token_gmail_readonly.json for persistence.
    On first run (or expired token), triggers browser OAuth flow.
    Returns Gmail API service object, or None on failure.
    """
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        print("ERROR: Google API libraries not installed.")
        print("Run: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        return None

    creds = None

    # Load existing token if available
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), GMAIL_SCOPES)

    # Refresh or re-authenticate if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                print("[auth] Token refreshed successfully.")
            except Exception as e:
                print(f"[auth] Token refresh failed: {e}")
                creds = None

        if not creds:
            if not CREDENTIALS_FILE.exists():
                print(f"ERROR: credentials.json not found at {CREDENTIALS_FILE}")
                print("Cannot authenticate without OAuth client credentials.")
                return None
            print("[auth] Initiating OAuth flow — browser will open for authorization...")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the token for next run
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        print(f"[auth] Token saved to {TOKEN_FILE.name}")

    from googleapiclient.discovery import build
    service = build("gmail", "v1", credentials=creds)
    return service


# ─── Outreach Tracking ────────────────────────────────────────────────────────

def load_tracked_recipients() -> dict[str, dict]:
    """
    Load all outreach_tracking_*.json files and return a dict keyed by email.
    Each value: {first_name, company, sent_at, subject}
    """
    recipients = {}
    for f in sorted(OUTREACH_DIR.glob("outreach_tracking_*.json")):
        try:
            data = json.loads(f.read_text())
            for email_entry in data.get("emails", []):
                if email_entry.get("status") == "sent":
                    addr = email_entry["recipient"].lower().strip()
                    recipients[addr] = {
                        "first_name": email_entry.get("first_name", ""),
                        "company": email_entry.get("company", ""),
                        "sent_at": email_entry.get("sent_at", ""),
                        "subject": email_entry.get("subject", ""),
                        "source_file": f.name,
                    }
        except Exception as e:
            print(f"[load] Warning: could not read {f.name}: {e}")

    print(f"[load] Tracking {len(recipients)} recipient(s) across outreach files.")
    return recipients


def load_processed_replies() -> set:
    """Load set of already-processed Gmail message IDs."""
    if PROCESSED_REPLIES_FILE.exists():
        try:
            data = json.loads(PROCESSED_REPLIES_FILE.read_text())
            return set(data.get("processed_ids", []))
        except Exception:
            return set()
    return set()


def save_processed_replies(processed_ids: set) -> None:
    """Persist processed message IDs to disk."""
    data = {
        "processed_ids": sorted(list(processed_ids)),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    PROCESSED_REPLIES_FILE.write_text(json.dumps(data, indent=2))


def update_tracking_json_reply(email: str, reply_at: str, dry_run: bool = False) -> bool:
    """
    Mark a recipient as replied in all outreach_tracking_*.json files.
    Sets reply_received=True, reply_at=<timestamp>, pipeline_stage="Qualified".
    Returns True if at least one record was updated.
    """
    email_lower = email.lower().strip()
    updated = False

    for tracking_file in sorted(OUTREACH_DIR.glob("outreach_tracking_*.json")):
        try:
            data = json.loads(tracking_file.read_text())
        except Exception as e:
            print(f"  [tracking-json] Could not read {tracking_file.name}: {e}")
            continue

        changed = False
        for entry in data.get("emails", []):
            if entry.get("recipient", "").lower().strip() == email_lower:
                if dry_run:
                    print(f"  [dry-run] Would update {tracking_file.name}: {email} -> reply_received=True")
                else:
                    entry["reply_received"] = True
                    entry["reply_at"] = reply_at
                    entry["pipeline_stage"] = "Qualified"
                    changed = True
                updated = True

        if changed and not dry_run:
            try:
                tracking_file.write_text(json.dumps(data, indent=2))
                print(f"  [tracking-json] Updated {tracking_file.name}: {email} marked replied.")
            except Exception as e:
                print(f"  [tracking-json] Could not write {tracking_file.name}: {e}")

    if not updated:
        print(f"  [tracking-json] No tracking record found for {email} — skipping JSON update.")

    return updated


# ─── Gmail Search ─────────────────────────────────────────────────────────────

def extract_email_address(header_value: str) -> str:
    """Extract bare email address from a From/To header value."""
    match = re.search(r"<([^>]+)>", header_value)
    if match:
        return match.group(1).lower().strip()
    return header_value.lower().strip()


def search_replies(service, tracked_recipients: dict[str, dict]) -> list[dict]:
    """
    Search Gmail INBOX for messages FROM any tracked recipient.
    Returns list of message detail dicts for unread/new replies.
    """
    if not tracked_recipients:
        return []

    # Build OR query: from:email1 OR from:email2 ...
    from_clauses = " OR ".join(f"from:{addr}" for addr in tracked_recipients)
    query = f"in:inbox ({from_clauses})"

    try:
        result = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=50,
        ).execute()
    except Exception as e:
        print(f"[gmail] Search failed: {e}")
        return []

    messages = result.get("messages", [])
    if not messages:
        print("[gmail] No replies found in inbox.")
        return []

    print(f"[gmail] Found {len(messages)} potential reply(ies) in inbox.")
    return messages


def get_message_details(service, message_id: str) -> dict:
    """Fetch full message details from Gmail API."""
    try:
        msg = service.users().messages().get(
            userId="me",
            id=message_id,
            format="metadata",
            metadataHeaders=["From", "To", "Subject", "Date"],
        ).execute()

        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        return {
            "message_id": message_id,
            "thread_id": msg.get("threadId", ""),
            "from_email": extract_email_address(headers.get("From", "")),
            "from_raw": headers.get("From", ""),
            "to_raw": headers.get("To", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
            "snippet": msg.get("snippet", ""),
            "labels": msg.get("labelIds", []),
        }
    except Exception as e:
        print(f"[gmail] Could not fetch message {message_id}: {e}")
        return {}


# ─── Pipeline DB ──────────────────────────────────────────────────────────────

def get_pipeline_db() -> sqlite3.Connection:
    """Open (or create) the pipeline SQLite DB."""
    PIPELINE_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(PIPELINE_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    # Ensure tables exist (compatible with existing pipeline schema)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            contact_name TEXT,
            contact_phone TEXT,
            contact_email TEXT,
            industry TEXT DEFAULT 'Other',
            pain_points TEXT,
            lead_source TEXT,
            stage TEXT DEFAULT 'Intake',
            next_action TEXT,
            next_action_date TEXT,
            proposal_amount REAL DEFAULT 0,
            setup_fee REAL DEFAULT 0,
            monthly_fee REAL DEFAULT 0,
            close_date TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id INTEGER REFERENCES deals(id),
            activity_type TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS outreach_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id INTEGER REFERENCES deals(id),
            company TEXT,
            contact TEXT,
            channel TEXT DEFAULT 'Email',
            message_summary TEXT,
            response TEXT,
            follow_up_date TEXT,
            lead_source TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn


def find_or_create_deal(conn: sqlite3.Connection, email: str, info: dict, dry_run: bool = False) -> int | None:
    """
    Find existing deal by contact_email, or create a new one.
    Returns deal_id.
    """
    row = conn.execute(
        "SELECT id FROM deals WHERE contact_email = ? LIMIT 1", (email,)
    ).fetchone()

    if row:
        return row["id"]

    if dry_run:
        print(f"  [dry-run] Would create deal: {info.get('company')} <{email}>")
        return None

    cur = conn.execute(
        """INSERT INTO deals (company, contact_email, contact_name, stage, lead_source, notes, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))""",
        (
            info.get("company", "Unknown"),
            email,
            info.get("first_name", ""),
            STAGE_COLD_SENT,
            "cold-email-sprint-2026-03-23",
            f"Cold email sent: {info.get('subject', '')}",
        ),
    )
    conn.commit()
    deal_id = cur.lastrowid
    conn.execute(
        "INSERT INTO activities (deal_id, activity_type, description) VALUES (?, ?, ?)",
        (deal_id, "outreach", f"Cold email sent: {info.get('subject', '')}"),
    )
    conn.commit()
    return deal_id


def mark_replied(conn: sqlite3.Connection, deal_id: int, msg: dict, dry_run: bool = False) -> None:
    """Update deal stage to Qualified (replied) and log the activity."""
    if dry_run:
        print(f"  [dry-run] Would update deal {deal_id} -> stage=Qualified")
        return

    conn.execute(
        """UPDATE deals SET stage = ?, next_action = ?, updated_at = datetime('now')
           WHERE id = ? AND stage = ?""",
        (
            STAGE_REPLIED,
            "Reply received — respond within 2 hours",
            deal_id,
            STAGE_COLD_SENT,
        ),
    )
    conn.commit()

    conn.execute(
        "INSERT INTO activities (deal_id, activity_type, description) VALUES (?, ?, ?)",
        (
            deal_id,
            "reply_received",
            f"Reply from {msg.get('from_raw', '')} | Subject: {msg.get('subject', '')} | {msg.get('snippet', '')[:120]}",
        ),
    )
    conn.commit()


def seed_pipeline_from_outreach(tracked_recipients: dict[str, dict], dry_run: bool = False) -> int:
    """
    Ensure every tracked prospect has a deal record in the pipeline DB.
    Creates records for any that don't exist yet (stage: Intake/cold_sent).
    Returns count of newly created records.
    """
    conn = get_pipeline_db()
    created = 0

    for email, info in tracked_recipients.items():
        existing = conn.execute(
            "SELECT id FROM deals WHERE contact_email = ? LIMIT 1", (email,)
        ).fetchone()

        if existing:
            print(f"  [seed] Already in pipeline: {info['company']} <{email}>")
            continue

        if dry_run:
            print(f"  [dry-run] Would seed: {info['company']} <{email}> (stage=Intake)")
            created += 1
            continue

        cur = conn.execute(
            """INSERT INTO deals (company, contact_email, contact_name, stage, lead_source, notes, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
            (
                info.get("company", "Unknown"),
                email,
                info.get("first_name", ""),
                STAGE_COLD_SENT,
                "cold-email-sprint-2026-03-23",
                f"Cold email sent {info.get('sent_at', '')[:10]}: {info.get('subject', '')}",
                info.get("sent_at", datetime.now(timezone.utc).isoformat())[:19],
            ),
        )
        deal_id = cur.lastrowid
        conn.commit()

        conn.execute(
            "INSERT INTO activities (deal_id, activity_type, description) VALUES (?, ?, ?)",
            (deal_id, "outreach", f"Cold email sent: {info.get('subject', '')}"),
        )
        conn.commit()
        print(f"  [seed] Created: {info['company']} <{email}> (stage=Intake)")
        created += 1

    conn.close()
    return created


# ─── Telegram ─────────────────────────────────────────────────────────────────

def send_telegram(message: str, dry_run: bool = False) -> bool:
    """Send a Telegram notification to William's chat."""
    if dry_run:
        print(f"  [dry-run] Would send Telegram:\n{message}")
        return True

    if not TELEGRAM_BOT_TOKEN:
        print("[telegram] No TELEGRAM_BOT_TOKEN in .env — skipping notification.")
        return False

    try:
        resp = requests.post(
            TELEGRAM_API_URL,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            print("[telegram] Notification sent.")
            return True
        else:
            print(f"[telegram] Failed: {resp.status_code} {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"[telegram] Error: {e}")
        return False


def format_reply_notification(company: str, first_name: str, email: str, subject: str, snippet: str) -> str:
    """Format Telegram notification message for a reply."""
    snippet_clean = snippet[:150].replace("<", "&lt;").replace(">", "&gt;") if snippet else "(no preview)"
    return (
        f"<b>REPLY — AI Sprint</b>\n\n"
        f"<b>{company}</b> ({first_name}) replied!\n"
        f"<b>From:</b> {email}\n"
        f"<b>Subject:</b> {subject}\n\n"
        f"<i>{snippet_clean}</i>\n\n"
        f"Pipeline updated → Qualified\n"
        f"Respond within 2 hours."
    )


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Gmail Reply Watcher — AI Client Sprint")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing to DB or sending Telegram")
    parser.add_argument("--seed-only", action="store_true", help="Only seed pipeline DB from outreach files, skip Gmail check")
    args = parser.parse_args()

    dry_run = args.dry_run
    if dry_run:
        print("[mode] DRY RUN — no writes, no notifications\n")

    # Step 1: Load tracked recipients from outreach files
    tracked = load_tracked_recipients()
    if not tracked:
        print("No tracked recipients found. Exiting.")
        sys.exit(0)

    # Step 2: Seed pipeline DB with all sent prospects
    print("\n[pipeline] Seeding pipeline DB with outreach prospects...")
    seeded = seed_pipeline_from_outreach(tracked, dry_run=dry_run)
    print(f"[pipeline] {seeded} new record(s) created in pipeline DB.")

    if args.seed_only:
        print("\n[done] Seed-only mode. Skipping Gmail check.")
        return

    # Step 3: Connect to Gmail
    print("\n[gmail] Connecting to Gmail API...")
    service = get_gmail_service()
    if not service:
        print("ERROR: Could not connect to Gmail API. Check OAuth credentials.")
        sys.exit(1)
    print("[gmail] Connected.")

    # Step 4: Load already-processed reply IDs
    processed_ids = load_processed_replies()
    print(f"[state] {len(processed_ids)} reply(ies) already processed.")

    # Step 5: Search for replies from tracked recipients
    raw_messages = search_replies(service, tracked)

    # Step 6: Process new replies
    new_replies = 0
    conn = get_pipeline_db()

    for msg_meta in raw_messages:
        msg_id = msg_meta["id"]

        # Skip already processed
        if msg_id in processed_ids:
            continue

        # Get message details
        msg = get_message_details(service, msg_id)
        if not msg:
            continue

        from_email = msg["from_email"]

        # Skip if not from a tracked recipient
        if from_email not in tracked:
            print(f"  [skip] Message from {from_email} — not a tracked recipient.")
            processed_ids.add(msg_id)  # mark so we don't re-check
            continue

        info = tracked[from_email]
        print(f"\n[REPLY] {info['company']} ({from_email}) replied!")
        print(f"  Subject: {msg['subject']}")
        print(f"  Preview: {msg['snippet'][:100]}")

        # Step 6a: Find or create deal in pipeline
        deal_id = find_or_create_deal(conn, from_email, info, dry_run=dry_run)

        # Step 6b: Update deal to Qualified stage
        if deal_id:
            mark_replied(conn, deal_id, msg, dry_run=dry_run)
            if not dry_run:
                print(f"  [pipeline] Deal {deal_id} updated -> Qualified")

        # Step 6b2: Update outreach tracking JSON
        reply_timestamp = datetime.now(timezone.utc).isoformat()
        update_tracking_json_reply(from_email, reply_timestamp, dry_run=dry_run)

        # Step 6c: Send Telegram notification
        notification = format_reply_notification(
            company=info.get("company", "Unknown"),
            first_name=info.get("first_name", ""),
            email=from_email,
            subject=msg.get("subject", ""),
            snippet=msg.get("snippet", ""),
        )
        send_telegram(notification, dry_run=dry_run)

        # Step 6d: Mark as processed
        processed_ids.add(msg_id)
        new_replies += 1

    conn.close()

    # Step 7: Save processed IDs
    if not dry_run:
        save_processed_replies(processed_ids)

    # Summary
    print(f"\n{'='*50}")
    print(f"[done] Checked {len(tracked)} tracked recipient(s).")
    print(f"[done] {new_replies} new reply(ies) processed.")
    if not dry_run and new_replies > 0:
        print(f"[done] Pipeline DB updated. Telegram notification(s) sent.")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
