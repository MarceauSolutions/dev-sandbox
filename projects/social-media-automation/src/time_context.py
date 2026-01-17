#!/usr/bin/env python3
"""
time_context.py - Time awareness utility for social media automation

Ensures all scheduling decisions are made with correct time context.
Validates schedules against content strategy rules.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo


class TimeContext:
    """
    Provides time-aware context for scheduling decisions.
    All times are handled in the configured timezone (default: America/New_York).
    """

    STRATEGY_FILE = Path(__file__).parent.parent / "templates" / "content_strategy.json"
    DEFAULT_TIMEZONE = "America/New_York"

    def __init__(self, timezone: str = None):
        self.timezone = ZoneInfo(timezone or self.DEFAULT_TIMEZONE)
        self.strategy = self._load_strategy()

    def _load_strategy(self) -> Dict:
        """Load content strategy configuration."""
        if self.STRATEGY_FILE.exists():
            with open(self.STRATEGY_FILE) as f:
                return json.load(f)
        return {}

    @property
    def now(self) -> datetime:
        """Get current time in configured timezone."""
        return datetime.now(self.timezone)

    @property
    def today(self) -> str:
        """Get today's date as YYYY-MM-DD."""
        return self.now.strftime("%Y-%m-%d")

    @property
    def day_of_week(self) -> str:
        """Get current day of week (lowercase)."""
        return self.now.strftime("%A").lower()

    @property
    def is_weekend(self) -> bool:
        """Check if today is weekend (Saturday or Sunday)."""
        return self.now.weekday() >= 5

    @property
    def hour(self) -> int:
        """Get current hour (0-23)."""
        return self.now.hour

    def get_context_summary(self) -> Dict:
        """
        Get a summary of current time context for logging/display.
        This should be called before any scheduling decisions.
        """
        now = self.now
        return {
            "current_time": now.isoformat(),
            "date": self.today,
            "day_of_week": self.day_of_week.capitalize(),
            "hour": self.hour,
            "is_weekend": self.is_weekend,
            "timezone": str(self.timezone),
            "optimal_posting_hours": self._get_todays_posting_hours(),
            "todays_theme": self._get_todays_theme(),
            "todays_hashtags": self._get_todays_hashtags()
        }

    def _get_todays_posting_hours(self) -> List[str]:
        """Get optimal posting hours for today based on strategy."""
        schedule = self.strategy.get("posting_schedule", {})
        if self.is_weekend:
            weekend = schedule.get("weekend", {})
            return [weekend.get("primary", "09:00")]
        else:
            weekday = schedule.get("weekday", {})
            return [
                weekday.get("primary", "09:00"),
                weekday.get("secondary", "12:00"),
                weekday.get("tertiary", "15:00"),
                weekday.get("evening", "18:00")
            ]

    def _get_todays_theme(self) -> Optional[str]:
        """Get content theme for today based on strategy."""
        content_mix = self.strategy.get("daily_content_mix", {})
        day_config = content_mix.get(self.day_of_week, {})
        return day_config.get("theme")

    def _get_todays_hashtags(self) -> List[str]:
        """Get recommended hashtags for today."""
        content_mix = self.strategy.get("daily_content_mix", {})
        day_config = content_mix.get(self.day_of_week, {})
        return day_config.get("hashtags", [])

    def get_next_optimal_slot(self) -> Tuple[datetime, str]:
        """
        Get the next optimal posting time slot.

        Returns:
            Tuple of (datetime, reason)
        """
        now = self.now
        today_hours = self._get_todays_posting_hours()

        # Check if any slot is still available today
        for time_str in today_hours:
            hour, minute = map(int, time_str.split(":"))
            slot_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

            if slot_time > now:
                return (slot_time, f"Today's {time_str} slot ({self.day_of_week.capitalize()})")

        # No slots left today, find next available day
        days_ahead = 1
        while days_ahead <= 7:
            next_date = now + timedelta(days=days_ahead)
            next_day = next_date.strftime("%A").lower()
            next_is_weekend = next_date.weekday() >= 5

            # Sunday is optional per strategy
            if next_day == "sunday":
                content_mix = self.strategy.get("daily_content_mix", {})
                sunday_config = content_mix.get("sunday", {})
                if sunday_config.get("post_frequency") == "optional":
                    days_ahead += 1
                    continue

            # Get first slot for that day
            schedule = self.strategy.get("posting_schedule", {})
            if next_is_weekend:
                first_slot = schedule.get("weekend", {}).get("primary", "09:00")
            else:
                first_slot = schedule.get("weekday", {}).get("primary", "09:00")

            hour, minute = map(int, first_slot.split(":"))
            slot_time = next_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

            return (slot_time, f"{next_day.capitalize()} {first_slot} slot")

        # Fallback: tomorrow 9 AM
        tomorrow = now + timedelta(days=1)
        return (tomorrow.replace(hour=9, minute=0, second=0, microsecond=0), "Tomorrow 9 AM (fallback)")

    def validate_schedule(self, scheduled_time: datetime, count_for_day: int = 1) -> Dict:
        """
        Validate a scheduled time against content strategy rules.

        Args:
            scheduled_time: The proposed posting time
            count_for_day: How many posts are already scheduled for that day

        Returns:
            Dict with 'valid' bool and 'warnings' list
        """
        warnings = []

        # Check timezone
        if scheduled_time.tzinfo is None:
            scheduled_time = scheduled_time.replace(tzinfo=self.timezone)

        day_of_week = scheduled_time.strftime("%A").lower()
        is_weekend = scheduled_time.weekday() >= 5
        hour = scheduled_time.hour

        # Rule 1: Weekend should have max 1 post
        if is_weekend and count_for_day > 1:
            warnings.append(f"Weekend ({day_of_week}) should have max 1 post per day, not {count_for_day}")

        # Rule 2: Sunday is optional
        if day_of_week == "sunday":
            warnings.append("Sunday is marked as optional rest day in strategy")

        # Rule 3: Check optimal hours
        schedule = self.strategy.get("posting_schedule", {})
        if is_weekend:
            optimal_hours = [int(schedule.get("weekend", {}).get("primary", "09:00").split(":")[0])]
        else:
            weekday = schedule.get("weekday", {})
            optimal_hours = [
                int(weekday.get("primary", "09:00").split(":")[0]),
                int(weekday.get("secondary", "12:00").split(":")[0]),
                int(weekday.get("tertiary", "15:00").split(":")[0]),
                int(weekday.get("evening", "18:00").split(":")[0])
            ]

        if hour not in optimal_hours:
            warnings.append(f"Hour {hour}:00 is not an optimal posting time. Optimal: {optimal_hours}")

        # Rule 4: Past time check
        if scheduled_time < self.now:
            warnings.append(f"Scheduled time {scheduled_time} is in the past")

        return {
            "valid": len(warnings) == 0,
            "warnings": warnings,
            "scheduled_time": scheduled_time.isoformat(),
            "day_of_week": day_of_week.capitalize(),
            "is_weekend": is_weekend
        }

    def get_week_schedule_template(self, start_date: datetime = None) -> List[Dict]:
        """
        Generate a week's schedule template based on content strategy.

        Returns:
            List of day configurations with optimal slots and themes
        """
        if start_date is None:
            start_date = self.now

        week = []
        for i in range(7):
            day_date = start_date + timedelta(days=i)
            day_name = day_date.strftime("%A").lower()
            is_weekend = day_date.weekday() >= 5

            content_mix = self.strategy.get("daily_content_mix", {})
            day_config = content_mix.get(day_name, {})

            schedule = self.strategy.get("posting_schedule", {})
            if is_weekend:
                slots = [schedule.get("weekend", {}).get("primary", "09:00")]
            else:
                weekday = schedule.get("weekday", {})
                slots = [
                    weekday.get("primary", "09:00"),
                    weekday.get("secondary", "12:00"),
                    weekday.get("tertiary", "15:00"),
                    weekday.get("evening", "18:00")
                ]

            week.append({
                "date": day_date.strftime("%Y-%m-%d"),
                "day": day_name.capitalize(),
                "is_weekend": is_weekend,
                "theme": day_config.get("theme", "general"),
                "content_types": day_config.get("content_types", []),
                "hashtags": day_config.get("hashtags", []),
                "optimal_slots": slots,
                "max_posts": 1 if is_weekend else 4,
                "optional": day_config.get("post_frequency") == "optional"
            })

        return week


def print_context():
    """CLI utility to print current time context."""
    ctx = TimeContext()
    summary = ctx.get_context_summary()

    print("\n" + "=" * 60)
    print("CURRENT TIME CONTEXT")
    print("=" * 60)
    print(f"  Time:      {summary['current_time']}")
    print(f"  Day:       {summary['day_of_week']}")
    print(f"  Weekend:   {'Yes' if summary['is_weekend'] else 'No'}")
    print(f"  Timezone:  {summary['timezone']}")
    print(f"  Theme:     {summary['todays_theme'] or 'None'}")
    print(f"  Hashtags:  {', '.join(summary['todays_hashtags']) if summary['todays_hashtags'] else 'None'}")
    print(f"  Optimal:   {', '.join(summary['optimal_posting_hours'])}")

    next_slot, reason = ctx.get_next_optimal_slot()
    print(f"\n  Next slot: {next_slot.strftime('%Y-%m-%d %H:%M')} ({reason})")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    print_context()
