#!/usr/bin/env python3
"""
A/B Testing Framework for SMS Campaign Optimization

Enables split testing of template variants to identify highest-performing messages.

Features:
- Automatic lead splitting (50/50 control vs variant)
- Statistical significance testing (chi-square, 85% confidence threshold)
- Winner declaration when criteria met
- Auto-promotion of winning templates

Usage:
    # Create A/B test
    python -m src.ab_testing create --name "pain_vs_social_proof" \\
        --control no_website_intro --variant social_proof_intro \\
        --sample-size 100 --business marceau-solutions

    # Check test results
    python -m src.ab_testing results --name "pain_vs_social_proof"

    # List all tests
    python -m src.ab_testing list
"""

import argparse
import json
import os
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import random

# Statistical testing
from scipy import stats


class TestStatus(Enum):
    """Status of an A/B test."""
    ACTIVE = "active"
    COMPLETE = "complete"
    WINNER_DECLARED = "winner_declared"
    ARCHIVED = "archived"


@dataclass
class ABTest:
    """A/B test configuration and results."""
    test_id: str
    name: str
    business_id: str
    control_template: str
    variant_template: str
    sample_size: int
    created_at: str

    # Lead assignments
    control_group: List[str] = field(default_factory=list)
    variant_group: List[str] = field(default_factory=list)

    # Performance metrics
    control_sent: int = 0
    variant_sent: int = 0
    control_responses: int = 0
    variant_responses: int = 0
    control_rate: float = 0.0
    variant_rate: float = 0.0

    # Statistical results
    confidence: float = 0.0
    p_value: float = 1.0
    winner: str = ""  # "control", "variant", or ""
    status: str = "active"

    # Metadata
    completed_at: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ABTestingFramework:
    """
    A/B testing system for campaign optimization.

    Manages test creation, lead assignment, performance tracking,
    and statistical significance testing.
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.tests_file = self.output_dir / "ab_tests.json"
        self.tests: Dict[str, ABTest] = {}

        self._load_tests()

    def _load_tests(self) -> None:
        """Load existing tests."""
        if self.tests_file.exists():
            with open(self.tests_file, 'r') as f:
                data = json.load(f)
                for test_data in data.get("tests", []):
                    test = ABTest(**test_data)
                    self.tests[test.test_id] = test

    def _save_tests(self) -> None:
        """Save tests to file."""
        data = {
            "tests": [t.to_dict() for t in self.tests.values()],
            "updated_at": datetime.now().isoformat()
        }
        with open(self.tests_file, 'w') as f:
            json.dump(data, f, indent=2)

    def create_test(
        self,
        name: str,
        control_template: str,
        variant_template: str,
        sample_size: int,
        business_id: str = "marceau-solutions"
    ) -> ABTest:
        """
        Create a new A/B test.

        Args:
            name: Human-readable test name
            control_template: Template name for control group
            variant_template: Template name for variant group
            sample_size: Total leads to test (split 50/50)
            business_id: Which business is running this test

        Returns:
            Created ABTest object
        """
        test_id = f"test_{len(self.tests) + 1:03d}"

        test = ABTest(
            test_id=test_id,
            name=name,
            business_id=business_id,
            control_template=control_template,
            variant_template=variant_template,
            sample_size=sample_size,
            created_at=datetime.now().isoformat(),
            status="active"
        )

        self.tests[test_id] = test
        self._save_tests()

        print(f"Created A/B test: {test_id}")
        print(f"  Name: {name}")
        print(f"  Control: {control_template}")
        print(f"  Variant: {variant_template}")
        print(f"  Sample Size: {sample_size} leads ({sample_size//2} per group)")

        return test

    def assign_lead(
        self,
        test_id: str,
        lead_id: str
    ) -> Tuple[str, str]:
        """
        Assign a lead to control or variant group.

        Args:
            test_id: ID of the A/B test
            lead_id: Lead to assign

        Returns:
            Tuple of (group: "control" or "variant", template: str)
        """
        if test_id not in self.tests:
            raise ValueError(f"Test not found: {test_id}")

        test = self.tests[test_id]

        # Check if lead already assigned
        if lead_id in test.control_group:
            return ("control", test.control_template)
        if lead_id in test.variant_group:
            return ("variant", test.variant_template)

        # Check if test is full
        if len(test.control_group) + len(test.variant_group) >= test.sample_size:
            raise ValueError(f"Test {test_id} is full ({test.sample_size} leads)")

        # Assign to group (50/50 split, balance as we go)
        control_count = len(test.control_group)
        variant_count = len(test.variant_group)

        # If one group is behind, assign there
        if control_count < variant_count:
            group = "control"
            test.control_group.append(lead_id)
            template = test.control_template
        elif variant_count < control_count:
            group = "variant"
            test.variant_group.append(lead_id)
            template = test.variant_template
        else:
            # Equal, randomly assign
            if random.random() < 0.5:
                group = "control"
                test.control_group.append(lead_id)
                template = test.control_template
            else:
                group = "variant"
                test.variant_group.append(lead_id)
                template = test.variant_template

        self._save_tests()

        return (group, template)

    def record_send(self, test_id: str, lead_id: str, group: str) -> None:
        """Record that a message was sent for a test lead."""
        if test_id not in self.tests:
            return

        test = self.tests[test_id]

        if group == "control":
            test.control_sent += 1
        elif group == "variant":
            test.variant_sent += 1

        self._save_tests()

    def record_response(
        self,
        test_id: str,
        lead_id: str,
        group: str
    ) -> None:
        """
        Record a response from a test lead.

        Args:
            test_id: ID of the A/B test
            lead_id: Lead that responded
            group: "control" or "variant"
        """
        if test_id not in self.tests:
            return

        test = self.tests[test_id]

        if group == "control":
            test.control_responses += 1
        elif group == "variant":
            test.variant_responses += 1

        # Update rates
        if test.control_sent > 0:
            test.control_rate = test.control_responses / test.control_sent
        if test.variant_sent > 0:
            test.variant_rate = test.variant_responses / test.variant_sent

        self._save_tests()

        # Check for significance
        self.check_significance(test_id)

    def check_significance(self, test_id: str) -> Dict[str, Any]:
        """
        Check if test results are statistically significant.

        Uses chi-square test with 85% confidence threshold.

        Args:
            test_id: Test to check

        Returns:
            Dict with significance results
        """
        if test_id not in self.tests:
            raise ValueError(f"Test not found: {test_id}")

        test = self.tests[test_id]

        # Need minimum sample size (100 per group)
        min_sample = 100
        if test.control_sent < min_sample or test.variant_sent < min_sample:
            return {
                "significant": False,
                "reason": f"Insufficient data (need {min_sample} per group)",
                "control_sent": test.control_sent,
                "variant_sent": test.variant_sent
            }

        # Construct contingency table
        # [[control_responses, control_non_responses],
        #  [variant_responses, variant_non_responses]]
        contingency_table = [
            [test.control_responses, test.control_sent - test.control_responses],
            [test.variant_responses, test.variant_sent - test.variant_responses]
        ]

        # Chi-square test
        chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)

        # 85% confidence = p < 0.15
        confidence_threshold = 0.15
        is_significant = p_value < confidence_threshold

        # Calculate confidence level
        confidence = (1 - p_value) * 100

        # Update test
        test.p_value = p_value
        test.confidence = confidence

        result = {
            "significant": is_significant,
            "p_value": p_value,
            "confidence": confidence,
            "control_rate": test.control_rate * 100,
            "variant_rate": test.variant_rate * 100,
            "difference": (test.variant_rate - test.control_rate) * 100
        }

        # Declare winner if significant
        if is_significant:
            if test.variant_rate > test.control_rate:
                test.winner = "variant"
                result["winner"] = "variant"
                result["winner_template"] = test.variant_template
            else:
                test.winner = "control"
                result["winner"] = "control"
                result["winner_template"] = test.control_template

            test.status = "winner_declared"
            test.completed_at = datetime.now().isoformat()

            print(f"\n🏆 WINNER DECLARED for test {test_id}!")
            print(f"  Winner: {result['winner'].upper()} ({result['winner_template']})")
            print(f"  Control rate: {result['control_rate']:.1f}%")
            print(f"  Variant rate: {result['variant_rate']:.1f}%")
            print(f"  Improvement: {result['difference']:+.1f}%")
            print(f"  Confidence: {confidence:.1f}% (p={p_value:.4f})")

        self._save_tests()

        return result

    def get_test_results(self, test_id: str) -> Dict[str, Any]:
        """Get detailed results for a test."""
        if test_id not in self.tests:
            raise ValueError(f"Test not found: {test_id}")

        test = self.tests[test_id]

        # Run significance check (updates internal state)
        sig_result = self.check_significance(test_id)

        results = {
            "test_id": test.test_id,
            "name": test.name,
            "status": test.status,
            "business_id": test.business_id,
            "control": {
                "template": test.control_template,
                "assigned": len(test.control_group),
                "sent": test.control_sent,
                "responses": test.control_responses,
                "rate": test.control_rate * 100
            },
            "variant": {
                "template": test.variant_template,
                "assigned": len(test.variant_group),
                "sent": test.variant_sent,
                "responses": test.variant_responses,
                "rate": test.variant_rate * 100
            },
            "statistics": {
                "p_value": test.p_value,
                "confidence": test.confidence,
                "significant": sig_result.get("significant", False),
                "winner": test.winner
            },
            "created_at": test.created_at,
            "completed_at": test.completed_at
        }

        return results

    def print_results(self, test_id: str) -> str:
        """Generate formatted results report."""
        results = self.get_test_results(test_id)

        lines = []
        lines.append("=" * 80)
        lines.append(f"A/B TEST RESULTS: {results['name']}")
        lines.append(f"Test ID: {results['test_id']}")
        lines.append(f"Status: {results['status'].upper()}")
        lines.append(f"Business: {results['business_id']}")
        lines.append("=" * 80)

        lines.append("\n## CONTROL GROUP")
        lines.append(f"Template: {results['control']['template']}")
        lines.append(f"Assigned: {results['control']['assigned']} leads")
        lines.append(f"Sent:     {results['control']['sent']} messages")
        lines.append(f"Responses: {results['control']['responses']}")
        lines.append(f"Rate:      {results['control']['rate']:.1f}%")

        lines.append("\n## VARIANT GROUP")
        lines.append(f"Template: {results['variant']['template']}")
        lines.append(f"Assigned: {results['variant']['assigned']} leads")
        lines.append(f"Sent:     {results['variant']['sent']} messages")
        lines.append(f"Responses: {results['variant']['responses']}")
        lines.append(f"Rate:      {results['variant']['rate']:.1f}%")

        lines.append("\n## STATISTICAL ANALYSIS")
        stats_data = results['statistics']
        lines.append(f"P-value:    {stats_data['p_value']:.4f}")
        lines.append(f"Confidence: {stats_data['confidence']:.1f}%")
        lines.append(f"Significant: {'YES ✅' if stats_data['significant'] else 'NO ⏳ (need more data)'}")

        if stats_data['winner']:
            winner_data = results['control'] if stats_data['winner'] == 'control' else results['variant']
            loser_data = results['variant'] if stats_data['winner'] == 'control' else results['control']
            improvement = winner_data['rate'] - loser_data['rate']

            lines.append(f"\n🏆 WINNER: {stats_data['winner'].upper()}")
            lines.append(f"  Winning Template: {winner_data['template']}")
            lines.append(f"  Improvement: +{improvement:.1f}% over {stats_data['winner'] == 'control' and 'variant' or 'control'}")
            lines.append(f"\n💡 RECOMMENDATION: Use '{winner_data['template']}' for future campaigns")
            lines.append(f"  Archive '{loser_data['template']}' (underperforming)")

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)

    def list_tests(self, business_id: Optional[str] = None, status: Optional[str] = None) -> List[ABTest]:
        """List all tests, optionally filtered."""
        tests = list(self.tests.values())

        if business_id:
            tests = [t for t in tests if t.business_id == business_id]

        if status:
            tests = [t for t in tests if t.status == status]

        return tests


def main():
    """CLI entry point."""
    import sys

    parser = argparse.ArgumentParser(description="A/B Testing Framework")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Create test
    create_parser = subparsers.add_parser("create", help="Create new A/B test")
    create_parser.add_argument("--name", required=True, help="Test name")
    create_parser.add_argument("--control", required=True, help="Control template")
    create_parser.add_argument("--variant", required=True, help="Variant template")
    create_parser.add_argument("--sample-size", type=int, default=100, help="Total sample size")
    create_parser.add_argument("--business", default="marceau-solutions",
                              help="Business ID")
    create_parser.add_argument("--output-dir", default="output", help="Output directory")

    # Results
    results_parser = subparsers.add_parser("results", help="Show test results")
    results_parser.add_argument("--name", help="Test name")
    results_parser.add_argument("--test-id", help="Test ID")
    results_parser.add_argument("--output-dir", default="output", help="Output directory")

    # List tests
    list_parser = subparsers.add_parser("list", help="List all tests")
    list_parser.add_argument("--business", help="Filter by business")
    list_parser.add_argument("--status", help="Filter by status")
    list_parser.add_argument("--output-dir", default="output", help="Output directory")

    args = parser.parse_args()

    if args.command == "create":
        framework = ABTestingFramework(output_dir=args.output_dir)
        test = framework.create_test(
            name=args.name,
            control_template=args.control,
            variant_template=args.variant,
            sample_size=args.sample_size,
            business_id=args.business
        )
        print(f"\nNext step: Assign leads to this test using test ID: {test.test_id}")
        return

    if args.command == "results":
        framework = ABTestingFramework(output_dir=args.output_dir)

        # Find test by name or ID
        test_id = args.test_id
        if args.name and not test_id:
            for t in framework.tests.values():
                if t.name == args.name:
                    test_id = t.test_id
                    break

        if not test_id:
            print(f"Test not found: {args.name or args.test_id}")
            return 1

        print(framework.print_results(test_id))
        return

    if args.command == "list":
        framework = ABTestingFramework(output_dir=args.output_dir)
        tests = framework.list_tests(business_id=args.business, status=args.status)

        print("\n" + "=" * 100)
        print("A/B TESTS")
        print("=" * 100)
        print(f"{'ID':<10} {'Name':<25} {'Status':<15} {'Control→Variant':>20} {'Progress':>15}")
        print("-" * 100)

        for test in tests:
            progress = f"{len(test.control_group) + len(test.variant_group)}/{test.sample_size}"
            comparison = f"{test.control_rate*100:.1f}% → {test.variant_rate*100:.1f}%"
            print(f"{test.test_id:<10} {test.name[:25]:<25} {test.status:<15} {comparison:>20} {progress:>15}")

        if not tests:
            print("No tests found.")

        print()
        return

    parser.print_help()
    return 0


if __name__ == "__main__":
    exit(main())
