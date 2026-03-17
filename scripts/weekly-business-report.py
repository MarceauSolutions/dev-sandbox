#!/usr/bin/env python3
"""
Weekly Business Report — Branded PDF via Telegram

WHAT: Pulls Scorecard (Sheets), Stripe, AutoIterator data → branded PDF → Telegram
WHY: Automated Monday morning business pulse, no manual work required
INPUT: Google Sheets Scorecard, Stripe API, local experiment files
OUTPUT: Branded PDF sent via Telegram

QUICK USAGE:
    python scripts/weekly-business-report.py              # Generate + send
    python scripts/weekly-business-report.py --preview    # Generate + open locally (no send)
    python scripts/weekly-business-report.py --json       # Raw metrics as JSON

SCHEDULE: Monday 9am ET via launchd (com.marceausolutions.weekly-report.plist)

DEPENDENCIES: google-auth, google-auth-oauthlib, google-api-python-client, stripe, requests, reportlab
API_KEYS: STRIPE_SECRET_KEY, TELEGRAM_BOT_TOKEN, SCORECARD_SPREADSHEET_ID (all in .env)
GOOGLE_AUTH: credentials.json + token_sheets.json (OAuth flow)

Created: 2026-03-17
"""

import os
import sys
import json
import argparse
import subprocess
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

# Google Sheets auth
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False

# Stripe
try:
    from execution.stripe_payments import StripePayments
    HAS_STRIPE = True
except ImportError:
    HAS_STRIPE = False

# PDF engine
try:
    from execution.branded_pdf_engine import BrandedPDFEngine
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

# --- Configuration ---
SPREADSHEET_ID = os.getenv("SCORECARD_SPREADSHEET_ID", "1Y5PwloUBbHM8AeiL032_zWy9jjo9vwhyRZkl7qaKw5o")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = "5692454753"
TOKEN_FILE = PROJECT_ROOT / "token_sheets.json"
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file"]

# Sheet tab ranges
DAILY_LOG_RANGE = "'Daily Log'!A:K"
WEEKLY_SUMMARY_RANGE = "'Weekly Summary'!A:O"
GOALS_RANGE = "'90-Day Goals'!A:F"

# Weekly targets (for red/yellow/green)
TARGETS = {
    "outreach": 25,
    "meetings": 3,
    "videos": 2,
    "content": 5,
    "training": 5,
}


def get_sheets_credentials():
    """Get Google Sheets OAuth credentials."""
    if not HAS_GOOGLE:
        return None

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
        else:
            print("ERROR: Google Sheets credentials expired and cannot auto-refresh.")
            print("       Run: python scripts/create-scorecard-sheet.py to re-authenticate.")
            return None

    return creds


def get_sheets_service():
    """Build Sheets API service."""
    creds = get_sheets_credentials()
    if not creds:
        return None
    return build("sheets", "v4", credentials=creds)


def fetch_sheet_data(service, range_name: str) -> List[List[str]]:
    """Fetch data from a sheet tab."""
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
        ).execute()
        return result.get("values", [])
    except Exception as e:
        print(f"Error fetching {range_name}: {e}")
        return []


def get_current_week_number() -> int:
    """Get current week number in the 90-day plan (week 1 starts 2026-03-17)."""
    start = datetime(2026, 3, 17)
    now = datetime.now()
    delta = (now - start).days
    return max(1, (delta // 7) + 1)


def parse_daily_log(rows: List[List[str]]) -> Dict[str, Any]:
    """Parse Daily Log tab and sum metrics for the current week."""
    if not rows or len(rows) < 2:
        return {"outreach": 0, "meetings": 0, "videos": 0, "content": 0, "training": 0, "days_logged": 0}

    headers = rows[0]
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())  # Monday
    week_end = week_start + timedelta(days=6)

    totals = {"outreach": 0, "meetings": 0, "videos": 0, "content": 0, "training": 0, "days_logged": 0}

    # Column indices
    col_map = {}
    for i, h in enumerate(headers):
        h_lower = h.lower().replace(" ", "_")
        if "outreach" in h_lower:
            col_map["outreach"] = i
        elif "meeting" in h_lower:
            col_map["meetings"] = i
        elif "video" in h_lower:
            col_map["videos"] = i
        elif "content" in h_lower:
            col_map["content"] = i
        elif "training" in h_lower:
            col_map["training"] = i
        elif "date" == h_lower:
            col_map["date"] = i

    date_col = col_map.get("date", 0)

    for row in rows[1:]:
        if len(row) <= date_col or not row[date_col].strip():
            continue

        try:
            row_date = datetime.strptime(row[date_col].strip(), "%Y-%m-%d").date()
        except ValueError:
            try:
                row_date = datetime.strptime(row[date_col].strip(), "%m/%d/%Y").date()
            except ValueError:
                continue

        if week_start <= row_date <= week_end:
            totals["days_logged"] += 1
            for key, col_idx in col_map.items():
                if key == "date":
                    continue
                if col_idx < len(row):
                    try:
                        val = int(row[col_idx]) if row[col_idx].strip() else 0
                    except (ValueError, IndexError):
                        val = 0
                    totals[key] = totals.get(key, 0) + val

    return totals


def parse_weekly_summary(rows: List[List[str]]) -> Dict[str, Any]:
    """Parse Weekly Summary tab for current week."""
    if not rows or len(rows) < 2:
        return {}

    headers = rows[0]
    week_num = get_current_week_number()

    for row in rows[1:]:
        if not row:
            continue
        try:
            row_week = int(row[0]) if row[0].strip() else 0
        except ValueError:
            continue

        if row_week == week_num:
            result = {}
            for i, h in enumerate(headers):
                result[h] = row[i] if i < len(row) else ""
            return result

    return {}


def parse_goals(rows: List[List[str]]) -> List[Dict[str, str]]:
    """Parse 90-Day Goals tab."""
    if not rows or len(rows) < 2:
        return []

    headers = rows[0]
    goals = []
    for row in rows[1:]:
        if not row or not row[0].strip():
            continue
        goal = {}
        for i, h in enumerate(headers):
            goal[h] = row[i] if i < len(row) else ""
        goals.append(goal)

    return goals


def get_stripe_metrics() -> Dict[str, Any]:
    """Get Stripe revenue data."""
    if not HAS_STRIPE:
        return {"error": "Stripe not available"}

    try:
        sp = StripePayments()

        # 7-day revenue
        start_7 = datetime.now() - timedelta(days=7)
        report_7 = sp.get_revenue_report(start_7)

        # 30-day revenue
        start_30 = datetime.now() - timedelta(days=30)
        report_30 = sp.get_revenue_report(start_30)

        # Active subscriptions
        import stripe
        stripe.api_key = sp.api_key
        subs = stripe.Subscription.list(status="active", limit=100)
        active_subs = len(subs.data)
        mrr = sum(
            (sub.items.data[0].price.unit_amount or 0) * (sub.items.data[0].quantity or 1)
            for sub in subs.data
            if sub.items.data
        ) / 100  # cents to dollars

        return {
            "revenue_7d": report_7["summary"]["total_revenue_dollars"],
            "charges_7d": report_7["summary"]["successful_charges"],
            "revenue_30d": report_30["summary"]["total_revenue_dollars"],
            "charges_30d": report_30["summary"]["successful_charges"],
            "mrr": mrr,
            "active_subs": active_subs,
            "pending_invoices": report_7["summary"]["pending_invoices"],
            "pending_amount": report_7["summary"]["pending_amount_dollars"],
        }
    except Exception as e:
        return {"error": str(e)}


def get_auto_iterator_count() -> int:
    """Count AutoIterator experiments."""
    experiments_dir = PROJECT_ROOT / "data" / "auto_iterator" / "experiments"
    if not experiments_dir.exists():
        return 0

    count = 0
    for f in experiments_dir.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            if isinstance(data, list):
                count += len(data)
            elif isinstance(data, dict):
                count += len(data.get("experiments", [data]))
        except Exception:
            count += 1

    return count


def status_indicator(actual: float, target: float) -> str:
    """Return GREEN/YELLOW/RED text indicator based on % of target."""
    if target <= 0:
        return "[GREEN]"
    pct = actual / target
    if pct >= 0.8:
        return "[GREEN]"
    elif pct >= 0.5:
        return "[YELLOW]"
    else:
        return "[RED]"


def build_report_data(daily: Dict, weekly: Dict, goals: List[Dict], stripe_data: Dict, experiments: int) -> Dict:
    """Build the data dict for the branded PDF template."""
    now = datetime.now()
    week_num = get_current_week_number()

    # Metrics vs targets section
    metrics_lines = []
    for key, target in TARGETS.items():
        actual = daily.get(key, 0)
        indicator = status_indicator(actual, target)
        label = key.replace("_", " ").title()
        metrics_lines.append(f"| {label} | {actual} | {target} | {indicator} |")

    metrics_table = "| Metric | Actual | Target | Status |\n|---|---|---|---|\n" + "\n".join(metrics_lines)

    # Pipeline / weekly summary
    pipeline_lines = []
    if weekly:
        for key in ["Total_Outreach", "Total_Meetings", "Total_Proposals", "Clients_Closed"]:
            val = weekly.get(key, "0") or "0"
            label = key.replace("_", " ")
            pipeline_lines.append(f"- **{label}**: {val}")
        win = weekly.get("Win_of_Week", "")
        if win:
            pipeline_lines.append(f"- **Win of the Week**: {win}")
        focus = weekly.get("Focus_Area", "")
        if focus:
            pipeline_lines.append(f"- **Focus Area**: {focus}")

    pipeline_md = "\n".join(pipeline_lines) if pipeline_lines else "No weekly summary data yet."

    # Revenue section
    if "error" not in stripe_data:
        revenue_md = (
            f"| Metric | Value |\n|---|---|\n"
            f"| 7-Day Revenue | ${stripe_data.get('revenue_7d', 0):,.2f} |\n"
            f"| 30-Day Revenue | ${stripe_data.get('revenue_30d', 0):,.2f} |\n"
            f"| MRR | ${stripe_data.get('mrr', 0):,.2f} |\n"
            f"| Active Subscriptions | {stripe_data.get('active_subs', 0)} |\n"
            f"| Pending Invoices | {stripe_data.get('pending_invoices', 0)} (${stripe_data.get('pending_amount', 0):,.2f}) |"
        )
    else:
        revenue_md = f"Stripe data unavailable: {stripe_data['error']}"

    # 90-day goals
    goals_lines = []
    for g in goals:
        goal_name = g.get("Goal", "")
        current = g.get("Current", "")
        target = g.get("Target", "")
        pct = g.get("Pct_Complete", "")
        status = g.get("Status", "Not Started")
        goals_lines.append(f"| {goal_name[:50]} | {current} | {target} | {pct} | {status} |")

    goals_table = ("| Goal | Current | Target | % | Status |\n|---|---|---|---|---|\n" +
                    "\n".join(goals_lines)) if goals_lines else "No goals data."

    # Build full markdown
    content = f"""## This Week's Metrics (Week {week_num})

Days logged: {daily.get('days_logged', 0)} / 7

{metrics_table}

## Pipeline Summary

{pipeline_md}

## Revenue Summary

{revenue_md}

## 90-Day Goal Progress

{goals_table}

## AutoIterator Experiments

Total experiments tracked: **{experiments}**

---

*Report generated {now.strftime('%B %d, %Y at %I:%M %p')}*
"""

    return {
        "title": "Weekly Business Report",
        "subtitle": f"Week {week_num} — {now.strftime('%B %d, %Y')}",
        "author": "Marceau Solutions",
        "date": now.strftime("%Y-%m-%d"),
        "content_markdown": content,
    }


def generate_pdf(data: Dict) -> str:
    """Generate branded PDF, return file path."""
    if not HAS_PDF:
        raise RuntimeError("Branded PDF engine not available (reportlab missing?)")

    engine = BrandedPDFEngine()
    output_dir = PROJECT_ROOT / "output" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"weekly-report-{datetime.now().strftime('%Y-%m-%d')}.pdf"
    output_path = str(output_dir / filename)

    engine.generate_to_file("generic_document", data, output_path)
    return output_path


def send_telegram(pdf_path: str):
    """Send PDF via Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set in .env")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    week_num = get_current_week_number()
    caption = f"Weekly Business Report — Week {week_num} ({datetime.now().strftime('%B %d, %Y')})"

    try:
        with open(pdf_path, "rb") as f:
            resp = requests.post(url, data={
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption,
            }, files={"document": (Path(pdf_path).name, f, "application/pdf")})

        if resp.status_code == 200 and resp.json().get("ok"):
            print(f"Sent to Telegram chat {TELEGRAM_CHAT_ID}")
            return True
        else:
            print(f"Telegram send failed: {resp.text}")
            return False
    except Exception as e:
        print(f"Telegram send error: {e}")
        return False


def collect_all_metrics() -> Dict[str, Any]:
    """Collect all metrics from all sources."""
    # Google Sheets
    daily = {"outreach": 0, "meetings": 0, "videos": 0, "content": 0, "training": 0, "days_logged": 0}
    weekly = {}
    goals = []

    service = get_sheets_service()
    if service:
        daily_rows = fetch_sheet_data(service, DAILY_LOG_RANGE)
        daily = parse_daily_log(daily_rows)

        weekly_rows = fetch_sheet_data(service, WEEKLY_SUMMARY_RANGE)
        weekly = parse_weekly_summary(weekly_rows)

        goals_rows = fetch_sheet_data(service, GOALS_RANGE)
        goals = parse_goals(goals_rows)
    else:
        print("WARNING: Google Sheets not available, using empty data.")

    # Stripe
    stripe_data = get_stripe_metrics()

    # AutoIterator
    experiments = get_auto_iterator_count()

    return {
        "daily": daily,
        "weekly": weekly,
        "goals": goals,
        "stripe": stripe_data,
        "experiments": experiments,
    }


def main():
    parser = argparse.ArgumentParser(description="Weekly Business Report")
    parser.add_argument("--preview", action="store_true", help="Generate PDF and open locally (no Telegram)")
    parser.add_argument("--json", action="store_true", help="Output raw metrics as JSON")
    args = parser.parse_args()

    print("=" * 60)
    print("  WEEKLY BUSINESS REPORT")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # Collect data
    print("\nCollecting metrics...")
    metrics = collect_all_metrics()

    if args.json:
        # Serialize goals list for JSON output
        print(json.dumps(metrics, indent=2, default=str))
        return

    # Build report
    print("Building report...")
    report_data = build_report_data(
        metrics["daily"], metrics["weekly"], metrics["goals"],
        metrics["stripe"], metrics["experiments"]
    )

    # Generate PDF
    print("Generating branded PDF...")
    pdf_path = generate_pdf(report_data)
    print(f"PDF: {pdf_path}")

    if args.preview:
        # Open locally
        subprocess.run(["open", pdf_path])
        print("Opened PDF for preview.")
    else:
        # Send via Telegram
        print("Sending via Telegram...")
        success = send_telegram(pdf_path)
        if success:
            print("\nDone! Report delivered.")
        else:
            print("\nTelegram delivery failed. PDF saved locally.")
            subprocess.run(["open", pdf_path])


if __name__ == "__main__":
    main()
