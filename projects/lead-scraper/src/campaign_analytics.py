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
    sending_business_id: str = ""  # NEW: Which business sent this campaign (marceau-solutions, swflorida-hvac, shipping-logistics)

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
class TemplateScore:
    """Composite score for template performance."""
    template_name: str

    # Raw metrics
    response_rate: float = 0.0
    qualification_rate: float = 0.0  # (hot + warm) / total_responses
    conversion_rate: float = 0.0  # converted / qualified
    opt_out_rate: float = 0.0
    delivery_rate: float = 0.0

    # Weighted components (0-100 each)
    response_score: float = 0.0  # 40% weight
    qualification_score: float = 0.0  # 30% weight
    conversion_score: float = 0.0  # 20% weight
    opt_out_score: float = 0.0  # 5% weight (penalty)
    delivery_score: float = 0.0  # 5% weight

    # Final composite score (0-100)
    composite_score: float = 0.0

    # Sample size
    total_sent: int = 0
    total_responses: int = 0

    # Recommendation
    recommendation: str = ""  # "Winning template", "Good performer", "Test more", "Archive"


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

    def _generate_summary(self, filtered_leads: Optional[List[LeadRecord]] = None) -> Dict[str, Any]:
        """
        Generate overall summary metrics.

        Args:
            filtered_leads: Optional list of leads to include (filters by business_id)
        """
        leads_to_use = filtered_leads if filtered_leads is not None else list(self.leads.values())

        # Calculate metrics from filtered leads
        total_sent = sum(len(lead.touches) for lead in leads_to_use)
        total_responses = sum(1 for lead in leads_to_use if lead.has_responded)
        total_converted = sum(1 for lead in leads_to_use if lead.funnel_stage == "converted")
        total_revenue = sum(lead.conversion_value for lead in leads_to_use)

        return {
            "total_campaigns": len(self.campaigns),
            "total_leads": len(leads_to_use),
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

            # Extract business_id from record
            sending_business_id = record.get("sending_business_id", "")

            # Create or update lead record
            if lead_id not in self.leads:
                self.leads[lead_id] = LeadRecord(
                    lead_id=lead_id,
                    business_name=business_name,
                    phone=phone,
                    campaign_id=campaign_id,
                    sending_business_id=sending_business_id,
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

            # Auto-create ClickUp task for qualified leads (hot/warm only)
            if not lead.clickup_task_id:  # Don't create duplicate tasks
                task_id = self._create_clickup_task(lead, category, response_text)
                if task_id:
                    lead.clickup_task_id = task_id
                    print(f"✅ Created ClickUp task for {lead.business_name}: {task_id}")

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

    def _create_clickup_task(
        self,
        lead: LeadRecord,
        category: str,
        response_text: str
    ) -> Optional[str]:
        """
        Create a ClickUp task for a qualified lead (hot/warm only).

        Args:
            lead: LeadRecord with response
            category: hot_lead or warm_lead
            response_text: The lead's response message

        Returns:
            Task ID if created, None if failed
        """
        import requests

        # Get ClickUp credentials from environment
        api_token = os.getenv("CLICKUP_API_TOKEN")
        list_id = os.getenv("CLICKUP_LIST_ID")

        if not api_token or not list_id:
            print("⚠️  ClickUp credentials not configured (CLICKUP_API_TOKEN, CLICKUP_LIST_ID)")
            return None

        # Determine priority (hot = urgent, warm = high)
        priority_map = {
            "hot_lead": 1,  # Urgent
            "warm_lead": 2,  # High
        }
        priority = priority_map.get(category, 3)

        # Create task payload
        task_name = f"{lead.business_name} - {category.replace('_', ' ').title()}"

        description = f"""**Lead Response Received**

**Business:** {lead.business_name}
**Phone:** {lead.phone}
**Category:** {category.replace('_', ' ').title()}
**Response:** "{response_text}"

**Campaign:** {lead.campaign_id}
**Touch #{lead.converting_touch_number}** got the response
**Days to response:** {lead.days_to_first_response:.1f} days

**Next Steps:**
- [ ] Call/text back within 24 hours
- [ ] Qualify needs and pain points
- [ ] Schedule discovery call
- [ ] Send proposal

---
*Auto-created by Campaign Analytics*
"""

        payload = {
            "name": task_name,
            "description": description,
            "priority": priority,
            "status": "to do",
            "tags": [category, "sms_outreach", f"touch_{lead.converting_touch_number}"]
        }

        # API request
        headers = {
            "Authorization": api_token,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                f"https://api.clickup.com/api/v2/list/{list_id}/task",
                headers=headers,
                json=payload
            )

            if response.status_code == 200:
                task_data = response.json()
                task_id = task_data.get("id")
                return task_id
            else:
                print(f"❌ ClickUp API error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"❌ Failed to create ClickUp task: {e}")
            return None

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

    def get_report(self, business_id: Optional[str] = None) -> str:
        """
        Generate comprehensive analytics report.

        Args:
            business_id: Filter by business (marceau-solutions, swflorida-hvac, shipping-logistics)
                        If None, show all businesses with separate sections
        """
        lines = []
        lines.append("=" * 70)
        lines.append("CAMPAIGN ANALYTICS REPORT")
        if business_id:
            lines.append(f"Business Filter: {business_id}")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 70)

        # Filter leads by business_id if specified
        filtered_leads = self.leads.values()
        if business_id:
            filtered_leads = [lead for lead in self.leads.values() if lead.sending_business_id == business_id]

        summary = self._generate_summary(filtered_leads=list(filtered_leads))

        lines.append("\n## OVERALL SUMMARY")
        lines.append(f"Total Campaigns: {summary['total_campaigns']}")
        lines.append(f"Total Leads: {summary['total_leads']}")
        lines.append(f"Total Messages Sent: {summary['total_messages_sent']}")
        lines.append(f"Total Responses: {summary['total_responses']}")
        lines.append(f"Overall Response Rate: {summary['overall_response_rate']:.1f}%")
        lines.append(f"Total Conversions: {summary['total_conversions']}")
        lines.append(f"Total Revenue: ${summary['total_revenue']:,.2f}")

        # If no business filter, show per-business breakdowns
        if not business_id:
            # Group leads by business
            leads_by_business = defaultdict(list)
            for lead in self.leads.values():
                biz_id = lead.sending_business_id or "unknown"
                leads_by_business[biz_id].append(lead)

            if leads_by_business:
                lines.append("\n## PER-BUSINESS PERFORMANCE")
                lines.append("-" * 70)

                for biz_id in sorted(leads_by_business.keys()):
                    biz_leads = leads_by_business[biz_id]
                    biz_summary = self._generate_summary(filtered_leads=biz_leads)

                    lines.append(f"\n### {biz_id.upper()}")
                    lines.append(f"Total Contacts: {biz_summary['total_leads']}")
                    lines.append(f"Messages Sent: {biz_summary['total_messages_sent']}")
                    lines.append(f"Responses: {biz_summary['total_responses']}")
                    lines.append(f"Response Rate: {biz_summary['overall_response_rate']:.1f}%")

                    # Hot/Warm/Cold breakdown
                    hot = sum(1 for lead in biz_leads if lead.response_category == "hot_lead")
                    warm = sum(1 for lead in biz_leads if lead.response_category == "warm_lead")
                    cold = sum(1 for lead in biz_leads if lead.response_category == "cold_lead")

                    if hot + warm + cold > 0:
                        lines.append(f"  Hot Leads: {hot}")
                        lines.append(f"  Warm Leads: {warm}")
                        lines.append(f"  Cold Leads: {cold}")

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

    def get_dashboard(self, business_id: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
        """
        Generate comprehensive campaign performance dashboard.

        Args:
            business_id: Filter by business (marceau-solutions, swflorida-hvac, shipping-logistics)
            days: Time window for trends (7, 30, or 90 days)

        Returns:
            Dict with dashboard data
        """
        # Filter leads by business and date range
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_leads = []

        for lead in self.leads.values():
            # Filter by business
            if business_id and lead.sending_business_id != business_id:
                continue

            # Filter by date range
            if lead.first_contact_date:
                try:
                    contact_dt = datetime.fromisoformat(lead.first_contact_date)
                    if contact_dt < cutoff_date:
                        continue
                except:
                    pass

            filtered_leads.append(lead)

        # Calculate metrics
        total_sent = sum(len(lead.touches) for lead in filtered_leads)
        total_delivered = sum(1 for lead in filtered_leads for t in lead.touches if t.status == "delivered")
        total_responses = sum(1 for lead in filtered_leads if lead.has_responded)

        hot_leads = sum(1 for lead in filtered_leads if lead.response_category == "hot_lead")
        warm_leads = sum(1 for lead in filtered_leads if lead.response_category == "warm_lead")
        cold_leads = sum(1 for lead in filtered_leads if lead.response_category == "cold_lead")
        opt_outs = sum(1 for lead in filtered_leads if lead.response_category == "opt_out")

        qualified = hot_leads + warm_leads
        converted = sum(1 for lead in filtered_leads if lead.funnel_stage == "converted")

        # Calculate rates
        delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
        response_rate = (total_responses / total_sent * 100) if total_sent > 0 else 0
        qualification_rate = (qualified / total_responses * 100) if total_responses > 0 else 0
        conversion_rate = (converted / qualified * 100) if qualified > 0 else 0
        opt_out_rate = (opt_outs / total_sent * 100) if total_sent > 0 else 0

        # Response time analysis
        response_times = [lead.days_to_first_response for lead in filtered_leads
                         if lead.has_responded and lead.days_to_first_response > 0]
        median_time_to_response = sorted(response_times)[len(response_times)//2] * 24 if response_times else 0

        # Template leaderboard (top 3)
        template_performance = defaultdict(lambda: {"sent": 0, "responses": 0, "rate": 0})

        for lead in filtered_leads:
            for touch in lead.touches:
                template = touch.template
                template_performance[template]["sent"] += 1
                if touch.response_received:
                    template_performance[template]["responses"] += 1

        for template, data in template_performance.items():
            if data["sent"] > 0:
                data["rate"] = data["responses"] / data["sent"] * 100

        top_templates = sorted(template_performance.items(),
                              key=lambda x: x[1]["rate"],
                              reverse=True)[:3]

        # Time-series trends (by week)
        weeks_data = defaultdict(lambda: {"sent": 0, "responses": 0, "rate": 0})

        for lead in filtered_leads:
            for touch in lead.touches:
                if touch.sent_at:
                    try:
                        sent_dt = datetime.fromisoformat(touch.sent_at.replace("Z", "+00:00"))
                        week_key = sent_dt.strftime("%Y-W%U")
                        weeks_data[week_key]["sent"] += 1
                        if touch.response_received:
                            weeks_data[week_key]["responses"] += 1
                    except:
                        pass

        for week, data in weeks_data.items():
            if data["sent"] > 0:
                data["rate"] = data["responses"] / data["sent"] * 100

        # Business comparison (if no filter)
        business_comparison = {}
        if not business_id:
            for biz_id in ["marceau-solutions", "swflorida-hvac", "shipping-logistics"]:
                biz_leads = [l for l in filtered_leads if l.sending_business_id == biz_id]
                if biz_leads:
                    biz_sent = sum(len(l.touches) for l in biz_leads)
                    biz_responses = sum(1 for l in biz_leads if l.has_responded)
                    business_comparison[biz_id] = {
                        "sent": biz_sent,
                        "responses": biz_responses,
                        "response_rate": (biz_responses / biz_sent * 100) if biz_sent > 0 else 0,
                        "hot_leads": sum(1 for l in biz_leads if l.response_category == "hot_lead"),
                        "warm_leads": sum(1 for l in biz_leads if l.response_category == "warm_lead")
                    }

        dashboard = {
            "business_id": business_id or "all",
            "time_window_days": days,
            "summary_metrics": {
                "total_sent": total_sent,
                "delivery_rate": round(delivery_rate, 1),
                "response_rate": round(response_rate, 1),
                "qualification_rate": round(qualification_rate, 1),
                "conversion_rate": round(conversion_rate, 1),
                "opt_out_rate": round(opt_out_rate, 1),
                "median_time_to_response_hours": round(median_time_to_response, 1)
            },
            "breakdown": {
                "hot_leads": hot_leads,
                "warm_leads": warm_leads,
                "cold_leads": cold_leads,
                "opt_outs": opt_outs
            },
            "funnel": {
                "contacted": len(filtered_leads),
                "responded": total_responses,
                "qualified": qualified,
                "converted": converted
            },
            "top_templates": [
                {
                    "template": template,
                    "sent": data["sent"],
                    "responses": data["responses"],
                    "rate": round(data["rate"], 1)
                }
                for template, data in top_templates
            ],
            "trends": {
                "by_week": dict(sorted(weeks_data.items()))
            },
            "business_comparison": business_comparison
        }

        return dashboard

    def print_dashboard(self, business_id: Optional[str] = None, days: int = 30) -> str:
        """Generate formatted dashboard report."""
        dashboard = self.get_dashboard(business_id, days)

        lines = []
        lines.append("=" * 80)
        lines.append("CAMPAIGN PERFORMANCE DASHBOARD")
        lines.append(f"Business: {dashboard['business_id'].upper()}")
        lines.append(f"Time Window: Last {days} days")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 80)

        # Summary metrics
        metrics = dashboard["summary_metrics"]
        lines.append("\n## KEY METRICS")
        lines.append("-" * 80)
        lines.append(f"{'Metric':<30} {'Value':>15} {'Target':>15} {'Status':>10}")
        lines.append("-" * 80)

        # Define targets based on business
        targets = {
            "marceau-solutions": {"response_rate": 12, "qualification_rate": 50, "conversion_rate": 20},
            "swflorida-hvac": {"response_rate": 8, "qualification_rate": 50, "conversion_rate": 20},
            "shipping-logistics": {"response_rate": 6, "qualification_rate": 50, "conversion_rate": 20},
            "all": {"response_rate": 10, "qualification_rate": 50, "conversion_rate": 20}
        }

        target_set = targets.get(dashboard["business_id"], targets["all"])

        def status_icon(actual, target):
            if actual >= target:
                return "✅"
            elif actual >= target * 0.8:
                return "⚠️"
            else:
                return "❌"

        lines.append(f"{'Total Messages Sent':<30} {metrics['total_sent']:>15,} {'-':>15} {'-':>10}")
        lines.append(f"{'Delivery Rate':<30} {metrics['delivery_rate']:>14.1f}% {'>95%':>15} {status_icon(metrics['delivery_rate'], 95):>10}")
        lines.append(f"{'Response Rate':<30} {metrics['response_rate']:>14.1f}% {target_set['response_rate']:>14.0f}% {status_icon(metrics['response_rate'], target_set['response_rate']):>10}")
        lines.append(f"{'Qualification Rate':<30} {metrics['qualification_rate']:>14.1f}% {target_set['qualification_rate']:>14.0f}% {status_icon(metrics['qualification_rate'], target_set['qualification_rate']):>10}")
        lines.append(f"{'Conversion Rate':<30} {metrics['conversion_rate']:>14.1f}% {target_set['conversion_rate']:>14.0f}% {status_icon(metrics['conversion_rate'], target_set['conversion_rate']):>10}")
        lines.append(f"{'Opt-out Rate':<30} {metrics['opt_out_rate']:>14.1f}% {'<2%':>15} {status_icon(2 - metrics['opt_out_rate'], 0):>10}")
        lines.append(f"{'Median Time to Response':<30} {metrics['median_time_to_response_hours']:>13.1f}h {'-':>15} {'-':>10}")

        # Breakdown
        breakdown = dashboard["breakdown"]
        lines.append("\n## RESPONSE BREAKDOWN")
        lines.append(f"  Hot Leads:  {breakdown['hot_leads']:>3}")
        lines.append(f"  Warm Leads: {breakdown['warm_leads']:>3}")
        lines.append(f"  Cold Leads: {breakdown['cold_leads']:>3}")
        lines.append(f"  Opt-outs:   {breakdown['opt_outs']:>3}")

        # Funnel
        funnel = dashboard["funnel"]
        lines.append("\n## CONVERSION FUNNEL")
        max_width = 50
        if funnel["contacted"] > 0:
            for stage, count in [
                ("Contacted", funnel["contacted"]),
                ("Responded", funnel["responded"]),
                ("Qualified", funnel["qualified"]),
                ("Converted", funnel["converted"])
            ]:
                pct = (count / funnel["contacted"]) * 100
                bar_width = int((count / funnel["contacted"]) * max_width)
                bar = "█" * bar_width + "░" * (max_width - bar_width)
                lines.append(f"{stage:<12} {bar} {count:>4} ({pct:>5.1f}%)")

        # Top templates
        lines.append("\n## TOP 3 TEMPLATES")
        lines.append(f"{'Template':<35} {'Sent':>6} {'Resp':>6} {'Rate':>8}")
        lines.append("-" * 60)
        for template_data in dashboard["top_templates"]:
            lines.append(f"{template_data['template'][:35]:<35} "
                        f"{template_data['sent']:>6} "
                        f"{template_data['responses']:>6} "
                        f"{template_data['rate']:>7.1f}%")

        # Business comparison (if showing all)
        if dashboard["business_comparison"]:
            lines.append("\n## BUSINESS COMPARISON")
            lines.append(f"{'Business':<25} {'Sent':>8} {'Resp':>8} {'Rate':>8} {'Hot':>5} {'Warm':>5}")
            lines.append("-" * 70)
            for biz_id, biz_data in dashboard["business_comparison"].items():
                lines.append(f"{biz_id:<25} "
                           f"{biz_data['sent']:>8} "
                           f"{biz_data['responses']:>8} "
                           f"{biz_data['response_rate']:>7.1f}% "
                           f"{biz_data['hot_leads']:>5} "
                           f"{biz_data['warm_leads']:>5}")

        # Trends
        lines.append("\n## RESPONSE RATE TRENDS")
        lines.append(f"{'Week':<12} {'Sent':>6} {'Resp':>6} {'Rate':>8}")
        lines.append("-" * 40)
        for week, week_data in list(dashboard["trends"]["by_week"].items())[-4:]:  # Last 4 weeks
            lines.append(f"{week:<12} "
                        f"{week_data['sent']:>6} "
                        f"{week_data['responses']:>6} "
                        f"{week_data['rate']:>7.1f}%")

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)

    def get_attribution_analysis(self, business_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze which touch points drive responses (multi-touch attribution).

        Args:
            business_id: Filter by business

        Returns:
            Dict with attribution data
        """
        # Filter leads
        filtered_leads = self.leads.values()
        if business_id:
            filtered_leads = [l for l in self.leads.values() if l.sending_business_id == business_id]

        # Only include leads that responded
        responded_leads = [l for l in filtered_leads if l.has_responded and l.converting_touch_number > 0]

        if not responded_leads:
            return {
                "total_responses": 0,
                "by_touch": {},
                "recommendations": []
            }

        # Count responses by touch number
        responses_by_touch = defaultdict(int)
        for lead in responded_leads:
            touch_num = lead.converting_touch_number
            responses_by_touch[touch_num] += 1

        total_responses = len(responded_leads)

        # Calculate percentages
        touch_distribution = {}
        for touch_num, count in responses_by_touch.items():
            pct = (count / total_responses) * 100
            touch_distribution[touch_num] = {
                "count": count,
                "percentage": round(pct, 1)
            }

        # Find most effective touch
        most_effective = max(responses_by_touch.items(), key=lambda x: x[1])
        most_effective_touch = most_effective[0]
        most_effective_pct = (most_effective[1] / total_responses) * 100

        # Generate recommendations
        recommendations = []

        # Recommendation 1: Optimize most effective touch
        if most_effective_pct > 25:
            recommendations.append({
                "priority": "high",
                "insight": f"Touch #{most_effective_touch} drives {most_effective_pct:.0f}% of all responses",
                "action": f"Prioritize optimizing the Touch #{most_effective_touch} message template for maximum impact"
            })

        # Recommendation 2: Drop-off analysis
        max_touch = max(responses_by_touch.keys())
        if max_touch >= 3:
            late_responses = sum(count for touch, count in responses_by_touch.items() if touch >= 3)
            late_pct = (late_responses / total_responses) * 100
            if late_pct > 20:
                recommendations.append({
                    "priority": "medium",
                    "insight": f"{late_pct:.0f}% of responses come from touch 3+",
                    "action": "Don't give up early - persistence pays off"
                })

        # Recommendation 3: Touch 1 performance
        touch_1_pct = touch_distribution.get(1, {}).get("percentage", 0)
        if touch_1_pct < 20:
            recommendations.append({
                "priority": "high",
                "insight": f"Only {touch_1_pct:.0f}% respond to initial message",
                "action": "Test more compelling intro templates to increase Touch 1 conversion"
            })

        # Calculate average touch to conversion
        avg_touch = sum(lead.converting_touch_number for lead in responded_leads) / len(responded_leads)

        return {
            "business_id": business_id or "all",
            "total_responses": total_responses,
            "by_touch": dict(sorted(touch_distribution.items())),
            "most_effective_touch": most_effective_touch,
            "most_effective_percentage": round(most_effective_pct, 1),
            "average_touch_to_conversion": round(avg_touch, 1),
            "max_touches_needed": max_touch,
            "recommendations": recommendations
        }

    def print_attribution(self, business_id: Optional[str] = None) -> str:
        """Generate formatted attribution report."""
        data = self.get_attribution_analysis(business_id)

        lines = []
        lines.append("=" * 80)
        lines.append("MULTI-TOUCH ATTRIBUTION ANALYSIS")
        lines.append(f"Business: {data['business_id'].upper()}")
        lines.append("=" * 80)

        if data["total_responses"] == 0:
            lines.append("\nNo response data available yet.")
            return "\n".join(lines)

        lines.append(f"\nTotal Responses: {data['total_responses']}")
        lines.append(f"Average Touch to Conversion: {data['average_touch_to_conversion']:.1f}")
        lines.append(f"Max Touches Before Conversion: {data['max_touches_needed']}")

        lines.append("\n## RESPONSES BY TOUCH NUMBER")
        lines.append(f"{'Touch #':<10} {'Count':>8} {'Percentage':>12} {'Bar':<40}")
        lines.append("-" * 75)

        max_width = 40
        for touch_num, touch_data in data["by_touch"].items():
            count = touch_data["count"]
            pct = touch_data["percentage"]
            bar_width = int((pct / 100) * max_width)
            bar = "█" * bar_width + "░" * (max_width - bar_width)

            icon = "🏆" if touch_num == data["most_effective_touch"] else "  "
            lines.append(f"{icon} Touch #{touch_num:<6} {count:>8} {pct:>11.1f}% {bar}")

        lines.append(f"\n🏆 MOST EFFECTIVE: Touch #{data['most_effective_touch']} "
                    f"({data['most_effective_percentage']:.0f}% of all responses)")

        # Drop-off insights
        lines.append("\n## DROP-OFF INSIGHTS")

        # Touch 1 vs later touches
        touch_1_pct = data["by_touch"].get(1, {}).get("percentage", 0)
        later_pct = 100 - touch_1_pct

        lines.append(f"  Initial touch (Touch 1):     {touch_1_pct:.1f}%")
        lines.append(f"  Follow-up touches (2+):      {later_pct:.1f}%")

        if later_pct > 50:
            lines.append(f"\n  💡 Insight: {later_pct:.0f}% of responses require follow-up")
            lines.append(f"     Multi-touch sequences are CRITICAL to success")

        # Recommendations
        if data["recommendations"]:
            lines.append("\n## OPTIMIZATION RECOMMENDATIONS")
            for i, rec in enumerate(data["recommendations"], 1):
                priority_icon = "🔴" if rec["priority"] == "high" else "🟡"
                lines.append(f"\n{i}. {priority_icon} {rec['insight']}")
                lines.append(f"   → ACTION: {rec['action']}")

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)

    def calculate_template_score(self, template_name: str, business_id: Optional[str] = None) -> TemplateScore:
        """
        Calculate composite performance score for a template.

        Scoring formula:
        - Response rate: 40% weight
        - Qualification rate (hot+warm/responses): 30% weight
        - Conversion rate (converted/qualified): 20% weight
        - Opt-out rate: 5% weight (penalty - lower is better)
        - Delivery rate: 5% weight

        Returns score 0-100.
        """
        # Get template metrics
        template_metrics = None
        for lead in self.leads.values():
            if business_id and lead.sending_business_id != business_id:
                continue

            for touch in lead.touches:
                if touch.template == template_name:
                    # Found this template - aggregate metrics
                    if template_metrics is None:
                        template_metrics = {
                            "sent": 0,
                            "delivered": 0,
                            "responses": 0,
                            "hot": 0,
                            "warm": 0,
                            "opt_outs": 0,
                            "qualified": 0,
                            "converted": 0
                        }

                    template_metrics["sent"] += 1
                    if touch.status == "delivered":
                        template_metrics["delivered"] += 1
                    if touch.response_received:
                        template_metrics["responses"] += 1
                        if touch.response_category == "hot_lead":
                            template_metrics["hot"] += 1
                            template_metrics["qualified"] += 1
                        elif touch.response_category == "warm_lead":
                            template_metrics["warm"] += 1
                            template_metrics["qualified"] += 1
                        elif touch.response_category == "opt_out":
                            template_metrics["opt_outs"] += 1

                    # Check if lead converted
                    if lead.funnel_stage in ["meeting", "converted"]:
                        template_metrics["converted"] += 1

        if template_metrics is None or template_metrics["sent"] == 0:
            return TemplateScore(template_name=template_name, recommendation="Insufficient data")

        # Calculate raw rates
        delivery_rate = template_metrics["delivered"] / template_metrics["sent"] if template_metrics["sent"] > 0 else 0
        response_rate = template_metrics["responses"] / template_metrics["sent"] if template_metrics["sent"] > 0 else 0
        qualification_rate = (template_metrics["hot"] + template_metrics["warm"]) / template_metrics["responses"] if template_metrics["responses"] > 0 else 0
        conversion_rate = template_metrics["converted"] / template_metrics["qualified"] if template_metrics["qualified"] > 0 else 0
        opt_out_rate = template_metrics["opt_outs"] / template_metrics["responses"] if template_metrics["responses"] > 0 else 0

        # Normalize to 0-100 scales
        # Response rate: 0% = 0, 15% = 100 (15% is excellent for cold outreach)
        response_score = min((response_rate / 0.15) * 100, 100)

        # Qualification rate: 0% = 0, 60% = 100 (60% hot/warm is excellent)
        qualification_score = min((qualification_rate / 0.60) * 100, 100)

        # Conversion rate: 0% = 0, 25% = 100 (25% qualified-to-converted is excellent)
        conversion_score = min((conversion_rate / 0.25) * 100, 100)

        # Opt-out rate: 0% = 100, 5% = 0 (penalty - lower is better)
        opt_out_score = max(100 - (opt_out_rate / 0.05) * 100, 0)

        # Delivery rate: 90% = 0, 100% = 100
        delivery_score = max((delivery_rate - 0.90) / 0.10 * 100, 0)

        # Composite score (weighted average)
        composite = (
            response_score * 0.40 +
            qualification_score * 0.30 +
            conversion_score * 0.20 +
            opt_out_score * 0.05 +
            delivery_score * 0.05
        )

        # Recommendation based on score and sample size
        if template_metrics["sent"] < 100:
            recommendation = "Test more (need 100+ sends)"
        elif composite >= 75:
            recommendation = "🏆 Winning template - scale up"
        elif composite >= 60:
            recommendation = "✅ Good performer - keep using"
        elif composite >= 50:
            recommendation = "⚠️ Acceptable - monitor closely"
        else:
            recommendation = "❌ Archive - underperforming"

        return TemplateScore(
            template_name=template_name,
            response_rate=response_rate,
            qualification_rate=qualification_rate,
            conversion_rate=conversion_rate,
            opt_out_rate=opt_out_rate,
            delivery_rate=delivery_rate,
            response_score=response_score,
            qualification_score=qualification_score,
            conversion_score=conversion_score,
            opt_out_score=opt_out_score,
            delivery_score=delivery_score,
            composite_score=composite,
            total_sent=template_metrics["sent"],
            total_responses=template_metrics["responses"],
            recommendation=recommendation
        )

    def get_all_template_scores(self, business_id: Optional[str] = None, sort_by: str = "score") -> List[TemplateScore]:
        """Get scores for all templates, sorted by performance."""
        # Collect all unique templates
        templates = set()
        for lead in self.leads.values():
            if business_id and lead.sending_business_id != business_id:
                continue
            for touch in lead.touches:
                templates.add(touch.template)

        # Score each template
        scores = []
        for template in templates:
            score = self.calculate_template_score(template, business_id)
            if score.total_sent > 0:  # Only include templates that have been used
                scores.append(score)

        # Sort
        if sort_by == "score":
            scores.sort(key=lambda s: s.composite_score, reverse=True)
        elif sort_by == "responses":
            scores.sort(key=lambda s: s.total_responses, reverse=True)
        elif sort_by == "name":
            scores.sort(key=lambda s: s.template_name)

        return scores

    def print_template_scores(self, business_id: Optional[str] = None, sort_by: str = "score") -> str:
        """Generate formatted template leaderboard."""
        scores = self.get_all_template_scores(business_id, sort_by)

        lines = []
        lines.append("=" * 100)
        lines.append("TEMPLATE PERFORMANCE LEADERBOARD")
        if business_id:
            lines.append(f"Business: {business_id.upper()}")
        lines.append("=" * 100)

        if not scores:
            lines.append("\nNo template data available yet.")
            return "\n".join(lines)

        lines.append(f"\n{'Rank':<6} {'Template':<35} {'Score':>7} {'Sent':>7} {'Resp':>7} {'Qual':>7} {'Conv':>7} {'Recommendation':<25}")
        lines.append("-" * 100)

        for rank, score in enumerate(scores, 1):
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "

            lines.append(
                f"{medal} {rank:<4} {score.template_name:<35} "
                f"{score.composite_score:>6.1f} "
                f"{score.total_sent:>7} "
                f"{score.response_rate * 100:>6.1f}% "
                f"{score.qualification_rate * 100:>6.1f}% "
                f"{score.conversion_rate * 100:>6.1f}% "
                f"{score.recommendation}"
            )

        lines.append("\n## SCORING FORMULA")
        lines.append("  Response Rate:      40% weight (target: 12-15%)")
        lines.append("  Qualification Rate: 30% weight (target: 50-60% hot/warm)")
        lines.append("  Conversion Rate:    20% weight (target: 20-25% qualified→converted)")
        lines.append("  Opt-out Rate:        5% weight (penalty - target: <2%)")
        lines.append("  Delivery Rate:       5% weight (target: >95%)")

        lines.append("\n" + "=" * 100)

        return "\n".join(lines)

    def get_cohort_analysis(self, group_by: str = "category", business_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze performance by cohort.

        Args:
            group_by: Dimension to group by (category, pain_point, scrape_date, location)
            business_id: Filter by business

        Returns:
            Dict with cohort performance data
        """
        cohorts = defaultdict(lambda: {
            "total_sent": 0,
            "total_responses": 0,
            "hot_leads": 0,
            "warm_leads": 0,
            "cold_leads": 0,
            "converted": 0
        })

        for lead in self.leads.values():
            if business_id and lead.sending_business_id != business_id:
                continue

            # Determine cohort key
            cohort_key = "unknown"

            if group_by == "category":
                # Extract category from business_name or tags (simplified)
                business_lower = lead.business_name.lower()
                if "gym" in business_lower or "fitness" in business_lower:
                    cohort_key = "gym"
                elif "salon" in business_lower or "spa" in business_lower or "beauty" in business_lower:
                    cohort_key = "salon"
                elif "restaurant" in business_lower or "cafe" in business_lower or "food" in business_lower:
                    cohort_key = "restaurant"
                elif "retail" in business_lower or "store" in business_lower:
                    cohort_key = "retail"
                elif "ecommerce" in business_lower or "online" in business_lower:
                    cohort_key = "ecommerce"

            elif group_by == "pain_point":
                # Get from campaign (would need to track this - simplified)
                cohort_key = "no_website"  # Placeholder

            elif group_by == "scrape_date":
                # Group by week
                if lead.first_contact_date:
                    try:
                        date_obj = datetime.fromisoformat(lead.first_contact_date.replace("Z", "+00:00"))
                        week_start = date_obj - timedelta(days=date_obj.weekday())
                        cohort_key = week_start.strftime("%Y-%m-%d")
                    except:
                        cohort_key = "unknown"

            elif group_by == "location":
                # Extract from business_name (simplified)
                business_lower = lead.business_name.lower()
                if "naples" in business_lower:
                    cohort_key = "naples"
                elif "fort myers" in business_lower or "ft myers" in business_lower:
                    cohort_key = "fort_myers"
                elif "bonita" in business_lower:
                    cohort_key = "bonita_springs"

            # Increment cohort metrics
            if lead.total_touches > 0:
                cohorts[cohort_key]["total_sent"] += 1

            if lead.has_responded:
                cohorts[cohort_key]["total_responses"] += 1

                if lead.response_category == "hot_lead":
                    cohorts[cohort_key]["hot_leads"] += 1
                elif lead.response_category == "warm_lead":
                    cohorts[cohort_key]["warm_leads"] += 1
                else:
                    cohorts[cohort_key]["cold_leads"] += 1

            if lead.funnel_stage in ["meeting", "converted"]:
                cohorts[cohort_key]["converted"] += 1

        # Calculate rates
        cohort_results = {}
        for cohort, metrics in cohorts.items():
            response_rate = metrics["total_responses"] / metrics["total_sent"] if metrics["total_sent"] > 0 else 0
            qualification_rate = (metrics["hot_leads"] + metrics["warm_leads"]) / metrics["total_responses"] if metrics["total_responses"] > 0 else 0
            conversion_rate = metrics["converted"] / metrics["total_sent"] if metrics["total_sent"] > 0 else 0

            cohort_results[cohort] = {
                **metrics,
                "response_rate": response_rate,
                "qualification_rate": qualification_rate,
                "conversion_rate": conversion_rate
            }

        # Sort by response rate
        sorted_cohorts = sorted(
            cohort_results.items(),
            key=lambda x: x[1]["response_rate"],
            reverse=True
        )

        return {
            "group_by": group_by,
            "business_id": business_id or "all",
            "cohorts": dict(sorted_cohorts),
            "best_cohort": sorted_cohorts[0][0] if sorted_cohorts else None,
            "best_response_rate": sorted_cohorts[0][1]["response_rate"] if sorted_cohorts else 0
        }

    def print_cohort_analysis(self, group_by: str = "category", business_id: Optional[str] = None) -> str:
        """Generate formatted cohort analysis report."""
        data = self.get_cohort_analysis(group_by, business_id)

        lines = []
        lines.append("=" * 90)
        lines.append(f"COHORT ANALYSIS: {group_by.upper().replace('_', ' ')}")
        if business_id:
            lines.append(f"Business: {business_id.upper()}")
        lines.append("=" * 90)

        if not data["cohorts"]:
            lines.append("\nNo cohort data available yet.")
            return "\n".join(lines)

        lines.append(f"\n{'Cohort':<20} {'Sent':>8} {'Resp':>8} {'Rate':>8} {'Qual':>8} {'Conv':>8} {'Performance':<20}")
        lines.append("-" * 90)

        for rank, (cohort, metrics) in enumerate(data["cohorts"].items(), 1):
            icon = "🏆" if cohort == data["best_cohort"] else "  "

            perf = ""
            if metrics["response_rate"] >= 0.12:
                perf = "🟢 Excellent"
            elif metrics["response_rate"] >= 0.08:
                perf = "🟡 Good"
            elif metrics["response_rate"] >= 0.05:
                perf = "🟠 Fair"
            else:
                perf = "🔴 Poor"

            lines.append(
                f"{icon} {cohort:<18} "
                f"{metrics['total_sent']:>8} "
                f"{metrics['total_responses']:>8} "
                f"{metrics['response_rate'] * 100:>7.1f}% "
                f"{metrics['qualification_rate'] * 100:>7.1f}% "
                f"{metrics['conversion_rate'] * 100:>7.1f}% "
                f"{perf}"
            )

        lines.append(f"\n🏆 BEST PERFORMING COHORT: {data['best_cohort']} ({data['best_response_rate'] * 100:.1f}% response rate)")

        # Recommendations
        lines.append("\n## OPTIMIZATION RECOMMENDATIONS")
        best_3 = list(data["cohorts"].items())[:3]
        if len(best_3) >= 2:
            top_cohort = best_3[0][0]
            top_rate = best_3[0][1]["response_rate"]
            bottom_rate = list(data["cohorts"].values())[-1]["response_rate"]

            if top_rate > bottom_rate * 1.5:
                lines.append(f"  1. 🔥 PRIORITIZE: Focus 60-70% of outreach on '{top_cohort}' cohort")
                lines.append(f"     → {top_rate * 100:.0f}% response rate vs {bottom_rate * 100:.0f}% for worst cohort")

            if len(best_3) >= 3:
                top_3_cohorts = ", ".join([c[0] for c in best_3])
                lines.append(f"  2. 📊 ALLOCATE: Target top 3 cohorts: {top_3_cohorts}")

        lines.append("\n" + "=" * 90)

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Campaign Analytics Engine")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Update command
    update_parser = subparsers.add_parser("update", help="Import/update analytics from campaign data")
    update_parser.add_argument("--campaign-id", help="Campaign ID to assign")

    # Report command
    report_parser = subparsers.add_parser("report", help="Show comprehensive analytics report")
    report_parser.add_argument("--business", help="Filter by business ID (marceau-solutions, swflorida-hvac, shipping-logistics)")

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
    export_parser.add_argument("--business", help="Filter by business ID")

    # Dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Campaign performance dashboard")
    dashboard_parser.add_argument("--business", help="Filter by business ID (marceau-solutions, swflorida-hvac, shipping-logistics)")
    dashboard_parser.add_argument("--days", type=int, default=30, help="Time window for trends (7, 30, or 90 days)")
    dashboard_parser.add_argument("--export", choices=["csv", "json"], help="Export dashboard data")

    # Attribution command
    attribution_parser = subparsers.add_parser("attribution", help="Multi-touch attribution analysis")
    attribution_parser.add_argument("--business", help="Filter by business ID")

    # Template scoring command
    scoring_parser = subparsers.add_parser("template-scores", help="Template performance scoring (0-100)")
    scoring_parser.add_argument("--business", help="Filter by business ID")
    scoring_parser.add_argument("--sort-by", choices=["score", "responses", "name"], default="score", help="Sort templates by")

    # Cohort analysis command
    cohort_parser = subparsers.add_parser("cohorts", help="Cohort analysis (group by category, pain_point, date, location)")
    cohort_parser.add_argument("--group-by", choices=["category", "pain_point", "scrape_date", "location"], default="category", help="Dimension to group by")
    cohort_parser.add_argument("--business", help="Filter by business ID")

    args = parser.parse_args()

    # Change to project directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    analytics = CampaignAnalytics()

    if args.command == "update":
        analytics.import_from_campaigns(args.campaign_id)

    elif args.command == "report":
        print(analytics.get_report(business_id=getattr(args, 'business', None)))

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

    elif args.command == "dashboard":
        if args.export:
            dashboard_data = analytics.get_dashboard(business_id=args.business, days=args.days)
            if args.export == "json":
                print(json.dumps(dashboard_data, indent=2))
            else:
                # CSV export
                import csv
                import sys
                writer = csv.writer(sys.stdout)
                writer.writerow(["Metric", "Value"])
                for key, value in dashboard_data["summary_metrics"].items():
                    writer.writerow([key, value])
        else:
            print(analytics.print_dashboard(business_id=args.business, days=args.days))

    elif args.command == "attribution":
        print(analytics.print_attribution(business_id=args.business))

    elif args.command == "template-scores":
        print(analytics.print_template_scores(business_id=args.business, sort_by=args.sort_by))

    elif args.command == "cohorts":
        print(analytics.print_cohort_analysis(group_by=args.group_by, business_id=args.business))

    elif args.command == "export":
        business_filter = getattr(args, 'business', None)
        if args.format == "json":
            if business_filter:
                filtered_leads = [l for l in analytics.leads.values() if l.sending_business_id == business_filter]
                summary = analytics._generate_summary(filtered_leads=filtered_leads)
            else:
                summary = analytics._generate_summary()
            print(json.dumps(summary, indent=2))
        else:
            print("CSV export not yet implemented")

    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    exit(main())
