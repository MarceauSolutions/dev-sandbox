#!/usr/bin/env python3
"""
Pipeline Test Script — Verify all components work before going live.

Checks:
  1. Database connection and schema
  2. API credentials (Apollo, SMTP, Twilio, Google Sheets)
  3. Lead scoring on sample leads
  4. Follow-up routing logic
  5. A/B test framework
  6. Daily report generation (dry run)

Usage:
    python -m src.orchestrator.test_pipeline
"""

import sys
import json
import sqlite3
import os
from datetime import datetime
from pathlib import Path

# Ensure we can import from the orchestrator package
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def _pass(msg: str):
    print(f"  PASS: {msg}")


def _fail(msg: str):
    print(f"  FAIL: {msg}")


def _warn(msg: str):
    print(f"  WARN: {msg}")


def test_database() -> bool:
    """Test 1: Verify database connection and schema."""
    print("\n--- Test 1: Database Connection ---")
    from .config import DB_PATH

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        # Check tables exist
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = [t["name"] for t in tables]

        if "deals" not in table_names:
            _fail("'deals' table not found")
            return False
        _pass(f"Database connected at {DB_PATH}")

        # Check deal count
        count = conn.execute("SELECT COUNT(*) FROM deals").fetchone()[0]
        _pass(f"Deals table has {count} records")

        outreach_count = conn.execute("SELECT COUNT(*) FROM outreach_log").fetchone()[0]
        _pass(f"Outreach log has {outreach_count} records")

        # Check required columns
        cols = {row[1] for row in conn.execute("PRAGMA table_info(deals)").fetchall()}
        required = {"company", "contact_name", "contact_phone", "contact_email",
                     "industry", "stage", "tier", "lead_score", "next_action", "next_action_date"}
        missing = required - cols
        if missing:
            _warn(f"Missing columns (migration may add them): {missing}")

        # Check stage distribution
        stages = conn.execute("SELECT stage, COUNT(*) as c FROM deals GROUP BY stage ORDER BY c DESC").fetchall()
        for s in stages:
            print(f"    {s['stage']}: {s['c']}")

        conn.close()
        return True
    except Exception as e:
        _fail(f"Database error: {e}")
        return False


def test_api_credentials() -> bool:
    """Test 2: Verify API credentials are configured."""
    print("\n--- Test 2: API Credentials ---")
    from .config import (
        APOLLO_API_KEY, SMTP_USERNAME, SMTP_PASSWORD,
        TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN,
        SPREADSHEET_ID, ANTHROPIC_API_KEY, TOKEN_PATH,
    )

    all_ok = True

    # Apollo
    if APOLLO_API_KEY:
        _pass(f"Apollo API key configured ({APOLLO_API_KEY[:8]}...)")
    else:
        _warn("Apollo API key NOT set — lead acquisition will skip")
        all_ok = False

    # SMTP
    if SMTP_USERNAME and SMTP_PASSWORD:
        _pass(f"SMTP configured ({SMTP_USERNAME})")
    else:
        _fail("SMTP credentials NOT set — email outreach won't work")
        all_ok = False

    # Twilio
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
        _pass(f"Twilio configured (SID: {TWILIO_ACCOUNT_SID[:8]}...)")
    else:
        _warn("Twilio NOT configured — SMS features disabled")

    # Google Sheets
    if SPREADSHEET_ID:
        _pass(f"Google Sheets configured (ID: {SPREADSHEET_ID[:12]}...)")
    else:
        _fail("SPREADSHEET_ID NOT set — call sheet generation won't work")
        all_ok = False

    # Google token
    if os.path.exists(TOKEN_PATH):
        _pass(f"Google token found at {TOKEN_PATH}")
    else:
        _fail(f"Google token NOT found at {TOKEN_PATH}")
        all_ok = False

    # Anthropic (for pitch briefer)
    if ANTHROPIC_API_KEY:
        _pass(f"Anthropic API configured ({ANTHROPIC_API_KEY[:8]}...)")
    else:
        _warn("Anthropic API NOT set — some features limited")

    return all_ok


def test_lead_scoring() -> bool:
    """Test 3: Score 5 sample leads."""
    print("\n--- Test 3: Lead Scoring (5 samples) ---")
    from .config import DB_PATH
    from .lead_scorer import score_lead

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Get 5 diverse leads
    deals = conn.execute("""
        SELECT * FROM deals
        WHERE stage NOT IN ('Closed Won', 'Closed Lost')
        ORDER BY RANDOM()
        LIMIT 5
    """).fetchall()

    if not deals:
        _fail("No active deals to score")
        conn.close()
        return False

    all_ok = True
    for deal in deals:
        d = dict(deal)
        score, tier, breakdown = score_lead(d)

        if score < 0 or score > 100:
            _fail(f"{d['company']}: Score {score} out of range")
            all_ok = False
        elif tier not in (1, 2, 3):
            _fail(f"{d['company']}: Invalid tier {tier}")
            all_ok = False
        else:
            _pass(f"{d['company']}: Score={score}, Tier={tier} — {breakdown}")

    conn.close()
    return all_ok


def test_follow_up_routing() -> bool:
    """Test 4: Verify routing logic."""
    print("\n--- Test 4: Follow-Up Routing ---")
    from .follow_up_router import route_lead

    # Test T1 lead with phone + email in Naples
    t1 = route_lead({
        "id": 999, "company": "Test HVAC Co", "contact_name": "John Owner",
        "contact_phone": "(239) 555-0100", "contact_email": "john@testhvac.com",
        "industry": "HVAC", "tier": 1, "city": "Naples", "stage": "Prospect",
        "lead_score": 90, "next_action_date": None,
    })
    assert "call" in t1["actions"], "T1 should have call action"
    assert "email" in t1["actions"], "T1 should have email action"
    assert "in_person_flag" in t1["actions"], "T1 Naples should have in_person"
    assert t1["priority"] == "high", "T1 should be high priority"
    _pass(f"T1 routing: {t1['actions']} (priority={t1['priority']})")

    # Test T2 lead with email only
    t2 = route_lead({
        "id": 998, "company": "Test Restaurant", "contact_name": "",
        "contact_phone": "", "contact_email": "info@testrest.com",
        "industry": "Restaurant", "tier": 2, "city": "Fort Myers", "stage": "Contacted",
        "lead_score": 55, "next_action_date": "2026-03-26",
    })
    assert "email" in t2["actions"], "T2 with email should have email action"
    assert t2["priority"] == "medium", "T2 should be medium priority"
    _pass(f"T2 routing: {t2['actions']} (priority={t2['priority']})")

    # Test T3 lead - email only
    t3 = route_lead({
        "id": 997, "company": "Test Salon", "contact_name": "",
        "contact_phone": "(239) 555-0102", "contact_email": "salon@test.com",
        "industry": "Salon", "tier": 3, "city": "Cape Coral", "stage": "Prospect",
        "lead_score": 30, "next_action_date": None,
    })
    assert "email" in t3["actions"], "T3 with email should get email"
    assert "call" not in t3["actions"], "T3 should NOT get call"
    assert t3["priority"] == "low", "T3 should be low priority"
    _pass(f"T3 routing: {t3['actions']} (priority={t3['priority']})")

    # Test lead with no contact info
    no_contact = route_lead({
        "id": 996, "company": "Mystery Co", "contact_name": "",
        "contact_phone": "", "contact_email": "",
        "industry": "Other", "tier": 3, "city": "", "stage": "Prospect",
        "lead_score": 10, "next_action_date": None,
    })
    assert "needs_contact_info" in no_contact["actions"], "No contact should flag for research"
    _pass(f"No contact: {no_contact['actions']}")

    return True


def test_ab_testing() -> bool:
    """Test 5: Verify A/B test framework."""
    print("\n--- Test 5: A/B Testing Framework ---")
    from .ab_testing_manager import (
        assign_variant, get_subject_text, get_body_text,
        get_opener, get_ab_status,
    )

    # Test variant assignment is deterministic
    v1 = assign_variant("email_subjects", 100)
    v2 = assign_variant("email_subjects", 101)
    v1_again = assign_variant("email_subjects", 100)

    if v1 != v1_again:
        _fail("Variant assignment not deterministic")
        return False
    _pass(f"Variant assignment deterministic: deal 100 -> {v1}, deal 101 -> {v2}")

    # Test subject text generation
    subject = get_subject_text(v1, "Acme Corp", "John")
    if not subject or "{" in subject:
        _fail(f"Subject text has unresolved variables: {subject}")
        return False
    _pass(f"Subject text: '{subject}'")

    # Test body text generation
    body = get_body_text("body_a", "John", "Acme Corp", "HVAC")
    if not body or "{" in body:
        _fail(f"Body text has unresolved variables")
        return False
    if "ai" in body.lower() and "repair" not in body.lower():
        _warn("Body may contain 'AI' language — review templates")
    _pass(f"Body text generated ({len(body)} chars)")

    # Test opener
    opener = get_opener("opener_v1", "John", "HVAC")
    if not opener.get("script"):
        _fail("Opener script empty")
        return False
    _pass(f"Opener: '{opener['script'][:60]}...'")

    # Test status retrieval
    status = get_ab_status()
    _pass(f"A/B status has {len(status)} categories")

    return True


def test_daily_report_dry() -> bool:
    """Test 6: Generate a test call sheet (dry run)."""
    print("\n--- Test 6: Daily Report (Dry Run) ---")
    from .follow_up_router import run_routing
    from .daily_report import generate_call_sheet

    try:
        tasks = run_routing(dry_run=True, include_scripts=False)

        if not tasks:
            _warn("No tasks generated — pipeline may be empty or all leads are closed")
            return True  # Not a failure, just empty

        result = generate_call_sheet(tasks[:5], dry_run=True)
        if result:
            _pass(f"Call sheet generation (dry): {result}")
        else:
            _warn("Call sheet generated but returned empty URL (expected in dry run)")

        _pass(f"Would generate sheet with {len(tasks)} leads")
        return True
    except Exception as e:
        _fail(f"Daily report error: {e}")
        return False


def test_pipeline_validation() -> bool:
    """Test 7: Verify pipeline validation catches issues."""
    print("\n--- Test 7: Pipeline Validation (Dry Run) ---")
    from .main_orchestrator import _validate_pipeline

    try:
        fixes = _validate_pipeline(dry_run=True)
        _pass(f"Validation found: {fixes}")
        return True
    except Exception as e:
        _fail(f"Validation error: {e}")
        return False


def run_all_tests():
    """Run all pipeline tests and report results."""
    print("=" * 60)
    print("  SALES PIPELINE ORCHESTRATOR — TEST SUITE")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    tests = [
        ("Database Connection", test_database),
        ("API Credentials", test_api_credentials),
        ("Lead Scoring", test_lead_scoring),
        ("Follow-Up Routing", test_follow_up_routing),
        ("A/B Testing", test_ab_testing),
        ("Daily Report (Dry)", test_daily_report_dry),
        ("Pipeline Validation", test_pipeline_validation),
    ]

    results = {}
    for name, test_fn in tests:
        try:
            results[name] = test_fn()
        except Exception as e:
            _fail(f"{name} crashed: {e}")
            results[name] = False

    # Summary
    print("\n" + "=" * 60)
    print("  TEST RESULTS")
    print("=" * 60)
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)

    for name, ok in results.items():
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")

    print(f"\n  {passed}/{len(tests)} passed, {failed} failed")

    if failed > 0:
        print("\n  Fix failed tests before running live pipeline.")
        sys.exit(1)
    else:
        print("\n  All tests passed. Ready to run:")
        print("    python -m src.orchestrator.main_orchestrator --dry-run")
        print("    python -m src.orchestrator.main_orchestrator")
        sys.exit(0)


if __name__ == "__main__":
    run_all_tests()
