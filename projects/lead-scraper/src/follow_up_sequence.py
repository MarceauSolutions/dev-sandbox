#!/usr/bin/env python3
"""
Multi-Touch Follow-Up Sequence - Hormozi Framework Implementation.

Implements the "Rule of 100" with 5-7 touchpoints per lead:
- Day 0: Initial outreach
- Day 2: Quick follow-up
- Day 5: Value-add follow-up
- Day 10: Alternative offer
- Day 15: Breakup message
- Day 30: Re-engagement
- Day 60: Final attempt

Research shows:
- 80% of sales require 5+ follow-ups
- Most salespeople give up after 1-2
- The fortune is in the follow-up

Usage:
    python -m src.follow_up_sequence status
    python -m src.follow_up_sequence process --dry-run
    python -m src.follow_up_sequence process --for-real
    python -m src.follow_up_sequence queue --days 3
"""

import os
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum

from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

from .models import Lead, LeadCollection
from .sms_outreach import SMSOutreachManager, SMSRecord, SMS_TEMPLATES

logger = logging.getLogger(__name__)


class TouchStatus(Enum):
    """Status of a touchpoint."""
    PENDING = "pending"
    SENT = "sent"
    RESPONDED = "responded"
    OPTED_OUT = "opted_out"
    CONVERTED = "converted"
    SKIPPED = "skipped"


class LeadStatus(Enum):
    """Overall status of lead in sequence."""
    NEW = "new"
    IN_SEQUENCE = "in_sequence"
    RESPONDED = "responded"
    CONVERTED = "converted"
    OPTED_OUT = "opted_out"
    EXHAUSTED = "exhausted"  # All touches completed, no response


@dataclass
class TouchPoint:
    """Individual touchpoint in the sequence."""
    touch_number: int
    template_name: str
    days_after_initial: int
    scheduled_at: str = ""
    sent_at: str = ""
    status: str = "pending"
    message_sid: str = ""
    response: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LeadSequence:
    """Tracks a lead's progress through the follow-up sequence."""
    lead_id: str
    phone: str
    business_name: str
    status: str = "new"  # LeadStatus value
    started_at: str = ""
    last_touch_at: str = ""
    response_at: str = ""
    notes: str = ""
    touchpoints: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def current_touch(self) -> int:
        """Get the current touchpoint number (1-indexed)."""
        sent_touches = [t for t in self.touchpoints if t.get("status") == "sent"]
        return len(sent_touches)

    @property
    def next_touch(self) -> Optional[Dict[str, Any]]:
        """Get the next pending touchpoint."""
        for t in self.touchpoints:
            if t.get("status") == "pending":
                return t
        return None


# =============================================================================
# FOLLOW-UP SEQUENCE TEMPLATES (Hormozi Framework)
# =============================================================================
# 5-7 touches over 60 days, each with distinct messaging angle

FOLLOW_UP_SEQUENCE = [
    # Touch 1: Initial outreach (Day 0) - Uses template from pain point
    {
        "touch_number": 1,
        "days_after_initial": 0,
        "template": "auto_select",  # Based on pain points
        "strategy": "Initial value proposition",
        "notes": "First contact - direct value offer"
    },

    # Touch 2: Quick Follow-up (Day 2) - "9-word email" SMS version
    {
        "touch_number": 2,
        "days_after_initial": 2,
        "template": "still_looking",
        "strategy": "Quick check-in, no pitch",
        "notes": "Short, curiosity-based"
    },

    # Touch 3: Value Add (Day 5) - Social proof
    {
        "touch_number": 3,
        "days_after_initial": 5,
        "template": "social_proof",
        "strategy": "Share results from similar business",
        "notes": "Build credibility with proof"
    },

    # Touch 4: Alternative Angle (Day 10) - Different offer
    {
        "touch_number": 4,
        "days_after_initial": 10,
        "template": "competitor_hook",
        "strategy": "Create FOMO with competitor story",
        "notes": "Shift from direct offer to competitor angle"
    },

    # Touch 5: Direct Question (Day 15) - Re-engage
    {
        "touch_number": 5,
        "days_after_initial": 15,
        "template": "direct_question",
        "strategy": "Ask if they have someone handling this",
        "notes": "Opens dialogue vs selling"
    },

    # Touch 6: Breakup Message (Day 30) - Creates urgency
    {
        "touch_number": 6,
        "days_after_initial": 30,
        "template": "breakup",  # Custom template below
        "strategy": "Last chance framing",
        "notes": "Breakup creates urgency, high conversion"
    },

    # Touch 7: Re-engagement (Day 60) - Final attempt
    {
        "touch_number": 7,
        "days_after_initial": 60,
        "template": "re_engage",  # Custom template below
        "strategy": "Fresh start positioning",
        "notes": "Position as checking back in"
    },
]

# Additional templates for follow-up sequence
FOLLOW_UP_TEMPLATES = {
    "breakup": {
        "body": "Hey, closing out my list of Naples gyms for website help. Last chance if you're interested. -William. Reply STOP to opt out.",
        "char_count": 119,
        "notes": "Breakup message creates urgency"
    },

    "re_engage": {
        "body": "Hey $business_name, wanted to check back in. Still looking for help with your online presence? -William. Reply STOP to opt out.",
        "char_count": 124,
        "notes": "Re-engagement after cool-off period"
    },

    "value_drop": {
        "body": "Hi, found 3 things that could help $business_name get more members. Free to share if interested. -William. Reply STOP to opt out.",
        "char_count": 128,
        "notes": "Lead with value, not pitch"
    },
}


class FollowUpSequenceManager:
    """
    Manages multi-touch follow-up sequences for leads.

    Features:
    - Tracks each lead's position in the sequence
    - Schedules touchpoints based on days since initial
    - Automatically advances or exits based on response
    - Integrates with SMS outreach for sending
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load existing sequence data
        self.sequences_file = self.output_dir / "follow_up_sequences.json"
        self.sequences: Dict[str, LeadSequence] = {}
        self._load_sequences()

        # SMS manager for sending
        self.sms_manager = SMSOutreachManager(output_dir=output_dir)

        # Merge follow-up templates into SMS templates
        SMS_TEMPLATES.update(FOLLOW_UP_TEMPLATES)

    def _load_sequences(self) -> None:
        """Load existing sequence data."""
        if self.sequences_file.exists():
            with open(self.sequences_file, 'r') as f:
                data = json.load(f)
                for seq_data in data.get("sequences", []):
                    seq = LeadSequence(
                        lead_id=seq_data["lead_id"],
                        phone=seq_data["phone"],
                        business_name=seq_data["business_name"],
                        status=seq_data.get("status", "new"),
                        started_at=seq_data.get("started_at", ""),
                        last_touch_at=seq_data.get("last_touch_at", ""),
                        response_at=seq_data.get("response_at", ""),
                        notes=seq_data.get("notes", ""),
                        touchpoints=seq_data.get("touchpoints", [])
                    )
                    self.sequences[seq.lead_id] = seq

    def _save_sequences(self) -> None:
        """Save sequence data."""
        data = {
            "sequences": [s.to_dict() for s in self.sequences.values()],
            "updated_at": datetime.now().isoformat()
        }
        with open(self.sequences_file, 'w') as f:
            json.dump(data, f, indent=2)

    def enroll_lead(self, lead: Lead) -> LeadSequence:
        """
        Enroll a lead into the follow-up sequence.

        Creates touchpoint schedule based on current date.
        """
        if lead.id in self.sequences:
            logger.info(f"Lead {lead.business_name} already enrolled")
            return self.sequences[lead.id]

        now = datetime.now()

        # Build touchpoint schedule
        touchpoints = []
        for touch_config in FOLLOW_UP_SEQUENCE:
            scheduled_date = now + timedelta(days=touch_config["days_after_initial"])

            # Auto-select template for first touch based on pain points
            template = touch_config["template"]
            if template == "auto_select":
                template = self.sms_manager.select_template_for_lead(lead)

            touchpoint = {
                "touch_number": touch_config["touch_number"],
                "template_name": template,
                "days_after_initial": touch_config["days_after_initial"],
                "scheduled_at": scheduled_date.isoformat(),
                "sent_at": "",
                "status": "pending",
                "message_sid": "",
                "response": ""
            }
            touchpoints.append(touchpoint)

        # Create sequence record
        sequence = LeadSequence(
            lead_id=lead.id,
            phone=lead.phone or "",
            business_name=lead.business_name,
            status="in_sequence",
            started_at=now.isoformat(),
            touchpoints=touchpoints
        )

        self.sequences[lead.id] = sequence
        self._save_sequences()

        logger.info(f"Enrolled {lead.business_name} in {len(touchpoints)}-touch sequence")
        return sequence

    def get_due_touchpoints(self, as_of: Optional[datetime] = None) -> List[Tuple[LeadSequence, Dict]]:
        """
        Get all touchpoints that are due to be sent.

        Args:
            as_of: Check against this time (default: now)

        Returns:
            List of (sequence, touchpoint) tuples
        """
        if as_of is None:
            as_of = datetime.now()

        due = []

        for sequence in self.sequences.values():
            # Skip leads not in active sequence
            if sequence.status not in ["new", "in_sequence"]:
                continue

            # Find next pending touchpoint
            for touchpoint in sequence.touchpoints:
                if touchpoint["status"] != "pending":
                    continue

                scheduled = datetime.fromisoformat(touchpoint["scheduled_at"])
                if scheduled <= as_of:
                    due.append((sequence, touchpoint))
                    break  # Only one touchpoint per lead

        return due

    def send_touchpoint(
        self,
        sequence: LeadSequence,
        touchpoint: Dict,
        lead: Lead,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Send a single touchpoint message.

        Args:
            sequence: Lead's sequence record
            touchpoint: The touchpoint to send
            lead: Lead object
            dry_run: Preview without sending

        Returns:
            Result dict
        """
        template_name = touchpoint["template_name"]

        # Generate message
        try:
            message_body = self.sms_manager.generate_sms(lead, template_name)
        except Exception as e:
            logger.error(f"Template error: {e}")
            return {"status": "error", "error": str(e)}

        # Send via SMS manager
        result = self.sms_manager.send_sms(
            to_phone=sequence.phone,
            body=message_body,
            dry_run=dry_run
        )

        # Update touchpoint
        if result["status"] in ["sent", "dry_run", "queued"]:
            # Mark as sent for queued messages (will send at 9 AM via Twilio)
            touchpoint["status"] = "sent" if result["status"] in ["sent", "dry_run"] else "queued"
            touchpoint["sent_at"] = datetime.now().isoformat() if result["status"] == "sent" else ("DRY_RUN" if result["status"] == "dry_run" else "QUEUED")
            touchpoint["message_sid"] = result.get("message_sid", "")

            sequence.last_touch_at = datetime.now().isoformat()
            self._save_sequences()

        return {
            "status": result["status"],
            "touch_number": touchpoint["touch_number"],
            "template": template_name,
            "message": message_body[:50] + "...",
            "message_sid": result.get("message_sid", "")
        }

    def process_due_touchpoints(
        self,
        leads_collection: LeadCollection,
        dry_run: bool = True,
        limit: int = 100,
        delay_seconds: float = 2.0
    ) -> Dict[str, Any]:
        """
        Process all due touchpoints across all sequences.

        Args:
            leads_collection: LeadCollection for lead data
            dry_run: Preview without sending
            limit: Max messages to send
            delay_seconds: Delay between messages

        Returns:
            Processing statistics
        """
        import time

        stats = {
            "total_due": 0,
            "processed": 0,
            "sent": 0,
            "errors": [],
            "by_touch_number": {}
        }

        due_touchpoints = self.get_due_touchpoints()
        stats["total_due"] = len(due_touchpoints)

        for i, (sequence, touchpoint) in enumerate(due_touchpoints[:limit]):
            if i > 0:
                time.sleep(delay_seconds)

            touch_num = touchpoint["touch_number"]
            logger.info(f"Processing Touch #{touch_num} for {sequence.business_name}")

            # Get lead data
            lead = leads_collection.leads.get(sequence.lead_id)
            if not lead:
                stats["errors"].append(f"Lead not found: {sequence.lead_id}")
                continue

            # Send touchpoint
            result = self.send_touchpoint(
                sequence=sequence,
                touchpoint=touchpoint,
                lead=lead,
                dry_run=dry_run
            )

            if result["status"] in ["sent", "dry_run", "queued"]:
                stats["sent"] += 1
                stats["by_touch_number"][touch_num] = stats["by_touch_number"].get(touch_num, 0) + 1
            else:
                stats["errors"].append(f"{sequence.business_name}: {result.get('error', 'Unknown error')}")

            stats["processed"] += 1

        return stats

    def mark_response(
        self,
        phone: str,
        response_type: str = "responded",
        notes: str = ""
    ) -> Optional[LeadSequence]:
        """
        Mark a lead as having responded.

        Args:
            phone: Phone number that responded
            response_type: Type of response (responded, converted, opted_out)
            notes: Optional notes about the response

        Returns:
            Updated sequence or None
        """
        # Normalize phone
        normalized = self.sms_manager._normalize_phone(phone)

        # Find sequence by phone
        for sequence in self.sequences.values():
            seq_phone = self.sms_manager._normalize_phone(sequence.phone)
            if seq_phone == normalized:
                sequence.status = response_type
                sequence.response_at = datetime.now().isoformat()
                sequence.notes = notes

                # Mark remaining touchpoints as skipped
                for touchpoint in sequence.touchpoints:
                    if touchpoint["status"] == "pending":
                        touchpoint["status"] = "skipped"

                self._save_sequences()
                logger.info(f"Marked {sequence.business_name} as {response_type}")
                return sequence

        logger.warning(f"No sequence found for phone: {phone}")
        return None

    def get_sequence_stats(self) -> Dict[str, Any]:
        """Get overall sequence statistics."""
        stats = {
            "total_sequences": len(self.sequences),
            "by_status": {},
            "by_current_touch": {},
            "response_rate": 0,
            "conversion_rate": 0
        }

        for sequence in self.sequences.values():
            # By status
            stats["by_status"][sequence.status] = stats["by_status"].get(sequence.status, 0) + 1

            # By current touch (for active sequences)
            if sequence.status == "in_sequence":
                current = sequence.current_touch
                stats["by_current_touch"][current] = stats["by_current_touch"].get(current, 0) + 1

        # Calculate rates
        total = len(self.sequences)
        if total > 0:
            responded = sum(1 for s in self.sequences.values()
                          if s.status in ["responded", "converted"])
            converted = sum(1 for s in self.sequences.values() if s.status == "converted")

            stats["response_rate"] = round(responded / total * 100, 1)
            stats["conversion_rate"] = round(converted / total * 100, 1)

        return stats

    def get_queue_preview(self, days: int = 7) -> Dict[str, List[str]]:
        """
        Preview touchpoints scheduled for the next N days.

        Args:
            days: Number of days to look ahead

        Returns:
            Dict of date -> list of lead names
        """
        cutoff = datetime.now() + timedelta(days=days)
        preview = {}

        for sequence in self.sequences.values():
            if sequence.status not in ["new", "in_sequence"]:
                continue

            for touchpoint in sequence.touchpoints:
                if touchpoint["status"] != "pending":
                    continue

                scheduled = datetime.fromisoformat(touchpoint["scheduled_at"])
                if scheduled <= cutoff:
                    date_str = scheduled.strftime("%Y-%m-%d")
                    if date_str not in preview:
                        preview[date_str] = []
                    preview[date_str].append(
                        f"Touch #{touchpoint['touch_number']}: {sequence.business_name}"
                    )
                break

        return preview


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """CLI entry point for follow-up sequence management."""
    import argparse

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description="Multi-Touch Follow-Up Sequence Manager")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show sequence statistics")
    status_parser.add_argument("--output-dir", "-o", default="output", help="Output directory")

    # Enroll command
    enroll_parser = subparsers.add_parser("enroll", help="Enroll leads in sequence")
    enroll_parser.add_argument("--pain-point", "-p", help="Filter by pain point")
    enroll_parser.add_argument("--limit", "-l", type=int, default=100, help="Max leads to enroll")
    enroll_parser.add_argument("--output-dir", "-o", default="output", help="Output directory")

    # Process command
    process_parser = subparsers.add_parser("process", help="Process due touchpoints")
    process_parser.add_argument("--dry-run", action="store_true", default=True, help="Preview without sending")
    process_parser.add_argument("--for-real", action="store_true", help="Actually send messages")
    process_parser.add_argument("--limit", "-l", type=int, default=100, help="Max messages")
    process_parser.add_argument("--output-dir", "-o", default="output", help="Output directory")

    # Queue command
    queue_parser = subparsers.add_parser("queue", help="Preview upcoming touchpoints")
    queue_parser.add_argument("--days", "-d", type=int, default=7, help="Days to look ahead")
    queue_parser.add_argument("--output-dir", "-o", default="output", help="Output directory")

    # Response command
    response_parser = subparsers.add_parser("response", help="Mark lead as responded")
    response_parser.add_argument("phone", help="Phone number that responded")
    response_parser.add_argument("--type", "-t", choices=["responded", "converted", "opted_out"],
                                default="responded", help="Response type")
    response_parser.add_argument("--notes", "-n", default="", help="Notes about response")
    response_parser.add_argument("--output-dir", "-o", default="output", help="Output directory")

    # Sequence info command
    sequence_parser = subparsers.add_parser("sequence", help="Show sequence configuration")

    args = parser.parse_args()

    if args.command == "sequence":
        print("\n=== Follow-Up Sequence (Hormozi Framework) ===\n")
        for config in FOLLOW_UP_SEQUENCE:
            print(f"Touch #{config['touch_number']} (Day {config['days_after_initial']})")
            print(f"  Template: {config['template']}")
            print(f"  Strategy: {config['strategy']}")
            print(f"  Notes: {config['notes']}")
            print()
        return

    if args.command == "status":
        manager = FollowUpSequenceManager(output_dir=args.output_dir)
        stats = manager.get_sequence_stats()
        print("\n=== Follow-Up Sequence Statistics ===")
        print(f"Total Sequences: {stats['total_sequences']}")
        print(f"Response Rate: {stats['response_rate']}%")
        print(f"Conversion Rate: {stats['conversion_rate']}%")
        print("\nBy Status:")
        for status, count in stats["by_status"].items():
            print(f"  {status}: {count}")
        print("\nActive Sequences by Touch #:")
        for touch, count in sorted(stats["by_current_touch"].items()):
            print(f"  Touch #{touch}: {count} leads")
        return

    if args.command == "queue":
        manager = FollowUpSequenceManager(output_dir=args.output_dir)
        preview = manager.get_queue_preview(days=args.days)
        print(f"\n=== Touchpoints Scheduled (Next {args.days} Days) ===\n")
        if not preview:
            print("No touchpoints scheduled.")
        for date, leads in sorted(preview.items()):
            print(f"{date}:")
            for lead in leads:
                print(f"  - {lead}")
        return

    if args.command == "response":
        manager = FollowUpSequenceManager(output_dir=args.output_dir)
        result = manager.mark_response(
            phone=args.phone,
            response_type=args.type,
            notes=args.notes
        )
        if result:
            print(f"Marked {result.business_name} as {args.type}")
        else:
            print(f"No sequence found for phone: {args.phone}")
        return

    if args.command == "enroll":
        # Load leads
        collection = LeadCollection(output_dir=args.output_dir)
        collection.load_json()

        leads = [l for l in collection.leads.values() if l.phone]

        # Filter by pain point if specified
        if args.pain_point:
            leads = [l for l in leads if args.pain_point in l.pain_points]

        manager = FollowUpSequenceManager(output_dir=args.output_dir)

        enrolled = 0
        for lead in leads[:args.limit]:
            if lead.id not in manager.sequences:
                manager.enroll_lead(lead)
                enrolled += 1

        print(f"\nEnrolled {enrolled} new leads in sequence")
        print(f"Total sequences: {len(manager.sequences)}")
        return

    if args.command == "process":
        # Load leads
        collection = LeadCollection(output_dir=args.output_dir)
        collection.load_json()

        manager = FollowUpSequenceManager(output_dir=args.output_dir)

        dry_run = not args.for_real

        stats = manager.process_due_touchpoints(
            leads_collection=collection,
            dry_run=dry_run,
            limit=args.limit
        )

        print("\n=== Processing Results ===")
        print(f"Total Due: {stats['total_due']}")
        print(f"Processed: {stats['processed']}")
        print(f"Sent: {stats['sent']}")
        print("\nBy Touch Number:")
        for touch, count in sorted(stats["by_touch_number"].items()):
            print(f"  Touch #{touch}: {count}")
        if stats["errors"]:
            print(f"\nErrors: {len(stats['errors'])}")


if __name__ == "__main__":
    main()
