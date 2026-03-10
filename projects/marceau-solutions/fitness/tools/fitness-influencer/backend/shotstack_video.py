#!/usr/bin/env python3
"""
Shotstack Video Generation for Fitness Influencer Backend
Creates downloadable video ads from AI-generated images.

Pricing: ~$0.04-0.10 per video
"""

import os
import time
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class ShotstackVideo:
    """
    Create professional video ads using Shotstack API.
    Integrates with Grok-generated images from the AI arbitrator.
    """

    # Stock audio for fitness videos
    MUSIC_TRACKS = {
        "energetic": "https://shotstack-assets.s3.ap-southeast-2.amazonaws.com/music/unminus/palmtrees.mp3",
        "motivational": "https://shotstack-assets.s3.ap-southeast-2.amazonaws.com/music/unminus/lit.mp3",
        "upbeat": "https://shotstack-assets.s3.ap-southeast-2.amazonaws.com/music/unminus/ambisax.mp3",
    }

    def __init__(self, api_key: str = None):
        """Initialize with Shotstack API key."""
        self.api_key = api_key or os.getenv('SHOTSTACK_API_KEY')
        self.environment = os.getenv('SHOTSTACK_ENV', 'stage')  # 'stage' for sandbox, 'v1' for production
        self.base_url = f"https://api.shotstack.io/{self.environment}"

        if not self.api_key:
            print("WARNING: SHOTSTACK_API_KEY not configured")

    def _get_headers(self) -> Dict[str, str]:
        """Get API headers."""
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    async def create_fitness_video(
        self,
        image_urls: List[str],
        headline: str = "",
        cta_text: str = "Start Your Journey",
        duration: float = 15.0,
        music_style: str = "energetic"
    ) -> Dict[str, Any]:
        """
        Create a fitness ad video from images.

        Args:
            image_urls: List of image URLs (from Grok)
            headline: Main headline text
            cta_text: Call-to-action text
            duration: Total video duration
            music_style: "energetic", "motivational", or "upbeat"

        Returns:
            Dict with video_url if successful
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "SHOTSTACK_API_KEY not configured. Get one at https://dashboard.shotstack.io/"
            }

        if not image_urls:
            return {"success": False, "error": "No images provided"}

        # Calculate timing
        num_images = len(image_urls)
        duration_per_clip = duration / num_images

        # Build clips
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
                "length": duration_per_clip,
                "fit": "cover",
                "effect": "zoomIn" if i % 2 == 0 else "zoomOut"
            }

            # Add transitions (only include valid ones, not None)
            transition = {}
            if i > 0:
                transition["in"] = "fade"
            if i < num_images - 1:
                transition["out"] = "fade"
            if transition:
                clip["transition"] = transition

            clips.append(clip)
            start_time += duration_per_clip

        # Text overlays track
        text_clips = []

        # Headline on first clip
        if headline:
            text_clips.append({
                "asset": {
                    "type": "title",
                    "text": headline,
                    "style": "minimal",
                    "size": "medium"
                },
                "start": 0,
                "length": duration_per_clip * min(2, num_images),
                "position": "center",
                "transition": {"in": "fade", "out": "fade"}
            })

        # CTA on last clip
        if cta_text:
            text_clips.append({
                "asset": {
                    "type": "title",
                    "text": cta_text,
                    "style": "minimal",
                    "size": "small"
                },
                "start": duration - duration_per_clip,
                "length": duration_per_clip,
                "position": "bottom",
                "transition": {"in": "slideUp"}
            })

        # Build timeline
        tracks = [{"clips": clips}]
        if text_clips:
            tracks.append({"clips": text_clips})

        # Soundtrack
        music_url = self.MUSIC_TRACKS.get(music_style, self.MUSIC_TRACKS["energetic"])

        timeline = {
            "soundtrack": {
                "src": music_url,
                "effect": "fadeOut",
                "volume": 0.7
            },
            "tracks": tracks
        }

        # Render request
        render_request = {
            "timeline": timeline,
            "output": {
                "format": "mp4",
                "resolution": "hd",
                "aspectRatio": "9:16"  # Vertical for social media
            }
        }

        try:
            # Submit render
            print(f"[Shotstack] Submitting render to {self.base_url}/render")
            print(f"[Shotstack] Images: {len(image_urls)}, Duration: {duration}s")

            response = requests.post(
                f"{self.base_url}/render",
                headers=self._get_headers(),
                json=render_request,
                timeout=30
            )

            print(f"[Shotstack] Response status: {response.status_code}")

            if response.status_code not in [200, 201]:
                error_msg = f"API error {response.status_code}: {response.text}"
                print(f"[Shotstack] Error: {error_msg}")
                return {"success": False, "error": error_msg}

            data = response.json()
            render_id = data.get("response", {}).get("id")

            if not render_id:
                print(f"[Shotstack] No render ID in response: {data}")
                return {"success": False, "error": "No render ID returned"}

            print(f"[Shotstack] Render submitted: {render_id}")

            # Wait for completion
            result = await self._wait_for_render(render_id)
            return result

        except Exception as e:
            print(f"[Shotstack] Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    async def _wait_for_render(
        self,
        render_id: str,
        max_wait: int = 120,
        poll_interval: int = 5
    ) -> Dict[str, Any]:
        """Wait for render to complete."""
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                response = requests.get(
                    f"{self.base_url}/render/{render_id}",
                    headers=self._get_headers(),
                    timeout=30
                )

                if response.status_code != 200:
                    return {"success": False, "error": response.text}

                data = response.json()
                render_data = data.get("response", {})
                status = render_data.get("status")

                if status == "done":
                    return {
                        "success": True,
                        "video_url": render_data.get("url"),
                        "render_id": render_id,
                        "status": "done",
                        "cost": 0.05  # Approximate cost
                    }
                elif status == "failed":
                    return {
                        "success": False,
                        "error": render_data.get("error", "Render failed"),
                        "render_id": render_id,
                        "status": "failed"
                    }

                time.sleep(poll_interval)

            except Exception as e:
                return {"success": False, "error": str(e)}

        return {
            "success": False,
            "error": "Render timeout",
            "render_id": render_id,
            "status": "timeout"
        }

    def check_status(self, render_id: str) -> Dict[str, Any]:
        """Check render status (non-blocking)."""
        if not self.api_key:
            return {"success": False, "error": "SHOTSTACK_API_KEY not configured"}

        try:
            response = requests.get(
                f"{self.base_url}/render/{render_id}",
                headers=self._get_headers(),
                timeout=30
            )

            if response.status_code != 200:
                return {"success": False, "error": response.text}

            data = response.json()
            render_data = data.get("response", {})

            return {
                "success": True,
                "status": render_data.get("status"),
                "video_url": render_data.get("url"),
                "render_id": render_id
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton instance
_video_api = None


def get_video_api() -> ShotstackVideo:
    """Get or create Shotstack API instance."""
    global _video_api
    if _video_api is None:
        _video_api = ShotstackVideo()
    return _video_api


async def create_video_ad(
    image_urls: List[str],
    headline: str = "",
    cta_text: str = "Start Your Journey",
    duration: float = 15.0
) -> Dict[str, Any]:
    """
    Convenience function to create a fitness video ad.

    Args:
        image_urls: List of image URLs from Grok
        headline: Main headline
        cta_text: Call-to-action text
        duration: Video duration in seconds

    Returns:
        Dict with video_url if successful
    """
    api = get_video_api()
    return await api.create_fitness_video(
        image_urls=image_urls,
        headline=headline,
        cta_text=cta_text,
        duration=duration
    )
