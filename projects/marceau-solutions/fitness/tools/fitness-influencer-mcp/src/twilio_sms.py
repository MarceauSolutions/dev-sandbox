#!/usr/bin/env python3
"""
twilio_sms.py - SMS Messaging via Twilio

WHAT: Send SMS messages for lead nurturing and notifications
WHY: Engage leads with personalized text messages, confirmations, and follow-ups
INPUT: Phone number, message text, optional template
OUTPUT: Message SID and delivery status
COST: ~$0.0079 per SMS (US toll-free)

QUICK USAGE:
  python twilio_sms.py --to "+15551234567" --message "Welcome to Marceau Solutions!"
  python twilio_sms.py --to "+15551234567" --template welcome --name "John"

CAPABILITIES:
  • Send individual SMS messages
  • Use message templates for consistency
  • Track delivery status
  • Batch messaging for campaigns
  • Webhook support for responses

DEPENDENCIES: twilio
API_KEYS: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
"""

import os
import sys
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
except ImportError:
    print("ERROR: twilio package not installed")
    print("Install with: pip install twilio")
    sys.exit(1)

load_dotenv()


class TwilioSMS:
    """
    Send SMS messages via Twilio API for lead nurturing.
    
    Features:
    - Individual and batch messaging
    - Template-based messages
    - Delivery tracking
    - Cost monitoring
    """
    
    # Message templates for lead nurturing
    TEMPLATES = {
        "welcome": (
            "Hi {name}! 👋 Thanks for signing up for Marceau Solutions Fitness "
            "Influencer AI. We're excited to help you grow your fitness business! "
            "Check your email for next steps. Reply STOP to opt out."
        ),
        "followup_1": (
            "Hey {name}! Just checking in from Marceau Solutions. Did you get a "
            "chance to explore your AI assistant? We'd love to hear your feedback. "
            "Reply with any questions!"
        ),
        "followup_2": (
            "Hi {name}, your Fitness AI assistant is ready to create amazing "
            "content! Try asking it to generate a workout video or social media "
            "graphic. Need help? Just reply!"
        ),
        "feature_highlight": (
            "{name}, did you know your AI can automatically edit videos with "
            "jump cuts? Upload a raw video and watch the magic happen! ✨ "
            "Questions? Reply here."
        ),
        "appointment_reminder": (
            "Hi {name}! Just a reminder about your scheduled call with Marceau "
            "Solutions tomorrow at {time}. Looking forward to chatting! "
            "Reply to reschedule."
        ),
        "new_inquiry": (
            "Thanks for your interest in a custom AI assistant, {name}! "
            "We've received your inquiry and will reach out within 24 hours. "
            "In the meantime, check out marceausolutions.com/ai"
        ),
        "custom_project": (
            "Hi {name}! Thanks for submitting your custom AI project request. "
            "Our team is reviewing your requirements for: {project_type}. "
            "We'll be in touch soon!"
        )
    }
    
    def __init__(self):
        """Initialize Twilio client."""
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not all([self.account_sid, self.auth_token, self.from_number]):
            raise ValueError(
                "Missing Twilio credentials. Set TWILIO_ACCOUNT_SID, "
                "TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER in .env"
            )
        
        self.client = Client(self.account_sid, self.auth_token)
        self.messages_sent = 0
        
        # Log directory for message tracking
        self.log_dir = Path(".tmp/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "sms_log.jsonl"
    
    def send_message(
        self,
        to: str,
        message: str = "",
        template: str = None,
        template_vars: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Send an SMS message.
        
        Args:
            to: Phone number to send to (E.164 format: +1XXXXXXXXXX)
            message: Message text (ignored if template is provided)
            template: Template name from TEMPLATES
            template_vars: Variables to substitute in template
            
        Returns:
            Dict with message_sid, status, and delivery info
        """
        print(f"\n{'='*70}")
        print("TWILIO SMS")
        print(f"{'='*70}")
        
        # Format phone number
        to = self._format_phone(to)
        if not to:
            return {"success": False, "error": "Invalid phone number"}
        
        # Use template if specified
        if template:
            if template not in self.TEMPLATES:
                return {
                    "success": False,
                    "error": f"Unknown template: {template}",
                    "available_templates": list(self.TEMPLATES.keys())
                }
            
            template_vars = template_vars or {}
            message = self.TEMPLATES[template].format(**template_vars)
        
        print(f"To: {to}")
        print(f"From: {self.from_number}")
        print(f"Message: {message[:80]}{'...' if len(message) > 80 else ''}")
        
        try:
            # Send SMS
            sms = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to
            )
            
            self.messages_sent += 1
            
            # Log the message
            self._log_message(to, message, sms.sid, sms.status, template)
            
            print(f"\n✓ Message sent!")
            print(f"  SID: {sms.sid}")
            print(f"  Status: {sms.status}")
            print(f"  Cost: ~$0.0079")
            
            return {
                "success": True,
                "message_sid": sms.sid,
                "status": sms.status,
                "to": to,
                "from": self.from_number,
                "cost": 0.0079
            }
            
        except TwilioRestException as e:
            print(f"\n✗ Twilio Error: {e.msg}")
            return {
                "success": False,
                "error": str(e.msg),
                "code": e.code
            }
        except Exception as e:
            print(f"\n✗ Error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_batch(
        self,
        recipients: List[Dict[str, str]],
        template: str,
        delay_seconds: float = 1.0
    ) -> Dict[str, Any]:
        """
        Send batch SMS messages using a template.
        
        Args:
            recipients: List of dicts with 'phone' and template variable keys
            template: Template name to use
            delay_seconds: Delay between messages (rate limiting)
            
        Returns:
            Dict with results for each recipient
        """
        import time
        
        print(f"\n{'='*70}")
        print(f"BATCH SMS - {len(recipients)} recipients")
        print(f"{'='*70}")
        
        results = {
            "total": len(recipients),
            "sent": 0,
            "failed": 0,
            "results": []
        }
        
        for i, recipient in enumerate(recipients, 1):
            print(f"\n[{i}/{len(recipients)}] Sending to {recipient.get('phone', 'unknown')}...")
            
            phone = recipient.pop('phone', None)
            if not phone:
                results["failed"] += 1
                results["results"].append({
                    "success": False,
                    "error": "No phone number"
                })
                continue
            
            result = self.send_message(
                to=phone,
                message="",
                template=template,
                template_vars=recipient
            )
            
            results["results"].append(result)
            if result.get("success"):
                results["sent"] += 1
            else:
                results["failed"] += 1
            
            # Rate limiting
            if i < len(recipients):
                time.sleep(delay_seconds)
        
        print(f"\n{'='*70}")
        print(f"BATCH COMPLETE: {results['sent']}/{results['total']} sent")
        print(f"{'='*70}")
        
        return results
    
    def get_message_status(self, message_sid: str) -> Dict[str, Any]:
        """
        Get status of a sent message.
        
        Args:
            message_sid: Message SID from send_message
            
        Returns:
            Dict with message status and details
        """
        try:
            message = self.client.messages(message_sid).fetch()
            
            return {
                "success": True,
                "sid": message.sid,
                "status": message.status,
                "date_sent": str(message.date_sent),
                "direction": message.direction,
                "error_code": message.error_code,
                "error_message": message.error_message,
                "price": message.price,
                "price_unit": message.price_unit
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_phone(self, phone: str) -> Optional[str]:
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
            if len(cleaned) == 10:  # US number without country code
                cleaned = '+1' + cleaned
            elif len(cleaned) == 11 and cleaned.startswith('1'):
                cleaned = '+' + cleaned
            else:
                return None
        
        # Validate length
        if len(cleaned) < 11 or len(cleaned) > 15:
            return None
        
        return cleaned
    
    def _log_message(
        self,
        to: str,
        message: str,
        sid: str,
        status: str,
        template: str = None
    ):
        """Log sent message to JSONL file."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "to": to,
            "message": message[:100] + "..." if len(message) > 100 else message,
            "sid": sid,
            "status": status,
            "template": template
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def list_templates(self):
        """Print available message templates."""
        print(f"\n{'='*70}")
        print("AVAILABLE SMS TEMPLATES")
        print(f"{'='*70}\n")
        
        for name, template in self.TEMPLATES.items():
            print(f"📝 {name}")
            print(f"   {template[:80]}...")
            print()


def main():
    """CLI for Twilio SMS."""
    parser = argparse.ArgumentParser(
        description="Send SMS messages via Twilio for lead nurturing"
    )
    
    parser.add_argument('--to', help='Phone number to send to')
    parser.add_argument('--message', help='Message text')
    parser.add_argument('--template', help='Template name to use')
    parser.add_argument('--name', help='Recipient name (for templates)')
    parser.add_argument('--time', help='Time (for appointment template)')
    parser.add_argument('--project_type', help='Project type (for custom_project template)')
    parser.add_argument('--list-templates', action='store_true', help='List available templates')
    parser.add_argument('--status', help='Check status of message SID')
    
    args = parser.parse_args()
    
    try:
        sms = TwilioSMS()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # List templates
    if args.list_templates:
        sms.list_templates()
        sys.exit(0)
    
    # Check message status
    if args.status:
        result = sms.get_message_status(args.status)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get("success") else 1)
    
    # Send message
    if not args.to:
        print("Error: --to phone number required")
        sys.exit(1)
    
    if not args.message and not args.template:
        print("Error: --message or --template required")
        sys.exit(1)
    
    # Build template variables
    template_vars = {}
    if args.name:
        template_vars['name'] = args.name
    if args.time:
        template_vars['time'] = args.time
    if args.project_type:
        template_vars['project_type'] = args.project_type
    
    result = sms.send_message(
        to=args.to,
        message=args.message or "",
        template=args.template,
        template_vars=template_vars
    )
    
    if result.get("success"):
        print("\n✓ Success!")
        sys.exit(0)
    else:
        print(f"\n✗ Failed: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
