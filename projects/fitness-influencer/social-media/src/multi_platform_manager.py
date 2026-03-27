#!/usr/bin/env python3
"""
multi_platform_manager.py - Unified Multi-Platform Social Media Management

Coordinates content distribution across multiple social media platforms:
- X (Twitter) - Text posts and short videos
- YouTube - Long-form videos and Shorts
- Instagram - Reels and Stories (via later integration)
- TikTok - Short-form video (via later integration)
- LinkedIn - Professional content (via later integration)

This module serves as the central hub for the content repurposing pipeline,
following Nick Saraev's multi-platform strategy.

Usage:
    # Check platform status
    python -m src.multi_platform_manager status

    # Post to specific platform
    python -m src.multi_platform_manager post --platform x --content "My post"

    # Repurpose long-form video to all platforms
    python -m src.multi_platform_manager repurpose --video path/to/video.mp4

    # Generate weekly content calendar
    python -m src.multi_platform_manager calendar --week
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field
from enum import Enum

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class Platform(Enum):
    """Supported social media platforms."""
    X = "x"
    YOUTUBE = "youtube"
    YOUTUBE_SHORTS = "youtube_shorts"
    INSTAGRAM = "instagram"
    INSTAGRAM_REELS = "instagram_reels"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"


class ContentType(Enum):
    """Types of content that can be posted."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO_SHORT = "video_short"  # <60s
    VIDEO_LONG = "video_long"    # >60s
    THREAD = "thread"
    CAROUSEL = "carousel"


class PlatformStatus(Enum):
    """Status of platform integration."""
    READY = "ready"
    CONFIGURED = "configured"      # API keys set but not tested
    NOT_CONFIGURED = "not_configured"
    COMING_SOON = "coming_soon"


# Platform specifications and limits
PLATFORM_SPECS = {
    Platform.X: {
        "name": "X (Twitter)",
        "content_types": [ContentType.TEXT, ContentType.IMAGE, ContentType.VIDEO_SHORT, ContentType.THREAD],
        "video_max_duration": 140,
        "text_max_length": 280,
        "posts_per_day_limit": 50,
        "api_module": "x_scheduler",
        "env_keys": ["X_BEARER_TOKEN", "X_ACCESS_TOKEN", "X_ACCESS_SECRET"],
    },
    Platform.YOUTUBE: {
        "name": "YouTube",
        "content_types": [ContentType.VIDEO_LONG],
        "video_max_duration": 43200,  # 12 hours
        "posts_per_day_limit": 10,
        "api_module": "youtube_uploader",
        "env_keys": ["YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET"],
    },
    Platform.YOUTUBE_SHORTS: {
        "name": "YouTube Shorts",
        "content_types": [ContentType.VIDEO_SHORT],
        "video_max_duration": 60,
        "posts_per_day_limit": 10,
        "api_module": "youtube_uploader",
        "env_keys": ["YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET"],
    },
    Platform.INSTAGRAM: {
        "name": "Instagram",
        "content_types": [ContentType.IMAGE, ContentType.CAROUSEL],
        "text_max_length": 2200,
        "posts_per_day_limit": 25,
        "api_module": None,  # Coming soon
        "env_keys": ["INSTAGRAM_ACCESS_TOKEN"],
    },
    Platform.INSTAGRAM_REELS: {
        "name": "Instagram Reels",
        "content_types": [ContentType.VIDEO_SHORT],
        "video_max_duration": 90,
        "posts_per_day_limit": 25,
        "api_module": None,  # Coming soon
        "env_keys": ["INSTAGRAM_ACCESS_TOKEN"],
    },
    Platform.TIKTOK: {
        "name": "TikTok",
        "content_types": [ContentType.VIDEO_SHORT],
        "video_max_duration": 180,
        "posts_per_day_limit": 50,
        "api_module": None,  # Coming soon
        "env_keys": ["TIKTOK_ACCESS_TOKEN"],
    },
    Platform.LINKEDIN: {
        "name": "LinkedIn",
        "content_types": [ContentType.TEXT, ContentType.IMAGE, ContentType.VIDEO_SHORT],
        "text_max_length": 3000,
        "video_max_duration": 600,
        "posts_per_day_limit": 20,
        "api_module": None,  # Coming soon
        "env_keys": ["LINKEDIN_ACCESS_TOKEN"],
    },
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class PlatformInfo:
    """Information about a platform's configuration status."""
    platform: str
    name: str
    status: str
    content_types: List[str]
    configured_keys: List[str]
    missing_keys: List[str]
    ready: bool


@dataclass
class PostResult:
    """Result of posting to a platform."""
    success: bool
    platform: str
    post_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None
    posted_at: Optional[str] = None


@dataclass
class RepurposeResult:
    """Result of repurposing content to multiple platforms."""
    source_file: str
    source_type: str
    results: List[PostResult] = field(default_factory=list)
    clips_generated: int = 0

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def failure_count(self) -> int:
        return sum(1 for r in self.results if not r.success)


# ============================================================================
# MAIN CLASS
# ============================================================================

class MultiPlatformManager:
    """
    Manages content distribution across multiple social media platforms.

    Implements Nick Saraev's content repurposing strategy:
    1. Create long-form YouTube content
    2. Extract clips for Shorts/Reels/TikTok
    3. Create text versions for X/LinkedIn
    4. Schedule across platforms with staggered timing
    """

    CONFIG_DIR = Path(__file__).parent.parent / "config"
    TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
    OUTPUT_DIR = Path(__file__).parent.parent / "output"

    def __init__(self):
        """Initialize the multi-platform manager."""
        self._ensure_directories()
        self.nick_style = self._load_nick_style()
        self._platforms = {}
        self._init_platforms()

    def _ensure_directories(self):
        """Create necessary directories."""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def _load_nick_style(self) -> Dict:
        """Load Nick Saraev style configuration."""
        style_file = self.TEMPLATES_DIR / "nick_saraev_style.json"
        if style_file.exists():
            with open(style_file) as f:
                return json.load(f)
        return {}

    def _init_platforms(self):
        """Initialize platform integrations."""
        for platform, spec in PLATFORM_SPECS.items():
            self._platforms[platform] = self._check_platform_status(platform, spec)

    def _check_platform_status(self, platform: Platform, spec: Dict) -> PlatformInfo:
        """Check the configuration status of a platform."""
        configured_keys = []
        missing_keys = []

        for key in spec.get("env_keys", []):
            if os.getenv(key):
                configured_keys.append(key)
            else:
                missing_keys.append(key)

        # Determine status
        if spec.get("api_module") is None:
            status = PlatformStatus.COMING_SOON
            ready = False
        elif not missing_keys:
            status = PlatformStatus.READY
            ready = True
        elif configured_keys:
            status = PlatformStatus.CONFIGURED
            ready = False
        else:
            status = PlatformStatus.NOT_CONFIGURED
            ready = False

        return PlatformInfo(
            platform=platform.value,
            name=spec["name"],
            status=status.value,
            content_types=[ct.value for ct in spec["content_types"]],
            configured_keys=configured_keys,
            missing_keys=missing_keys,
            ready=ready
        )

    def get_platform_status(self) -> Dict[str, PlatformInfo]:
        """Get the status of all platforms."""
        return {p.value: info for p, info in self._platforms.items()}

    def get_ready_platforms(self) -> List[Platform]:
        """Get list of platforms ready for posting."""
        return [p for p, info in self._platforms.items() if info.ready]

    def print_status(self):
        """Print a formatted status report of all platforms."""
        print("\n" + "=" * 60)
        print("MULTI-PLATFORM STATUS REPORT")
        print("=" * 60)

        ready_count = 0
        coming_soon_count = 0

        for platform, info in self._platforms.items():
            status_emoji = {
                "ready": "✅",
                "configured": "⚠️",
                "not_configured": "❌",
                "coming_soon": "🔜"
            }.get(info.status, "❓")

            print(f"\n{status_emoji} {info.name}")
            print(f"   Status: {info.status.replace('_', ' ').title()}")
            print(f"   Content Types: {', '.join(info.content_types)}")

            if info.status == "ready":
                ready_count += 1
                print(f"   Ready to post!")
            elif info.status == "coming_soon":
                coming_soon_count += 1
                print(f"   Integration coming soon")
            elif info.missing_keys:
                print(f"   Missing: {', '.join(info.missing_keys)}")

        print(f"\n{'=' * 60}")
        print(f"Ready: {ready_count} | Coming Soon: {coming_soon_count} | Total: {len(self._platforms)}")
        print("=" * 60 + "\n")

    def post_to_x(self, content: str, media_path: Optional[str] = None) -> PostResult:
        """Post content to X (Twitter)."""
        info = self._platforms.get(Platform.X)
        if not info or not info.ready:
            return PostResult(
                success=False,
                platform="x",
                error="X platform not configured"
            )

        try:
            from .x_scheduler import PostScheduler
            scheduler = PostScheduler()

            # Add to queue and post immediately
            post_id = scheduler.add_post(content, post_now=True)

            if post_id:
                return PostResult(
                    success=True,
                    platform="x",
                    post_id=str(post_id),
                    url=f"https://x.com/i/status/{post_id}",
                    posted_at=datetime.now().isoformat()
                )
            else:
                return PostResult(
                    success=False,
                    platform="x",
                    error="Failed to post - check scheduler logs"
                )
        except Exception as e:
            logger.error(f"Error posting to X: {e}")
            return PostResult(
                success=False,
                platform="x",
                error=str(e)
            )

    def post_to_youtube(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        is_short: bool = False,
        privacy: str = "private"
    ) -> PostResult:
        """Post video to YouTube or YouTube Shorts."""
        platform = Platform.YOUTUBE_SHORTS if is_short else Platform.YOUTUBE
        info = self._platforms.get(platform)

        if not info or not info.ready:
            return PostResult(
                success=False,
                platform=platform.value,
                error=f"{platform.value} not configured"
            )

        try:
            from .youtube_uploader import YouTubeUploader
            uploader = YouTubeUploader()

            if not uploader.is_ready():
                return PostResult(
                    success=False,
                    platform=platform.value,
                    error="YouTube uploader not authenticated"
                )

            if is_short:
                result = uploader.upload_short(
                    video_path=video_path,
                    title=title,
                    description=description,
                    tags=tags,
                    privacy=privacy
                )
            else:
                result = uploader.upload_video(
                    video_path=video_path,
                    title=title,
                    description=description,
                    tags=tags,
                    privacy=privacy
                )

            if result.success:
                return PostResult(
                    success=True,
                    platform=platform.value,
                    post_id=result.video_id,
                    url=result.url,
                    posted_at=datetime.now().isoformat()
                )
            else:
                return PostResult(
                    success=False,
                    platform=platform.value,
                    error=result.error
                )
        except Exception as e:
            logger.error(f"Error posting to YouTube: {e}")
            return PostResult(
                success=False,
                platform=platform.value,
                error=str(e)
            )

    def repurpose_video(
        self,
        video_path: str,
        title: str,
        description: str = "",
        platforms: Optional[List[str]] = None,
        generate_clips: bool = True
    ) -> RepurposeResult:
        """
        Repurpose a long-form video to multiple platforms.

        Following Nick Saraev's repurposing pipeline:
        1. Upload original to YouTube
        2. Generate short clips (if enabled)
        3. Post clips to Shorts/Reels/TikTok
        4. Create text summary for X/LinkedIn

        Args:
            video_path: Path to the source video
            title: Video title
            description: Video description
            platforms: List of platforms to post to (default: all ready)
            generate_clips: Whether to generate short clips

        Returns:
            RepurposeResult with all posting results
        """
        result = RepurposeResult(
            source_file=video_path,
            source_type="video_long"
        )

        # Determine target platforms
        target_platforms = platforms or [p.value for p in self.get_ready_platforms()]

        # 1. Post to YouTube (long-form)
        if "youtube" in target_platforms:
            yt_result = self.post_to_youtube(
                video_path=video_path,
                title=title,
                description=description,
                is_short=False,
                privacy="private"  # Start private, make public later
            )
            result.results.append(yt_result)

        # 2. Generate clips (placeholder - would use video_jumpcut.py)
        if generate_clips:
            # TODO: Integrate with video_jumpcut.py to extract clips
            logger.info("Clip generation placeholder - integrate video_jumpcut.py")
            result.clips_generated = 0

        # 3. Create text summary for X
        if "x" in target_platforms:
            # Generate text version of key points
            text_summary = self._generate_text_summary(title, description)
            x_result = self.post_to_x(text_summary)
            result.results.append(x_result)

        return result

    def _generate_text_summary(self, title: str, description: str) -> str:
        """Generate a text summary for X/Twitter from video content."""
        # Use Nick Saraev style hook template
        hooks = self.nick_style.get("video_structure", {}).get("hook", {}).get("examples", [])

        if hooks:
            import random
            hook = random.choice(hooks)
        else:
            hook = title

        # Compose tweet
        tweet = f"{hook}\n\n{description[:200]}..." if len(description) > 200 else f"{hook}\n\n{description}"

        # Truncate to X limit
        if len(tweet) > 280:
            tweet = tweet[:277] + "..."

        return tweet

    def generate_weekly_calendar(self, start_date: Optional[datetime] = None) -> Dict:
        """
        Generate a weekly content calendar following Nick Saraev strategy.

        Returns:
            Dict with day-by-day content plan
        """
        if start_date is None:
            start_date = datetime.now()
            # Start from next Monday
            days_until_monday = (7 - start_date.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            start_date = start_date + timedelta(days=days_until_monday)

        # Get weekly calendar from Nick style
        weekly_plan = self.nick_style.get("weekly_content_calendar", {})

        calendar = {
            "week_start": start_date.strftime("%Y-%m-%d"),
            "week_end": (start_date + timedelta(days=6)).strftime("%Y-%m-%d"),
            "platforms_ready": [p.value for p in self.get_ready_platforms()],
            "days": []
        }

        days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

        for i, day_name in enumerate(days_of_week):
            day_date = start_date + timedelta(days=i)
            day_plan = weekly_plan.get(day_name, {})

            calendar["days"].append({
                "date": day_date.strftime("%Y-%m-%d"),
                "day": day_name.capitalize(),
                "long_form": day_plan.get("long_form"),
                "short_form": day_plan.get("short_form", []),
                "action": day_plan.get("action")
            })

        return calendar

    def print_weekly_calendar(self):
        """Print a formatted weekly content calendar."""
        calendar = self.generate_weekly_calendar()

        print("\n" + "=" * 70)
        print(f"WEEKLY CONTENT CALENDAR: {calendar['week_start']} to {calendar['week_end']}")
        print("=" * 70)
        print(f"Ready Platforms: {', '.join(calendar['platforms_ready'])}")
        print("-" * 70)

        for day in calendar["days"]:
            print(f"\n{day['day']} ({day['date']}):")

            if day["long_form"]:
                print(f"  📹 Long-form: {day['long_form']}")

            if day["short_form"]:
                for item in day["short_form"]:
                    print(f"  📱 Short-form: {item}")

            if day["action"]:
                print(f"  📝 Action: {day['action']}")

            if not day["long_form"] and not day["short_form"] and not day["action"]:
                print("  (No content scheduled)")

        print("\n" + "=" * 70 + "\n")


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI for multi-platform manager."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Multi-Platform Social Media Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Check platform status:
    python -m src.multi_platform_manager status

  Post to X:
    python -m src.multi_platform_manager post --platform x --content "My post"

  Post video to YouTube:
    python -m src.multi_platform_manager post --platform youtube --video video.mp4 --title "Title"

  View weekly calendar:
    python -m src.multi_platform_manager calendar

  Repurpose video (coming soon):
    python -m src.multi_platform_manager repurpose --video video.mp4 --title "Title"
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Status command
    subparsers.add_parser('status', help='Show platform status')

    # Post command
    post_parser = subparsers.add_parser('post', help='Post to a platform')
    post_parser.add_argument('--platform', '-p', required=True,
                            choices=['x', 'youtube', 'youtube_shorts'],
                            help='Target platform')
    post_parser.add_argument('--content', '-c', help='Text content')
    post_parser.add_argument('--video', '-v', help='Video file path')
    post_parser.add_argument('--title', '-t', help='Video title')
    post_parser.add_argument('--description', '-d', default='', help='Description')
    post_parser.add_argument('--tags', nargs='+', help='Tags (space-separated)')
    post_parser.add_argument('--privacy', default='private',
                            choices=['public', 'private', 'unlisted'],
                            help='Privacy setting')

    # Calendar command
    subparsers.add_parser('calendar', help='Show weekly content calendar')

    # Repurpose command
    repurpose_parser = subparsers.add_parser('repurpose', help='Repurpose video to multiple platforms')
    repurpose_parser.add_argument('--video', '-v', required=True, help='Video file path')
    repurpose_parser.add_argument('--title', '-t', required=True, help='Video title')
    repurpose_parser.add_argument('--description', '-d', default='', help='Description')
    repurpose_parser.add_argument('--platforms', nargs='+', help='Target platforms')
    repurpose_parser.add_argument('--no-clips', action='store_true', help='Skip clip generation')

    args = parser.parse_args()

    manager = MultiPlatformManager()

    if args.command == 'status':
        manager.print_status()

    elif args.command == 'calendar':
        manager.print_weekly_calendar()

    elif args.command == 'post':
        if args.platform == 'x':
            if not args.content:
                print("Error: --content required for X posts")
                return 1
            result = manager.post_to_x(args.content)

        elif args.platform in ['youtube', 'youtube_shorts']:
            if not args.video or not args.title:
                print("Error: --video and --title required for YouTube posts")
                return 1

            is_short = args.platform == 'youtube_shorts'
            result = manager.post_to_youtube(
                video_path=args.video,
                title=args.title,
                description=args.description,
                tags=args.tags,
                is_short=is_short,
                privacy=args.privacy
            )

        else:
            print(f"Platform {args.platform} not yet supported")
            return 1

        if result.success:
            print(f"\n✅ Posted successfully to {result.platform}")
            print(f"   Post ID: {result.post_id}")
            print(f"   URL: {result.url}")
        else:
            print(f"\n❌ Failed to post to {result.platform}")
            print(f"   Error: {result.error}")
            return 1

    elif args.command == 'repurpose':
        result = manager.repurpose_video(
            video_path=args.video,
            title=args.title,
            description=args.description,
            platforms=args.platforms,
            generate_clips=not args.no_clips
        )

        print(f"\n📹 Repurpose Results for: {result.source_file}")
        print("-" * 50)
        print(f"Clips generated: {result.clips_generated}")
        print(f"Posts attempted: {len(result.results)}")
        print(f"Successful: {result.success_count}")
        print(f"Failed: {result.failure_count}")

        for r in result.results:
            status = "✅" if r.success else "❌"
            print(f"\n{status} {r.platform}")
            if r.success:
                print(f"   URL: {r.url}")
            else:
                print(f"   Error: {r.error}")

    else:
        parser.print_help()

    return 0


if __name__ == '__main__':
    exit(main())
