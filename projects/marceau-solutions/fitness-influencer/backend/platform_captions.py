"""
Platform-Specific Caption Styling for Fitness Influencer AI

Adapts caption styles per platform. TikTok gets casual/trending,
LinkedIn gets professional, YouTube gets SEO-optimized text.

Story 014: Add platform-specific caption styling

Usage:
    from backend.platform_captions import adapt_captions, Platform

    # Get platform-optimized caption style
    style = adapt_captions(
        base_style="trending",
        platform=Platform.LINKEDIN
    )
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

from backend.caption_styles import (
    get_style,
    StyleTemplate,
    PRESET_STYLES,
    StyleAnimation,
    HighlightStyle
)
from backend.platform_exporter import Platform, PLATFORM_SPECS


@dataclass
class PlatformCaptionConfig:
    """Platform-specific caption configuration."""
    platform: Platform
    recommended_style: str
    font_size_range: tuple  # (min, max)
    position: str
    animation_allowed: bool
    emoji_friendly: bool
    hashtag_in_caption: bool
    max_characters: int
    line_count_max: int
    tone: str  # casual, professional, mixed
    color_recommendations: List[str]
    notes: str = ""


# Platform-specific caption configurations
PLATFORM_CAPTION_CONFIGS: Dict[Platform, PlatformCaptionConfig] = {
    Platform.TIKTOK: PlatformCaptionConfig(
        platform=Platform.TIKTOK,
        recommended_style="trending",
        font_size_range=(48, 72),
        position="bottom",
        animation_allowed=True,
        emoji_friendly=True,
        hashtag_in_caption=True,
        max_characters=150,
        line_count_max=3,
        tone="casual",
        color_recommendations=["#FFFFFF", "#00F2EA", "#FF0050"],  # TikTok colors
        notes="Bold, punchy captions. Trend-aware language."
    ),
    Platform.INSTAGRAM_REELS: PlatformCaptionConfig(
        platform=Platform.INSTAGRAM_REELS,
        recommended_style="clean",
        font_size_range=(42, 64),
        position="bottom",
        animation_allowed=True,
        emoji_friendly=True,
        hashtag_in_caption=False,  # Hashtags go in description
        max_characters=125,
        line_count_max=2,
        tone="casual",
        color_recommendations=["#FFFFFF", "#833AB4", "#FD1D1D"],  # Instagram gradient
        notes="Clean, aesthetic. Minimal text on video."
    ),
    Platform.INSTAGRAM_FEED: PlatformCaptionConfig(
        platform=Platform.INSTAGRAM_FEED,
        recommended_style="minimal",
        font_size_range=(36, 56),
        position="center",
        animation_allowed=True,
        emoji_friendly=True,
        hashtag_in_caption=False,
        max_characters=100,
        line_count_max=2,
        tone="mixed",
        color_recommendations=["#FFFFFF", "#000000"],
        notes="Subtle captions for feed aesthetic."
    ),
    Platform.INSTAGRAM_STORY: PlatformCaptionConfig(
        platform=Platform.INSTAGRAM_STORY,
        recommended_style="glow",
        font_size_range=(42, 60),
        position="center",
        animation_allowed=True,
        emoji_friendly=True,
        hashtag_in_caption=False,
        max_characters=100,
        line_count_max=2,
        tone="casual",
        color_recommendations=["#FFFFFF", "#FF6B6B", "#4ECDC4"],
        notes="Eye-catching, short-form."
    ),
    Platform.YOUTUBE_SHORTS: PlatformCaptionConfig(
        platform=Platform.YOUTUBE_SHORTS,
        recommended_style="subtitle",
        font_size_range=(36, 52),
        position="bottom",
        animation_allowed=False,  # Cleaner for YouTube
        emoji_friendly=False,
        hashtag_in_caption=False,  # Hashtags in title/description
        max_characters=200,
        line_count_max=2,
        tone="mixed",
        color_recommendations=["#FFFFFF", "#FF0000"],  # YouTube red
        notes="Keyword-rich for SEO. Clear, readable."
    ),
    Platform.YOUTUBE_LONG: PlatformCaptionConfig(
        platform=Platform.YOUTUBE_LONG,
        recommended_style="subtitle",
        font_size_range=(32, 48),
        position="bottom",
        animation_allowed=False,
        emoji_friendly=False,
        hashtag_in_caption=False,
        max_characters=250,
        line_count_max=2,
        tone="professional",
        color_recommendations=["#FFFFFF"],
        notes="Standard subtitles. Accessibility focus."
    ),
    Platform.LINKEDIN: PlatformCaptionConfig(
        platform=Platform.LINKEDIN,
        recommended_style="professional",
        font_size_range=(32, 48),
        position="bottom",
        animation_allowed=False,
        emoji_friendly=False,  # Limited emoji use
        hashtag_in_caption=False,
        max_characters=200,
        line_count_max=2,
        tone="professional",
        color_recommendations=["#FFFFFF", "#0077B5"],  # LinkedIn blue
        notes="Formal language. Industry terms welcome."
    ),
    Platform.TWITTER: PlatformCaptionConfig(
        platform=Platform.TWITTER,
        recommended_style="bold",
        font_size_range=(40, 56),
        position="bottom",
        animation_allowed=True,
        emoji_friendly=True,
        hashtag_in_caption=True,
        max_characters=100,
        line_count_max=2,
        tone="casual",
        color_recommendations=["#FFFFFF", "#1DA1F2"],  # Twitter blue
        notes="Punchy, conversation-starting."
    ),
    Platform.FACEBOOK_REELS: PlatformCaptionConfig(
        platform=Platform.FACEBOOK_REELS,
        recommended_style="clean",
        font_size_range=(42, 60),
        position="bottom",
        animation_allowed=True,
        emoji_friendly=True,
        hashtag_in_caption=False,
        max_characters=125,
        line_count_max=2,
        tone="casual",
        color_recommendations=["#FFFFFF", "#1877F2"],  # Facebook blue
        notes="Similar to Instagram Reels styling."
    ),
}


@dataclass
class AdaptedStyle:
    """Adapted caption style for a specific platform."""
    platform: str
    base_style: str
    adapted_style: StyleTemplate
    config: PlatformCaptionConfig
    adaptations_made: List[str]

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "base_style": self.base_style,
            "adapted_style": {
                "font_family": self.adapted_style.font_family,
                "font_size": self.adapted_style.font_size,
                "font_color": self.adapted_style.font_color,
                "outline_color": self.adapted_style.outline_color,
                "outline_width": self.adapted_style.outline_width,
                "shadow_color": self.adapted_style.shadow_color,
                "shadow_offset": self.adapted_style.shadow_offset,
                "highlight_color": self.adapted_style.highlight_color,
                "animation": self.adapted_style.animation.value if self.adapted_style.animation else "none",
                "position": self.adapted_style.position,
            },
            "adaptations_made": self.adaptations_made,
            "platform_config": {
                "tone": self.config.tone,
                "max_characters": self.config.max_characters,
                "emoji_friendly": self.config.emoji_friendly,
            }
        }


def adapt_captions(
    base_style: str,
    platform: Platform,
    custom_overrides: Optional[Dict[str, Any]] = None
) -> AdaptedStyle:
    """
    Adapt a base caption style for a specific platform.

    Args:
        base_style: Name of base style (trending, minimal, etc.)
        platform: Target platform
        custom_overrides: Optional overrides for specific properties

    Returns:
        AdaptedStyle with platform-optimized settings
    """
    # Get base style
    try:
        style = get_style(base_style)
    except ValueError:
        style = get_style("trending")  # Default fallback
        base_style = "trending"

    # Get platform config
    config = PLATFORM_CAPTION_CONFIGS.get(
        platform,
        PLATFORM_CAPTION_CONFIGS[Platform.TIKTOK]
    )

    adaptations = []

    # Create adapted style by copying and modifying
    adapted = StyleTemplate(
        name=f"{base_style}_{platform.value}",
        font_family=style.font_family,
        font_size=style.font_size,
        font_color=style.font_color,
        outline_color=style.outline_color,
        outline_width=style.outline_width,
        shadow_color=style.shadow_color,
        shadow_offset=style.shadow_offset,
        shadow_blur=style.shadow_blur,
        highlight_color=style.highlight_color,
        highlight_style=style.highlight_style,
        animation=style.animation,
        position=style.position,
        background_color=style.background_color,
        background_opacity=style.background_opacity,
        line_spacing=style.line_spacing,
    )

    # Adapt font size to platform range
    min_size, max_size = config.font_size_range
    if adapted.font_size < min_size:
        adapted.font_size = min_size
        adaptations.append(f"Increased font size to {min_size} (platform minimum)")
    elif adapted.font_size > max_size:
        adapted.font_size = max_size
        adaptations.append(f"Reduced font size to {max_size} (platform maximum)")

    # Adapt position
    if adapted.position != config.position:
        adapted.position = config.position
        adaptations.append(f"Changed position to {config.position}")

    # Disable animation if not allowed
    if not config.animation_allowed and adapted.animation != StyleAnimation.NONE:
        adapted.animation = StyleAnimation.NONE
        adaptations.append("Disabled animation (not recommended for platform)")

    # Use platform-recommended color if current color doesn't contrast well
    if config.color_recommendations and adapted.font_color not in config.color_recommendations:
        # Keep white as it works universally
        if adapted.font_color.upper() != "#FFFFFF":
            adaptations.append(f"Recommend using {config.color_recommendations[0]} for better platform consistency")

    # Apply custom overrides
    if custom_overrides:
        for key, value in custom_overrides.items():
            if hasattr(adapted, key):
                setattr(adapted, key, value)
                adaptations.append(f"Applied custom override: {key}={value}")

    return AdaptedStyle(
        platform=platform.value,
        base_style=base_style,
        adapted_style=adapted,
        config=config,
        adaptations_made=adaptations
    )


def get_platform_caption_config(platform: Platform) -> Dict[str, Any]:
    """Get caption configuration for a platform."""
    config = PLATFORM_CAPTION_CONFIGS.get(
        platform,
        PLATFORM_CAPTION_CONFIGS[Platform.TIKTOK]
    )

    return {
        "platform": platform.value,
        "recommended_style": config.recommended_style,
        "font_size_range": {
            "min": config.font_size_range[0],
            "max": config.font_size_range[1]
        },
        "position": config.position,
        "animation_allowed": config.animation_allowed,
        "emoji_friendly": config.emoji_friendly,
        "hashtag_in_caption": config.hashtag_in_caption,
        "max_characters": config.max_characters,
        "line_count_max": config.line_count_max,
        "tone": config.tone,
        "color_recommendations": config.color_recommendations,
        "notes": config.notes
    }


def recommend_style_for_platform(platform: Platform) -> str:
    """Get recommended caption style for a platform."""
    config = PLATFORM_CAPTION_CONFIGS.get(
        platform,
        PLATFORM_CAPTION_CONFIGS[Platform.TIKTOK]
    )
    return config.recommended_style


def list_platform_caption_configs() -> List[Dict[str, Any]]:
    """List all platform caption configurations."""
    return [
        get_platform_caption_config(p)
        for p in Platform
    ]


# Tone-based text transformations
def adapt_text_tone(
    text: str,
    target_tone: str,
    source_tone: str = "neutral"
) -> str:
    """
    Adapt text to match platform tone.

    Note: This is a placeholder for future AI-based text adaptation.
    Currently returns text unchanged.
    """
    # TODO: Integrate with AI for actual tone adaptation
    # For now, return unchanged
    return text


# Character limit enforcement
def enforce_character_limit(
    text: str,
    max_chars: int,
    truncation_suffix: str = "..."
) -> str:
    """Enforce character limit with smart truncation."""
    if len(text) <= max_chars:
        return text

    # Try to truncate at word boundary
    truncated = text[:max_chars - len(truncation_suffix)]
    last_space = truncated.rfind(" ")

    if last_space > max_chars * 0.7:  # Keep at least 70% of content
        truncated = truncated[:last_space]

    return truncated.rstrip() + truncation_suffix
