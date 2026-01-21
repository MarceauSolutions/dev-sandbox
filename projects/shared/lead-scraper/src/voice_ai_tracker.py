"""
Voice AI Call Tracking with Lead Intake Integration

Tracks voice AI calls from Twilio, captures call outcomes, and integrates
with lead intake system for unified lead management.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, List, Literal
from datetime import datetime

from src.lead_intake import LeadIntakeSystem, BusinessID


# Call outcome types
CallOutcome = Literal[
    'appointment_booked',
    'callback_requested',
    'info_only',
    'not_interested',
    'wrong_number'
]


class VoiceAITracker:
    """Voice AI call tracking and lead integration"""

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

    def handle_call_completed(self,
                              call_sid: str,
                              caller_phone: str,
                              business_id: BusinessID,
                              outcome: CallOutcome,
                              call_duration: int = 0,
                              call_transcript: str = None,
                              account_sid: str = None,
                              additional_data: Dict = None) -> Dict:
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

        Returns:
            Result dict with lead_id and status
        """
        # Determine status and priority
        status = self._determine_status_from_outcome(outcome)
        priority = self._determine_priority_from_outcome(outcome)

        # Build source detail
        source_detail = {
            'call_sid': call_sid,
            'outcome': outcome,
            'call_duration': call_duration,
            'call_timestamp': datetime.now().isoformat()
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

        # Add lead to intake system
        lead = self.lead_system.add_lead(
            source_channel='voice_ai_call',
            business_id=business_id,
            contact_info={
                'phone': caller_phone,
                'name': 'Voice AI Caller'  # Can be updated later from transcript
            },
            source_detail=source_detail,
            status=status,
            priority=priority,
            metadata={
                'voice_ai_outcome': outcome,
                'requires_follow_up': outcome in ['appointment_booked', 'callback_requested']
            }
        )

        # Save call record
        call_record = {
            'call_sid': call_sid,
            'timestamp': datetime.now().isoformat(),
            'caller_phone': caller_phone,
            'business_id': business_id,
            'outcome': outcome,
            'call_duration': call_duration,
            'lead_id': lead['lead_id'],
            'status': status,
            'priority': priority
        }

        self.calls.append(call_record)
        self._save_calls()

        # Determine if CRM sync should be triggered immediately
        trigger_crm_sync = outcome in ['appointment_booked', 'callback_requested']

        return {
            'success': True,
            'lead_id': lead['lead_id'],
            'status': status,
            'priority': priority,
            'trigger_crm_sync': trigger_crm_sync,
            'was_duplicate': len(lead.get('touchpoint_history', [])) > 1,
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

    if len(sys.argv) < 2:
        print("Usage: python -m src.voice_ai_tracker <command>")
        print("\nCommands:")
        print("  report              - Show voice AI call report")
        print("  test                - Simulate test call")
        sys.exit(1)

    command = sys.argv[1]
    tracker = VoiceAITracker()

    if command == 'report':
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

    elif command == 'test':
        # Simulate test call
        result = tracker.handle_call_completed(
            call_sid='CA1234567890abcdef',
            caller_phone='2393334444',
            business_id='marceau-solutions',
            outcome='appointment_booked',
            call_duration=180,
            call_transcript='Customer wants to schedule website consultation for next Tuesday',
            account_sid='AC1234567890abcdef'
        )

        print("\n=== TEST CALL PROCESSED ===\n")
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
