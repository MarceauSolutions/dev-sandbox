#!/usr/bin/env python3
"""
claude_client.py - Claude AI Integration for Elder Tech Concierge

WHAT: Wrapper for Claude API calls tailored for senior assistance
WHY: Provide AI-powered conversation with senior-friendly responses
"""

import os
import sys
from typing import Optional, Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic package not installed")
    print("Install with: pip install anthropic")
    anthropic = None

from config import config, ELDER_ASSISTANT_SYSTEM_PROMPT


class ClaudeClient:
    """
    Claude AI client optimized for elderly user interactions.

    Features:
    - Senior-friendly response formatting
    - Context-aware assistance
    - Action extraction for app commands
    """

    # Actions that Claude can suggest
    ACTIONS = {
        'send_sms': 'Send a text message',
        'read_emails': 'Read recent emails',
        'check_calendar': 'Check today\'s schedule',
        'call_family': 'Call a family member',
        'emergency': 'Contact emergency services',
    }

    def __init__(self, api_key: str = None):
        """
        Initialize Claude client.

        Args:
            api_key: Anthropic API key (defaults to config)
        """
        self.api_key = api_key or config.claude_api_key
        self.model = config.claude_model
        self.client = None
        self.conversation_history: List[Dict[str, str]] = []

        if anthropic and self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)

    def is_available(self) -> bool:
        """Check if Claude API is available."""
        return self.client is not None

    def clear_conversation(self):
        """Clear conversation history."""
        self.conversation_history = []

    def chat(
        self,
        user_message: str,
        include_actions: bool = True,
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """
        Send a message to Claude and get a response.

        Args:
            user_message: The user's message or voice transcription
            include_actions: Whether to extract suggested actions
            max_tokens: Maximum response length

        Returns:
            Dict with response text and optional suggested actions
        """
        if not self.client:
            return {
                'success': False,
                'response': "I'm sorry, I'm having trouble connecting right now. Please try again in a moment.",
                'error': 'Claude API not available'
            }

        try:
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })

            # Build system prompt with action awareness
            system_prompt = ELDER_ASSISTANT_SYSTEM_PROMPT

            if include_actions:
                system_prompt += """

IMPORTANT: If the user wants to perform an action, include the action type at the end of your response in this format:
[ACTION: action_name]

Available actions:
- [ACTION: send_sms] - when user wants to text someone
- [ACTION: read_emails] - when user wants to check their email
- [ACTION: check_calendar] - when user wants to see their schedule
- [ACTION: call_family] - when user wants to call someone
- [ACTION: emergency] - when user needs urgent help

Only include ONE action per response, and only if the user clearly wants to do that action."""

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=self.conversation_history
            )

            # Extract response text
            assistant_message = response.content[0].text

            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            # Keep history manageable (last 10 exchanges)
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]

            # Extract any suggested action
            suggested_action = None
            clean_response = assistant_message

            if include_actions and '[ACTION:' in assistant_message:
                for action_key in self.ACTIONS.keys():
                    action_tag = f'[ACTION: {action_key}]'
                    if action_tag in assistant_message:
                        suggested_action = action_key
                        clean_response = assistant_message.replace(action_tag, '').strip()
                        break

            return {
                'success': True,
                'response': clean_response,
                'action': suggested_action,
                'action_description': self.ACTIONS.get(suggested_action) if suggested_action else None,
                'raw_response': assistant_message
            }

        except anthropic.APIError as e:
            return {
                'success': False,
                'response': "I'm sorry, I had a little trouble there. Could you say that again?",
                'error': str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'response': "Something went wrong. Let me try again.",
                'error': str(e)
            }

    def get_sms_content(self, recipient_name: str, user_intent: str) -> Dict[str, Any]:
        """
        Help the user compose an SMS message.

        Args:
            recipient_name: Who to send the message to
            user_intent: What the user wants to say

        Returns:
            Dict with suggested message text
        """
        prompt = f"""The user wants to send a text message to {recipient_name}.

Their intent: {user_intent}

Write a friendly, simple text message (max 160 characters) that they can send.
Just provide the message text, nothing else. Keep it warm and simple."""

        response = self.chat(prompt, include_actions=False, max_tokens=200)

        if response['success']:
            return {
                'success': True,
                'message': response['response'].strip('"').strip()
            }
        return {
            'success': False,
            'message': f"Hi {recipient_name}! Hope you're doing well!",
            'error': response.get('error')
        }

    def summarize_email(self, email_subject: str, email_body: str, sender: str) -> Dict[str, Any]:
        """
        Summarize an email in simple terms.

        Args:
            email_subject: Email subject line
            email_body: Email body text
            sender: Who sent the email

        Returns:
            Dict with simple summary
        """
        prompt = f"""Summarize this email in 2-3 simple sentences for an elderly person:

From: {sender}
Subject: {email_subject}

{email_body[:1000]}

Provide a friendly, easy-to-understand summary. Start with "This email is from..."
"""
        response = self.chat(prompt, include_actions=False, max_tokens=300)

        if response['success']:
            return {
                'success': True,
                'summary': response['response']
            }
        return {
            'success': False,
            'summary': f"You have an email from {sender} about: {email_subject}",
            'error': response.get('error')
        }

    def format_calendar_summary(self, events: List[Dict]) -> Dict[str, Any]:
        """
        Format calendar events in a senior-friendly way.

        Args:
            events: List of calendar event dictionaries

        Returns:
            Dict with formatted schedule summary
        """
        if not events:
            return {
                'success': True,
                'summary': "You have no appointments scheduled for today. It's a free day!"
            }

        events_text = "\n".join([
            f"- {e.get('summary', 'Event')} at {e.get('start', {}).get('dateTime', 'sometime')}"
            for e in events[:5]
        ])

        prompt = f"""Format these calendar events as a friendly spoken summary for an elderly person:

{events_text}

Speak naturally, like telling a friend about their day. Mention times in a clear way (like "at two o'clock in the afternoon")."""

        response = self.chat(prompt, include_actions=False, max_tokens=400)

        if response['success']:
            return {
                'success': True,
                'summary': response['response']
            }
        return {
            'success': True,
            'summary': f"You have {len(events)} thing{'s' if len(events) > 1 else ''} on your calendar today."
        }


# CLI testing
if __name__ == "__main__":
    client = ClaudeClient()

    if not client.is_available():
        print("Claude API not available. Check your API key.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("ELDER TECH CONCIERGE - Claude Client Test")
    print("=" * 60 + "\n")

    # Test conversation
    test_messages = [
        "Hello, can you help me send a message to my daughter?",
        "I want to tell her I'm doing fine and thinking of her.",
        "What appointments do I have today?"
    ]

    for msg in test_messages:
        print(f"User: {msg}")
        response = client.chat(msg)
        print(f"Claude: {response['response']}")
        if response.get('action'):
            print(f"  [Suggested Action: {response['action']}]")
        print()
