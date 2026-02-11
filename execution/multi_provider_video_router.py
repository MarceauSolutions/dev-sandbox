#!/usr/bin/env python3
"""
Multi-Provider Video Router - Intelligent Cost-Optimized Video Generation

Routes video generation across multiple providers to:
1. Minimize costs by using free/cheap providers first
2. Mitigate rate limits by switching providers when needed
3. Match quality tier to content importance
4. Track costs and rate limits per provider

Providers (in priority order):
- FREE: MoviePy (local, $0, 70-85% success)
- BUDGET: Hailuo Fast ($0.10/video via Replicate)
- STANDARD: Creatomate ($0.05), Grok Imagine ($0.07/sec)
- PREMIUM: Veo 3 ($0.40-2.00 via Kie.ai)

Retired: Hailuo via fal.ai (balance exhausted, migrated to Replicate)
See docs/service-standards.md for full service standards.

Usage:
    # Auto-select best provider
    python multi_provider_video_router.py --images URL1,URL2 --headline "Transform"

    # Use specific quality tier
    python multi_provider_video_router.py --images URL1,URL2 --tier premium

    # View stats and rate limits
    python multi_provider_video_router.py --stats
    python multi_provider_video_router.py --limits
"""

import os
import sys
import json
import time
import argparse
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import requests
from dotenv import load_dotenv

load_dotenv()


class QualityTier(Enum):
    """Quality tiers for video generation."""
    FREE = "free"          # MoviePy only
    BUDGET = "budget"      # Hailuo Fast
    STANDARD = "standard"  # Creatomate, Grok Imagine
    PREMIUM = "premium"    # Veo 3


class Provider(Enum):
    """Available video generation providers."""
    MOVIEPY = "moviepy"
    HAILUO_FAST = "hailuo_fast"
    HAILUO = "hailuo"
    CREATOMATE = "creatomate"
    GROK_IMAGINE = "grok_imagine"
    VEO3_FAST = "veo3_fast"
    VEO3 = "veo3"


@dataclass
class ProviderConfig:
    """Configuration for a video provider."""
    name: str
    tier: QualityTier
    cost_per_second: float
    base_cost: float  # Minimum cost per video
    max_duration: float
    rate_limit_per_hour: int
    rate_limit_per_day: int
    api_key_env: str
    enabled: bool = True
    success_rate: float = 0.95


# Provider configurations with current pricing
PROVIDER_CONFIGS: Dict[Provider, ProviderConfig] = {
    Provider.MOVIEPY: ProviderConfig(
        name="MoviePy (Local)",
        tier=QualityTier.FREE,
        cost_per_second=0.0,
        base_cost=0.0,
        max_duration=60.0,
        rate_limit_per_hour=9999,
        rate_limit_per_day=9999,
        api_key_env="",  # No API key needed
        success_rate=0.75
    ),
    Provider.HAILUO_FAST: ProviderConfig(
        name="Hailuo 02 Fast (via Replicate)",
        tier=QualityTier.BUDGET,
        cost_per_second=0.017,  # 512P pricing
        base_cost=0.10,
        max_duration=10.0,
        rate_limit_per_hour=60,
        rate_limit_per_day=500,
        api_key_env="REPLICATE_API_TOKEN",
        success_rate=0.92
    ),
    Provider.HAILUO: ProviderConfig(
        name="Hailuo 02 (via Replicate)",
        tier=QualityTier.STANDARD,
        cost_per_second=0.045,  # 768P pricing
        base_cost=0.27,
        max_duration=10.0,
        rate_limit_per_hour=40,
        rate_limit_per_day=300,
        api_key_env="REPLICATE_API_TOKEN",
        success_rate=0.94
    ),
    Provider.CREATOMATE: ProviderConfig(
        name="Creatomate",
        tier=QualityTier.STANDARD,
        cost_per_second=0.0,
        base_cost=0.05,
        max_duration=60.0,
        rate_limit_per_hour=100,
        rate_limit_per_day=1000,
        api_key_env="CREATOMATE_API_KEY",
        success_rate=0.95
    ),
    Provider.GROK_IMAGINE: ProviderConfig(
        name="Grok Imagine Video (xAI)",
        tier=QualityTier.STANDARD,
        cost_per_second=0.07,  # $4.20/min = $0.07/sec
        base_cost=0.35,  # 5-second minimum
        max_duration=10.0,
        rate_limit_per_hour=30,
        rate_limit_per_day=200,
        api_key_env="XAI_API_KEY",
        success_rate=0.90
    ),
    Provider.VEO3_FAST: ProviderConfig(
        name="Veo 3 Fast (via Kie.ai)",
        tier=QualityTier.PREMIUM,
        cost_per_second=0.05,  # $0.40 for 8-sec
        base_cost=0.40,
        max_duration=8.0,
        rate_limit_per_hour=20,
        rate_limit_per_day=100,
        api_key_env="KIE_API_KEY",
        success_rate=0.95
    ),
    Provider.VEO3: ProviderConfig(
        name="Veo 3 Quality (via Kie.ai)",
        tier=QualityTier.PREMIUM,
        cost_per_second=0.25,  # $2.00 for 8-sec
        base_cost=2.00,
        max_duration=8.0,
        rate_limit_per_hour=10,
        rate_limit_per_day=50,
        api_key_env="KIE_API_KEY",
        success_rate=0.97
    ),
}


class RateLimitTracker:
    """Track rate limits across providers."""

    def __init__(self, data_dir: str = ".tmp/rate_limits"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.data_file = self.data_dir / "rate_limits.json"
        self.usage = self._load_usage()

    def _load_usage(self) -> Dict[str, Any]:
        """Load usage data from disk."""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"providers": {}}

    def _save_usage(self):
        """Save usage data to disk."""
        with open(self.data_file, 'w') as f:
            json.dump(self.usage, f, indent=2, default=str)

    def record_usage(self, provider: Provider):
        """Record a usage event for a provider."""
        provider_name = provider.value
        now = datetime.now().isoformat()

        if provider_name not in self.usage["providers"]:
            self.usage["providers"][provider_name] = {"events": []}

        self.usage["providers"][provider_name]["events"].append(now)
        self._cleanup_old_events(provider_name)
        self._save_usage()

    def _cleanup_old_events(self, provider_name: str):
        """Remove events older than 24 hours."""
        cutoff = datetime.now() - timedelta(hours=24)
        events = self.usage["providers"][provider_name]["events"]
        self.usage["providers"][provider_name]["events"] = [
            e for e in events
            if datetime.fromisoformat(e) > cutoff
        ]

    def get_hourly_usage(self, provider: Provider) -> int:
        """Get usage count for last hour."""
        provider_name = provider.value
        if provider_name not in self.usage["providers"]:
            return 0

        cutoff = datetime.now() - timedelta(hours=1)
        events = self.usage["providers"][provider_name]["events"]
        return len([e for e in events if datetime.fromisoformat(e) > cutoff])

    def get_daily_usage(self, provider: Provider) -> int:
        """Get usage count for last 24 hours."""
        provider_name = provider.value
        if provider_name not in self.usage["providers"]:
            return 0

        return len(self.usage["providers"][provider_name]["events"])

    def is_rate_limited(self, provider: Provider) -> bool:
        """Check if provider is rate limited."""
        config = PROVIDER_CONFIGS[provider]
        hourly = self.get_hourly_usage(provider)
        daily = self.get_daily_usage(provider)

        return hourly >= config.rate_limit_per_hour or daily >= config.rate_limit_per_day

    def get_all_limits(self) -> Dict[str, Any]:
        """Get rate limit status for all providers."""
        result = {}
        for provider in Provider:
            config = PROVIDER_CONFIGS[provider]
            hourly = self.get_hourly_usage(provider)
            daily = self.get_daily_usage(provider)

            result[provider.value] = {
                "name": config.name,
                "hourly_used": hourly,
                "hourly_limit": config.rate_limit_per_hour,
                "daily_used": daily,
                "daily_limit": config.rate_limit_per_day,
                "is_limited": self.is_rate_limited(provider)
            }
        return result


class CostTracker:
    """Track costs across providers."""

    def __init__(self, data_dir: str = ".tmp/costs"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.data_file = self.data_dir / "cost_tracking.json"
        self.costs = self._load_costs()

    def _load_costs(self) -> Dict[str, Any]:
        """Load cost data from disk."""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"events": [], "totals": {}}

    def _save_costs(self):
        """Save cost data to disk."""
        with open(self.data_file, 'w') as f:
            json.dump(self.costs, f, indent=2, default=str)

    def record_cost(self, provider: Provider, cost: float, duration: float, success: bool):
        """Record a cost event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "provider": provider.value,
            "cost": cost,
            "duration": duration,
            "success": success
        }
        self.costs["events"].append(event)

        # Update totals
        provider_name = provider.value
        if provider_name not in self.costs["totals"]:
            self.costs["totals"][provider_name] = {
                "count": 0, "cost": 0, "success": 0, "failed": 0
            }

        self.costs["totals"][provider_name]["count"] += 1
        self.costs["totals"][provider_name]["cost"] += cost
        if success:
            self.costs["totals"][provider_name]["success"] += 1
        else:
            self.costs["totals"][provider_name]["failed"] += 1

        self._cleanup_old_events()
        self._save_costs()

    def _cleanup_old_events(self):
        """Keep only last 30 days of events."""
        cutoff = datetime.now() - timedelta(days=30)
        self.costs["events"] = [
            e for e in self.costs["events"]
            if datetime.fromisoformat(e["timestamp"]) > cutoff
        ]

    def get_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get cost summary for specified period."""
        cutoff = datetime.now() - timedelta(days=days)

        # Filter events by time period
        recent_events = [
            e for e in self.costs["events"]
            if datetime.fromisoformat(e["timestamp"]) > cutoff
        ]

        # Aggregate by provider
        by_provider = {}
        total_cost = 0
        total_videos = 0

        for event in recent_events:
            provider = event["provider"]
            if provider not in by_provider:
                by_provider[provider] = {"count": 0, "cost": 0, "success": 0}

            by_provider[provider]["count"] += 1
            by_provider[provider]["cost"] += event["cost"]
            if event["success"]:
                by_provider[provider]["success"] += 1
                total_videos += 1

            total_cost += event["cost"]

        # Calculate average cost
        avg_cost = total_cost / total_videos if total_videos > 0 else 0

        return {
            "period_days": days,
            "total_cost": total_cost,
            "total_videos": total_videos,
            "average_cost": avg_cost,
            "by_provider": by_provider
        }


class MultiProviderVideoRouter:
    """
    Intelligent multi-provider video router.

    Features:
    - Quality tier-based routing
    - Automatic rate limit handling
    - Cost optimization
    - Fallback chains
    - Usage analytics
    """

    # Fallback chains per quality tier
    FALLBACK_CHAINS = {
        QualityTier.FREE: [Provider.MOVIEPY],
        QualityTier.BUDGET: [
            Provider.MOVIEPY,
            Provider.HAILUO_FAST,
            Provider.CREATOMATE
        ],
        QualityTier.STANDARD: [
            Provider.MOVIEPY,
            Provider.CREATOMATE,
            Provider.HAILUO,
            Provider.GROK_IMAGINE
        ],
        QualityTier.PREMIUM: [
            Provider.VEO3_FAST,
            Provider.VEO3,
            Provider.GROK_IMAGINE,
            Provider.CREATOMATE
        ]
    }

    def __init__(self, data_dir: str = ".tmp"):
        """Initialize multi-provider router."""
        self.rate_limiter = RateLimitTracker(f"{data_dir}/rate_limits")
        self.cost_tracker = CostTracker(f"{data_dir}/costs")
        self.log_dir = Path(f"{data_dir}/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Initialize available providers
        self._init_providers()

    def _init_providers(self):
        """Initialize provider clients based on available API keys."""
        self.providers = {}

        # MoviePy - always available (local)
        try:
            from moviepy_video_generator import MoviePyVideoGenerator
            self.providers[Provider.MOVIEPY] = MoviePyVideoGenerator()
        except ImportError:
            print("Warning: MoviePy not available")

        # Creatomate
        if os.getenv("CREATOMATE_API_KEY"):
            try:
                from creatomate_api import CreatomateAPI
                self.providers[Provider.CREATOMATE] = CreatomateAPI()
            except ImportError:
                pass

        # Grok Imagine - uses xAI API
        if os.getenv("XAI_API_KEY"):
            self.providers[Provider.GROK_IMAGINE] = GrokImagineProvider()

        # Hailuo via Replicate (migrated from fal.ai)
        if os.getenv("REPLICATE_API_TOKEN"):
            self.providers[Provider.HAILUO_FAST] = HailuoProvider(fast=True)
            self.providers[Provider.HAILUO] = HailuoProvider(fast=False)

        # Veo 3 via Kie.ai
        if os.getenv("KIE_API_KEY"):
            self.providers[Provider.VEO3_FAST] = Veo3Provider(fast=True)
            self.providers[Provider.VEO3] = Veo3Provider(fast=False)

        print(f"Initialized {len(self.providers)} providers: {[p.value for p in self.providers.keys()]}")

    def _select_provider(self, tier: QualityTier) -> Optional[Provider]:
        """Select best available provider for quality tier."""
        chain = self.FALLBACK_CHAINS[tier]

        for provider in chain:
            # Check if provider is available
            if provider not in self.providers:
                continue

            # Check if rate limited
            if self.rate_limiter.is_rate_limited(provider):
                print(f"  {provider.value}: Rate limited, skipping")
                continue

            return provider

        return None

    def create_video(
        self,
        image_urls: List[str] = None,
        prompt: str = None,
        headline: str = "",
        cta_text: str = "",
        duration: float = 10.0,
        music_style: str = "energetic",
        tier: QualityTier = QualityTier.STANDARD,
        force_provider: Provider = None
    ) -> Dict[str, Any]:
        """
        Create video using intelligent multi-provider routing.

        Args:
            image_urls: List of image URLs (for image-to-video)
            prompt: Text prompt (for text-to-video)
            headline: Headline text overlay
            cta_text: CTA text overlay
            duration: Video duration in seconds
            music_style: Background music style
            tier: Quality tier (FREE, BUDGET, STANDARD, PREMIUM)
            force_provider: Override automatic provider selection

        Returns:
            Dict with success status, video URL/path, provider used, and cost
        """
        print(f"\n{'='*70}")
        print("MULTI-PROVIDER VIDEO ROUTER")
        print(f"{'='*70}")
        print(f"Quality Tier: {tier.value}")
        print(f"Duration: {duration}s")

        start_time = time.time()

        # Select provider
        if force_provider:
            provider = force_provider
            print(f"Forced Provider: {provider.value}")
        else:
            provider = self._select_provider(tier)
            if not provider:
                return {
                    "success": False,
                    "error": f"No available providers for tier {tier.value}",
                    "tier": tier.value
                }
            print(f"Selected Provider: {provider.value}")

        # Get provider config
        config = PROVIDER_CONFIGS[provider]
        estimated_cost = config.base_cost + (config.cost_per_second * duration)
        print(f"Estimated Cost: ${estimated_cost:.3f}")

        # Attempt generation
        result = self._generate_with_provider(
            provider=provider,
            image_urls=image_urls,
            prompt=prompt,
            headline=headline,
            cta_text=cta_text,
            duration=duration,
            music_style=music_style
        )

        # Record metrics
        self.rate_limiter.record_usage(provider)
        self.cost_tracker.record_cost(
            provider=provider,
            cost=estimated_cost if result.get("success") else 0,
            duration=duration,
            success=result.get("success", False)
        )

        # If failed and not at end of chain, try fallback
        if not result.get("success") and not force_provider:
            print(f"\n{provider.value} failed, trying fallback...")

            chain = self.FALLBACK_CHAINS[tier]
            current_idx = chain.index(provider) if provider in chain else -1

            for fallback in chain[current_idx + 1:]:
                if fallback not in self.providers:
                    continue
                if self.rate_limiter.is_rate_limited(fallback):
                    continue

                print(f"Trying fallback: {fallback.value}")

                result = self._generate_with_provider(
                    provider=fallback,
                    image_urls=image_urls,
                    prompt=prompt,
                    headline=headline,
                    cta_text=cta_text,
                    duration=duration,
                    music_style=music_style
                )

                fallback_config = PROVIDER_CONFIGS[fallback]
                fallback_cost = fallback_config.base_cost + (fallback_config.cost_per_second * duration)

                self.rate_limiter.record_usage(fallback)
                self.cost_tracker.record_cost(
                    provider=fallback,
                    cost=fallback_cost if result.get("success") else 0,
                    duration=duration,
                    success=result.get("success", False)
                )

                if result.get("success"):
                    result["provider"] = fallback.value
                    result["cost"] = fallback_cost
                    break
        else:
            result["provider"] = provider.value
            result["cost"] = estimated_cost if result.get("success") else 0

        # Add timing
        result["generation_time"] = time.time() - start_time
        result["tier"] = tier.value

        # Log result
        self._log_result(result)

        return result

    def _generate_with_provider(
        self,
        provider: Provider,
        image_urls: List[str] = None,
        prompt: str = None,
        headline: str = "",
        cta_text: str = "",
        duration: float = 10.0,
        music_style: str = "energetic"
    ) -> Dict[str, Any]:
        """Generate video using specific provider."""

        client = self.providers.get(provider)
        if not client:
            return {"success": False, "error": f"Provider {provider.value} not available"}

        try:
            if provider == Provider.MOVIEPY:
                return client.create_fitness_ad(
                    image_urls=image_urls or [],
                    headline=headline,
                    cta_text=cta_text,
                    duration=duration,
                    music_style=music_style
                )

            elif provider == Provider.CREATOMATE:
                return client.create_fitness_ad(
                    image_urls=image_urls or [],
                    headline=headline,
                    cta_text=cta_text,
                    duration=duration,
                    music_style=music_style
                )

            elif provider == Provider.GROK_IMAGINE:
                return client.generate_video(
                    prompt=prompt or f"{headline}. {cta_text}",
                    duration=int(duration)
                )

            elif provider in [Provider.HAILUO_FAST, Provider.HAILUO]:
                return client.generate_video(
                    prompt=prompt or f"{headline}. {cta_text}",
                    image_urls=image_urls,
                    duration=int(duration)
                )

            elif provider in [Provider.VEO3_FAST, Provider.VEO3]:
                return client.generate_video(
                    prompt=prompt or f"{headline}. {cta_text}",
                    duration=int(min(duration, 8))  # Veo3 max 8 seconds
                )

            else:
                return {"success": False, "error": f"Unknown provider: {provider.value}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _log_result(self, result: Dict[str, Any]):
        """Log generation result."""
        log_file = self.log_dir / "generations.jsonl"
        entry = {
            "timestamp": datetime.now().isoformat(),
            **result
        }
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get usage statistics."""
        cost_summary = self.cost_tracker.get_summary(days)
        rate_limits = self.rate_limiter.get_all_limits()

        return {
            "costs": cost_summary,
            "rate_limits": rate_limits,
            "available_providers": [p.value for p in self.providers.keys()]
        }

    def print_statistics(self, days: int = 30):
        """Print formatted statistics."""
        stats = self.get_statistics(days)

        print(f"\n{'='*70}")
        print(f"MULTI-PROVIDER VIDEO ROUTER STATISTICS (Last {days} Days)")
        print(f"{'='*70}\n")

        # Cost summary
        costs = stats["costs"]
        print(f"Total Videos: {costs['total_videos']}")
        print(f"Total Cost: ${costs['total_cost']:.2f}")
        print(f"Average Cost: ${costs['average_cost']:.3f}/video")
        print()

        # By provider
        print("BY PROVIDER:")
        for provider, data in costs.get("by_provider", {}).items():
            success_rate = data["success"] / data["count"] * 100 if data["count"] > 0 else 0
            print(f"  {provider}:")
            print(f"    Videos: {data['count']} (success: {success_rate:.0f}%)")
            print(f"    Cost: ${data['cost']:.2f}")
        print()

        # Rate limits
        print("RATE LIMIT STATUS:")
        for provider, limits in stats["rate_limits"].items():
            status = "⚠️ LIMITED" if limits["is_limited"] else "✓ OK"
            print(f"  {limits['name']}:")
            print(f"    Hourly: {limits['hourly_used']}/{limits['hourly_limit']} | Daily: {limits['daily_used']}/{limits['daily_limit']} {status}")
        print()

        # Available providers
        print(f"Available Providers: {', '.join(stats['available_providers'])}")
        print()

    def print_rate_limits(self):
        """Print current rate limit status."""
        limits = self.rate_limiter.get_all_limits()

        print(f"\n{'='*70}")
        print("RATE LIMIT STATUS")
        print(f"{'='*70}\n")

        for provider, data in limits.items():
            status = "🔴 LIMITED" if data["is_limited"] else "🟢 OK"
            hourly_pct = data["hourly_used"] / data["hourly_limit"] * 100 if data["hourly_limit"] > 0 else 0
            daily_pct = data["daily_used"] / data["daily_limit"] * 100 if data["daily_limit"] > 0 else 0

            print(f"{data['name']} {status}")
            print(f"  Hourly: {data['hourly_used']}/{data['hourly_limit']} ({hourly_pct:.0f}%)")
            print(f"  Daily:  {data['daily_used']}/{data['daily_limit']} ({daily_pct:.0f}%)")
            print()


# Provider implementations

class GrokImagineProvider:
    """Grok Imagine Video provider (xAI)."""

    API_URL = "https://api.x.ai/v1/videos/generations"

    def __init__(self):
        self.api_key = os.getenv("XAI_API_KEY")

    def generate_video(self, prompt: str, duration: int = 10) -> Dict[str, Any]:
        """Generate video from text prompt."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "grok-imagine-video",
            "prompt": prompt,
            "duration": min(duration, 10),
            "aspect_ratio": "16:9",
            "resolution": "720p"
        }

        try:
            # Initial request
            response = requests.post(self.API_URL, headers=headers, json=payload, timeout=30)

            if response.status_code != 200:
                return {"success": False, "error": f"API error: {response.status_code}"}

            data = response.json()

            # Poll for completion (simple implementation)
            video_url = data.get("url") or data.get("data", [{}])[0].get("url")

            if video_url:
                return {
                    "success": True,
                    "video_url": video_url,
                    "method": "grok_imagine"
                }
            else:
                return {"success": False, "error": "No video URL in response"}

        except Exception as e:
            return {"success": False, "error": str(e)}


class HailuoProvider:
    """Hailuo/Minimax provider via Replicate (migrated from fal.ai 2026-02-11)."""

    def __init__(self, fast: bool = False):
        self.fast = fast
        self.model_id = "minimax/hailuo-02-fast" if fast else "minimax/hailuo-02"

    def generate_video(
        self,
        prompt: str,
        image_urls: List[str] = None,
        duration: int = 6
    ) -> Dict[str, Any]:
        """Generate video using Hailuo via Replicate."""

        try:
            import replicate

            input_params = {
                "prompt": prompt,
                "duration": min(duration, 10)
            }

            if image_urls:
                input_params["first_frame_image"] = image_urls[0]

            output = replicate.run(self.model_id, input=input_params)

            # Replicate returns the video URL directly
            video_url = str(output) if output else None

            if video_url:
                return {
                    "success": True,
                    "video_url": video_url,
                    "method": "hailuo_fast" if self.fast else "hailuo"
                }
            else:
                return {"success": False, "error": "No video URL in response"}

        except Exception as e:
            return {"success": False, "error": str(e)}


class Veo3Provider:
    """Veo 3 provider via Kie.ai third-party API."""

    def __init__(self, fast: bool = True):
        self.fast = fast
        self.api_key = os.getenv("KIE_API_KEY")
        # Kie.ai endpoint
        self.base_url = "https://api.kie.ai/v1"

    def generate_video(self, prompt: str, duration: int = 8) -> Dict[str, Any]:
        """Generate video using Veo 3 via Kie.ai."""

        if not self.api_key:
            return {"success": False, "error": "KIE_API_KEY not set"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        model = "veo-3-fast" if self.fast else "veo-3"

        payload = {
            "model": model,
            "prompt": prompt,
            "duration": min(duration, 8),  # Veo3 max 8 seconds
            "aspect_ratio": "16:9"
        }

        try:
            response = requests.post(
                f"{self.base_url}/videos/generations",
                headers=headers,
                json=payload,
                timeout=180
            )

            if response.status_code != 200:
                return {"success": False, "error": f"API error: {response.status_code}"}

            data = response.json()
            video_url = data.get("url") or data.get("video_url")

            if video_url:
                return {
                    "success": True,
                    "video_url": video_url,
                    "method": "veo3_fast" if self.fast else "veo3"
                }
            else:
                return {"success": False, "error": "No video URL in response"}

        except Exception as e:
            return {"success": False, "error": str(e)}


def main():
    """CLI for multi-provider video router."""
    parser = argparse.ArgumentParser(
        description="Multi-provider video router with intelligent cost optimization"
    )

    # Generation arguments
    parser.add_argument('--images', help='Comma-separated image URLs')
    parser.add_argument('--prompt', help='Text prompt for video generation')
    parser.add_argument('--headline', default='', help='Headline text overlay')
    parser.add_argument('--cta', default='', help='CTA text overlay')
    parser.add_argument('--duration', type=float, default=10.0, help='Video duration')
    parser.add_argument('--music', default='energetic', help='Music style')

    # Tier selection
    parser.add_argument('--tier',
                       choices=['free', 'budget', 'standard', 'premium'],
                       default='standard',
                       help='Quality tier')

    # Force specific provider
    parser.add_argument('--provider',
                       choices=[p.value for p in Provider],
                       help='Force specific provider')

    # Statistics
    parser.add_argument('--stats', action='store_true', help='Show usage statistics')
    parser.add_argument('--limits', action='store_true', help='Show rate limit status')
    parser.add_argument('--days', type=int, default=30, help='Days to analyze')

    args = parser.parse_args()

    router = MultiProviderVideoRouter()

    # Show statistics
    if args.stats:
        router.print_statistics(days=args.days)
        return 0

    # Show rate limits
    if args.limits:
        router.print_rate_limits()
        return 0

    # Generate video
    if not args.images and not args.prompt:
        print("Error: Either --images or --prompt required")
        print("Use --stats or --limits to view statistics")
        return 1

    image_urls = [u.strip() for u in args.images.split(',')] if args.images else None
    tier = QualityTier(args.tier)
    provider = Provider(args.provider) if args.provider else None

    result = router.create_video(
        image_urls=image_urls,
        prompt=args.prompt,
        headline=args.headline,
        cta_text=args.cta,
        duration=args.duration,
        music_style=args.music,
        tier=tier,
        force_provider=provider
    )

    if result.get("success"):
        print(f"\n{'='*70}")
        print("VIDEO GENERATION COMPLETE!")
        print(f"{'='*70}")
        print(f"Provider: {result.get('provider')}")
        print(f"Tier: {result.get('tier')}")
        print(f"Cost: ${result.get('cost', 0):.3f}")
        print(f"Time: {result.get('generation_time', 0):.1f}s")
        print(f"Video: {result.get('video_url') or result.get('video_path')}")
        return 0
    else:
        print(f"\n✗ Video generation failed: {result.get('error')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
