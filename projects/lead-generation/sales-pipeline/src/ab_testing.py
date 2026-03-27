#!/usr/bin/env python3
"""
A/B Testing Engine for Sales Pipeline

Automatically runs A/B tests on various sales elements:
- Email subject lines and content
- Call scripts and messaging
- Follow-up timing
- Proposal templates
- Landing page variations

Integrates with the existing pipeline to:
1. Assign variants to new deals
2. Track conversions based on target metrics
3. Provide statistical analysis
4. Automatically adopt winning variants
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

from .models import (
    get_db, create_ab_test, get_active_ab_tests, assign_variant_to_deal,
    record_ab_conversion, get_ab_test_results, get_deal_ab_assignments,
    get_ab_test_summary, complete_ab_test, log_outreach, update_deal,
    get_deal
)


class ABTestingEngine:
    """
    Core A/B testing engine that integrates with the sales pipeline.

    Features:
    - Automatic variant assignment for new deals
    - Conversion tracking based on pipeline stage changes
    - Statistical significance testing
    - Winner detection and auto-adoption
    """

    # Pre-defined test templates
    TEST_TEMPLATES = {
        "email_subject": {
            "name": "Email Subject Line Test",
            "target_metric": "response_rate",
            "control": "Transform Your Business with AI Automation",
            "variants": [
                "Stop Wasting Time on Manual Tasks",
                "How AI Can 10x Your Business Growth",
                "The Secret to Scaling Without Hiring",
                "AI Solutions That Pay for Themselves"
            ]
        },
        "email_content": {
            "name": "Email Content Test",
            "target_metric": "meeting_booked",
            "control": "Standard value proposition focused on features",
            "variants": [
                "Problem-focused: address pain points first",
                "ROI-focused: emphasize financial benefits",
                "Social proof: highlight success stories",
                "Urgency: limited-time offer approach"
            ]
        },
        "call_script": {
            "name": "Call Script Test",
            "target_metric": "meeting_booked",
            "control": "Standard discovery script",
            "variants": [
                "Challenge-focused: question current approach",
                "Vision-focused: paint future state",
                "ROI-focused: quantify benefits immediately",
                "Storytelling: use customer success stories"
            ]
        },
        "followup_timing": {
            "name": "Follow-up Timing Test",
            "target_metric": "response_rate",
            "control": "3 days after initial contact",
            "variants": [
                "1 day after initial contact",
                "1 week after initial contact",
                "2 days after initial contact",
                "Same day follow-up"
            ]
        },
        "proposal_template": {
            "name": "Proposal Template Test",
            "target_metric": "closed_won",
            "control": "Standard feature-benefit format",
            "variants": [
                "Problem-solution format",
                "ROI-focused with calculations",
                "Timeline and milestone focused",
                "Risk-reduction focused"
            ]
        }
    }

    def __init__(self):
        self.db_conn = None

    def _get_conn(self):
        """Get database connection."""
        if not self.db_conn:
            self.db_conn = get_db()
        return self.db_conn

    def create_test_from_template(self, template_name: str, custom_name: str = None,
                                sample_size: int = 100) -> int:
        """
        Create an A/B test from a predefined template.

        Args:
            template_name: Name of template (email_subject, email_content, etc.)
            custom_name: Custom test name (optional)
            sample_size: Target sample size for statistical significance

        Returns:
            Test ID
        """
        if template_name not in self.TEST_TEMPLATES:
            raise ValueError(f"Unknown template: {template_name}")

        template = self.TEST_TEMPLATES[template_name]
        test_name = custom_name or template["name"]

        conn = self._get_conn()
        return create_ab_test(
            conn=conn,
            test_name=test_name,
            test_type=template_name,
            target_metric=template["target_metric"],
            control_variant=json.dumps({"description": template["control"]}),
            test_variants=json.dumps(template["variants"]),
            sample_size=sample_size
        )

    def assign_variant_for_deal(self, deal_id: int, test_type: str) -> Optional[str]:
        """
        Assign a variant for a deal based on active tests of the given type.

        Args:
            deal_id: Deal ID
            test_type: Type of test (email_subject, call_script, etc.)

        Returns:
            Assigned variant name, or None if no active tests
        """
        conn = self._get_conn()

        # Find active test of this type
        active_tests = get_active_ab_tests(conn, test_type)
        if not active_tests:
            return None

        # Use the most recent active test
        test = active_tests[0]
        return assign_variant_to_deal(conn, deal_id, test["id"])

    def get_variant_content(self, deal_id: int, test_type: str) -> Dict[str, Any]:
        """
        Get the content for a deal's assigned variant.

        Args:
            deal_id: Deal ID
            test_type: Type of test

        Returns:
            Dict with variant content and metadata
        """
        conn = self._get_conn()

        assignments = get_deal_ab_assignments(conn, deal_id)
        for assignment in assignments:
            if assignment["test_type"] == test_type:
                test = conn.execute("SELECT * FROM ab_tests WHERE id = ?",
                                  (assignment["test_id"],)).fetchone()
                if test:
                    variants = json.loads(test["test_variants"])
                    variant_name = assignment["variant_name"]

                    if variant_name == "control":
                        content = json.loads(test["control_variant"])
                    else:
                        # Find variant by index (variant_name is like "variant_0", "variant_1")
                        try:
                            idx = int(variant_name.split("_")[1])
                            content = {"description": variants[idx]}
                        except (IndexError, ValueError):
                            content = {"description": variant_name}

                    return {
                        "variant_name": variant_name,
                        "content": content,
                        "test_id": test["id"],
                        "test_name": test["test_name"],
                        "assigned_at": assignment["assigned_at"]
                    }

        return {"variant_name": "default", "content": {"description": "Default content"}}

    def track_conversion(self, deal_id: int, target_metric: str):
        """
        Track a conversion event for all A/B tests assigned to a deal.

        Args:
            deal_id: Deal ID
            target_metric: The metric that was achieved (response_rate, meeting_booked, etc.)
        """
        conn = self._get_conn()

        assignments = get_deal_ab_assignments(conn, deal_id)
        for assignment in assignments:
            if assignment["target_metric"] == target_metric and not assignment["converted"]:
                record_ab_conversion(conn, deal_id, assignment["test_id"], assignment["variant_name"])

    def get_test_results(self, test_id: int) -> Dict[str, Any]:
        """
        Get comprehensive results for an A/B test.

        Returns:
            Dict with test details, variant performance, and statistical analysis
        """
        conn = self._get_conn()

        test = conn.execute("SELECT * FROM ab_tests WHERE id = ?", (test_id,)).fetchone()
        if not test:
            return {}

        results = get_ab_test_results(conn, test_id)

        return {
            "test": dict(test),
            "results": results,
            "total_impressions": sum(r["impressions"] for r in results),
            "total_conversions": sum(r["conversions"] for r in results),
            "best_performing": max(results, key=lambda x: x["conversion_rate"]) if results else None,
            "winner_detected": any(r.get("is_winner", False) for r in results)
        }

    def auto_adopt_winners(self):
        """
        Automatically adopt winning variants for completed tests.

        This would integrate with email templates, call scripts, etc.
        For now, just marks tests as completed and logs the winner.
        """
        conn = self._get_conn()

        active_tests = get_active_ab_tests(conn)
        for test in active_tests:
            results = get_ab_test_results(conn, test["id"])

            # Check if any variant has reached sample size and statistical significance
            for result in results:
                if (result["impressions"] >= test["sample_size"] and
                    result.get("is_winner", False)):
                    complete_ab_test(conn, test["id"], result["variant_name"])
                    print(f"Auto-adopted winner for test '{test['test_name']}': {result['variant_name']}")
                    break

    def get_recommendations(self, deal_id: int) -> List[Dict[str, Any]]:
        """
        Get A/B testing recommendations for a deal.

        Analyzes deal characteristics and suggests which tests would be valuable.
        """
        conn = self._get_conn()
        deal = get_deal(conn, deal_id)

        if not deal:
            return []

        recommendations = []
        deal_dict = dict(deal)

        # Email subject test recommendation
        if deal_dict.get("contact_email") and deal_dict.get("stage") == "Intake":
            recommendations.append({
                "test_type": "email_subject",
                "reason": "New lead with email - test subject lines for better open rates",
                "expected_impact": "15-30% improvement in response rates",
                "confidence": "high"
            })

        # Call script test recommendation
        if deal_dict.get("contact_phone") and deal_dict.get("tier") == 1:
            recommendations.append({
                "test_type": "call_script",
                "reason": "High-value lead - optimize call approach",
                "expected_impact": "10-25% improvement in meeting booking rates",
                "confidence": "high"
            })

        # Follow-up timing test
        if deal_dict.get("stage") in ["Qualified", "Meeting Booked"]:
            recommendations.append({
                "test_type": "followup_timing",
                "reason": "Lead engaged - optimize follow-up cadence",
                "expected_impact": "20-40% improvement in conversion velocity",
                "confidence": "medium"
            })

        return recommendations

    def run_automated_testing(self):
        """
        Main automation function called by the pipeline.

        This should be called:
        1. When new deals are created
        2. When deals change stages (for conversion tracking)
        3. Daily/weekly for winner detection and adoption
        """
        conn = self._get_conn()

        # 1. Check for winner adoption
        self.auto_adopt_winners()

        # 2. Update any pending conversions based on stage changes
        # This would be called when deals move through pipeline stages

        conn.close()


# ─── Integration Functions ───────────────────────────────────

def assign_ab_tests_to_deal(deal_id: int):
    """
    Automatically assign A/B tests to a new deal based on its characteristics.

    Called when a new deal is created.
    """
    engine = ABTestingEngine()

    # Always assign email subject test if they have email
    conn = get_db()
    deal = get_deal(conn, deal_id)
    if deal and deal["contact_email"]:
        engine.assign_variant_for_deal(deal_id, "email_subject")

    # Assign call script test for phone-qualified leads
    if deal and deal["contact_phone"] and deal["tier"] == 1:
        engine.assign_variant_for_deal(deal_id, "call_script")

    conn.close()


def track_pipeline_conversion(deal_id: int, new_stage: str):
    """
    Track conversions when deals move through pipeline stages.

    Called whenever a deal's stage changes.
    """
    engine = ABTestingEngine()

    # Map pipeline stages to A/B test metrics
    stage_to_metric = {
        "Replied": "response_rate",
        "Meeting Booked": "meeting_booked",
        "Proposal Sent": "proposal_sent",
        "Closed Won": "closed_won"
    }

    if new_stage in stage_to_metric:
        engine.track_conversion(deal_id, stage_to_metric[new_stage])


def get_personalized_content(deal_id: int, content_type: str) -> Dict[str, Any]:
    """
    Get personalized content for a deal based on A/B test assignments.

    Args:
        deal_id: Deal ID
        content_type: Type of content (email_subject, call_script, etc.)

    Returns:
        Dict with content and variant info
    """
    engine = ABTestingEngine()
    return engine.get_variant_content(deal_id, content_type)


# ─── CLI Interface ───────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="A/B Testing Engine for Sales Pipeline")
    parser.add_argument("--create-test", help="Create test from template")
    parser.add_argument("--template", help="Template name")
    parser.add_argument("--list-tests", action="store_true", help="List active tests")
    parser.add_argument("--test-results", type=int, help="Show results for test ID")
    parser.add_argument("--auto-adopt", action="store_true", help="Auto-adopt winning variants")

    args = parser.parse_args()

    engine = ABTestingEngine()

    if args.create_test:
        test_id = engine.create_test_from_template(args.template, args.create_test)
        print(f"Created test: {test_id}")

    elif args.list_tests:
        conn = get_db()
        tests = get_ab_test_summary(conn)
        conn.close()
        for test in tests:
            print(f"{test['id']}: {test['test_name']} ({test['status']}) - {test.get('total_conversions', 0)}/{test.get('total_assignments', 0)} conversions")

    elif args.test_results:
        results = engine.get_test_results(args.test_results)
        if results:
            print(json.dumps(results, indent=2))
        else:
            print("Test not found")

    elif args.auto_adopt:
        engine.auto_adopt_winners()
        print("Checked for winners to adopt")

    else:
        parser.print_help()