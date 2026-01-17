#!/usr/bin/env python3
"""
usage_tracker.py - Usage Tracking for Fitness Influencer MCP Pricing Tiers

WHAT: Tracks feature usage per user and enforces tier-based limits
WHY: Enable freemium model with metered usage for free tier users
INPUT: User email, feature name, reset period
OUTPUT: Usage status, limit checks, upgrade prompts

USAGE:
    from usage_tracker import UsageTracker

    tracker = UsageTracker()

    # Check if user can proceed
    can_proceed, message = tracker.check_limit("user@example.com", "ai_image")
    if not can_proceed:
        return message  # Contains upgrade prompt

    # Increment after successful operation
    tracker.increment_usage("user@example.com", "ai_image")

    # Get usage summary
    summary = tracker.get_usage_summary("user@example.com")

LIMIT PERIODS:
    - daily: Resets at midnight (comment categorization)
    - weekly: Resets on Monday (content calendars)
    - monthly: Resets on 1st of month (video jumpcuts, workout plans, AI images)

INTEGRATION:
    - Works with SubscriptionManager to get user's tier
    - Tier determines which limits apply (free users have limits, paid don't)
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Feature configuration with limits and periods
FEATURE_CONFIG: Dict[str, Dict[str, Any]] = {
    "video_jumpcut": {
        "display_name": "Video Jump-Cuts",
        "period": "monthly",
        "limits": {
            "free": 5,
            "starter": 25,
            "pro": float("inf"),
            "agency": float("inf"),
        },
        "upgrade_benefit": "25 jump-cut videos per month",
        "next_tier": "Starter ($19/mo)",
    },
    "comment_categorization": {
        "display_name": "Comment Categorization",
        "period": "daily",
        "limits": {
            "free": 10,
            "starter": float("inf"),
            "pro": float("inf"),
            "agency": float("inf"),
        },
        "upgrade_benefit": "unlimited comment categorization",
        "next_tier": "Starter ($19/mo)",
    },
    "workout_plan": {
        "display_name": "Workout Plans",
        "period": "monthly",
        "limits": {
            "free": 3,
            "starter": float("inf"),
            "pro": float("inf"),
            "agency": float("inf"),
        },
        "upgrade_benefit": "unlimited workout plans",
        "next_tier": "Starter ($19/mo)",
    },
    "content_calendar": {
        "display_name": "Content Calendars",
        "period": "weekly",
        "limits": {
            "free": 1,
            "starter": float("inf"),
            "pro": float("inf"),
            "agency": float("inf"),
        },
        "upgrade_benefit": "unlimited content calendars",
        "next_tier": "Starter ($19/mo)",
    },
    "ai_image": {
        "display_name": "AI Images",
        "period": "monthly",
        "limits": {
            "free": 2,
            "starter": 10,
            "pro": 20,
            "agency": 50,
        },
        "upgrade_benefit": "10 AI images per month",
        "next_tier": "Starter ($19/mo)",
    },
    "video_blueprint": {
        "display_name": "Video Blueprints",
        "period": "monthly",
        "limits": {
            "free": 5,
            "starter": 15,
            "pro": float("inf"),
            "agency": float("inf"),
        },
        "upgrade_benefit": "15 video blueprints per month",
        "next_tier": "Starter ($19/mo)",
    },
}


class UsageTracker:
    """
    Tracks feature usage per user and enforces tier-based limits.

    Usage data is stored in a JSON file at ~/.fitness_mcp_usage.json
    for simplicity and portability (no database required).
    """

    DEFAULT_STORAGE_PATH = "~/.fitness_mcp_usage.json"

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the usage tracker.

        Args:
            storage_path: Path to JSON storage file. Defaults to ~/.fitness_mcp_usage.json
        """
        if storage_path is None:
            storage_path = self.DEFAULT_STORAGE_PATH

        self.storage_path = Path(storage_path).expanduser()
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        """Create storage file if it doesn't exist."""
        if not self.storage_path.exists():
            self._save_data({})
            logger.info(f"Created usage storage at {self.storage_path}")

    def _load_data(self) -> Dict[str, Any]:
        """Load usage data from JSON file."""
        try:
            with open(self.storage_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Error loading usage data: {e}. Creating fresh storage.")
            return {}

    def _save_data(self, data: Dict[str, Any]) -> None:
        """Save usage data to JSON file."""
        try:
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except IOError as e:
            logger.error(f"Error saving usage data: {e}")
            raise

    def _get_current_period_key(self, period: str) -> str:
        """
        Get the current period key for tracking.

        Args:
            period: One of "daily", "weekly", "monthly"

        Returns:
            Period key string (e.g., "2026-01" for monthly, "2026-W03" for weekly)
        """
        now = datetime.now()

        if period == "daily":
            return now.strftime("%Y-%m-%d")
        elif period == "weekly":
            # ISO week format: 2026-W03
            return now.strftime("%Y-W%W")
        elif period == "monthly":
            return now.strftime("%Y-%m")
        else:
            logger.warning(f"Unknown period '{period}', defaulting to monthly")
            return now.strftime("%Y-%m")

    def _get_user_tier(self, user_email: str) -> str:
        """
        Get user's subscription tier.

        Integrates with SubscriptionManager if available,
        falls back to 'free' if not.

        Args:
            user_email: User's email address

        Returns:
            Tier string: "free", "starter", "pro", or "agency"
        """
        try:
            from .subscription_manager import SubscriptionManager
            manager = SubscriptionManager()
            return manager.get_tier(user_email)
        except ImportError:
            logger.warning("SubscriptionManager not available, assuming free tier")
            return "free"
        except Exception as e:
            logger.error(f"Error getting user tier: {e}")
            return "free"

    def check_limit(self, user_email: str, feature: str) -> Tuple[bool, str]:
        """
        Check if user can use a feature based on their tier and current usage.

        Args:
            user_email: User's email address
            feature: Feature name (e.g., "ai_image", "video_jumpcut")

        Returns:
            Tuple of (can_proceed: bool, message: str)
            - If can_proceed is True, message is empty or informational
            - If can_proceed is False, message contains limit info and upgrade prompt
        """
        # Validate feature
        if feature not in FEATURE_CONFIG:
            logger.warning(f"Unknown feature: {feature}")
            return True, ""  # Allow unknown features (no limit)

        config = FEATURE_CONFIG[feature]
        tier = self._get_user_tier(user_email)

        # Get limit for user's tier
        limit = config["limits"].get(tier, config["limits"]["free"])

        # Unlimited tiers can always proceed
        if limit == float("inf"):
            return True, ""

        # Get current usage
        period = config["period"]
        period_key = self._get_current_period_key(period)
        current_usage = self._get_usage(user_email, feature, period_key)

        # Check if within limit
        if current_usage < limit:
            remaining = int(limit - current_usage)
            return True, f"{remaining} {config['display_name'].lower()} remaining this {period}."

        # Limit reached - return upgrade message
        period_display = {
            "daily": "day",
            "weekly": "week",
            "monthly": "month"
        }.get(period, period)

        message = (
            f"You've reached your {tier} tier limit of {int(limit)} "
            f"{config['display_name'].lower()} this {period_display}.\n\n"
            f"Upgrade to {config['next_tier']} for {config['upgrade_benefit']}.\n"
            f"https://marceausolutions.com/fitness-pro"
        )

        return False, message

    def _get_usage(self, user_email: str, feature: str, period_key: str) -> int:
        """
        Get current usage count for a user/feature/period.

        Args:
            user_email: User's email address
            feature: Feature name
            period_key: Period key (e.g., "2026-01")

        Returns:
            Current usage count (0 if no usage recorded)
        """
        data = self._load_data()

        user_data = data.get(user_email, {})
        feature_data = user_data.get(feature, {})

        return feature_data.get(period_key, 0)

    def increment_usage(self, user_email: str, feature: str, count: int = 1) -> int:
        """
        Increment usage counter for a feature.

        Call this AFTER successfully completing the feature operation.

        Args:
            user_email: User's email address
            feature: Feature name
            count: Amount to increment (default 1)

        Returns:
            New usage count
        """
        if feature not in FEATURE_CONFIG:
            logger.warning(f"Unknown feature: {feature}, still tracking")

        config = FEATURE_CONFIG.get(feature, {"period": "monthly"})
        period = config.get("period", "monthly")
        period_key = self._get_current_period_key(period)

        data = self._load_data()

        # Initialize nested structure if needed
        if user_email not in data:
            data[user_email] = {}
        if feature not in data[user_email]:
            data[user_email][feature] = {}

        # Increment counter
        current = data[user_email][feature].get(period_key, 0)
        new_count = current + count
        data[user_email][feature][period_key] = new_count

        # Update last_used timestamp
        data[user_email][f"_last_used_{feature}"] = datetime.now().isoformat()

        self._save_data(data)

        logger.info(f"Usage incremented: {user_email}/{feature}/{period_key} = {new_count}")

        return new_count

    def get_usage_summary(self, user_email: str) -> Dict[str, Any]:
        """
        Get complete usage summary for a user.

        Args:
            user_email: User's email address

        Returns:
            Dict containing:
            - tier: User's subscription tier
            - features: Dict of feature usage with limits and remaining
            - total_operations: Total operations this month
            - upgrade_url: URL to upgrade
        """
        tier = self._get_user_tier(user_email)
        data = self._load_data()
        user_data = data.get(user_email, {})

        features_summary = {}
        total_operations = 0

        for feature, config in FEATURE_CONFIG.items():
            period = config["period"]
            period_key = self._get_current_period_key(period)

            current_usage = self._get_usage(user_email, feature, period_key)
            limit = config["limits"].get(tier, config["limits"]["free"])

            total_operations += current_usage

            features_summary[feature] = {
                "display_name": config["display_name"],
                "period": period,
                "period_key": period_key,
                "used": current_usage,
                "limit": int(limit) if limit != float("inf") else "unlimited",
                "remaining": "unlimited" if limit == float("inf") else max(0, int(limit - current_usage)),
                "at_limit": False if limit == float("inf") else current_usage >= limit,
            }

        return {
            "user_email": user_email,
            "tier": tier,
            "tier_display": tier.capitalize(),
            "features": features_summary,
            "total_operations_this_month": total_operations,
            "upgrade_url": "https://marceausolutions.com/fitness-pro",
            "generated_at": datetime.now().isoformat(),
        }

    def reset_usage(self, user_email: str, period: str, feature: Optional[str] = None) -> bool:
        """
        Reset usage counters for a user.

        This is typically called automatically when a new period begins,
        but can be used manually for admin purposes.

        Args:
            user_email: User's email address
            period: Period type to reset ("daily", "weekly", "monthly", or "all")
            feature: Specific feature to reset (None = all features)

        Returns:
            True if reset was performed
        """
        data = self._load_data()

        if user_email not in data:
            logger.info(f"No usage data for {user_email}")
            return False

        user_data = data[user_email]

        # Determine which period key to reset
        if period == "all":
            # Reset all periods
            period_key = None
        else:
            period_key = self._get_current_period_key(period)

        features_to_reset = [feature] if feature else list(FEATURE_CONFIG.keys())

        for feat in features_to_reset:
            if feat not in user_data:
                continue

            if period_key:
                # Reset specific period
                if period_key in user_data[feat]:
                    del user_data[feat][period_key]
                    logger.info(f"Reset {user_email}/{feat}/{period_key}")
            else:
                # Reset all periods for this feature
                user_data[feat] = {}
                logger.info(f"Reset all usage for {user_email}/{feat}")

        self._save_data(data)
        return True

    def cleanup_old_periods(self, days_to_keep: int = 90) -> int:
        """
        Remove old period data to keep storage file size manageable.

        Args:
            days_to_keep: Number of days of history to retain

        Returns:
            Number of old entries removed
        """
        data = self._load_data()
        cutoff = datetime.now() - timedelta(days=days_to_keep)
        removed_count = 0

        for user_email in data:
            user_data = data[user_email]

            for feature in list(user_data.keys()):
                if feature.startswith("_"):  # Skip metadata fields
                    continue

                if not isinstance(user_data[feature], dict):
                    continue

                for period_key in list(user_data[feature].keys()):
                    try:
                        # Parse period key to date
                        if "-W" in period_key:
                            # Weekly format: 2026-W03
                            year, week = period_key.split("-W")
                            period_date = datetime.strptime(f"{year}-W{week}-1", "%Y-W%W-%w")
                        elif period_key.count("-") == 2:
                            # Daily format: 2026-01-16
                            period_date = datetime.strptime(period_key, "%Y-%m-%d")
                        else:
                            # Monthly format: 2026-01
                            period_date = datetime.strptime(period_key, "%Y-%m")

                        if period_date < cutoff:
                            del user_data[feature][period_key]
                            removed_count += 1

                    except ValueError:
                        # Can't parse period key, skip
                        continue

        if removed_count > 0:
            self._save_data(data)
            logger.info(f"Cleaned up {removed_count} old period entries")

        return removed_count

    def get_all_users_summary(self) -> Dict[str, Any]:
        """
        Get usage summary for all users (admin view).

        Returns:
            Dict with usage statistics across all users
        """
        data = self._load_data()

        total_users = len([k for k in data.keys() if not k.startswith("_")])

        # Count users by tier
        tier_counts = {"free": 0, "starter": 0, "pro": 0, "agency": 0}
        total_operations = 0

        for user_email in data:
            if user_email.startswith("_"):
                continue

            tier = self._get_user_tier(user_email)
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

            # Count operations
            for feature in FEATURE_CONFIG:
                if feature in data[user_email]:
                    for period_key, count in data[user_email][feature].items():
                        if isinstance(count, int):
                            total_operations += count

        return {
            "total_users": total_users,
            "users_by_tier": tier_counts,
            "total_operations": total_operations,
            "storage_path": str(self.storage_path),
            "generated_at": datetime.now().isoformat(),
        }


# CLI interface for testing and admin
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Usage Tracker for Fitness Influencer MCP")
    parser.add_argument("--check", nargs=2, metavar=("EMAIL", "FEATURE"),
                        help="Check if user can use feature")
    parser.add_argument("--increment", nargs=2, metavar=("EMAIL", "FEATURE"),
                        help="Increment usage for user/feature")
    parser.add_argument("--summary", metavar="EMAIL", help="Get usage summary for user")
    parser.add_argument("--all-users", action="store_true", help="Get all users summary")
    parser.add_argument("--reset", nargs=3, metavar=("EMAIL", "PERIOD", "FEATURE"),
                        help="Reset usage (feature can be 'all')")
    parser.add_argument("--cleanup", type=int, metavar="DAYS", default=90,
                        help="Cleanup old period data (default: 90 days)")

    args = parser.parse_args()

    tracker = UsageTracker()

    if args.check:
        email, feature = args.check
        can_proceed, message = tracker.check_limit(email, feature)
        print(f"Can proceed: {can_proceed}")
        if message:
            print(f"Message: {message}")

    elif args.increment:
        email, feature = args.increment
        new_count = tracker.increment_usage(email, feature)
        print(f"New count: {new_count}")

    elif args.summary:
        summary = tracker.get_usage_summary(args.summary)
        print(json.dumps(summary, indent=2))

    elif args.all_users:
        summary = tracker.get_all_users_summary()
        print(json.dumps(summary, indent=2))

    elif args.reset:
        email, period, feature = args.reset
        feature = None if feature == "all" else feature
        success = tracker.reset_usage(email, period, feature)
        print(f"Reset: {'success' if success else 'no data to reset'}")

    elif args.cleanup:
        removed = tracker.cleanup_old_periods(args.cleanup)
        print(f"Removed {removed} old entries")

    else:
        parser.print_help()
