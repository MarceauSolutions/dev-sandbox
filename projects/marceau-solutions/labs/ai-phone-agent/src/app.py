#!/usr/bin/env python3.11
"""
AI Phone Agent - Twilio-First Inbound Call Handler
All calls route through Twilio/AI receptionist first.
William's cell only rings when the AI decides to transfer.

Architecture:
  Caller → (855) or forwarded (239) → AI Receptionist (ElevenLabs voice clone)
  → If transfer needed → Try William's cell (20s timeout)
  → If cell fails → Voicemail + Telegram alert with full context

Deployment: ai-phone.marceausolutions.com
Port: 8795
"""

from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from twilio.rest import Client
import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('/home/clawdbot/dev-sandbox/.env')

app = Flask(__name__)
CORS(app)

# =============================================================================
# Configuration
# =============================================================================

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
WEBHOOK_URL = os.getenv('LEAD_WEBHOOK_URL', 'http://localhost:5678/webhook/ai-phone-lead')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = '5692454753'

APP_BASE_URL = os.getenv('APP_BASE_URL', 'https://ai-phone.marceausolutions.com')

# Load agent config
CONFIG_PATH = Path(__file__).parent.parent / 'config' / 'agent_config.json'
with open(CONFIG_PATH) as f:
    AGENT_CONFIG = json.load(f)

ROUTING = AGENT_CONFIG.get('routing', {})
WILLIAM_CELL = ROUTING.get('william_cell', '+12393985676')
TRANSFER_ENABLED = ROUTING.get('transfer_enabled', True)
TRANSFER_TIMEOUT = ROUTING.get('transfer_timeout_seconds', 20)
PERSONAL_NUMBER = ROUTING.get('forwarded_from_personal', '+12393985676')
TWILIO_NUMBER = AGENT_CONFIG.get('twilio_config', {}).get('phone_number', '+18552399364')

# In-memory state
active_calls = {}
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# =============================================================================
# Cell Reliability Tracker
# =============================================================================

CELL_TRACKER_PATH = Path(__file__).parent.parent / 'data' / 'cell_reliability.json'
CELL_TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_cell_tracker():
    if CELL_TRACKER_PATH.exists():
        with open(CELL_TRACKER_PATH) as f:
            return json.load(f)
    return {
        'attempts': [],
        'ai_only_mode': False,
        'ai_only_set_at': None,
        'total_transfers': 0,
        'total_answered': 0
    }


def save_cell_tracker(tracker):
    with open(CELL_TRACKER_PATH, 'w') as f:
        json.dump(tracker, f, indent=2)


def record_transfer_attempt(answered, call_sid, caller):
    tracker = load_cell_tracker()
    tracker['attempts'].append({
        'timestamp': datetime.now().isoformat(),
        'call_sid': call_sid,
        'caller': caller,
        'answered': answered
    })
    tracker['total_transfers'] += 1
    if answered:
        tracker['total_answered'] += 1
    # Keep only last 50 attempts
    tracker['attempts'] = tracker['attempts'][-50:]
    save_cell_tracker(tracker)

    # Check if we should auto-enable AI-only mode
    window = ROUTING.get('reliability_window_attempts', 10)
    threshold = ROUTING.get('reliability_threshold', 0.5)
    recent = tracker['attempts'][-window:]
    if len(recent) >= window:
        success_rate = sum(1 for a in recent if a['answered']) / len(recent)
        if success_rate < threshold and not tracker.get('ai_only_mode'):
            tracker['ai_only_mode'] = True
            tracker['ai_only_set_at'] = datetime.now().isoformat()
            save_cell_tracker(tracker)
            send_telegram_alert(
                f"<b>Auto AI-Only Mode Activated</b>\n"
                f"Your cell answered only {success_rate:.0%} of the last {window} transfer attempts.\n"
                f"All calls will be handled by AI until you re-enable transfers.\n\n"
                f"To re-enable: POST {APP_BASE_URL}/admin/routing with "
                f'{{"ai_only_mode": false}}'
            )


def is_ai_only_mode():
    tracker = load_cell_tracker()
    # Config override takes precedence
    if ROUTING.get('ai_only_mode', False):
        return True
    return tracker.get('ai_only_mode', False)


def get_cell_reliability():
    tracker = load_cell_tracker()
    window = ROUTING.get('reliability_window_attempts', 10)
    recent = tracker['attempts'][-window:]
    if not recent:
        return {'rate': 1.0, 'attempts': 0, 'window': window, 'ai_only': is_ai_only_mode()}
    success_rate = sum(1 for a in recent if a['answered']) / len(recent)
    return {
        'rate': round(success_rate, 2),
        'attempts': len(recent),
        'window': window,
        'total_transfers': tracker.get('total_transfers', 0),
        'total_answered': tracker.get('total_answered', 0),
        'ai_only': is_ai_only_mode(),
        'last_attempt': recent[-1] if recent else None
    }


# =============================================================================
# Telegram Alerts
# =============================================================================

def send_telegram_alert(message):
    """Send instant Telegram alert to William."""
    if not TELEGRAM_BOT_TOKEN:
        print("No TELEGRAM_BOT_TOKEN configured, skipping alert")
        return
    try:
        requests.post(
            f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
            json={'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'},
            timeout=5
        )
    except Exception as e:
        print(f"Telegram alert failed: {e}")


# =============================================================================
# Helper: Detect call origin
# =============================================================================

def detect_call_origin(req):
    """Determine if call came through (855) directly or was forwarded from (239)."""
    forwarded_from = req.values.get('ForwardedFrom', '')
    to_number = req.values.get('To', '')
    caller = req.values.get('From', 'Unknown')

    # Check if this is a forwarded call from William's personal number
    is_forwarded = (
        forwarded_from == PERSONAL_NUMBER or
        forwarded_from == f'+1{PERSONAL_NUMBER.lstrip("+1")}' or
        'ForwardedFrom' in req.values
    )

    # Check if caller is a known contact
    known = ROUTING.get('known_contacts', {}).get(caller, None)

    return {
        'caller': caller,
        'to_number': to_number,
        'forwarded_from': forwarded_from,
        'is_forwarded_from_personal': is_forwarded,
        'known_contact': known,
        'auto_transfer': known.get('auto_transfer', False) if known else False
    }


# =============================================================================
# Routes: Health & Admin
# =============================================================================

@app.route('/health', methods=['GET'])
def health():
    reliability = get_cell_reliability()
    return jsonify({
        'status': 'ok',
        'service': 'AI Phone Agent (Twilio-First)',
        'timestamp': datetime.now().isoformat(),
        'agent_name': AGENT_CONFIG.get('name'),
        'phone': TWILIO_NUMBER,
        'personal_number': PERSONAL_NUMBER,
        'ai_only_mode': is_ai_only_mode(),
        'transfer_enabled': TRANSFER_ENABLED,
        'cell_reliability': reliability
    })


@app.route('/admin/routing', methods=['GET', 'POST'])
def admin_routing():
    """View and toggle routing configuration."""
    tracker = load_cell_tracker()

    if request.method == 'POST':
        data = request.json or {}
        if 'ai_only_mode' in data:
            tracker['ai_only_mode'] = bool(data['ai_only_mode'])
            if not tracker['ai_only_mode']:
                tracker['ai_only_set_at'] = None
            else:
                tracker['ai_only_set_at'] = datetime.now().isoformat()
            save_cell_tracker(tracker)
            mode = "AI-only" if tracker['ai_only_mode'] else "Transfer-enabled"
            send_telegram_alert(f"<b>Routing Mode Changed</b>\nNow: {mode}")
            return jsonify({'status': 'updated', 'ai_only_mode': tracker['ai_only_mode']})

        return jsonify({'error': 'No recognized fields to update'}), 400

    return jsonify({
        'ai_only_mode': is_ai_only_mode(),
        'transfer_enabled': TRANSFER_ENABLED,
        'transfer_timeout': TRANSFER_TIMEOUT,
        'william_cell': WILLIAM_CELL,
        'personal_number': PERSONAL_NUMBER,
        'twilio_number': TWILIO_NUMBER,
        'cell_reliability': get_cell_reliability(),
        'recent_attempts': tracker.get('attempts', [])[-10:]
    })


@app.route('/admin/test-cell', methods=['POST'])
def admin_test_cell():
    """Trigger a test call to William's cell to check if it's working."""
    try:
        call = twilio_client.calls.create(
            twiml='<Response><Say voice="Polly.Joanna">This is a test call from your AI receptionist system. '
                  'If you can hear this, your cell phone is working. Goodbye.</Say><Hangup/></Response>',
            to=WILLIAM_CELL,
            from_=TWILIO_NUMBER,
            status_callback=f'{APP_BASE_URL}/william-cell-status',
            status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
            status_callback_method='POST',
            timeout=TRANSFER_TIMEOUT
        )
        return jsonify({'status': 'test_call_initiated', 'call_sid': call.sid})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Routes: Incoming Call Handler (Twilio-First)
# =============================================================================

@app.route('/incoming-call', methods=['POST'])
def incoming_call():
    """
    Twilio-first incoming call handler.
    ALL calls hit the AI receptionist first, regardless of which number was dialed.
    """
    call_sid = request.values.get('CallSid')
    origin = detect_call_origin(request)
    caller = origin['caller']

    print(f"[{datetime.now()}] Incoming call from {caller} (SID: {call_sid})")
    if origin['is_forwarded_from_personal']:
        print(f"  → Forwarded from personal number {origin['forwarded_from']}")

    # Telegram alert
    source_label = "forwarded from (239)" if origin['is_forwarded_from_personal'] else "direct to (855)"
    send_telegram_alert(
        f"<b>Incoming Call</b>\n"
        f"From: {caller}\n"
        f"Route: {source_label}\n"
        f"Time: {datetime.now().strftime('%I:%M %p')}\n"
        f"AI receptionist is handling it."
    )

    # Store call data
    active_calls[call_sid] = {
        'caller': caller,
        'started_at': datetime.now().isoformat(),
        'status': 'ai_handling',
        'origin': origin,
        'transcript': [],
        'collected_data': {}
    }

    # Known contact with auto-transfer? Skip AI, go straight to transfer.
    if origin['auto_transfer'] and not is_ai_only_mode():
        print(f"  → Known contact {origin['known_contact']['name']}, auto-transferring")
        active_calls[call_sid]['status'] = 'auto_transfer'
        return _initiate_transfer_twiml(call_sid)

    # Everyone else gets the AI receptionist
    response = VoiceResponse()

    try:
        agent_id = os.getenv('ELEVENLABS_AGENT_ID', '')
        if not agent_id:
            raise Exception("No ELEVENLABS_AGENT_ID configured")

        el_response = requests.get(
            f'https://api.elevenlabs.io/v1/convai/conversation/get_signed_url?agent_id={agent_id}',
            headers={'xi-api-key': ELEVENLABS_API_KEY},
            timeout=5
        )

        if el_response.status_code == 200:
            signed_url = el_response.json().get('signed_url')
            connect = Connect()
            stream = Stream(url=signed_url)
            # Pass CallSid as custom parameter so ElevenLabs tool callbacks can reference it
            stream.parameter(name='call_sid', value=call_sid)
            stream.parameter(name='caller', value=caller)
            stream.parameter(name='is_forwarded', value=str(origin['is_forwarded_from_personal']))
            connect.append(stream)
            response.append(connect)
        else:
            raise Exception(f"ElevenLabs returned {el_response.status_code}")

    except Exception as e:
        print(f"ElevenLabs unavailable ({e}), using fallback TTS")
        # Fallback: Twilio TTS qualifying flow
        if origin['is_forwarded_from_personal']:
            response.say(
                "Hi, thanks for calling! William is currently unavailable. "
                "I'm his AI assistant. Can I take a message or help you with something?",
                voice='Polly.Joanna'
            )
        else:
            response.say(
                AGENT_CONFIG.get('first_message'),
                voice='Polly.Joanna'
            )
        response.gather(
            input='speech',
            action='/gather-response',
            method='POST',
            timeout=5,
            speechTimeout='auto',
            language='en-US'
        )
        response.say("I didn't catch that. Let me transfer you to voicemail.")
        response.redirect('/voicemail')

    return Response(str(response), mimetype='text/xml')


# =============================================================================
# Routes: ElevenLabs Tool Callback — Transfer Request
# =============================================================================

@app.route('/elevenlabs-tool/transfer', methods=['POST'])
def elevenlabs_transfer_tool():
    """
    Called by ElevenLabs Conversational AI when the agent decides to transfer.
    The AI agent has a server-side tool 'transfer_to_william' that hits this endpoint.
    """
    data = request.json or {}
    call_sid = data.get('call_sid', '')
    caller_name = data.get('caller_name', 'Unknown')
    reason = data.get('reason', 'Caller requested transfer')
    urgency = data.get('urgency', 'medium')

    print(f"[{datetime.now()}] ElevenLabs transfer request: {caller_name} ({reason})")

    # Store transfer context
    if call_sid in active_calls:
        active_calls[call_sid]['transfer_reason'] = reason
        active_calls[call_sid]['caller_name'] = caller_name
        active_calls[call_sid]['urgency'] = urgency
        active_calls[call_sid]['status'] = 'transferring'

    if is_ai_only_mode():
        # Don't attempt transfer, tell the AI to take a message instead
        print("  → AI-only mode active, rejecting transfer")
        return jsonify({
            'status': 'rejected',
            'reason': 'ai_only_mode',
            'message': "William's phone is currently unavailable. Please take a detailed message "
                       "including their name, phone number, and what they need. "
                       "Tell them William will call back within 2 hours."
        })

    # Redirect the Twilio call to the transfer flow
    try:
        twilio_client.calls(call_sid).update(
            url=f'{APP_BASE_URL}/initiate-transfer',
            method='POST'
        )
        return jsonify({
            'status': 'transferring',
            'message': 'Tell the caller: "Let me connect you with William now. One moment please."'
        })
    except Exception as e:
        print(f"Failed to redirect call for transfer: {e}")
        return jsonify({
            'status': 'error',
            'reason': str(e),
            'message': "I wasn't able to transfer right now. Please take a message and "
                       "William will call them back shortly."
        })


# =============================================================================
# Routes: Transfer Flow
# =============================================================================

def _initiate_transfer_twiml(call_sid):
    """Generate TwiML to bridge caller to William's cell."""
    response = VoiceResponse()
    response.say(
        "Let me connect you with William now. One moment please.",
        voice='Polly.Joanna'
    )
    response.play(url='http://com.twilio.sounds.music.s3.amazonaws.com/MARKOVICHAMP-B7.mp3')

    dial = response.dial(
        action=f'{APP_BASE_URL}/transfer-result',
        method='POST',
        timeout=TRANSFER_TIMEOUT,
        caller_id=TWILIO_NUMBER
    )
    dial.number(
        WILLIAM_CELL,
        status_callback=f'{APP_BASE_URL}/william-cell-status',
        status_callback_event='initiated ringing answered completed',
        status_callback_method='POST'
    )

    return Response(str(response), mimetype='text/xml')


@app.route('/initiate-transfer', methods=['POST'])
def initiate_transfer():
    """TwiML endpoint that dials William's cell with timeout and fallback."""
    call_sid = request.values.get('CallSid')
    print(f"[{datetime.now()}] Initiating transfer for call {call_sid}")

    response = VoiceResponse()
    response.say(
        "Connecting you with William now. One moment please.",
        voice='Polly.Joanna'
    )

    dial = response.dial(
        action='/transfer-result',
        method='POST',
        timeout=TRANSFER_TIMEOUT,
        caller_id=TWILIO_NUMBER
    )
    dial.number(
        WILLIAM_CELL,
        status_callback=f'{APP_BASE_URL}/william-cell-status',
        status_callback_event='initiated ringing answered completed',
        status_callback_method='POST'
    )

    return Response(str(response), mimetype='text/xml')


@app.route('/transfer-result', methods=['POST'])
def transfer_result():
    """Called after <Dial> to William's cell completes — handle answered vs failed."""
    call_sid = request.values.get('CallSid')
    dial_status = request.values.get('DialCallStatus', 'unknown')
    dial_duration = request.values.get('DialCallDuration', '0')
    caller = request.values.get('From', 'Unknown')

    print(f"[{datetime.now()}] Transfer result for {call_sid}: {dial_status} ({dial_duration}s)")

    call_data = active_calls.get(call_sid, {})

    if dial_status == 'completed':
        # William answered — success
        record_transfer_attempt(True, call_sid, caller)
        active_calls.pop(call_sid, None)

        send_telegram_alert(
            f"<b>Transfer Successful</b>\n"
            f"Caller: {caller}\n"
            f"Duration: {dial_duration}s\n"
            f"William answered the call."
        )

        response = VoiceResponse()
        response.hangup()
        return Response(str(response), mimetype='text/xml')

    # William didn't answer — fallback
    record_transfer_attempt(False, call_sid, caller)
    print(f"  → Transfer failed ({dial_status}), falling back to voicemail")

    # Build context for the alert
    caller_name = call_data.get('caller_name', '')
    reason = call_data.get('transfer_reason', '')
    urgency = call_data.get('urgency', 'medium')
    collected = call_data.get('collected_data', {})

    alert = (
        f"<b>Missed Transfer — {dial_status.upper()}</b>\n"
        f"Caller: {caller}"
    )
    if caller_name:
        alert += f" ({caller_name})"
    alert += f"\nReason: {reason or 'Caller requested'}"
    alert += f"\nUrgency: {urgency}"
    if collected.get('business_type'):
        alert += f"\nBusiness: {collected['business_type']}"
    if collected.get('pain_points'):
        alert += f"\nPain Point: {collected['pain_points']}"
    alert += f"\nTime: {datetime.now().strftime('%I:%M %p')}"
    alert += "\n\n<b>Caller is being sent to voicemail now.</b>"
    send_telegram_alert(alert)

    # Send caller to voicemail
    response = VoiceResponse()
    response.say(
        "I wasn't able to reach William right now, but don't worry — "
        "let me take a message and he'll call you back as soon as possible.",
        voice='Polly.Joanna'
    )
    response.record(
        action='/voicemail-complete',
        method='POST',
        maxLength=180,
        transcribe=True,
        transcribeCallback='/voicemail-transcription'
    )
    response.say("I didn't hear a message. Goodbye!", voice='Polly.Joanna')
    response.hangup()

    return Response(str(response), mimetype='text/xml')


@app.route('/william-cell-status', methods=['POST'])
def william_cell_status():
    """Twilio status callback for the dial-to-William leg. Tracks reliability."""
    call_sid = request.values.get('CallSid')
    status = request.values.get('CallStatus')
    print(f"[{datetime.now()}] William cell status: {status} (parent SID: {call_sid})")
    return '', 200


# =============================================================================
# Routes: Fallback Gather Flow (when ElevenLabs is down)
# =============================================================================

@app.route('/gather-response', methods=['POST'])
def gather_response():
    """Handle speech input from caller (fallback mode when ElevenLabs is unavailable)."""
    call_sid = request.values.get('CallSid')
    speech_result = request.values.get('SpeechResult', '')
    confidence = request.values.get('Confidence', 0)

    print(f"Caller said: {speech_result} (confidence: {confidence})")

    if call_sid in active_calls:
        active_calls[call_sid]['transcript'].append({
            'speaker': 'caller',
            'text': speech_result,
            'timestamp': datetime.now().isoformat()
        })

    response = VoiceResponse()

    call_data = active_calls.get(call_sid, {})
    collected = call_data.get('collected_data', {})

    # Check if caller is asking to speak to William
    transfer_phrases = ['speak to william', 'talk to william', 'is william there',
                        'transfer me', 'speak to someone', 'talk to a person',
                        'returning his call', 'returning a call', 'he called me']
    if any(phrase in speech_result.lower() for phrase in transfer_phrases):
        if not is_ai_only_mode():
            active_calls[call_sid]['transfer_reason'] = f'Caller said: {speech_result}'
            return _initiate_transfer_twiml(call_sid)
        else:
            response.say(
                "William is currently unavailable. Let me take a message and "
                "he'll call you back within 2 hours.",
                voice='Polly.Joanna'
            )
            response.record(
                action='/voicemail-complete',
                method='POST',
                maxLength=180,
                transcribe=True,
                transcribeCallback='/voicemail-transcription'
            )
            return Response(str(response), mimetype='text/xml')

    questions = AGENT_CONFIG['conversation_flow']['qualifying_questions']
    current_q_idx = len(collected)

    if current_q_idx < len(questions):
        current_q = questions[current_q_idx - 1] if current_q_idx > 0 else None
        if current_q:
            collected[current_q['id']] = speech_result
            active_calls[call_sid]['collected_data'] = collected

        if current_q_idx < len(questions):
            next_q = questions[current_q_idx]
            response.say(next_q['question'], voice='Polly.Joanna')
            response.gather(
                input='speech',
                action='/gather-response',
                method='POST',
                timeout=5,
                speechTimeout='auto'
            )
        else:
            response.redirect('/call-complete')
    else:
        response.redirect('/call-complete')

    return Response(str(response), mimetype='text/xml')


# =============================================================================
# Routes: Call Complete & Voicemail
# =============================================================================

@app.route('/call-complete', methods=['POST'])
def call_complete():
    """Wrap up call and send lead data."""
    call_sid = request.values.get('CallSid')
    caller = request.values.get('From', 'Unknown')

    call_data = active_calls.get(call_sid, {})

    response = VoiceResponse()
    response.say(
        AGENT_CONFIG['conversation_flow']['closing']['qualified'],
        voice='Polly.Joanna'
    )
    response.say(
        "Thanks for calling Marceau Solutions. Have a great day!",
        voice='Polly.Joanna'
    )
    response.hangup()

    # Send lead data to webhook
    lead_data = {
        'source': 'ai-phone-agent',
        'phone': caller,
        'call_sid': call_sid,
        'timestamp': datetime.now().isoformat(),
        'collected_data': call_data.get('collected_data', {}),
        'transcript': call_data.get('transcript', []),
        'origin': call_data.get('origin', {}),
        'status': 'warm_lead'
    }

    try:
        requests.post(WEBHOOK_URL, json=lead_data, timeout=10)
        print(f"Lead data sent to webhook: {lead_data}")
    except Exception as e:
        print(f"Failed to send lead data: {e}")

    # Telegram alert
    collected = call_data.get('collected_data', {})
    alert = f"<b>Call Complete — Warm Lead</b>\nPhone: {caller}\n"
    if collected.get('business_type'):
        alert += f"Business: {collected['business_type']}\n"
    if collected.get('pain_points'):
        alert += f"Pain Point: {collected['pain_points']}\n"
    if collected.get('timeline'):
        alert += f"Timeline: {collected['timeline']}\n"
    alert += f"Time: {datetime.now().strftime('%I:%M %p')}"
    send_telegram_alert(alert)

    active_calls.pop(call_sid, None)
    return Response(str(response), mimetype='text/xml')


@app.route('/voicemail', methods=['POST'])
def voicemail():
    """Fallback voicemail."""
    response = VoiceResponse()
    response.say(
        "Sorry I couldn't help you directly. Please leave a message after the beep "
        "with your name, number, and what you're looking for. "
        "William will call you back within 24 hours.",
        voice='Polly.Joanna'
    )
    response.record(
        action='/voicemail-complete',
        method='POST',
        maxLength=180,
        transcribe=True,
        transcribeCallback='/voicemail-transcription'
    )
    return Response(str(response), mimetype='text/xml')


@app.route('/voicemail-complete', methods=['POST'])
def voicemail_complete():
    """Handle voicemail completion."""
    recording_url = request.values.get('RecordingUrl')
    caller = request.values.get('From', 'Unknown')
    call_sid = request.values.get('CallSid')

    call_data = active_calls.get(call_sid, {})

    lead_data = {
        'source': 'voicemail',
        'phone': caller,
        'recording_url': recording_url,
        'timestamp': datetime.now().isoformat(),
        'collected_data': call_data.get('collected_data', {}),
        'origin': call_data.get('origin', {}),
        'status': 'voicemail_lead'
    }

    try:
        requests.post(WEBHOOK_URL, json=lead_data, timeout=10)
    except Exception as e:
        print(f"Failed to send voicemail notification: {e}")

    send_telegram_alert(
        f"<b>New Voicemail</b>\n"
        f"From: {caller}\n"
        f"Recording: {recording_url}\n"
        f"Time: {datetime.now().strftime('%I:%M %p')}"
    )

    active_calls.pop(call_sid, None)

    response = VoiceResponse()
    response.say("Thanks! William will get back to you soon.", voice='Polly.Joanna')
    response.hangup()
    return Response(str(response), mimetype='text/xml')


@app.route('/voicemail-transcription', methods=['POST'])
def voicemail_transcription():
    """Handle voicemail transcription callback."""
    transcription = request.values.get('TranscriptionText', '')
    recording_sid = request.values.get('RecordingSid')
    caller = request.values.get('From', 'Unknown')

    print(f"Voicemail transcription ({recording_sid}): {transcription}")

    if transcription:
        send_telegram_alert(
            f"<b>Voicemail Transcription</b>\n"
            f"From: {caller}\n"
            f"Message: {transcription}"
        )

    return '', 200


@app.route('/call-status', methods=['POST'])
def call_status():
    """Twilio call status webhook."""
    call_sid = request.values.get('CallSid')
    status = request.values.get('CallStatus')
    duration = request.values.get('CallDuration', 0)

    print(f"Call {call_sid} status: {status} (duration: {duration}s)")
    return '', 200


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == '__main__':
    print(f"AI Phone Agent (Twilio-First) starting on port 8795")
    print(f"  Twilio number: {TWILIO_NUMBER}")
    print(f"  Personal number: {PERSONAL_NUMBER}")
    print(f"  William cell: {WILLIAM_CELL}")
    print(f"  Transfer enabled: {TRANSFER_ENABLED}")
    print(f"  AI-only mode: {is_ai_only_mode()}")
    print(f"  Transfer timeout: {TRANSFER_TIMEOUT}s")
    app.run(host='0.0.0.0', port=8795, debug=False)
