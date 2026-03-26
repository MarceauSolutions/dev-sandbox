#!/usr/bin/env python3
"""
grok_infographic_gen.py - AI Infographic Generation for Cold Outreach & Social Media

WHAT: Generate compelling infographics using Grok Imagine (Aurora model)
WHY: Visual content increases engagement 94% - critical for cold outreach and social
INPUT: Infographic type, topic, customization options
OUTPUT: Generated image file ready for use
COST: $0.07 per image

QUICK USAGE:
  # Generate cold outreach infographic
  python -m src.grok_infographic_gen cold-outreach --pain-point no_website

  # Generate social media infographic
  python -m src.grok_infographic_gen social --topic automation_stats

  # Generate with custom text
  python -m src.grok_infographic_gen custom --text "80% of customers search online first"

GROK IMAGINE BEST PRACTICES (as of Jan 2026):
  - Use detailed, specific prompts
  - Request "clean, professional design" for business content
  - Include "text clearly visible" for text-heavy graphics
  - Aurora model excels at photorealistic rendering and text accuracy
  - Keep text short (Grok handles ~20 words well, struggles with paragraphs)
"""

import argparse
import sys
import os
import json
from pathlib import Path
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()


class GrokInfographicGenerator:
    """
    Generate infographics using Grok Imagine API optimized for business use.
    """

    API_URL = "https://api.x.ai/v1/images/generations"
    MODEL = "grok-2-image-1212"
    COST_PER_IMAGE = 0.07

    # Output directory for generated infographics
    OUTPUT_DIR = Path(__file__).parent.parent / "output" / "infographics"

    # Infographic templates for cold outreach
    COLD_OUTREACH_TEMPLATES = {
        "no_website": {
            "headline": "80% of customers search online first",
            "subtext": "Is your business invisible?",
            "cta": "Free Website Audit",
            "style": "dark_professional",
            "colors": "electric blue accent on dark background"
        },
        "few_reviews": {
            "headline": "93% read reviews before buying",
            "subtext": "Your competition has 4.8 stars",
            "cta": "Get More Reviews",
            "style": "star_rating",
            "colors": "gold stars on dark navy"
        },
        "no_online_payments": {
            "headline": "67% prefer paying online",
            "subtext": "Don't lose customers at checkout",
            "cta": "Free Payment Setup",
            "style": "payment_icons",
            "colors": "green money accent on clean white"
        },
        "local_seo": {
            "headline": "46% of Google searches are local",
            "subtext": "Are you showing up?",
            "cta": "Free SEO Check",
            "style": "map_pin",
            "colors": "red pin on map background"
        },
        "competitor_analysis": {
            "headline": "Your competitors are already online",
            "subtext": "Don't get left behind",
            "cta": "See Their Strategy",
            "style": "comparison_chart",
            "colors": "red vs green comparison"
        }
    }

    # Social media infographic templates
    SOCIAL_MEDIA_TEMPLATES = {
        "automation_stats": {
            "headline": "AI Automation saves 40+ hours/month",
            "points": ["Email Management", "Social Posting", "Lead Follow-up"],
            "style": "modern_tech",
            "colors": "cyan gradient on dark"
        },
        "business_growth": {
            "headline": "3X Your Business Growth",
            "points": ["Automate repetitive tasks", "Focus on high-value work", "Scale without hiring"],
            "style": "growth_chart",
            "colors": "green upward trend"
        },
        "time_savings": {
            "headline": "What would you do with 10 extra hours?",
            "points": ["Strategic planning", "Client relationships", "Personal time"],
            "style": "clock_visual",
            "colors": "orange highlights on minimal background"
        },
        "ai_tips": {
            "headline": "5 Ways AI Can Help Your Business Today",
            "points": ["Customer service chatbots", "Email automation", "Social media scheduling",
                      "Lead scoring", "Invoice processing"],
            "style": "numbered_list",
            "colors": "professional blue theme"
        },
        "cost_comparison": {
            "headline": "Hire an Employee vs. AI Automation",
            "points": ["$50K/year salary vs $200/month", "40 hours/week vs 24/7", "Training vs instant"],
            "style": "side_by_side",
            "colors": "red/green cost comparison"
        }
    }

    def __init__(self, api_key=None):
        """Initialize with xAI API key."""
        self.api_key = api_key or os.getenv('XAI_API_KEY')

        if not self.api_key:
            print("ERROR: XAI_API_KEY not found in environment")
            print("Set it in .env file or export XAI_API_KEY=your_key")
            sys.exit(1)

        # Create output directory
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        self.images_generated = 0
        self.total_cost = 0.0

    def _build_cold_outreach_prompt(self, pain_point: str) -> str:
        """Build optimized prompt for cold outreach infographic."""
        template = self.COLD_OUTREACH_TEMPLATES.get(pain_point)
        if not template:
            raise ValueError(f"Unknown pain point: {pain_point}. Available: {list(self.COLD_OUTREACH_TEMPLATES.keys())}")

        # Grok Imagine prompt optimized for business infographics
        prompt = f"""Create a professional business infographic with the following specifications:

MAIN TEXT (large, bold, centered): "{template['headline']}"
SUBTEXT (smaller, below main): "{template['subtext']}"
CALL TO ACTION (button style at bottom): "{template['cta']}"

DESIGN REQUIREMENTS:
- Style: {template['style']} - clean, modern, professional
- Colors: {template['colors']}
- Layout: Vertical format, mobile-friendly proportions
- Text must be clearly readable and spelled correctly
- Include subtle business/tech visual elements that support the message
- Professional gradient or solid background
- The text should be the focal point
- Marceau Solutions branding at bottom (small logo placeholder area)

The overall feel should be: trustworthy, professional, compelling to a small business owner.
This is for B2B cold outreach - it needs to grab attention and communicate value quickly."""

        return prompt

    def _build_social_media_prompt(self, topic: str) -> str:
        """Build optimized prompt for social media infographic."""
        template = self.SOCIAL_MEDIA_TEMPLATES.get(topic)
        if not template:
            raise ValueError(f"Unknown topic: {topic}. Available: {list(self.SOCIAL_MEDIA_TEMPLATES.keys())}")

        points_text = "\n".join(f"- {point}" for point in template.get('points', []))

        prompt = f"""Create a social media infographic with these specifications:

HEADLINE (bold, attention-grabbing): "{template['headline']}"
KEY POINTS (if applicable):
{points_text}

DESIGN REQUIREMENTS:
- Style: {template['style']} - eye-catching, shareable
- Colors: {template['colors']}
- Layout: Square format (1080x1080) optimized for social media
- Modern, clean design with good whitespace
- Text must be large enough to read on mobile
- Include relevant icons or visual elements
- Professional but not corporate - approachable feel
- Subtle branding area at bottom

The overall feel should be: engaging, informative, share-worthy.
This is for X/Twitter and LinkedIn - needs to stop the scroll."""

        return prompt

    def _build_custom_prompt(self, text: str, style: str = "professional") -> str:
        """Build prompt for custom infographic."""
        styles = {
            "professional": "clean, corporate, trustworthy - navy and white color scheme",
            "modern": "bold, tech-forward, innovative - gradient blues and purples",
            "minimal": "simple, clean, lots of whitespace - black text on white",
            "bold": "high contrast, attention-grabbing - bright colors on dark background",
            "stats": "data visualization focused - charts, numbers, comparisons"
        }

        style_desc = styles.get(style, styles["professional"])

        prompt = f"""Create a professional infographic featuring:

MAIN MESSAGE: "{text}"

DESIGN:
- Style: {style_desc}
- The text should be the absolute focal point
- Professional, business-appropriate design
- Text must be clearly legible and correctly spelled
- Include subtle supporting visual elements
- Square format for social media compatibility

This should look like something from a professional marketing agency."""

        return prompt

    def generate_image(self, prompt: str, output_name: str = None) -> dict:
        """
        Generate image using Grok Imagine API.

        Args:
            prompt: Full image generation prompt
            output_name: Optional filename (without extension)

        Returns:
            Dict with url, path, cost info
        """
        print(f"\n{'='*70}")
        print("GROK INFOGRAPHIC GENERATION")
        print(f"{'='*70}")
        print(f"Prompt preview: {prompt[:100]}...")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "prompt": prompt,
            "n": 1,
            "model": self.MODEL
        }

        print(f"\n→ Generating infographic...")

        try:
            response = requests.post(
                self.API_URL,
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code != 200:
                print(f"  ✗ API Error: {response.status_code}")
                print(f"  {response.text}")
                return {"success": False, "error": response.text}

            data = response.json()
            images = data.get('data', [])

            if not images:
                print("  ✗ No images returned")
                return {"success": False, "error": "No images returned"}

            image_url = images[0].get('url')
            self.images_generated += 1
            self.total_cost += self.COST_PER_IMAGE

            print(f"  ✓ Image generated")
            print(f"  💰 Cost: ${self.COST_PER_IMAGE:.2f}")

            # Download and save image
            if output_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{output_name}_{timestamp}.png"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"infographic_{timestamp}.png"

            output_path = self.OUTPUT_DIR / filename

            img_response = requests.get(image_url, timeout=30)
            if img_response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(img_response.content)
                print(f"  ✓ Saved: {output_path}")
            else:
                print(f"  ⚠ Could not download image, URL available")
                output_path = None

            result = {
                "success": True,
                "url": image_url,
                "path": str(output_path) if output_path else None,
                "cost": self.COST_PER_IMAGE,
                "prompt_preview": prompt[:200]
            }

            print(f"\n✅ SUCCESS!")
            print(f"{'='*70}\n")

            return result

        except requests.RequestException as e:
            print(f"  ✗ Request failed: {e}")
            return {"success": False, "error": str(e)}

    def generate_cold_outreach(self, pain_point: str) -> dict:
        """Generate cold outreach infographic for specific pain point."""
        prompt = self._build_cold_outreach_prompt(pain_point)
        return self.generate_image(prompt, f"cold_outreach_{pain_point}")

    def generate_social_media(self, topic: str) -> dict:
        """Generate social media infographic for specific topic."""
        prompt = self._build_social_media_prompt(topic)
        return self.generate_image(prompt, f"social_{topic}")

    def generate_custom(self, text: str, style: str = "professional") -> dict:
        """Generate custom infographic with specified text."""
        prompt = self._build_custom_prompt(text, style)
        # Create safe filename from text
        safe_name = "".join(c if c.isalnum() else "_" for c in text[:30])
        return self.generate_image(prompt, f"custom_{safe_name}")

    def generate_batch(self, infographic_type: str, items: list) -> list:
        """
        Generate multiple infographics.

        Args:
            infographic_type: 'cold_outreach' or 'social_media'
            items: List of pain_points or topics

        Returns:
            List of generation results
        """
        results = []

        for item in items:
            if infographic_type == "cold_outreach":
                result = self.generate_cold_outreach(item)
            elif infographic_type == "social_media":
                result = self.generate_social_media(item)
            else:
                print(f"Unknown type: {infographic_type}")
                continue

            results.append({
                "item": item,
                **result
            })

        print(f"\n📊 BATCH SUMMARY:")
        print(f"   Generated: {len([r for r in results if r.get('success')])}/{len(items)}")
        print(f"   Total cost: ${self.total_cost:.2f}")

        return results

    def list_templates(self):
        """List all available templates."""
        print("\n📋 COLD OUTREACH TEMPLATES:")
        print("-" * 40)
        for name, template in self.COLD_OUTREACH_TEMPLATES.items():
            print(f"  {name}:")
            print(f"    Headline: {template['headline']}")
            print(f"    CTA: {template['cta']}")
            print()

        print("\n📱 SOCIAL MEDIA TEMPLATES:")
        print("-" * 40)
        for name, template in self.SOCIAL_MEDIA_TEMPLATES.items():
            print(f"  {name}:")
            print(f"    Headline: {template['headline']}")
            print()


def main():
    """CLI for infographic generation."""
    parser = argparse.ArgumentParser(
        description='Generate infographics using Grok Imagine for cold outreach and social media'
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Cold outreach command
    cold_parser = subparsers.add_parser('cold-outreach', help='Generate cold outreach infographic')
    cold_parser.add_argument('--pain-point', required=True,
                            choices=list(GrokInfographicGenerator.COLD_OUTREACH_TEMPLATES.keys()),
                            help='Pain point to target')

    # Social media command
    social_parser = subparsers.add_parser('social', help='Generate social media infographic')
    social_parser.add_argument('--topic', required=True,
                              choices=list(GrokInfographicGenerator.SOCIAL_MEDIA_TEMPLATES.keys()),
                              help='Topic for infographic')

    # Custom command
    custom_parser = subparsers.add_parser('custom', help='Generate custom infographic')
    custom_parser.add_argument('--text', required=True, help='Main text for infographic')
    custom_parser.add_argument('--style', default='professional',
                              choices=['professional', 'modern', 'minimal', 'bold', 'stats'],
                              help='Visual style')

    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Generate batch of infographics')
    batch_parser.add_argument('--type', required=True, choices=['cold_outreach', 'social_media'],
                             help='Type of infographics')
    batch_parser.add_argument('--all', action='store_true', help='Generate all templates')
    batch_parser.add_argument('--items', nargs='+', help='Specific items to generate')

    # List templates command
    list_parser = subparsers.add_parser('list', help='List available templates')

    args = parser.parse_args()

    generator = GrokInfographicGenerator()

    if args.command == 'cold-outreach':
        result = generator.generate_cold_outreach(args.pain_point)
        if result.get('success'):
            print(f"\n✅ Infographic ready: {result.get('path')}")
        else:
            print(f"\n❌ Failed: {result.get('error')}")
            return 1

    elif args.command == 'social':
        result = generator.generate_social_media(args.topic)
        if result.get('success'):
            print(f"\n✅ Infographic ready: {result.get('path')}")
        else:
            print(f"\n❌ Failed: {result.get('error')}")
            return 1

    elif args.command == 'custom':
        result = generator.generate_custom(args.text, args.style)
        if result.get('success'):
            print(f"\n✅ Infographic ready: {result.get('path')}")
        else:
            print(f"\n❌ Failed: {result.get('error')}")
            return 1

    elif args.command == 'batch':
        if args.all:
            if args.type == 'cold_outreach':
                items = list(GrokInfographicGenerator.COLD_OUTREACH_TEMPLATES.keys())
            else:
                items = list(GrokInfographicGenerator.SOCIAL_MEDIA_TEMPLATES.keys())
        elif args.items:
            items = args.items
        else:
            print("ERROR: Specify --all or --items")
            return 1

        results = generator.generate_batch(args.type, items)
        successful = [r for r in results if r.get('success')]
        print(f"\n✅ Generated {len(successful)}/{len(items)} infographics")
        print(f"📁 Output: {generator.OUTPUT_DIR}")

    elif args.command == 'list':
        generator.list_templates()

    else:
        parser.print_help()

    return 0


if __name__ == '__main__':
    sys.exit(main())
