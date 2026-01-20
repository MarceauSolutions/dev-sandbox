"""CLI for testing AI Customer Service locally."""

import asyncio
import argparse
from .voice_engine import VoiceEngine
from .models import Restaurant, MenuItem
from .twilio_handler import get_demo_restaurant


def simulate_conversation():
    """Simulate a phone conversation in the terminal."""
    restaurant = get_demo_restaurant()
    engine = VoiceEngine(restaurant)
    state = engine.create_initial_state("test-call-001")

    print("\n" + "=" * 60)
    print(f"  Simulating call to {restaurant.name}")
    print("  Type 'quit' to end, 'transfer' to request transfer")
    print("=" * 60 + "\n")

    # Print greeting
    print(f"🤖 AI: {engine.get_greeting()}\n")

    while True:
        # Get customer input
        try:
            customer_input = input("👤 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nCall ended.")
            break

        if not customer_input:
            continue

        if customer_input.lower() == "quit":
            print("\n📞 Call ended by customer.")
            break

        # Process through voice engine
        try:
            ai_response, state = asyncio.run(
                engine.process_turn(state, customer_input)
            )
        except Exception as e:
            print(f"\n❌ Error: {e}")
            continue

        print(f"\n🤖 AI: {ai_response}\n")

        # Check for special states
        if state.transfer_requested:
            print(f"📞 Transferring to {restaurant.fallback_number}...")
            break

        if state.current_order:
            print("\n" + "=" * 40)
            print("  ORDER COMPLETE")
            print("=" * 40)
            for item in state.current_order.items:
                print(f"  • {item.name} x {item.quantity}: ${item.total_price:.2f}")
            print(f"  Subtotal: ${state.current_order.subtotal:.2f}")
            print(f"  Tax: ${state.current_order.tax:.2f}")
            print(f"  Total: ${state.current_order.total:.2f}")
            print("=" * 40 + "\n")
            break


def show_menu():
    """Display the demo restaurant menu."""
    restaurant = get_demo_restaurant()

    print("\n" + "=" * 50)
    print(f"  {restaurant.name} - Menu")
    print("=" * 50)

    current_category = None
    for item in restaurant.menu:
        if isinstance(item, dict):
            category = item.get("category", "Other")
            name = item.get("name", "Unknown")
            price = item.get("price", 0)
            desc = item.get("description", "")
        else:
            category = item.category
            name = item.name
            price = item.price
            desc = item.description or ""

        if category != current_category:
            current_category = category
            print(f"\n  {category}")
            print("  " + "-" * 30)

        print(f"    {name}: ${price:.2f}")
        if desc:
            print(f"      {desc}")

    print("\n" + "=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser(description="AI Customer Service CLI")
    parser.add_argument(
        "command",
        choices=["simulate", "menu", "serve"],
        help="Command to run"
    )
    parser.add_argument(
        "--port", type=int, default=8000,
        help="Port for serve command"
    )

    args = parser.parse_args()

    if args.command == "simulate":
        simulate_conversation()
    elif args.command == "menu":
        show_menu()
    elif args.command == "serve":
        import uvicorn
        print(f"\n🚀 Starting server on http://localhost:{args.port}")
        print("   Twilio webhook: http://localhost:{args.port}/twilio/voice\n")
        uvicorn.run(
            "src.main:app",
            host="0.0.0.0",
            port=args.port,
            reload=True
        )


if __name__ == "__main__":
    main()
