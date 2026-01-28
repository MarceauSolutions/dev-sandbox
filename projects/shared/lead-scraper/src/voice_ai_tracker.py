"""
Voice AI Call Tracking with Lead Intake Integration

Tracks voice AI calls from Twilio, captures call outcomes, and integrates
with lead intake system for unified lead management.

Features:
- Customer information extraction from transcripts
- Appointment scheduling integration
- Service interest tracking
- Follow-up task creation
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Optional, List, Literal
from datetime import datetime
from dataclasses import dataclass, asdict

from src.lead_intake import LeadIntakeSystem, BusinessID


# Call outcome types
CallOutcome = Literal[
    'appointment_booked',
    'callback_requested',
    'info_only',
    'not_interested',
    'wrong_number',
    'voicemail_left',
    'transferred_to_human'
]


@dataclass
class CustomerInfo:
    """Extracted customer information from voice AI call"""
    name: str = ""
    email: str = ""
    phone: str = ""
    business_name: str = ""
    business_type: str = ""
    service_interested: str = ""
    budget_mentioned: str = ""
    timeline: str = ""
    pain_points: List[str] = None
    preferred_callback_time: str = ""
    notes: str = ""

    def __post_init__(self):
        if self.pain_points is None:
            self.pain_points = []

    def to_dict(self) -> Dict:
        return asdict(self)


class VoiceAITracker:
    """Voice AI call tracking and lead integration with customer info extraction"""

    # Patterns for extracting customer info from transcripts
    NAME_PATTERNS = [
        r"(?:my name is|this is|i'm|i am)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"(?:name[:\s]+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
    ]

    EMAIL_PATTERNS = [
        r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
        r"(?:email is|email[:\s]+)([a-zA-Z0-9._%+-]+\s*(?:at|@)\s*[a-zA-Z0-9.-]+\s*(?:dot|\.)\s*[a-zA-Z]{2,})",
    ]

    BUSINESS_PATTERNS = [
        r"(?:i own|i run|my business is|company is|business called)\s+([A-Z][A-Za-z\s&']+)",
        r"(?:from|with|at)\s+([A-Z][A-Za-z\s&']+?)(?:\s+and|\s+we|\.|,|$)",
    ]

    SERVICE_KEYWORDS = {
        'voice_ai': ['voice ai', 'phone system', 'answering service', 'call handling', 'ai phone', 'missed calls'],
        'website': ['website', 'web design', 'online presence', 'landing page'],
        'automation': ['automation', 'automate', 'workflow', 'crm', 'lead generation'],
        'sms': ['sms', 'text message', 'texting', 'messaging'],
    }

    PAIN_POINT_KEYWORDS = [
        'missing calls', 'can\'t answer', 'too busy', 'after hours', 'losing customers',
        'no website', 'bad reviews', 'need more leads', 'expensive staff', 'overwhelmed'
    ]

    def __init__(self):
        """Initialize voice AI tracker"""
        self.lead_system = LeadIntakeSystem()

        # Track calls separately for reporting
        project_root = Path(__file__).parent.parent
        self.calls_file = project_root / 'output' / 'voice_ai_calls.json'
        self.calls_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_calls()

    def _load_calls(self):
        """Load existing call records"""
        if self.calls_file.exists():
            with open(self.calls_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.calls = data
                else:
                    self.calls = []
        else:
            self.calls = []

    def _save_calls(self):
        """Save call records to file"""
        with open(self.calls_file, 'w') as f:
            json.dump(self.calls, f, indent=2, default=str)

    def _determine_status_from_outcome(self, outcome: CallOutcome) -> str:
        """Determine lead status based on call outcome

        Args:
            outcome: Call outcome

        Returns:
            Lead status
        """
        outcome_to_status = {
            'appointment_booked': 'converted',
            'callback_requested': 'qualified',
            'info_only': 'contacted',
            'not_interested': 'lost',
            'wrong_number': 'lost'
        }
        return outcome_to_status.get(outcome, 'contacted')

    def _determine_priority_from_outcome(self, outcome: CallOutcome) -> str:
        """Determine lead priority based on call outcome

        Args:
            outcome: Call outcome

        Returns:
            Lead priority
        """
        outcome_to_priority = {
            'appointment_booked': 'critical',
            'callback_requested': 'high',
            'info_only': 'medium',
            'not_interested': 'low',
            'wrong_number': 'low'
        }
        return outcome_to_priority.get(outcome, 'medium')

    def _generate_twilio_recording_url(self, account_sid: str, call_sid: str) -> str:
        """Generate Twilio recording URL

        Args:
            account_sid: Twilio account SID
            call_sid: Twilio call SID

        Returns:
            URL to call recording
        """
        return f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls/{call_sid}/Recordings"

    def extract_customer_info(self, transcript: str, caller_phone: str = "") -> CustomerInfo:
        """Extract customer information from call transcript

        Args:
            transcript: Call transcript text
            caller_phone: Caller's phone number

        Returns:
            CustomerInfo object with extracted data
        """
        if not transcript:
            return CustomerInfo(phone=caller_phone)

        transcript_lower = transcript.lower()
        info = CustomerInfo(phone=caller_phone)

        # Extract name
        for pattern in self.NAME_PATTERNS:
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                info.name = match.group(1).strip()
                break

        # Extract email (handle spoken format like "john at gmail dot com")
        for pattern in self.EMAIL_PATTERNS:
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                email = match.group(1)
                # Normalize spoken email format
                email = email.replace(' at ', '@').replace(' dot ', '.')
                email = re.sub(r'\s+', '', email)
                info.email = email.lower()
                break

        # Extract business name
        for pattern in self.BUSINESS_PATTERNS:
            match = re.search(pattern, transcript)
            if match:
                info.business_name = match.group(1).strip()
                break

        # Detect service interest
        services_mentioned = []
        for service, keywords in self.SERVICE_KEYWORDS.items():
            if any(kw in transcript_lower for kw in keywords):
                services_mentioned.append(service)
        if services_mentioned:
            info.service_interested = ', '.join(services_mentioned)

        # Detect pain points
        for pain_point in self.PAIN_POINT_KEYWORDS:
            if pain_point in transcript_lower:
                info.pain_points.append(pain_point)

        # Extract budget mentions
        budget_match = re.search(r'\$[\d,]+(?:\.\d{2})?|\d+\s*(?:dollars|bucks|hundred|thousand)', transcript_lower)
        if budget_match:
            info.budget_mentioned = budget_match.group(0)

        # Extract timeline
        timeline_patterns = [
            r'(?:need it|want it|looking for)\s+(?:by|within|in)\s+([^.]+)',
            r'(?:asap|immediately|urgent|this week|next week|this month)',
        ]
        for pattern in timeline_patterns:
            match = re.search(pattern, transcript_lower)
            if match:
                info.timeline = match.group(0) if match.lastindex is None else match.group(1)
                break

        # Extract callback preferences
        callback_match = re.search(
            r'(?:call me|call back|reach me|available)\s+(?:at|around|after|before)?\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|\w+day)',
            transcript_lower
        )
        if callback_match:
            info.preferred_callback_time = callback_match.group(0)

        return info

    def handle_call_completed(self,
                              call_sid: str,
                              caller_phone: str,
                              business_id: BusinessID,
                              outcome: CallOutcome,
                              call_duration: int = 0,
                              call_transcript: str = None,
                              account_sid: str = None,
                              additional_data: Dict = None,
                              customer_info: Dict = None) -> Dict:
        """Handle completed voice AI call from Twilio webhook

        Args:
            call_sid: Twilio call SID
            caller_phone: Caller's phone number
            business_id: Business that received the call
            outcome: Call outcome (appointment_booked, callback_requested, etc.)
            call_duration: Call duration in seconds
            call_transcript: Optional call transcript
            account_sid: Twilio account SID (for recording URL)
            additional_data: Additional call metadata
            customer_info: Pre-extracted customer info dict (optional)

        Returns:
            Result dict with lead_id, status, and extracted customer info
        """
        # Determine status and priority
        status = self._determine_status_from_outcome(outcome)
        priority = self._determine_priority_from_outcome(outcome)

        # Extract customer info from transcript if not provided
        if customer_info:
            extracted_info = CustomerInfo(**customer_info)
        elif call_transcript:
            extracted_info = self.extract_customer_info(call_transcript, caller_phone)
        else:
            extracted_info = CustomerInfo(phone=caller_phone)

        # Build source detail
        source_detail = {
            'call_sid': call_sid,
            'outcome': outcome,
            'call_duration': call_duration,
            'call_timestamp': datetime.now().isoformat(),
            'customer_info': extracted_info.to_dict()
        }

        # Add recording URL if account_sid provided
        if account_sid:
            source_detail['recording_url'] = self._generate_twilio_recording_url(account_sid, call_sid)

        # Add transcript if available
        if call_transcript:
            source_detail['transcript'] = call_transcript

        # Add any additional data
        if additional_data:
            source_detail.update(additional_data)

        # Build contact info from extracted data
        contact_info = {
            'phone': caller_phone,
            'name': extracted_info.name or 'Voice AI Caller',
            'email': extracted_info.email,
            'business_name': extracted_info.business_name
        }

        # Add lead to intake system
        lead = self.lead_system.add_lead(
            source_channel='voice_ai_call',
            business_id=business_id,
            contact_info=contact_info,
            source_detail=source_detail,
            status=status,
            priority=priority,
            metadata={
                'voice_ai_outcome': outcome,
                'requires_follow_up': outcome in ['appointment_booked', 'callback_requested', 'transferred_to_human'],
                'service_interested': extracted_info.service_interested,
                'pain_points': extracted_info.pain_points,
                'budget_mentioned': extracted_info.budget_mentioned,
                'timeline': extracted_info.timeline,
                'preferred_callback_time': extracted_info.preferred_callback_time
            }
        )

        # Save call record with extracted customer info
        call_record = {
            'call_sid': call_sid,
            'timestamp': datetime.now().isoformat(),
            'caller_phone': caller_phone,
            'caller_name': extracted_info.name,
            'caller_email': extracted_info.email,
            'caller_business': extracted_info.business_name,
            'business_id': business_id,
            'outcome': outcome,
            'call_duration': call_duration,
            'lead_id': lead['lead_id'],
            'status': status,
            'priority': priority,
            'service_interested': extracted_info.service_interested,
            'pain_points': extracted_info.pain_points
        }

        self.calls.append(call_record)
        self._save_calls()

        # Determine if CRM sync should be triggered immediately
        trigger_crm_sync = outcome in ['appointment_booked', 'callback_requested', 'transferred_to_human']

        return {
            'success': True,
            'lead_id': lead['lead_id'],
            'status': status,
            'priority': priority,
            'trigger_crm_sync': trigger_crm_sync,
            'was_duplicate': len(lead.get('touchpoint_history', [])) > 1,
            'customer_info': extracted_info.to_dict(),
            'message': f'Voice AI call processed: {outcome}'
        }

    def get_calls_by_business(self, business_id: BusinessID) -> List[Dict]:
        """Get all calls for a specific business

        Args:
            business_id: Business to filter by

        Returns:
            List of call records
        """
        return [call for call in self.calls if call.get('business_id') == business_id]

    def get_calls_by_outcome(self, outcome: CallOutcome) -> List[Dict]:
        """Get calls by outcome type

        Args:
            outcome: Outcome to filter by

        Returns:
            List of call records
        """
        return [call for call in self.calls if call.get('outcome') == outcome]

    def get_report(self) -> Dict:
        """Generate voice AI call report

        Returns:
            Report dict with call statistics
        """
        total_calls = len(self.calls)

        report = {
            'total_calls': total_calls,
            'by_outcome': {},
            'by_business': {},
            'appointments': 0,
            'callbacks': 0,
            'conversion_rate': 0
        }

        for call in self.calls:
            # Count by outcome
            outcome = call.get('outcome', 'unknown')
            report['by_outcome'][outcome] = report['by_outcome'].get(outcome, 0) + 1

            # Count by business
            business = call.get('business_id', 'unknown')
            report['by_business'][business] = report['by_business'].get(business, 0) + 1

            # Count high-value outcomes
            if outcome == 'appointment_booked':
                report['appointments'] += 1
            elif outcome == 'callback_requested':
                report['callbacks'] += 1

        # Calculate conversion rate (appointments + callbacks / total)
        if total_calls > 0:
            high_value = report['appointments'] + report['callbacks']
            report['conversion_rate'] = round(high_value / total_calls * 100, 1)

        return report


def main():
    """CLI for voice AI tracker"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Voice AI Call Tracker")
    subparsers = parser.add_subparsers(dest='command')

    # Report command
    subparsers.add_parser('report', help='Show voice AI call report')

    # Test command
    test_parser = subparsers.add_parser('test', help='Simulate test call with transcript')
    test_parser.add_argument('--transcript', '-t', help='Call transcript to process')

    # Extract command - test extraction from transcript
    extract_parser = subparsers.add_parser('extract', help='Test customer info extraction from transcript')
    extract_parser.add_argument('transcript', help='Transcript text to extract from')

    # Recent command - show recent calls
    recent_parser = subparsers.add_parser('recent', help='Show recent calls')
    recent_parser.add_argument('--limit', '-n', type=int, default=5, help='Number of calls to show')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    tracker = VoiceAITracker()

    if args.command == 'report':
        report = tracker.get_report()

        print("\n=== VOICE AI CALL REPORT ===\n")
        print(f"Total Calls: {report['total_calls']}")
        print(f"Appointments Booked: {report['appointments']}")
        print(f"Callbacks Requested: {report['callbacks']}")
        print(f"Conversion Rate: {report['conversion_rate']}%")

        if report['by_outcome']:
            print("\nBy Outcome:")
            for outcome, count in sorted(report['by_outcome'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {outcome}: {count}")

        if report['by_business']:
            print("\nBy Business:")
            for business, count in sorted(report['by_business'].items()):
                print(f"  {business}: {count}")

    elif args.command == 'test':
        # Simulate test call with realistic transcript
        transcript = args.transcript or """
        Hi, my name is Sarah Johnson. I own a small yoga studio called Zen Flow Yoga.
        I'm really interested in your voice AI system because we're missing so many calls
        after hours and during classes. My email is sarah@zenflow.com.
        I heard you guys can help with automation and I'd love to know more.
        Can you call me back around 2pm tomorrow? We have a budget of about $500 per month.
        """

        result = tracker.handle_call_completed(
            call_sid='CA' + datetime.now().strftime('%Y%m%d%H%M%S'),
            caller_phone='2395551234',
            business_id='marceau-solutions',
            outcome='callback_requested',
            call_duration=180,
            call_transcript=transcript,
            account_sid=os.getenv('TWILIO_ACCOUNT_SID', 'AC1234567890abcdef')
        )

        print("\n=== TEST CALL PROCESSED ===\n")
        print(json.dumps(result, indent=2))

        # Show extracted info
        print("\n=== EXTRACTED CUSTOMER INFO ===\n")
        for key, value in result.get('customer_info', {}).items():
            if value:
                print(f"  {key}: {value}")

    elif args.command == 'extract':
        # Test extraction only
        info = tracker.extract_customer_info(args.transcript, '2395550000')

        print("\n=== EXTRACTED CUSTOMER INFO ===\n")
        for key, value in info.to_dict().items():
            if value:
                print(f"  {key}: {value}")

    elif args.command == 'recent':
        # Show recent calls
        recent_calls = tracker.calls[-args.limit:] if tracker.calls else []

        print(f"\n=== RECENT {len(recent_calls)} CALLS ===\n")
        for call in reversed(recent_calls):
            print(f"[{call.get('timestamp', 'Unknown')}] {call.get('outcome', 'unknown')}")
            print(f"  Phone: {call.get('caller_phone', 'Unknown')}")
            if call.get('caller_name'):
                print(f"  Name: {call.get('caller_name')}")
            if call.get('caller_business'):
                print(f"  Business: {call.get('caller_business')}")
            if call.get('service_interested'):
                print(f"  Interested in: {call.get('service_interested')}")
            print(f"  Status: {call.get('status')} | Priority: {call.get('priority')}")
            print()

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
