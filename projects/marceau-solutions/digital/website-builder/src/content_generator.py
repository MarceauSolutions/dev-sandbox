#!/usr/bin/env python3
"""
content_generator.py - AI-Powered Website Copywriting

Generates all website content based on research data and brand personality:
- Headlines and taglines matching brand voice
- About section with authentic storytelling
- Services descriptions with appropriate tone
- Call-to-action text that converts
- Meta descriptions for SEO

Enhanced with personality-driven content generation:
- Uses brand voice settings (tone, formality, emotion)
- Applies content strategy (headline style, paragraph style)
- Matches communication patterns from social analysis

Usage:
    from content_generator import generate_content, generate_personality_content
    from research_engine import research_with_social

    # Basic generation
    research = research_company("Company", "Owner")
    content = generate_content(research)

    # Personality-driven generation
    research = research_with_social("Company", "Owner", social_profiles)
    content = generate_personality_content(research)
"""

import os
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

import anthropic
from dotenv import load_dotenv

load_dotenv()


@dataclass
class HeroContent:
    """Hero section content."""
    headline: str
    subheadline: str
    cta_primary: str
    cta_secondary: str


@dataclass
class AboutContent:
    """About section content."""
    title: str
    story: str
    mission: str
    founder_bio: str


@dataclass
class ServiceContent:
    """Individual service content."""
    name: str
    description: str
    benefits: List[str]
    icon_suggestion: str


@dataclass
class TestimonialContent:
    """Testimonial content (generated/placeholder)."""
    quote: str
    author: str
    title: str


@dataclass
class ContactContent:
    """Contact section content."""
    title: str
    subtitle: str
    cta: str


@dataclass
class SEOContent:
    """SEO metadata."""
    title: str
    description: str
    keywords: List[str]


@dataclass
class WebsiteContent:
    """Complete website content."""
    hero: HeroContent
    about: AboutContent
    services: List[ServiceContent]
    testimonials: List[TestimonialContent]
    contact: ContactContent
    seo: SEOContent
    footer_tagline: str


class ContentGenerator:
    """
    AI-powered content generator for websites.

    Uses Claude to generate compelling, industry-appropriate
    copy for all website sections.
    """

    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.model = "claude-sonnet-4-20250514"

    def generate_content(self, research: Dict[str, Any]) -> WebsiteContent:
        """
        Generate all website content from research data.

        Args:
            research: Dictionary from ResearchEngine.to_dict()

        Returns:
            WebsiteContent with all sections
        """

        company = research.get("company", {})
        owner = research.get("owner", {})
        tone = research.get("tone", "professional")

        prompt = f"""Generate compelling website content for the following business:

## Business Information
- Name: {company.get('name', 'Business')}
- Industry: {company.get('industry', 'General')}
- Location: {company.get('location', '')}
- Description: {company.get('description', '')}
- Services: {', '.join(company.get('services', []))}
- Target Audience: {company.get('target_audience', '')}
- Unique Selling Points: {', '.join(company.get('unique_selling_points', []))}

## Owner Information
- Name: {owner.get('name', '')}
- Title: {owner.get('title', 'Owner')}
- Background: {owner.get('background', '')}
- Expertise: {', '.join(owner.get('expertise', []))}

## Content Requirements
- Tone: {tone}
- Style: Engaging, clear, action-oriented
- Focus: Benefits over features
- Length: Concise but impactful

Generate content in this exact JSON format:
{{
    "hero": {{
        "headline": "Powerful headline (6-10 words)",
        "subheadline": "Supporting text explaining value proposition (15-25 words)",
        "cta_primary": "Primary button text (2-4 words)",
        "cta_secondary": "Secondary button text (2-4 words)"
    }},
    "about": {{
        "title": "About section title",
        "story": "Company story paragraph (50-100 words)",
        "mission": "Mission statement (20-40 words)",
        "founder_bio": "Founder bio paragraph (40-80 words)"
    }},
    "services": [
        {{
            "name": "Service name",
            "description": "Service description (20-40 words)",
            "benefits": ["Benefit 1", "Benefit 2", "Benefit 3"],
            "icon_suggestion": "icon name (e.g., 'dumbbell', 'chart', 'users')"
        }}
    ],
    "testimonials": [
        {{
            "quote": "Testimonial quote (20-40 words)",
            "author": "Customer Name",
            "title": "Customer title/description"
        }}
    ],
    "contact": {{
        "title": "Contact section title",
        "subtitle": "Encouraging text (10-20 words)",
        "cta": "Form submit button text"
    }},
    "seo": {{
        "title": "Page title for browser tab (50-60 chars)",
        "description": "Meta description (150-160 chars)",
        "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
    }},
    "footer_tagline": "Short tagline for footer (5-10 words)"
}}

Generate 3-5 services based on what the business offers.
Generate 3 realistic-sounding testimonials (these are placeholders to be replaced with real ones).
Make all content specific to this business, not generic.
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text

        # Parse JSON from response
        try:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                data = json.loads(response_text[json_start:json_end])
            else:
                raise ValueError("No JSON found")
        except json.JSONDecodeError:
            data = self._create_fallback_content(company, owner)

        # Build structured content
        return WebsiteContent(
            hero=HeroContent(**data.get("hero", {})),
            about=AboutContent(**data.get("about", {})),
            services=[ServiceContent(**s) for s in data.get("services", [])],
            testimonials=[TestimonialContent(**t) for t in data.get("testimonials", [])],
            contact=ContactContent(**data.get("contact", {})),
            seo=SEOContent(**data.get("seo", {})),
            footer_tagline=data.get("footer_tagline", f"© {company.get('name', 'Company')}")
        )

    def _create_fallback_content(
        self,
        company: Dict[str, Any],
        owner: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create fallback content if generation fails."""
        name = company.get("name", "Our Company")
        return {
            "hero": {
                "headline": f"Welcome to {name}",
                "subheadline": "We're here to help you succeed.",
                "cta_primary": "Get Started",
                "cta_secondary": "Learn More"
            },
            "about": {
                "title": f"About {name}",
                "story": f"{name} was founded with a mission to serve our community.",
                "mission": "Our mission is to provide exceptional service.",
                "founder_bio": f"Founded by {owner.get('name', 'our team')}."
            },
            "services": [],
            "testimonials": [],
            "contact": {
                "title": "Get In Touch",
                "subtitle": "We'd love to hear from you.",
                "cta": "Send Message"
            },
            "seo": {
                "title": name,
                "description": f"{name} - Your trusted partner.",
                "keywords": [name.lower()]
            },
            "footer_tagline": f"© {name}"
        }

    def to_dict(self, content: WebsiteContent) -> Dict[str, Any]:
        """Convert content to dictionary."""
        return {
            "hero": asdict(content.hero),
            "about": asdict(content.about),
            "services": [asdict(s) for s in content.services],
            "testimonials": [asdict(t) for t in content.testimonials],
            "contact": asdict(content.contact),
            "seo": asdict(content.seo),
            "footer_tagline": content.footer_tagline
        }

    def generate_personality_content(self, research: Dict[str, Any]) -> WebsiteContent:
        """
        Generate website content using brand personality data.

        Uses the synthesized brand personality to create content that
        authentically matches the brand's voice and style.

        Args:
            research: Dictionary from ResearchEngine.to_dict() with brand_personality

        Returns:
            WebsiteContent with personality-matched copy
        """
        company = research.get("company", {})
        owner = research.get("owner", {})
        tone = research.get("tone", "professional")

        # Get brand personality if available
        personality = research.get("brand_personality", {})
        voice = personality.get("voice", {}) if personality else {}
        content_strategy = personality.get("content_strategy", {}) if personality else {}

        # Build detailed voice instructions
        voice_instructions = self._build_voice_instructions(voice, content_strategy)

        # Build personality context
        personality_context = ""
        if personality:
            personality_context = f"""
## Brand Personality
- Brand Name: {personality.get('brand_name', company.get('name', 'Company'))}
- Tagline: {personality.get('tagline', '')}
- Elevator Pitch: {personality.get('elevator_pitch', '')}
- Primary Audience: {personality.get('primary_audience', '')}
- Key Differentiators: {', '.join(personality.get('key_differentiators', []))}

## Audience Insights
- Pain Points: {', '.join(personality.get('audience_pain_points', []))}
- Desires: {', '.join(personality.get('audience_desires', []))}

## Voice & Tone Guidelines
{voice_instructions}
"""

        prompt = f"""Generate compelling website content that PERFECTLY matches this brand's personality and voice:

## Business Information
- Name: {company.get('name', 'Business')}
- Industry: {company.get('industry', 'General')}
- Location: {company.get('location', '')}
- Description: {company.get('description', '')}
- Services: {', '.join(company.get('services', []))}
- Target Audience: {company.get('target_audience', '')}
- Unique Selling Points: {', '.join(company.get('unique_selling_points', []))}

## Owner Information
- Name: {owner.get('name', '')}
- Title: {owner.get('title', 'Owner')}
- Background: {owner.get('background', '')}
- Expertise: {', '.join(owner.get('expertise', []))}
{personality_context}

## CRITICAL VOICE GUIDELINES
The content MUST:
1. Match the exact tone and formality specified
2. Use the specified sentence structure
3. Follow the headline and CTA style guidelines
4. Reflect the brand's authentic personality
5. Address the audience's pain points and desires
6. Highlight the key differentiators naturally

Generate content in this exact JSON format:
{{
    "hero": {{
        "headline": "Powerful headline matching brand voice",
        "subheadline": "Supporting text that reinforces value proposition",
        "cta_primary": "Primary button matching CTA style",
        "cta_secondary": "Secondary button text"
    }},
    "about": {{
        "title": "About section title",
        "story": "Company story that feels authentic to the brand voice (50-100 words)",
        "mission": "Mission statement matching formality level (20-40 words)",
        "founder_bio": "Founder bio that reflects their personality (40-80 words)"
    }},
    "services": [
        {{
            "name": "Service name",
            "description": "Service description in brand voice (20-40 words)",
            "benefits": ["Benefit 1", "Benefit 2", "Benefit 3"],
            "icon_suggestion": "icon name"
        }}
    ],
    "testimonials": [
        {{
            "quote": "Testimonial that sounds like a real customer (20-40 words)",
            "author": "Customer Name",
            "title": "Customer title"
        }}
    ],
    "contact": {{
        "title": "Contact section title matching brand voice",
        "subtitle": "Encouraging text (10-20 words)",
        "cta": "Form submit button matching CTA style"
    }},
    "seo": {{
        "title": "Page title for browser tab (50-60 chars)",
        "description": "Meta description (150-160 chars)",
        "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
    }},
    "footer_tagline": "Short tagline matching brand voice (5-10 words)"
}}

Generate 3-5 services based on what the business offers.
Generate 3 testimonials that sound authentic to the target audience.
Make ALL content specific to this brand's voice - not generic."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text

        # Parse JSON from response
        try:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                data = json.loads(response_text[json_start:json_end])
            else:
                raise ValueError("No JSON found")
        except json.JSONDecodeError:
            data = self._create_fallback_content(company, owner)

        # Build structured content
        return WebsiteContent(
            hero=HeroContent(**data.get("hero", {})),
            about=AboutContent(**data.get("about", {})),
            services=[ServiceContent(**s) for s in data.get("services", [])],
            testimonials=[TestimonialContent(**t) for t in data.get("testimonials", [])],
            contact=ContactContent(**data.get("contact", {})),
            seo=SEOContent(**data.get("seo", {})),
            footer_tagline=data.get("footer_tagline", f"© {company.get('name', 'Company')}")
        )

    def _build_voice_instructions(
        self,
        voice: Dict[str, Any],
        content_strategy: Dict[str, Any]
    ) -> str:
        """Build detailed voice instructions from personality data."""
        if not voice and not content_strategy:
            return "- Tone: professional\n- Style: clear and engaging"

        instructions = []

        # Voice attributes
        if voice:
            if voice.get("tone"):
                instructions.append(f"- Tone: {voice['tone']}")

            if voice.get("personality_adjectives"):
                instructions.append(f"- Brand personality: {', '.join(voice['personality_adjectives'])}")

            if voice.get("speaking_style"):
                style_map = {
                    "first_person": "Use 'I' and 'my' (personal, direct)",
                    "third_person": "Use company name and 'they' (formal)",
                    "we_voice": "Use 'we' and 'our' (team-oriented)"
                }
                instructions.append(f"- Voice: {style_map.get(voice['speaking_style'], voice['speaking_style'])}")

            formality = voice.get("formality_level", 5)
            if formality <= 3:
                instructions.append("- Formality: Casual, conversational, relaxed")
            elif formality <= 6:
                instructions.append("- Formality: Semi-formal, approachable yet professional")
            else:
                instructions.append("- Formality: Formal, polished, corporate")

            emotion = voice.get("emotion_intensity", 5)
            if emotion <= 3:
                instructions.append("- Emotion: Reserved, factual, understated")
            elif emotion <= 6:
                instructions.append("- Emotion: Moderate warmth, balanced")
            else:
                instructions.append("- Emotion: Expressive, enthusiastic, passionate")

            if voice.get("sentence_length"):
                length_map = {
                    "short": "Short, punchy sentences. Direct and impactful.",
                    "medium": "Medium-length sentences. Clear and readable.",
                    "long": "Longer, detailed sentences. Thoughtful and comprehensive.",
                    "varied": "Mix of sentence lengths for rhythm and engagement."
                }
                instructions.append(f"- Sentences: {length_map.get(voice['sentence_length'], '')}")

            if voice.get("use_emojis"):
                instructions.append("- Emojis: Use sparingly for emphasis")
            else:
                instructions.append("- Emojis: Do NOT use emojis")

            exclaim = voice.get("exclamation_frequency", "rare")
            exclaim_map = {
                "never": "Never use exclamation marks",
                "rare": "Rarely use exclamation marks (max 1-2 per page)",
                "occasional": "Occasional exclamation marks for emphasis",
                "frequent": "Use exclamation marks for energy and enthusiasm"
            }
            instructions.append(f"- Punctuation: {exclaim_map.get(exclaim, '')}")

            if voice.get("key_phrases"):
                instructions.append(f"- Key phrases to incorporate: {', '.join(voice['key_phrases'][:5])}")

            if voice.get("primary_message"):
                instructions.append(f"- Primary message: {voice['primary_message']}")

            if voice.get("value_proposition"):
                instructions.append(f"- Value proposition: {voice['value_proposition']}")

        # Content strategy
        if content_strategy:
            if content_strategy.get("headline_style"):
                style_map = {
                    "direct": "Headlines should be direct and clear",
                    "clever": "Headlines can be clever/witty",
                    "emotional": "Headlines should evoke emotion",
                    "benefit_focused": "Headlines should lead with benefits",
                    "question": "Headlines can pose questions to engage"
                }
                instructions.append(f"- Headlines: {style_map.get(content_strategy['headline_style'], '')}")

            if content_strategy.get("cta_style"):
                cta_map = {
                    "action_verb": "CTAs should start with action verbs (Get, Start, Join)",
                    "benefit_driven": "CTAs should highlight benefit (See Results, Transform Today)",
                    "urgency": "CTAs can create urgency (Limited Time, Act Now)",
                    "friendly": "CTAs should be warm and inviting (Let's Talk, Say Hello)"
                }
                instructions.append(f"- CTAs: {cta_map.get(content_strategy['cta_style'], '')}")

            if content_strategy.get("cta_examples"):
                instructions.append(f"- CTA examples to match: {', '.join(content_strategy['cta_examples'][:3])}")

        return "\n".join(instructions)


def generate_content(research: Dict[str, Any]) -> WebsiteContent:
    """Generate website content from research data."""
    generator = ContentGenerator()
    return generator.generate_content(research)


def generate_personality_content(research: Dict[str, Any]) -> WebsiteContent:
    """Generate personality-driven website content from research data."""
    generator = ContentGenerator()
    return generator.generate_personality_content(research)


if __name__ == "__main__":
    # Test with sample data including brand personality
    sample_research = {
        "company": {
            "name": "Project Evolve",
            "industry": "Fitness",
            "location": "Naples, FL",
            "description": "Small-group personal training gym",
            "services": ["Personal Training", "Nutrition Coaching", "Group Classes"],
            "target_audience": "Adults 40+",
            "unique_selling_points": ["Small groups", "Personalized attention", "Community focus"]
        },
        "owner": {
            "name": "Jake Raleigh",
            "title": "Owner & Head Coach",
            "background": "Fitness professional with years of experience",
            "expertise": ["Strength training", "Nutrition", "Lifestyle coaching"]
        },
        "tone": "inspirational",
        "brand_personality": {
            "brand_name": "Project Evolve",
            "tagline": "Transform Your Body, Transform Your Life",
            "elevator_pitch": "Small-group personal training for adults 40+ who want to get stronger and healthier in a supportive community.",
            "primary_audience": "Adults 40+ seeking fitness transformation",
            "audience_pain_points": ["Feeling out of shape", "Intimidated by big gyms", "Lack of accountability"],
            "audience_desires": ["Feel stronger", "More energy", "Supportive community"],
            "key_differentiators": ["Small group focus", "Personalized attention", "Community atmosphere"],
            "voice": {
                "tone": "inspirational",
                "personality_adjectives": ["motivating", "supportive", "energetic", "authentic", "empowering"],
                "speaking_style": "we_voice",
                "formality_level": 4,
                "emotion_intensity": 7,
                "sentence_length": "varied",
                "use_emojis": False,
                "exclamation_frequency": "occasional",
                "key_phrases": ["transform your life", "stronger every day", "you've got this"],
                "primary_message": "It's never too late to transform your health",
                "value_proposition": "Personal attention in a supportive community"
            },
            "content_strategy": {
                "headline_style": "emotional",
                "cta_style": "action_verb",
                "cta_examples": ["Start Your Transformation", "Join the Community", "Book Your Free Session"]
            }
        }
    }

    generator = ContentGenerator()

    print("=" * 60)
    print("PERSONALITY-DRIVEN CONTENT GENERATION")
    print("=" * 60)

    content = generator.generate_personality_content(sample_research)
    print(json.dumps(generator.to_dict(content), indent=2))
