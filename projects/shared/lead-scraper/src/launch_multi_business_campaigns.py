#!/usr/bin/env python3
"""
Multi-Business Campaign Launcher

Launches parallel SMS campaigns for multiple businesses:
1. Southwest Florida Comfort (HVAC) - Voice AI for missed calls
2. Marceau Solutions - AI Automation for manual tasks

Features:
- Apollo MCP integration for lead discovery
- Lead scoring (1-10) based on pain point severity
- Top 20% enrichment via Apollo
- 3-touch follow-up sequences (Hormozi framework)
- Multi-tenant tracking (separate campaigns per business)

Usage:
    # Preview both campaigns (dry run)
    python -m src.launch_multi_business_campaigns --dry-run

    # Launch Southwest Florida Comfort only
    python -m src.launch_multi_business_campaigns --business swflorida-hvac --for-real

    # Launch Marceau Solutions only
    python -m src.launch_multi_business_campaigns --business marceau-solutions --for-real

    # Launch both campaigns
    python -m src.launch_multi_business_campaigns --for-real

    # Check campaign status
    python -m src.launch_multi_business_campaigns --status
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path)

from .models import Lead, LeadCollection
from .sms_outreach import SMSOutreachManager, SMS_TEMPLATES
from .follow_up_sequence import FollowUpSequenceManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# CAMPAIGN DEFINITIONS
# =============================================================================

CAMPAIGNS = {
    "swflorida-hvac": {
        "business_name": "Southwest Florida Comfort",
        "campaign_file": "output/campaigns/swfl_comfort_hvac_campaign.json",
        "target_industries": ["HVAC", "Air Conditioning", "Heating & Cooling"],
        "geography": "Naples, FL 50 mile radius",
        "initial_template": "hvac_voice_ai_intro",
        "lead_limit": 50,
        "budget_limit": 50.00
    },
    "marceau-solutions": {
        "business_name": "Marceau Solutions",
        "campaign_file": "output/campaigns/marceau_solutions_automation_campaign.json",
        "target_industries": ["Gyms", "Restaurants", "Medical Practices"],
        "geography": "Naples, FL 30 mile radius",
        "initial_template": "automation_intro",
        "lead_limit": 100,
        "budget_limit": 100.00
    }
}


# Add new templates for campaigns
NEW_TEMPLATES = {
    # HVAC Voice AI Templates
    "hvac_voice_ai_intro": {
        "body": "Hi, William from SW Florida Comfort. How many AC service calls do you miss after 5 PM? Our Voice AI answers 24/7. Want a free demo? (239) XXX-XXXX. Reply STOP to opt out.",
        "pain_points": ["missed_calls", "after_hours"],
        "char_count": 178,
        "business_id": "swflorida-hvac"
    },
    "hvac_voice_ai_followup_question": {
        "body": "Quick question for your HVAC business: How many customers call your competitor because you don't answer after hours? We solve this. (239) XXX-XXXX. Reply STOP to opt out.",
        "pain_points": ["missed_calls"],
        "char_count": 175,
        "business_id": "swflorida-hvac"
    },
    "hvac_voice_ai_breakup": {
        "body": "Last text - SW Florida Comfort. Only setting up 2 more HVAC businesses with Voice AI this month. Want 24/7 coverage? Text YES or call (239) XXX-XXXX. Reply STOP to opt out.",
        "pain_points": ["missed_calls"],
        "char_count": 185,
        "business_id": "swflorida-hvac"
    },

    # Marceau Solutions AI Automation Templates
    "automation_intro": {
        "body": "Hi, William from Marceau Solutions. How many hours do you spend each week on scheduling, emails, and follow-ups? Our AI automates this. Want a free audit? (239) 398-5676. Reply STOP to opt out.",
        "pain_points": ["manual_tasks", "time_waste"],
        "char_count": 197,
        "business_id": "marceau-solutions"
    },
    "automation_followup_question": {
        "body": "Quick question: If you could save 10+ hours/week on admin work, what would you do with that time? We automate scheduling, emails & more. (239) 398-5676. Reply STOP to opt out.",
        "pain_points": ["manual_tasks"],
        "char_count": 188,
        "business_id": "marceau-solutions"
    },
    "automation_breakup": {
        "body": "Final message - Marceau Solutions. Only taking 3 more automation clients this month. Want to save 10 hrs/week? Text YES or call (239) 398-5676. Reply STOP to opt out.",
        "pain_points": ["manual_tasks"],
        "char_count": 181,
        "business_id": "marceau-solutions"
    },

    # Segment-specific templates for Marceau Solutions
    "automation_gyms": {
        "body": "Hi, William from Marceau Solutions. Gym owners waste 12 hrs/week on member check-ins & follow-ups. Our AI handles this automatically. Free demo? (239) 398-5676. Reply STOP to opt out.",
        "pain_points": ["manual_tasks"],
        "char_count": 190,
        "business_id": "marceau-solutions"
    },
    "automation_restaurants": {
        "body": "Hi, William from Marceau Solutions. Restaurants lose $500/week from no-shows. Our AI sends automated reminders & confirmations. Want a demo? (239) 398-5676. Reply STOP to opt out.",
        "pain_points": ["no_shows"],
        "char_count": 185,
        "business_id": "marceau-solutions"
    },
    "automation_medical": {
        "body": "Hi, William from Marceau Solutions. Medical practices spend 20 hrs/week on appointment reminders. Our AI automates this 24/7. Free trial? (239) 398-5676. Reply STOP to opt out.",
        "pain_points": ["manual_tasks"],
        "char_count": 183,
        "business_id": "marceau-solutions"
    }
}

# Add templates to SMS_TEMPLATES
SMS_TEMPLATES.update(NEW_TEMPLATES)


class MultiBusinessCampaignLauncher:
    """
    Launches and manages campaigns for multiple businesses.

    Each business has:
    - Separate lead lists
    - Separate templates
    - Separate tracking
    - Separate follow-up sequences
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.campaigns_dir = self.output_dir / "campaigns"
        self.campaigns_dir.mkdir(parents=True, exist_ok=True)

        # Initialize managers
        self.sms_manager = SMSOutreachManager(output_dir=str(self.output_dir))
        self.sequence_manager = FollowUpSequenceManager(output_dir=str(self.output_dir))

        # Load leads
        self.leads_collection = LeadCollection(str(self.output_dir))
        try:
            self.leads_collection.load_json()
        except FileNotFoundError:
            logger.warning("No existing leads file - starting fresh")

    def discover_leads_apollo(
        self,
        business_id: str,
        industries: List[str],
        location: str,
        limit: int = 100
    ) -> List[Lead]:
        """
        Use Apollo MCP to discover leads.

        NOTE: This requires Apollo MCP to be running.
        For now, returns empty list - will integrate when Apollo MCP is available.
        """
        logger.info(f"[{business_id}] Apollo lead discovery not yet integrated")
        logger.info(f"  Industries: {industries}")
        logger.info(f"  Location: {location}")
        logger.info(f"  Limit: {limit}")

        # TODO: Integrate with Apollo MCP when available
        # For now, use existing leads or manual import

        return []

    def score_leads(
        self,
        leads: List[Lead],
        business_id: str
    ) -> List[Dict[str, Any]]:
        """
        Score leads 1-10 based on pain point severity and fit.

        Scoring factors vary by business:
        - HVAC: After-hours calls, competitor presence, business size
        - Automation: Manual processes, no website/booking, industry fit
        """
        scored_leads = []

        for lead in leads:
            score = 0
            reasons = []

            if business_id == "swflorida-hvac":
                # HVAC-specific scoring
                if "missed_calls" in lead.pain_points:
                    score += 3
                    reasons.append("High missed call rate")
                if lead.review_count > 50:
                    score += 2
                    reasons.append("Established business (50+ reviews)")
                if lead.competitor_name:
                    score += 2
                    reasons.append("Competitor present")
                if lead.website:
                    score += 1
                    reasons.append("Has website (likely tech-savvy)")

            elif business_id == "marceau-solutions":
                # Automation-specific scoring
                if "no_website" in lead.pain_points:
                    score += 3
                    reasons.append("No website (needs automation)")
                if "no_online_transactions" in lead.pain_points:
                    score += 3
                    reasons.append("No online booking (prime candidate)")
                if lead.review_count > 25:
                    score += 2
                    reasons.append("Successful business (25+ reviews)")
                if lead.category in ["Gyms", "Restaurants", "Medical"]:
                    score += 2
                    reasons.append("Prime industry for automation")

            scored_leads.append({
                "lead": lead,
                "score": min(score, 10),  # Cap at 10
                "reasons": reasons
            })

        # Sort by score descending
        scored_leads.sort(key=lambda x: x["score"], reverse=True)

        return scored_leads

    def enrich_top_leads(
        self,
        scored_leads: List[Dict[str, Any]],
        top_percent: float = 0.2
    ) -> List[Lead]:
        """
        Enrich top X% of leads via Apollo.

        For now, just returns the top leads without enrichment.
        TODO: Integrate Apollo enrichment API
        """
        top_count = max(1, int(len(scored_leads) * top_percent))
        top_leads = [item["lead"] for item in scored_leads[:top_count]]

        logger.info(f"Selected top {top_count} leads ({top_percent*100:.0f}%)")

        # TODO: Enrich via Apollo API
        # For now, just return top leads

        return top_leads

    def launch_campaign(
        self,
        business_id: str,
        dry_run: bool = True,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Launch a campaign for a specific business.

        Steps:
        1. Load campaign configuration
        2. Discover/filter leads
        3. Score leads
        4. Enrich top 20%
        5. Send initial outreach (Touch 1)
        6. Enroll in 3-touch follow-up sequence
        """
        if business_id not in CAMPAIGNS:
            raise ValueError(f"Unknown business: {business_id}")

        campaign_config = CAMPAIGNS[business_id]
        logger.info(f"\n{'='*60}")
        logger.info(f"Launching: {campaign_config['business_name']}")
        logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        logger.info(f"{'='*60}\n")

        # Load campaign file
        campaign_file = Path(campaign_config["campaign_file"])
        if not campaign_file.exists():
            logger.error(f"Campaign file not found: {campaign_file}")
            return {"status": "error", "reason": "Campaign file missing"}

        with open(campaign_file) as f:
            campaign_data = json.load(f)

        # Get leads (existing or Apollo discovery)
        leads = list(self.leads_collection.leads.values())

        # Filter by industry/geography if specified
        # (For now, using existing leads - will filter when Apollo integrated)

        # Score leads
        scored_leads = self.score_leads(leads, business_id)
        logger.info(f"Scored {len(scored_leads)} leads")

        # Show top 5 scored leads
        logger.info("\nTop 5 Scored Leads:")
        for item in scored_leads[:5]:
            logger.info(f"  {item['lead'].business_name} - Score: {item['score']}/10")
            logger.info(f"    Reasons: {', '.join(item['reasons'])}")

        # Enrich top 20%
        top_leads = self.enrich_top_leads(scored_leads)

        # Apply limit
        max_leads = limit or campaign_config["lead_limit"]
        target_leads = top_leads[:max_leads]

        logger.info(f"\nTargeting {len(target_leads)} leads for initial outreach")

        # Send initial outreach (Touch 1)
        stats = {
            "business_id": business_id,
            "business_name": campaign_config["business_name"],
            "total_targeted": len(target_leads),
            "sent": 0,
            "enrolled_in_sequence": 0,
            "errors": [],
            "dry_run": dry_run
        }

        template_name = campaign_config["initial_template"]

        for lead in target_leads:
            try:
                # Generate message
                message_body = self.sms_manager.generate_sms(lead, template_name)

                # Send SMS
                result = self.sms_manager.send_sms(
                    to_phone=lead.phone,
                    body=message_body,
                    dry_run=dry_run
                )

                if result["status"] in ["sent", "dry_run", "queued"]:
                    stats["sent"] += 1

                    # Enroll in follow-up sequence
                    self.sequence_manager.enroll_lead(lead, business_id=business_id)
                    stats["enrolled_in_sequence"] += 1

                    logger.info(f"  ✓ {lead.business_name} - {result['status']}")
                else:
                    stats["errors"].append(f"{lead.business_name}: {result.get('error')}")
                    logger.error(f"  ✗ {lead.business_name} - {result.get('error')}")

            except Exception as e:
                stats["errors"].append(f"{lead.business_name}: {str(e)}")
                logger.error(f"  ✗ {lead.business_name} - {e}")

        # Save campaign state
        campaign_data["status"] = "active" if not dry_run else "preview"
        campaign_data["launched_at"] = datetime.now().isoformat()
        campaign_data["stats"] = stats

        with open(campaign_file, 'w') as f:
            json.dump(campaign_data, f, indent=2)

        logger.info(f"\n{'='*60}")
        logger.info(f"Campaign Results: {campaign_config['business_name']}")
        logger.info(f"  Sent: {stats['sent']}/{stats['total_targeted']}")
        logger.info(f"  Enrolled in sequence: {stats['enrolled_in_sequence']}")
        logger.info(f"  Errors: {len(stats['errors'])}")
        logger.info(f"{'='*60}\n")

        return stats

    def get_campaign_status(self) -> Dict[str, Any]:
        """Get status of all campaigns."""
        status = {}

        for business_id, config in CAMPAIGNS.items():
            campaign_file = Path(config["campaign_file"])

            if campaign_file.exists():
                with open(campaign_file) as f:
                    data = json.load(f)
                    status[business_id] = {
                        "business_name": config["business_name"],
                        "status": data.get("status", "not_started"),
                        "launched_at": data.get("launched_at", ""),
                        "stats": data.get("stats", {})
                    }
            else:
                status[business_id] = {
                    "business_name": config["business_name"],
                    "status": "not_configured"
                }

        # Get follow-up sequence stats
        sequence_stats = self.sequence_manager.get_sequence_stats()
        status["follow_up_sequences"] = sequence_stats

        return status


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Multi-Business Campaign Launcher")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Preview without sending")
    parser.add_argument("--for-real", action="store_true", help="Actually send messages")
    parser.add_argument("--business", choices=["swflorida-hvac", "marceau-solutions"], help="Launch specific business only")
    parser.add_argument("--limit", type=int, help="Max leads per campaign")
    parser.add_argument("--status", action="store_true", help="Show campaign status")
    parser.add_argument("--output-dir", default="output", help="Output directory")

    args = parser.parse_args()

    launcher = MultiBusinessCampaignLauncher(output_dir=args.output_dir)

    if args.status:
        status = launcher.get_campaign_status()
        print(json.dumps(status, indent=2))
        return 0

    dry_run = not args.for_real

    # Launch campaigns
    results = {}

    if args.business:
        # Launch single business
        results[args.business] = launcher.launch_campaign(
            business_id=args.business,
            dry_run=dry_run,
            limit=args.limit
        )
    else:
        # Launch all businesses
        for business_id in CAMPAIGNS.keys():
            results[business_id] = launcher.launch_campaign(
                business_id=business_id,
                dry_run=dry_run,
                limit=args.limit
            )

    # Show summary
    print("\n" + "="*60)
    print("CAMPAIGN SUMMARY")
    print("="*60)
    for business_id, stats in results.items():
        print(f"\n{stats['business_name']}:")
        print(f"  Sent: {stats['sent']}/{stats['total_targeted']}")
        print(f"  Enrolled: {stats['enrolled_in_sequence']}")
        print(f"  Errors: {len(stats['errors'])}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
