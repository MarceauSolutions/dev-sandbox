#!/usr/bin/env python3
"""
x_scheduler.py - Post Queue Management for X Platform

Manages a queue of scheduled posts with:
- Priority scheduling
- Optimal time slot selection
- Rate limit aware execution
- Queue persistence

Usage:
    # Add post to queue
    python -m src.x_scheduler add "Your tweet text" --priority high

    # Process queue (posts ready items)
    python -m src.x_scheduler process

    # View queue
    python -m src.x_scheduler list

    # Schedule for specific time
    python -m src.x_scheduler add "Tweet" --schedule "2026-01-20 10:00"
"""

import os
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging

from dotenv import load_dotenv
load_dotenv()

# Import local modules
from .x_api import XClient, PostResult
from .link_manager import LinkManager
from .time_context import TimeContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PostPriority(Enum):
    """Post priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class PostStatus(Enum):
    """Post status in queue."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    POSTED = "posted"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledPost:
    """A post in the queue."""
    id: str
    text: str
    priority: str = "normal"
    status: str = "pending"
    scheduled_time: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    posted_at: Optional[str] = None
    tweet_id: Optional[str] = None
    error: Optional[str] = None
    campaign: Optional[str] = None
    utm_params: Optional[Dict[str, str]] = None
    media_paths: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    business_id: Optional[str] = None
    template_type: Optional[str] = None
    generate_image: bool = False


class PostScheduler:
    """
    Manages a queue of posts with scheduling and rate limiting.
    """

    QUEUE_FILE = Path(__file__).parent.parent / "output" / "scheduled_posts.json"
    HISTORY_FILE = Path(__file__).parent.parent / "output" / "post_history.json"

    # Optimal posting times (EST) based on engagement research
    OPTIMAL_HOURS = [9, 12, 15, 18, 20]  # 9AM, 12PM, 3PM, 6PM, 8PM

    def __init__(self):
        self.client = XClient()
        self.link_manager = LinkManager()
        self.time_context = TimeContext()
        self.queue = self._load_queue()
        self.history = self._load_history()

    def _load_queue(self) -> List[ScheduledPost]:
        """Load queue from file."""
        if self.QUEUE_FILE.exists():
            try:
                with open(self.QUEUE_FILE) as f:
                    data = json.load(f)
                # Migrate old posts to add missing fields
                migrated_posts = []
                for post in data:
                    # Generate ID if missing (from business_scheduler posts)
                    if 'id' not in post:
                        import hashlib
                        # Use text + scheduled_time to generate deterministic ID
                        content = post.get('text', '') + post.get('scheduled_time', '') + str(datetime.now().timestamp())
                        post['id'] = hashlib.md5(content.encode()).hexdigest()[:12]

                    # Add default values for new fields if they don't exist (from old x_scheduler posts)
                    if 'business_id' not in post:
                        post['business_id'] = None
                    if 'template_type' not in post:
                        post['template_type'] = None
                    if 'generate_image' not in post:
                        post['generate_image'] = False

                    # Add old fields if missing (from business_scheduler posts)
                    if 'priority' not in post:
                        post['priority'] = 'normal'
                    if 'status' not in post:
                        post['status'] = 'pending'
                    if 'created_at' not in post:
                        post['created_at'] = datetime.now().isoformat()
                    if 'posted_at' not in post:
                        post['posted_at'] = None
                    if 'tweet_id' not in post:
                        post['tweet_id'] = None
                    if 'error' not in post:
                        post['error'] = None
                    if 'utm_params' not in post:
                        post['utm_params'] = None
                    if 'media_paths' not in post:
                        post['media_paths'] = []
                    if 'retry_count' not in post:
                        post['retry_count'] = 0
                    if 'max_retries' not in post:
                        post['max_retries'] = 3

                    migrated_posts.append(ScheduledPost(**post))
                return migrated_posts
            except Exception as e:
                logger.warning(f"Error loading queue: {e}")
                import traceback
                logger.warning(traceback.format_exc())
        return []

    def _save_queue(self):
        """Save queue to file."""
        self.QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.QUEUE_FILE, 'w') as f:
            json.dump([asdict(p) for p in self.queue], f, indent=2)

    def _load_history(self) -> List[Dict]:
        """Load post history."""
        if self.HISTORY_FILE.exists():
            try:
                with open(self.HISTORY_FILE) as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_history(self):
        """Save post history."""
        self.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.HISTORY_FILE, 'w') as f:
            json.dump(self.history[-1000:], f, indent=2)  # Keep last 1000

    def _generate_id(self) -> str:
        """Generate unique post ID."""
        import hashlib
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:12]

    def _get_next_optimal_time(self) -> datetime:
        """Get next optimal posting time using content strategy."""
        # Log current time context for transparency
        ctx = self.time_context.get_context_summary()
        logger.info(f"Time context: {ctx['day_of_week']} {ctx['current_time'][:19]} ({ctx['timezone']})")
        logger.info(f"Today's theme: {ctx['todays_theme'] or 'N/A'}, Weekend: {ctx['is_weekend']}")

        # Use TimeContext for strategy-aware scheduling
        next_slot, reason = self.time_context.get_next_optimal_slot()
        logger.info(f"Next optimal slot: {next_slot.strftime('%Y-%m-%d %H:%M')} - {reason}")

        # Return as naive datetime for compatibility
        return next_slot.replace(tzinfo=None)

    def add_post(
        self,
        text: str,
        priority: str = "normal",
        scheduled_time: Optional[str] = None,
        campaign: Optional[str] = None,
        utm_source: str = "x",
        utm_medium: str = "social",
        utm_campaign: Optional[str] = None,
        media_paths: Optional[List[str]] = None,
        auto_schedule: bool = True
    ) -> ScheduledPost:
        """
        Add a post to the queue.

        Args:
            text: Tweet text
            priority: low/normal/high/urgent
            scheduled_time: ISO datetime string (optional)
            campaign: Campaign name for tracking
            utm_source: UTM source parameter
            utm_medium: UTM medium parameter
            utm_campaign: UTM campaign parameter
            media_paths: List of media file paths
            auto_schedule: Auto-assign optimal time if not specified

        Returns:
            Created ScheduledPost
        """
        # Generate UTM params
        utm_params = {
            "utm_source": utm_source,
            "utm_medium": utm_medium,
            "utm_campaign": utm_campaign or campaign or "auto"
        }

        # Process text to add UTM tracking to links
        processed_text = self.link_manager.process_text(text, utm_params)

        # Validate length after UTM processing
        if len(processed_text) > 280:
            logger.warning(f"Tweet too long after UTM processing: {len(processed_text)} chars")
            # Try to shorten by removing UTM params
            processed_text = text
            if len(processed_text) > 280:
                raise ValueError(f"Tweet too long: {len(text)} chars (max 280)")

        # Determine schedule time
        if scheduled_time:
            schedule = scheduled_time
            status = PostStatus.SCHEDULED.value
        elif auto_schedule:
            schedule = self._get_next_optimal_time().isoformat()
            status = PostStatus.SCHEDULED.value
        else:
            schedule = None
            status = PostStatus.PENDING.value

        post = ScheduledPost(
            id=self._generate_id(),
            text=processed_text,
            priority=priority,
            status=status,
            scheduled_time=schedule,
            campaign=campaign,
            utm_params=utm_params,
            media_paths=media_paths or []
        )

        self.queue.append(post)
        self._save_queue()

        logger.info(f"Post added to queue: {post.id}")
        if schedule:
            logger.info(f"Scheduled for: {schedule}")

        return post

    def get_ready_posts(self) -> List[ScheduledPost]:
        """Get posts that are ready to be posted."""
        now = datetime.now()
        ready = []

        for post in self.queue:
            if post.status not in [PostStatus.PENDING.value, PostStatus.SCHEDULED.value]:
                continue

            # Check if scheduled time has passed
            if post.scheduled_time:
                scheduled = datetime.fromisoformat(post.scheduled_time)
                if scheduled <= now:
                    ready.append(post)
            elif post.status == PostStatus.PENDING.value:
                # Unscheduled pending posts are always ready
                ready.append(post)

        # Sort by priority (highest first) then scheduled time
        priority_order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
        ready.sort(key=lambda p: (
            priority_order.get(p.priority, 2),
            p.scheduled_time or "9999"
        ))

        return ready

    def process_queue(self, max_posts: int = 5, dry_run: bool = False) -> List[PostResult]:
        """
        Process the queue and post ready items.

        Args:
            max_posts: Maximum posts to process in one run
            dry_run: If True, don't actually post

        Returns:
            List of PostResults
        """
        ready = self.get_ready_posts()[:max_posts]
        results = []

        if not ready:
            logger.info("No posts ready to process")
            return results

        logger.info(f"Processing {len(ready)} posts from queue")

        for post in ready:
            # Check rate limit
            can_post, reason = self.client.rate_limiter.can_post()
            if not can_post:
                logger.warning(f"Rate limited: {reason}")
                break

            if dry_run:
                logger.info(f"[DRY RUN] Would post: {post.text[:50]}...")
                results.append(PostResult(success=True, text=post.text))
                continue

            # Upload media if any
            media_ids = []
            for media_path in post.media_paths:
                if os.path.exists(media_path):
                    media_id = self.client.upload_media(media_path)
                    if media_id:
                        media_ids.append(media_id)

            # Post the tweet
            result = self.client.post_tweet(
                text=post.text,
                media_ids=media_ids if media_ids else None
            )

            # Update post status
            if result.success:
                post.status = PostStatus.POSTED.value
                post.posted_at = datetime.now().isoformat()
                post.tweet_id = result.tweet_id

                # Add to history
                self.history.append({
                    "post_id": post.id,
                    "tweet_id": result.tweet_id,
                    "text": post.text,
                    "campaign": post.campaign,
                    "utm_params": post.utm_params,
                    "posted_at": post.posted_at
                })
            else:
                post.retry_count += 1
                if post.retry_count >= post.max_retries:
                    post.status = PostStatus.FAILED.value
                post.error = result.error

            results.append(result)

        # Save updates
        self._save_queue()
        self._save_history()

        return results

    def cancel_post(self, post_id: str) -> bool:
        """Cancel a scheduled post."""
        for post in self.queue:
            if post.id == post_id:
                if post.status in [PostStatus.PENDING.value, PostStatus.SCHEDULED.value]:
                    post.status = PostStatus.CANCELLED.value
                    self._save_queue()
                    logger.info(f"Post {post_id} cancelled")
                    return True
                else:
                    logger.warning(f"Cannot cancel post with status: {post.status}")
                    return False
        logger.warning(f"Post {post_id} not found")
        return False

    def reschedule_post(self, post_id: str, new_time: str) -> bool:
        """Reschedule a post."""
        for post in self.queue:
            if post.id == post_id:
                if post.status in [PostStatus.PENDING.value, PostStatus.SCHEDULED.value]:
                    post.scheduled_time = new_time
                    post.status = PostStatus.SCHEDULED.value
                    self._save_queue()
                    logger.info(f"Post {post_id} rescheduled to {new_time}")
                    return True
        return False

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        stats = {
            "total": len(self.queue),
            "by_status": {},
            "by_priority": {},
            "by_campaign": {},
            "next_scheduled": None
        }

        for post in self.queue:
            # Count by status
            stats["by_status"][post.status] = stats["by_status"].get(post.status, 0) + 1

            # Count by priority
            stats["by_priority"][post.priority] = stats["by_priority"].get(post.priority, 0) + 1

            # Count by campaign
            if post.campaign:
                stats["by_campaign"][post.campaign] = stats["by_campaign"].get(post.campaign, 0) + 1

            # Find next scheduled
            if post.status == PostStatus.SCHEDULED.value and post.scheduled_time:
                if not stats["next_scheduled"] or post.scheduled_time < stats["next_scheduled"]:
                    stats["next_scheduled"] = post.scheduled_time

        return stats

    def list_queue(self, status: Optional[str] = None) -> List[Dict]:
        """List posts in queue with optional status filter."""
        posts = []
        for post in self.queue:
            if status and post.status != status:
                continue

            # Add day of week for scheduled posts
            day_of_week = None
            if post.scheduled_time:
                try:
                    scheduled_dt = datetime.fromisoformat(post.scheduled_time)
                    day_of_week = scheduled_dt.strftime("%A")
                except ValueError:
                    pass

            posts.append({
                "id": post.id,
                "text": post.text[:50] + "..." if len(post.text) > 50 else post.text,
                "priority": post.priority,
                "status": post.status,
                "scheduled": post.scheduled_time,
                "day_of_week": day_of_week,
                "campaign": post.campaign
            })
        return posts

    def get_time_context(self) -> Dict:
        """Get current time context for scheduling decisions."""
        return self.time_context.get_context_summary()

    def clear_completed(self) -> int:
        """Remove completed/cancelled posts from queue."""
        original_count = len(self.queue)
        self.queue = [
            p for p in self.queue
            if p.status not in [PostStatus.POSTED.value, PostStatus.CANCELLED.value]
        ]
        removed = original_count - len(self.queue)
        self._save_queue()
        return removed


def main():
    """CLI for post scheduler."""
    parser = argparse.ArgumentParser(description='X Post Scheduler')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add post to queue')
    add_parser.add_argument('text', help='Tweet text')
    add_parser.add_argument('--priority', choices=['low', 'normal', 'high', 'urgent'], default='normal')
    add_parser.add_argument('--schedule', help='Schedule time (ISO format)')
    add_parser.add_argument('--campaign', help='Campaign name')
    add_parser.add_argument('--no-auto-schedule', action='store_true', help='Do not auto-schedule')

    # Process command
    process_parser = subparsers.add_parser('process', help='Process queue')
    process_parser.add_argument('--max', type=int, default=5, help='Max posts to process')
    process_parser.add_argument('--dry-run', action='store_true', help='Preview without posting')

    # List command
    list_parser = subparsers.add_parser('list', help='List queue')
    list_parser.add_argument('--status', choices=['pending', 'scheduled', 'posted', 'failed', 'cancelled'])

    # Stats command
    subparsers.add_parser('stats', help='Show queue statistics')

    # Context command - show current time context
    subparsers.add_parser('context', help='Show current time context for scheduling')

    # Cancel command
    cancel_parser = subparsers.add_parser('cancel', help='Cancel a post')
    cancel_parser.add_argument('post_id', help='Post ID to cancel')

    # Clear command
    subparsers.add_parser('clear', help='Clear completed/cancelled posts')

    args = parser.parse_args()

    scheduler = PostScheduler()

    if args.command == 'add':
        try:
            post = scheduler.add_post(
                text=args.text,
                priority=args.priority,
                scheduled_time=args.schedule,
                campaign=args.campaign,
                auto_schedule=not args.no_auto_schedule
            )
            print(f"\nPost added to queue:")
            print(f"  ID: {post.id}")
            print(f"  Status: {post.status}")
            print(f"  Priority: {post.priority}")
            if post.scheduled_time:
                print(f"  Scheduled: {post.scheduled_time}")
        except ValueError as e:
            print(f"Error: {e}")
            return 1

    elif args.command == 'process':
        results = scheduler.process_queue(max_posts=args.max, dry_run=args.dry_run)
        print(f"\nProcessed {len(results)} posts:")
        for r in results:
            status = "OK" if r.success else f"FAIL: {r.error}"
            print(f"  - {status}")

    elif args.command == 'list':
        # Show time context first
        ctx = scheduler.get_time_context()
        print(f"\n[Now: {ctx['day_of_week']} {ctx['current_time'][:16]}]")

        posts = scheduler.list_queue(status=args.status)
        if not posts:
            print("\nQueue is empty")
        else:
            print(f"\nQueue ({len(posts)} posts):")
            for p in posts:
                print(f"  [{p['id']}] {p['status']} | {p['priority']} | {p['text']}")
                if p['scheduled']:
                    day = p.get('day_of_week', '')
                    print(f"           Scheduled: {day} {p['scheduled']}")

    elif args.command == 'stats':
        stats = scheduler.get_queue_stats()
        print("\nQueue Statistics:")
        print(f"  Total posts: {stats['total']}")
        print(f"\n  By Status:")
        for status, count in stats['by_status'].items():
            print(f"    {status}: {count}")
        print(f"\n  By Priority:")
        for priority, count in stats['by_priority'].items():
            print(f"    {priority}: {count}")
        if stats['by_campaign']:
            print(f"\n  By Campaign:")
            for campaign, count in stats['by_campaign'].items():
                print(f"    {campaign}: {count}")
        if stats['next_scheduled']:
            print(f"\n  Next scheduled: {stats['next_scheduled']}")

    elif args.command == 'context':
        ctx = scheduler.get_time_context()
        print("\n" + "=" * 60)
        print("CURRENT TIME CONTEXT")
        print("=" * 60)
        print(f"  Time:      {ctx['current_time'][:19]}")
        print(f"  Day:       {ctx['day_of_week']}")
        print(f"  Weekend:   {'Yes' if ctx['is_weekend'] else 'No'}")
        print(f"  Timezone:  {ctx['timezone']}")
        print(f"  Theme:     {ctx['todays_theme'] or 'None'}")
        print(f"  Hashtags:  {', '.join(ctx['todays_hashtags']) if ctx['todays_hashtags'] else 'None'}")
        print(f"  Optimal:   {', '.join(ctx['optimal_posting_hours'])}")
        print("=" * 60)

    elif args.command == 'cancel':
        if scheduler.cancel_post(args.post_id):
            print(f"Post {args.post_id} cancelled")
        else:
            print(f"Could not cancel post {args.post_id}")
            return 1

    elif args.command == 'clear':
        removed = scheduler.clear_completed()
        print(f"Cleared {removed} completed/cancelled posts")

    else:
        parser.print_help()

    return 0


if __name__ == '__main__':
    exit(main())
