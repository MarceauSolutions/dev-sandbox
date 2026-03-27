"""
Accountability Dashboard — Data Layer

Reads from Google Sheets scorecard and Stripe for live metrics.
Also reads local tasks.json and outreach tracking files.
"""

import os
import sys
import json
import csv
from datetime import datetime, timedelta, date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GOOGLE_OK = True
except ImportError:
    GOOGLE_OK = False

try:
    import stripe
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_OK = bool(stripe.api_key)
except ImportError:
    STRIPE_OK = False

# Constants
PLAN_START = datetime(2026, 3, 17)
PLAN_END = datetime(2026, 6, 7)
SCORECARD_ID = "1Y5PwloUBbHM8AeiL032_zWy9jjo9vwhyRZkl7qaKw5o"
TASKS_FILE = PROJECT_ROOT / "projects/marceau-solutions/fitness/tools/fitness-influencer/data/tenants/wmarceau/tasks.json"
TRACKING_DIR = PROJECT_ROOT / "projects/lead-generation/output"
APOLLO_CSV = PROJECT_ROOT / "projects/marceau-solutions/digital/outputs/naples-ai-prospects-apollo-enriched-2026-03-23.csv"
PIPELINE_DB = PROJECT_ROOT / "projects/lead-generation/sales-pipeline/data/pipeline.db"
CALENDAR_TOKEN = PROJECT_ROOT / "token.json"
TIME_BLOCKS_CALENDAR_ID = "c_710cb4eceeac036e44157b8626fe6447b430ce3fd0100020d4b32fc44af1f164@group.calendar.google.com"

TOKEN_PATHS = [
    PROJECT_ROOT / "token_sheets.json",
    Path.home() / "dev-sandbox" / "token_sheets.json",
    Path("/home/clawdbot/dev-sandbox/token_sheets.json"),
]

# Weekly targets
TARGETS = {
    "outreach": 500,
    "meetings": 5,
    "videos": 2,
    "content": 4,
    "training": 5,
}

# 90-day goals
GOALS = [
    {"name": "AI Clients", "target": 3, "metric": "clients_closed", "icon": "🤖"},
    {"name": "YouTube Subs", "target": 500, "metric": "youtube_subs", "icon": "📺"},
    {"name": "Digital Product", "target": 1, "metric": "products_live", "icon": "📦"},
    {"name": "Group Coaching Waitlist", "target": 5, "metric": "waitlist_count", "icon": "💪"},
    {"name": "Monthly Revenue", "target": 3000, "metric": "mrr", "icon": "💰"},
]


def _get_sheets():
    if not GOOGLE_OK:
        return None
    for p in TOKEN_PATHS:
        if p.exists():
            creds = Credentials.from_authorized_user_file(
                str(p), ["https://www.googleapis.com/auth/spreadsheets"]
            )
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(p, "w") as f:
                    f.write(creds.to_json())
            return build("sheets", "v4", credentials=creds)
    return None


def _read_tab(service, tab_name):
    result = service.spreadsheets().values().get(
        spreadsheetId=SCORECARD_ID, range=f"{tab_name}!A:O"
    ).execute()
    rows = result.get("values", [])
    if not rows:
        return []
    headers = rows[0]
    return [dict(zip(headers, row + [""] * (len(headers) - len(row)))) for row in rows[1:]]


def get_context():
    now = datetime.now()
    days_since = (now - PLAN_START).days
    day_number = max(1, days_since + 1)
    week_number = min(12, max(1, (day_number + 6) // 7))
    days_remaining = max(0, 84 - days_since)
    pct_complete = min(100, round((day_number / 84) * 100))
    return {
        "day_number": day_number,
        "week_number": week_number,
        "days_remaining": days_remaining,
        "today": now.strftime("%Y-%m-%d"),
        "day_of_week": now.strftime("%A"),
        "pct_complete": pct_complete,
        "plan_start": PLAN_START.strftime("%b %d"),
        "plan_end": PLAN_END.strftime("%b %d, %Y"),
    }


def get_daily_log():
    service = _get_sheets()
    if not service:
        return []
    return _read_tab(service, "Daily Log")


def get_weekly_summary():
    service = _get_sheets()
    if not service:
        return []
    return _read_tab(service, "Weekly Summary")


def get_goals_data():
    service = _get_sheets()
    if not service:
        return []
    return _read_tab(service, "90-Day Goals")


def get_milestones():
    service = _get_sheets()
    if not service:
        return []
    return _read_tab(service, "Milestones")


def get_stripe_mrr():
    if not STRIPE_OK:
        return 0
    try:
        subs = stripe.Subscription.list(status="active", limit=100)
        mrr_cents = 0
        for sub in subs.auto_paging_iter():
            for item in sub["items"]["data"]:
                amount = item["price"]["unit_amount"] or 0
                interval = item["price"]["recurring"]["interval"]
                if interval == "year":
                    mrr_cents += amount / 12
                elif interval == "month":
                    mrr_cents += amount
                elif interval == "week":
                    mrr_cents += amount * 4.33
        return round(mrr_cents / 100, 2)
    except Exception:
        return 0


def _safe_int(val, default=0):
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _safe_float(val, default=0.0):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def get_dashboard_data():
    """Get all data needed for the dashboard in one call."""
    ctx = get_context()
    daily = get_daily_log()
    weekly = get_weekly_summary()
    goals_raw = get_goals_data()
    milestones_raw = get_milestones()
    mrr = get_stripe_mrr()

    # Today's data
    today_data = None
    for row in reversed(daily):
        if row.get("Date") == ctx["today"]:
            today_data = row
            break

    # This week's daily entries
    this_week = [r for r in daily if _safe_int(r.get("Week_Number")) == ctx["week_number"]]

    # Weekly totals
    week_totals = {
        "outreach": sum(_safe_int(r.get("Outreach_Count")) for r in this_week),
        "meetings": sum(_safe_int(r.get("Meetings_Booked")) for r in this_week),
        "videos": sum(_safe_int(r.get("Videos_Filmed")) for r in this_week),
        "content": sum(_safe_int(r.get("Content_Posted")) for r in this_week),
        "training": sum(1 for r in this_week if r.get("Training_Session", "").upper() in ("TRUE", "YES", "1")),
    }

    # Week percentages vs targets
    week_pcts = {}
    for key, target in TARGETS.items():
        week_pcts[key] = min(100, round((week_totals[key] / target) * 100)) if target else 0

    # Overall on-track score (weighted)
    weights = {"outreach": 0.30, "meetings": 0.25, "videos": 0.15, "content": 0.10, "training": 0.20}
    on_track = sum(week_pcts.get(k, 0) * w for k, w in weights.items())

    # Energy trend (last 7 days)
    energy_data = []
    for row in daily[-14:]:
        e = _safe_int(row.get("Morning_Energy"))
        if e > 0:
            energy_data.append({"date": row.get("Date", ""), "energy": e, "pain": _safe_int(row.get("Pain_Level"))})

    # Streak calculation
    streak = 0
    for row in reversed(daily):
        outreach = _safe_int(row.get("Outreach_Count"))
        if outreach > 0:
            streak += 1
        else:
            break

    # Goals with progress
    goals = []
    for g in GOALS:
        # Try to find in sheets data
        sheet_goal = next((r for r in goals_raw if g["name"] in r.get("Goal", "")), None)
        current = _safe_float(sheet_goal.get("Current", 0)) if sheet_goal else 0
        if g["metric"] == "mrr":
            current = mrr
        pct = min(100, round((current / g["target"]) * 100)) if g["target"] else 0
        goals.append({**g, "current": current, "pct": pct})

    # Milestones
    milestones = []
    for m in milestones_raw:
        milestones.append({
            "name": m.get("Milestone_Name", ""),
            "achieved": m.get("Achieved", "").upper() in ("TRUE", "YES", "1"),
            "date": m.get("Achieved_Date", ""),
        })

    # Cumulative outreach
    total_outreach = sum(_safe_int(r.get("Outreach_Count")) for r in daily)

    # Weekly chart data (all weeks)
    weekly_chart = []
    for w in weekly:
        weekly_chart.append({
            "week": _safe_int(w.get("Week_Number")),
            "outreach": _safe_int(w.get("Total_Outreach")),
            "meetings": _safe_int(w.get("Total_Meetings")),
            "videos": _safe_int(w.get("Videos_Published")),
            "score": _safe_float(w.get("On_Track_Score")),
        })

    # Load local tasks
    tasks_data = get_local_tasks()

    # Load today's outreach log
    outreach_log = get_today_outreach_log()

    # Outreach count fallback: use tracking files if Sheets returns 0
    if week_totals["outreach"] == 0:
        today_tracking_count = _count_today_outreach()
        if today_tracking_count > 0:
            week_totals["outreach"] = today_tracking_count
            # Recalculate pct
            week_pcts["outreach"] = min(100, round((today_tracking_count / TARGETS["outreach"]) * 100))
            on_track = sum(week_pcts.get(k, 0) * w for k, w in weights.items())

    sheets_ok = bool(daily)  # If daily log has data, Sheets is connected

    return {
        "context": ctx,
        "today": today_data,
        "this_week": this_week,
        "week_totals": week_totals,
        "week_pcts": week_pcts,
        "targets": TARGETS,
        "on_track": round(on_track),
        "energy_data": energy_data,
        "streak": streak,
        "goals": goals,
        "milestones": milestones,
        "total_outreach": total_outreach,
        "mrr": mrr,
        "weekly_chart": weekly_chart,
        "daily_log": daily[-7:],  # Last 7 days
        "tasks": tasks_data,
        "outreach_log": outreach_log,
        "sheets_ok": sheets_ok,
    }


def get_local_tasks():
    """Load tasks from local tasks.json grouped by section."""
    result = {"today": [], "this_week": [], "circle_back": [], "recently_done": []}
    try:
        if not TASKS_FILE.exists():
            return result
        data = json.loads(TASKS_FILE.read_text())
        for t in data.get("tasks", []):
            section = t.get("section", "this_week")
            if section in result:
                result[section].append(t)
            # Tasks with status=complete always go to recently_done regardless of section
        # Sort each section: incomplete first by priority, then complete
        priority_order = {"high": 0, "medium": 1, "low": 2, "deferred": 3}
        for key in ("today", "this_week", "circle_back"):
            result[key].sort(key=lambda t: (
                1 if t.get("status") == "complete" else 0,
                priority_order.get(t.get("priority", "medium"), 1)
            ))
    except Exception:
        pass
    return result


def _count_today_outreach():
    """Count outreach emails sent today from tracking files."""
    today_str = str(date.today())
    total = 0
    try:
        for f in TRACKING_DIR.glob("outreach_tracking_*.json"):
            data = json.loads(f.read_text())
            if data.get("date") == today_str:
                total += data.get("total_sent", 0)
    except Exception:
        pass
    return total


def get_today_outreach_log():
    """Load today's outreach emails with Apollo industry enrichment."""
    today_str = str(date.today())
    emails = []
    try:
        # Load Apollo CSV for industry lookup
        apollo_by_email = {}
        apollo_by_company = {}
        if APOLLO_CSV.exists():
            with open(APOLLO_CSV, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    em = (row.get("email") or "").lower().strip()
                    co = (row.get("company_name") or "").lower().strip()
                    if em:
                        apollo_by_email[em] = row
                    if co:
                        apollo_by_company[co] = row

        # Load pipeline DB for stage info
        pipeline_stages = {}
        try:
            import sqlite3
            if PIPELINE_DB.exists():
                conn = sqlite3.connect(str(PIPELINE_DB))
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # Try common table structures
                try:
                    rows = cur.execute("SELECT email, stage FROM deals").fetchall()
                    for r in rows:
                        pipeline_stages[(r["email"] or "").lower()] = r["stage"]
                except Exception:
                    pass
                conn.close()
        except Exception:
            pass

        # Read tracking files for today
        for f in sorted(TRACKING_DIR.glob("outreach_tracking_*.json")):
            data = json.loads(f.read_text())
            if data.get("date") != today_str:
                continue
            for em in data.get("emails", []):
                recipient = (em.get("recipient") or "").lower()
                company_key = (em.get("company") or "").lower()

                # Enrich from Apollo
                apollo = apollo_by_email.get(recipient) or apollo_by_company.get(company_key) or {}
                industry = apollo.get("industry") or apollo.get("apollo_industry") or "—"

                # Pipeline stage
                stage = pipeline_stages.get(recipient, "")

                emails.append({
                    "first_name": em.get("first_name", ""),
                    "company": em.get("company", ""),
                    "email": em.get("recipient", ""),
                    "subject": em.get("subject", ""),
                    "industry": industry,
                    "sent_at": em.get("sent_at", ""),
                    "status": em.get("status", "sent"),
                    "pipeline_stage": stage,
                })
    except Exception:
        pass
    return emails


def get_current_time_block():
    """Fetch current and next time block from Google Calendar."""
    result = {"current": None, "next": None, "error": None}
    try:
        if not CALENDAR_TOKEN.exists():
            result["error"] = "Calendar token not found"
            return result

        creds = None
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
        except ImportError:
            result["error"] = "Google API libraries not installed"
            return result

        creds = Credentials.from_authorized_user_file(str(CALENDAR_TOKEN))
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

        service = build("calendar", "v3", credentials=creds)
        now = datetime.utcnow()
        time_min = now.strftime("%Y-%m-%dT00:00:00Z")
        time_max = now.strftime("%Y-%m-%dT23:59:59Z")

        events_result = service.events().list(
            calendarId=TIME_BLOCKS_CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        events = events_result.get("items", [])

        # Find current and next
        now_aware = datetime.utcnow()
        for i, ev in enumerate(events):
            start_str = ev.get("start", {}).get("dateTime") or ev.get("start", {}).get("date")
            end_str = ev.get("end", {}).get("dateTime") or ev.get("end", {}).get("date")
            if not start_str or not end_str:
                continue
            try:
                # Parse datetime (strip timezone for simple comparison)
                start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00")).replace(tzinfo=None)
                end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                continue

            if start_dt <= now_aware <= end_dt:
                mins_left = int((end_dt - now_aware).total_seconds() / 60)
                result["current"] = {
                    "title": ev.get("summary", "Untitled"),
                    "start": start_dt.strftime("%I:%M %p"),
                    "end": end_dt.strftime("%I:%M %p"),
                    "mins_left": mins_left,
                }
                # Find next
                if i + 1 < len(events):
                    nxt = events[i + 1]
                    nxt_start = nxt.get("start", {}).get("dateTime") or ""
                    try:
                        nxt_start_dt = datetime.fromisoformat(nxt_start.replace("Z", "+00:00")).replace(tzinfo=None)
                        result["next"] = {
                            "title": nxt.get("summary", "Untitled"),
                            "start": nxt_start_dt.strftime("%I:%M %p"),
                        }
                    except Exception:
                        pass
                break
            elif start_dt > now_aware and result["current"] is None:
                # No active block — show upcoming
                mins_until = int((start_dt - now_aware).total_seconds() / 60)
                result["next"] = {
                    "title": ev.get("summary", "Untitled"),
                    "start": start_dt.strftime("%I:%M %p"),
                    "mins_until": mins_until,
                }
                break

    except Exception as e:
        result["error"] = str(e)
    return result
