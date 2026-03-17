#!/usr/bin/env python3
"""
Monthly Business Review — Branded PDF via Telegram

WHAT: Pulls all weekly data for the month, computes trends, generates detailed review PDF
WHY: End-of-month business pulse with month-over-month comparison and recommendations
INPUT: Google Sheets Scorecard (all weekly summaries), Stripe API
OUTPUT: Branded PDF sent via Telegram

QUICK USAGE:
    python scripts/monthly-business-review.py              # Generate + send
    python scripts/monthly-business-review.py --preview    # Generate + open locally
    python scripts/monthly-business-review.py --month 3    # Specific month (1-12)
    python scripts/monthly-business-review.py --json       # Raw metrics as JSON

SCHEDULE: 1st of month 9am ET via launchd (com.marceausolutions.monthly-review.plist)

DEPENDENCIES: google-auth, google-auth-oauthlib, google-api-python-client, stripe, requests, reportlab
API_KEYS: STRIPE_SECRET_KEY, TELEGRAM_BOT_TOKEN, SCORECARD_SPREADSHEET_ID (all in .env)

Created: 2026-03-17
"""

import os
import sys
import json
import argparse
import subprocess
import requests
import calendar
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False

try:
    from execution.stripe_payments import StripePayments
    import stripe as stripe_lib
    HAS_STRIPE = True
except ImportError:
    HAS_STRIPE = False

try:
    from execution.branded_pdf_engine import BrandedPDFEngine
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

# Config
SPREADSHEET_ID = os.getenv("SCORECARD_SPREADSHEET_ID", "1Y5PwloUBbHM8AeiL032_zWy9jjo9vwhyRZkl7qaKw5o")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = "5692454753"
TOKEN_FILE = PROJECT_ROOT / "token_sheets.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file"]

DAILY_LOG_RANGE = "'Daily Log'!A:K"
WEEKLY_SUMMARY_RANGE = "'Weekly Summary'!A:O"
GOALS_RANGE = "'90-Day Goals'!A:F"


def get_sheets_service():
    """Build Sheets API service."""
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
            print("ERROR: Google Sheets credentials need re-auth.")
            return None
    return build("sheets", "v4", credentials=creds)


def fetch_sheet_data(service, range_name: str) -> List[List[str]]:
    """Fetch data from a sheet tab."""
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID, range=range_name
        ).execute()
        return result.get("values", [])
    except Exception as e:
        print(f"Error fetching {range_name}: {e}")
        return []


def get_month_boundaries(year: int, month: int) -> Tuple[datetime, datetime]:
    """Return (first_day, last_day) of the given month."""
    first = datetime(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    last = datetime(year, month, last_day, 23, 59, 59)
    return first, last


def parse_daily_log_for_month(rows: List[List[str]], year: int, month: int) -> Dict[str, Any]:
    """Sum daily metrics for entire month, grouped by week."""
    if not rows or len(rows) < 2:
        return {"total": {}, "by_week": {}, "days_logged": 0}

    headers = rows[0]
    col_map = {}
    for i, h in enumerate(headers):
        h_lower = h.lower().replace(" ", "_")
        if "outreach" in h_lower: col_map["outreach"] = i
        elif "meeting" in h_lower: col_map["meetings"] = i
        elif "video" in h_lower: col_map["videos"] = i
        elif "content" in h_lower: col_map["content"] = i
        elif "training" in h_lower: col_map["training"] = i
        elif "date" == h_lower: col_map["date"] = i

    date_col = col_map.get("date", 0)
    first, last = get_month_boundaries(year, month)
    month_total = {"outreach": 0, "meetings": 0, "videos": 0, "content": 0, "training": 0}
    by_week = {}
    days_logged = 0

    for row in rows[1:]:
        if len(row) <= date_col or not row[date_col].strip():
            continue
        try:
            row_date = datetime.strptime(row[date_col].strip(), "%Y-%m-%d")
        except ValueError:
            try:
                row_date = datetime.strptime(row[date_col].strip(), "%m/%d/%Y")
            except ValueError:
                continue

        if first <= row_date <= last:
            days_logged += 1
            iso_week = row_date.isocalendar()[1]
            if iso_week not in by_week:
                by_week[iso_week] = {"outreach": 0, "meetings": 0, "videos": 0, "content": 0, "training": 0}

            for key, idx in col_map.items():
                if key == "date":
                    continue
                if idx < len(row):
                    try:
                        val = int(row[idx]) if row[idx].strip() else 0
                    except ValueError:
                        val = 0
                    month_total[key] += val
                    by_week[iso_week][key] += val

    return {"total": month_total, "by_week": by_week, "days_logged": days_logged}


def parse_weekly_summaries_for_month(rows: List[List[str]], year: int, month: int) -> List[Dict[str, str]]:
    """Get all weekly summary rows that fall within the month."""
    if not rows or len(rows) < 2:
        return []

    headers = rows[0]
    first, last = get_month_boundaries(year, month)
    month_weeks = []

    for row in rows[1:]:
        if not row or len(row) < 2:
            continue
        date_str = row[1] if len(row) > 1 else ""
        if not date_str.strip():
            continue
        try:
            week_start = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        except ValueError:
            continue

        if first <= week_start <= last:
            week_data = {}
            for i, h in enumerate(headers):
                week_data[h] = row[i] if i < len(row) else ""
            month_weeks.append(week_data)

    return month_weeks


def get_stripe_monthly(year: int, month: int) -> Dict[str, Any]:
    """Get Stripe revenue for the month and previous month."""
    if not HAS_STRIPE:
        return {"error": "Stripe not available"}

    try:
        sp = StripePayments()
        stripe_lib.api_key = sp.api_key

        # This month
        first, last = get_month_boundaries(year, month)
        report = sp.get_revenue_report(first, last)

        # Previous month
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        prev_first, prev_last = get_month_boundaries(prev_year, prev_month)
        prev_report = sp.get_revenue_report(prev_first, prev_last)

        # Active subs
        subs = stripe_lib.Subscription.list(status="active", limit=100)
        active_subs = len(subs.data)
        mrr = sum(
            (sub.items.data[0].price.unit_amount or 0) * (sub.items.data[0].quantity or 1)
            for sub in subs.data if sub.items.data
        ) / 100

        return {
            "revenue": report["summary"]["total_revenue_dollars"],
            "charges": report["summary"]["successful_charges"],
            "prev_revenue": prev_report["summary"]["total_revenue_dollars"],
            "prev_charges": prev_report["summary"]["successful_charges"],
            "mrr": mrr,
            "active_subs": active_subs,
        }
    except Exception as e:
        return {"error": str(e)}


def trend_label(current: float, previous: float) -> str:
    """Return trend descriptor."""
    if previous == 0 and current == 0:
        return "Flat"
    if previous == 0:
        return "New (no prior data)"
    pct_change = ((current - previous) / previous) * 100
    if pct_change > 10:
        return f"Increasing (+{pct_change:.0f}%)"
    elif pct_change < -10:
        return f"Decreasing ({pct_change:.0f}%)"
    else:
        return f"Flat ({pct_change:+.0f}%)"


def generate_recommendations(daily: Dict, stripe_data: Dict, goals: List[Dict]) -> List[str]:
    """Generate actionable recommendations based on gaps."""
    recs = []
    totals = daily.get("total", {})

    if totals.get("outreach", 0) < 80:
        recs.append("Outreach is below target. Aim for 25+/week. Batch LinkedIn/email sessions daily.")

    if totals.get("meetings", 0) < 8:
        recs.append("Meeting volume is low. Review outreach messaging. Test new angles in DMs.")

    if totals.get("videos", 0) < 6:
        recs.append("Video output behind schedule. Batch-film 2-3 videos on dedicated shoot days.")

    if totals.get("content", 0) < 16:
        recs.append("Content posting below target. Schedule posts in advance using buffer days.")

    if "error" not in stripe_data:
        if stripe_data.get("revenue", 0) < 1000:
            recs.append("Revenue under $1,000/mo. Focus on closing pipeline deals this week.")
        if stripe_data.get("active_subs", 0) < 2:
            recs.append("Low subscription count. Prioritize converting leads to recurring clients.")

    for g in goals:
        status = g.get("Status", "")
        if status == "At Risk":
            recs.append(f"Goal at risk: '{g.get('Goal', '')[:40]}' — needs immediate attention.")

    if not recs:
        recs.append("All metrics trending well. Stay consistent and maintain current pace.")

    return recs


def build_monthly_report(year: int, month: int, daily: Dict, weeks: List[Dict],
                          goals: List[Dict], stripe_data: Dict) -> Dict:
    """Build the PDF data dict."""
    month_name = calendar.month_name[month]
    now = datetime.now()
    totals = daily.get("total", {})

    # Weekly breakdown table
    week_rows = []
    for w in weeks:
        week_rows.append(
            f"| {w.get('Week_Number', '')} | {w.get('Week_Starting', '')} | "
            f"{w.get('Total_Outreach', '0')} | {w.get('Total_Meetings', '0')} | "
            f"{w.get('Videos_Published', '0')} | {w.get('On_Track_Score', '')} |"
        )

    weekly_table = (
        "| Week | Starting | Outreach | Meetings | Videos | Score |\n"
        "|---|---|---|---|---|---|\n" + "\n".join(week_rows)
    ) if week_rows else "No weekly summary data available."

    # Month totals
    totals_md = (
        f"| Metric | This Month |\n|---|---|\n"
        f"| Outreach | {totals.get('outreach', 0)} |\n"
        f"| Meetings | {totals.get('meetings', 0)} |\n"
        f"| Videos | {totals.get('videos', 0)} |\n"
        f"| Content Posts | {totals.get('content', 0)} |\n"
        f"| Training Sessions | {totals.get('training', 0)} |\n"
        f"| Days Logged | {daily.get('days_logged', 0)} |"
    )

    # Revenue comparison
    if "error" not in stripe_data:
        rev_trend = trend_label(stripe_data.get("revenue", 0), stripe_data.get("prev_revenue", 0))
        charges_trend = trend_label(stripe_data.get("charges", 0), stripe_data.get("prev_charges", 0))
        revenue_md = (
            f"| Metric | This Month | Last Month | Trend |\n|---|---|---|---|\n"
            f"| Revenue | ${stripe_data.get('revenue', 0):,.2f} | ${stripe_data.get('prev_revenue', 0):,.2f} | {rev_trend} |\n"
            f"| Charges | {stripe_data.get('charges', 0)} | {stripe_data.get('prev_charges', 0)} | {charges_trend} |\n"
            f"| MRR | ${stripe_data.get('mrr', 0):,.2f} | — | — |\n"
            f"| Active Subs | {stripe_data.get('active_subs', 0)} | — | — |"
        )
    else:
        revenue_md = f"Stripe data unavailable: {stripe_data['error']}"

    # Goals
    goals_lines = []
    for g in goals:
        goals_lines.append(
            f"| {g.get('Goal', '')[:45]} | {g.get('Current', '')} | {g.get('Target', '')} | {g.get('Status', '')} |"
        )
    goals_table = (
        "| Goal | Current | Target | Status |\n|---|---|---|---|\n" + "\n".join(goals_lines)
    ) if goals_lines else "No goals data."

    # Recommendations
    recs = generate_recommendations(daily, stripe_data, goals)
    recs_md = "\n".join(f"- {r}" for r in recs)

    content = f"""## Monthly Summary — {month_name} {year}

{totals_md}

## Weekly Breakdown

{weekly_table}

## Revenue — Month-over-Month

{revenue_md}

## 90-Day Goal Progress

{goals_table}

## Trend Analysis

- **Outreach**: {trend_label(totals.get('outreach', 0), 0)}
- **Meetings**: {trend_label(totals.get('meetings', 0), 0)}
- **Videos**: {trend_label(totals.get('videos', 0), 0)}
- **Content**: {trend_label(totals.get('content', 0), 0)}

## Recommendations

{recs_md}

---

*Monthly Business Review generated {now.strftime('%B %d, %Y at %I:%M %p')}*
"""

    return {
        "title": "Monthly Business Review",
        "subtitle": f"{month_name} {year}",
        "author": "Marceau Solutions",
        "date": now.strftime("%Y-%m-%d"),
        "content_markdown": content,
    }


def generate_pdf(data: Dict) -> str:
    """Generate branded PDF."""
    if not HAS_PDF:
        raise RuntimeError("Branded PDF engine not available")

    engine = BrandedPDFEngine()
    output_dir = PROJECT_ROOT / "output" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"monthly-review-{data.get('date', datetime.now().strftime('%Y-%m-%d'))}.pdf"
    output_path = str(output_dir / filename)
    engine.generate_to_file("generic_document", data, output_path)
    return output_path


def send_telegram(pdf_path: str, month_name: str, year: int):
    """Send PDF via Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    caption = f"Monthly Business Review — {month_name} {year}"

    try:
        with open(pdf_path, "rb") as f:
            resp = requests.post(url, data={
                "chat_id": TELEGRAM_CHAT_ID, "caption": caption,
            }, files={"document": (Path(pdf_path).name, f, "application/pdf")})

        if resp.status_code == 200 and resp.json().get("ok"):
            print(f"Sent to Telegram chat {TELEGRAM_CHAT_ID}")
            return True
        else:
            print(f"Telegram send failed: {resp.text}")
            return False
    except Exception as e:
        print(f"Telegram error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Monthly Business Review")
    parser.add_argument("--preview", action="store_true", help="Open locally, don't send")
    parser.add_argument("--month", type=int, help="Month number (1-12), default: previous month")
    parser.add_argument("--year", type=int, help="Year, default: current year")
    parser.add_argument("--json", action="store_true", help="Raw metrics as JSON")
    args = parser.parse_args()

    now = datetime.now()

    # Default: review the previous month (run on 1st of month)
    if args.month:
        month = args.month
        year = args.year or now.year
    else:
        # If run on 1st-7th, review previous month; otherwise review current month
        if now.day <= 7:
            month = now.month - 1 if now.month > 1 else 12
            year = now.year if now.month > 1 else now.year - 1
        else:
            month = now.month
            year = now.year

    if args.year:
        year = args.year

    month_name = calendar.month_name[month]

    print("=" * 60)
    print(f"  MONTHLY BUSINESS REVIEW — {month_name} {year}")
    print("=" * 60)

    # Collect data
    print("\nCollecting metrics...")
    service = get_sheets_service()

    daily = {"total": {}, "by_week": {}, "days_logged": 0}
    weeks = []
    goals = []

    if service:
        daily_rows = fetch_sheet_data(service, DAILY_LOG_RANGE)
        daily = parse_daily_log_for_month(daily_rows, year, month)

        weekly_rows = fetch_sheet_data(service, WEEKLY_SUMMARY_RANGE)
        weeks = parse_weekly_summaries_for_month(weekly_rows, year, month)

        goals_rows = fetch_sheet_data(service, GOALS_RANGE)
        if goals_rows and len(goals_rows) > 1:
            headers = goals_rows[0]
            for row in goals_rows[1:]:
                if row and row[0].strip():
                    goal = {headers[i]: (row[i] if i < len(row) else "") for i in range(len(headers))}
                    goals.append(goal)

    stripe_data = get_stripe_monthly(year, month)

    if args.json:
        print(json.dumps({"daily": daily, "weeks": weeks, "goals": goals, "stripe": stripe_data},
                         indent=2, default=str))
        return

    # Build report
    print("Building report...")
    report_data = build_monthly_report(year, month, daily, weeks, goals, stripe_data)

    # Generate PDF
    print("Generating branded PDF...")
    pdf_path = generate_pdf(report_data)
    print(f"PDF: {pdf_path}")

    if args.preview:
        subprocess.run(["open", pdf_path])
        print("Opened PDF for preview.")
    else:
        print("Sending via Telegram...")
        success = send_telegram(pdf_path, month_name, year)
        if success:
            print("\nDone! Monthly review delivered.")
        else:
            print("\nTelegram delivery failed. PDF saved locally.")
            subprocess.run(["open", pdf_path])


if __name__ == "__main__":
    main()
