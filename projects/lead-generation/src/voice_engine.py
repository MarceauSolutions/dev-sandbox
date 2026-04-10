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

EMOTIONAL TONE GUIDELINES:
- Greetings: Warm and welcoming ("Thank you for calling!" with enthusiasm)
- Taking orders: Friendly and attentive ("Great choice!" "Got it!")
- Confirming items: Professional but positive ("Perfect, one pepperoni pizza")
- When something is unavailable: Empathetic, then helpful ("Oh, I'm sorry we're out of that today. Can I suggest...")
- Upselling: Cheerful, not pushy ("Would you like to add some garlic bread? It's really popular!")
- Order completion: Excited and appreciative ("Awesome! Your order will be ready in about 20 minutes!")
- Apologies: Sincere and calm ("I apologize for the confusion. Let me fix that.")
- Transferring: Reassuring ("No problem, let me connect you with someone who can help.")

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


class ConsultingVoiceEngine:
    """Handles AI conversation for consulting outreach calls."""

    def __init__(self, config: Restaurant, person_context: dict = None):
        self.config = config
        self.settings = get_settings()
        self.client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
        self.person_context = person_context or {}

    def get_system_prompt(self) -> str:
        """Generate system prompt for consulting outreach."""
        # Add personalized context if available
        person_info = ""
        if self.person_context:
            person_info = f"""
PERSON YOU'RE CALLING:
- Name: {self.person_context.get('person_name', 'Unknown')}
- Company: {self.person_context.get('business_name', 'Unknown')}
- Industry: {self.person_context.get('business_type', 'Unknown')}
- Background: {self.person_context.get('custom_context', 'No additional context')}

Use this information naturally in conversation. Reference their work or company where relevant.
"""

        return f"""You are an AI assistant making outbound calls on behalf of William Marceau, an AI consultant.
{person_info}

YOUR MISSION:
- Gauge interest in AI consulting services
- Have a natural, friendly conversation
- Learn about their business and potential AI needs
- If interested, offer to schedule a call with William

ABOUT WILLIAM'S SERVICES:
- AI automation for businesses (customer service, data processing, workflows)
- Custom AI assistants and chatbots
- Voice AI for phone systems (like this call!)
- AI strategy consulting

CONVERSATION GUIDELINES:
- Be warm, friendly, and NOT pushy
- Ask open-ended questions about their business
- Listen for pain points that AI could solve
- Keep responses SHORT (1-2 sentences) - this is a phone call
- If they're not interested, thank them and end politely
- If they seem busy, offer to call back at a better time

EMOTIONAL TONE GUIDELINES:
- Opening: Warm and approachable, like a friendly neighbor
- Describing services: Enthusiastic but genuine ("It's really cool actually!")
- When they show interest: Excited but not over-the-top ("That's great to hear!")
- Asking questions: Curious and genuinely interested in their business
- When they're hesitant: Understanding and patient ("I totally get it, no pressure at all")
- When they're not interested: Graceful and warm ("No worries at all! Thanks for taking the time")
- When they're busy: Respectful ("I can tell you're busy - when would be a better time?")
- Closing: Appreciative and positive ("Thanks so much for chatting!")

RESPONSE TRIGGERS:

If they say YES/interested:
"That's great! William would love to chat with you. Would it be okay if he reached out to schedule a quick 15-minute call to learn more about your business?"
[INTERESTED]

If they say NO/not interested:
"No problem at all! Thanks for taking the time to chat. Have a great day!"
[NOT_INTERESTED]

If they want to schedule now:
"Perfect! William will follow up with you shortly to find a time that works. What's the best way to reach you?"
[SCHEDULE_CALLBACK]

If they ask to be called back later:
"Absolutely, when would be a better time to call?"
[CALLBACK_REQUESTED]

If they hang up or seem annoyed:
"Thank you for your time. Have a great day!"
[END_CALL]

If they explicitly ask to speak with William or a real person:
"Absolutely! Let me connect you with William right now. Please hold for just a moment."
[TRANSFER_TO_WILLIAM]

IMPORTANT:
- Never claim William is available right now
- Don't make specific promises about pricing
- Be honest that you're an AI assistant
- Keep it conversational, not scripted"""

    async def process_turn(
        self,
        state: ConversationState,
        customer_input: str
    ) -> tuple[str, ConversationState]:
        """Process a conversation turn for consulting outreach."""
        # Add customer message to context
        state.context.append({
            "role": "user",
            "content": customer_input
        })

        # Get AI response - using Haiku for faster response time on phone calls
        response = self.client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=150,
            system=self.get_system_prompt(),
            messages=state.context
        )

        ai_text = response.content[0].text

        # Add AI response to context
        state.context.append({
            "role": "assistant",
            "content": ai_text
        })

        # Check for outcome markers
        if "[NOT_INTERESTED]" in ai_text:
            state.transfer_requested = True  # Use this to signal end
            ai_text = ai_text.replace("[NOT_INTERESTED]", "").strip()
        elif "[INTERESTED]" in ai_text:
            state.awaiting_confirmation = True  # Signal positive outcome
            ai_text = ai_text.replace("[INTERESTED]", "").strip()
        elif "[SCHEDULE_CALLBACK]" in ai_text:
            state.awaiting_confirmation = True
            ai_text = ai_text.replace("[SCHEDULE_CALLBACK]", "").strip()
        elif "[CALLBACK_REQUESTED]" in ai_text:
            ai_text = ai_text.replace("[CALLBACK_REQUESTED]", "").strip()
        elif "[END_CALL]" in ai_text:
            state.transfer_requested = True
            ai_text = ai_text.replace("[END_CALL]", "").strip()
        elif "[TRANSFER_TO_WILLIAM]" in ai_text:
            state.live_transfer_requested = True  # New flag for live transfer
            ai_text = ai_text.replace("[TRANSFER_TO_WILLIAM]", "").strip()

        return ai_text, state

    def create_initial_state(self, call_id: str) -> ConversationState:
        """Create initial conversation state for outreach call."""
        return ConversationState(
            call_id=call_id,
            restaurant_id=self.config.id,
            context=[{
                "role": "assistant",
                "content": self.config.greeting
            }]
        )

    def get_greeting(self) -> str:
        """Get the initial greeting for the outreach call."""
        return self.config.greeting


class InboundAssistantEngine:
    """
    Fast-qualifying receptionist for William's inbound calls.

    Goal: Quickly determine if caller is a HOT LEAD and transfer immediately.
    NOT a data-gathering bot - a smart routing assistant.
    """

    def __init__(self):
        self.settings = get_settings()
        self.client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)

    def get_system_prompt(self) -> str:
        """Generate system prompt for fast-qualifying receptionist."""
        return """You are William Marceau's receptionist. Your job is to QUICKLY qualify callers and transfer hot leads immediately.

ABOUT WILLIAM:
- AI consultant helping businesses automate with voice AI, chatbots, and automation
- Based in Naples, Florida

YOUR MISSION: Fast qualification - immediate transfer for real leads

ALWAYS TRANSFER (no questions needed):
- They mention needing AI, automation, or tech help for their business
- They're calling about a project or potential work
- They want to discuss services or pricing
- They sound like a business owner with a problem to solve
- They specifically asked to speak with William
- Media/press inquiries (reporters, journalists, podcast hosts)
- Partnership or collaboration requests from other businesses
- Existing customer with a complaint or issue
- Referrals mentioning who sent them
- Urgent/emergency language ("down", "broken", "urgent", "help now")
- Personal calls (friends, family) - still transfer, just note it

NON-LEADS (take message or end call):
- Sales calls / vendors trying to sell something
- Spam / robocalls
- Wrong numbers
- Recruiters
- Surveys or research calls
- General inquiries with no urgency (offer to take message)

SCAM/ROBOCALL DETECTION (end immediately):
- Recorded voice with "you've won", "selected", "free cruise"
- IRS, SSA, or government impersonation
- Requests for personal/financial information
Response: End without engaging or brief "We're not interested. Goodbye."
[END_CALL]

CONVERSATION STYLE:
- Be warm but efficient - 1-2 sentence responses MAX
- Don't interrogate - one quick question to qualify if unclear
- If they sound like a lead, TRANSFER IMMEDIATELY
- Don't make them repeat themselves

CONVERSATION LIMITS:
- Maximum 2 qualifying questions before deciding
- After 4 exchanges with no substance, offer to take message or end politely
- Don't get into debates or explanations

SAFETY - End immediately if:
- Threats or threatening language
- Continued harassment
- Impaired caller who cannot communicate

Response: "I'm going to end this call now. Goodbye."
[END_CALL]

EXAMPLE FLOWS:

Caller: "Hi, I'm looking for help automating my business"
You: "Absolutely! Let me connect you with William right now."
[TRANSFER_NOW]

Caller: "I saw William's work and wanted to discuss a project"
You: "Perfect, let me get William on the line for you."
[TRANSFER_NOW]

Caller: "Is William available?"
You: "He is! What's this regarding?"
(Then qualify based on response)

Caller: "I'm a reporter from TechCrunch"
You: "Great! Let me connect you with William."
[TRANSFER_NOW]

Caller: "I'm selling insurance..."
You: "Thanks for calling, but we're all set. Have a great day!"
[END_CALL]

Caller: (robocall voice) "Congratulations, you've been selected..."
[END_CALL]

Caller: "Just wanted to leave a message"
You: "Of course! What would you like me to tell him?"
(Take brief message, then:)
[MESSAGE_COMPLETE]

RESPONSE TRIGGERS:

[TRANSFER_NOW] - Hot lead detected, transfer immediately
[MESSAGE_COMPLETE] - Non-urgent, took their message
[END_CALL] - Sales call, spam, threat, or caller wants to end

CRITICAL: Bias toward transferring. When in doubt, TRANSFER. William would rather take a borderline call than miss a real opportunity."""

    async def process_turn(
        self,
        state: ConversationState,
        caller_input: str
    ) -> tuple[str, ConversationState]:
        """Process a conversation turn - fast qualification."""
        state.context.append({
            "role": "user",
            "content": caller_input
        })

        # Use Haiku for speed - qualification doesn't need Sonnet
        response = self.client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=100,  # Short responses only
            system=self.get_system_prompt(),
            messages=state.context
        )

        ai_text = response.content[0].text

        state.context.append({
            "role": "assistant",
            "content": ai_text
        })

        # Check for triggers
        if "[TRANSFER_NOW]" in ai_text:
            state.live_transfer_requested = True
            ai_text = ai_text.replace("[TRANSFER_NOW]", "").strip()

        elif "[MESSAGE_COMPLETE]" in ai_text:
            ai_text = ai_text.replace("[MESSAGE_COMPLETE]", "").strip()
            state.awaiting_confirmation = True

        elif "[END_CALL]" in ai_text:
            state.transfer_requested = True
            ai_text = ai_text.replace("[END_CALL]", "").strip()

        return ai_text, state

    def create_initial_state(self, call_id: str) -> ConversationState:
        """Create initial conversation state for inbound call."""
        return ConversationState(
            call_id=call_id,
            restaurant_id="william_assistant",
            context=[{
                "role": "assistant",
                "content": "Hi, you've reached William Marceau's office. How can I help you?"
            }]
        )

    def get_greeting(self) -> str:
        """Short, professional greeting."""
        return "Hi, you've reached William Marceau's office. How can I help you?"


class WarmFollowUpEngine:
    """
    For confirming scheduled calls - NOT cold outreach.

    Use case: "Hi, this is William's office confirming your 2pm call today"
    Human (William) takes the actual conversation.
    """

    def __init__(self):
        self.settings = get_settings()
        self.client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)

    def get_confirmation_greeting(self, person_name: str, scheduled_time: str) -> str:
        """Generate a warm confirmation greeting."""
        if person_name:
            return f"Hi {person_name}, this is William Marceau's office calling to confirm your {scheduled_time} call. Is this still a good time?"
        return f"Hi, this is William Marceau's office calling to confirm your {scheduled_time} call. Is this still a good time?"

    def get_system_prompt(self) -> str:
        """System prompt for confirmation calls only."""
        return """You are confirming a scheduled call for William Marceau.

YOUR ONLY JOB: Confirm the appointment and transfer to William

FLOW:
1. Confirm they're available for the scheduled call
2. If yes → transfer to William immediately
3. If no → offer to reschedule and take their preferred time

RESPONSES:

If they confirm (yes, ready, available, etc):
"Perfect! Let me connect you with William now."
[TRANSFER_NOW]

If they need to reschedule:
"No problem! When would work better for you?"
(Note their preferred time)
"Got it, William will reach out to confirm the new time. Thanks!"
[RESCHEDULE]
New time: {their response}

If it's a bad number or wrong person:
"I apologize for the confusion. Have a great day!"
[END_CALL]

Keep responses to ONE sentence. Be warm but brief."""

    async def process_turn(
        self,
        state: ConversationState,
        caller_input: str
    ) -> tuple[str, ConversationState]:
        """Process confirmation call turn."""
        state.context.append({
            "role": "user",
            "content": caller_input
        })

        response = self.client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=80,
            system=self.get_system_prompt(),
            messages=state.context
        )

        ai_text = response.content[0].text

        state.context.append({
            "role": "assistant",
            "content": ai_text
        })

        if "[TRANSFER_NOW]" in ai_text:
            state.live_transfer_requested = True
            ai_text = ai_text.replace("[TRANSFER_NOW]", "").strip()

        elif "[RESCHEDULE]" in ai_text:
            parts = ai_text.split("[RESCHEDULE]")
            ai_text = parts[0].strip()
            if len(parts) > 1:
                state.message_for_william = f"Reschedule request: {parts[1].strip()}"
            state.awaiting_confirmation = True

        elif "[END_CALL]" in ai_text:
            state.transfer_requested = True
            ai_text = ai_text.replace("[END_CALL]", "").strip()

        return ai_text, state

    def create_initial_state(self, call_id: str, person_name: str = None, scheduled_time: str = None) -> ConversationState:
        """Create state for confirmation call."""
        greeting = self.get_confirmation_greeting(person_name, scheduled_time or "scheduled")
        return ConversationState(
            call_id=call_id,
            restaurant_id="william_followup",
            context=[{
                "role": "assistant",
                "content": greeting
            }],
            person_context={
                "person_name": person_name,
                "scheduled_time": scheduled_time
            }
        )
