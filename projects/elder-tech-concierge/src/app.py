#!/usr/bin/env python3
"""
app.py - Elder Tech Concierge Web Application

WHAT: Flask web server with endpoints for tablet interface
WHY: Provide a voice-first, senior-friendly AI assistant

ENDPOINTS:
- GET / - Main interface (templates/index.html)
- POST /api/chat - Send message to Claude
- POST /api/sms - Send SMS message
- GET /api/emails - Get recent emails
- GET /api/calendar - Get today's schedule
- POST /api/emergency - Send emergency alerts
- GET /api/contacts - List available contacts
- GET /api/status - Service status check
"""

import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from datetime import datetime
from typing import Dict, Any

from config import config
from integrations.claude_client import ClaudeClient
from integrations.sms_client import SMSClient
from integrations.email_client import EmailClient
from integrations.calendar_client import CalendarClient

# Initialize Flask app
app = Flask(
    __name__,
    template_folder=str(config.templates_dir),
    static_folder=str(config.static_dir)
)
CORS(app)

# Initialize service clients
claude_client = ClaudeClient()
sms_client = SMSClient()
email_client = EmailClient()
calendar_client = CalendarClient()

# Register admin blueprint and setup routes
from admin import admin_bp, register_setup_route
app.register_blueprint(admin_bp)
register_setup_route(app)

# Register feature flag routes (Tesla-style OTA updates)
from feature_flags import register_feature_routes
register_feature_routes(app)


# ============================================================================
# WEB ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve the main tablet interface."""
    return render_template('index.html', config={
        'app_name': config.app_name,
        'speech_rate': config.speech_rate,
        'voice_volume': config.voice_volume,
        'contacts': [c.name for c in config.family_contacts[:5]]
    })


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory(config.static_dir, filename)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/status', methods=['GET'])
def get_status():
    """
    Check status of all services.

    Returns:
        JSON with service availability
    """
    return jsonify({
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'services': {
            'claude': claude_client.is_available(),
            'sms': sms_client.is_available(),
            'email': email_client.is_available(),
            'calendar': calendar_client.is_available()
        },
        'contacts': {
            'family': len(config.family_contacts),
            'emergency': len(config.emergency_contacts)
        }
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Send a message to Claude.

    Request body:
        message (str): User's message or voice transcription

    Returns:
        JSON with response and optional action
    """
    data = request.get_json() or {}
    message = data.get('message', '').strip()

    if not message:
        return jsonify({
            'success': False,
            'response': "I didn't catch that. Could you say it again?",
            'error': 'No message provided'
        }), 400

    # Send to Claude
    result = claude_client.chat(message, include_actions=True)

    return jsonify(result)


@app.route('/api/sms', methods=['POST'])
def send_sms():
    """
    Send an SMS message.

    Request body:
        to (str): Recipient name or phone number
        message (str): Message text
        compose_with_claude (bool): Use Claude to help compose message

    Returns:
        JSON with send result
    """
    data = request.get_json() or {}
    to = data.get('to', '').strip()
    message = data.get('message', '').strip()
    compose_with_claude = data.get('compose_with_claude', False)

    if not to:
        return jsonify({
            'success': False,
            'spoken_response': "Who would you like to send a message to?"
        }), 400

    # If compose_with_claude and we have intent but no message
    if compose_with_claude and data.get('intent'):
        compose_result = claude_client.get_sms_content(to, data['intent'])
        if compose_result['success']:
            message = compose_result['message']

    if not message:
        return jsonify({
            'success': False,
            'spoken_response': "What would you like to say in your message?"
        }), 400

    # Send the message
    result = sms_client.send_message(to=to, message=message)

    return jsonify(result)


@app.route('/api/emails', methods=['GET'])
def get_emails():
    """
    Get recent emails.

    Query params:
        hours (int): Hours to look back (default 24)
        priority_only (bool): Only priority emails
        limit (int): Max emails (default 10)

    Returns:
        JSON with emails and spoken summary
    """
    hours = request.args.get('hours', 24, type=int)
    priority_only = request.args.get('priority_only', 'false').lower() == 'true'
    limit = request.args.get('limit', 10, type=int)

    result = email_client.get_recent_emails(
        hours_back=hours,
        max_results=limit,
        priority_only=priority_only
    )

    return jsonify(result)


@app.route('/api/emails/<email_id>', methods=['GET'])
def get_email_detail(email_id):
    """
    Get detailed content of a specific email.

    Returns:
        JSON with email content for reading aloud
    """
    result = email_client.get_email_detail(email_id)
    return jsonify(result)


@app.route('/api/calendar', methods=['GET'])
def get_calendar():
    """
    Get calendar events.

    Query params:
        period (str): 'today', 'week', or 'next' (default: today)

    Returns:
        JSON with events and spoken summary
    """
    period = request.args.get('period', 'today')

    if period == 'today':
        result = calendar_client.get_todays_events()
    elif period == 'week':
        result = calendar_client.get_upcoming_events(days=7)
    elif period == 'next':
        result = calendar_client.get_next_event()
    else:
        result = calendar_client.get_todays_events()

    return jsonify(result)


@app.route('/api/emergency', methods=['POST'])
def emergency():
    """
    Send emergency alert to all emergency contacts.

    Request body:
        message (str): Optional custom message

    Returns:
        JSON with alert results
    """
    data = request.get_json() or {}
    custom_message = data.get('message', None)

    result = sms_client.send_emergency_alert(message=custom_message)

    return jsonify(result)


@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    """
    Get list of available contacts.

    Returns:
        JSON with family and emergency contacts
    """
    return jsonify(sms_client.list_contacts())


@app.route('/api/call', methods=['POST'])
def initiate_call():
    """
    Initiate a phone call (opens tel: link on client).

    Request body:
        contact (str): Contact name

    Returns:
        JSON with phone number to call
    """
    data = request.get_json() or {}
    contact_name = data.get('contact', '').strip()

    if not contact_name:
        return jsonify({
            'success': False,
            'spoken_response': "Who would you like to call?"
        }), 400

    # Find contact
    contact = sms_client.find_contact_by_name(contact_name)

    if not contact:
        return jsonify({
            'success': False,
            'spoken_response': f"I couldn't find {contact_name} in your contacts. Who else would you like to call?"
        }), 404

    phone = sms_client.format_phone(contact.phone)

    return jsonify({
        'success': True,
        'contact_name': contact.name,
        'phone_number': phone,
        'tel_link': f'tel:{phone}',
        'spoken_response': f"I'll connect you to {contact.name} now."
    })


# ============================================================================
# CONVERSATION MANAGEMENT
# ============================================================================

@app.route('/api/conversation/clear', methods=['POST'])
def clear_conversation():
    """Clear Claude conversation history."""
    claude_client.clear_conversation()
    return jsonify({
        'success': True,
        'spoken_response': "I've cleared our conversation. How can I help you?"
    })


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Not found',
        'spoken_response': "I'm not sure what you're looking for. Let me help you with something else."
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'spoken_response': "Something went wrong on my end. Let's try again."
    }), 500


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run the application."""
    print("\n" + "=" * 70)
    print("ELDER TECH CONCIERGE")
    print("=" * 70 + "\n")

    # Print configuration status
    config.print_status()

    # Print service status
    print("Service Status:")
    print(f"  Claude AI:  {'[OK]' if claude_client.is_available() else '[NOT CONFIGURED]'}")
    print(f"  Twilio SMS: {'[OK]' if sms_client.is_available() else '[NOT CONFIGURED]'}")
    print(f"  Gmail:      {'[OK]' if email_client.is_available() else '[NOT CONFIGURED]'}")
    print(f"  Calendar:   {'[OK]' if calendar_client.is_available() else '[NOT CONFIGURED]'}")

    print(f"\nStarting server at http://{config.app_host}:{config.app_port}")
    print("\nAccess the app from your iPad at the address above.")
    print("Press Ctrl+C to stop the server.\n")
    print("=" * 70 + "\n")

    app.run(
        host=config.app_host,
        port=config.app_port,
        debug=config.debug
    )


if __name__ == '__main__':
    main()
