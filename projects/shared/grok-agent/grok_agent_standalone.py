#!/usr/bin/env python3
"""
Grok Agentic Assistant - Standalone Server
Mirrors Clawdbot's capabilities but powered by Grok

Endpoint: POST http://localhost:8790/agent
Body: {"message": "your request here"}
"""

import os
import json
import subprocess
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv('/home/clawdbot/dev-sandbox/.env')

app = Flask(__name__)

XAI_API_KEY = os.getenv('XAI_API_KEY')
BRAVE_API_KEY = os.getenv('BRAVE_API_KEY')

SYSTEM_PROMPT = """You are Grok Agent, an AI assistant with tool access running on William Marceau's infrastructure.

Analyze the user request and respond with JSON:
{"action": "tool_name", "params": {...}, "direct_response": "text if no tool needed"}

Available tools:
- web_search: {"query": "search terms"} - Search the web via Brave
- pipeline_status: {} - Get sales pipeline summary
- calendar_check: {"days": 7} - Check upcoming calendar events
- send_telegram: {"message": "text"} - Send message to William on Telegram
- execute_python: {"code": "python code"} - Execute Python code
- direct_response: {} - Just respond directly without tools

Rules:
1. Pick the MOST appropriate tool for the request
2. If it's a general question or conversation, use direct_response
3. For factual lookups, use web_search
4. For business questions, use pipeline_status
5. Always include a direct_response field with your commentary

Respond ONLY with valid JSON, no markdown."""


def call_grok(messages: list, temperature: float = 0.7) -> str:
    """Call Grok API"""
    resp = requests.post(
        'https://api.x.ai/v1/chat/completions',
        headers={
            'Authorization': f'Bearer {XAI_API_KEY}',
            'Content-Type': 'application/json'
        },
        json={
            'model': 'grok-3-latest',
            'messages': messages,
            'temperature': temperature
        },
        timeout=60
    )
    resp.raise_for_status()
    return resp.json()['choices'][0]['message']['content']


def tool_web_search(params: dict) -> str:
    """Search the web via Brave API"""
    query = params.get('query', '')
    resp = requests.get(
        'https://api.search.brave.com/res/v1/web/search',
        headers={'X-Subscription-Token': BRAVE_API_KEY},
        params={'q': query, 'count': 5},
        timeout=30
    )
    resp.raise_for_status()
    results = resp.json().get('web', {}).get('results', [])
    return '\n'.join([f"• {r['title']}: {r['url']}" for r in results[:5]])


def tool_pipeline_status(params: dict) -> str:
    """Get pipeline summary"""
    try:
        resp = requests.get('http://localhost:8786/route', 
                          json={'text': 'pipeline status'}, timeout=10)
        return resp.json().get('response', 'Pipeline service unavailable')
    except:
        try:
            resp = requests.get('http://localhost:5010/pipeline/summary', timeout=10)
            return resp.text
        except:
            return "Pipeline service unavailable"


def tool_calendar_check(params: dict) -> str:
    """Check calendar events"""
    days = params.get('days', 7)
    try:
        result = subprocess.run(
            ['python3.11', '/home/clawdbot/dev-sandbox/execution/smart_calendar.py', 
             '--no-transitions', '--no-projects', f'--days={days}'],
            capture_output=True, text=True, timeout=30, cwd='/home/clawdbot/dev-sandbox'
        )
        return result.stdout or "No events found"
    except Exception as e:
        return f"Calendar error: {e}"


def tool_send_telegram(params: dict) -> str:
    """Send Telegram message"""
    message = params.get('message', '')
    try:
        # Use clawdbot's message endpoint
        resp = requests.post(
            'http://localhost:5002/webhook/telegram/send',
            json={'chat_id': '5692454753', 'text': f"[Grok Agent] {message}"},
            timeout=10
        )
        return "Message sent to Telegram"
    except:
        return "Telegram send failed"


def tool_execute_python(params: dict) -> str:
    """Execute Python code (sandboxed)"""
    code = params.get('code', '')
    try:
        result = subprocess.run(
            ['python3.11', '-c', code],
            capture_output=True, text=True, timeout=30,
            cwd='/tmp'
        )
        output = result.stdout or result.stderr or "No output"
        return output[:2000]  # Truncate
    except Exception as e:
        return f"Execution error: {e}"


TOOLS = {
    'web_search': tool_web_search,
    'pipeline_status': tool_pipeline_status,
    'calendar_check': tool_calendar_check,
    'send_telegram': tool_send_telegram,
    'execute_python': tool_execute_python,
}


@app.route('/agent', methods=['POST'])
def agent():
    """Main agent endpoint"""
    data = request.get_json() or {}
    user_message = data.get('message') or data.get('text') or 'Hello'
    
    # Step 1: Grok decides what to do
    try:
        decision = call_grok([
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': user_message}
        ])
        
        # Parse Grok's JSON response
        try:
            # Handle markdown code blocks
            if '```' in decision:
                import re
                match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', decision)
                decision = match.group(1) if match else decision
            parsed = json.loads(decision)
        except:
            parsed = {'action': 'direct_response', 'direct_response': decision}
        
        action = parsed.get('action', 'direct_response')
        params = parsed.get('params', {})
        direct = parsed.get('direct_response', '')
        
        # Step 2: Execute tool if needed
        tool_result = None
        if action in TOOLS:
            tool_result = TOOLS[action](params)
        
        # Step 3: Grok summarizes with tool results
        if tool_result:
            final_response = call_grok([
                {'role': 'system', 'content': 'Summarize the tool results helpfully. Be conversational and concise.'},
                {'role': 'user', 'content': f"User asked: {user_message}\n\nTool ({action}) returned:\n{tool_result}\n\nYour initial thought: {direct}"}
            ])
        else:
            final_response = direct or decision
        
        return jsonify({
            'success': True,
            'agent': 'grok',
            'action': action,
            'response': final_response
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'agent': 'grok',
            'error': str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'agent': 'grok'})


if __name__ == '__main__':
    print("🚀 Grok Agentic Assistant starting on port 8790...")
    print("   POST /agent with {\"message\": \"your request\"}")
    app.run(host='0.0.0.0', port=8790, debug=False)
