"""
Facebook Graph API Integration
Posts content to Facebook Pages via Graph API
"""

import os
import requests
import json
from typing import Optional, List, Dict
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

class FacebookAPI:
    """Facebook Graph API client for posting to Pages."""

    def __init__(self, page_access_token: str = None, page_id: str = None):
        """
        Initialize Facebook API client.

        Args:
            page_access_token: Permanent page access token
            page_id: Facebook Page ID
        """
        self.access_token = page_access_token or os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
        self.page_id = page_id or os.getenv("FACEBOOK_PAGE_ID")
        self.base_url = "https://graph.facebook.com/v18.0"

        if not self.access_token:
            raise ValueError("FACEBOOK_PAGE_ACCESS_TOKEN not found in environment")
        if not self.page_id:
            raise ValueError("FACEBOOK_PAGE_ID not found in environment")

    def create_text_post(self, message: str, link: str = None) -> Dict:
        """
        Create a text post on Facebook Page.

        Args:
            message: Post text content
            link: Optional URL to include

        Returns:
            dict: Response with post_id
        """
        url = f"{self.base_url}/{self.page_id}/feed"

        payload = {
            "message": message,
            "access_token": self.access_token
        }

        if link:
            payload["link"] = link

        response = requests.post(url, data=payload)

        if response.status_code != 200:
            raise Exception(f"Facebook API error: {response.text}")

        result = response.json()
        print(f"✅ Posted to Facebook: {result.get('id')}")

        return result

    def create_photo_post(self, image_path: str, caption: str = "") -> Dict:
        """
        Post an image to Facebook Page.

        Args:
            image_path: Path to image file
            caption: Photo caption

        Returns:
            dict: Response with post_id
        """
        url = f"{self.base_url}/{self.page_id}/photos"

        with open(image_path, 'rb') as image_file:
            files = {'source': image_file}
            data = {
                'caption': caption,
                'access_token': self.access_token
            }

            response = requests.post(url, files=files, data=data)

        if response.status_code != 200:
            raise Exception(f"Facebook API error: {response.text}")

        result = response.json()
        print(f"✅ Posted photo to Facebook: {result.get('id')}")

        return result

    def create_video_post(self, video_path: str, description: str = "") -> Dict:
        """
        Post a video to Facebook Page.

        Args:
            video_path: Path to video file
            description: Video description

        Returns:
            dict: Response with post_id
        """
        url = f"{self.base_url}/{self.page_id}/videos"

        with open(video_path, 'rb') as video_file:
            files = {'source': video_file}
            data = {
                'description': description,
                'access_token': self.access_token
            }

            response = requests.post(url, files=files, data=data)

        if response.status_code != 200:
            raise Exception(f"Facebook API error: {response.text}")

        result = response.json()
        print(f"✅ Posted video to Facebook: {result.get('id')}")

        return result

    def schedule_post(self, message: str, scheduled_time: int, link: str = None) -> Dict:
        """
        Schedule a post for future publication.

        Args:
            message: Post text
            scheduled_time: Unix timestamp for publication
            link: Optional URL

        Returns:
            dict: Response with post_id
        """
        url = f"{self.base_url}/{self.page_id}/feed"

        payload = {
            "message": message,
            "published": False,
            "scheduled_publish_time": scheduled_time,
            "access_token": self.access_token
        }

        if link:
            payload["link"] = link

        response = requests.post(url, data=payload)

        if response.status_code != 200:
            raise Exception(f"Facebook API error: {response.text}")

        result = response.json()
        print(f"⏰ Scheduled Facebook post for {datetime.fromtimestamp(scheduled_time)}")

        return result

    def get_page_insights(self, metrics: List[str] = None) -> Dict:
        """
        Get Page insights/analytics.

        Args:
            metrics: List of metrics to retrieve (default: page_impressions, page_engaged_users)

        Returns:
            dict: Insights data
        """
        if metrics is None:
            metrics = ["page_impressions", "page_engaged_users", "page_post_engagements"]

        url = f"{self.base_url}/{self.page_id}/insights"

        params = {
            "metric": ",".join(metrics),
            "access_token": self.access_token
        }

        response = requests.get(url, params=params)

        if response.status_code != 200:
            raise Exception(f"Facebook API error: {response.text}")

        return response.json()

    def delete_post(self, post_id: str) -> bool:
        """
        Delete a post.

        Args:
            post_id: Facebook post ID

        Returns:
            bool: True if deleted successfully
        """
        url = f"{self.base_url}/{post_id}"

        params = {"access_token": self.access_token}

        response = requests.delete(url, params=params)

        if response.status_code != 200:
            raise Exception(f"Facebook API error: {response.text}")

        print(f"🗑️  Deleted Facebook post: {post_id}")
        return True


def test_facebook_api():
    """Test Facebook API with a sample post."""
    try:
        api = FacebookAPI()

        # Test text post
        result = api.create_text_post(
            message="🧪 Test post from automation system - SW Florida Comfort HVAC is now automated! ❄️",
            link="https://www.swfloridacomfort.com"
        )

        print(f"\n✅ Test successful!")
        print(f"Post ID: {result.get('id')}")
        print(f"View at: https://www.facebook.com/{result.get('id')}")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check FACEBOOK_PAGE_ACCESS_TOKEN in .env")
        print("2. Check FACEBOOK_PAGE_ID in .env")
        print("3. Verify token has pages_manage_posts permission")
        print("4. Make sure token is long-lived (permanent)")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_facebook_api()
    else:
        print("Usage: python -m src.facebook_api test")
