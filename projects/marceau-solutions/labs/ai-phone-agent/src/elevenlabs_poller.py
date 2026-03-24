#!/usr/bin/env python3.11
"""
ElevenLabs Conversation Poller

Since ElevenLabs doesn't support webhooks for call completion,
this script polls the API for new conversations and processes them.

Run via cron every 5 minutes:
*/5 * * * * /usr/bin/python3.11 /home/clawdbot/dev-sandbox/projects/marceau-solutions/labs/ai-phone-agent/src/elevenlabs_poller.py

Or run as a systemd service for real-time polling.
"""

import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('/home/clawdbot/dev-sandbox/.env')

# Config
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
AGENT_ID = os.getenv('ELEVENLABS_AGENT_ID', 'agent_9801kmgjg670fb7bdv5z9r96y66d')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = '5692454753'

# Data storage
DATA_DIR = Path(__file__).parent.parent / 'data'
DATA_DIR.mkdir(exist_ok=True)
PROCESSED_FILE = DATA_DIR / 'processed_conversations.json'
CALLS_FILE = DATA_DIR / 'calls.json'
LEADS_FILE = DATA_DIR / 'leads.json'


def load_processed():
    """Load list of already processed conversation IDs."""
    if PROCESSED_FILE.exists():
        with open(PROCESSED_FILE) as f:
            return set(json.load(f))
    return set()


def save_processed(processed: set):
    """Save processed conversation IDs."""
    with open(PROCESSED_FILE, 'w') as f:
        json.dump(list(processed), f)


def load_calls():
    if CALLS_FILE.exists():
        with open(CALLS_FILE) as f:
            return json.load(f)
    return []


def save_calls(calls):
    with open(CALLS_FILE, 'w') as f:
        json.dump(calls, f, indent=2, default=str)


def load_leads():
    if LEADS_FILE.exists():
        with open(LEADS_FILE) as f:
            return json.load(f)
    return []


def save_leads(leads):
    with open(LEADS_FILE, 'w') as f:
        json.dump(leads, f, indent=2, default=str)


def get_recent_conversations():
    """Fetch recent conversations from ElevenLabs API."""
    try:
        response = requests.get(
            f'https://api.elevenlabs.io/v1/convai/conversations',
            headers={'xi-api-key': ELEVENLABS_API_KEY},
            params={'agent_id': AGENT_ID},
            timeout=30
        )
        if response.status_code == 200:
            return response.json().get('conversations', [])
        else:
            print(f"Error fetching conversations: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []


def get_conversation_details(conversation_id: str) -> dict:
    """Fetch full details of a specific conversation."""
    try:
        response = requests.get(
            f'https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}',
            headers={'xi-api-key': ELEVENLABS_API_KEY},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        return {}
    except Exception as e:
        print(f"Error fetching conversation {conversation_id}: {e}")
        return {}


def parse_transcript(transcript: list) -> dict:
    """Parse transcript to extract key information."""
    collected = {
        'name': None,
        'business_type': None,
        'pain_points': None,
        'phone_number': None,
        'callback_requested': False,
        'key_message': None,
        'interested': True
    }
    
    full_text = ''
    for turn in transcript:
        role = turn.get('role', '')
        message = turn.get('message', '')
        if message and message != '...':
            full_text += f"{role}: {message}\n"
    
    text_lower = full_text.lower()
    
    # Look for name patterns
    import re
    name_patterns = [
        r'(?:my name is|this is|i\'m|i am) ([A-Z][a-z]+ ?[A-Z]?[a-z]*)',
        r'([A-Z][a-z]+ [A-Z][a-z]+) (?:from|calling from|at|with)'
    ]
    for pattern in name_patterns:
        match = re.search(pattern, full_text)
        if match:
            collected['name'] = match.group(1).strip()
            break
    
    # Look for phone numbers
    phone_match = re.search(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})', full_text)
    if phone_match:
        collected['phone_number'] = phone_match.group(1)
    
    # Look for callback requests
    if any(phrase in text_lower for phrase in ['call back', 'call me back', 'give me a call', 'return my call']):
        collected['callback_requested'] = True
    
    # Extract key message (first substantive user message)
    for turn in transcript:
        if turn.get('role') == 'user':
            msg = turn.get('message', '')
            if msg and msg != '...' and len(msg) > 20:
                collected['key_message'] = msg[:200]
                break
    
    # Detect business type
    business_keywords = ['plumbing', 'hvac', 'electrical', 'roofing', 'dental', 'chiropractic', 
                        'real estate', 'pool', 'landscaping', 'pest control', 'restaurant',
                        'auto', 'car', 'insurance', 'law', 'attorney', 'medical', 'clinic']
    for keyword in business_keywords:
        if keyword in text_lower:
            collected['business_type'] = keyword.title()
            break
    
    return collected


def determine_priority(conversation: dict, collected: dict) -> dict:
    """Determine lead priority based on conversation data."""
    score = 0
    reasons = []
    
    duration = conversation.get('metadata', {}).get('call_duration_secs', 0)
    message_count = len([t for t in conversation.get('transcript', []) if t.get('message') != '...'])
    
    # Duration scoring
    if duration >= 120:
        score += 30
        reasons.append(f'Long call ({duration}s)')
    elif duration >= 60:
        score += 20
        reasons.append(f'Good engagement ({duration}s)')
    elif duration >= 30:
        score += 10
    
    # Message engagement
    if message_count >= 6:
        score += 20
        reasons.append(f'Active conversation ({message_count} messages)')
    
    # Callback requested
    if collected.get('callback_requested'):
        score += 30
        reasons.append('Callback requested')
    
    # Name provided
    if collected.get('name'):
        score += 15
        reasons.append(f'Name: {collected["name"]}')
    
    # Phone provided
    if collected.get('phone_number'):
        score += 10
        reasons.append(f'Phone: {collected["phone_number"]}')
    
    # Determine priority
    if score >= 60:
        priority = 'hot'
    elif score >= 30:
        priority = 'warm'
    elif score >= 15:
        priority = 'cold'
    else:
        priority = 'low'
    
    return {
        'score': min(score, 100),
        'priority': priority,
        'reasons': reasons,
        'follow_up': score >= 30
    }


def send_telegram_notification(conversation: dict, collected: dict, lead_score: dict):
    """Send notification to William via Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        print("No Telegram bot token")
        return
    
    caller = conversation.get('user_id', 'Unknown')
    duration = conversation.get('metadata', {}).get('call_duration_secs', 0)
    priority = lead_score.get('priority', 'unknown')
    score = lead_score.get('score', 0)
    summary = conversation.get('analysis', {}).get('transcript_summary', '')
    title = conversation.get('analysis', {}).get('call_summary_title', 'Call')
    
    # Emoji based on priority
    emoji = {'hot': '🔥', 'warm': '☀️', 'cold': '❄️', 'low': '⚪'}.get(priority, '📞')
    
    # Build message
    timestamp = datetime.fromtimestamp(
        conversation.get('metadata', {}).get('start_time_unix_secs', 0)
    ).strftime('%Y-%m-%d %H:%M')
    
    message = f"""{emoji} <b>{title}</b>

📞 <b>Caller:</b> {caller}
⏱️ <b>Duration:</b> {duration}s
📊 <b>Score:</b> {score}/100 ({priority.upper()})
🕐 <b>Time:</b> {timestamp}
"""
    
    if collected.get('name'):
        message += f"\n👤 <b>Name:</b> {collected['name']}"
    if collected.get('phone_number'):
        message += f"\n📱 <b>Callback #:</b> {collected['phone_number']}"
    if collected.get('business_type'):
        message += f"\n🏢 <b>Business:</b> {collected['business_type']}"
    
    if summary:
        message += f"\n\n📝 <b>Summary:</b>\n{summary[:300]}"
    elif collected.get('key_message'):
        message += f"\n\n💬 <b>Key Message:</b>\n<i>\"{collected['key_message']}\"</i>"
    
    if lead_score.get('follow_up'):
        message += f"\n\n⚡ <b>Action Required:</b> Call back"
    
    try:
        requests.post(
            f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
            json={
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'
            },
            timeout=10
        )
        print(f"Notification sent for {conversation.get('conversation_id')}")
    except Exception as e:
        print(f"Failed to send notification: {e}")


def process_conversation(conversation_summary: dict, processed: set):
    """Process a single conversation."""
    conv_id = conversation_summary.get('conversation_id')
    
    if conv_id in processed:
        return False
    
    # Skip very short calls (likely hangups)
    if conversation_summary.get('call_duration_secs', 0) < 10:
        processed.add(conv_id)
        return False
    
    print(f"Processing conversation: {conv_id}")
    
    # Get full details
    details = get_conversation_details(conv_id)
    if not details:
        return False
    
    # Parse transcript
    transcript = details.get('transcript', [])
    collected = parse_transcript(transcript)
    
    # Determine priority
    lead_score = determine_priority(details, collected)
    
    # Build call record
    call_record = {
        'id': conv_id,
        'conversation_id': conv_id,
        'caller_number': details.get('user_id', 'Unknown'),
        'call_sid': details.get('metadata', {}).get('phone_call', {}).get('call_sid', ''),
        'timestamp': datetime.fromtimestamp(
            details.get('metadata', {}).get('start_time_unix_secs', 0)
        ).isoformat(),
        'duration_seconds': details.get('metadata', {}).get('call_duration_secs', 0),
        'transcript': '\n'.join([
            f"{t.get('role', 'unknown')}: {t.get('message', '')}"
            for t in transcript if t.get('message') != '...'
        ]),
        'collected_data': collected,
        'lead_score': lead_score,
        'summary': details.get('analysis', {}).get('transcript_summary', ''),
        'title': details.get('analysis', {}).get('call_summary_title', ''),
        'raw_data': conversation_summary,
        'processed_at': datetime.now().isoformat()
    }
    
    # Save to calls
    calls = load_calls()
    # Check if already exists
    if not any(c.get('id') == conv_id for c in calls):
        calls.insert(0, call_record)
        save_calls(calls)
    
    # Save as lead if significant
    if lead_score.get('follow_up'):
        leads = load_leads()
        if not any(l.get('call_id') == conv_id for l in leads):
            lead = {
                'id': len(leads) + 1,
                'call_id': conv_id,
                'phone': details.get('user_id', ''),
                'name': collected.get('name', ''),
                'email': '',
                'source': 'elevenlabs-ai',
                'status': f"{lead_score['priority']}_lead",
                'business_type': collected.get('business_type', ''),
                'pain_points': '',
                'timeline': '',
                'notes': collected.get('key_message', ''),
                'score': lead_score['score'],
                'created_at': datetime.now().isoformat(),
                'follow_up_at': (datetime.now() + timedelta(hours=24)).isoformat(),
                'contacted': False
            }
            leads.insert(0, lead)
            save_leads(leads)
    
    # Send notification
    send_telegram_notification(details, collected, lead_score)
    
    # Mark as processed
    processed.add(conv_id)
    
    return True


def main():
    """Main polling loop."""
    print(f"[{datetime.now()}] Starting ElevenLabs poller...")
    
    processed = load_processed()
    print(f"Already processed: {len(processed)} conversations")
    
    # Get recent conversations
    conversations = get_recent_conversations()
    print(f"Found {len(conversations)} conversations")
    
    new_count = 0
    for conv in conversations:
        if process_conversation(conv, processed):
            new_count += 1
    
    # Save processed list
    save_processed(processed)
    
    print(f"[{datetime.now()}] Done. Processed {new_count} new conversations.")
    
    return new_count


if __name__ == '__main__':
    main()
