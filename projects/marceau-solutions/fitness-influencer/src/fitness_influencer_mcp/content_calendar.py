#!/usr/bin/env python3
"""
Content Calendar Generator Module

Generates balanced content calendars for fitness influencers to prevent burnout
and maintain consistent posting schedules across platforms.

Features:
- 30-day content calendar generation
- Workload balancing (avoids back-to-back high-effort days)
- Content type variety (workout, nutrition, motivation, behind-scenes, etc.)
- Platform-specific posting frequency recommendations
- Holiday and event-aware scheduling
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import calendar
import random


@dataclass
class ContentSlot:
    """Represents a single content slot in the calendar."""
    date: str  # YYYY-MM-DD
    day_of_week: str
    content_type: str
    platform: str
    title_suggestion: str
    effort_level: str  # low, medium, high
    notes: Optional[str] = None
    is_holiday: bool = False
    holiday_name: Optional[str] = None


@dataclass
class ContentTheme:
    """Defines a content theme with associated metadata."""
    name: str
    category: str  # workout, nutrition, motivation, lifestyle, education
    effort_level: str
    suggested_platforms: list[str]
    description: str
    hashtag_suggestions: list[str] = field(default_factory=list)


class ContentCalendarGenerator:
    """Generate balanced content calendars for fitness influencers."""

    # Content categories with effort levels and platform fit
    CONTENT_THEMES = {
        "workout": [
            ContentTheme(
                name="Full Workout Video",
                category="workout",
                effort_level="high",
                suggested_platforms=["youtube", "instagram_reels", "tiktok"],
                description="Complete workout routine with demonstrations",
                hashtag_suggestions=["#workout", "#fitness", "#exercise", "#fitfam"]
            ),
            ContentTheme(
                name="Quick Exercise Demo",
                category="workout",
                effort_level="low",
                suggested_platforms=["instagram_reels", "tiktok", "youtube_shorts"],
                description="Single exercise tutorial or form check",
                hashtag_suggestions=["#exercisetip", "#formcheck", "#fitnesstips"]
            ),
            ContentTheme(
                name="Workout Challenge",
                category="workout",
                effort_level="medium",
                suggested_platforms=["tiktok", "instagram_reels"],
                description="Trending fitness challenge participation",
                hashtag_suggestions=["#fitnesschallenge", "#workoutchallenge"]
            ),
            ContentTheme(
                name="Progress Update",
                category="workout",
                effort_level="low",
                suggested_platforms=["instagram_feed", "instagram_stories", "threads"],
                description="Before/after or transformation content",
                hashtag_suggestions=["#transformation", "#progress", "#fitnessjourney"]
            ),
        ],
        "nutrition": [
            ContentTheme(
                name="Meal Prep Tutorial",
                category="nutrition",
                effort_level="high",
                suggested_platforms=["youtube", "instagram_reels", "tiktok"],
                description="Full meal prep guide with recipes",
                hashtag_suggestions=["#mealprep", "#healthyeating", "#nutrition"]
            ),
            ContentTheme(
                name="Quick Recipe",
                category="nutrition",
                effort_level="medium",
                suggested_platforms=["instagram_reels", "tiktok"],
                description="Simple healthy recipe in 60 seconds",
                hashtag_suggestions=["#healthyrecipe", "#easyrecipe", "#fitfood"]
            ),
            ContentTheme(
                name="What I Eat in a Day",
                category="nutrition",
                effort_level="medium",
                suggested_platforms=["youtube", "tiktok", "instagram_stories"],
                description="Full day of eating documentation",
                hashtag_suggestions=["#whatieatinaday", "#fulldayofeating"]
            ),
            ContentTheme(
                name="Supplement Review",
                category="nutrition",
                effort_level="low",
                suggested_platforms=["youtube", "instagram_feed", "tiktok"],
                description="Review of supplements or products",
                hashtag_suggestions=["#supplementreview", "#fitnesssupplements"]
            ),
        ],
        "motivation": [
            ContentTheme(
                name="Motivational Talk",
                category="motivation",
                effort_level="low",
                suggested_platforms=["instagram_reels", "tiktok", "youtube_shorts"],
                description="Inspirational content or pep talk",
                hashtag_suggestions=["#motivation", "#fitnessmotivation", "#mindset"]
            ),
            ContentTheme(
                name="Story Time",
                category="motivation",
                effort_level="medium",
                suggested_platforms=["youtube", "tiktok", "instagram_reels"],
                description="Personal story or journey sharing",
                hashtag_suggestions=["#storytime", "#myjourney", "#fitnessjourney"]
            ),
            ContentTheme(
                name="Q&A Session",
                category="motivation",
                effort_level="medium",
                suggested_platforms=["instagram_stories", "youtube", "tiktok"],
                description="Answering follower questions",
                hashtag_suggestions=["#qanda", "#askmeanything", "#fitnessqna"]
            ),
        ],
        "lifestyle": [
            ContentTheme(
                name="Day in My Life",
                category="lifestyle",
                effort_level="high",
                suggested_platforms=["youtube", "tiktok"],
                description="Vlog-style content showing daily routine",
                hashtag_suggestions=["#dayinmylife", "#fitnesslifestyle", "#vlog"]
            ),
            ContentTheme(
                name="Behind the Scenes",
                category="lifestyle",
                effort_level="low",
                suggested_platforms=["instagram_stories", "tiktok", "threads"],
                description="Unfiltered look at content creation",
                hashtag_suggestions=["#behindthescenes", "#bts", "#reallife"]
            ),
            ContentTheme(
                name="Gym Tour/Setup",
                category="lifestyle",
                effort_level="medium",
                suggested_platforms=["youtube", "instagram_reels", "tiktok"],
                description="Show gym space or equipment setup",
                hashtag_suggestions=["#homegym", "#gymsetup", "#fitnessequipment"]
            ),
        ],
        "education": [
            ContentTheme(
                name="Fitness Tips",
                category="education",
                effort_level="low",
                suggested_platforms=["instagram_feed", "twitter", "threads", "linkedin"],
                description="Educational carousel or thread",
                hashtag_suggestions=["#fitnesstips", "#workouttips", "#fitnessadvice"]
            ),
            ContentTheme(
                name="Myth Busting",
                category="education",
                effort_level="medium",
                suggested_platforms=["instagram_reels", "tiktok", "youtube_shorts"],
                description="Debunking common fitness myths",
                hashtag_suggestions=["#mythbusting", "#fitnessmyths", "#truthaboutfitness"]
            ),
            ContentTheme(
                name="Science Explained",
                category="education",
                effort_level="high",
                suggested_platforms=["youtube", "instagram_feed"],
                description="Deep dive into fitness science",
                hashtag_suggestions=["#fitnessscience", "#exercisescience"]
            ),
        ],
    }

    # US holidays for 2026 (extensible)
    HOLIDAYS_2026 = {
        "2026-01-01": "New Year's Day",
        "2026-01-19": "MLK Day",
        "2026-02-14": "Valentine's Day",
        "2026-02-16": "Presidents Day",
        "2026-03-17": "St. Patrick's Day",
        "2026-04-05": "Easter",
        "2026-05-10": "Mother's Day",
        "2026-05-25": "Memorial Day",
        "2026-06-21": "Father's Day",
        "2026-07-04": "Independence Day",
        "2026-09-07": "Labor Day",
        "2026-10-31": "Halloween",
        "2026-11-26": "Thanksgiving",
        "2026-12-25": "Christmas",
        "2026-12-31": "New Year's Eve",
    }

    # Fitness-specific dates
    FITNESS_DATES = {
        "01-01": "New Year New You",
        "03-01": "Spring Training Start",
        "05-01": "Summer Body Season",
        "09-01": "Fall Fitness Reset",
    }

    def __init__(self):
        """Initialize the calendar generator."""
        self.effort_weights = {
            "low": 1,
            "medium": 2,
            "high": 3
        }

    def generate_calendar(
        self,
        start_date: Optional[str] = None,
        days: int = 30,
        posts_per_day: int = 2,
        platforms: Optional[list[str]] = None,
        content_focus: Optional[list[str]] = None,
        max_high_effort_per_week: int = 2,
        rest_days: Optional[list[str]] = None
    ) -> dict:
        """
        Generate a balanced content calendar.

        Args:
            start_date: Start date (YYYY-MM-DD), defaults to tomorrow
            days: Number of days to plan
            posts_per_day: Target posts per day (1-4)
            platforms: List of platforms to post on (defaults to all)
            content_focus: Categories to focus on (defaults to balanced mix)
            max_high_effort_per_week: Maximum high-effort content per week
            rest_days: Days of week to skip (e.g., ["Sunday"])

        Returns:
            Complete content calendar with metadata
        """
        # Set defaults
        if start_date is None:
            start = datetime.now() + timedelta(days=1)
        else:
            start = datetime.strptime(start_date, "%Y-%m-%d")

        if platforms is None:
            platforms = ["tiktok", "instagram_reels", "instagram_feed",
                        "instagram_stories", "youtube", "youtube_shorts"]

        if content_focus is None:
            content_focus = list(self.CONTENT_THEMES.keys())

        if rest_days is None:
            rest_days = []

        # Generate calendar
        calendar_slots = []
        weekly_high_effort = 0
        current_week = start.isocalendar()[1]

        for day_offset in range(days):
            current_date = start + timedelta(days=day_offset)
            date_str = current_date.strftime("%Y-%m-%d")
            day_name = current_date.strftime("%A")
            week_num = current_date.isocalendar()[1]

            # Reset weekly counter
            if week_num != current_week:
                weekly_high_effort = 0
                current_week = week_num

            # Skip rest days
            if day_name in rest_days:
                calendar_slots.append(ContentSlot(
                    date=date_str,
                    day_of_week=day_name,
                    content_type="REST DAY",
                    platform="none",
                    title_suggestion="Take a break - recovery is important!",
                    effort_level="none",
                    notes="Scheduled rest day"
                ))
                continue

            # Check for holidays
            is_holiday = date_str in self.HOLIDAYS_2026
            holiday_name = self.HOLIDAYS_2026.get(date_str)

            # Generate content slots for this day
            day_slots = self._generate_day_content(
                date_str=date_str,
                day_name=day_name,
                posts_count=posts_per_day,
                platforms=platforms,
                categories=content_focus,
                weekly_high_effort=weekly_high_effort,
                max_high_effort_per_week=max_high_effort_per_week,
                is_holiday=is_holiday,
                holiday_name=holiday_name
            )

            # Update weekly high effort counter
            for slot in day_slots:
                if slot.effort_level == "high":
                    weekly_high_effort += 1

            calendar_slots.extend(day_slots)

        # Calculate statistics
        stats = self._calculate_stats(calendar_slots)

        return {
            "calendar": [self._slot_to_dict(s) for s in calendar_slots],
            "summary": {
                "start_date": start.strftime("%Y-%m-%d"),
                "end_date": (start + timedelta(days=days-1)).strftime("%Y-%m-%d"),
                "total_days": days,
                "total_content_pieces": len([s for s in calendar_slots if s.content_type != "REST DAY"]),
                "platforms_covered": list(set(s.platform for s in calendar_slots if s.platform != "none")),
                "rest_days_count": len([s for s in calendar_slots if s.content_type == "REST DAY"]),
                "holidays_included": [s.holiday_name for s in calendar_slots if s.is_holiday and s.holiday_name]
            },
            "statistics": stats,
            "recommendations": self._generate_recommendations(calendar_slots, stats)
        }

    def _generate_day_content(
        self,
        date_str: str,
        day_name: str,
        posts_count: int,
        platforms: list[str],
        categories: list[str],
        weekly_high_effort: int,
        max_high_effort_per_week: int,
        is_holiday: bool,
        holiday_name: Optional[str]
    ) -> list[ContentSlot]:
        """Generate content slots for a single day."""
        slots = []
        used_categories = []

        for i in range(posts_count):
            # Avoid same category back-to-back
            available_categories = [c for c in categories if c not in used_categories]
            if not available_categories:
                available_categories = categories

            category = random.choice(available_categories)
            used_categories.append(category)

            # Get themes for this category
            themes = self.CONTENT_THEMES.get(category, [])
            if not themes:
                continue

            # Filter by effort level if needed
            can_do_high_effort = weekly_high_effort < max_high_effort_per_week
            if not can_do_high_effort:
                themes = [t for t in themes if t.effort_level != "high"]
                if not themes:
                    themes = self.CONTENT_THEMES.get(category, [])

            theme = random.choice(themes)

            # Select platform
            suitable_platforms = [p for p in theme.suggested_platforms if p in platforms]
            if not suitable_platforms:
                suitable_platforms = platforms
            platform = random.choice(suitable_platforms)

            # Generate title suggestion
            title = self._generate_title_suggestion(theme, is_holiday, holiday_name)

            # Create notes
            notes = None
            if is_holiday:
                notes = f"Holiday content opportunity: {holiday_name}"

            slots.append(ContentSlot(
                date=date_str,
                day_of_week=day_name,
                content_type=theme.name,
                platform=platform,
                title_suggestion=title,
                effort_level=theme.effort_level,
                notes=notes,
                is_holiday=is_holiday,
                holiday_name=holiday_name
            ))

        return slots

    def _generate_title_suggestion(
        self,
        theme: ContentTheme,
        is_holiday: bool,
        holiday_name: Optional[str]
    ) -> str:
        """Generate a title suggestion for the content."""
        base_titles = {
            "Full Workout Video": [
                "Complete {muscle} Workout - No Equipment Needed",
                "30-Minute Full Body Blast",
                "The Ultimate {goal} Workout",
                "{duration}-Minute Killer {muscle} Session"
            ],
            "Quick Exercise Demo": [
                "How to Perfect Your {exercise}",
                "One Exercise You're Doing Wrong",
                "Try This {muscle} Move",
                "Quick Tip: {exercise} Form Check"
            ],
            "Workout Challenge": [
                "Can You Do This? 💪",
                "Challenge Accepted!",
                "Try This With Me",
                "Fitness Challenge Day {n}"
            ],
            "Meal Prep Tutorial": [
                "Meal Prep Sunday: {meals} Easy Meals",
                "How I Prep {days} Days of Healthy Food",
                "Budget Meal Prep Under ${budget}",
                "High Protein Meal Prep Guide"
            ],
            "Quick Recipe": [
                "{calories}-Calorie Snack in 2 Minutes",
                "Healthy {meal} Under 5 Minutes",
                "My Go-To Post-Workout Meal",
                "Easy High-Protein {food}"
            ],
            "Motivational Talk": [
                "What I Wish I Knew When I Started",
                "The Truth About {topic}",
                "Stop Doing This!",
                "Real Talk: {topic}"
            ],
            "Behind the Scenes": [
                "What My Day Actually Looks Like",
                "The Reality of Content Creation",
                "Not Everything You See is Real",
                "Raw & Unfiltered"
            ],
            "Fitness Tips": [
                "{n} Tips for Better {result}",
                "Mistakes Everyone Makes at the Gym",
                "How to Actually {goal}",
                "The Science Behind {topic}"
            ],
        }

        titles = base_titles.get(theme.name, [f"{theme.name} - {theme.description}"])
        title = random.choice(titles)

        # Add holiday theme if applicable
        if is_holiday and holiday_name:
            holiday_prefixes = [
                f"{holiday_name} Special: ",
                f"Happy {holiday_name}! ",
                f"{holiday_name} Edition: "
            ]
            title = random.choice(holiday_prefixes) + title

        return title

    def _calculate_stats(self, slots: list[ContentSlot]) -> dict:
        """Calculate calendar statistics."""
        content_slots = [s for s in slots if s.content_type != "REST DAY"]

        effort_counts = {"low": 0, "medium": 0, "high": 0}
        platform_counts = {}
        category_counts = {}

        for slot in content_slots:
            # Effort levels
            if slot.effort_level in effort_counts:
                effort_counts[slot.effort_level] += 1

            # Platforms
            platform_counts[slot.platform] = platform_counts.get(slot.platform, 0) + 1

        # Calculate workload score
        total_effort = sum(
            count * self.effort_weights.get(level, 1)
            for level, count in effort_counts.items()
        )
        avg_daily_effort = total_effort / max(len(slots), 1)

        return {
            "effort_distribution": effort_counts,
            "platform_distribution": platform_counts,
            "total_effort_points": total_effort,
            "average_daily_effort": round(avg_daily_effort, 2),
            "workload_assessment": self._assess_workload(avg_daily_effort)
        }

    def _assess_workload(self, avg_effort: float) -> str:
        """Assess overall workload level."""
        if avg_effort <= 2:
            return "Sustainable - Good balance for long-term consistency"
        elif avg_effort <= 3.5:
            return "Moderate - Manageable but monitor for burnout signs"
        elif avg_effort <= 5:
            return "Heavy - Consider reducing high-effort content"
        else:
            return "Unsustainable - High risk of burnout, reduce immediately"

    def _generate_recommendations(self, slots: list[ContentSlot], stats: dict) -> list[str]:
        """Generate recommendations based on the calendar."""
        recommendations = []

        # Check effort balance
        effort_dist = stats["effort_distribution"]
        high_percentage = effort_dist.get("high", 0) / max(sum(effort_dist.values()), 1)

        if high_percentage > 0.3:
            recommendations.append(
                "Consider reducing high-effort content. Currently {:.0%} of posts are high-effort. "
                "Aim for under 30% to prevent burnout.".format(high_percentage)
            )

        if high_percentage < 0.1:
            recommendations.append(
                "Your calendar is light on flagship content. Consider adding 1-2 high-effort "
                "pieces per week for better engagement and growth."
            )

        # Check platform distribution
        platform_dist = stats["platform_distribution"]
        if len(platform_dist) < 3:
            recommendations.append(
                "You're only posting to {} platform(s). Consider diversifying to reach "
                "wider audiences.".format(len(platform_dist))
            )

        # Check for consecutive high effort
        consecutive_high = 0
        max_consecutive = 0
        for slot in slots:
            if slot.effort_level == "high":
                consecutive_high += 1
                max_consecutive = max(max_consecutive, consecutive_high)
            else:
                consecutive_high = 0

        if max_consecutive >= 3:
            recommendations.append(
                "You have {} consecutive high-effort posts. Space these out with "
                "low-effort content to maintain energy.".format(max_consecutive)
            )

        # General recommendations
        recommendations.append(
            "Batch similar content types together to improve efficiency "
            "(e.g., film all workout videos in one session)."
        )

        recommendations.append(
            "Prepare evergreen content during high-energy weeks to use during "
            "low-energy periods or emergencies."
        )

        return recommendations

    def _slot_to_dict(self, slot: ContentSlot) -> dict:
        """Convert ContentSlot to dictionary."""
        return {
            "date": slot.date,
            "day_of_week": slot.day_of_week,
            "content_type": slot.content_type,
            "platform": slot.platform,
            "title_suggestion": slot.title_suggestion,
            "effort_level": slot.effort_level,
            "notes": slot.notes,
            "is_holiday": slot.is_holiday,
            "holiday_name": slot.holiday_name
        }

    def get_week_overview(self, calendar_result: dict, week_number: int = 1) -> dict:
        """
        Get overview for a specific week in the calendar.

        Args:
            calendar_result: Result from generate_calendar()
            week_number: Week number (1-based)

        Returns:
            Week-specific overview
        """
        all_slots = calendar_result["calendar"]
        start_idx = (week_number - 1) * 7
        end_idx = min(start_idx + 7, len(all_slots))

        week_slots = all_slots[start_idx:end_idx]

        effort_sum = sum(
            self.effort_weights.get(s["effort_level"], 0)
            for s in week_slots
        )

        return {
            "week_number": week_number,
            "slots": week_slots,
            "total_posts": len([s for s in week_slots if s["content_type"] != "REST DAY"]),
            "effort_score": effort_sum,
            "busiest_day": max(
                set(s["day_of_week"] for s in week_slots),
                key=lambda d: len([s for s in week_slots if s["day_of_week"] == d])
            ) if week_slots else None
        }


# Convenience function
def generate_content_calendar(
    days: int = 30,
    posts_per_day: int = 2,
    platforms: Optional[list[str]] = None,
    content_focus: Optional[list[str]] = None,
    rest_days: Optional[list[str]] = None
) -> dict:
    """
    Convenience function to generate a content calendar.

    Args:
        days: Number of days to plan
        posts_per_day: Target posts per day
        platforms: Platforms to post on
        content_focus: Categories to focus on
        rest_days: Days to skip (e.g., ["Sunday"])

    Returns:
        Complete content calendar
    """
    generator = ContentCalendarGenerator()
    return generator.generate_calendar(
        days=days,
        posts_per_day=posts_per_day,
        platforms=platforms,
        content_focus=content_focus,
        rest_days=rest_days
    )
