"""Voice AI Engine - Core conversation handler."""

import uuid
import json
from datetime import datetime
from typing import Optional
import anthropic

from .config import get_settings
from .models import (
    Call, CallStatus, Restaurant, ConversationState,
    Order, OrderItem, OrderStatus, TranscriptEntry
)


class VoiceEngine:
    """Handles AI conversation logic for phone orders."""

    def __init__(self, restaurant: Restaurant):
        self.restaurant = restaurant
        self.settings = get_settings()
        self.client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)

    def get_system_prompt(self) -> str:
        """Generate system prompt for the restaurant."""
        menu_text = self._format_menu()

        return f"""You are an AI phone assistant for {self.restaurant.name}. Your job is to:
1. Greet customers warmly
2. Take their food orders accurately
3. Answer menu questions
4. Confirm orders before completing

RESTAURANT INFO:
- Name: {self.restaurant.name}
- Greeting: {self.restaurant.greeting}

MENU:
{menu_text}

GUIDELINES:
- Be conversational but concise (1-2 sentences per response)
- Always confirm items as you add them
- If unsure, ask for clarification
- For complex requests, suggest speaking with staff
- Use natural language, not robotic responses
- If customer asks for something not on menu, politely suggest alternatives

TRANSFER TRIGGERS (say you'll connect them to staff):
- Customer explicitly asks for a person
- Catering or large party orders
- Complaints or issues
- Reservations
- Anything you can't handle

RESPONSE FORMAT:
Respond naturally as if speaking on the phone. Keep responses SHORT - this is a voice call.

When the order is complete and confirmed, end your response with:
[ORDER_COMPLETE]
Items: item1 x qty, item2 x qty
Total: $XX.XX

When transferring, end with:
[TRANSFER]
Reason: reason for transfer"""

    def _format_menu(self) -> str:
        """Format menu for LLM context."""
        if not self.restaurant.menu:
            return "Menu not configured. Ask customer what they'd like and confirm availability."

        lines = []
        current_category = None
        for item in self.restaurant.menu:
            if item.category != current_category:
                current_category = item.category
                lines.append(f"\n## {current_category}")
            lines.append(f"- {item.name}: ${item.price:.2f}")
            if item.description:
                lines.append(f"  ({item.description})")
        return "\n".join(lines)

    async def process_turn(
        self,
        state: ConversationState,
        customer_input: str
    ) -> tuple[str, ConversationState]:
        """
        Process a conversation turn.

        Args:
            state: Current conversation state
            customer_input: What the customer said (transcribed)

        Returns:
            Tuple of (AI response text, updated state)
        """
        # Add customer message to context
        state.context.append({
            "role": "user",
            "content": customer_input
        })

        # Get AI response
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            system=self.get_system_prompt(),
            messages=state.context
        )

        ai_text = response.content[0].text

        # Add AI response to context
        state.context.append({
            "role": "assistant",
            "content": ai_text
        })

        # Check for special markers
        if "[TRANSFER]" in ai_text:
            state.transfer_requested = True
            # Extract transfer reason
            if "Reason:" in ai_text:
                reason = ai_text.split("Reason:")[-1].strip()
                # Clean up the response for speaking
                ai_text = ai_text.split("[TRANSFER]")[0].strip()

        elif "[ORDER_COMPLETE]" in ai_text:
            # Parse completed order
            state.awaiting_confirmation = False
            order_info = ai_text.split("[ORDER_COMPLETE]")[-1].strip()
            # Clean up for speaking
            ai_text = ai_text.split("[ORDER_COMPLETE]")[0].strip()
            # Parse and create order (simplified - would need more robust parsing)
            state.current_order = self._parse_order(order_info, state)

        return ai_text, state

    def _parse_order(self, order_text: str, state: ConversationState) -> Order:
        """Parse order from AI response. Simplified version."""
        order = Order(
            id=str(uuid.uuid4()),
            call_id=state.call_id,
            restaurant_id=state.restaurant_id,
            status=OrderStatus.PENDING
        )

        # Parse items line
        lines = order_text.strip().split("\n")
        for line in lines:
            if line.startswith("Items:"):
                items_str = line.replace("Items:", "").strip()
                # Simple parsing - in production, would use structured output
                for item_str in items_str.split(","):
                    item_str = item_str.strip()
                    if " x " in item_str:
                        name, qty = item_str.rsplit(" x ", 1)
                        qty = int(qty) if qty.isdigit() else 1
                    else:
                        name = item_str
                        qty = 1
                    # Find price from menu
                    price = 0.0
                    for menu_item in self.restaurant.menu:
                        if menu_item.name.lower() in name.lower():
                            price = menu_item.price
                            break
                    order.items.append(OrderItem(
                        menu_item_id=name.lower().replace(" ", "_"),
                        name=name,
                        quantity=qty,
                        unit_price=price,
                        total_price=price * qty
                    ))

            elif line.startswith("Total:"):
                total_str = line.replace("Total:", "").strip().replace("$", "")
                try:
                    order.total = float(total_str)
                except ValueError:
                    pass

        # Calculate subtotal and tax if not provided
        order.subtotal = sum(item.total_price for item in order.items)
        if order.total == 0:
            order.tax = order.subtotal * 0.07  # 7% tax
            order.total = order.subtotal + order.tax

        return order

    def create_initial_state(self, call_id: str) -> ConversationState:
        """Create initial conversation state for a new call."""
        return ConversationState(
            call_id=call_id,
            restaurant_id=self.restaurant.id,
            context=[{
                "role": "assistant",
                "content": self.restaurant.greeting
            }]
        )

    def get_greeting(self) -> str:
        """Get the initial greeting for the call."""
        return self.restaurant.greeting
