#!/usr/bin/env python3
"""
Queue X posts from CSV into Google Sheets for the n8n X-Social-Post-Scheduler.

Usage:
    python execution/queue_x_posts.py                    # Queue all pending posts from default CSV
    python execution/queue_x_posts.py --csv custom.csv   # From custom CSV
    python execution/queue_x_posts.py --dry-run           # Preview without writing

Requires: token_sheets.json (run Google OAuth flow first)
"""

import argparse
import csv
import sys
from datetime import datetime, timedelta
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
PROJECT_ROOT = Path(__file__).parent.parent
TOKEN_FILE = PROJECT_ROOT / "token_sheets.json"
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"

# Social Media Automation Google Sheet
SPREADSHEET_ID = "1frkdH8tqlNtnLXGAUiPioYQuU8e_g7Gev-C_Rhxb20o"
SHEET_NAME = "X_Post_Queue"

# Default CSV with posts
DEFAULT_CSV = PROJECT_ROOT / "projects/shared/social-media-automation/content-queue/x-posts-week-1.csv"

# Posting schedule (EST)
POSTING_TIMES = ["09:00", "12:00", "15:00", "18:00"]

# Day mapping for scheduling
DAY_MAP = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}


def get_credentials():
    """Get or refresh OAuth credentials."""
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
        else:
            if not CREDENTIALS_FILE.exists():
                print(f"ERROR: credentials.json not found. Run Google OAuth flow first.")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())

    return creds


def get_next_weekday(day_name: str) -> str:
    """Get the next occurrence of a weekday from today."""
    today = datetime.now()
    target = DAY_MAP.get(day_name.lower(), 0)
    days_ahead = target - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    next_day = today + timedelta(days=days_ahead)
    return next_day.strftime("%Y-%m-%d")


def load_posts(csv_path: str) -> list:
    """Load posts from CSV."""
    posts = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("Status", "").upper() == "PENDING":
                posts.append(row)
    return posts


def main():
    parser = argparse.ArgumentParser(description="Queue X posts to Google Sheets")
    parser.add_argument("--csv", default=str(DEFAULT_CSV), help="CSV file with posts")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    posts = load_posts(args.csv)
    if not posts:
        print("No pending posts found.")
        return

    print(f"Found {len(posts)} pending posts\n")

    # Prepare rows for Google Sheets
    # Expected columns: Post_ID | Content | Status | Category | Scheduled_Date | Scheduled_Time | Platform
    rows = []
    time_idx = 0
    for post in posts:
        day = post.get("Scheduled_Day", "monday")
        scheduled_date = get_next_weekday(day)
        scheduled_time = POSTING_TIMES[time_idx % len(POSTING_TIMES)]
        time_idx += 1

        row = [
            post.get("Post_ID", ""),
            post.get("Content", ""),
            "PENDING",
            post.get("Category", ""),
            scheduled_date,
            scheduled_time,
            "X/Twitter",
        ]
        rows.append(row)
        print(f"  {row[0]:10s} | {scheduled_date} {scheduled_time} | {row[1][:60]}...")

    if args.dry_run:
        print(f"\n[DRY RUN] Would write {len(rows)} rows to {SHEET_NAME}")
        return

    print(f"\nWriting {len(rows)} posts to Google Sheets...")
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)

    # Append rows to the sheet
    body = {"values": rows}
    result = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A:G",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body=body,
    ).execute()

    updated = result.get("updates", {}).get("updatedRows", 0)
    print(f"Queued {updated} posts to {SHEET_NAME}")
    print(f"Sheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")


if __name__ == "__main__":
    main()
