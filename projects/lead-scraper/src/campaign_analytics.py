#!/usr/bin/env python3
"""
Campaign Analytics Engine

Tracks comprehensive metrics for SMS outreach campaigns:
- Response rates by template
- Conversion funnel (Contacted → Responded → Qualified → Converted)
- Multi-touch attribution (which touch point drove the response)
- A/B test performance
- Cohort analysis

Integration:
- Reads from: sms_campaigns.json, sms_replies.json
- Writes to: campaign_analytics.json
- Creates ClickUp tasks ONLY for qualified leads (hot/warm)

Usage:
    # Update analytics from campaign data
    python -m src.campaign_analytics update

    # View summary report
    python -m src.campaign_analytics report

    # View template performance
    python -m src.campaign_analytics templates

    # View funnel metrics
    python -m src.campaign_analytics funnel

    # Export to CSV
    python -m src.campaign_analytics export --format csv
"""

import argparse
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from collections import defaultdict

# Load environment
from dotenv import load_dotenv
load_dotenv()


@dataclass
class TouchPoint:
    """Single touch in a multi-touch sequence."""
    touch_number: int
    template: str
    sent_at: str
    message_sid: str = ""
    status: str = "sent"  # sent, delivered, failed
    response_received: bool = False
    response_at: str = ""
    response_text: str = ""
    response_category: str = ""  # hot_lead, warm_lead, cold_lead, opt_out
    days_to_response: float = -1


@dataclass
class LeadRecord:
    """Complete record for a lead across all touches."""
    lead_id: str
    business_name: str
    phone: str
    campaign_id: str = ""

    # Funnel tracking
    funnel_stage: str = "contacted"  # contacted, responded, qualified, meeting, converted

    # Touch history
    touches: List[TouchPoint] = field(default_factory=list)
    total_touches: int = 0

    # Response tracking
    has_responded: bool = False
    first_response_at: str = ""
    response_category: str = ""
    converting_touch_number: int = 0  # Which touch got the response
    days_to_first_response: float = -1

    # Conversion tracking
    qualified_at: str = ""
    converted_at: str = ""
    conversion_value: float = 0.0

    # ClickUp integration
    clickup_task_id: str = ""  # Only created for qualified leads

    # Timestamps
    first_contact_date: str = ""
    last_activity: str = ""


@dataclass
class TemplateMetrics:
    """Performance metrics for a single template."""
    template_name: str
    total_sent: int = 0
    total_delivered: int = 0
    total_responses: int = 0
    response_rate: float = 0.0

    # Response breakdown
    hot_leads: int = 0
    warm_leads: int = 0
    cold_leads: int = 0
    opt_outs: int = 0

    # Conversion metrics
    qualified: int = 0
    converted: int = 0
    conversion_rate: float = 0.0

    # Timing
    avg_days_to_response: float = 0.0

    # Touch position effectiveness
    responses_as_touch_1: int = 0
    responses_as_touch_2: int = 0
    responses_as_touch_3: int = 0
    responses_as_touch_4_plus: int = 0


@dataclass
class CampaignMetrics:
    """Aggregate metrics for a campaign."""
    campaign_id: str
    campaign_name: str
    start_date: str

    # Volume
    total_leads: int = 0
    total_messages_sent: int = 0
    total_messages_delivered: int = 0

    # Funnel
    funnel_contacted: int = 0
    funnel_responded: int = 0
    funnel_qualified: int = 0
    funnel_meeting: int = 0
    funnel_converted: int = 0

    # Rates
    response_rate: float = 0.0
    qualification_rate: float = 0.0
    conversion_rate: float = 0.0

    # Revenue
    total_revenue: float = 0.0
    revenue_per_lead: float = 0.0

    # Template performance
    templates: Dict[str, TemplateMetrics] = field(default_factory=dict)

    # Attribution
    conversions_by_touch: Dict[int, int] = field(default_factory=dict)


class CampaignAnalytics:
    """
    Campaign analytics engine.

    Processes raw campaign data into actionable metrics.
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Data files
        self.campaigns_file = self.output_dir / "sms_campaigns.json"
        self.replies_file = self.output_dir / "sms_replies.json"
        self.analytics_file = self.output_dir / "campaign_analytics.json"
        self.leads_file = self.output_dir / "lead_records.json"

        # In-memory data
        self.leads: Dict[str, LeadRecord] = {}
        self.campaigns: Dict[str, CampaignMetrics] = {}
        self.templates: Dict[str, TemplateMetrics] = {}

        # Load existing data
        self._load_data()

    def _load_data(self):
        """Load existing analytics data."""
        if self.leads_file.exists():
            with open(self.leads_file) as f:
                data = json.load(f)
                for lead_id, lead_data in data.get("leads", {}).items():
                    # Convert touches back to TouchPoint objects
                    touches = [TouchPoint(**t) for t in lead_data.pop("touches", [])]
                    self.leads[lead_id] = LeadRecord(**lead_data, touches=touches)

        if self.analytics_file.exists():
            with open(self.analytics_file) as f:
                data = json.load(f)
                for campaign_id, campaign_data in data.get("campaigns", {}).items():
                    templates = {
                        k: TemplateMetrics(**v)
                        for k, v in campaign_data.pop("templates", {}).items()
                    }
                    self.campaigns[campaign_id] = CampaignMetrics(**campaign_data, templates=templates)

    def _save_data(self):
        """Save analytics data to files."""
        # Save lead records
        leads_data = {
            "leads": {
                lead_id: {
                    **asdict(lead),
                    "touches": [asdict(t) for t in lead.touches]
                }
                for lead_id, lead in self.leads.items()
            },
            "updated_at": datetime.now().isoformat()
        }
        with open(self.leads_file, "w") as f:
            json.dump(leads_data, f, indent=2)

        # Save campaign analytics
        analytics_data = {
            "campaigns": {
                campaign_id: {
                    **asdict(campaign),
                    "templates": {k: asdict(v) for k, v in campaign.templates.items()}
                }
                for campaign_id, campaign in self.campaigns.items()
            },
            "summary": self._generate_summary(),
            "updated_at": datetime.now().isoformat()
        }
        with open(self.analytics_file, "w") as f:
            json.dump(analytics_data, f, indent=2)

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate overall summary metrics."""
        total_sent = sum(c.total_messages_sent for c in self.campaigns.values())
        total_responses = sum(c.funnel_responded for c in self.campaigns.values())
        total_converted = sum(c.funnel_converted for c in self.campaigns.values())
        total_revenue = sum(c.total_revenue for c in self.campaigns.values())

        return {
            "total_campaigns": len(self.campaigns),
            "total_leads": len(self.leads),
            "total_messages_sent": total_sent,
            "total_responses": total_responses,
            "overall_response_rate": (total_responses / total_sent * 100) if total_sent > 0 else 0,
            "total_conversions": total_converted,
            "overall_conversion_rate": (total_converted / total_sent * 100) if total_sent > 0 else 0,
            "total_revenue": total_revenue
        }

    def import_from_campaigns(self, campaign_id: str = None):
        """
        Import data from sms_campaigns.json into analytics system.

        Args:
            campaign_id: Optional campaign ID to assign (auto-generated if None)
        """
        if not self.campaigns_file.exists():
            print(f"No campaigns file found at {self.campaigns_file}")
            return

        with open(self.campaigns_file) as f:
            raw_data = json.load(f)

        records = raw_data.get("records", [])
        if not records:
            print("No records found in campaigns file")
            return

        # Auto-generate campaign ID from first record date
        if not campaign_id:
            first_sent = records[0].get("sent_at", "")
            if first_sent:
                date_part = first_sent[:10].replace("-", "")
                campaign_id = f"campaign_{date_part}"
            else:
                campaign_id = f"campaign_{datetime.now().strftime('%Y%m%d')}"

        # Initialize campaign if new
        if campaign_id not in self.campaigns:
            self.campaigns[campaign_id] = CampaignMetrics(
                campaign_id=campaign_id,
                campaign_name=f"SMS Campaign {campaign_id}",
                start_date=records[0].get("sent_at", "")[:10] if records else ""
            )

        campaign = self.campaigns[campaign_id]

        # Process each record
        for record in records:
            lead_id = record.get("lead_id", "")
            phone = record.get("phone", "")
            business_name = record.get("business_name", "")
            template = record.get("template_used", "")
            sent_at = record.get("sent_at", "")
            status = record.get("status", "sent")
            message_sid = record.get("message_sid", "")

            # Create or update lead record
            if lead_id not in self.leads:
                self.leads[lead_id] = LeadRecord(
                    lead_id=lead_id,
                    business_name=business_name,
                    phone=phone,
                    campaign_id=campaign_id,
                    first_contact_date=sent_at[:10] if sent_at else ""
                )

            lead = self.leads[lead_id]

            # Add touch point
            touch_number = len(lead.touches) + 1
            touch = TouchPoint(
                touch_number=touch_number,
                template=template,
                sent_at=sent_at,
                message_sid=message_sid,
                status="delivered" if status == "sent" else status
            )
            lead.touches.append(touch)
            lead.total_touches = len(lead.touches)
            lead.last_activity = sent_at

            # Update campaign metrics
            campaign.total_messages_sent += 1
            if status == "sent":
                campaign.total_messages_delivered += 1
                campaign.funnel_contacted += 1

            # Initialize template metrics
            if template not in campaign.templates:
                campaign.templates[template] = TemplateMetrics(template_name=template)

            campaign.templates[template].total_sent += 1
            if status == "sent":
                campaign.templates[template].total_delivered += 1

        campaign.total_leads = len([l for l in self.leads.values() if l.campaign_id == campaign_id])

        print(f"Imported {len(records)} records into campaign '{campaign_id}'")
        print(f"Total leads: {campaign.total_leads}")
        print(f"Total messages: {campaign.total_messages_sent}")

        self._save_data()

    def record_response(
        self,
        phone: str,
        response_text: str,
        category: str,
        received_at: str = None
    ):
        """
        Record a response from a lead.

        Args:
            phone: Phone number that responded
            response_text: The response message
            category: hot_lead, warm_lead, cold_lead, opt_out
            received_at: Timestamp of response (defaults to now)
        """
        received_at = received_at or datetime.now().isoformat()

        # Find lead by phone
        lead = None
        for l in self.leads.values():
            if l.phone == phone or l.phone.replace(" ", "").replace("-", "") == phone.replace(" ", "").replace("-", ""):
                lead = l
                break

        if not lead:
            print(f"No lead found for phone: {phone}")
            return

        # Update lead record
        lead.has_responded = True
        lead.first_response_at = received_at
        lead.response_category = category
        lead.last_activity = received_at

        # Find which touch got the response (most recent)
        if lead.touches:
            last_touch = lead.touches[-1]
            last_touch.response_received = True
            last_touch.response_at = received_at
            last_touch.response_text = response_text
            last_touch.response_category = category

            # Calculate days to response
            sent_dt = datetime.fromisoformat(last_touch.sent_at.replace("Z", "+00:00"))
            resp_dt = datetime.fromisoformat(received_at.replace("Z", "+00:00"))
            days = (resp_dt - sent_dt).total_seconds() / 86400
            last_touch.days_to_response = round(days, 2)
            lead.days_to_first_response = days
            lead.converting_touch_number = last_touch.touch_number

        # Update funnel stage
        if category in ["hot_lead", "warm_lead"]:
            lead.funnel_stage = "qualified"
            lead.qualified_at = received_at
        elif category == "opt_out":
            lead.funnel_stage = "opted_out"
        else:
            lead.funnel_stage = "responded"

        # Update campaign metrics
        if lead.campaign_id in self.campaigns:
            campaign = self.campaigns[lead.campaign_id]
            campaign.funnel_responded += 1

            if category in ["hot_lead", "warm_lead"]:
                campaign.funnel_qualified += 1

            # Update template metrics
            if lead.touches:
                template = lead.touches[-1].template
                if template in campaign.templates:
                    tm = campaign.templates[template]
                    tm.total_responses += 1
                    tm.response_rate = (tm.total_responses / tm.total_sent * 100) if tm.total_sent > 0 else 0

                    if category == "hot_lead":
                        tm.hot_leads += 1
                    elif category == "warm_lead":
                        tm.warm_leads += 1
                    elif category == "cold_lead":
                        tm.cold_leads += 1
                    elif category == "opt_out":
                        tm.opt_outs += 1

                    tm.qualified = tm.hot_leads + tm.warm_leads

                    # Track by touch position
                    touch_num = lead.converting_touch_number
                    if touch_num == 1:
                        tm.responses_as_touch_1 += 1
                    elif touch_num == 2:
                        tm.responses_as_touch_2 += 1
                    elif touch_num == 3:
                        tm.responses_as_touch_3 += 1
                    else:
                        tm.responses_as_touch_4_plus += 1

            # Update campaign rates
            campaign.response_rate = (campaign.funnel_responded / campaign.funnel_contacted * 100) if campaign.funnel_contacted > 0 else 0
            campaign.qualification_rate = (campaign.funnel_qualified / campaign.funnel_contacted * 100) if campaign.funnel_contacted > 0 else 0

            # Update attribution
            touch_num = lead.converting_touch_number
            if touch_num not in campaign.conversions_by_touch:
                campaign.conversions_by_touch[touch_num] = 0
            campaign.conversions_by_touch[touch_num] += 1

        print(f"Recorded response from {lead.business_name} ({phone})")
        print(f"  Category: {category}")
        print(f"  Touch #{lead.converting_touch_number}")
        print(f"  Days to response: {lead.days_to_first_response:.1f}")

        self._save_data()

        return lead

    def record_conversion(self, lead_id: str, value: float = 0.0):
        """Record a conversion (lead became customer)."""
        if lead_id not in self.leads:
            print(f"Lead not found: {lead_id}")
            return

        lead = self.leads[lead_id]
        lead.funnel_stage = "converted"
        lead.converted_at = datetime.now().isoformat()
        lead.conversion_value = value

        if lead.campaign_id in self.campaigns:
            campaign = self.campaigns[lead.campaign_id]
            campaign.funnel_converted += 1
            campaign.total_revenue += value
            campaign.conversion_rate = (campaign.funnel_converted / campaign.funnel_contacted * 100) if campaign.funnel_contacted > 0 else 0
            campaign.revenue_per_lead = campaign.total_revenue / campaign.total_leads if campaign.total_leads > 0 else 0

        print(f"Recorded conversion for {lead.business_name}")
        print(f"  Value: ${value:,.2f}")

        self._save_data()

    def get_report(self) -> str:
        """Generate comprehensive analytics report."""
        lines = []
        lines.append("=" * 70)
        lines.append("CAMPAIGN ANALYTICS REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 70)

        summary = self._generate_summary()

        lines.append("\n## OVERALL SUMMARY")
        lines.append(f"Total Campaigns: {summary['total_campaigns']}")
        lines.append(f"Total Leads: {summary['total_leads']}")
        lines.append(f"Total Messages Sent: {summary['total_messages_sent']}")
        lines.append(f"Total Responses: {summary['total_responses']}")
        lines.append(f"Overall Response Rate: {summary['overall_response_rate']:.1f}%")
        lines.append(f"Total Conversions: {summary['total_conversions']}")
        lines.append(f"Total Revenue: ${summary['total_revenue']:,.2f}")

        for campaign_id, campaign in self.campaigns.items():
            lines.append(f"\n## CAMPAIGN: {campaign.campaign_name}")
            lines.append("-" * 50)
            lines.append(f"Start Date: {campaign.start_date}")
            lines.append(f"Total Leads: {campaign.total_leads}")
            lines.append(f"Messages Sent: {campaign.total_messages_sent}")

            lines.append("\n### CONVERSION FUNNEL")
            lines.append(f"{'Stage':<20} {'Count':>8} {'Rate':>10}")
            lines.append("-" * 40)

            funnel_data = [
                ("Contacted", campaign.funnel_contacted, 100.0),
                ("Responded", campaign.funnel_responded, campaign.response_rate),
                ("Qualified", campaign.funnel_qualified, campaign.qualification_rate),
                ("Meeting", campaign.funnel_meeting, 0),
                ("Converted", campaign.funnel_converted, campaign.conversion_rate),
            ]

            for stage, count, rate in funnel_data:
                lines.append(f"{stage:<20} {count:>8} {rate:>9.1f}%")

            if campaign.templates:
                lines.append("\n### TEMPLATE PERFORMANCE")
                lines.append(f"{'Template':<25} {'Sent':>6} {'Resp':>6} {'Rate':>8} {'Hot':>5} {'Warm':>5}")
                lines.append("-" * 60)

                for template_name, tm in campaign.templates.items():
                    lines.append(
                        f"{template_name[:25]:<25} {tm.total_sent:>6} {tm.total_responses:>6} "
                        f"{tm.response_rate:>7.1f}% {tm.hot_leads:>5} {tm.warm_leads:>5}"
                    )

            if campaign.conversions_by_touch:
                lines.append("\n### ATTRIBUTION (Responses by Touch #)")
                for touch_num in sorted(campaign.conversions_by_touch.keys()):
                    count = campaign.conversions_by_touch[touch_num]
                    lines.append(f"  Touch #{touch_num}: {count} responses")

        lines.append("\n" + "=" * 70)

        return "\n".join(lines)

    def get_template_comparison(self) -> str:
        """Generate template comparison report."""
        lines = []
        lines.append("=" * 80)
        lines.append("TEMPLATE PERFORMANCE COMPARISON")
        lines.append("=" * 80)

        # Aggregate across all campaigns
        all_templates: Dict[str, TemplateMetrics] = {}

        for campaign in self.campaigns.values():
            for template_name, tm in campaign.templates.items():
                if template_name not in all_templates:
                    all_templates[template_name] = TemplateMetrics(template_name=template_name)

                agg = all_templates[template_name]
                agg.total_sent += tm.total_sent
                agg.total_responses += tm.total_responses
                agg.hot_leads += tm.hot_leads
                agg.warm_leads += tm.warm_leads
                agg.cold_leads += tm.cold_leads
                agg.opt_outs += tm.opt_outs

        # Calculate rates
        for tm in all_templates.values():
            tm.response_rate = (tm.total_responses / tm.total_sent * 100) if tm.total_sent > 0 else 0
            tm.qualified = tm.hot_leads + tm.warm_leads

        # Sort by response rate
        sorted_templates = sorted(all_templates.values(), key=lambda x: x.response_rate, reverse=True)

        lines.append(f"\n{'Template':<30} {'Sent':>6} {'Resp':>6} {'Rate':>8} {'Hot':>5} {'Warm':>5} {'OptOut':>6}")
        lines.append("-" * 80)

        for tm in sorted_templates:
            lines.append(
                f"{tm.template_name[:30]:<30} {tm.total_sent:>6} {tm.total_responses:>6} "
                f"{tm.response_rate:>7.1f}% {tm.hot_leads:>5} {tm.warm_leads:>5} {tm.opt_outs:>6}"
            )

        if sorted_templates:
            best = sorted_templates[0]
            lines.append(f"\n🏆 BEST PERFORMER: {best.template_name} ({best.response_rate:.1f}% response rate)")

        return "\n".join(lines)

    def get_funnel_report(self) -> str:
        """Generate funnel visualization."""
        lines = []
        lines.append("=" * 60)
        lines.append("CONVERSION FUNNEL")
        lines.append("=" * 60)

        # Aggregate funnel
        total_contacted = sum(c.funnel_contacted for c in self.campaigns.values())
        total_responded = sum(c.funnel_responded for c in self.campaigns.values())
        total_qualified = sum(c.funnel_qualified for c in self.campaigns.values())
        total_meeting = sum(c.funnel_meeting for c in self.campaigns.values())
        total_converted = sum(c.funnel_converted for c in self.campaigns.values())

        funnel = [
            ("1. Contacted", total_contacted),
            ("2. Responded", total_responded),
            ("3. Qualified", total_qualified),
            ("4. Meeting", total_meeting),
            ("5. Converted", total_converted),
        ]

        max_width = 40

        for stage, count in funnel:
            if total_contacted > 0:
                pct = (count / total_contacted) * 100
                bar_width = int((count / total_contacted) * max_width) if total_contacted > 0 else 0
            else:
                pct = 0
                bar_width = 0

            bar = "█" * bar_width + "░" * (max_width - bar_width)
            lines.append(f"{stage:<15} {bar} {count:>5} ({pct:>5.1f}%)")

        # Drop-off analysis
        if total_contacted > 0:
            lines.append("\n### DROP-OFF ANALYSIS")

            if total_responded > 0:
                responded_rate = (total_responded / total_contacted) * 100
                lines.append(f"Contacted → Responded: {100 - responded_rate:.1f}% drop-off")

            if total_qualified > 0 and total_responded > 0:
                qualified_rate = (total_qualified / total_responded) * 100
                lines.append(f"Responded → Qualified: {100 - qualified_rate:.1f}% drop-off")

            if total_converted > 0 and total_qualified > 0:
                converted_rate = (total_converted / total_qualified) * 100
                lines.append(f"Qualified → Converted: {100 - converted_rate:.1f}% drop-off")

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Campaign Analytics Engine")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Update command
    update_parser = subparsers.add_parser("update", help="Import/update analytics from campaign data")
    update_parser.add_argument("--campaign-id", help="Campaign ID to assign")

    # Report command
    subparsers.add_parser("report", help="Show comprehensive analytics report")

    # Templates command
    subparsers.add_parser("templates", help="Show template performance comparison")

    # Funnel command
    subparsers.add_parser("funnel", help="Show conversion funnel")

    # Response command
    response_parser = subparsers.add_parser("response", help="Record a response")
    response_parser.add_argument("--phone", required=True, help="Phone number that responded")
    response_parser.add_argument("--text", required=True, help="Response text")
    response_parser.add_argument("--category", required=True,
                                  choices=["hot_lead", "warm_lead", "cold_lead", "opt_out"],
                                  help="Response category")

    # Conversion command
    convert_parser = subparsers.add_parser("convert", help="Record a conversion")
    convert_parser.add_argument("--lead-id", required=True, help="Lead ID that converted")
    convert_parser.add_argument("--value", type=float, default=0.0, help="Conversion value")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export data")
    export_parser.add_argument("--format", choices=["csv", "json"], default="json")

    args = parser.parse_args()

    # Change to project directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    analytics = CampaignAnalytics()

    if args.command == "update":
        analytics.import_from_campaigns(args.campaign_id)

    elif args.command == "report":
        print(analytics.get_report())

    elif args.command == "templates":
        print(analytics.get_template_comparison())

    elif args.command == "funnel":
        print(analytics.get_funnel_report())

    elif args.command == "response":
        analytics.record_response(
            phone=args.phone,
            response_text=args.text,
            category=args.category
        )

    elif args.command == "convert":
        analytics.record_conversion(args.lead_id, args.value)

    elif args.command == "export":
        if args.format == "json":
            print(json.dumps(analytics._generate_summary(), indent=2))
        else:
            print("CSV export not yet implemented")

    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    exit(main())
