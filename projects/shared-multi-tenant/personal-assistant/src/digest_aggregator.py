#!/usr/bin/env python3
"""
digest_aggregator.py - Unified Data Aggregator for Morning Digest

Combines data from multiple sources:
- Gmail (email categorization)
- SMS Replies (from sms_campaigns.json)
- Form Submissions (from Google Sheets)
- Calendar Events (from Google Calendar API)
- Campaign Metrics (from campaign_analytics.py)

Usage:
    python -m src.digest_aggregator --hours 24
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any

# Add parent paths for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "fitness-influencer" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "lead-scraper" / "src"))

# Try to import dependencies
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    print("Warning: Google API libraries not installed. Some features disabled.")


@dataclass
class EmailSummary:
    """Summary of email inbox."""
    total: int = 0
    urgent: int = 0
    sponsorship: int = 0
    business: int = 0
    customer: int = 0
    other: int = 0
    action_required: List[Dict] = field(default_factory=list)


@dataclass
class SMSReplySummary:
    """Summary of SMS replies."""
    total: int = 0
    hot_leads: int = 0
    warm_leads: int = 0
    questions: int = 0
    opt_outs: int = 0
    callbacks_requested: int = 0
    action_required: List[Dict] = field(default_factory=list)


@dataclass
class FormSubmissionSummary:
    """Summary of form submissions."""
    total: int = 0
    sources: Dict[str, int] = field(default_factory=dict)
    new_inquiries: List[Dict] = field(default_factory=list)


@dataclass
class CalendarSummary:
    """Summary of calendar events."""
    today_events: List[Dict] = field(default_factory=list)
    upcoming_week: List[Dict] = field(default_factory=list)


@dataclass
class CampaignSummary:
    """Summary of campaign metrics."""
    total_contacted: int = 0
    total_responded: int = 0
    response_rate: float = 0.0
    funnel_stages: Dict[str, int] = field(default_factory=dict)


@dataclass
class DigestData:
    """Complete digest data structure."""
    generated_at: str = ""
    hours_covered: int = 24
    email: EmailSummary = field(default_factory=EmailSummary)
    sms: SMSReplySummary = field(default_factory=SMSReplySummary)
    forms: FormSubmissionSummary = field(default_factory=FormSubmissionSummary)
    calendar: CalendarSummary = field(default_factory=CalendarSummary)
    campaign: CampaignSummary = field(default_factory=CampaignSummary)
    action_items: List[str] = field(default_factory=list)


class DigestAggregator:
    """
    Aggregates data from multiple sources for morning digest.
    """

    # Google API scopes needed
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/calendar.readonly',
        'https://www.googleapis.com/auth/spreadsheets.readonly'
    ]

    # Email categories and keywords
    EMAIL_CATEGORIES = {
        'sponsorship': ['sponsorship', 'sponsor', 'brand deal', 'collaboration', 'partnership', 'paid promotion'],
        'business': ['invoice', 'payment', 'revenue', 'affiliate', 'commission', 'earnings', 'payout'],
        'customer': ['refund', 'support', 'help', 'question', 'issue', 'problem', 'course', 'purchased'],
    }

    def __init__(self, credentials_path: str = 'credentials.json', token_path: str = 'token.json'):
        """Initialize aggregator with Google credentials."""
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.gmail_service = None
        self.calendar_service = None
        self.sheets_service = None

        # Lead scraper paths
        self.lead_scraper_root = PROJECT_ROOT / "lead-scraper"
        self.sms_campaigns_file = self.lead_scraper_root / "output" / "sms_campaigns.json"
        self.form_submissions_file = self.lead_scraper_root / "output" / "form_submissions.json"

    def authenticate(self) -> bool:
        """Authenticate with Google APIs."""
        if not GOOGLE_AVAILABLE:
            print("Google libraries not available")
            return False

        creds = None

        # Load existing token
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    print(f"ERROR: Credentials file not found: {self.credentials_path}")
                    return False

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save token
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        # Build services
        try:
            self.gmail_service = build('gmail', 'v1', credentials=creds)
            self.calendar_service = build('calendar', 'v3', credentials=creds)
            self.sheets_service = build('sheets', 'v4', credentials=creds)
            return True
        except Exception as e:
            print(f"ERROR building services: {e}")
            return False

    def get_email_summary(self, hours_back: int = 24) -> EmailSummary:
        """
        Get email summary from Gmail.

        Args:
            hours_back: Hours to look back

        Returns:
            EmailSummary with categorized counts
        """
        summary = EmailSummary()

        if not self.gmail_service:
            print("Gmail service not available")
            return summary

        try:
            # Calculate date for query
            after_date = datetime.now() - timedelta(hours=hours_back)
            after_timestamp = int(after_date.timestamp())
            query = f'after:{after_timestamp} in:inbox'

            # Get message list
            results = self.gmail_service.users().messages().list(
                userId='me',
                q=query,
                maxResults=100
            ).execute()

            messages = results.get('messages', [])
            summary.total = len(messages)

            # Categorize each email
            for msg in messages:
                email = self.gmail_service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['Subject', 'From']
                ).execute()

                # Extract headers
                headers = {h['name'].lower(): h['value'] for h in email['payload']['headers']}
                subject = headers.get('subject', '').lower()
                snippet = email.get('snippet', '').lower()
                content = f"{subject} {snippet}"

                # Categorize
                category = 'other'
                priority = 3

                for cat, keywords in self.EMAIL_CATEGORIES.items():
                    if any(kw in content for kw in keywords):
                        category = cat
                        priority = 1 if cat in ['sponsorship', 'business'] else 2
                        break

                # Update counts
                if category == 'sponsorship':
                    summary.sponsorship += 1
                elif category == 'business':
                    summary.business += 1
                elif category == 'customer':
                    summary.customer += 1
                else:
                    summary.other += 1

                # Track urgent/action required
                if priority == 1:
                    summary.urgent += 1
                    summary.action_required.append({
                        'subject': headers.get('subject', 'No Subject'),
                        'from': headers.get('from', 'Unknown'),
                        'category': category
                    })

        except HttpError as e:
            print(f"Gmail API error: {e}")

        return summary

    def get_sms_reply_summary(self, hours_back: int = 24) -> SMSReplySummary:
        """
        Get SMS reply summary from campaign data.

        Args:
            hours_back: Hours to look back

        Returns:
            SMSReplySummary with categorized counts
        """
        summary = SMSReplySummary()
        cutoff = datetime.now() - timedelta(hours=hours_back)

        if not self.sms_campaigns_file.exists():
            return summary

        try:
            with open(self.sms_campaigns_file) as f:
                data = json.load(f)

            # Handle both formats: {records: [...]} or [...]
            if isinstance(data, dict):
                records = data.get('records', [])
                replies = data.get('replies', [])  # Separate replies array if exists
            else:
                records = data if isinstance(data, list) else []
                replies = []

            # Check for replies in campaign records
            for record in records:
                if not isinstance(record, dict):
                    continue

                # Check if record has replies
                record_replies = record.get('replies', [])
                for reply in record_replies:
                    # Check timestamp
                    reply_time = datetime.fromisoformat(reply.get('received_at', '2000-01-01'))
                    if reply_time < cutoff:
                        continue

                    summary.total += 1
                    category = reply.get('category', 'unknown').lower()

                    if category in ['hot_lead', 'positive']:
                        summary.hot_leads += 1
                        summary.action_required.append({
                            'phone': reply.get('phone', 'Unknown'),
                            'message': reply.get('message', '')[:100],
                            'business': reply.get('business_name', 'Unknown'),
                            'category': 'hot_lead'
                        })
                    elif category in ['warm_lead', 'interested']:
                        summary.warm_leads += 1
                    elif category in ['question', 'inquiry']:
                        summary.questions += 1
                        summary.action_required.append({
                            'phone': reply.get('phone', 'Unknown'),
                            'message': reply.get('message', '')[:100],
                            'category': 'question'
                        })
                    elif category in ['opt_out', 'stop']:
                        summary.opt_outs += 1
                    elif category in ['callback', 'call_me']:
                        summary.callbacks_requested += 1
                        summary.action_required.append({
                            'phone': reply.get('phone', 'Unknown'),
                            'message': reply.get('message', '')[:100],
                            'business': reply.get('business_name', 'Unknown'),
                            'category': 'callback_requested'
                        })

            # Also check standalone replies array
            for reply in replies:
                if not isinstance(reply, dict):
                    continue
                reply_time = datetime.fromisoformat(reply.get('received_at', '2000-01-01'))
                if reply_time < cutoff:
                    continue
                summary.total += 1
                # Apply same categorization logic...

        except Exception as e:
            print(f"Error reading SMS campaigns: {e}")

        return summary

    def get_form_submission_summary(self, hours_back: int = 24) -> FormSubmissionSummary:
        """
        Get form submission summary.

        Args:
            hours_back: Hours to look back

        Returns:
            FormSubmissionSummary with counts by source
        """
        summary = FormSubmissionSummary()
        cutoff = datetime.now() - timedelta(hours=hours_back)

        if not self.form_submissions_file.exists():
            return summary

        try:
            with open(self.form_submissions_file) as f:
                data = json.load(f)

            # Handle both formats: {submissions: [...]} or [...]
            if isinstance(data, dict):
                submissions = data.get('submissions', data.get('records', []))
            else:
                submissions = data if isinstance(data, list) else []

            for sub in submissions:
                if not isinstance(sub, dict):
                    continue

                # Check timestamp
                sub_time = datetime.fromisoformat(sub.get('submitted_at', '2000-01-01'))
                if sub_time < cutoff:
                    continue

                summary.total += 1
                source = sub.get('source', 'unknown')
                summary.sources[source] = summary.sources.get(source, 0) + 1

                summary.new_inquiries.append({
                    'name': sub.get('name', 'Unknown'),
                    'email': sub.get('email', ''),
                    'source': source,
                    'message': sub.get('message', '')[:100]
                })

        except Exception as e:
            print(f"Error reading form submissions: {e}")

        return summary

    def get_calendar_summary(self) -> CalendarSummary:
        """
        Get calendar events for today and upcoming week.

        Returns:
            CalendarSummary with today and upcoming events
        """
        summary = CalendarSummary()

        if not self.calendar_service:
            return summary

        try:
            # Get today's events
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)

            # Format for API
            time_min = today_start.isoformat() + 'Z'
            time_max = today_end.isoformat() + 'Z'

            events_result = self.calendar_service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                summary.today_events.append({
                    'summary': event.get('summary', 'No Title'),
                    'start': start,
                    'location': event.get('location', '')
                })

            # Get upcoming week
            week_end = today_start + timedelta(days=7)
            time_max_week = week_end.isoformat() + 'Z'

            week_result = self.calendar_service.events().list(
                calendarId='primary',
                timeMin=time_max,  # Start from tomorrow
                timeMax=time_max_week,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            upcoming = week_result.get('items', [])

            for event in upcoming:
                start = event['start'].get('dateTime', event['start'].get('date'))
                summary.upcoming_week.append({
                    'summary': event.get('summary', 'No Title'),
                    'start': start
                })

        except HttpError as e:
            print(f"Calendar API error: {e}")

        return summary

    def get_campaign_summary(self) -> CampaignSummary:
        """
        Get campaign performance summary.

        Returns:
            CampaignSummary with key metrics
        """
        summary = CampaignSummary()

        if not self.sms_campaigns_file.exists():
            return summary

        try:
            with open(self.sms_campaigns_file) as f:
                data = json.load(f)

            # Handle {records: [...]} format
            if isinstance(data, dict):
                records = data.get('records', [])
            else:
                records = data if isinstance(data, list) else []

            total_sent = len(records)
            total_replied = 0

            # Count records with status 'replied' or check for replies array
            for record in records:
                if not isinstance(record, dict):
                    continue
                if record.get('status') == 'replied':
                    total_replied += 1
                elif record.get('replies'):
                    total_replied += len(record.get('replies', []))

            summary.total_contacted = total_sent
            summary.total_responded = total_replied
            summary.response_rate = (total_replied / total_sent * 100) if total_sent > 0 else 0

            # Funnel stages (simplified)
            summary.funnel_stages = {
                'contacted': total_sent,
                'responded': total_replied,
                'qualified': int(total_replied * 0.5),  # Estimate
                'converted': 0  # From ClickUp
            }

        except Exception as e:
            print(f"Error reading campaign data: {e}")

        return summary

    def generate_action_items(self, digest: DigestData) -> List[str]:
        """
        Generate prioritized action items from digest data.

        Args:
            digest: Complete digest data

        Returns:
            List of action item strings
        """
        actions = []
        priority = 1

        # URGENT: Form submissions that have been waiting too long
        # These are HOT LEADS that must not wait 26 hours like Jane Fitness did!
        for item in digest.forms.new_inquiries:
            name = item.get('name', 'Unknown')
            email = item.get('email', '')
            source = item.get('source', '')
            message = item.get('message', '')

            # Skip test emails
            if '@example.com' in email or '@test.com' in email:
                continue

            # Check if this looks like a hot lead
            is_hot = any(kw in message.lower() for kw in [
                'website', 'interested', 'need', 'want', 'help',
                'quote', 'price', 'asap', 'urgent', 'gym', 'fitness'
            ])

            if is_hot:
                actions.insert(0, f"{priority}. 🚨 [URGENT HOT LEAD] Follow up with {name} NOW - {source}")
                priority += 1
            else:
                actions.append(f"{priority}. Follow up with {name} (form inquiry)")
                priority += 1

        # Hot leads / callback requests from SMS
        for item in digest.sms.action_required:
            if item.get('category') in ['hot_lead', 'callback_requested']:
                business = item.get('business', 'Unknown business')
                actions.insert(0, f"🚨 [URGENT] Call back {business} - hot lead")

        # Urgent emails
        for item in digest.email.action_required[:3]:  # Top 3
            subject = item.get('subject', 'No subject')[:50]
            actions.append(f"{len(actions)+1}. Respond to: {subject}")

        # SMS questions
        for item in digest.sms.action_required:
            if item.get('category') == 'question':
                phone = item.get('phone', 'Unknown')
                actions.append(f"{len(actions)+1}. Answer SMS question from {phone}")

        if not actions:
            actions.append("No urgent actions required")

        return actions

    def aggregate(self, hours_back: int = 24) -> DigestData:
        """
        Aggregate all data sources into unified digest.

        Args:
            hours_back: Hours to look back for data

        Returns:
            DigestData with all summaries
        """
        digest = DigestData(
            generated_at=datetime.now().isoformat(),
            hours_covered=hours_back
        )

        print(f"Aggregating data for last {hours_back} hours...")

        # Collect from all sources
        print("  - Fetching email summary...")
        digest.email = self.get_email_summary(hours_back)

        print("  - Fetching SMS reply summary...")
        digest.sms = self.get_sms_reply_summary(hours_back)

        print("  - Fetching form submissions...")
        digest.forms = self.get_form_submission_summary(hours_back)

        print("  - Fetching calendar events...")
        digest.calendar = self.get_calendar_summary()

        print("  - Fetching campaign metrics...")
        digest.campaign = self.get_campaign_summary()

        # Generate action items
        print("  - Generating action items...")
        digest.action_items = self.generate_action_items(digest)

        print("Done!")
        return digest

    def to_dict(self, digest: DigestData) -> Dict[str, Any]:
        """Convert digest to dictionary for JSON serialization."""
        return {
            'generated_at': digest.generated_at,
            'hours_covered': digest.hours_covered,
            'email': asdict(digest.email),
            'sms': asdict(digest.sms),
            'forms': asdict(digest.forms),
            'calendar': asdict(digest.calendar),
            'campaign': asdict(digest.campaign),
            'action_items': digest.action_items
        }


def main():
    """CLI for digest aggregator."""
    parser = argparse.ArgumentParser(description='Aggregate data for morning digest')
    parser.add_argument('--hours', type=int, default=24, help='Hours to look back')
    parser.add_argument('--credentials', default='credentials.json', help='Google credentials file')
    parser.add_argument('--token', default='token.json', help='Google token file')
    parser.add_argument('--output', help='Output JSON file (optional)')
    parser.add_argument('--no-auth', action='store_true', help='Skip Google auth (local data only)')

    args = parser.parse_args()

    aggregator = DigestAggregator(
        credentials_path=args.credentials,
        token_path=args.token
    )

    # Authenticate unless skipped
    if not args.no_auth:
        print("Authenticating with Google...")
        if not aggregator.authenticate():
            print("Warning: Google auth failed, continuing with local data only")

    # Aggregate data
    digest = aggregator.aggregate(hours_back=args.hours)

    # Output
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(aggregator.to_dict(digest), f, indent=2)
        print(f"\nDigest saved to: {output_path}")
    else:
        # Print summary
        print(f"\n{'='*60}")
        print(f"DIGEST SUMMARY - Last {args.hours} Hours")
        print(f"{'='*60}\n")

        print(f"📧 EMAILS: {digest.email.total}")
        print(f"   Urgent: {digest.email.urgent}")
        print(f"   Sponsorship: {digest.email.sponsorship}")
        print(f"   Business: {digest.email.business}")
        print(f"   Customer: {digest.email.customer}")

        print(f"\n📱 SMS REPLIES: {digest.sms.total}")
        print(f"   Hot Leads: {digest.sms.hot_leads}")
        print(f"   Questions: {digest.sms.questions}")
        print(f"   Callbacks: {digest.sms.callbacks_requested}")
        print(f"   Opt-outs: {digest.sms.opt_outs}")

        print(f"\n📝 FORM SUBMISSIONS: {digest.forms.total}")
        for source, count in digest.forms.sources.items():
            print(f"   {source}: {count}")

        print(f"\n📅 TODAY'S CALENDAR: {len(digest.calendar.today_events)} events")
        for event in digest.calendar.today_events[:5]:
            print(f"   - {event['start']}: {event['summary']}")

        print(f"\n📊 CAMPAIGN METRICS:")
        print(f"   Total Contacted: {digest.campaign.total_contacted}")
        print(f"   Total Responded: {digest.campaign.total_responded}")
        print(f"   Response Rate: {digest.campaign.response_rate:.1f}%")

        print(f"\n{'='*60}")
        print("ACTION ITEMS:")
        print(f"{'='*60}")
        for action in digest.action_items:
            print(f"  {action}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
