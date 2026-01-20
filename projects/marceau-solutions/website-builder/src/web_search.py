#!/usr/bin/env python3
"""
web_search.py - Web Search Integration for Research

Provides web search capabilities using multiple providers:
- Brave Search API (free tier available)
- Tavily API (AI-focused search)
- Fallback to Claude's knowledge

Usage:
    from web_search import WebSearcher

    searcher = WebSearcher()
    results = searcher.search("Company Name reviews")
    context = searcher.gather_business_context("Company", "Owner", "Location")
"""

import os
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()


@dataclass
class SearchResult:
    """Individual search result."""
    title: str
    url: str
    snippet: str
    source: str = ""
    published_date: Optional[str] = None


@dataclass
class SearchResults:
    """Collection of search results."""
    query: str
    results: List[SearchResult]
    provider: str
    searched_at: str


@dataclass
class BusinessContext:
    """Aggregated context about a business from web search."""
    company_name: str
    owner_name: Optional[str]
    location: Optional[str]

    # Gathered information
    news_mentions: List[Dict[str, str]] = field(default_factory=list)
    reviews: List[Dict[str, str]] = field(default_factory=list)
    social_mentions: List[Dict[str, str]] = field(default_factory=list)
    industry_context: List[Dict[str, str]] = field(default_factory=list)
    competitor_info: List[Dict[str, str]] = field(default_factory=list)

    # Synthesized insights
    reputation_summary: str = ""
    market_position: str = ""
    key_differentiators: List[str] = field(default_factory=list)
    potential_concerns: List[str] = field(default_factory=list)

    searched_at: str = ""


class WebSearcher:
    """
    Multi-provider web search for business research.

    Supports Brave Search, Tavily, and AI-assisted search.
    """

    def __init__(self):
        self.brave_api_key = os.getenv("BRAVE_SEARCH_API_KEY")
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")

        # Check which providers are available
        self.providers = []
        if self.brave_api_key:
            self.providers.append("brave")
        if self.tavily_api_key:
            self.providers.append("tavily")

        # Always have AI fallback
        self.providers.append("ai_fallback")

    def search_brave(
        self,
        query: str,
        count: int = 10,
        freshness: Optional[str] = None
    ) -> SearchResults:
        """
        Search using Brave Search API.

        Args:
            query: Search query
            count: Number of results (max 20)
            freshness: Time filter (pd=past day, pw=past week, pm=past month, py=past year)

        Returns:
            SearchResults
        """
        if not self.brave_api_key:
            raise ValueError("Brave Search API key not configured")

        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.brave_api_key
        }
        params = {
            "q": query,
            "count": min(count, 20)
        }
        if freshness:
            params["freshness"] = freshness

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("web", {}).get("results", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", ""),
                    source=item.get("meta_url", {}).get("hostname", ""),
                    published_date=item.get("age")
                ))

            return SearchResults(
                query=query,
                results=results,
                provider="brave",
                searched_at=datetime.now().isoformat()
            )
        except requests.RequestException as e:
            print(f"Brave Search error: {e}")
            return SearchResults(
                query=query,
                results=[],
                provider="brave",
                searched_at=datetime.now().isoformat()
            )

    def search_tavily(
        self,
        query: str,
        max_results: int = 10,
        search_depth: str = "basic"
    ) -> SearchResults:
        """
        Search using Tavily API (AI-optimized search).

        Args:
            query: Search query
            max_results: Number of results
            search_depth: "basic" or "advanced"

        Returns:
            SearchResults
        """
        if not self.tavily_api_key:
            raise ValueError("Tavily API key not configured")

        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.tavily_api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "include_answer": True
        }

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                    source=item.get("url", "").split("/")[2] if item.get("url") else "",
                    published_date=item.get("published_date")
                ))

            return SearchResults(
                query=query,
                results=results,
                provider="tavily",
                searched_at=datetime.now().isoformat()
            )
        except requests.RequestException as e:
            print(f"Tavily Search error: {e}")
            return SearchResults(
                query=query,
                results=[],
                provider="tavily",
                searched_at=datetime.now().isoformat()
            )

    def search(
        self,
        query: str,
        count: int = 10,
        provider: Optional[str] = None
    ) -> SearchResults:
        """
        Search using best available provider.

        Args:
            query: Search query
            count: Number of results
            provider: Specific provider to use (optional)

        Returns:
            SearchResults
        """
        # Use specific provider if requested and available
        if provider:
            if provider == "brave" and "brave" in self.providers:
                return self.search_brave(query, count)
            elif provider == "tavily" and "tavily" in self.providers:
                return self.search_tavily(query, count)

        # Try providers in order
        for p in self.providers:
            if p == "brave":
                results = self.search_brave(query, count)
                if results.results:
                    return results
            elif p == "tavily":
                results = self.search_tavily(query, count)
                if results.results:
                    return results

        # Return empty results if all providers fail
        return SearchResults(
            query=query,
            results=[],
            provider="none",
            searched_at=datetime.now().isoformat()
        )

    def gather_business_context(
        self,
        company_name: str,
        owner_name: Optional[str] = None,
        location: Optional[str] = None
    ) -> BusinessContext:
        """
        Gather comprehensive context about a business.

        Performs multiple searches to build a complete picture:
        - Company reviews
        - News mentions
        - Owner background
        - Industry context
        - Competitor analysis

        Args:
            company_name: Name of the business
            owner_name: Optional owner/founder name
            location: Optional location for local context

        Returns:
            BusinessContext with aggregated information
        """
        context = BusinessContext(
            company_name=company_name,
            owner_name=owner_name,
            location=location,
            searched_at=datetime.now().isoformat()
        )

        # Build location qualifier
        loc_query = f" {location}" if location else ""

        # Search for reviews
        review_query = f'"{company_name}"{loc_query} reviews'
        review_results = self.search(review_query, count=5)
        context.reviews = [
            {"title": r.title, "snippet": r.snippet, "url": r.url}
            for r in review_results.results
        ]

        # Search for news mentions
        news_query = f'"{company_name}"{loc_query}'
        news_results = self.search(news_query, count=5)
        context.news_mentions = [
            {"title": r.title, "snippet": r.snippet, "url": r.url, "date": r.published_date}
            for r in news_results.results
        ]

        # Search for owner if provided
        if owner_name:
            owner_query = f'"{owner_name}" {company_name}'
            owner_results = self.search(owner_query, count=5)
            context.social_mentions = [
                {"title": r.title, "snippet": r.snippet, "url": r.url}
                for r in owner_results.results
            ]

        # Industry context
        industry_query = f"{company_name} industry competitors{loc_query}"
        industry_results = self.search(industry_query, count=5)
        context.industry_context = [
            {"title": r.title, "snippet": r.snippet, "url": r.url}
            for r in industry_results.results
        ]

        # Synthesize insights from gathered data
        context = self._synthesize_insights(context)

        return context

    def _synthesize_insights(self, context: BusinessContext) -> BusinessContext:
        """
        Synthesize insights from gathered search results.

        This is a basic synthesis - for production, you'd want
        to use AI to analyze the search results more deeply.
        """
        # Extract key themes from reviews
        review_snippets = [r.get("snippet", "") for r in context.reviews]
        context.reputation_summary = self._extract_sentiment(review_snippets)

        # Identify differentiators from industry context
        industry_snippets = [i.get("snippet", "") for i in context.industry_context]
        context.key_differentiators = self._extract_differentiators(industry_snippets)

        return context

    def _extract_sentiment(self, snippets: List[str]) -> str:
        """Basic sentiment extraction from snippets."""
        if not snippets:
            return "No reviews found"

        # Simple keyword-based sentiment
        positive_keywords = ["great", "excellent", "amazing", "best", "love", "recommend", "professional"]
        negative_keywords = ["bad", "poor", "terrible", "worst", "avoid", "disappointing"]

        combined = " ".join(snippets).lower()

        positive_count = sum(1 for kw in positive_keywords if kw in combined)
        negative_count = sum(1 for kw in negative_keywords if kw in combined)

        if positive_count > negative_count * 2:
            return "Generally positive reviews"
        elif negative_count > positive_count:
            return "Mixed or negative reviews - investigate further"
        else:
            return "Limited or neutral reviews"

    def _extract_differentiators(self, snippets: List[str]) -> List[str]:
        """Extract potential differentiators from industry context."""
        if not snippets:
            return []

        # Simple extraction - in production, use AI
        differentiators = []
        keywords = ["unique", "only", "first", "best", "exclusive", "specialized", "custom"]

        for snippet in snippets:
            for kw in keywords:
                if kw in snippet.lower():
                    # Extract sentence containing keyword
                    sentences = snippet.split(".")
                    for sentence in sentences:
                        if kw in sentence.lower() and len(sentence) > 20:
                            differentiators.append(sentence.strip())
                            break

        return differentiators[:5]  # Return top 5

    def to_dict(self, context: BusinessContext) -> Dict[str, Any]:
        """Convert BusinessContext to dictionary."""
        return asdict(context)


# Convenience function
def search_web(query: str, count: int = 10) -> SearchResults:
    """Perform web search."""
    searcher = WebSearcher()
    return searcher.search(query, count)


def gather_business_context(
    company_name: str,
    owner_name: Optional[str] = None,
    location: Optional[str] = None
) -> BusinessContext:
    """Gather business context from web search."""
    searcher = WebSearcher()
    return searcher.gather_business_context(company_name, owner_name, location)


if __name__ == "__main__":
    import sys

    # Check for API keys
    searcher = WebSearcher()
    print(f"Available providers: {searcher.providers}")

    if len(sys.argv) < 2:
        print("\nUsage: python web_search.py 'Company Name' ['Owner Name'] ['Location']")
        print("\nSet environment variables:")
        print("  BRAVE_SEARCH_API_KEY - Brave Search API key")
        print("  TAVILY_API_KEY - Tavily API key")
        sys.exit(0)

    company = sys.argv[1]
    owner = sys.argv[2] if len(sys.argv) > 2 else None
    location = sys.argv[3] if len(sys.argv) > 3 else None

    print(f"\nGathering context for: {company}")
    if owner:
        print(f"Owner: {owner}")
    if location:
        print(f"Location: {location}")

    context = searcher.gather_business_context(company, owner, location)

    print("\n" + "=" * 60)
    print("BUSINESS CONTEXT")
    print("=" * 60)
    print(json.dumps(searcher.to_dict(context), indent=2))
