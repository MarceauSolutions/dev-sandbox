"""Test the voice engine conversation flow."""

import asyncio
import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from src.voice_engine import VoiceEngine
from src.twilio_handler import get_demo_restaurant


async def test_order_flow():
    """Test a complete order conversation."""
    restaurant = get_demo_restaurant()
    engine = VoiceEngine(restaurant)
    state = engine.create_initial_state("test-001")

    print("\n" + "=" * 60)
    print("  Testing Order Flow: Pepperoni Pizza + Garlic Bread")
    print("=" * 60)

    # Simulate conversation
    turns = [
        "I'd like to order a large pepperoni pizza",
        "And also some garlic bread please",
        "That's all, thanks",
        "Yes that's correct"
    ]

    print(f"\n🤖 AI: {engine.get_greeting()}")

    for customer_input in turns:
        print(f"\n👤 Customer: {customer_input}")

        response, state = await engine.process_turn(state, customer_input)
        print(f"🤖 AI: {response}")

        if state.transfer_requested:
            print("\n📞 [Transfer requested]")
            break

        if state.current_order:
            print("\n✅ [Order Complete]")
            print(f"   Items: {len(state.current_order.items)}")
            print(f"   Total: ${state.current_order.total:.2f}")
            break

    print("\n" + "=" * 60)
    return state


async def test_menu_question():
    """Test menu question handling."""
    restaurant = get_demo_restaurant()
    engine = VoiceEngine(restaurant)
    state = engine.create_initial_state("test-002")

    print("\n" + "=" * 60)
    print("  Testing Menu Question")
    print("=" * 60)

    print(f"\n🤖 AI: {engine.get_greeting()}")

    question = "What kind of pizzas do you have?"
    print(f"\n👤 Customer: {question}")

    response, state = await engine.process_turn(state, question)
    print(f"🤖 AI: {response}")

    print("\n" + "=" * 60)
    return state


async def test_transfer_request():
    """Test transfer to human."""
    restaurant = get_demo_restaurant()
    engine = VoiceEngine(restaurant)
    state = engine.create_initial_state("test-003")

    print("\n" + "=" * 60)
    print("  Testing Transfer Request")
    print("=" * 60)

    print(f"\n🤖 AI: {engine.get_greeting()}")

    request = "I need to speak with a manager please"
    print(f"\n👤 Customer: {request}")

    response, state = await engine.process_turn(state, request)
    print(f"🤖 AI: {response}")

    if state.transfer_requested:
        print("\n📞 [Transfer triggered correctly]")
    else:
        print("\n⚠️  [Transfer NOT triggered - may need prompt tuning]")

    print("\n" + "=" * 60)
    return state


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  AI Customer Service - Conversation Tests")
    print("=" * 60)

    # Test 1: Order flow
    await test_order_flow()

    # Test 2: Menu question
    await test_menu_question()

    # Test 3: Transfer
    await test_transfer_request()

    print("\n✅ All tests complete!\n")


if __name__ == "__main__":
    asyncio.run(main())
