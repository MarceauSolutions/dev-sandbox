#!/usr/bin/env python3
"""
Cold Outreach System - Hormozi-style email templates and campaign management.

Based on Alex Hormozi's cold outreach framework:
1. Rule of 100: 100 reachouts per day
2. Personalization: "Cocktail Party Effect" - look like a friend
3. Big Fast Value (BFV): Give away the farm in 30 seconds
4. Multi-channel follow-up: 5-7+ touchpoints
5. The "Still Looking" reactivation

Usage:
    python -m src.cold_outreach generate --template no_website --limit 50
    python -m src.cold_outreach send --dry-run
    python -m src.cold_outreach stats
"""

import os
import json
import logging
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from string import Template

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

from .models import Lead, LeadCollection
from .apollo import ApolloClient

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """SMTP configuration from environment."""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    sender_name: str = ""
    sender_email: str = ""

    @classmethod
    def from_env(cls) -> "EmailConfig":
        return cls(
            smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_username=os.getenv("SMTP_USERNAME", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            sender_name=os.getenv("SENDER_NAME", ""),
            sender_email=os.getenv("SENDER_EMAIL", "")
        )


@dataclass
class OutreachRecord:
    """Track outreach attempts to a lead."""
    lead_id: str
    email: str
    business_name: str
    owner_name: str
    template_used: str
    subject: str
    sent_at: str = ""
    status: str = "pending"  # pending, sent, bounced, replied, opted_out
    follow_up_count: int = 0
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# HORMOZI-STYLE EMAIL TEMPLATES
# =============================================================================

TEMPLATES = {
    # Template 1: No Website Pain Point
    "no_website": {
        "subject": "$business_name - Quick question about your online presence",
        "body": """Hi $first_name,

I noticed $business_name doesn't have a website yet. In Naples, over 80% of customers search online before visiting a gym.

I built a simple site for another local gym last month - they got 23 new members in the first 30 days.

Would you be open to a free mockup of what your site could look like? No strings attached - you can use it as a reference even if we never work together.

Takes me about 20 minutes to put together.

Best,
William
Marceau Solutions

P.S. - Here's what I did for Hardcore Gym: [link]
""",
        "pain_points": ["no_website", "outdated_website"],
        "category": "gym"
    },

    # Template 2: Few Reviews Pain Point
    "few_reviews": {
        "subject": "Getting more 5-star reviews for $business_name",
        "body": """Hi $first_name,

Saw $business_name on Yelp - looks like a great spot.

Quick thought: I noticed you have $review_count reviews. Most of your competitors have 50+.

I have a simple 3-step system that helped another Naples gym go from 12 reviews to 67 in 60 days. No fake reviews, no gimmicks - just making it stupid easy for happy members to leave one.

Want me to send you the exact steps? Takes 5 minutes to read.

Best,
William

P.S. - This works especially well for gyms because members are already on their phones between sets.
""",
        "pain_points": ["few_reviews", "no_reviews", "low_rating"],
        "category": "gym"
    },

    # Template 3: No Online Booking
    "no_booking": {
        "subject": "Let members book classes at $business_name online?",
        "body": """$first_name,

Quick question - do members currently have to call or walk in to book classes at $business_name?

If so, you're probably losing people who want to sign up at 11pm when they're motivated.

I set up online booking for a gym in Fort Myers - they saw a 34% increase in class attendance in the first month because members could book from their couch.

Would a 15-minute call be worth it to see if this could work for you?

William
""",
        "pain_points": ["no_online_booking", "no_online_transactions"],
        "category": "gym"
    },

    # Template 4: Competitor Callback (Hormozi favorite)
    "competitor_callback": {
        "subject": "Regarding $competitor_name",
        "body": """$first_name,

Calling about $competitor_name.

Give me a call back at your convenience: (555) 123-4567

William
""",
        "pain_points": [],  # Works for any lead
        "category": "gym",
        "notes": "Ultra short. Creates open loop. Best for voicemail/SMS follow-up."
    },

    # Template 5: Still Looking (9-word reactivation)
    "still_looking": {
        "subject": "Still looking to get more gym members?",
        "body": """Are you still looking to get more members at $business_name?

William
""",
        "pain_points": [],
        "category": "gym",
        "notes": "Use for dormant leads who didn't respond to initial outreach."
    },

    # Template 6: Big Fast Value - Free Audit
    "free_audit": {
        "subject": "Free marketing audit for $business_name (no pitch)",
        "body": """$first_name,

I put together a quick marketing audit for $business_name. Took me about 15 minutes.

Found 3 things you could fix today that would probably bring in more members:

1. [Specific observation about their online presence]
2. [Specific observation about reviews/ratings]
3. [Specific observation about social/booking]

Full audit is attached. Use it however you want - I'm not going to follow up with a sales pitch.

If you want to chat about implementing any of it, I'm around. If not, no worries.

William
""",
        "pain_points": [],
        "category": "gym",
        "notes": "Highest conversion but requires manual personalization."
    },

    # Template 7: Social Proof
    "social_proof": {
        "subject": "How [Other Naples Gym] got 40 new members last month",
        "body": """$first_name,

Not sure if you know [Other Gym Owner] over at [Other Naples Gym], but we helped them add 40 new members last month using a simple online system.

They were skeptical at first too - their words: "We've always done word of mouth."

But they gave it a shot, and now they're asking us to help with their second location.

Would you be open to a quick call to see if something similar could work for $business_name?

Either way, happy to share exactly what we did if you want to try it yourself.

William
""",
        "pain_points": [],
        "category": "gym"
    }
}


class ColdOutreachManager:
    """
    Manages cold email campaigns using Hormozi framework.

    Key principles:
    - Rule of 100: Volume negates luck
    - Personalization: 1-3 facts a friend would know
    - BFV: Give crazy value upfront
    - Multi-touch: 5-7 attempts before giving up
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.email_config = EmailConfig.from_env()
        self.apollo = ApolloClient()

        # Load existing campaign data
        self.campaigns_file = self.output_dir / "outreach_campaigns.json"
        self.campaigns: Dict[str, OutreachRecord] = {}
        self._load_campaigns()

    def _load_campaigns(self) -> None:
        """Load existing campaign records."""
        if self.campaigns_file.exists():
            with open(self.campaigns_file, 'r') as f:
                data = json.load(f)
                for record in data.get("records", []):
                    self.campaigns[record["lead_id"]] = OutreachRecord(**record)

    def _save_campaigns(self) -> None:
        """Save campaign records."""
        data = {
            "records": [r.to_dict() for r in self.campaigns.values()],
            "updated_at": datetime.now().isoformat()
        }
        with open(self.campaigns_file, 'w') as f:
            json.dump(data, f, indent=2)

    def enrich_lead_with_owner(self, lead: Lead) -> Optional[Dict[str, Any]]:
        """
        Use Apollo to find the owner/decision-maker for a lead.

        Returns dict with owner info if found.
        """
        if not lead.website:
            logger.warning(f"No website for {lead.business_name}, can't enrich")
            return None

        # Extract domain from website
        domain = lead.website.replace("https://", "").replace("http://", "").split("/")[0]

        # Search for decision makers
        decision_makers = self.apollo.find_decision_makers(
            company_domain=domain,
            titles=["owner", "founder", "ceo", "president", "general manager", "manager"]
        )

        if decision_makers:
            person = decision_makers[0]
            return {
                "first_name": person.get("first_name", ""),
                "last_name": person.get("last_name", ""),
                "email": person.get("email", ""),
                "title": person.get("title", ""),
                "linkedin": person.get("linkedin_url", "")
            }

        return None

    def generate_email(
        self,
        lead: Lead,
        template_name: str,
        owner_info: Optional[Dict[str, Any]] = None,
        custom_vars: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Generate personalized email from template.

        Applies Hormozi's "Cocktail Party Effect" - make it look like
        you know them with 1-3 personal facts.
        """
        template = TEMPLATES.get(template_name)
        if not template:
            raise ValueError(f"Unknown template: {template_name}")

        # Build substitution variables
        vars = {
            "business_name": lead.business_name,
            "city": lead.city or "Naples",
            "review_count": str(lead.review_count),
            "rating": str(lead.rating),
            "category": lead.category,
            "first_name": "there",  # Default if no owner found
            "competitor_name": "a competitor",  # Placeholder
        }

        # Add owner info if available
        if owner_info:
            vars["first_name"] = owner_info.get("first_name", "there")
            vars["owner_title"] = owner_info.get("title", "")
        elif lead.owner_name:
            vars["first_name"] = lead.owner_name.split()[0]  # First name only

        # Add custom overrides
        if custom_vars:
            vars.update(custom_vars)

        # Render template
        subject = Template(template["subject"]).safe_substitute(vars)
        body = Template(template["body"]).safe_substitute(vars)

        return {
            "subject": subject,
            "body": body,
            "template_name": template_name
        }

    def select_template_for_lead(self, lead: Lead) -> str:
        """
        Select best template based on lead's pain points.

        Priority:
        1. No website = highest opportunity
        2. Few reviews = easy quick win
        3. No online booking = clear pain point
        4. Default to social proof
        """
        pain_points = set(lead.pain_points)

        if "no_website" in pain_points or not lead.website:
            return "no_website"
        elif "no_reviews" in pain_points or lead.review_count == 0:
            return "few_reviews"
        elif "few_reviews" in pain_points or lead.review_count < 10:
            return "few_reviews"
        elif "no_online_booking" in pain_points or "no_online_transactions" in pain_points:
            return "no_booking"
        else:
            return "social_proof"

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        dry_run: bool = True
    ) -> bool:
        """
        Send email via SMTP.

        Args:
            to_email: Recipient email
            subject: Email subject
            body: Email body (plain text)
            dry_run: If True, just log without sending

        Returns:
            True if sent successfully
        """
        if dry_run:
            logger.info(f"[DRY RUN] Would send to: {to_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body:\n{body[:200]}...")
            return True

        if not self.email_config.smtp_username:
            logger.error("SMTP not configured. Set SMTP_* environment variables.")
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = f"{self.email_config.sender_name} <{self.email_config.sender_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(self.email_config.smtp_host, self.email_config.smtp_port) as server:
                server.starttls()
                server.login(self.email_config.smtp_username, self.email_config.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent to: {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def run_campaign(
        self,
        leads: List[Lead],
        template_name: Optional[str] = None,
        enrich: bool = True,
        dry_run: bool = True,
        daily_limit: int = 100,
        delay_seconds: float = 5.0
    ) -> Dict[str, Any]:
        """
        Run cold outreach campaign on a list of leads.

        Implements:
        - Rule of 100: Respects daily_limit
        - Personalization: Enriches with Apollo if enrich=True
        - Rate limiting: Delays between sends

        Args:
            leads: List of Lead objects
            template_name: Force specific template (or auto-select)
            enrich: Use Apollo to find owner emails
            dry_run: Preview without sending
            daily_limit: Max emails per run (Rule of 100)
            delay_seconds: Delay between emails

        Returns:
            Campaign statistics
        """
        stats = {
            "total_leads": len(leads),
            "processed": 0,
            "enriched": 0,
            "emails_generated": 0,
            "emails_sent": 0,
            "skipped_no_email": 0,
            "skipped_already_contacted": 0,
            "errors": []
        }

        for i, lead in enumerate(leads[:daily_limit]):
            if i > 0:
                time.sleep(delay_seconds)

            logger.info(f"Processing {i+1}/{min(len(leads), daily_limit)}: {lead.business_name}")

            # Skip if already contacted
            if lead.id in self.campaigns:
                stats["skipped_already_contacted"] += 1
                continue

            # Get owner info via Apollo
            owner_info = None
            email = lead.email

            if enrich and lead.website:
                owner_info = self.enrich_lead_with_owner(lead)
                if owner_info and owner_info.get("email"):
                    email = owner_info["email"]
                    stats["enriched"] += 1

            # Skip if no email available
            if not email:
                stats["skipped_no_email"] += 1
                continue

            # Select template
            template = template_name or self.select_template_for_lead(lead)

            # Generate email
            email_content = self.generate_email(lead, template, owner_info)
            stats["emails_generated"] += 1

            # Send email
            success = self.send_email(
                to_email=email,
                subject=email_content["subject"],
                body=email_content["body"],
                dry_run=dry_run
            )

            if success:
                stats["emails_sent"] += 1

                # Record outreach
                record = OutreachRecord(
                    lead_id=lead.id,
                    email=email,
                    business_name=lead.business_name,
                    owner_name=owner_info.get("first_name", "") if owner_info else "",
                    template_used=template,
                    subject=email_content["subject"],
                    sent_at=datetime.now().isoformat() if not dry_run else "",
                    status="sent" if not dry_run else "pending"
                )
                self.campaigns[lead.id] = record

            stats["processed"] += 1

        # Save campaign data
        self._save_campaigns()

        return stats

    def get_campaign_stats(self) -> Dict[str, Any]:
        """Get overall campaign statistics."""
        stats = {
            "total_contacts": len(self.campaigns),
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

    def generate_follow_up_list(self, days_since_contact: int = 3) -> List[OutreachRecord]:
        """
        Get leads that need follow-up (no reply after X days).

        Hormozi says most give up after 1.3 attempts - we do 5-7.
        """
        from datetime import datetime, timedelta

        cutoff = datetime.now() - timedelta(days=days_since_contact)
        follow_ups = []

        for record in self.campaigns.values():
            if record.status == "sent" and record.follow_up_count < 5:
                if record.sent_at:
                    sent_date = datetime.fromisoformat(record.sent_at)
                    if sent_date < cutoff:
                        follow_ups.append(record)

        return follow_ups


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """CLI entry point for cold outreach."""
    import argparse

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description="Cold Outreach Campaign Manager")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate emails for leads")
    gen_parser.add_argument("--template", "-t", choices=list(TEMPLATES.keys()), help="Force specific template")
    gen_parser.add_argument("--pain-point", "-p", help="Filter by pain point")
    gen_parser.add_argument("--limit", "-l", type=int, default=10, help="Number of leads to process")
    gen_parser.add_argument("--enrich", action="store_true", help="Enrich with Apollo")
    gen_parser.add_argument("--output-dir", "-o", default="output", help="Output directory")

    # Send command
    send_parser = subparsers.add_parser("send", help="Send email campaign")
    send_parser.add_argument("--dry-run", action="store_true", default=True, help="Preview without sending")
    send_parser.add_argument("--for-real", action="store_true", help="Actually send emails")
    send_parser.add_argument("--limit", "-l", type=int, default=100, help="Daily limit (Rule of 100)")
    send_parser.add_argument("--output-dir", "-o", default="output", help="Output directory")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show campaign statistics")
    stats_parser.add_argument("--output-dir", "-o", default="output", help="Output directory")

    # Templates command
    templates_parser = subparsers.add_parser("templates", help="List available templates")

    args = parser.parse_args()

    if args.command == "templates":
        print("\n=== Available Email Templates ===\n")
        for name, template in TEMPLATES.items():
            print(f"📧 {name}")
            print(f"   Subject: {template['subject'][:60]}...")
            print(f"   Pain Points: {template.get('pain_points', 'Any')}")
            print(f"   Notes: {template.get('notes', 'General use')}")
            print()
        return

    if args.command == "stats":
        manager = ColdOutreachManager(output_dir=args.output_dir)
        stats = manager.get_campaign_stats()
        print("\n=== Campaign Statistics ===")
        print(f"Total Contacts: {stats['total_contacts']}")
        print("\nBy Status:")
        for status, count in stats["by_status"].items():
            print(f"  {status}: {count}")
        print("\nBy Template:")
        for template, count in stats["by_template"].items():
            print(f"  {template}: {count}")
        return

    if args.command in ["generate", "send"]:
        # Load leads
        collection = LeadCollection(output_dir=args.output_dir)
        collection.load_json()

        leads = list(collection.leads.values())

        # Filter by pain point if specified
        if hasattr(args, 'pain_point') and args.pain_point:
            leads = [l for l in leads if args.pain_point in l.pain_points]

        print(f"\nLoaded {len(leads)} leads")

        manager = ColdOutreachManager(output_dir=args.output_dir)

        dry_run = True
        if hasattr(args, 'for_real') and args.for_real:
            dry_run = False

        stats = manager.run_campaign(
            leads=leads[:args.limit],
            template_name=getattr(args, 'template', None),
            enrich=getattr(args, 'enrich', False),
            dry_run=dry_run,
            daily_limit=args.limit
        )

        print("\n=== Campaign Results ===")
        for key, value in stats.items():
            if key != "errors":
                print(f"{key}: {value}")

        if stats["errors"]:
            print(f"\nErrors: {len(stats['errors'])}")


if __name__ == "__main__":
    main()
