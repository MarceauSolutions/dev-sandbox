#!/usr/bin/env python3
"""
Cross-Platform Content Optimizer Module

Generates platform-specific optimization recommendations for fitness content.
Helps influencers adapt one piece of content for multiple platforms efficiently.

Supported Platforms:
- TikTok
- Instagram (Feed, Reels, Stories)
- YouTube (Standard, Shorts)
- Twitter/X
- Facebook
- LinkedIn
- Threads
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import json


@dataclass
class PlatformSpecs:
    """Platform-specific content specifications."""
    name: str
    video_aspect_ratio: str
    max_video_length: int  # seconds
    ideal_video_length: tuple[int, int]  # min, max in seconds
    max_caption_length: int
    ideal_caption_length: tuple[int, int]
    hashtag_limit: int
    ideal_hashtag_count: tuple[int, int]
    best_posting_times: list[str]  # HH:MM format
    best_days: list[str]
    features: list[str]
    tips: list[str]


class CrossPlatformOptimizer:
    """Optimize content for different social media platforms."""

    PLATFORMS = {
        "tiktok": PlatformSpecs(
            name="TikTok",
            video_aspect_ratio="9:16",
            max_video_length=600,  # 10 minutes
            ideal_video_length=(15, 60),
            max_caption_length=2200,
            ideal_caption_length=(50, 150),
            hashtag_limit=100,
            ideal_hashtag_count=(3, 5),
            best_posting_times=["07:00", "12:00", "15:00", "19:00", "21:00"],
            best_days=["Tuesday", "Thursday", "Friday"],
            features=["duets", "stitches", "sounds", "effects", "green_screen"],
            tips=[
                "Hook viewers in first 1-3 seconds",
                "Use trending sounds for discovery",
                "Face-to-camera content performs best",
                "End with call-to-action or question",
                "Post 1-4x per day for growth"
            ]
        ),
        "instagram_reels": PlatformSpecs(
            name="Instagram Reels",
            video_aspect_ratio="9:16",
            max_video_length=90,
            ideal_video_length=(15, 30),
            max_caption_length=2200,
            ideal_caption_length=(125, 200),
            hashtag_limit=30,
            ideal_hashtag_count=(3, 5),
            best_posting_times=["06:00", "12:00", "17:00", "20:00"],
            best_days=["Monday", "Tuesday", "Wednesday"],
            features=["collab", "remix", "audio", "effects", "templates"],
            tips=[
                "First frame must be compelling (thumbnail)",
                "Use on-screen text for silent viewers",
                "Reels get 2x reach vs feed posts",
                "Cross-post to Facebook Reels automatically",
                "Add 3-5 relevant hashtags in caption"
            ]
        ),
        "instagram_feed": PlatformSpecs(
            name="Instagram Feed",
            video_aspect_ratio="4:5",
            max_video_length=60,
            ideal_video_length=(15, 30),
            max_caption_length=2200,
            ideal_caption_length=(150, 300),
            hashtag_limit=30,
            ideal_hashtag_count=(5, 10),
            best_posting_times=["11:00", "13:00", "19:00"],
            best_days=["Monday", "Wednesday", "Friday"],
            features=["carousel", "tags", "location", "alt_text"],
            tips=[
                "Carousel posts get highest engagement",
                "First slide determines swipe rate",
                "Educational carousels perform well",
                "Use consistent visual branding",
                "Mix hashtag sizes (big, medium, niche)"
            ]
        ),
        "instagram_stories": PlatformSpecs(
            name="Instagram Stories",
            video_aspect_ratio="9:16",
            max_video_length=60,
            ideal_video_length=(5, 15),
            max_caption_length=0,  # No traditional caption
            ideal_caption_length=(0, 50),  # On-screen text
            hashtag_limit=10,
            ideal_hashtag_count=(1, 3),
            best_posting_times=["08:00", "12:00", "20:00"],
            best_days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            features=["polls", "questions", "quizzes", "links", "mentions", "countdown"],
            tips=[
                "Post 3-7 stories per day",
                "Use interactive stickers for engagement",
                "Stories expire in 24h - create urgency",
                "First 3 frames determine if viewers continue",
                "Behind-the-scenes content works well"
            ]
        ),
        "youtube": PlatformSpecs(
            name="YouTube",
            video_aspect_ratio="16:9",
            max_video_length=43200,  # 12 hours
            ideal_video_length=(480, 900),  # 8-15 minutes
            max_caption_length=5000,
            ideal_caption_length=(200, 500),
            hashtag_limit=15,
            ideal_hashtag_count=(3, 5),
            best_posting_times=["14:00", "15:00", "16:00", "17:00"],
            best_days=["Friday", "Saturday", "Sunday"],
            features=["chapters", "cards", "end_screens", "playlists", "community"],
            tips=[
                "8-15 minute videos perform best for ad revenue",
                "First 30 seconds determine watch time",
                "Custom thumbnails are mandatory",
                "Use chapters for longer videos",
                "Consistency matters more than frequency"
            ]
        ),
        "youtube_shorts": PlatformSpecs(
            name="YouTube Shorts",
            video_aspect_ratio="9:16",
            max_video_length=60,
            ideal_video_length=(15, 45),
            max_caption_length=100,
            ideal_caption_length=(30, 60),
            hashtag_limit=3,
            ideal_hashtag_count=(1, 2),
            best_posting_times=["12:00", "15:00", "18:00"],
            best_days=["Saturday", "Sunday"],
            features=["shorts_shelf", "remix", "sounds"],
            tips=[
                "Must be under 60 seconds with 9:16 ratio",
                "#Shorts in title/description helps discovery",
                "Loop-worthy content gets more views",
                "Shorts can drive subscribers to long-form",
                "Post 2-3 Shorts per long-form video"
            ]
        ),
        "twitter": PlatformSpecs(
            name="Twitter/X",
            video_aspect_ratio="16:9",
            max_video_length=140,
            ideal_video_length=(15, 45),
            max_caption_length=280,
            ideal_caption_length=(100, 200),
            hashtag_limit=10,
            ideal_hashtag_count=(1, 2),
            best_posting_times=["08:00", "12:00", "17:00"],
            best_days=["Wednesday", "Thursday"],
            features=["threads", "polls", "spaces", "communities"],
            tips=[
                "Video tweets get 10x more engagement",
                "Keep hashtags minimal (1-2 max)",
                "Threads perform well for fitness tips",
                "Engage in replies for algorithm boost",
                "Tweet 3-5x per day for visibility"
            ]
        ),
        "threads": PlatformSpecs(
            name="Threads",
            video_aspect_ratio="9:16",
            max_video_length=300,
            ideal_video_length=(15, 60),
            max_caption_length=500,
            ideal_caption_length=(100, 300),
            hashtag_limit=0,  # No hashtags yet
            ideal_hashtag_count=(0, 0),
            best_posting_times=["09:00", "12:00", "20:00"],
            best_days=["Monday", "Tuesday", "Wednesday"],
            features=["replies", "reposts", "quotes"],
            tips=[
                "Text-based platform - captions matter most",
                "Cross-post from Instagram for reach",
                "Conversational content performs well",
                "No hashtag support yet",
                "Still early - high organic reach"
            ]
        ),
        "linkedin": PlatformSpecs(
            name="LinkedIn",
            video_aspect_ratio="1:1",
            max_video_length=600,
            ideal_video_length=(30, 120),
            max_caption_length=3000,
            ideal_caption_length=(150, 300),
            hashtag_limit=30,
            ideal_hashtag_count=(3, 5),
            best_posting_times=["07:00", "08:00", "12:00", "17:00"],
            best_days=["Tuesday", "Wednesday", "Thursday"],
            features=["articles", "newsletters", "polls", "documents"],
            tips=[
                "Professional/educational content only",
                "First line is crucial (before 'see more')",
                "Native video gets 5x more reach than links",
                "Document carousels perform extremely well",
                "B2B fitness content (corporate wellness) works"
            ]
        )
    }

    def __init__(self):
        """Initialize the optimizer."""
        pass

    def get_platform_specs(self, platform: str) -> Optional[PlatformSpecs]:
        """Get specifications for a specific platform."""
        return self.PLATFORMS.get(platform.lower())

    def optimize_for_platform(
        self,
        content_type: str,
        original_caption: str,
        target_platform: str,
        video_duration: Optional[int] = None,
        hashtags: Optional[list[str]] = None
    ) -> dict:
        """
        Generate optimization recommendations for a specific platform.

        Args:
            content_type: Type of content (video, image, carousel)
            original_caption: Original caption text
            target_platform: Target platform to optimize for
            video_duration: Video duration in seconds (if applicable)
            hashtags: List of hashtags to use

        Returns:
            Optimization recommendations
        """
        specs = self.get_platform_specs(target_platform)
        if not specs:
            return {"error": f"Unknown platform: {target_platform}"}

        result = {
            "platform": specs.name,
            "content_type": content_type,
            "recommendations": {},
            "warnings": [],
            "tips": specs.tips
        }

        # Video optimization
        if content_type == "video" and video_duration:
            result["recommendations"]["video"] = {
                "aspect_ratio": specs.video_aspect_ratio,
                "current_duration": video_duration,
                "max_duration": specs.max_video_length,
                "ideal_duration": f"{specs.ideal_video_length[0]}-{specs.ideal_video_length[1]} seconds",
                "duration_ok": specs.ideal_video_length[0] <= video_duration <= specs.ideal_video_length[1]
            }

            if video_duration > specs.max_video_length:
                result["warnings"].append(
                    f"Video exceeds max length ({specs.max_video_length}s). Must trim."
                )
            elif video_duration > specs.ideal_video_length[1]:
                result["warnings"].append(
                    f"Video longer than ideal ({specs.ideal_video_length[1]}s). Consider shorter version."
                )
            elif video_duration < specs.ideal_video_length[0]:
                result["warnings"].append(
                    f"Video shorter than ideal ({specs.ideal_video_length[0]}s). May need more content."
                )

        # Caption optimization
        caption_length = len(original_caption)
        result["recommendations"]["caption"] = {
            "current_length": caption_length,
            "max_length": specs.max_caption_length,
            "ideal_length": f"{specs.ideal_caption_length[0]}-{specs.ideal_caption_length[1]} chars",
            "length_ok": specs.ideal_caption_length[0] <= caption_length <= specs.ideal_caption_length[1],
            "optimized_caption": self._optimize_caption(original_caption, specs)
        }

        if caption_length > specs.max_caption_length:
            result["warnings"].append(
                f"Caption exceeds max length ({specs.max_caption_length}). Must shorten."
            )

        # Hashtag optimization
        if hashtags:
            result["recommendations"]["hashtags"] = {
                "provided": len(hashtags),
                "max_allowed": specs.hashtag_limit,
                "ideal_count": f"{specs.ideal_hashtag_count[0]}-{specs.ideal_hashtag_count[1]}",
                "recommended": hashtags[:specs.ideal_hashtag_count[1]] if len(hashtags) > specs.ideal_hashtag_count[1] else hashtags
            }

            if len(hashtags) > specs.hashtag_limit:
                result["warnings"].append(
                    f"Too many hashtags ({len(hashtags)}). Max is {specs.hashtag_limit}."
                )

        # Posting time recommendations
        result["recommendations"]["posting"] = {
            "best_times": specs.best_posting_times,
            "best_days": specs.best_days,
            "suggested_time": self._get_next_optimal_time(specs)
        }

        # Platform features to leverage
        result["recommendations"]["features"] = {
            "available": specs.features,
            "suggested": self._suggest_features(content_type, specs)
        }

        return result

    def optimize_for_all_platforms(
        self,
        content_type: str,
        original_caption: str,
        video_duration: Optional[int] = None,
        hashtags: Optional[list[str]] = None,
        platforms: Optional[list[str]] = None
    ) -> dict:
        """
        Generate optimization recommendations for multiple platforms.

        Args:
            content_type: Type of content
            original_caption: Original caption
            video_duration: Video duration (if applicable)
            hashtags: Hashtags to use
            platforms: List of platforms (defaults to all)

        Returns:
            Recommendations for each platform
        """
        if platforms is None:
            platforms = list(self.PLATFORMS.keys())

        results = {
            "original": {
                "content_type": content_type,
                "caption_length": len(original_caption),
                "video_duration": video_duration,
                "hashtag_count": len(hashtags) if hashtags else 0
            },
            "platforms": {},
            "summary": {
                "ready_platforms": [],
                "needs_adjustment": [],
                "not_suitable": []
            }
        }

        for platform in platforms:
            opt = self.optimize_for_platform(
                content_type=content_type,
                original_caption=original_caption,
                target_platform=platform,
                video_duration=video_duration,
                hashtags=hashtags
            )

            if "error" in opt:
                continue

            results["platforms"][platform] = opt

            # Categorize platform readiness
            if not opt["warnings"]:
                results["summary"]["ready_platforms"].append(platform)
            elif any("exceeds max" in w.lower() for w in opt["warnings"]):
                results["summary"]["not_suitable"].append(platform)
            else:
                results["summary"]["needs_adjustment"].append(platform)

        return results

    def _optimize_caption(self, caption: str, specs: PlatformSpecs) -> str:
        """Generate platform-optimized caption."""
        # Truncate if needed
        if len(caption) > specs.max_caption_length:
            caption = caption[:specs.max_caption_length - 3] + "..."

        # For short-form platforms, make it punchy
        if specs.ideal_caption_length[1] <= 200 and len(caption) > specs.ideal_caption_length[1]:
            # Take first sentence or up to ideal length
            sentences = caption.split('. ')
            optimized = sentences[0]
            if len(optimized) > specs.ideal_caption_length[1]:
                optimized = optimized[:specs.ideal_caption_length[1] - 3] + "..."
            return optimized

        return caption

    def _get_next_optimal_time(self, specs: PlatformSpecs) -> str:
        """Get the next optimal posting time."""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_day = now.strftime("%A")

        # Find next best time today
        for time in sorted(specs.best_posting_times):
            if time > current_time:
                return f"Today at {time}"

        # Otherwise, suggest tomorrow
        tomorrow = now + timedelta(days=1)
        tomorrow_day = tomorrow.strftime("%A")
        best_time = specs.best_posting_times[0]

        return f"Tomorrow ({tomorrow_day}) at {best_time}"

    def _suggest_features(self, content_type: str, specs: PlatformSpecs) -> list[str]:
        """Suggest platform features to use."""
        suggestions = []

        # Video-specific features
        if content_type == "video":
            video_features = ["sounds", "audio", "effects", "remix", "chapters"]
            suggestions.extend([f for f in specs.features if f in video_features])

        # Engagement features
        engagement = ["polls", "questions", "quizzes", "countdown"]
        suggestions.extend([f for f in specs.features if f in engagement])

        # Discovery features
        discovery = ["hashtags", "tags", "location", "collab"]
        suggestions.extend([f for f in specs.features if f in discovery])

        return suggestions[:5]  # Return top 5 suggestions


# Convenience function
def optimize_content(
    content_type: str,
    caption: str,
    platforms: list[str],
    video_duration: Optional[int] = None,
    hashtags: Optional[list[str]] = None
) -> dict:
    """
    Convenience function to optimize content for multiple platforms.

    Args:
        content_type: video, image, or carousel
        caption: Original caption text
        platforms: Target platforms
        video_duration: Video duration in seconds
        hashtags: Hashtags to include

    Returns:
        Optimization recommendations for each platform
    """
    optimizer = CrossPlatformOptimizer()
    return optimizer.optimize_for_all_platforms(
        content_type=content_type,
        original_caption=caption,
        video_duration=video_duration,
        hashtags=hashtags,
        platforms=platforms
    )
