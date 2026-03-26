#!/usr/bin/env python3
"""
Response Tracker - Links SMS replies to templates for A/B testing analysis.

Per Hormozi's "100M Leads" framework:
1. Track every response and link to template that generated it
2. Calculate response rates by template (not just total)
3. Weekly optimization: shift volume to winning templates
4. Kill underperformers, test new variations

This module bridges the gap between:
- sms_campaigns.json (what we sent)
- sms_replies.json (what we received)
- outreach_optimizer.py (which templates to use next)

Usage:
    python -m src.response_tracker sync     # Link replies to templates
    python -m src.response_tracker report   # Show response rates by template
    python -m src.response_tracker weekly   # Weekly optimization review
    python -m src.response_tracker alert    # Check for concerning metrics
"""

import os
import json
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path)

logger = logging.getLogger(__name__)


@dataclass
class TemplateStats:
    """Performance stats for a single template."""
    template_name: str
    total_sent: int = 0
    total_responses: int = 0
    hot_leads: int = 0
    warm_leads: int = 0
    cold_leads: int = 0
    opt_outs: int = 0
    response_rate: float = 0.0
    quality_score: float = 0.0  # hot*3 + warm*2 + response*1 - optout*2


@dataclass
class ResponseLink:
    """Links a reply to the outreach that generated it."""
    reply_phone: str
    reply_body: str
    reply_category: str
    reply_date: str
    outreach_template: str
    outreach_date: str
    outreach_message_sid: str
    lead_id: str
    business_name: str
    days_to_response: float


class ResponseTracker:
    """
    Tracks and analyzes response rates by template.

    Implements Hormozi's optimization loop:
    1. MEASURE - Track response rates per template
    2. ANALYZE - Identify winners and losers
    3. OPTIMIZE - Shift volume to winners
    4. REPEAT - Weekly review cycle
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.campaigns_file = self.output_dir / "sms_campaigns.json"
        self.replies_file = self.output_dir / "sms_replies.json"
        self.linked_file = self.output_dir / "response_links.json"
        self.stats_file = self.output_dir / "template_stats.json"

        # Load data
        self.campaigns: List[Dict] = []
        self.replies: List[Dict] = []
        self.links: List[ResponseLink] = []
        self._load_data()

    def _load_data(self) -> None:
        """Load campaign and reply data."""
        if self.campaigns_file.exists():
            with open(self.campaigns_file, 'r') as f:
                data = json.load(f)
                self.campaigns = data.get("records", [])

        if self.replies_file.exists():
            with open(self.replies_file, 'r') as f:
                data = json.load(f)
                self.replies = data.get("replies", [])

        if self.linked_file.exists():
            with open(self.linked_file, 'r') as f:
                data = json.load(f)
                self.links = [ResponseLink(**link) for link in data.get("links", [])]

    def _save_links(self) -> None:
        """Save response links."""
        data = {
            "links": [asdict(link) for link in self.links],
            "updated_at": datetime.now().isoformat()
        }
        with open(self.linked_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone for matching."""
        return ''.join(c for c in phone if c.isdigit())[-10:]

    def sync_replies_to_templates(self) -> Dict[str, int]:
        """
        Link each reply to the template that generated it.

        Matches replies to campaigns by phone number.
        """
        stats = {"new_links": 0, "already_linked": 0, "no_match": 0}

        # Build lookup by phone
        campaigns_by_phone: Dict[str, Dict] = {}
        for campaign in self.campaigns:
            phone = self._normalize_phone(campaign.get("phone", ""))
            if phone:
                campaigns_by_phone[phone] = campaign

        # Existing link phones
        linked_phones = {self._normalize_phone(link.reply_phone) for link in self.links}

        for reply in self.replies:
            reply_phone = self._normalize_phone(reply.get("from_phone", ""))

            # Skip if already linked
            if reply_phone in linked_phones:
                stats["already_linked"] += 1
                continue

            # Find matching campaign
            campaign = campaigns_by_phone.get(reply_phone)
            if not campaign:
                stats["no_match"] += 1
                continue

            # Calculate days to response
            try:
                sent_date = datetime.fromisoformat(campaign.get("sent_at", "").replace("Z", "+00:00"))
                reply_date = datetime.fromisoformat(reply.get("date_sent", "").replace("Z", "+00:00"))
                days_to_response = (reply_date - sent_date).total_seconds() / 86400
            except:
                days_to_response = -1

            # Create link
            link = ResponseLink(
                reply_phone=reply.get("from_phone", ""),
                reply_body=reply.get("body", ""),
                reply_category=reply.get("category", "unknown"),
                reply_date=reply.get("date_sent", ""),
                outreach_template=campaign.get("template_used", "unknown"),
                outreach_date=campaign.get("sent_at", ""),
                outreach_message_sid=campaign.get("message_sid", ""),
                lead_id=campaign.get("lead_id", ""),
                business_name=reply.get("business_name", campaign.get("business_name", "")),
                days_to_response=days_to_response
            )

            self.links.append(link)
            linked_phones.add(reply_phone)
            stats["new_links"] += 1

            # Update campaign record status
            campaign["status"] = "responded" if reply.get("category") != "opt_out" else "opted_out"

        # Save updated links
        self._save_links()

        # Update campaigns file with response status
        with open(self.campaigns_file, 'w') as f:
            json.dump({
                "records": self.campaigns,
                "sent_today": {},
                "updated_at": datetime.now().isoformat()
            }, f, indent=2)

        return stats

    def get_template_stats(self) -> Dict[str, TemplateStats]:
        """Calculate stats for each template."""
        stats: Dict[str, TemplateStats] = {}

        # Count sends by template
        for campaign in self.campaigns:
            template = campaign.get("template_used", "unknown")
            if template not in stats:
                stats[template] = TemplateStats(template_name=template)
            stats[template].total_sent += 1

        # Count responses by template
        for link in self.links:
            template = link.outreach_template
            if template not in stats:
                stats[template] = TemplateStats(template_name=template)

            stats[template].total_responses += 1

            if link.reply_category == "hot_lead":
                stats[template].hot_leads += 1
            elif link.reply_category == "warm_lead":
                stats[template].warm_leads += 1
            elif link.reply_category == "cold_lead":
                stats[template].cold_leads += 1
            elif link.reply_category == "opt_out":
                stats[template].opt_outs += 1

        # Calculate rates and scores
        for template, s in stats.items():
            if s.total_sent > 0:
                s.response_rate = s.total_responses / s.total_sent
                # Quality score: hot=3, warm=2, response=1, opt_out=-2
                s.quality_score = (
                    s.hot_leads * 3 +
                    s.warm_leads * 2 +
                    s.total_responses * 1 -
                    s.opt_outs * 2
                ) / s.total_sent

        return stats

    def generate_report(self) -> str:
        """Generate Hormozi-style performance report."""
        stats = self.get_template_stats()

        lines = [
            "=" * 70,
            "📊 RESPONSE RATE ANALYSIS (Hormozi Framework)",
            "=" * 70,
            "",
            "Rule of 100: Track EVERY response. Know your numbers.",
            "",
        ]

        # Summary
        total_sent = sum(s.total_sent for s in stats.values())
        total_responses = sum(s.total_responses for s in stats.values())
        total_hot = sum(s.hot_leads for s in stats.values())
        total_warm = sum(s.warm_leads for s in stats.values())
        total_optout = sum(s.opt_outs for s in stats.values())

        overall_rate = total_responses / total_sent if total_sent > 0 else 0

        lines.extend([
            "📈 OVERALL METRICS:",
            f"   Total Sent:     {total_sent:,}",
            f"   Total Responses: {total_responses} ({overall_rate:.1%})",
            f"   Hot Leads:      {total_hot}",
            f"   Warm Leads:     {total_warm}",
            f"   Opt-Outs:       {total_optout}",
            "",
        ])

        # Template breakdown
        lines.extend([
            "📋 BY TEMPLATE:",
            f"{'Template':<30} {'Sent':>6} {'Resp':>6} {'Rate':>8} {'Hot':>5} {'Warm':>5} {'OptOut':>6} {'Score':>7}",
            "-" * 78
        ])

        # Sort by quality score
        sorted_stats = sorted(stats.values(), key=lambda s: s.quality_score, reverse=True)

        for s in sorted_stats:
            icon = "🏆" if s == sorted_stats[0] and s.total_sent >= 50 else "  "
            lines.append(
                f"{icon}{s.template_name[:28]:<28} {s.total_sent:>6} {s.total_responses:>6} "
                f"{s.response_rate:>7.1%} {s.hot_leads:>5} {s.warm_leads:>5} {s.opt_outs:>6} {s.quality_score:>7.2f}"
            )

        # Hormozi-style recommendations
        lines.extend([
            "",
            "=" * 70,
            "🎯 OPTIMIZATION RECOMMENDATIONS (Hormozi Protocol):",
            ""
        ])

        if len(sorted_stats) >= 2:
            best = sorted_stats[0]
            worst = sorted_stats[-1]

            if best.total_sent >= 50:
                lines.append(f"✅ SCALE WINNER: '{best.template_name}' ({best.response_rate:.1%} response rate)")
                lines.append(f"   → Allocate 70% of outreach to this template")
            else:
                lines.append(f"⏳ NEED MORE DATA: '{best.template_name}' only has {best.total_sent} sends")
                lines.append(f"   → Continue testing until 50+ sends per template")

            if worst.total_sent >= 50 and worst.quality_score < 0:
                lines.append(f"❌ KILL LOSER: '{worst.template_name}' has negative quality score")
                lines.append(f"   → Stop using this template, create new variation")

        # Check for concerning metrics
        if total_optout / total_sent > 0.10 if total_sent > 0 else False:
            lines.append(f"⚠️  HIGH OPT-OUT RATE: {total_optout / total_sent:.1%} (target: <5%)")
            lines.append(f"   → Review message content, may be too aggressive")

        if overall_rate < 0.02 and total_sent >= 100:
            lines.append(f"⚠️  LOW RESPONSE RATE: {overall_rate:.1%} (target: >5%)")
            lines.append(f"   → Test new angles, check lead quality")

        lines.extend([
            "",
            "=" * 70
        ])

        return "\n".join(lines)

    def generate_weekly_review(self) -> str:
        """Generate weekly optimization review."""
        stats = self.get_template_stats()

        lines = [
            "=" * 70,
            "📅 WEEKLY OPTIMIZATION REVIEW",
            f"   Week of: {datetime.now().strftime('%Y-%m-%d')}",
            "=" * 70,
            "",
        ]

        # This week's numbers
        week_ago = datetime.now() - timedelta(days=7)

        week_sends = 0
        week_responses = 0
        for campaign in self.campaigns:
            try:
                sent_date = datetime.fromisoformat(campaign.get("sent_at", "").replace("Z", "+00:00"))
                if sent_date > week_ago:
                    week_sends += 1
            except:
                pass

        for link in self.links:
            try:
                reply_date = datetime.fromisoformat(link.reply_date.replace("Z", "+00:00"))
                if reply_date > week_ago:
                    week_responses += 1
            except:
                pass

        week_rate = week_responses / week_sends if week_sends > 0 else 0

        lines.extend([
            "📊 THIS WEEK'S PERFORMANCE:",
            f"   Messages Sent:   {week_sends}",
            f"   Responses:       {week_responses}",
            f"   Response Rate:   {week_rate:.1%}",
            "",
        ])

        # Template recommendations
        lines.append("🎯 NEXT WEEK'S ALLOCATION:")

        sorted_stats = sorted(stats.values(), key=lambda s: s.quality_score, reverse=True)

        exploration_phase = all(s.total_sent < 50 for s in sorted_stats)

        if exploration_phase:
            lines.append("   STATUS: EXPLORATION PHASE (need 50+ sends per template)")
            lines.append("   ALLOCATION: Equal distribution across templates")
            for s in sorted_stats[:3]:
                lines.append(f"   - {s.template_name}: 33% ({s.total_sent}/50 tested)")
        else:
            best = sorted_stats[0]
            lines.append(f"   STATUS: EXPLOITATION PHASE")
            lines.append(f"   WINNER: {best.template_name} ({best.response_rate:.1%} rate)")
            lines.append(f"   ALLOCATION:")
            lines.append(f"   - {best.template_name}: 70%")
            for s in sorted_stats[1:3]:
                lines.append(f"   - {s.template_name}: 15% (testing)")

        # Action items
        lines.extend([
            "",
            "✅ ACTION ITEMS:",
            "   1. Review opt-out reasons (see sms_replies.json)",
            "   2. Update templates based on feedback",
            "   3. Run lead_monitor to check inventory",
            "   4. Adjust daily batch size if needed",
            "",
            "=" * 70
        ])

        return "\n".join(lines)

    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for concerning metrics that need attention."""
        alerts = []
        stats = self.get_template_stats()

        total_sent = sum(s.total_sent for s in stats.values())
        total_optout = sum(s.opt_outs for s in stats.values())
        total_responses = sum(s.total_responses for s in stats.values())

        # High opt-out rate
        if total_sent >= 50:
            optout_rate = total_optout / total_sent
            if optout_rate > 0.10:
                alerts.append({
                    "level": "CRITICAL",
                    "metric": "opt_out_rate",
                    "value": optout_rate,
                    "message": f"Opt-out rate {optout_rate:.1%} exceeds 10% threshold",
                    "action": "Review message content immediately"
                })
            elif optout_rate > 0.05:
                alerts.append({
                    "level": "WARNING",
                    "metric": "opt_out_rate",
                    "value": optout_rate,
                    "message": f"Opt-out rate {optout_rate:.1%} exceeds 5% target",
                    "action": "Monitor closely, consider message adjustments"
                })

        # Low response rate
        if total_sent >= 100:
            response_rate = total_responses / total_sent
            if response_rate < 0.01:
                alerts.append({
                    "level": "WARNING",
                    "metric": "response_rate",
                    "value": response_rate,
                    "message": f"Response rate {response_rate:.1%} is very low",
                    "action": "Test new templates, check lead quality"
                })

        # Template with negative quality
        for s in stats.values():
            if s.total_sent >= 50 and s.quality_score < -0.5:
                alerts.append({
                    "level": "WARNING",
                    "metric": "template_quality",
                    "value": s.quality_score,
                    "message": f"Template '{s.template_name}' has negative quality score",
                    "action": "Stop using this template"
                })

        return alerts


def main():
    """CLI for response tracker."""
    parser = argparse.ArgumentParser(description="Response Rate Tracker (Hormozi Framework)")
    parser.add_argument("command", choices=["sync", "report", "weekly", "alert"],
                       help="Command to run")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Change to project directory
    project_dir = Path(__file__).parent.parent
    os.chdir(project_dir)

    tracker = ResponseTracker()

    if args.command == "sync":
        print("Syncing replies to templates...")
        stats = tracker.sync_replies_to_templates()
        print(f"\n✅ Sync complete:")
        print(f"   New links:      {stats['new_links']}")
        print(f"   Already linked: {stats['already_linked']}")
        print(f"   No match:       {stats['no_match']}")

    elif args.command == "report":
        print(tracker.generate_report())

    elif args.command == "weekly":
        print(tracker.generate_weekly_review())

    elif args.command == "alert":
        alerts = tracker.check_alerts()
        if not alerts:
            print("✅ All metrics within normal ranges")
        else:
            for alert in alerts:
                icon = "🔴" if alert["level"] == "CRITICAL" else "🟡"
                print(f"{icon} [{alert['level']}] {alert['message']}")
                print(f"   Action: {alert['action']}")


if __name__ == "__main__":
    main()
