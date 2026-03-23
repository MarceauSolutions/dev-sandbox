#!/usr/bin/env python3
"""
Multi-Touch Follow-Up Sequence - Conservative 3-Touch Approach (No False Social Proof)

CRITICAL SAFEGUARDS AGAINST SPAM:
1. Auto-stop on response (mark_response())
2. Auto-stop on opt-out (mark_response(..., "opted_out"))
3. Max 3 touches total (vs 7-touch Hormozi)
4. 3-5 day delays between touches
5. Different message angles (no repetition)

3-Touch Sequence:
- Day 0: Initial outreach (pain point angle)
- Day 3: Follow-up #1 (question/curiosity - makes them think)
- Day 7: Follow-up #2 (scarcity/breakup - final chance)

Key Changes from Original:
- NO fake social proof ("Just helped 3 Naples gyms...")
- Use question hooks instead ("How many customers do you lose...")
- Use scarcity/breakup for final touch
- SMS channel requires prior express consent (sms_consent: true on lead record).
  Email-only sequences do NOT require consent. Never cold-text a prospect.
  TCPA violation = $500-$1,500 per unsolicited automated message.

Usage:
    python -m src.follow_up_sequence status
    python -m src.follow_up_sequence process --dry-run
    python -m src.follow_up_sequence process --for-real
    python -m src.follow_up_sequence queue --days 7
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
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
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
    sending_business_id: str = ""  # NEW: Which business is running this sequence
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
# FOLLOW-UP SEQUENCE TEMPLATES (Conservative 3-Touch, No Fake Social Proof)
# =============================================================================
# CRITICAL: Only 3 touches over 7 days to avoid appearing spammy
# NO fake social proof - only honest value propositions

FOLLOW_UP_SEQUENCE = [
    # Touch 1: Initial outreach (Day 0) - Uses template from pain point
    {
        "touch_number": 1,
        "days_after_initial": 0,
        "template": "auto_select",  # Based on pain points (no_website_v2_compliant, etc.)
        "strategy": "Initial value proposition",
        "notes": "First contact - direct value offer (already sent, enrolled into sequence)"
    },

    # Touch 2: Follow-up (Day 3) - Question hook (NO social proof)
    {
        "touch_number": 2,
        "days_after_initial": 3,
        "template": "followup_question",  # Pain-point specific question templates
        "strategy": "Question hook - makes them think about the problem",
        "notes": "Different angle from initial - curiosity-based, not salesy"
    },

    # Touch 3: Breakup (Day 7) - Scarcity + final chance
    {
        "touch_number": 3,
        "days_after_initial": 7,
        "template": "followup_breakup",  # Pain-point specific breakup templates
        "strategy": "Scarcity/breakup - last message",
        "notes": "Creates urgency with time-limited availability, then exit sequence"
    },
]

# Additional templates for follow-up sequence (NO FAKE SOCIAL PROOF)
# These are pain-point-specific and use honest value propositions only
FOLLOW_UP_TEMPLATES = {
    # NO_WEBSITE follow-ups
    "no_website_followup_question": {
        "body": "Hi $business_name - William from Marceau Solutions again. Quick question: how many customers do you lose each week because you don't show up on Google? (239) 398-5676 - Reply STOP to opt out.",
        "char_count": 190,
        "notes": "Question hook - makes them think about the problem"
    },

    "no_website_followup_breakup": {
        "body": "Last message - William from Marceau Solutions. Only taking 2 more website projects this month. If interested, text YES or call (239) 398-5676. Otherwise I'll remove you. Reply STOP to opt out.",
        "char_count": 202,
        "notes": "Scarcity + breakup language"
    },

    # NO_ONLINE_TRANSACTIONS follow-ups
    "no_online_transactions_followup_question": {
        "body": "Hi $business_name - William again. Quick question: how many appointments do you lose because people can't book online 24/7? (239) 398-5676 - Reply STOP to opt out.",
        "char_count": 172,
        "notes": "Question hook for booking pain"
    },

    "no_online_transactions_followup_breakup": {
        "body": "Last text - William from Marceau Solutions. Only setting up 2 more online booking systems this month. Interested? Text YES or call (239) 398-5676. Reply STOP to opt out.",
        "char_count": 183,
        "notes": "Scarcity for booking systems"
    },

    # FEW_REVIEWS follow-ups
    "few_reviews_followup_question": {
        "body": "Hi $business_name - William here. Quick question: how many customers check your reviews before deciding to call? (239) 398-5676 - Reply STOP to opt out.",
        "char_count": 161,
        "notes": "Question hook for review importance"
    },

    "few_reviews_followup_breakup": {
        "body": "Final message - William from Marceau Solutions. Only helping 2 more businesses boost reviews this month. Want details? Text YES or call (239) 398-5676. Reply STOP to opt out.",
        "char_count": 185,
        "notes": "Scarcity for review help"
    },

    # APOLLO B2B follow-ups (uses $first_name instead of $business_name)
    "apollo_b2b_followup_question": {
        "body": "$first_name - William again. Quick question: what % of your no-shows and cancellations get a follow-up text? (239) 398-5676. Reply STOP to opt out.",
        "char_count": 153,
        "notes": "Apollo B2B follow-up - pain point question"
    },

    "apollo_b2b_followup_breakup": {
        "body": "Last text $first_name - only taking 3 more automation clients this month. If interested in saving 10+ hrs/week on member outreach, text YES. Reply STOP to opt out.",
        "char_count": 172,
        "notes": "Apollo B2B breakup - scarcity + exit"
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
                        sending_business_id=seq_data.get("sending_business_id", ""),
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

    def enroll_lead(self, lead: Lead, business_id: str = "marceau-solutions") -> LeadSequence:
        """
        Enroll a lead into the follow-up sequence.

        Args:
            lead: Lead object to enroll
            business_id: Which business is running this sequence

        Creates touchpoint schedule based on current date.
        """
        if lead.id in self.sequences:
            logger.info(f"Lead {lead.business_name} already enrolled")
            return self.sequences[lead.id]

        now = datetime.now()

        # Build touchpoint schedule
        touchpoints = []

        # Determine lead's primary pain point for template selection
        primary_pain_point = lead.pain_points[0] if lead.pain_points else "no_website"

        for touch_config in FOLLOW_UP_SEQUENCE:
            scheduled_date = now + timedelta(days=touch_config["days_after_initial"])

            # Select template based on touch number and pain point
            template = touch_config["template"]
            if template == "auto_select":
                # Touch 1: Use initial pain-point template
                template = self.sms_manager.select_template_for_lead(lead)
            elif template == "followup_question":
                # Touch 2: Question template for this pain point
                template = f"{primary_pain_point}_followup_question"
            elif template == "followup_breakup":
                # Touch 3: Breakup template for this pain point
                template = f"{primary_pain_point}_followup_breakup"

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
            sending_business_id=business_id,
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

            # Get lead data - try collection first, then create from sequence
            lead = leads_collection.leads.get(sequence.lead_id)
            if not lead:
                # Create a minimal Lead from sequence data for template generation
                lead = Lead(
                    id=sequence.lead_id,
                    business_name=sequence.business_name,
                    phone=sequence.phone,
                    source="follow_up_sequence"
                )
                logger.debug(f"Created lead from sequence data: {sequence.business_name}")

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
