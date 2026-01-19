#!/usr/bin/env python3
"""Internal tests for Voice AI flow - no actual phone calls needed.

This simulates the Twilio webhook flow locally to verify:
1. Greeting generation with personalization
2. AI response generation
3. Conversation state management
4. TwiML response format

Run: python -m tests.test_voice_flow
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.voice_engine import ConsultingVoiceEngine, VoiceEngine
from src.models import Restaurant, ConversationState
from src.twilio_handler import get_ai_consulting_config, get_demo_restaurant
from src.voice_styles import get_voice_name


def test_voice_name():
    """Test voice name generation."""
    print("\n" + "="*60)
    print("TEST 1: Voice Name Configuration")
    print("="*60)

    voice = get_voice_name("female_us")
    print(f"  Female US voice: {voice}")
    assert voice == "Polly.Joanna-Neural", f"Expected Polly.Joanna-Neural, got {voice}"

    voice = get_voice_name("male_us")
    print(f"  Male US voice: {voice}")
    assert voice == "Polly.Matthew-Neural", f"Expected Polly.Matthew-Neural, got {voice}"

    print("  ✅ PASSED")


def test_personalized_greeting():
    """Test greeting generation with personalization."""
    print("\n" + "="*60)
    print("TEST 2: Personalized Greeting Generation")
    print("="*60)

    # Test with full personalization
    config = get_ai_consulting_config(
        person_name="Angela",
        business_name="Insulet Corporation",
        business_type="medical device",
        custom_context="diabetes care and clinical data insights"
    )

    print(f"\n  Greeting for Angela at Insulet:")
    print(f"  {config.greeting[:100]}...")

    assert "Angela" in config.greeting, "Person name not in greeting"
    assert "Insulet" in config.greeting, "Business name not in greeting"
    assert "diabetes" in config.greeting, "Custom context not in greeting"

    # Test without personalization
    config_generic = get_ai_consulting_config()
    print(f"\n  Generic greeting (no personalization):")
    print(f"  {config_generic.greeting[:100]}...")

    assert "William Marceau" in config_generic.greeting, "William's name not in generic greeting"

    print("\n  ✅ PASSED")


def test_system_prompt():
    """Test system prompt includes person context."""
    print("\n" + "="*60)
    print("TEST 3: System Prompt with Person Context")
    print("="*60)

    person_context = {
        "person_name": "Julia",
        "business_name": "Boab Fit",
        "business_type": "fitness",
        "custom_context": "fitness coaching and personal training"
    }

    config = get_ai_consulting_config(**person_context)
    engine = ConsultingVoiceEngine(config, person_context=person_context)

    prompt = engine.get_system_prompt()

    print(f"\n  System prompt contains person info:")
    print(f"  - Name: {'Julia' in prompt}")
    print(f"  - Company: {'Boab Fit' in prompt}")
    print(f"  - Industry: {'fitness' in prompt}")

    assert "Julia" in prompt, "Person name not in system prompt"
    assert "Boab Fit" in prompt, "Business name not in system prompt"
    assert "fitness" in prompt, "Business type not in system prompt"

    print("\n  ✅ PASSED")


async def test_conversation_turn():
    """Test a full conversation turn with AI response."""
    print("\n" + "="*60)
    print("TEST 4: Conversation Turn (AI Response)")
    print("="*60)

    person_context = {
        "person_name": "Test User",
        "business_name": "Test Company",
        "business_type": "technology",
        "custom_context": "software development"
    }

    config = get_ai_consulting_config(**person_context)
    engine = ConsultingVoiceEngine(config, person_context=person_context)
    state = engine.create_initial_state("test-call-123")

    # Simulate user saying "Yes, I'm interested"
    test_inputs = [
        "Yes, I have a moment",
        "Tell me more about AI automation",
        "I'm not interested, thanks"
    ]

    for user_input in test_inputs:
        print(f"\n  User: \"{user_input}\"")

        try:
            ai_response, state = await engine.process_turn(state, user_input)
            print(f"  AI: \"{ai_response[:150]}...\"" if len(ai_response) > 150 else f"  AI: \"{ai_response}\"")

            # Check for outcome markers
            if state.transfer_requested:
                print("  [END CALL - Not Interested]")
            elif state.awaiting_confirmation:
                print("  [INTERESTED - Will Follow Up]")
            else:
                print("  [CONTINUING CONVERSATION]")

        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            return False

    print("\n  ✅ PASSED")
    return True


def test_restaurant_greeting():
    """Test restaurant demo greeting."""
    print("\n" + "="*60)
    print("TEST 5: Restaurant Demo Greeting")
    print("="*60)

    restaurant = get_demo_restaurant()

    print(f"\n  Restaurant: {restaurant.name}")
    print(f"  Greeting: {restaurant.greeting}")
    print(f"  Menu items: {len(restaurant.menu)}")

    for item in restaurant.menu[:3]:
        print(f"    - {item.name}: ${item.price}")

    assert "Mario" in restaurant.greeting, "Restaurant name not in greeting"
    assert len(restaurant.menu) > 0, "No menu items"

    print("\n  ✅ PASSED")


async def test_restaurant_conversation():
    """Test restaurant order conversation."""
    print("\n" + "="*60)
    print("TEST 6: Restaurant Order Conversation")
    print("="*60)

    restaurant = get_demo_restaurant()
    engine = VoiceEngine(restaurant)
    state = engine.create_initial_state("test-order-123")

    test_inputs = [
        "I'd like to order a pepperoni pizza",
        "And some garlic bread please",
        "That's all, thank you"
    ]

    for user_input in test_inputs:
        print(f"\n  Customer: \"{user_input}\"")

        try:
            ai_response, state = await engine.process_turn(state, user_input)
            print(f"  AI: \"{ai_response[:150]}...\"" if len(ai_response) > 150 else f"  AI: \"{ai_response}\"")

            if state.transfer_requested:
                print("  [TRANSFERRING TO STAFF]")
            elif state.current_order:
                print(f"  [ORDER: {len(state.current_order.items)} items, ${state.current_order.total:.2f}]")

        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            return False

    print("\n  ✅ PASSED")
    return True


def test_twiml_generation():
    """Test TwiML XML generation (mock without actual Twilio)."""
    print("\n" + "="*60)
    print("TEST 7: TwiML Response Format")
    print("="*60)

    from twilio.twiml.voice_response import VoiceResponse, Gather

    response = VoiceResponse()
    voice = get_voice_name("female_us")

    response.say("Hello, this is a test greeting.", voice=voice)

    gather = Gather(
        input="speech",
        action="/twilio/gather",
        method="POST",
        speech_timeout="auto",
        speech_model="phone_call"
    )
    response.append(gather)

    response.say("I didn't catch that.", voice=voice)

    twiml = str(response)

    print(f"\n  Generated TwiML:")
    print(f"  {twiml[:200]}...")

    assert "<Response>" in twiml, "Missing Response tag"
    assert "<Say" in twiml, "Missing Say tag"
    assert "<Gather" in twiml, "Missing Gather tag"
    assert "Polly.Joanna-Neural" in twiml, "Missing Polly voice"

    print("\n  ✅ PASSED")


async def run_all_tests():
    """Run all internal tests."""
    print("\n" + "#"*60)
    print("# VOICE AI INTERNAL TEST SUITE")
    print("#"*60)

    tests_passed = 0
    tests_failed = 0

    try:
        test_voice_name()
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        tests_failed += 1

    try:
        test_personalized_greeting()
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        tests_failed += 1

    try:
        test_system_prompt()
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        tests_failed += 1

    try:
        await test_conversation_turn()
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        tests_failed += 1

    try:
        test_restaurant_greeting()
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        tests_failed += 1

    try:
        await test_restaurant_conversation()
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        tests_failed += 1

    try:
        test_twiml_generation()
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        tests_failed += 1

    print("\n" + "="*60)
    print(f"RESULTS: {tests_passed} passed, {tests_failed} failed")
    print("="*60)

    return tests_failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
