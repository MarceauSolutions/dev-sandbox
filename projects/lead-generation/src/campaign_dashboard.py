#!/usr/bin/env python3
"""
Multi-Business Campaign Dashboard

Real-time tracking for parallel outreach campaigns:
- Southwest Florida Comfort (HVAC Voice AI)
- Marceau Solutions (AI Automation)

Tracks:
- Delivery rates
- Response rates per touch
- Opt-outs
- Conversions
- Cost per campaign
- Follow-up sequence progress

Usage:
    # Show dashboard
    python -m src.campaign_dashboard

    # Show specific business
    python -m src.campaign_dashboard --business swflorida-hvac

    # Export to JSON
    python -m src.campaign_dashboard --export dashboard_export.json
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict

from .models import LeadCollection
from .sms_outreach import SMSOutreachManager
from .follow_up_sequence import FollowUpSequenceManager


class CampaignDashboard:
    """
    Dashboard for tracking multi-business campaigns.
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.campaigns_dir = self.output_dir / "campaigns"

        # Load managers
        self.sms_manager = SMSOutreachManager(output_dir=output_dir)
        self.sequence_manager = FollowUpSequenceManager(output_dir=output_dir)

        # Load campaigns
        self.campaigns = self._load_all_campaigns()

    def _load_all_campaigns(self) -> Dict[str, Dict[str, Any]]:
        """Load all campaign configurations."""
        campaigns = {}

        if not self.campaigns_dir.exists():
            return campaigns

        for campaign_file in self.campaigns_dir.glob("*.json"):
            with open(campaign_file) as f:
                data = json.load(f)
                business_id = data.get("business_id")
                if business_id:
                    campaigns[business_id] = data

        return campaigns

    def get_campaign_metrics(self, business_id: str) -> Dict[str, Any]:
        """
        Get comprehensive metrics for a campaign.
        """
        if business_id not in self.campaigns:
            return {"error": f"Campaign not found: {business_id}"}

        campaign = self.campaigns[business_id]

        # Get SMS records for this business
        sms_records = [
            r for r in self.sms_manager.campaigns.values()
            if r.sending_business_id == business_id
        ]

        # Get sequence records for this business
        sequences = [
            s for s in self.sequence_manager.sequences.values()
            if s.sending_business_id == business_id
        ]

        # Calculate metrics
        total_sent = len(sms_records)
        delivered = sum(1 for r in sms_records if r.status == "delivered")
        failed = sum(1 for r in sms_records if r.status == "failed")
        opted_out = sum(1 for r in sms_records if r.status == "opted_out")

        # Response metrics from sequences
        responded = sum(1 for s in sequences if s.status == "responded")
        converted = sum(1 for s in sequences if s.status == "converted")

        # Cost calculation
        cost_per_sms = 0.0079
        total_cost = total_sent * cost_per_sms

        # Response rate by touch
        touch_stats = defaultdict(lambda: {"sent": 0, "responded": 0})
        for seq in sequences:
            for touch in seq.touchpoints:
                if touch.get("status") == "sent":
                    touch_num = touch.get("touch_number")
                    touch_stats[touch_num]["sent"] += 1
                if touch.get("response"):
                    touch_num = touch.get("touch_number")
                    touch_stats[touch_num]["responded"] += 1

        return {
            "business_id": business_id,
            "business_name": campaign.get("business_name"),
            "campaign_status": campaign.get("status", "unknown"),
            "launched_at": campaign.get("launched_at", ""),
            "outreach_metrics": {
                "total_sent": total_sent,
                "delivered": delivered,
                "failed": failed,
                "opted_out": opted_out,
                "delivery_rate": round(delivered / total_sent * 100, 1) if total_sent > 0 else 0,
                "opt_out_rate": round(opted_out / total_sent * 100, 1) if total_sent > 0 else 0
            },
            "response_metrics": {
                "total_sequences": len(sequences),
                "responded": responded,
                "converted": converted,
                "response_rate": round(responded / len(sequences) * 100, 1) if sequences else 0,
                "conversion_rate": round(converted / len(sequences) * 100, 1) if sequences else 0
            },
            "touch_breakdown": {
                f"touch_{num}": {
                    "sent": stats["sent"],
                    "responded": stats["responded"],
                    "response_rate": round(stats["responded"] / stats["sent"] * 100, 1) if stats["sent"] > 0 else 0
                }
                for num, stats in sorted(touch_stats.items())
            },
            "cost_metrics": {
                "total_cost": round(total_cost, 2),
                "cost_per_message": cost_per_sms,
                "cost_per_response": round(total_cost / responded, 2) if responded > 0 else 0,
                "cost_per_conversion": round(total_cost / converted, 2) if converted > 0 else 0
            }
        }

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get metrics for all campaigns."""
        all_metrics = {}

        for business_id in self.campaigns.keys():
            all_metrics[business_id] = self.get_campaign_metrics(business_id)

        # Calculate totals
        total_sent = sum(m["outreach_metrics"]["total_sent"] for m in all_metrics.values())
        total_cost = sum(m["cost_metrics"]["total_cost"] for m in all_metrics.values())
        total_responded = sum(m["response_metrics"]["responded"] for m in all_metrics.values())
        total_converted = sum(m["response_metrics"]["converted"] for m in all_metrics.values())

        all_metrics["totals"] = {
            "total_businesses": len(self.campaigns),
            "total_messages_sent": total_sent,
            "total_cost": round(total_cost, 2),
            "total_responses": total_responded,
            "total_conversions": total_converted,
            "overall_response_rate": round(total_responded / total_sent * 100, 1) if total_sent > 0 else 0,
            "overall_conversion_rate": round(total_converted / total_sent * 100, 1) if total_sent > 0 else 0
        }

        return all_metrics

    def print_dashboard(self, business_id: str = None):
        """
        Print formatted dashboard to console.
        """
        if business_id:
            metrics = self.get_campaign_metrics(business_id)
            self._print_campaign_metrics(metrics)
        else:
            all_metrics = self.get_all_metrics()

            print("\n" + "="*80)
            print("MULTI-BUSINESS CAMPAIGN DASHBOARD")
            print("="*80)

            # Print totals first
            totals = all_metrics.pop("totals")
            print("\n📊 OVERALL METRICS")
            print("-" * 80)
            print(f"  Total Businesses:        {totals['total_businesses']}")
            print(f"  Total Messages Sent:     {totals['total_messages_sent']}")
            print(f"  Total Cost:              ${totals['total_cost']:.2f}")
            print(f"  Total Responses:         {totals['total_responses']}")
            print(f"  Total Conversions:       {totals['total_conversions']}")
            print(f"  Overall Response Rate:   {totals['overall_response_rate']}%")
            print(f"  Overall Conversion Rate: {totals['overall_conversion_rate']}%")

            # Print per-business metrics
            for business_id, metrics in all_metrics.items():
                print("\n" + "="*80)
                self._print_campaign_metrics(metrics)

    def _print_campaign_metrics(self, metrics: Dict[str, Any]):
        """Print metrics for a single campaign."""
        print(f"\n🏢 {metrics['business_name']} ({metrics['business_id']})")
        print("-" * 80)
        print(f"  Status: {metrics['campaign_status']}")
        print(f"  Launched: {metrics['launched_at']}")

        out = metrics["outreach_metrics"]
        print(f"\n📤 OUTREACH:")
        print(f"  Total Sent:      {out['total_sent']}")
        print(f"  Delivered:       {out['delivered']} ({out['delivery_rate']}%)")
        print(f"  Failed:          {out['failed']}")
        print(f"  Opted Out:       {out['opted_out']} ({out['opt_out_rate']}%)")

        resp = metrics["response_metrics"]
        print(f"\n💬 RESPONSES:")
        print(f"  Total Sequences: {resp['total_sequences']}")
        print(f"  Responded:       {resp['responded']} ({resp['response_rate']}%)")
        print(f"  Converted:       {resp['converted']} ({resp['conversion_rate']}%)")

        print(f"\n📞 BY TOUCH:")
        for touch_name, touch_data in metrics["touch_breakdown"].items():
            print(f"  {touch_name.replace('_', ' ').title()}: {touch_data['sent']} sent, {touch_data['responded']} responded ({touch_data['response_rate']}%)")

        cost = metrics["cost_metrics"]
        print(f"\n💰 COSTS:")
        print(f"  Total Cost:           ${cost['total_cost']:.2f}")
        print(f"  Cost per Message:     ${cost['cost_per_message']:.4f}")
        print(f"  Cost per Response:    ${cost['cost_per_response']:.2f}" if cost['cost_per_response'] > 0 else "  Cost per Response:    N/A")
        print(f"  Cost per Conversion:  ${cost['cost_per_conversion']:.2f}" if cost['cost_per_conversion'] > 0 else "  Cost per Conversion:  N/A")

    def export_to_json(self, output_file: str):
        """Export dashboard data to JSON."""
        all_metrics = self.get_all_metrics()

        with open(output_file, 'w') as f:
            json.dump(all_metrics, f, indent=2)

        print(f"Dashboard exported to: {output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Campaign Dashboard")
    parser.add_argument("--business", choices=["swflorida-hvac", "marceau-solutions"], help="Show specific business only")
    parser.add_argument("--export", help="Export to JSON file")
    parser.add_argument("--output-dir", default="output", help="Output directory")

    args = parser.parse_args()

    dashboard = CampaignDashboard(output_dir=args.output_dir)

    if args.export:
        dashboard.export_to_json(args.export)
    else:
        dashboard.print_dashboard(business_id=args.business)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
