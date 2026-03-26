#!/usr/bin/env python3
"""
Brand Research Module for Fitness Influencer AI Assistant

Researches social media profiles to extract brand identity, visual style,
content themes, and audience characteristics. Creates a brand profile that
can be used to personalize ad creation and content generation.

Approach: Hybrid web fetch + AI analysis
"""

import os
import json
import re
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

# Brand profiles storage
BRAND_PROFILES_DIR = Path(__file__).parent / "brand_profiles"
BRAND_PROFILES_DIR.mkdir(exist_ok=True)


class BrandResearcher:
    """
    Research and analyze fitness influencer brands from social media.
    Creates comprehensive brand profiles for personalized content creation.
    """

    def __init__(self, anthropic_key: str = None):
        """Initialize with API keys."""
        self.anthropic_key = anthropic_key or os.getenv('ANTHROPIC_API_KEY')

    async def research_brand(
        self,
        handle: str,
        platforms: List[str] = None
    ) -> Dict[str, Any]:
        """
        Research a brand across social media platforms.

        Args:
            handle: Social media handle (e.g., "boabfit", "@boabfit")
            platforms: List of platforms to research (default: instagram, tiktok)

        Returns:
            Brand profile dict with visual style, tone, audience, etc.
        """
        # Clean handle
        handle = handle.strip().lstrip('@').lower()
        platforms = platforms or ["instagram", "tiktok"]

        print(f"[BrandResearch] Researching @{handle} on {platforms}")

        # Gather raw data from each platform
        raw_data = {}
        for platform in platforms:
            try:
                if platform == "instagram":
                    raw_data["instagram"] = await self._fetch_instagram_data(handle)
                elif platform == "tiktok":
                    raw_data["tiktok"] = await self._fetch_tiktok_data(handle)
                elif platform == "youtube":
                    raw_data["youtube"] = await self._fetch_youtube_data(handle)
            except Exception as e:
                print(f"[BrandResearch] Error fetching {platform}: {e}")
                raw_data[platform] = {"error": str(e)}

        # Use Claude to analyze and create brand profile
        brand_profile = await self._analyze_with_ai(handle, raw_data)

        # Save profile
        self._save_profile(handle, brand_profile)

        return brand_profile

    async def _fetch_instagram_data(self, handle: str) -> Dict[str, Any]:
        """
        Fetch public Instagram profile data.
        Uses web scraping approach for public profiles.
        """
        try:
            # Try to fetch public profile page
            url = f"https://www.instagram.com/{handle}/"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                return {"error": f"Profile not accessible (status {response.status_code})"}

            html = response.text

            # Extract basic info from meta tags
            data = {
                "platform": "instagram",
                "handle": handle,
                "url": url,
            }

            # Try to extract description from meta
            desc_match = re.search(r'<meta property="og:description" content="([^"]+)"', html)
            if desc_match:
                data["bio_snippet"] = desc_match.group(1)

            # Try to extract follower count from description
            follower_match = re.search(r'([\d,.]+[KMB]?)\s*Followers', data.get("bio_snippet", ""), re.IGNORECASE)
            if follower_match:
                data["followers"] = follower_match.group(1)

            # Extract title
            title_match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
            if title_match:
                data["display_name"] = title_match.group(1).split("•")[0].strip()

            return data

        except Exception as e:
            return {"error": str(e), "platform": "instagram"}

    async def _fetch_tiktok_data(self, handle: str) -> Dict[str, Any]:
        """Fetch public TikTok profile data."""
        try:
            url = f"https://www.tiktok.com/@{handle}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            }

            response = requests.get(url, headers=headers, timeout=10)

            data = {
                "platform": "tiktok",
                "handle": handle,
                "url": url,
                "accessible": response.status_code == 200
            }

            if response.status_code == 200:
                html = response.text
                # Extract meta description
                desc_match = re.search(r'<meta name="description" content="([^"]+)"', html)
                if desc_match:
                    data["bio_snippet"] = desc_match.group(1)

            return data

        except Exception as e:
            return {"error": str(e), "platform": "tiktok"}

    async def _fetch_youtube_data(self, handle: str) -> Dict[str, Any]:
        """Fetch public YouTube channel data."""
        try:
            # Try both @handle and /c/handle formats
            url = f"https://www.youtube.com/@{handle}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            }

            response = requests.get(url, headers=headers, timeout=10)

            data = {
                "platform": "youtube",
                "handle": handle,
                "url": url,
                "accessible": response.status_code == 200
            }

            return data

        except Exception as e:
            return {"error": str(e), "platform": "youtube"}

    async def _analyze_with_ai(
        self,
        handle: str,
        raw_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use Claude to analyze raw data and create comprehensive brand profile.
        """
        if not self.anthropic_key:
            return self._create_fallback_profile(handle, raw_data)

        analysis_prompt = f"""You are a brand analyst specializing in fitness influencers. Analyze the following social media data and create a comprehensive brand profile.

SOCIAL MEDIA HANDLE: @{handle}

RAW DATA FROM PLATFORMS:
{json.dumps(raw_data, indent=2)}

Based on this data (and your knowledge if you're familiar with this influencer), create a detailed brand profile. If you don't have enough data, make reasonable inferences for a fitness influencer brand.

OUTPUT FORMAT - Return a JSON object with this exact structure:
{{
    "brand_name": "Display name or brand name",
    "handle": "{handle}",
    "tagline": "Their main message or tagline if known",
    "brand_voice": {{
        "tone": "e.g., motivational, casual, professional, edgy",
        "personality": "e.g., friendly coach, hardcore athlete, wellness guru",
        "key_phrases": ["phrases they might use"],
        "emoji_style": "heavy, moderate, minimal, none"
    }},
    "visual_style": {{
        "color_palette": ["primary color", "secondary color", "accent"],
        "aesthetic": "e.g., clean/minimal, bold/vibrant, dark/moody, natural/earthy",
        "photography_style": "e.g., professional studio, lifestyle, raw/authentic",
        "typography_preference": "e.g., bold sans-serif, elegant script, modern minimal"
    }},
    "content_themes": {{
        "primary_topics": ["main content topics"],
        "content_types": ["e.g., workouts, nutrition tips, motivation, vlogs"],
        "posting_style": "e.g., educational, entertaining, inspirational"
    }},
    "target_audience": {{
        "demographics": "e.g., women 25-40, men 18-35, all fitness levels",
        "fitness_level": "e.g., beginners, intermediate, advanced, all levels",
        "interests": ["related interests beyond fitness"]
    }},
    "brand_values": ["3-5 core values"],
    "unique_differentiator": "What makes this brand stand out",
    "ad_recommendations": {{
        "best_formats": ["e.g., short-form video, carousel, story"],
        "messaging_angle": "Recommended approach for ads",
        "call_to_action_style": "e.g., direct, soft, urgency-based"
    }},
    "confidence_score": 0.0 to 1.0 based on data quality
}}

Return ONLY the JSON object, no other text."""

        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": analysis_prompt}]
                },
                timeout=30
            )

            if response.status_code != 200:
                print(f"[BrandResearch] AI analysis failed: {response.status_code}")
                return self._create_fallback_profile(handle, raw_data)

            result = response.json()
            content = result["content"][0]["text"]

            # Parse JSON from response
            try:
                # Try to extract JSON if wrapped in markdown
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    profile = json.loads(json_match.group())
                else:
                    profile = json.loads(content)

                # Add metadata
                profile["_metadata"] = {
                    "researched_at": datetime.now().isoformat(),
                    "platforms_checked": list(raw_data.keys()),
                    "raw_data_available": {k: "error" not in v for k, v in raw_data.items()}
                }

                return profile

            except json.JSONDecodeError as e:
                print(f"[BrandResearch] JSON parse error: {e}")
                return self._create_fallback_profile(handle, raw_data)

        except Exception as e:
            print(f"[BrandResearch] AI analysis error: {e}")
            return self._create_fallback_profile(handle, raw_data)

    def _create_fallback_profile(
        self,
        handle: str,
        raw_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a basic profile when AI analysis isn't available."""
        return {
            "brand_name": handle.title(),
            "handle": handle,
            "tagline": "Fitness & Wellness",
            "brand_voice": {
                "tone": "motivational",
                "personality": "fitness coach",
                "key_phrases": ["Let's go!", "You got this!", "Transform your body"],
                "emoji_style": "moderate"
            },
            "visual_style": {
                "color_palette": ["#000000", "#FFD700", "#FFFFFF"],
                "aesthetic": "bold/vibrant",
                "photography_style": "lifestyle",
                "typography_preference": "bold sans-serif"
            },
            "content_themes": {
                "primary_topics": ["workouts", "nutrition", "motivation"],
                "content_types": ["workout videos", "tips", "transformations"],
                "posting_style": "inspirational"
            },
            "target_audience": {
                "demographics": "fitness enthusiasts 18-45",
                "fitness_level": "all levels",
                "interests": ["health", "wellness", "self-improvement"]
            },
            "brand_values": ["consistency", "hard work", "transformation", "community"],
            "unique_differentiator": "Authentic fitness journey",
            "ad_recommendations": {
                "best_formats": ["short-form video", "carousel"],
                "messaging_angle": "transformation and results",
                "call_to_action_style": "motivational"
            },
            "confidence_score": 0.3,
            "_metadata": {
                "researched_at": datetime.now().isoformat(),
                "platforms_checked": list(raw_data.keys()),
                "note": "Fallback profile - limited data available"
            }
        }

    def _save_profile(self, handle: str, profile: Dict[str, Any]) -> None:
        """Save brand profile to disk."""
        filepath = BRAND_PROFILES_DIR / f"{handle}.json"
        with open(filepath, "w") as f:
            json.dump(profile, f, indent=2)
        print(f"[BrandResearch] Profile saved: {filepath}")

    def get_profile(self, handle: str) -> Optional[Dict[str, Any]]:
        """Load an existing brand profile."""
        handle = handle.strip().lstrip('@').lower()
        filepath = BRAND_PROFILES_DIR / f"{handle}.json"

        if filepath.exists():
            with open(filepath) as f:
                return json.load(f)
        return None

    def list_profiles(self) -> List[str]:
        """List all saved brand profiles."""
        return [f.stem for f in BRAND_PROFILES_DIR.glob("*.json")]

    def delete_profile(self, handle: str) -> bool:
        """Delete a brand profile."""
        handle = handle.strip().lstrip('@').lower()
        filepath = BRAND_PROFILES_DIR / f"{handle}.json"

        if filepath.exists():
            filepath.unlink()
            return True
        return False


# Singleton instance
_researcher = None


def get_researcher() -> BrandResearcher:
    """Get or create researcher instance."""
    global _researcher
    if _researcher is None:
        _researcher = BrandResearcher()
    return _researcher


async def research_brand(handle: str, platforms: List[str] = None) -> Dict[str, Any]:
    """
    Convenience function to research a brand.

    Args:
        handle: Social media handle (e.g., "boabfit")
        platforms: Platforms to check (default: instagram, tiktok)

    Returns:
        Brand profile dict
    """
    researcher = get_researcher()
    return await researcher.research_brand(handle, platforms)


def get_brand_profile(handle: str) -> Optional[Dict[str, Any]]:
    """Get an existing brand profile."""
    researcher = get_researcher()
    return researcher.get_profile(handle)


def format_brand_profile_for_display(profile: Dict[str, Any]) -> str:
    """Format a brand profile as readable text for chat display."""
    if not profile:
        return "No brand profile found."

    lines = [
        f"**Brand Profile: {profile.get('brand_name', profile.get('handle', 'Unknown'))}**",
        f"Handle: @{profile.get('handle', 'unknown')}",
        "",
        f"**Tagline:** {profile.get('tagline', 'N/A')}",
        "",
        "**Brand Voice:**",
        f"  - Tone: {profile.get('brand_voice', {}).get('tone', 'N/A')}",
        f"  - Personality: {profile.get('brand_voice', {}).get('personality', 'N/A')}",
        "",
        "**Visual Style:**",
        f"  - Aesthetic: {profile.get('visual_style', {}).get('aesthetic', 'N/A')}",
        f"  - Colors: {', '.join(profile.get('visual_style', {}).get('color_palette', []))}",
        f"  - Photography: {profile.get('visual_style', {}).get('photography_style', 'N/A')}",
        "",
        "**Content Themes:**",
        f"  - Topics: {', '.join(profile.get('content_themes', {}).get('primary_topics', []))}",
        f"  - Style: {profile.get('content_themes', {}).get('posting_style', 'N/A')}",
        "",
        "**Target Audience:**",
        f"  - Demographics: {profile.get('target_audience', {}).get('demographics', 'N/A')}",
        f"  - Fitness Level: {profile.get('target_audience', {}).get('fitness_level', 'N/A')}",
        "",
        f"**Brand Values:** {', '.join(profile.get('brand_values', []))}",
        "",
        f"**Unique Differentiator:** {profile.get('unique_differentiator', 'N/A')}",
        "",
        "**Ad Recommendations:**",
        f"  - Best Formats: {', '.join(profile.get('ad_recommendations', {}).get('best_formats', []))}",
        f"  - Messaging: {profile.get('ad_recommendations', {}).get('messaging_angle', 'N/A')}",
        "",
        f"_Confidence: {profile.get('confidence_score', 0) * 100:.0f}%_",
    ]

    return "\n".join(lines)
