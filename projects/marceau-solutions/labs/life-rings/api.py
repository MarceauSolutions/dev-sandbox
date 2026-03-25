#!/usr/bin/env python3
"""
Life Rings API — Bridges the web app to the accountability Google Sheets scorecard.
Reads/writes to the same Sheet that accountability_handler.py + Clawdbot use.

Runs on port 8797 and serves both the static files AND the API.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add project root for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    HAS_SHEETS = True
except ImportError:
    HAS_SHEETS = False
    print("WARNING: Google Sheets API not available. Running in localStorage-only mode.")

# Constants — same as accountability_handler.py
SCORECARD_SHEET_ID = "1Y5PwloUBbHM8AeiL032_zWy9jjo9vwhyRZkl7qaKw5o"
TOKEN_CANDIDATES = [
    PROJECT_ROOT / "token_sheets.json",
    Path.home() / "dev-sandbox" / "token_sheets.json",
]
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

COL_MAP = {
    "Date": "A", "Day_Number": "B", "Week_Number": "C", "Day_of_Week": "D",
    "Morning_Energy": "E", "Outreach_Count": "F", "Meetings_Booked": "G",
    "Videos_Filmed": "H", "Content_Posted": "I", "Training_Session": "J", "Notes": "K",
    "Pain_Level": "L", "Sleep_Quality": "M", "Training_Details": "N", "MRR_Snapshot": "O",
}


def get_sheets_service():
    """Get authenticated Google Sheets service."""
    if not HAS_SHEETS:
        return None
    creds = None
    token_path = None
    for candidate in TOKEN_CANDIDATES:
        if candidate.exists():
            token_path = candidate
            break
    if not token_path:
        return None
    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_path, "w") as f:
            f.write(creds.to_json())
    return build("sheets", "v4", credentials=creds)


def read_daily_log(service, days=7):
    """Read last N days from the Daily Log tab."""
    result = service.spreadsheets().values().get(
        spreadsheetId=SCORECARD_SHEET_ID,
        range="Daily Log!A:O"
    ).execute()
    rows = result.get("values", [])
    if not rows:
        return []
    headers = rows[0]
    data = []
    for row in rows[1:]:
        entry = dict(zip(headers, row + [""] * (len(headers) - len(row))))
        data.append(entry)
    # Return last N days
    return data[-days:] if len(data) > days else data


def read_goals(service):
    """Read 90-day goals."""
    result = service.spreadsheets().values().get(
        spreadsheetId=SCORECARD_SHEET_ID,
        range="90-Day Goals!A:D"
    ).execute()
    rows = result.get("values", [])
    if not rows:
        return []
    headers = rows[0]
    return [dict(zip(headers, row + [""] * (len(headers) - len(row)))) for row in rows[1:]]


def update_cell(service, tab, row_idx, col, value):
    """Update a single cell. row_idx is 1-based (row 2 = first data row)."""
    cell = f"{tab}!{col}{row_idx}"
    service.spreadsheets().values().update(
        spreadsheetId=SCORECARD_SHEET_ID,
        range=cell,
        valueInputOption="USER_ENTERED",
        body={"values": [[value]]}
    ).execute()


class LifeRingsHandler(SimpleHTTPRequestHandler):
    """Serve static files + API endpoints."""

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == '/api/today':
            self.handle_today()
        elif parsed.path == '/api/week':
            self.handle_week()
        elif parsed.path == '/api/goals':
            self.handle_goals()
        elif parsed.path == '/api/health':
            self.json_response({"status": "ok", "sheets": HAS_SHEETS})
        else:
            # Serve static files
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_len = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(content_len)) if content_len else {}

        if parsed.path == '/api/log':
            self.handle_log(body)
        else:
            self.json_response({"error": "not found"}, 404)

    def handle_today(self):
        service = get_sheets_service()
        if not service:
            self.json_response({"error": "sheets_unavailable", "data": {}})
            return
        try:
            rows = read_daily_log(service, days=1)
            today = datetime.now().strftime("%Y-%m-%d")
            today_data = None
            for row in rows:
                if row.get("Date") == today:
                    today_data = row
                    break
            self.json_response({"date": today, "data": today_data or {}})
        except Exception as e:
            self.json_response({"error": str(e)})

    def handle_week(self):
        service = get_sheets_service()
        if not service:
            self.json_response({"error": "sheets_unavailable", "data": []})
            return
        try:
            rows = read_daily_log(service, days=7)
            self.json_response({"data": rows})
        except Exception as e:
            self.json_response({"error": str(e)})

    def handle_goals(self):
        service = get_sheets_service()
        if not service:
            self.json_response({"error": "sheets_unavailable", "data": []})
            return
        try:
            goals = read_goals(service)
            self.json_response({"data": goals})
        except Exception as e:
            self.json_response({"error": str(e)})

    def handle_log(self, body):
        """Log a metric to the Sheets scorecard."""
        service = get_sheets_service()
        if not service:
            self.json_response({"error": "sheets_unavailable"})
            return
        try:
            field = body.get("field")
            value = body.get("value")
            if not field or field not in COL_MAP:
                self.json_response({"error": f"unknown field: {field}"})
                return

            today = datetime.now().strftime("%Y-%m-%d")
            rows = read_daily_log(service, days=30)

            # Find today's row
            row_idx = None
            for i, row in enumerate(rows):
                if row.get("Date") == today:
                    # Row index in sheet = header(1) + data rows before this + 1
                    result = service.spreadsheets().values().get(
                        spreadsheetId=SCORECARD_SHEET_ID,
                        range="Daily Log!A:A"
                    ).execute()
                    all_dates = [r[0] if r else "" for r in result.get("values", [])]
                    for j, d in enumerate(all_dates):
                        if d == today:
                            row_idx = j + 1
                            break
                    break

            if row_idx:
                update_cell(service, "Daily Log", row_idx, COL_MAP[field], value)
                self.json_response({"status": "updated", "field": field, "value": value})
            else:
                self.json_response({"error": "no row for today — run EOD first"})
        except Exception as e:
            self.json_response({"error": str(e)})

    def json_response(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        pass  # Suppress request logging


if __name__ == "__main__":
    PORT = 8797
    os.chdir(Path(__file__).parent)
    server = HTTPServer(("", PORT), LifeRingsHandler)
    print(f"Life Rings running at http://127.0.0.1:{PORT}")
    server.serve_forever()
