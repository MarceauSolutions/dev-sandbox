#!/usr/bin/env python3
"""
subscription_manager.py - Subscription Management for Fitness Influencer MCP

WHAT: Manages user subscriptions with tiered pricing (free/starter/pro/agency)
WHY: Enable paid features while maintaining a generous free tier
INPUT: User email, subscription tier, Stripe customer ID
OUTPUT: Tier validation, usage limits, subscriber management

PRICING TIERS:
    - FREE: Basic access with usage limits
    - STARTER ($19/mo): Enhanced limits, unlimited comments
    - PRO ($49/mo): Most features unlimited
    - AGENCY ($149/mo): Full access + multi-client + API

STORAGE: Local JSON file at ~/.fitness_mcp_pro_users.json
         (Phase 1: Manual Stripe integration)

USAGE:
    from subscription_manager import SubscriptionManager

    manager = SubscriptionManager()

    # Check user's tier
    tier = manager.get_tier("user@example.com")

    # Check if paid user
    if manager.is_paid("user@example.com"):
        # Unlock premium features
        pass

    # Add new subscriber (after Stripe webhook)
    manager.add_subscriber("user@example.com", "pro", "cus_xxx123")

    # Get limits for a tier
    limits = manager.get_tier_limits("starter")
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Configure logging
logger = logging.getLogger(__name__)


class SubscriptionManager:
    """Manages user subscriptions and tier-based access control.

    Implements a four-tier pricing model with local JSON storage.
    Designed for Phase 1 (Local JSON + Manual Stripe) integration.

    Attributes:
        TIERS: Dict of tier names to their monthly prices
        TIER_LIMITS: Dict of tier names to their usage limits
    """

    # Pricing tiers with monthly costs
    TIERS: Dict[str, Dict[str, Any]] = {
        "free": {
            "price": 0,
            "display_name": "Free",
            "description": "Basic access with usage limits"
        },
        "starter": {
            "price": 19,
            "display_name": "Starter",
            "description": "Enhanced limits for growing creators"
        },
        "pro": {
            "price": 49,
            "display_name": "Pro",
            "description": "Full access for serious creators"
        },
        "agency": {
            "price": 149,
            "display_name": "Agency",
            "description": "Multi-client access with API"
        }
    }

    # Usage limits per tier
    TIER_LIMITS: Dict[str, Dict[str, Any]] = {
        "free": {
            "video_jumpcuts": 5,           # per month
            "comments": 10,                 # per day
            "workout_plans": 3,             # per month
            "calendars": 1,                 # per week
            "ai_images": 2,                 # per month
            "video_blueprints": 3,          # per month
            "multi_client": False,
            "api_access": False,
            "priority_support": False,
            "white_label": False
        },
        "starter": {
            "video_jumpcuts": 25,           # per month
            "comments": -1,                 # unlimited (-1)
            "workout_plans": -1,            # unlimited
            "calendars": -1,                # unlimited
            "ai_images": 10,                # per month
            "video_blueprints": 15,         # per month
            "multi_client": False,
            "api_access": False,
            "priority_support": False,
            "white_label": False
        },
        "pro": {
            "video_jumpcuts": -1,           # unlimited
            "comments": -1,                 # unlimited
            "workout_plans": -1,            # unlimited
            "calendars": -1,                # unlimited
            "ai_images": 20,                # per month (still capped due to cost)
            "video_blueprints": -1,         # unlimited
            "multi_client": False,
            "api_access": False,
            "priority_support": True,
            "white_label": False
        },
        "agency": {
            "video_jumpcuts": -1,           # unlimited
            "comments": -1,                 # unlimited
            "workout_plans": -1,            # unlimited
            "calendars": -1,                # unlimited
            "ai_images": 50,                # per month (higher cap for agencies)
            "video_blueprints": -1,         # unlimited
            "multi_client": True,           # manage multiple clients
            "api_access": True,             # direct API access
            "priority_support": True,
            "white_label": True             # remove branding
        }
    }

    # Default storage path
    DEFAULT_STORAGE_PATH = Path.home() / ".fitness_mcp_pro_users.json"

    def __init__(self, storage_path: Optional[str] = None):
        """Initialize the subscription manager.

        Args:
            storage_path: Path to JSON storage file. Defaults to ~/.fitness_mcp_pro_users.json
        """
        self.storage_path = Path(storage_path) if storage_path else self.DEFAULT_STORAGE_PATH
        self._ensure_storage_exists()
        logger.info(f"SubscriptionManager initialized with storage: {self.storage_path}")

    def _ensure_storage_exists(self) -> None:
        """Ensure the storage file exists with valid JSON structure."""
        if not self.storage_path.exists():
            self._write_storage({"subscribers": {}, "metadata": {"created": datetime.now().isoformat()}})
            logger.info(f"Created new storage file: {self.storage_path}")

    def _read_storage(self) -> Dict[str, Any]:
        """Read the storage file.

        Returns:
            Dict containing subscriber data

        Raises:
            json.JSONDecodeError: If file contains invalid JSON
        """
        try:
            with open(self.storage_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in storage file: {e}")
            # Backup corrupted file and create new one
            backup_path = self.storage_path.with_suffix(".json.bak")
            self.storage_path.rename(backup_path)
            logger.warning(f"Backed up corrupted file to {backup_path}")
            self._ensure_storage_exists()
            return self._read_storage()
        except FileNotFoundError:
            self._ensure_storage_exists()
            return self._read_storage()

    def _write_storage(self, data: Dict[str, Any]) -> None:
        """Write data to the storage file.

        Args:
            data: Dict to serialize and write
        """
        # Update last modified timestamp
        data["metadata"] = data.get("metadata", {})
        data["metadata"]["last_modified"] = datetime.now().isoformat()

        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)
        logger.debug(f"Storage updated: {len(data.get('subscribers', {}))} subscribers")

    def get_tier(self, user_email: str) -> str:
        """Get the subscription tier for a user.

        Args:
            user_email: User's email address (case-insensitive)

        Returns:
            Tier name: 'free', 'starter', 'pro', or 'agency'
        """
        email_lower = user_email.lower().strip()
        storage = self._read_storage()
        subscribers = storage.get("subscribers", {})

        if email_lower in subscribers:
            subscriber = subscribers[email_lower]
            # Check if subscription is still active
            if subscriber.get("status") == "active":
                return subscriber.get("tier", "free")

        return "free"

    def is_paid(self, user_email: str) -> bool:
        """Check if a user is on any paid tier.

        Args:
            user_email: User's email address

        Returns:
            True if user is on starter, pro, or agency tier
        """
        tier = self.get_tier(user_email)
        return tier in ["starter", "pro", "agency"]

    def add_subscriber(
        self,
        email: str,
        tier: str,
        stripe_customer_id: str,
        stripe_subscription_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add or update a subscriber.

        Args:
            email: User's email address
            tier: Subscription tier ('starter', 'pro', 'agency')
            stripe_customer_id: Stripe customer ID (e.g., 'cus_xxx')
            stripe_subscription_id: Optional Stripe subscription ID
            metadata: Optional additional metadata

        Returns:
            Dict with subscriber info

        Raises:
            ValueError: If tier is invalid
        """
        # Validate tier
        tier_lower = tier.lower()
        if tier_lower not in self.TIERS:
            raise ValueError(f"Invalid tier: {tier}. Valid tiers: {list(self.TIERS.keys())}")

        if tier_lower == "free":
            raise ValueError("Cannot add subscriber with 'free' tier. Use remove_subscriber instead.")

        email_lower = email.lower().strip()
        storage = self._read_storage()

        now = datetime.now().isoformat()

        subscriber_data = {
            "email": email_lower,
            "tier": tier_lower,
            "stripe_customer_id": stripe_customer_id,
            "stripe_subscription_id": stripe_subscription_id,
            "status": "active",
            "created_at": storage.get("subscribers", {}).get(email_lower, {}).get("created_at", now),
            "updated_at": now,
            "metadata": metadata or {}
        }

        storage.setdefault("subscribers", {})[email_lower] = subscriber_data
        self._write_storage(storage)

        logger.info(f"Added/updated subscriber: {email_lower} -> {tier_lower}")
        return subscriber_data

    def remove_subscriber(self, email: str, reason: Optional[str] = None) -> bool:
        """Remove a subscriber (for cancellations).

        Args:
            email: User's email address
            reason: Optional cancellation reason

        Returns:
            True if subscriber was found and removed, False if not found
        """
        email_lower = email.lower().strip()
        storage = self._read_storage()

        if email_lower not in storage.get("subscribers", {}):
            logger.warning(f"Subscriber not found for removal: {email_lower}")
            return False

        # Mark as cancelled rather than deleting (for records)
        subscriber = storage["subscribers"][email_lower]
        subscriber["status"] = "cancelled"
        subscriber["cancelled_at"] = datetime.now().isoformat()
        subscriber["cancellation_reason"] = reason

        self._write_storage(storage)
        logger.info(f"Removed subscriber: {email_lower} (reason: {reason})")
        return True

    def list_all_subscribers(self, include_cancelled: bool = False) -> List[Dict[str, Any]]:
        """List all subscribers.

        Args:
            include_cancelled: Whether to include cancelled subscriptions

        Returns:
            List of subscriber dicts with email, tier, status, etc.
        """
        storage = self._read_storage()
        subscribers = storage.get("subscribers", {})

        result = []
        for email, data in subscribers.items():
            if not include_cancelled and data.get("status") != "active":
                continue
            result.append({
                "email": email,
                "tier": data.get("tier"),
                "tier_display": self.TIERS.get(data.get("tier"), {}).get("display_name", "Unknown"),
                "price": self.TIERS.get(data.get("tier"), {}).get("price", 0),
                "status": data.get("status"),
                "stripe_customer_id": data.get("stripe_customer_id"),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at")
            })

        # Sort by created_at descending (newest first)
        result.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return result

    def get_tier_limits(self, tier: str) -> Dict[str, Any]:
        """Get the usage limits for a tier.

        Args:
            tier: Tier name ('free', 'starter', 'pro', 'agency')

        Returns:
            Dict of limits with -1 indicating unlimited

        Raises:
            ValueError: If tier is invalid
        """
        tier_lower = tier.lower()
        if tier_lower not in self.TIER_LIMITS:
            raise ValueError(f"Invalid tier: {tier}. Valid tiers: {list(self.TIER_LIMITS.keys())}")

        limits = self.TIER_LIMITS[tier_lower].copy()

        # Add tier info
        limits["tier"] = tier_lower
        limits["tier_display"] = self.TIERS[tier_lower]["display_name"]
        limits["price"] = self.TIERS[tier_lower]["price"]

        return limits

    def get_user_limits(self, user_email: str) -> Dict[str, Any]:
        """Get the usage limits for a specific user based on their tier.

        Args:
            user_email: User's email address

        Returns:
            Dict of limits for the user's current tier
        """
        tier = self.get_tier(user_email)
        return self.get_tier_limits(tier)

    def check_feature_access(self, user_email: str, feature: str) -> Dict[str, Any]:
        """Check if a user has access to a specific feature.

        Args:
            user_email: User's email address
            feature: Feature name (e.g., 'multi_client', 'api_access')

        Returns:
            Dict with 'allowed' (bool), 'limit' (int or None), 'tier_required' (str)
        """
        tier = self.get_tier(user_email)
        limits = self.TIER_LIMITS.get(tier, self.TIER_LIMITS["free"])

        if feature not in limits:
            return {
                "allowed": False,
                "limit": None,
                "tier_required": None,
                "error": f"Unknown feature: {feature}"
            }

        value = limits[feature]

        # Boolean features
        if isinstance(value, bool):
            if value:
                return {"allowed": True, "limit": None, "tier_required": None}
            else:
                # Find minimum tier that has this feature
                for check_tier in ["starter", "pro", "agency"]:
                    if self.TIER_LIMITS[check_tier].get(feature):
                        return {
                            "allowed": False,
                            "limit": None,
                            "tier_required": check_tier,
                            "upgrade_message": f"Upgrade to {self.TIERS[check_tier]['display_name']} (${self.TIERS[check_tier]['price']}/mo) to unlock {feature.replace('_', ' ')}"
                        }
                return {"allowed": False, "limit": None, "tier_required": "agency"}

        # Numeric limits
        if value == -1:  # Unlimited
            return {"allowed": True, "limit": None, "tier_required": None, "unlimited": True}
        elif value > 0:
            return {"allowed": True, "limit": value, "tier_required": None, "unlimited": False}
        else:  # Zero or disabled
            # Find minimum tier with this feature
            for check_tier in ["starter", "pro", "agency"]:
                check_limit = self.TIER_LIMITS[check_tier].get(feature, 0)
                if check_limit != 0:
                    return {
                        "allowed": False,
                        "limit": 0,
                        "tier_required": check_tier,
                        "upgrade_message": f"Upgrade to {self.TIERS[check_tier]['display_name']} to access {feature.replace('_', ' ')}"
                    }
            return {"allowed": False, "limit": 0, "tier_required": None}

    def update_tier(self, email: str, new_tier: str) -> Dict[str, Any]:
        """Update a subscriber's tier (for upgrades/downgrades).

        Args:
            email: User's email address
            new_tier: New tier name

        Returns:
            Updated subscriber data

        Raises:
            ValueError: If new_tier is invalid or user not found
        """
        email_lower = email.lower().strip()
        new_tier_lower = new_tier.lower()

        if new_tier_lower not in self.TIERS:
            raise ValueError(f"Invalid tier: {new_tier}. Valid: {list(self.TIERS.keys())}")

        storage = self._read_storage()

        if email_lower not in storage.get("subscribers", {}):
            raise ValueError(f"Subscriber not found: {email_lower}")

        old_tier = storage["subscribers"][email_lower].get("tier")
        storage["subscribers"][email_lower]["tier"] = new_tier_lower
        storage["subscribers"][email_lower]["updated_at"] = datetime.now().isoformat()
        storage["subscribers"][email_lower]["tier_history"] = storage["subscribers"][email_lower].get("tier_history", [])
        storage["subscribers"][email_lower]["tier_history"].append({
            "from": old_tier,
            "to": new_tier_lower,
            "changed_at": datetime.now().isoformat()
        })

        self._write_storage(storage)
        logger.info(f"Updated tier for {email_lower}: {old_tier} -> {new_tier_lower}")

        return storage["subscribers"][email_lower]

    def get_subscriber_stats(self) -> Dict[str, Any]:
        """Get aggregate statistics about subscribers.

        Returns:
            Dict with counts by tier, MRR, etc.
        """
        subscribers = self.list_all_subscribers(include_cancelled=False)

        by_tier = {"free": 0, "starter": 0, "pro": 0, "agency": 0}
        mrr = 0

        for sub in subscribers:
            tier = sub.get("tier", "free")
            by_tier[tier] = by_tier.get(tier, 0) + 1
            mrr += self.TIERS.get(tier, {}).get("price", 0)

        return {
            "total_active": len(subscribers),
            "by_tier": by_tier,
            "mrr": mrr,
            "arr": mrr * 12,
            "average_revenue_per_user": round(mrr / len(subscribers), 2) if subscribers else 0
        }


# CLI interface for testing and manual management
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fitness Influencer MCP Subscription Manager")
    parser.add_argument("--add", nargs=3, metavar=("EMAIL", "TIER", "STRIPE_ID"),
                        help="Add subscriber: email tier stripe_customer_id")
    parser.add_argument("--remove", metavar="EMAIL", help="Remove subscriber by email")
    parser.add_argument("--check", metavar="EMAIL", help="Check subscriber tier")
    parser.add_argument("--list", action="store_true", help="List all subscribers")
    parser.add_argument("--stats", action="store_true", help="Show subscriber statistics")
    parser.add_argument("--limits", metavar="TIER", help="Show limits for a tier")
    parser.add_argument("--upgrade", nargs=2, metavar=("EMAIL", "NEW_TIER"),
                        help="Upgrade/downgrade subscriber")

    args = parser.parse_args()

    manager = SubscriptionManager()

    if args.add:
        email, tier, stripe_id = args.add
        try:
            result = manager.add_subscriber(email, tier, stripe_id)
            print(f"Added subscriber: {result['email']} -> {result['tier']}")
        except ValueError as e:
            print(f"Error: {e}")

    if args.remove:
        if manager.remove_subscriber(args.remove):
            print(f"Removed subscriber: {args.remove}")
        else:
            print(f"Subscriber not found: {args.remove}")

    if args.check:
        tier = manager.get_tier(args.check)
        is_paid = manager.is_paid(args.check)
        limits = manager.get_user_limits(args.check)
        print(f"Email: {args.check}")
        print(f"Tier: {tier} ({'PAID' if is_paid else 'FREE'})")
        print(f"Price: ${manager.TIERS[tier]['price']}/month")
        print(f"Limits:")
        for key, value in limits.items():
            if key not in ["tier", "tier_display", "price"]:
                display_val = "unlimited" if value == -1 else value
                print(f"  {key}: {display_val}")

    if args.list:
        subscribers = manager.list_all_subscribers()
        if not subscribers:
            print("No active subscribers")
        else:
            print(f"{'Email':<40} {'Tier':<10} {'Price':<8} {'Status':<10}")
            print("-" * 70)
            for sub in subscribers:
                print(f"{sub['email']:<40} {sub['tier']:<10} ${sub['price']:<7} {sub['status']:<10}")

    if args.stats:
        stats = manager.get_subscriber_stats()
        print("\n=== SUBSCRIBER STATISTICS ===")
        print(f"Total Active: {stats['total_active']}")
        print(f"\nBy Tier:")
        for tier, count in stats['by_tier'].items():
            price = manager.TIERS[tier]['price']
            print(f"  {tier.capitalize()}: {count} (${price}/mo)")
        print(f"\nMRR: ${stats['mrr']:.2f}")
        print(f"ARR: ${stats['arr']:.2f}")
        print(f"ARPU: ${stats['average_revenue_per_user']:.2f}")

    if args.limits:
        try:
            limits = manager.get_tier_limits(args.limits)
            print(f"\n=== {limits['tier_display'].upper()} TIER (${limits['price']}/mo) ===")
            for key, value in limits.items():
                if key not in ["tier", "tier_display", "price"]:
                    display_val = "unlimited" if value == -1 else ("Yes" if value is True else ("No" if value is False else value))
                    unit = ""
                    if key in ["video_jumpcuts", "workout_plans", "ai_images", "video_blueprints"]:
                        unit = "/month"
                    elif key == "comments":
                        unit = "/day"
                    elif key == "calendars":
                        unit = "/week"
                    print(f"  {key.replace('_', ' ').title()}: {display_val}{unit}")
        except ValueError as e:
            print(f"Error: {e}")

    if args.upgrade:
        email, new_tier = args.upgrade
        try:
            result = manager.update_tier(email, new_tier)
            print(f"Updated {email} to {new_tier}")
        except ValueError as e:
            print(f"Error: {e}")
