#!/usr/bin/env python3
"""
post_analytics.py - Social Media Post Performance Tracking

Tracks post performance metrics to optimize content strategy:
- Engagement rates (likes, retweets, replies, impressions)
- Image vs non-image post comparison
- Template performance analysis
- Time-of-day effectiveness
- ROI for Grok-generated images

Usage:
    # Record post metrics after posting
    python -m src.post_analytics record --post-id 123 --impressions 1000 --likes 50 --retweets 10

    # Import metrics from X API
    python -m src.post_analytics import-from-x --days 7

    # View performance report
    python -m src.post_analytics report

    # Compare image vs non-image posts
    python -m src.post_analytics compare-media

    # Analyze template performance
    python -m src.post_analytics templates

    # Get best posting times
    python -m src.post_analytics best-times
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
ANALYTICS_PATH = PROJECT_ROOT / "output" / "post_analytics.json"
POSTED_QUEUE_PATH = PROJECT_ROOT / "output" / "scheduled_posts.json"


@dataclass
class PostMetrics:
    """Metrics for a single post."""
    post_id: str
    business_id: str
    content: str
    template_type: str
    campaign: str
    posted_at: str  # ISO timestamp
    has_image: bool
    image_cost: float  # $0.07 if Grok-generated, 0 otherwise

    # Engagement metrics (collected from X API)
    impressions: int = 0
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    profile_clicks: int = 0
    link_clicks: int = 0

    # Calculated metrics
    engagement_rate: float = 0.0  # (likes + retweets + replies) / impressions
    cost_per_engagement: float = 0.0  # image_cost / total_engagements

    # Metadata
    hour_posted: int = 0  # 0-23
    day_of_week: str = ""  # "monday", "tuesday", etc.
    recorded_at: str = ""  # When metrics were last updated


class PostAnalytics:
    """
    Track and analyze social media post performance.
    """

    def __init__(self):
        self.analytics = self._load_analytics()

    def _load_analytics(self) -> Dict:
        """Load existing analytics data."""
        if ANALYTICS_PATH.exists():
            with open(ANALYTICS_PATH) as f:
                return json.load(f)
        return {
            "posts": [],
            "summary": {
                "total_posts": 0,
                "posts_with_images": 0,
                "total_impressions": 0,
                "total_engagements": 0,
                "total_image_cost": 0.0
            }
        }

    def _save_analytics(self):
        """Save analytics data."""
        ANALYTICS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(ANALYTICS_PATH, 'w') as f:
            json.dump(self.analytics, f, indent=2, default=str)

    def record_post_metrics(
        self,
        post_id: str,
        business_id: str,
        content: str,
        template_type: str,
        campaign: str,
        posted_at: str,
        has_image: bool,
        impressions: int = 0,
        likes: int = 0,
        retweets: int = 0,
        replies: int = 0,
        profile_clicks: int = 0,
        link_clicks: int = 0
    ) -> PostMetrics:
        """
        Record metrics for a post.

        Args:
            post_id: Unique post identifier (X tweet ID)
            business_id: Which business this post is for
            content: Post text content
            template_type: Template used
            campaign: Campaign name
            posted_at: ISO timestamp when posted
            has_image: Whether post includes Grok-generated image
            impressions: Number of times post was seen
            likes: Number of likes
            retweets: Number of retweets
            replies: Number of replies
            profile_clicks: Clicks to profile
            link_clicks: Clicks on links

        Returns:
            PostMetrics object with calculated fields
        """
        # Parse posted_at to get hour and day
        dt = datetime.fromisoformat(posted_at.replace('Z', '+00:00'))
        hour_posted = dt.hour
        day_of_week = dt.strftime('%A').lower()

        # Calculate engagement rate
        total_engagements = likes + retweets + replies
        engagement_rate = (total_engagements / impressions * 100) if impressions > 0 else 0.0

        # Calculate cost per engagement
        image_cost = 0.07 if has_image else 0.0
        cost_per_engagement = (image_cost / total_engagements) if total_engagements > 0 else 0.0

        metrics = PostMetrics(
            post_id=post_id,
            business_id=business_id,
            content=content,
            template_type=template_type,
            campaign=campaign,
            posted_at=posted_at,
            has_image=has_image,
            image_cost=image_cost,
            impressions=impressions,
            likes=likes,
            retweets=retweets,
            replies=replies,
            profile_clicks=profile_clicks,
            link_clicks=link_clicks,
            engagement_rate=engagement_rate,
            cost_per_engagement=cost_per_engagement,
            hour_posted=hour_posted,
            day_of_week=day_of_week,
            recorded_at=datetime.now().isoformat()
        )

        # Update or add to analytics
        existing = next(
            (i for i, p in enumerate(self.analytics["posts"]) if p["post_id"] == post_id),
            None
        )

        if existing is not None:
            self.analytics["posts"][existing] = asdict(metrics)
        else:
            self.analytics["posts"].append(asdict(metrics))

        # Update summary
        self._update_summary()
        self._save_analytics()

        return metrics

    def _update_summary(self):
        """Recalculate summary statistics."""
        posts = self.analytics["posts"]

        self.analytics["summary"] = {
            "total_posts": len(posts),
            "posts_with_images": sum(1 for p in posts if p["has_image"]),
            "total_impressions": sum(p["impressions"] for p in posts),
            "total_engagements": sum(
                p["likes"] + p["retweets"] + p["replies"] for p in posts
            ),
            "total_image_cost": sum(p["image_cost"] for p in posts),
            "avg_engagement_rate": sum(p["engagement_rate"] for p in posts) / len(posts) if posts else 0.0,
            "last_updated": datetime.now().isoformat()
        }

    def compare_media_performance(self) -> Dict:
        """
        Compare performance of posts with vs without images.

        Returns:
            Dict with comparison metrics
        """
        posts = self.analytics["posts"]

        with_images = [p for p in posts if p["has_image"]]
        without_images = [p for p in posts if not p["has_image"]]

        def avg(posts, field):
            return sum(p[field] for p in posts) / len(posts) if posts else 0

        return {
            "with_images": {
                "count": len(with_images),
                "avg_impressions": avg(with_images, "impressions"),
                "avg_likes": avg(with_images, "likes"),
                "avg_retweets": avg(with_images, "retweets"),
                "avg_engagement_rate": avg(with_images, "engagement_rate"),
                "total_cost": sum(p["image_cost"] for p in with_images),
                "avg_cost_per_engagement": avg(with_images, "cost_per_engagement")
            },
            "without_images": {
                "count": len(without_images),
                "avg_impressions": avg(without_images, "impressions"),
                "avg_likes": avg(without_images, "likes"),
                "avg_retweets": avg(without_images, "retweets"),
                "avg_engagement_rate": avg(without_images, "engagement_rate"),
            },
            "lift": {
                "impressions": (
                    (avg(with_images, "impressions") - avg(without_images, "impressions"))
                    / avg(without_images, "impressions") * 100
                ) if without_images else 0,
                "engagement_rate": (
                    (avg(with_images, "engagement_rate") - avg(without_images, "engagement_rate"))
                    / avg(without_images, "engagement_rate") * 100
                ) if without_images else 0
            }
        }

    def analyze_template_performance(self) -> Dict:
        """
        Analyze which templates perform best.

        Returns:
            Dict mapping template_type to performance metrics
        """
        posts = self.analytics["posts"]

        by_template = defaultdict(list)
        for p in posts:
            by_template[p["template_type"]].append(p)

        results = {}
        for template, template_posts in by_template.items():
            results[template] = {
                "count": len(template_posts),
                "avg_impressions": sum(p["impressions"] for p in template_posts) / len(template_posts),
                "avg_engagement_rate": sum(p["engagement_rate"] for p in template_posts) / len(template_posts),
                "total_engagements": sum(
                    p["likes"] + p["retweets"] + p["replies"] for p in template_posts
                )
            }

        # Sort by engagement rate
        results = dict(sorted(results.items(), key=lambda x: x[1]["avg_engagement_rate"], reverse=True))

        return results

    def find_best_posting_times(self) -> Dict:
        """
        Identify best hours and days for posting.

        Returns:
            Dict with best hours and days of week
        """
        posts = self.analytics["posts"]

        by_hour = defaultdict(list)
        by_day = defaultdict(list)

        for p in posts:
            by_hour[p["hour_posted"]].append(p)
            by_day[p["day_of_week"]].append(p)

        # Calculate avg engagement rate per hour
        hour_performance = {}
        for hour, hour_posts in by_hour.items():
            hour_performance[hour] = {
                "count": len(hour_posts),
                "avg_engagement_rate": sum(p["engagement_rate"] for p in hour_posts) / len(hour_posts)
            }

        # Calculate avg engagement rate per day
        day_performance = {}
        for day, day_posts in by_day.items():
            day_performance[day] = {
                "count": len(day_posts),
                "avg_engagement_rate": sum(p["engagement_rate"] for p in day_posts) / len(day_posts)
            }

        # Sort by engagement rate
        best_hours = sorted(hour_performance.items(), key=lambda x: x[1]["avg_engagement_rate"], reverse=True)
        best_days = sorted(day_performance.items(), key=lambda x: x[1]["avg_engagement_rate"], reverse=True)

        return {
            "best_hours": best_hours[:5],  # Top 5 hours
            "best_days": best_days[:3],    # Top 3 days
            "all_hours": hour_performance,
            "all_days": day_performance
        }

    def generate_report(self) -> str:
        """
        Generate comprehensive performance report.

        Returns:
            Formatted report string
        """
        summary = self.analytics["summary"]
        media_comparison = self.compare_media_performance()
        template_perf = self.analyze_template_performance()
        best_times = self.find_best_posting_times()

        report = []
        report.append("=" * 70)
        report.append("SOCIAL MEDIA POST PERFORMANCE REPORT")
        report.append("=" * 70)
        report.append("")

        # Summary
        report.append("SUMMARY")
        report.append("-" * 70)
        report.append(f"Total Posts: {summary['total_posts']}")
        report.append(f"Posts with Images: {summary['posts_with_images']} ({summary['posts_with_images']/summary['total_posts']*100:.1f}%)" if summary['total_posts'] > 0 else "Posts with Images: 0")
        report.append(f"Total Impressions: {summary['total_impressions']:,}")
        report.append(f"Total Engagements: {summary['total_engagements']:,}")
        report.append(f"Avg Engagement Rate: {summary['avg_engagement_rate']:.2f}%")
        report.append(f"Total Image Cost: ${summary['total_image_cost']:.2f}")
        report.append("")

        # Media comparison
        report.append("IMAGE VS NON-IMAGE PERFORMANCE")
        report.append("-" * 70)
        with_img = media_comparison["with_images"]
        without_img = media_comparison["without_images"]
        lift = media_comparison["lift"]

        report.append(f"\nWith Images ({with_img['count']} posts):")
        report.append(f"  Avg Impressions: {with_img['avg_impressions']:.0f}")
        report.append(f"  Avg Engagement Rate: {with_img['avg_engagement_rate']:.2f}%")
        report.append(f"  Total Cost: ${with_img['total_cost']:.2f}")
        report.append(f"  Cost per Engagement: ${with_img['avg_cost_per_engagement']:.4f}")

        report.append(f"\nWithout Images ({without_img['count']} posts):")
        report.append(f"  Avg Impressions: {without_img['avg_impressions']:.0f}")
        report.append(f"  Avg Engagement Rate: {without_img['avg_engagement_rate']:.2f}%")

        report.append(f"\nLift from Images:")
        report.append(f"  Impressions: {lift['impressions']:+.1f}%")
        report.append(f"  Engagement Rate: {lift['engagement_rate']:+.1f}%")
        report.append("")

        # Template performance
        report.append("TOP PERFORMING TEMPLATES")
        report.append("-" * 70)
        for i, (template, metrics) in enumerate(list(template_perf.items())[:5], 1):
            report.append(f"{i}. {template}")
            report.append(f"   Posts: {metrics['count']}, Avg Engagement: {metrics['avg_engagement_rate']:.2f}%")
        report.append("")

        # Best times
        report.append("BEST POSTING TIMES")
        report.append("-" * 70)
        report.append("Top Hours:")
        for hour, metrics in best_times["best_hours"]:
            report.append(f"  {hour}:00 - Engagement: {metrics['avg_engagement_rate']:.2f}% ({metrics['count']} posts)")

        report.append("\nTop Days:")
        for day, metrics in best_times["best_days"]:
            report.append(f"  {day.capitalize()} - Engagement: {metrics['avg_engagement_rate']:.2f}% ({metrics['count']} posts)")

        report.append("")
        report.append("=" * 70)

        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="Social Media Post Analytics")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # record command
    record_parser = subparsers.add_parser("record", help="Record post metrics")
    record_parser.add_argument("--post-id", required=True, help="Post/tweet ID")
    record_parser.add_argument("--business-id", required=True, help="Business ID")
    record_parser.add_argument("--content", required=True, help="Post content")
    record_parser.add_argument("--template", required=True, help="Template type")
    record_parser.add_argument("--campaign", default="general", help="Campaign name")
    record_parser.add_argument("--posted-at", required=True, help="Posted timestamp (ISO)")
    record_parser.add_argument("--has-image", action="store_true", help="Post has image")
    record_parser.add_argument("--impressions", type=int, default=0)
    record_parser.add_argument("--likes", type=int, default=0)
    record_parser.add_argument("--retweets", type=int, default=0)
    record_parser.add_argument("--replies", type=int, default=0)

    # report command
    report_parser = subparsers.add_parser("report", help="Generate performance report")

    # compare-media command
    compare_parser = subparsers.add_parser("compare-media", help="Compare image vs non-image")

    # templates command
    templates_parser = subparsers.add_parser("templates", help="Analyze template performance")

    # best-times command
    times_parser = subparsers.add_parser("best-times", help="Find best posting times")

    args = parser.parse_args()
    analytics = PostAnalytics()

    if args.command == "record":
        metrics = analytics.record_post_metrics(
            post_id=args.post_id,
            business_id=args.business_id,
            content=args.content,
            template_type=args.template,
            campaign=args.campaign,
            posted_at=args.posted_at,
            has_image=args.has_image,
            impressions=args.impressions,
            likes=args.likes,
            retweets=args.retweets,
            replies=args.replies
        )
        print(f"✅ Recorded metrics for post {args.post_id}")
        print(f"Engagement rate: {metrics.engagement_rate:.2f}%")
        if metrics.has_image:
            print(f"Cost per engagement: ${metrics.cost_per_engagement:.4f}")

    elif args.command == "report":
        report = analytics.generate_report()
        print(report)

    elif args.command == "compare-media":
        comparison = analytics.compare_media_performance()
        print("\n" + "=" * 50)
        print("IMAGE VS NON-IMAGE COMPARISON")
        print("=" * 50)
        print(json.dumps(comparison, indent=2))

    elif args.command == "templates":
        templates = analytics.analyze_template_performance()
        print("\n" + "=" * 50)
        print("TEMPLATE PERFORMANCE")
        print("=" * 50)
        for template, metrics in templates.items():
            print(f"\n{template}:")
            print(f"  Count: {metrics['count']}")
            print(f"  Avg Engagement Rate: {metrics['avg_engagement_rate']:.2f}%")

    elif args.command == "best-times":
        times = analytics.find_best_posting_times()
        print("\n" + "=" * 50)
        print("BEST POSTING TIMES")
        print("=" * 50)
        print("\nTop 5 Hours:")
        for hour, metrics in times["best_hours"]:
            print(f"  {hour}:00 - {metrics['avg_engagement_rate']:.2f}% ({metrics['count']} posts)")
        print("\nTop 3 Days:")
        for day, metrics in times["best_days"]:
            print(f"  {day.capitalize()} - {metrics['avg_engagement_rate']:.2f}% ({metrics['count']} posts)")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
