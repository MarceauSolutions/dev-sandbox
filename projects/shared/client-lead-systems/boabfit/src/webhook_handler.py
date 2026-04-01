#!/usr/bin/env python3
"""
BoabFit Webhook Handler - Flask app to receive signups and process leads
Run on port 5025
"""
from flask import Flask, request, jsonify
import os
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from lead_db import add_lead, get_due_emails, mark_email_sent, get_lead_stats
from email_sender import send_welcome_email, send_drip_email

app = Flask(__name__)

@app.route('/webhook/boabfit-signup', methods=['POST'])
def handle_signup():
    """Handle new signup from landing page"""
    try:
        data = request.json or {}
        
        email = data.get('email', '').strip()
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        committed = data.get('committed', '')
        
        if not email:
            return jsonify({'success': False, 'error': 'Email required'}), 400
        
        # Add lead to database (schedules drip sequence automatically)
        lead_id = add_lead(email, name, phone, committed)
        
        if lead_id:
            # Send immediate welcome email
            first_name = name.split()[0] if name else 'there'
            send_welcome_email(email, first_name)
            
            return jsonify({
                'success': True,
                'message': 'Signup processed',
                'lead_id': lead_id
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Lead already exists',
                'lead_id': None
            })
            
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/webhook/boabfit-abandon', methods=['POST'])
def handle_abandon():
    """Handle form abandonment (partial signup)"""
    try:
        data = request.json or {}
        email = data.get('email', '').strip()
        step = data.get('step', 1)
        
        if not email:
            return jsonify({'success': True, 'message': 'No email to track'})
        
        # TODO: Add abandonment tracking and recovery sequence
        print(f"Form abandoned at step {step}: {email}")
        
        return jsonify({'success': True, 'message': 'Abandonment tracked'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/process-queue', methods=['POST', 'GET'])
def process_email_queue():
    """Process due emails in the queue - called by cron"""
    try:
        due_emails = get_due_emails()
        sent_count = 0
        
        for item in due_emails:
            try:
                first_name = item['name'].split()[0] if item.get('name') else 'there'
                success = send_drip_email(
                    item['email'], 
                    first_name,
                    item['template']
                )
                if success:
                    mark_email_sent(item['id'])
                    sent_count += 1
            except Exception as e:
                print(f"Failed to send {item['template']} to {item['email']}: {e}")
        
        return jsonify({
            'success': True,
            'processed': len(due_emails),
            'sent': sent_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/stats', methods=['GET'])
def stats():
    """Get lead stats"""
    return jsonify(get_lead_stats())

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'healthy', 'service': 'boabfit-leads'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5025, debug=False)
