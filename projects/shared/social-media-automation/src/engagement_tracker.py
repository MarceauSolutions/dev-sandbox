#!/usr/bin/env python3
"""
engagement_tracker.py - X Platform Analytics and Engagement Tracking

Tracks:
- Tweet performance (likes, retweets, replies, impressions)
- Engagement rates over time
- Campaign effectiveness
- Conversion funnel (post → click → landing page → form submission)

Usage:
    # Update engagement for recent tweets
    python -m src.engagement_tracker update

    # View engagement report
    python -m src.engagement_tracker report --campaign fitness-launch

    # Export to CSV
    python -m src.engagement_tracker export
"""

import os
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict, field
import logging

from dotenv import load_dotenv
load_dotenv()

from .x_api import XClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TweetMetrics:
    """Metrics for a single tweet."""
    tweet_id: str
    text: str
    created_at: str
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    quotes: int = 0
    impressions: int = 0
    url_clicks: int = 0
    profile_clicks: int = 0
    engagement_rate: float = 0.0
    campaign: Optional[str] = None
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CampaignMetrics:
    """Aggregated metrics for a campaign."""
    campaign: str
    total_tweets: int = 0
    total_likes: int = 0
    total_retweets: int = 0
    total_replies: int = 0
    total_impressions: int = 0
    avg_engagement_rate: float = 0.0
    best_performing_tweet: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class EngagementTracker:
    """
    Tracks and analyzes engagement metrics for X posts.
    """

    METRICS_FILE = Path(__file__).parent.parent / "output" / "tweet_metrics.json"
    CAMPAIGNS_FILE = Path(__file__).parent.parent / "output" / "campaign_metrics.json"
    HISTORY_FILE = Path(__file__).parent.parent / "output" / "post_history.json"

    def __init__(self):
        self.client = XClient()
        self.metrics = self._load_metrics()
        self.campaigns = self._load_campaigns()

    def _load_metrics(self) -> Dict[str, TweetMetrics]:
        """Load tweet metrics from file."""
        if self.METRICS_FILE.exists():
            try:
                with open(self.METRICS_FILE) as f:
                    data = json.load(f)
                return {k: TweetMetrics(**v) for k, v in data.items()}
            except Exception as e:
                logger.warning(f"Error loading metrics: {e}")
        return {}

    def _save_metrics(self):
        """Save tweet metrics to file."""
        self.METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.METRICS_FILE, 'w') as f:
            json.dump({k: asdict(v) for k, v in self.metrics.items()}, f, indent=2)

    def _load_campaigns(self) -> Dict[str, CampaignMetrics]:
        """Load campaign metrics."""
        if self.CAMPAIGNS_FILE.exists():
            try:
                with open(self.CAMPAIGNS_FILE) as f:
                    data = json.load(f)
                return {k: CampaignMetrics(**v) for k, v in data.items()}
            except Exception:
                pass
        return {}

    def _save_campaigns(self):
        """Save campaign metrics."""
        self.CAMPAIGNS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.CAMPAIGNS_FILE, 'w') as f:
            json.dump({k: asdict(v) for k, v in self.campaigns.items()}, f, indent=2)

    def _load_post_history(self) -> List[Dict]:
        """Load post history for tweet IDs."""
        if self.HISTORY_FILE.exists():
            try:
                with open(self.HISTORY_FILE) as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def fetch_tweet_metrics(self, tweet_id: str) -> Optional[TweetMetrics]:
        """
        Fetch metrics for a specific tweet from X API.

        Args:
            tweet_id: Tweet ID to fetch

        Returns:
            TweetMetrics or None
        """
        tweet_data = self.client.get_tweet(tweet_id)
        if not tweet_data:
            return None

        metrics = tweet_data.get('metrics', {})

        # Calculate engagement rate
        impressions = metrics.get('impression_count', 0)
        engagements = (
            metrics.get('like_count', 0) +
            metrics.get('retweet_count', 0) +
            metrics.get('reply_count', 0) +
            metrics.get('quote_count', 0)
        )
        engagement_rate = (engagements / impressions * 100) if impressions > 0 else 0

        # Get campaign from history
        campaign = None
        history = self._load_post_history()
        for post in history:
            if post.get('tweet_id') == tweet_id:
                campaign = post.get('campaign')
                break

        return TweetMetrics(
            tweet_id=tweet_id,
            text=tweet_data.get('text', ''),
            created_at=tweet_data.get('created_at', ''),
            likes=metrics.get('like_count', 0),
            retweets=metrics.get('retweet_count', 0),
            replies=metrics.get('reply_count', 0),
            quotes=metrics.get('quote_count', 0),
            impressions=impressions,
            engagement_rate=round(engagement_rate, 2),
            campaign=campaign
        )

    def update_metrics(self, tweet_ids: Optional[List[str]] = None) -> int:
        """
        Update metrics for tweets.

        Args:
            tweet_ids: Specific tweet IDs to update (or all from history)

        Returns:
            Number of tweets updated
        """
        if not self.client.is_ready():
            logger.warning("X client not ready. Check credentials.")
            return 0

        # Get tweet IDs from history if not provided
        if tweet_ids is None:
            history = self._load_post_history()
            tweet_ids = [p['tweet_id'] for p in history if p.get('tweet_id')]

        updated = 0
        for tweet_id in tweet_ids:
            try:
                metrics = self.fetch_tweet_metrics(tweet_id)
                if metrics:
                    self.metrics[tweet_id] = metrics
                    updated += 1
                    logger.info(f"Updated metrics for {tweet_id}")
            except Exception as e:
                logger.warning(f"Error updating {tweet_id}: {e}")

        self._save_metrics()
        self._update_campaign_metrics()
        return updated

    def _update_campaign_metrics(self):
        """Recalculate campaign-level metrics."""
        campaigns: Dict[str, List[TweetMetrics]] = {}

        # Group metrics by campaign
        for metrics in self.metrics.values():
            if metrics.campaign:
                if metrics.campaign not in campaigns:
                    campaigns[metrics.campaign] = []
                campaigns[metrics.campaign].append(metrics)

        # Calculate aggregates
        for campaign_name, tweets in campaigns.items():
            total_engagement = sum(t.likes + t.retweets + t.replies for t in tweets)
            total_impressions = sum(t.impressions for t in tweets)

            avg_rate = (total_engagement / total_impressions * 100) if total_impressions > 0 else 0

            best_tweet = max(tweets, key=lambda t: t.engagement_rate) if tweets else None

            dates = [t.created_at for t in tweets if t.created_at]
            start_date = min(dates) if dates else None
            end_date = max(dates) if dates else None

            self.campaigns[campaign_name] = CampaignMetrics(
                campaign=campaign_name,
                total_tweets=len(tweets),
                total_likes=sum(t.likes for t in tweets),
                total_retweets=sum(t.retweets for t in tweets),
                total_replies=sum(t.replies for t in tweets),
                total_impressions=total_impressions,
                avg_engagement_rate=round(avg_rate, 2),
                best_performing_tweet=best_tweet.tweet_id if best_tweet else None,
                start_date=start_date,
                end_date=end_date
            )

        self._save_campaigns()

    def get_campaign_report(self, campaign: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate engagement report.

        Args:
            campaign: Filter by campaign name (optional)

        Returns:
            Report dictionary
        """
        if campaign and campaign in self.campaigns:
            c = self.campaigns[campaign]
            tweets = [m for m in self.metrics.values() if m.campaign == campaign]

            return {
                "campaign": campaign,
                "summary": {
                    "total_tweets": c.total_tweets,
                    "total_likes": c.total_likes,
                    "total_retweets": c.total_retweets,
                    "total_replies": c.total_replies,
                    "total_impressions": c.total_impressions,
                    "avg_engagement_rate": f"{c.avg_engagement_rate}%"
                },
                "date_range": {
                    "start": c.start_date,
                    "end": c.end_date
                },
                "best_tweet": c.best_performing_tweet,
                "tweets": [
                    {
                        "id": t.tweet_id,
                        "text": t.text[:50] + "..." if len(t.text) > 50 else t.text,
                        "likes": t.likes,
                        "retweets": t.retweets,
                        "engagement_rate": f"{t.engagement_rate}%"
                    }
                    for t in sorted(tweets, key=lambda x: x.engagement_rate, reverse=True)
                ]
            }

        # Overall report
        total_tweets = len(self.metrics)
        total_likes = sum(m.likes for m in self.metrics.values())
        total_retweets = sum(m.retweets for m in self.metrics.values())
        total_impressions = sum(m.impressions for m in self.metrics.values())

        return {
            "overall": {
                "total_tweets": total_tweets,
                "total_likes": total_likes,
                "total_retweets": total_retweets,
                "total_impressions": total_impressions,
                "avg_engagement_rate": f"{(total_likes + total_retweets) / total_impressions * 100:.2f}%" if total_impressions > 0 else "0%"
            },
            "campaigns": {
                name: {
                    "tweets": c.total_tweets,
                    "engagement_rate": f"{c.avg_engagement_rate}%"
                }
                for name, c in self.campaigns.items()
            },
            "top_tweets": [
                {
                    "id": t.tweet_id,
                    "text": t.text[:50] + "...",
                    "engagement_rate": f"{t.engagement_rate}%"
                }
                for t in sorted(
                    self.metrics.values(),
                    key=lambda x: x.engagement_rate,
                    reverse=True
                )[:5]
            ]
        }

    def get_daily_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get daily engagement statistics.

        Args:
            days: Number of days to include

        Returns:
            List of daily stats
        """
        cutoff = datetime.now() - timedelta(days=days)
        daily_stats = {}

        for metrics in self.metrics.values():
            if not metrics.created_at:
                continue

            try:
                tweet_date = datetime.fromisoformat(metrics.created_at.replace('Z', '+00:00'))
                if tweet_date < cutoff:
                    continue

                date_key = tweet_date.strftime('%Y-%m-%d')
                if date_key not in daily_stats:
                    daily_stats[date_key] = {
                        "date": date_key,
                        "tweets": 0,
                        "likes": 0,
                        "retweets": 0,
                        "impressions": 0
                    }

                daily_stats[date_key]["tweets"] += 1
                daily_stats[date_key]["likes"] += metrics.likes
                daily_stats[date_key]["retweets"] += metrics.retweets
                daily_stats[date_key]["impressions"] += metrics.impressions

            except Exception:
                continue

        return sorted(daily_stats.values(), key=lambda x: x['date'])

    def export_to_csv(self, filepath: Optional[str] = None) -> str:
        """
        Export metrics to CSV.

        Args:
            filepath: Output file path (optional)

        Returns:
            Path to exported file
        """
        if not filepath:
            filepath = str(self.METRICS_FILE.parent / f"engagement_export_{datetime.now().strftime('%Y%m%d')}.csv")

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'tweet_id', 'text', 'created_at', 'campaign',
                'likes', 'retweets', 'replies', 'impressions', 'engagement_rate'
            ])

            for metrics in self.metrics.values():
                writer.writerow([
                    metrics.tweet_id,
                    metrics.text,
                    metrics.created_at,
                    metrics.campaign or '',
                    metrics.likes,
                    metrics.retweets,
                    metrics.replies,
                    metrics.impressions,
                    metrics.engagement_rate
                ])

        logger.info(f"Exported to {filepath}")
        return filepath

    def get_conversion_funnel(self, campaign: Optional[str] = None) -> Dict[str, Any]:
        """
        Get conversion funnel metrics.

        Tracks: Post → Impressions → Engagements → Clicks → Conversions

        Args:
            campaign: Filter by campaign

        Returns:
            Funnel metrics
        """
        if campaign:
            tweets = [m for m in self.metrics.values() if m.campaign == campaign]
        else:
            tweets = list(self.metrics.values())

        if not tweets:
            return {"error": "No tweets found"}

        total_impressions = sum(t.impressions for t in tweets)
        total_engagements = sum(t.likes + t.retweets + t.replies for t in tweets)
        total_clicks = sum(t.url_clicks for t in tweets)

        # Load link clicks for conversion tracking
        link_manager_file = Path(__file__).parent.parent / "output" / "tracked_links.json"
        link_clicks = 0
        if link_manager_file.exists():
            try:
                with open(link_manager_file) as f:
                    links = json.load(f)
                if campaign:
                    link_clicks = sum(
                        l.get('click_count', 0) for l in links.values()
                        if l.get('utm_campaign') == campaign
                    )
                else:
                    link_clicks = sum(l.get('click_count', 0) for l in links.values())
            except Exception:
                pass

        return {
            "campaign": campaign or "all",
            "funnel": {
                "posts": len(tweets),
                "impressions": total_impressions,
                "engagements": total_engagements,
                "url_clicks": total_clicks or link_clicks,
                "conversions": 0  # Would need form submission tracking
            },
            "rates": {
                "impression_to_engagement": f"{total_engagements / total_impressions * 100:.2f}%" if total_impressions > 0 else "0%",
                "engagement_to_click": f"{(total_clicks or link_clicks) / total_engagements * 100:.2f}%" if total_engagements > 0 else "0%"
            }
        }


def main():
    """CLI for engagement tracker."""
    import argparse

    parser = argparse.ArgumentParser(description='X Engagement Tracker')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Update command
    update_parser = subparsers.add_parser('update', help='Update tweet metrics')
    update_parser.add_argument('--tweet-id', help='Specific tweet ID')

    # Report command
    report_parser = subparsers.add_parser('report', help='Generate engagement report')
    report_parser.add_argument('--campaign', help='Filter by campaign')

    # Daily command
    daily_parser = subparsers.add_parser('daily', help='Daily statistics')
    daily_parser.add_argument('--days', type=int, default=7, help='Number of days')

    # Funnel command
    funnel_parser = subparsers.add_parser('funnel', help='Conversion funnel')
    funnel_parser.add_argument('--campaign', help='Filter by campaign')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export to CSV')
    export_parser.add_argument('--output', help='Output file path')

    args = parser.parse_args()

    tracker = EngagementTracker()

    if args.command == 'update':
        tweet_ids = [args.tweet_id] if args.tweet_id else None
        count = tracker.update_metrics(tweet_ids)
        print(f"\nUpdated metrics for {count} tweets")

    elif args.command == 'report':
        report = tracker.get_campaign_report(args.campaign)

        if args.campaign:
            print(f"\nCampaign Report: {args.campaign}")
            print("=" * 50)
            summary = report.get('summary', {})
            print(f"  Tweets: {summary.get('total_tweets', 0)}")
            print(f"  Likes: {summary.get('total_likes', 0)}")
            print(f"  Retweets: {summary.get('total_retweets', 0)}")
            print(f"  Impressions: {summary.get('total_impressions', 0)}")
            print(f"  Avg Engagement: {summary.get('avg_engagement_rate', '0%')}")

            if report.get('tweets'):
                print(f"\nTop Tweets:")
                for t in report['tweets'][:3]:
                    print(f"  [{t['engagement_rate']}] {t['text']}")
        else:
            print("\nOverall Engagement Report")
            print("=" * 50)
            overall = report.get('overall', {})
            print(f"  Total Tweets: {overall.get('total_tweets', 0)}")
            print(f"  Total Likes: {overall.get('total_likes', 0)}")
            print(f"  Total Impressions: {overall.get('total_impressions', 0)}")
            print(f"  Avg Engagement: {overall.get('avg_engagement_rate', '0%')}")

            if report.get('campaigns'):
                print(f"\nBy Campaign:")
                for name, data in report['campaigns'].items():
                    print(f"  {name}: {data['tweets']} tweets, {data['engagement_rate']}")

    elif args.command == 'daily':
        stats = tracker.get_daily_stats(args.days)
        print(f"\nDaily Stats (last {args.days} days)")
        print("=" * 50)
        for day in stats:
            print(f"  {day['date']}: {day['tweets']} tweets, {day['likes']} likes, {day['impressions']} impressions")

    elif args.command == 'funnel':
        funnel = tracker.get_conversion_funnel(args.campaign)
        print(f"\nConversion Funnel: {funnel.get('campaign', 'all')}")
        print("=" * 50)
        f = funnel.get('funnel', {})
        print(f"  Posts: {f.get('posts', 0)}")
        print(f"  Impressions: {f.get('impressions', 0)}")
        print(f"  Engagements: {f.get('engagements', 0)}")
        print(f"  URL Clicks: {f.get('url_clicks', 0)}")

        r = funnel.get('rates', {})
        print(f"\n  Impression → Engagement: {r.get('impression_to_engagement', '0%')}")
        print(f"  Engagement → Click: {r.get('engagement_to_click', '0%')}")

    elif args.command == 'export':
        filepath = tracker.export_to_csv(args.output)
        print(f"\nExported to: {filepath}")

    else:
        parser.print_help()

    return 0


if __name__ == '__main__':
    exit(main())
