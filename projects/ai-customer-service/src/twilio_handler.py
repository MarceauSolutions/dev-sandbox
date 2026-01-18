"""Twilio webhook handlers for voice calls."""

import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.request_validator import RequestValidator

from .config import get_settings
from .models import Call, CallStatus, Restaurant, ConversationState, TranscriptEntry
from .voice_engine import VoiceEngine


router = APIRouter(prefix="/twilio", tags=["twilio"])

# In-memory stores (replace with database in production)
active_calls: dict[str, Call] = {}
conversation_states: dict[str, ConversationState] = {}
restaurants: dict[str, Restaurant] = {}


def get_demo_restaurant() -> Restaurant:
    """Get or create demo restaurant for testing."""
    if "demo" not in restaurants:
        restaurants["demo"] = Restaurant(
            id="demo",
            name="Mario's Pizzeria",
            phone_number="+18552399364",  # Your Twilio number
            fallback_number="+12395555555",
            greeting="Thank you for calling Mario's Pizzeria! What can I get for you today?",
            menu=[
                {"id": "cheese_pizza", "name": "Cheese Pizza", "price": 14.99, "category": "Pizza", "description": "Classic cheese pizza"},
                {"id": "pepperoni_pizza", "name": "Pepperoni Pizza", "price": 16.99, "category": "Pizza", "description": "Pepperoni with mozzarella"},
                {"id": "veggie_pizza", "name": "Veggie Pizza", "price": 17.99, "category": "Pizza", "description": "Bell peppers, onions, mushrooms"},
                {"id": "wings", "name": "Buffalo Wings", "price": 12.99, "category": "Appetizers", "description": "10 crispy wings with buffalo sauce"},
                {"id": "garlic_bread", "name": "Garlic Bread", "price": 5.99, "category": "Appetizers", "description": "Toasted with garlic butter"},
                {"id": "caesar_salad", "name": "Caesar Salad", "price": 9.99, "category": "Salads", "description": "Romaine, parmesan, croutons"},
                {"id": "soda", "name": "Soda", "price": 2.99, "category": "Drinks", "description": "Coke, Sprite, or Dr Pepper"},
            ]
        )
    return restaurants["demo"]


def validate_twilio_request(request: Request, params: dict) -> bool:
    """Validate that request came from Twilio."""
    settings = get_settings()
    if not settings.twilio_auth_token:
        return True  # Skip validation in dev

    validator = RequestValidator(settings.twilio_auth_token)
    signature = request.headers.get("X-Twilio-Signature", "")
    url = str(request.url)

    return validator.validate(url, params, signature)


@router.post("/voice")
async def handle_incoming_call(
    request: Request,
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...)
):
    """Handle incoming voice call from Twilio."""
    settings = get_settings()

    # Create call record
    call = Call(
        id=str(uuid.uuid4()),
        restaurant_id="demo",  # Would look up by To number
        twilio_sid=CallSid,
        caller_number=From,
        status=CallStatus.IN_PROGRESS
    )
    active_calls[CallSid] = call

    # Get restaurant and create conversation state
    restaurant = get_demo_restaurant()
    engine = VoiceEngine(restaurant)
    state = engine.create_initial_state(call.id)
    conversation_states[CallSid] = state

    # Add greeting to transcript
    call.transcript.append(TranscriptEntry(
        role="ai",
        content=restaurant.greeting
    ))

    # Build TwiML response
    response = VoiceResponse()

    # Say greeting
    response.say(
        restaurant.greeting,
        voice="Polly.Joanna"  # AWS Polly voice
    )

    # Gather speech input
    gather = Gather(
        input="speech",
        action=f"{settings.base_url}/twilio/gather",
        method="POST",
        speech_timeout="auto",
        speech_model="phone_call",
        language="en-US"
    )
    response.append(gather)

    # If no input, prompt again
    response.say("I didn't catch that. What would you like to order?", voice="Polly.Joanna")
    response.redirect(f"{settings.base_url}/twilio/voice")

    return Response(content=str(response), media_type="application/xml")


@router.post("/gather")
async def handle_speech_input(
    request: Request,
    CallSid: str = Form(...),
    SpeechResult: str = Form(None),
    Confidence: float = Form(None)
):
    """Handle speech input from customer."""
    import logging
    logging.basicConfig(level=logging.INFO)
    logging.info(f"GATHER: CallSid={CallSid}, Speech={SpeechResult}, Confidence={Confidence}")

    settings = get_settings()

    if not SpeechResult:
        # No speech detected
        response = VoiceResponse()
        response.say("I didn't catch that. Could you please repeat?", voice="Polly.Joanna")
        gather = Gather(
            input="speech",
            action=f"{settings.base_url}/twilio/gather",
            method="POST",
            speech_timeout="auto"
        )
        response.append(gather)
        return Response(content=str(response), media_type="application/xml")

    # Get call and state
    call = active_calls.get(CallSid)
    state = conversation_states.get(CallSid)

    if not call or not state:
        response = VoiceResponse()
        response.say("I'm sorry, there was an error. Please call back.", voice="Polly.Joanna")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    # Log customer input
    call.transcript.append(TranscriptEntry(
        role="customer",
        content=SpeechResult
    ))

    # Process through voice engine
    restaurant = get_demo_restaurant()
    engine = VoiceEngine(restaurant)

    try:
        ai_response, state = await engine.process_turn(state, SpeechResult)
        conversation_states[CallSid] = state

        # Log AI response
        call.transcript.append(TranscriptEntry(
            role="ai",
            content=ai_response
        ))

    except Exception as e:
        # Error handling
        ai_response = "I'm having trouble understanding. Let me connect you with our staff."
        state.transfer_requested = True

    # Build response
    response = VoiceResponse()

    if state.transfer_requested:
        # Transfer to human
        response.say(ai_response, voice="Polly.Joanna")
        response.say("Please hold while I transfer you.", voice="Polly.Joanna")
        response.dial(restaurant.fallback_number)
        call.status = CallStatus.TRANSFERRED
        call.transfer_reason = "Customer request or AI limitation"

    elif state.current_order and state.current_order.status.value == "pending":
        # Order complete
        response.say(ai_response, voice="Polly.Joanna")
        response.say(
            f"Your order total is ${state.current_order.total:.2f}. "
            "It will be ready in about 20 minutes. Thank you for calling!",
            voice="Polly.Joanna"
        )
        response.hangup()
        call.status = CallStatus.COMPLETED
        call.order_id = state.current_order.id

    else:
        # Continue conversation
        response.say(ai_response, voice="Polly.Joanna")
        gather = Gather(
            input="speech",
            action=f"{settings.base_url}/twilio/gather",
            method="POST",
            speech_timeout="auto",
            speech_model="phone_call"
        )
        response.append(gather)

        # Fallback if no response
        response.say("Are you still there?", voice="Polly.Joanna")
        response.redirect(f"{settings.base_url}/twilio/gather")

    return Response(content=str(response), media_type="application/xml")


@router.post("/status")
async def handle_call_status(
    request: Request,
    CallSid: str = Form(...),
    CallStatus: str = Form(None)
):
    """Handle call status updates from Twilio."""
    import logging
    logging.info(f"Status update: {CallSid} -> {CallStatus}")

    call = active_calls.get(CallSid)
    if call and CallStatus:
        from .models import CallStatus as CallStatusEnum
        if CallStatus == "completed":
            call.status = CallStatusEnum.COMPLETED
            call.ended_at = datetime.utcnow()
            call.duration_seconds = int((call.ended_at - call.started_at).total_seconds())
        elif CallStatus == "failed":
            call.status = CallStatusEnum.FAILED
        elif CallStatus == "no-answer":
            call.status = CallStatusEnum.ABANDONED

    return {"status": "ok"}


@router.get("/calls/{call_sid}")
async def get_call(call_sid: str):
    """Get call details (for debugging)."""
    call = active_calls.get(call_sid)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call


@router.get("/calls")
async def list_calls():
    """List all calls (for debugging)."""
    return list(active_calls.values())
