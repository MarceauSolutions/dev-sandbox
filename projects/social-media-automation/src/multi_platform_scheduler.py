"""
Multi-Platform Social Media Scheduler
Posts content to X, Facebook, LinkedIn, and TikTok from unified interface
"""

import os
import json
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Import platform APIs
from .facebook_api import FacebookAPI
from .linkedin_api import LinkedInAPI
from .tiktok_api import TikTokAPI
# X API assumed to exist from existing automation

load_dotenv()

class MultiPlatformScheduler:
    """Unified scheduler for posting to multiple social platforms."""

    def __init__(self):
        """Initialize all platform APIs."""
        self.platforms = {}

        # Initialize Facebook
        try:
            self.platforms['facebook'] = FacebookAPI()
            print("✅ Facebook API initialized")
        except Exception as e:
            print(f"⚠️  Facebook API not available: {e}")

        # Initialize LinkedIn
        try:
            self.platforms['linkedin'] = LinkedInAPI()
            print("✅ LinkedIn API initialized")
        except Exception as e:
            print(f"⚠️  LinkedIn API not available: {e}")

        # Initialize TikTok
        try:
            self.platforms['tiktok'] = TikTokAPI()
            print("✅ TikTok API initialized")
        except Exception as e:
            print(f"⚠️  TikTok API not available: {e}")

        # X API integration would go here
        # self.platforms['x'] = XAPI()

    def post_text(
        self,
        text: str,
        platforms: List[str],
        link: str = None
    ) -> Dict[str, any]:
        """
        Post text content to multiple platforms.

        Args:
            text: Post content
            platforms: List of platform names ['facebook', 'linkedin', 'x']
            link: Optional URL to include

        Returns:
            dict: Results per platform
        """
        results = {}

        for platform in platforms:
            try:
                if platform == 'facebook' and 'facebook' in self.platforms:
                    result = self.platforms['facebook'].create_text_post(text, link)
                    results['facebook'] = {'success': True, 'post_id': result.get('id')}

                elif platform == 'linkedin' and 'linkedin' in self.platforms:
                    result = self.platforms['linkedin'].create_text_post(text)
                    results['linkedin'] = {'success': True, 'post_id': result.get('id')}

                elif platform == 'x':
                    # X API integration
                    results['x'] = {'success': False, 'error': 'X API not yet integrated'}

                else:
                    results[platform] = {'success': False, 'error': 'Platform not available'}

            except Exception as e:
                results[platform] = {'success': False, 'error': str(e)}

        return results

    def post_video(
        self,
        video_path: str,
        caption: str,
        platforms: List[str]
    ) -> Dict[str, any]:
        """
        Post video content to multiple platforms.

        Args:
            video_path: Path to video file
            caption: Video description
            platforms: List of platform names ['facebook', 'tiktok']

        Returns:
            dict: Results per platform
        """
        results = {}

        for platform in platforms:
            try:
                if platform == 'facebook' and 'facebook' in self.platforms:
                    result = self.platforms['facebook'].create_video_post(video_path, caption)
                    results['facebook'] = {'success': True, 'post_id': result.get('id')}

                elif platform == 'tiktok' and 'tiktok' in self.platforms:
                    result = self.platforms['tiktok'].post_video(video_path, caption)
                    results['tiktok'] = {'success': True, 'publish_id': result.get('publish_id')}

                else:
                    results[platform] = {'success': False, 'error': 'Platform not available'}

            except Exception as e:
                results[platform] = {'success': False, 'error': str(e)}

        return results

    def post_image(
        self,
        image_path: str,
        caption: str,
        platforms: List[str]
    ) -> Dict[str, any]:
        """
        Post image content to multiple platforms.

        Args:
            image_path: Path to image file
            caption: Image caption
            platforms: List of platform names ['facebook', 'linkedin']

        Returns:
            dict: Results per platform
        """
        results = {}

        for platform in platforms:
            try:
                if platform == 'facebook' and 'facebook' in self.platforms:
                    result = self.platforms['facebook'].create_photo_post(image_path, caption)
                    results['facebook'] = {'success': True, 'post_id': result.get('id')}

                elif platform == 'linkedin' and 'linkedin' in self.platforms:
                    # LinkedIn requires public URL, not file path
                    results['linkedin'] = {'success': False, 'error': 'Need public image URL for LinkedIn'}

                else:
                    results[platform] = {'success': False, 'error': 'Platform not available'}

            except Exception as e:
                results[platform] = {'success': False, 'error': str(e)}

        return results


def format_content_for_platform(base_text: str, platform: str) -> str:
    """
    Adapt content length/style for each platform.

    Args:
        base_text: Original content
        platform: Target platform name

    Returns:
        str: Formatted content
    """
    if platform == 'x':
        # X: 280 character limit
        if len(base_text) > 280:
            return base_text[:277] + "..."
        return base_text

    elif platform == 'linkedin':
        # LinkedIn: Longer form (500-3,000 chars recommended)
        # Can add more context, professional tone
        return base_text

    elif platform == 'facebook':
        # Facebook: Medium length (40-80 chars optimal)
        return base_text

    elif platform == 'tiktok':
        # TikTok: Short captions with hashtags
        # Max 150 characters recommended
        if len(base_text) > 150:
            return base_text[:147] + "..."
        return base_text

    return base_text


def test_multi_platform():
    """Test posting to all available platforms."""
    scheduler = MultiPlatformScheduler()

    print("\n📤 Testing multi-platform posting...\n")

    # Test text post
    text = """🧪 Test post from unified automation system.

Building AI automation for local businesses.

#AI #Automation #SmallBusiness"""

    results = scheduler.post_text(
        text=text,
        platforms=['facebook', 'linkedin'],
        link="https://marceausolutions.com"
    )

    print("\n📊 Results:")
    for platform, result in results.items():
        if result['success']:
            print(f"✅ {platform}: Posted successfully")
        else:
            print(f"❌ {platform}: {result.get('error')}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_multi_platform()
    else:
        print("Usage: python -m src.multi_platform_scheduler test")
