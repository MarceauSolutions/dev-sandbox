"""
LinkedIn Company Page API Integration
Posts content to Marceau Solutions LLC company page via Community Management API
"""

import os
import requests
import json
from typing import Optional, Dict
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LinkedInCompanyAPI:
    """LinkedIn API client for posting to company pages."""

    def __init__(self, access_token: str = None):
        """
        Initialize LinkedIn Company API client.

        Args:
            access_token: OAuth 2.0 access token (from company posting app)
        """
        self.access_token = access_token or os.getenv("LINKEDIN_COMPANY_ACCESS_TOKEN")
        self.base_url = "https://api.linkedin.com/v2"

        if not self.access_token:
            raise ValueError("LINKEDIN_COMPANY_ACCESS_TOKEN not found in environment")

        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": "202401"
        }

    def get_organization_id(self) -> str:
        """
        Get the organization ID for Marceau Solutions LLC.

        You need to be an admin of the organization to access this.

        Returns:
            str: Organization ID (numeric)
        """
        url = f"{self.base_url}/organizationAcls"
        params = {"q": "roleAssignee"}

        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code != 200:
            raise Exception(f"LinkedIn API error: {response.text}")

        result = response.json()

        # Get first organization ID
        if "elements" in result and len(result["elements"]) > 0:
            org_urn = result["elements"][0].get("organization")
            # Extract numeric ID from URN like "urn:li:organization:123456"
            org_id = org_urn.split(":")[-1]
            print(f"✅ Organization ID: {org_id}")
            print(f"   Organization URN: {org_urn}")
            return org_id
        else:
            raise Exception("No organizations found. Make sure you're an admin of Marceau Solutions LLC.")

    def create_text_post(
        self,
        text: str,
        organization_id: str,
        visibility: str = "PUBLIC"
    ) -> Dict:
        """
        Create a text post on company page.

        Args:
            text: Post content (max 3,000 characters)
            organization_id: Organization ID (numeric)
            visibility: PUBLIC or CONNECTIONS

        Returns:
            dict: Response with post URN
        """
        url = f"{self.base_url}/ugcPosts"

        payload = {
            "author": f"urn:li:organization:{organization_id}",
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

        print(f"✅ Posted to company page!")
        print(f"   Post URN: {post_id}")
        print(f"   View at: https://www.linkedin.com/company/marceau-solutions-llc/")

        return result

    def create_link_post(
        self,
        text: str,
        link_url: str,
        organization_id: str,
        link_title: str = "",
        visibility: str = "PUBLIC"
    ) -> Dict:
        """
        Create a post with a link on company page.

        Args:
            text: Post commentary
            link_url: URL to share
            organization_id: Organization ID (numeric)
            link_title: Title for the link preview
            visibility: PUBLIC or CONNECTIONS

        Returns:
            dict: Response with post URN
        """
        url = f"{self.base_url}/ugcPosts"

        payload = {
            "author": f"urn:li:organization:{organization_id}",
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

        print(f"✅ Posted link to company page!")
        print(f"   Post URN: {post_id}")

        return result


def test_company_api():
    """Test LinkedIn Company API with a sample post."""
    try:
        api = LinkedInCompanyAPI()

        print("📋 Step 1: Getting organization ID...")
        org_id = api.get_organization_id()

        print(f"\n📝 Step 2: Creating test post...")
        post = api.create_text_post(
            text="""🚀 Exciting update from Marceau Solutions!

We're building AI automation systems that help local businesses:

✅ Answer every customer call (24/7 Voice AI)
✅ Generate qualified leads automatically
✅ Automate repetitive workflows

If you're a small business owner losing revenue to missed calls or manual work, let's talk.

#AI #Automation #SmallBusiness #LocalBusiness""",
            organization_id=org_id,
            visibility="PUBLIC"
        )

        print(f"\n✅ Test successful!")
        print(f"\nPost details:")
        print(f"- Posted to: Marceau Solutions LLC company page")
        print(f"- Post ID: {post.get('id')}")
        print(f"- View at: https://www.linkedin.com/company/marceau-solutions-llc/")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check LINKEDIN_COMPANY_ACCESS_TOKEN in .env")
        print("2. Verify Community Management API is approved")
        print("3. Make sure token has w_organization_social scope")
        print("4. Ensure you're an admin of Marceau Solutions LLC")
        print("5. Run OAuth flow first: python -m src.linkedin_company_auth")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "get-org-id":
            api = LinkedInCompanyAPI()
            org_id = api.get_organization_id()
        elif command == "test":
            test_company_api()
        else:
            print("Usage:")
            print("  python -m src.linkedin_company_api get-org-id")
            print("  python -m src.linkedin_company_api test")
    else:
        print("Usage:")
        print("  python -m src.linkedin_company_api get-org-id")
        print("  python -m src.linkedin_company_api test")
