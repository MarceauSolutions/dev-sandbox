#!/usr/bin/env python3
"""
ai_news_digest.py - Automated AI & Job Market News Digest Generator

Fetches and summarizes the latest AI news, job market trends, and industry
developments to help stay informed about AI's impact on work.

Features:
- Web search for latest AI news (via Anthropic's Claude)
- Job market trend tracking
- Industry-specific impact analysis
- Weekly/daily summary generation

Usage:
    python -m src.ai_news_digest                  # Generate daily digest
    python -m src.ai_news_digest --weekly         # Generate weekly deep dive
    python -m src.ai_news_digest --topic "AI jobs" # Focus on specific topic
    python -m src.ai_news_digest --output json    # Output as JSON

Requirements:
    - ANTHROPIC_API_KEY in .env
    - Internet connection for web searches

Note: This module is designed to be invoked through Claude Code or
integrated into the morning digest system.
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")


@dataclass
class NewsItem:
    """Represents a single news item."""
    title: str
    source: str
    url: str
    summary: str
    category: str  # ai_development, job_market, industry_adoption, regulation, skills
    impact_level: str  # high, medium, low
    date_found: str


@dataclass
class AINewsDigest:
    """Complete AI news digest."""
    generated_at: str
    period: str  # daily, weekly
    summary: str
    key_developments: List[NewsItem]
    job_market_trends: Dict[str, Any]
    skills_in_demand: List[str]
    industries_affected: List[Dict[str, str]]
    actionable_insights: List[str]
    sources: List[str]


class AINewsDigestGenerator:
    """
    Generates AI and job market news digests.

    This generator is designed to work with Claude Code's web search
    capabilities to fetch and analyze the latest AI news.
    """

    # Key topics to track
    TRACKING_TOPICS = [
        "AI job displacement layoffs 2026",
        "AI skills in demand hiring trends",
        "generative AI enterprise adoption",
        "AI automation impact industries",
        "AI regulation policy updates",
        "AI tools productivity software",
        "machine learning job market",
        "AI startups funding news"
    ]

    # Industries to monitor
    INDUSTRIES = [
        "technology/software",
        "finance/banking",
        "healthcare",
        "legal",
        "marketing/advertising",
        "customer service",
        "manufacturing",
        "education"
    ]

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize the generator."""
        self.output_dir = output_dir or Path(__file__).parent.parent / "output" / "ai-digests"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_search_queries(self, period: str = "daily") -> List[str]:
        """
        Generate search queries for the digest.

        Args:
            period: "daily" or "weekly"

        Returns:
            List of search queries to execute
        """
        base_queries = [
            "AI job market news today",
            "AI layoffs announcements this week",
            "AI skills hiring trends 2026",
            "generative AI company news",
            "AI automation impact workers"
        ]

        if period == "weekly":
            base_queries.extend([
                "AI policy regulation news this week",
                "AI startups funding rounds",
                "AI enterprise adoption statistics"
            ])

        return base_queries

    def create_digest_prompt(self, period: str = "daily") -> str:
        """
        Create a prompt for Claude to generate the digest.

        This prompt should be used with Claude's web search capabilities.

        Args:
            period: "daily" or "weekly"

        Returns:
            Prompt string for Claude
        """
        today = datetime.now().strftime("%B %d, %Y")

        if period == "daily":
            time_frame = "the past 24 hours"
        else:
            time_frame = "the past week"

        prompt = f"""Generate an AI & Job Market News Digest for {today}.

Research {time_frame} and provide:

1. **KEY DEVELOPMENTS** (3-5 items)
   - Major AI announcements from companies (OpenAI, Anthropic, Google, Meta, etc.)
   - AI-related layoffs or hiring announcements
   - New AI tools or capabilities released
   - Policy/regulation updates

2. **JOB MARKET TRENDS**
   - Which roles are being affected by AI?
   - What new AI jobs are appearing?
   - Any statistics on AI-related employment changes?

3. **SKILLS IN DEMAND**
   - Top 5 AI skills employers are seeking
   - Emerging skill requirements

4. **INDUSTRY IMPACT**
   - Which industries saw AI-related news?
   - Specific company examples

5. **ACTIONABLE INSIGHTS**
   - 3-5 specific actions readers should take
   - What to watch in the coming week

Format the response as a structured report with clear sections.
Include source URLs for all major claims.
Be factual and balanced - include both positive and concerning developments.
Focus on practical implications for workers and businesses.

Today's date: {today}
Search timeframe: {time_frame}
"""
        return prompt

    def create_manual_digest_template(self) -> Dict[str, Any]:
        """
        Create a template for manual digest creation.

        Returns:
            Dictionary template that can be filled in
        """
        return {
            "generated_at": datetime.now().isoformat(),
            "period": "daily",
            "summary": "[ONE PARAGRAPH SUMMARY OF KEY DEVELOPMENTS]",
            "key_developments": [
                {
                    "title": "[HEADLINE]",
                    "source": "[SOURCE NAME]",
                    "url": "[URL]",
                    "summary": "[2-3 SENTENCE SUMMARY]",
                    "category": "[ai_development|job_market|industry_adoption|regulation|skills]",
                    "impact_level": "[high|medium|low]",
                    "date_found": datetime.now().strftime("%Y-%m-%d")
                }
            ],
            "job_market_trends": {
                "jobs_at_risk": ["[ROLE 1]", "[ROLE 2]"],
                "jobs_growing": ["[ROLE 1]", "[ROLE 2]"],
                "notable_layoffs": [],
                "notable_hiring": []
            },
            "skills_in_demand": [
                "prompt engineering",
                "AI integration",
                "MLOps",
                "AI safety",
                "domain expertise + AI"
            ],
            "industries_affected": [
                {"industry": "[INDUSTRY]", "impact": "[DESCRIPTION]"}
            ],
            "actionable_insights": [
                "[ACTION 1]",
                "[ACTION 2]",
                "[ACTION 3]"
            ],
            "sources": [
                "[SOURCE URL 1]",
                "[SOURCE URL 2]"
            ]
        }

    def save_digest(self, digest: Dict[str, Any], period: str = "daily") -> Path:
        """
        Save digest to file.

        Args:
            digest: Digest data dictionary
            period: "daily" or "weekly"

        Returns:
            Path to saved file
        """
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"ai-news-digest-{period}-{today}.json"
        filepath = self.output_dir / filename

        with open(filepath, 'w') as f:
            json.dump(digest, f, indent=2)

        print(f"Digest saved to: {filepath}")
        return filepath

    def format_markdown_report(self, digest: Dict[str, Any]) -> str:
        """
        Format digest as a markdown report.

        Args:
            digest: Digest data dictionary

        Returns:
            Markdown formatted string
        """
        lines = []
        today = datetime.now().strftime("%B %d, %Y")
        period = digest.get("period", "daily").title()

        lines.append(f"# AI & Job Market {period} Digest")
        lines.append(f"*{today}*")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Summary
        if digest.get("summary"):
            lines.append("## Summary")
            lines.append("")
            lines.append(digest["summary"])
            lines.append("")

        # Key Developments
        if digest.get("key_developments"):
            lines.append("## Key Developments")
            lines.append("")
            for item in digest["key_developments"]:
                lines.append(f"### {item.get('title', 'Untitled')}")
                lines.append(f"*Source: {item.get('source', 'Unknown')}*")
                lines.append("")
                lines.append(item.get('summary', ''))
                if item.get('url'):
                    lines.append(f"[Read more]({item['url']})")
                lines.append("")

        # Job Market Trends
        if digest.get("job_market_trends"):
            lines.append("## Job Market Trends")
            lines.append("")
            trends = digest["job_market_trends"]
            if trends.get("jobs_at_risk"):
                lines.append("**Jobs at Risk:**")
                for job in trends["jobs_at_risk"]:
                    lines.append(f"- {job}")
                lines.append("")
            if trends.get("jobs_growing"):
                lines.append("**Jobs Growing:**")
                for job in trends["jobs_growing"]:
                    lines.append(f"- {job}")
                lines.append("")

        # Skills in Demand
        if digest.get("skills_in_demand"):
            lines.append("## Skills in Demand")
            lines.append("")
            for skill in digest["skills_in_demand"]:
                lines.append(f"- {skill}")
            lines.append("")

        # Industries Affected
        if digest.get("industries_affected"):
            lines.append("## Industries Affected")
            lines.append("")
            for item in digest["industries_affected"]:
                lines.append(f"**{item.get('industry', 'Unknown')}**: {item.get('impact', '')}")
            lines.append("")

        # Actionable Insights
        if digest.get("actionable_insights"):
            lines.append("## Actionable Insights")
            lines.append("")
            for i, insight in enumerate(digest["actionable_insights"], 1):
                lines.append(f"{i}. {insight}")
            lines.append("")

        # Sources
        if digest.get("sources"):
            lines.append("## Sources")
            lines.append("")
            for source in digest["sources"]:
                lines.append(f"- {source}")
            lines.append("")

        lines.append("---")
        lines.append(f"*Generated: {digest.get('generated_at', datetime.now().isoformat())}*")

        return "\n".join(lines)

    def integrate_with_morning_digest(self) -> str:
        """
        Generate a short AI summary for the morning digest.

        Returns:
            Short summary suitable for morning digest email
        """
        prompt = """Generate a brief AI & Job Market update (max 150 words) for a morning digest email.

Include:
- 1-2 key AI developments from the past 24 hours
- Any notable job market news related to AI
- One actionable tip

Keep it concise and actionable. Use bullet points.
"""
        return prompt


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate AI & Job Market News Digest"
    )
    parser.add_argument(
        "--weekly",
        action="store_true",
        help="Generate weekly deep dive instead of daily"
    )
    parser.add_argument(
        "--template",
        action="store_true",
        help="Output a blank template for manual filling"
    )
    parser.add_argument(
        "--output",
        choices=["json", "markdown", "both"],
        default="both",
        help="Output format"
    )
    parser.add_argument(
        "--prompt-only",
        action="store_true",
        help="Just output the prompt for Claude to use with web search"
    )

    args = parser.parse_args()
    generator = AINewsDigestGenerator()
    period = "weekly" if args.weekly else "daily"

    if args.template:
        template = generator.create_manual_digest_template()
        print(json.dumps(template, indent=2))
        return

    if args.prompt_only:
        prompt = generator.create_digest_prompt(period)
        print("=" * 60)
        print("PROMPT FOR CLAUDE (use with web search)")
        print("=" * 60)
        print(prompt)
        return

    # Without Claude API, provide the prompt and template
    print("=" * 60)
    print(f"AI NEWS DIGEST GENERATOR - {period.upper()}")
    print("=" * 60)
    print()
    print("To generate the digest, use one of these methods:")
    print()
    print("1. Use Claude Code with web search:")
    print("   Copy the prompt below and run it in a Claude Code session")
    print("   that has web search enabled.")
    print()
    print("2. Manual generation:")
    print("   Run with --template flag to get a JSON template,")
    print("   then fill in the data manually from your research.")
    print()
    print("=" * 60)
    print("PROMPT:")
    print("=" * 60)
    print(generator.create_digest_prompt(period))
    print()
    print("=" * 60)
    print("SEARCH QUERIES TO RUN:")
    print("=" * 60)
    for query in generator.generate_search_queries(period):
        print(f"  - {query}")


if __name__ == "__main__":
    main()
