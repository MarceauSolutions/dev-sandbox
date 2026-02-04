#!/usr/bin/env python3
"""
Ideas Queue Manager

Reads pending ideas from Google Sheets that were captured via Telegram
when you weren't working. Used with "check my ideas" command.

Usage:
    python -m src.ideas_queue list          # Show pending ideas
    python -m src.ideas_queue complete 1    # Mark idea #1 as complete
    python -m src.ideas_queue action 1      # Action on idea #1
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    import pickle
except ImportError:
    print("Install: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

# Configuration
SPREADSHEET_ID = "1KfTupeA0VQASuYHccG4SmC9vFtJMtY0prJXe5xt36rE"
SHEET_NAME = "Sheet1"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_sheets_service():
    """Get authenticated Google Sheets service."""
    creds = None
    token_path = Path(__file__).parent.parent / "token.json"
    creds_path = Path(__file__).parent.parent.parent.parent.parent / "credentials.json"

    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                print(f"Missing credentials.json at {creds_path}")
                print("Generate from Google Cloud Console or run:")
                print("  python -c \"...\" # See CLAUDE.md for credential setup")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return build('sheets', 'v4', credentials=creds)

def list_pending_ideas():
    """List all pending ideas from the queue."""
    service = get_sheets_service()
    if not service:
        return []

    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A:E"
        ).execute()

        values = result.get('values', [])
        if not values or len(values) < 2:
            print("\n✨ No pending ideas! Your queue is empty.\n")
            return []

        headers = values[0]
        ideas = []

        print("\n" + "="*60)
        print("📋 YOUR IDEAS QUEUE")
        print("="*60 + "\n")

        for i, row in enumerate(values[1:], 1):
            # Pad row to expected length
            while len(row) < 5:
                row.append("")

            timestamp, idea, from_user, status, chat_id = row[:5]

            if status.lower() == "pending":
                ideas.append({
                    "row": i + 1,
                    "timestamp": timestamp,
                    "idea": idea,
                    "from": from_user,
                    "status": status
                })

                # Format timestamp
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime("%b %d, %I:%M %p")
                except:
                    time_str = timestamp[:16] if len(timestamp) > 16 else timestamp

                print(f"  [{i}] {time_str}")
                print(f"      💡 {idea}")
                print()

        if not ideas:
            print("  ✨ No pending ideas! All caught up.\n")
        else:
            print("-"*60)
            print(f"  {len(ideas)} pending idea(s)")
            print()
            print("  Commands:")
            print("    python -m src.ideas_queue complete <#>  - Mark done")
            print("    python -m src.ideas_queue action <#>    - Act on idea")
            print()

        return ideas

    except Exception as e:
        print(f"Error reading ideas: {e}")
        return []

def mark_complete(idea_num: int):
    """Mark an idea as complete."""
    service = get_sheets_service()
    if not service:
        return False

    try:
        # Update status column (D) for the given row
        row = idea_num + 1  # Account for header
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!D{row}",
            valueInputOption="RAW",
            body={"values": [["completed"]]}
        ).execute()

        print(f"\n✅ Idea #{idea_num} marked as complete!\n")
        return True

    except Exception as e:
        print(f"Error updating idea: {e}")
        return False

def action_on_idea(idea_num: int):
    """Show idea details for actioning."""
    ideas = list_pending_ideas()

    for idea in ideas:
        if idea["row"] - 1 == idea_num:
            print("\n" + "="*60)
            print(f"🎯 ACTIONING IDEA #{idea_num}")
            print("="*60)
            print(f"\n📝 {idea['idea']}\n")
            print("What would you like to do with this idea?")
            print("  1. Create a task/project")
            print("  2. Research it")
            print("  3. Schedule for later")
            print("  4. Mark as complete")
            print()
            return idea

    print(f"\n❌ Idea #{idea_num} not found in pending queue.\n")
    return None

def main():
    if len(sys.argv) < 2:
        list_pending_ideas()
        return

    command = sys.argv[1].lower()

    if command == "list":
        list_pending_ideas()
    elif command == "complete" and len(sys.argv) > 2:
        mark_complete(int(sys.argv[2]))
    elif command == "action" and len(sys.argv) > 2:
        action_on_idea(int(sys.argv[2]))
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
