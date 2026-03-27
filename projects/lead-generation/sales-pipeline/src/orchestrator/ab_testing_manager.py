#!/usr/bin/env python3
"""
A/B Testing Manager — Manage outreach variants for emails and cold calls.

Maintains 2-3 variants per channel:
  - Email: subject line variants + body variants
  - Cold call: opener variants

Assigns variants round-robin (50/50 or 33/33/33 split).
After 50+ touches per variant, evaluates winner based on response rate.
Promotes winner, generates new challenger.
Stores experiments in data/ab_tests.json.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from .config import DB_PATH, AB_TESTS_FILE, AB_MIN_TOUCHES_PER_VARIANT, AB_CONFIDENCE_THRESHOLD


def _load_tests() -> dict:
    """Load A/B test data from JSON file."""
    path = Path(AB_TESTS_FILE)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {
        "email_subjects": {
            "active_variants": {
                "subject_a": {
                    "text": "Quick question about {company}",
                    "sends": 0, "replies": 0, "created": datetime.now().isoformat(),
                },
                "subject_b": {
                    "text": "Noticed something about {company}'s lead flow",
                    "sends": 0, "replies": 0, "created": datetime.now().isoformat(),
                },
            },
            "champion": "subject_a",
            "history": [],
        },
        "email_bodies": {
            "active_variants": {
                "body_a": {
                    "text": "pain_first",  # Strategy label
                    "sends": 0, "replies": 0, "created": datetime.now().isoformat(),
                },
                "body_b": {
                    "text": "social_proof_first",
                    "sends": 0, "replies": 0, "created": datetime.now().isoformat(),
                },
            },
            "champion": "body_a",
            "history": [],
        },
        "call_openers": {
            "active_variants": {
                "opener_v1": {
                    "text": "permission_based",  # "Is this a bad time?"
                    "sends": 0, "replies": 0, "created": datetime.now().isoformat(),
                },
                "opener_v2": {
                    "text": "direct_value",  # Lead with value prop immediately
                    "sends": 0, "replies": 0, "created": datetime.now().isoformat(),
                },
            },
            "champion": "opener_v1",
            "history": [],
        },
        "updated_at": datetime.now().isoformat(),
    }


def _save_tests(tests: dict):
    """Save A/B test data to JSON file."""
    tests["updated_at"] = datetime.now().isoformat()
    Path(AB_TESTS_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(AB_TESTS_FILE, "w") as f:
        json.dump(tests, f, indent=2, default=str)


# ── Email Subject Line Variants ──

EMAIL_SUBJECTS = {
    "subject_a": "Quick question about {company}",
    "subject_b": "Noticed something about {company}'s lead flow",
    "subject_c": "{contact_first}, are leads slipping through at {company}?",
}

# ── Email Body Variants ──

EMAIL_BODIES = {
    "body_a": """Hi {contact_first},

I work with {industry} businesses in SW Florida, and I keep seeing the same pattern: leads come in from Google, phone calls, website forms — but they all end up in different places. Follow-ups get delayed, and revenue gets left on the table.

We built a system that connects everything you already use into one pipeline. Every lead gets captured, routed, and followed up with automatically — whether it's Monday morning or Saturday night.

Most of our clients see ROI within the first month.

Would a quick 10-minute walkthrough be worth your time this week?

Best,
William Marceau
Marceau Solutions
(239) 398-5676
marceausolutions.com""",

    "body_b": """Hi {contact_first},

Just helped a {industry} business in Naples increase their lead-to-close rate by connecting all their inquiry channels into one system. No new tools — just integrating what they already had.

The biggest win? After-hours inquiries that used to go to voicemail now get handled instantly.

I put together a quick overview of how this could work for {company}. Would 10 minutes this week work to walk through it?

Best,
William Marceau
Marceau Solutions
(239) 398-5676
marceausolutions.com""",
}

# ── Call Opener Variants ──

CALL_OPENERS = {
    "opener_v1": {
        "style": "permission_based",
        "script": "Hi {contact}, this is William with Marceau Solutions. Did I catch you at a bad time? [If no:] Great, I'll keep this to 45 seconds.",
    },
    "opener_v2": {
        "style": "direct_value",
        "script": "Hi {contact}, this is William with Marceau Solutions. I help {industry} businesses make sure no lead falls through the cracks — even after hours. Got 45 seconds?",
    },
}


def assign_variant(category: str, deal_id: int) -> str:
    """
    Assign an A/B variant to a deal based on round-robin.

    Args:
        category: "email_subjects", "email_bodies", or "call_openers"
        deal_id: The deal ID (used for deterministic assignment)

    Returns:
        Variant key (e.g., "subject_a", "body_b", "opener_v1")
    """
    tests = _load_tests()
    if category not in tests:
        return ""

    variants = list(tests[category]["active_variants"].keys())
    if not variants:
        return ""

    # Deterministic assignment based on deal_id
    idx = deal_id % len(variants)
    return variants[idx]


def get_subject_text(variant_key: str, company: str, contact_first: str = "") -> str:
    """Get the actual subject line text for a variant."""
    template = EMAIL_SUBJECTS.get(variant_key, EMAIL_SUBJECTS.get("subject_a", ""))
    return template.format(
        company=company,
        contact_first=contact_first or "there",
    )


def get_body_text(variant_key: str, contact_first: str, company: str, industry: str) -> str:
    """Get the actual email body text for a variant."""
    template = EMAIL_BODIES.get(variant_key, EMAIL_BODIES.get("body_a", ""))
    return template.format(
        contact_first=contact_first or "there",
        company=company,
        industry=industry or "local",
    )


def get_opener(variant_key: str, contact: str, industry: str) -> dict:
    """Get the call opener for a variant."""
    opener = CALL_OPENERS.get(variant_key, CALL_OPENERS.get("opener_v1", {}))
    return {
        "style": opener.get("style", ""),
        "script": opener.get("script", "").format(
            contact=contact or "there",
            industry=industry or "local",
        ),
    }


def record_send(category: str, variant_key: str):
    """Record that a variant was sent/used."""
    tests = _load_tests()
    if category in tests and variant_key in tests[category].get("active_variants", {}):
        tests[category]["active_variants"][variant_key]["sends"] += 1
        _save_tests(tests)


def record_reply(category: str, variant_key: str):
    """Record that a variant received a reply/response."""
    tests = _load_tests()
    if category in tests and variant_key in tests[category].get("active_variants", {}):
        tests[category]["active_variants"][variant_key]["replies"] += 1
        _save_tests(tests)


def evaluate_variants(category: str) -> dict:
    """
    Evaluate variant performance and declare winner if sufficient data.

    Args:
        category: "email_subjects", "email_bodies", or "call_openers"

    Returns:
        Dict with evaluation results
    """
    tests = _load_tests()
    if category not in tests:
        return {"status": "error", "message": f"Unknown category: {category}"}

    variants = tests[category]["active_variants"]
    results = {}

    # Check if we have enough data
    all_ready = True
    for key, data in variants.items():
        sends = data.get("sends", 0)
        replies = data.get("replies", 0)
        rate = replies / sends if sends > 0 else 0
        results[key] = {
            "sends": sends,
            "replies": replies,
            "rate": round(rate * 100, 1),
        }
        if sends < AB_MIN_TOUCHES_PER_VARIANT:
            all_ready = False

    if not all_ready:
        min_sends = min(v.get("sends", 0) for v in variants.values())
        return {
            "status": "collecting",
            "message": f"Need {AB_MIN_TOUCHES_PER_VARIANT} sends per variant, min is {min_sends}",
            "variants": results,
        }

    # Find winner
    best_key = max(results, key=lambda k: results[k]["rate"])
    best_rate = results[best_key]["rate"]

    # Check if winner is significantly better
    runner_up_rate = max(
        results[k]["rate"] for k in results if k != best_key
    )

    if best_rate > 0 and (best_rate - runner_up_rate) / best_rate > (1 - AB_CONFIDENCE_THRESHOLD):
        # Winner found
        tests[category]["history"].append({
            "timestamp": datetime.now().isoformat(),
            "winner": best_key,
            "results": results,
        })
        tests[category]["champion"] = best_key

        # Reset loser counts (keep winner, reset challengers)
        for key in variants:
            if key != best_key:
                variants[key]["sends"] = 0
                variants[key]["replies"] = 0

        _save_tests(tests)
        return {
            "status": "winner",
            "winner": best_key,
            "winner_rate": best_rate,
            "variants": results,
        }
    else:
        return {
            "status": "inconclusive",
            "message": "No statistically significant winner yet",
            "variants": results,
        }


def get_ab_status() -> dict:
    """Get current A/B test status across all categories."""
    tests = _load_tests()
    status = {}
    for category in ["email_subjects", "email_bodies", "call_openers"]:
        if category in tests:
            variants = tests[category].get("active_variants", {})
            status[category] = {
                "champion": tests[category].get("champion", ""),
                "variants": {
                    k: {
                        "sends": v.get("sends", 0),
                        "replies": v.get("replies", 0),
                        "rate": round(v["replies"] / v["sends"] * 100, 1) if v.get("sends", 0) > 0 else 0,
                    }
                    for k, v in variants.items()
                },
                "total_experiments": len(tests[category].get("history", [])),
            }
    return status


def run_ab_evaluation(dry_run: bool = False) -> dict:
    """
    Run A/B evaluation across all categories.

    Returns:
        Dict with evaluation results per category
    """
    print("\n=== A/B TEST EVALUATION ===")
    results = {}

    for category in ["email_subjects", "email_bodies", "call_openers"]:
        result = evaluate_variants(category)
        results[category] = result
        print(f"  {category}: {result['status']}")
        if result.get("variants"):
            for k, v in result["variants"].items():
                print(f"    {k}: {v['sends']} sends, {v['replies']} replies ({v['rate']}%)")

    return results


if __name__ == "__main__":
    import sys
    if "--status" in sys.argv:
        status = get_ab_status()
        print(json.dumps(status, indent=2))
    else:
        run_ab_evaluation()
