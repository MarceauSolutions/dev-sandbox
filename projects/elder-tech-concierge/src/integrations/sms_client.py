#!/usr/bin/env python3
"""
sms_client.py - Twilio SMS Integration for Elder Tech Concierge

WHAT: Send SMS messages to family members and emergency contacts
WHY: Allow seniors to easily text family without navigating complex UIs
"""

import os
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
except ImportError:
    print("ERROR: twilio package not installed")
    print("Install with: pip install twilio")
    Client = None
    TwilioRestException = Exception

from config import config, Contact


class SMSClient:
    """
    Twilio SMS client for sending messages to family/emergency contacts.

    Features:
    - Simple interface for sending texts
    - Contact lookup by name
    - Message history tracking
    - Emergency broadcast capability
    """

    def __init__(
        self,
        account_sid: str = None,
        auth_token: str = None,
        from_number: str = None
    ):
        """
        Initialize Twilio SMS client.

        Args:
            account_sid: Twilio Account SID (defaults to config)
            auth_token: Twilio Auth Token (defaults to config)
            from_number: Twilio phone number (defaults to config)
        """
        self.account_sid = account_sid or config.twilio_account_sid
        self.auth_token = auth_token or config.twilio_auth_token
        self.from_number = from_number or config.twilio_phone_number

        self.client = None
        if Client and self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)

        # Message history for this session
        self.message_history: List[Dict] = []

    def is_available(self) -> bool:
        """Check if Twilio SMS is available."""
        return self.client is not None and bool(self.from_number)

    def format_phone(self, phone: str) -> Optional[str]:
        """
        Format phone number to E.164 format.

        Args:
            phone: Phone number in various formats

        Returns:
            E.164 formatted phone number or None if invalid
        """
        # Remove all non-numeric characters except +
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')

        # Add +1 for US numbers if not present
        if not cleaned.startswith('+'):
            if len(cleaned) == 10:
                cleaned = '+1' + cleaned
            elif len(cleaned) == 11 and cleaned.startswith('1'):
                cleaned = '+' + cleaned
            else:
                return None

        # Validate length
        if len(cleaned) < 11 or len(cleaned) > 15:
            return None

        return cleaned

    def find_contact_by_name(self, name: str) -> Optional[Contact]:
        """
        Find a contact by name (case-insensitive, partial match).

        Args:
            name: Name to search for

        Returns:
            Contact object if found, None otherwise
        """
        name_lower = name.lower().strip()
        all_contacts = config.get_all_contacts()

        # Try exact match first
        for contact in all_contacts:
            if contact.name.lower() == name_lower:
                return contact

        # Try partial match
        for contact in all_contacts:
            if name_lower in contact.name.lower():
                return contact

        # Try relationship match (e.g., "daughter", "son")
        for contact in all_contacts:
            if name_lower in contact.relationship.lower():
                return contact

        return None

    def send_message(
        self,
        to: str,
        message: str,
        contact_name: str = None
    ) -> Dict[str, Any]:
        """
        Send an SMS message.

        Args:
            to: Phone number (E.164 format) or contact name
            message: Message text
            contact_name: Optional contact name for logging

        Returns:
            Dict with success status and message details
        """
        if not self.client:
            return {
                'success': False,
                'error': 'SMS service not available. Please check configuration.',
                'spoken_response': "I'm sorry, I can't send text messages right now. The text service isn't set up."
            }

        # Check if 'to' is a name and find the contact
        to_number = self.format_phone(to)
        recipient_name = contact_name

        if not to_number:
            # Try to find contact by name
            contact = self.find_contact_by_name(to)
            if contact:
                to_number = self.format_phone(contact.phone)
                recipient_name = contact.name
            else:
                return {
                    'success': False,
                    'error': f"Could not find contact: {to}",
                    'spoken_response': f"I couldn't find {to} in your contacts. Would you like to try a different name?"
                }

        if not to_number:
            return {
                'success': False,
                'error': 'Invalid phone number',
                'spoken_response': "That phone number doesn't look right. Could you check it and try again?"
            }

        try:
            # Send the SMS
            sms = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )

            # Log the message
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'to': to_number,
                'to_name': recipient_name,
                'message': message,
                'sid': sms.sid,
                'status': sms.status
            }
            self.message_history.append(log_entry)

            spoken_name = recipient_name or "your contact"
            return {
                'success': True,
                'message_sid': sms.sid,
                'status': sms.status,
                'to': to_number,
                'to_name': recipient_name,
                'spoken_response': f"Great! I've sent your message to {spoken_name}. They should receive it any moment now."
            }

        except TwilioRestException as e:
            return {
                'success': False,
                'error': str(e.msg) if hasattr(e, 'msg') else str(e),
                'spoken_response': "I had trouble sending that message. Would you like me to try again?"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'spoken_response': "Something went wrong sending the message. Let's try again."
            }

    def send_to_contact(
        self,
        contact: Contact,
        message: str
    ) -> Dict[str, Any]:
        """
        Send SMS to a specific Contact object.

        Args:
            contact: Contact object
            message: Message text

        Returns:
            Dict with success status and details
        """
        return self.send_message(
            to=contact.phone,
            message=message,
            contact_name=contact.name
        )

    def send_emergency_alert(
        self,
        message: str = None
    ) -> Dict[str, Any]:
        """
        Send emergency alert to all emergency contacts.

        Args:
            message: Optional custom message (defaults to emergency template)

        Returns:
            Dict with results for each contact
        """
        if not message:
            message = (
                "URGENT: This is an automated alert from your family member's "
                "Elder Tech Assistant. They may need immediate assistance. "
                "Please call or check on them as soon as possible."
            )

        emergency_contacts = config.emergency_contacts
        if not emergency_contacts:
            return {
                'success': False,
                'error': 'No emergency contacts configured',
                'spoken_response': "I don't have any emergency contacts saved. Would you like me to call 911 instead?"
            }

        results = {
            'success': True,
            'sent_to': [],
            'failed': [],
            'spoken_response': ''
        }

        for contact in emergency_contacts:
            result = self.send_to_contact(contact, message)
            if result['success']:
                results['sent_to'].append(contact.name)
            else:
                results['failed'].append(contact.name)

        if results['sent_to']:
            names = ', '.join(results['sent_to'])
            results['spoken_response'] = f"I've sent an emergency alert to: {names}. Help is on the way."
        else:
            results['success'] = False
            results['spoken_response'] = "I couldn't send the emergency alert. Would you like me to call 911?"

        return results

    def get_recent_messages(self, limit: int = 5) -> List[Dict]:
        """Get recent messages sent this session."""
        return self.message_history[-limit:]

    def list_contacts(self) -> Dict[str, Any]:
        """
        Get list of available contacts for sending messages.

        Returns:
            Dict with family and emergency contacts
        """
        return {
            'family': [
                {'name': c.name, 'relationship': c.relationship}
                for c in config.family_contacts
            ],
            'emergency': [
                {'name': c.name, 'relationship': c.relationship}
                for c in config.emergency_contacts
            ],
            'spoken_response': self._format_contacts_spoken()
        }

    def _format_contacts_spoken(self) -> str:
        """Format contacts list for voice output."""
        family = config.family_contacts
        emergency = config.emergency_contacts

        if not family and not emergency:
            return "You don't have any contacts saved yet."

        parts = []
        if family:
            names = ', '.join([c.name for c in family[:3]])
            if len(family) > 3:
                names += f', and {len(family) - 3} more'
            parts.append(f"Your family contacts include: {names}")

        if emergency:
            names = ', '.join([c.name for c in emergency])
            parts.append(f"Your emergency contacts are: {names}")

        return '. '.join(parts)


# CLI testing
if __name__ == "__main__":
    client = SMSClient()

    print("\n" + "=" * 60)
    print("ELDER TECH CONCIERGE - SMS Client Test")
    print("=" * 60 + "\n")

    if not client.is_available():
        print("SMS service not available. Check your Twilio configuration.")
        sys.exit(1)

    print("SMS service is available!")
    print("\nConfigured contacts:")
    contacts = client.list_contacts()
    print(f"  Family: {contacts['family']}")
    print(f"  Emergency: {contacts['emergency']}")
    print(f"\n{contacts['spoken_response']}")
