#!/usr/bin/env python3
"""
outreach_image_generator.py - Generate personalized images for cold outreach

WHAT: Create custom mockup/visual images for each business in cold outreach campaigns
WHY: Significantly increase response rates with visual proof of value
INPUT: Lead data (business name, pain point, industry)
OUTPUT: Personalized image (mockup, infographic, before/after)
COST: $0.07 per image via Grok
TIME: ~10-15 seconds per image

USAGE:
    # Generate mockup for gym with no website
    python -m src.outreach_image_generator generate \
        --business-name "Hardcore Gym Naples" \
        --pain-point no_website \
        --output mockups/hardcore_gym.png

    # Batch generate for all leads in file
    python -m src.outreach_image_generator batch \
        --leads output/leads.json \
        --output-dir mockups/

    # Generate savings infographic for shipping lead
    python -m src.outreach_image_generator generate \
        --business-name "Acme E-commerce" \
        --pain-point high_shipping_costs \
        --template savings_infographic \
        --output mockups/acme_savings.png

INTEGRATION WITH COLD OUTREACH:
    1. cold_outreach.py generates personalized email
    2. This tool generates personalized image mockup
    3. Email includes: "Here's what your site could look like: [image]"
    4. Attach image to email or upload to hosting and link
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, List
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

# Import Grok image generator
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared" / "utils"))
from grok_image_gen import GrokImageGenerator

logger = logging.getLogger(__name__)


class OutreachImageGenerator:
    """
    Generate personalized mockup images for cold outreach campaigns.
    """

    # Prompt templates for different pain points
    PROMPT_TEMPLATES = {
        "no_website": {
            "gym": "Professional website mockup for '{business_name}', a modern fitness gym. "
                   "Clean design with hero image of people working out, class schedule section, "
                   "membership pricing cards, and contact form. Navy blue and orange color scheme. "
                   "Mobile-friendly layout. Photorealistic browser mockup.",

            "hvac": "Professional website mockup for '{business_name}', an HVAC company. "
                    "Clean design with hero image of technician, service areas map, "
                    "emergency contact button, and customer testimonials. Blue and white color scheme. "
                    "Photorealistic browser mockup.",

            "default": "Professional website mockup for '{business_name}'. "
                      "Modern, clean design with hero section, services overview, and contact form. "
                      "Photorealistic browser mockup."
        },

        "high_shipping_costs": {
            "default": "Infographic showing shipping cost savings for '{business_name}'. "
                      "Before/after comparison: Current carrier ($X/month) vs Square Foot Shipping ($Y/month). "
                      "Professional chart with dollar signs, arrows showing 40% savings. "
                      "Clean, business-friendly design."
        },

        "few_reviews": {
            "gym": "Before/after mockup showing '{business_name}' Google listing. "
                   "Left side: 12 reviews, 4.2 stars. Right side: 67 reviews, 4.8 stars. "
                   "Arrow between them showing growth. Professional, clean design.",

            "default": "Before/after mockup showing '{business_name}' online reviews. "
                      "Left: few reviews. Right: many 5-star reviews. Professional design."
        },

        "no_online_booking": {
            "gym": "Mobile app mockup showing class booking for '{business_name}'. "
                   "iPhone screen with calendar interface, available class times, "
                   "one-tap booking button. Modern fitness app UI.",

            "default": "Online booking system mockup for '{business_name}'. "
                      "Calendar interface with available times and booking CTA."
        }
    }

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Grok API key."""
        self.generator = GrokImageGenerator(api_key=api_key)
        self.images_created = []

    def generate_mockup(
        self,
        business_name: str,
        pain_point: str = "no_website",
        industry: str = "default",
        output_path: Optional[str] = None,
        custom_prompt: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate a personalized mockup image for a business.

        Args:
            business_name: Name of the business
            pain_point: Pain point to address (no_website, few_reviews, etc.)
            industry: Industry category (gym, hvac, shipping, default)
            output_path: Where to save the image
            custom_prompt: Override with custom Grok prompt

        Returns:
            Path to saved image or URL
        """
        print(f"\n{'='*70}")
        print(f"GENERATING OUTREACH IMAGE")
        print(f"{'='*70}")
        print(f"Business: {business_name}")
        print(f"Pain Point: {pain_point}")
        print(f"Industry: {industry}")

        # Get prompt template
        if custom_prompt:
            prompt = custom_prompt
        else:
            pain_templates = self.PROMPT_TEMPLATES.get(pain_point, {})
            template = pain_templates.get(industry, pain_templates.get("default", ""))

            if not template:
                logger.error(f"No template found for pain_point={pain_point}, industry={industry}")
                return None

            prompt = template.format(business_name=business_name)

        print(f"\nPrompt: {prompt[:100]}...")

        # Generate image
        results = self.generator.generate_image(
            prompt=prompt,
            count=1,
            output_path=output_path
        )

        if results:
            result = results[0]
            self.images_created.append({
                'business_name': business_name,
                'pain_point': pain_point,
                'industry': industry,
                'path': result
            })
            print(f"\n✅ Image created: {result}")
            return result
        else:
            print(f"\n❌ Image generation failed")
            return None

    def batch_generate(
        self,
        leads: List[Dict],
        output_dir: str = "mockups",
        pain_point_field: str = "pain_points",
        category_field: str = "category"
    ) -> List[Dict]:
        """
        Generate mockups for multiple leads.

        Args:
            leads: List of lead dictionaries
            output_dir: Directory to save images
            pain_point_field: Field name containing pain points
            category_field: Field name containing industry category

        Returns:
            List of results with image paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = []

        print(f"\n{'='*70}")
        print(f"BATCH IMAGE GENERATION")
        print(f"{'='*70}")
        print(f"Leads: {len(leads)}")
        print(f"Output: {output_dir}/")

        for i, lead in enumerate(leads, 1):
            business_name = lead.get('business_name', 'Business')
            pain_points = lead.get(pain_point_field, [])
            industry = lead.get(category_field, 'default')

            # Get primary pain point
            if isinstance(pain_points, list) and pain_points:
                pain_point = pain_points[0]
            elif isinstance(pain_points, str):
                pain_point = pain_points
            else:
                pain_point = "no_website"  # Default

            # Create safe filename
            safe_name = "".join(c if c.isalnum() else "_" for c in business_name.lower())
            output_file = output_path / f"{safe_name}_mockup.png"

            print(f"\n[{i}/{len(leads)}] Generating for: {business_name}")

            result_path = self.generate_mockup(
                business_name=business_name,
                pain_point=pain_point,
                industry=industry,
                output_path=str(output_file)
            )

            results.append({
                'business_name': business_name,
                'image_path': result_path,
                'pain_point': pain_point,
                'industry': industry
            })

        # Summary
        successful = sum(1 for r in results if r['image_path'])
        total_cost = successful * 0.07

        print(f"\n{'='*70}")
        print(f"BATCH COMPLETE")
        print(f"{'='*70}")
        print(f"✓ Generated: {successful}/{len(leads)}")
        print(f"💰 Total cost: ${total_cost:.2f}")
        print(f"{'='*70}\n")

        return results

    def save_results(self, output_file: str):
        """Save image generation results to JSON."""
        with open(output_file, 'w') as f:
            json.dump(self.images_created, f, indent=2)
        print(f"Results saved: {output_file}")


def main():
    """CLI for outreach image generation."""
    parser = argparse.ArgumentParser(
        description='Generate personalized images for cold outreach'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Single image generation
    gen_parser = subparsers.add_parser('generate', help='Generate single image')
    gen_parser.add_argument('--business-name', required=True, help='Business name')
    gen_parser.add_argument('--pain-point', default='no_website', help='Pain point to address')
    gen_parser.add_argument('--industry', default='default', help='Industry category')
    gen_parser.add_argument('--output', help='Output file path')
    gen_parser.add_argument('--prompt', help='Custom Grok prompt (overrides template)')

    # Batch generation
    batch_parser = subparsers.add_parser('batch', help='Generate images for multiple leads')
    batch_parser.add_argument('--leads', required=True, help='Path to leads JSON file')
    batch_parser.add_argument('--output-dir', default='mockups', help='Output directory')
    batch_parser.add_argument('--limit', type=int, help='Limit number of images to generate')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Create generator
    gen = OutreachImageGenerator()

    if args.command == 'generate':
        result = gen.generate_mockup(
            business_name=args.business_name,
            pain_point=args.pain_point,
            industry=args.industry,
            output_path=args.output,
            custom_prompt=args.prompt
        )

        return 0 if result else 1

    elif args.command == 'batch':
        # Load leads
        with open(args.leads) as f:
            leads = json.load(f)

        # Limit if specified
        if args.limit:
            leads = leads[:args.limit]

        results = gen.batch_generate(
            leads=leads,
            output_dir=args.output_dir
        )

        # Save results
        results_file = Path(args.output_dir) / "image_generation_results.json"
        gen.save_results(str(results_file))

        return 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
