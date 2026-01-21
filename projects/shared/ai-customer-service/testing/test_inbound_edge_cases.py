"""
Edge case tests for InboundAssistantEngine.

Usage:
    python -m testing.test_inbound_edge_cases

Or with pytest:
    pytest testing/test_inbound_edge_cases.py -v
"""

import asyncio
import os
import sys
from dataclasses import dataclass
from typing import Optional, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.voice_engine import InboundAssistantEngine
from src.models import ConversationState


@dataclass
class TestCase:
    """A single test case for the InboundAssistantEngine."""
    name: str
    category: str
    input_text: str
    expected_trigger: Optional[str]  # "TRANSFER_NOW", "END_CALL", "MESSAGE_COMPLETE", or None
    description: str


@dataclass
class TestResult:
    """Result of running a test case."""
    test_case: TestCase
    response: str
    actual_trigger: Optional[str]
    passed: bool
    notes: str = ""


# Define test cases based on INBOUND-EDGE-CASES.md
TEST_CASES = [
    # Category 1: Clear Hot Leads
    TestCase(
        name="direct_automation_request",
        category="hot_leads",
        input_text="I need help automating my restaurant's phone system",
        expected_trigger="TRANSFER_NOW",
        description="Direct request for automation services"
    ),
    TestCase(
        name="project_discussion",
        category="hot_leads",
        input_text="I saw your work online and want to discuss a project",
        expected_trigger="TRANSFER_NOW",
        description="Caller wants to discuss a project"
    ),
    TestCase(
        name="pricing_inquiry",
        category="hot_leads",
        input_text="What do you charge for voice AI?",
        expected_trigger="TRANSFER_NOW",
        description="Pricing questions indicate buying intent"
    ),
    TestCase(
        name="business_owner_pain",
        category="hot_leads",
        input_text="I own a dental practice and our front desk is overwhelmed with calls",
        expected_trigger="TRANSFER_NOW",
        description="Business owner with specific pain point"
    ),
    TestCase(
        name="referral_mention",
        category="hot_leads",
        input_text="My friend Mike told me William helped him with chatbots",
        expected_trigger="TRANSFER_NOW",
        description="Referral from existing contact"
    ),

    # Category 2: Clear Non-Leads
    TestCase(
        name="insurance_sales",
        category="non_leads",
        input_text="Hi, I'm calling from XYZ Insurance to offer you a great deal on business coverage",
        expected_trigger="END_CALL",
        description="Vendor sales pitch"
    ),
    TestCase(
        name="wrong_number",
        category="non_leads",
        input_text="Wrong number, sorry",
        expected_trigger="END_CALL",
        description="Caller self-identified wrong number"
    ),
    TestCase(
        name="misdialed_business",
        category="non_leads",
        input_text="Is this the pizza place?",
        expected_trigger="END_CALL",
        description="Caller looking for different business"
    ),
    TestCase(
        name="b2b_software_sales",
        category="non_leads",
        input_text="Hi, I'm from Salesforce and I'd love to show you how our CRM can help your business",
        expected_trigger="END_CALL",
        description="Inbound software sales call"
    ),
    TestCase(
        name="recruiter_call",
        category="non_leads",
        input_text="Hi, I'm a recruiter and I have an exciting opportunity for William",
        expected_trigger="END_CALL",
        description="Recruiter - not a client lead"
    ),

    # Category 3: Edge Cases
    TestCase(
        name="vague_availability_check",
        category="edge_cases",
        input_text="Is William available?",
        expected_trigger=None,  # Should ask qualifying question
        description="Need one more question to qualify"
    ),
    TestCase(
        name="developer_curiosity",
        category="edge_cases",
        input_text="I'm a developer interested in your tech stack - how did you build the voice AI?",
        expected_trigger="TRANSFER_NOW",  # Bias toward transfer
        description="Could be collaborator or future client"
    ),
    TestCase(
        name="customer_complaint",
        category="edge_cases",
        input_text="I want to complain about your service",
        expected_trigger="TRANSFER_NOW",
        description="Customer retention is critical"
    ),
    TestCase(
        name="press_inquiry",
        category="edge_cases",
        input_text="Hi, I'm a reporter from TechCrunch writing about voice AI startups",
        expected_trigger="TRANSFER_NOW",
        description="Press = opportunity, never screen out"
    ),
    TestCase(
        name="partnership_request",
        category="edge_cases",
        input_text="I run an AI agency and wanted to explore potential partnership",
        expected_trigger="TRANSFER_NOW",
        description="Partnership opportunities are valuable"
    ),

    # Category 4: Hostile Scenarios
    TestCase(
        name="anti_robot_hostility",
        category="hostile",
        input_text="I hate talking to robots. Put me through to a real person now!",
        expected_trigger="TRANSFER_NOW",
        description="Honor explicit demand for human"
    ),
    TestCase(
        name="immediate_transfer_demand",
        category="hostile",
        input_text="Just transfer me. Now.",
        expected_trigger="TRANSFER_NOW",
        description="Don't waste time with impatient caller"
    ),
    TestCase(
        name="scam_attempt",
        category="hostile",
        input_text="This is the IRS. You have unpaid taxes and a warrant for your arrest.",
        expected_trigger="END_CALL",
        description="Known scam pattern - firm rejection"
    ),
]


def determine_trigger(state: ConversationState, response: str) -> Optional[str]:
    """Determine which trigger was activated based on state and response."""
    if state.live_transfer_requested:
        return "TRANSFER_NOW"
    if state.transfer_requested:
        return "END_CALL"
    if state.awaiting_confirmation:
        return "MESSAGE_COMPLETE"

    # Also check response text for triggers (in case state wasn't updated properly)
    if "[TRANSFER_NOW]" in response:
        return "TRANSFER_NOW"
    if "[END_CALL]" in response:
        return "END_CALL"
    if "[MESSAGE_COMPLETE]" in response:
        return "MESSAGE_COMPLETE"

    return None


async def run_test(engine: InboundAssistantEngine, test_case: TestCase) -> TestResult:
    """Run a single test case and return the result."""
    # Create fresh state for each test
    state = engine.create_initial_state(f"test_{test_case.name}")

    try:
        response, updated_state = await engine.process_turn(state, test_case.input_text)
        actual_trigger = determine_trigger(updated_state, response)

        passed = actual_trigger == test_case.expected_trigger

        notes = ""
        if not passed:
            notes = f"Expected {test_case.expected_trigger}, got {actual_trigger}"

        return TestResult(
            test_case=test_case,
            response=response,
            actual_trigger=actual_trigger,
            passed=passed,
            notes=notes
        )
    except Exception as e:
        return TestResult(
            test_case=test_case,
            response="",
            actual_trigger=None,
            passed=False,
            notes=f"Exception: {str(e)}"
        )


async def run_all_tests() -> List[TestResult]:
    """Run all test cases and return results."""
    engine = InboundAssistantEngine()
    results = []

    for test_case in TEST_CASES:
        result = await run_test(engine, test_case)
        results.append(result)

        # Print progress
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {test_case.category}/{test_case.name}")
        if not result.passed:
            print(f"       Expected: {test_case.expected_trigger}")
            print(f"       Actual: {result.actual_trigger}")
            print(f"       Response: {result.response[:100]}...")

    return results


def print_summary(results: List[TestResult]):
    """Print test summary."""
    passed = sum(1 for r in results if r.passed)
    total = len(results)

    print("\n" + "=" * 50)
    print(f"SUMMARY: {passed}/{total} tests passed ({100*passed/total:.1f}%)")
    print("=" * 50)

    # Group by category
    categories = {}
    for r in results:
        cat = r.test_case.category
        if cat not in categories:
            categories[cat] = {"passed": 0, "total": 0}
        categories[cat]["total"] += 1
        if r.passed:
            categories[cat]["passed"] += 1

    print("\nBy Category:")
    for cat, stats in categories.items():
        pct = 100 * stats["passed"] / stats["total"]
        status = "OK" if pct == 100 else "ISSUES"
        print(f"  {cat}: {stats['passed']}/{stats['total']} ({pct:.0f}%) [{status}]")

    # List failures
    failures = [r for r in results if not r.passed]
    if failures:
        print("\nFailed Tests:")
        for f in failures:
            print(f"  - {f.test_case.name}: {f.notes}")


def main():
    """Main entry point."""
    print("InboundAssistantEngine Edge Case Tests")
    print("=" * 50)
    print()

    results = asyncio.run(run_all_tests())
    print_summary(results)

    # Exit with error code if any tests failed
    failures = sum(1 for r in results if not r.passed)
    sys.exit(failures)


if __name__ == "__main__":
    main()
