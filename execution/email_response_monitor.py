"""
Unified Email Response Monitoring System

Monitors Gmail inbox for responses to outreach emails across all projects:
- Elder Tech iPad procurement inquiries
- HVAC distributor RFQs
- Fitness Influencer cold outreach
- Website Builder cold outreach
- Lead Scraper campaigns

Uses Gmail API to:
1. Monitor for new emails matching inquiry/campaign reference IDs
2. Categorize responses (quote, question, rejection, auto-reply)
3. Update tracking records
4. Generate notifications/digests
"""

import os
import re
import json
import logging
import base64
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field, asdict
from email.utils import parsedate_to_datetime

logger = logging.getLogger(__name__)


@dataclass
class EmailResponse:
    """Represents an incoming email response."""
    message_id: str
    thread_id: str
    from_email: str
    from_name: str
    to_email: str
    subject: str
    body_preview: str
    received_at: datetime

    # Classification
    project: str = ""  # elder-tech, hvac, fitness, website-builder, lead-scraper
    inquiry_id: str = ""  # Reference ID extracted from subject/body
    response_type: str = ""  # quote, question, rejection, auto-reply, other

    # Status
    processed: bool = False
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['received_at'] = self.received_at.isoformat() if self.received_at else None
        return d


@dataclass
class OutreachTracking:
    """Tracks outreach status for a single inquiry/campaign."""
    id: str
    project: str
    recipient_email: str
    recipient_name: str
    subject: str
    sent_at: datetime

    # Tracking
    status: str = "sent"  # sent, responded, no_response, bounced
    response_received: bool = False
    response_at: Optional[datetime] = None
    response_type: str = ""
    follow_up_count: int = 0
    last_follow_up: Optional[datetime] = None

    # Context
    inquiry_type: str = ""  # bulk_pricing, rfq, cold_outreach
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['sent_at'] = self.sent_at.isoformat() if self.sent_at else None
        d['response_at'] = self.response_at.isoformat() if self.response_at else None
        d['last_follow_up'] = self.last_follow_up.isoformat() if self.last_follow_up else None
        return d


class EmailResponseMonitor:
    """
    Monitors Gmail inbox for responses to outreach emails.

    Works with Gmail API (when available) or can be run manually
    by checking inbox and pasting email content.
    """

    # Project detection patterns
    PROJECT_PATTERNS = {
        'elder-tech': [
            r'inquiry[- ]#?([a-f0-9]{8})',
            r'bulk pricing inquiry',
            r'elder tech',
            r'tablet.*procurement',
            r'ipad.*inquiry',
        ],
        'hvac': [
            r'rfq[- ]#?([a-f0-9]{8})',
            r'hvac.*quote',
            r'equipment.*quote',
            r'carrier|trane|lennox|daikin',
        ],
        'fitness': [
            r'fitness.*influencer',
            r'fitness.*assistant',
            r'gym.*members',
            r'workout.*plan',
        ],
        'website-builder': [
            r'website.*mockup',
            r'online.*presence',
            r'web.*design',
        ],
        'lead-scraper': [
            r'marketing.*audit',
            r'5-star.*reviews',
            r'online.*booking',
        ],
    }

    # Response type patterns
    RESPONSE_PATTERNS = {
        'quote': [
            r'quote',
            r'pricing',
            r'\$\d+',
            r'per unit',
            r'cost.*is',
            r'price.*is',
            r'wholesale.*price',
            r'bulk.*discount',
            r'availability',
            r'in stock',
            r'lead time',
            r'delivery',
        ],
        'question': [
            r'\?$',
            r'can you',
            r'could you',
            r'what.*is',
            r'how.*much',
            r'more.*information',
            r'clarify',
            r'details',
        ],
        'rejection': [
            r'not interested',
            r'no thank',
            r'unsubscribe',
            r'remove.*from',
            r'stop.*email',
            r'don\'t contact',
            r'not.*time',
            r'out of stock',
            r'discontinued',
        ],
        'auto-reply': [
            r'out of office',
            r'automatic.*reply',
            r'auto.*response',
            r'away from.*desk',
            r'currently.*unavailable',
            r'will.*respond.*soon',
            r'thank.*for.*email',
            r'received.*your.*message',
        ],
    }

    def __init__(self, data_dir: str = None):
        """Initialize the monitor."""
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(__file__).parent.parent / "data" / "email_monitoring"

        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Load tracking data
        self.tracking_file = self.data_dir / "outreach_tracking.json"
        self.responses_file = self.data_dir / "responses.json"

        self.tracking: Dict[str, OutreachTracking] = {}
        self.responses: List[EmailResponse] = []

        self._load_data()

    def _load_data(self) -> None:
        """Load tracking and response data."""
        if self.tracking_file.exists():
            with open(self.tracking_file, 'r') as f:
                data = json.load(f)
                for record in data.get('records', []):
                    # Parse dates
                    if record.get('sent_at'):
                        record['sent_at'] = datetime.fromisoformat(record['sent_at'])
                    if record.get('response_at'):
                        record['response_at'] = datetime.fromisoformat(record['response_at'])
                    if record.get('last_follow_up'):
                        record['last_follow_up'] = datetime.fromisoformat(record['last_follow_up'])
                    self.tracking[record['id']] = OutreachTracking(**record)

        if self.responses_file.exists():
            with open(self.responses_file, 'r') as f:
                data = json.load(f)
                for resp in data.get('responses', []):
                    if resp.get('received_at'):
                        resp['received_at'] = datetime.fromisoformat(resp['received_at'])
                    self.responses.append(EmailResponse(**resp))

    def _save_data(self) -> None:
        """Save tracking and response data."""
        # Save tracking
        tracking_data = {
            'records': [t.to_dict() for t in self.tracking.values()],
            'updated_at': datetime.now().isoformat()
        }
        with open(self.tracking_file, 'w') as f:
            json.dump(tracking_data, f, indent=2)

        # Save responses
        response_data = {
            'responses': [r.to_dict() for r in self.responses],
            'updated_at': datetime.now().isoformat()
        }
        with open(self.responses_file, 'w') as f:
            json.dump(response_data, f, indent=2)

    def register_outreach(
        self,
        inquiry_id: str,
        project: str,
        recipient_email: str,
        recipient_name: str,
        subject: str,
        inquiry_type: str = "bulk_pricing",
        metadata: Dict[str, Any] = None
    ) -> OutreachTracking:
        """
        Register a new outreach email for tracking.

        Call this after sending an inquiry/outreach email.
        """
        record = OutreachTracking(
            id=inquiry_id,
            project=project,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            subject=subject,
            sent_at=datetime.now(),
            inquiry_type=inquiry_type,
            metadata=metadata or {}
        )

        self.tracking[inquiry_id] = record
        self._save_data()

        logger.info(f"Registered outreach: {inquiry_id} to {recipient_email}")
        return record

    def detect_project(self, subject: str, body: str) -> Tuple[str, str]:
        """
        Detect which project an email relates to.

        Returns (project_name, inquiry_id).
        """
        combined = f"{subject} {body}".lower()

        for project, patterns in self.PROJECT_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, combined, re.IGNORECASE)
                if match:
                    # Try to extract inquiry ID
                    inquiry_id = ""
                    if match.groups():
                        inquiry_id = match.group(1)
                    else:
                        # Try to find any 8-character hex ID
                        id_match = re.search(r'#?([a-f0-9]{8})', combined)
                        if id_match:
                            inquiry_id = id_match.group(1)

                    return project, inquiry_id

        return "unknown", ""

    def classify_response(self, subject: str, body: str) -> str:
        """
        Classify the type of response.

        Returns: quote, question, rejection, auto-reply, or other
        """
        combined = f"{subject} {body}".lower()

        # Check patterns in priority order
        for response_type in ['auto-reply', 'rejection', 'quote', 'question']:
            patterns = self.RESPONSE_PATTERNS[response_type]
            for pattern in patterns:
                if re.search(pattern, combined, re.IGNORECASE):
                    return response_type

        return "other"

    def process_incoming_email(
        self,
        from_email: str,
        from_name: str,
        to_email: str,
        subject: str,
        body: str,
        received_at: datetime = None,
        message_id: str = "",
        thread_id: str = ""
    ) -> EmailResponse:
        """
        Process an incoming email and match it to outreach records.

        Can be called manually or via Gmail API integration.
        """
        if not received_at:
            received_at = datetime.now()

        if not message_id:
            message_id = f"manual-{datetime.now().timestamp()}"

        # Detect project and inquiry ID
        project, inquiry_id = self.detect_project(subject, body)

        # Classify response type
        response_type = self.classify_response(subject, body)

        # Create response record
        response = EmailResponse(
            message_id=message_id,
            thread_id=thread_id or message_id,
            from_email=from_email,
            from_name=from_name,
            to_email=to_email,
            subject=subject,
            body_preview=body[:500] if len(body) > 500 else body,
            received_at=received_at,
            project=project,
            inquiry_id=inquiry_id,
            response_type=response_type
        )

        # Try to match to tracked outreach
        matched = False

        # First, try exact inquiry ID match
        if inquiry_id and inquiry_id in self.tracking:
            self._update_tracking_record(inquiry_id, response)
            matched = True

        # If no exact match, try email match
        if not matched:
            for record_id, record in self.tracking.items():
                if record.recipient_email.lower() == from_email.lower():
                    self._update_tracking_record(record_id, response)
                    response.inquiry_id = record_id
                    matched = True
                    break

        response.processed = matched
        self.responses.append(response)
        self._save_data()

        logger.info(
            f"Processed response from {from_email}: "
            f"project={project}, type={response_type}, matched={matched}"
        )

        return response

    def _update_tracking_record(self, inquiry_id: str, response: EmailResponse) -> None:
        """Update tracking record with response."""
        if inquiry_id not in self.tracking:
            return

        record = self.tracking[inquiry_id]
        record.status = "responded"
        record.response_received = True
        record.response_at = response.received_at
        record.response_type = response.response_type

    def get_pending_responses(self, days: int = 7) -> List[OutreachTracking]:
        """
        Get outreach records awaiting response.

        Returns records sent in the last N days that haven't received a response.
        """
        cutoff = datetime.now() - timedelta(days=days)
        pending = []

        for record in self.tracking.values():
            if record.status == "sent" and record.sent_at > cutoff:
                pending.append(record)

        return sorted(pending, key=lambda r: r.sent_at)

    def get_needs_follow_up(self, min_days: int = 3, max_follow_ups: int = 5) -> List[OutreachTracking]:
        """
        Get outreach records that need follow-up.

        Returns records that:
        - Haven't responded
        - Were sent more than min_days ago
        - Haven't exceeded max follow-ups
        """
        cutoff = datetime.now() - timedelta(days=min_days)
        needs_follow_up = []

        for record in self.tracking.values():
            if record.status == "sent":
                check_date = record.last_follow_up or record.sent_at
                if check_date < cutoff and record.follow_up_count < max_follow_ups:
                    needs_follow_up.append(record)

        return sorted(needs_follow_up, key=lambda r: r.sent_at)

    def record_follow_up(self, inquiry_id: str) -> bool:
        """Record that a follow-up was sent."""
        if inquiry_id not in self.tracking:
            return False

        record = self.tracking[inquiry_id]
        record.follow_up_count += 1
        record.last_follow_up = datetime.now()
        self._save_data()

        return True

    def get_summary(self, project: str = None) -> Dict[str, Any]:
        """
        Get summary statistics.

        Args:
            project: Filter by project (or None for all)
        """
        records = list(self.tracking.values())
        if project:
            records = [r for r in records if r.project == project]

        # Count by status
        by_status = {}
        for record in records:
            by_status[record.status] = by_status.get(record.status, 0) + 1

        # Count by response type
        by_response_type = {}
        for record in records:
            if record.response_type:
                by_response_type[record.response_type] = by_response_type.get(record.response_type, 0) + 1

        # Count by project
        by_project = {}
        for record in self.tracking.values():  # All records for project breakdown
            by_project[record.project] = by_project.get(record.project, 0) + 1

        # Calculate response rate
        total_sent = len([r for r in records if r.status in ['sent', 'responded']])
        total_responded = len([r for r in records if r.response_received])
        response_rate = (total_responded / total_sent * 100) if total_sent > 0 else 0

        # Needs follow-up
        needs_follow_up = len(self.get_needs_follow_up())

        return {
            'total_outreach': len(records),
            'total_responded': total_responded,
            'response_rate': f"{response_rate:.1f}%",
            'needs_follow_up': needs_follow_up,
            'by_status': by_status,
            'by_response_type': by_response_type,
            'by_project': by_project,
            'pending': len(self.get_pending_responses()),
        }

    def generate_digest(self) -> str:
        """Generate a human-readable digest of email status."""
        summary = self.get_summary()

        lines = [
            "=" * 60,
            "EMAIL RESPONSE MONITORING DIGEST",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 60,
            "",
            f"Total Outreach: {summary['total_outreach']}",
            f"Responses Received: {summary['total_responded']}",
            f"Response Rate: {summary['response_rate']}",
            f"Awaiting Response: {summary['pending']}",
            f"Needs Follow-up: {summary['needs_follow_up']}",
            "",
            "BY PROJECT:",
            "-" * 40,
        ]

        for project, count in summary['by_project'].items():
            lines.append(f"  {project}: {count}")

        lines.extend([
            "",
            "BY STATUS:",
            "-" * 40,
        ])

        for status, count in summary['by_status'].items():
            lines.append(f"  {status}: {count}")

        if summary['by_response_type']:
            lines.extend([
                "",
                "BY RESPONSE TYPE:",
                "-" * 40,
            ])
            for resp_type, count in summary['by_response_type'].items():
                lines.append(f"  {resp_type}: {count}")

        # Add pending follow-ups
        follow_ups = self.get_needs_follow_up()
        if follow_ups:
            lines.extend([
                "",
                "NEEDS FOLLOW-UP:",
                "-" * 40,
            ])
            for record in follow_ups[:10]:  # Top 10
                days_ago = (datetime.now() - record.sent_at).days
                lines.append(
                    f"  [{record.project}] {record.recipient_name} ({record.recipient_email})"
                )
                lines.append(f"       Sent {days_ago} days ago, {record.follow_up_count} follow-ups")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)


# CLI interface
if __name__ == '__main__':
    import argparse

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description="Email Response Monitor")
    subparsers = parser.add_subparsers(dest='command')

    # Digest command
    digest_parser = subparsers.add_parser('digest', help='Show monitoring digest')

    # Summary command
    summary_parser = subparsers.add_parser('summary', help='Show summary stats')
    summary_parser.add_argument('--project', '-p', help='Filter by project')

    # Follow-up command
    followup_parser = subparsers.add_parser('follow-up', help='Show leads needing follow-up')
    followup_parser.add_argument('--days', '-d', type=int, default=3, help='Days since last contact')

    # Process command (manual email entry)
    process_parser = subparsers.add_parser('process', help='Process an email response')
    process_parser.add_argument('--from-email', '-f', required=True, help='Sender email')
    process_parser.add_argument('--from-name', '-n', default='', help='Sender name')
    process_parser.add_argument('--subject', '-s', required=True, help='Email subject')
    process_parser.add_argument('--body', '-b', required=True, help='Email body')

    # Register command
    register_parser = subparsers.add_parser('register', help='Register outreach for tracking')
    register_parser.add_argument('--id', required=True, help='Inquiry/campaign ID')
    register_parser.add_argument('--project', '-p', required=True, help='Project name')
    register_parser.add_argument('--email', '-e', required=True, help='Recipient email')
    register_parser.add_argument('--name', '-n', default='', help='Recipient name')
    register_parser.add_argument('--subject', '-s', required=True, help='Email subject')

    args = parser.parse_args()

    monitor = EmailResponseMonitor()

    if args.command == 'digest':
        print(monitor.generate_digest())

    elif args.command == 'summary':
        summary = monitor.get_summary(project=args.project)
        print(json.dumps(summary, indent=2))

    elif args.command == 'follow-up':
        records = monitor.get_needs_follow_up(min_days=args.days)
        print(f"\n{len(records)} outreach records need follow-up:\n")
        for record in records:
            days = (datetime.now() - record.sent_at).days
            print(f"  [{record.project}] {record.recipient_email}")
            print(f"       Sent {days} days ago | {record.follow_up_count} follow-ups")
            print()

    elif args.command == 'process':
        response = monitor.process_incoming_email(
            from_email=args.from_email,
            from_name=args.from_name,
            to_email=os.environ.get('SMTP_USER', ''),
            subject=args.subject,
            body=args.body
        )
        print(f"Processed: project={response.project}, type={response.response_type}")
        print(f"Inquiry ID: {response.inquiry_id or 'Not matched'}")

    elif args.command == 'register':
        record = monitor.register_outreach(
            inquiry_id=args.id,
            project=args.project,
            recipient_email=args.email,
            recipient_name=args.name,
            subject=args.subject
        )
        print(f"Registered outreach: {record.id}")

    else:
        parser.print_help()
