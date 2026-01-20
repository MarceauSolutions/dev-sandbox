#!/usr/bin/env python3
"""
Automated Campaign Optimization Recommendations

Analyzes all campaign data (template scores, cohort performance, A/B tests, attribution)
and generates actionable recommendations for improving cold outreach performance.

Usage:
    # Get recommendations for a business
    python -m src.campaign_optimizer recommend --business marceau-solutions

    # Get recommendations for all businesses
    python -m src.campaign_optimizer recommend

    # Generate next A/B test ideas
    python -m src.campaign_optimizer suggest-tests --business marceau-solutions
"""

import argparse
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Import our analytics modules
from src.campaign_analytics import CampaignAnalytics
from src.ab_testing import ABTestingFramework


@dataclass
class Recommendation:
    """Single optimization recommendation."""
    priority: str  # critical, high, medium, low
    category: str  # template, cohort, timing, ab_test, budget, pause
    insight: str  # What the data shows
    action: str  # What to do about it
    expected_impact: str  # Estimated improvement
    business_id: str


class CampaignOptimizer:
    """AI-powered campaign optimization engine."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.analytics = CampaignAnalytics(output_dir)
        self.ab_manager = ABTestingFramework(output_dir)

    def get_recommendations(self, business_id: Optional[str] = None) -> List[Recommendation]:
        """
        Generate comprehensive optimization recommendations.

        Args:
            business_id: Filter by business (or None for all businesses)

        Returns:
            List of prioritized recommendations
        """
        recommendations = []

        # 1. Template recommendations (use top performers, archive losers)
        recommendations.extend(self._analyze_templates(business_id))

        # 2. Cohort recommendations (prioritize high-response segments)
        recommendations.extend(self._analyze_cohorts(business_id))

        # 3. Timing recommendations (optimal send times)
        recommendations.extend(self._analyze_timing(business_id))

        # 4. A/B test recommendations (what to test next)
        recommendations.extend(self._suggest_ab_tests(business_id))

        # 5. Budget allocation (where to focus outreach capacity)
        recommendations.extend(self._analyze_budget_allocation(business_id))

        # 6. Pause recommendations (underperforming campaigns)
        recommendations.extend(self._identify_pauses(business_id))

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda r: priority_order.get(r.priority, 99))

        return recommendations

    def _analyze_templates(self, business_id: Optional[str] = None) -> List[Recommendation]:
        """Analyze template performance and recommend best practices."""
        recs = []

        # Get template scores
        scores = self.analytics.get_all_template_scores(business_id, sort_by="score")

        if not scores:
            return recs

        # Top performer recommendation
        top_template = scores[0]
        if top_template.composite_score >= 75 and top_template.total_sent >= 100:
            recs.append(Recommendation(
                priority="high",
                category="template",
                insight=f"Template '{top_template.template_name}' has exceptional performance (score: {top_template.composite_score:.0f}/100, {top_template.response_rate*100:.1f}% response rate)",
                action=f"Scale up usage of '{top_template.template_name}' - allocate 60-70% of new campaigns to this template",
                expected_impact="+15-20% overall response rate",
                business_id=business_id or "all"
            ))

        # Archive underperformers
        for template in scores:
            if template.composite_score < 50 and template.total_sent >= 100:
                recs.append(Recommendation(
                    priority="medium",
                    category="template",
                    insight=f"Template '{template.template_name}' is underperforming (score: {template.composite_score:.0f}/100, {template.response_rate*100:.1f}% response rate)",
                    action=f"Archive '{template.template_name}' and replace with higher-scoring alternatives",
                    expected_impact="+5-10% response rate by eliminating low performers",
                    business_id=business_id or "all"
                ))

        # Insufficient testing warning
        for template in scores:
            if template.total_sent < 100:
                recs.append(Recommendation(
                    priority="low",
                    category="template",
                    insight=f"Template '{template.template_name}' has insufficient data ({template.total_sent} sends)",
                    action=f"Continue testing '{template.template_name}' until reaching 100+ sends before making decisions",
                    expected_impact="Better data quality for optimization",
                    business_id=business_id or "all"
                ))
                break  # Only show this once

        return recs

    def _analyze_cohorts(self, business_id: Optional[str] = None) -> List[Recommendation]:
        """Analyze cohort performance and recommend targeting priorities."""
        recs = []

        # Analyze by category
        category_data = self.analytics.get_cohort_analysis("category", business_id)

        if not category_data["cohorts"]:
            return recs

        cohorts_list = list(category_data["cohorts"].items())

        # Best cohort recommendation
        if len(cohorts_list) >= 2:
            best_cohort, best_metrics = cohorts_list[0]
            worst_cohort, worst_metrics = cohorts_list[-1]

            if best_metrics["response_rate"] > worst_metrics["response_rate"] * 1.5:
                recs.append(Recommendation(
                    priority="critical",
                    category="cohort",
                    insight=f"Cohort '{best_cohort}' has {best_metrics['response_rate']*100:.0f}% response rate vs {worst_metrics['response_rate']*100:.0f}% for '{worst_cohort}'",
                    action=f"Shift 60-70% of outreach budget to '{best_cohort}' segment. Reduce '{worst_cohort}' to <20%",
                    expected_impact="+20-30% response rate from better targeting",
                    business_id=business_id or "all"
                ))

        # Top 3 cohorts recommendation
        if len(cohorts_list) >= 3:
            top_3 = [c[0] for c in cohorts_list[:3]]
            top_3_str = ", ".join(top_3)
            recs.append(Recommendation(
                priority="high",
                category="cohort",
                insight=f"Top 3 performing cohorts: {top_3_str}",
                action=f"Focus 90% of total outreach on these 3 segments. Test expansion cautiously.",
                expected_impact="+10-15% response rate from concentration",
                business_id=business_id or "all"
            ))

        return recs

    def _analyze_timing(self, business_id: Optional[str] = None) -> List[Recommendation]:
        """Analyze send timing and recommend optimal schedules."""
        recs = []

        # Get attribution data to understand timing
        attribution = self.analytics.get_attribution_analysis(business_id)

        if attribution["total_responses"] == 0:
            return recs

        # Multi-touch insight
        touch_1_pct = attribution["by_touch"].get(1, {}).get("percentage", 0)
        later_pct = 100 - touch_1_pct

        if later_pct > 60:
            recs.append(Recommendation(
                priority="high",
                category="timing",
                insight=f"{later_pct:.0f}% of responses come from follow-up touches (not initial contact)",
                action="Ensure 7-touch follow-up sequences are enabled for all campaigns. Don't give up after touch 1.",
                expected_impact="+40-60% total responses from persistence",
                business_id=business_id or "all"
            ))

        # Most effective touch optimization
        most_effective = attribution["most_effective_touch"]
        if most_effective > 1:
            recs.append(Recommendation(
                priority="medium",
                category="timing",
                insight=f"Touch #{most_effective} is most effective ({attribution['most_effective_percentage']:.0f}% of responses)",
                action=f"Optimize message quality for touch #{most_effective}. Test different angles/CTAs at this stage.",
                expected_impact="+5-10% response rate from touch optimization",
                business_id=business_id or "all"
            ))

        return recs

    def _suggest_ab_tests(self, business_id: Optional[str] = None) -> List[Recommendation]:
        """Suggest next A/B tests based on gaps in data."""
        recs = []

        # Get template scores to identify opportunities
        scores = self.analytics.get_all_template_scores(business_id, sort_by="score")

        if len(scores) >= 2:
            # Test top 2 performers against each other
            top_1 = scores[0]
            top_2 = scores[1]

            if abs(top_1.composite_score - top_2.composite_score) < 10:
                recs.append(Recommendation(
                    priority="high",
                    category="ab_test",
                    insight=f"'{top_1.template_name}' (score {top_1.composite_score:.0f}) vs '{top_2.template_name}' (score {top_2.composite_score:.0f}) - too close to call",
                    action=f"Run A/B test: '{top_1.template_name}' (control) vs '{top_2.template_name}' (variant), 200 leads total",
                    expected_impact="Identify clear winner, +3-5% response rate",
                    business_id=business_id or "all"
                ))

        # Suggest testing new angles
        cohort_data = self.analytics.get_cohort_analysis("category", business_id)
        if cohort_data["best_cohort"]:
            best_cohort = cohort_data["best_cohort"]
            recs.append(Recommendation(
                priority="medium",
                category="ab_test",
                insight=f"High-performing cohort '{best_cohort}' may respond to specialized messaging",
                action=f"A/B test: Generic message vs {best_cohort}-specific value prop (e.g., gym-specific pain points)",
                expected_impact="+5-8% response rate for best cohort",
                business_id=business_id or "all"
            ))

        return recs

    def _analyze_budget_allocation(self, business_id: Optional[str] = None) -> List[Recommendation]:
        """Recommend how to allocate outreach capacity across segments."""
        recs = []

        # Get cohort performance
        cohort_data = self.analytics.get_cohort_analysis("category", business_id)

        if not cohort_data["cohorts"] or len(cohort_data["cohorts"]) < 2:
            return recs

        cohorts_list = list(cohort_data["cohorts"].items())

        # Calculate ROI-weighted allocation
        total_response_value = sum(m["response_rate"] for c, m in cohorts_list)

        allocation = []
        for cohort, metrics in cohorts_list:
            if total_response_value > 0:
                pct = (metrics["response_rate"] / total_response_value) * 100
                allocation.append((cohort, pct, metrics["response_rate"]))

        # Build recommendation
        allocation_str = "\n".join([f"  • {cohort}: {pct:.0f}% ({rate*100:.1f}% response)" for cohort, pct, rate in allocation[:3]])

        recs.append(Recommendation(
            priority="high",
            category="budget",
            insight="Current budget allocation may not match cohort performance",
            action=f"Reallocate outreach capacity based on ROI:\n{allocation_str}",
            expected_impact="+10-15% overall response rate from optimal allocation",
            business_id=business_id or "all"
        ))

        return recs

    def _identify_pauses(self, business_id: Optional[str] = None) -> List[Recommendation]:
        """Identify campaigns that should be paused due to poor performance."""
        recs = []

        # Get template scores
        scores = self.analytics.get_all_template_scores(business_id, sort_by="score")

        for template in scores:
            if template.composite_score < 40 and template.total_sent >= 100:
                recs.append(Recommendation(
                    priority="critical",
                    category="pause",
                    insight=f"Template '{template.template_name}' has very poor performance (score: {template.composite_score:.0f}/100, {template.response_rate*100:.1f}% response)",
                    action=f"PAUSE all campaigns using '{template.template_name}' immediately. Wasting outreach capacity.",
                    expected_impact="Stop burning budget on ineffective messaging",
                    business_id=business_id or "all"
                ))

        return recs

    def print_recommendations(self, business_id: Optional[str] = None) -> str:
        """Generate formatted recommendations report."""
        recs = self.get_recommendations(business_id)

        lines = []
        lines.append("=" * 90)
        lines.append("CAMPAIGN OPTIMIZATION RECOMMENDATIONS")
        if business_id:
            lines.append(f"Business: {business_id.upper()}")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 90)

        if not recs:
            lines.append("\n✅ No recommendations - campaigns performing well!")
            return "\n".join(lines)

        # Group by priority
        by_priority = {"critical": [], "high": [], "medium": [], "low": []}
        for rec in recs:
            by_priority[rec.priority].append(rec)

        # Print by priority
        for priority in ["critical", "high", "medium", "low"]:
            priority_recs = by_priority[priority]
            if not priority_recs:
                continue

            icon = "🔴" if priority == "critical" else "🟠" if priority == "high" else "🟡" if priority == "medium" else "⚪"
            lines.append(f"\n## {icon} {priority.upper()} PRIORITY ({len(priority_recs)} items)")
            lines.append("-" * 90)

            for i, rec in enumerate(priority_recs, 1):
                category_icon = {
                    "template": "📝",
                    "cohort": "🎯",
                    "timing": "⏰",
                    "ab_test": "🧪",
                    "budget": "💰",
                    "pause": "🛑"
                }.get(rec.category, "📊")

                lines.append(f"\n{i}. {category_icon} [{rec.category.upper()}]")
                lines.append(f"   💡 INSIGHT: {rec.insight}")
                lines.append(f"   ⚡ ACTION: {rec.action}")
                lines.append(f"   📈 IMPACT: {rec.expected_impact}")

        # Summary
        lines.append("\n" + "=" * 90)
        lines.append("SUMMARY")
        lines.append(f"  Total Recommendations: {len(recs)}")
        lines.append(f"  Critical: {len(by_priority['critical'])} (act immediately)")
        lines.append(f"  High: {len(by_priority['high'])} (act this week)")
        lines.append(f"  Medium: {len(by_priority['medium'])} (act this month)")
        lines.append(f"  Low: {len(by_priority['low'])} (track over time)")
        lines.append("=" * 90)

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Campaign Optimization Recommendations")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Recommend command
    recommend_parser = subparsers.add_parser("recommend", help="Generate optimization recommendations")
    recommend_parser.add_argument("--business", help="Filter by business ID")
    recommend_parser.add_argument("--export", choices=["json"], help="Export recommendations")

    # Suggest tests command
    suggest_parser = subparsers.add_parser("suggest-tests", help="Suggest next A/B tests")
    suggest_parser.add_argument("--business", help="Filter by business ID")

    args = parser.parse_args()

    # Change to project directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    optimizer = CampaignOptimizer()

    if args.command == "recommend":
        if args.export == "json":
            recs = optimizer.get_recommendations(args.business)
            print(json.dumps([asdict(r) for r in recs], indent=2))
        else:
            print(optimizer.print_recommendations(args.business))

    elif args.command == "suggest-tests":
        # Get only A/B test recommendations
        all_recs = optimizer.get_recommendations(args.business)
        test_recs = [r for r in all_recs if r.category == "ab_test"]

        print("=" * 80)
        print("SUGGESTED A/B TESTS")
        if args.business:
            print(f"Business: {args.business.upper()}")
        print("=" * 80)

        if not test_recs:
            print("\n✅ No A/B test suggestions at this time")
        else:
            for i, rec in enumerate(test_recs, 1):
                print(f"\n{i}. 🧪 {rec.insight}")
                print(f"   ACTION: {rec.action}")
                print(f"   IMPACT: {rec.expected_impact}")

    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    exit(main())
