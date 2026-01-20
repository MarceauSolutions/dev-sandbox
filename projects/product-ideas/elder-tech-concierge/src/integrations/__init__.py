"""
Elder Tech Concierge - Integrations Package

This package contains client wrappers for external services:
- Claude AI for conversation
- Twilio for SMS messaging
- Gmail for email reading
- Google Calendar for schedule
"""

from .claude_client import ClaudeClient
from .sms_client import SMSClient
from .email_client import EmailClient
from .calendar_client import CalendarClient

__all__ = ['ClaudeClient', 'SMSClient', 'EmailClient', 'CalendarClient']
