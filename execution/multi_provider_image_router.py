#!/usr/bin/env python3
"""
Multi-Provider Image Router - Intelligent Cost-Optimized Image Generation

Routes image generation across multiple providers to:
1. Minimize costs by using cheap providers for bulk generation
2. Mitigate rate limits by switching providers when needed
3. Match quality tier to content importance

Providers (in priority order):
- BUDGET: Stable Diffusion via Replicate (~$0.003/image)
- STANDARD: xAI Grok ($0.07/image)
- PREMIUM: DALL-E 3 (~$0.04-0.12/image)

Usage:
    # Auto-select best provider
    python multi_provider_image_router.py --prompt "Fitness workout" --count 4

    # Use specific quality tier
    python multi_provider_image_router.py --prompt "Hero image" --tier premium

    # View stats
    python multi_provider_image_router.py --stats
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from enum import Enum
import requests
from dotenv import load_dotenv

load_dotenv()


class ImageQualityTier(Enum):
    """Quality tiers for image generation."""
    BUDGET = "budget"      # Replicate/SD
    STANDARD = "standard"  # Grok
    PREMIUM = "premium"    # DALL-E 3


class ImageProvider(Enum):
    """Available image generation providers."""
    REPLICATE_SD = "replicate_sd"
    GROK = "grok"
    DALLE3 = "dalle3"
    IDEOGRAM = "ideogram"


# Provider configurations
IMAGE_PROVIDER_CONFIGS = {
    ImageProvider.REPLICATE_SD: {
        "name": "Stable Diffusion (Replicate)",
        "tier": ImageQualityTier.BUDGET,
        "cost_per_image": 0.003,
        "rate_limit_per_hour": 200,
        "rate_limit_per_day": 2000,
        "api_key_env": "REPLICATE_API_TOKEN",
        "resolution": "1024x1024",
        "quality_score": 7
    },
    ImageProvider.GROK: {
        "name": "Grok Aurora (xAI)",
        "tier": ImageQualityTier.STANDARD,
        "cost_per_image": 0.07,
        "rate_limit_per_hour": 60,
        "rate_limit_per_day": 500,
        "api_key_env": "XAI_API_KEY",
        "resolution": "1024x768",
        "quality_score": 8
    },
    ImageProvider.DALLE3: {
        "name": "DALL-E 3 (OpenAI)",
        "tier": ImageQualityTier.PREMIUM,
        "cost_per_image": 0.08,  # HD quality
        "rate_limit_per_hour": 50,
        "rate_limit_per_day": 200,
        "api_key_env": "OPENAI_API_KEY",
        "resolution": "1024x1024",
        "quality_score": 9
    },
    ImageProvider.IDEOGRAM: {
        "name": "Ideogram",
        "tier": ImageQualityTier.STANDARD,
        "cost_per_image": 0.05,
        "rate_limit_per_hour": 100,
        "rate_limit_per_day": 1000,
        "api_key_env": "IDEOGRAM_API_KEY",
        "resolution": "1024x1024",
        "quality_score": 8
    }
}


class ImageRateLimitTracker:
    """Track rate limits for image providers."""

    def __init__(self, data_dir: str = ".tmp/image_limits"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.data_file = self.data_dir / "image_limits.json"
        self.usage = self._load()

    def _load(self) -> Dict:
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"providers": {}}

    def _save(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.usage, f, indent=2, default=str)

    def record(self, provider: ImageProvider, count: int = 1):
        name = provider.value
        now = datetime.now().isoformat()

        if name not in self.usage["providers"]:
            self.usage["providers"][name] = {"events": []}

        for _ in range(count):
            self.usage["providers"][name]["events"].append(now)

        self._cleanup(name)
        self._save()

    def _cleanup(self, name: str):
        cutoff = datetime.now() - timedelta(hours=24)
        events = self.usage["providers"][name]["events"]
        self.usage["providers"][name]["events"] = [
            e for e in events if datetime.fromisoformat(e) > cutoff
        ]

    def get_hourly(self, provider: ImageProvider) -> int:
        name = provider.value
        if name not in self.usage["providers"]:
            return 0
        cutoff = datetime.now() - timedelta(hours=1)
        return len([e for e in self.usage["providers"][name]["events"]
                   if datetime.fromisoformat(e) > cutoff])

    def get_daily(self, provider: ImageProvider) -> int:
        name = provider.value
        if name not in self.usage["providers"]:
            return 0
        return len(self.usage["providers"][name]["events"])

    def is_limited(self, provider: ImageProvider) -> bool:
        config = IMAGE_PROVIDER_CONFIGS[provider]
        return (self.get_hourly(provider) >= config["rate_limit_per_hour"] or
                self.get_daily(provider) >= config["rate_limit_per_day"])


class ImageCostTracker:
    """Track costs for image generation."""

    def __init__(self, data_dir: str = ".tmp/image_costs"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.data_file = self.data_dir / "image_costs.json"
        self.costs = self._load()

    def _load(self) -> Dict:
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"events": []}

    def _save(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.costs, f, indent=2, default=str)

    def record(self, provider: ImageProvider, count: int, cost: float, success: bool):
        self.costs["events"].append({
            "timestamp": datetime.now().isoformat(),
            "provider": provider.value,
            "count": count,
            "cost": cost,
            "success": success
        })
        self._cleanup()
        self._save()

    def _cleanup(self):
        cutoff = datetime.now() - timedelta(days=30)
        self.costs["events"] = [
            e for e in self.costs["events"]
            if datetime.fromisoformat(e["timestamp"]) > cutoff
        ]

    def get_summary(self, days: int = 30) -> Dict:
        cutoff = datetime.now() - timedelta(days=days)
        recent = [e for e in self.costs["events"]
                 if datetime.fromisoformat(e["timestamp"]) > cutoff]

        by_provider = {}
        total_cost = 0
        total_images = 0

        for event in recent:
            prov = event["provider"]
            if prov not in by_provider:
                by_provider[prov] = {"count": 0, "cost": 0}
            by_provider[prov]["count"] += event["count"]
            by_provider[prov]["cost"] += event["cost"]
            total_cost += event["cost"]
            if event["success"]:
                total_images += event["count"]

        return {
            "period_days": days,
            "total_cost": total_cost,
            "total_images": total_images,
            "avg_cost": total_cost / total_images if total_images > 0 else 0,
            "by_provider": by_provider
        }


class MultiProviderImageRouter:
    """
    Intelligent multi-provider image router.

    Features:
    - Quality tier-based routing
    - Rate limit handling
    - Cost optimization
    - Automatic fallback
    """

    FALLBACK_CHAINS = {
        ImageQualityTier.BUDGET: [
            ImageProvider.REPLICATE_SD,
            ImageProvider.GROK
        ],
        ImageQualityTier.STANDARD: [
            ImageProvider.GROK,
            ImageProvider.IDEOGRAM,
            ImageProvider.REPLICATE_SD
        ],
        ImageQualityTier.PREMIUM: [
            ImageProvider.DALLE3,
            ImageProvider.GROK,
            ImageProvider.IDEOGRAM
        ]
    }

    def __init__(self, data_dir: str = ".tmp"):
        self.rate_limiter = ImageRateLimitTracker(f"{data_dir}/image_limits")
        self.cost_tracker = ImageCostTracker(f"{data_dir}/image_costs")
        self._init_providers()

    def _init_providers(self):
        """Initialize available providers."""
        self.providers = {}

        # xAI Grok
        if os.getenv("XAI_API_KEY"):
            self.providers[ImageProvider.GROK] = GrokImageClient()

        # Replicate
        if os.getenv("REPLICATE_API_TOKEN"):
            self.providers[ImageProvider.REPLICATE_SD] = ReplicateSDClient()

        # OpenAI DALL-E 3
        if os.getenv("OPENAI_API_KEY"):
            self.providers[ImageProvider.DALLE3] = DallE3Client()

        # Ideogram
        if os.getenv("IDEOGRAM_API_KEY"):
            self.providers[ImageProvider.IDEOGRAM] = IdeogramClient()

        print(f"Initialized {len(self.providers)} image providers: {[p.value for p in self.providers.keys()]}")

    def _select_provider(self, tier: ImageQualityTier) -> Optional[ImageProvider]:
        """Select best available provider."""
        for provider in self.FALLBACK_CHAINS[tier]:
            if provider not in self.providers:
                continue
            if self.rate_limiter.is_limited(provider):
                print(f"  {provider.value}: Rate limited, skipping")
                continue
            return provider
        return None

    def generate_images(
        self,
        prompt: str,
        count: int = 1,
        tier: ImageQualityTier = ImageQualityTier.STANDARD,
        output_dir: str = None,
        force_provider: ImageProvider = None
    ) -> Dict[str, Any]:
        """
        Generate images using intelligent routing.

        Args:
            prompt: Text description
            count: Number of images (1-10)
            tier: Quality tier
            output_dir: Save images to directory
            force_provider: Override provider selection

        Returns:
            Dict with success, image URLs/paths, provider, cost
        """
        print(f"\n{'='*70}")
        print("MULTI-PROVIDER IMAGE ROUTER")
        print(f"{'='*70}")
        print(f"Prompt: {prompt[:60]}...")
        print(f"Count: {count}")
        print(f"Tier: {tier.value}")

        # Select provider
        if force_provider:
            provider = force_provider
        else:
            provider = self._select_provider(tier)
            if not provider:
                return {"success": False, "error": f"No providers available for tier {tier.value}"}

        config = IMAGE_PROVIDER_CONFIGS[provider]
        estimated_cost = config["cost_per_image"] * count
        print(f"Provider: {config['name']}")
        print(f"Estimated Cost: ${estimated_cost:.3f}")

        # Generate
        result = self._generate_with_provider(provider, prompt, count, output_dir)

        # Track
        self.rate_limiter.record(provider, count)
        self.cost_tracker.record(
            provider=provider,
            count=count,
            cost=estimated_cost if result.get("success") else 0,
            success=result.get("success", False)
        )

        # Fallback if failed
        if not result.get("success") and not force_provider:
            chain = self.FALLBACK_CHAINS[tier]
            idx = chain.index(provider) if provider in chain else -1

            for fallback in chain[idx + 1:]:
                if fallback not in self.providers:
                    continue
                if self.rate_limiter.is_limited(fallback):
                    continue

                print(f"Trying fallback: {fallback.value}")
                result = self._generate_with_provider(fallback, prompt, count, output_dir)

                fb_config = IMAGE_PROVIDER_CONFIGS[fallback]
                fb_cost = fb_config["cost_per_image"] * count

                self.rate_limiter.record(fallback, count)
                self.cost_tracker.record(
                    provider=fallback,
                    count=count,
                    cost=fb_cost if result.get("success") else 0,
                    success=result.get("success", False)
                )

                if result.get("success"):
                    result["provider"] = fallback.value
                    result["cost"] = fb_cost
                    break
        else:
            result["provider"] = provider.value
            result["cost"] = estimated_cost if result.get("success") else 0

        result["tier"] = tier.value
        return result

    def _generate_with_provider(
        self,
        provider: ImageProvider,
        prompt: str,
        count: int,
        output_dir: str = None
    ) -> Dict[str, Any]:
        """Generate with specific provider."""
        client = self.providers.get(provider)
        if not client:
            return {"success": False, "error": f"Provider {provider.value} not available"}

        try:
            return client.generate(prompt, count, output_dir)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_statistics(self, days: int = 30) -> Dict:
        return self.cost_tracker.get_summary(days)

    def print_statistics(self, days: int = 30):
        stats = self.get_statistics(days)

        print(f"\n{'='*70}")
        print(f"IMAGE GENERATION STATISTICS (Last {days} Days)")
        print(f"{'='*70}\n")
        print(f"Total Images: {stats['total_images']}")
        print(f"Total Cost: ${stats['total_cost']:.2f}")
        print(f"Average Cost: ${stats['avg_cost']:.4f}/image")
        print()

        print("BY PROVIDER:")
        for prov, data in stats.get("by_provider", {}).items():
            avg = data["cost"] / data["count"] if data["count"] > 0 else 0
            print(f"  {prov}: {data['count']} images, ${data['cost']:.2f} (${avg:.4f}/img)")


# Provider clients

class GrokImageClient:
    """Grok/xAI image generation client."""

    API_URL = "https://api.x.ai/v1/images/generations"

    def __init__(self):
        self.api_key = os.getenv("XAI_API_KEY")

    def generate(self, prompt: str, count: int = 1, output_dir: str = None) -> Dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "prompt": prompt,
            "n": min(count, 10),
            "model": "grok-2-image-1212"
        }

        try:
            response = requests.post(self.API_URL, headers=headers, json=payload, timeout=60)
            if response.status_code != 200:
                return {"success": False, "error": f"API error: {response.status_code}"}

            data = response.json()
            urls = [img.get("url") for img in data.get("data", []) if img.get("url")]

            if output_dir:
                paths = self._download(urls, output_dir)
                return {"success": True, "paths": paths, "urls": urls}

            return {"success": True, "urls": urls}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _download(self, urls: List[str], output_dir: str) -> List[str]:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        paths = []
        for i, url in enumerate(urls):
            try:
                resp = requests.get(url, timeout=30)
                path = f"{output_dir}/image_{i+1}.png"
                with open(path, 'wb') as f:
                    f.write(resp.content)
                paths.append(path)
            except:
                pass
        return paths


class ReplicateSDClient:
    """Stable Diffusion via Replicate."""

    def __init__(self):
        self.api_key = os.getenv("REPLICATE_API_TOKEN")

    def generate(self, prompt: str, count: int = 1, output_dir: str = None) -> Dict:
        try:
            import replicate

            outputs = []
            for _ in range(count):
                output = replicate.run(
                    "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
                    input={
                        "prompt": prompt,
                        "width": 1024,
                        "height": 1024,
                        "num_outputs": 1
                    }
                )
                if output:
                    outputs.extend(output)

            if output_dir:
                paths = self._download(outputs, output_dir)
                return {"success": True, "paths": paths, "urls": outputs}

            return {"success": True, "urls": outputs}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _download(self, urls: List[str], output_dir: str) -> List[str]:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        paths = []
        for i, url in enumerate(urls):
            try:
                resp = requests.get(url, timeout=30)
                path = f"{output_dir}/sd_image_{i+1}.png"
                with open(path, 'wb') as f:
                    f.write(resp.content)
                paths.append(path)
            except:
                pass
        return paths


class DallE3Client:
    """DALL-E 3 via OpenAI."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")

    def generate(self, prompt: str, count: int = 1, output_dir: str = None) -> Dict:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            urls = []
            # DALL-E 3 only supports n=1, so loop
            for _ in range(count):
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024",
                    quality="hd",
                    n=1
                )
                if response.data:
                    urls.append(response.data[0].url)

            if output_dir:
                paths = self._download(urls, output_dir)
                return {"success": True, "paths": paths, "urls": urls}

            return {"success": True, "urls": urls}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _download(self, urls: List[str], output_dir: str) -> List[str]:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        paths = []
        for i, url in enumerate(urls):
            try:
                resp = requests.get(url, timeout=30)
                path = f"{output_dir}/dalle_image_{i+1}.png"
                with open(path, 'wb') as f:
                    f.write(resp.content)
                paths.append(path)
            except:
                pass
        return paths


class IdeogramClient:
    """Ideogram image generation."""

    def __init__(self):
        self.api_key = os.getenv("IDEOGRAM_API_KEY")

    def generate(self, prompt: str, count: int = 1, output_dir: str = None) -> Dict:
        headers = {
            "Api-Key": self.api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "image_request": {
                "prompt": prompt,
                "model": "V_2",
                "magic_prompt_option": "AUTO"
            }
        }

        try:
            urls = []
            for _ in range(count):
                response = requests.post(
                    "https://api.ideogram.ai/generate",
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                if response.status_code == 200:
                    data = response.json()
                    for img in data.get("data", []):
                        if img.get("url"):
                            urls.append(img["url"])

            if output_dir:
                paths = self._download(urls, output_dir)
                return {"success": True, "paths": paths, "urls": urls}

            return {"success": True, "urls": urls}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _download(self, urls: List[str], output_dir: str) -> List[str]:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        paths = []
        for i, url in enumerate(urls):
            try:
                resp = requests.get(url, timeout=30)
                path = f"{output_dir}/ideogram_image_{i+1}.png"
                with open(path, 'wb') as f:
                    f.write(resp.content)
                paths.append(path)
            except:
                pass
        return paths


def main():
    parser = argparse.ArgumentParser(description="Multi-provider image router")

    parser.add_argument('--prompt', help='Image description')
    parser.add_argument('--count', type=int, default=1, help='Number of images')
    parser.add_argument('--tier', choices=['budget', 'standard', 'premium'],
                       default='standard', help='Quality tier')
    parser.add_argument('--provider', choices=[p.value for p in ImageProvider],
                       help='Force specific provider')
    parser.add_argument('--output', help='Output directory')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--days', type=int, default=30, help='Days for stats')

    args = parser.parse_args()

    router = MultiProviderImageRouter()

    if args.stats:
        router.print_statistics(args.days)
        return 0

    if not args.prompt:
        print("Error: --prompt required")
        return 1

    tier = ImageQualityTier(args.tier)
    provider = ImageProvider(args.provider) if args.provider else None

    result = router.generate_images(
        prompt=args.prompt,
        count=args.count,
        tier=tier,
        output_dir=args.output,
        force_provider=provider
    )

    if result.get("success"):
        print(f"\n✅ Generated {len(result.get('urls', []))} images")
        print(f"Provider: {result.get('provider')}")
        print(f"Cost: ${result.get('cost', 0):.3f}")
        for i, url in enumerate(result.get("urls", [])):
            print(f"  {i+1}. {url[:80]}...")
        return 0
    else:
        print(f"\n✗ Failed: {result.get('error')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
