#!/usr/bin/env python3.11
"""
AI Phone Agent - Enhanced Call Handler
Receives webhooks from ElevenLabs Conversational AI and processes call data.

This is the central hub that:
1. Receives call completion data from ElevenLabs
2. Parses transcripts and extracts qualification data
3. Determines follow-up priority
4. Sends rich Telegram notifications
5. Routes leads to CRM (Google Sheets + Sales Pipeline)
6. Stores structured call records

Deployment: ai-phone.marceausolutions.com
Port: 8795
"""

import os
import json
import re
import requests
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

load_dotenv('/home/clawdbot/dev-sandbox/.env')

app = Flask(__name__)
CORS(app)

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = '5692454753'  # William

# Google Sheets CRM
GOOGLE_SHEETS_ID = os.getenv('PHONE_LEADS_SHEET_ID', '1D5vKHJqTYPjLYPLYPLYPLYPLY')  # Will need to create this
SERVICE_ACCOUNT_FILE = '/home/clawdbot/dev-sandbox/credentials.json'

# Sales Pipeline API
PIPELINE_API = 'http://localhost:5010'

# Data storage
DATA_DIR = Path(__file__).parent.parent / 'data'
DATA_DIR.mkdir(exist_ok=True)
CALLS_FILE = DATA_DIR / 'calls.json'
LEADS_FILE = DATA_DIR / 'leads.json'

# Load agent config for context
CONFIG_PATH = Path(__file__).parent.parent / 'config' / 'agent_config.json'
with open(CONFIG_PATH) as f:
    AGENT_CONFIG = json.load(f)


# ==============================================================================
# DATA STORAGE
# ==============================================================================

def load_calls():
    """Load call history from JSON file."""
    if CALLS_FILE.exists():
        with open(CALLS_FILE) as f:
            return json.load(f)
    return []


def save_calls(calls):
    """Save call history to JSON file."""
    with open(CALLS_FILE, 'w') as f:
        json.dump(calls, f, indent=2, default=str)


def load_leads():
    """Load leads from JSON file."""
    if LEADS_FILE.exists():
        with open(LEADS_FILE) as f:
            return json.load(f)
    return []


def save_leads(leads):
    """Save leads to JSON file."""
    with open(LEADS_FILE, 'w') as f:
        json.dump(leads, f, indent=2, default=str)


# ==============================================================================
# TRANSCRIPT PARSING & QUALIFICATION
# ==============================================================================

def parse_transcript(transcript_text: str) -> dict:
    """
    Parse the call transcript to extract qualification data.
    Returns structured data based on the qualifying questions.
    """
    collected = {
        'business_type': None,
        'pain_points': None,
        'current_tech': None,
        'timeline': None,
        'budget': None,
        'callback_requested': False,
        'callback_time': None,
        'email': None,
        'name': None,
        'interested': True,
        'key_quotes': []
    }
    
    # Common patterns to extract
    text_lower = transcript_text.lower()
    
    # Business type detection
    business_patterns = [
        (r'(?:i run|i have|i own|we\'re|we are|it\'s) (?:a |an )?(.+?)(?:business|company|shop|store|service)', 'business_type'),
        (r'(?:hvac|plumbing|electrical|roofing|dental|chiropractic|real estate|pool|landscaping|pest control)', 'business_type'),
    ]
    
    for pattern, field in business_patterns:
        match = re.search(pattern, text_lower)
        if match and not collected[field]:
            collected[field] = match.group(1).strip() if match.lastindex else match.group(0)
    
    # Pain points detection
    pain_patterns = [
        r'(?:biggest challenge|headache|problem|issue|struggle) (?:is |with )?(.+?)(?:\.|,|$)',
        r'(?:missing|losing) (?:calls?|customers?|leads?)',
        r'(?:after hours?|nights?|weekends?) (?:calls?|coverage)',
        r'(?:too busy|overwhelmed|can\'t keep up)',
    ]
    
    for pattern in pain_patterns:
        match = re.search(pattern, text_lower)
        if match:
            collected['pain_points'] = match.group(0)[:200]
            break
    
    # Timeline detection
    if any(word in text_lower for word in ['asap', 'immediately', 'right away', 'this week', 'urgent']):
        collected['timeline'] = 'urgent'
    elif any(word in text_lower for word in ['next month', 'few weeks', 'soon']):
        collected['timeline'] = 'soon'
    elif any(word in text_lower for word in ['exploring', 'just looking', 'researching', 'maybe later']):
        collected['timeline'] = 'exploring'
    
    # Interest/disqualification signals
    negative_signals = ['not interested', 'wrong number', 'stop calling', 'remove me', 'no thanks']
    if any(signal in text_lower for signal in negative_signals):
        collected['interested'] = False
    
    # Email extraction
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', transcript_text)
    if email_match:
        collected['email'] = email_match.group(0)
    
    # Name extraction (look for "my name is" or "this is")
    name_match = re.search(r'(?:my name is|this is|i\'m|i am) ([A-Z][a-z]+ ?[A-Z]?[a-z]*)', transcript_text)
    if name_match:
        collected['name'] = name_match.group(1).strip()
    
    # Extract key quotes (sentences with qualifying info)
    sentences = re.split(r'[.!?]', transcript_text)
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 20 and any(word in sentence.lower() for word in 
            ['need', 'want', 'looking for', 'interested', 'help with', 'problem', 'challenge']):
            collected['key_quotes'].append(sentence[:150])
            if len(collected['key_quotes']) >= 3:
                break
    
    return collected


def determine_lead_score(collected_data: dict, call_duration: int) -> dict:
    """
    Determine lead quality score and follow-up priority.
    Returns score (0-100) and priority (hot/warm/cold/disqualified).
    """
    score = 0
    reasons = []
    
    # Not interested = immediate disqualification
    if not collected_data.get('interested', True):
        return {
            'score': 0,
            'priority': 'disqualified',
            'reasons': ['Expressed no interest'],
            'follow_up': False
        }
    
    # Call duration scoring (longer = more engaged)
    if call_duration >= 180:  # 3+ minutes
        score += 30
        reasons.append('High engagement (3+ min call)')
    elif call_duration >= 60:  # 1-3 minutes
        score += 20
        reasons.append('Good engagement (1-3 min)')
    elif call_duration >= 30:  # 30-60 seconds
        score += 10
        reasons.append('Brief conversation')
    else:
        score += 5
    
    # Pain points identified
    if collected_data.get('pain_points'):
        score += 25
        reasons.append(f'Pain point: {collected_data["pain_points"][:50]}...')
    
    # Timeline urgency
    timeline = collected_data.get('timeline')
    if timeline == 'urgent':
        score += 25
        reasons.append('Urgent timeline')
    elif timeline == 'soon':
        score += 15
        reasons.append('Near-term timeline')
    elif timeline == 'exploring':
        score += 5
        reasons.append('Exploring options')
    
    # Business type identified
    if collected_data.get('business_type'):
        score += 10
        reasons.append(f'Business: {collected_data["business_type"]}')
    
    # Contact info provided
    if collected_data.get('email'):
        score += 10
        reasons.append('Email provided')
    if collected_data.get('name'):
        score += 5
        reasons.append(f'Name: {collected_data["name"]}')
    
    # Determine priority
    if score >= 70:
        priority = 'hot'
        follow_up = True
    elif score >= 40:
        priority = 'warm'
        follow_up = True
    elif score >= 20:
        priority = 'cold'
        follow_up = True
    else:
        priority = 'low'
        follow_up = False
    
    return {
        'score': min(score, 100),
        'priority': priority,
        'reasons': reasons,
        'follow_up': follow_up
    }


# ==============================================================================
# NOTIFICATIONS
# ==============================================================================

def send_telegram_notification(call_record: dict):
    """
    Send rich Telegram notification with call details.
    Uses different formats based on lead priority.
    """
    if not TELEGRAM_BOT_TOKEN:
        print("No TELEGRAM_BOT_TOKEN configured")
        return
    
    lead_score = call_record.get('lead_score', {})
    priority = lead_score.get('priority', 'unknown')
    score = lead_score.get('score', 0)
    collected = call_record.get('collected_data', {})
    
    # Priority emoji
    priority_emoji = {
        'hot': '🔥',
        'warm': '☀️',
        'cold': '❄️',
        'low': '⚪',
        'disqualified': '❌'
    }.get(priority, '❓')
    
    # Build message
    caller = call_record.get('caller_number', 'Unknown')
    duration = call_record.get('duration_seconds', 0)
    duration_str = f"{duration // 60}:{duration % 60:02d}"
    
    # Header based on priority
    if priority == 'hot':
        header = f"🔥 <b>HOT LEAD — CALL BACK NOW</b> 🔥"
    elif priority == 'warm':
        header = f"☀️ <b>Warm Lead Captured</b>"
    elif priority == 'disqualified':
        header = f"❌ <b>Call Handled — No Follow-up Needed</b>"
    else:
        header = f"{priority_emoji} <b>Call Completed</b>"
    
    message = f"""{header}

📞 <b>Caller:</b> {caller}
⏱️ <b>Duration:</b> {duration_str}
📊 <b>Score:</b> {score}/100 ({priority})
🕐 <b>Time:</b> {call_record.get('timestamp', 'Unknown')}
"""
    
    # Add collected data if available
    if collected.get('name'):
        message += f"\n👤 <b>Name:</b> {collected['name']}"
    if collected.get('business_type'):
        message += f"\n🏢 <b>Business:</b> {collected['business_type']}"
    if collected.get('pain_points'):
        message += f"\n😣 <b>Pain Point:</b> {collected['pain_points'][:100]}"
    if collected.get('timeline'):
        message += f"\n📅 <b>Timeline:</b> {collected['timeline']}"
    if collected.get('email'):
        message += f"\n📧 <b>Email:</b> {collected['email']}"
    
    # Add scoring reasons
    if lead_score.get('reasons'):
        message += f"\n\n<b>Qualification:</b>"
        for reason in lead_score['reasons'][:5]:
            message += f"\n• {reason}"
    
    # Add key quotes if available
    if collected.get('key_quotes'):
        message += f"\n\n💬 <b>Key Quotes:</b>"
        for quote in collected['key_quotes'][:2]:
            message += f"\n<i>\"{quote}\"</i>"
    
    # Add action items for hot/warm leads
    if priority in ['hot', 'warm']:
        message += f"\n\n⚡ <b>Action:</b> Call back within "
        if priority == 'hot':
            message += "1 hour"
        else:
            message += "24 hours"
    
    # Recording link if available
    if call_record.get('recording_url'):
        message += f"\n\n🎙️ <a href=\"{call_record['recording_url']}\">Listen to Recording</a>"
    
    try:
        response = requests.post(
            f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
            json={
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            },
            timeout=10
        )
        print(f"Telegram notification sent: {response.status_code}")
    except Exception as e:
        print(f"Failed to send Telegram notification: {e}")


# ==============================================================================
# CRM INTEGRATION
# ==============================================================================

def add_to_google_sheets(call_record: dict):
    """Add lead to Google Sheets CRM."""
    try:
        # Use service account credentials
        if not Path(SERVICE_ACCOUNT_FILE).exists():
            print("No service account file, skipping Sheets")
            return
        
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
        client = gspread.authorize(creds)
        
        # Open or create the sheet
        try:
            sheet = client.open_by_key(os.getenv('PHONE_LEADS_SHEET_ID'))
        except:
            print("Could not open Google Sheet, skipping")
            return
        
        worksheet = sheet.sheet1
        
        collected = call_record.get('collected_data', {})
        lead_score = call_record.get('lead_score', {})
        
        # Append row
        row = [
            call_record.get('timestamp', ''),
            call_record.get('caller_number', ''),
            collected.get('name', ''),
            collected.get('business_type', ''),
            collected.get('pain_points', ''),
            collected.get('timeline', ''),
            collected.get('email', ''),
            lead_score.get('score', 0),
            lead_score.get('priority', ''),
            'Yes' if lead_score.get('follow_up') else 'No',
            call_record.get('duration_seconds', 0),
            call_record.get('recording_url', ''),
            'Pending'  # Status column
        ]
        
        worksheet.append_row(row)
        print("Added to Google Sheets")
        
    except Exception as e:
        print(f"Failed to add to Google Sheets: {e}")


def add_to_sales_pipeline(call_record: dict):
    """Add qualified lead to the sales pipeline."""
    try:
        collected = call_record.get('collected_data', {})
        lead_score = call_record.get('lead_score', {})
        
        # Only add warm+ leads to pipeline
        if lead_score.get('priority') not in ['hot', 'warm']:
            return
        
        deal_data = {
            'company': collected.get('business_type', 'Unknown Business'),
            'contact_name': collected.get('name', ''),
            'contact_phone': call_record.get('caller_number', ''),
            'contact_email': collected.get('email', ''),
            'industry': collected.get('business_type', 'Other'),
            'pain_points': collected.get('pain_points', ''),
            'lead_source': 'ai-phone-inbound',
            'stage': 'Qualified' if lead_score.get('priority') == 'hot' else 'Intake',
            'notes': f"AI Phone Agent capture. Score: {lead_score.get('score')}/100. Timeline: {collected.get('timeline', 'unknown')}",
            'lead_score': lead_score.get('score', 0)
        }
        
        response = requests.post(
            f'{PIPELINE_API}/pipeline/deal/add',
            json=deal_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"Added to sales pipeline: {response.json()}")
        else:
            print(f"Pipeline API error: {response.status_code}")
            
    except Exception as e:
        print(f"Failed to add to pipeline: {e}")


# ==============================================================================
# WEBHOOK ENDPOINTS
# ==============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'service': 'AI Phone Agent - Enhanced Call Handler',
        'version': '2.0',
        'timestamp': datetime.now().isoformat(),
        'features': [
            'ElevenLabs webhook receiver',
            'Transcript parsing',
            'Lead qualification',
            'Telegram notifications',
            'Google Sheets CRM',
            'Sales Pipeline integration'
        ]
    })


@app.route('/webhook/elevenlabs', methods=['POST'])
def elevenlabs_webhook():
    """
    Receive call completion webhook from ElevenLabs Conversational AI.
    
    ElevenLabs sends data like:
    {
        "conversation_id": "...",
        "call_sid": "...",
        "caller": "+1234567890",
        "duration": 180,
        "transcript": [...],
        "recording_url": "...",
        "status": "completed"
    }
    """
    try:
        data = request.json or {}
        print(f"[{datetime.now()}] ElevenLabs webhook received: {json.dumps(data, indent=2)[:500]}")
        
        # Extract basic call info
        caller_number = data.get('caller') or data.get('from') or data.get('phone_number', 'Unknown')
        call_sid = data.get('call_sid') or data.get('conversation_id', '')
        duration = data.get('duration') or data.get('call_duration', 0)
        
        # Get transcript
        transcript_data = data.get('transcript', [])
        if isinstance(transcript_data, list):
            # ElevenLabs format: list of {role, message} objects
            transcript_text = '\n'.join([
                f"{t.get('role', 'unknown')}: {t.get('message', t.get('text', ''))}"
                for t in transcript_data
            ])
        elif isinstance(transcript_data, str):
            transcript_text = transcript_data
        else:
            transcript_text = ''
        
        # Parse transcript for qualification data
        collected_data = parse_transcript(transcript_text)
        
        # Determine lead score and priority
        lead_score = determine_lead_score(collected_data, duration)
        
        # Build call record
        call_record = {
            'id': call_sid or f"call_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'caller_number': caller_number,
            'call_sid': call_sid,
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': duration,
            'transcript': transcript_text,
            'collected_data': collected_data,
            'lead_score': lead_score,
            'recording_url': data.get('recording_url', ''),
            'raw_data': data,
            'processed': True
        }
        
        # Store call record
        calls = load_calls()
        calls.insert(0, call_record)
        save_calls(calls)
        
        # Send Telegram notification
        send_telegram_notification(call_record)
        
        # Add to CRM systems
        add_to_google_sheets(call_record)
        add_to_sales_pipeline(call_record)
        
        # Also store as lead for dashboard
        leads = load_leads()
        lead_entry = {
            'id': len(leads) + 1,
            'phone': caller_number,
            'name': collected_data.get('name', ''),
            'email': collected_data.get('email', ''),
            'source': 'elevenlabs-ai',
            'status': f"{lead_score['priority']}_lead",
            'business_type': collected_data.get('business_type', ''),
            'pain_points': collected_data.get('pain_points', ''),
            'timeline': collected_data.get('timeline', ''),
            'notes': '; '.join(collected_data.get('key_quotes', [])),
            'call_sid': call_sid,
            'recording_url': data.get('recording_url', ''),
            'score': lead_score['score'],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'follow_up_at': (datetime.now() + timedelta(hours=24)).isoformat() if lead_score['follow_up'] else None,
            'contacted': False
        }
        leads.insert(0, lead_entry)
        save_leads(leads)
        
        return jsonify({
            'status': 'processed',
            'lead_score': lead_score,
            'call_id': call_record['id']
        })
        
    except Exception as e:
        print(f"Error processing ElevenLabs webhook: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/webhook/twilio-status', methods=['POST'])
def twilio_status():
    """Receive Twilio call status updates."""
    call_sid = request.values.get('CallSid')
    status = request.values.get('CallStatus')
    duration = request.values.get('CallDuration', 0)
    caller = request.values.get('From', 'Unknown')
    
    print(f"[{datetime.now()}] Twilio status: {call_sid} = {status} ({duration}s) from {caller}")
    
    # Send alert for completed calls that weren't captured by ElevenLabs
    if status == 'completed' and int(duration or 0) > 10:
        # Check if we already processed this call
        calls = load_calls()
        if not any(c.get('call_sid') == call_sid for c in calls):
            # Send basic notification - call wasn't captured by ElevenLabs
            try:
                requests.post(
                    f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
                    json={
                        'chat_id': TELEGRAM_CHAT_ID,
                        'text': f"📞 <b>Call Completed (no transcript)</b>\nFrom: {caller}\nDuration: {duration}s\n\n⚠️ ElevenLabs didn't capture this call. Consider calling back.",
                        'parse_mode': 'HTML'
                    },
                    timeout=5
                )
            except:
                pass
    
    return '', 200


@app.route('/webhook/test', methods=['POST'])
def test_webhook():
    """Test endpoint to simulate a call."""
    data = request.json or {
        'caller': '+12395551234',
        'duration': 120,
        'transcript': [
            {'role': 'assistant', 'message': "Hi, thanks for calling Marceau Solutions!"},
            {'role': 'user', 'message': "Hi, my name is John. I run a plumbing company here in Naples."},
            {'role': 'assistant', 'message': "Great! What's your biggest headache with customer calls?"},
            {'role': 'user', 'message': "We're losing a lot of after-hours calls. People call at night and we miss them."},
            {'role': 'assistant', 'message': "I hear that a lot. What's your timeline for fixing this?"},
            {'role': 'user', 'message': "I'd like to get something set up in the next week or two."}
        ]
    }
    
    # Process as if it came from ElevenLabs
    return elevenlabs_webhook()


# ==============================================================================
# API ENDPOINTS
# ==============================================================================

@app.route('/api/calls', methods=['GET'])
def get_calls():
    """Get call history."""
    calls = load_calls()
    limit = request.args.get('limit', 50, type=int)
    priority = request.args.get('priority')
    
    if priority:
        calls = [c for c in calls if c.get('lead_score', {}).get('priority') == priority]
    
    return jsonify({
        'calls': calls[:limit],
        'total': len(calls)
    })


@app.route('/api/calls/<call_id>', methods=['GET'])
def get_call(call_id):
    """Get specific call details."""
    calls = load_calls()
    for call in calls:
        if call.get('id') == call_id or call.get('call_sid') == call_id:
            return jsonify(call)
    return jsonify({'error': 'Call not found'}), 404


@app.route('/api/leads', methods=['GET'])
def get_leads():
    """Get all leads."""
    leads = load_leads()
    return jsonify({'leads': leads, 'count': len(leads)})


@app.route('/api/leads', methods=['POST'])
def add_lead():
    """Manually add a lead."""
    data = request.json
    leads = load_leads()
    
    lead = {
        'id': len(leads) + 1,
        'phone': data.get('phone', 'Unknown'),
        'name': data.get('name', ''),
        'email': data.get('email', ''),
        'source': data.get('source', 'manual'),
        'status': data.get('status', 'warm_lead'),
        'business_type': data.get('business_type', ''),
        'pain_points': data.get('pain_points', ''),
        'timeline': data.get('timeline', ''),
        'notes': data.get('notes', ''),
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'follow_up_at': None,
        'contacted': False
    }
    
    leads.insert(0, lead)
    save_leads(leads)
    
    return jsonify({'status': 'created', 'lead': lead})


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get call and lead statistics."""
    calls = load_calls()
    leads = load_leads()
    
    today = datetime.now().date().isoformat()
    
    return jsonify({
        'total_calls': len(calls),
        'calls_today': len([c for c in calls if c.get('timestamp', '').startswith(today)]),
        'total_leads': len(leads),
        'hot_leads': len([l for l in leads if 'hot' in l.get('status', '')]),
        'warm_leads': len([l for l in leads if 'warm' in l.get('status', '')]),
        'pending_followup': len([l for l in leads if not l.get('contacted') and l.get('follow_up_at')]),
        'avg_score': sum(c.get('lead_score', {}).get('score', 0) for c in calls) / max(len(calls), 1)
    })


# ==============================================================================
# DASHBOARD
# ==============================================================================

@app.route('/')
def dashboard():
    """Render the enhanced leads dashboard."""
    calls = load_calls()[:20]
    leads = load_leads()
    
    # Statistics
    stats = {
        'total_calls': len(load_calls()),
        'hot_leads': len([l for l in leads if 'hot' in l.get('status', '')]),
        'warm_leads': len([l for l in leads if 'warm' in l.get('status', '')]),
        'pending': len([l for l in leads if not l.get('contacted')])
    }
    
    html = f'''
<!DOCTYPE html>
<html>
<head>
    <title>AI Phone Agent | Marceau Solutions</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a; color: #fff; padding: 20px; min-height: 100vh;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ font-size: 1.8rem; margin-bottom: 10px; }}
        .subtitle {{ color: #888; margin-bottom: 30px; }}
        
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 30px; }}
        .stat-card {{ background: #1a1a1a; padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #333; }}
        .stat-value {{ font-size: 2.5rem; font-weight: bold; }}
        .stat-label {{ color: #888; font-size: 0.85rem; margin-top: 5px; }}
        .stat-card.hot .stat-value {{ color: #ef4444; }}
        .stat-card.warm .stat-value {{ color: #f59e0b; }}
        
        .section {{ margin-bottom: 40px; }}
        .section-title {{ font-size: 1.2rem; margin-bottom: 15px; color: #fff; }}
        
        .call-card {{ background: #1a1a1a; border-radius: 12px; padding: 20px; margin-bottom: 15px; border: 1px solid #333; }}
        .call-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
        .caller {{ font-family: monospace; font-size: 1.1rem; }}
        .priority {{ padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }}
        .priority.hot {{ background: #ef444422; color: #ef4444; }}
        .priority.warm {{ background: #f59e0b22; color: #f59e0b; }}
        .priority.cold {{ background: #3b82f622; color: #3b82f6; }}
        
        .call-details {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
        .detail {{ }}
        .detail-label {{ color: #666; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; }}
        .detail-value {{ margin-top: 4px; }}
        
        .transcript {{ background: #111; padding: 15px; border-radius: 8px; margin-top: 15px; font-size: 0.9rem; max-height: 200px; overflow-y: auto; }}
        
        .btn {{ padding: 10px 20px; border-radius: 8px; border: none; cursor: pointer; font-size: 0.9rem; }}
        .btn-primary {{ background: #3b82f6; color: white; }}
        .btn-success {{ background: #22c55e; color: white; }}
        
        .empty {{ text-align: center; padding: 60px; color: #666; }}
        
        @media (max-width: 768px) {{
            .call-details {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📞 AI Phone Agent Dashboard</h1>
        <p class="subtitle">Inbound call tracking and lead qualification</p>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{stats['total_calls']}</div>
                <div class="stat-label">Total Calls</div>
            </div>
            <div class="stat-card hot">
                <div class="stat-value">{stats['hot_leads']}</div>
                <div class="stat-label">Hot Leads</div>
            </div>
            <div class="stat-card warm">
                <div class="stat-value">{stats['warm_leads']}</div>
                <div class="stat-label">Warm Leads</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['pending']}</div>
                <div class="stat-label">Pending Follow-up</div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">Recent Calls</h2>
            {''.join([f"""
            <div class="call-card">
                <div class="call-header">
                    <span class="caller">{call.get('caller_number', 'Unknown')}</span>
                    <span class="priority {call.get('lead_score', {}).get('priority', 'cold')}">
                        {call.get('lead_score', {}).get('priority', 'unknown').upper()} ({call.get('lead_score', {}).get('score', 0)})
                    </span>
                </div>
                <div class="call-details">
                    <div class="detail">
                        <div class="detail-label">Time</div>
                        <div class="detail-value">{call.get('timestamp', 'Unknown')[:16].replace('T', ' ')}</div>
                    </div>
                    <div class="detail">
                        <div class="detail-label">Duration</div>
                        <div class="detail-value">{call.get('duration_seconds', 0) // 60}:{call.get('duration_seconds', 0) % 60:02d}</div>
                    </div>
                    <div class="detail">
                        <div class="detail-label">Business</div>
                        <div class="detail-value">{call.get('collected_data', {}).get('business_type', '-')}</div>
                    </div>
                    <div class="detail">
                        <div class="detail-label">Pain Point</div>
                        <div class="detail-value">{call.get('collected_data', {}).get('pain_points', '-')[:100]}</div>
                    </div>
                </div>
                {'<div class="transcript">' + call.get('transcript', 'No transcript')[:500] + '</div>' if call.get('transcript') else ''}
            </div>
            """ for call in calls]) if calls else '<div class="empty">No calls yet. When someone calls (855) 239-9364, calls will appear here.</div>'}
        </div>
    </div>
    
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
'''
    return html


if __name__ == '__main__':
    print("Starting AI Phone Agent - Enhanced Call Handler")
    print(f"Webhook URL: https://ai-phone.marceausolutions.com/webhook/elevenlabs")
    app.run(host='0.0.0.0', port=8795, debug=False)
