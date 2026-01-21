#!/usr/bin/env python3
"""Simulate Twilio webhook calls to test the full HTTP flow.

This tests the actual FastAPI endpoints without making real phone calls.

Run: python -m tests.test_webhook_simulation
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from src.main import app


def test_health_endpoint():
    """Test health check endpoint."""
    print("\n" + "="*60)
    print("TEST 1: Health Endpoint")
    print("="*60)

    with TestClient(app) as client:
        response = client.get("/health")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    print("  ✅ PASSED")


def test_incoming_call_webhook():
    """Simulate incoming call to restaurant."""
    print("\n" + "="*60)
    print("TEST 2: Incoming Call Webhook (/twilio/voice)")
    print("="*60)

    with TestClient(app) as client:
        # Simulate Twilio POST data
        form_data = {
            "CallSid": "CA_TEST_INCOMING_001",
            "From": "+12395551234",
            "To": "+18552399364"
        }

        response = client.post("/twilio/voice", data=form_data)
        print(f"  Status: {response.status_code}")
        print(f"  Content-Type: {response.headers.get('content-type')}")

        twiml = response.text
        print(f"  TwiML (first 300 chars):")
        print(f"  {twiml[:300]}...")

        assert response.status_code == 200
        assert "application/xml" in response.headers.get("content-type", "")
        assert "<Response>" in twiml
        assert "Mario" in twiml  # Restaurant name in greeting
        assert "Polly" in twiml  # Neural voice

    print("  ✅ PASSED")


def test_outreach_call_webhook():
    """Simulate outbound consulting call."""
    print("\n" + "="*60)
    print("TEST 3: Outreach Call Webhook (/twilio/outreach)")
    print("="*60)

    with TestClient(app) as client:
        # Simulate Twilio POST with personalization params
        form_data = {
            "CallSid": "CA_TEST_OUTREACH_001",
            "From": "+18552399364",
            "To": "+12395551234"
        }

        # Add query params for personalization
        params = {
            "person_name": "TestPerson",
            "business_name": "TestCompany",
            "business_type": "technology",
            "custom_context": "software development and AI"
        }

        response = client.post("/twilio/outreach", data=form_data, params=params)
        print(f"  Status: {response.status_code}")

        twiml = response.text
        print(f"  TwiML (first 400 chars):")
        print(f"  {twiml[:400]}...")

        assert response.status_code == 200
        assert "TestPerson" in twiml  # Personalized name
        assert "TestCompany" in twiml  # Company name
        assert "software development" in twiml  # Custom context

    print("  ✅ PASSED")


def test_gather_endpoint():
    """Simulate speech input during call."""
    print("\n" + "="*60)
    print("TEST 4: Gather Endpoint (/twilio/gather)")
    print("="*60)

    with TestClient(app) as client:
        # First create a call state by triggering incoming call
        client.post("/twilio/voice", data={
            "CallSid": "CA_TEST_GATHER_001",
            "From": "+12395551234",
            "To": "+18552399364"
        })

        # Now simulate speech input
        form_data = {
            "CallSid": "CA_TEST_GATHER_001",
            "SpeechResult": "I'd like to order a pepperoni pizza",
            "Confidence": 0.95
        }

        response = client.post("/twilio/gather", data=form_data)
        print(f"  Status: {response.status_code}")

        twiml = response.text
        print(f"  TwiML response:")
        print(f"  {twiml[:500]}...")

        assert response.status_code == 200
        # Should contain AI response about the order
        assert "<Say" in twiml

    print("  ✅ PASSED")


def test_outreach_gather_endpoint():
    """Simulate speech input during outreach call."""
    print("\n" + "="*60)
    print("TEST 5: Outreach Gather Endpoint (/twilio/outreach-gather)")
    print("="*60)

    with TestClient(app) as client:
        # First create outreach call state
        client.post("/twilio/outreach", data={
            "CallSid": "CA_TEST_OUTREACH_GATHER_001",
            "From": "+18552399364",
            "To": "+12395551234"
        }, params={
            "person_name": "TestPerson",
            "business_name": "TestCompany"
        })

        # Simulate positive response
        form_data = {
            "CallSid": "CA_TEST_OUTREACH_GATHER_001",
            "SpeechResult": "Yes, I'm interested in learning more",
            "Confidence": 0.92
        }

        response = client.post("/twilio/outreach-gather", data=form_data)
        print(f"  Status: {response.status_code}")

        twiml = response.text
        print(f"  TwiML response (first 500 chars):")
        print(f"  {twiml[:500]}...")

        assert response.status_code == 200
        assert "<Say" in twiml

    print("  ✅ PASSED")


def test_call_status_webhook():
    """Simulate call status update."""
    print("\n" + "="*60)
    print("TEST 6: Status Webhook (/twilio/status)")
    print("="*60)

    with TestClient(app) as client:
        form_data = {
            "CallSid": "CA_TEST_STATUS_001",
            "CallStatus": "completed"
        }

        response = client.post("/twilio/status", data=form_data)
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    print("  ✅ PASSED")


def test_list_calls():
    """Test call listing endpoint."""
    print("\n" + "="*60)
    print("TEST 7: List Calls Endpoint (/twilio/calls)")
    print("="*60)

    with TestClient(app) as client:
        response = client.get("/twilio/calls")
        print(f"  Status: {response.status_code}")
        print(f"  Active calls: {len(response.json())}")

        assert response.status_code == 200

    print("  ✅ PASSED")


def test_no_speech_handling():
    """Test handling when no speech is detected."""
    print("\n" + "="*60)
    print("TEST 8: No Speech Handling")
    print("="*60)

    with TestClient(app) as client:
        # Create a call first
        client.post("/twilio/voice", data={
            "CallSid": "CA_TEST_NOSPEECH_001",
            "From": "+12395551234",
            "To": "+18552399364"
        })

        # Send empty speech result
        form_data = {
            "CallSid": "CA_TEST_NOSPEECH_001",
            "SpeechResult": None,
            "Confidence": None
        }

        response = client.post("/twilio/gather", data=form_data)
        print(f"  Status: {response.status_code}")

        twiml = response.text
        print(f"  TwiML: {twiml[:300]}...")

        assert response.status_code == 200
        assert "didn't catch that" in twiml.lower() or "repeat" in twiml.lower()

    print("  ✅ PASSED")


def run_all_tests():
    """Run all webhook simulation tests."""
    print("\n" + "#"*60)
    print("# WEBHOOK SIMULATION TEST SUITE")
    print("#"*60)

    tests_passed = 0
    tests_failed = 0

    test_functions = [
        test_health_endpoint,
        test_incoming_call_webhook,
        test_outreach_call_webhook,
        test_gather_endpoint,
        test_outreach_gather_endpoint,
        test_call_status_webhook,
        test_list_calls,
        test_no_speech_handling,
    ]

    for test_func in test_functions:
        try:
            test_func()
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            tests_failed += 1

    print("\n" + "="*60)
    print(f"RESULTS: {tests_passed} passed, {tests_failed} failed")
    print("="*60)

    return tests_failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
