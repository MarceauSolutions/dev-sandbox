#!/usr/bin/env python3
"""
grok_video_gen.py - AI Video Generation via Grok Imagine / xAI

WHAT: Generate AI videos from text prompts or images using Grok Imagine
WHY: Create B-roll footage, product videos, and visual content on-demand
INPUT: Text prompt (and optional image URL), duration, aspect ratio
OUTPUT: Video file (MP4) or URL

QUICK USAGE:
  # Text to video
  python grok_video_gen.py --prompt "Athletic person doing deadlift in modern gym"

  # Image to video (animate a still image)
  python grok_video_gen.py --prompt "Camera slowly orbits around subject" --image frame.png

  # Specify duration and aspect ratio
  python grok_video_gen.py --prompt "..." --duration 12 --aspect-ratio 16:9 --output broll.mp4

CAPABILITIES:
  - Text-to-video generation (6-15 seconds)
  - Image-to-video (animate starting frames)
  - 720p resolution, 24 FPS
  - Synchronized audio generation
  - Aspect ratio control (16:9, 9:16, 4:3, 1:1)

API DOCS: https://docs.x.ai/docs/guides/video-generations
DEPENDENCIES: requests, python-dotenv
API_KEYS: XAI_API_KEY (from x.ai console)
"""

import argparse
import sys
import os
import time
import base64
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()


class GrokVideoGenerator:
    """
    Generate videos using Grok Imagine / xAI API.
    """

    API_BASE = "https://api.x.ai/v1"
    MODEL = "grok-imagine-video"

    # Pricing estimate (may vary)
    COST_PER_SECOND = 0.02  # USD estimate

    def __init__(self, api_key=None):
        """
        Initialize Grok video generator.

        Args:
            api_key: xAI API key (or from XAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('XAI_API_KEY')

        if not self.api_key:
            print("ERROR: XAI_API_KEY not found in environment")
            print("Set it with: export XAI_API_KEY=your_api_key")
            sys.exit(1)

        self.videos_generated = 0
        self.total_duration = 0

    def _get_headers(self):
        """Get API request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _encode_image(self, image_path):
        """Encode local image to base64 data URL."""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Determine MIME type
        suffix = path.suffix.lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp'
        }
        mime_type = mime_types.get(suffix, 'image/png')

        with open(path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')

        return f"data:{mime_type};base64,{encoded}"

    def generate_video(
        self,
        prompt,
        duration=8,
        aspect_ratio="16:9",
        resolution="720p",
        image_path=None,
        image_url=None,
        output_path=None
    ):
        """
        Generate video from text prompt (and optional image).

        Args:
            prompt: Text description of desired video
            duration: Video length in seconds (1-15)
            aspect_ratio: "16:9", "9:16", "4:3", or "1:1"
            resolution: "480p" or "720p"
            image_path: Local path to starting frame image
            image_url: URL of starting frame image
            output_path: Where to save video file

        Returns:
            Video URL or local path if output_path specified
        """
        print(f"\n{'='*70}")
        print(f"GROK IMAGINE VIDEO GENERATION")
        print(f"{'='*70}")
        print(f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        print(f"Duration: {duration}s | Aspect: {aspect_ratio} | Resolution: {resolution}")

        if image_path:
            print(f"Starting frame: {image_path}")
        elif image_url:
            print(f"Starting frame URL: {image_url[:50]}...")

        # Validate duration
        if duration < 1 or duration > 15:
            print("ERROR: Duration must be between 1 and 15 seconds")
            return None

        # Build payload
        payload = {
            "model": self.MODEL,
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution
        }

        # Add image if provided
        if image_path:
            payload["image_url"] = self._encode_image(image_path)
        elif image_url:
            payload["image_url"] = image_url

        print(f"\n→ Starting video generation...")

        try:
            # Start async generation
            response = requests.post(
                f"{self.API_BASE}/videos/generations",
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )

            if response.status_code not in [200, 201, 202]:
                print(f"  ✗ API Error: {response.status_code}")
                print(f"  {response.text}")
                return None

            data = response.json()

            # Check if we got a direct result or need to poll
            if 'url' in data:
                video_url = data['url']
            elif 'request_id' in data:
                # Poll for completion
                request_id = data['request_id']
                print(f"  Request ID: {request_id}")
                video_url = self._poll_for_result(request_id)
                if not video_url:
                    return None
            elif 'data' in data and len(data['data']) > 0:
                video_url = data['data'][0].get('url')
            else:
                print(f"  ✗ Unexpected response format: {data}")
                return None

            self.videos_generated += 1
            self.total_duration += duration

            estimated_cost = duration * self.COST_PER_SECOND
            print(f"  ✓ Video generated!")
            print(f"  💰 Estimated cost: ${estimated_cost:.2f}")

            # Download if output path specified
            if output_path and video_url:
                return self._download_video(video_url, output_path)

            print(f"\n✅ SUCCESS!")
            print(f"   Video URL: {video_url}")
            print(f"{'='*70}\n")

            return video_url

        except requests.RequestException as e:
            print(f"  ✗ Request failed: {e}")
            return None
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _poll_for_result(self, request_id, max_wait=300, poll_interval=5):
        """
        Poll for async video generation result.

        Args:
            request_id: The generation request ID
            max_wait: Maximum seconds to wait
            poll_interval: Seconds between polls

        Returns:
            Video URL or None if failed/timeout
        """
        print(f"  → Waiting for generation to complete...")

        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                response = requests.get(
                    f"{self.API_BASE}/videos/{request_id}",
                    headers=self._get_headers(),
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', '').lower()

                    if status == 'completed' or status == 'succeeded':
                        return data.get('url') or data.get('video_url')
                    elif status == 'failed':
                        print(f"  ✗ Generation failed: {data.get('error', 'Unknown error')}")
                        return None
                    else:
                        elapsed = int(time.time() - start_time)
                        print(f"    Status: {status} ({elapsed}s elapsed)")

                time.sleep(poll_interval)

            except Exception as e:
                print(f"  ⚠ Poll error: {e}")
                time.sleep(poll_interval)

        print(f"  ✗ Timeout waiting for video generation")
        return None

    def _download_video(self, url, output_path):
        """Download video from URL to local file."""
        print(f"\n→ Downloading video...")

        try:
            response = requests.get(url, timeout=120, stream=True)

            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                file_size = os.path.getsize(output_path)
                print(f"  ✓ Saved: {output_path} ({file_size / 1024 / 1024:.1f} MB)")
                print(f"\n✅ SUCCESS!")
                print(f"{'='*70}\n")
                return output_path
            else:
                print(f"  ✗ Download failed: {response.status_code}")
                return url  # Return URL as fallback

        except Exception as e:
            print(f"  ✗ Download error: {e}")
            return url

    def get_usage_summary(self):
        """Get summary of videos generated."""
        estimated_cost = self.total_duration * self.COST_PER_SECOND

        return {
            'videos_generated': self.videos_generated,
            'total_duration': self.total_duration,
            'estimated_cost': estimated_cost
        }


def main():
    """CLI for Grok video generation."""
    parser = argparse.ArgumentParser(
        description='Grok Imagine Video Generation - Generate AI videos from text/images',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple text-to-video
  python grok_video_gen.py --prompt "Person lifting weights in gym"

  # With duration and output file
  python grok_video_gen.py --prompt "..." --duration 12 --output broll.mp4

  # Animate a starting frame
  python grok_video_gen.py --prompt "Camera orbits subject" --image frame.png

  # Vertical video for shorts/reels
  python grok_video_gen.py --prompt "..." --aspect-ratio 9:16
        """
    )

    parser.add_argument('--prompt', required=True, help='Text description of desired video')
    parser.add_argument('--duration', type=int, default=12, help='Video length in seconds (1-15)')
    parser.add_argument('--aspect-ratio', default='16:9', choices=['16:9', '9:16', '4:3', '1:1'],
                        help='Video aspect ratio')
    parser.add_argument('--resolution', default='720p', choices=['480p', '720p'],
                        help='Video resolution')
    parser.add_argument('--image', help='Local path to starting frame image')
    parser.add_argument('--image-url', help='URL of starting frame image')
    parser.add_argument('--output', help='Output file path (e.g., video.mp4)')
    parser.add_argument('--api-key', help='xAI API key (or use XAI_API_KEY env var)')

    args = parser.parse_args()

    # Create generator
    generator = GrokVideoGenerator(api_key=args.api_key)

    # Generate video
    try:
        result = generator.generate_video(
            prompt=args.prompt,
            duration=args.duration,
            aspect_ratio=args.aspect_ratio,
            resolution=args.resolution,
            image_path=args.image,
            image_url=args.image_url,
            output_path=args.output
        )

        if not result:
            print("\n✗ Video generation failed")
            return 1

        # Print usage summary
        usage = generator.get_usage_summary()
        print(f"\n📊 SESSION USAGE:")
        print(f"   Videos generated: {usage['videos_generated']}")
        print(f"   Total duration: {usage['total_duration']}s")
        print(f"   Estimated cost: ${usage['estimated_cost']:.2f}\n")

        return 0

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
