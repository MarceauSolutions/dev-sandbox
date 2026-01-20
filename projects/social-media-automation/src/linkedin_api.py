"""
LinkedIn API Integration
Posts content to LinkedIn via Marketing Developer Platform API
"""

import os
import requests
import json
from typing import Optional, Dict, List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LinkedInAPI:
    """LinkedIn API client for posting to personal profiles."""

    def __init__(self, access_token: str = None):
        """
        Initialize LinkedIn API client.

        Args:
            access_token: OAuth 2.0 access token
        """
        self.access_token = access_token or os.getenv("LINKEDIN_ACCESS_TOKEN")
        self.base_url = "https://api.linkedin.com/v2"

        if not self.access_token:
            raise ValueError("LINKEDIN_ACCESS_TOKEN not found in environment")

        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }

    def get_user_id(self) -> str:
        """
        Get the authenticated user's LinkedIn ID.

        Returns:
            str: LinkedIn user ID (URN format)
        """
        url = f"{self.base_url}/me"

        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            raise Exception(f"LinkedIn API error: {response.text}")

        result = response.json()
        user_id = result.get("id")

        return user_id

    def create_text_post(
        self,
        text: str,
        visibility: str = "PUBLIC"
    ) -> Dict:
        """
        Create a text post on LinkedIn.

        Args:
            text: Post content (max 3,000 characters recommended)
            visibility: PUBLIC or CONNECTIONS

        Returns:
            dict: Response with post URN
        """
        user_id = self.get_user_id()

        url = f"{self.base_url}/ugcPosts"

        payload = {
            "author": f"urn:li:person:{user_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }

        response = requests.post(
            url,
            headers=self.headers,
            data=json.dumps(payload)
        )

        if response.status_code != 201:
            raise Exception(f"LinkedIn API error: {response.text}")

        result = response.json()
        post_id = result.get("id")

        print(f"✅ Posted to LinkedIn: {post_id}")

        return result

    def create_link_post(
        self,
        text: str,
        link_url: str,
        link_title: str = "",
        visibility: str = "PUBLIC"
    ) -> Dict:
        """
        Create a post with a link on LinkedIn.

        Args:
            text: Post commentary
            link_url: URL to share
            link_title: Title for the link preview
            visibility: PUBLIC or CONNECTIONS

        Returns:
            dict: Response with post URN
        """
        user_id = self.get_user_id()

        url = f"{self.base_url}/ugcPosts"

        payload = {
            "author": f"urn:li:person:{user_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "ARTICLE",
                    "media": [
                        {
                            "status": "READY",
                            "originalUrl": link_url,
                            "title": {
                                "text": link_title or link_url
                            }
                        }
                    ]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }

        response = requests.post(
            url,
            headers=self.headers,
            data=json.dumps(payload)
        )

        if response.status_code != 201:
            raise Exception(f"LinkedIn API error: {response.text}")

        result = response.json()
        post_id = result.get("id")

        print(f"✅ Posted link to LinkedIn: {post_id}")

        return result

    def create_image_post(
        self,
        text: str,
        image_url: str,
        visibility: str = "PUBLIC"
    ) -> Dict:
        """
        Create a post with an image on LinkedIn.

        Args:
            text: Post commentary
            image_url: Public URL of the image
            visibility: PUBLIC or CONNECTIONS

        Returns:
            dict: Response with post URN
        """
        user_id = self.get_user_id()

        url = f"{self.base_url}/ugcPosts"

        payload = {
            "author": f"urn:li:person:{user_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "IMAGE",
                    "media": [
                        {
                            "status": "READY",
                            "originalUrl": image_url
                        }
                    ]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }

        response = requests.post(
            url,
            headers=self.headers,
            data=json.dumps(payload)
        )

        if response.status_code != 201:
            raise Exception(f"LinkedIn API error: {response.text}")

        result = response.json()
        post_id = result.get("id")

        print(f"✅ Posted image to LinkedIn: {post_id}")

        return result

    def get_profile_stats(self) -> Dict:
        """
        Get basic profile statistics.

        Returns:
            dict: Profile data
        """
        url = f"{self.base_url}/me"

        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            raise Exception(f"LinkedIn API error: {response.text}")

        return response.json()


def test_linkedin_api():
    """Test LinkedIn API with a sample post."""
    try:
        api = LinkedInAPI()

        # Get user ID first
        user_id = api.get_user_id()
        print(f"✅ Connected as LinkedIn user: {user_id}")

        # Test text post
        result = api.create_text_post(
            text="""🧪 Test post from automation system.

Building AI automation for local businesses - Voice AI, lead generation, and workflow automation.

If you're a small business owner spending 10+ hours/week on repetitive tasks, let's talk.

#AI #Automation #SmallBusiness""",
            visibility="PUBLIC"
        )

        print(f"\n✅ Test successful!")
        print(f"Post URN: {result.get('id')}")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check LINKEDIN_ACCESS_TOKEN in .env")
        print("2. Verify Marketing Developer Platform is approved")
        print("3. Make sure token has w_member_social scope")
        print("4. Run OAuth flow first: python -m src.linkedin_auth")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_linkedin_api()
    else:
        print("Usage: python -m src.linkedin_api test")
