#!/usr/bin/env python3
"""
build_onboarding_packet.py — Generate branded onboarding PDF for new coaching clients.

Usage:
    python execution/build_onboarding_packet.py --client "John Doe" --start-date 2026-03-10
    python execution/build_onboarding_packet.py --client "Jane Smith" --start-date 2026-03-10 --output /tmp/onboarding.pdf
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from branded_pdf_engine import BrandedPDFEngine


def build_onboarding_data(client_name: str, start_date: str, coach_name: str = "William Marceau") -> dict:
    """Build onboarding packet data with William's standard content."""
    return {
        "client_name": client_name,
        "start_date": start_date,
        "coach_name": coach_name,
        "welcome_message": (
            f"Welcome aboard, {client_name}! I'm genuinely excited to work with you. "
            "This packet covers everything you need to know to get started. "
            "My goal is to give you the most effective, science-backed program possible — "
            "tailored to YOUR body, YOUR schedule, and YOUR goals."
        ),
        "what_to_expect": [
            "A custom training program designed around your goals, experience, and equipment",
            "Personalized nutrition protocol with macro targets and meal timing",
            "Weekly Monday check-ins via SMS to track progress and adjust as needed",
            "Monthly progress reviews via Google Meet (15-20 min)",
            "Direct access to me via text for quick questions (Mon-Fri, 8am-7pm ET)",
            "Peptide education resources if applicable to your goals",
        ],
        "communication_guidelines": {
            "sms_texts": "Quick questions, weekly check-ins, reminders — response within 4 hours (Mon-Fri)",
            "email": "Program updates, detailed recaps, documents — response within 24 hours",
            "google_meet": "Kickoff call + monthly progress reviews",
            "google_drive": "Your program files, progress tracking sheets, and resources",
        },
        "weekly_schedule": {
            "Sunday PM": "New week's program uploaded to your Drive folder",
            "Monday 9am": "Automated check-in SMS — rate your week 1-10 + any notes",
            "Tuesday": "Follow-up on check-in if needed",
            "Wednesday": "Mid-week motivation + training tip",
            "Friday": "Weekly recap and next week preview",
            "Month End": "15-min Google Meet progress review (Calendly link provided)",
        },
        "app_setup_steps": [
            "Book your kickoff call: calendly.com/wmarceau/kickoff-call",
            "Complete your intake form (link in welcome email) — do this BEFORE the kickoff call",
            "Save my number: +1 (855) 239-9364 (this is where check-in texts come from)",
            "Check your Google Drive for a shared 'Coaching — [Your Name]' folder",
            "Sign and return the liability waiver (in your Drive folder or attached to welcome email)",
        ],
        "faq": [
            {
                "q": "What if I miss a check-in?",
                "a": "No stress — just reply when you can. Consistency matters more than perfection. I'll follow up Tuesday if I don't hear from you.",
            },
            {
                "q": "Can I adjust my program?",
                "a": "Absolutely. Your program evolves with you. If something isn't working, tell me and we'll adjust within 48 hours.",
            },
            {
                "q": "What about supplements/peptides?",
                "a": "I provide evidence-based education on peptides and supplements. Any protocol decisions are between you and your healthcare provider.",
            },
            {
                "q": "How do I cancel?",
                "a": "Cancel anytime through your Stripe billing portal. No contracts, no cancellation fees. I earn your loyalty every month.",
            },
        ],
        "important_links": {
            "kickoff_call": "calendly.com/wmarceau/kickoff-call",
            "intake_form": "docs.google.com/forms (link in welcome email)",
            "coaching_page": "marceausolutions.com/coaching",
            "billing_portal": "Stripe link in your welcome email",
            "coach_email": "wmarceau@marceausolutions.com",
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Generate branded onboarding PDF for coaching clients")
    parser.add_argument("--client", required=True, help="Client's full name")
    parser.add_argument("--start-date", required=True, help="Coaching start date (YYYY-MM-DD)")
    parser.add_argument("--coach", default="William Marceau", help="Coach name")
    parser.add_argument("--output", "-o", help="Output PDF path (default: ./onboarding_{client}.pdf)")
    args = parser.parse_args()

    # Build data
    data = build_onboarding_data(args.client, args.start_date, args.coach)

    # Generate PDF
    engine = BrandedPDFEngine()
    safe_name = args.client.lower().replace(" ", "_")
    output_path = args.output or f"onboarding_{safe_name}.pdf"

    engine.generate_to_file("onboarding_packet", data, output_path)
    print(f"Onboarding packet generated: {output_path}")
    return output_path


if __name__ == "__main__":
    main()
