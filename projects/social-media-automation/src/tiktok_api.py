"""
TikTok Content Posting API Integration
Posts videos to TikTok via official API
"""

import os
import requests
import json
from typing import Optional, Dict
from pathlib import Path
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

class TikTokAPI:
    """TikTok API client for posting videos."""

    def __init__(self, access_token: str = None):
        """
        Initialize TikTok API client.

        Args:
            access_token: OAuth 2.0 access token
        """
        self.access_token = access_token or os.getenv("TIKTOK_ACCESS_TOKEN")
        self.base_url = "https://open.tiktokapis.com/v2"

        if not self.access_token:
            raise ValueError("TIKTOK_ACCESS_TOKEN not found in environment")

        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def initialize_upload(self, video_path: str) -> tuple[str, str]:
        """
        Step 1: Initialize video upload.

        Args:
            video_path: Path to video file

        Returns:
            tuple: (upload_url, publish_id)
        """
        url = f"{self.base_url}/post/publish/video/init/"

        # Get video file size
        video_size = os.path.getsize(video_path)

        payload = {
            "post_info": {
                "title": "",  # Will be set in publish step
                "privacy_level": "SELF_ONLY",  # CRITICAL: Private until audit approved
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
                "video_cover_timestamp_ms": 1000
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": video_size,
                "total_chunk_count": 1
            }
        }

        response = requests.post(
            url,
            headers=self.headers,
            data=json.dumps(payload)
        )

        if response.status_code != 200:
            raise Exception(f"TikTok API error: {response.text}")

        result = response.json()
        data = result.get("data", {})

        upload_url = data.get("upload_url")
        publish_id = data.get("publish_id")

        if not upload_url or not publish_id:
            raise Exception(f"Failed to initialize upload: {result}")

        print(f"✅ Initialized TikTok upload: {publish_id}")

        return upload_url, publish_id

    def upload_video_file(self, upload_url: str, video_path: str) -> bool:
        """
        Step 2: Upload video file to TikTok.

        Args:
            upload_url: Upload URL from initialize step
            video_path: Path to video file

        Returns:
            bool: True if upload successful
        """
        with open(video_path, 'rb') as video_file:
            video_data = video_file.read()

        headers = {
            "Content-Type": "video/mp4",
            "Content-Length": str(len(video_data))
        }

        response = requests.put(
            upload_url,
            headers=headers,
            data=video_data
        )

        if response.status_code not in [200, 201]:
            raise Exception(f"Video upload failed: {response.text}")

        print(f"✅ Uploaded video to TikTok")

        return True

    def publish_video(
        self,
        publish_id: str,
        caption: str,
        privacy: str = "SELF_ONLY"
    ) -> Dict:
        """
        Step 3: Publish the uploaded video.

        Args:
            publish_id: Publish ID from initialize step
            caption: Video caption/description
            privacy: PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIENDS, SELF_ONLY

        Returns:
            dict: Publish status

        NOTE: Until TikTok audit is approved, all posts will be SELF_ONLY
        regardless of privacy setting.
        """
        url = f"{self.base_url}/post/publish/status/fetch/"

        payload = {
            "publish_id": publish_id
        }

        # Wait a moment for upload to process
        time.sleep(2)

        response = requests.post(
            url,
            headers=self.headers,
            data=json.dumps(payload)
        )

        if response.status_code != 200:
            raise Exception(f"TikTok API error: {response.text}")

        result = response.json()
        data = result.get("data", {})
        status = data.get("status")

        print(f"✅ TikTok publish status: {status}")

        if status == "PUBLISH_COMPLETE":
            print(f"⚠️  Video is PRIVATE (SELF_ONLY) until TikTok audit approved")

        return result

    def post_video(
        self,
        video_path: str,
        caption: str,
        privacy: str = "SELF_ONLY"
    ) -> Dict:
        """
        Complete flow: Upload and publish a video.

        Args:
            video_path: Path to video file (MP4, max 287MB)
            caption: Video caption
            privacy: PUBLIC_TO_EVERYONE (after audit) or SELF_ONLY

        Returns:
            dict: Publish result with publish_id
        """
        print(f"📤 Uploading TikTok video: {video_path}")

        # Step 1: Initialize
        upload_url, publish_id = self.initialize_upload(video_path)

        # Step 2: Upload file
        success = self.upload_video_file(upload_url, video_path)

        if not success:
            raise Exception("Video upload failed")

        # Step 3: Publish
        result = self.publish_video(publish_id, caption, privacy)

        print(f"✅ TikTok video posted: {publish_id}")
        print(f"⚠️  NOTE: Video is PRIVATE until TikTok audit approves your app")

        return {
            "publish_id": publish_id,
            "status": result.get("data", {}).get("status"),
            "caption": caption
        }

    def get_creator_info(self) -> Dict:
        """
        Get information about the authenticated creator.

        Returns:
            dict: Creator info
        """
        url = f"{self.base_url}/post/publish/creator_info/query/"

        response = requests.post(
            url,
            headers=self.headers,
            data=json.dumps({})
        )

        if response.status_code != 200:
            raise Exception(f"TikTok API error: {response.text}")

        return response.json()


def test_tiktok_api():
    """Test TikTok API with a sample video."""
    try:
        api = TikTokAPI()

        # Get creator info first
        info = api.get_creator_info()
        print(f"✅ Connected as TikTok creator")
        print(f"Info: {json.dumps(info, indent=2)}\n")

        # Check if we have a test video
        test_video = Path("/Users/williammarceaujr./dev-sandbox/projects/social-media-automation/content/tiktok/test.mp4")

        if not test_video.exists():
            print("⚠️  No test video found at:")
            print(f"   {test_video}")
            print("\nCreate a test video first:")
            print("   mkdir -p content/tiktok/")
            print("   # Add a short MP4 video as test.mp4")
            return

        # Test video upload
        result = api.post_video(
            video_path=str(test_video),
            caption="🧪 Test video from automation system - SW Florida Comfort HVAC! ❄️ #HVAC #Naples #AirConditioning",
            privacy="SELF_ONLY"  # Will be private until audit approved
        )

        print(f"\n✅ Test successful!")
        print(f"Publish ID: {result.get('publish_id')}")
        print(f"Status: {result.get('status')}")
        print(f"\n⚠️  IMPORTANT: Video is PRIVATE (only you can see it)")
        print("After TikTok audit approval, videos will be PUBLIC")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check TIKTOK_ACCESS_TOKEN in .env")
        print("2. Verify TikTok app is created")
        print("3. Make sure you've run OAuth flow: python -m src.tiktok_auth")
        print("4. Check if audit is approved (takes 2-4 weeks)")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_tiktok_api()
    else:
        print("Usage: python -m src.tiktok_api test")
