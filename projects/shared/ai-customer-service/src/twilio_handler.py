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
from .voice_engine import VoiceEngine, ConsultingVoiceEngine, InboundAssistantEngine, WarmFollowUpEngine
from .voice_styles import get_voice_name


router = APIRouter(prefix="/twilio", tags=["twilio"])

# In-memory stores (replace with database in production)
active_calls: dict[str, Call] = {}
conversation_states: dict[str, ConversationState] = {}
restaurants: dict[str, Restaurant] = {}
outreach_personalization: dict[str, dict] = {}  # phone_number -> personalization data


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


def get_ai_consulting_config(
    business_name: str = None,
    business_type: str = None,
    person_name: str = None,
    custom_context: str = None
) -> Restaurant:
    """Get AI consulting outreach configuration with optional personalization."""
    # Build personalized greeting based on available info
    if person_name and business_name and custom_context:
        # Highly personalized - we researched them
        greeting = (
            f"Hi, is this {person_name}? "
            f"This is an AI assistant calling on behalf of William Marceau. "
            f"He came across your profile at {business_name} and was really impressed by your work in {custom_context}. "
            f"He thought there might be some interesting ways AI could help with things like data analysis, training automation, or workflow optimization. "
            f"Do you have a moment to chat?"
        )
    elif person_name and business_name:
        greeting = (
            f"Hi, is this {person_name}? "
            f"This is an AI assistant calling on behalf of William Marceau. "
            f"He noticed your work at {business_name} and wanted to reach out about some AI consulting services that might be helpful. "
            f"Do you have a moment to chat?"
        )
    elif business_name and business_type:
        greeting = (
            f"Hi! This is an AI assistant calling on behalf of William Marceau. "
            f"He noticed {business_name} and wanted to reach out to see if you might be interested in any AI services for your {business_type} business. "
            f"Things like automated customer service, booking systems, or content creation. Do you have a moment to chat?"
        )
    elif business_name:
        greeting = (
            f"Hi! This is an AI assistant calling on behalf of William Marceau. "
            f"He noticed {business_name} and wanted to reach out to see if you might be interested in any AI consulting services for your business. "
            f"Do you have a moment to chat?"
        )
    else:
        greeting = (
            "Hi! This is an AI assistant calling on behalf of William Marceau. "
            "He wanted to reach out and see if you might be interested in any AI consulting services for your business. "
            "Do you have a moment to chat?"
        )

    # Update or create config
    restaurants["consulting"] = Restaurant(
        id="consulting",
        name="William's AI Consulting",
        phone_number="+18552399364",
        fallback_number="+12393985676",  # William's number
        greeting=greeting,
        menu=[]  # Not used for consulting
    )
    return restaurants["consulting"]


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

    # Neural voice for natural sound
    voice = get_voice_name("female_us")  # Polly.Joanna-Neural

    # Say greeting (plain text - Polly adds natural prosody)
    response.say(restaurant.greeting, voice=voice)

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
    response.say("I didn't catch that. What would you like to order?", voice=voice)
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

    # Neural voice for natural sound
    voice = get_voice_name("female_us")

    if not SpeechResult:
        # No speech detected
        response = VoiceResponse()
        response.say("I didn't catch that. Could you please repeat?", voice=voice)
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
        response.say("I'm sorry, there was an error. Please call back.", voice=voice)
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

    # Build response (plain text - Polly neural voice adds natural prosody)
    response = VoiceResponse()

    if state.transfer_requested:
        # Transfer to human
        response.say(ai_response, voice=voice)
        response.say("Please hold while I transfer you.", voice=voice)
        response.dial(restaurant.fallback_number)
        call.status = CallStatus.TRANSFERRED
        call.transfer_reason = "Customer request or AI limitation"

    elif state.current_order and state.current_order.status.value == "pending":
        # Order complete
        response.say(ai_response, voice=voice)
        total_text = (
            f"Your order total is ${state.current_order.total:.2f}. "
            "It will be ready in about 20 minutes. Thank you for calling!"
        )
        response.say(total_text, voice=voice)
        response.hangup()
        call.status = CallStatus.COMPLETED
        call.order_id = state.current_order.id

    else:
        # Continue conversation
        response.say(ai_response, voice=voice)
        gather = Gather(
            input="speech",
            action=f"{settings.base_url}/twilio/gather",
            method="POST",
            speech_timeout="auto",
            speech_model="phone_call"
        )
        response.append(gather)

        # Fallback if no response
        response.say("Are you still there?", voice=voice)
        response.redirect(f"{settings.base_url}/twilio/gather")

    return Response(content=str(response), media_type="application/xml")


@router.post("/status")
async def handle_call_status(request: Request):
    """Handle call status updates from Twilio."""
    import logging
    logging.basicConfig(level=logging.INFO)

    try:
        form = await request.form()
        call_sid = form.get("CallSid")
        call_status = form.get("CallStatus")
        logging.info(f"Status update: {call_sid} -> {call_status}")

        call = active_calls.get(call_sid)
        if call and call_status:
            from .models import CallStatus as CallStatusEnum
            if call_status == "completed":
                call.status = CallStatusEnum.COMPLETED
                call.ended_at = datetime.utcnow()
                call.duration_seconds = int((call.ended_at - call.started_at).total_seconds())
            elif call_status == "failed":
                call.status = CallStatusEnum.FAILED
            elif call_status == "no-answer":
                call.status = CallStatusEnum.ABANDONED

        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Status endpoint error: {e}")
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


# ============================================
# OUTREACH ENDPOINTS (Consulting Calls)
# ============================================

@router.post("/register-outreach")
async def register_outreach_personalization(request: Request):
    """Register personalization data for an upcoming outreach call."""
    import logging
    logging.basicConfig(level=logging.INFO)

    try:
        data = await request.json()
        to_number = data.get("to_number")
        if to_number:
            # Normalize phone number
            to_number = to_number.replace(" ", "").replace("-", "")
            if not to_number.startswith("+"):
                to_number = "+1" + to_number.lstrip("+1")

            outreach_personalization[to_number] = {
                "person_name": data.get("person_name"),
                "business_name": data.get("business_name"),
                "business_type": data.get("business_type"),
                "custom_context": data.get("custom_context")
            }
            logging.info(f"Registered personalization for {to_number}: {outreach_personalization[to_number]}")
            return {"status": "ok", "phone": to_number}
        return {"status": "error", "message": "to_number required"}
    except Exception as e:
        logging.error(f"Register error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/outreach")
async def handle_outreach_call(request: Request):
    """Handle outbound consulting call - initial greeting."""
    import logging
    logging.basicConfig(level=logging.INFO)

    try:
        settings = get_settings()

        # Parse form data flexibly
        form = await request.form()
        CallSid = form.get("CallSid")
        From = form.get("From")
        To = form.get("To")

        # Look up personalization by To number (registered before call)
        personalization = outreach_personalization.get(To, {})
        business_name = personalization.get("business_name") or form.get("business_name") or request.query_params.get("business_name")
        business_type = personalization.get("business_type") or form.get("business_type") or request.query_params.get("business_type")
        person_name = personalization.get("person_name") or form.get("person_name") or request.query_params.get("person_name")
        custom_context = personalization.get("custom_context") or form.get("custom_context") or request.query_params.get("custom_context")

        logging.info(f"OUTREACH: CallSid={CallSid}, To={To}, Person={person_name}, Business={business_name}, Type={business_type}")

        # Create call record
        call = Call(
            id=str(uuid.uuid4()),
            restaurant_id="consulting",
            twilio_sid=CallSid,
            caller_number=To,  # For outbound, "To" is who we're calling
            status=CallStatus.IN_PROGRESS
        )
        active_calls[CallSid] = call

        # Get consulting config with personalization and create conversation state
        config = get_ai_consulting_config(
            business_name=business_name,
            business_type=business_type,
            person_name=person_name,
            custom_context=custom_context
        )

        # Build person context for the AI engine
        person_context = {
            "person_name": person_name,
            "business_name": business_name,
            "business_type": business_type,
            "custom_context": custom_context
        }

        engine = ConsultingVoiceEngine(config, person_context=person_context)
        state = engine.create_initial_state(call.id)

        # Store person context in state for later turns
        state.person_context = person_context
        conversation_states[CallSid] = state

        # Add greeting to transcript
        call.transcript.append(TranscriptEntry(
            role="ai",
            content=config.greeting
        ))

        # Build TwiML response
        response = VoiceResponse()

        # Neural voice for natural sound
        voice = get_voice_name("female_us")

        # Say greeting (plain text - Polly neural voice adds natural prosody)
        response.say(config.greeting, voice=voice)

        # Gather speech input
        gather = Gather(
            input="speech",
            action=f"{settings.base_url}/twilio/outreach-gather",
            method="POST",
            speech_timeout="auto",
            speech_model="phone_call",
            language="en-US"
        )
        response.append(gather)

        # If no input, prompt again
        response.say("Hello? Are you still there?", voice=voice)
        response.redirect(f"{settings.base_url}/twilio/outreach")

        return Response(content=str(response), media_type="application/xml")

    except Exception as e:
        # Log the error and return a graceful TwiML response
        logging.error(f"OUTREACH ERROR: {e}")
        import traceback
        logging.error(traceback.format_exc())

        # Still return valid TwiML so call doesn't fail
        response = VoiceResponse()
        voice = get_voice_name("female_us")
        response.say("I apologize, we're experiencing technical difficulties. Please try again later.", voice=voice)
        response.hangup()
        return Response(content=str(response), media_type="application/xml")


# ============================================
# INBOUND ASSISTANT ENDPOINTS (William's Personal AI)
# ============================================

@router.post("/inbound")
async def handle_inbound_call(
    request: Request,
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...)
):
    """Handle inbound call to William's assistant."""
    import logging
    logging.basicConfig(level=logging.INFO)
    logging.info(f"INBOUND CALL: CallSid={CallSid}, From={From}")

    settings = get_settings()

    # Create call record
    call = Call(
        id=str(uuid.uuid4()),
        restaurant_id="william_assistant",
        twilio_sid=CallSid,
        caller_number=From,
        status=CallStatus.IN_PROGRESS
    )
    active_calls[CallSid] = call

    # Create inbound assistant engine and state
    engine = InboundAssistantEngine()
    state = engine.create_initial_state(call.id)
    conversation_states[CallSid] = state

    # Add greeting to transcript
    greeting = engine.get_greeting()
    call.transcript.append(TranscriptEntry(
        role="ai",
        content=greeting
    ))

    # Build TwiML response
    response = VoiceResponse()
    voice = get_voice_name("female_us")

    # Say greeting
    response.say(greeting, voice=voice)

    # Gather speech input
    gather = Gather(
        input="speech",
        action=f"{settings.base_url}/twilio/inbound-gather",
        method="POST",
        speech_timeout="auto",
        speech_model="phone_call",
        language="en-US"
    )
    response.append(gather)

    # If no input, prompt again
    response.say("Hello? Are you still there?", voice=voice)
    response.redirect(f"{settings.base_url}/twilio/inbound")

    return Response(content=str(response), media_type="application/xml")


@router.post("/inbound-gather")
async def handle_inbound_speech(
    request: Request,
    CallSid: str = Form(...),
    SpeechResult: str = Form(None),
    Confidence: float = Form(None)
):
    """Handle speech input during inbound call."""
    import logging
    logging.basicConfig(level=logging.INFO)
    logging.info(f"INBOUND GATHER: CallSid={CallSid}, Speech={SpeechResult}")

    settings = get_settings()
    voice = get_voice_name("female_us")

    if not SpeechResult:
        response = VoiceResponse()
        response.say("I didn't catch that. Could you please repeat?", voice=voice)
        gather = Gather(
            input="speech",
            action=f"{settings.base_url}/twilio/inbound-gather",
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
        response.say("I'm sorry, there was an error. Please call back.", voice=voice)
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    # Log caller input
    call.transcript.append(TranscriptEntry(
        role="customer",
        content=SpeechResult
    ))

    # Process through inbound assistant engine
    engine = InboundAssistantEngine()

    try:
        ai_response, state = await engine.process_turn(state, SpeechResult)
        conversation_states[CallSid] = state

        call.transcript.append(TranscriptEntry(
            role="ai",
            content=ai_response
        ))

    except Exception as e:
        logging.error(f"Error in inbound: {e}")
        ai_response = "I'm having trouble. Let me connect you with William."
        state.live_transfer_requested = True

    # Build response
    response = VoiceResponse()

    if getattr(state, 'live_transfer_requested', False):
        # Try to connect to William
        response.say(ai_response, voice=voice)
        response.say("Connecting you now. Please hold.", voice=voice)
        # Use callerId so William's phone shows the business number, not "Unknown"
        dial = response.dial(caller_id=settings.twilio_phone_number, timeout=30)
        dial.number("+12393985676")
        call.status = CallStatus.TRANSFERRED

    elif state.transfer_requested:
        # End call
        response.say(ai_response, voice=voice)
        response.hangup()
        call.status = CallStatus.COMPLETED

    elif state.awaiting_confirmation:
        # Message taken - send notification to William
        response.say(ai_response, voice=voice)
        response.say("Thanks for calling! Have a great day!", voice=voice)
        response.hangup()
        call.status = CallStatus.COMPLETED

        # Log the message for William (would integrate with SMS/email in production)
        if state.message_for_william:
            logging.info(f"MESSAGE FOR WILLIAM from {call.caller_number}:")
            logging.info(state.message_for_william)

    else:
        # Continue conversation
        response.say(ai_response, voice=voice)
        gather = Gather(
            input="speech",
            action=f"{settings.base_url}/twilio/inbound-gather",
            method="POST",
            speech_timeout="auto",
            speech_model="phone_call"
        )
        response.append(gather)

        response.say("Are you still there?", voice=voice)
        response.redirect(f"{settings.base_url}/twilio/inbound-gather")

    return Response(content=str(response), media_type="application/xml")


@router.post("/outreach-gather")
async def handle_outreach_speech(request: Request):
    """Handle speech input during consulting outreach call."""
    import logging
    logging.basicConfig(level=logging.INFO)

    settings = get_settings()
    voice = get_voice_name("female_us")

    try:
        # Parse form data flexibly (like /outreach endpoint)
        form = await request.form()
        CallSid = form.get("CallSid")
        SpeechResult = form.get("SpeechResult")
        Confidence = form.get("Confidence")

        logging.info(f"OUTREACH GATHER: CallSid={CallSid}, Speech={SpeechResult}, Confidence={Confidence}")

        if not SpeechResult:
            # No speech detected
            response = VoiceResponse()
            response.say("I didn't catch that. Could you please repeat?", voice=voice)
            gather = Gather(
                input="speech",
                action=f"{settings.base_url}/twilio/outreach-gather",
                method="POST",
                speech_timeout="auto"
            )
            response.append(gather)
            return Response(content=str(response), media_type="application/xml")

        # Get call and state
        call = active_calls.get(CallSid)
        state = conversation_states.get(CallSid)

        if not call or not state:
            logging.error(f"No call/state found for {CallSid}")
            response = VoiceResponse()
            response.say("I'm sorry, there was an error. Thank you for your time!", voice=voice)
            response.hangup()
            return Response(content=str(response), media_type="application/xml")

        # Log customer input
        call.transcript.append(TranscriptEntry(
            role="customer",
            content=SpeechResult
        ))

        # Process through consulting voice engine with person context from state
        person_context = getattr(state, 'person_context', {}) or {}
        config = get_ai_consulting_config(
            business_name=person_context.get('business_name'),
            business_type=person_context.get('business_type'),
            person_name=person_context.get('person_name'),
            custom_context=person_context.get('custom_context')
        )
        engine = ConsultingVoiceEngine(config, person_context=person_context)

        try:
            ai_response, state = await engine.process_turn(state, SpeechResult)
            conversation_states[CallSid] = state

            # Log AI response
            call.transcript.append(TranscriptEntry(
                role="ai",
                content=ai_response
            ))

        except Exception as e:
            logging.error(f"Error in AI processing: {e}")
            ai_response = "I apologize, I'm having some technical difficulties. Thank you for your time!"
            state.transfer_requested = True

        # Build response
        response = VoiceResponse()

        # Check for live transfer to William
        if getattr(state, 'live_transfer_requested', False):
            response.say(ai_response, voice=voice)
            response.say("Connecting you now. Please hold.", voice=voice)
            # Use callerId so William's phone shows the business number
            dial = response.dial(caller_id=settings.twilio_phone_number, timeout=30)
            dial.number("+12393985676")
            call.status = CallStatus.TRANSFERRED
            call.transfer_reason = "Caller requested to speak with William"

        elif state.transfer_requested:
            response.say(ai_response, voice=voice)
            response.hangup()
            call.status = CallStatus.COMPLETED

        elif state.awaiting_confirmation:
            response.say(ai_response, voice=voice)
            response.say("William will be in touch soon. Thanks so much for your time today!", voice=voice)
            response.hangup()
            call.status = CallStatus.COMPLETED

        else:
            response.say(ai_response, voice=voice)
            gather = Gather(
                input="speech",
                action=f"{settings.base_url}/twilio/outreach-gather",
                method="POST",
                speech_timeout="auto",
                speech_model="phone_call"
            )
            response.append(gather)

            response.say("Are you still there?", voice=voice)
            response.redirect(f"{settings.base_url}/twilio/outreach-gather")

        return Response(content=str(response), media_type="application/xml")

    except Exception as e:
        logging.error(f"OUTREACH-GATHER ERROR: {e}")
        import traceback
        logging.error(traceback.format_exc())
        # Always return valid TwiML
        response = VoiceResponse()
        response.say("I apologize, we're experiencing technical difficulties. Thank you for your time!", voice=voice)
        response.hangup()
        return Response(content=str(response), media_type="application/xml")


# ============================================
# BUSINESS-SPECIFIC VOICE ENDPOINTS
# ============================================
# These endpoints route calls based on which phone number was called

from .business_voice_engine import get_engine_for_business, get_business_by_phone

# Store for business calls
business_calls: dict[str, Call] = {}
business_states: dict[str, ConversationState] = {}


@router.post("/business-voice")
async def handle_business_call(
    request: Request,
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...)
):
    """Handle incoming call to a business phone number."""
    import logging
    logging.basicConfig(level=logging.INFO)
    logging.info(f"BUSINESS CALL: From={From}, To={To}, SID={CallSid}")

    settings = get_settings()
    voice = get_voice_name("female_us")

    # Get business configuration based on the number that was called
    business = get_business_by_phone(To)

    if not business:
        # Unknown number - fallback to generic response
        logging.error(f"No business configured for {To}")
        response = VoiceResponse()
        response.say(
            "Thank you for calling. This number is not currently configured. Please try again later.",
            voice=voice
        )
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    logging.info(f"Matched business: {business['name']}")

    # Create call record
    call = Call(
        id=str(uuid.uuid4()),
        restaurant_id=business['name'],  # Using restaurant_id for business name
        twilio_sid=CallSid,
        caller_number=From,
        status=CallStatus.IN_PROGRESS
    )
    business_calls[CallSid] = call

    # Get engine and create conversation state
    engine = get_engine_for_business(To)
    state = engine.create_initial_state(call.id)
    business_states[CallSid] = state

    # Add greeting to transcript
    call.transcript.append(TranscriptEntry(
        role="ai",
        content=business['greeting']
    ))

    # Build TwiML response
    response = VoiceResponse()
    response.say(business['greeting'], voice=voice)

    # Gather speech input
    gather = Gather(
        input="speech",
        action=f"{settings.base_url}/twilio/business-gather?to={To}",
        method="POST",
        speech_timeout="auto",
        speech_model="phone_call",
        language="en-US"
    )
    response.append(gather)

    # If no response, prompt again
    response.say("Are you still there? How can I help you today?", voice=voice)
    response.redirect(f"{settings.base_url}/twilio/business-voice")

    return Response(content=str(response), media_type="application/xml")


@router.post("/business-gather")
async def handle_business_speech(
    request: Request,
    to: str = None  # Query param to know which business
):
    """Handle speech input during business call."""
    import logging
    logging.basicConfig(level=logging.INFO)

    settings = get_settings()
    voice = get_voice_name("female_us")

    try:
        form = await request.form()
        CallSid = form.get("CallSid")
        SpeechResult = form.get("SpeechResult")
        To = form.get("To") or to  # Get from form or query param

        logging.info(f"BUSINESS GATHER: SID={CallSid}, Speech={SpeechResult}, To={To}")

        if not SpeechResult:
            response = VoiceResponse()
            response.say("I didn't catch that. Could you please repeat?", voice=voice)
            gather = Gather(
                input="speech",
                action=f"{settings.base_url}/twilio/business-gather?to={To}",
                method="POST",
                speech_timeout="auto"
            )
            response.append(gather)
            return Response(content=str(response), media_type="application/xml")

        # Get call and state
        call = business_calls.get(CallSid)
        state = business_states.get(CallSid)

        if not call or not state:
            logging.error(f"No call/state found for {CallSid}")
            response = VoiceResponse()
            response.say("I'm sorry, there was an error. Please call back.", voice=voice)
            response.hangup()
            return Response(content=str(response), media_type="application/xml")

        # Log customer input
        call.transcript.append(TranscriptEntry(
            role="customer",
            content=SpeechResult
        ))

        # Get the right engine for this business
        engine = get_engine_for_business(To)

        # Process through voice engine
        ai_response, state = await engine.process_turn(state, SpeechResult)
        business_states[CallSid] = state

        # Log AI response
        call.transcript.append(TranscriptEntry(
            role="ai",
            content=ai_response
        ))

        # Build response
        response = VoiceResponse()

        if state.transfer_requested:
            # Transfer to business owner
            business = get_business_by_phone(To)
            owner_phone = business.get("owner_phone")
            response.say(ai_response, voice=voice)
            response.say("Please hold while I connect you.", voice=voice)
            if owner_phone:
                # Dial the owner's phone number
                response.dial(owner_phone, caller_id=business.get("phone"))
            else:
                response.say("I apologize, but I'm unable to connect you right now. Please try calling back.", voice=voice)
                response.hangup()
            call.status = CallStatus.TRANSFERRED

        elif state.awaiting_confirmation:
            # Info collected
            response.say(ai_response, voice=voice)
            response.say("Thank you for calling! Have a great day!", voice=voice)
            response.hangup()
            call.status = CallStatus.COMPLETED

        else:
            # Continue conversation
            response.say(ai_response, voice=voice)
            gather = Gather(
                input="speech",
                action=f"{settings.base_url}/twilio/business-gather?to={To}",
                method="POST",
                speech_timeout="auto",
                speech_model="phone_call"
            )
            response.append(gather)

            response.say("Are you still there?", voice=voice)
            response.redirect(f"{settings.base_url}/twilio/business-gather?to={To}")

        return Response(content=str(response), media_type="application/xml")

    except Exception as e:
        logging.error(f"BUSINESS GATHER ERROR: {e}")
        import traceback
        logging.error(traceback.format_exc())
        response = VoiceResponse()
        response.say("I apologize, we're experiencing technical difficulties. Please call back.", voice=voice)
        response.hangup()
        return Response(content=str(response), media_type="application/xml")


@router.get("/businesses")
async def list_configured_businesses():
    """List all businesses with voice AI configured."""
    from .business_voice_engine import list_configured_businesses
    return list_configured_businesses()


@router.post("/call-status")
async def handle_call_status_callback(request: Request):
    """Handle Twilio call status callbacks (e.g., call completed).

    Integrates with lead intake system to track voice AI calls.
    """
    import logging
    from urllib.parse import parse_qs

    try:
        # Parse form data from Twilio
        body = await request.body()
        params = parse_qs(body.decode())

        # Extract Twilio parameters
        call_sid = params.get('CallSid', [''])[0]
        call_status = params.get('CallStatus', [''])[0]
        from_number = params.get('From', [''])[0]
        to_number = params.get('To', [''])[0]
        call_duration = params.get('CallDuration', ['0'])[0]
        account_sid = params.get('AccountSid', [''])[0]

        logging.info(f"Call status webhook: {call_sid} - {call_status}")

        # Only process completed calls
        if call_status.lower() == 'completed':
            # Try to import voice_ai_tracker
            try:
                import sys
                from pathlib import Path

                # Add lead-scraper to path
                lead_scraper_path = Path(__file__).parent.parent.parent.parent / 'lead-scraper'
                if lead_scraper_path.exists() and str(lead_scraper_path) not in sys.path:
                    sys.path.insert(0, str(lead_scraper_path))

                from src.voice_ai_tracker import VoiceAITracker

                # Get call data from active_calls if available
                call = active_calls.get(call_sid)

                # Determine business and outcome
                business_id = 'marceau-solutions'  # Default
                outcome = 'info_only'  # Default

                if call:
                    # Try to determine outcome from call state
                    state = conversation_states.get(call_sid)
                    if state and hasattr(state, 'awaiting_confirmation') and state.awaiting_confirmation:
                        outcome = 'appointment_booked'
                    elif state and hasattr(state, 'collected_info'):
                        outcome = 'callback_requested'

                # Track the call
                tracker = VoiceAITracker()
                result = tracker.handle_call_completed(
                    call_sid=call_sid,
                    caller_phone=from_number,
                    business_id=business_id,
                    outcome=outcome,
                    call_duration=int(call_duration),
                    account_sid=account_sid,
                    additional_data={
                        'to_number': to_number,
                        'call_status': call_status
                    }
                )

                logging.info(f"Voice AI call tracked: {result}")

            except ImportError as e:
                logging.warning(f"Could not import voice_ai_tracker: {e}")
            except Exception as e:
                logging.error(f"Error tracking voice AI call: {e}")

        return {"status": "ok", "call_sid": call_sid}

    except Exception as e:
        logging.error(f"Call status callback error: {e}")
        return {"status": "error", "message": str(e)}
