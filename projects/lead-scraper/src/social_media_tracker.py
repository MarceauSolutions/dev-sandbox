"""
Social Media Lead Tracking for All Businesses

Tracks social media campaigns for marceau-solutions (active), swflorida-hvac
(ready), and shipping-logistics (ready). Monitors clicks, conversions, and
campaign performance across platforms.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict

from src.lead_intake import LeadIntakeSystem, BusinessID
from src.utm_tracker import UTMTracker


class SocialMediaTracker:
    """Social media campaign tracking and analytics"""

    # Business campaign status
    BUSINESS_STATUS = {
        'marceau-solutions': 'ACTIVE - currently posting 25x/day with UTM tracking',
        'swflorida-hvac': 'READY - templates exist, scheduler configured, waiting to launch',
        'shipping-logistics': 'READY - templates exist, scheduler configured, waiting to launch'
    }

    def __init__(self):
        """Initialize social media tracker"""
        self.lead_system = LeadIntakeSystem()
        self.utm_tracker = UTMTracker()

        # Track social media specific data
        project_root = Path(__file__).parent.parent
        self.social_data_file = project_root / 'output' / 'social_media_tracking.json'
        self.social_data_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_social_data()

    def _load_social_data(self):
        """Load social media tracking data"""
        if self.social_data_file.exists():
            with open(self.social_data_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    self.social_data = data
                else:
                    self.social_data = {'posts': [], 'clicks': []}
        else:
            self.social_data = {
                'posts': [],  # Posted content with UTM links
                'clicks': []  # Click tracking data
            }

    def _save_social_data(self):
        """Save social media tracking data"""
        with open(self.social_data_file, 'w') as f:
            json.dump(self.social_data, f, indent=2, default=str)

    def track_post(self,
                   business_id: BusinessID,
                   platform: str,
                   post_id: str,
                   campaign: str,
                   utm_link: str,
                   post_content: str = None):
        """Track social media post

        Args:
            business_id: Which business
            platform: Social platform (twitter, linkedin, facebook)
            post_id: Unique post identifier
            campaign: Campaign name
            utm_link: UTM-tracked link in post
            post_content: Optional post content
        """
        post_record = {
            'timestamp': datetime.now().isoformat(),
            'business_id': business_id,
            'platform': platform,
            'post_id': post_id,
            'campaign': campaign,
            'utm_link': utm_link,
            'content': post_content
        }

        self.social_data['posts'].append(post_record)
        self._save_social_data()

    def track_click(self,
                    utm_link: str,
                    visitor_info: Dict = None):
        """Track click on social media link

        Args:
            utm_link: UTM-tracked link that was clicked
            visitor_info: Optional visitor metadata
        """
        # Parse UTM params to get business and campaign
        utm_params = self.utm_tracker.parse_utm_params(utm_link)

        click_record = {
            'timestamp': datetime.now().isoformat(),
            'utm_link': utm_link,
            'utm_params': utm_params,
            'visitor_info': visitor_info or {}
        }

        self.social_data['clicks'].append(click_record)
        self._save_social_data()

        # Also track in UTM tracker
        self.utm_tracker.track_click(utm_link, visitor_info)

    def get_clicks_by_business(self, business_id: BusinessID) -> List[Dict]:
        """Get all clicks for a business

        Args:
            business_id: Business to filter by

        Returns:
            List of click records
        """
        # Need to determine business from UTM params or link
        # For now, filter by domain in utm_link
        domain_map = {
            'marceau-solutions': 'marceausolutions.com',
            'swflorida-hvac': 'swfloridahvac.com',
            'shipping-logistics': 'swfllogistics.com'
        }

        target_domain = domain_map.get(business_id, 'marceausolutions.com')

        return [
            click for click in self.social_data['clicks']
            if target_domain in click.get('utm_link', '')
        ]

    def get_posts_by_business(self, business_id: BusinessID) -> List[Dict]:
        """Get all posts for a business

        Args:
            business_id: Business to filter by

        Returns:
            List of post records
        """
        return [
            post for post in self.social_data['posts']
            if post.get('business_id') == business_id
        ]

    def get_conversion_rate(self, business_id: BusinessID = None) -> Dict:
        """Calculate conversion rate (clicks -> form submissions)

        Args:
            business_id: Optional business filter

        Returns:
            Dict with conversion metrics
        """
        # Get clicks
        if business_id:
            clicks = self.get_clicks_by_business(business_id)
        else:
            clicks = self.social_data['clicks']

        # Get form submissions from social sources
        # (would query lead_intake for source_channel='form_submission' with utm_source in social platforms)
        social_platforms = ['twitter', 'linkedin', 'facebook', 'instagram']

        leads = self.lead_system.leads
        social_leads = [
            lead for lead in leads
            if lead.get('source_detail', {}).get('utm_source') in social_platforms
        ]

        if business_id:
            social_leads = [
                lead for lead in social_leads
                if lead.get('business_id') == business_id
            ]

        conversion_rate = 0
        if len(clicks) > 0:
            conversion_rate = round(len(social_leads) / len(clicks) * 100, 1)

        return {
            'business_id': business_id or 'all',
            'clicks': len(clicks),
            'form_submissions': len(social_leads),
            'conversion_rate': conversion_rate
        }

    def get_campaign_status(self, business_id: BusinessID = None) -> Dict:
        """Get campaign status for business(es)

        Args:
            business_id: Optional business filter

        Returns:
            Dict with campaign status
        """
        if business_id:
            businesses = {business_id: self.BUSINESS_STATUS.get(business_id, 'Unknown')}
        else:
            businesses = self.BUSINESS_STATUS

        status_report = {}

        for biz_id, status in businesses.items():
            posts = self.get_posts_by_business(biz_id)
            clicks = self.get_clicks_by_business(biz_id)
            conversion = self.get_conversion_rate(biz_id)

            status_report[biz_id] = {
                'status': status,
                'total_posts': len(posts),
                'total_clicks': len(clicks),
                'conversions': conversion['form_submissions'],
                'conversion_rate': conversion['conversion_rate']
            }

        return status_report

    def get_report(self, business_id: BusinessID = None) -> Dict:
        """Generate social media tracking report

        Args:
            business_id: Optional business filter

        Returns:
            Report dict
        """
        if business_id:
            posts = self.get_posts_by_business(business_id)
            clicks = self.get_clicks_by_business(business_id)
        else:
            posts = self.social_data['posts']
            clicks = self.social_data['clicks']

        # Count by platform
        by_platform = defaultdict(int)
        for post in posts:
            platform = post.get('platform', 'unknown')
            by_platform[platform] += 1

        # Count by campaign
        by_campaign = defaultdict(int)
        for post in posts:
            campaign = post.get('campaign', 'unknown')
            by_campaign[campaign] += 1

        report = {
            'business_id': business_id or 'all',
            'total_posts': len(posts),
            'total_clicks': len(clicks),
            'by_platform': dict(by_platform),
            'by_campaign': dict(by_campaign),
            'conversion_metrics': self.get_conversion_rate(business_id)
        }

        return report


def main():
    """CLI for social media tracker"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.social_media_tracker <command>")
        print("\nCommands:")
        print("  status [business_id]         - Show campaign status")
        print("  clicks --business <id>       - Show click data")
        print("  conversion-rate [business]   - Show conversion rate")
        print("  test                         - Add test data")
        sys.exit(1)

    command = sys.argv[1]
    tracker = SocialMediaTracker()

    if command == 'status':
        business_id = sys.argv[2] if len(sys.argv) > 2 else None
        status = tracker.get_campaign_status(business_id)

        print("\n=== SOCIAL MEDIA CAMPAIGN STATUS ===\n")

        for biz_id, data in status.items():
            print(f"Business: {biz_id}")
            print(f"  Status: {data['status']}")
            print(f"  Posts: {data['total_posts']}")
            print(f"  Clicks: {data['total_clicks']}")
            print(f"  Conversions: {data['conversions']}")
            print(f"  Conversion Rate: {data['conversion_rate']}%")
            print()

    elif command == 'clicks':
        if '--business' not in sys.argv:
            print("Usage: python -m src.social_media_tracker clicks --business <business_id>")
            sys.exit(1)

        business_idx = sys.argv.index('--business') + 1
        business_id = sys.argv[business_idx]

        clicks = tracker.get_clicks_by_business(business_id)

        print(f"\n=== SOCIAL MEDIA CLICKS: {business_id.upper()} ===\n")
        print(f"Total Clicks: {len(clicks)}")

        if len(clicks) > 0:
            print("\nRecent Clicks:")
            for click in clicks[-5:]:  # Last 5
                print(f"  {click['timestamp']}: {click['utm_link']}")
        else:
            print("\nNo clicks yet. Campaign may not be active.")

    elif command == 'conversion-rate':
        business_id = sys.argv[2] if len(sys.argv) > 2 else None
        metrics = tracker.get_conversion_rate(business_id)

        title = "=== SOCIAL MEDIA CONVERSION RATE"
        if business_id:
            title += f": {business_id.upper()}"
        title += " ==="

        print(f"\n{title}\n")
        print(f"Clicks: {metrics['clicks']}")
        print(f"Form Submissions: {metrics['form_submissions']}")
        print(f"Conversion Rate: {metrics['conversion_rate']}%")

    elif command == 'test':
        # Add test post and click
        tracker.track_post(
            business_id='marceau-solutions',
            platform='twitter',
            post_id='test_post_123',
            campaign='ai_automation_jan26',
            utm_link='https://marceausolutions.com?utm_source=twitter&utm_campaign=ai_automation_jan26&utm_content=test_post_123',
            post_content='Test post about AI automation'
        )

        tracker.track_click(
            utm_link='https://marceausolutions.com?utm_source=twitter&utm_campaign=ai_automation_jan26&utm_content=test_post_123',
            visitor_info={'ip': '1.2.3.4'}
        )

        print("\n✓ Test post and click tracked")
        print("\nRun: python -m src.social_media_tracker status")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
