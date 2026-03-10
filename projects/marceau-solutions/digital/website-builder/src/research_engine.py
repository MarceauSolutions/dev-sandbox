#!/usr/bin/env python3
"""
research_engine.py - Company and Owner Research

Uses Claude + web search + social media analysis to gather comprehensive
information about a business and its owner/founder for website generation.

Enhanced Pipeline:
1. Parse social media URLs provided by user
2. Analyze social profiles for personality/brand voice
3. Gather web context (reviews, news, competitors)
4. Synthesize into unified brand personality profile
5. Return structured research for website generation

Usage:
    from research_engine import research_company, research_with_social

    # Basic research (AI-generated)
    result = research_company("Project Evolve", "Jake Raleigh")

    # Enhanced research with social profiles
    result = research_with_social(
        company_name="Project Evolve",
        owner_name="Jake Raleigh",
        social_profiles={
            "x": "https://x.com/projectevolve",
            "instagram": "https://instagram.com/projectevolve"
        }
    )
"""

import os
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from datetime import datetime

import anthropic
from dotenv import load_dotenv

# Import new modules
from .social_profile_analyzer import SocialProfileAnalyzer, SocialProfileAnalysis
from .web_search import WebSearcher, BusinessContext
from .personality_synthesizer import PersonalitySynthesizer, BrandPersonality

load_dotenv()


@dataclass
class CompanyResearch:
    """Structured company research data."""
    name: str
    industry: str
    location: str
    description: str
    services: List[str]
    target_audience: str
    unique_selling_points: List[str]
    competitors: List[str]
    website_url: Optional[str]
    social_media: Dict[str, str]
    reviews_summary: Optional[str]
    founded_year: Optional[str]


@dataclass
class OwnerResearch:
    """Structured owner/founder research data."""
    name: str
    title: str
    background: str
    expertise: List[str]
    social_profiles: Dict[str, str]
    notable_achievements: List[str]
    public_quotes: List[str]


@dataclass
class WebsiteResearch:
    """Combined research for website generation."""
    company: CompanyResearch
    owner: OwnerResearch
    recommended_template: str
    suggested_sections: List[str]
    tone: str
    color_scheme: Dict[str, str]
    researched_at: str

    # Enhanced fields from new pipeline
    brand_personality: Optional[Dict[str, Any]] = None
    social_analysis: Optional[Dict[str, Any]] = None
    web_context: Optional[Dict[str, Any]] = None
    research_sources: List[str] = field(default_factory=list)
    confidence_score: float = 0.5


class ResearchEngine:
    """
    AI-powered research engine for website generation.

    Uses Claude with web search to gather comprehensive
    information about businesses and their owners.
    """

    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.model = "claude-sonnet-4-20250514"

    def research_company(
        self,
        company_name: str,
        owner_name: str,
        location: Optional[str] = None
    ) -> WebsiteResearch:
        """
        Research a company and owner for website generation.

        Args:
            company_name: Name of the business
            owner_name: Name of owner/founder
            location: Optional location to narrow search

        Returns:
            WebsiteResearch with all gathered data
        """

        # Build search context
        search_context = f"{company_name}"
        if location:
            search_context += f" {location}"
        if owner_name:
            search_context += f" {owner_name}"

        # Research prompt
        research_prompt = f"""Research the following business for website creation:

Company: {company_name}
Owner/Founder: {owner_name}
Location: {location or "Unknown"}

Please gather and structure the following information:

## Company Information
1. Industry/sector
2. Physical location(s)
3. Business description (what they do)
4. Services or products offered
5. Target audience/ideal customer
6. Unique selling points (what makes them different)
7. Competitors in the area
8. Current website (if any)
9. Social media presence
10. Customer reviews summary
11. Year founded (if available)

## Owner Information
1. Full name and title
2. Professional background
3. Areas of expertise
4. Social media profiles
5. Notable achievements or credentials
6. Any public quotes or philosophy

## Website Recommendations
Based on the research, recommend:
1. Best template style (business, fitness, restaurant, ecommerce, portfolio)
2. Suggested website sections
3. Appropriate tone (professional, friendly, bold, luxury, etc.)
4. Color scheme suggestions based on industry/brand

Format your response as structured JSON matching this schema:
{{
    "company": {{
        "name": "",
        "industry": "",
        "location": "",
        "description": "",
        "services": [],
        "target_audience": "",
        "unique_selling_points": [],
        "competitors": [],
        "website_url": null,
        "social_media": {{}},
        "reviews_summary": null,
        "founded_year": null
    }},
    "owner": {{
        "name": "",
        "title": "",
        "background": "",
        "expertise": [],
        "social_profiles": {{}},
        "notable_achievements": [],
        "public_quotes": []
    }},
    "recommended_template": "",
    "suggested_sections": [],
    "tone": "",
    "color_scheme": {{
        "primary": "",
        "secondary": "",
        "accent": "",
        "background": "",
        "text": ""
    }}
}}
"""

        # Call Claude with web search capability
        # Note: In production, this would use Claude's web search tool
        # For now, we'll use the standard API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": research_prompt
                }
            ]
        )

        # Parse response
        response_text = response.content[0].text

        # Extract JSON from response
        try:
            # Find JSON in response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
        except json.JSONDecodeError as e:
            print(f"Failed to parse research response: {e}")
            # Return minimal structure
            data = self._create_minimal_research(company_name, owner_name)

        # Build structured result
        company = CompanyResearch(
            name=data.get("company", {}).get("name", company_name),
            industry=data.get("company", {}).get("industry", "General Business"),
            location=data.get("company", {}).get("location", location or ""),
            description=data.get("company", {}).get("description", ""),
            services=data.get("company", {}).get("services", []),
            target_audience=data.get("company", {}).get("target_audience", ""),
            unique_selling_points=data.get("company", {}).get("unique_selling_points", []),
            competitors=data.get("company", {}).get("competitors", []),
            website_url=data.get("company", {}).get("website_url"),
            social_media=data.get("company", {}).get("social_media", {}),
            reviews_summary=data.get("company", {}).get("reviews_summary"),
            founded_year=data.get("company", {}).get("founded_year")
        )

        owner = OwnerResearch(
            name=data.get("owner", {}).get("name", owner_name),
            title=data.get("owner", {}).get("title", "Owner"),
            background=data.get("owner", {}).get("background", ""),
            expertise=data.get("owner", {}).get("expertise", []),
            social_profiles=data.get("owner", {}).get("social_profiles", {}),
            notable_achievements=data.get("owner", {}).get("notable_achievements", []),
            public_quotes=data.get("owner", {}).get("public_quotes", [])
        )

        return WebsiteResearch(
            company=company,
            owner=owner,
            recommended_template=data.get("recommended_template", "business"),
            suggested_sections=data.get("suggested_sections", [
                "hero", "about", "services", "testimonials", "contact"
            ]),
            tone=data.get("tone", "professional"),
            color_scheme=data.get("color_scheme", {
                "primary": "#1a1a2e",
                "secondary": "#667eea",
                "accent": "#4ade80",
                "background": "#ffffff",
                "text": "#1f2937"
            }),
            researched_at=datetime.now().isoformat()
        )

    def _create_minimal_research(
        self,
        company_name: str,
        owner_name: str
    ) -> Dict[str, Any]:
        """Create minimal research structure when parsing fails."""
        return {
            "company": {
                "name": company_name,
                "industry": "General Business",
                "location": "",
                "description": f"{company_name} is a business owned by {owner_name}.",
                "services": [],
                "target_audience": "General consumers",
                "unique_selling_points": [],
                "competitors": [],
                "website_url": None,
                "social_media": {},
                "reviews_summary": None,
                "founded_year": None
            },
            "owner": {
                "name": owner_name,
                "title": "Owner",
                "background": "",
                "expertise": [],
                "social_profiles": {},
                "notable_achievements": [],
                "public_quotes": []
            },
            "recommended_template": "business",
            "suggested_sections": ["hero", "about", "services", "contact"],
            "tone": "professional",
            "color_scheme": {
                "primary": "#1a1a2e",
                "secondary": "#667eea",
                "accent": "#4ade80",
                "background": "#ffffff",
                "text": "#1f2937"
            }
        }

    def to_dict(self, research: WebsiteResearch) -> Dict[str, Any]:
        """Convert research to dictionary."""
        return {
            "company": asdict(research.company),
            "owner": asdict(research.owner),
            "recommended_template": research.recommended_template,
            "suggested_sections": research.suggested_sections,
            "tone": research.tone,
            "color_scheme": research.color_scheme,
            "researched_at": research.researched_at,
            "brand_personality": research.brand_personality,
            "social_analysis": research.social_analysis,
            "web_context": research.web_context,
            "research_sources": research.research_sources,
            "confidence_score": research.confidence_score
        }

    def research_with_social(
        self,
        company_name: str,
        owner_name: str,
        social_profiles: Dict[str, str],
        location: Optional[str] = None,
        enable_web_search: bool = True,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> WebsiteResearch:
        """
        Enhanced research using social media profiles.

        This is the main entry point for the enhanced pipeline:
        1. Analyze provided social profiles
        2. Gather web context (if enabled)
        3. Synthesize brand personality
        4. Return enriched WebsiteResearch

        Args:
            company_name: Name of the business
            owner_name: Name of owner/founder
            social_profiles: Dict of {platform: url} for social profiles
            location: Optional location for local context
            enable_web_search: Whether to search web for additional context
            user_preferences: Optional user overrides for brand preferences

        Returns:
            WebsiteResearch with enhanced personality data
        """
        research_sources = []
        social_analysis_dict = None
        web_context_dict = None
        brand_personality_dict = None

        # Step 1: Analyze social profiles
        print(f"Analyzing social profiles for {company_name}...")
        social_analyzer = SocialProfileAnalyzer()

        try:
            social_analysis = social_analyzer.analyze_profiles(
                profile_urls=social_profiles,
                company_name=company_name,
                owner_name=owner_name,
                fetch_data=True
            )
            social_analysis_dict = social_analyzer.to_dict(social_analysis)
            research_sources.append("social_media")
            print(f"  Found {len(social_analysis.profiles)} profiles")
        except Exception as e:
            print(f"  Social analysis failed: {e}")
            social_analysis_dict = None

        # Step 2: Gather web context (if enabled)
        if enable_web_search:
            print(f"Gathering web context...")
            web_searcher = WebSearcher()

            if web_searcher.providers and web_searcher.providers != ["ai_fallback"]:
                try:
                    web_context = web_searcher.gather_business_context(
                        company_name=company_name,
                        owner_name=owner_name,
                        location=location
                    )
                    web_context_dict = web_searcher.to_dict(web_context)
                    research_sources.append("web_search")
                    print(f"  Found {len(web_context.reviews)} reviews, {len(web_context.news_mentions)} news mentions")
                except Exception as e:
                    print(f"  Web search failed: {e}")
                    web_context_dict = None
            else:
                print("  No web search API keys configured, skipping")

        # Step 3: Get basic company/owner research (AI-generated baseline)
        print(f"Generating baseline research...")
        basic_research = self.research_company(company_name, owner_name, location)
        research_sources.append("ai_research")

        # Step 4: Synthesize brand personality
        print(f"Synthesizing brand personality...")
        synthesizer = PersonalitySynthesizer()

        try:
            brand_personality = synthesizer.synthesize(
                social_analysis=social_analysis_dict,
                web_context=web_context_dict,
                company_info=asdict(basic_research.company),
                owner_info=asdict(basic_research.owner),
                user_preferences=user_preferences
            )
            brand_personality_dict = synthesizer.to_dict(brand_personality)
            research_sources.append("personality_synthesis")
            print(f"  Brand personality synthesized (confidence: {brand_personality.confidence_score:.0%})")
        except Exception as e:
            print(f"  Personality synthesis failed: {e}")
            brand_personality_dict = None

        # Step 5: Enrich basic research with synthesized data
        enriched_research = self._enrich_research(
            basic_research=basic_research,
            brand_personality=brand_personality_dict,
            social_analysis=social_analysis_dict,
            web_context=web_context_dict,
            research_sources=research_sources
        )

        return enriched_research

    def _enrich_research(
        self,
        basic_research: WebsiteResearch,
        brand_personality: Optional[Dict[str, Any]],
        social_analysis: Optional[Dict[str, Any]],
        web_context: Optional[Dict[str, Any]],
        research_sources: List[str]
    ) -> WebsiteResearch:
        """
        Enrich basic research with synthesized personality data.

        Overrides basic research values with more accurate data
        from social analysis and personality synthesis.
        """
        # Start with basic research
        enriched = basic_research

        # Add raw analysis data
        enriched.brand_personality = brand_personality
        enriched.social_analysis = social_analysis
        enriched.web_context = web_context
        enriched.research_sources = research_sources

        # Override with personality data if available
        if brand_personality:
            # Update tone from personality
            voice = brand_personality.get("voice", {})
            enriched.tone = voice.get("tone", enriched.tone)

            # Update color scheme from visual identity
            visual = brand_personality.get("visual_identity", {})
            if visual:
                enriched.color_scheme = {
                    "primary": visual.get("primary_color", enriched.color_scheme.get("primary")),
                    "secondary": visual.get("secondary_color", enriched.color_scheme.get("secondary")),
                    "accent": visual.get("accent_color", enriched.color_scheme.get("accent")),
                    "background": visual.get("background_color", enriched.color_scheme.get("background", "#ffffff")),
                    "text": visual.get("text_color", enriched.color_scheme.get("text", "#1f2937"))
                }

            # Update sections from content strategy
            content = brand_personality.get("content_strategy", {})
            if content.get("priority_sections"):
                enriched.suggested_sections = content["priority_sections"]

            # Update template recommendation
            template_style = visual.get("layout_style", "")
            if template_style:
                template_map = {
                    "spacious": "modern",
                    "compact": "business",
                    "asymmetric": "creative",
                    "grid": "portfolio"
                }
                enriched.recommended_template = template_map.get(template_style, enriched.recommended_template)

            # Calculate confidence score
            enriched.confidence_score = brand_personality.get("confidence_score", 0.5)

        # Enrich company data from web context
        if web_context:
            if web_context.get("key_differentiators"):
                enriched.company.unique_selling_points = (
                    enriched.company.unique_selling_points +
                    web_context["key_differentiators"]
                )[:5]  # Keep top 5

        return enriched

    def research_owner_socials(
        self,
        owner_name: str,
        social_profiles: Dict[str, str],
        company_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Research owner's personality from their social profiles.

        Use this for owner-focused businesses where the owner's
        personality should drive the brand.

        Args:
            owner_name: Owner's name
            social_profiles: Dict of {platform: url}
            company_name: Optional company name for context

        Returns:
            Dict with owner personality analysis
        """
        analyzer = SocialProfileAnalyzer()

        analysis = analyzer.analyze_profiles(
            profile_urls=social_profiles,
            company_name=company_name,
            owner_name=owner_name,
            fetch_data=True
        )

        return analyzer.to_dict(analysis)


# Convenience functions
def research_company(
    company_name: str,
    owner_name: str,
    location: Optional[str] = None
) -> WebsiteResearch:
    """Research a company for website generation (basic AI research)."""
    engine = ResearchEngine()
    return engine.research_company(company_name, owner_name, location)


def research_with_social(
    company_name: str,
    owner_name: str,
    social_profiles: Dict[str, str],
    location: Optional[str] = None,
    enable_web_search: bool = True,
    user_preferences: Optional[Dict[str, Any]] = None
) -> WebsiteResearch:
    """
    Enhanced research using social media profiles.

    Args:
        company_name: Name of the business
        owner_name: Name of owner/founder
        social_profiles: Dict of {platform: url} for social profiles
            Example: {"x": "https://x.com/username", "instagram": "https://instagram.com/username"}
        location: Optional location for local context
        enable_web_search: Whether to search web for additional context
        user_preferences: Optional user overrides for brand preferences

    Returns:
        WebsiteResearch with enhanced personality data
    """
    engine = ResearchEngine()
    return engine.research_with_social(
        company_name=company_name,
        owner_name=owner_name,
        social_profiles=social_profiles,
        location=location,
        enable_web_search=enable_web_search,
        user_preferences=user_preferences
    )


if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("WEBSITE BUILDER - RESEARCH ENGINE")
    print("=" * 60)

    if len(sys.argv) < 3:
        print("""
Usage:
  Basic research:
    python research_engine.py 'Company Name' 'Owner Name' [Location]

  Enhanced research with social profiles:
    python research_engine.py 'Company Name' 'Owner Name' [Location] --social x=URL linkedin=URL

Examples:
  python research_engine.py "Project Evolve" "Jake Raleigh" "Naples, FL"

  python research_engine.py "Project Evolve" "Jake Raleigh" "Naples, FL" \\
    --social x=https://x.com/projectevolve instagram=https://instagram.com/projectevolve

Environment Variables:
  ANTHROPIC_API_KEY - Required for AI research
  BRAVE_SEARCH_API_KEY - Optional for web search
  TAVILY_API_KEY - Optional for web search
""")
        sys.exit(0)

    company = sys.argv[1]
    owner = sys.argv[2]
    location = None
    social_profiles = {}

    # Parse arguments
    i = 3
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--social":
            # Parse social profile URLs
            i += 1
            while i < len(sys.argv) and not sys.argv[i].startswith("--"):
                if "=" in sys.argv[i]:
                    platform, url = sys.argv[i].split("=", 1)
                    social_profiles[platform] = url
                i += 1
            continue
        elif not arg.startswith("--"):
            location = arg
        i += 1

    engine = ResearchEngine()

    if social_profiles:
        print(f"\nEnhanced research for: {company}")
        print(f"Owner: {owner}")
        if location:
            print(f"Location: {location}")
        print(f"Social profiles: {list(social_profiles.keys())}")
        print()

        result = engine.research_with_social(
            company_name=company,
            owner_name=owner,
            social_profiles=social_profiles,
            location=location
        )
    else:
        print(f"\nBasic research for: {company}")
        print(f"Owner: {owner}")
        if location:
            print(f"Location: {location}")
        print()

        result = engine.research_company(company, owner, location)

    print("\n" + "=" * 60)
    print("RESEARCH RESULTS")
    print("=" * 60)
    print(json.dumps(engine.to_dict(result), indent=2))
