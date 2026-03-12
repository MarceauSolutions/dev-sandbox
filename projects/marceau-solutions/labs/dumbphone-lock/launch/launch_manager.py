#!/usr/bin/env python3
"""
DumbPhone Lock — Automated Launch Manager

Pipeline stages (run in order):
  1. preflight   Verify all systems are live before posting
  2. validate    Start 48h organic validation window + content schedule
  3. gate        Evaluate organic results — blocks paid ads until data justifies it
  4. status      Current signups, UTM breakdown, phase-aware verdict
  5. watch       Live monitor — SMS alerts at milestones
  6. feedback    Surface SMS drip replies as qualitative market signal
  7. report      Generate branded PDF launch report
  8. iterate     Generate new copy variants based on what's converting

Usage:
    python launch/launch_manager.py preflight
    python launch/launch_manager.py validate
    python launch/launch_manager.py gate
    python launch/launch_manager.py status
    python launch/launch_manager.py watch
    python launch/launch_manager.py feedback
    python launch/launch_manager.py report
    python launch/launch_manager.py iterate
"""

import os
import sys
import json
import time
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

# ─── Paths ───────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
ROOT = PROJECT_DIR.parents[3]  # dev-sandbox root

load_dotenv(ROOT / ".env")

# ─── Config ──────────────────────────────────────────────────────────────────

N8N_BASE_URL = os.getenv("N8N_BASE_URL", "https://n8n.marceausolutions.com")
N8N_API_KEY = os.getenv("N8N_API_KEY", "")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM = os.getenv("TWILIO_PHONE_NUMBER", "")
WILLIAM_PHONE = "+12393985676"

SHEETS_ID = "13bEJ2eEdgRN3vM-wAOv1CrEp-7AtlKnAQTCnutP535E"
WAITLIST_TAB = "DumbPhone Waitlist"

LANDING_PAGE_URL = "https://marceausolutions.com/dumbphone"

N8N_WORKFLOWS = {
    "Waitlist Capture": "A9TdMLSIjUBXYXiI",
    "Email Confirm": "ilNn24FqfZcYGxcT",
    "SMS Drip": "4GKRU7i0JOh01yVT",
}

# Go/No-Go thresholds (from KICKOFF.md)
VALIDATION_HOURS = 48
GO_THRESHOLD = 100
PIVOT_THRESHOLD = 50
MILESTONES = [25, 50, 100, 150, 200, 500]

AD_KILL_CPC = 1.00
AD_KILL_CTR = 0.5
AD_KILL_CPL = 5.00

# Phases
PHASES = ["preflight", "organic_validation", "gate_passed", "paid_ads", "scaling", "killed"]

# State file — persists phase, timestamps, decisions across runs
STATE_FILE = SCRIPT_DIR / "launch_state.json"

# Organic content posting schedule (platform, timing offset in hours, description)
POSTING_SCHEDULE = [
    {"order": 1,  "platform": "Reddit r/nosurf",          "offset_h": 0,    "key": "reddit_nosurf"},
    {"order": 2,  "platform": "Twitter/X thread",          "offset_h": 0.5,  "key": "twitter"},
    {"order": 3,  "platform": "Reddit r/productivity",     "offset_h": 1,    "key": "reddit_productivity"},
    {"order": 4,  "platform": "Instagram Reel",            "offset_h": 1.5,  "key": "instagram"},
    {"order": 5,  "platform": "Reddit r/digitalminimalism","offset_h": 2,    "key": "reddit_dm"},
    {"order": 6,  "platform": "TikTok",                    "offset_h": 2.5,  "key": "tiktok"},
    {"order": 7,  "platform": "Reddit r/dumbphones",       "offset_h": 3,    "key": "reddit_dumbphones"},
    {"order": 8,  "platform": "Hacker News Show HN",       "offset_h": 4,    "key": "hackernews"},
    {"order": 9,  "platform": "Reddit r/getdisciplined",   "offset_h": 6,    "key": "reddit_getdisciplined"},
    {"order": 10, "platform": "Reddit comments (hunt)",    "offset_h": 0,    "key": "reddit_comments"},
]

# ─── Terminal colors ──────────────────────────────────────────────────────────

BOLD = "\033[1m"
DIM = "\033[2m"
GOLD = "\033[38;2;201;150;60m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RESET = "\033[0m"

# ─── State Management ────────────────────────────────────────────────────────

def load_state():
    """Load persistent launch state from disk."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "phase": "preflight",
        "validation_started": None,
        "validation_ended": None,
        "posts_completed": {},
        "milestones_hit": [],
        "gate_decision": None,
        "gate_decided_at": None,
        "gate_signups": None,
        "notes": [],
    }


def save_state(state):
    """Persist launch state to disk."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_validation_elapsed(state):
    """Return hours elapsed since validation started, or None."""
    if not state.get("validation_started"):
        return None
    started = datetime.fromisoformat(state["validation_started"])
    return (datetime.now() - started).total_seconds() / 3600


def get_validation_remaining(state):
    """Return hours remaining in validation window, or None."""
    elapsed = get_validation_elapsed(state)
    if elapsed is None:
        return None
    return max(0, VALIDATION_HOURS - elapsed)


# ─── Google Sheets ────────────────────────────────────────────────────────────

def get_sheets_service():
    """Get authenticated Google Sheets service."""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        token_path = ROOT / "token.json"
        if not token_path.exists():
            print(f"  {RED}No token.json found. Run: python execution/google_auth_setup.py{RESET}")
            return None

        creds = Credentials.from_authorized_user_file(
            str(token_path),
            ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        return build("sheets", "v4", credentials=creds)
    except Exception as e:
        print(f"  {RED}Sheets auth error: {e}{RESET}")
        return None


def get_waitlist_data():
    """Pull all waitlist rows from Google Sheets."""
    svc = get_sheets_service()
    if not svc:
        return None

    try:
        result = (
            svc.spreadsheets()
            .values()
            .get(spreadsheetId=SHEETS_ID, range=f"{WAITLIST_TAB}!A:H")
            .execute()
        )
        rows = result.get("values", [])
        if len(rows) < 2:
            return []

        headers = [h.strip().lower().replace(" ", "_") for h in rows[0]]
        data = []
        for row in rows[1:]:
            padded = row + [""] * (len(headers) - len(row))
            data.append(dict(zip(headers, padded)))
        return data
    except Exception as e:
        print(f"  {RED}Sheets read error: {e}{RESET}")
        return None


def get_utm_breakdown(data):
    """Summarize signups by UTM source."""
    sources = {}
    for row in data:
        source = row.get("source") or row.get("utm_source") or "organic"
        sources[source] = sources.get(source, 0) + 1
    return dict(sorted(sources.items(), key=lambda x: x[1], reverse=True))

# ─── n8n Checks ──────────────────────────────────────────────────────────────

def check_n8n_workflow(workflow_id):
    """Check if an n8n workflow is active and recently executed."""
    headers = {"X-N8N-API-KEY": N8N_API_KEY}
    try:
        r = requests.get(
            f"{N8N_BASE_URL}/api/v1/workflows/{workflow_id}",
            headers=headers, timeout=10
        )
        if r.status_code != 200:
            return {"active": False, "error": f"HTTP {r.status_code}"}

        wf = r.json()
        active = wf.get("active", False)

        # Get last execution
        ex_r = requests.get(
            f"{N8N_BASE_URL}/api/v1/executions",
            headers=headers,
            params={"workflowId": workflow_id, "limit": 1},
            timeout=10
        )
        last_run = None
        last_status = None
        if ex_r.status_code == 200:
            execs = ex_r.json().get("data", [])
            if execs:
                last_run = execs[0].get("startedAt", "")
                last_status = execs[0].get("status", "")

        return {
            "name": wf.get("name", ""),
            "active": active,
            "last_run": last_run,
            "last_status": last_status,
        }
    except Exception as e:
        return {"active": False, "error": str(e)}


def check_landing_page():
    """Verify landing page returns 200."""
    try:
        r = requests.get(LANDING_PAGE_URL, timeout=10)
        return r.status_code == 200, r.status_code
    except Exception as e:
        return False, str(e)

# ─── SMS Alert ────────────────────────────────────────────────────────────────

def send_sms_alert(message):
    """Send SMS to William via Twilio."""
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        print(f"  {DIM}SMS alert skipped — Twilio not configured{RESET}")
        return

    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=message,
            from_=TWILIO_FROM,
            to=WILLIAM_PHONE
        )
        print(f"  {GREEN}SMS sent: {msg.sid}{RESET}")
    except Exception as e:
        print(f"  {RED}SMS failed: {e}{RESET}")

# ─── Go/No-Go Engine ─────────────────────────────────────────────────────────

def get_verdict(count, hours_elapsed=None):
    """Return GO / PIVOT / NO-GO verdict."""
    if count >= GO_THRESHOLD:
        return "GO", GREEN, "100+ signups — BUY $99 Apple Dev account. Scale paid ads."
    elif count >= PIVOT_THRESHOLD:
        return "PIVOT", YELLOW, "50-99 signups — Iterate copy/positioning. Don't invest yet."
    else:
        if hours_elapsed and hours_elapsed >= 48:
            return "NO-GO", RED, "Under 50 signups after 48hrs — Rethink product or audience."
        remaining = PIVOT_THRESHOLD - count
        return "BUILDING", CYAN, f"{remaining} more signups needed to reach PIVOT threshold."

# ─── Commands ────────────────────────────────────────────────────────────────

def _print_copy_teaser(key, interactive=False):
    """Print a one-line copy snippet for a ready platform."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "content_pipeline", SCRIPT_DIR / "content_pipeline.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        title, body, _ = mod.get_platform_copy(key)
        platform = mod.PLATFORMS.get(key, {})
        autonomy = platform.get("autonomy", 1)

        autonomy_labels = {3: "auto-post", 2: "browser-assist", 1: "manual copy"}
        hint = autonomy_labels.get(autonomy, "")

        if title:
            teaser = title[:70]
        elif body:
            teaser = body.split("\n")[0][:70]
        else:
            return

        label = f"  {DIM}({hint}){RESET}" if hint else ""
        if interactive:
            action_hint = f"  {DIM}→ menu option 7 to post{RESET}"
        else:
            action_hint = f"  {DIM}→ launch_manager.py content {key}{RESET}"
        print(f"         {DIM}\"{teaser}\"{RESET}{label}")
        print(f"         {action_hint}")
    except Exception:
        pass  # Never break validate output due to pipeline import issues


def cmd_validate(args):
    """Start or resume the 48h organic validation window."""
    state = load_state()

    print(f"\n{GOLD}{BOLD}  DumbPhone Lock — Organic Validation Stage{RESET}\n")

    # If already gate-passed or further, warn
    if state["phase"] in ("gate_passed", "paid_ads", "scaling"):
        print(f"  {YELLOW}Validation already completed. Phase: {state['phase']}{RESET}")
        print(f"  Gate decision: {state.get('gate_decision')} at {state.get('gate_decided_at', '')[:16]}\n")
        return

    # Start the clock if not already running
    if not state["validation_started"]:
        state["validation_started"] = datetime.now().isoformat()
        state["phase"] = "organic_validation"
        save_state(state)
        print(f"  {GREEN}{BOLD}Validation window STARTED{RESET}")
        print(f"  Clock: {datetime.now().strftime('%Y-%m-%d %H:%M')} → ends {(datetime.now() + timedelta(hours=VALIDATION_HOURS)).strftime('%Y-%m-%d %H:%M')}")
    else:
        elapsed = get_validation_elapsed(state)
        remaining = get_validation_remaining(state)
        started_str = state["validation_started"][:16].replace("T", " ")
        print(f"  {CYAN}Validation in progress{RESET} — started {started_str}")
        print(f"  {elapsed:.1f}h elapsed / {remaining:.1f}h remaining")

    # Content posting schedule
    elapsed_h = get_validation_elapsed(state) or 0
    started_dt = datetime.fromisoformat(state["validation_started"]) if state["validation_started"] else datetime.now()
    posts_done = state.get("posts_completed", {})

    interactive = getattr(args, "interactive", False)

    print(f"\n  {BOLD}Content Posting Schedule{RESET}")
    if not interactive:
        print(f"  {DIM}Mark complete: validate --mark <key>{RESET}\n")
    else:
        print(f"  {DIM}After each post, go back to the menu → option 4 (Mark a post as done){RESET}\n")

    for post in POSTING_SCHEDULE:
        key = post["key"]
        done = key in posts_done
        post_time = started_dt + timedelta(hours=post["offset_h"])
        ready = datetime.now() >= post_time
        time_str = post_time.strftime("%H:%M")

        if done:
            done_at = posts_done[key][:16].replace("T", " ")
            icon = f"{GREEN}✓{RESET}"
            note = f"{DIM}done {done_at}{RESET}"
            print(f"    {icon}  {post['order']:>2}. {post['platform']:<32} {note}")
        elif ready:
            icon = f"{GOLD}→{RESET}"
            note = f"{YELLOW}READY TO POST{RESET}"
            print(f"    {icon}  {post['order']:>2}. {post['platform']:<32} {note}")
            # Show the first line of copy as a teaser
            _print_copy_teaser(key, interactive)
        else:
            wait_min = int((post_time - datetime.now()).total_seconds() / 60)
            icon = f"{DIM}○{RESET}"
            note = f"{DIM}in {wait_min}m ({time_str}){RESET}"
            print(f"    {icon}  {post['order']:>2}. {post['platform']:<32} {note}")

    total_posts = len(POSTING_SCHEDULE)
    done_count = len(posts_done)
    print(f"\n  {DIM}{done_count}/{total_posts} posts completed{RESET}")

    # Current signup pulse
    data = get_waitlist_data() or []
    total = len(data)
    verdict, color, advice = get_verdict(total, elapsed_h)
    print(f"\n  {BOLD}Current Pulse{RESET}")
    bar_filled = min(int(total / GO_THRESHOLD * 30), 30)
    bar = "█" * bar_filled + "░" * (30 - bar_filled)
    print(f"  {GOLD}{bar}{RESET}  {BOLD}{total}{RESET} / {GO_THRESHOLD}   {color}{verdict}{RESET}")

    remaining = get_validation_remaining(state)
    if remaining is not None and remaining <= 0:
        if interactive:
            print(f"\n  {GOLD}{BOLD}48h window closed.{RESET} Go back to the menu and choose option 1 to run the Validation Gate.\n")
        else:
            print(f"\n  {GOLD}{BOLD}48h window closed.{RESET} Run `gate` to evaluate and get your GO/NO-GO decision.\n")
    else:
        hrs_left = remaining or VALIDATION_HOURS
        if interactive:
            print(f"\n  {DIM}After posting, come back and use option 4 to mark each post done.")
            print(f"  Use option 2 (Status) anytime to see live signup counts.")
            print(f"  After {hrs_left:.0f}h, the menu will recommend running the Validation Gate.{RESET}\n")
        else:
            print(f"\n  {DIM}Run `watch` in a separate terminal for live alerts.")
            print(f"  Run `validate --mark <key>` after each post.")
            print(f"  Run `gate` after {hrs_left:.0f}h to evaluate results.{RESET}\n")

    # Handle --mark flag
    if hasattr(args, "mark") and args.mark:
        key = args.mark
        matching = [p for p in POSTING_SCHEDULE if p["key"] == key]
        if not matching:
            valid_keys = ", ".join(p["key"] for p in POSTING_SCHEDULE)
            print(f"  {RED}Unknown key '{key}'. Valid keys: {valid_keys}{RESET}\n")
            return
        if key in posts_done:
            print(f"  {DIM}Already marked: {matching[0]['platform']}{RESET}\n")
            return
        state["posts_completed"][key] = datetime.now().isoformat()
        save_state(state)
        print(f"  {GREEN}✓ Marked: {matching[0]['platform']}{RESET}\n")


def cmd_gate(args):
    """Evaluate organic validation results. Gates paid ads — must pass before spending money."""
    state = load_state()

    print(f"\n{GOLD}{BOLD}  DumbPhone Lock — Validation Gate{RESET}\n")

    if state["phase"] == "preflight":
        print(f"  {RED}Validation hasn't started. Run `validate` first.{RESET}\n")
        return

    if state["phase"] in ("gate_passed", "paid_ads", "scaling"):
        print(f"  {GREEN}Gate already passed. Phase: {state['phase']}{RESET}")
        print(f"  Decision: {state.get('gate_decision')} ({state.get('gate_decided_at', '')[:16]})\n")
        return

    elapsed_h = get_validation_elapsed(state) or 0
    remaining_h = get_validation_remaining(state) or 0
    window_closed = remaining_h <= 0

    # Pull live data
    data = get_waitlist_data() or []
    total = len(data)
    utm = get_utm_breakdown(data)

    # UTM conversion rate — which source is performing
    posts_done = state.get("posts_completed", {})
    posts_attempted = len(posts_done)

    # Calculate signup velocity (signups per hour)
    dates = []
    for row in data:
        d = row.get("date") or row.get("timestamp") or ""
        if d:
            try:
                dates.append(datetime.fromisoformat(d.replace("Z", "+00:00")))
            except Exception:
                pass
    velocity = (total / elapsed_h) if elapsed_h > 0 else 0
    projected_48h = int(velocity * VALIDATION_HOURS) if elapsed_h > 0 else 0

    # Qualitative signal: count of SMS drip replies (logged in n8n)
    sms_replies = _count_sms_replies()

    print(f"  {BOLD}Validation Summary{RESET}")
    print(f"  {'─' * 50}")
    print(f"  Elapsed:          {elapsed_h:.1f}h / {VALIDATION_HOURS}h")
    print(f"  Posts completed:  {posts_attempted} / {len(POSTING_SCHEDULE)}")
    print(f"  Total signups:    {BOLD}{total}{RESET}")
    print(f"  Signup velocity:  {velocity:.1f}/hr  →  {projected_48h} projected at 48h")
    print(f"  SMS drip replies: {sms_replies} {'(strong signal!)' if sms_replies > 0 else '(none yet)'}")

    print(f"\n  {BOLD}By Source{RESET}")
    for source, count in utm.items():
        pct = int(count / total * 100) if total else 0
        print(f"    {source:<22} {count:>3}  ({pct}%)")

    # Warning if window isn't closed yet
    if not window_closed:
        print(f"\n  {YELLOW}⚠  {remaining_h:.1f}h remaining in validation window.{RESET}")
        if not (hasattr(args, "force") and args.force):
            print(f"  Use --force to gate early, or wait until the 48h window closes.\n")
            return

    # ── Gate Decision ──
    print(f"\n  {BOLD}Gate Decision{RESET}")
    print(f"  {'─' * 50}")

    # Score the result
    decision = None
    reasons = []
    next_actions = []

    if total >= GO_THRESHOLD:
        decision = "GO"
        reasons.append(f"✓ {total} signups — hit the 100-signup GO threshold")
        if velocity >= 2:
            reasons.append(f"✓ Strong velocity: {velocity:.1f} signups/hr")
        if sms_replies > 0:
            reasons.append(f"✓ {sms_replies} SMS drip replies — engaged audience")
        next_actions = [
            "BUY $99 Apple Developer account",
            "Activate paid ads: Meta ($50) + TikTok ($25) + Reddit ($25)",
            "Start TestFlight beta with waitlist",
            "Run `watch` to monitor paid conversion rate",
        ]
    elif total >= PIVOT_THRESHOLD:
        decision = "PIVOT"
        reasons.append(f"△ {total} signups — above PIVOT floor but below GO")
        if projected_48h >= GO_THRESHOLD:
            reasons.append(f"△ Projected {projected_48h} at 48h — may still hit GO threshold")
        else:
            reasons.append(f"✗ Projected {projected_48h} at 48h — below GO threshold")
        if posts_attempted < len(POSTING_SCHEDULE) // 2:
            reasons.append(f"✗ Only {posts_attempted}/{len(POSTING_SCHEDULE)} posts completed — more reach needed")
        next_actions = [
            "Run `iterate` for new copy variants — test pain/identity hook",
            "Complete remaining posts: " + ", ".join(
                p["platform"] for p in POSTING_SCHEDULE if p["key"] not in posts_done
            )[:60],
            "DO NOT spend money on paid ads yet",
            "Extend organic window 24h, re-run gate",
        ]
    else:
        if elapsed_h >= VALIDATION_HOURS:
            decision = "NO-GO"
            reasons.append(f"✗ Only {total} signups after {elapsed_h:.0f}h — below PIVOT threshold")
            if posts_attempted < len(POSTING_SCHEDULE) // 2:
                reasons.append(f"△ But only {posts_attempted}/{len(POSTING_SCHEDULE)} posts done — consider finishing distribution first")
            if sms_replies == 0:
                reasons.append("✗ Zero SMS drip replies — no engagement signal")
            next_actions = [
                "Rethink positioning — try a different target audience",
                "Run `iterate` for fundamentally different angle",
                "Consider pivoting: white-label to parents vs. adults?",
                "DO NOT buy Apple Dev account or spend on ads",
            ]
        else:
            decision = "BUILDING"
            reasons.append(f"△ {total} signups with {remaining_h:.0f}h remaining")
            reasons.append(f"△ Projected {projected_48h} at 48h")
            next_actions = [
                "Continue posting remaining channels",
                "Run `watch` for milestone alerts",
                f"Re-run gate in {remaining_h:.0f}h when window closes",
            ]

    color = {
        "GO": GREEN, "PIVOT": YELLOW, "NO-GO": RED, "BUILDING": CYAN
    }.get(decision, RESET)

    print(f"\n  {color}{BOLD}  {decision}  {RESET}\n")
    for r in reasons:
        print(f"    {r}")

    print(f"\n  {BOLD}Next Actions{RESET}")
    for action in next_actions:
        print(f"    → {action}")

    # Persist decision (only for final verdicts)
    if decision in ("GO", "PIVOT", "NO-GO"):
        state["gate_decision"] = decision
        state["gate_decided_at"] = datetime.now().isoformat()
        state["gate_signups"] = total
        if decision == "GO":
            state["phase"] = "gate_passed"
        elif decision == "NO-GO":
            state["phase"] = "killed"
        state["notes"].append(f"{datetime.now().strftime('%Y-%m-%d %H:%M')} Gate: {decision} ({total} signups)")
        save_state(state)
        print(f"\n  {DIM}Decision saved to launch_state.json{RESET}")

        if decision == "GO":
            send_sms_alert(
                f"DumbPhone Lock GATE PASSED: {total} signups. GO decision. "
                f"Buy $99 Apple Dev account now. Start paid ads ($100 budget)."
            )

    print()


def cmd_feedback(args):
    """Surface SMS drip replies as qualitative market signal."""
    print(f"\n{GOLD}{BOLD}  DumbPhone Lock — Feedback / Market Signal{RESET}\n")

    replies = _get_sms_reply_details()

    if not replies:
        print(f"  {DIM}No SMS drip replies yet.{RESET}")
        print(f"  Replies start coming in Day 3-7 of the drip sequence.")
        print(f"  When people text back with feature requests = real demand signal.\n")
    else:
        print(f"  {GREEN}{BOLD}{len(replies)} replies received{RESET} — strong engagement signal\n")
        for i, reply in enumerate(replies, 1):
            print(f"  {GOLD}{i}.{RESET} {reply.get('from', 'unknown')}  {DIM}{reply.get('date', '')[:10]}{RESET}")
            print(f"     \"{reply.get('body', '')}\"")
            print()

    # Also show n8n drip execution stats
    print(f"  {BOLD}SMS Drip Pipeline Stats{RESET}")
    wf_result = check_n8n_workflow(N8N_WORKFLOWS["SMS Drip"])
    if wf_result.get("error"):
        print(f"    {RED}✗ Drip workflow error: {wf_result['error']}{RESET}")
    else:
        status_color = GREEN if wf_result.get("active") else RED
        print(f"    Workflow:  {status_color}{'active' if wf_result.get('active') else 'inactive'}{RESET}")
        if wf_result.get("last_run"):
            print(f"    Last run:  {wf_result['last_run'][:19]}")
            print(f"    Status:    {wf_result.get('last_status', 'unknown')}")

    print(f"\n  {DIM}Feature requests in replies = product-market fit signal.")
    print(f"  Objections in replies = copy/positioning issues to fix.{RESET}\n")


def _count_sms_replies():
    """Count inbound SMS replies via Twilio (best-effort)."""
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return 0
    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        # Inbound messages to our number in last 7 days
        since = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
        messages = client.messages.list(to=TWILIO_FROM, date_sent_after=since, limit=50)
        return len(messages)
    except Exception:
        return 0


def _get_sms_reply_details():
    """Get full inbound SMS reply details via Twilio."""
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return []
    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        since = (datetime.utcnow() - timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%SZ")
        messages = client.messages.list(to=TWILIO_FROM, date_sent_after=since, limit=50)
        return [
            {
                "from": m.from_,
                "body": m.body,
                "date": str(m.date_sent),
            }
            for m in messages
        ]
    except Exception:
        return []


# ─── Commands ────────────────────────────────────────────────────────────────

def cmd_preflight(args):
    """Verify all systems before going live."""
    print(f"\n{GOLD}{BOLD}  DumbPhone Lock — Pre-Launch Checklist{RESET}\n")

    all_pass = True

    # 1. Landing page
    print(f"  {BOLD}Landing Page{RESET}")
    ok, code = check_landing_page()
    if ok:
        print(f"    {GREEN}✓{RESET} {LANDING_PAGE_URL} ({code})")
    else:
        print(f"    {RED}✗{RESET} {LANDING_PAGE_URL} — {code}")
        all_pass = False

    # 2. n8n workflows
    print(f"\n  {BOLD}n8n Workflows{RESET}")
    for name, wf_id in N8N_WORKFLOWS.items():
        result = check_n8n_workflow(wf_id)
        if result.get("error"):
            print(f"    {RED}✗{RESET} {name} — {result['error']}")
            all_pass = False
        elif result.get("active"):
            last = result.get("last_run", "never")[:19] if result.get("last_run") else "never"
            status_icon = GREEN if result.get("last_status") != "error" else YELLOW
            print(f"    {GREEN}✓{RESET} {name} (active) — last run: {status_icon}{last}{RESET}")
        else:
            print(f"    {RED}✗{RESET} {name} — INACTIVE")
            all_pass = False

    # 3. Google Sheets
    print(f"\n  {BOLD}Google Sheets — Waitlist Tab{RESET}")
    data = get_waitlist_data()
    if data is None:
        print(f"    {RED}✗{RESET} Could not read sheet")
        all_pass = False
    else:
        print(f"    {GREEN}✓{RESET} Sheet accessible — {len(data)} rows")

    # 4. Summary
    print(f"\n  {GOLD}{'─' * 44}{RESET}")
    if all_pass:
        print(f"  {GREEN}{BOLD}All systems GO.{RESET} You're clear to post.\n")
    else:
        print(f"  {RED}{BOLD}Fix issues above before posting.{RESET}\n")

    return all_pass


def cmd_status(args):
    """Show current phase, signup count, UTM breakdown, and go/no-go verdict."""
    state = load_state()

    print(f"\n{GOLD}{BOLD}  DumbPhone Lock — Launch Status{RESET}")
    print(f"  {DIM}{datetime.now().strftime('%Y-%m-%d %H:%M')}{RESET}\n")

    # Phase banner
    phase = state.get("phase", "preflight")
    phase_labels = {
        "preflight":          (DIM,    "PRE-LAUNCH     — run `preflight` then `validate`"),
        "organic_validation": (CYAN,   "ORGANIC VALIDATION — 48h window running"),
        "gate_passed":        (GREEN,  "GATE PASSED    — proceed to paid ads"),
        "paid_ads":           (YELLOW, "PAID ADS       — $100 budget running"),
        "scaling":            (GOLD,   "SCALING        — validated, growing"),
        "killed":             (RED,    "NO-GO          — pivot or restart"),
    }
    p_color, p_label = phase_labels.get(phase, (DIM, phase))
    print(f"  {BOLD}Phase:{RESET}  {p_color}{p_label}{RESET}")

    # Validation window progress
    elapsed_h = get_validation_elapsed(state)
    remaining_h = get_validation_remaining(state)
    if elapsed_h is not None:
        pct = min(int(elapsed_h / VALIDATION_HOURS * 20), 20)
        time_bar = "█" * pct + "░" * (20 - pct)
        print(f"  {BOLD}Window:{RESET} {GOLD}{time_bar}{RESET}  {elapsed_h:.1f}h / {VALIDATION_HOURS}h", end="")
        if remaining_h and remaining_h > 0:
            print(f"  {DIM}({remaining_h:.1f}h left){RESET}")
        else:
            print(f"  {YELLOW} — CLOSED → run `gate`{RESET}")

    print()

    # Signup data
    data = get_waitlist_data()
    if data is None:
        print(f"  {RED}Could not read waitlist data.{RESET}\n")
        return

    total = len(data)
    utm = get_utm_breakdown(data)

    # Velocity
    dates = []
    for row in data:
        d = row.get("date") or row.get("timestamp") or ""
        if d:
            try:
                dates.append(datetime.fromisoformat(d.replace("Z", "+00:00")))
            except Exception:
                pass
    velocity = 0.0
    if dates and elapsed_h and elapsed_h > 0:
        velocity = total / elapsed_h

    verdict, color, advice = get_verdict(total, elapsed_h)

    # Signup bar
    bar_filled = min(int(total / GO_THRESHOLD * 40), 40)
    bar = "█" * bar_filled + "░" * (40 - bar_filled)

    print(f"  {BOLD}Signups{RESET}")
    print(f"  {GOLD}{bar}{RESET}  {BOLD}{total}{RESET} / {GO_THRESHOLD}")
    if velocity > 0:
        projected = int(velocity * VALIDATION_HOURS)
        print(f"  {DIM}{velocity:.1f}/hr velocity  →  {projected} projected at 48h{RESET}")

    # UTM breakdown
    if utm:
        print(f"\n  {BOLD}By Source{RESET}")
        for source, count in utm.items():
            pct = int(count / total * 100) if total else 0
            src_bar = "█" * int(pct / 5)
            print(f"    {source:<20} {count:>4}  {DIM}{src_bar}{RESET}")

    # Posts completed
    posts_done = len(state.get("posts_completed", {}))
    total_posts = len(POSTING_SCHEDULE)
    print(f"\n  {BOLD}Posts{RESET}  {posts_done}/{total_posts} completed", end="")
    if posts_done < total_posts:
        print(f"  {DIM}(run `validate` for schedule){RESET}")
    else:
        print()

    # Verdict
    print(f"\n  {BOLD}Verdict{RESET}")
    print(f"  {color}{BOLD}{verdict}{RESET}  —  {advice}")

    # Next milestone
    next_ms = next((m for m in MILESTONES if m > total), None)
    if next_ms:
        print(f"\n  {DIM}Next milestone: {next_ms} signups ({next_ms - total} to go){RESET}")

    # Gate decision if made
    if state.get("gate_decision"):
        gd_color = {"GO": GREEN, "PIVOT": YELLOW, "NO-GO": RED}.get(state["gate_decision"], RESET)
        print(f"\n  {BOLD}Gate:{RESET} {gd_color}{state['gate_decision']}{RESET}  {DIM}({state.get('gate_decided_at', '')[:16]}  {state.get('gate_signups', 0)} signups){RESET}")

    print()


def cmd_watch(args):
    """Continuously monitor — alert at milestones."""
    interval = getattr(args, "interval", 300)  # default 5 min

    print(f"\n{GOLD}{BOLD}  DumbPhone Lock — Live Monitor{RESET}")
    print(f"  {DIM}Checking every {interval // 60}m. Ctrl+C to stop.{RESET}\n")

    last_count = None
    alerted_milestones = set()

    try:
        while True:
            data = get_waitlist_data()
            if data is None:
                print(f"  {RED}[{datetime.now().strftime('%H:%M')}] Sheets error{RESET}")
                time.sleep(interval)
                continue

            count = len(data)
            verdict, color, advice = get_verdict(count)
            ts = datetime.now().strftime("%H:%M")

            if last_count is None or count != last_count:
                delta = f" (+{count - last_count})" if last_count is not None else ""
                print(f"  [{ts}] {BOLD}{count} signups{RESET}{GREEN}{delta}{RESET}  {color}{verdict}{RESET}")
                last_count = count

                # Milestone alerts
                for ms in MILESTONES:
                    if count >= ms and ms not in alerted_milestones:
                        alerted_milestones.add(ms)
                        msg = f"DumbPhone Lock: {count} signups reached milestone {ms}! Verdict: {verdict}. {advice}"
                        print(f"\n  {GOLD}{BOLD}MILESTONE {ms} HIT!{RESET}")
                        send_sms_alert(msg)
                        print()
            else:
                print(f"  [{ts}] {DIM}{count} signups (no change){RESET}", end="\r")

            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n\n  {DIM}Monitor stopped.{RESET}\n")


def cmd_report(args):
    """Generate a branded PDF launch report."""
    print(f"\n{GOLD}{BOLD}  Generating Launch Report...{RESET}\n")

    data = get_waitlist_data() or []
    total = len(data)
    utm = get_utm_breakdown(data)

    verdict, _, advice = get_verdict(total)

    # Build workflow status
    wf_status = []
    for name, wf_id in N8N_WORKFLOWS.items():
        result = check_n8n_workflow(wf_id)
        wf_status.append({
            "name": name,
            "active": result.get("active", False),
            "last_run": result.get("last_run", ""),
            "last_status": result.get("last_status", ""),
        })

    # Build JSON for branded PDF engine
    landing_ok, landing_code = check_landing_page()

    report_content = f"""# DumbPhone Lock — Launch Report

**Generated:** {datetime.now().strftime("%B %d, %Y at %H:%M")}
**Verdict:** {verdict}
**Recommendation:** {advice}

---

## Waitlist Metrics

| Metric | Value |
|--------|-------|
| Total Signups | **{total}** |
| GO Threshold | 100 signups |
| Current Status | {verdict} |

## Traffic by Source

| Source | Signups | % of Total |
|--------|---------|------------|
{"".join(f"| {src} | {cnt} | {int(cnt/total*100) if total else 0}% |\n" for src, cnt in utm.items()) if utm else "| No data yet | — | — |\n"}

## Systems Status

| System | Status |
|--------|--------|
| Landing Page ({LANDING_PAGE_URL}) | {"✓ Live" if landing_ok else "✗ Down"} |
{"".join(f'| n8n: {wf["name"]} | {"✓ Active" if wf["active"] else "✗ Inactive"} |\n' for wf in wf_status)}

## Go / No-Go Framework

| Result | Signups | Action |
|--------|---------|--------|
| **GO** | 100+ | Buy $99 Apple Developer account. Scale paid ads. |
| **PIVOT** | 50–99 | Iterate copy and positioning. Hold dev investment. |
| **NO-GO** | Under 50 after 48h | Rethink product or audience. |

**Current position: {total} signups → {verdict}**

{advice}

## Ad Performance Kill Criteria

| Metric | Kill If | Status |
|--------|---------|--------|
| CPC | > $1.00 | Monitor in ad dashboards |
| CTR | < 0.5% | Monitor in ad dashboards |
| Cost per Lead | > $5.00 | Monitor in ad dashboards |

## Next Actions

{"- **BUY $99 Apple Developer account immediately**" if verdict == "GO" else ""}
{"- **Scale paid ads** — Meta, TikTok, Reddit ($100 budget)" if verdict == "GO" else ""}
{"- **Iterate copy** — run `launch_manager.py iterate` for new variants" if verdict == "PIVOT" else ""}
{"- Review UTM data to find top-performing channel" if total > 0 else "- Post organic content to Reddit, X, Instagram, TikTok"}
{"- Monitor SMS drip replies for feature requests" if total > 10 else ""}
- Run `launch_manager.py watch` for live milestone alerts
- Check back in 12 hours for updated metrics

---
*Marceau Solutions — Embrace the Pain & Defy the Odds*
"""

    import tempfile

    json_input = {
        "title": "DumbPhone Lock — Launch Report",
        "subtitle": f"Waitlist: {total} signups | Verdict: {verdict}",
        "content": report_content,
        "date": datetime.now().strftime("%B %d, %Y"),
    }

    input_file = Path("/tmp/dumbphone-launch-report.json")
    output_file = PROJECT_DIR / "launch" / f"launch-report-{datetime.now().strftime('%Y-%m-%d')}.pdf"

    with open(input_file, "w") as f:
        json.dump(json_input, f)

    branded_pdf = ROOT / "execution" / "branded_pdf_engine.py"
    result = subprocess.run(
        [
            sys.executable, str(branded_pdf),
            "--template", "generic_document",
            "--input", str(input_file),
            "--output", str(output_file),
        ],
        capture_output=True, text=True
    )

    if result.returncode == 0 and output_file.exists():
        print(f"  {GREEN}Report generated:{RESET} {output_file}")
        subprocess.run(["open", str(output_file)])
    else:
        print(f"  {RED}PDF generation failed:{RESET}")
        print(result.stderr)
        # Fallback: print to terminal
        print(f"\n{report_content}")


def cmd_iterate(args):
    """Generate new copy variants based on current performance."""
    print(f"\n{GOLD}{BOLD}  Copy Iteration Engine{RESET}\n")

    data = get_waitlist_data() or []
    total = len(data)
    utm = get_utm_breakdown(data)

    if not utm:
        top_source = "organic"
    else:
        top_source = list(utm.keys())[0]

    print(f"  {DIM}Total signups: {total} | Top source: {top_source}{RESET}\n")
    print(f"  {BOLD}New Copy Variants to Test{RESET}\n")

    variants = [
        {
            "hook": "Pain Hook (identity)",
            "platform": "Reddit / X",
            "copy": (
                "I have 147 apps on my phone. I use 6 of them.\n\n"
                "The other 141 are just slots in a casino I carry in my pocket.\n\n"
                "Built an iOS app that locks you into only the 6 you actually need.\n"
                "Same tech Apple uses for parental controls — you literally can't bypass it.\n\n"
                f"Waitlist: {LANDING_PAGE_URL}"
            ),
        },
        {
            "hook": "Stat Hook (social proof)",
            "platform": "Reddit / TikTok caption",
            "copy": (
                "Americans check their phones 96 times per day.\n"
                "That's every 10 minutes.\n"
                "Every. Single. Day.\n\n"
                "Screen Time limits fail because one tap dismisses them.\n"
                "I built DumbPhone Lock — uses Apple's FamilyControls API (parental controls).\n"
                "No bypass. No dismiss. Just focus.\n\n"
                f"{LANDING_PAGE_URL}"
            ),
        },
        {
            "hook": "Competitor comparison",
            "platform": "Reddit r/nosurf",
            "copy": (
                "Opal: $79.99/yr. One Sec: $4.99/mo. Light Phone: $299 + new plan.\n\n"
                "Or: DumbPhone Lock — uses your existing iPhone and costs less.\n"
                "Same FamilyControls API they all claim to use but don't fully implement.\n"
                "You set it. You can't undo it without a time delay.\n\n"
                f"Early access: {LANDING_PAGE_URL}"
            ),
        },
        {
            "hook": "Vulnerability / story",
            "platform": "Instagram / TikTok",
            "copy": (
                "I deleted Instagram 4 times last year.\n"
                "I reinstalled it 4 times last year.\n\n"
                "That's when I realized the problem isn't willpower — it's friction.\n"
                "So I built the friction into the phone itself.\n\n"
                "DumbPhone Lock — waitlist link in bio."
            ),
        },
        {
            "hook": "HN / technical",
            "platform": "Hacker News Show HN",
            "copy": (
                "Show HN: DumbPhone Lock — FamilyControls API to turn iPhone into a dumb phone\n\n"
                "I got tired of app blockers that send a notification you dismiss in one tap.\n"
                "FamilyControls is the same API Apple uses for Screen Time parental controls — "
                "it runs at the system level and cannot be bypassed by the blocked app.\n\n"
                "The launcher shows only your approved apps. Everything else is invisible.\n"
                "No notifications from blocked apps. No mental bandwidth wasted.\n\n"
                f"Still in market validation phase: {LANDING_PAGE_URL}\n"
                "Would love HN's honest feedback on the concept."
            ),
        },
    ]

    for i, v in enumerate(variants):
        print(f"  {GOLD}{BOLD}Variant {i + 1}: {v['hook']}{RESET}")
        print(f"  {DIM}Platform: {v['platform']}{RESET}\n")
        for line in v["copy"].split("\n"):
            print(f"    {line}")
        print(f"\n  {DIM}{'─' * 50}{RESET}\n")

    print(f"  {DIM}Tip: A/B test 2 variants at a time. Post 30 min apart.")
    print(f"  Run `status` after 24h to see which source is converting best.{RESET}\n")


# ─── Content Pipeline Commands ───────────────────────────────────────────────

def _get_pipeline():
    """Import content_pipeline from the launch/ directory."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "content_pipeline",
        SCRIPT_DIR / "content_pipeline.py"
    )
    mod = importlib.util.load_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cmd_content(args):
    """Generate image + post content for a platform (or next ready platform)."""
    pipeline = _get_pipeline()

    key = getattr(args, "key", None)
    if not key:
        ready = pipeline.list_ready()
        if not ready:
            print(f"\n  {YELLOW}No platforms ready to post yet. Check the posting schedule with `validate`.{RESET}\n")
            return
        key = ready[0]
        print(f"\n  {DIM}Auto-selected next ready platform: {pipeline.PLATFORMS[key]['label']}{RESET}")

    skip_image = getattr(args, "no_image", False)
    pipeline.run_post(key, skip_image=skip_image)


def cmd_generate(args):
    """Pre-generate images for all platforms."""
    pipeline = _get_pipeline()
    force = getattr(args, "force", False)
    pipeline.run_generate_all(force=force)


def cmd_show(args):
    """Print ready-to-paste copy for a platform."""
    pipeline = _get_pipeline()
    pipeline.show_copy(args.key)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="DumbPhone Lock — Automated Launch Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("preflight", help="Verify all systems are live before posting")

    validate_p = sub.add_parser("validate", help="Start/resume 48h organic validation window")
    validate_p.add_argument("--mark", type=str, default=None, metavar="KEY",
                            help="Mark a post as completed (e.g. --mark reddit_nosurf)")
    validate_p.add_argument("--interactive", action="store_true",
                            help="Called from interactive launcher — show menu-friendly guidance")

    gate_p = sub.add_parser("gate", help="Evaluate organic results — gates paid ad spend")
    gate_p.add_argument("--force", action="store_true", help="Evaluate before 48h window closes")

    sub.add_parser("status", help="Current phase, signups, UTM breakdown, verdict")
    sub.add_parser("feedback", help="Surface SMS drip replies as market signal")

    watch_p = sub.add_parser("watch", help="Live monitor with milestone SMS alerts")
    watch_p.add_argument("--interval", type=int, default=300, help="Check interval in seconds (default: 300)")

    sub.add_parser("report", help="Generate branded PDF launch report")
    sub.add_parser("iterate", help="Generate new copy variants to A/B test")

    content_p = sub.add_parser("content", help="Generate image + post content for a platform")
    content_p.add_argument("key", nargs="?", default=None, help="Platform key (omit to post next ready platform)")
    content_p.add_argument("--no-image", action="store_true", help="Skip image generation")

    gen_p = sub.add_parser("generate", help="Pre-generate images for all platforms")
    gen_p.add_argument("--force", action="store_true", help="Re-generate existing images")

    show_p = sub.add_parser("show", help="Print ready-to-paste copy for a platform")
    show_p.add_argument("key", help="Platform key (e.g. twitter, reddit_nosurf)")

    args = parser.parse_args()

    if args.command == "preflight":
        cmd_preflight(args)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "gate":
        cmd_gate(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "feedback":
        cmd_feedback(args)
    elif args.command == "watch":
        cmd_watch(args)
    elif args.command == "report":
        cmd_report(args)
    elif args.command == "iterate":
        cmd_iterate(args)
    elif args.command == "content":
        cmd_content(args)
    elif args.command == "generate":
        cmd_generate(args)
    elif args.command == "show":
        cmd_show(args)
    else:
        print(f"\n{GOLD}{BOLD}  DumbPhone Lock — Launch Manager{RESET}\n")
        print(f"  {BOLD}Pipeline (run in order):{RESET}")
        print(f"    {GOLD}1.{RESET} {CYAN}preflight{RESET}   Verify all systems are live")
        print(f"    {GOLD}2.{RESET} {CYAN}validate{RESET}    Start 48h organic validation window")
        print(f"    {GOLD}3.{RESET} {CYAN}watch{RESET}       Run in background — SMS at milestones")
        print(f"    {GOLD}4.{RESET} {CYAN}gate{RESET}        Evaluate results — gates paid ad spend")
        print(f"\n  {BOLD}Anytime:{RESET}")
        print(f"    {CYAN}status{RESET}      Phase, signups, UTM breakdown, verdict")
        print(f"    {CYAN}feedback{RESET}    SMS drip replies as market signal")
        print(f"    {CYAN}iterate{RESET}     New copy variants to A/B test")
        print(f"    {CYAN}report{RESET}      Branded PDF launch report")
        print(f"\n  {DIM}Run from dev-sandbox root:")
        print(f"  python projects/marceau-solutions/labs/dumbphone-lock/launch/launch_manager.py <command>{RESET}\n")


if __name__ == "__main__":
    main()
