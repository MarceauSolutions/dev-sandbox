#!/usr/bin/env python3
"""
social_media_status.py - Social Media Status Dashboard

Provides a unified view of:
- Post queue status (pending, posted, failed, overdue)
- Rate limit status
- Recent errors
- System health metrics

Usage:
    python -m src.social_media_status
    python -m src.social_media_status --format json
    python -m src.social_media_status --errors
    python -m src.social_media_status --overdue
"""

import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Import from local modules
from .x_scheduler import PostScheduler, PostStatus
from .x_api import XClient


@dataclass
class StatusSummary:
    """Summary of social media system status."""
    total_posts: int = 0
    pending: int = 0
    scheduled: int = 0
    posted: int = 0
    failed: int = 0
    archived: int = 0
    cancelled: int = 0
    overdue: int = 0
    retryable_failed: int = 0


class SocialMediaDashboard:
    """
    Dashboard for monitoring social media automation health.
    """

    OUTPUT_DIR = Path(__file__).parent.parent / "output"

    def __init__(self):
        self.scheduler = PostScheduler()
        self.client = XClient()

    def get_summary(self) -> StatusSummary:
        """Get overall status summary."""
        summary = StatusSummary()
        now = datetime.now()

        for post in self.scheduler.queue:
            summary.total_posts += 1

            # Count by status
            if post.status == PostStatus.PENDING.value:
                summary.pending += 1
            elif post.status == PostStatus.SCHEDULED.value:
                summary.scheduled += 1
            elif post.status == PostStatus.POSTED.value:
                summary.posted += 1
            elif post.status == PostStatus.FAILED.value:
                summary.failed += 1
                # Check if retryable
                if post.error_type in ['retryable', 'unknown', None] and post.retry_count < post.max_retries:
                    summary.retryable_failed += 1
            elif post.status == PostStatus.ARCHIVED.value:
                summary.archived += 1
            elif post.status == PostStatus.CANCELLED.value:
                summary.cancelled += 1

            # Check if overdue
            if post.status in [PostStatus.PENDING.value, PostStatus.SCHEDULED.value]:
                if post.scheduled_time:
                    try:
                        scheduled = datetime.fromisoformat(post.scheduled_time)
                        if scheduled < now:
                            summary.overdue += 1
                    except (ValueError, TypeError):
                        pass

        return summary

    def get_overdue_posts(self) -> List[Dict[str, Any]]:
        """Get list of overdue posts with details."""
        now = datetime.now()
        overdue = []

        for post in self.scheduler.queue:
            if post.status not in [PostStatus.PENDING.value, PostStatus.SCHEDULED.value]:
                continue

            if not post.scheduled_time:
                continue

            try:
                scheduled = datetime.fromisoformat(post.scheduled_time)
                if scheduled < now:
                    hours_overdue = (now - scheduled).total_seconds() / 3600
                    overdue.append({
                        "id": post.id,
                        "text": post.text[:50] + "..." if len(post.text) > 50 else post.text,
                        "scheduled_time": post.scheduled_time,
                        "hours_overdue": round(hours_overdue, 1),
                        "status": post.status,
                        "retry_count": post.retry_count,
                        "campaign": post.campaign
                    })
            except (ValueError, TypeError):
                pass

        # Sort by most overdue first
        overdue.sort(key=lambda p: p["hours_overdue"], reverse=True)
        return overdue

    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent errors with details."""
        errors = []

        for post in self.scheduler.queue:
            if post.status not in [PostStatus.FAILED.value, PostStatus.ARCHIVED.value]:
                continue

            if not post.error:
                continue

            errors.append({
                "id": post.id,
                "text": post.text[:50] + "..." if len(post.text) > 50 else post.text,
                "error": post.error,
                "error_type": post.error_type or "unknown",
                "status": post.status,
                "retry_count": post.retry_count,
                "last_retry_at": post.last_retry_at,
                "campaign": post.campaign
            })

        # Sort by last_retry_at (most recent first), then by status
        errors.sort(key=lambda e: (e["last_retry_at"] or "0000", e["status"]), reverse=True)
        return errors[:limit]

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        return self.client.get_rate_limit_status()

    def get_posting_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get posting statistics for the last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        stats = {
            "period_days": days,
            "posts_sent": 0,
            "by_campaign": {},
            "by_day": {}
        }

        for entry in self.scheduler.history:
            posted_at = entry.get("posted_at")
            if not posted_at:
                continue

            try:
                post_time = datetime.fromisoformat(posted_at)
                if post_time < cutoff:
                    continue

                stats["posts_sent"] += 1

                # Count by campaign
                campaign = entry.get("campaign", "unknown")
                stats["by_campaign"][campaign] = stats["by_campaign"].get(campaign, 0) + 1

                # Count by day
                day = post_time.strftime("%Y-%m-%d")
                stats["by_day"][day] = stats["by_day"].get(day, 0) + 1

            except (ValueError, TypeError):
                pass

        return stats

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status."""
        summary = self.get_summary()
        rate_limit = self.get_rate_limit_status()
        overdue = self.get_overdue_posts()

        # Calculate health score (0-100)
        health_score = 100

        # Deduct for overdue posts
        if summary.overdue > 0:
            health_score -= min(30, summary.overdue * 2)  # Max 30 point deduction

        # Deduct for failed posts
        if summary.failed > 0:
            health_score -= min(20, summary.failed * 2)  # Max 20 point deduction

        # Deduct for rate limit issues
        if rate_limit.get("in_backoff"):
            health_score -= 20

        if not rate_limit.get("can_post"):
            health_score -= 10

        # Determine status
        if health_score >= 80:
            status = "healthy"
        elif health_score >= 50:
            status = "degraded"
        else:
            status = "critical"

        # Find most critical issue
        critical_issue = None
        if rate_limit.get("in_backoff"):
            critical_issue = f"In rate limit backoff ({rate_limit.get('backoff_remaining_seconds', 0)}s remaining)"
        elif len(overdue) > 10:
            critical_issue = f"{len(overdue)} posts are overdue"
        elif summary.failed > 5:
            critical_issue = f"{summary.failed} posts have failed"

        return {
            "status": status,
            "health_score": max(0, health_score),
            "critical_issue": critical_issue,
            "summary": {
                "total": summary.total_posts,
                "pending": summary.pending,
                "scheduled": summary.scheduled,
                "posted": summary.posted,
                "failed": summary.failed,
                "archived": summary.archived,
                "overdue": summary.overdue,
                "retryable_failed": summary.retryable_failed
            },
            "rate_limit": {
                "can_post": rate_limit.get("can_post"),
                "posts_today": rate_limit.get("posts_today"),
                "posts_remaining_today": rate_limit.get("posts_remaining_today"),
                "in_backoff": rate_limit.get("in_backoff"),
                "backoff_remaining": rate_limit.get("backoff_remaining_seconds", 0)
            }
        }

    def print_dashboard(self):
        """Print formatted dashboard to console."""
        health = self.get_health_status()
        summary = health["summary"]
        rate_limit = health["rate_limit"]

        # Header
        print("\n" + "=" * 60)
        print("SOCIAL MEDIA STATUS DASHBOARD")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # Health Status
        status_emoji = {"healthy": "[OK]", "degraded": "[WARN]", "critical": "[CRIT]"}
        print(f"\n{status_emoji.get(health['status'], '[?]')} System Status: {health['status'].upper()} (Score: {health['health_score']}/100)")

        if health["critical_issue"]:
            print(f"    Critical Issue: {health['critical_issue']}")

        # Summary
        print("\n--- Post Queue Summary ---")
        print(f"  Total in queue: {summary['total']}")
        print(f"  Pending:        {summary['pending']}")
        print(f"  Scheduled:      {summary['scheduled']}")
        print(f"  Posted:         {summary['posted']}")
        print(f"  Failed:         {summary['failed']} ({summary['retryable_failed']} retryable)")
        print(f"  Archived:       {summary['archived']}")
        print(f"  OVERDUE:        {summary['overdue']}")

        # Rate Limit Status
        print("\n--- Rate Limit Status ---")
        can_post = "Yes" if rate_limit["can_post"] else "No"
        print(f"  Can post now:     {can_post}")
        print(f"  Posts today:      {rate_limit['posts_today']}")
        print(f"  Remaining today:  {rate_limit['posts_remaining_today']}")

        if rate_limit["in_backoff"]:
            print(f"  IN BACKOFF:       {rate_limit['backoff_remaining']} seconds remaining")

        # Recent Errors
        errors = self.get_recent_errors(limit=5)
        if errors:
            print("\n--- Recent Errors (last 5) ---")
            for err in errors:
                print(f"  [{err['id']}] {err['error_type']}: {err['error'][:40]}...")

        # Overdue Posts
        overdue = self.get_overdue_posts()[:5]
        if overdue:
            print("\n--- Most Overdue Posts (top 5) ---")
            for post in overdue:
                print(f"  [{post['id']}] {post['hours_overdue']}h overdue: {post['text'][:30]}...")

        print("\n" + "=" * 60)

        # Recommendations
        if summary["overdue"] > 0:
            print("\nRecommendations:")
            if summary["overdue"] > 10:
                print("  - Run: python -m src.x_scheduler archive-old --hours 48")
            if summary["retryable_failed"] > 0:
                print("  - Run: python -m src.x_scheduler retry")
            print("  - Run: python -m src.x_scheduler dedupe")

        print("")


def main():
    """CLI for social media status dashboard."""
    parser = argparse.ArgumentParser(description='Social Media Status Dashboard')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                       help='Output format (default: text)')
    parser.add_argument('--errors', action='store_true',
                       help='Show detailed error list')
    parser.add_argument('--overdue', action='store_true',
                       help='Show detailed overdue list')
    parser.add_argument('--stats', action='store_true',
                       help='Show posting statistics')
    parser.add_argument('--days', type=int, default=7,
                       help='Days for statistics (default: 7)')

    args = parser.parse_args()

    dashboard = SocialMediaDashboard()

    if args.format == 'json':
        # JSON output
        output = {
            "generated_at": datetime.now().isoformat(),
            "health": dashboard.get_health_status()
        }

        if args.errors:
            output["errors"] = dashboard.get_recent_errors(limit=20)
        if args.overdue:
            output["overdue_posts"] = dashboard.get_overdue_posts()
        if args.stats:
            output["posting_stats"] = dashboard.get_posting_stats(days=args.days)

        print(json.dumps(output, indent=2))

    else:
        # Text output
        if args.errors:
            errors = dashboard.get_recent_errors(limit=20)
            print("\n=== Detailed Error List ===\n")
            for err in errors:
                print(f"Post ID: {err['id']}")
                print(f"  Status: {err['status']}")
                print(f"  Error Type: {err['error_type']}")
                print(f"  Error: {err['error']}")
                print(f"  Retry Count: {err['retry_count']}")
                print(f"  Last Retry: {err['last_retry_at'] or 'N/A'}")
                print(f"  Campaign: {err['campaign'] or 'N/A'}")
                print(f"  Text: {err['text']}")
                print()

        elif args.overdue:
            overdue = dashboard.get_overdue_posts()
            print(f"\n=== Overdue Posts ({len(overdue)} total) ===\n")
            for post in overdue:
                print(f"Post ID: {post['id']}")
                print(f"  Hours Overdue: {post['hours_overdue']}")
                print(f"  Scheduled: {post['scheduled_time']}")
                print(f"  Status: {post['status']}")
                print(f"  Retry Count: {post['retry_count']}")
                print(f"  Campaign: {post['campaign'] or 'N/A'}")
                print(f"  Text: {post['text']}")
                print()

        elif args.stats:
            stats = dashboard.get_posting_stats(days=args.days)
            print(f"\n=== Posting Statistics (last {stats['period_days']} days) ===\n")
            print(f"Total Posts Sent: {stats['posts_sent']}")
            print("\nBy Campaign:")
            for campaign, count in sorted(stats['by_campaign'].items(), key=lambda x: -x[1]):
                print(f"  {campaign}: {count}")
            print("\nBy Day:")
            for day, count in sorted(stats['by_day'].items()):
                print(f"  {day}: {count}")

        else:
            dashboard.print_dashboard()

    return 0


if __name__ == '__main__':
    exit(main())
