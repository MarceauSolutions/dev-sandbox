#!/usr/bin/env python3
"""
A/B Testing Framework for SMS Campaigns

Splits leads into control/variant groups and tracks response rates to find winning templates.

Usage:
    # Create A/B test
    python -m src.a_b_test create --name "no_website_test" --control no_website_v2 --variant no_website_v2_variant_a --leads 100

    # View test status
    python -m src.a_b_test status --name "no_website_test"

    # Get results (after sufficient data)
    python -m src.a_b_test results --name "no_website_test"
"""

import json
import argparse
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from scipy import stats
import random

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"


@dataclass
class ABTestVariant:
    """A variant in an A/B test."""
    variant_id: str
    template_name: str
    total_sent: int = 0
    total_delivered: int = 0
    total_responses: int = 0
    response_rate: float = 0.0
    lead_ids: List[str] = None

    def __post_init__(self):
        if self.lead_ids is None:
            self.lead_ids = []

    def calculate_response_rate(self):
        """Calculate response rate as percentage."""
        if self.total_delivered > 0:
            self.response_rate = (self.total_responses / self.total_delivered) * 100
        else:
            self.response_rate = 0.0


@dataclass
class ABTest:
    """An A/B test comparing two or more template variants."""
    test_id: str
    test_name: str
    created_at: str
    status: str  # "running", "completed", "inconclusive"

    # Variants
    control: ABTestVariant
    variants: List[ABTestVariant]

    # Test parameters
    min_sample_size: int = 50  # Min contacts per variant
    confidence_threshold: float = 0.85  # 85% confidence

    # Results
    winner: Optional[str] = None  # variant_id of winner
    p_value: Optional[float] = None
    confidence_level: Optional[float] = None

    def is_ready_for_analysis(self) -> bool:
        """Check if test has enough data for statistical analysis."""
        if self.control.total_delivered < self.min_sample_size:
            return False

        for variant in self.variants:
            if variant.total_delivered < self.min_sample_size:
                return False

        return True

    def calculate_statistical_significance(self):
        """
        Calculate if difference between control and variant is statistically significant.

        Uses Chi-square test for proportions.
        """
        if not self.is_ready_for_analysis():
            return

        # Recalculate response rates
        self.control.calculate_response_rate()
        for variant in self.variants:
            variant.calculate_response_rate()

        # Find best performing variant
        all_variants = [self.control] + self.variants
        best_variant = max(all_variants, key=lambda v: v.response_rate)

        # Compare best variant to control
        if best_variant.variant_id == self.control.variant_id:
            # Control is best
            self.winner = "control"
            self.status = "completed"
            return

        # Chi-square test: control vs best variant
        observed = [
            [self.control.total_responses, self.control.total_delivered - self.control.total_responses],
            [best_variant.total_responses, best_variant.total_delivered - best_variant.total_responses]
        ]

        chi2, p_value, dof, expected = stats.chi2_contingency(observed)

        self.p_value = p_value
        self.confidence_level = 1 - p_value

        # Determine winner if statistically significant
        if self.confidence_level >= self.confidence_threshold:
            self.winner = best_variant.variant_id
            self.status = "completed"
        else:
            self.status = "inconclusive"  # Need more data


class ABTestManager:
    """Manage A/B tests for SMS campaigns."""

    def __init__(self):
        self.ab_tests_file = OUTPUT_DIR / "ab_tests.json"
        self.tests: Dict[str, ABTest] = self._load_tests()

    def _load_tests(self) -> Dict[str, ABTest]:
        """Load existing A/B tests."""
        if self.ab_tests_file.exists():
            with open(self.ab_tests_file) as f:
                data = json.load(f)
                tests = {}
                for test_id, test_data in data.items():
                    # Reconstruct ABTest from dict
                    control = ABTestVariant(**test_data['control'])
                    variants = [ABTestVariant(**v) for v in test_data['variants']]

                    test = ABTest(
                        test_id=test_data['test_id'],
                        test_name=test_data['test_name'],
                        created_at=test_data['created_at'],
                        status=test_data['status'],
                        control=control,
                        variants=variants,
                        min_sample_size=test_data.get('min_sample_size', 50),
                        confidence_threshold=test_data.get('confidence_threshold', 0.85),
                        winner=test_data.get('winner'),
                        p_value=test_data.get('p_value'),
                        confidence_level=test_data.get('confidence_level')
                    )
                    tests[test_id] = test

                return tests
        return {}

    def _save_tests(self):
        """Save A/B tests to disk."""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        data = {}
        for test_id, test in self.tests.items():
            data[test_id] = {
                'test_id': test.test_id,
                'test_name': test.test_name,
                'created_at': test.created_at,
                'status': test.status,
                'control': asdict(test.control),
                'variants': [asdict(v) for v in test.variants],
                'min_sample_size': test.min_sample_size,
                'confidence_threshold': test.confidence_threshold,
                'winner': test.winner,
                'p_value': test.p_value,
                'confidence_level': test.confidence_level
            }

        with open(self.ab_tests_file, 'w') as f:
            json.dump(data, f, indent=2)

    def create_test(
        self,
        test_name: str,
        control_template: str,
        variant_templates: List[str],
        total_leads: int,
        min_sample_size: int = 50
    ) -> ABTest:
        """
        Create a new A/B test.

        Args:
            test_name: Human-readable name
            control_template: Template name for control group
            variant_templates: List of variant template names
            total_leads: Total number of leads to split
            min_sample_size: Minimum contacts per variant

        Returns:
            Created ABTest object
        """
        test_id = f"ab_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Calculate split (equal distribution)
        num_groups = 1 + len(variant_templates)  # control + variants
        leads_per_group = total_leads // num_groups

        control = ABTestVariant(
            variant_id="control",
            template_name=control_template,
            total_sent=0,
            lead_ids=[]
        )

        variants = []
        for i, template_name in enumerate(variant_templates, 1):
            variant = ABTestVariant(
                variant_id=f"variant_{chr(96 + i)}",  # variant_a, variant_b, etc.
                template_name=template_name,
                total_sent=0,
                lead_ids=[]
            )
            variants.append(variant)

        test = ABTest(
            test_id=test_id,
            test_name=test_name,
            created_at=datetime.now().isoformat(),
            status="running",
            control=control,
            variants=variants,
            min_sample_size=min_sample_size,
            confidence_threshold=0.85
        )

        self.tests[test_id] = test
        self._save_tests()

        return test

    def assign_lead_to_variant(self, test_id: str, lead_id: str) -> str:
        """
        Assign a lead to a variant (random assignment).

        Returns:
            variant_id that lead was assigned to
        """
        test = self.tests.get(test_id)
        if not test:
            raise ValueError(f"Test {test_id} not found")

        # Random assignment
        all_variants = [test.control] + test.variants
        variant = random.choice(all_variants)

        variant.lead_ids.append(lead_id)
        variant.total_sent += 1

        self._save_tests()

        return variant.variant_id

    def record_delivery(self, test_id: str, lead_id: str):
        """Record that a message was delivered."""
        test = self.tests.get(test_id)
        if not test:
            return

        # Find variant for this lead
        for variant in [test.control] + test.variants:
            if lead_id in variant.lead_ids:
                variant.total_delivered += 1
                break

        self._save_tests()

    def record_response(self, test_id: str, lead_id: str):
        """Record that a lead responded."""
        test = self.tests.get(test_id)
        if not test:
            return

        # Find variant for this lead
        for variant in [test.control] + test.variants:
            if lead_id in variant.lead_ids:
                variant.total_responses += 1
                variant.calculate_response_rate()
                break

        # Check if we can calculate results
        if test.is_ready_for_analysis():
            test.calculate_statistical_significance()

        self._save_tests()

    def get_test_status(self, test_id: str) -> str:
        """Get formatted status report for a test."""
        test = self.tests.get(test_id)
        if not test:
            return f"Test {test_id} not found"

        report = []
        report.append(f"\nA/B Test: {test.test_name}")
        report.append(f"Status: {test.status.upper()}")
        report.append(f"Created: {test.created_at}")
        report.append("")

        # Control
        report.append(f"CONTROL ({test.control.template_name}):")
        report.append(f"  Sent: {test.control.total_sent}")
        report.append(f"  Delivered: {test.control.total_delivered}")
        report.append(f"  Responses: {test.control.total_responses}")
        report.append(f"  Response Rate: {test.control.response_rate:.2f}%")
        report.append("")

        # Variants
        for variant in test.variants:
            report.append(f"{variant.variant_id.upper()} ({variant.template_name}):")
            report.append(f"  Sent: {variant.total_sent}")
            report.append(f"  Delivered: {variant.total_delivered}")
            report.append(f"  Responses: {variant.total_responses}")
            report.append(f"  Response Rate: {variant.response_rate:.2f}%")
            report.append("")

        # Results
        if test.status == "completed" and test.winner:
            report.append("RESULTS:")
            winner_name = test.winner.replace("_", " ").title()
            report.append(f"  🏆 Winner: {winner_name}")
            report.append(f"  Confidence: {test.confidence_level * 100:.1f}%")
            report.append(f"  P-value: {test.p_value:.4f}")

            # Find winner variant
            all_variants = [test.control] + test.variants
            winner_variant = next(v for v in all_variants if v.variant_id == test.winner or (test.winner == "control" and v.variant_id == "control"))

            report.append(f"  Winning Template: {winner_variant.template_name}")
            report.append(f"  Winning Response Rate: {winner_variant.response_rate:.2f}%")

        elif test.status == "inconclusive":
            report.append("RESULTS: INCONCLUSIVE")
            report.append(f"  Need more data for statistical significance")
            report.append(f"  Current confidence: {test.confidence_level * 100:.1f}% (need {test.confidence_threshold * 100:.0f}%)")

        else:
            report.append("STATUS: TEST RUNNING")
            min_needed = test.min_sample_size
            report.append(f"  Need {min_needed} delivered per variant for analysis")
            report.append(f"  Control: {test.control.total_delivered}/{min_needed}")
            for variant in test.variants:
                report.append(f"  {variant.variant_id}: {variant.total_delivered}/{min_needed}")

        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="A/B Testing for SMS Campaigns")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # create command
    create_parser = subparsers.add_parser("create", help="Create new A/B test")
    create_parser.add_argument("--name", required=True, help="Test name")
    create_parser.add_argument("--control", required=True, help="Control template name")
    create_parser.add_argument("--variants", nargs="+", required=True, help="Variant template names")
    create_parser.add_argument("--leads", type=int, default=100, help="Total leads to split")
    create_parser.add_argument("--min-sample", type=int, default=50, help="Min sample size per variant")

    # status command
    status_parser = subparsers.add_parser("status", help="View test status")
    status_parser.add_argument("--test-id", help="Test ID")

    # results command
    results_parser = subparsers.add_parser("results", help="Get test results")
    results_parser.add_argument("--test-id", required=True, help="Test ID")

    # list command
    list_parser = subparsers.add_parser("list", help="List all tests")

    args = parser.parse_args()
    manager = ABTestManager()

    if args.command == "create":
        test = manager.create_test(
            test_name=args.name,
            control_template=args.control,
            variant_templates=args.variants,
            total_leads=args.leads,
            min_sample_size=args.min_sample
        )
        print(f"✅ Created A/B test: {test.test_id}")
        print(f"Test name: {test.test_name}")
        print(f"Control: {test.control.template_name}")
        for variant in test.variants:
            print(f"{variant.variant_id}: {variant.template_name}")

    elif args.command == "status":
        if args.test_id:
            print(manager.get_test_status(args.test_id))
        else:
            # Show all running tests
            for test_id, test in manager.tests.items():
                if test.status == "running":
                    print(manager.get_test_status(test_id))

    elif args.command == "results":
        print(manager.get_test_status(args.test_id))

    elif args.command == "list":
        print("\nAll A/B Tests:")
        print("-" * 60)
        for test_id, test in manager.tests.items():
            status_icon = "🏆" if test.status == "completed" else "🔄" if test.status == "running" else "❓"
            print(f"{status_icon} {test.test_name} ({test_id})")
            print(f"   Status: {test.status}")
            if test.winner:
                print(f"   Winner: {test.winner}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
