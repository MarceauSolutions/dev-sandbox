#!/usr/bin/env python3
"""
personality_synthesizer.py - Brand Personality Synthesis

Combines all research sources into a unified brand personality profile:
- Social media analysis
- Web search context
- Direct company research
- Owner background

The synthesized profile drives all website generation decisions.

Usage:
    from personality_synthesizer import synthesize_brand_personality

    profile = synthesize_brand_personality(
        social_analysis=social_data,
        web_context=search_data,
        company_info=company_data,
        owner_info=owner_data
    )
"""

import os
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from datetime import datetime

import anthropic
from dotenv import load_dotenv

load_dotenv()


@dataclass
class BrandVoice:
    """Brand voice characteristics for content generation."""
    tone: str  # professional, casual, inspirational, bold, warm, luxury
    personality_adjectives: List[str]  # 3-5 words describing the brand
    speaking_style: str  # first_person, third_person, we_voice
    formality_level: int  # 1-10 (1=very casual, 10=very formal)
    emotion_intensity: int  # 1-10 (1=reserved, 10=very expressive)
    humor_level: int  # 1-10 (1=no humor, 10=very playful)

    # Language patterns
    sentence_length: str  # short, medium, long, varied
    vocabulary_complexity: str  # simple, moderate, sophisticated
    use_jargon: bool
    use_emojis: bool
    exclamation_frequency: str  # never, rare, occasional, frequent

    # Messaging priorities
    primary_message: str  # The one thing they want customers to know
    value_proposition: str  # Why choose them
    trust_builders: List[str]  # What makes them credible


@dataclass
class VisualIdentity:
    """Visual brand identity for website design."""
    # Colors
    primary_color: str
    secondary_color: str
    accent_color: str
    background_color: str
    text_color: str
    color_mood: str  # warm, cool, neutral, vibrant, muted

    # Typography
    heading_style: str  # bold_sans, elegant_serif, modern_geometric, playful, classic
    body_style: str  # clean, sophisticated, casual
    font_weight_preference: str  # light, regular, bold

    # Layout & Style
    layout_style: str  # spacious, compact, asymmetric, grid
    imagery_style: str  # photography, illustrations, abstract, minimal, mixed
    border_radius: str  # none, subtle, rounded, pill
    shadow_intensity: str  # none, subtle, medium, dramatic

    # Animation & Interaction
    animation_level: str  # none, subtle, moderate, dynamic
    hover_style: str  # simple, lift, glow, color_shift


@dataclass
class ContentStrategy:
    """Content strategy derived from brand personality."""
    # Headlines
    headline_style: str  # direct, clever, emotional, benefit_focused, question
    headline_length: str  # short (3-5 words), medium (6-10), long (11+)

    # Body copy
    paragraph_style: str  # concise, detailed, story_driven
    bullet_point_preference: bool
    testimonial_style: str  # quote_only, with_story, video_preferred

    # CTAs
    cta_style: str  # action_verb, benefit_driven, urgency, friendly
    cta_examples: List[str]

    # Sections to emphasize
    priority_sections: List[str]  # Ordered by importance
    optional_sections: List[str]
    avoid_sections: List[str]


@dataclass
class BrandPersonality:
    """Complete synthesized brand personality profile."""
    # Core identity
    brand_name: str
    tagline: str
    elevator_pitch: str  # 1-2 sentences
    brand_story_summary: str  # 3-4 sentences

    # Personality components
    voice: BrandVoice
    visual_identity: VisualIdentity
    content_strategy: ContentStrategy

    # Target audience
    primary_audience: str
    audience_pain_points: List[str]
    audience_desires: List[str]

    # Competitive positioning
    market_position: str  # leader, challenger, niche, disruptor
    key_differentiators: List[str]
    competitive_advantages: List[str]

    # Meta
    confidence_score: float  # 0-1, how confident we are in this profile
    data_sources: List[str]  # What sources informed this profile
    synthesized_at: str


class PersonalitySynthesizer:
    """
    Synthesizes brand personality from multiple research sources.

    Uses AI to intelligently combine and resolve conflicts between
    different data sources to create a coherent brand profile.
    """

    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.model = "claude-sonnet-4-20250514"

    def synthesize(
        self,
        social_analysis: Optional[Dict[str, Any]] = None,
        web_context: Optional[Dict[str, Any]] = None,
        company_info: Optional[Dict[str, Any]] = None,
        owner_info: Optional[Dict[str, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> BrandPersonality:
        """
        Synthesize brand personality from all available sources.

        Args:
            social_analysis: Output from SocialProfileAnalyzer
            web_context: Output from WebSearcher.gather_business_context
            company_info: Basic company information
            owner_info: Owner/founder information
            user_preferences: Direct user input/preferences (highest priority)

        Returns:
            Complete BrandPersonality profile
        """
        # Track which sources we're using
        data_sources = []

        # Build comprehensive context for AI synthesis
        context_parts = []

        if user_preferences:
            data_sources.append("user_preferences")
            context_parts.append(self._format_user_preferences(user_preferences))

        if social_analysis:
            data_sources.append("social_media_analysis")
            context_parts.append(self._format_social_analysis(social_analysis))

        if web_context:
            data_sources.append("web_search")
            context_parts.append(self._format_web_context(web_context))

        if company_info:
            data_sources.append("company_info")
            context_parts.append(self._format_company_info(company_info))

        if owner_info:
            data_sources.append("owner_info")
            context_parts.append(self._format_owner_info(owner_info))

        if not context_parts:
            raise ValueError("At least one data source is required")

        # Synthesize with AI
        synthesis_prompt = self._build_synthesis_prompt(context_parts, data_sources)
        result = self._call_synthesis_ai(synthesis_prompt)

        # Add metadata
        result["confidence_score"] = self._calculate_confidence(data_sources)
        result["data_sources"] = data_sources
        result["synthesized_at"] = datetime.now().isoformat()

        return self._build_brand_personality(result)

    def _format_user_preferences(self, prefs: Dict[str, Any]) -> str:
        """Format user preferences for synthesis."""
        return f"""## User Preferences (HIGHEST PRIORITY - override other sources)
{json.dumps(prefs, indent=2)}"""

    def _format_social_analysis(self, analysis: Dict[str, Any]) -> str:
        """Format social media analysis for synthesis."""
        comm_style = analysis.get("communication_style", {})
        personality = analysis.get("personality", {})
        recommendations = analysis.get("website_recommendations", {})

        return f"""## Social Media Analysis
Brand Summary: {analysis.get('brand_summary', 'N/A')}

Communication Style:
- Tone: {comm_style.get('tone', 'N/A')}
- Voice: {comm_style.get('voice', 'N/A')}
- Formality: {comm_style.get('formality', 'N/A')}
- Emotion Level: {comm_style.get('emotion_level', 'N/A')}
- Key Phrases: {', '.join(comm_style.get('key_phrases', []))}

Personality Traits:
- Authority Level: {personality.get('authority_level', 'N/A')}
- Values: {', '.join(personality.get('values', []))}
- Motivations: {', '.join(personality.get('motivations', []))}
- Extraversion: {personality.get('extraversion', 5)}/10
- Openness: {personality.get('openness', 5)}/10

Design Recommendations:
{json.dumps(recommendations, indent=2)}"""

    def _format_web_context(self, context: Dict[str, Any]) -> str:
        """Format web search context for synthesis."""
        return f"""## Web Search Context
Company: {context.get('company_name', 'N/A')}
Location: {context.get('location', 'N/A')}

Reputation: {context.get('reputation_summary', 'N/A')}
Market Position: {context.get('market_position', 'N/A')}

Key Differentiators:
{chr(10).join(['- ' + d for d in context.get('key_differentiators', [])])}

Review Snippets:
{chr(10).join(['- ' + r.get('snippet', '')[:200] for r in context.get('reviews', [])[:3]])}

News Mentions:
{chr(10).join(['- ' + n.get('title', '') for n in context.get('news_mentions', [])[:3]])}"""

    def _format_company_info(self, info: Dict[str, Any]) -> str:
        """Format company info for synthesis."""
        return f"""## Company Information
Name: {info.get('name', 'N/A')}
Industry: {info.get('industry', 'N/A')}
Location: {info.get('location', 'N/A')}
Description: {info.get('description', 'N/A')}

Services:
{chr(10).join(['- ' + s for s in info.get('services', [])])}

Target Audience: {info.get('target_audience', 'N/A')}

Unique Selling Points:
{chr(10).join(['- ' + u for u in info.get('unique_selling_points', [])])}"""

    def _format_owner_info(self, info: Dict[str, Any]) -> str:
        """Format owner info for synthesis."""
        return f"""## Owner/Founder Information
Name: {info.get('name', 'N/A')}
Title: {info.get('title', 'N/A')}
Background: {info.get('background', 'N/A')}

Expertise:
{chr(10).join(['- ' + e for e in info.get('expertise', [])])}

Notable Achievements:
{chr(10).join(['- ' + a for a in info.get('notable_achievements', [])])}

Public Quotes:
{chr(10).join(['- "' + q + '"' for q in info.get('public_quotes', [])])}"""

    def _build_synthesis_prompt(
        self,
        context_parts: List[str],
        data_sources: List[str]
    ) -> str:
        """Build the AI synthesis prompt."""
        context = "\n\n".join(context_parts)

        return f"""You are a brand strategist synthesizing a comprehensive brand personality profile.

# Research Data
{context}

# Instructions
Analyze all the research data and synthesize a unified brand personality profile. When sources conflict:
1. User preferences always win
2. Social media analysis reflects actual behavior
3. Web context provides external perception
4. Company info is aspirational/stated identity

Create a coherent brand personality that:
- Matches how they actually communicate (from social)
- Aligns with how they're perceived (from web)
- Achieves their business goals (from company info)
- Reflects the owner's personality (from owner info)

# Output Format
Return a complete JSON object with this exact structure:
{{
    "brand_name": "Company Name",
    "tagline": "Short memorable tagline (5-8 words)",
    "elevator_pitch": "1-2 sentence description of the business",
    "brand_story_summary": "3-4 sentence brand story",

    "voice": {{
        "tone": "professional|casual|inspirational|bold|warm|luxury",
        "personality_adjectives": ["adj1", "adj2", "adj3", "adj4", "adj5"],
        "speaking_style": "first_person|third_person|we_voice",
        "formality_level": 1-10,
        "emotion_intensity": 1-10,
        "humor_level": 1-10,
        "sentence_length": "short|medium|long|varied",
        "vocabulary_complexity": "simple|moderate|sophisticated",
        "use_jargon": true/false,
        "use_emojis": true/false,
        "exclamation_frequency": "never|rare|occasional|frequent",
        "primary_message": "The one thing they want customers to know",
        "value_proposition": "Why choose them over competitors",
        "trust_builders": ["credibility point 1", "credibility point 2"]
    }},

    "visual_identity": {{
        "primary_color": "#hex",
        "secondary_color": "#hex",
        "accent_color": "#hex",
        "background_color": "#hex",
        "text_color": "#hex",
        "color_mood": "warm|cool|neutral|vibrant|muted",
        "heading_style": "bold_sans|elegant_serif|modern_geometric|playful|classic",
        "body_style": "clean|sophisticated|casual",
        "font_weight_preference": "light|regular|bold",
        "layout_style": "spacious|compact|asymmetric|grid",
        "imagery_style": "photography|illustrations|abstract|minimal|mixed",
        "border_radius": "none|subtle|rounded|pill",
        "shadow_intensity": "none|subtle|medium|dramatic",
        "animation_level": "none|subtle|moderate|dynamic",
        "hover_style": "simple|lift|glow|color_shift"
    }},

    "content_strategy": {{
        "headline_style": "direct|clever|emotional|benefit_focused|question",
        "headline_length": "short|medium|long",
        "paragraph_style": "concise|detailed|story_driven",
        "bullet_point_preference": true/false,
        "testimonial_style": "quote_only|with_story|video_preferred",
        "cta_style": "action_verb|benefit_driven|urgency|friendly",
        "cta_examples": ["Example CTA 1", "Example CTA 2", "Example CTA 3"],
        "priority_sections": ["section1", "section2", "section3"],
        "optional_sections": ["section4", "section5"],
        "avoid_sections": []
    }},

    "primary_audience": "Description of ideal customer",
    "audience_pain_points": ["pain1", "pain2", "pain3"],
    "audience_desires": ["desire1", "desire2", "desire3"],

    "market_position": "leader|challenger|niche|disruptor",
    "key_differentiators": ["diff1", "diff2", "diff3"],
    "competitive_advantages": ["advantage1", "advantage2"]
}}

Ensure all values are specific to this brand, not generic placeholders.
Colors should be appropriate for the industry and personality.
CTAs should match the brand voice."""

    def _call_synthesis_ai(self, prompt: str) -> Dict[str, Any]:
        """Call AI to synthesize brand personality."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text

        try:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                return json.loads(response_text[json_start:json_end])
            raise ValueError("No JSON found in response")
        except json.JSONDecodeError as e:
            print(f"Failed to parse synthesis response: {e}")
            return self._get_default_profile()

    def _calculate_confidence(self, data_sources: List[str]) -> float:
        """Calculate confidence score based on data sources."""
        # More sources = higher confidence
        source_weights = {
            "user_preferences": 0.3,
            "social_media_analysis": 0.25,
            "web_search": 0.2,
            "company_info": 0.15,
            "owner_info": 0.1
        }

        confidence = sum(
            source_weights.get(source, 0.1)
            for source in data_sources
        )

        return min(confidence, 1.0)

    def _get_default_profile(self) -> Dict[str, Any]:
        """Return default profile when synthesis fails."""
        return {
            "brand_name": "Company",
            "tagline": "Your trusted partner",
            "elevator_pitch": "We provide quality services to our customers.",
            "brand_story_summary": "Founded with a mission to serve.",
            "voice": {
                "tone": "professional",
                "personality_adjectives": ["reliable", "professional", "trustworthy"],
                "speaking_style": "we_voice",
                "formality_level": 6,
                "emotion_intensity": 5,
                "humor_level": 3,
                "sentence_length": "medium",
                "vocabulary_complexity": "moderate",
                "use_jargon": False,
                "use_emojis": False,
                "exclamation_frequency": "rare",
                "primary_message": "We're here to help",
                "value_proposition": "Quality service you can trust",
                "trust_builders": ["Experience", "Customer satisfaction"]
            },
            "visual_identity": {
                "primary_color": "#1a1a2e",
                "secondary_color": "#667eea",
                "accent_color": "#4ade80",
                "background_color": "#ffffff",
                "text_color": "#1f2937",
                "color_mood": "neutral",
                "heading_style": "bold_sans",
                "body_style": "clean",
                "font_weight_preference": "regular",
                "layout_style": "spacious",
                "imagery_style": "photography",
                "border_radius": "rounded",
                "shadow_intensity": "subtle",
                "animation_level": "subtle",
                "hover_style": "lift"
            },
            "content_strategy": {
                "headline_style": "benefit_focused",
                "headline_length": "medium",
                "paragraph_style": "concise",
                "bullet_point_preference": True,
                "testimonial_style": "quote_only",
                "cta_style": "action_verb",
                "cta_examples": ["Get Started", "Learn More", "Contact Us"],
                "priority_sections": ["hero", "about", "services", "contact"],
                "optional_sections": ["testimonials", "faq"],
                "avoid_sections": []
            },
            "primary_audience": "General consumers",
            "audience_pain_points": [],
            "audience_desires": [],
            "market_position": "challenger",
            "key_differentiators": [],
            "competitive_advantages": []
        }

    def _build_brand_personality(self, data: Dict[str, Any]) -> BrandPersonality:
        """Build BrandPersonality dataclass from dictionary."""
        voice_data = data.get("voice", {})
        visual_data = data.get("visual_identity", {})
        content_data = data.get("content_strategy", {})

        voice = BrandVoice(
            tone=voice_data.get("tone", "professional"),
            personality_adjectives=voice_data.get("personality_adjectives", []),
            speaking_style=voice_data.get("speaking_style", "we_voice"),
            formality_level=voice_data.get("formality_level", 6),
            emotion_intensity=voice_data.get("emotion_intensity", 5),
            humor_level=voice_data.get("humor_level", 3),
            sentence_length=voice_data.get("sentence_length", "medium"),
            vocabulary_complexity=voice_data.get("vocabulary_complexity", "moderate"),
            use_jargon=voice_data.get("use_jargon", False),
            use_emojis=voice_data.get("use_emojis", False),
            exclamation_frequency=voice_data.get("exclamation_frequency", "rare"),
            primary_message=voice_data.get("primary_message", ""),
            value_proposition=voice_data.get("value_proposition", ""),
            trust_builders=voice_data.get("trust_builders", [])
        )

        visual_identity = VisualIdentity(
            primary_color=visual_data.get("primary_color", "#1a1a2e"),
            secondary_color=visual_data.get("secondary_color", "#667eea"),
            accent_color=visual_data.get("accent_color", "#4ade80"),
            background_color=visual_data.get("background_color", "#ffffff"),
            text_color=visual_data.get("text_color", "#1f2937"),
            color_mood=visual_data.get("color_mood", "neutral"),
            heading_style=visual_data.get("heading_style", "bold_sans"),
            body_style=visual_data.get("body_style", "clean"),
            font_weight_preference=visual_data.get("font_weight_preference", "regular"),
            layout_style=visual_data.get("layout_style", "spacious"),
            imagery_style=visual_data.get("imagery_style", "photography"),
            border_radius=visual_data.get("border_radius", "rounded"),
            shadow_intensity=visual_data.get("shadow_intensity", "subtle"),
            animation_level=visual_data.get("animation_level", "subtle"),
            hover_style=visual_data.get("hover_style", "lift")
        )

        content_strategy = ContentStrategy(
            headline_style=content_data.get("headline_style", "benefit_focused"),
            headline_length=content_data.get("headline_length", "medium"),
            paragraph_style=content_data.get("paragraph_style", "concise"),
            bullet_point_preference=content_data.get("bullet_point_preference", True),
            testimonial_style=content_data.get("testimonial_style", "quote_only"),
            cta_style=content_data.get("cta_style", "action_verb"),
            cta_examples=content_data.get("cta_examples", []),
            priority_sections=content_data.get("priority_sections", []),
            optional_sections=content_data.get("optional_sections", []),
            avoid_sections=content_data.get("avoid_sections", [])
        )

        return BrandPersonality(
            brand_name=data.get("brand_name", "Company"),
            tagline=data.get("tagline", ""),
            elevator_pitch=data.get("elevator_pitch", ""),
            brand_story_summary=data.get("brand_story_summary", ""),
            voice=voice,
            visual_identity=visual_identity,
            content_strategy=content_strategy,
            primary_audience=data.get("primary_audience", ""),
            audience_pain_points=data.get("audience_pain_points", []),
            audience_desires=data.get("audience_desires", []),
            market_position=data.get("market_position", "challenger"),
            key_differentiators=data.get("key_differentiators", []),
            competitive_advantages=data.get("competitive_advantages", []),
            confidence_score=data.get("confidence_score", 0.5),
            data_sources=data.get("data_sources", []),
            synthesized_at=data.get("synthesized_at", datetime.now().isoformat())
        )

    def to_dict(self, personality: BrandPersonality) -> Dict[str, Any]:
        """Convert BrandPersonality to dictionary."""
        return {
            "brand_name": personality.brand_name,
            "tagline": personality.tagline,
            "elevator_pitch": personality.elevator_pitch,
            "brand_story_summary": personality.brand_story_summary,
            "voice": asdict(personality.voice),
            "visual_identity": asdict(personality.visual_identity),
            "content_strategy": asdict(personality.content_strategy),
            "primary_audience": personality.primary_audience,
            "audience_pain_points": personality.audience_pain_points,
            "audience_desires": personality.audience_desires,
            "market_position": personality.market_position,
            "key_differentiators": personality.key_differentiators,
            "competitive_advantages": personality.competitive_advantages,
            "confidence_score": personality.confidence_score,
            "data_sources": personality.data_sources,
            "synthesized_at": personality.synthesized_at
        }


# Convenience function
def synthesize_brand_personality(
    social_analysis: Optional[Dict[str, Any]] = None,
    web_context: Optional[Dict[str, Any]] = None,
    company_info: Optional[Dict[str, Any]] = None,
    owner_info: Optional[Dict[str, Any]] = None,
    user_preferences: Optional[Dict[str, Any]] = None
) -> BrandPersonality:
    """Synthesize brand personality from research data."""
    synthesizer = PersonalitySynthesizer()
    return synthesizer.synthesize(
        social_analysis=social_analysis,
        web_context=web_context,
        company_info=company_info,
        owner_info=owner_info,
        user_preferences=user_preferences
    )


if __name__ == "__main__":
    # Test with sample data
    sample_social = {
        "brand_summary": "A fitness-focused brand with an inspirational, motivational tone.",
        "communication_style": {
            "tone": "inspirational",
            "voice": "first_person",
            "formality": "informal",
            "emotion_level": "expressive",
            "key_phrases": ["transform your life", "you've got this", "stronger every day"]
        },
        "personality": {
            "authority_level": "approachable_expert",
            "values": ["health", "community", "persistence"],
            "motivations": ["helping others", "personal growth"],
            "extraversion": 8,
            "openness": 7
        },
        "website_recommendations": {
            "template_style": "bold_creative",
            "color_palette": {
                "primary": "#1e40af",
                "secondary": "#f59e0b",
                "accent": "#10b981"
            }
        }
    }

    sample_company = {
        "name": "Project Evolve",
        "industry": "Fitness",
        "location": "Naples, FL",
        "description": "Small-group personal training for adults 40+",
        "services": ["Personal Training", "Nutrition Coaching", "Group Classes"],
        "target_audience": "Adults 40+ looking to transform their health",
        "unique_selling_points": ["Small groups", "Personalized attention", "Supportive community"]
    }

    sample_owner = {
        "name": "Jake Raleigh",
        "title": "Owner & Head Coach",
        "background": "Former athlete turned fitness coach",
        "expertise": ["Strength training", "Nutrition", "Motivation"],
        "notable_achievements": ["Certified personal trainer", "Helped 500+ clients"],
        "public_quotes": ["Age is just a number", "Every rep counts"]
    }

    print("Synthesizing brand personality...")
    synthesizer = PersonalitySynthesizer()
    result = synthesizer.synthesize(
        social_analysis=sample_social,
        company_info=sample_company,
        owner_info=sample_owner
    )

    print("\n" + "=" * 60)
    print("BRAND PERSONALITY")
    print("=" * 60)
    print(json.dumps(synthesizer.to_dict(result), indent=2))
