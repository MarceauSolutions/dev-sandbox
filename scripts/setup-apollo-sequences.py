#!/usr/bin/env python3
"""
Apollo.io Email Sequence Creator

Creates email sequences in Apollo.io from the templates in docs/cold-email-sequences.md.
If the Sequences API isn't available on the current plan, outputs ready-to-paste
templates formatted for manual entry.

Sequences:
  A: General Local Business (3 emails, days 0/3/7)
  B: HVAC / Home Services (3 emails, days 0/3/7)
  C: Med Spa / Dental (3 emails, days 0/3/7)
  D: Restaurant / Hospitality (3 emails, days 0/3/7)

Usage:
    python scripts/setup-apollo-sequences.py
    python scripts/setup-apollo-sequences.py --dry-run   # Preview only, no API calls
"""

import requests
import json
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load .env from repo root
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
APOLLO_BASE_URL = "https://api.apollo.io/v1"

CALENDLY_LINK = "https://calendly.com/wmarceau/free-fitness-strategy-call"
SPOTS_REMAINING = "2"

# ─── Sequence Definitions ──────────────────────────────────────────────────────

SEQUENCES = [
    {
        "name": "Naples AI Outreach — A: General Local Business",
        "steps": [
            {
                "day": 0,
                "subject": "Quick question about {{company_name}}",
                "body": (
                    "Hi {{first_name}},\n\n"
                    "I noticed {{company_name}} doesn't have automated lead follow-up — which means "
                    "you're probably losing 30-50% of inbound leads to slow response time. Most Naples businesses are.\n\n"
                    "I build AI systems that capture, qualify, and follow up with every lead automatically — "
                    "24/7, no staff needed. One of my clients went from missing half their leads to booking "
                    "10+ qualified appointments per week within 30 days.\n\n"
                    "Worth a 15-minute call to see if it fits?\n\n"
                    "William Marceau\n"
                    "Marceau Solutions\n"
                    "(239) 398-5676"
                ),
            },
            {
                "day": 3,
                "subject": "Re: Quick question about {{company_name}}",
                "body": (
                    "{{first_name}},\n\n"
                    "I recorded a quick 2-min video showing exactly what an AI lead system would look like "
                    "for a {{industry}} business like yours: {{loom_link}}\n\n"
                    "No fluff — just the specific automations and what they'd save you in time and missed revenue.\n\n"
                    "Happy to walk through it live if it looks interesting.\n\n"
                    "William"
                ),
            },
            {
                "day": 7,
                "subject": "Last note on this",
                "body": (
                    "{{first_name}},\n\n"
                    f"I only take 5 automation clients per quarter (every system is built personally, not outsourced). "
                    f"I have {SPOTS_REMAINING} spots left for Q2.\n\n"
                    "If automating your lead follow-up and booking isn't a priority right now, no worries at all. "
                    f"But if it is — let's grab 15 minutes this week before the spots fill.\n\n"
                    f"Book here: {CALENDLY_LINK}\n\n"
                    "William"
                ),
            },
        ],
    },
    {
        "name": "Naples AI Outreach — B: HVAC / Home Services",
        "steps": [
            {
                "day": 0,
                "subject": "{{company_name}} — missed calls costing you jobs?",
                "body": (
                    "Hi {{first_name}},\n\n"
                    "Here's what I see with most HVAC companies in Southwest Florida: a customer calls about "
                    "a broken AC at 8pm, gets voicemail, and calls the next company on Google. That one missed "
                    "call is $3,000-$8,000 in lost revenue.\n\n"
                    "I build AI phone systems that answer every call, qualify the job, and book it on your "
                    "schedule — 24/7, including weekends and holidays. No answering service, no call center. "
                    "Just an AI that sounds natural and knows your business.\n\n"
                    "Worth a 15-minute call to see how it works?\n\n"
                    "William Marceau\n"
                    "Marceau Solutions | (239) 398-5676"
                ),
            },
            {
                "day": 3,
                "subject": "Re: {{company_name}} — missed calls costing you jobs?",
                "body": (
                    "{{first_name}},\n\n"
                    "Quick math: if you miss just 3 after-hours calls per week and each job averages $4,000 "
                    "— that's $48,000/month walking to your competitors.\n\n"
                    "An AI receptionist costs $750/month and captures every single one. The ROI isn't even close.\n\n"
                    f"I can show you exactly how it works in 15 minutes: {CALENDLY_LINK}\n\n"
                    "William"
                ),
            },
            {
                "day": 7,
                "subject": "One more thing for {{company_name}}",
                "body": (
                    "{{first_name}},\n\n"
                    "I build these systems personally (not outsourced) so I only take 5 clients per quarter. "
                    "If after-hours calls and slow follow-up aren't costing you money, ignore this completely.\n\n"
                    "But if they are — I guarantee 10 qualified leads in 30 days or I work free until it happens. "
                    "No risk on your end.\n\n"
                    f"{CALENDLY_LINK}\n\n"
                    "William"
                ),
            },
        ],
    },
    {
        "name": "Naples AI Outreach — C: Med Spa / Dental",
        "steps": [
            {
                "day": 0,
                "subject": "{{company_name}} — filling last-minute cancellations?",
                "body": (
                    "Hi {{first_name}},\n\n"
                    "The #1 revenue killer for med spas and dental practices isn't marketing — it's "
                    "cancellations and no-shows. Most practices lose 15-25% of booked revenue to them every month.\n\n"
                    "I build AI systems that automatically fill cancellations from your waitlist, send smart "
                    "reminders that actually reduce no-shows, and follow up with every inquiry within 60 seconds "
                    "— even at midnight.\n\n"
                    "One practice I work with cut their no-show rate by 40% in the first month.\n\n"
                    "Worth a quick call?\n\n"
                    "William Marceau\n"
                    "Marceau Solutions | (239) 398-5676"
                ),
            },
            {
                "day": 3,
                "subject": "Re: {{company_name}} — filling last-minute cancellations?",
                "body": (
                    "{{first_name}},\n\n"
                    "Here's exactly what the system does for an appointment-based business:\n\n"
                    "1. Patient inquires (web, phone, Instagram DM) — AI responds in under 60 seconds\n"
                    "2. Cancellation happens — AI texts the top 5 waitlist patients instantly\n"
                    "3. 24 hours before appointment — smart reminder goes out (not a generic text)\n"
                    "4. After visit — automated review request at the perfect moment\n\n"
                    "All of this runs without your front desk touching it. I recorded a 2-min demo: {{loom_link}}\n\n"
                    "William"
                ),
            },
            {
                "day": 7,
                "subject": "Final note — {{company_name}}",
                "body": (
                    "{{first_name}},\n\n"
                    f"I take 5 clients per quarter and have {SPOTS_REMAINING} spots left. Every system is built "
                    "personally, which is why it works and why capacity is limited.\n\n"
                    "If no-shows and slow follow-up aren't a problem for you — great, ignore this. But if they "
                    "are: 15 minutes and I'll show you exactly how much revenue you're leaving on the table.\n\n"
                    f"{CALENDLY_LINK}\n\n"
                    "William"
                ),
            },
        ],
    },
    {
        "name": "Naples AI Outreach — D: Restaurant / Hospitality",
        "steps": [
            {
                "day": 0,
                "subject": "{{company_name}} — your reviews on autopilot?",
                "body": (
                    "Hi {{first_name}},\n\n"
                    "Two things kill restaurants on Google: not enough reviews, and not responding to the "
                    "bad ones fast enough. Most Naples restaurants have half the reviews they should because "
                    "they never ask — and one angry 1-star sits unanswered for weeks.\n\n"
                    "I build AI systems that automatically request reviews after every visit, respond to "
                    "every Google/Yelp review within hours (positive and negative), and handle reservation "
                    "inquiries 24/7 — even when you're slammed on a Saturday night.\n\n"
                    "Worth 15 minutes to see how it works?\n\n"
                    "William Marceau\n"
                    "Marceau Solutions | (239) 398-5676"
                ),
            },
            {
                "day": 3,
                "subject": "Re: {{company_name}} — your reviews on autopilot?",
                "body": (
                    "{{first_name}},\n\n"
                    "Quick numbers: restaurants that actively collect reviews see 18% more foot traffic from Google. "
                    "And responding to negative reviews within 24 hours reduces their impact by 70%.\n\n"
                    "The system I build does both automatically — plus handles reservation questions via text, "
                    "Instagram DM, and your website so your host staff isn't tied to the phone.\n\n"
                    f"Happy to show you in 15 minutes: {CALENDLY_LINK}\n\n"
                    "William"
                ),
            },
            {
                "day": 7,
                "subject": "Last note for {{company_name}}",
                "body": (
                    "{{first_name}},\n\n"
                    "I work with 5 businesses per quarter — every system built personally, not a cookie-cutter "
                    f"template. I have {SPOTS_REMAINING} Q2 spots remaining.\n\n"
                    "If online reviews and reservation management are handled — great. But if not, I guarantee "
                    "measurable results in 30 days or I keep working for free until it delivers.\n\n"
                    f"{CALENDLY_LINK}\n\n"
                    "William"
                ),
            },
        ],
    },
]


def get_headers():
    return {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": APOLLO_API_KEY,
    }


def create_sequence_via_api(sequence):
    """
    Attempt to create a sequence via Apollo's Sequences/Emailer Campaigns API.
    Returns (success: bool, message: str).
    """
    url = f"{APOLLO_BASE_URL}/emailer_campaigns"

    # Build the sequence payload
    # Apollo's emailer_campaigns endpoint structure
    payload = {
        "api_key": APOLLO_API_KEY,
        "name": sequence["name"],
        "permissions": "team",
        "active": False,  # Create as draft, don't auto-send
        "emailer_steps": [],
    }

    for step in sequence["steps"]:
        payload["emailer_steps"].append({
            "wait_time": step["day"],  # days to wait
            "type": "auto_email",
            "priority": "normal",
            "emailer_template": {
                "subject": step["subject"],
                "body_html": step["body"].replace("\n", "<br>"),
                "body_text": step["body"],
            },
        })

    try:
        response = requests.post(url, headers=get_headers(), json=payload, timeout=30)

        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            campaign_id = data.get("emailer_campaign", {}).get("id", "unknown")
            return True, f"Created (ID: {campaign_id})"
        elif response.status_code == 403 or response.status_code == 401:
            return False, f"Plan restriction — {response.status_code}: Sequences API not available on current plan"
        elif response.status_code == 422:
            return False, f"Validation error: {response.text[:200]}"
        else:
            return False, f"HTTP {response.status_code}: {response.text[:200]}"

    except requests.exceptions.RequestException as e:
        return False, f"Request failed: {e}"


def print_sequence_templates():
    """Print all sequences as ready-to-paste templates for manual Apollo entry."""
    repo_root = Path(__file__).resolve().parent.parent
    output_path = repo_root / "docs" / "apollo-sequence-templates.txt"

    lines = []
    lines.append("=" * 70)
    lines.append("APOLLO.IO EMAIL SEQUENCE TEMPLATES")
    lines.append("Ready to paste into Apollo.io Sequences UI")
    lines.append(f"Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 70)

    for seq in SEQUENCES:
        lines.append(f"\n{'─' * 70}")
        lines.append(f"SEQUENCE: {seq['name']}")
        lines.append(f"{'─' * 70}")

        for i, step in enumerate(seq["steps"], 1):
            lines.append(f"\n  Step {i} — Day {step['day']}")
            lines.append(f"  Subject: {step['subject']}")
            lines.append(f"  {'.' * 50}")
            # Indent body
            for line in step["body"].split("\n"):
                lines.append(f"  {line}")
            lines.append("")

    output_text = "\n".join(lines)

    # Write to file
    with open(output_path, "w") as f:
        f.write(output_text)

    print(f"\nTemplates saved to: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Create Apollo.io email sequences")
    parser.add_argument("--dry-run", action="store_true", help="Preview templates without API calls")
    args = parser.parse_args()

    if not APOLLO_API_KEY:
        print("ERROR: APOLLO_API_KEY not found in .env")
        sys.exit(1)

    print("=" * 70)
    print("Apollo.io Email Sequence Setup")
    print(f"Sequences to create: {len(SEQUENCES)}")
    print("=" * 70)

    if args.dry_run:
        print("\n[DRY RUN] Skipping API calls, printing templates only.\n")
        print_sequence_templates()
        # Also print to stdout
        for seq in SEQUENCES:
            print(f"\n  {seq['name']}")
            for step in seq["steps"]:
                print(f"    Step Day {step['day']}: {step['subject']}")
        print("\nDone (dry run).")
        return

    # Attempt API creation
    api_available = True
    results = []

    for seq in SEQUENCES:
        print(f"\nCreating: {seq['name']}...")
        success, message = create_sequence_via_api(seq)
        results.append((seq["name"], success, message))
        print(f"  -> {message}")

        if not success and ("Plan restriction" in message or "403" in message or "401" in message):
            api_available = False
            print("\n  Sequences API not available on current Apollo plan.")
            print("  Switching to template export mode.\n")
            break

        import time
        time.sleep(1.5)

    # Summary
    print(f"\n{'=' * 70}")
    print("Results Summary")
    print(f"{'=' * 70}")

    created = sum(1 for _, s, _ in results if s)
    failed = sum(1 for _, s, _ in results if not s)

    for name, success, message in results:
        status = "OK" if success else "FAILED"
        print(f"  [{status}] {name}: {message}")

    if not api_available or failed > 0:
        print(f"\n  API creation {'unavailable' if not api_available else 'had failures'}.")
        print("  Exporting all sequences as ready-to-paste templates...")
        template_path = print_sequence_templates()
        print(f"\n  Templates file: {template_path}")
        print("  -> Open Apollo.io > Engage > Sequences > New Sequence")
        print("  -> Paste each step's subject + body from the templates file")
    else:
        print(f"\n  All {created} sequences created successfully in Apollo.io!")
        print("  -> Go to Apollo.io > Engage > Sequences to review and activate")

    print(f"\n{'=' * 70}")
    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
