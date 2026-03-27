#!/usr/bin/env python3
"""
tiktok_api.py - TikTok Content Posting API Client

Handles video upload and publishing to TikTok using the official Content Posting API.

IMPORTANT: Unaudited apps can only post PRIVATE videos. To post PUBLIC:
1. Submit app for TikTok audit
2. Get approval (2-4 weeks)
3. Then set privacy_level="PUBLIC_TO_EVERYONE"

Environment Variables Required:
    TIKTOK_ACCESS_TOKEN - OAuth access token (from tiktok_auth.py)

Usage:
    from src.tiktok_api import TikTokAPI, PrivacyLevel

    api = TikTokAPI()
    result = api.post_video(
        video_path="video.mp4",
        caption="My video #tiktok",
        privacy=PrivacyLevel.SELF_ONLY  # Until audited
    )
"""

import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum

from dotenv import load_dotenv
load_dotenv()

# Try to import requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests not installed. Run: pip install requests")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PrivacyLevel(Enum):
    """TikTok video privacy levels."""
    PUBLIC_TO_EVERYONE = "PUBLIC_TO_EVERYONE"  # Requires audit approval
    MUTUAL_FOLLOW_FRIENDS = "MUTUAL_FOLLOW_FRIENDS"
    SELF_ONLY = "SELF_ONLY"  # Default for unaudited apps


@dataclass
class UploadResult:
    """Result of a TikTok upload operation."""
    success: bool
    publish_id: Optional[str] = None
    video_url: Optional[str] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class VideoStatus:
    """Status of a TikTok video."""
    publish_id: str
    status: str  # PROCESSING, PUBLISHED, FAILED
    video_id: Optional[str] = None
    error: Optional[str] = None


class TikTokAPI:
    """
    TikTok Content Posting API Client.

    Supports video upload and publishing using the official API.
    """

    BASE_URL = "https://open.tiktokapis.com/v2"
    POST_LOG_FILE = Path(__file__).parent.parent / "output" / "tiktok_posts.json"

    # Supported video formats
    SUPPORTED_FORMATS = {'.mp4', '.mov', '.webm'}

    # TikTok video requirements
    MAX_FILE_SIZE = 287.6 * 1024 * 1024  # 287.6 MB
    MAX_DURATION = 600  # 10 minutes
    MIN_DURATION = 3  # 3 seconds

    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize TikTok API client.

        Args:
            access_token: OAuth access token (or use TIKTOK_ACCESS_TOKEN env var)
        """
        self.access_token = access_token or os.getenv("TIKTOK_ACCESS_TOKEN")
        self.posts: List[Dict[str, Any]] = []

        self._load_post_history()

        if not self.access_token:
            logger.warning("No TikTok access token. Run tiktok_auth.py authorize first.")

    def _load_post_history(self):
        """Load post history from file."""
        if self.POST_LOG_FILE.exists():
            try:
                with open(self.POST_LOG_FILE) as f:
                    self.posts = json.load(f)
            except Exception as e:
                logger.warning(f"Error loading post history: {e}")

    def _save_post_history(self):
        """Save post history to file."""
        self.POST_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.POST_LOG_FILE, 'w') as f:
            json.dump(self.posts, f, indent=2)

    def _log_post(self, result: UploadResult, video_path: str, caption: str):
        """Log a post attempt."""
        self.posts.append({
            "timestamp": datetime.now().isoformat(),
            "video_path": video_path,
            "caption": caption[:100] + "..." if len(caption) > 100 else caption,
            "success": result.success,
            "publish_id": result.publish_id,
            "video_url": result.video_url,
            "error": result.error
        })
        self._save_post_history()

    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def _validate_video(self, video_path: str) -> Optional[str]:
        """
        Validate video file before upload.

        Returns:
            Error message if invalid, None if valid
        """
        path = Path(video_path)

        if not path.exists():
            return f"Video file not found: {video_path}"

        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            return f"Unsupported format: {path.suffix}. Use: {self.SUPPORTED_FORMATS}"

        file_size = path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            return f"File too large: {file_size / (1024*1024):.1f}MB (max {self.MAX_FILE_SIZE / (1024*1024):.1f}MB)"

        return None

    def is_ready(self) -> bool:
        """Check if API client is ready to post."""
        return bool(self.access_token)

    def initialize_upload(self, video_path: str) -> Dict[str, Any]:
        """
        Step 1: Initialize video upload and get upload URL.

        Args:
            video_path: Path to video file

        Returns:
            Response with upload_url and publish_id
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library required")

        file_size = os.path.getsize(video_path)

        payload = {
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": file_size,  # Single chunk upload
                "total_chunk_count": 1
            }
        }

        response = requests.post(
            f"{self.BASE_URL}/post/publish/video/init/",
            headers=self._get_headers(),
            json=payload
        )

        result = response.json()
        logger.debug(f"Initialize upload response: {result}")

        return result

    def upload_video_file(self, upload_url: str, video_path: str) -> bool:
        """
        Step 2: Upload video file to TikTok.

        Args:
            upload_url: Upload URL from initialize_upload
            video_path: Path to video file

        Returns:
            True if upload successful
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library required")

        # Determine content type
        suffix = Path(video_path).suffix.lower()
        content_types = {
            '.mp4': 'video/mp4',
            '.mov': 'video/quicktime',
            '.webm': 'video/webm'
        }
        content_type = content_types.get(suffix, 'video/mp4')

        with open(video_path, "rb") as video_file:
            response = requests.put(
                upload_url,
                headers={
                    "Content-Type": content_type,
                    "Content-Range": f"bytes 0-{os.path.getsize(video_path) - 1}/{os.path.getsize(video_path)}"
                },
                data=video_file
            )

        logger.debug(f"Upload response status: {response.status_code}")
        return response.status_code in [200, 201]

    def publish_video(
        self,
        publish_id: str,
        caption: str,
        privacy_level: PrivacyLevel = PrivacyLevel.SELF_ONLY,
        disable_duet: bool = False,
        disable_comment: bool = False,
        disable_stitch: bool = False,
        video_cover_timestamp_ms: int = 1000
    ) -> Dict[str, Any]:
        """
        Step 3: Publish uploaded video.

        Args:
            publish_id: ID from initialize_upload
            caption: Video caption (max 2,200 chars, includes hashtags)
            privacy_level: Privacy setting (SELF_ONLY until audited)
            disable_duet: Disable duet feature
            disable_comment: Disable comments
            disable_stitch: Disable stitch feature
            video_cover_timestamp_ms: Thumbnail timestamp in milliseconds

        Returns:
            Publish response data
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library required")

        # Truncate caption if too long
        max_caption_length = 2200
        if len(caption) > max_caption_length:
            caption = caption[:max_caption_length - 3] + "..."
            logger.warning(f"Caption truncated to {max_caption_length} characters")

        payload = {
            "post_info": {
                "title": caption,
                "privacy_level": privacy_level.value,
                "disable_duet": disable_duet,
                "disable_comment": disable_comment,
                "disable_stitch": disable_stitch,
                "video_cover_timestamp_ms": video_cover_timestamp_ms
            },
            "source_info": {
                "source": "FILE_UPLOAD"
            }
        }

        response = requests.post(
            f"{self.BASE_URL}/post/publish/video/publish/",
            headers=self._get_headers(),
            json=payload
        )

        result = response.json()
        logger.debug(f"Publish response: {result}")

        return result

    def get_publish_status(self, publish_id: str) -> VideoStatus:
        """
        Get status of a published video.

        Args:
            publish_id: Publish ID from post_video

        Returns:
            VideoStatus with current status
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library required")

        response = requests.post(
            f"{self.BASE_URL}/post/publish/status/fetch/",
            headers=self._get_headers(),
            json={"publish_id": publish_id}
        )

        result = response.json()
        data = result.get("data", {})

        return VideoStatus(
            publish_id=publish_id,
            status=data.get("status", "UNKNOWN"),
            video_id=data.get("video_id"),
            error=result.get("error", {}).get("message")
        )

    def post_video(
        self,
        video_path: str,
        caption: str,
        privacy: PrivacyLevel = PrivacyLevel.SELF_ONLY,
        wait_for_publish: bool = True,
        max_wait_seconds: int = 300
    ) -> UploadResult:
        """
        Complete flow: Upload and publish video.

        Args:
            video_path: Path to video file
            caption: Video caption with hashtags
            privacy: Privacy level (SELF_ONLY until audited)
            wait_for_publish: Wait for video to finish processing
            max_wait_seconds: Maximum wait time for processing

        Returns:
            UploadResult with success status and video URL
        """
        # Validate prerequisites
        if not self.is_ready():
            return UploadResult(
                success=False,
                error="TikTok API not ready. Run tiktok_auth.py authorize first."
            )

        # Validate video
        validation_error = self._validate_video(video_path)
        if validation_error:
            return UploadResult(success=False, error=validation_error)

        try:
            # Step 1: Initialize upload
            logger.info(f"Initializing upload for: {video_path}")
            init_result = self.initialize_upload(video_path)

            if "error" in init_result:
                error_msg = init_result.get("error", {}).get("message", "Unknown error")
                return UploadResult(
                    success=False,
                    error=f"Initialize failed: {error_msg}",
                    error_code=init_result.get("error", {}).get("code")
                )

            upload_url = init_result.get("data", {}).get("upload_url")
            publish_id = init_result.get("data", {}).get("publish_id")

            if not upload_url or not publish_id:
                return UploadResult(
                    success=False,
                    error=f"Invalid init response: {init_result}"
                )

            # Step 2: Upload file
            logger.info("Uploading video file...")
            upload_success = self.upload_video_file(upload_url, video_path)

            if not upload_success:
                return UploadResult(
                    success=False,
                    error="Video file upload failed",
                    publish_id=publish_id
                )

            # Step 3: Publish
            logger.info(f"Publishing video with privacy: {privacy.value}")
            publish_result = self.publish_video(publish_id, caption, privacy)

            if "error" in publish_result:
                error_msg = publish_result.get("error", {}).get("message", "Unknown error")
                return UploadResult(
                    success=False,
                    error=f"Publish failed: {error_msg}",
                    error_code=publish_result.get("error", {}).get("code"),
                    publish_id=publish_id
                )

            # Wait for processing if requested
            video_id = None
            if wait_for_publish:
                logger.info("Waiting for video processing...")
                start_time = time.time()

                while time.time() - start_time < max_wait_seconds:
                    status = self.get_publish_status(publish_id)

                    if status.status == "PUBLISHED":
                        video_id = status.video_id
                        logger.info(f"Video published: {video_id}")
                        break
                    elif status.status == "FAILED":
                        result = UploadResult(
                            success=False,
                            error=f"Processing failed: {status.error}",
                            publish_id=publish_id
                        )
                        self._log_post(result, video_path, caption)
                        return result

                    time.sleep(5)  # Check every 5 seconds

            # Build video URL (TikTok account username needed for full URL)
            video_url = None
            if video_id:
                # Note: Full URL requires account username
                video_url = f"https://www.tiktok.com/@user/video/{video_id}"

            result = UploadResult(
                success=True,
                publish_id=publish_id,
                video_url=video_url,
                created_at=datetime.now().isoformat()
            )

            self._log_post(result, video_path, caption)
            logger.info(f"Video posted successfully! Publish ID: {publish_id}")

            return result

        except Exception as e:
            logger.error(f"Error posting video: {e}")
            result = UploadResult(success=False, error=str(e))
            self._log_post(result, video_path, caption)
            return result

    def get_post_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent post history."""
        return self.posts[-limit:][::-1]  # Most recent first


def main():
    """CLI for TikTok API client."""
    import argparse

    parser = argparse.ArgumentParser(description='TikTok Content Posting API')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Post command
    post_parser = subparsers.add_parser('post', help='Post a video')
    post_parser.add_argument('video_path', help='Path to video file')
    post_parser.add_argument('--caption', '-c', required=True, help='Video caption')
    post_parser.add_argument(
        '--privacy', '-p',
        choices=['public', 'friends', 'private'],
        default='private',
        help='Privacy level (default: private)'
    )

    # Status command
    status_parser = subparsers.add_parser('status', help='Get video publish status')
    status_parser.add_argument('publish_id', help='Publish ID to check')

    # History command
    history_parser = subparsers.add_parser('history', help='Show post history')
    history_parser.add_argument('--limit', '-n', type=int, default=10, help='Number of posts')

    args = parser.parse_args()

    api = TikTokAPI()

    if args.command == 'post':
        privacy_map = {
            'public': PrivacyLevel.PUBLIC_TO_EVERYONE,
            'friends': PrivacyLevel.MUTUAL_FOLLOW_FRIENDS,
            'private': PrivacyLevel.SELF_ONLY
        }
        privacy = privacy_map[args.privacy]

        if privacy == PrivacyLevel.PUBLIC_TO_EVERYONE:
            print("\nWARNING: Public posting requires TikTok audit approval.")
            print("If not audited, video will be posted as PRIVATE.\n")

        result = api.post_video(
            video_path=args.video_path,
            caption=args.caption,
            privacy=privacy
        )

        if result.success:
            print(f"\nVideo posted successfully!")
            print(f"Publish ID: {result.publish_id}")
            if result.video_url:
                print(f"URL: {result.video_url}")
        else:
            print(f"\nPost failed: {result.error}")
            return 1

    elif args.command == 'status':
        status = api.get_publish_status(args.publish_id)
        print(f"\nPublish Status:")
        print(f"  ID: {status.publish_id}")
        print(f"  Status: {status.status}")
        if status.video_id:
            print(f"  Video ID: {status.video_id}")
        if status.error:
            print(f"  Error: {status.error}")

    elif args.command == 'history':
        history = api.get_post_history(limit=args.limit)
        if not history:
            print("No post history found.")
        else:
            print(f"\nRecent Posts ({len(history)}):")
            print("-" * 60)
            for post in history:
                status = "✓" if post['success'] else "✗"
                print(f"{status} {post['timestamp'][:19]}")
                print(f"  Caption: {post['caption']}")
                if post['publish_id']:
                    print(f"  Publish ID: {post['publish_id']}")
                if post['error']:
                    print(f"  Error: {post['error']}")
                print()

    else:
        parser.print_help()

    return 0


if __name__ == '__main__':
    exit(main())
