#!/usr/bin/env python3
"""
content_generator.py - AI-Powered Content Generator for X

Generates engaging social media posts using Fitness Influencer tools.
Integrates with x_scheduler for automated posting.

Usage:
    # Generate single post
    python -m src.content_generator single --type workout_tip --campaign fitness-launch

    # Generate batch of posts
    python -m src.content_generator batch --count 5 --campaign fitness-launch

    # Generate week of content
    python -m src.content_generator weekly --posts-per-day 3 --campaign fitness-launch
"""

import sys
import json
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "fitness-influencer" / "src"))

from .x_scheduler import PostScheduler


class FitnessContentGenerator:
    """
    Generates fitness-focused content for X using Fitness Influencer tools.
    """

    TEMPLATES_PATH = Path(__file__).parent.parent / "templates" / "post_templates.json"
    AI_PROMPTS_PATH = Path(__file__).parent.parent / "templates" / "ai_prompts.json"

    # Content types that can be generated
    CONTENT_TYPES = {
        "workout_tip": {
            "description": "Quick workout tip or form advice",
            "template": "pain_point",
            "tool": "generate_workout_plan",
            "hashtags": ["FitnessCoach", "WorkoutTips"]
        },
        "video_teaser": {
            "description": "Teaser for upcoming video content",
            "template": "question_hook",
            "tool": "generate_video_blueprint",
            "hashtags": ["FitnessVideo", "ContentCreator"]
        },
        "transformation": {
            "description": "Transformation story or results showcase",
            "template": "before_after",
            "tool": None,
            "hashtags": ["Transformation", "FitnessResults"]
        },
        "stat_insight": {
            "description": "Industry statistic or data-driven insight",
            "template": "stat_driven",
            "tool": None,
            "hashtags": ["FitnessFacts", "HealthData"]
        },
        "value_tips": {
            "description": "List of actionable tips",
            "template": "value_list",
            "tool": "generate_workout_plan",
            "hashtags": ["FitnessTips", "WorkoutAdvice"]
        },
        "motivation": {
            "description": "Motivational content",
            "template": "question_hook",
            "tool": None,
            "hashtags": ["Motivation", "FitnessMotivation"]
        }
    }

    # Pre-written content snippets for generation
    CONTENT_BANK = {
        "pain_points": [
            "Struggling to build muscle",
            "Can't stick to your workout routine",
            "Not seeing results from your training",
            "Feeling lost in the gym",
            "Hitting a plateau in your fitness journey",
            "Don't have time for long workouts",
            "Confused about what exercises to do",
            "Motivation running low"
        ],
        "solutions": [
            "A structured workout plan changes everything",
            "The right program makes all the difference",
            "Strategic training beats random workouts",
            "Consistency with a plan beats intensity without one",
            "Smart programming gets results faster"
        ],
        "benefits": [
            "build muscle efficiently",
            "finally see the results you deserve",
            "train smarter, not harder",
            "transform your physique",
            "break through plateaus",
            "maximize every workout"
        ],
        "stats": [
            "80% of gym-goers quit within 5 months",
            "Only 23% of people meet fitness guidelines",
            "Structured plans increase success rates by 70%",
            "Consistency beats intensity 95% of the time",
            "Proper form reduces injury risk by 50%"
        ],
        "tips": [
            "Focus on compound movements first",
            "Progressive overload is key to muscle growth",
            "Rest days are when muscles actually grow",
            "Track your workouts to measure progress",
            "Form always comes before weight",
            "Warm up properly - 5-10 minutes minimum",
            "Sleep 7-9 hours for optimal recovery",
            "Protein within 2 hours post-workout",
            "Hydration affects performance by 20%",
            "Mind-muscle connection matters"
        ],
        "questions": [
            "What if you could build muscle faster",
            "What if you could train smarter, not harder",
            "What if you had a coach in your pocket",
            "What if you never missed a workout again",
            "What if your workouts were planned for you"
        ]
    }

    def __init__(self):
        self.templates = self._load_templates()
        self.scheduler = PostScheduler()

    def _load_templates(self) -> Dict:
        """Load post templates from JSON."""
        if self.TEMPLATES_PATH.exists():
            with open(self.TEMPLATES_PATH) as f:
                return json.load(f)
        return {"templates": {}, "campaigns": {}, "hashtag_sets": {}}

    def _get_campaign_link(self, campaign: str) -> str:
        """Get the landing page link for a campaign."""
        campaigns = self.templates.get("campaigns", {})
        if campaign in campaigns:
            return campaigns[campaign].get("landing_page", "https://marceausolutions.com/fitness")
        return "https://marceausolutions.com/fitness"

    def _get_campaign_hashtags(self, campaign: str) -> List[str]:
        """Get hashtags for a campaign."""
        campaigns = self.templates.get("campaigns", {})
        if campaign in campaigns:
            return campaigns[campaign].get("hashtags", ["FitnessCoach", "FitnessBusiness"])
        return ["FitnessCoach", "FitnessBusiness"]

    def _format_hashtags(self, hashtags: List[str], max_count: int = 2) -> str:
        """Format hashtags for post."""
        selected = hashtags[:max_count]
        return " ".join(f"#{tag}" for tag in selected)

    def generate_workout_tip_post(self, campaign: str = "fitness-launch") -> str:
        """Generate a workout tip post."""
        pain_point = random.choice(self.CONTENT_BANK["pain_points"])
        solution = random.choice(self.CONTENT_BANK["solutions"])
        tip = random.choice(self.CONTENT_BANK["tips"])
        link = self._get_campaign_link(campaign)
        hashtags = self._format_hashtags(self._get_campaign_hashtags(campaign))

        templates = [
            f"{pain_point}?\n\nPro tip: {tip}\n\n{link}\n\n{hashtags}",
            f"💪 Quick tip: {tip}\n\n{solution}.\n\n{link}\n\n{hashtags}",
            f"Fitness coaches know: {tip}\n\nStop guessing, start growing.\n\n{link}\n\n{hashtags}",
        ]

        post = random.choice(templates)
        return self._ensure_length(post)

    def generate_video_teaser_post(self, campaign: str = "fitness-launch") -> str:
        """Generate a video teaser post."""
        question = random.choice(self.CONTENT_BANK["questions"])
        benefit = random.choice(self.CONTENT_BANK["benefits"])
        link = self._get_campaign_link(campaign)
        hashtags = self._format_hashtags(self._get_campaign_hashtags(campaign))

        templates = [
            f"{question}?\n\nNew content dropping soon that'll help you {benefit}.\n\n{link}\n\n{hashtags}",
            f"🎬 Coming soon: Your guide to {benefit}\n\nStay tuned.\n\n{link}\n\n{hashtags}",
        ]

        post = random.choice(templates)
        return self._ensure_length(post)

    def generate_stat_driven_post(self, campaign: str = "fitness-launch") -> str:
        """Generate a statistic-driven post."""
        stat = random.choice(self.CONTENT_BANK["stats"])
        solution = random.choice(self.CONTENT_BANK["solutions"])
        link = self._get_campaign_link(campaign)
        hashtags = self._format_hashtags(self._get_campaign_hashtags(campaign))

        post = f"📊 {stat}.\n\n{solution}.\n\n{link}\n\n{hashtags}"
        return self._ensure_length(post)

    def generate_value_list_post(self, campaign: str = "fitness-launch") -> str:
        """Generate a value-first list post."""
        tips = random.sample(self.CONTENT_BANK["tips"], 3)
        link = self._get_campaign_link(campaign)
        hashtags = self._format_hashtags(self._get_campaign_hashtags(campaign))

        post = f"3 things that'll transform your training:\n\n1. {tips[0]}\n2. {tips[1]}\n3. {tips[2]}\n\nWant more? {link}\n\n{hashtags}"
        return self._ensure_length(post)

    def generate_motivation_post(self, campaign: str = "fitness-launch") -> str:
        """Generate a motivational post."""
        question = random.choice(self.CONTENT_BANK["questions"])
        benefit = random.choice(self.CONTENT_BANK["benefits"])
        link = self._get_campaign_link(campaign)
        hashtags = self._format_hashtags(self._get_campaign_hashtags(campaign))

        post = f"{question}?\n\nIt's possible. Time to {benefit}.\n\n{link}\n\n{hashtags}"
        return self._ensure_length(post)

    def generate_transformation_post(self, campaign: str = "fitness-launch") -> str:
        """Generate a before/after transformation post."""
        pain = random.choice(self.CONTENT_BANK["pain_points"])
        benefit = random.choice(self.CONTENT_BANK["benefits"])
        link = self._get_campaign_link(campaign)
        hashtags = self._format_hashtags(self._get_campaign_hashtags(campaign))

        post = f"Before: {pain}\n\nAfter: Learning to {benefit}\n\nThe difference? A proper plan.\n\n{link}\n\n{hashtags}"
        return self._ensure_length(post)

    def _ensure_length(self, post: str, max_length: int = 280) -> str:
        """Ensure post is within character limit."""
        if len(post) <= max_length:
            return post

        # Truncate while keeping link and hashtags
        lines = post.split("\n")

        # Find link and hashtag lines
        link_line = None
        hashtag_line = None
        content_lines = []

        for line in lines:
            if line.startswith("http"):
                link_line = line
            elif line.startswith("#"):
                hashtag_line = line
            else:
                content_lines.append(line)

        # Rebuild with truncation
        content = "\n".join(content_lines)
        suffix_len = len(link_line or "") + len(hashtag_line or "") + 4  # newlines
        max_content = max_length - suffix_len - 3  # "..."

        if len(content) > max_content:
            content = content[:max_content] + "..."

        parts = [content]
        if link_line:
            parts.append(link_line)
        if hashtag_line:
            parts.append(hashtag_line)

        return "\n\n".join(parts)

    def generate_single(
        self,
        content_type: str = "workout_tip",
        campaign: str = "fitness-launch"
    ) -> str:
        """
        Generate a single post of specified type.

        Args:
            content_type: Type of content (workout_tip, video_teaser, etc.)
            campaign: Campaign name for links and hashtags

        Returns:
            Generated post text
        """
        generators = {
            "workout_tip": self.generate_workout_tip_post,
            "video_teaser": self.generate_video_teaser_post,
            "stat_insight": self.generate_stat_driven_post,
            "value_tips": self.generate_value_list_post,
            "motivation": self.generate_motivation_post,
            "transformation": self.generate_transformation_post,
        }

        generator = generators.get(content_type, self.generate_workout_tip_post)
        return generator(campaign)

    def generate_batch(
        self,
        count: int = 5,
        campaign: str = "fitness-launch",
        content_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple posts with variety.

        Args:
            count: Number of posts to generate
            campaign: Campaign name
            content_types: List of content types to use (defaults to all)

        Returns:
            List of generated posts with metadata
        """
        if content_types is None:
            content_types = list(self.CONTENT_TYPES.keys())

        posts = []
        for i in range(count):
            content_type = content_types[i % len(content_types)]
            post_text = self.generate_single(content_type, campaign)

            posts.append({
                "text": post_text,
                "content_type": content_type,
                "campaign": campaign,
                "character_count": len(post_text),
                "generated_at": datetime.now().isoformat()
            })

        return posts

    def generate_and_schedule(
        self,
        count: int = 5,
        campaign: str = "fitness-launch",
        content_types: Optional[List[str]] = None,
        priority: str = "normal"
    ) -> List[Dict[str, Any]]:
        """
        Generate posts and add them to the scheduler queue.

        Args:
            count: Number of posts to generate
            campaign: Campaign name
            content_types: List of content types
            priority: Post priority (urgent, high, normal, low)

        Returns:
            List of scheduled posts with IDs
        """
        posts = self.generate_batch(count, campaign, content_types)

        # Normalize priority to string (scheduler expects string, not enum)
        post_priority = priority.lower() if priority else "normal"

        scheduled = []
        for post in posts:
            scheduled_post = self.scheduler.add_post(
                text=post["text"],
                campaign=campaign,
                priority=post_priority
            )
            scheduled.append({
                **post,
                "post_id": scheduled_post.id,
                "scheduled_time": scheduled_post.scheduled_time,
                "status": scheduled_post.status
            })

        return scheduled

    def generate_weekly(
        self,
        posts_per_day: int = 3,
        campaign: str = "fitness-launch",
        start_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate a week of varied content.

        Args:
            posts_per_day: Number of posts per day
            campaign: Campaign name
            start_date: Start date (defaults to tomorrow)

        Returns:
            List of posts organized by day
        """
        if start_date is None:
            start_date = datetime.now() + timedelta(days=1)

        # Content distribution by day
        day_themes = {
            0: ["motivation", "workout_tip"],  # Monday
            1: ["value_tips", "video_teaser"],  # Tuesday
            2: ["stat_insight", "transformation"],  # Wednesday
            3: ["workout_tip", "motivation"],  # Thursday
            4: ["transformation", "value_tips"],  # Friday
            5: ["stat_insight"],  # Saturday
            6: ["motivation"],  # Sunday (rest day - fewer posts)
        }

        weekly_posts = []

        for day_offset in range(7):
            current_date = start_date + timedelta(days=day_offset)
            day_of_week = current_date.weekday()
            themes = day_themes.get(day_of_week, ["workout_tip"])

            # Adjust posts for weekend
            day_posts = posts_per_day if day_of_week < 5 else max(1, posts_per_day - 2)

            for i in range(day_posts):
                content_type = themes[i % len(themes)]
                post_text = self.generate_single(content_type, campaign)

                weekly_posts.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "day_of_week": current_date.strftime("%A"),
                    "post_number": i + 1,
                    "content_type": content_type,
                    "text": post_text,
                    "campaign": campaign,
                    "character_count": len(post_text)
                })

        return weekly_posts


def main():
    """CLI for content generator."""
    import argparse

    parser = argparse.ArgumentParser(description='AI-Powered Content Generator for X')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Single post command
    single_parser = subparsers.add_parser('single', help='Generate single post')
    single_parser.add_argument('--type', default='workout_tip',
                              choices=list(FitnessContentGenerator.CONTENT_TYPES.keys()),
                              help='Content type')
    single_parser.add_argument('--campaign', default='fitness-launch', help='Campaign name')

    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Generate batch of posts')
    batch_parser.add_argument('--count', type=int, default=5, help='Number of posts')
    batch_parser.add_argument('--campaign', default='fitness-launch', help='Campaign name')
    batch_parser.add_argument('--types', nargs='+', help='Content types to use')
    batch_parser.add_argument('--schedule', action='store_true', help='Add to scheduler queue')
    batch_parser.add_argument('--priority', default='normal', help='Post priority')

    # Weekly command
    weekly_parser = subparsers.add_parser('weekly', help='Generate week of content')
    weekly_parser.add_argument('--posts-per-day', type=int, default=3, help='Posts per day')
    weekly_parser.add_argument('--campaign', default='fitness-launch', help='Campaign name')

    args = parser.parse_args()

    generator = FitnessContentGenerator()

    if args.command == 'single':
        post = generator.generate_single(args.type, args.campaign)
        print("\n" + "=" * 50)
        print("GENERATED POST")
        print("=" * 50)
        print(post)
        print(f"\n[{len(post)} characters]")

    elif args.command == 'batch':
        if args.schedule:
            posts = generator.generate_and_schedule(
                count=args.count,
                campaign=args.campaign,
                content_types=args.types,
                priority=args.priority
            )
            print(f"\n✅ Generated and scheduled {len(posts)} posts")
        else:
            posts = generator.generate_batch(
                count=args.count,
                campaign=args.campaign,
                content_types=args.types
            )
            print(f"\n✅ Generated {len(posts)} posts")

        for i, post in enumerate(posts, 1):
            print(f"\n--- Post {i} ({post['content_type']}) ---")
            print(post['text'][:100] + "..." if len(post['text']) > 100 else post['text'])
            print(f"[{post['character_count']} chars]")
            if 'post_id' in post:
                print(f"[Scheduled: {post.get('scheduled_time', 'Pending')}]")

    elif args.command == 'weekly':
        posts = generator.generate_weekly(
            posts_per_day=args.posts_per_day,
            campaign=args.campaign
        )
        print(f"\n✅ Generated {len(posts)} posts for the week")

        current_date = None
        for post in posts:
            if post['date'] != current_date:
                current_date = post['date']
                print(f"\n📅 {post['day_of_week']} ({post['date']})")
            print(f"  {post['post_number']}. [{post['content_type']}] {post['text'][:50]}...")

    else:
        parser.print_help()

    return 0


if __name__ == '__main__':
    exit(main())
