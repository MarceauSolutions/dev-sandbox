#!/usr/bin/env python3
"""
business_scheduler.py - Multi-Business Automated Posting Scheduler

Manages automated posting schedules for multiple businesses.
Generates content, schedules posts, and processes the queue.

Usage:
    # Generate and schedule a week of content for all businesses
    python -m src.business_scheduler schedule-week

    # Generate and schedule content for one business
    python -m src.business_scheduler schedule-week --business squarefoot-shipping

    # Process the posting queue (run via cron or manually)
    python -m src.business_scheduler process

    # View scheduled posts
    python -m src.business_scheduler view-queue

    # Clear the queue
    python -m src.business_scheduler clear-queue --business squarefoot-shipping

    # Run daily automation (generates + schedules + processes)
    python -m src.business_scheduler daily-run
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict

from .business_content_generator import BusinessContentGenerator, GeneratedPost
from .x_scheduler import PostScheduler, ScheduledPost, PostPriority, PostStatus

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "businesses.json"
SCHEDULE_PATH = PROJECT_ROOT / "output" / "business_schedule.json"


@dataclass
class BusinessScheduleConfig:
    """Configuration for a business's posting schedule."""
    business_id: str
    posts_per_day: int = 2
    optimal_times: List[str] = None  # ["09:00", "15:00"]
    active_days: List[str] = None  # ["monday", "tuesday", ...]
    campaign: str = "general-awareness"

    def __post_init__(self):
        if self.optimal_times is None:
            self.optimal_times = ["09:00", "15:00"]
        if self.active_days is None:
            self.active_days = ["monday", "tuesday", "wednesday", "thursday", "friday"]


class BusinessPostingScheduler:
    """
    Manages automated posting for multiple businesses.
    """

    def __init__(self):
        self.generator = BusinessContentGenerator()
        self.post_scheduler = PostScheduler()
        self.config = self._load_config()
        self.schedule_data = self._load_schedule()

    def _generate_post_image(self, post: GeneratedPost) -> Optional[str]:
        """
        Generate Grok image for a post using its image_prompt.

        Args:
            post: GeneratedPost with image_prompt set

        Returns:
            Path to generated image file, or None if generation failed
        """
        if not post.image_prompt:
            return None

        try:
            # Import Grok generator from shared utilities
            import sys
            sys.path.insert(0, str(PROJECT_ROOT.parent / "execution"))
            from grok_image_gen import GrokImageGenerator

            grok = GrokImageGenerator()

            # Create output directory
            output_dir = PROJECT_ROOT / "output" / "images"
            output_dir.mkdir(parents=True, exist_ok=True)

            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_filename = f"{post.business_id}_{timestamp}.png"
            image_path = output_dir / image_filename

            # Generate image using post's image_prompt
            results = grok.generate_image(
                prompt=post.image_prompt,
                count=1,
                output_path=str(image_path)
            )

            if results and len(results) > 0:
                return str(results[0])
            else:
                return None

        except Exception as e:
            # Don't crash if image generation fails - just log and continue
            print(f"Warning: Grok image generation failed for {post.business_id}: {e}")
            return None

    def _load_config(self) -> Dict:
        """Load business configuration."""
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                return json.load(f)
        return {}

    def _load_schedule(self) -> Dict:
        """Load existing schedule data."""
        if SCHEDULE_PATH.exists():
            with open(SCHEDULE_PATH) as f:
                return json.load(f)
        return {"scheduled_posts": [], "last_run": None}

    def _save_schedule(self):
        """Save schedule data."""
        SCHEDULE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(SCHEDULE_PATH, 'w') as f:
            json.dump(self.schedule_data, f, indent=2, default=str)

    def get_schedule_config(self, business_id: str) -> BusinessScheduleConfig:
        """Get schedule configuration for a business."""
        # Check if business has custom posting schedule
        businesses = self.config.get("businesses", {})
        biz_config = businesses.get(business_id, {})
        biz_schedule = biz_config.get("posting_schedule", {})

        # Fall back to global config if business doesn't have custom schedule
        posting_config = self.config.get("posting_config", {})

        posts_per_day = biz_schedule.get("posts_per_day") or posting_config.get("posts_per_business_per_day", 2)

        # Convert optimal_times (hours) to time strings if needed
        optimal_times = biz_schedule.get("optimal_times")
        if optimal_times and isinstance(optimal_times[0], int):
            # Convert hours [6, 9, 12] to time strings ["06:00", "09:00", "12:00"]
            optimal_times = [f"{h:02d}:00" for h in optimal_times]
        elif not optimal_times:
            optimal_times = posting_config.get("optimal_times_est", ["09:00", "15:00"])

        return BusinessScheduleConfig(
            business_id=business_id,
            posts_per_day=posts_per_day,
            optimal_times=optimal_times,
        )

    def schedule_day(
        self,
        business_id: str,
        date: datetime,
        campaign: str = "general-awareness"
    ) -> List[GeneratedPost]:
        """
        Schedule posts for a specific business on a specific day.

        Args:
            business_id: The business to schedule for
            date: The date to schedule posts
            campaign: Campaign to use

        Returns:
            List of generated and scheduled posts
        """
        config = self.get_schedule_config(business_id)

        # Get business-specific image generation percentage
        businesses = self.config.get("businesses", {})
        biz_config = businesses.get(business_id, {})
        biz_schedule = biz_config.get("posting_schedule", {})
        image_percentage = biz_schedule.get("image_generation_percentage", 0)

        # Generate posts for the day with image generation
        scheduled_posts = []
        templates = list(self.generator.content.get(business_id, {}).get("post_templates", {}).keys())

        for i in range(config.posts_per_day):
            # Rotate through templates
            template = templates[i % len(templates)] if templates else None

            # Determine if this post gets an image (based on percentage)
            generate_image = (i % (100 // max(image_percentage, 1))) < (image_percentage / (100 // max(image_percentage, 1))) if image_percentage > 0 else False

            # For 50%, this simplifies to: every other post (i % 2 == 0)
            if image_percentage == 50:
                generate_image = (i % 2 == 0)

            # Generate post
            post = self.generator.generate_post(
                business_id,
                template_type=template,
                campaign=campaign,
                generate_image=generate_image
            )

            # Generate Grok image if post has image_prompt
            if post.image_prompt:
                image_path = self._generate_post_image(post)
                if image_path:
                    post.media_paths = [image_path]

            # Schedule at optimal time
            if i < len(config.optimal_times):
                time_str = config.optimal_times[i]
                hour, minute = map(int, time_str.split(":"))
                scheduled_time = date.replace(hour=hour, minute=minute, second=0, microsecond=0)

                post.scheduled_for = scheduled_time.isoformat()

                # Add to x_scheduler queue (with media if available)
                self.post_scheduler.add_post(
                    text=post.content,
                    priority="normal",
                    campaign=f"{business_id}-{campaign}",
                    scheduled_time=scheduled_time.strftime("%Y-%m-%d %H:%M"),
                    media_paths=post.media_paths
                )

                scheduled_posts.append(post)

                # Track in our schedule
                self.schedule_data["scheduled_posts"].append({
                    "business_id": business_id,
                    "content": post.content[:100] + "...",
                    "scheduled_for": post.scheduled_for,
                    "campaign": campaign,
                    "status": "scheduled"
                })

        self._save_schedule()
        return scheduled_posts

    def schedule_week(
        self,
        business_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        campaign: str = "general-awareness"
    ) -> Dict[str, List[GeneratedPost]]:
        """
        Schedule a week of posts for one or all businesses.

        Args:
            business_id: Specific business or None for all
            start_date: Start date (defaults to tomorrow)
            campaign: Campaign to use

        Returns:
            Dict mapping business_id to list of scheduled posts
        """
        if start_date is None:
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            start_date += timedelta(days=1)  # Start tomorrow

        businesses = [business_id] if business_id else list(self.config.get("businesses", {}).keys())
        all_scheduled = {}

        for bid in businesses:
            all_scheduled[bid] = []
            config = self.get_schedule_config(bid)

            for day_offset in range(7):
                date = start_date + timedelta(days=day_offset)
                day_name = date.strftime("%A").lower()

                # Skip inactive days
                if day_name not in config.active_days:
                    continue

                # Schedule posts for this day
                posts = self.schedule_day(bid, date, campaign)
                all_scheduled[bid].extend(posts)

        return all_scheduled

    def view_queue(self, business_id: Optional[str] = None) -> List[Dict]:
        """View scheduled posts, optionally filtered by business."""
        posts = self.schedule_data.get("scheduled_posts", [])
        if business_id:
            posts = [p for p in posts if p.get("business_id") == business_id]
        return posts

    def clear_queue(self, business_id: Optional[str] = None):
        """Clear scheduled posts, optionally for a specific business."""
        if business_id:
            self.schedule_data["scheduled_posts"] = [
                p for p in self.schedule_data.get("scheduled_posts", [])
                if p.get("business_id") != business_id
            ]
        else:
            self.schedule_data["scheduled_posts"] = []
        self._save_schedule()

    def process_queue(self, max_posts: int = 10) -> int:
        """
        Process the posting queue - post any scheduled posts that are due.

        Args:
            max_posts: Maximum posts to process in one run

        Returns:
            Number of posts processed
        """
        return self.post_scheduler.process_queue(max_posts=max_posts)

    def daily_run(self, days_ahead: int = 3):
        """
        Daily automation run:
        1. Generate content for upcoming days
        2. Schedule posts
        3. Process any due posts

        Args:
            days_ahead: How many days ahead to schedule
        """
        print(f"\n{'='*50}")
        print(f"Daily Automation Run - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*50}\n")

        # 1. Schedule posts for upcoming days (if not already scheduled)
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        for day_offset in range(days_ahead):
            date = start_date + timedelta(days=day_offset)
            date_str = date.strftime("%Y-%m-%d")

            # Check if already scheduled for this date
            existing = [
                p for p in self.schedule_data.get("scheduled_posts", [])
                if p.get("scheduled_for", "").startswith(date_str)
            ]

            if not existing:
                print(f"Scheduling posts for {date_str}...")
                for business_id in self.config.get("businesses", {}).keys():
                    posts = self.schedule_day(business_id, date)
                    print(f"  {business_id}: {len(posts)} posts scheduled")
            else:
                print(f"Already have {len(existing)} posts scheduled for {date_str}")

        # 2. Process any due posts
        print(f"\nProcessing posting queue...")
        posted = self.process_queue(max_posts=10)
        print(f"Posted {posted} posts")

        # 3. Update last run time
        self.schedule_data["last_run"] = datetime.now().isoformat()
        self._save_schedule()

        print(f"\nDaily run complete!")
        return posted

    def get_status(self) -> Dict:
        """Get overall scheduling status."""
        posts = self.schedule_data.get("scheduled_posts", [])
        by_business = {}
        for p in posts:
            bid = p.get("business_id", "unknown")
            if bid not in by_business:
                by_business[bid] = {"scheduled": 0, "posted": 0}
            if p.get("status") == "posted":
                by_business[bid]["posted"] += 1
            else:
                by_business[bid]["scheduled"] += 1

        return {
            "total_scheduled": len([p for p in posts if p.get("status") != "posted"]),
            "total_posted": len([p for p in posts if p.get("status") == "posted"]),
            "by_business": by_business,
            "last_run": self.schedule_data.get("last_run")
        }


def main():
    parser = argparse.ArgumentParser(description="Multi-Business Posting Scheduler")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # schedule-week command
    week_parser = subparsers.add_parser("schedule-week", help="Schedule a week of posts")
    week_parser.add_argument("--business", "-b", help="Business ID (or all)")
    week_parser.add_argument("--campaign", default="general-awareness", help="Campaign")

    # schedule-day command
    day_parser = subparsers.add_parser("schedule-day", help="Schedule posts for today")
    day_parser.add_argument("--business", "-b", help="Business ID (or all)")
    day_parser.add_argument("--campaign", default="general-awareness", help="Campaign")

    # process command
    process_parser = subparsers.add_parser("process", help="Process posting queue")
    process_parser.add_argument("--max", type=int, default=10, help="Max posts to process")

    # view-queue command
    view_parser = subparsers.add_parser("view-queue", help="View scheduled posts")
    view_parser.add_argument("--business", "-b", help="Filter by business")

    # clear-queue command
    clear_parser = subparsers.add_parser("clear-queue", help="Clear scheduled posts")
    clear_parser.add_argument("--business", "-b", help="Clear only this business")

    # daily-run command
    daily_parser = subparsers.add_parser("daily-run", help="Run daily automation")
    daily_parser.add_argument("--days", type=int, default=3, help="Days ahead to schedule")

    # status command
    status_parser = subparsers.add_parser("status", help="View scheduling status")

    args = parser.parse_args()
    scheduler = BusinessPostingScheduler()

    if args.command == "schedule-week":
        print(f"\nScheduling week of posts...")
        all_posts = scheduler.schedule_week(args.business, campaign=args.campaign)
        for bid, posts in all_posts.items():
            print(f"\n{bid}: {len(posts)} posts scheduled")
            for post in posts[:3]:  # Show first 3
                print(f"  - {post.scheduled_for}: {post.content[:50]}...")

    elif args.command == "schedule-day":
        today = datetime.now()
        businesses = [args.business] if args.business else list(scheduler.config.get("businesses", {}).keys())
        for bid in businesses:
            posts = scheduler.schedule_day(bid, today, args.campaign)
            print(f"\n{bid}: {len(posts)} posts scheduled for today")
            for post in posts:
                print(f"  - {post.scheduled_for}: {post.content[:50]}...")

    elif args.command == "process":
        print("Processing posting queue...")
        count = scheduler.process_queue(max_posts=args.max)
        print(f"Processed {count} posts")

    elif args.command == "view-queue":
        posts = scheduler.view_queue(args.business)
        print(f"\nScheduled Posts ({len(posts)} total):")
        print("-" * 60)
        for post in posts[:20]:  # Show first 20
            print(f"  [{post.get('business_id')}] {post.get('scheduled_for')}")
            print(f"    {post.get('content', '')[:60]}...")
            print()

    elif args.command == "clear-queue":
        scheduler.clear_queue(args.business)
        target = args.business or "all businesses"
        print(f"Cleared queue for {target}")

    elif args.command == "daily-run":
        scheduler.daily_run(days_ahead=args.days)

    elif args.command == "status":
        status = scheduler.get_status()
        print("\nScheduling Status:")
        print("-" * 40)
        print(f"Total Scheduled: {status['total_scheduled']}")
        print(f"Total Posted: {status['total_posted']}")
        print(f"Last Run: {status['last_run']}")
        print("\nBy Business:")
        for bid, counts in status.get("by_business", {}).items():
            print(f"  {bid}: {counts['scheduled']} scheduled, {counts['posted']} posted")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
