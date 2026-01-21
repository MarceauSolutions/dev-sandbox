#!/usr/bin/env python3
"""
Apollo Metrics Dashboard

Tracks Apollo.io usage, costs, and campaign performance:
- Credits used vs remaining
- Cost per lead calculations
- Campaign ROI analysis
- Quality score trends over time
- Conversion funnel tracking

Usage:
    # View current credits
    python -m src.apollo_metrics credits

    # Campaign performance
    python -m src.apollo_metrics campaign --name "Naples Gyms Jan 2026"

    # Cost analysis
    python -m src.apollo_metrics costs --days 30

    # ROI report
    python -m src.apollo_metrics roi --campaign "Naples Gyms Jan 2026"

    # Full dashboard
    python -m src.apollo_metrics dashboard
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict

from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

logger = logging.getLogger(__name__)


@dataclass
class CreditUsage:
    """Track Apollo credit usage."""
    date: str
    campaign_name: str
    search_results: int
    enriched_leads: int
    credits_spent: int
    credits_remaining: int
    cost_per_lead: float


@dataclass
class CampaignMetrics:
    """Track campaign performance."""
    campaign_name: str
    start_date: str
    total_leads_found: int
    enriched_leads: int
    sms_sent: int
    responses: int
    qualified_leads: int
    converted_leads: int
    apollo_credits_spent: int
    apollo_cost: float
    sms_cost: float
    total_cost: float
    response_rate: float
    conversion_rate: float
    cost_per_conversion: float
    roi: float


class ApolloMetrics:
    """
    Track and analyze Apollo.io usage metrics.
    """

    def __init__(self, output_dir: str = "output"):
        """
        Initialize metrics tracker.

        Args:
            output_dir: Directory for storing metrics data
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.metrics_file = self.output_dir / "apollo_metrics.json"
        self.campaigns_file = self.output_dir / "apollo_campaigns.json"

        self.api_key = os.getenv("APOLLO_API_KEY")

    def get_current_credits(self) -> Optional[Dict[str, Any]]:
        """
        Get current Apollo credit balance.

        Returns:
            Dictionary with credit info or None on failure
        """
        try:
            from apollo_mcp.apollo import ApolloClient

            client = ApolloClient(api_key=self.api_key)
            balance = client.get_credit_balance()

            return {
                "credits_remaining": balance.get("credits_remaining", 0),
                "total_credits": balance.get("total_credits", 0),
                "credits_used": balance.get("credits_used", 0),
                "percentage_used": round((balance.get("credits_used", 0) / balance.get("total_credits", 1)) * 100, 2),
                "checked_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get credit balance: {e}")
            return None

    def log_campaign_usage(
        self,
        campaign_name: str,
        search_results: int,
        enriched_leads: int,
        credits_spent: int
    ):
        """
        Log Apollo credit usage for a campaign.

        Args:
            campaign_name: Campaign identifier
            search_results: Total search results found
            enriched_leads: Number of leads enriched
            credits_spent: Credits used for enrichment
        """
        # Get current balance
        balance = self.get_current_credits()
        if not balance:
            logger.warning("Could not get credit balance")
            credits_remaining = 0
        else:
            credits_remaining = balance["credits_remaining"]

        # Calculate cost per lead
        cost_per_lead = round(credits_spent / enriched_leads, 2) if enriched_leads > 0 else 0

        # Create usage record
        usage = CreditUsage(
            date=datetime.now().isoformat(),
            campaign_name=campaign_name,
            search_results=search_results,
            enriched_leads=enriched_leads,
            credits_spent=credits_spent,
            credits_remaining=credits_remaining,
            cost_per_lead=cost_per_lead
        )

        # Load existing metrics
        metrics = []
        if self.metrics_file.exists():
            with open(self.metrics_file) as f:
                metrics = json.load(f)

        # Add new usage
        metrics.append(asdict(usage))

        # Save updated metrics
        with open(self.metrics_file, "w") as f:
            json.dump(metrics, f, indent=2)

        logger.info(f"Logged usage: {credits_spent} credits for {campaign_name}")

    def calculate_campaign_metrics(
        self,
        campaign_name: str,
        apollo_credits: int,
        sms_sent: int,
        responses: int = 0,
        qualified: int = 0,
        converted: int = 0,
        revenue: float = 0.0
    ) -> CampaignMetrics:
        """
        Calculate comprehensive campaign metrics.

        Args:
            campaign_name: Campaign identifier
            apollo_credits: Credits spent on Apollo
            sms_sent: Number of SMS sent
            responses: Number of responses received
            qualified: Number of qualified leads
            converted: Number of conversions
            revenue: Revenue generated

        Returns:
            CampaignMetrics object
        """
        # Cost calculations
        apollo_cost = apollo_credits * 0.10  # $0.10 per credit (estimate)
        sms_cost = sms_sent * 0.015  # $0.015 per SMS via Twilio
        total_cost = apollo_cost + sms_cost

        # Performance metrics
        response_rate = round((responses / sms_sent * 100), 2) if sms_sent > 0 else 0
        conversion_rate = round((converted / sms_sent * 100), 2) if sms_sent > 0 else 0
        cost_per_conversion = round(total_cost / converted, 2) if converted > 0 else 0

        # ROI
        roi = round(((revenue - total_cost) / total_cost * 100), 2) if total_cost > 0 else 0

        return CampaignMetrics(
            campaign_name=campaign_name,
            start_date=datetime.now().isoformat(),
            total_leads_found=0,  # Can be updated later
            enriched_leads=apollo_credits // 2,  # Assuming 2 credits per lead
            sms_sent=sms_sent,
            responses=responses,
            qualified_leads=qualified,
            converted_leads=converted,
            apollo_credits_spent=apollo_credits,
            apollo_cost=apollo_cost,
            sms_cost=sms_cost,
            total_cost=total_cost,
            response_rate=response_rate,
            conversion_rate=conversion_rate,
            cost_per_conversion=cost_per_conversion,
            roi=roi
        )

    def get_cost_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get cost summary for the last N days.

        Args:
            days: Number of days to analyze

        Returns:
            Summary dictionary
        """
        if not self.metrics_file.exists():
            return {
                "total_credits_spent": 0,
                "total_cost": 0.0,
                "campaigns": 0,
                "avg_cost_per_lead": 0.0
            }

        with open(self.metrics_file) as f:
            metrics = json.load(f)

        # Filter to last N days
        cutoff = datetime.now() - timedelta(days=days)
        recent = [
            m for m in metrics
            if datetime.fromisoformat(m["date"]) >= cutoff
        ]

        # Calculate totals
        total_credits = sum(m["credits_spent"] for m in recent)
        total_leads = sum(m["enriched_leads"] for m in recent)
        total_cost = total_credits * 0.10  # $0.10 per credit estimate

        return {
            "period_days": days,
            "total_credits_spent": total_credits,
            "total_cost": round(total_cost, 2),
            "campaigns": len(set(m["campaign_name"] for m in recent)),
            "total_leads_enriched": total_leads,
            "avg_cost_per_lead": round(total_cost / total_leads, 2) if total_leads > 0 else 0.0,
            "avg_credits_per_campaign": round(total_credits / len(recent), 2) if recent else 0.0
        }

    def print_dashboard(self):
        """
        Print comprehensive Apollo metrics dashboard.
        """
        print("\n" + "="*80)
        print("APOLLO METRICS DASHBOARD")
        print("="*80)

        # Credit balance
        balance = self.get_current_credits()
        if balance:
            print(f"\n📊 CREDIT BALANCE")
            print(f"   Remaining: {balance['credits_remaining']:,} credits")
            print(f"   Used: {balance['credits_used']:,} / {balance['total_credits']:,}")
            print(f"   Usage: {balance['percentage_used']}%")

        # 30-day cost summary
        summary = self.get_cost_summary(days=30)
        print(f"\n💰 LAST 30 DAYS")
        print(f"   Credits Spent: {summary['total_credits_spent']:,}")
        print(f"   Est. Cost: ${summary['total_cost']:.2f}")
        print(f"   Campaigns: {summary['campaigns']}")
        print(f"   Leads Enriched: {summary['total_leads_enriched']}")
        print(f"   Avg Cost/Lead: ${summary['avg_cost_per_lead']:.2f}")

        # Recent campaigns
        if self.metrics_file.exists():
            with open(self.metrics_file) as f:
                metrics = json.load(f)

            recent_campaigns = sorted(metrics, key=lambda x: x["date"], reverse=True)[:5]

            print(f"\n📈 RECENT CAMPAIGNS")
            for i, campaign in enumerate(recent_campaigns, 1):
                print(f"\n   {i}. {campaign['campaign_name']}")
                print(f"      Date: {campaign['date'][:10]}")
                print(f"      Enriched: {campaign['enriched_leads']} leads")
                print(f"      Credits: {campaign['credits_spent']}")
                print(f"      Cost/Lead: ${campaign['cost_per_lead']:.2f}")

        print("\n" + "="*80 + "\n")


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """CLI entry point for Apollo metrics."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(
        description="Apollo Metrics Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Credits command
    credits_parser = subparsers.add_parser("credits", help="Show current credit balance")

    # Campaign command
    campaign_parser = subparsers.add_parser("campaign", help="Analyze campaign performance")
    campaign_parser.add_argument("--name", required=True, help="Campaign name")
    campaign_parser.add_argument("--responses", type=int, default=0, help="Number of responses")
    campaign_parser.add_argument("--conversions", type=int, default=0, help="Number of conversions")
    campaign_parser.add_argument("--revenue", type=float, default=0.0, help="Revenue generated")

    # Costs command
    costs_parser = subparsers.add_parser("costs", help="Cost summary")
    costs_parser.add_argument("--days", type=int, default=30, help="Days to analyze")

    # Dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Show full dashboard")

    args = parser.parse_args()

    metrics = ApolloMetrics()

    if args.command == "credits":
        balance = metrics.get_current_credits()
        if balance:
            print(f"\nCredits Remaining: {balance['credits_remaining']:,}")
            print(f"Total Credits: {balance['total_credits']:,}")
            print(f"Credits Used: {balance['credits_used']:,} ({balance['percentage_used']}%)")
        else:
            print("Failed to retrieve credit balance")

    elif args.command == "costs":
        summary = metrics.get_cost_summary(days=args.days)
        print(f"\nCost Summary (Last {args.days} Days)")
        print(f"{'='*50}")
        print(f"Credits Spent: {summary['total_credits_spent']:,}")
        print(f"Est. Cost: ${summary['total_cost']:.2f}")
        print(f"Campaigns: {summary['campaigns']}")
        print(f"Leads Enriched: {summary['total_leads_enriched']}")
        print(f"Avg Cost/Lead: ${summary['avg_cost_per_lead']:.2f}")

    elif args.command == "dashboard":
        metrics.print_dashboard()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
