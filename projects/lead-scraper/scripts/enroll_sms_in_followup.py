#!/usr/bin/env python3
"""
Enroll existing SMS campaign leads into 7-touch follow-up sequence.

This script:
1. Loads all SMS campaign records
2. Filters for leads that were sent initial message but haven't responded
3. Enrolls them in the 7-touch follow-up sequence
4. Starts at touch #2 (they already got touch #1)

Usage:
    python scripts/enroll_sms_in_followup.py --dry-run   # Preview
    python scripts/enroll_sms_in_followup.py --for-real  # Actually enroll
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.follow_up_sequence import (
    FollowUpSequenceManager, LeadSequence, TouchPoint,
    LeadStatus, TouchStatus
)
from src.models import Lead

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 7-Touch Sequence Template (Hormozi Framework)
SEVEN_TOUCH_SEQUENCE = [
    # Touch 1: Initial outreach (already sent via SMS campaign)
    {"touch": 1, "days": 0, "template": "no_website_intro"},
    # Touch 2: Quick follow-up
    {"touch": 2, "days": 2, "template": "still_looking"},
    # Touch 3: Value-add
    {"touch": 3, "days": 5, "template": "free_mockup"},
    # Touch 4: Alternative offer
    {"touch": 4, "days": 10, "template": "seo_audit"},
    # Touch 5: Breakup message
    {"touch": 5, "days": 15, "template": "breakup"},
    # Touch 6: Re-engagement
    {"touch": 6, "days": 30, "template": "competitor_launched"},
    # Touch 7: Final attempt
    {"touch": 7, "days": 60, "template": "final_chance"}
]


def load_sms_campaigns(output_dir: str = "output") -> list:
    """Load SMS campaign records."""
    campaigns_file = Path(output_dir) / "sms_campaigns.json"

    if not campaigns_file.exists():
        logger.error(f"SMS campaigns file not found: {campaigns_file}")
        return []

    with open(campaigns_file, 'r') as f:
        data = json.load(f)
        return data.get("records", [])


def filter_enrollable_leads(sms_records: list) -> list:
    """
    Filter SMS records for leads eligible for follow-up enrollment.

    Criteria:
    - Status: sent (successfully delivered)
    - No response recorded
    - Not opted out
    - Sent more than 2 days ago (ready for touch #2)
    """
    enrollable = []

    for record in sms_records:
        # Must be successfully sent
        if record.get("status") != "sent":
            continue

        # Must not have opted out
        if record.get("status") == "opted_out":
            continue

        # Must not have response recorded
        if record.get("response"):
            continue

        # Check if sent >2 days ago (ready for touch #2)
        sent_at_str = record.get("sent_at")
        if sent_at_str:
            try:
                sent_at = datetime.fromisoformat(sent_at_str)
                days_ago = (datetime.now() - sent_at).days

                # Only enroll if sent 2+ days ago
                if days_ago >= 2:
                    enrollable.append(record)
            except Exception as e:
                logger.warning(f"Could not parse sent_at: {sent_at_str} - {e}")
                continue

    return enrollable


def create_sequence_from_sms(sms_record: dict) -> LeadSequence:
    """
    Create a LeadSequence from an SMS campaign record.

    Starts at touch #2 since touch #1 (initial SMS) was already sent.
    """
    lead_id = sms_record.get("lead_id")
    phone = sms_record.get("phone")
    business_name = sms_record.get("business_name", "Unknown Business")
    sent_at = sms_record.get("sent_at")

    # Create sequence starting at touch #2
    touchpoints = []

    # Touch 1 - already sent (mark as sent)
    touch1 = TouchPoint(
        touch_number=1,
        template_name=sms_record.get("template_used", "no_website_intro"),
        days_after_initial=0,
        scheduled_at=sent_at,
        sent_at=sent_at,
        status="sent",
        message_sid=sms_record.get("message_sid", "")
    )
    touchpoints.append(touch1.to_dict())

    # Touches 2-7 - schedule based on initial send date
    initial_date = datetime.fromisoformat(sent_at)

    for touch_config in SEVEN_TOUCH_SEQUENCE[1:]:  # Skip touch 1
        touch_number = touch_config["touch"]
        days_after = touch_config["days"]
        template = touch_config["template"]

        scheduled_date = initial_date + timedelta(days=days_after)

        touchpoint = TouchPoint(
            touch_number=touch_number,
            template_name=template,
            days_after_initial=days_after,
            scheduled_at=scheduled_date.isoformat(),
            status="pending"
        )
        touchpoints.append(touchpoint.to_dict())

    # Create sequence
    sequence = LeadSequence(
        lead_id=lead_id,
        phone=phone,
        business_name=business_name,
        status=LeadStatus.IN_SEQUENCE.value,
        started_at=sent_at,
        last_touch_at=sent_at,
        touchpoints=touchpoints
    )

    return sequence


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Enroll SMS leads in follow-up sequence")
    parser.add_argument("--dry-run", action="store_true", help="Preview without enrolling")
    parser.add_argument("--for-real", action="store_true", help="Actually enroll leads")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    parser.add_argument("--limit", type=int, help="Limit number of enrollments")

    args = parser.parse_args()

    if not args.dry_run and not args.for_real:
        print("Error: Must specify --dry-run or --for-real")
        return 1

    # Load SMS campaigns
    logger.info("Loading SMS campaign records...")
    sms_records = load_sms_campaigns(args.output_dir)
    logger.info(f"Found {len(sms_records)} total SMS records")

    # Filter for enrollable leads
    enrollable = filter_enrollable_leads(sms_records)
    logger.info(f"Found {len(enrollable)} leads eligible for follow-up enrollment")

    if args.limit:
        enrollable = enrollable[:args.limit]
        logger.info(f"Limited to {len(enrollable)} leads")

    if not enrollable:
        print("\nNo leads found eligible for enrollment.")
        print("Criteria: sent >2 days ago, no response, not opted out")
        return 0

    # Preview
    print(f"\n{'='*60}")
    print(f"FOLLOW-UP SEQUENCE ENROLLMENT")
    print(f"{'='*60}")
    print(f"Eligible leads: {len(enrollable)}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'ENROLLING FOR REAL'}")
    print(f"\n7-Touch Sequence:")
    for i, touch in enumerate(SEVEN_TOUCH_SEQUENCE, 1):
        days = touch['days']
        template = touch['template']
        print(f"  Touch {i}: Day {days} - {template}")

    print(f"\n{'='*60}")
    print(f"Sample Leads to Enroll:")
    print(f"{'='*60}")

    for i, record in enumerate(enrollable[:5], 1):
        business = record.get("business_name", "Unknown")
        phone = record.get("phone", "Unknown")
        sent = record.get("sent_at", "Unknown")
        print(f"{i}. {business} ({phone})")
        print(f"   Initial SMS sent: {sent}")

    if len(enrollable) > 5:
        print(f"   ... and {len(enrollable) - 5} more")

    # Enroll if for-real
    if args.for_real:
        print(f"\n{'='*60}")
        print(f"ENROLLING LEADS...")
        print(f"{'='*60}")

        manager = FollowUpSequenceManager(output_dir=args.output_dir)
        enrolled_count = 0

        for record in enrollable:
            try:
                sequence = create_sequence_from_sms(record)
                manager.sequences[sequence.lead_id] = sequence
                enrolled_count += 1

                if enrolled_count % 10 == 0:
                    logger.info(f"Enrolled {enrolled_count}/{len(enrollable)}...")

            except Exception as e:
                logger.error(f"Failed to enroll {record.get('business_name')}: {e}")

        manager._save_sequences()
        print(f"\n✅ Successfully enrolled {enrolled_count} leads in follow-up sequence")
        print(f"\nNext steps:")
        print(f"1. Run daily: python -m src.follow_up_sequence process --for-real")
        print(f"2. Check status: python -m src.follow_up_sequence status")
        print(f"3. Monitor responses and opt-outs")

    else:
        print(f"\n{'='*60}")
        print(f"DRY RUN COMPLETE - No leads enrolled")
        print(f"{'='*60}")
        print(f"\nTo enroll for real, run:")
        print(f"  python scripts/enroll_sms_in_followup.py --for-real")

    return 0


if __name__ == "__main__":
    sys.exit(main())
