"""Business Voice Engine - Multi-business AI phone handler."""

import uuid
import json
from datetime import datetime
from typing import Optional
import anthropic

from .config import get_settings
from .models import ConversationState, TranscriptEntry


class BusinessVoiceEngine:
    """Handles AI conversation logic for any business type."""

    def __init__(self, business_config: dict, system_prompt: str):
        """
        Initialize voice engine for a specific business.

        Args:
            business_config: Business configuration dict (name, services, etc.)
            system_prompt: The full system prompt for the AI
        """
        self.config = business_config
        self.system_prompt = system_prompt
        self.settings = get_settings()
        self.client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)

    def create_initial_state(self, call_id: str) -> ConversationState:
        """Create initial conversation state for a new call."""
        return ConversationState(
            call_id=call_id,
            restaurant_id=self.config.get("name", "unknown"),  # Use business name as ID
            context=[],  # Message history for LLM
            transfer_requested=False,
            awaiting_confirmation=False
        )

    async def process_turn(
        self,
        state: ConversationState,
        customer_input: str
    ) -> tuple[str, ConversationState]:
        """
        Process a conversation turn.

        Args:
            state: Current conversation state
            customer_input: What the customer said

        Returns:
            Tuple of (AI response text, updated state)
        """
        # Add customer input to history
        state.context.append({
            "role": "user",
            "content": customer_input
        })

        # Build messages for Claude
        messages = state.context.copy()

        # Call Claude
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",  # Fast and capable
                max_tokens=300,  # Keep responses short for phone
                system=self.system_prompt,
                messages=messages
            )

            ai_response = response.content[0].text

            # Check for special markers in response
            if "[TRANSFER]" in ai_response:
                state.transfer_requested = True
                # Extract response before marker
                ai_response = ai_response.split("[TRANSFER]")[0].strip()

            if "[APPOINTMENT_SCHEDULED]" in ai_response or "[QUOTE_REQUEST]" in ai_response:
                state.awaiting_confirmation = True
                # Extract collected info if present
                ai_response = ai_response.split("[APPOINTMENT_SCHEDULED]")[0].strip()
                ai_response = ai_response.split("[QUOTE_REQUEST]")[0].strip()

            # Add AI response to history
            state.context.append({
                "role": "assistant",
                "content": ai_response
            })

            return ai_response, state

        except Exception as e:
            # Graceful error handling
            error_response = (
                "I apologize, I'm having a bit of trouble. "
                "Let me connect you with someone who can help."
            )
            state.transfer_requested = True
            return error_response, state


# Business registry - maps phone numbers to configurations
BUSINESS_REGISTRY = {
    # Square Foot Shipping
    "+12398803365": {
        "name": "Square Foot Shipping",
        "phone": "+12398803365",
        "owner": "William George",
        "owner_phone": "+12396921101",  # William George's personal number for transfers
        "type": "logistics",
        "greeting": "Thank you for calling Square Foot Shipping! This is our AI assistant. How can I help you today?",
        "services": [
            "Warehouse Storage - Climate-controlled with 24/7 security",
            "Freight Shipping - LTL and FTL ground freight",
            "Fulfillment Services - Pick, pack, and ship",
            "Cross-Docking - Rapid turnaround",
            "Last-Mile Delivery - Same-day available",
            "Inventory Management - Real-time tracking"
        ],
        "system_prompt": """You are an AI phone assistant for Square Foot Shipping, a logistics company owned by William George.

GREETING: "Thank you for calling Square Foot Shipping! This is our AI assistant. How can I help you today?"

YOUR JOB:
1. Answer questions about shipping and storage services
2. Collect information for quotes (name, phone, what they need)
3. Schedule callbacks with William George
4. Transfer for complex inquiries

SERVICES:
- Warehouse Storage: Climate-controlled, 24/7 security
- Freight Shipping: LTL and FTL ground freight
- Fulfillment: Pick, pack, ship for e-commerce
- Cross-Docking: Rapid turnaround
- Last-Mile Delivery: Same-day options
- Inventory Management: Real-time tracking

PRICING: We don't give prices over phone - quotes are customized based on needs.

For quotes, collect: Name, phone, email, what they need shipped/stored, timing.

TONE: Professional but friendly. We have 99% on-time rate - mention our reliability!

End with [TRANSFER] if they need to speak to William.
End with [QUOTE_REQUEST] when you've collected their info for a quote.

Keep responses SHORT - this is a phone call."""
    },

    # SW Florida Comfort HVAC
    "+12397666129": {
        "name": "SW Florida Comfort HVAC",
        "phone": "+12397666129",
        "owner": "William Marceau Sr.",
        "owner_phone": "+12393987544",  # Bill's personal number for service calls/transfers
        "type": "hvac",
        "greeting": "Thank you for calling SW Florida Comfort HVAC! This is our AI assistant. Are you calling about an emergency, or can I help you schedule a service?",
        "services": [
            "AC Repair - Same-day service, all brands",
            "AC Installation - Free estimates, financing available",
            "Maintenance Plans - $199/year, 2 tune-ups",
            "24/7 Emergency - No overtime charges",
            "Duct Services - Cleaning, repair, insulation",
            "Indoor Air Quality - UV lights, HEPA filters"
        ],
        "system_prompt": """You are an AI phone assistant for SW Florida Comfort HVAC, owned by William Marceau Sr. (Bill).

GREETING: "Thank you for calling SW Florida Comfort HVAC! This is our AI assistant. Are you calling about an emergency, or can I help you schedule a service?"

PRIORITY: Identify EMERGENCIES first! If their AC is out in Florida, treat it urgently.

EMERGENCY SIGNALS:
- "AC is out" / "not cooling" / "no cold air"
- Mentions elderly, children, pets without AC
- "It's really hot"

FOR EMERGENCIES: "I understand - help is on the way. What's your address?"

SERVICES & PRICING:
- AC Repair: $89 diagnostic (waived with repair), same-day available
- AC Installation: Free estimates, 10-year warranties, financing
- Maintenance Plans: $199/year - 2 tune-ups, priority scheduling, 15% off repairs
- Emergency Service: 24/7, no overtime charges
- Duct Services: Cleaning, repair, insulation
- Air Quality: UV lights, HEPA filtration, dehumidifiers

SERVICE AREAS: Naples, Fort Myers, Cape Coral, Bonita Springs, Estero, Marco Island, Lehigh Acres, Sanibel

For scheduling, collect: Name, address, phone, issue description, system brand/age if known.

TONE: Empathetic for emergencies, efficient for scheduling. Bill personally oversees major installs.

End with [TRANSFER] to connect to Bill.
End with [APPOINTMENT_SCHEDULED] when appointment is booked.

Keep responses SHORT - this is a phone call."""
    }
}


def get_business_by_phone(to_number: str) -> Optional[dict]:
    """
    Get business configuration by the phone number that was called.

    Args:
        to_number: The Twilio 'To' number (the number that was called)

    Returns:
        Business config dict or None if not found
    """
    # Normalize phone number
    clean_number = ''.join(filter(str.isdigit, to_number))
    if not clean_number.startswith('1'):
        clean_number = '1' + clean_number
    clean_number = '+' + clean_number

    return BUSINESS_REGISTRY.get(clean_number)


def get_engine_for_business(to_number: str) -> Optional[BusinessVoiceEngine]:
    """
    Get a voice engine configured for the business that was called.

    Args:
        to_number: The Twilio 'To' number

    Returns:
        Configured BusinessVoiceEngine or None
    """
    config = get_business_by_phone(to_number)
    if not config:
        return None

    return BusinessVoiceEngine(
        business_config=config,
        system_prompt=config["system_prompt"]
    )


def list_configured_businesses():
    """List all businesses with voice AI configured."""
    return [
        {
            "name": config["name"],
            "phone": config["phone"],
            "type": config["type"],
            "owner": config["owner"]
        }
        for config in BUSINESS_REGISTRY.values()
    ]
