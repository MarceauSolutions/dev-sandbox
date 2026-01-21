#!/usr/bin/env python3
"""
grok_image_gen.py - AI Image Generation via Grok/xAI

WHAT: Generate AI images from text prompts using Grok's Aurora model
WHY: Create custom fitness images, backgrounds, and visual content on-demand
INPUT: Text prompt describing desired image, count (1-10 images)
OUTPUT: Image URLs or downloaded files (1024x768 default)
COST: $0.07 per image
TIME: ~10-15 seconds per image

QUICK USAGE:
  python grok_image_gen.py --prompt "Fitness influencer doing workout"

CAPABILITIES:
  - Text-to-image generation with photorealistic quality
  - Batch generation (up to 10 images per request)
  - Automatic cost tracking and reporting
  - Optional local file download
  - Precise text instruction following

DEPENDENCIES: requests, python-dotenv
API_KEYS: XAI_API_KEY (from x.ai console)

---
Original Features:
- Text-to-image generation
- Batch generation (up to 10 images)
- Cost tracking ($0.07 per image)

Usage:
    python grok_image_gen.py --prompt "Fitness influencer doing workout"
    python grok_image_gen.py --prompt "Gym background" --count 3 --output gym_bg.png
"""

import argparse
import sys
import os
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()


class GrokImageGenerator:
    """
    Generate images using Grok/xAI API.
    """

    API_URL = "https://api.x.ai/v1/images/generations"
    MODEL = "grok-2-image-1212"
    COST_PER_IMAGE = 0.07  # USD

    def __init__(self, api_key=None):
        """
        Initialize Grok image generator.

        Args:
            api_key: xAI API key (or from XAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('XAI_API_KEY')

        if not self.api_key:
            print("ERROR: XAI_API_KEY not found in environment")
            print("Set it with: export XAI_API_KEY=your_api_key")
            sys.exit(1)

        self.images_generated = 0

    def generate_image(self, prompt, count=1, output_path=None):
        """
        Generate image(s) from text prompt.

        Args:
            prompt: Text description of image
            count: Number of images to generate (1-10)
            output_path: Where to save image(s)

        Returns:
            List of image URLs or paths
        """
        print(f"\\n{'='*70}")
        print(f"GROK IMAGE GENERATION")
        print(f"{'='*70}")
        print(f"Prompt: {prompt}")
        print(f"Count: {count}")

        if count < 1 or count > 10:
            print("ERROR: Count must be between 1 and 10")
            return []

        # API request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "prompt": prompt,
            "n": count,
            "model": self.MODEL
        }

        print(f"\\n→ Generating {count} image(s)...")

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
                return []

            data = response.json()

            # Extract image URLs
            images = data.get('data', [])
            image_urls = [img.get('url') for img in images if img.get('url')]

            self.images_generated += len(image_urls)

            print(f"  ✓ Generated {len(image_urls)} image(s)")
            print(f"  💰 Cost: ${len(image_urls) * self.COST_PER_IMAGE:.2f}")

            # Download images if output path specified
            if output_path:
                saved_paths = []

                for i, url in enumerate(image_urls):
                    if count == 1:
                        save_path = output_path
                    else:
                        # Multiple images: add number to filename
                        path = Path(output_path)
                        save_path = str(path.parent / f"{path.stem}_{i+1}{path.suffix}")

                    print(f"\\n→ Downloading image {i+1}/{len(image_urls)}...")

                    img_response = requests.get(url, timeout=30)
                    if img_response.status_code == 200:
                        with open(save_path, 'wb') as f:
                            f.write(img_response.content)

                        print(f"  ✓ Saved: {save_path}")
                        saved_paths.append(save_path)
                    else:
                        print(f"  ✗ Failed to download image")

                print(f"\\n✅ SUCCESS!")
                print(f"   Generated {len(saved_paths)} image(s)")
                print(f"   Total cost: ${len(image_urls) * self.COST_PER_IMAGE:.2f}")
                print(f"{'='*70}\\n")

                return saved_paths

            else:
                # Return URLs
                print(f"\\n✅ SUCCESS!")
                print(f"   Image URLs:")
                for i, url in enumerate(image_urls):
                    print(f"   {i+1}. {url}")

                print(f"\\n   Total cost: ${len(image_urls) * self.COST_PER_IMAGE:.2f}")
                print(f"{'='*70}\\n")

                return image_urls

        except requests.RequestException as e:
            print(f"  ✗ Request failed: {e}")
            return []
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_usage_summary(self):
        """
        Get summary of images generated and costs.

        Returns:
            Dict with usage stats
        """
        total_cost = self.images_generated * self.COST_PER_IMAGE

        return {
            'images_generated': self.images_generated,
            'total_cost': total_cost,
            'cost_per_image': self.COST_PER_IMAGE
        }


def main():
    """CLI for Grok image generation."""
    parser = argparse.ArgumentParser(
        description='Grok/xAI Image Generation - Generate AI images from text'
    )
    parser.add_argument('--prompt', required=True, help='Text description of image')
    parser.add_argument('--count', type=int, default=1, help='Number of images to generate (1-10)')
    parser.add_argument('--output', help='Output file path (if saving locally)')
    parser.add_argument('--api-key', help='xAI API key (or use XAI_API_KEY env var)')

    args = parser.parse_args()

    # Create generator
    generator = GrokImageGenerator(api_key=args.api_key)

    # Generate images
    try:
        results = generator.generate_image(
            prompt=args.prompt,
            count=args.count,
            output_path=args.output
        )

        if not results:
            print("\\n✗ Image generation failed")
            return 1

        # Print usage summary
        usage = generator.get_usage_summary()
        print(f"\\n📊 SESSION USAGE:")
        print(f"   Images generated: {usage['images_generated']}")
        print(f"   Total cost: ${usage['total_cost']:.2f}\\n")

        return 0

    except Exception as e:
        print(f"\\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())