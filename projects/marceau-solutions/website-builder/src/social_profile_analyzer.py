#!/usr/bin/env python3
"""
social_profile_analyzer.py - Social Media Profile Analysis

Fetches and analyzes social media profiles to extract:
- Communication style and tone
- Topics and themes they discuss
- Visual brand preferences (colors, imagery)
- Personality traits
- Engagement patterns

Supports: X (Twitter), LinkedIn, Instagram (public data)

Usage:
    from social_profile_analyzer import analyze_social_profiles

    profiles = {
        "x": "https://x.com/username",
        "linkedin": "https://linkedin.com/in/username"
    }
    analysis = analyze_social_profiles(profiles)
"""

import os
import re
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from datetime import datetime
from urllib.parse import urlparse

import anthropic
from dotenv import load_dotenv

load_dotenv()


@dataclass
class SocialProfile:
    """Parsed social media profile information."""
    platform: str
    username: str
    url: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    followers: Optional[int] = None
    following: Optional[int] = None
    post_count: Optional[int] = None
    verified: bool = False
    profile_image_url: Optional[str] = None
    banner_image_url: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    joined_date: Optional[str] = None


@dataclass
class ContentAnalysis:
    """Analysis of social media content/posts."""
    topics: List[str] = field(default_factory=list)
    themes: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    mentions_style: str = ""  # how they interact with others
    content_types: List[str] = field(default_factory=list)  # text, images, videos, links
    posting_frequency: str = ""  # daily, weekly, sporadic
    engagement_level: str = ""  # high, medium, low
    sample_posts: List[str] = field(default_factory=list)


@dataclass
class CommunicationStyle:
    """Analyzed communication patterns."""
    tone: str  # professional, casual, inspirational, educational, humorous
    voice: str  # first person, third person, brand voice
    formality: str  # formal, semi-formal, informal
    emotion_level: str  # reserved, moderate, expressive
    key_phrases: List[str] = field(default_factory=list)
    vocabulary_level: str = ""  # simple, moderate, sophisticated
    sentence_structure: str = ""  # short and punchy, long and detailed, mixed


@dataclass
class VisualBrandAnalysis:
    """Visual branding preferences from social profiles."""
    dominant_colors: List[str] = field(default_factory=list)
    color_mood: str = ""  # warm, cool, neutral, bold, muted
    imagery_style: str = ""  # photography, graphics, mixed, minimal
    aesthetic: str = ""  # modern, classic, playful, professional
    logo_description: Optional[str] = None


@dataclass
class PersonalityTraits:
    """Inferred personality traits from social presence."""
    # Big Five traits (1-10 scale)
    openness: int = 5
    conscientiousness: int = 5
    extraversion: int = 5
    agreeableness: int = 5
    neuroticism: int = 5

    # Business-relevant traits
    authority_level: str = ""  # thought leader, peer, approachable expert
    trust_signals: List[str] = field(default_factory=list)
    values: List[str] = field(default_factory=list)
    motivations: List[str] = field(default_factory=list)


@dataclass
class SocialProfileAnalysis:
    """Complete analysis of all social profiles."""
    profiles: List[SocialProfile]
    content_analysis: ContentAnalysis
    communication_style: CommunicationStyle
    visual_brand: VisualBrandAnalysis
    personality: PersonalityTraits
    brand_summary: str
    website_recommendations: Dict[str, Any]
    analyzed_at: str


class SocialProfileAnalyzer:
    """
    Analyzes social media profiles for website personality matching.

    Uses a combination of URL parsing, public data fetching,
    and AI analysis to build a comprehensive profile.
    """

    PLATFORM_PATTERNS = {
        "x": [
            r"(?:https?://)?(?:www\.)?(?:twitter|x)\.com/([^/?]+)",
        ],
        "linkedin": [
            r"(?:https?://)?(?:www\.)?linkedin\.com/in/([^/?]+)",
            r"(?:https?://)?(?:www\.)?linkedin\.com/company/([^/?]+)",
        ],
        "instagram": [
            r"(?:https?://)?(?:www\.)?instagram\.com/([^/?]+)",
        ],
        "facebook": [
            r"(?:https?://)?(?:www\.)?facebook\.com/([^/?]+)",
        ],
        "youtube": [
            r"(?:https?://)?(?:www\.)?youtube\.com/@([^/?]+)",
            r"(?:https?://)?(?:www\.)?youtube\.com/c/([^/?]+)",
            r"(?:https?://)?(?:www\.)?youtube\.com/channel/([^/?]+)",
        ],
        "tiktok": [
            r"(?:https?://)?(?:www\.)?tiktok\.com/@([^/?]+)",
        ],
    }

    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.model = "claude-sonnet-4-20250514"

    def parse_profile_url(self, url: str) -> Optional[SocialProfile]:
        """
        Parse a social media URL to extract platform and username.

        Args:
            url: Social media profile URL

        Returns:
            SocialProfile with platform and username, or None if invalid
        """
        url = url.strip()

        for platform, patterns in self.PLATFORM_PATTERNS.items():
            for pattern in patterns:
                match = re.match(pattern, url, re.IGNORECASE)
                if match:
                    username = match.group(1)
                    # Clean username
                    username = username.rstrip("/").split("?")[0]
                    return SocialProfile(
                        platform=platform,
                        username=username,
                        url=url
                    )

        return None

    def parse_multiple_urls(self, urls: Dict[str, str]) -> List[SocialProfile]:
        """
        Parse multiple social media URLs.

        Args:
            urls: Dictionary of {platform: url} or {label: url}

        Returns:
            List of parsed SocialProfile objects
        """
        profiles = []

        for key, url in urls.items():
            if not url:
                continue

            profile = self.parse_profile_url(url)
            if profile:
                profiles.append(profile)
            else:
                # If URL parsing failed but we have a platform hint
                key_lower = key.lower()
                for platform in self.PLATFORM_PATTERNS.keys():
                    if platform in key_lower:
                        # Extract username from end of URL
                        parsed = urlparse(url)
                        username = parsed.path.strip("/").split("/")[-1]
                        if username:
                            profiles.append(SocialProfile(
                                platform=platform,
                                username=username,
                                url=url
                            ))
                        break

        return profiles

    def fetch_profile_data(
        self,
        profile: SocialProfile,
        additional_context: Optional[str] = None
    ) -> SocialProfile:
        """
        Fetch public profile data using web search.

        Note: This uses AI to search and synthesize public information.
        For production, you'd want direct API access where available.

        Args:
            profile: SocialProfile with platform and username
            additional_context: Optional context about the person/company

        Returns:
            Updated SocialProfile with fetched data
        """
        # Build search prompt
        search_prompt = f"""Research the {profile.platform} profile for username "{profile.username}".
URL: {profile.url}
{f"Additional context: {additional_context}" if additional_context else ""}

Find and extract:
1. Display name
2. Bio/description
3. Location (if available)
4. Website link (if available)
5. Approximate follower count
6. Recent post topics/themes
7. Any notable quotes or statements
8. Verification status

Return as JSON:
{{
    "display_name": "",
    "bio": "",
    "location": "",
    "website": "",
    "followers": null,
    "verified": false,
    "recent_topics": [],
    "notable_quotes": [],
    "profile_summary": ""
}}

If information is not available, use null or empty values."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": search_prompt}]
        )

        response_text = response.content[0].text

        try:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                data = json.loads(response_text[json_start:json_end])

                # Update profile with fetched data
                profile.display_name = data.get("display_name")
                profile.bio = data.get("bio")
                profile.location = data.get("location")
                profile.website = data.get("website")
                profile.followers = data.get("followers")
                profile.verified = data.get("verified", False)
        except json.JSONDecodeError:
            pass  # Keep original profile data

        return profile

    def analyze_communication_style(
        self,
        profiles: List[SocialProfile],
        sample_content: Optional[List[str]] = None
    ) -> CommunicationStyle:
        """
        Analyze communication style from profile data.

        Args:
            profiles: List of social profiles with data
            sample_content: Optional list of sample posts/content

        Returns:
            CommunicationStyle analysis
        """
        # Build context from profiles
        profile_context = "\n".join([
            f"- {p.platform}: @{p.username}\n  Bio: {p.bio or 'N/A'}"
            for p in profiles
        ])

        content_context = ""
        if sample_content:
            content_context = "\n\nSample content:\n" + "\n---\n".join(sample_content[:10])

        prompt = f"""Analyze the communication style of this person/brand based on their social media presence:

Profiles:
{profile_context}
{content_context}

Analyze and return JSON:
{{
    "tone": "professional|casual|inspirational|educational|humorous|authoritative|friendly",
    "voice": "first_person|third_person|brand_voice|mixed",
    "formality": "formal|semi_formal|informal",
    "emotion_level": "reserved|moderate|expressive",
    "key_phrases": ["phrase1", "phrase2"],
    "vocabulary_level": "simple|moderate|sophisticated",
    "sentence_structure": "short_punchy|long_detailed|mixed"
}}"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text

        try:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            data = json.loads(response_text[json_start:json_end])

            return CommunicationStyle(
                tone=data.get("tone", "professional"),
                voice=data.get("voice", "mixed"),
                formality=data.get("formality", "semi_formal"),
                emotion_level=data.get("emotion_level", "moderate"),
                key_phrases=data.get("key_phrases", []),
                vocabulary_level=data.get("vocabulary_level", "moderate"),
                sentence_structure=data.get("sentence_structure", "mixed")
            )
        except json.JSONDecodeError:
            return CommunicationStyle(
                tone="professional",
                voice="mixed",
                formality="semi_formal",
                emotion_level="moderate"
            )

    def analyze_personality(
        self,
        profiles: List[SocialProfile],
        communication_style: CommunicationStyle
    ) -> PersonalityTraits:
        """
        Infer personality traits from social presence.

        Args:
            profiles: Social profiles with data
            communication_style: Analyzed communication patterns

        Returns:
            PersonalityTraits analysis
        """
        profile_context = "\n".join([
            f"- {p.platform}: {p.bio or 'No bio'}"
            for p in profiles
        ])

        prompt = f"""Based on this social media presence, analyze the personality:

Profiles:
{profile_context}

Communication style:
- Tone: {communication_style.tone}
- Voice: {communication_style.voice}
- Formality: {communication_style.formality}
- Key phrases: {', '.join(communication_style.key_phrases)}

Return JSON with personality analysis:
{{
    "openness": 1-10,
    "conscientiousness": 1-10,
    "extraversion": 1-10,
    "agreeableness": 1-10,
    "neuroticism": 1-10,
    "authority_level": "thought_leader|expert|peer|approachable_expert",
    "trust_signals": ["signal1", "signal2"],
    "values": ["value1", "value2", "value3"],
    "motivations": ["motivation1", "motivation2"]
}}

Base scores on evidence from their social presence."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text

        try:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            data = json.loads(response_text[json_start:json_end])

            return PersonalityTraits(
                openness=data.get("openness", 5),
                conscientiousness=data.get("conscientiousness", 5),
                extraversion=data.get("extraversion", 5),
                agreeableness=data.get("agreeableness", 5),
                neuroticism=data.get("neuroticism", 5),
                authority_level=data.get("authority_level", "expert"),
                trust_signals=data.get("trust_signals", []),
                values=data.get("values", []),
                motivations=data.get("motivations", [])
            )
        except json.JSONDecodeError:
            return PersonalityTraits()

    def generate_website_recommendations(
        self,
        profiles: List[SocialProfile],
        communication_style: CommunicationStyle,
        personality: PersonalityTraits
    ) -> Dict[str, Any]:
        """
        Generate website recommendations based on social analysis.

        Args:
            profiles: Analyzed social profiles
            communication_style: Communication style analysis
            personality: Personality analysis

        Returns:
            Dictionary of website recommendations
        """
        prompt = f"""Based on this social media analysis, recommend website design:

Communication Style:
- Tone: {communication_style.tone}
- Formality: {communication_style.formality}
- Emotion level: {communication_style.emotion_level}

Personality:
- Authority: {personality.authority_level}
- Values: {', '.join(personality.values)}
- Extraversion: {personality.extraversion}/10
- Openness: {personality.openness}/10

Generate website recommendations as JSON:
{{
    "template_style": "modern_minimal|bold_creative|professional_corporate|warm_friendly|luxury_elegant|tech_forward",
    "color_palette": {{
        "primary": "#hex",
        "secondary": "#hex",
        "accent": "#hex",
        "background": "#hex",
        "text": "#hex"
    }},
    "typography": {{
        "heading_style": "bold_sans|elegant_serif|modern_geometric|playful|professional",
        "body_style": "clean_readable|sophisticated|casual"
    }},
    "imagery_style": "photography|illustrations|abstract|minimal|mixed",
    "layout_style": "spacious|compact|asymmetric|grid_based",
    "animation_level": "none|subtle|moderate|dynamic",
    "cta_style": "bold_buttons|subtle_links|rounded_pills|sharp_corners",
    "overall_mood": "describe the feeling the site should evoke",
    "copy_guidelines": {{
        "headline_style": "direct|clever|emotional|benefit_focused",
        "paragraph_length": "short|medium|long",
        "use_of_emoji": true/false,
        "exclamation_frequency": "none|rare|occasional|frequent"
    }}
}}

Match the website personality to their social media personality."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text

        try:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            return json.loads(response_text[json_start:json_end])
        except json.JSONDecodeError:
            return {
                "template_style": "professional_corporate",
                "color_palette": {
                    "primary": "#1a1a2e",
                    "secondary": "#667eea",
                    "accent": "#4ade80",
                    "background": "#ffffff",
                    "text": "#1f2937"
                },
                "typography": {
                    "heading_style": "bold_sans",
                    "body_style": "clean_readable"
                },
                "imagery_style": "photography",
                "layout_style": "spacious",
                "animation_level": "subtle",
                "cta_style": "rounded_pills",
                "overall_mood": "Professional and trustworthy",
                "copy_guidelines": {
                    "headline_style": "benefit_focused",
                    "paragraph_length": "medium",
                    "use_of_emoji": False,
                    "exclamation_frequency": "rare"
                }
            }

    def analyze_profiles(
        self,
        profile_urls: Dict[str, str],
        company_name: Optional[str] = None,
        owner_name: Optional[str] = None,
        fetch_data: bool = True
    ) -> SocialProfileAnalysis:
        """
        Complete analysis of all provided social profiles.

        Args:
            profile_urls: Dictionary of {platform: url} or {label: url}
            company_name: Optional company name for context
            owner_name: Optional owner name for context
            fetch_data: Whether to fetch additional profile data

        Returns:
            Complete SocialProfileAnalysis
        """
        # Parse URLs
        profiles = self.parse_multiple_urls(profile_urls)

        if not profiles:
            raise ValueError("No valid social media URLs provided")

        # Build context
        context = ""
        if company_name:
            context += f"Company: {company_name}. "
        if owner_name:
            context += f"Owner: {owner_name}."

        # Fetch profile data
        if fetch_data:
            for profile in profiles:
                profile = self.fetch_profile_data(profile, context)

        # Analyze communication style
        communication_style = self.analyze_communication_style(profiles)

        # Analyze personality
        personality = self.analyze_personality(profiles, communication_style)

        # Generate website recommendations
        recommendations = self.generate_website_recommendations(
            profiles, communication_style, personality
        )

        # Generate brand summary
        brand_summary = self._generate_brand_summary(
            profiles, communication_style, personality
        )

        return SocialProfileAnalysis(
            profiles=profiles,
            content_analysis=ContentAnalysis(),  # Populated if we have actual post data
            communication_style=communication_style,
            visual_brand=VisualBrandAnalysis(),  # Populated if we have visual analysis
            personality=personality,
            brand_summary=brand_summary,
            website_recommendations=recommendations,
            analyzed_at=datetime.now().isoformat()
        )

    def _generate_brand_summary(
        self,
        profiles: List[SocialProfile],
        communication_style: CommunicationStyle,
        personality: PersonalityTraits
    ) -> str:
        """Generate a concise brand summary."""
        prompt = f"""Write a 2-3 sentence brand personality summary based on:

Social profiles: {', '.join([f'{p.platform}: @{p.username}' for p in profiles])}
Bios: {'; '.join([p.bio or 'N/A' for p in profiles])}
Tone: {communication_style.tone}
Authority: {personality.authority_level}
Values: {', '.join(personality.values)}

Write as if describing the brand to a web designer. Be specific and actionable."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    def to_dict(self, analysis: SocialProfileAnalysis) -> Dict[str, Any]:
        """Convert analysis to dictionary."""
        return {
            "profiles": [asdict(p) for p in analysis.profiles],
            "content_analysis": asdict(analysis.content_analysis),
            "communication_style": asdict(analysis.communication_style),
            "visual_brand": asdict(analysis.visual_brand),
            "personality": asdict(analysis.personality),
            "brand_summary": analysis.brand_summary,
            "website_recommendations": analysis.website_recommendations,
            "analyzed_at": analysis.analyzed_at
        }


# Convenience function
def analyze_social_profiles(
    profile_urls: Dict[str, str],
    company_name: Optional[str] = None,
    owner_name: Optional[str] = None
) -> SocialProfileAnalysis:
    """Analyze social media profiles for website generation."""
    analyzer = SocialProfileAnalyzer()
    return analyzer.analyze_profiles(profile_urls, company_name, owner_name)


if __name__ == "__main__":
    import sys

    # Test with sample URLs
    test_urls = {
        "x": "https://x.com/example",
        "linkedin": "https://linkedin.com/in/example"
    }

    if len(sys.argv) > 1:
        # Parse command line URLs
        test_urls = {}
        for arg in sys.argv[1:]:
            if "twitter.com" in arg or "x.com" in arg:
                test_urls["x"] = arg
            elif "linkedin.com" in arg:
                test_urls["linkedin"] = arg
            elif "instagram.com" in arg:
                test_urls["instagram"] = arg

    print(f"Analyzing profiles: {test_urls}")

    analyzer = SocialProfileAnalyzer()
    result = analyzer.analyze_profiles(test_urls, fetch_data=True)

    print("\n" + "=" * 60)
    print("SOCIAL PROFILE ANALYSIS")
    print("=" * 60)
    print(json.dumps(analyzer.to_dict(result), indent=2))
