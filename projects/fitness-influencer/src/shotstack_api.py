#!/usr/bin/env python3
"""
Shotstack Video Generation API Wrapper
Creates professional video ads from images, text, and audio.

Pricing: ~$0.04-0.10 per video (pay-per-use)
API Docs: https://shotstack.io/docs/api/

Usage:
    python shotstack_api.py create-video --images img1.jpg,img2.jpg --text "Your Ad Text"
    python shotstack_api.py check-status RENDER_ID
    python shotstack_api.py get-video RENDER_ID --output ad_video.mp4

Features:
- Combine AI-generated images into video
- Add text overlays with animations
- Include background music
- Apply transitions between clips
- Export in multiple formats (mp4, gif, etc.)
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# Shotstack API Configuration
SHOTSTACK_API_BASE = "https://api.shotstack.io/stage"  # Use "v1" for production
SHOTSTACK_API_KEY = os.getenv('SHOTSTACK_API_KEY')


class ShotstackAPI:
    """
    Shotstack Video Generation API wrapper.

    Creates professional videos from images, text overlays, and audio.
    Cost: ~$0.04-0.10 per video depending on resolution and length.
    """

    # Cost estimates (USD)
    COSTS = {
        "sd_per_second": 0.002,   # SD video
        "hd_per_second": 0.004,   # HD video
        "fhd_per_second": 0.006,  # Full HD video
        "base_render": 0.01,      # Base render cost
    }

    # Available transitions
    TRANSITIONS = [
        "fade", "reveal", "wipeLeft", "wipeRight", "wipeUp", "wipeDown",
        "slideLeft", "slideRight", "slideUp", "slideDown",
        "carouselLeft", "carouselRight", "zoom"
    ]

    # Stock audio tracks (free with Shotstack)
    STOCK_AUDIO = {
        "upbeat": "https://shotstack-assets.s3.ap-southeast-2.amazonaws.com/music/unminus/ambisax.mp3",
        "motivational": "https://shotstack-assets.s3.ap-southeast-2.amazonaws.com/music/unminus/lit.mp3",
        "energetic": "https://shotstack-assets.s3.ap-southeast-2.amazonaws.com/music/unminus/palmtrees.mp3",
        "calm": "https://shotstack-assets.s3.ap-southeast-2.amazonaws.com/music/unminus/ambisax.mp3",
    }

    def __init__(self, api_key: str = None, environment: str = "v1"):
        """
        Initialize Shotstack API wrapper.

        Args:
            api_key: Shotstack API key (or from SHOTSTACK_API_KEY env var)
            environment: "v1" for production, "stage" for testing
        """
        self.api_key = api_key or os.getenv('SHOTSTACK_API_KEY')
        self.environment = os.getenv('SHOTSTACK_ENV', environment)
        self.base_url = f"https://api.shotstack.io/{self.environment}"

        # Track usage
        self.videos_rendered = 0
        self.total_cost = 0.0

        if not self.api_key:
            print("WARNING: SHOTSTACK_API_KEY not found in environment")
            print("Video generation will fail until the key is configured")
            print("Get your API key at: https://dashboard.shotstack.io/")

    def get_headers(self) -> Dict[str, str]:
        """Get API headers with authentication."""
        if not self.api_key:
            raise ValueError(
                "SHOTSTACK_API_KEY not set.\n"
                "Get your API key from: https://dashboard.shotstack.io/"
            )
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def create_video_from_images(
        self,
        image_urls: List[str],
        text_overlays: List[str] = None,
        duration_per_image: float = 3.0,
        transition: str = "fade",
        music: str = "upbeat",
        resolution: str = "hd",
        output_format: str = "mp4"
    ) -> Dict[str, Any]:
        """
        Create a video from a list of images with optional text overlays.

        Args:
            image_urls: List of image URLs to include in video
            text_overlays: List of text to overlay on each image (optional)
            duration_per_image: Seconds to show each image
            transition: Transition effect between images
            music: Music track key or URL
            resolution: "sd", "hd", or "fhd"
            output_format: "mp4", "gif", or "webm"

        Returns:
            Dict with render_id and status
        """
        print(f"\n{'='*70}")
        print("SHOTSTACK VIDEO GENERATION")
        print(f"{'='*70}")
        print(f"Images: {len(image_urls)}")
        print(f"Duration per image: {duration_per_image}s")
        print(f"Total duration: {len(image_urls) * duration_per_image}s")
        print(f"Transition: {transition}")
        print(f"Resolution: {resolution}")

        if not self.api_key:
            return {"success": False, "error": "SHOTSTACK_API_KEY not configured"}

        # Build video timeline
        clips = []
        start_time = 0.0

        for i, image_url in enumerate(image_urls):
            # Image clip
            clip = {
                "asset": {
                    "type": "image",
                    "src": image_url
                },
                "start": start_time,
                "length": duration_per_image,
                "fit": "cover",
                "transition": {
                    "in": transition if i > 0 else None,
                    "out": transition if i < len(image_urls) - 1 else None
                }
            }
            clips.append(clip)

            # Text overlay if provided
            if text_overlays and i < len(text_overlays) and text_overlays[i]:
                text_clip = {
                    "asset": {
                        "type": "title",
                        "text": text_overlays[i],
                        "style": "blockbuster",
                        "size": "medium",
                        "position": "bottom"
                    },
                    "start": start_time,
                    "length": duration_per_image,
                    "transition": {
                        "in": "fade",
                        "out": "fade"
                    }
                }
                clips.append(text_clip)

            start_time += duration_per_image

        # Build soundtrack
        soundtrack = None
        if music:
            music_url = self.STOCK_AUDIO.get(music, music)
            soundtrack = {
                "src": music_url,
                "effect": "fadeOut"
            }

        # Build timeline
        timeline = {
            "soundtrack": soundtrack,
            "tracks": [
                {"clips": clips}
            ]
        }

        # Build output settings
        output = {
            "format": output_format,
            "resolution": resolution,
            "aspectRatio": "16:9"
        }

        # Full render request
        render_request = {
            "timeline": timeline,
            "output": output
        }

        print(f"\n-> Submitting render job...")

        try:
            response = requests.post(
                f"{self.base_url}/render",
                headers=self.get_headers(),
                json=render_request,
                timeout=30
            )

            if response.status_code not in [200, 201]:
                print(f"  X API Error: {response.status_code}")
                print(f"  {response.text}")
                return {"success": False, "error": response.text}

            data = response.json()
            render_id = data.get("response", {}).get("id")

            # Estimate cost
            total_duration = len(image_urls) * duration_per_image
            cost_key = f"{resolution}_per_second"
            estimated_cost = self.COSTS.get(cost_key, 0.004) * total_duration + self.COSTS["base_render"]

            print(f"  OK Render job submitted!")
            print(f"  Render ID: {render_id}")
            print(f"  Estimated cost: ${estimated_cost:.3f}")

            self.videos_rendered += 1
            self.total_cost += estimated_cost

            return {
                "success": True,
                "render_id": render_id,
                "status": "queued",
                "estimated_cost": estimated_cost,
                "duration": total_duration
            }

        except requests.RequestException as e:
            print(f"  X Request failed: {e}")
            return {"success": False, "error": str(e)}

    def check_render_status(self, render_id: str) -> Dict[str, Any]:
        """
        Check the status of a render job.

        Args:
            render_id: The render ID from create_video

        Returns:
            Dict with status and video URL if complete
        """
        if not self.api_key:
            return {"success": False, "error": "SHOTSTACK_API_KEY not configured"}

        try:
            response = requests.get(
                f"{self.base_url}/render/{render_id}",
                headers=self.get_headers(),
                timeout=30
            )

            if response.status_code != 200:
                return {"success": False, "error": response.text}

            data = response.json()
            render_response = data.get("response", {})

            status = render_response.get("status")
            result = {
                "success": True,
                "render_id": render_id,
                "status": status
            }

            if status == "done":
                result["video_url"] = render_response.get("url")
                print(f"  OK Video ready: {result['video_url']}")
            elif status == "failed":
                result["error"] = render_response.get("error", "Unknown error")
                print(f"  X Render failed: {result['error']}")
            else:
                print(f"  ... Status: {status}")

            return result

        except requests.RequestException as e:
            return {"success": False, "error": str(e)}

    def wait_for_render(self, render_id: str, max_wait: int = 120, poll_interval: int = 5) -> Dict[str, Any]:
        """
        Wait for a render to complete.

        Args:
            render_id: The render ID to wait for
            max_wait: Maximum seconds to wait
            poll_interval: Seconds between status checks

        Returns:
            Final render status with video URL if successful
        """
        print(f"\n-> Waiting for render to complete (max {max_wait}s)...")

        start_time = time.time()
        while time.time() - start_time < max_wait:
            result = self.check_render_status(render_id)

            if not result.get("success"):
                return result

            status = result.get("status")

            if status == "done":
                return result
            elif status == "failed":
                return result

            time.sleep(poll_interval)

        return {
            "success": False,
            "render_id": render_id,
            "status": "timeout",
            "error": f"Render did not complete within {max_wait} seconds"
        }

    def download_video(self, video_url: str, output_path: str) -> bool:
        """
        Download a rendered video to local file.

        Args:
            video_url: URL of the rendered video
            output_path: Local path to save video

        Returns:
            True if download successful
        """
        print(f"\n-> Downloading video to {output_path}...")

        try:
            response = requests.get(video_url, stream=True, timeout=120)

            if response.status_code != 200:
                print(f"  X Download failed: {response.status_code}")
                return False

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size = Path(output_path).stat().st_size / (1024 * 1024)
            print(f"  OK Downloaded: {output_path} ({file_size:.1f} MB)")
            return True

        except Exception as e:
            print(f"  X Download error: {e}")
            return False

    def create_fitness_ad(
        self,
        image_urls: List[str],
        headline: str,
        cta_text: str = "Start Your Journey",
        duration: float = 15.0,
        music: str = "energetic"
    ) -> Dict[str, Any]:
        """
        Create a fitness-focused advertisement video.

        Args:
            image_urls: List of fitness-related image URLs
            headline: Main ad headline
            cta_text: Call-to-action text
            duration: Total video duration in seconds
            music: Music style ("energetic", "motivational", "upbeat")

        Returns:
            Dict with render status and video URL
        """
        print(f"\n{'='*70}")
        print("CREATING FITNESS AD VIDEO")
        print(f"{'='*70}")
        print(f"Headline: {headline}")
        print(f"CTA: {cta_text}")
        print(f"Duration: {duration}s")
        print(f"Images: {len(image_urls)}")

        if not image_urls:
            return {"success": False, "error": "No images provided"}

        # Calculate timing
        num_images = len(image_urls)
        duration_per_image = duration / num_images

        # Build text overlays - headline on first, CTA on last
        text_overlays = [""] * num_images
        text_overlays[0] = headline
        text_overlays[-1] = cta_text

        # Create the video
        result = self.create_video_from_images(
            image_urls=image_urls,
            text_overlays=text_overlays,
            duration_per_image=duration_per_image,
            transition="slideLeft",
            music=music,
            resolution="hd",
            output_format="mp4"
        )

        if not result.get("success"):
            return result

        # Wait for render
        final_result = self.wait_for_render(result["render_id"])

        return final_result

    def get_usage_summary(self) -> Dict[str, Any]:
        """
        Get summary of videos rendered and costs.

        Returns:
            Dict with usage stats
        """
        return {
            "videos_rendered": self.videos_rendered,
            "total_cost": self.total_cost,
            "average_cost_per_video": self.total_cost / max(self.videos_rendered, 1)
        }


# Convenience function for simple video creation
async def create_ad_video(
    image_urls: List[str],
    headline: str,
    cta_text: str = "Start Your Journey",
    duration: float = 15.0
) -> Dict[str, Any]:
    """
    Create a fitness ad video from images.

    Args:
        image_urls: List of image URLs (from Grok image generation)
        headline: Ad headline text
        cta_text: Call-to-action text
        duration: Video duration in seconds

    Returns:
        Dict with video_url if successful
    """
    api = ShotstackAPI()
    result = api.create_fitness_ad(
        image_urls=image_urls,
        headline=headline,
        cta_text=cta_text,
        duration=duration
    )

    return {
        "success": result.get("success", False),
        "video_url": result.get("video_url"),
        "render_id": result.get("render_id"),
        "status": result.get("status"),
        "cost": result.get("estimated_cost", 0),
        "error": result.get("error")
    }


def main():
    """CLI for Shotstack video generation."""
    if len(sys.argv) < 2:
        print("Usage: python shotstack_api.py <command> [options]")
        print("\nCommands:")
        print("  create-video --images URL1,URL2 [--text 'Text1,Text2'] [--duration 3] [--music upbeat]")
        print("  create-fitness-ad --images URL1,URL2 --headline 'Your Text' [--cta 'Start Now']")
        print("  check-status RENDER_ID")
        print("  download RENDER_ID --output video.mp4")
        print("\nMusic options: upbeat, motivational, energetic, calm")
        print("\nEnvironment: Set SHOTSTACK_API_KEY in .env file")
        sys.exit(1)

    command = sys.argv[1]
    api = ShotstackAPI()

    try:
        if command == "create-video":
            # Parse arguments
            images = []
            texts = []
            duration = 3.0
            music = "upbeat"

            if "--images" in sys.argv:
                idx = sys.argv.index("--images")
                images = sys.argv[idx + 1].split(",")

            if "--text" in sys.argv:
                idx = sys.argv.index("--text")
                texts = sys.argv[idx + 1].split(",")

            if "--duration" in sys.argv:
                idx = sys.argv.index("--duration")
                duration = float(sys.argv[idx + 1])

            if "--music" in sys.argv:
                idx = sys.argv.index("--music")
                music = sys.argv[idx + 1]

            result = api.create_video_from_images(
                image_urls=images,
                text_overlays=texts if texts else None,
                duration_per_image=duration,
                music=music
            )

            if result.get("success"):
                print(f"\nRender ID: {result['render_id']}")
                print("Use 'check-status' command to monitor progress")

        elif command == "create-fitness-ad":
            images = []
            headline = "Transform Your Body"
            cta = "Start Your Journey"

            if "--images" in sys.argv:
                idx = sys.argv.index("--images")
                images = sys.argv[idx + 1].split(",")

            if "--headline" in sys.argv:
                idx = sys.argv.index("--headline")
                headline = sys.argv[idx + 1]

            if "--cta" in sys.argv:
                idx = sys.argv.index("--cta")
                cta = sys.argv[idx + 1]

            result = api.create_fitness_ad(
                image_urls=images,
                headline=headline,
                cta_text=cta
            )

            if result.get("video_url"):
                print(f"\nVideo URL: {result['video_url']}")

        elif command == "check-status":
            render_id = sys.argv[2]
            result = api.check_render_status(render_id)
            print(f"\nStatus: {result.get('status')}")
            if result.get("video_url"):
                print(f"Video URL: {result['video_url']}")

        elif command == "download":
            render_id = sys.argv[2]
            output_path = "video.mp4"

            if "--output" in sys.argv:
                idx = sys.argv.index("--output")
                output_path = sys.argv[idx + 1]

            # First check status to get URL
            result = api.check_render_status(render_id)
            if result.get("video_url"):
                api.download_video(result["video_url"], output_path)
            else:
                print(f"Video not ready. Status: {result.get('status')}")

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
