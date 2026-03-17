#!/usr/bin/env python3
"""
progress_dashboard.py — Marceau Execution System Progress Dashboard

WHAT: Real-time terminal dashboard showing 12-week plan progress
WHY: William needs a single command to see where he stands — no browser, no spreadsheet digging
INPUT: Google Sheets (Weekly Scorecard), Stripe API (live MRR)
OUTPUT: Color-coded terminal dashboard with ASCII progress bars

QUICK USAGE:
  python scripts/progress_dashboard.py              # Full dashboard
  python scripts/progress_dashboard.py --quick       # One-line summary
  python scripts/progress_dashboard.py --json        # JSON output (for n8n/automation)

DEPENDENCIES: google-auth, google-auth-oauthlib, google-api-python-client, stripe, python-dotenv
API_KEYS: STRIPE_SECRET_KEY, SCORECARD_SPREADSHEET_ID (in .env)
GOOGLE_AUTH: credentials.json + token_sheets.json (OAuth2 flow)
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

# ─── Configuration ────────────────────────────────────────────────────────────

PLAN_START_DATE = datetime(2026, 3, 17)  # Monday of Week 1
PLAN_END_DATE = datetime(2026, 6, 8)     # End of Week 12 (Sunday)
PLAN_DURATION_DAYS = 84                  # 12 weeks

# Google Sheets
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token_sheets.json"
SCORECARD_SHEET_ID = os.getenv("SCORECARD_SPREADSHEET_ID", "")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Stripe
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")

# 90-Day Targets
TARGETS_90DAY = {
    "ai_clients":       {"label": "AI Services Clients",     "target": 3,    "unit": "clients"},
    "youtube_subs":     {"label": "YouTube Subscribers",      "target": 500,  "unit": "subs"},
    "digital_product":  {"label": "Digital Product Live",     "target": 1,    "unit": "product"},
    "group_coaching":   {"label": "Group Coaching Forming",   "target": 5,    "unit": "waitlist"},
    "monthly_revenue":  {"label": "Monthly Revenue",          "target": 3000, "unit": "$"},
}

# Weekly targets by phase
WEEKLY_TARGETS = {
    "weeks_1_2": {
        "outreach": 500, "meetings": 4, "proposals": 2, "clients": 1,
        "mrr": 0, "videos": 2, "shorts": 4, "training": 4,
    },
    "weeks_3_4": {
        "outreach": 500, "meetings": 7, "proposals": 4, "clients": 1,
        "mrr": 750, "videos": 2, "shorts": 4, "training": 4,
    },
    "month_2_plus": {
        "outreach": 300, "meetings": 7, "proposals": 4, "clients": 1,
        "mrr": 2000, "videos": 2, "shorts": 4, "training": 4,
    },
}

# ─── Terminal Colors ──────────────────────────────────────────────────────────

class C:
    """ANSI color codes for terminal output."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    GOLD    = "\033[38;2;201;150;60m"     # #C9963C
    CHARCOAL = "\033[38;2;51;51;51m"
    GREEN   = "\033[38;2;34;197;94m"
    YELLOW  = "\033[38;2;245;158;11m"
    RED     = "\033[38;2;239;68;68m"
    BLUE    = "\033[38;2;59;130;246m"
    WHITE   = "\033[97m"
    GRAY    = "\033[90m"
    BG_DARK = "\033[48;2;45;45;45m"
    BG_GOLD = "\033[48;2;201;150;60m"


def color_status(pct: float) -> str:
    """Return color code based on percentage to target."""
    if pct >= 100:
        return C.GREEN
    elif pct >= 60:
        return C.YELLOW
    else:
        return C.RED


def status_label(pct: float) -> str:
    """Return status label based on percentage."""
    if pct >= 100:
        return f"{C.GREEN}ON TRACK{C.RESET}"
    elif pct >= 60:
        return f"{C.YELLOW}AT RISK{C.RESET}"
    else:
        return f"{C.RED}BEHIND{C.RESET}"


def progress_bar(pct: float, width: int = 30) -> str:
    """Render an ASCII progress bar with color."""
    pct = min(pct, 100)
    filled = int(width * pct / 100)
    empty = width - filled
    color = color_status(pct)
    bar = f"{color}{'█' * filled}{C.GRAY}{'░' * empty}{C.RESET}"
    return bar


# ─── Google Sheets Integration ────────────────────────────────────────────────

def get_sheets_credentials():
    """Get or refresh Google OAuth credentials."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
    except ImportError:
        print(f"{C.YELLOW}[WARN] google-auth not installed. Run: pip install google-auth google-auth-oauthlib google-api-python-client{C.RESET}")
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
            print(f"{C.YELLOW}[WARN] No valid Google credentials. Run a Sheets script first to authenticate.{C.RESET}")
            return None

    return creds


def fetch_scorecard_data() -> Dict[str, Any]:
    """Fetch current week's data from the Weekly Scorecard Google Sheet."""
    if not SCORECARD_SHEET_ID:
        return {"error": "SCORECARD_SPREADSHEET_ID not set in .env"}

    creds = get_sheets_credentials()
    if not creds:
        return {"error": "Google credentials not available"}

    try:
        from googleapiclient.discovery import build
        service = build("sheets", "v4", credentials=creds)

        # Fetch Weekly Scorecard — all rows to find latest
        result = service.spreadsheets().values().get(
            spreadsheetId=SCORECARD_SHEET_ID,
            range="Weekly Scorecard!A1:Z100",
        ).execute()
        weekly_rows = result.get("values", [])

        # Fetch 90-Day Goals
        result90 = service.spreadsheets().values().get(
            spreadsheetId=SCORECARD_SHEET_ID,
            range="90-Day Goals!A1:J10",
        ).execute()
        goals_rows = result90.get("values", [])

        # Fetch Daily Tracker for this week
        result_daily = service.spreadsheets().values().get(
            spreadsheetId=SCORECARD_SHEET_ID,
            range="Daily Tracker!A1:L100",
        ).execute()
        daily_rows = result_daily.get("values", [])

        # Fetch Monthly Revenue
        result_monthly = service.spreadsheets().values().get(
            spreadsheetId=SCORECARD_SHEET_ID,
            range="Monthly Revenue!A1:J20",
        ).execute()
        monthly_rows = result_monthly.get("values", [])

        return {
            "weekly": weekly_rows,
            "goals": goals_rows,
            "daily": daily_rows,
            "monthly": monthly_rows,
        }

    except Exception as e:
        return {"error": f"Sheets API error: {e}"}


def parse_scorecard(data: Dict) -> Dict[str, Any]:
    """Parse raw Sheets data into structured metrics."""
    parsed = {
        "outreach_total": 0,
        "meetings_total": 0,
        "proposals_total": 0,
        "clients_total": 0,
        "setup_revenue": 0,
        "mrr": 0,
        "videos_total": 0,
        "shorts_total": 0,
        "youtube_subs": 0,
        "email_list": 0,
        "digital_sales": 0,
        "training_avg": 0,
        "energy_avg": 0,
        "sleep_avg": 0,
        "weeks_entered": 0,
        "current_week_outreach": 0,
        "current_week_meetings": 0,
    }

    if "error" in data:
        return parsed

    # Parse weekly scorecard rows (skip header + target rows = rows 0-2, data starts row 3)
    weekly = data.get("weekly", [])
    if len(weekly) > 3:
        headers = weekly[0] if weekly else []

        # Find column indices by header name matching
        col_map = {}
        for i, h in enumerate(headers):
            h_lower = h.lower().strip() if h else ""
            if "outreach" in h_lower and "message" in h_lower:
                col_map["outreach"] = i
            elif "meetings booked" in h_lower:
                col_map["meetings"] = i
            elif "proposals" in h_lower:
                col_map["proposals"] = i
            elif "clients closed" in h_lower:
                col_map["clients"] = i
            elif "setup revenue" in h_lower:
                col_map["setup_revenue"] = i
            elif "monthly recurring" in h_lower or "mrr" in h_lower:
                col_map["mrr"] = i
            elif "youtube videos" in h_lower:
                col_map["videos"] = i
            elif "shorts" in h_lower or "reels" in h_lower:
                col_map["shorts"] = i
            elif "subscriber" in h_lower:
                col_map["youtube_subs"] = i
            elif "email list" in h_lower:
                col_map["email_list"] = i
            elif "digital product" in h_lower:
                col_map["digital_sales"] = i
            elif "training" in h_lower:
                col_map["training"] = i
            elif "energy" in h_lower:
                col_map["energy"] = i
            elif "sleep" in h_lower:
                col_map["sleep"] = i

        data_rows = weekly[3:]  # Skip header + 2 target rows
        parsed["weeks_entered"] = len(data_rows)

        for row in data_rows:
            def safe_num(idx):
                try:
                    val = row[idx] if idx < len(row) else "0"
                    return float(str(val).replace("$", "").replace(",", "").strip() or "0")
                except (ValueError, IndexError):
                    return 0

            if "outreach" in col_map:
                parsed["outreach_total"] += safe_num(col_map["outreach"])
            if "meetings" in col_map:
                parsed["meetings_total"] += safe_num(col_map["meetings"])
            if "proposals" in col_map:
                parsed["proposals_total"] += safe_num(col_map["proposals"])
            if "clients" in col_map:
                parsed["clients_total"] += safe_num(col_map["clients"])
            if "setup_revenue" in col_map:
                parsed["setup_revenue"] += safe_num(col_map["setup_revenue"])
            if "videos" in col_map:
                parsed["videos_total"] += safe_num(col_map["videos"])
            if "shorts" in col_map:
                parsed["shorts_total"] += safe_num(col_map["shorts"])
            if "training" in col_map:
                parsed["training_avg"] += safe_num(col_map["training"])

        # Last row = current week (for MRR, subs — these are point-in-time, not cumulative)
        if data_rows:
            last = data_rows[-1]
            def safe_last(key):
                try:
                    idx = col_map.get(key, -1)
                    if idx < 0 or idx >= len(last):
                        return 0
                    return float(str(last[idx]).replace("$", "").replace(",", "").strip() or "0")
                except (ValueError, IndexError):
                    return 0

            parsed["mrr"] = safe_last("mrr")
            parsed["youtube_subs"] = safe_last("youtube_subs")
            parsed["email_list"] = safe_last("email_list")
            parsed["digital_sales"] += safe_last("digital_sales")
            parsed["current_week_outreach"] = safe_last("outreach")
            parsed["current_week_meetings"] = safe_last("meetings")

        if parsed["weeks_entered"] > 0:
            parsed["training_avg"] = parsed["training_avg"] / parsed["weeks_entered"]

    # Parse 90-Day Goals
    goals = data.get("goals", [])
    parsed["goals"] = []
    if len(goals) > 1:
        goal_headers = goals[0]
        for row in goals[1:]:
            if len(row) >= 4:
                parsed["goals"].append({
                    "goal": row[0] if len(row) > 0 else "",
                    "target": row[1] if len(row) > 1 else "",
                    "current": row[2] if len(row) > 2 else "",
                    "pct": row[3] if len(row) > 3 else "0%",
                    "status": row[7] if len(row) > 7 else "Unknown",
                })

    return parsed


# ─── Stripe Integration ───────────────────────────────────────────────────────

def fetch_stripe_mrr() -> Dict[str, Any]:
    """Fetch live MRR from Stripe active subscriptions."""
    if not STRIPE_SECRET_KEY:
        return {"mrr": 0, "error": "STRIPE_SECRET_KEY not set"}

    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY

        # Get active subscriptions
        subscriptions = stripe.Subscription.list(status="active", limit=100)
        mrr = 0
        sub_count = 0
        for sub in subscriptions.auto_paging_iter():
            for item in sub["items"]["data"]:
                amount = item["price"]["unit_amount"] or 0
                interval = item["price"]["recurring"]["interval"] if item["price"].get("recurring") else "month"
                if interval == "year":
                    mrr += amount / 12
                elif interval == "month":
                    mrr += amount
                elif interval == "week":
                    mrr += amount * 4.33
            sub_count += 1

        mrr_dollars = mrr / 100  # Stripe amounts are in cents

        # Get recent charges (this month)
        now = datetime.now()
        month_start = datetime(now.year, now.month, 1)
        charges = stripe.Charge.list(
            created={"gte": int(month_start.timestamp())},
            limit=100,
        )
        month_revenue = sum(c["amount"] for c in charges.auto_paging_iter() if c["paid"] and not c["refunded"]) / 100

        return {
            "mrr": mrr_dollars,
            "active_subscriptions": sub_count,
            "month_revenue": month_revenue,
        }

    except ImportError:
        return {"mrr": 0, "error": "stripe package not installed. Run: pip install stripe"}
    except Exception as e:
        return {"mrr": 0, "error": f"Stripe API error: {e}"}


# ─── Time Calculations ────────────────────────────────────────────────────────

def get_time_context() -> Dict[str, Any]:
    """Calculate current position in the 12-week plan."""
    now = datetime.now()
    days_in = max(0, (now - PLAN_START_DATE).days)
    days_remaining = max(0, (PLAN_END_DATE - now).days)
    week_number = min(12, max(1, (days_in // 7) + 1))
    pct_time_elapsed = min(100, round((days_in / PLAN_DURATION_DAYS) * 100, 1))

    # Determine which target set to use
    if week_number <= 2:
        target_key = "weeks_1_2"
        target_label = "Weeks 1-2"
    elif week_number <= 4:
        target_key = "weeks_3_4"
        target_label = "Weeks 3-4"
    else:
        target_key = "month_2_plus"
        target_label = "Month 2+"

    return {
        "now": now,
        "days_in": days_in,
        "days_remaining": days_remaining,
        "week_number": week_number,
        "pct_time_elapsed": pct_time_elapsed,
        "target_key": target_key,
        "target_label": target_label,
        "plan_started": days_in >= 0,
        "plan_complete": days_remaining <= 0,
    }


# ─── Health Score ─────────────────────────────────────────────────────────────

def calculate_health_score(metrics: Dict, stripe_data: Dict, time_ctx: Dict) -> Tuple[float, Dict]:
    """
    Calculate weighted health score (0-100) across all dimensions.

    Weights:
    - Revenue/Clients: 35% (this is what pays bills)
    - Outreach/Pipeline: 30% (leading indicator)
    - Content/Brand: 20% (long-term wealth)
    - Health/Energy: 15% (sustainability)
    """
    targets = WEEKLY_TARGETS[time_ctx["target_key"]]
    weeks = max(1, metrics.get("weeks_entered", 1))

    scores = {}

    # Revenue & Clients (35%)
    mrr = stripe_data.get("mrr", 0) or metrics.get("mrr", 0)
    mrr_target = TARGETS_90DAY["monthly_revenue"]["target"]
    client_pct = min(100, (metrics["clients_total"] / TARGETS_90DAY["ai_clients"]["target"]) * 100) if TARGETS_90DAY["ai_clients"]["target"] > 0 else 0
    mrr_pct = min(100, (mrr / mrr_target) * 100) if mrr_target > 0 else 0
    scores["revenue"] = {"score": (client_pct * 0.5 + mrr_pct * 0.5), "weight": 0.35, "label": "Revenue & Clients"}

    # Outreach & Pipeline (30%)
    outreach_pct = min(100, (metrics.get("current_week_outreach", 0) / targets["outreach"]) * 100) if targets["outreach"] > 0 else 0
    meetings_pct = min(100, (metrics.get("current_week_meetings", 0) / targets["meetings"]) * 100) if targets["meetings"] > 0 else 0
    scores["pipeline"] = {"score": (outreach_pct * 0.6 + meetings_pct * 0.4), "weight": 0.30, "label": "Outreach & Pipeline"}

    # Content & Brand (20%)
    video_pct = min(100, (metrics["videos_total"] / max(1, targets["videos"] * weeks)) * 100)
    subs_pct = min(100, (metrics["youtube_subs"] / TARGETS_90DAY["youtube_subs"]["target"]) * 100)
    scores["content"] = {"score": (video_pct * 0.5 + subs_pct * 0.5), "weight": 0.20, "label": "Content & Brand"}

    # Health (15%)
    training_pct = min(100, (metrics["training_avg"] / targets["training"]) * 100) if targets["training"] > 0 else 0
    energy_pct = min(100, (metrics.get("energy_avg", 5) / 10) * 100)
    scores["health"] = {"score": (training_pct * 0.6 + energy_pct * 0.4), "weight": 0.15, "label": "Health & Energy"}

    # Weighted total
    total = sum(s["score"] * s["weight"] for s in scores.values())

    return round(total, 1), scores


# ─── Dashboard Rendering ──────────────────────────────────────────────────────

def render_header(time_ctx: Dict):
    """Render the dashboard header."""
    w = time_ctx["week_number"]
    dr = time_ctx["days_remaining"]
    pct = time_ctx["pct_time_elapsed"]

    print()
    print(f"  {C.BG_DARK}{C.GOLD}{C.BOLD}  ╔══════════════════════════════════════════════════════════╗  {C.RESET}")
    print(f"  {C.BG_DARK}{C.GOLD}{C.BOLD}  ║          MARCEAU EXECUTION SYSTEM — DASHBOARD           ║  {C.RESET}")
    print(f"  {C.BG_DARK}{C.GOLD}{C.BOLD}  ║            Embrace the Pain & Defy the Odds             ║  {C.RESET}")
    print(f"  {C.BG_DARK}{C.GOLD}{C.BOLD}  ╚══════════════════════════════════════════════════════════╝  {C.RESET}")
    print()
    print(f"  {C.WHITE}{C.BOLD}Week {w}/12{C.RESET}  {C.GRAY}|{C.RESET}  {C.WHITE}{dr} days remaining{C.RESET}  {C.GRAY}|{C.RESET}  {C.WHITE}{pct}% of plan elapsed{C.RESET}")
    print(f"  {C.GRAY}Target phase: {time_ctx['target_label']}{C.RESET}")
    print(f"  {C.GRAY}{time_ctx['now'].strftime('%A, %B %d, %Y — %I:%M %p')}{C.RESET}")
    print()


def render_90day_goals(metrics: Dict, stripe_data: Dict):
    """Render the 90-day goal progress section."""
    print(f"  {C.GOLD}{C.BOLD}── 90-DAY GOALS ──────────────────────────────────────────{C.RESET}")
    print()

    mrr = stripe_data.get("mrr", 0) or metrics.get("mrr", 0)

    goals = [
        ("AI Services Clients",    metrics["clients_total"],    TARGETS_90DAY["ai_clients"]["target"],    "clients"),
        ("YouTube Subscribers",     metrics["youtube_subs"],     TARGETS_90DAY["youtube_subs"]["target"],  "subs"),
        ("Digital Product Live",    metrics["digital_sales"] > 0 and 1 or 0, TARGETS_90DAY["digital_product"]["target"], "product"),
        ("Group Coaching Waitlist", 0,                           TARGETS_90DAY["group_coaching"]["target"], "signups"),
        ("Monthly Revenue",         mrr,                         TARGETS_90DAY["monthly_revenue"]["target"], "$"),
    ]

    for label, current, target, unit in goals:
        pct = min(100, (current / target * 100)) if target > 0 else 0
        bar = progress_bar(pct, 25)
        if unit == "$":
            current_str = f"${current:,.0f}"
            target_str = f"${target:,.0f}"
        else:
            current_str = f"{int(current)}"
            target_str = f"{int(target)}"

        status = status_label(pct)
        print(f"  {C.WHITE}{label:<26}{C.RESET} {bar} {color_status(pct)}{pct:5.1f}%{C.RESET}  {current_str}/{target_str} {unit}  {status}")

    print()


def render_weekly_metrics(metrics: Dict, time_ctx: Dict):
    """Render current week's performance vs targets."""
    targets = WEEKLY_TARGETS[time_ctx["target_key"]]

    print(f"  {C.GOLD}{C.BOLD}── THIS WEEK vs TARGETS ({time_ctx['target_label']}) ────────────────────{C.RESET}")
    print()

    items = [
        ("Outreach Messages",  metrics.get("current_week_outreach", 0), targets["outreach"]),
        ("Meetings Booked",    metrics.get("current_week_meetings", 0), targets["meetings"]),
        ("Videos Published",   metrics.get("videos_total", 0) % max(1, metrics.get("weeks_entered", 1) or 1), targets["videos"]),
        ("Training Sessions",  metrics.get("training_avg", 0), targets["training"]),
    ]

    for label, current, target in items:
        pct = min(100, (current / target * 100)) if target > 0 else 0
        bar = progress_bar(pct, 20)
        color = color_status(pct)
        print(f"  {C.WHITE}{label:<22}{C.RESET} {bar} {color}{int(current)}/{int(target)}{C.RESET}")

    print()


def render_revenue_tracker(metrics: Dict, stripe_data: Dict):
    """Render revenue breakdown."""
    print(f"  {C.GOLD}{C.BOLD}── REVENUE TRACKER ───────────────────────────────────────{C.RESET}")
    print()

    mrr = stripe_data.get("mrr", 0) or metrics.get("mrr", 0)
    setup = metrics.get("setup_revenue", 0)
    month_rev = stripe_data.get("month_revenue", 0)
    active_subs = stripe_data.get("active_subscriptions", 0)

    print(f"  {C.WHITE}MRR (Stripe):         {C.GREEN}${mrr:,.2f}{C.RESET}/mo  ({active_subs} active subscriptions)")
    print(f"  {C.WHITE}Setup Revenue (cum.):  {C.GREEN}${setup:,.2f}{C.RESET}")
    print(f"  {C.WHITE}This Month (Stripe):   {C.GREEN}${month_rev:,.2f}{C.RESET}")

    # Revenue target bar
    target = TARGETS_90DAY["monthly_revenue"]["target"]
    pct = min(100, (mrr / target * 100)) if target > 0 else 0
    bar = progress_bar(pct, 30)
    print(f"  {C.WHITE}Progress to $3K/mo:    {bar} {color_status(pct)}{pct:.1f}%{C.RESET}")

    print()


def render_content_tracker(metrics: Dict):
    """Render content production metrics."""
    print(f"  {C.GOLD}{C.BOLD}── CONTENT OUTPUT ────────────────────────────────────────{C.RESET}")
    print()

    print(f"  {C.WHITE}YouTube Videos:    {C.BLUE}{int(metrics['videos_total'])}{C.RESET}  (target: 2/week)")
    print(f"  {C.WHITE}Shorts/Reels:      {C.BLUE}{int(metrics['shorts_total'])}{C.RESET}  (target: 4/week)")
    print(f"  {C.WHITE}Subscribers:       {C.BLUE}{int(metrics['youtube_subs'])}{C.RESET}  (target: 500 by day 90)")
    print(f"  {C.WHITE}Email List:        {C.BLUE}{int(metrics['email_list'])}{C.RESET}")

    print()


def render_health_score(total_score: float, component_scores: Dict):
    """Render the overall health score."""
    print(f"  {C.GOLD}{C.BOLD}── OVERALL HEALTH SCORE ──────────────────────────────────{C.RESET}")
    print()

    # Big score display
    color = color_status(total_score)
    bar = progress_bar(total_score, 40)
    print(f"  {color}{C.BOLD}  {total_score:.0f}/100{C.RESET}  {bar}")
    print()

    # Component breakdown
    for key, data in component_scores.items():
        score = data["score"]
        weight = data["weight"]
        label = data["label"]
        color = color_status(score)
        mini_bar = progress_bar(score, 15)
        print(f"  {C.WHITE}{label:<22}{C.RESET} {mini_bar} {color}{score:5.1f}%{C.RESET}  {C.GRAY}(weight: {int(weight*100)}%){C.RESET}")

    print()


def render_pipeline_summary(metrics: Dict):
    """Render outreach and pipeline cumulative stats."""
    print(f"  {C.GOLD}{C.BOLD}── PIPELINE (CUMULATIVE) ─────────────────────────────────{C.RESET}")
    print()

    outreach = int(metrics["outreach_total"])
    meetings = int(metrics["meetings_total"])
    proposals = int(metrics["proposals_total"])
    clients = int(metrics["clients_total"])

    # Funnel visualization
    o2m = (meetings / outreach * 100) if outreach > 0 else 0
    m2p = (proposals / meetings * 100) if meetings > 0 else 0
    p2c = (clients / proposals * 100) if proposals > 0 else 0

    print(f"  {C.WHITE}Outreach:    {C.BOLD}{outreach:>6}{C.RESET}  messages sent")
    print(f"  {C.WHITE}    └─►  Meetings:  {C.BOLD}{meetings:>4}{C.RESET}  booked  ({C.BLUE}{o2m:.1f}%{C.RESET} conversion)")
    print(f"  {C.WHITE}           └─►  Proposals: {C.BOLD}{proposals:>3}{C.RESET}  sent    ({C.BLUE}{m2p:.1f}%{C.RESET} conversion)")
    print(f"  {C.WHITE}                  └─►  Clients:   {C.BOLD}{clients:>2}{C.RESET}  closed  ({C.BLUE}{p2c:.1f}%{C.RESET} conversion)")

    print()


def render_footer():
    """Render the motivational footer."""
    print(f"  {C.GRAY}{'─' * 58}{C.RESET}")
    print()
    print(f"  {C.GOLD}{C.BOLD}  \"You are one offer away.\"{C.RESET}  {C.GRAY}— Alex Hormozi{C.RESET}")
    print()
    print(f"  {C.GRAY}Data: Google Sheets + Stripe API | Run anytime: python scripts/progress_dashboard.py{C.RESET}")
    print()


def render_data_warnings(sheets_data: Dict, stripe_data: Dict):
    """Show warnings about data availability."""
    warnings = []
    if "error" in sheets_data:
        warnings.append(f"Sheets: {sheets_data['error']}")
    if "error" in stripe_data:
        warnings.append(f"Stripe: {stripe_data['error']}")

    if warnings:
        print(f"  {C.YELLOW}{C.BOLD}WARNINGS:{C.RESET}")
        for w in warnings:
            print(f"  {C.YELLOW}  - {w}{C.RESET}")
        print()


# ─── Output Modes ─────────────────────────────────────────────────────────────

def render_quick_summary(metrics: Dict, stripe_data: Dict, time_ctx: Dict, health_score: float):
    """One-line summary for quick checks."""
    mrr = stripe_data.get("mrr", 0) or metrics.get("mrr", 0)
    w = time_ctx["week_number"]
    dr = time_ctx["days_remaining"]
    clients = int(metrics["clients_total"])
    outreach = int(metrics["outreach_total"])
    color = color_status(health_score)

    print(f"{color}[{health_score:.0f}/100]{C.RESET} Week {w}/12 | {dr}d left | {clients}/3 clients | ${mrr:,.0f}/${TARGETS_90DAY['monthly_revenue']['target']:,} MRR | {outreach} outreach msgs")


def output_json(metrics: Dict, stripe_data: Dict, time_ctx: Dict, health_score: float, scores: Dict):
    """JSON output for automation/n8n consumption."""
    output = {
        "timestamp": datetime.now().isoformat(),
        "week_number": time_ctx["week_number"],
        "days_remaining": time_ctx["days_remaining"],
        "pct_time_elapsed": time_ctx["pct_time_elapsed"],
        "health_score": health_score,
        "component_scores": {k: {"score": v["score"], "weight": v["weight"]} for k, v in scores.items()},
        "metrics": {
            "clients_total": metrics["clients_total"],
            "outreach_total": metrics["outreach_total"],
            "meetings_total": metrics["meetings_total"],
            "mrr": stripe_data.get("mrr", 0) or metrics.get("mrr", 0),
            "setup_revenue": metrics["setup_revenue"],
            "videos_total": metrics["videos_total"],
            "youtube_subs": metrics["youtube_subs"],
            "training_avg": metrics["training_avg"],
        },
        "targets_90day": TARGETS_90DAY,
    }
    print(json.dumps(output, indent=2))


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Marceau Execution System — Progress Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/progress_dashboard.py          Full dashboard
  python scripts/progress_dashboard.py --quick   One-line summary
  python scripts/progress_dashboard.py --json    JSON for automation
  python scripts/progress_dashboard.py --offline Skip API calls, show template
        """,
    )
    parser.add_argument("--quick", action="store_true", help="One-line summary")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--offline", action="store_true", help="Skip API calls, use defaults")
    args = parser.parse_args()

    # Time context (always available)
    time_ctx = get_time_context()

    # Fetch data
    if args.offline:
        sheets_data = {"error": "Offline mode — using defaults"}
        stripe_data = {"mrr": 0, "active_subscriptions": 0, "month_revenue": 0, "error": "Offline mode"}
    else:
        sheets_data = fetch_scorecard_data()
        stripe_data = fetch_stripe_mrr()

    # Parse metrics
    metrics = parse_scorecard(sheets_data)

    # Calculate health score
    health_score, component_scores = calculate_health_score(metrics, stripe_data, time_ctx)

    # Render based on mode
    if args.quick:
        render_quick_summary(metrics, stripe_data, time_ctx, health_score)
        return

    if args.json:
        output_json(metrics, stripe_data, time_ctx, health_score, component_scores)
        return

    # Full dashboard
    render_header(time_ctx)
    render_data_warnings(sheets_data, stripe_data)
    render_90day_goals(metrics, stripe_data)
    render_revenue_tracker(metrics, stripe_data)
    render_pipeline_summary(metrics)
    render_weekly_metrics(metrics, time_ctx)
    render_content_tracker(metrics)
    render_health_score(health_score, component_scores)
    render_footer()


if __name__ == "__main__":
    main()
