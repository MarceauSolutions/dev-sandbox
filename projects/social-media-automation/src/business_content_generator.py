#!/usr/bin/env python3
"""
business_content_generator.py - Multi-Business Content Generator

Generates social media posts for multiple businesses (Square Foot Shipping, SW Florida HVAC).
Integrates with x_scheduler for automated posting.

Usage:
    # Generate posts for a specific business
    python -m src.business_content_generator generate --business squarefoot-shipping --count 5

    # Generate posts for all businesses
    python -m src.business_content_generator generate-all --count 3

    # Generate and schedule posts
    python -m src.business_content_generator generate --business swflorida-hvac --count 5 --schedule

    # List configured businesses
    python -m src.business_content_generator list-businesses

    # Preview content for a business
    python -m src.business_content_generator preview --business squarefoot-shipping --template service_highlight
"""

import json
import random
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "businesses.json"
CONTENT_PATH = PROJECT_ROOT / "templates" / "business_content.json"
OUTPUT_PATH = PROJECT_ROOT / "output"


@dataclass
class GeneratedPost:
    """A generated social media post."""
    business_id: str
    business_name: str
    content: str
    template_used: str
    campaign: str
    hashtags: List[str]
    cta: str
    created_at: str
    scheduled_for: Optional[str] = None
    posted: bool = False


class BusinessContentGenerator:
    """
    Generates content for multiple businesses based on templates and content banks.
    """

    def __init__(self):
        self.config = self._load_config()
        self.content = self._load_content()
        self.businesses = self.config.get("businesses", {})

    def _load_config(self) -> Dict:
        """Load business configuration."""
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                return json.load(f)
        raise FileNotFoundError(f"Business config not found: {CONFIG_PATH}")

    def _load_content(self) -> Dict:
        """Load content templates and banks."""
        if CONTENT_PATH.exists():
            with open(CONTENT_PATH) as f:
                return json.load(f)
        raise FileNotFoundError(f"Content templates not found: {CONTENT_PATH}")

    def list_businesses(self) -> List[Dict]:
        """List all configured businesses."""
        return [
            {
                "id": bid,
                "name": biz.get("name"),
                "type": biz.get("type"),
                "phone": biz.get("phone"),
                "website": biz.get("website")
            }
            for bid, biz in self.businesses.items()
        ]

    def get_business(self, business_id: str) -> Optional[Dict]:
        """Get a specific business configuration."""
        return self.businesses.get(business_id)

    def get_business_content(self, business_id: str) -> Optional[Dict]:
        """Get content bank and templates for a business."""
        return self.content.get(business_id)

    def _select_random_items(self, items: List[str], count: int = 1) -> List[str]:
        """Select random items from a list."""
        return random.sample(items, min(count, len(items)))

    def _format_hashtags(self, business_id: str, campaign: str = "general-awareness") -> List[str]:
        """Get hashtags for a business and campaign."""
        biz = self.businesses.get(business_id, {})
        hashtag_config = biz.get("hashtags", {})
        content_config = self.content.get(business_id, {})
        campaign_config = content_config.get("campaigns", {}).get(campaign, {})

        # Combine hashtags from different sources
        all_hashtags = []
        all_hashtags.extend(hashtag_config.get("primary", [])[:2])
        all_hashtags.extend(hashtag_config.get("local", [])[:1])

        # Add campaign-specific hashtags
        if campaign_config:
            all_hashtags.extend(campaign_config.get("hashtags", [])[:2])

        # Dedupe and limit
        seen = set()
        unique = []
        for h in all_hashtags:
            if h not in seen:
                seen.add(h)
                unique.append(h)
        return unique[:4]  # Max 4 hashtags

    def generate_post(
        self,
        business_id: str,
        template_type: Optional[str] = None,
        campaign: str = "general-awareness"
    ) -> GeneratedPost:
        """
        Generate a single post for a business.

        Args:
            business_id: The business identifier (e.g., 'squarefoot-shipping')
            template_type: Specific template to use, or None for random
            campaign: Campaign to generate for

        Returns:
            GeneratedPost object
        """
        biz = self.get_business(business_id)
        content_bank = self.get_business_content(business_id)

        if not biz or not content_bank:
            raise ValueError(f"Business not found: {business_id}")

        # Get templates
        templates = content_bank.get("post_templates", {})
        if not templates:
            raise ValueError(f"No templates found for: {business_id}")

        # Select template
        if template_type and template_type in templates:
            template_name = template_type
        else:
            template_name = random.choice(list(templates.keys()))

        template = templates[template_name]
        bank = content_bank.get("content_bank", {})

        # Generate content based on template type
        content = self._fill_template(template_name, template, bank, biz, campaign)

        # Get hashtags and CTA
        hashtags = self._format_hashtags(business_id, campaign)
        cta_options = biz.get("cta_options", ["Contact us"])
        cta = random.choice(cta_options)

        return GeneratedPost(
            business_id=business_id,
            business_name=biz["name"],
            content=content,
            template_used=template_name,
            campaign=campaign,
            hashtags=hashtags,
            cta=cta,
            created_at=datetime.now().isoformat()
        )

    def _fill_template(
        self,
        template_name: str,
        template: Dict,
        bank: Dict,
        biz: Dict,
        campaign: str
    ) -> str:
        """Fill a template with content from the bank."""

        # If template has examples, sometimes just use one directly
        examples = template.get("examples", [])
        if examples and random.random() < 0.3:  # 30% chance to use example as-is
            return random.choice(examples)

        # Otherwise, generate dynamically based on template type
        phone = biz.get("phone", "")

        if template_name == "service_highlight":
            services = biz.get("services", [])
            if services:
                service = random.choice(services)
                benefits = self._select_random_items(bank.get("benefits", ["Great service"]), 3)
                hashtags = self._format_hashtags(biz.get("type", ""), campaign)
                return (
                    f"{service['name']} that actually works.\n\n"
                    f"{benefits[0]}\n"
                    f"{benefits[1] if len(benefits) > 1 else ''}\n"
                    f"{benefits[2] if len(benefits) > 2 else ''}\n\n"
                    f"Get a free quote: {phone}\n\n"
                    f"#{hashtags[0] if hashtags else 'Business'} #{hashtags[1] if len(hashtags) > 1 else 'SWFL'}"
                ).strip()

        elif template_name == "pain_solution":
            pain = random.choice(bank.get("pain_points", ["Need help?"]))
            solution = random.choice(bank.get("solutions", ["We can help"]))
            benefit = random.choice(bank.get("benefits", ["Great results"]))
            hashtags = self._format_hashtags(biz.get("type", ""), campaign)
            return (
                f"{pain}\n\n"
                f"That's why we offer {solution.lower()}.\n\n"
                f"{benefit}.\n\n"
                f"Call {phone} for a free quote.\n\n"
                f"#{hashtags[0] if hashtags else 'Business'} #{hashtags[1] if len(hashtags) > 1 else 'SWFL'}"
            )

        elif template_name == "stat_insight" or template_name == "stat_hook":
            stat = random.choice(bank.get("stats", ["Our customers love us"]))
            cta = random.choice(biz.get("cta_options", ["Contact us"]))
            hashtags = self._format_hashtags(biz.get("type", ""), campaign)
            return (
                f"{stat}\n\n"
                f"{cta}: {phone}\n\n"
                f"#{hashtags[0] if hashtags else 'Business'} #{hashtags[1] if len(hashtags) > 1 else 'SWFL'}"
            )

        elif template_name == "tip_list" or template_name == "tip_educational":
            tips = self._select_random_items(bank.get("tips", ["Stay prepared"]), 3)
            topic = "tips for success" if biz.get("type") == "logistics" else "HVAC tips"
            hashtags = self._format_hashtags(biz.get("type", ""), campaign)
            return (
                f"3 {topic}:\n\n"
                f"1. {tips[0]}\n"
                f"2. {tips[1] if len(tips) > 1 else 'Plan ahead'}\n"
                f"3. {tips[2] if len(tips) > 2 else 'Stay prepared'}\n\n"
                f"Need help? {phone}\n\n"
                f"#{hashtags[0] if hashtags else 'Tips'}"
            )

        elif template_name == "emergency_ready":
            urgency = bank.get("urgency_posts", ["Need help fast? We're here."])
            message = random.choice(urgency)
            hashtags = self._format_hashtags(biz.get("type", ""), campaign)
            return (
                f"{message}\n\n"
                f"{phone}\n\n"
                f"#{hashtags[0] if hashtags else 'Emergency'} #{hashtags[1] if len(hashtags) > 1 else 'SWFL'}"
            )

        elif template_name == "local_pride":
            area = biz.get("service_area", "Southwest Florida")
            tagline = biz.get("brand", {}).get("tagline", "Here to help")
            services = [s["name"] for s in biz.get("services", [])[:3]]
            hashtags = self._format_hashtags(biz.get("type", ""), campaign)
            return (
                f"Proudly serving {area}.\n\n"
                f"{chr(10).join(services)}\n\n"
                f"{tagline}\n\n"
                f"{phone}\n\n"
                f"#{hashtags[0] if hashtags else 'LocalBusiness'} #{hashtags[1] if len(hashtags) > 1 else 'SWFL'}"
            )

        # Fallback: use an example if available
        if examples:
            return random.choice(examples)

        # Ultimate fallback
        return f"Contact {biz['name']} for great service. {phone}"

    def generate_batch(
        self,
        business_id: str,
        count: int = 5,
        campaign: str = "general-awareness"
    ) -> List[GeneratedPost]:
        """Generate multiple posts for a business."""
        posts = []
        templates = list(self.content.get(business_id, {}).get("post_templates", {}).keys())

        for i in range(count):
            # Rotate through templates
            template = templates[i % len(templates)] if templates else None
            post = self.generate_post(business_id, template, campaign)
            posts.append(post)

        return posts

    def generate_all_businesses(
        self,
        count_per_business: int = 3,
        campaign: str = "general-awareness"
    ) -> Dict[str, List[GeneratedPost]]:
        """Generate posts for all configured businesses."""
        all_posts = {}
        for business_id in self.businesses.keys():
            all_posts[business_id] = self.generate_batch(business_id, count_per_business, campaign)
        return all_posts

    def schedule_posts(
        self,
        posts: List[GeneratedPost],
        start_time: Optional[datetime] = None,
        interval_hours: int = 4
    ) -> List[GeneratedPost]:
        """
        Schedule posts for future posting.

        Args:
            posts: List of posts to schedule
            start_time: When to start (defaults to next optimal time)
            interval_hours: Hours between posts

        Returns:
            Posts with scheduled_for filled in
        """
        from .x_scheduler import PostScheduler

        scheduler = PostScheduler()
        current_time = start_time or datetime.now()

        for i, post in enumerate(posts):
            scheduled_time = current_time + timedelta(hours=i * interval_hours)
            post.scheduled_for = scheduled_time.isoformat()

            # Add to scheduler queue
            scheduler.add_post(
                text=post.content,
                priority="normal",
                campaign=f"{post.business_id}-{post.campaign}",
                scheduled_time=scheduled_time.strftime("%Y-%m-%d %H:%M")
            )

        return posts

    def save_generated_posts(self, posts: List[GeneratedPost], filename: str = None):
        """Save generated posts to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_posts_{timestamp}.json"

        output_file = OUTPUT_PATH / filename
        output_file.parent.mkdir(parents=True, exist_ok=True)

        posts_data = [
            {
                "business_id": p.business_id,
                "business_name": p.business_name,
                "content": p.content,
                "template_used": p.template_used,
                "campaign": p.campaign,
                "hashtags": p.hashtags,
                "cta": p.cta,
                "created_at": p.created_at,
                "scheduled_for": p.scheduled_for,
                "posted": p.posted
            }
            for p in posts
        ]

        with open(output_file, 'w') as f:
            json.dump(posts_data, f, indent=2)

        print(f"Saved {len(posts)} posts to {output_file}")
        return output_file


def main():
    parser = argparse.ArgumentParser(description="Multi-Business Content Generator")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # list-businesses command
    list_parser = subparsers.add_parser("list-businesses", help="List configured businesses")

    # generate command
    gen_parser = subparsers.add_parser("generate", help="Generate posts for a business")
    gen_parser.add_argument("--business", "-b", required=True, help="Business ID")
    gen_parser.add_argument("--count", "-c", type=int, default=5, help="Number of posts")
    gen_parser.add_argument("--campaign", default="general-awareness", help="Campaign name")
    gen_parser.add_argument("--schedule", "-s", action="store_true", help="Schedule posts")
    gen_parser.add_argument("--save", action="store_true", help="Save posts to file")

    # generate-all command
    all_parser = subparsers.add_parser("generate-all", help="Generate for all businesses")
    all_parser.add_argument("--count", "-c", type=int, default=3, help="Posts per business")
    all_parser.add_argument("--campaign", default="general-awareness", help="Campaign name")
    all_parser.add_argument("--schedule", "-s", action="store_true", help="Schedule posts")
    all_parser.add_argument("--save", action="store_true", help="Save posts to file")

    # preview command
    preview_parser = subparsers.add_parser("preview", help="Preview a template")
    preview_parser.add_argument("--business", "-b", required=True, help="Business ID")
    preview_parser.add_argument("--template", "-t", help="Template name")
    preview_parser.add_argument("--count", "-c", type=int, default=3, help="Number of previews")

    args = parser.parse_args()
    generator = BusinessContentGenerator()

    if args.command == "list-businesses":
        businesses = generator.list_businesses()
        print("\nConfigured Businesses:")
        print("-" * 50)
        for biz in businesses:
            print(f"\n  ID: {biz['id']}")
            print(f"  Name: {biz['name']}")
            print(f"  Type: {biz['type']}")
            print(f"  Phone: {biz['phone']}")
            print(f"  Website: {biz['website']}")
        print()

    elif args.command == "generate":
        print(f"\nGenerating {args.count} posts for {args.business}...")
        posts = generator.generate_batch(args.business, args.count, args.campaign)

        for i, post in enumerate(posts, 1):
            print(f"\n--- Post {i} ({post.template_used}) ---")
            print(post.content)
            print(f"Hashtags: {', '.join(post.hashtags)}")

        if args.schedule:
            print("\nScheduling posts...")
            posts = generator.schedule_posts(posts)
            for post in posts:
                print(f"  Scheduled: {post.scheduled_for}")

        if args.save:
            generator.save_generated_posts(posts)

    elif args.command == "generate-all":
        print(f"\nGenerating {args.count} posts per business...")
        all_posts = generator.generate_all_businesses(args.count, args.campaign)

        all_flat = []
        for business_id, posts in all_posts.items():
            print(f"\n=== {business_id} ===")
            for i, post in enumerate(posts, 1):
                print(f"\n--- Post {i} ({post.template_used}) ---")
                print(post.content[:150] + "..." if len(post.content) > 150 else post.content)
            all_flat.extend(posts)

        if args.schedule:
            print("\nScheduling all posts...")
            all_flat = generator.schedule_posts(all_flat)

        if args.save:
            generator.save_generated_posts(all_flat, "all_businesses_posts.json")

    elif args.command == "preview":
        print(f"\nPreviewing templates for {args.business}...")
        for i in range(args.count):
            post = generator.generate_post(args.business, args.template)
            print(f"\n--- Preview {i+1} ({post.template_used}) ---")
            print(post.content)
            print(f"Characters: {len(post.content)}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
