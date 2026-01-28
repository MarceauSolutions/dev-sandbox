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
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
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
    sending_business_id: str = ""  # NEW: Which business sent this (marceau-solutions, swflorida-hvac, shipping-logistics)
    message_sid: str = ""
    sent_at: str = ""
    status: str = "pending"  # pending, sent, delivered, failed, opted_out
    error_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# BUSINESS-SPECIFIC TEMPLATE MAPPINGS
# =============================================================================
# Each business can only use templates relevant to their services
# Prevents sending HVAC offers to website leads, or website offers to shipping leads

BUSINESS_TEMPLATE_MAP = {
    "marceau-solutions": {
        "allowed_templates": [
            # No website templates (ONLY for verified no-website leads)
            "no_website_intro",
            "no_website_v2_compliant",
            "no_website_followup_question",
            "no_website_followup_breakup",
            # Aggregator only (has Yelp/Facebook but no real site)
            "aggregator_only_intro",
            "aggregator_google_ranking",
            # Few reviews templates
            "few_reviews",
            "few_reviews_v2",
            "few_reviews_system",
            "few_reviews_v2_compliant",
            "few_reviews_followup_question",
            "few_reviews_followup_breakup",
            # Low rating templates
            "low_rating_recovery",
            "low_rating_reputation",
            # Franchise templates (for locally-owned chain locations)
            "franchise_intro",
            "franchise_member_retention",
            "franchise_operations",
            # Apollo B2B templates (fitness industry owners)
            "apollo_b2b_intro",
            "apollo_b2b_followup_question",
            "apollo_b2b_followup_breakup",
            "apollo_decision_maker",
            "apollo_automation_offer",
            # Online transactions templates
            "no_online_transactions",
            "no_online_transactions_v2",
            "online_booking_offer",
            "no_online_transactions_v2_compliant",
            "no_online_transactions_followup_question",
            "no_online_transactions_followup_breakup",
            # General templates
            "competitor_hook",
            "social_proof",
            "still_looking"
        ],
        "business_name": "Marceau Solutions",
        "phone": "(239) 398-5676",
        "services": ["AI automation", "website development", "online booking", "review systems"]
    },
    "swflorida-hvac": {
        "allowed_templates": [
            "hvac_maintenance",
            "hvac_energy_savings",
            "hvac_followup_question",
            "hvac_followup_breakup"
        ],
        "business_name": "SW Florida Comfort HVAC",
        "phone": "(239) XXX-XXXX",  # TODO: Add real phone
        "services": ["HVAC maintenance", "AC repair", "energy savings", "commercial HVAC"]
    },
    "shipping-logistics": {
        "allowed_templates": [
            "shipping_cost_savings",
            "shipping_fulfillment_speed",
            "shipping_followup_question",
            "shipping_followup_breakup"
        ],
        "business_name": "Shipping Solutions",
        "phone": "(239) XXX-XXXX",  # TODO: Add real phone
        "services": ["shipping cost reduction", "faster fulfillment", "carrier optimization"]
    }
}


# =============================================================================
# SMS TEMPLATES - Updated 2026-01-22
# =============================================================================
# Keep messages under 160 chars when possible (single SMS segment)
# Always include opt-out language for compliance
#
# LESSONS LEARNED:
# - Lead with discovery questions, not product pitches
# - "Automation" umbrella > specific products (voice AI, websites)
# - Avoid confusing messaging (competitor_hook was terrible)
# - Be clear about what we're offering

SMS_TEMPLATES = {
    # =============================================================================
    # PRIMARY TEMPLATES - DISCOVERY FOCUSED (Use these first)
    # =============================================================================
    # Our niche: Finding problems clients don't know they have, and building
    # better solutions than what they originally asked for.

    # Discovery question - works for any business (RECOMMENDED)
    "discovery_question": {
        "body": "Hi, this is William. Quick Q for $business_name - what's taking up most of your time that you wish you could hand off? Curious if I can help. Reply STOP to opt out.",
        "pain_points": [],
        "char_count": 172,
        "notes": "PRIMARY - Pure discovery, no pitch. Opens conversation."
    },

    # Consultant positioning - emphasizes we diagnose first
    "consultant_intro": {
        "body": "Hi, William here. I help local businesses find where they're leaking time and money - then fix it with automation. Worth a quick chat? Reply STOP to opt out.",
        "pain_points": [],
        "char_count": 163,
        "notes": "Positions us as consultants, not vendors. Discovery-first."
    },

    # Gap finder - our specialty
    "gap_finder": {
        "body": "Hi, this is William. I specialize in finding gaps in business operations that owners don't know exist. Quick call to see if I can spot anything for $business_name? Reply STOP to opt out.",
        "pain_points": [],
        "char_count": 189,
        "notes": "Emphasizes our specialty - finding hidden problems"
    },

    # Better solution angle - for clients who think they know what they need
    "better_solution": {
        "body": "Hi, William here. I work with businesses who have a problem in mind - then build something better than what they originally asked for. Open to a quick chat? Reply STOP to opt out.",
        "pain_points": [],
        "char_count": 183,
        "notes": "For clients who already have an idea - we make it better"
    },

    # =============================================================================
    # SECONDARY TEMPLATES - AUTOMATION FOCUSED
    # =============================================================================

    # Time-saving angle - universal pain point
    "automation_time_saver": {
        "body": "Hi, William here. I help local businesses automate the repetitive stuff - follow-ups, scheduling, inquiries. Worth a quick chat? -William. Reply STOP to opt out.",
        "pain_points": [],
        "char_count": 168,
        "notes": "General automation pitch - clear value prop"
    },

    # Direct automation offer
    "automation_direct": {
        "body": "Hi, this is William. I build AI systems that handle customer follow-ups, booking, and inquiries 24/7. Interested in seeing how it works? Reply STOP to opt out.",
        "pain_points": [],
        "char_count": 167,
        "notes": "Direct automation offer - specific capabilities"
    },

    # Legacy alias (keep for backwards compatibility)
    "automation_discovery": {
        "body": "Hi, this is William. Quick Q for $business_name - what's taking up most of your time that you wish you could hand off? Curious if I can help. Reply STOP to opt out.",
        "pain_points": [],
        "char_count": 172,
        "notes": "ALIAS for discovery_question - use discovery_question instead"
    },

    # =============================================================================
    # LEGACY TEMPLATES - WEBSITE/REVIEW FOCUSED (Still valid for specific pain points)
    # =============================================================================

    # Template 1: No Website - Direct Value Offer
    "no_website_intro": {
        "body": "Hi, this is William. I noticed $business_name doesn't have a website. 80% of customers search online first. Want a free mockup? Reply STOP to opt out.",
        "pain_points": ["no_website"],
        "char_count": 158,
        "notes": "For leads without websites - specific pain point"
    },

    # DEPRECATED - competitor_hook caused confusion (Inhale Exhale 2026-01-22)
    # "competitor_hook" - REMOVED: Message was confusing ("gym near your spa got members")
    # Lesson: Don't use competitor references that don't make sense for the business type

    # =============================================================================
    # INDUSTRY-SPECIFIC AUTOMATION TEMPLATES
    # =============================================================================

    # Wellness/Spa specific
    "wellness_automation": {
        "body": "Hi, this is William. For wellness businesses like $business_name - do you have automated rebooking reminders for past clients? Can help with that. Reply STOP to opt out.",
        "pain_points": ["wellness", "spa"],
        "char_count": 174,
        "notes": "Wellness/spa specific - rebooking angle"
    },

    # Fitness/Gym specific
    "fitness_automation": {
        "body": "Hi, William here. Quick Q for $business_name - what happens when someone misses a class or their membership lapses? I automate that follow-up. Reply STOP to opt out.",
        "pain_points": ["fitness", "gym"],
        "char_count": 174,
        "notes": "Fitness specific - retention angle"
    },

    # Service business (HVAC, plumbing, etc)
    "service_business_automation": {
        "body": "Hi, this is William. For service businesses like $business_name - do you have automated follow-ups after jobs? Helps get reviews + repeat business. Reply STOP to opt out.",
        "pain_points": ["service_business"],
        "char_count": 178,
        "notes": "Service business - post-job automation"
    },

    # =============================================================================
    # FOLLOW-UP SEQUENCE (Automation focused)
    # =============================================================================

    # Follow-up 1: Still interested
    "automation_followup_1": {
        "body": "Hey, William again. Still curious if automation could help $business_name? No pressure - just thought I'd check. Reply STOP to opt out.",
        "pain_points": [],
        "char_count": 139,
        "notes": "Follow-up 1 - soft check-in"
    },

    # Follow-up 2: Specific value
    "automation_followup_2": {
        "body": "Hi $business_name - most businesses I work with save 5-10 hrs/week once we automate their follow-ups. Worth a quick call? Reply STOP to opt out.",
        "pain_points": [],
        "char_count": 151,
        "notes": "Follow-up 2 - time savings angle"
    },

    # Follow-up 3: Breakup
    "automation_breakup": {
        "body": "Should I stop texting about automation for $business_name? If so, no worries - just ignore this. If not, text back. -William. Reply STOP to opt out.",
        "pain_points": [],
        "char_count": 155,
        "notes": "Follow-up 3 - permission to stop (gets highest responses)"
    },

    # =============================================================================
    # LEGACY TEMPLATES - REVIEW/WEBSITE FOCUSED
    # =============================================================================

    # Template 3: Few Reviews - Quick Win
    "few_reviews": {
        "body": "Hi, saw $business_name has $review_count reviews. I helped another Naples gym go from 12 to 67 reviews in 60 days. Interested? Reply STOP to opt out.",
        "pain_points": ["few_reviews", "no_reviews"],
        "char_count": 155,
        "notes": "Targets review pain point"
    },

    # Template 4: Still Looking (9-word reactivation) - UPDATED to be more general
    "still_looking": {
        "body": "Still interested in automating some of the busywork at $business_name? -William. Reply STOP to opt out.",
        "pain_points": [],
        "char_count": 102,
        "notes": "Follow-up for non-responders - now automation focused"
    },

    # Template 5: Social Proof - UPDATED to automation focus
    "social_proof": {
        "body": "Just helped a Naples business automate their customer follow-ups - saved them 8 hrs/week. Want to know how? -William. Reply STOP to opt out.",
        "pain_points": [],
        "char_count": 147,
        "notes": "Leads with social proof - automation angle"
    },

    # Template 6: Direct Question - UPDATED to automation
    "direct_question": {
        "body": "Quick Q for $business_name - do you have automated follow-ups for leads and customers? If not, I can set that up. -William. Reply STOP to opt out.",
        "pain_points": [],
        "char_count": 154,
        "notes": "Opens conversation - automation focus"
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
    },

    # =============================================================================
    # APOLLO B2B TEMPLATES (Decision-Maker Outreach - Fitness Industry)
    # =============================================================================
    # These templates use first_name personalization for B2B decision makers
    # Source: Apollo.io leads with verified contact info
    # Variables: $first_name, $business_name, $title

    # Initial B2B outreach - personal and direct
    "apollo_b2b_intro": {
        "body": "Hi $first_name, this is William. I help fitness business owners automate member follow-ups and booking. Curious if that's on your radar? Reply STOP to opt out.",
        "pain_points": ["apollo_b2b"],
        "char_count": 167,
        "notes": "Apollo leads - personal B2B intro, no claims"
    },

    # Decision maker angle - respects their role
    "apollo_decision_maker": {
        "body": "Hi $first_name, saw you run $business_name. Quick question - how do you currently handle member retention follow-ups? -William. Reply STOP to opt out.",
        "pain_points": ["apollo_b2b"],
        "char_count": 159,
        "notes": "Apollo leads - question hook for decision makers"
    },

    # Automation value proposition
    "apollo_automation_offer": {
        "body": "Hi $first_name, I build AI systems that handle member outreach for gyms (texts, emails, reminders). Saves 10+ hrs/week. Worth a quick call? Reply STOP to opt out.",
        "pain_points": ["apollo_b2b"],
        "char_count": 172,
        "notes": "Apollo leads - concrete value proposition"
    },

    # Apollo follow-up question (Touch 2)
    "apollo_b2b_followup_question": {
        "body": "$first_name - William again. Quick question: what % of your no-shows and cancellations get a follow-up text? (239) 398-5676. Reply STOP to opt out.",
        "pain_points": ["apollo_b2b"],
        "char_count": 153,
        "notes": "Apollo B2B follow-up - pain point question"
    },

    # Apollo breakup (Touch 3)
    "apollo_b2b_followup_breakup": {
        "body": "Last text $first_name - only taking 3 more automation clients this month. If interested in saving 10+ hrs/week on member outreach, text YES. Reply STOP to opt out.",
        "pain_points": ["apollo_b2b"],
        "char_count": 172,
        "notes": "Apollo B2B breakup - scarcity + exit"
    },

    # =============================================================================
    # FRANCHISE TEMPLATES (For locally-owned chain locations)
    # =============================================================================
    # These DO NOT make false claims about missing websites
    # Focus on automation, member retention, and operational efficiency

    "franchise_intro": {
        "body": "Hi, this is William. I help local fitness owners like $business_name automate no-show follow-ups and boost member retention. Worth a quick chat? Reply STOP to opt out.",
        "pain_points": ["franchise"],
        "char_count": 172,
        "notes": "For franchises - no website claims, focus on automation"
    },

    "franchise_member_retention": {
        "body": "Hi, $business_name owner? I've helped 5 Naples gyms boost retention 20% with automated member follow-ups. Interested? -William. Reply STOP to opt out.",
        "pain_points": ["franchise"],
        "char_count": 159,
        "notes": "For franchises - social proof + retention focus"
    },

    "franchise_operations": {
        "body": "Hi, quick Q for $business_name: Do you have automated texts for missed appointments and membership renewals? Can set that up. -William. Reply STOP to opt out.",
        "pain_points": ["franchise"],
        "char_count": 168,
        "notes": "For franchises - operational pain point"
    },

    # =============================================================================
    # FEW REVIEWS TEMPLATES (5-10 reviews)
    # =============================================================================

    "few_reviews_v2": {
        "body": "Hi, this is William. Noticed $business_name has solid ratings but could use more reviews. I helped a local gym 5x their Google reviews in 60 days. Interested? Reply STOP to opt out.",
        "pain_points": ["few_reviews"],
        "char_count": 189,
        "notes": "Few reviews - social proof angle"
    },

    "few_reviews_system": {
        "body": "Hi $business_name - most gyms leave reviews to chance. I build automated systems that ask happy members at the right time. Want details? -William. Reply STOP to opt out.",
        "pain_points": ["few_reviews"],
        "char_count": 173,
        "notes": "Few reviews - system offer"
    },

    # =============================================================================
    # LOW RATING TEMPLATES (Under 3.5 stars)
    # =============================================================================

    "low_rating_recovery": {
        "body": "Hi, this is William. Saw $business_name has room to improve ratings. I help businesses recover by getting more 5-star reviews to balance things out. Chat? Reply STOP to opt out.",
        "pain_points": ["low_rating"],
        "char_count": 183,
        "notes": "Low rating - recovery focus, not critical"
    },

    "low_rating_reputation": {
        "body": "Hi, $business_name - 70% of customers won't visit if ratings are under 4 stars. I help local gyms fix that fast. Want to know how? -William. Reply STOP to opt out.",
        "pain_points": ["low_rating"],
        "char_count": 168,
        "notes": "Low rating - urgency with stat"
    },

    # =============================================================================
    # NO/FEW ONLINE TRANSACTIONS TEMPLATES
    # =============================================================================

    "no_online_transactions_v2": {
        "body": "Hi, this is William. Quick Q: Can members at $business_name book classes or buy packages online? If not, I can help set that up. Reply STOP to opt out.",
        "pain_points": ["no_online_transactions"],
        "char_count": 160,
        "notes": "Online transactions - question hook"
    },

    "online_booking_offer": {
        "body": "Hi, $business_name - I help gyms add online booking that works with their schedule. Members love it, owners save time. Interested? -William. Reply STOP to opt out.",
        "pain_points": ["no_online_transactions"],
        "char_count": 172,
        "notes": "Online transactions - value focus"
    },

    # =============================================================================
    # AGGREGATOR ONLY TEMPLATES (Has Yelp/Facebook but no real website)
    # =============================================================================

    "aggregator_only_intro": {
        "body": "Hi, saw $business_name on Yelp but couldn't find your own website. Having one helps you control your brand. Want a free mockup? -William. Reply STOP to opt out.",
        "pain_points": ["aggregator_only"],
        "char_count": 166,
        "notes": "Aggregator - validates they have online presence, offers upgrade"
    },

    "aggregator_google_ranking": {
        "body": "Hi, $business_name shows on Google Maps but competitors with websites rank higher. Want to level the playing field? -William. Reply STOP to opt out.",
        "pain_points": ["aggregator_only"],
        "char_count": 157,
        "notes": "Aggregator - SEO angle"
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
                        'message_body', 'sending_business_id', 'message_sid', 'sent_at', 'status', 'error_message'
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

    def validate_template_for_business(self, business_id: str, template_name: str) -> None:
        """
        Validate that a template is allowed for a business.

        Args:
            business_id: Business sending the campaign (marceau-solutions, swflorida-hvac, shipping-logistics)
            template_name: Template to validate

        Raises:
            ValueError: If template not allowed for this business
        """
        if business_id not in BUSINESS_TEMPLATE_MAP:
            logger.warning(f"Unknown business_id: {business_id}. Defaulting to marceau-solutions.")
            business_id = "marceau-solutions"

        allowed_templates = BUSINESS_TEMPLATE_MAP[business_id]["allowed_templates"]

        if template_name not in allowed_templates:
            business_name = BUSINESS_TEMPLATE_MAP[business_id]["business_name"]
            raise ValueError(
                f"Template '{template_name}' is not allowed for {business_name}. "
                f"Allowed templates: {', '.join(allowed_templates)}"
            )

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
        # Handle first_name with fallback
        first_name = getattr(lead, 'first_name', '') or ''
        if not first_name and lead.owner_name:
            first_name = lead.owner_name.split()[0]
        if not first_name:
            first_name = "there"

        vars = {
            "business_name": lead.business_name[:30],  # Truncate for SMS length
            "city": lead.city or "Naples",
            "review_count": str(lead.review_count),
            "rating": str(lead.rating),
            # Apollo B2B fields
            "first_name": first_name,
            "last_name": getattr(lead, 'last_name', '') or '',
            "title": getattr(lead, 'title', '') or '',
        }

        if custom_vars:
            vars.update(custom_vars)

        # Render template
        body = Template(template["body"]).safe_substitute(vars)

        return body

    def select_template_for_lead(self, lead: Lead, use_optimizer: bool = True) -> str:
        """
        Select best SMS template based on lead's pain points.

        Uses outreach optimizer for A/B testing when available.

        CRITICAL: Match templates to VERIFIED pain points only.
        - franchise → franchise templates (no website claims)
        - no_website → no_website templates (verified no site)
        - aggregator_only → aggregator templates (has Yelp but no site)
        - low_rating → rating recovery templates
        - few_reviews → review templates
        """
        pain_points = set(lead.pain_points)

        # Try to use optimizer for A/B testing
        if use_optimizer:
            try:
                from .outreach_optimizer import OutreachOptimizer
                optimizer = OutreachOptimizer(output_dir=str(self.output_dir))

                if "apollo_b2b" in pain_points or getattr(lead, 'source', '') == 'apollo':
                    return optimizer.select_template_for_lead("apollo")
                else:
                    return optimizer.select_template_for_lead("google_places")
            except Exception as e:
                logger.debug(f"Optimizer not available, using default: {e}")

        # Priority-based template selection (most specific first)

        # 1. Apollo B2B leads (decision-maker outreach)
        if "apollo_b2b" in pain_points or getattr(lead, 'source', '') == 'apollo':
            return "apollo_b2b_intro"

        # 2. Franchises - NEVER claim they don't have a website
        if "franchise" in pain_points:
            return "franchise_intro"

        # 3. Aggregator only (has Yelp/Facebook but no real website)
        if "aggregator_only" in pain_points:
            return "aggregator_only_intro"

        # 4. Truly no website (verified by website_validator)
        if "no_website" in pain_points:
            return "no_website_intro"

        # 5. Low rating (under 3.5 stars)
        if "low_rating" in pain_points:
            return "low_rating_recovery"

        # 6. No online transactions
        if "no_online_transactions" in pain_points:
            return "no_online_transactions_v2"

        # 7. Few or no reviews
        if "no_reviews" in pain_points or "few_reviews" in pain_points or lead.review_count < 10:
            return "few_reviews"

        # 8. Default - generic value hook
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
        delay_seconds: float = 2.0,
        business_id: str = "marceau-solutions"  # NEW: Which business is sending (marceau-solutions, swflorida-hvac, shipping-logistics)
    ) -> Dict[str, Any]:
        """
        Run SMS campaign on a list of leads.

        Args:
            leads: List of Lead objects
            template_name: Force specific template (or auto-select)
            dry_run: Preview without sending
            daily_limit: Max messages per run
            delay_seconds: Delay between messages
            business_id: Which business is sending this campaign

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

            # Validate template matches business_id (BUSINESS-SPECIFIC VALIDATION)
            try:
                self.validate_template_for_business(business_id, template)
            except ValueError as e:
                stats["errors"].append(f"Template validation error for {lead.business_name}: {e}")
                logger.error(f"  {e}")
                continue

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
                    sending_business_id=business_id,  # Track which business sent this
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
