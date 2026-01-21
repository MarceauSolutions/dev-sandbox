"""
Form Submission Tracking for All Businesses

Handles form submissions from all 3 business websites (marceau-solutions,
swflorida-hvac, shipping-logistics), parses UTM parameters, deduplicates,
and integrates with lead intake system.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
from urllib.parse import urlparse, parse_qs

from src.lead_intake import LeadIntakeSystem, BusinessID
from src.utm_tracker import UTMTracker


class FormTracker:
    """Form submission tracking across all business websites"""

    def __init__(self):
        """Initialize form tracker"""
        self.lead_system = LeadIntakeSystem()
        self.utm_tracker = UTMTracker()

        # Track form submissions separately for reporting
        project_root = Path(__file__).parent.parent
        self.submissions_file = project_root / 'output' / 'form_submissions.json'
        self.submissions_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_submissions()

    def _load_submissions(self):
        """Load existing form submissions"""
        if self.submissions_file.exists():
            with open(self.submissions_file, 'r') as f:
                data = json.load(f)
                # Handle both list and dict formats
                if isinstance(data, list):
                    self.submissions = data
                else:
                    self.submissions = []
        else:
            self.submissions = []

    def _save_submissions(self):
        """Save form submissions to file"""
        with open(self.submissions_file, 'w') as f:
            json.dump(self.submissions, f, indent=2, default=str)

    def parse_form_data(self, form_data: Dict, business_id: BusinessID = None) -> Dict:
        """Parse form submission data

        Args:
            form_data: Raw form data (name, email, phone, message, etc.)
            business_id: Business ID (auto-detected from referrer if not provided)

        Returns:
            Parsed form data with UTM parameters
        """
        # Extract standard form fields
        name = form_data.get('name', '')
        email = form_data.get('email', '')
        phone = form_data.get('phone', '')
        message = form_data.get('message', '')

        # Parse UTM parameters from referrer or direct fields
        utm_params = {}

        # Method 1: Direct UTM fields in form data
        for key in ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term']:
            if key in form_data:
                utm_params[key] = form_data[key]

        # Method 2: Parse from referrer URL
        if 'referrer' in form_data and not utm_params:
            utm_params = self.utm_tracker.parse_utm_params(form_data['referrer'])

        # Method 3: Parse from page URL
        if 'url' in form_data and not utm_params:
            utm_params = self.utm_tracker.parse_utm_params(form_data['url'])

        # Auto-detect business from referrer/URL if not provided
        if not business_id:
            business_id = self._detect_business_from_url(
                form_data.get('referrer') or form_data.get('url', '')
            )

        parsed = {
            'name': name,
            'email': email,
            'phone': phone,
            'message': message,
            'utm_params': utm_params,
            'business_id': business_id,
            'raw_form_data': form_data,
            'timestamp': datetime.now().isoformat()
        }

        return parsed

    def _detect_business_from_url(self, url: str) -> BusinessID:
        """Auto-detect business from URL

        Args:
            url: Referrer or form URL

        Returns:
            Business ID
        """
        if not url:
            return 'marceau-solutions'  # Default

        url_lower = url.lower()

        if 'swfloridahvac.com' in url_lower or 'hvac' in url_lower:
            return 'swflorida-hvac'
        elif 'swfllogistics.com' in url_lower or 'shipping' in url_lower or 'logistics' in url_lower:
            return 'shipping-logistics'
        else:
            return 'marceau-solutions'

    def _check_for_urgent_keywords(self, message: str) -> bool:
        """Check if form message contains urgent keywords

        Args:
            message: Form message text

        Returns:
            True if urgent keywords found
        """
        urgent_keywords = [
            'urgent', 'asap', 'emergency', 'immediately', 'right away',
            'today', 'now', 'critical', 'important'
        ]

        message_lower = message.lower()
        return any(keyword in message_lower for keyword in urgent_keywords)

    def handle_form_submission(self, form_data: Dict, business_id: BusinessID = None) -> Dict:
        """Handle form submission from website

        Args:
            form_data: Raw form data from website
            business_id: Business ID (auto-detected if not provided)

        Returns:
            Result dict with lead_id and status
        """
        # Parse form data
        parsed = self.parse_form_data(form_data, business_id)

        # Save raw submission
        self.submissions.append({
            'submission_id': len(self.submissions) + 1,
            'timestamp': parsed['timestamp'],
            'business_id': parsed['business_id'],
            'form_data': parsed
        })
        self._save_submissions()

        # Determine priority based on message content
        priority = 'high' if self._check_for_urgent_keywords(parsed['message']) else 'medium'

        # Determine status
        status = 'qualified' if self._check_for_urgent_keywords(parsed['message']) else 'new'

        # Add lead to intake system (handles deduplication automatically)
        lead = self.lead_system.add_lead(
            source_channel='form_submission',
            business_id=parsed['business_id'],
            contact_info={
                'name': parsed['name'],
                'email': parsed['email'],
                'phone': parsed['phone']
            },
            source_detail={
                **parsed['utm_params'],
                'form_message': parsed['message'],
                'submission_timestamp': parsed['timestamp']
            },
            status=status,
            priority=priority,
            metadata={
                'form_source': 'website',
                'has_urgent_keywords': self._check_for_urgent_keywords(parsed['message'])
            }
        )

        # Track UTM conversion
        if parsed['utm_params']:
            # Reconstruct URL with UTM params for tracking
            url_with_utm = f"https://example.com?utm_source={parsed['utm_params'].get('utm_source', '')}"
            self.utm_tracker.track_conversion(
                url=url_with_utm,
                lead_id=lead['lead_id'],
                conversion_type='form_submission'
            )

        return {
            'success': True,
            'lead_id': lead['lead_id'],
            'status': status,
            'priority': priority,
            'was_duplicate': len(lead.get('touchpoint_history', [])) > 1,
            'message': 'Form submission processed successfully'
        }

    def get_submissions_by_business(self, business_id: BusinessID) -> List[Dict]:
        """Get all form submissions for a business

        Args:
            business_id: Business to filter by

        Returns:
            List of submission dicts
        """
        return [
            sub for sub in self.submissions
            if sub.get('business_id') == business_id
        ]

    def get_submissions_by_source(self, business_id: BusinessID, utm_source: str) -> List[Dict]:
        """Get form submissions by UTM source

        Args:
            business_id: Business to filter by
            utm_source: UTM source (e.g., 'sms', 'twitter', 'google')

        Returns:
            List of submission dicts
        """
        business_subs = self.get_submissions_by_business(business_id)
        return [
            sub for sub in business_subs
            if sub.get('form_data', {}).get('utm_params', {}).get('utm_source') == utm_source
        ]

    def get_report(self, business_id: BusinessID = None) -> Dict:
        """Generate form submission report

        Args:
            business_id: Optional business filter

        Returns:
            Report dict with submission stats
        """
        if business_id:
            subs = self.get_submissions_by_business(business_id)
        else:
            subs = self.submissions

        report = {
            'total_submissions': len(subs),
            'by_business': {},
            'by_source': {},
            'urgent_count': 0
        }

        for sub in subs:
            # Count by business
            biz_id = sub.get('business_id', 'unknown')
            report['by_business'][biz_id] = report['by_business'].get(biz_id, 0) + 1

            # Count by source
            utm_source = sub.get('form_data', {}).get('utm_params', {}).get('utm_source', 'direct')
            report['by_source'][utm_source] = report['by_source'].get(utm_source, 0) + 1

            # Count urgent
            message = sub.get('form_data', {}).get('message', '')
            if self._check_for_urgent_keywords(message):
                report['urgent_count'] += 1

        return report


def main():
    """CLI for form tracker"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.form_tracker <command>")
        print("\nCommands:")
        print("  report [business_id]    - Show form submission report")
        print("  test                    - Submit test form")
        sys.exit(1)

    command = sys.argv[1]
    tracker = FormTracker()

    if command == 'report':
        business_id = sys.argv[2] if len(sys.argv) > 2 else None
        report = tracker.get_report(business_id)

        title = f"=== FORM SUBMISSION REPORT"
        if business_id:
            title += f": {business_id.upper()}"
        title += " ==="

        print(f"\n{title}\n")
        print(f"Total Submissions: {report['total_submissions']}")

        if report['by_business']:
            print("\nBy Business:")
            for biz, count in sorted(report['by_business'].items()):
                print(f"  {biz}: {count}")

        if report['by_source']:
            print("\nBy Source:")
            for source, count in sorted(report['by_source'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {source}: {count}")

        print(f"\nUrgent Submissions: {report['urgent_count']}")

    elif command == 'test':
        # Submit test form
        test_form = {
            'name': 'Test Customer',
            'email': 'test@example.com',
            'phone': '2393334444',
            'message': 'I need help with my website ASAP',
            'utm_source': 'sms',
            'utm_campaign': 'no_website_jan26',
            'utm_content': 'test_template',
            'url': 'https://marceausolutions.com/contact'
        }

        result = tracker.handle_form_submission(test_form, business_id='marceau-solutions')
        print("\n=== TEST FORM SUBMITTED ===\n")
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
