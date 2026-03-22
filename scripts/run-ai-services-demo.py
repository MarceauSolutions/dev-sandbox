#!/usr/bin/env python3
"""
AI Services Demo — Live Sales Video Recording Tool

WHAT: Simulates a full AI automation chain with visual terminal output for Loom recordings
WHY: William needs compelling screen-recorded demos showing real-time automation
INPUT: --live flag to trigger real n8n webhooks instead of simulation
OUTPUT: Animated terminal output showing lead → CRM → email → SMS → booking pipeline

QUICK USAGE:
  python scripts/run-ai-services-demo.py          # Simulated (practice)
  python scripts/run-ai-services-demo.py --live    # Real webhooks fire

DEPENDENCIES: requests (for --live mode only)
"""

import sys
import time
import argparse
import json
from datetime import datetime, timedelta

# ── ANSI Colors ──────────────────────────────────────────────

RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
ITALIC  = "\033[3m"

# Foreground
WHITE   = "\033[97m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
CYAN    = "\033[96m"
RED     = "\033[91m"
BLUE    = "\033[94m"
MAGENTA = "\033[95m"
GRAY    = "\033[90m"
GOLD    = "\033[38;5;178m"

# Background
BG_BLACK  = "\033[40m"
BG_GREEN  = "\033[42m"
BG_BLUE   = "\033[44m"
BG_GOLD   = "\033[48;5;178m"
BG_RED    = "\033[41m"
BG_CYAN   = "\033[46m"


def clear_screen():
    print("\033[2J\033[H", end="")


def type_print(text, delay=0.03, end="\n"):
    """Print text character by character for a 'live' feel."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(end)
    sys.stdout.flush()


def fast_print(text, delay=0.01, end="\n"):
    """Faster typing for less important lines."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(end)
    sys.stdout.flush()


def instant_print(text):
    """Instant print with flush."""
    print(text, flush=True)


def progress_bar(label, duration=2.0, width=30):
    """Animated progress bar."""
    sys.stdout.write(f"  {GRAY}{label} {RESET}")
    sys.stdout.flush()
    for i in range(width + 1):
        filled = "█" * i
        empty = "░" * (width - i)
        pct = int(i / width * 100)
        sys.stdout.write(f"\r  {GRAY}{label} {CYAN}[{filled}{empty}]{RESET} {WHITE}{pct}%{RESET}")
        sys.stdout.flush()
        time.sleep(duration / width)
    sys.stdout.write("\n")
    sys.stdout.flush()


def spinner(label, duration=2.0):
    """Animated spinner."""
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    end_time = time.time() + duration
    i = 0
    while time.time() < end_time:
        sys.stdout.write(f"\r  {CYAN}{frames[i % len(frames)]}{RESET} {label}")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    sys.stdout.write(f"\r  {GREEN}✓{RESET} {label}\n")
    sys.stdout.flush()


def print_box(lines, color=GOLD, width=60):
    """Print a styled box with content."""
    top    = f"  {color}╔{'═' * (width - 2)}╗{RESET}"
    bottom = f"  {color}╚{'═' * (width - 2)}╝{RESET}"
    instant_print(top)
    for line in lines:
        # Pad line (accounting for ANSI codes by using visible length)
        visible = line
        for code in [RESET, BOLD, DIM, WHITE, GREEN, YELLOW, CYAN, RED, BLUE, MAGENTA, GRAY, GOLD,
                     BG_BLACK, BG_GREEN, BG_BLUE, BG_GOLD, BG_RED, BG_CYAN, ITALIC]:
            visible = visible.replace(code, "")
        pad = width - 4 - len(visible)
        if pad < 0:
            pad = 0
        instant_print(f"  {color}║{RESET} {line}{' ' * pad} {color}║{RESET}")
    instant_print(bottom)


def divider():
    instant_print(f"\n  {DIM}{'─' * 58}{RESET}\n")


# ── Live Mode Helpers ────────────────────────────────────────

def fire_webhook(url, payload):
    """POST to a real n8n webhook."""
    try:
        import requests
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code
    except ImportError:
        instant_print(f"  {RED}ERROR: 'requests' not installed. Run: pip install requests{RESET}")
        return None
    except Exception as e:
        instant_print(f"  {RED}ERROR: Webhook failed — {e}{RESET}")
        return None


# ── Demo Steps ───────────────────────────────────────────────

def step_banner(live_mode):
    """Step 1: Opening banner."""
    clear_screen()
    instant_print("")
    instant_print("")

    banner_lines = [
        "",
        f"{BOLD}{WHITE}  NAPLES AC PROS{RESET}",
        f"{DIM}  AI-Powered Business Automation{RESET}",
        "",
        f"{GOLD}  ❄  HVAC Lead Capture → CRM → Follow-Up → Booking{RESET}",
        f"{GOLD}  ❄  100% Automated  •  Zero Manual Work{RESET}",
        "",
    ]

    mode_label = f"{BG_RED}{WHITE}{BOLD} LIVE MODE — REAL WEBHOOKS {RESET}" if live_mode else f"{BG_BLUE}{WHITE}{BOLD} DEMO MODE — SIMULATED {RESET}"

    instant_print(f"  {GOLD}{'━' * 58}{RESET}")
    for line in banner_lines:
        instant_print(line)
    instant_print(f"    {mode_label}")
    instant_print("")
    instant_print(f"  {GOLD}{'━' * 58}{RESET}")
    instant_print("")

    time.sleep(3)


def step_lead_detected(live_mode):
    """Step 2: A new lead comes in."""
    divider()

    instant_print(f"  {BG_GOLD}{BOLD}{WHITE} 🔔 NEW LEAD DETECTED {RESET}")
    instant_print("")
    time.sleep(0.5)

    type_print(f"  {BOLD}{WHITE}Name:{RESET}     Mike Johnson")
    type_print(f"  {BOLD}{WHITE}Business:{RESET} Naples AC Pros")
    type_print(f"  {BOLD}{WHITE}Phone:{RESET}    (239) 555-0123")
    type_print(f"  {BOLD}{WHITE}Email:{RESET}    mike@naplesacpros.com")
    type_print(f"  {BOLD}{WHITE}Service:{RESET}  AC Repair + Maintenance Contract")
    type_print(f"  {BOLD}{WHITE}Source:{RESET}   Website Contact Form")

    instant_print("")
    time.sleep(1)

    if live_mode:
        instant_print(f"  {YELLOW}→ Firing webhook to n8n Inbound-Lead-Router...{RESET}")
        status = fire_webhook("https://n8n.marceausolutions.com/webhook/route-lead", {
            "name": "Mike Johnson (DEMO)",
            "email": "demo@naplesacpros.com",
            "phone": "(239) 555-0123",
            "service": "AC Repair",
            "source": "AI Services Demo",
            "business": "Naples AC Pros",
            "demo": True
        })
        if status and 200 <= status < 300:
            instant_print(f"  {GREEN}✅ Webhook fired successfully (HTTP {status}){RESET}")
        else:
            instant_print(f"  {RED}⚠  Webhook returned {status} — check n8n{RESET}")
        time.sleep(1)

    spinner("Logging to CRM pipeline...", duration=2.0)
    instant_print(f"  {GREEN}✅ Lead logged to pipeline{RESET}  →  {CYAN}Stage: New Lead{RESET}")

    if live_mode:
        instant_print(f"  {YELLOW}→ Firing visit-log webhook...{RESET}")
        fire_webhook("https://n8n.marceausolutions.com/webhook/log-visit", {
            "client": "Mike Johnson (DEMO)",
            "action": "Lead captured via AI demo",
            "source": "demo-script",
            "demo": True
        })
        time.sleep(0.5)

    time.sleep(2)


def step_follow_up(live_mode):
    """Step 3: Automated follow-up."""
    divider()

    instant_print(f"  {BOLD}{CYAN}📧 AUTOMATED FOLLOW-UP SEQUENCE{RESET}")
    instant_print("")
    time.sleep(0.5)

    # Email
    instant_print(f"  {YELLOW}→ Composing personalized follow-up email...{RESET}")
    progress_bar("Generating email", duration=2.0)
    instant_print("")
    print_box([
        f"{BOLD}To:{RESET} mike@naplesacpros.com",
        f"{BOLD}Subject:{RESET} Automating Naples AC Pros — Here's How",
        "",
        f"Hi Mike,",
        "",
        f"Thanks for reaching out about automating your",
        f"HVAC business. I help companies like yours capture",
        f"leads 24/7 and book appointments on autopilot.",
        "",
        f"Here's a quick case study from another HVAC company",
        f"that went from 5 to 23 leads/week...",
    ], color=CYAN)
    instant_print(f"  {GREEN}✅ Email sent{RESET}")

    time.sleep(2)

    # SMS
    instant_print("")
    instant_print(f"  {YELLOW}→ Sending SMS follow-up...{RESET}")
    spinner("Delivering SMS to (239) 555-0123...", duration=2.0)
    instant_print("")
    print_box([
        f"{BOLD}SMS to (239) 555-0123:{RESET}",
        "",
        f"Hi Mike! This is William from Marceau Solutions.",
        f"Got your inquiry about automating Naples AC Pros.",
        f"Would love to show you a quick 15-min demo.",
        f"Here's my calendar: calendly.com/wmarceau",
    ], color=GREEN)
    instant_print(f"  {GREEN}✅ SMS delivered{RESET}")

    time.sleep(2)


def step_nurture_sequence(live_mode):
    """Step 4: Lead nurture setup."""
    divider()

    instant_print(f"  {BOLD}{MAGENTA}⏰ AUTO-SCHEDULING NURTURE SEQUENCE{RESET}")
    instant_print("")
    time.sleep(0.5)

    now = datetime.now()

    sequences = [
        ("Day 1", "Value email — HVAC case study + ROI calculator", now + timedelta(days=1)),
        ("Day 3", "Personalized Loom video walkthrough", now + timedelta(days=3)),
        ("Day 5", "SMS check-in + testimonial from similar client", now + timedelta(days=5)),
        ("Day 7", "Availability check + special offer", now + timedelta(days=7)),
    ]

    for label, desc, dt in sequences:
        time.sleep(0.5)
        date_str = dt.strftime("%b %d, %I:%M %p")
        instant_print(f"  {GOLD}▸{RESET} {BOLD}{label}{RESET}  {desc}")
        fast_print(f"    {DIM}Scheduled: {date_str}{RESET}", delay=0.005)

    instant_print("")
    spinner("Activating nurture sequence...", duration=1.5)
    instant_print(f"  {GREEN}✅ 4-touch nurture sequence activated{RESET}")
    instant_print(f"  {DIM}  All automated — no manual follow-up needed{RESET}")

    time.sleep(2)


def step_booking(live_mode):
    """Step 5: Discovery call booked."""
    divider()

    instant_print("")
    instant_print(f"  {BG_GREEN}{BOLD}{WHITE} 🎉  DISCOVERY CALL BOOKED! {RESET}")
    instant_print("")
    time.sleep(1)

    now = datetime.now()
    call_date = now + timedelta(days=2)
    call_str = call_date.strftime("%A, %B %d at 2:00 PM")

    type_print(f"  {BOLD}{WHITE}Mike Johnson{RESET} just booked a discovery call")
    type_print(f"  {CYAN}📅 {call_str}{RESET}")

    instant_print("")
    time.sleep(0.5)

    actions = [
        ("Google Calendar updated", 0.8),
        ("Prep email sent to William with lead intel", 1.0),
        ("Pipeline updated: New Lead → Discovery", 0.8),
        ("Slack notification sent to team", 0.6),
    ]

    for action, dur in actions:
        spinner(action, duration=dur)

    instant_print("")
    instant_print(f"  {GREEN}✅ All systems updated automatically{RESET}")

    time.sleep(2)


def step_dashboard(live_mode):
    """Step 6: Weekly dashboard summary."""
    divider()

    instant_print(f"  {BOLD}{GOLD}📊 WEEKLY AUTOMATION DASHBOARD{RESET}")
    instant_print("")
    time.sleep(0.5)

    # Main stats box
    print_box([
        f"{BOLD}{WHITE}  THIS WEEK'S PERFORMANCE{RESET}",
        "",
        f"  {BOLD}23{RESET}  leads captured automatically",
        f"  {BOLD}15{RESET}  follow-up emails sent",
        f"  {BOLD}12{RESET}  SMS messages delivered",
        f"  {BOLD} 3{RESET}  discovery calls booked",
        "",
        f"  {BOLD}{GREEN}Response Rate:   34%{RESET}",
        f"  {BOLD}{GREEN}Booking Rate:    13%{RESET}",
        f"  {BOLD}{GOLD}Pipeline Value:  $12,500{RESET}",
        "",
        f"  {DIM}All automated. Zero manual work.{RESET}",
    ], color=GOLD, width=50)

    time.sleep(1)

    instant_print("")

    # Before/after comparison
    instant_print(f"  {BOLD}{WHITE}Before AI Automation:{RESET}")
    instant_print(f"    {RED}✗{RESET} 2-3 leads/week from word of mouth")
    instant_print(f"    {RED}✗{RESET} Hours spent on manual follow-up")
    instant_print(f"    {RED}✗{RESET} Missed calls = lost customers")
    instant_print("")
    instant_print(f"  {BOLD}{WHITE}After AI Automation:{RESET}")
    instant_print(f"    {GREEN}✓{RESET} 23 leads/week from multiple channels")
    instant_print(f"    {GREEN}✓{RESET} Instant follow-up, every single time")
    instant_print(f"    {GREEN}✓{RESET} Never miss a lead, even at 2 AM")

    time.sleep(3)


def step_cta(live_mode):
    """Step 7: Call to action."""
    divider()
    instant_print("")

    print_box([
        "",
        f"{BOLD}{WHITE}  Want this for YOUR business?{RESET}",
        "",
        f"  Book a free 15-minute discovery call:",
        "",
        f"  {BOLD}{CYAN}  calendly.com/wmarceau/ai-services-discovery-call{RESET}",
        "",
        f"  {DIM}William Marceau  •  Marceau Solutions{RESET}",
        f"  {DIM}Naples, FL  •  AI Business Automation{RESET}",
        "",
    ], color=GOLD, width=54)

    instant_print("")
    instant_print(f"  {DIM}Demo complete. Press Ctrl+C to exit.{RESET}")
    instant_print("")


# ── Main ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI Services Demo for Loom Sales Videos")
    parser.add_argument("--live", action="store_true",
                        help="Fire REAL n8n webhooks (triggers actual Telegram alerts)")
    args = parser.parse_args()

    if args.live:
        print(f"\n  {BG_RED}{WHITE}{BOLD} ⚠  LIVE MODE {RESET}")
        print(f"  {YELLOW}This will fire REAL webhooks and send REAL notifications.{RESET}")
        print(f"  {YELLOW}Press Enter to continue or Ctrl+C to abort...{RESET}")
        try:
            input()
        except KeyboardInterrupt:
            print("\n  Aborted.")
            sys.exit(0)

    try:
        step_banner(args.live)
        step_lead_detected(args.live)
        step_follow_up(args.live)
        step_nurture_sequence(args.live)
        step_booking(args.live)
        step_dashboard(args.live)
        step_cta(args.live)
    except KeyboardInterrupt:
        print(f"\n\n  {DIM}Demo stopped.{RESET}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
