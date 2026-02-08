"""
Content Metadata Generator for Fitness Influencer AI

Generate platform-optimized hashtags, descriptions, and SEO keywords.
Includes trending hashtag integration and fitness-specific tag library.

Story 015: Implement hashtag and description generator

Usage:
    from backend.content_metadata import generate_metadata, Platform

    # Generate metadata for TikTok fitness video
    metadata = await generate_metadata(
        transcription_text="Today we're doing a 10-minute HIIT workout...",
        platform=Platform.TIKTOK,
        category="workout"
    )

    print(f"Hashtags: {metadata.hashtags}")
    print(f"Description: {metadata.description}")
"""

import os
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set
from enum import Enum
import random
from datetime import datetime, timedelta

from backend.platform_exporter import Platform
from backend.logging_config import get_logger

logger = get_logger(__name__)


class FitnessCategory(Enum):
    """Fitness content categories."""
    WORKOUT = "workout"
    NUTRITION = "nutrition"
    MOTIVATION = "motivation"
    TRANSFORMATION = "transformation"
    TUTORIAL = "tutorial"
    TIPS = "tips"
    CHALLENGE = "challenge"
    EQUIPMENT = "equipment"
    RECOVERY = "recovery"
    LIFESTYLE = "lifestyle"


# Fitness-specific hashtag library (100+ tags organized by category)
FITNESS_HASHTAGS: Dict[FitnessCategory, List[str]] = {
    FitnessCategory.WORKOUT: [
        "workout", "fitness", "gym", "training", "exercise", "fitnessmotivation",
        "gymlife", "workoutmotivation", "fitnessjourney", "homeworkout",
        "strengthtraining", "cardio", "hiit", "functionaltraining", "bootcamp",
        "crossfit", "bodybuilding", "powerlifting", "workoutroutine", "fitfam",
        "legday", "armday", "chestday", "backday", "shoulderday", "absworkout",
        "fullbodyworkout", "morningworkout", "nightworkout", "gymrat"
    ],
    FitnessCategory.NUTRITION: [
        "nutrition", "healthyeating", "mealprep", "eatclean", "healthyfood",
        "macros", "protein", "diet", "weightloss", "cleaneating",
        "healthylifestyle", "wholefoods", "mealplan", "highprotein", "lowcarb",
        "keto", "vegan", "plantbased", "supplements", "preworkout"
    ],
    FitnessCategory.MOTIVATION: [
        "motivation", "fitnessmotivation", "gymotivation", "noexcuses", "mindset",
        "dedication", "discipline", "consistency", "goals", "nevergiveup",
        "believeinyourself", "pushyourself", "workhard", "grind", "hustle",
        "inspiration", "fitspiration", "motivationmonday", "transformationtuesday"
    ],
    FitnessCategory.TRANSFORMATION: [
        "transformation", "beforeandafter", "weightlosstransformation", "fitnesstransformation",
        "bodytransformation", "progresspic", "weightlossjourney", "gains",
        "musclegain", "fatloss", "gettingfit", "fitnessgoals", "results"
    ],
    FitnessCategory.TUTORIAL: [
        "tutorial", "howtotutorial", "exercisetutorial", "formcheck", "properform",
        "fitnesstips", "workouttips", "gymtips", "learntoday", "technique",
        "formtips", "exercise101", "beginnerfitness"
    ],
    FitnessCategory.TIPS: [
        "fitnesstips", "healthtips", "gymtips", "workouttips", "nutritiontips",
        "weightlosstips", "musclebuildingtips", "recoverytips", "lifehacks"
    ],
    FitnessCategory.CHALLENGE: [
        "fitnesschallenge", "workoutchallenge", "30daychallenge", "challenge",
        "plankchallenge", "squatchallenge", "pushupchallenge", "abschallenge"
    ],
    FitnessCategory.EQUIPMENT: [
        "homegym", "gymequipment", "dumbbells", "kettlebells", "resistancebands",
        "barbells", "fitnessequipment", "homeworkoutequipment"
    ],
    FitnessCategory.RECOVERY: [
        "recovery", "restday", "stretching", "flexibility", "mobility",
        "yoga", "foam roller", "massage", "sleep", "selfcare"
    ],
    FitnessCategory.LIFESTYLE: [
        "fitlife", "healthylifestyle", "fitnesslifestyle", "activelifestyle",
        "wellness", "health", "selfimprovement", "mindandbody"
    ],
}

# Platform-specific hashtag limits and recommendations
PLATFORM_HASHTAG_LIMITS: Dict[Platform, Dict[str, int]] = {
    Platform.TIKTOK: {"min": 3, "max": 5, "optimal": 4},
    Platform.INSTAGRAM_REELS: {"min": 5, "max": 30, "optimal": 10},
    Platform.INSTAGRAM_FEED: {"min": 5, "max": 30, "optimal": 15},
    Platform.INSTAGRAM_STORY: {"min": 1, "max": 10, "optimal": 3},
    Platform.YOUTUBE_SHORTS: {"min": 3, "max": 15, "optimal": 8},
    Platform.YOUTUBE_LONG: {"min": 5, "max": 15, "optimal": 10},
    Platform.LINKEDIN: {"min": 3, "max": 5, "optimal": 3},
    Platform.TWITTER: {"min": 1, "max": 3, "optimal": 2},
    Platform.FACEBOOK_REELS: {"min": 3, "max": 10, "optimal": 5},
}

# Description length limits by platform
PLATFORM_DESCRIPTION_LIMITS: Dict[Platform, int] = {
    Platform.TIKTOK: 2200,
    Platform.INSTAGRAM_REELS: 2200,
    Platform.INSTAGRAM_FEED: 2200,
    Platform.INSTAGRAM_STORY: 0,  # No description on stories
    Platform.YOUTUBE_SHORTS: 100,  # Title only
    Platform.YOUTUBE_LONG: 5000,
    Platform.LINKEDIN: 3000,
    Platform.TWITTER: 280,
    Platform.FACEBOOK_REELS: 2200,
}


@dataclass
class ContentMetadata:
    """Generated metadata for content."""
    hashtags: List[str]
    description: str
    keywords: List[str]
    category: str
    platform: str
    hashtag_string: str  # Pre-formatted for copy-paste

    def to_dict(self) -> dict:
        return {
            "hashtags": self.hashtags,
            "hashtag_count": len(self.hashtags),
            "hashtag_string": self.hashtag_string,
            "description": self.description,
            "keywords": self.keywords,
            "category": self.category,
            "platform": self.platform
        }


def extract_keywords(text: str, max_keywords: int = 20) -> List[str]:
    """
    Extract keywords from transcription text.

    Uses simple word frequency analysis and fitness term matching.
    """
    if not text:
        return []

    # Normalize text
    text_lower = text.lower()

    # Common fitness keywords to look for
    fitness_keywords = {
        "workout", "exercise", "reps", "sets", "muscle", "strength",
        "cardio", "hiit", "weight", "lift", "squat", "deadlift",
        "bench", "press", "curl", "pullup", "pushup", "plank",
        "core", "abs", "legs", "arms", "back", "chest", "shoulders",
        "protein", "calories", "diet", "nutrition", "meal", "prep",
        "recovery", "rest", "sleep", "hydration", "stretch",
        "transformation", "goals", "motivation", "progress", "results",
        "beginner", "advanced", "form", "technique", "tip",
        "challenge", "routine", "program", "plan", "schedule"
    }

    # Find matching keywords
    found = []
    words = re.findall(r'\b[a-z]+\b', text_lower)

    for word in words:
        if word in fitness_keywords and word not in found:
            found.append(word)

    # Add frequency-based keywords
    word_count = {}
    for word in words:
        if len(word) > 4:  # Skip short words
            word_count[word] = word_count.get(word, 0) + 1

    # Sort by frequency
    frequent = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
    for word, count in frequent[:max_keywords]:
        if word not in found and count >= 2:
            found.append(word)

    return found[:max_keywords]


def categorize_content(keywords: List[str]) -> FitnessCategory:
    """
    Determine content category based on keywords.
    """
    category_scores = {cat: 0 for cat in FitnessCategory}

    category_keywords = {
        FitnessCategory.WORKOUT: {"workout", "exercise", "reps", "sets", "hiit", "cardio"},
        FitnessCategory.NUTRITION: {"protein", "calories", "diet", "meal", "nutrition", "eat"},
        FitnessCategory.MOTIVATION: {"motivation", "goals", "mindset", "dedication"},
        FitnessCategory.TRANSFORMATION: {"transformation", "progress", "before", "after", "results"},
        FitnessCategory.TUTORIAL: {"how", "technique", "form", "tutorial", "guide"},
        FitnessCategory.TIPS: {"tip", "tips", "advice", "mistake", "avoid"},
        FitnessCategory.CHALLENGE: {"challenge", "day", "week", "30"},
        FitnessCategory.EQUIPMENT: {"dumbbell", "barbell", "band", "equipment", "machine"},
        FitnessCategory.RECOVERY: {"recovery", "rest", "stretch", "sleep", "mobility"},
        FitnessCategory.LIFESTYLE: {"lifestyle", "life", "wellness", "health", "routine"},
    }

    for keyword in keywords:
        for cat, cat_words in category_keywords.items():
            if keyword in cat_words:
                category_scores[cat] += 1

    # Return highest scoring category, default to WORKOUT
    max_score = max(category_scores.values())
    if max_score == 0:
        return FitnessCategory.WORKOUT

    for cat, score in category_scores.items():
        if score == max_score:
            return cat

    return FitnessCategory.WORKOUT


def generate_hashtags(
    keywords: List[str],
    category: FitnessCategory,
    platform: Platform,
    count: Optional[int] = None
) -> List[str]:
    """
    Generate optimized hashtags for content.

    Combines:
    - Category-specific fitness hashtags
    - Keyword-based hashtags
    - Platform-optimized mix
    """
    limits = PLATFORM_HASHTAG_LIMITS.get(
        platform,
        {"min": 5, "max": 15, "optimal": 10}
    )

    target_count = count or limits["optimal"]
    target_count = max(limits["min"], min(limits["max"], target_count))

    selected = set()

    # 1. Add category hashtags (40% of target)
    category_tags = FITNESS_HASHTAGS.get(category, FITNESS_HASHTAGS[FitnessCategory.WORKOUT])
    category_count = max(1, int(target_count * 0.4))
    selected.update(random.sample(category_tags, min(category_count, len(category_tags))))

    # 2. Add keyword-based hashtags (30% of target)
    keyword_count = max(1, int(target_count * 0.3))
    for kw in keywords[:keyword_count]:
        if len(kw) > 3:
            selected.add(kw.replace(" ", ""))

    # 3. Add general fitness hashtags (30% of target)
    general_tags = ["fitness", "gym", "workout", "health", "fitfam", "gains", "fitspo"]
    remaining = target_count - len(selected)
    if remaining > 0:
        available = [t for t in general_tags if t not in selected]
        selected.update(random.sample(available, min(remaining, len(available))))

    # 4. Ensure we meet minimum
    while len(selected) < limits["min"]:
        fallback = random.choice(category_tags)
        selected.add(fallback)

    # 5. Limit to max
    hashtag_list = list(selected)[:limits["max"]]

    # 6. Sort by importance (shorter tags first for visibility)
    hashtag_list.sort(key=lambda x: len(x))

    return hashtag_list


def generate_description(
    text: str,
    keywords: List[str],
    platform: Platform,
    category: FitnessCategory
) -> str:
    """
    Generate platform-optimized description.
    """
    max_length = PLATFORM_DESCRIPTION_LIMITS.get(platform, 2200)

    if max_length == 0:
        return ""

    # Platform-specific templates
    templates = {
        Platform.TIKTOK: "{hook}\n\n{content}\n\n{cta}",
        Platform.INSTAGRAM_REELS: "{hook}\n\n{content}\n\n{cta}\n\n.",
        Platform.INSTAGRAM_FEED: "{hook}\n\n{content}\n\n{cta}\n\n.\n.\n.",
        Platform.YOUTUBE_SHORTS: "{hook} | {cta}",
        Platform.YOUTUBE_LONG: "{hook}\n\n{content}\n\n⏰ Timestamps:\n{timestamps}\n\n{cta}",
        Platform.LINKEDIN: "{hook}\n\n{content}\n\n{cta}",
        Platform.TWITTER: "{hook} {cta}",
        Platform.FACEBOOK_REELS: "{hook}\n\n{content}\n\n{cta}",
    }

    template = templates.get(platform, "{hook}\n\n{content}\n\n{cta}")

    # Generate components
    hook = generate_hook(text, category)
    content = summarize_content(text, category, max_length // 2)
    cta = generate_cta(platform, category)

    # Build description
    description = template.format(
        hook=hook,
        content=content,
        cta=cta,
        timestamps="0:00 - Intro"  # Placeholder
    )

    # Enforce length limit
    if len(description) > max_length:
        description = description[:max_length - 3] + "..."

    return description.strip()


def generate_hook(text: str, category: FitnessCategory) -> str:
    """Generate attention-grabbing hook based on category."""
    hooks = {
        FitnessCategory.WORKOUT: [
            "🔥 Try this workout!",
            "💪 Your daily dose of gains",
            "🏋️ Game-changing workout incoming",
        ],
        FitnessCategory.NUTRITION: [
            "🍎 Fuel your gains with this",
            "🥗 Clean eating made easy",
            "🔬 The science behind nutrition",
        ],
        FitnessCategory.MOTIVATION: [
            "💯 This changed everything for me",
            "🧠 Mindset is everything",
            "⚡ Your daily motivation",
        ],
        FitnessCategory.TRANSFORMATION: [
            "📈 The journey continues",
            "🎯 Progress update!",
            "✨ Transformation in progress",
        ],
        FitnessCategory.TUTORIAL: [
            "📚 Learn proper form",
            "🎓 Master this technique",
            "💡 Pro tip incoming",
        ],
        FitnessCategory.TIPS: [
            "💡 Quick tip for you",
            "🔑 The secret nobody tells you",
            "⚠️ Avoid this common mistake",
        ],
        FitnessCategory.CHALLENGE: [
            "🔥 Challenge accepted?",
            "💪 Can you do this?",
            "🎯 30-day challenge starts now",
        ],
        FitnessCategory.EQUIPMENT: [
            "🏠 Home gym essentials",
            "🔧 Equipment breakdown",
            "💰 Best bang for your buck",
        ],
        FitnessCategory.RECOVERY: [
            "😴 Recovery is key",
            "🧘 Rest day essentials",
            "💆 Take care of your body",
        ],
        FitnessCategory.LIFESTYLE: [
            "✨ Living the fit life",
            "🌟 Day in the life",
            "💪 Fitness lifestyle goals",
        ],
    }

    category_hooks = hooks.get(category, hooks[FitnessCategory.WORKOUT])
    return random.choice(category_hooks)


def summarize_content(text: str, category: FitnessCategory, max_length: int) -> str:
    """Summarize transcription content for description."""
    if not text:
        return ""

    # Simple sentence extraction
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    if not sentences:
        return ""

    # Take first few sentences up to max_length
    summary = ""
    for sentence in sentences[:3]:
        if len(summary) + len(sentence) + 2 > max_length:
            break
        summary += sentence + ". "

    return summary.strip()


def generate_cta(platform: Platform, category: FitnessCategory) -> str:
    """Generate call-to-action based on platform and category."""
    ctas = {
        Platform.TIKTOK: ["Follow for more!", "Like if this helped!", "Save for later!"],
        Platform.INSTAGRAM_REELS: ["Save this for your next workout!", "Follow @handle for daily tips!", "Tag someone who needs this!"],
        Platform.INSTAGRAM_FEED: ["Double tap if you agree! 👊", "What's your favorite exercise? Comment below! 👇"],
        Platform.YOUTUBE_SHORTS: ["Subscribe for more!"],
        Platform.YOUTUBE_LONG: ["👍 Like and Subscribe for more content!\n🔔 Hit the bell for notifications!"],
        Platform.LINKEDIN: ["What are your thoughts? Share in the comments!", "Follow for more fitness insights."],
        Platform.TWITTER: ["RT if you agree!", "Follow for more!"],
        Platform.FACEBOOK_REELS: ["Share with a friend who needs this!", "Follow for daily fitness tips!"],
    }

    platform_ctas = ctas.get(platform, ["Follow for more!"])
    return random.choice(platform_ctas)


async def generate_metadata(
    transcription_text: str,
    platform: Platform,
    category: Optional[str] = None,
    hashtag_count: Optional[int] = None
) -> ContentMetadata:
    """
    Generate complete metadata for content.

    Args:
        transcription_text: Video transcription text
        platform: Target platform
        category: Optional category override
        hashtag_count: Optional hashtag count override

    Returns:
        ContentMetadata with hashtags, description, keywords
    """
    # Extract keywords
    keywords = extract_keywords(transcription_text)

    # Determine category
    if category:
        try:
            content_category = FitnessCategory(category.lower())
        except ValueError:
            content_category = categorize_content(keywords)
    else:
        content_category = categorize_content(keywords)

    # Generate hashtags
    hashtags = generate_hashtags(keywords, content_category, platform, hashtag_count)

    # Generate description
    description = generate_description(
        transcription_text, keywords, platform, content_category
    )

    # Format hashtag string
    hashtag_string = " ".join([f"#{tag}" for tag in hashtags])

    return ContentMetadata(
        hashtags=hashtags,
        description=description,
        keywords=keywords,
        category=content_category.value,
        platform=platform.value,
        hashtag_string=hashtag_string
    )


def get_trending_hashtags(platform: Platform, limit: int = 10) -> List[str]:
    """
    Get trending hashtags for a platform.

    Note: This is a placeholder. Real implementation would integrate with
    platform APIs or third-party trending data providers.
    """
    # Placeholder trending tags (would be updated daily in production)
    trending = {
        Platform.TIKTOK: ["fyp", "foryou", "foryoupage", "viral", "trending", "fitness", "workout", "gym", "gains", "motivation"],
        Platform.INSTAGRAM_REELS: ["reels", "explore", "viral", "trending", "fitness", "workout", "health", "gymlife"],
        Platform.YOUTUBE_SHORTS: ["shorts", "ytshorts", "viral", "trending", "fitness", "workout"],
    }

    platform_trending = trending.get(platform, trending[Platform.TIKTOK])
    return platform_trending[:limit]
