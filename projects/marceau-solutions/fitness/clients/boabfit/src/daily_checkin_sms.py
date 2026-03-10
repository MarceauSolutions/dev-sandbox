#!/usr/bin/env python3
"""
BoabFit 6-Week Program — Daily Check-in SMS

SOP COMPLIANCE:
  - SOP 18: TCPA sender ID, opt-out language, quiet hours via TwilioSMS
  - SOP 18: Small batch first (--send-batch N), inbox monitor after sends
  - SOP 33: Pre-flight verified (Twilio balance, inventory check)
  - Service Standards: Uses execution/twilio_sms.py shared utility

Sends each client their daily workout breakdown with:
  - Day title (e.g., "FULL BODY - SCULPT + TONE")
  - Each exercise with a short form description
  - A girly hype blurb to get them excited
  - Sender ID: "— Julia from BOABFIT" (TCPA required)

Usage:
  python projects/boabfit/src/daily_checkin_sms.py --dry-run              # Preview today's message
  python projects/boabfit/src/daily_checkin_sms.py --test                  # Send to William only
  python projects/boabfit/src/daily_checkin_sms.py --send-batch 5          # Small batch (SOP 18)
  python projects/boabfit/src/daily_checkin_sms.py --send                  # Send to all clients
  python projects/boabfit/src/daily_checkin_sms.py --send --day tuesday    # Override day
  python projects/boabfit/src/daily_checkin_sms.py --preview-week          # Preview all 7 days
"""

import os
import sys
import json
import subprocess
import time as time_mod
import argparse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

# Import shared Twilio utility (SOP: reuse execution/ scripts)
sys.path.insert(0, str(ROOT / "execution"))
from twilio_sms import TwilioSMS

# Paths
PLAN_PATH = Path(__file__).parent / "workout_plan.json"
ROSTER_PATH = ROOT / "projects" / "boabfit" / "clients" / "roster.json"
LOG_DIR = ROOT / "projects" / "boabfit" / "clients"

# Phone numbers
WILLIAM_PHONE = "+12393985676"
JULIA_PHONE = "+12393985197"

# TCPA-compliant sender ID — appended to every message
SENDER_ID = "\n\n— JULZ - BOABFIT🫧🍑"


def load_plan():
    """Load the 6-week workout plan."""
    with open(PLAN_PATH) as f:
        return json.load(f)


def load_roster():
    """Load client roster."""
    with open(ROSTER_PATH) as f:
        return json.load(f)


def get_today_day(override=None):
    """Get today's day of the week (lowercase)."""
    if override:
        return override.lower()
    return datetime.now().strftime("%A").lower()


def get_nutrition_tip(plan):
    """Get a rotating nutrition/water tip based on the day of the year."""
    tips = plan.get("nutrition_tips", [])
    if not tips:
        return ""
    day_of_year = datetime.now().timetuple().tm_yday
    return tips[day_of_year % len(tips)]


def build_workout_message(plan, day):
    """
    Build the daily check-in SMS for a workout day (full form tips).

    Returns (message_text, error_string_or_None).
    """
    schedule = plan["weekly_schedule"]
    hype_blurbs = plan["hype_blurbs"]

    workout_key = schedule.get(day)
    if not workout_key:
        return None, f"No schedule entry for {day}"

    hype = hype_blurbs.get(day, "")
    nutrition_tip = get_nutrition_tip(plan)

    # Rest day — just send the hype blurb + nutrition tip
    if workout_key == "rest":
        lines = [
            f"Hey girl! {hype}",
        ]
        if nutrition_tip:
            lines.append("")
            lines.append(f"💧 {nutrition_tip}")
        lines.append(SENDER_ID)
        lines.append("")
        lines.append("Reply STOP to opt out.")
        return "\n".join(lines), None

    # Workout day — build the full breakdown
    workout = plan["workouts"].get(workout_key)
    if not workout:
        return None, f"Workout not found: {workout_key}"

    lines = [
        f"Hey girl!! Today is {workout['title']} day!!",
        f"{workout['duration']} | Dumbbells & Booty Band",
        "",
        hype,
        "",
        "Here's your workout breakdown:",
        "",
    ]

    for loop in workout["loops"]:
        lines.append(f"{loop['name'].upper()}:")
        for ex in loop["exercises"]:
            lines.append(f"  {ex['name']}")
            lines.append(f"  >> {ex['form_tip']}")
            lines.append("")

    lines.append(f"FOCUS: {workout['focus_cue']}")
    lines.append("")
    lines.append("You've got this babe!! GO CRUSH IT!!")
    if nutrition_tip:
        lines.append("")
        lines.append(f"💧 {nutrition_tip}")
    lines.append(SENDER_ID)
    lines.append("")
    lines.append("Reply STOP to opt out.")

    return "\n".join(lines), None


def build_short_workout_message(plan, day):
    """
    Build a shorter version — first sentence of each form tip only.
    Recommended for daily sends (fewer SMS segments = lower cost + better engagement).
    """
    schedule = plan["weekly_schedule"]
    hype_blurbs = plan["hype_blurbs"]

    workout_key = schedule.get(day)
    if not workout_key or workout_key == "rest":
        return build_workout_message(plan, day)

    workout = plan["workouts"].get(workout_key)
    hype = hype_blurbs.get(day, "")

    lines = [
        f"Hey girl!! Today is {workout['title']} day!!",
        f"{workout['duration']} | Dumbbells & Booty Band",
        "",
        hype,
        "",
    ]

    for loop in workout["loops"]:
        lines.append(f"{loop['name'].upper()}:")
        for ex in loop["exercises"]:
            tip = ex["form_tip"]
            first_sentence = tip.split(". ")[0] + "." if ". " in tip else tip
            lines.append(f"  {ex['name']} — {first_sentence}")
        lines.append("")

    lines.append("You've got this babe!! GO CRUSH IT!!")
    nutrition_tip = get_nutrition_tip(plan)
    if nutrition_tip:
        lines.append("")
        lines.append(f"💧 {nutrition_tip}")
    lines.append(SENDER_ID)
    lines.append("")
    lines.append("Reply STOP to opt out.")

    return "\n".join(lines), None


def run_inbox_monitor():
    """SOP 18: Complete the loop — run inbox monitor after sending."""
    print(f"\n--- INBOX MONITOR (SOP 18: complete the loop) ---")
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "execution" / "twilio_inbox_monitor.py"), "check"],
            capture_output=True, text=True, timeout=30, cwd=str(ROOT)
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"  Monitor stderr: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        print("  Inbox monitor timed out (30s) — will catch replies on next run.")
    except Exception as e:
        print(f"  Inbox monitor error: {e}")


def main():
    parser = argparse.ArgumentParser(description="BoabFit Daily Check-in SMS")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true', help='Preview today\'s message')
    group.add_argument('--test', action='store_true', help='Send test to William only')
    group.add_argument('--send', action='store_true', help='Send to all clients')
    group.add_argument('--send-batch', type=int, metavar='N',
                       help='Send to first N clients only (SOP 18 small batch test)')
    group.add_argument('--preview-week', action='store_true', help='Preview all 7 days')
    parser.add_argument('--day', help='Override day of week (e.g., monday, tuesday)')
    parser.add_argument('--short', action='store_true', help='Use shorter message format')
    args = parser.parse_args()

    plan = load_plan()
    roster = load_roster()
    day = get_today_day(args.day)

    # Initialize shared Twilio utility
    sms_client = TwilioSMS()

    print(f"\n{'='*60}")
    print(f"BOABFIT DAILY CHECK-IN SMS")
    print(f"{'='*60}")
    print(f"Day: {day.capitalize()}")
    print(f"Clients: {len(roster)}")
    print(f"From: {sms_client.from_number}")
    print(f"Time: {datetime.now().strftime('%I:%M %p ET')}")

    # Preview all 7 days
    if args.preview_week:
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for d in days:
            build_fn = build_short_workout_message if args.short else build_workout_message
            msg, err = build_fn(plan, d)
            print(f"\n{'='*60}")
            print(f"  {d.upper()}")
            print(f"{'='*60}")
            if err:
                print(f"  ERROR: {err}")
            else:
                print(f"  Length: {len(msg)} chars ({len(msg)//160 + 1} SMS segments)")
                print(f"\n{msg}")
        return

    # Build today's message
    build_fn = build_short_workout_message if args.short else build_workout_message
    message, err = build_fn(plan, day)

    if err:
        print(f"\nERROR: {err}")
        sys.exit(1)

    print(f"Message length: {len(message)} chars ({len(message)//160 + 1} SMS segments)")

    if args.dry_run:
        print(f"\n--- DRY RUN ---\n")
        print(message)
        print(f"\n--- RECIPIENTS ---")
        for i, c in enumerate(roster, 1):
            phone = sms_client._format_phone(c['phone'])
            status = "VALID" if phone else "INVALID"
            print(f"  {i:2d}. {c['name']:<25s} {(phone or c['phone']):<16s} [{status}]")
        valid = sum(1 for c in roster if sms_client._format_phone(c['phone']))
        segments = len(message) // 160 + 1
        print(f"\nWould send to {valid} clients. Est cost: ${valid * 0.0079 * segments:.2f}")
        return

    if args.test:
        print(f"\n--- TEST MODE: Sending to William ({WILLIAM_PHONE}) ---\n")
        print(f"MESSAGE:\n{message}\n")
        result = sms_client.send_message(to=WILLIAM_PHONE, message=message)
        if result.get('success'):
            print(f"  Sent! SID: {result['message_sid']} Status: {result['status']}")
        else:
            print(f"  Failed: {result.get('error')}")
        # SOP 18: complete the loop
        run_inbox_monitor()
        return

    # Determine recipient list
    send_roster = roster
    batch_mode = False
    if args.send_batch:
        send_roster = roster[:args.send_batch]
        batch_mode = True
        print(f"\n--- SMALL BATCH MODE: Sending to first {args.send_batch} of {len(roster)} clients (SOP 18) ---\n")
    else:
        print(f"\n--- SENDING TO ALL {len(roster)} CLIENTS ---\n")

    sent_names = []
    failed_entries = []

    for i, c in enumerate(send_roster, 1):
        phone = sms_client._format_phone(c['phone'])
        if not phone:
            print(f"  [{i:2d}/{len(send_roster)}] SKIP {c['name']} — invalid number")
            failed_entries.append({"name": c['name'], "error": "invalid number"})
            continue

        print(f"  [{i:2d}/{len(send_roster)}] {c['name']} ({phone})...", end=" ")
        result = sms_client.send_message(to=phone, message=message)

        if result.get('success'):
            print(f"sent")
            sent_names.append(c['name'])
        else:
            print(f"FAILED: {result.get('error')}")
            failed_entries.append({"name": c['name'], "error": result.get('error', 'unknown')})

        if i < len(send_roster):
            time_mod.sleep(1)

    # Send Julia a summary
    now = datetime.now().strftime('%I:%M %p')
    batch_note = f" (BATCH TEST: first {args.send_batch})" if batch_mode else ""
    summary = (
        f"Hey Julia! Your BOABFIT {day.capitalize()} check-in was sent at {now} ET{batch_note}.\n\n"
        f"Successfully sent to {len(sent_names)} clients.\n"
    )
    if failed_entries:
        summary += f"Failed: {len(failed_entries)} — "
        summary += ", ".join(e['name'] for e in failed_entries)
        summary += "\n"
    summary += f"\nTotal: {len(sent_names)}/{len(send_roster)} delivered."
    summary += "\n\n— William (automated)"

    print(f"\n--- NOTIFYING JULIA ---")
    result = sms_client.send_message(to=JULIA_PHONE, message=summary)
    if result.get('success'):
        print(f"  Julia notified! SID: {result['message_sid']}")
    else:
        print(f"  Failed to notify Julia: {result.get('error')}")

    # Save log
    batch_suffix = f"_batch{args.send_batch}" if batch_mode else ""
    log_path = LOG_DIR / f"checkin_log_{day}_{datetime.now().strftime('%Y%m%d')}{batch_suffix}.json"
    with open(log_path, 'w') as f:
        json.dump({
            "campaign": f"boabfit-6week-checkin-{day}",
            "day": day,
            "sent_at": datetime.now().isoformat(),
            "batch_mode": batch_mode,
            "batch_size": args.send_batch if batch_mode else len(roster),
            "message_length": len(message),
            "segments": len(message) // 160 + 1,
            "sent_to": sent_names,
            "failed": failed_entries,
            "julia_notified": result.get('success', False)
        }, f, indent=2)

    print(f"\n{'='*60}")
    print(f"COMPLETE: {len(sent_names)}/{len(send_roster)} sent")
    print(f"Log: {log_path}")
    if batch_mode:
        print(f"\nSOP 18: This was a batch test. Wait 24 hours and check:")
        print(f"  - Delivery rate (target >95%)")
        print(f"  - Opt-out rate (target <2%)")
        print(f"  - Reply rate (target 2-5%)")
        print(f"  Then run: python {__file__} --send --short --day {day}")
    print(f"{'='*60}")

    # SOP 18: Complete the loop — run inbox monitor
    run_inbox_monitor()


if __name__ == "__main__":
    main()
