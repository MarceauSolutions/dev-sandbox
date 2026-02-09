#!/usr/bin/env python3
"""
Content Calendar & Strategy for Fitness Influencer

This module provides:
- Weekly content strategy with trending topics
- Specific hooks for each day's content theme
- Integration with the video editing pipeline

Based on viral fitness content research for TikTok/Instagram/YouTube.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel


class ContentFormat(str, Enum):
    """Content format types"""
    SHORT_FORM = "short_form"      # 15-60 seconds
    MEDIUM_FORM = "medium_form"    # 1-5 minutes
    LONG_FORM = "long_form"        # 5-15 minutes
    PLANNING = "planning"          # Internal planning


class ContentTheme(str, Enum):
    """Weekly content themes"""
    QUICK_WORKOUT = "quick_workout"
    GYM_HACK = "gym_hack"
    MYTH_BUSTING = "myth_busting"
    EDUCATIONAL = "educational"
    TRANSFORMATION = "transformation"
    LIFESTYLE = "lifestyle"
    PLANNING = "planning"


# =============================================================================
# CONTENT CALENDAR - Specific trending topics for filming blocks
# Based on: https://www.miracamp.com/learn/content-creation/how-to-create-viral-fitness-content-on-tiktok-instagram
# =============================================================================
CONTENT_CALENDAR: Dict[str, Dict[str, Any]] = {
    "monday": {
        "theme": ContentTheme.QUICK_WORKOUT,
        "topic": "5-min Ab Burnout (no crunches)",
        "hook": "Stop doing crunches. Here's what actually works.",
        "format": ContentFormat.SHORT_FORM,
        "viral_angle": "Myth-busting + actionable",
        "filming_tips": [
            "Film 2-3 short clips (15-60s each)",
            "Raw footage is fine - edit later or post raw",
            "Show the full movement, then breakdown"
        ],
        "hashtag_strategy": ["#absworkout", "#fitnesstips", "#nocrunches", "#coreworkout"]
    },
    "tuesday": {
        "theme": ContentTheme.GYM_HACK,
        "topic": "3 exercises you're doing wrong",
        "hook": "I see this mistake EVERY day at the gym",
        "format": ContentFormat.SHORT_FORM,
        "viral_angle": "Educational + relatable",
        "filming_tips": [
            "Show the WRONG way first (brief)",
            "Then show the CORRECT form",
            "Use split-screen or before/after"
        ],
        "hashtag_strategy": ["#gymhacks", "#fitnesscoach", "#formcheck", "#gymtips"]
    },
    "wednesday": {
        "theme": ContentTheme.MYTH_BUSTING,
        "topic": "Peptide basics: What actually works",
        "hook": "Everyone's asking about peptides. Here's the truth.",
        "format": ContentFormat.MEDIUM_FORM,
        "viral_angle": "Trending topic + authority",
        "filming_tips": [
            "Medium-form (3-5 min)",
            "This is your authority-building content",
            "Include sources/research references"
        ],
        "hashtag_strategy": ["#peptides", "#fitnessscience", "#bodybuilding", "#biohacking"]
    },
    "thursday": {
        "theme": ContentTheme.EDUCATIONAL,
        "topic": "Full compound lift tutorial OR weekly routine",
        "hook": "The only 4 exercises you need for [muscle group]",
        "format": ContentFormat.LONG_FORM,
        "viral_angle": "High-value deep dive",
        "filming_tips": [
            "Structure: Script/outline (30 min) → Film (1 hr) → Edit (1.5 hr)",
            "Include timestamps for each exercise",
            "Show full reps with form cues"
        ],
        "hashtag_strategy": ["#workouttutorial", "#strengthtraining", "#compoundlifts", "#fitnesseducation"]
    },
    "friday": {
        "theme": ContentTheme.TRANSFORMATION,
        "topic": "Weekly transformation or challenge results",
        "hook": "7 days of [protocol]. Here's what happened.",
        "format": ContentFormat.SHORT_FORM,
        "viral_angle": "Before/after + social proof",
        "filming_tips": [
            "Review all filmed content from the week",
            "Quick edits on top 2-3 pieces",
            "Friday afternoon = high engagement time"
        ],
        "hashtag_strategy": ["#transformation", "#progresspic", "#fitnessjourney", "#results"]
    },
    "saturday": {
        "theme": ContentTheme.LIFESTYLE,
        "topic": "Day in the life or meal prep",
        "hook": "What I actually eat in a day",
        "format": ContentFormat.SHORT_FORM,
        "viral_angle": "Authenticity + relatability",
        "filming_tips": [
            "Keep it casual and authentic",
            "Show real meals, not perfect ones",
            "Include macros/calories if relevant"
        ],
        "hashtag_strategy": ["#dayinthelife", "#fitnessmealprep", "#whatieatinaday", "#fitfood"]
    },
    "sunday": {
        "theme": ContentTheme.PLANNING,
        "topic": "Plan content for the week",
        "hook": "N/A - planning session",
        "format": ContentFormat.PLANNING,
        "viral_angle": "N/A",
        "filming_tips": [
            "Write 5-7 short-form hooks",
            "Outline 1 long-form video",
            "Schedule posts if possible"
        ],
        "hashtag_strategy": []
    }
}


# Pydantic models for API responses
class DayContent(BaseModel):
    """Content strategy for a single day"""
    day: str
    theme: str
    topic: str
    hook: str
    format: str
    viral_angle: str
    filming_tips: List[str]
    hashtag_strategy: List[str]


class WeeklyContentPlan(BaseModel):
    """Full weekly content plan"""
    week_start: str
    week_end: str
    days: List[DayContent]
    total_pieces: int
    estimated_hours: float


def get_day_content(day_name: str) -> Optional[DayContent]:
    """
    Get content strategy for a specific day.

    Args:
        day_name: Day of week (monday, tuesday, etc.)

    Returns:
        DayContent model or None if not found
    """
    day_lower = day_name.lower()
    if day_lower not in CONTENT_CALENDAR:
        return None

    content = CONTENT_CALENDAR[day_lower]
    return DayContent(
        day=day_lower.capitalize(),
        theme=content["theme"].value if isinstance(content["theme"], Enum) else content["theme"],
        topic=content["topic"],
        hook=content["hook"],
        format=content["format"].value if isinstance(content["format"], Enum) else content["format"],
        viral_angle=content["viral_angle"],
        filming_tips=content["filming_tips"],
        hashtag_strategy=content["hashtag_strategy"]
    )


def get_today_content() -> DayContent:
    """Get content strategy for today"""
    today = datetime.now().strftime("%A").lower()
    return get_day_content(today)


def get_weekly_plan(start_date: Optional[datetime] = None) -> WeeklyContentPlan:
    """
    Generate a full weekly content plan.

    Args:
        start_date: Start date (defaults to next Monday)

    Returns:
        WeeklyContentPlan with all 7 days
    """
    if start_date is None:
        # Start from next Monday
        today = datetime.now()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        start_date = today + timedelta(days=days_until_monday)

    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=6)

    days = []
    content_pieces = 0

    day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for day_name in day_names:
        day_content = get_day_content(day_name)
        if day_content:
            days.append(day_content)
            if day_content.format != "planning":
                content_pieces += 1

    # Estimated hours: 1hr short, 2hr medium, 4hr long
    hours_map = {"short_form": 1, "medium_form": 2, "long_form": 4, "planning": 1}
    estimated_hours = sum(
        hours_map.get(d.format, 1) for d in days
    )

    return WeeklyContentPlan(
        week_start=start_date.strftime("%Y-%m-%d"),
        week_end=end_date.strftime("%Y-%m-%d"),
        days=days,
        total_pieces=content_pieces,
        estimated_hours=estimated_hours
    )


def generate_caption(day_name: str, custom_topic: Optional[str] = None) -> Dict[str, str]:
    """
    Generate captions for different platforms based on content strategy.

    Args:
        day_name: Day of week
        custom_topic: Override the default topic

    Returns:
        Dict with platform-specific captions
    """
    content = CONTENT_CALENDAR.get(day_name.lower(), {})
    if not content:
        return {"error": f"No content strategy for {day_name}"}

    topic = custom_topic or content["topic"]
    hook = content["hook"]
    hashtags = content.get("hashtag_strategy", [])

    # Platform-specific captions
    captions = {
        "tiktok": f"{hook}\n\n{topic}\n\n{' '.join(hashtags[:8])}",
        "instagram_reel": f"{hook}\n\n{topic}\n\n.\n.\n.\n{' '.join(hashtags[:20])}",
        "instagram_story": f"{hook}\n\nNew content 👆",
        "youtube_short": f"{hook} | {topic}",
        "youtube_long": f"{topic} | Complete Guide\n\n{hook}\n\nIn this video:\n- Point 1\n- Point 2\n- Point 3\n\n{' '.join(hashtags[:5])}"
    }

    return captions


# CLI interface for testing
if __name__ == "__main__":
    import json
    from datetime import datetime

    print("=" * 60)
    print("📅 FITNESS INFLUENCER CONTENT CALENDAR")
    print("=" * 60)

    today = get_today_content()
    if today:
        print(f"\n📆 TODAY ({today.day}):")
        print(f"   Theme: {today.theme}")
        print(f"   Topic: {today.topic}")
        print(f"   Hook: \"{today.hook}\"")
        print(f"   Format: {today.format}")
        print(f"   Viral angle: {today.viral_angle}")

    print("\n" + "=" * 60)
    print("📋 FULL WEEK PLAN:")
    print("=" * 60)

    week = get_weekly_plan()
    print(f"\nWeek: {week.week_start} to {week.week_end}")
    print(f"Total pieces: {week.total_pieces}")
    print(f"Estimated hours: {week.estimated_hours}")

    for day in week.days:
        print(f"\n{day.day}:")
        print(f"   {day.theme} | {day.topic}")
        print(f"   Hook: \"{day.hook}\"")
