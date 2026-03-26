"""
UTM Parameter Tracking for Source Attribution

Generates UTM-tracked links for all outbound channels (SMS, social, voice AI)
and provides reporting on lead sources based on UTM parameters.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlencode, urlparse, parse_qs
from datetime import datetime
from collections import defaultdict


class UTMTracker:
    """UTM parameter tracking and reporting system"""

    # Business domain mappings
    BUSINESS_DOMAINS = {
        'marceau-solutions': 'marceausolutions.com',
        'swflorida-hvac': 'swfloridahvac.com',
        'shipping-logistics': 'swfllogistics.com'
    }

    def __init__(self, data_file: str = None):
        """Initialize UTM tracker

        Args:
            data_file: Path to utm_tracking.json (default: output/utm_tracking.json)
        """
        if data_file is None:
            project_root = Path(__file__).parent.parent
            self.data_file = project_root / 'output' / 'utm_tracking.json'
        else:
            self.data_file = Path(data_file)

        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_tracking_data()

    def _load_tracking_data(self):
        """Load existing tracking data from JSON file"""
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                self.tracking_data = json.load(f)
        else:
            self.tracking_data = {
                'links_generated': [],
                'clicks_tracked': [],
                'conversions': []
            }

    def _save_tracking_data(self):
        """Save tracking data to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.tracking_data, f, indent=2, default=str)

    def generate_utm_link(self,
                         business_id: str,
                         utm_source: str,
                         utm_medium: str,
                         utm_campaign: str,
                         utm_content: str,
                         path: str = '') -> str:
        """Generate UTM-tracked link for outbound marketing

        Args:
            business_id: Which business (marceau-solutions, swflorida-hvac, shipping-logistics)
            utm_source: Traffic source (sms, twitter, linkedin, facebook, voice, email, referral)
            utm_medium: Marketing medium (cold_outreach, organic, paid, inbound)
            utm_campaign: Campaign identifier (e.g., naples_gyms_jan20)
            utm_content: Content identifier (template_name, post_id, variation)
            path: URL path (e.g., /free-audit, /demo, /callback)

        Returns:
            Full UTM-tracked URL
        """
        # Get base domain for business
        domain = self.BUSINESS_DOMAINS.get(business_id, 'marceausolutions.com')

        # Build UTM parameters
        utm_params = {
            'utm_source': utm_source,
            'utm_medium': utm_medium,
            'utm_campaign': utm_campaign,
            'utm_content': utm_content
        }

        # Build URL
        base_url = f"https://{domain}{path}"
        utm_string = urlencode(utm_params)
        full_url = f"{base_url}?{utm_string}"

        # Track link generation
        self.tracking_data['links_generated'].append({
            'timestamp': datetime.now().isoformat(),
            'business_id': business_id,
            'url': full_url,
            'utm_params': utm_params
        })
        self._save_tracking_data()

        return full_url

    def parse_utm_params(self, url: str) -> Dict[str, str]:
        """Parse UTM parameters from URL

        Args:
            url: URL with UTM parameters

        Returns:
            Dict of UTM parameters
        """
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        utm_params = {}
        for key in ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term']:
            if key in params:
                utm_params[key] = params[key][0]  # Get first value

        return utm_params

    def track_click(self, url: str, visitor_info: Dict = None):
        """Track click on UTM-tracked link

        Args:
            url: URL that was clicked
            visitor_info: Optional visitor metadata (IP, user agent, etc.)
        """
        utm_params = self.parse_utm_params(url)

        click_record = {
            'timestamp': datetime.now().isoformat(),
            'url': url,
            'utm_params': utm_params,
            'visitor_info': visitor_info or {}
        }

        self.tracking_data['clicks_tracked'].append(click_record)
        self._save_tracking_data()

    def track_conversion(self, url: str, lead_id: str, conversion_type: str = 'form_submission'):
        """Track conversion from UTM-tracked link

        Args:
            url: Original URL with UTM params
            lead_id: Lead ID from lead_intake system
            conversion_type: Type of conversion (form_submission, call, purchase)
        """
        utm_params = self.parse_utm_params(url)

        conversion_record = {
            'timestamp': datetime.now().isoformat(),
            'lead_id': lead_id,
            'url': url,
            'utm_params': utm_params,
            'conversion_type': conversion_type
        }

        self.tracking_data['conversions'].append(conversion_record)
        self._save_tracking_data()

    def get_source_attribution(self) -> Dict:
        """Get lead source attribution from conversions

        Returns:
            Dict with breakdown by source, medium, campaign
        """
        attribution = {
            'by_source': defaultdict(int),
            'by_medium': defaultdict(int),
            'by_campaign': defaultdict(int),
            'total_conversions': len(self.tracking_data['conversions'])
        }

        for conversion in self.tracking_data['conversions']:
            utm_params = conversion.get('utm_params', {})

            source = utm_params.get('utm_source', 'unknown')
            medium = utm_params.get('utm_medium', 'unknown')
            campaign = utm_params.get('utm_campaign', 'unknown')

            attribution['by_source'][source] += 1
            attribution['by_medium'][medium] += 1
            attribution['by_campaign'][campaign] += 1

        # Calculate percentages
        total = attribution['total_conversions']
        if total > 0:
            attribution['by_source_pct'] = {
                k: round(v / total * 100, 1)
                for k, v in attribution['by_source'].items()
            }
            attribution['by_medium_pct'] = {
                k: round(v / total * 100, 1)
                for k, v in attribution['by_medium'].items()
            }

        return dict(attribution)

    def get_campaign_performance(self, campaign: str) -> Dict:
        """Get performance metrics for specific campaign

        Args:
            campaign: Campaign identifier

        Returns:
            Dict with clicks, conversions, conversion rate
        """
        clicks = [
            c for c in self.tracking_data['clicks_tracked']
            if c.get('utm_params', {}).get('utm_campaign') == campaign
        ]

        conversions = [
            c for c in self.tracking_data['conversions']
            if c.get('utm_params', {}).get('utm_campaign') == campaign
        ]

        conversion_rate = 0
        if len(clicks) > 0:
            conversion_rate = round(len(conversions) / len(clicks) * 100, 1)

        return {
            'campaign': campaign,
            'clicks': len(clicks),
            'conversions': len(conversions),
            'conversion_rate': conversion_rate
        }


def generate_sms_link(business_id: str, campaign: str, template_name: str, path: str = '/free-audit') -> str:
    """Generate UTM-tracked link for SMS campaigns

    Args:
        business_id: Business identifier
        campaign: Campaign name
        template_name: SMS template name
        path: Landing page path

    Returns:
        UTM-tracked URL for SMS
    """
    tracker = UTMTracker()
    return tracker.generate_utm_link(
        business_id=business_id,
        utm_source='sms',
        utm_medium='cold_outreach',
        utm_campaign=campaign,
        utm_content=template_name,
        path=path
    )


def generate_social_link(business_id: str, platform: str, campaign: str, post_id: str, path: str = '') -> str:
    """Generate UTM-tracked link for social media posts

    Args:
        business_id: Business identifier
        platform: Social platform (twitter, linkedin, facebook)
        campaign: Campaign name
        post_id: Post identifier
        path: Landing page path

    Returns:
        UTM-tracked URL for social media
    """
    tracker = UTMTracker()
    return tracker.generate_utm_link(
        business_id=business_id,
        utm_source=platform,
        utm_medium='organic',
        utm_campaign=campaign,
        utm_content=post_id,
        path=path
    )


def generate_voice_link(business_id: str, campaign: str, call_sid: str, path: str = '/callback') -> str:
    """Generate UTM-tracked link for voice AI follow-ups

    Args:
        business_id: Business identifier
        campaign: Campaign name
        call_sid: Twilio call SID
        path: Landing page path

    Returns:
        UTM-tracked URL for voice AI
    """
    tracker = UTMTracker()
    return tracker.generate_utm_link(
        business_id=business_id,
        utm_source='voice',
        utm_medium='inbound',
        utm_campaign=campaign,
        utm_content=call_sid,
        path=path
    )


def main():
    """CLI for UTM tracking"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.utm_tracker <command>")
        print("\nCommands:")
        print("  report              - Show source attribution report")
        print("  campaign <name>     - Show campaign performance")
        print("  generate-sms        - Generate sample SMS link")
        print("  generate-social     - Generate sample social link")
        sys.exit(1)

    command = sys.argv[1]
    tracker = UTMTracker()

    if command == 'report':
        attribution = tracker.get_source_attribution()

        print("\n=== UTM SOURCE ATTRIBUTION REPORT ===\n")
        print(f"Total Conversions: {attribution['total_conversions']}")

        if attribution['total_conversions'] > 0:
            print("\nBy Source:")
            for source, count in sorted(attribution['by_source'].items(), key=lambda x: x[1], reverse=True):
                pct = attribution['by_source_pct'].get(source, 0)
                print(f"  {source}: {count} ({pct}%)")

            print("\nBy Medium:")
            for medium, count in sorted(attribution['by_medium'].items(), key=lambda x: x[1], reverse=True):
                pct = attribution['by_medium_pct'].get(medium, 0)
                print(f"  {medium}: {count} ({pct}%)")

            print("\nTop Campaigns:")
            for campaign, count in sorted(attribution['by_campaign'].items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {campaign}: {count}")
        else:
            print("\nNo conversions tracked yet. Start tracking by:")
            print("  1. Generate UTM links for campaigns")
            print("  2. Track conversions with tracker.track_conversion()")

    elif command == 'campaign':
        if len(sys.argv) < 3:
            print("Usage: python -m src.utm_tracker campaign <campaign_name>")
            sys.exit(1)

        campaign = sys.argv[2]
        perf = tracker.get_campaign_performance(campaign)

        print(f"\n=== CAMPAIGN PERFORMANCE: {campaign} ===\n")
        print(f"Clicks: {perf['clicks']}")
        print(f"Conversions: {perf['conversions']}")
        print(f"Conversion Rate: {perf['conversion_rate']}%")

    elif command == 'generate-sms':
        link = generate_sms_link(
            business_id='marceau-solutions',
            campaign='naples_gyms_jan20',
            template_name='no_website_intro',
            path='/free-audit'
        )
        print(f"\nSMS Link: {link}")

    elif command == 'generate-social':
        link = generate_social_link(
            business_id='marceau-solutions',
            platform='twitter',
            campaign='ai_automation_jan20',
            post_id='post_123',
            path=''
        )
        print(f"\nSocial Link: {link}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
