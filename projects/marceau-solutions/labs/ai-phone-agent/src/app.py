#!/usr/bin/env python3.11
"""
AI Phone Agent - Inbound Call Handler
Connects Twilio inbound calls to ElevenLabs Conversational AI

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
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('/home/clawdbot/dev-sandbox/.env')

app = Flask(__name__)
CORS(app)

# Config
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
WEBHOOK_URL = os.getenv('LEAD_WEBHOOK_URL', 'http://localhost:5678/webhook/ai-phone-lead')
EMAIL_TO = 'wmarceau@marceausolutions.com'

# Load agent config
CONFIG_PATH = Path(__file__).parent.parent / 'config' / 'agent_config.json'
with open(CONFIG_PATH) as f:
    AGENT_CONFIG = json.load(f)

# In-memory call storage (use Redis in production)
active_calls = {}

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'AI Phone Agent',
        'timestamp': datetime.now().isoformat(),
        'agent_name': AGENT_CONFIG.get('name'),
        'phone': AGENT_CONFIG.get('twilio_config', {}).get('phone_number')
    })


@app.route('/incoming-call', methods=['POST'])
def incoming_call():
    """Handle incoming Twilio call - connect to ElevenLabs Conversational AI"""
    caller = request.values.get('From', 'Unknown')
    call_sid = request.values.get('CallSid')
    
    print(f"[{datetime.now()}] Incoming call from {caller} (SID: {call_sid})")
    
    # Store call data
    active_calls[call_sid] = {
        'caller': caller,
        'started_at': datetime.now().isoformat(),
        'status': 'connected',
        'transcript': [],
        'collected_data': {}
    }
    
    response = VoiceResponse()
    
    # Check if ElevenLabs Conversational AI is available
    # For now, use Twilio's built-in capabilities with fallback
    try:
        # Try to get ElevenLabs signed URL for streaming
        el_response = requests.post(
            'https://api.elevenlabs.io/v1/convai/conversation/get_signed_url',
            headers={
                'xi-api-key': ELEVENLABS_API_KEY,
                'Content-Type': 'application/json'
            },
            json={'agent_id': os.getenv('ELEVENLABS_AGENT_ID', '')},
            timeout=5
        )
        
        if el_response.status_code == 200:
            signed_url = el_response.json().get('signed_url')
            # Connect to ElevenLabs via WebSocket stream
            connect = Connect()
            stream = Stream(url=signed_url)
            connect.append(stream)
            response.append(connect)
        else:
            raise Exception("ElevenLabs not available")
            
    except Exception as e:
        print(f"ElevenLabs unavailable ({e}), using fallback")
        # Fallback: Use Twilio's gather with TTS
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


@app.route('/gather-response', methods=['POST'])
def gather_response():
    """Handle speech input from caller (fallback mode)"""
    call_sid = request.values.get('CallSid')
    speech_result = request.values.get('SpeechResult', '')
    confidence = request.values.get('Confidence', 0)
    
    print(f"Caller said: {speech_result} (confidence: {confidence})")
    
    # Store transcript
    if call_sid in active_calls:
        active_calls[call_sid]['transcript'].append({
            'speaker': 'caller',
            'text': speech_result,
            'timestamp': datetime.now().isoformat()
        })
    
    response = VoiceResponse()
    
    # Simple qualifying flow in fallback mode
    call_data = active_calls.get(call_sid, {})
    collected = call_data.get('collected_data', {})
    
    questions = AGENT_CONFIG['conversation_flow']['qualifying_questions']
    current_q_idx = len(collected)
    
    if current_q_idx < len(questions):
        # Store current response
        current_q = questions[current_q_idx - 1] if current_q_idx > 0 else None
        if current_q:
            collected[current_q['id']] = speech_result
            active_calls[call_sid]['collected_data'] = collected
        
        # Ask next question
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
            # All questions answered
            response.redirect('/call-complete')
    else:
        response.redirect('/call-complete')
    
    return Response(str(response), mimetype='text/xml')


@app.route('/call-complete', methods=['POST'])
def call_complete():
    """Wrap up call and send lead data"""
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
        'status': 'warm_lead'
    }
    
    try:
        requests.post(WEBHOOK_URL, json=lead_data, timeout=10)
        print(f"Lead data sent to webhook: {lead_data}")
    except Exception as e:
        print(f"Failed to send lead data: {e}")
    
    # Clean up
    if call_sid in active_calls:
        del active_calls[call_sid]
    
    return Response(str(response), mimetype='text/xml')


@app.route('/voicemail', methods=['POST'])
def voicemail():
    """Fallback voicemail"""
    response = VoiceResponse()
    response.say(
        "Sorry I couldn't help you directly. Please leave a message after the beep with your name, number, and what you're looking for. William will call you back within 24 hours.",
        voice='Polly.Joanna'
    )
    response.record(
        action='/voicemail-complete',
        method='POST',
        maxLength=120,
        transcribe=True,
        transcribeCallback='/voicemail-transcription'
    )
    return Response(str(response), mimetype='text/xml')


@app.route('/voicemail-complete', methods=['POST'])
def voicemail_complete():
    """Handle voicemail completion"""
    recording_url = request.values.get('RecordingUrl')
    caller = request.values.get('From', 'Unknown')
    
    # Send voicemail notification
    lead_data = {
        'source': 'voicemail',
        'phone': caller,
        'recording_url': recording_url,
        'timestamp': datetime.now().isoformat(),
        'status': 'voicemail_lead'
    }
    
    try:
        requests.post(WEBHOOK_URL, json=lead_data, timeout=10)
    except Exception as e:
        print(f"Failed to send voicemail notification: {e}")
    
    response = VoiceResponse()
    response.say("Thanks! We'll get back to you soon.", voice='Polly.Joanna')
    response.hangup()
    return Response(str(response), mimetype='text/xml')


@app.route('/voicemail-transcription', methods=['POST'])
def voicemail_transcription():
    """Handle voicemail transcription callback"""
    transcription = request.values.get('TranscriptionText', '')
    recording_sid = request.values.get('RecordingSid')
    
    print(f"Voicemail transcription ({recording_sid}): {transcription}")
    
    # Could update the lead with transcription here
    return '', 200


@app.route('/call-status', methods=['POST'])
def call_status():
    """Twilio call status webhook"""
    call_sid = request.values.get('CallSid')
    status = request.values.get('CallStatus')
    duration = request.values.get('CallDuration', 0)
    
    print(f"Call {call_sid} status: {status} (duration: {duration}s)")
    return '', 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8795, debug=False)
