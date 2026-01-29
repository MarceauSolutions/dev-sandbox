#!/usr/bin/env python3
"""
Outreach Optimizer - Maximizes cold outreach volume with intelligent A/B testing.

Features:
1. Parallel template testing - rotates templates to gather performance data
2. Auto-optimization - shifts volume toward winning templates
3. Volume tracking - maximizes daily outreach within compliance limits
4. Real-time response tracking - updates template scores as responses come in

Strategy:
- Exploration phase: Equal distribution across templates (first 100 sends each)
- Exploitation phase: 70% to best performer, 30% to others for ongoing testing
- Continuous learning: Recalculates scores weekly

Usage:
    python -m src.outreach_optimizer status
    python -m src.outreach_optimizer recommend --limit 50
    python -m src.outreach_optimizer run --limit 50 --dry-run
    python -m src.outreach_optimizer run --limit 50 --for-real
"""

import os
import json
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict
import random

from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path)

logger = logging.getLogger(__name__)


@dataclass
class TemplatePerformance:
    """Performance metrics for a template."""
    template_name: str
    total_sent: int
    responses: int
    hot_leads: int
    warm_leads: int
    opt_outs: int
    response_rate: float
    quality_score: float  # Weighted: hot=3, warm=2, response=1, opt_out=-2


@dataclass
class OutreachPlan:
    """Planned outreach distribution."""
    template_name: str
    allocation: int  # Number of sends
    reason: str  # Why this allocation


# Templates to rotate for Apollo B2B outreach
APOLLO_TEMPLATES = [
    "apollo_b2b_intro",
    "apollo_decision_maker",
    "apollo_automation_offer",
]

# Templates for Google Places outreach - organized by pain point
# The optimizer will select from the appropriate category based on lead pain points

# For franchises (locally-owned chain locations) - NEVER claim they don't have a website
FRANCHISE_TEMPLATES = [
    "franchise_intro",
    "franchise_member_retention",
    "franchise_operations",
]

# For leads with aggregator pages but no real website
AGGREGATOR_TEMPLATES = [
    "aggregator_only_intro",
    "aggregator_google_ranking",
]

# For leads with verified no website
NO_WEBSITE_TEMPLATES = [
    "no_website_intro",
    "direct_question",
]

# For leads with few reviews
FEW_REVIEWS_TEMPLATES = [
    "few_reviews",
    "few_reviews_v2",
    "few_reviews_system",
]

# For leads with low ratings
LOW_RATING_TEMPLATES = [
    "low_rating_recovery",
    "low_rating_reputation",
]

# General templates (for leads without specific pain points)
GENERAL_TEMPLATES = [
    "competitor_hook",
    "social_proof",
]

# Legacy: Combined list for backward compatibility
GOOGLE_PLACES_TEMPLATES = [
    "franchise_intro",  # Safe default - no false claims
    "competitor_hook",
    "few_reviews",
    "social_proof",
]

# Minimum sends before we can evaluate a template
MIN_SENDS_FOR_EVALUATION = 50


class OutreachOptimizer:
    """
    Optimizes cold outreach by testing and rotating templates.

    Uses multi-armed bandit approach:
    - Exploration: Test all templates equally
    - Exploitation: Favor best performers
    - Balance: 70/30 exploit/explore after exploration phase
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.campaigns_file = self.output_dir / "sms_campaigns.json"
        self.optimizer_file = self.output_dir / "outreach_optimizer_state.json"

        # Load campaign data
        self.campaigns: List[Dict] = []
        self._load_campaigns()

        # Load optimizer state
        self.state: Dict = {}
        self._load_state()

    def _load_campaigns(self) -> None:
        """Load SMS campaign records."""
        if self.campaigns_file.exists():
            with open(self.campaigns_file, 'r') as f:
                data = json.load(f)
                self.campaigns = data.get("records", [])

    def _load_state(self) -> None:
        """Load optimizer state."""
        if self.optimizer_file.exists():
            with open(self.optimizer_file, 'r') as f:
                self.state = json.load(f)
        else:
            self.state = {
                "last_updated": datetime.now().isoformat(),
                "exploration_complete": {},
                "template_allocations": {}
            }

    def _save_state(self) -> None:
        """Save optimizer state."""
        self.state["last_updated"] = datetime.now().isoformat()
        with open(self.optimizer_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def get_template_performance(self, template_name: str) -> TemplatePerformance:
        """Calculate performance metrics for a template."""
        template_records = [
            r for r in self.campaigns
            if r.get("template_used") == template_name
        ]

        total_sent = len(template_records)
        responses = len([r for r in template_records if r.get("status") == "responded"])
        hot_leads = len([r for r in template_records if r.get("response_category") == "hot_lead"])
        warm_leads = len([r for r in template_records if r.get("response_category") == "warm_lead"])
        opt_outs = len([r for r in template_records if r.get("status") == "opted_out"])

        response_rate = responses / total_sent if total_sent > 0 else 0

        # Quality score: hot=3pts, warm=2pts, any_response=1pt, opt_out=-2pts
        quality_score = (hot_leads * 3 + warm_leads * 2 + responses * 1 - opt_outs * 2) / max(total_sent, 1)

        return TemplatePerformance(
            template_name=template_name,
            total_sent=total_sent,
            responses=responses,
            hot_leads=hot_leads,
            warm_leads=warm_leads,
            opt_outs=opt_outs,
            response_rate=response_rate,
            quality_score=quality_score
        )

    def get_all_performance(self, template_list: List[str]) -> List[TemplatePerformance]:
        """Get performance for all templates in a list."""
        return [self.get_template_performance(t) for t in template_list]

    def is_exploration_complete(self, template_list: List[str]) -> bool:
        """Check if all templates have minimum sends for evaluation."""
        for template in template_list:
            perf = self.get_template_performance(template)
            if perf.total_sent < MIN_SENDS_FOR_EVALUATION:
                return False
        return True

    def calculate_allocation(self, template_list: List[str], total_sends: int) -> List[OutreachPlan]:
        """
        Calculate optimal template allocation for outreach.

        Strategy:
        - Exploration phase: Equal distribution
        - Exploitation phase: 70% best, 30% others
        """
        plans = []
        performances = self.get_all_performance(template_list)

        if not self.is_exploration_complete(template_list):
            # Exploration phase - prioritize templates with fewer sends
            sorted_by_sends = sorted(performances, key=lambda p: p.total_sent)

            remaining = total_sends
            for i, perf in enumerate(sorted_by_sends):
                # Give more to less-tested templates
                needed = MIN_SENDS_FOR_EVALUATION - perf.total_sent
                allocation = min(needed, remaining // (len(sorted_by_sends) - i))
                allocation = max(allocation, remaining // len(sorted_by_sends))

                plans.append(OutreachPlan(
                    template_name=perf.template_name,
                    allocation=allocation,
                    reason=f"Exploration: {perf.total_sent}/{MIN_SENDS_FOR_EVALUATION} tested"
                ))
                remaining -= allocation
        else:
            # Exploitation phase - favor best performers
            sorted_by_score = sorted(performances, key=lambda p: p.quality_score, reverse=True)

            # Best performer gets 70%
            best = sorted_by_score[0]
            best_allocation = int(total_sends * 0.7)
            plans.append(OutreachPlan(
                template_name=best.template_name,
                allocation=best_allocation,
                reason=f"Best performer: {best.response_rate:.1%} response, {best.quality_score:.2f} score"
            ))

            # Others share 30%
            remaining = total_sends - best_allocation
            others = sorted_by_score[1:]
            if others:
                per_other = remaining // len(others)
                for perf in others:
                    plans.append(OutreachPlan(
                        template_name=perf.template_name,
                        allocation=per_other,
                        reason=f"Testing: {perf.response_rate:.1%} response"
                    ))

        return plans

    def select_template_for_lead(self, lead_source: str) -> str:
        """
        Select which template to use for the next lead.

        Uses weighted random selection based on current allocations.
        """
        template_list = APOLLO_TEMPLATES if lead_source == "apollo" else GOOGLE_PLACES_TEMPLATES

        # Get current allocations
        plans = self.calculate_allocation(template_list, 100)  # Normalize to 100

        # Weighted random selection
        total = sum(p.allocation for p in plans)
        if total == 0:
            return template_list[0]

        r = random.randint(1, total)
        cumulative = 0
        for plan in plans:
            cumulative += plan.allocation
            if r <= cumulative:
                return plan.template_name

        return plans[0].template_name

    def generate_status_report(self) -> str:
        """Generate optimization status report."""
        lines = [
            "=" * 60,
            "OUTREACH OPTIMIZER STATUS",
            "=" * 60,
            ""
        ]

        # Apollo templates
        lines.append("📊 APOLLO B2B TEMPLATES:")
        lines.append("-" * 40)
        apollo_perf = self.get_all_performance(APOLLO_TEMPLATES)
        exploration_complete = self.is_exploration_complete(APOLLO_TEMPLATES)

        lines.append(f"Phase: {'EXPLOITATION' if exploration_complete else 'EXPLORATION'}")
        lines.append("")
        lines.append(f"{'Template':<25} {'Sent':>6} {'Resp':>6} {'Rate':>8} {'Score':>8}")
        lines.append("-" * 55)

        for perf in sorted(apollo_perf, key=lambda p: p.quality_score, reverse=True):
            lines.append(
                f"{perf.template_name:<25} {perf.total_sent:>6} {perf.responses:>6} "
                f"{perf.response_rate:>7.1%} {perf.quality_score:>8.2f}"
            )

        lines.append("")

        # Recommended allocation for next 50
        lines.append("📋 RECOMMENDED ALLOCATION (next 50 sends):")
        plans = self.calculate_allocation(APOLLO_TEMPLATES, 50)
        for plan in plans:
            lines.append(f"  {plan.template_name}: {plan.allocation} ({plan.reason})")

        lines.append("")

        # Google Places templates
        lines.append("📊 GOOGLE PLACES TEMPLATES:")
        lines.append("-" * 40)
        gp_perf = self.get_all_performance(GOOGLE_PLACES_TEMPLATES)

        lines.append(f"{'Template':<25} {'Sent':>6} {'Resp':>6} {'Rate':>8} {'Score':>8}")
        lines.append("-" * 55)

        for perf in sorted(gp_perf, key=lambda p: p.quality_score, reverse=True):
            lines.append(
                f"{perf.template_name:<25} {perf.total_sent:>6} {perf.responses:>6} "
                f"{perf.response_rate:>7.1%} {perf.quality_score:>8.2f}"
            )

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def get_daily_capacity(self) -> Dict[str, int]:
        """Calculate daily outreach capacity based on compliance limits."""
        return {
            "apollo_initial": 20,  # New enrollments per day
            "apollo_followups": 50,  # Follow-ups per day
            "google_places_initial": 20,
            "google_places_followups": 50,
            "total_sms_per_day": 140,  # Twilio soft limit recommendation
        }


def main():
    """CLI for outreach optimizer."""
    parser = argparse.ArgumentParser(description="Outreach Optimizer")
    parser.add_argument("command", choices=["status", "recommend", "capacity"],
                       help="Command to run")
    parser.add_argument("--limit", type=int, default=50,
                       help="Number of sends to plan")
    parser.add_argument("--source", choices=["apollo", "google_places"], default="apollo",
                       help="Lead source")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Change to project directory
    project_dir = Path(__file__).parent.parent
    os.chdir(project_dir)

    optimizer = OutreachOptimizer()

    if args.command == "status":
        print(optimizer.generate_status_report())

    elif args.command == "recommend":
        template_list = APOLLO_TEMPLATES if args.source == "apollo" else GOOGLE_PLACES_TEMPLATES
        plans = optimizer.calculate_allocation(template_list, args.limit)

        print(f"\n📋 RECOMMENDED ALLOCATION for {args.limit} {args.source} sends:\n")
        for plan in plans:
            print(f"  {plan.template_name}: {plan.allocation}")
            print(f"    → {plan.reason}")

    elif args.command == "capacity":
        capacity = optimizer.get_daily_capacity()
        print("\n📊 DAILY OUTREACH CAPACITY:\n")
        for key, value in capacity.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
