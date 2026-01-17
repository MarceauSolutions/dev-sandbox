#!/usr/bin/env python3
"""
link_manager.py - UTM Tracking and Link Management

Handles:
- Adding UTM parameters to links
- Short link creation (optional)
- Link-in-bio page tracking
- Conversion tracking from X to landing pages

Usage:
    from link_manager import LinkManager

    manager = LinkManager()
    tracked_url = manager.add_utm_params(
        "https://marceausolutions.com/fitness",
        utm_source="x",
        utm_medium="social",
        utm_campaign="fitness-launch"
    )
"""

import os
import re
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
from dataclasses import dataclass, asdict, field
import logging

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TrackedLink:
    """A tracked link with UTM parameters."""
    id: str
    original_url: str
    tracked_url: str
    utm_source: str
    utm_medium: str
    utm_campaign: str
    utm_content: Optional[str] = None
    utm_term: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    click_count: int = 0
    last_clicked: Optional[str] = None


@dataclass
class LinkClick:
    """Record of a link click."""
    link_id: str
    timestamp: str
    referrer: Optional[str] = None
    user_agent: Optional[str] = None


class LinkManager:
    """
    Manages UTM tracking for links in social media posts.
    """

    LINKS_FILE = Path(__file__).parent.parent / "output" / "tracked_links.json"
    CLICKS_FILE = Path(__file__).parent.parent / "output" / "link_clicks.json"

    # Default UTM parameters
    DEFAULT_UTM = {
        "utm_source": "x",
        "utm_medium": "social",
        "utm_campaign": "auto"
    }

    # Landing pages to track
    LANDING_PAGES = [
        "marceausolutions.com",
        "fitnessinfluencer.io",  # Example
    ]

    # URL regex pattern
    URL_PATTERN = re.compile(
        r'https?://[^\s<>"{}|\\^`\[\]]+'
    )

    def __init__(self):
        self.links = self._load_links()
        self.clicks = self._load_clicks()

    def _load_links(self) -> Dict[str, TrackedLink]:
        """Load tracked links from file."""
        if self.LINKS_FILE.exists():
            try:
                with open(self.LINKS_FILE) as f:
                    data = json.load(f)
                return {k: TrackedLink(**v) for k, v in data.items()}
            except Exception as e:
                logger.warning(f"Error loading links: {e}")
        return {}

    def _save_links(self):
        """Save tracked links to file."""
        self.LINKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.LINKS_FILE, 'w') as f:
            json.dump({k: asdict(v) for k, v in self.links.items()}, f, indent=2)

    def _load_clicks(self) -> List[LinkClick]:
        """Load click history."""
        if self.CLICKS_FILE.exists():
            try:
                with open(self.CLICKS_FILE) as f:
                    data = json.load(f)
                return [LinkClick(**c) for c in data]
            except Exception:
                pass
        return []

    def _save_clicks(self):
        """Save click history."""
        self.CLICKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.CLICKS_FILE, 'w') as f:
            # Keep last 10000 clicks
            recent = self.clicks[-10000:]
            json.dump([asdict(c) for c in recent], f, indent=2)

    def _generate_link_id(self, url: str, params: Dict) -> str:
        """Generate unique link ID."""
        combined = f"{url}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(combined.encode()).hexdigest()[:12]

    def _should_track(self, url: str) -> bool:
        """Check if URL should have UTM tracking added."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove www prefix
        if domain.startswith("www."):
            domain = domain[4:]

        # Check if it's one of our landing pages
        for landing_page in self.LANDING_PAGES:
            if domain == landing_page or domain.endswith(f".{landing_page}"):
                return True

        return False

    def add_utm_params(
        self,
        url: str,
        utm_source: Optional[str] = None,
        utm_medium: Optional[str] = None,
        utm_campaign: Optional[str] = None,
        utm_content: Optional[str] = None,
        utm_term: Optional[str] = None
    ) -> str:
        """
        Add UTM parameters to a URL.

        Args:
            url: Original URL
            utm_source: Traffic source (default: x)
            utm_medium: Marketing medium (default: social)
            utm_campaign: Campaign name
            utm_content: Content variant (for A/B testing)
            utm_term: Search term (if applicable)

        Returns:
            URL with UTM parameters
        """
        parsed = urlparse(url)

        # Get existing query params
        existing_params = parse_qs(parsed.query)

        # Build UTM params (don't override existing)
        utm_params = {}
        if utm_source and "utm_source" not in existing_params:
            utm_params["utm_source"] = utm_source
        if utm_medium and "utm_medium" not in existing_params:
            utm_params["utm_medium"] = utm_medium
        if utm_campaign and "utm_campaign" not in existing_params:
            utm_params["utm_campaign"] = utm_campaign
        if utm_content and "utm_content" not in existing_params:
            utm_params["utm_content"] = utm_content
        if utm_term and "utm_term" not in existing_params:
            utm_params["utm_term"] = utm_term

        # Combine existing and new params
        all_params = {**{k: v[0] for k, v in existing_params.items()}, **utm_params}

        # Rebuild URL
        new_query = urlencode(all_params)
        new_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))

        return new_url

    def create_tracked_link(
        self,
        url: str,
        utm_source: str = "x",
        utm_medium: str = "social",
        utm_campaign: str = "auto",
        utm_content: Optional[str] = None,
        utm_term: Optional[str] = None
    ) -> TrackedLink:
        """
        Create a tracked link with UTM parameters.

        Args:
            url: Original URL
            utm_*: UTM parameters

        Returns:
            TrackedLink object
        """
        tracked_url = self.add_utm_params(
            url,
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
            utm_content=utm_content,
            utm_term=utm_term
        )

        link_id = self._generate_link_id(url, {
            "utm_source": utm_source,
            "utm_medium": utm_medium,
            "utm_campaign": utm_campaign
        })

        # Check if link already exists
        if link_id in self.links:
            return self.links[link_id]

        link = TrackedLink(
            id=link_id,
            original_url=url,
            tracked_url=tracked_url,
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
            utm_content=utm_content,
            utm_term=utm_term
        )

        self.links[link_id] = link
        self._save_links()

        logger.info(f"Created tracked link: {link_id}")
        return link

    def process_text(self, text: str, utm_params: Optional[Dict[str, str]] = None) -> str:
        """
        Process text and add UTM tracking to all relevant URLs.

        Args:
            text: Text containing URLs
            utm_params: UTM parameters to add

        Returns:
            Text with tracked URLs
        """
        if utm_params is None:
            utm_params = self.DEFAULT_UTM.copy()

        def replace_url(match):
            url = match.group(0)

            # Only track our landing pages
            if not self._should_track(url):
                return url

            # Add UTM params
            tracked = self.add_utm_params(
                url,
                utm_source=utm_params.get("utm_source"),
                utm_medium=utm_params.get("utm_medium"),
                utm_campaign=utm_params.get("utm_campaign"),
                utm_content=utm_params.get("utm_content"),
                utm_term=utm_params.get("utm_term")
            )

            # Create tracked link record
            self.create_tracked_link(
                url,
                **utm_params
            )

            return tracked

        return self.URL_PATTERN.sub(replace_url, text)

    def record_click(
        self,
        link_id: str,
        referrer: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Record a click on a tracked link."""
        if link_id in self.links:
            self.links[link_id].click_count += 1
            self.links[link_id].last_clicked = datetime.now().isoformat()
            self._save_links()

        click = LinkClick(
            link_id=link_id,
            timestamp=datetime.now().isoformat(),
            referrer=referrer,
            user_agent=user_agent
        )
        self.clicks.append(click)
        self._save_clicks()

    def get_link_stats(self, link_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for tracked links.

        Args:
            link_id: Specific link ID (optional, returns all if None)

        Returns:
            Statistics dictionary
        """
        if link_id:
            if link_id in self.links:
                link = self.links[link_id]
                return {
                    "id": link.id,
                    "original_url": link.original_url,
                    "tracked_url": link.tracked_url,
                    "clicks": link.click_count,
                    "campaign": link.utm_campaign,
                    "created_at": link.created_at,
                    "last_clicked": link.last_clicked
                }
            return {}

        # Aggregate stats
        stats = {
            "total_links": len(self.links),
            "total_clicks": sum(l.click_count for l in self.links.values()),
            "by_campaign": {},
            "by_source": {},
            "top_links": []
        }

        for link in self.links.values():
            # By campaign
            campaign = link.utm_campaign
            if campaign not in stats["by_campaign"]:
                stats["by_campaign"][campaign] = {"links": 0, "clicks": 0}
            stats["by_campaign"][campaign]["links"] += 1
            stats["by_campaign"][campaign]["clicks"] += link.click_count

            # By source
            source = link.utm_source
            if source not in stats["by_source"]:
                stats["by_source"][source] = {"links": 0, "clicks": 0}
            stats["by_source"][source]["links"] += 1
            stats["by_source"][source]["clicks"] += link.click_count

        # Top links by clicks
        sorted_links = sorted(
            self.links.values(),
            key=lambda l: l.click_count,
            reverse=True
        )[:10]
        stats["top_links"] = [
            {
                "id": l.id,
                "url": l.original_url,
                "clicks": l.click_count,
                "campaign": l.utm_campaign
            }
            for l in sorted_links
        ]

        return stats

    def get_campaign_links(self, campaign: str) -> List[TrackedLink]:
        """Get all links for a campaign."""
        return [l for l in self.links.values() if l.utm_campaign == campaign]

    def generate_link_in_bio(self, links: List[Dict[str, str]], campaign: str = "linkinbio") -> str:
        """
        Generate tracked links for a link-in-bio page.

        Args:
            links: List of {"label": "...", "url": "..."} dicts
            campaign: Campaign name for tracking

        Returns:
            JSON string of tracked links
        """
        tracked = []
        for link in links:
            tracked_link = self.create_tracked_link(
                link["url"],
                utm_source="x",
                utm_medium="linkinbio",
                utm_campaign=campaign,
                utm_content=link.get("label", "")
            )
            tracked.append({
                "label": link["label"],
                "url": tracked_link.tracked_url
            })
        return json.dumps(tracked, indent=2)


def main():
    """CLI for link manager."""
    import argparse

    parser = argparse.ArgumentParser(description='Link Manager with UTM Tracking')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Track command
    track_parser = subparsers.add_parser('track', help='Create tracked link')
    track_parser.add_argument('url', help='URL to track')
    track_parser.add_argument('--source', default='x', help='UTM source')
    track_parser.add_argument('--medium', default='social', help='UTM medium')
    track_parser.add_argument('--campaign', default='auto', help='UTM campaign')

    # Process command
    process_parser = subparsers.add_parser('process', help='Process text with URLs')
    process_parser.add_argument('text', help='Text containing URLs')
    process_parser.add_argument('--campaign', default='auto', help='UTM campaign')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show link statistics')
    stats_parser.add_argument('--link-id', help='Specific link ID')
    stats_parser.add_argument('--campaign', help='Filter by campaign')

    # List command
    list_parser = subparsers.add_parser('list', help='List tracked links')
    list_parser.add_argument('--campaign', help='Filter by campaign')

    args = parser.parse_args()

    manager = LinkManager()

    if args.command == 'track':
        link = manager.create_tracked_link(
            args.url,
            utm_source=args.source,
            utm_medium=args.medium,
            utm_campaign=args.campaign
        )
        print(f"\nTracked Link Created:")
        print(f"  ID: {link.id}")
        print(f"  Original: {link.original_url}")
        print(f"  Tracked: {link.tracked_url}")

    elif args.command == 'process':
        processed = manager.process_text(
            args.text,
            {"utm_source": "x", "utm_medium": "social", "utm_campaign": args.campaign}
        )
        print(f"\nProcessed text:")
        print(processed)

    elif args.command == 'stats':
        if args.link_id:
            stats = manager.get_link_stats(args.link_id)
            if stats:
                print(f"\nLink Stats ({args.link_id}):")
                print(f"  Original: {stats['original_url']}")
                print(f"  Clicks: {stats['clicks']}")
                print(f"  Campaign: {stats['campaign']}")
                print(f"  Last Clicked: {stats['last_clicked'] or 'Never'}")
            else:
                print(f"Link {args.link_id} not found")
        else:
            stats = manager.get_link_stats()
            print(f"\nLink Statistics:")
            print(f"  Total Links: {stats['total_links']}")
            print(f"  Total Clicks: {stats['total_clicks']}")

            if stats['by_campaign']:
                print(f"\n  By Campaign:")
                for campaign, data in stats['by_campaign'].items():
                    print(f"    {campaign}: {data['links']} links, {data['clicks']} clicks")

            if stats['top_links']:
                print(f"\n  Top Links:")
                for link in stats['top_links'][:5]:
                    print(f"    [{link['clicks']} clicks] {link['url'][:50]}...")

    elif args.command == 'list':
        links = manager.links.values()
        if args.campaign:
            links = [l for l in links if l.utm_campaign == args.campaign]

        if not links:
            print("\nNo tracked links found")
        else:
            print(f"\nTracked Links ({len(list(links))}):")
            for link in links:
                print(f"  [{link.id}] {link.utm_campaign} | {link.click_count} clicks")
                print(f"    {link.original_url[:60]}...")

    else:
        parser.print_help()

    return 0


if __name__ == '__main__':
    exit(main())
