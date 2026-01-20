#!/usr/bin/env python3
"""
SMS Cold Outreach System - Twilio-based SMS campaigns using Hormozi framework.

Implements:
1. Rule of 100: High volume outreach
2. Personalization: Business name in message
3. Compliance: STOP opt-out in every message
4. Tracking: Message delivery status and responses

Usage:
    python -m src.sms_outreach send --dry-run --limit 10
    python -m src.sms_outreach send --for-real --limit 100
    python -m src.sms_outreach templates
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any
from string import Template

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

from .models import Lead, LeadCollection
from .opt_out_manager import OptOutManager, check_before_send

logger = logging.getLogger(__name__)

# Try to import Twilio
try:
    from twilio.rest import Client as TwilioClient
    from twilio.base.exceptions import TwilioRestException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logger.warning("Twilio not installed. Run: pip install twilio")


@dataclass
class TwilioConfig:
    """Twilio configuration from environment."""
    account_sid: str = ""
    auth_token: str = ""
    phone_number: str = ""

    @classmethod
    def from_env(cls) -> "TwilioConfig":
        return cls(
            account_sid=os.getenv("TWILIO_ACCOUNT_SID", ""),
            auth_token=os.getenv("TWILIO_AUTH_TOKEN", ""),
            phone_number=os.getenv("TWILIO_PHONE_NUMBER", "")
        )

    def is_configured(self) -> bool:
        return bool(self.account_sid and self.auth_token and self.phone_number)


@dataclass
class SMSRecord:
    """Track SMS outreach attempts."""
    lead_id: str
    phone: str
    business_name: str
    template_used: str
    message_body: str
    message_sid: str = ""
    sent_at: str = ""
    status: str = "pending"  # pending, sent, delivered, failed, opted_out
    error_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# HORMOZI-STYLE SMS TEMPLATES
# =============================================================================
# Keep messages under 160 chars when possible (single SMS segment)
# Always include opt-out language for compliance

SMS_TEMPLATES = {
    # Template 1: No Website - Direct Value Offer
    "no_website_intro": {
        "body": "Hi, this is William. I noticed $business_name doesn't have a website. 80% of customers search online first. Want a free mockup? Reply STOP to opt out.",
        "pain_points": ["no_website"],
        "char_count": 158,
        "notes": "Primary template for leads without websites"
    },

    # Template 2: Competitor Hook (Hormozi favorite)
    "competitor_hook": {
        "body": "Hi, calling about a gym near $business_name that just got 23 new members from their website. Call back if interested. -William. Reply STOP to opt out.",
        "pain_points": [],
        "char_count": 156,
        "notes": "Creates curiosity and FOMO"
    },

    # Template 3: Few Reviews - Quick Win
    "few_reviews": {
        "body": "Hi, saw $business_name has $review_count reviews. I helped another Naples gym go from 12 to 67 reviews in 60 days. Interested? Reply STOP to opt out.",
        "pain_points": ["few_reviews", "no_reviews"],
        "char_count": 155,
        "notes": "Targets review pain point"
    },

    # Template 4: Still Looking (9-word reactivation)
    "still_looking": {
        "body": "Still looking to get more members at $business_name? -William. Reply STOP to opt out.",
        "pain_points": [],
        "char_count": 89,
        "notes": "Follow-up for non-responders"
    },

    # Template 5: Social Proof
    "social_proof": {
        "body": "Just helped a Naples gym add 40 members last month. Want to know how? Call me at this number. -William. Reply STOP to opt out.",
        "pain_points": [],
        "char_count": 131,
        "notes": "Leads with social proof"
    },

    # Template 6: Direct Question
    "direct_question": {
        "body": "Quick question for $business_name - do you have someone handling your online presence? If not, I'd love to help. -William. Reply STOP to opt out.",
        "pain_points": ["no_website"],
        "char_count": 152,
        "notes": "Opens conversation"
    },

    # 7-TOUCH SEQUENCE TEMPLATES (for follow_up_sequence.py)

    # Touch 3: Value-add (free mockup offer)
    "free_mockup": {
        "body": "Made a quick mockup for $business_name. Want to see it? Takes 30 seconds. Text YES or call me. -William. Reply STOP to opt out.",
        "pain_points": ["no_website"],
        "char_count": 138,
        "notes": "Touch 3 - Concrete value offer"
    },

    # Touch 4: Alternative offer (SEO audit)
    "seo_audit": {
        "body": "Or if you already have a site, I can send a free SEO audit for $business_name. Just take 5 min to check. Text YES. -William. STOP to opt out.",
        "pain_points": [],
        "char_count": 151,
        "notes": "Touch 4 - Different angle"
    },

    # Touch 5: Breakup message (Hormozi's favorite)
    "breakup": {
        "body": "Should I stop bugging you about $business_name's online presence? If yes, just ignore this. If no, text back. -William. Reply STOP to opt out.",
        "pain_points": [],
        "char_count": 153,
        "notes": "Touch 5 - Permission to stop (gets highest responses)"
    },

    # Touch 6: Re-engagement (competitor angle)
    "competitor_launched": {
        "body": "Saw a competitor near $business_name just launched a new site. Thought you'd want to know. Still interested in catching up? -William. STOP to opt out.",
        "pain_points": ["no_website"],
        "char_count": 158,
        "notes": "Touch 6 - FOMO reactivation"
    },

    # Touch 7: Final attempt
    "final_chance": {
        "body": "Last message - free mockup offer for $business_name expires this week. After that I'm focusing on other businesses. Want it? -William. STOP to opt out.",
        "pain_points": ["no_website"],
        "char_count": 158,
        "notes": "Touch 7 - Final scarcity"
    }
}


class SMSOutreachManager:
    """
    Manages SMS campaigns using Twilio.

    Compliance features:
    - STOP opt-out in every message
    - Rate limiting (1 message per number per day)
    - Business hours enforcement (9am-8pm)
    - Automatic opt-out tracking with OptOutManager integration
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.config = TwilioConfig.from_env()
        self.client = None

        if TWILIO_AVAILABLE and self.config.is_configured():
            self.client = TwilioClient(self.config.account_sid, self.config.auth_token)

        # Load existing campaign data
        self.campaigns_file = self.output_dir / "sms_campaigns.json"
        self.campaigns: Dict[str, SMSRecord] = {}
        self._load_campaigns()

        # Track sent numbers for rate limiting
        self.sent_today: Dict[str, str] = {}  # phone -> date

        # Initialize opt-out manager for compliance checks
        self.opt_out_manager = OptOutManager(output_dir=output_dir)

    def _load_campaigns(self) -> None:
        """Load existing campaign records."""
        if self.campaigns_file.exists():
            with open(self.campaigns_file, 'r') as f:
                data = json.load(f)
                for record in data.get("records", []):
                    # Filter to only known SMSRecord fields to handle any extra fields from sync
                    known_fields = {
                        'lead_id', 'phone', 'business_name', 'template_used',
                        'message_body', 'message_sid', 'sent_at', 'status', 'error_message'
                    }
                    filtered_record = {k: v for k, v in record.items() if k in known_fields}
                    self.campaigns[record["lead_id"]] = SMSRecord(**filtered_record)
                # Load sent_today tracking
                self.sent_today = data.get("sent_today", {})

    def _save_campaigns(self) -> None:
        """Save campaign records."""
        data = {
            "records": [r.to_dict() for r in self.campaigns.values()],
            "sent_today": self.sent_today,
            "updated_at": datetime.now().isoformat()
        }
        with open(self.campaigns_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _is_business_hours(self) -> bool:
        """Check if current time is within business hours (9am-8pm)."""
        now = datetime.now()
        return 9 <= now.hour < 20

    def _can_send_to_number(self, phone: str) -> bool:
        """Check if we can send to this number today (rate limiting)."""
        today = datetime.now().strftime("%Y-%m-%d")
        last_sent = self.sent_today.get(phone)
        return last_sent != today

    def _is_opted_out(self, phone: str) -> bool:
        """Check if phone number is on the opt-out list."""
        return self.opt_out_manager.is_opted_out(phone=phone)

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number to E.164 format."""
        # Remove common formatting
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')

        # Add +1 if US number without country code
        if not cleaned.startswith('+'):
            if cleaned.startswith('1') and len(cleaned) == 11:
                cleaned = '+' + cleaned
            elif len(cleaned) == 10:
                cleaned = '+1' + cleaned

        return cleaned

    def generate_sms(
        self,
        lead: Lead,
        template_name: str,
        custom_vars: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generate personalized SMS from template.

        Args:
            lead: Lead object
            template_name: Template to use
            custom_vars: Optional custom variables

        Returns:
            Rendered SMS body
        """
        template = SMS_TEMPLATES.get(template_name)
        if not template:
            raise ValueError(f"Unknown template: {template_name}")

        # Build substitution variables
        vars = {
            "business_name": lead.business_name[:30],  # Truncate for SMS length
            "city": lead.city or "Naples",
            "review_count": str(lead.review_count),
            "rating": str(lead.rating),
        }

        if custom_vars:
            vars.update(custom_vars)

        # Render template
        body = Template(template["body"]).safe_substitute(vars)

        return body

    def select_template_for_lead(self, lead: Lead) -> str:
        """Select best SMS template based on lead's pain points."""
        pain_points = set(lead.pain_points)

        if "no_website" in pain_points:
            return "no_website_intro"
        elif "no_reviews" in pain_points or lead.review_count == 0:
            return "few_reviews"
        elif "few_reviews" in pain_points or lead.review_count < 10:
            return "few_reviews"
        else:
            return "competitor_hook"

    def send_sms(
        self,
        to_phone: str,
        body: str,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Send SMS via Twilio.

        Args:
            to_phone: Recipient phone number
            body: Message body
            dry_run: If True, just log without sending

        Returns:
            Dict with status and message_sid
        """
        normalized_phone = self._normalize_phone(to_phone)

        if dry_run:
            logger.info(f"[DRY RUN] Would send to: {normalized_phone}")
            logger.info(f"Message ({len(body)} chars): {body}")
            return {"status": "dry_run", "message_sid": "dry_run_sid"}

        if not self.client:
            logger.error("Twilio client not initialized. Check credentials.")
            return {"status": "error", "error": "Twilio not configured"}

        if not self._is_business_hours():
            logger.warning("Outside business hours (9am-8pm). Message queued.")
            return {"status": "queued", "error": "Outside business hours"}

        try:
            message = self.client.messages.create(
                body=body,
                from_=self.config.phone_number,
                to=normalized_phone
            )

            logger.info(f"SMS sent to {normalized_phone}: {message.sid}")
            return {
                "status": "sent",
                "message_sid": message.sid
            }

        except TwilioRestException as e:
            logger.error(f"Twilio error: {e}")
            return {"status": "error", "error": str(e)}

    def run_campaign(
        self,
        leads: List[Lead],
        template_name: Optional[str] = None,
        dry_run: bool = True,
        daily_limit: int = 100,
        delay_seconds: float = 2.0
    ) -> Dict[str, Any]:
        """
        Run SMS campaign on a list of leads.

        Args:
            leads: List of Lead objects
            template_name: Force specific template (or auto-select)
            dry_run: Preview without sending
            daily_limit: Max messages per run
            delay_seconds: Delay between messages

        Returns:
            Campaign statistics
        """
        stats = {
            "total_leads": len(leads),
            "processed": 0,
            "messages_generated": 0,
            "messages_sent": 0,
            "skipped_no_phone": 0,
            "skipped_already_contacted": 0,
            "skipped_rate_limited": 0,
            "skipped_opted_out": 0,
            "errors": []
        }

        for i, lead in enumerate(leads[:daily_limit]):
            if i > 0:
                time.sleep(delay_seconds)

            logger.info(f"Processing {i+1}/{min(len(leads), daily_limit)}: {lead.business_name}")

            # Skip if no phone
            if not lead.phone:
                stats["skipped_no_phone"] += 1
                continue

            # Skip if opted out (COMPLIANCE CHECK - highest priority)
            if self._is_opted_out(lead.phone):
                stats["skipped_opted_out"] += 1
                logger.info(f"  Skipped (opted out): {lead.business_name}")
                continue

            # Skip if already contacted
            if lead.id in self.campaigns:
                stats["skipped_already_contacted"] += 1
                continue

            # Skip if rate limited
            if not self._can_send_to_number(lead.phone):
                stats["skipped_rate_limited"] += 1
                continue

            # Select template
            template = template_name or self.select_template_for_lead(lead)

            # Generate message
            try:
                message_body = self.generate_sms(lead, template)
                stats["messages_generated"] += 1
            except Exception as e:
                stats["errors"].append(f"Template error for {lead.business_name}: {e}")
                continue

            # Send SMS
            result = self.send_sms(
                to_phone=lead.phone,
                body=message_body,
                dry_run=dry_run
            )

            if result["status"] in ["sent", "dry_run"]:
                stats["messages_sent"] += 1

                # Record outreach
                record = SMSRecord(
                    lead_id=lead.id,
                    phone=lead.phone,
                    business_name=lead.business_name,
                    template_used=template,
                    message_body=message_body,
                    message_sid=result.get("message_sid", ""),
                    sent_at=datetime.now().isoformat() if not dry_run else "",
                    status="sent" if not dry_run else "pending"
                )
                self.campaigns[lead.id] = record

                # Track for rate limiting
                if not dry_run:
                    self.sent_today[lead.phone] = datetime.now().strftime("%Y-%m-%d")
            else:
                stats["errors"].append(f"Send error for {lead.business_name}: {result.get('error')}")

            stats["processed"] += 1

        # Save campaign data
        self._save_campaigns()

        return stats

    def get_campaign_stats(self) -> Dict[str, Any]:
        """Get overall campaign statistics."""
        stats = {
            "total_messages": len(self.campaigns),
            "by_status": {},
            "by_template": {},
            "by_date": {}
        }

        for record in self.campaigns.values():
            # By status
            stats["by_status"][record.status] = stats["by_status"].get(record.status, 0) + 1

            # By template
            stats["by_template"][record.template_used] = stats["by_template"].get(record.template_used, 0) + 1

            # By date
            if record.sent_at:
                date = record.sent_at[:10]
                stats["by_date"][date] = stats["by_date"].get(date, 0) + 1

        return stats

    def add_optout(self, phone: str, reason: str = "manual", business_name: str = "") -> None:
        """
        Add phone number to opt-out list using OptOutManager.

        Args:
            phone: Phone number to opt out
            reason: Reason for opt-out (e.g., "sms_stop", "manual")
            business_name: Associated business name
        """
        from .opt_out_manager import OptOutReason

        # Add to centralized opt-out manager
        try:
            reason_enum = OptOutReason(reason)
        except ValueError:
            reason_enum = OptOutReason.MANUAL

        self.opt_out_manager.add_opt_out(
            phone=phone,
            reason=reason_enum,
            business_name=business_name
        )

        # Update any existing campaign records
        normalized = self._normalize_phone(phone)
        for record in self.campaigns.values():
            if self._normalize_phone(record.phone) == normalized:
                record.status = "opted_out"

        self._save_campaigns()
        logger.info(f"Added to opt-out: {phone} ({reason})")


def list_templates():
    """Print available SMS templates."""
    print("\n=== Available SMS Templates (Hormozi Framework) ===\n")
    for name, template in SMS_TEMPLATES.items():
        print(f"📱 {name}")
        print(f"   Body: {template['body'][:80]}...")
        print(f"   Chars: {template['char_count']}")
        pain_points = template.get('pain_points', [])
        print(f"   Best for: {', '.join(pain_points) if pain_points else 'Any lead'}")
        if template.get('notes'):
            print(f"   Notes: {template['notes']}")
        print()


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """CLI entry point for SMS outreach."""
    import argparse

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description="SMS Cold Outreach Campaign Manager")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Send command
    send_parser = subparsers.add_parser("send", help="Send SMS campaign")
    send_parser.add_argument("--dry-run", action="store_true", default=True, help="Preview without sending")
    send_parser.add_argument("--for-real", action="store_true", help="Actually send messages")
    send_parser.add_argument("--template", "-t", choices=list(SMS_TEMPLATES.keys()), help="Force specific template")
    send_parser.add_argument("--pain-point", "-p", help="Filter by pain point")
    send_parser.add_argument("--limit", "-l", type=int, default=100, help="Daily limit")
    send_parser.add_argument("--output-dir", "-o", default="output", help="Output directory")

    # Templates command
    templates_parser = subparsers.add_parser("templates", help="List available templates")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show campaign statistics")
    stats_parser.add_argument("--output-dir", "-o", default="output", help="Output directory")

    # Optout command
    optout_parser = subparsers.add_parser("optout", help="Add number to opt-out list")
    optout_parser.add_argument("phone", help="Phone number to opt out")
    optout_parser.add_argument("--reason", "-r", default="manual", help="Reason for opt-out (sms_stop, manual, etc)")
    optout_parser.add_argument("--business", "-b", default="", help="Business name")
    optout_parser.add_argument("--output-dir", "-o", default="output", help="Output directory")

    args = parser.parse_args()

    if args.command == "templates":
        list_templates()
        return

    if args.command == "stats":
        manager = SMSOutreachManager(output_dir=args.output_dir)
        stats = manager.get_campaign_stats()
        print("\n=== SMS Campaign Statistics ===")
        print(f"Total Messages: {stats['total_messages']}")
        print("\nBy Status:")
        for status, count in stats["by_status"].items():
            print(f"  {status}: {count}")
        print("\nBy Template:")
        for template, count in stats["by_template"].items():
            print(f"  {template}: {count}")
        return

    if args.command == "optout":
        manager = SMSOutreachManager(output_dir=args.output_dir)
        manager.add_optout(args.phone, reason=args.reason, business_name=args.business)
        print(f"Added to opt-out list: {args.phone}")
        print(f"  Reason: {args.reason}")
        if args.business:
            print(f"  Business: {args.business}")
        return

    if args.command == "send":
        # Load leads
        collection = LeadCollection(output_dir=args.output_dir)
        collection.load_json()

        leads = list(collection.leads.values())

        # Filter to leads with phones
        leads = [l for l in leads if l.phone]

        # Filter by pain point if specified
        if args.pain_point:
            leads = [l for l in leads if args.pain_point in l.pain_points]

        print(f"\nLoaded {len(leads)} leads with phone numbers")

        manager = SMSOutreachManager(output_dir=args.output_dir)

        dry_run = not args.for_real

        stats = manager.run_campaign(
            leads=leads[:args.limit],
            template_name=args.template,
            dry_run=dry_run,
            daily_limit=args.limit
        )

        print("\n=== Campaign Results ===")
        for key, value in stats.items():
            if key != "errors":
                print(f"  {key}: {value}")

        if stats["errors"]:
            print(f"\n  Errors: {len(stats['errors'])}")


if __name__ == "__main__":
    main()
