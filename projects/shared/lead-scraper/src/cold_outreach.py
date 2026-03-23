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
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from string import Template

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path)

from .models import Lead, LeadCollection
from .apollo import ApolloClient

# Import image generator (optional - only if XAI_API_KEY is set)
try:
    from .outreach_image_generator import OutreachImageGenerator
    IMAGE_GEN_AVAILABLE = True
except ImportError:
    IMAGE_GEN_AVAILABLE = False

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
# DISCOVERY-FOCUSED EMAIL TEMPLATES
#
# Our niche: We specialize in two things:
# 1. Finding problems clients don't know they have
# 2. Building better solutions than what clients originally asked for
#
# These templates lead with DISCOVERY, not product pitches.
# =============================================================================

TEMPLATES = {
    # ==========================================================================
    # PRIMARY TEMPLATES - DISCOVERY FOCUSED (Use these first)
    # ==========================================================================

    # Template 1: Pure Discovery Question (PRIMARY - recommended)
    "discovery_question": {
        "subject": "Quick question for $business_name",
        "body": """Hi $first_name,

I work with local businesses in Naples to find where they're leaking time or money - then fix it with automation.

Quick question: What's taking up most of your time that you wish you could hand off to someone else?

Not trying to pitch you anything - genuinely curious if there's something I could help with.

William
Marceau Solutions
(239) 398-5676
""",
        "pain_points": [],
        "category": "general",
        "notes": "PRIMARY - Pure discovery, no pitch. Opens conversation."
    },

    # Template 2: Consultant Intro
    "consultant_intro": {
        "subject": "Automation question for $business_name",
        "body": """Hi $first_name,

I'm William - I work with local businesses to find gaps in their operations that they don't even know exist.

Most of my clients didn't know what they needed until we talked. I just ask questions and see if there's a fit.

Would a quick 10-minute chat be worth it to see if there's something I could help with at $business_name?

No pitch, no pressure. If there's no fit, I'll tell you honestly.

William
Marceau Solutions
(239) 398-5676
""",
        "pain_points": [],
        "category": "general",
        "notes": "Positions us as consultants who discover problems, not vendors pushing products."
    },

    # Template 3: Gap Finder
    "gap_finder": {
        "subject": "Noticed something about $business_name",
        "body": """Hi $first_name,

I specialize in finding operational gaps that business owners don't know they have.

Running a $category like $business_name, there are usually 2-3 things leaking time or money that you've just gotten used to dealing with.

Would you be open to a quick call where I ask a few questions? If I don't find anything worth fixing, I'll tell you straight up.

No sales pitch - I only work with businesses where I can actually help.

William
Marceau Solutions
(239) 398-5676
""",
        "pain_points": [],
        "category": "general",
        "notes": "Emphasizes our specialty - finding hidden problems."
    },

    # Template 4: Better Solution (for leads who mentioned a specific need)
    "better_solution": {
        "subject": "Re: Your $category operations",
        "body": """Hi $first_name,

I work with businesses who have a problem in mind - then build something more comprehensive than what they originally asked for.

Most of my clients come to me thinking they need X, and we discover that the real solution is Y (which solves 3 more problems they didn't even realize they had).

If you've got something you're trying to fix at $business_name, I'd be happy to take a look and see if there's a bigger picture solution.

Worth a quick chat?

William
Marceau Solutions
(239) 398-5676
""",
        "pain_points": [],
        "category": "general",
        "notes": "For clients who already have an idea - we make it better."
    },

    # ==========================================================================
    # INDUSTRY-SPECIFIC TEMPLATES (Use after discovery fails)
    # ==========================================================================

    # Template 5: Wellness/Spa Automation
    "wellness_automation": {
        "subject": "Automation question for $business_name",
        "body": """Hi $first_name,

I help wellness businesses automate the stuff that eats up their day - client follow-ups, appointment reminders, rebooking sequences.

Quick question: What's the most repetitive task at $business_name that you wish would just handle itself?

Not pitching anything specific - I'm curious what's actually a pain point for you.

William
Marceau Solutions
(239) 398-5676
""",
        "pain_points": ["wellness", "spa"],
        "category": "wellness",
        "notes": "Discovery-focused for wellness/spa businesses."
    },

    # Template 6: Fitness Automation
    "fitness_automation": {
        "subject": "Quick question for $business_name",
        "body": """Hi $first_name,

I work with gyms and fitness studios to automate the time-consuming stuff - lead follow-up, member check-ins, reactivation sequences.

Curious: If you could wave a magic wand and automate ONE thing at $business_name, what would it be?

Not trying to sell you anything - just seeing if there's a fit.

William
Marceau Solutions
(239) 398-5676
""",
        "pain_points": ["gym", "fitness"],
        "category": "gym",
        "notes": "Discovery-focused for fitness businesses."
    },

    # Template 7: Service Business Automation
    "service_automation": {
        "subject": "Automation question for $business_name",
        "body": """Hi $first_name,

I work with service businesses to automate customer follow-ups, scheduling, and lead response.

Quick question: What's eating up the most time at $business_name right now?

Most business owners I talk to have at least one thing they'd love to hand off. Curious what yours is.

William
Marceau Solutions
(239) 398-5676
""",
        "pain_points": ["service", "hvac", "plumbing", "contractor"],
        "category": "service",
        "notes": "Discovery-focused for service businesses."
    },

    # ==========================================================================
    # MISSED CALL / AI ANSWERING TEMPLATES
    # Offer: AI that answers missed calls, sends automated follow-up texts,
    # and books appointments — targeting Naples FL service businesses.
    #
    # These are industry-specific hooks tied to the REAL pain point:
    # owner-operators who miss revenue when they can't answer the phone
    # while on a job, under a house, or after hours.
    # ==========================================================================

    # Template A: HVAC / Plumbing — emergency call urgency
    "hvac_missed_call": {
        "subject": "HVAC calls you can't answer",
        "body": """Hi $first_name,

Quick question: when you're on a job and your phone rings with a new HVAC call — what happens to that customer if you can't pick up?

Most service techs lose those leads to whoever answers first. I built a system that answers the call, texts the customer back within 60 seconds, and puts them on your schedule automatically.

Would it be worth a 10-minute call to see if it makes sense for $business_name?

William Marceau
Marceau Solutions — Naples, FL
(239) 398-5676
""",
        "pain_points": ["hvac", "plumbing", "service"],
        "category": "hvac",
        "notes": "For HVAC/plumbing — hooks on the missed call while on a job scenario."
    },

    # Template B: Electrical — residential service calls
    "electrical_missed_call": {
        "subject": "Missed calls while on a job",
        "body": """Hi $first_name,

Running an electrical business solo or with a small crew means your phone rings while both hands are busy.

I help Naples electricians set up a system that automatically answers missed calls, texts the customer back immediately, and books them directly into your calendar — so you don't lose jobs while you're on one.

Is that something that would save you headaches at $business_name?

William Marceau
Marceau Solutions — Naples, FL
(239) 398-5676
""",
        "pain_points": ["electrical", "service"],
        "category": "electrical",
        "notes": "For electrical contractors — missed calls while on a job site."
    },

    # Template C: Roofing — storm season inbound volume
    "roofing_missed_call": {
        "subject": "Storm season call volume — $business_name",
        "body": """Hi $first_name,

In Naples, storm season brings a wave of inbound calls — and the roofers who respond fastest win those jobs.

I set up a system for local roofers that answers every missed call automatically, texts the homeowner within 60 seconds, and books an estimate on your calendar. No staff needed.

Worth a quick call to see if it fits how $business_name works?

William Marceau
Marceau Solutions — Naples, FL
(239) 398-5676
""",
        "pain_points": ["roofing", "service"],
        "category": "roofing",
        "notes": "For roofing — storm season call volume hook."
    },

    # Template D: Pool service — scheduling and new customer calls
    "pool_missed_call": {
        "subject": "New pool customers calling $business_name",
        "body": """Hi $first_name,

Pool service owners I talk to in Naples say the same thing — they miss new customer calls when they're in the middle of a service route.

I built a simple system that handles those calls automatically: answers, texts back, and gets them scheduled without you picking up the phone.

Would that be useful for $business_name?

William Marceau
Marceau Solutions — Naples, FL
(239) 398-5676
""",
        "pain_points": ["pool"],
        "category": "pool",
        "notes": "For pool service — on-route missed call scenario."
    },

    # Template E: General contractor / home services — referral + new call mix
    "contractor_missed_call": {
        "subject": "Leads that don't leave a message",
        "body": """Hi $first_name,

Most homeowners who call a contractor and don't get an answer just call the next one on the list. They don't leave a message.

I help local contractors set up a system that responds to every missed call automatically — a quick text goes out within 60 seconds, keeps the lead warm, and books them into your schedule.

Would it be worth 10 minutes to see if it makes sense for $business_name?

William Marceau
Marceau Solutions — Naples, FL
(239) 398-5676
""",
        "pain_points": ["contractor", "construction", "general"],
        "category": "contractor",
        "notes": "For general contractors / home services — lead lost to competitor hook."
    },

    # ==========================================================================
    # FOLLOW-UP TEMPLATES
    # ==========================================================================

    # Template 8: Still Looking (9-word reactivation)
    "still_looking": {
        "subject": "Still looking to streamline things at $business_name?",
        "body": """Are you still looking to free up time at $business_name?

William
""",
        "pain_points": [],
        "category": "general",
        "notes": "Use for dormant leads who didn't respond to initial outreach."
    },

    # Template 9: Check-in Follow-up
    "followup_checkin": {
        "subject": "Following up - $business_name",
        "body": """Hi $first_name,

Just following up on my last message. Totally understand if you're busy running $business_name.

If there's ever something eating up your time that you think automation could help with, I'm around.

No pressure either way.

William
Marceau Solutions
""",
        "pain_points": [],
        "category": "general",
        "notes": "Soft follow-up for non-responders."
    },

    # Template 10: Breakup Email
    "breakup": {
        "subject": "Closing the loop - $business_name",
        "body": """Hi $first_name,

I've reached out a few times about automation for $business_name, but haven't heard back.

No worries at all - I know timing isn't always right.

I'm going to stop reaching out, but if you ever want to chat about freeing up time at $business_name, just reply to this email.

Wishing you the best!

William
Marceau Solutions
""",
        "pain_points": [],
        "category": "general",
        "notes": "Final touch - respectful close."
    },

    # ==========================================================================
    # DEPRECATED TEMPLATES (Kept for backwards compatibility)
    # ==========================================================================

    # DEPRECATED - Too product-focused, caused confusion
    "no_website": {
        "subject": "$business_name - Quick question about your online presence",
        "body": """Hi $first_name,

I noticed $business_name doesn't have a website yet. In Naples, over 80% of customers search online before visiting.

Quick question: Is that something you've been meaning to tackle, or is it just not a priority right now?

Either way is fine - I'm curious what's working for you.

William
Marceau Solutions
(239) 398-5676
""",
        "pain_points": ["no_website", "outdated_website"],
        "category": "general",
        "notes": "DEPRECATED - Still starts with discovery question but more specific."
    },

    # DEPRECATED - Too specific about reviews
    "few_reviews": {
        "subject": "Quick question about $business_name",
        "body": """Hi $first_name,

I help local businesses with the operational stuff - automating follow-ups, getting more reviews, that kind of thing.

Curious: What's taking up the most time at $business_name right now?

Not pitching anything - just seeing if there's something I could help with.

William
Marceau Solutions
(239) 398-5676
""",
        "pain_points": ["few_reviews", "no_reviews", "low_rating"],
        "category": "general",
        "notes": "DEPRECATED - Leads with discovery, not review pitch."
    },

    # DEPRECATED - Original booking template
    "no_booking": {
        "subject": "Let members book at $business_name online?",
        "body": """$first_name,

Quick question - what's the most time-consuming part of handling bookings at $business_name?

I work with businesses to automate the repetitive stuff - scheduling, follow-ups, reminders.

If that's not a pain point for you, no worries. But if it is, worth a quick chat.

William
Marceau Solutions
""",
        "pain_points": ["no_online_booking", "no_online_transactions"],
        "category": "general",
        "notes": "DEPRECATED - Discovery-focused booking template."
    },

    # DEPRECATED - Competitor callback (confusing, caused issues)
    "competitor_callback": {
        "subject": "Quick call - $business_name",
        "body": """$first_name,

I had a quick question about $business_name - worth a 5-minute call?

(239) 398-5676

William
""",
        "pain_points": [],
        "category": "general",
        "notes": "DEPRECATED - Ultra short. Creates open loop."
    },

    # DEPRECATED - Too product-focused
    "apollo_voice_ai": {
        "subject": "Quick question for $business_name",
        "body": """Hi $first_name,

I work with businesses to automate the repetitive stuff - customer follow-ups, appointment handling, lead response.

Curious: What's eating up the most time at $business_name that you wish would just handle itself?

If there's a fit, I'll share some ideas. If not, no pitch.

William
Marceau Solutions
(239) 398-5676
""",
        "pain_points": ["apollo_b2b"],
        "category": "general",
        "source": "apollo",
        "notes": "DEPRECATED - Replaced with discovery-focused approach."
    },

    # DEPRECATED - Too specific about retention
    "apollo_retention": {
        "subject": "Quick question about $business_name",
        "body": """$first_name,

I help businesses automate their customer follow-up and retention systems.

What's the biggest operational challenge at $business_name right now?

Always curious what's actually a pain point vs. what I assume is a pain point.

William
Marceau Solutions
""",
        "pain_points": ["apollo_b2b"],
        "category": "general",
        "source": "apollo",
        "notes": "DEPRECATED - Discovery-focused retention template."
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

        # Initialize image generator if available
        self.image_generator = None
        if IMAGE_GEN_AVAILABLE:
            try:
                self.image_generator = OutreachImageGenerator()
                logger.info("Image generation enabled via Grok/xAI")
            except Exception as e:
                logger.warning(f"Image generation disabled: {e}")

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
            vars["title"] = owner_info.get("title", "run")
        elif lead.owner_name:
            vars["first_name"] = lead.owner_name.split()[0]  # First name only

        # Add title if available on lead (for Apollo leads)
        if hasattr(lead, 'title') and lead.title:
            vars["title"] = lead.title

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
        Select best template based on lead's category and pain points.

        Our niche: Discovery-focused consulting.
        Lead with discovery questions, not product pitches.

        Priority:
        1. Industry-specific discovery template (if available)
        2. General discovery template
        3. Fallback to generic consultant intro
        """
        category = (lead.category or "").lower()
        pain_points = set(lead.pain_points)

        # Industry-specific discovery templates
        if any(term in category for term in ["wellness", "spa", "massage", "salon"]):
            return "wellness_automation"
        elif any(term in category for term in ["gym", "fitness", "yoga", "pilates", "crossfit"]):
            return "fitness_automation"
        elif any(term in category for term in ["hvac", "plumbing", "contractor", "service", "repair"]):
            return "service_automation"

        # Apollo-sourced leads with verified contact info
        if "apollo_b2b" in pain_points:
            return "consultant_intro"

        # Default: Pure discovery question (our primary template)
        return "discovery_question"

    def generate_image_for_lead(
        self,
        lead: Lead,
        template_name: str,
        output_dir: str = "mockups"
    ) -> Optional[str]:
        """
        Generate a personalized mockup image for a lead.

        Args:
            lead: The lead to generate image for
            template_name: Template being used (determines image type)
            output_dir: Directory to save images

        Returns:
            Path to generated image or None
        """
        if not self.image_generator:
            logger.warning("Image generation not available (XAI_API_KEY not set)")
            return None

        # Map template to pain point for image generation
        pain_point_map = {
            "no_website": "no_website",
            "few_reviews": "few_reviews",
            "no_booking": "no_online_booking",
            "social_proof": "no_website"  # Default mockup
        }

        pain_point = pain_point_map.get(template_name, "no_website")

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Safe filename
        safe_name = "".join(c if c.isalnum() else "_" for c in lead.business_name.lower())
        image_path = output_path / f"{safe_name}_mockup.png"

        try:
            result = self.image_generator.generate_mockup(
                business_name=lead.business_name,
                pain_point=pain_point,
                industry=lead.category or "default",
                output_path=str(image_path)
            )
            return result
        except Exception as e:
            logger.error(f"Failed to generate image for {lead.business_name}: {e}")
            return None

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        dry_run: bool = True,
        image_path: Optional[str] = None
    ) -> bool:
        """
        Send email via SMTP.

        Args:
            to_email: Recipient email
            subject: Email subject
            body: Email body (plain text)
            dry_run: If True, just log without sending
            image_path: Optional path to image attachment (e.g., mockup)

        Returns:
            True if sent successfully
        """
        if dry_run:
            logger.info(f"[DRY RUN] Would send to: {to_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body:\n{body[:200]}...")
            if image_path:
                logger.info(f"Image attachment: {image_path}")
            return True

        if not self.email_config.smtp_username:
            logger.error("SMTP not configured. Set SMTP_* environment variables.")
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = f"{self.email_config.sender_name} <{self.email_config.sender_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            # Attach body text
            msg.attach(MIMEText(body, 'plain'))

            # Attach image if provided
            if image_path and Path(image_path).exists():
                with open(image_path, 'rb') as f:
                    img = MIMEImage(f.read())
                    img.add_header('Content-Disposition', 'attachment', filename=Path(image_path).name)
                    msg.attach(img)
                logger.info(f"Attached image: {image_path}")

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

                # Register for unified response monitoring (if not dry run)
                if not dry_run:
                    self._register_for_unified_tracking(lead, email, email_content, template)

            stats["processed"] += 1

        # Save campaign data
        self._save_campaigns()

        return stats

    def _register_for_unified_tracking(
        self,
        lead: Lead,
        email: str,
        email_content: Dict[str, str],
        template: str
    ) -> None:
        """Register outreach for unified response monitoring across all projects."""
        try:
            import sys
            # Path: projects/shared/lead-scraper/src/ -> projects/shared/lead-scraper/ -> projects/shared/ -> projects/ -> dev-sandbox/
            execution_path = Path(__file__).parent.parent.parent.parent.parent / 'execution'
            sys.path.insert(0, str(execution_path))
            from email_response_monitor import EmailResponseMonitor

            # Determine project based on template/category
            project = 'lead-scraper'
            if 'gym' in template or 'fitness' in lead.category.lower():
                project = 'fitness'
            elif 'website' in template:
                project = 'website-builder'

            monitor = EmailResponseMonitor()
            monitor.register_outreach(
                inquiry_id=lead.id,
                project=project,
                recipient_email=email,
                recipient_name=lead.owner_name or lead.business_name,
                subject=email_content["subject"],
                inquiry_type='cold_outreach',
                metadata={
                    'business_name': lead.business_name,
                    'template': template,
                    'category': lead.category,
                    'pain_points': lead.pain_points,
                }
            )
            logger.info(f"Registered cold outreach {lead.id} for unified tracking")
        except Exception as e:
            logger.warning(f"Failed to register for unified tracking: {e}")

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

    def send_followups(self, dry_run: bool = True, daily_limit: int = 100, delay_seconds: float = 3.0) -> Dict[str, Any]:
        """
        Process due follow-up emails for non-responding leads.
        Touch sequence (Hormozi):
          count 0->1: Day 3  — followup_checkin (soft check-in)
          count 1->2: Day 7  — social_proof (case study angle)
          count 2->3: Day 14 — direct_question (wrong inbox?)
          count 3->4: Day 21 — breakup (close the file)
        """
        from datetime import datetime, timedelta

        TOUCH_MAP = {
            0: ("followup_checkin",        3),
            1: ("social_proof_followup",   7),
            2: ("direct_question_followup", 14),
            3: ("breakup",                 21),
        }
        INLINE_TEMPLATES = {
            "social_proof_followup": {
                "subject": "Re: $business_name",
                "body": (
                    "Hi $first_name,\n\n"
                    "Wanted to follow up in case my last message got buried.\n\n"
                    "I've been helping local Naples businesses automate the repetitive stuff — one HVAC "
                    "company cut their missed-call follow-up time from 2 days to under 5 minutes. A med "
                    "spa owner saved 8 hours a week in her first month.\n\n"
                    "If there's something like that hiding at $business_name, I'd love to find it.\n\n"
                    "Worth a quick 15-minute call?\n\nWilliam\nMarceau Solutions\n(239) 398-5676"
                ),
            },
            "direct_question_followup": {
                "subject": "Did this land in the wrong inbox? — $business_name",
                "body": (
                    "Hi $first_name,\n\n"
                    "I've reached out a couple of times — just want to make sure this isn't lost in a "
                    "spam folder or going to the wrong person at $business_name.\n\n"
                    "If you're not the right contact, just let me know who handles operations and I'll "
                    "reach out to them instead. If the timing isn't right, say the word and I'll stop.\n\n"
                    "William\nMarceau Solutions\n(239) 398-5676"
                ),
            },
        }

        stats = {"total_due": 0, "sent": 0, "skipped": 0, "errors": [], "dry_run": dry_run}

        for record in list(self.campaigns.values()):
            touch = record.follow_up_count
            if touch not in TOUCH_MAP or record.status != "sent":
                continue
            template_name, min_days = TOUCH_MAP[touch]
            if not record.sent_at:
                continue
            last_dt = datetime.fromisoformat(record.sent_at)
            if datetime.now() - last_dt < timedelta(days=min_days):
                continue

            stats["total_due"] += 1
            if stats["sent"] >= daily_limit:
                stats["skipped"] += 1
                continue

            tmpl = INLINE_TEMPLATES.get(template_name) or TEMPLATES.get(template_name)
            if not tmpl:
                logger.warning(f"Unknown follow-up template: {template_name}")
                stats["skipped"] += 1
                continue

            first_name = (record.owner_name.split()[0] if record.owner_name else "there")
            subject = Template(tmpl["subject"]).safe_substitute(
                business_name=record.business_name, first_name=first_name)
            body = Template(tmpl["body"]).safe_substitute(
                business_name=record.business_name, first_name=first_name)

            logger.info(f"[Touch {touch+1}] {record.business_name} → {record.email} | {template_name}")
            success = self.send_email(record.email, subject, body, dry_run=dry_run)
            if success:
                stats["sent"] += 1
                if not dry_run:
                    record.follow_up_count += 1
                    record.sent_at = datetime.now().isoformat()
                    self._save_campaigns()
                time.sleep(delay_seconds)
            else:
                stats["errors"].append(record.email)

        return stats


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
    gen_parser.add_argument("--leads-file", help="Custom leads JSON file (default: leads.json)")
    gen_parser.add_argument("--output-dir", "-o", default="output", help="Output directory")

    # Send command
    send_parser = subparsers.add_parser("send", help="Send email campaign")
    send_parser.add_argument("--dry-run", action="store_true", default=True, help="Preview without sending")
    send_parser.add_argument("--for-real", action="store_true", help="Actually send emails")
    send_parser.add_argument("--limit", "-l", type=int, default=100, help="Daily limit (Rule of 100)")
    send_parser.add_argument("--leads-file", help="Custom leads JSON file (default: leads.json)")
    send_parser.add_argument("--template", "-t", choices=list(TEMPLATES.keys()), help="Force specific template")
    send_parser.add_argument("--output-dir", "-o", default="output", help="Output directory")

    # Follow-up command
    followup_parser = subparsers.add_parser("followup", help="Send follow-up emails to non-responding leads")
    followup_parser.add_argument("--dry-run", action="store_true", default=True, help="Preview without sending")
    followup_parser.add_argument("--for-real", action="store_true", help="Actually send follow-ups")
    followup_parser.add_argument("--limit", "-l", type=int, default=100, help="Daily limit")
    followup_parser.add_argument("--output-dir", "-o", default="output", help="Output directory")

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

    if args.command == "followup":
        manager = ColdOutreachManager(output_dir=args.output_dir)
        dry_run = not getattr(args, 'for_real', False)
        result = manager.send_followups(dry_run=dry_run, daily_limit=args.limit)
        print("\n=== Follow-Up Results ===")
        print(f"Total due:  {result['total_due']}")
        print(f"Sent:       {result['sent']}")
        print(f"Skipped:    {result['skipped']}")
        print(f"Errors:     {len(result['errors'])}")
        print(f"Mode:       {'DRY RUN' if dry_run else 'LIVE'}")
        if result['errors']:
            print(f"Failed addresses: {result['errors']}")
        return

    if args.command in ["generate", "send"]:
        # Load leads - either from custom file or default leads.json
        leads_file = getattr(args, 'leads_file', None)
        if leads_file:
            # Load from custom file (e.g., Apollo leads)
            import json
            leads_path = Path(args.output_dir) / leads_file if not Path(leads_file).is_absolute() else Path(leads_file)
            with open(leads_path, 'r') as f:
                data = json.load(f)
            leads_data = data.get('leads', data) if isinstance(data, dict) else data
            leads = []
            for ld in leads_data:
                lead = Lead(
                    id=ld.get('id', ''),
                    source=ld.get('source', 'custom'),
                    business_name=ld.get('business_name', ''),
                    owner_name=ld.get('owner_name', ''),
                    email=ld.get('email', ''),
                    phone=ld.get('phone', ''),
                    website=ld.get('website', ''),
                    address=ld.get('address', ''),
                    city=ld.get('city', ''),
                    state=ld.get('state', ''),
                    category=ld.get('category', ''),
                    rating=ld.get('rating', 0),
                    review_count=ld.get('review_count', 0),
                    pain_points=ld.get('pain_points', []),
                    notes=ld.get('notes', ''),
                    scraped_at=ld.get('scraped_at', '')
                )
                # Add extra fields for templates
                lead.first_name = ld.get('first_name', lead.owner_name.split()[0] if lead.owner_name else '')
                lead.title = ld.get('title', '')
                leads.append(lead)
            print(f"\nLoaded {len(leads)} leads from {leads_file}")
        else:
            # Default: load from leads.json
            collection = LeadCollection(output_dir=args.output_dir)
            collection.load_json()
            leads = list(collection.leads.values())
            print(f"\nLoaded {len(leads)} leads")

        # Filter by pain point if specified
        if hasattr(args, 'pain_point') and args.pain_point:
            leads = [l for l in leads if args.pain_point in l.pain_points]

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
