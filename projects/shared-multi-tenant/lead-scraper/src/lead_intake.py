"""
Unified Lead Intake System with Source Attribution

Captures ALL lead sources (form submissions, voice AI calls, SMS replies,
social media engagement) with comprehensive source tracking and deduplication.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List, Literal
import uuid

# Type definitions
SourceChannel = Literal[
    'form_submission',
    'voice_ai_call',
    'sms_reply',
    'social_media_click',
    'direct_inquiry',
    'referral'
]

LeadStatus = Literal[
    'new',
    'contacted',
    'qualified',
    'converted',
    'won',
    'lost'
]

BusinessID = Literal[
    'marceau-solutions',
    'swflorida-hvac',
    'shipping-logistics'
]


class LeadIntakeSystem:
    """Centralized lead intake with source attribution and deduplication"""

    def __init__(self, data_file: str = None):
        """Initialize lead intake system

        Args:
            data_file: Path to lead_intake.json (default: output/lead_intake.json)
        """
        if data_file is None:
            project_root = Path(__file__).parent.parent
            self.data_file = project_root / 'output' / 'lead_intake.json'
        else:
            self.data_file = Path(data_file)

        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_leads()

    def _load_leads(self):
        """Load existing leads from JSON file"""
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                self.leads = json.load(f)
        else:
            self.leads = []

    def _save_leads(self):
        """Save leads to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.leads, f, indent=2, default=str)

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number to +1XXXXXXXXXX format

        Args:
            phone: Phone number in any format

        Returns:
            Normalized phone number
        """
        if not phone:
            return ""

        # Remove all non-digit characters
        digits = ''.join(c for c in phone if c.isdigit())

        # Add country code if missing
        if len(digits) == 10:
            digits = '1' + digits

        return '+' + digits

    def _normalize_email(self, email: str) -> str:
        """Normalize email to lowercase, trimmed format

        Args:
            email: Email address

        Returns:
            Normalized email
        """
        if not email:
            return ""
        return email.lower().strip()

    def _find_duplicate(self, phone: str = None, email: str = None,
                       business_id: str = None) -> Optional[Dict]:
        """Find duplicate lead within 30-day window

        Args:
            phone: Phone number to check
            email: Email address to check
            business_id: Business to check within (optional - if None, checks all)

        Returns:
            Existing lead dict if duplicate found, None otherwise
        """
        if not phone and not email:
            return None

        phone_normalized = self._normalize_phone(phone) if phone else None
        email_normalized = self._normalize_email(email) if email else None

        # 30-day window
        cutoff_date = datetime.now() - timedelta(days=30)

        for lead in self.leads:
            # Check if within time window
            lead_date = datetime.fromisoformat(lead['timestamp'])
            if lead_date < cutoff_date:
                continue

            # Check if same business (if specified)
            if business_id and lead.get('business_id') != business_id:
                continue

            # Check phone match
            if phone_normalized and lead.get('contact_info', {}).get('phone') == phone_normalized:
                return lead

            # Check email match
            if email_normalized and lead.get('contact_info', {}).get('email') == email_normalized:
                return lead

        return None

    def add_lead(self,
                 source_channel: SourceChannel,
                 business_id: BusinessID,
                 contact_info: Dict[str, str],
                 source_detail: Dict = None,
                 status: LeadStatus = 'new',
                 priority: str = 'medium',
                 metadata: Dict = None) -> Dict:
        """Add a new lead or update existing lead with new touchpoint

        Args:
            source_channel: One of form_submission, voice_ai_call, sms_reply,
                          social_media_click, direct_inquiry, referral
            business_id: Which business this lead is for
            contact_info: Dict with name, phone, email (at least one required)
            source_detail: Channel-specific details (UTM params, campaign_id, call_sid, etc)
            status: Lead status (default: new)
            priority: Lead priority (low, medium, high, critical)
            metadata: Additional metadata to store with lead

        Returns:
            Lead dict (newly created or updated existing)
        """
        # Normalize contact info
        phone = contact_info.get('phone')
        email = contact_info.get('email')
        name = contact_info.get('name', 'Unknown')

        if phone:
            contact_info['phone'] = self._normalize_phone(phone)
        if email:
            contact_info['email'] = self._normalize_email(email)

        # Check for duplicate
        existing_lead = self._find_duplicate(
            phone=contact_info.get('phone'),
            email=contact_info.get('email'),
            business_id=business_id
        )

        if existing_lead:
            # Update existing lead with new touchpoint
            touchpoint = {
                'timestamp': datetime.now().isoformat(),
                'source_channel': source_channel,
                'source_detail': source_detail or {},
                'status': status
            }

            if 'touchpoint_history' not in existing_lead:
                existing_lead['touchpoint_history'] = []

            existing_lead['touchpoint_history'].append(touchpoint)
            existing_lead['last_contact'] = datetime.now().isoformat()

            # Update status if higher priority
            status_hierarchy = ['new', 'contacted', 'qualified', 'converted', 'won', 'lost']
            if status_hierarchy.index(status) > status_hierarchy.index(existing_lead['status']):
                existing_lead['status'] = status

            # Update priority if higher
            priority_hierarchy = ['low', 'medium', 'high', 'critical']
            current_priority = existing_lead.get('priority', 'medium')
            if priority_hierarchy.index(priority) > priority_hierarchy.index(current_priority):
                existing_lead['priority'] = priority

            self._save_leads()
            return existing_lead

        # Create new lead
        lead = {
            'lead_id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'last_contact': datetime.now().isoformat(),
            'business_id': business_id,
            'source_channel': source_channel,
            'source_detail': source_detail or {},
            'contact_info': contact_info,
            'status': status,
            'priority': priority,
            'crm_synced': False,
            'crm_sync_timestamp': None,
            'touchpoint_history': [
                {
                    'timestamp': datetime.now().isoformat(),
                    'source_channel': source_channel,
                    'source_detail': source_detail or {},
                    'status': status
                }
            ],
            'metadata': metadata or {}
        }

        self.leads.append(lead)
        self._save_leads()
        return lead

    def update_lead_status(self, lead_id: str, status: LeadStatus,
                          notes: str = None) -> Optional[Dict]:
        """Update lead status

        Args:
            lead_id: UUID of lead to update
            status: New status
            notes: Optional notes about status change

        Returns:
            Updated lead dict or None if not found
        """
        for lead in self.leads:
            if lead['lead_id'] == lead_id:
                lead['status'] = status
                lead['last_contact'] = datetime.now().isoformat()

                if notes:
                    if 'notes' not in lead:
                        lead['notes'] = []
                    lead['notes'].append({
                        'timestamp': datetime.now().isoformat(),
                        'note': notes
                    })

                self._save_leads()
                return lead

        return None

    def mark_crm_synced(self, lead_id: str, crm_task_id: str = None):
        """Mark lead as synced to CRM

        Args:
            lead_id: UUID of lead
            crm_task_id: CRM task ID (e.g., ClickUp task ID)
        """
        for lead in self.leads:
            if lead['lead_id'] == lead_id:
                lead['crm_synced'] = True
                lead['crm_sync_timestamp'] = datetime.now().isoformat()
                if crm_task_id:
                    lead['crm_task_id'] = crm_task_id
                break

        self._save_leads()

    def get_leads_by_business(self, business_id: BusinessID) -> List[Dict]:
        """Get all leads for a specific business

        Args:
            business_id: Business to filter by

        Returns:
            List of lead dicts
        """
        return [lead for lead in self.leads if lead['business_id'] == business_id]

    def get_leads_by_status(self, status: LeadStatus) -> List[Dict]:
        """Get all leads with specific status

        Args:
            status: Status to filter by

        Returns:
            List of lead dicts
        """
        return [lead for lead in self.leads if lead['status'] == status]

    def get_leads_by_source(self, source_channel: SourceChannel) -> List[Dict]:
        """Get all leads from specific source channel

        Args:
            source_channel: Source to filter by

        Returns:
            List of lead dicts
        """
        return [lead for lead in self.leads if lead['source_channel'] == source_channel]

    def get_unsynced_leads(self, priority: str = None) -> List[Dict]:
        """Get leads not yet synced to CRM

        Args:
            priority: Optional priority filter (e.g., 'high' for hot leads)

        Returns:
            List of lead dicts
        """
        unsynced = [lead for lead in self.leads if not lead.get('crm_synced', False)]

        if priority:
            unsynced = [lead for lead in unsynced if lead.get('priority') == priority]

        return unsynced

    def get_stats(self) -> Dict:
        """Get overall lead statistics

        Returns:
            Dict with lead counts by source, status, business
        """
        stats = {
            'total_leads': len(self.leads),
            'by_source': {},
            'by_status': {},
            'by_business': {},
            'by_priority': {},
            'crm_sync_rate': 0
        }

        for lead in self.leads:
            # Count by source
            source = lead['source_channel']
            stats['by_source'][source] = stats['by_source'].get(source, 0) + 1

            # Count by status
            status = lead['status']
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1

            # Count by business
            business = lead['business_id']
            stats['by_business'][business] = stats['by_business'].get(business, 0) + 1

            # Count by priority
            priority = lead.get('priority', 'medium')
            stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1

        # Calculate CRM sync rate
        synced = len([l for l in self.leads if l.get('crm_synced', False)])
        if len(self.leads) > 0:
            stats['crm_sync_rate'] = round(synced / len(self.leads) * 100, 1)

        return stats


def main():
    """CLI for lead intake system"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.lead_intake <command>")
        print("\nCommands:")
        print("  stats              - Show lead statistics")
        print("  list [status]      - List all leads (optionally filter by status)")
        print("  test               - Add test lead")
        sys.exit(1)

    command = sys.argv[1]
    system = LeadIntakeSystem()

    if command == 'stats':
        stats = system.get_stats()
        print("\n=== LEAD INTAKE STATISTICS ===\n")
        print(f"Total Leads: {stats['total_leads']}")
        print(f"CRM Sync Rate: {stats['crm_sync_rate']}%")

        print("\nBy Source:")
        for source, count in sorted(stats['by_source'].items()):
            print(f"  {source}: {count}")

        print("\nBy Status:")
        for status, count in sorted(stats['by_status'].items()):
            print(f"  {status}: {count}")

        print("\nBy Business:")
        for business, count in sorted(stats['by_business'].items()):
            print(f"  {business}: {count}")

        print("\nBy Priority:")
        for priority, count in sorted(stats['by_priority'].items()):
            print(f"  {priority}: {count}")

    elif command == 'list':
        status_filter = sys.argv[2] if len(sys.argv) > 2 else None

        if status_filter:
            leads = system.get_leads_by_status(status_filter)
            print(f"\n=== LEADS WITH STATUS: {status_filter.upper()} ===\n")
        else:
            leads = system.leads
            print("\n=== ALL LEADS ===\n")

        for lead in leads:
            contact = lead['contact_info']
            print(f"ID: {lead['lead_id'][:8]}...")
            print(f"  Business: {lead['business_id']}")
            print(f"  Contact: {contact.get('name', 'Unknown')} - {contact.get('phone', 'N/A')} - {contact.get('email', 'N/A')}")
            print(f"  Source: {lead['source_channel']}")
            print(f"  Status: {lead['status']} | Priority: {lead.get('priority', 'medium')}")
            print(f"  CRM Synced: {'Yes' if lead.get('crm_synced') else 'No'}")
            print(f"  Touchpoints: {len(lead.get('touchpoint_history', []))}")
            print()

    elif command == 'test':
        # Add test lead
        lead = system.add_lead(
            source_channel='form_submission',
            business_id='marceau-solutions',
            contact_info={
                'name': 'Test Lead',
                'phone': '2393334444',
                'email': 'test@example.com'
            },
            source_detail={
                'utm_source': 'sms',
                'utm_campaign': 'test_campaign',
                'utm_content': 'intro'
            },
            priority='high'
        )
        print(f"\nCreated test lead: {lead['lead_id']}")
        print(json.dumps(lead, indent=2, default=str))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
