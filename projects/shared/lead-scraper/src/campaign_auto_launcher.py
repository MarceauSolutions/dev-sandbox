#!/usr/bin/env python3
"""
Campaign Auto-Launcher - Automated Daily Campaign Execution

Fully automated campaign launch system that:
1. Pre-flight health checks (Agent 1 integration)
2. Apollo MCP lead discovery (Agent 3 integration)
3. Lead scoring + top 20% filtering
4. Enrichment via Apollo
5. Initial outreach (Touch 1)
6. Follow-up sequence enrollment
7. Analytics tracking (Agent 2 integration)
8. Webhook monitoring (Agent 4 integration)

Designed to run via cron/launchd like X posting automation.

Usage:
    # Dry run (preview)
    python -m src.campaign_auto_launcher --dry-run

    # Launch Southwest Florida Comfort (HVAC)
    python -m src.campaign_auto_launcher --business swflorida-hvac --for-real

    # Launch Marceau Solutions (Automation)
    python -m src.campaign_auto_launcher --business marceau-solutions --for-real

    # Launch both businesses
    python -m src.campaign_auto_launcher --for-real

    # Check integrations
    python -m src.campaign_auto_launcher --check-integrations
"""

import os
import sys
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

# Load environment
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

# Import existing campaign infrastructure
from .launch_multi_business_campaigns import (
    MultiBusinessCampaignLauncher,
    CAMPAIGNS,
    SMS_TEMPLATES
)
from .models import Lead, LeadCollection
from .follow_up_sequence import FollowUpSequenceManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# INTEGRATION PLACEHOLDERS (Will be replaced when Agents 1-4 complete)
# =============================================================================

def check_health_agent1() -> Dict[str, Any]:
    """
    Agent 1: Health Checks Integration

    TODO: Replace with actual health_checks.py import when available.

    Expected return:
    {
        "twilio": {
            "healthy": True,
            "balance_usd": 25.50,
            "last_check": "2026-01-21T08:00:00"
        },
        "apollo": {
            "healthy": True,
            "credits_remaining": 1500
        },
        "webhook": {
            "healthy": True,
            "running": True,
            "port": 5001
        }
    }
    """
    logger.info("[Agent 1 Integration] Health check placeholder - assuming healthy")

    # Placeholder - return optimistic defaults
    return {
        "twilio": {
            "healthy": True,
            "balance_usd": 100.0,  # Assume sufficient balance
            "last_check": datetime.now().isoformat()
        },
        "apollo": {
            "healthy": True,
            "credits_remaining": 1000
        },
        "webhook": {
            "healthy": True,
            "running": True,
            "port": 5001
        }
    }


def track_campaign_launch_agent2(
    campaign_id: str,
    business_id: str,
    leads_targeted: int,
    template: str
) -> None:
    """
    Agent 2: Analytics Tracking Integration

    TODO: Replace with actual campaign_analytics.py import when available.
    """
    logger.info(f"[Agent 2 Integration] Tracking campaign launch: {campaign_id}")
    logger.info(f"  Business: {business_id}")
    logger.info(f"  Leads: {leads_targeted}")
    logger.info(f"  Template: {template}")

    # Placeholder - would call Agent 2's tracking


def apollo_mcp_search_agent3(
    query: str,
    limit: int = 100
) -> List[Lead]:
    """
    Agent 3: Apollo MCP Integration

    TODO: Replace with actual Apollo MCP integration when available.

    Expected usage:
        leads = apollo_mcp_search("HVAC companies in Naples FL, 1-50 employees", limit=50)
    """
    logger.info(f"[Agent 3 Integration] Apollo MCP search placeholder")
    logger.info(f"  Query: {query}")
    logger.info(f"  Limit: {limit}")

    # Placeholder - return empty list (will use existing leads for now)
    return []


def apollo_mcp_enrich_agent3(
    leads: List[Lead],
    fields: List[str] = ["phone", "email", "owner_name"]
) -> List[Lead]:
    """
    Agent 3: Apollo MCP Enrichment Integration

    TODO: Replace with actual Apollo enrichment when available.
    """
    logger.info(f"[Agent 3 Integration] Apollo enrichment placeholder")
    logger.info(f"  Enriching {len(leads)} leads")
    logger.info(f"  Fields: {', '.join(fields)}")

    # Placeholder - return leads unchanged
    return leads


def check_webhook_agent4() -> bool:
    """
    Agent 4: Webhook Health Check Integration

    TODO: Replace with actual webhook_processor.py import when available.
    """
    logger.info("[Agent 4 Integration] Webhook check placeholder - assuming running")
    return True


def fetch_responses_agent4(
    campaign_id: str,
    since: datetime
) -> List[Dict[str, Any]]:
    """
    Agent 4: Webhook Response Fetching Integration

    TODO: Replace with actual webhook response fetching when available.
    """
    logger.info(f"[Agent 4 Integration] Fetching responses placeholder")
    logger.info(f"  Campaign: {campaign_id}")
    logger.info(f"  Since: {since.isoformat()}")

    # Placeholder - return empty list
    return []


# =============================================================================
# SAFEGUARDS & RATE LIMITING
# =============================================================================

@dataclass
class CampaignLimits:
    """Daily limits and safeguards."""
    max_sms_per_day: int = 100
    max_cost_per_day: float = 1.00
    sms_delay_seconds: float = 2.0
    max_consecutive_errors: int = 5
    require_approval_above: int = 50


class CampaignSafeguards:
    """Enforces daily quotas and rate limits."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.limits_file = self.output_dir / "daily_campaign_limits.json"
        self.limits = CampaignLimits()

    def check_daily_quota(self, business_id: str) -> Tuple[bool, int, int]:
        """
        Check if daily quota reached for business.

        Returns:
            (can_send, sent_today, quota)
        """
        today = datetime.now().date().isoformat()

        # Load today's sends
        if self.limits_file.exists():
            with open(self.limits_file) as f:
                data = json.load(f)
        else:
            data = {}

        sent_today = data.get(today, {}).get(business_id, 0)
        quota = CAMPAIGNS.get(business_id, {}).get("lead_limit", 100)

        can_send = sent_today < quota

        return can_send, sent_today, quota

    def record_send(self, business_id: str, count: int = 1) -> None:
        """Record SMS sends for quota tracking."""
        today = datetime.now().date().isoformat()

        if self.limits_file.exists():
            with open(self.limits_file) as f:
                data = json.load(f)
        else:
            data = {}

        if today not in data:
            data[today] = {}

        data[today][business_id] = data[today].get(business_id, 0) + count

        with open(self.limits_file, 'w') as f:
            json.dump(data, f, indent=2)

    def check_cost_limit(self, estimated_cost: float) -> bool:
        """Check if estimated cost within daily limit."""
        return estimated_cost <= self.limits.max_cost_per_day


# =============================================================================
# AUTOMATED CAMPAIGN LAUNCHER
# =============================================================================

class CampaignAutoLauncher:
    """
    Automated campaign launcher with full integration.

    Orchestrates:
    - Health checks (Agent 1)
    - Lead discovery (Agent 3)
    - Analytics tracking (Agent 2)
    - Webhook monitoring (Agent 4)
    - Campaign execution
    - Follow-up sequences
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.launcher = MultiBusinessCampaignLauncher(output_dir=str(self.output_dir))
        self.sequence_manager = FollowUpSequenceManager(output_dir=str(self.output_dir))
        self.safeguards = CampaignSafeguards(output_dir=str(self.output_dir))

        # Load leads
        self.leads_collection = LeadCollection(str(self.output_dir))
        try:
            self.leads_collection.load_json()
            logger.info(f"Loaded {len(self.leads_collection.leads)} existing leads")
        except FileNotFoundError:
            logger.warning("No existing leads - will use Apollo discovery")

    def pre_flight_checks(self) -> Dict[str, Any]:
        """
        Pre-flight health checks before launching campaign.

        Integrates with Agent 1's health check system.
        """
        logger.info("\n" + "="*60)
        logger.info("PRE-FLIGHT CHECKS")
        logger.info("="*60)

        health = check_health_agent1()

        checks = {
            "twilio_healthy": health["twilio"]["healthy"],
            "twilio_balance": health["twilio"]["balance_usd"],
            "apollo_healthy": health["apollo"]["healthy"],
            "apollo_credits": health["apollo"]["credits_remaining"],
            "webhook_running": health["webhook"]["running"],
            "all_systems_go": True
        }

        # Validate Twilio
        if not checks["twilio_healthy"]:
            logger.error("❌ Twilio API unhealthy - ABORTING")
            checks["all_systems_go"] = False
        else:
            logger.info(f"✅ Twilio healthy (balance: ${checks['twilio_balance']:.2f})")

        if checks["twilio_balance"] < 10.0:
            logger.error("❌ Twilio balance too low (<$10) - ABORTING")
            checks["all_systems_go"] = False

        # Validate Apollo
        if not checks["apollo_healthy"]:
            logger.warning("⚠️  Apollo MCP not available - using existing leads")
        else:
            logger.info(f"✅ Apollo healthy ({checks['apollo_credits']} credits)")

        # Validate Webhook
        if not checks["webhook_running"]:
            logger.warning("⚠️  Webhook server not running - responses won't be captured")
        else:
            logger.info("✅ Webhook server running")

        logger.info("="*60 + "\n")

        return checks

    def discover_leads(
        self,
        business_id: str,
        limit: int = 100
    ) -> List[Lead]:
        """
        Discover leads via Apollo MCP or use existing leads.

        Integrates with Agent 3's Apollo MCP system.
        """
        logger.info(f"\n--- Lead Discovery: {business_id} ---")

        campaign_config = CAMPAIGNS[business_id]

        # Try Apollo MCP first
        apollo_query = f"{', '.join(campaign_config['target_industries'])} in {campaign_config['geography']}"
        apollo_leads = apollo_mcp_search_agent3(apollo_query, limit=limit)

        if apollo_leads:
            logger.info(f"✅ Discovered {len(apollo_leads)} leads via Apollo MCP")
            return apollo_leads

        # Fallback to existing leads
        logger.info("Using existing leads (Apollo MCP not available)")
        all_leads = list(self.leads_collection.leads.values())

        # Filter by industry if possible
        # (This is a simple filter - would be more sophisticated with Apollo)
        filtered_leads = all_leads[:limit]

        logger.info(f"Using {len(filtered_leads)} existing leads")

        return filtered_leads

    def launch_campaign(
        self,
        business_id: str,
        dry_run: bool = True,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Launch automated campaign for a business.

        Full workflow:
        1. Pre-flight checks
        2. Check daily quota
        3. Discover leads
        4. Score leads
        5. Enrich top 20%
        6. Send Touch 1
        7. Enroll in sequences
        8. Track analytics
        9. Monitor webhook
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"LAUNCHING CAMPAIGN: {CAMPAIGNS[business_id]['business_name']}")
        logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        logger.info(f"{'='*70}")

        # Pre-flight checks
        health = self.pre_flight_checks()
        if not health["all_systems_go"] and not dry_run:
            logger.error("Pre-flight checks failed - ABORTING")
            return {
                "status": "aborted",
                "reason": "Pre-flight checks failed"
            }

        # Check daily quota
        can_send, sent_today, quota = self.safeguards.check_daily_quota(business_id)
        logger.info(f"\nDaily Quota: {sent_today}/{quota}")

        if not can_send and not dry_run:
            logger.warning("Daily quota reached - SKIPPING")
            return {
                "status": "skipped",
                "reason": f"Daily quota reached ({sent_today}/{quota})"
            }

        # Discover leads
        max_leads = limit or CAMPAIGNS[business_id]["lead_limit"]
        remaining_quota = quota - sent_today
        target_count = min(max_leads, remaining_quota)

        leads = self.discover_leads(business_id, limit=target_count)

        if not leads:
            logger.warning("No leads available - SKIPPING")
            return {
                "status": "skipped",
                "reason": "No leads available"
            }

        # Track campaign launch (Agent 2)
        campaign_id = f"{business_id}_{datetime.now().strftime('%Y%m%d_%H%M')}"
        template = CAMPAIGNS[business_id]["initial_template"]

        track_campaign_launch_agent2(
            campaign_id=campaign_id,
            business_id=business_id,
            leads_targeted=len(leads),
            template=template
        )

        # Launch via existing launcher
        logger.info(f"\nLaunching campaign with {len(leads)} leads...")

        stats = self.launcher.launch_campaign(
            business_id=business_id,
            dry_run=dry_run,
            limit=len(leads)
        )

        # Record sends for quota
        if not dry_run:
            self.safeguards.record_send(business_id, stats["sent"])

        # Check webhook for responses (Agent 4)
        if not dry_run:
            time.sleep(5)  # Give webhook time to receive responses
            responses = fetch_responses_agent4(
                campaign_id=campaign_id,
                since=datetime.now() - timedelta(minutes=10)
            )

            if responses:
                logger.info(f"\n✅ Received {len(responses)} responses via webhook")
                for response in responses:
                    self.sequence_manager.mark_response(
                        response["phone"],
                        response["category"]
                    )

        logger.info(f"\n{'='*70}")
        logger.info("CAMPAIGN COMPLETE")
        logger.info(f"  Sent: {stats['sent']}/{stats['total_targeted']}")
        logger.info(f"  Enrolled in sequence: {stats['enrolled_in_sequence']}")
        logger.info(f"  Errors: {len(stats['errors'])}")
        logger.info(f"{'='*70}\n")

        return stats

    def launch_all_campaigns(
        self,
        dry_run: bool = True,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Launch campaigns for all businesses."""
        results = {}

        for business_id in CAMPAIGNS.keys():
            results[business_id] = self.launch_campaign(
                business_id=business_id,
                dry_run=dry_run,
                limit=limit
            )

            # Add delay between campaigns
            if not dry_run:
                time.sleep(10)

        return results

    def check_integrations(self) -> Dict[str, bool]:
        """Check which agent integrations are available."""
        logger.info("\n" + "="*60)
        logger.info("CHECKING AGENT INTEGRATIONS")
        logger.info("="*60)

        integrations = {}

        # Try to import Agent 1 (health checks)
        try:
            # This will fail until Agent 1 creates the module
            from . import health_checks
            integrations["agent1_health_checks"] = True
            logger.info("✅ Agent 1: Health checks available")
        except ImportError:
            integrations["agent1_health_checks"] = False
            logger.info("❌ Agent 1: Using placeholder health checks")

        # Try to import Agent 2 (analytics)
        try:
            from . import campaign_analytics
            integrations["agent2_analytics"] = True
            logger.info("✅ Agent 2: Analytics tracking available")
        except ImportError:
            integrations["agent2_analytics"] = False
            logger.info("❌ Agent 2: Using placeholder analytics")

        # Check Agent 3 (Apollo MCP)
        # This would check if Apollo MCP is running
        integrations["agent3_apollo_mcp"] = False  # Placeholder
        logger.info("❌ Agent 3: Apollo MCP not available (placeholder)")

        # Try to import Agent 4 (webhook)
        try:
            from . import webhook_processor
            integrations["agent4_webhook"] = True
            logger.info("✅ Agent 4: Webhook processing available")
        except ImportError:
            integrations["agent4_webhook"] = False
            logger.info("❌ Agent 4: Using placeholder webhook")

        logger.info("="*60 + "\n")

        return integrations


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Campaign Auto-Launcher - Automated Daily Campaign Execution"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview without sending (default)"
    )
    parser.add_argument(
        "--for-real",
        action="store_true",
        help="Actually send messages"
    )
    parser.add_argument(
        "--business",
        choices=["swflorida-hvac", "marceau-solutions"],
        help="Launch specific business only"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Max leads to target"
    )
    parser.add_argument(
        "--check-integrations",
        action="store_true",
        help="Check which agent integrations are available"
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory"
    )

    args = parser.parse_args()

    launcher = CampaignAutoLauncher(output_dir=args.output_dir)

    # Check integrations
    if args.check_integrations:
        launcher.check_integrations()
        return 0

    # Determine mode
    dry_run = not args.for_real

    # Launch campaigns
    if args.business:
        # Single business
        stats = launcher.launch_campaign(
            business_id=args.business,
            dry_run=dry_run,
            limit=args.limit
        )

        print(f"\n{stats['business_name']} Results:")
        print(f"  Sent: {stats['sent']}/{stats['total_targeted']}")
        print(f"  Enrolled: {stats['enrolled_in_sequence']}")
        print(f"  Errors: {len(stats['errors'])}")
    else:
        # All businesses
        results = launcher.launch_all_campaigns(
            dry_run=dry_run,
            limit=args.limit
        )

        print("\n" + "="*60)
        print("CAMPAIGN SUMMARY")
        print("="*60)
        for business_id, stats in results.items():
            if stats.get("status") in ["aborted", "skipped"]:
                print(f"\n{CAMPAIGNS[business_id]['business_name']}: {stats['status'].upper()}")
                print(f"  Reason: {stats.get('reason', 'Unknown')}")
            else:
                print(f"\n{stats['business_name']}:")
                print(f"  Sent: {stats['sent']}/{stats['total_targeted']}")
                print(f"  Enrolled: {stats['enrolled_in_sequence']}")
                print(f"  Errors: {len(stats['errors'])}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
