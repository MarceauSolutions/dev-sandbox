#!/usr/bin/env python3
"""
youtube_uploader.py - YouTube Video Upload and Management

Handles video uploads, Shorts publishing, and metadata management using
the YouTube Data API v3.

Usage:
    from youtube_uploader import YouTubeUploader

    uploader = YouTubeUploader()
    result = uploader.upload_video(
        video_path="path/to/video.mp4",
        title="My Video Title",
        description="Video description",
        tags=["tag1", "tag2"],
        privacy="private"
    )

Environment Variables:
    YOUTUBE_CLIENT_ID - OAuth 2.0 Client ID
    YOUTUBE_CLIENT_SECRET - OAuth 2.0 Client Secret
    YOUTUBE_REFRESH_TOKEN - OAuth 2.0 Refresh Token

Or use credentials file:
    ~/.google/youtube_credentials.json

CLI Usage:
    python -m src.youtube_uploader upload --video path/to/video.mp4 --title "Title"
    python -m src.youtube_uploader upload-short --video path/to/short.mp4 --title "Title"
    python -m src.youtube_uploader status --video-id VIDEO_ID
    python -m src.youtube_uploader update --video-id VIDEO_ID --title "New Title"
"""

import os
import json
import logging
import time
import http.client
import httplib2
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Try to import Google API libraries
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================

# YouTube Shorts constraints
SHORTS_MAX_DURATION_SECONDS = 60
SHORTS_MIN_ASPECT_RATIO = 0.5625  # 9:16
SHORTS_RECOMMENDED_RESOLUTION = (1080, 1920)  # Width x Height (vertical)

# Standard video recommendations
RECOMMENDED_VIDEO_RESOLUTIONS = {
    "4K": (3840, 2160),
    "1440p": (2560, 1440),
    "1080p": (1920, 1080),
    "720p": (1280, 720),
    "480p": (854, 480),
    "360p": (640, 360),
}

# Supported video formats
SUPPORTED_VIDEO_FORMATS = [
    ".mp4", ".mov", ".avi", ".wmv", ".flv", ".3gp",
    ".webm", ".mkv", ".mpeg", ".mpg", ".m4v"
]

# Maximum file size (128 GB for videos, though API uses resumable uploads)
MAX_FILE_SIZE_BYTES = 128 * 1024 * 1024 * 1024

# YouTube category IDs
# See: https://developers.google.com/youtube/v3/docs/videoCategories/list
class YouTubeCategory(Enum):
    """YouTube video category IDs."""
    FILM_ANIMATION = "1"
    AUTOS_VEHICLES = "2"
    MUSIC = "10"
    PETS_ANIMALS = "15"
    SPORTS = "17"
    SHORT_MOVIES = "18"
    TRAVEL_EVENTS = "19"
    GAMING = "20"
    VIDEOBLOGGING = "21"
    PEOPLE_BLOGS = "22"
    COMEDY = "23"
    ENTERTAINMENT = "24"
    NEWS_POLITICS = "25"
    HOWTO_STYLE = "26"
    EDUCATION = "27"
    SCIENCE_TECH = "28"
    NONPROFITS_ACTIVISM = "29"
    MOVIES = "30"
    ANIME_ANIMATION = "31"
    ACTION_ADVENTURE = "32"
    CLASSICS = "33"
    DOCUMENTARY = "35"
    DRAMA = "36"
    FAMILY = "37"
    FOREIGN = "38"
    HORROR = "39"
    SCIFI_FANTASY = "40"
    THRILLER = "41"
    SHORTS = "42"
    SHOWS = "43"
    TRAILERS = "44"


# Common category shortcuts
CATEGORY_IDS = {
    "sports": "17",
    "education": "27",
    "entertainment": "24",
    "music": "10",
    "gaming": "20",
    "howto": "26",
    "science": "28",
    "comedy": "23",
    "news": "25",
    "people": "22",
    "pets": "15",
    "travel": "19",
    "film": "1",
    "autos": "2",
}

# Privacy settings
class PrivacyStatus(Enum):
    """YouTube video privacy settings."""
    PUBLIC = "public"
    PRIVATE = "private"
    UNLISTED = "unlisted"


# Upload retry configuration
MAX_RETRIES = 10
RETRY_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, http.client.NotConnected,
                    http.client.IncompleteRead, http.client.ImproperConnectionState,
                    http.client.CannotSendRequest, http.client.CannotSendHeader,
                    http.client.ResponseNotReady, http.client.BadStatusLine)

# OAuth scopes required
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class UploadResult:
    """Result of a video upload attempt."""
    success: bool
    video_id: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    privacy: Optional[str] = None
    upload_time: Optional[str] = None
    error: Optional[str] = None
    is_short: bool = False


@dataclass
class VideoStatus:
    """Status of an uploaded video."""
    video_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    privacy_status: Optional[str] = None
    upload_status: Optional[str] = None
    failure_reason: Optional[str] = None
    rejection_reason: Optional[str] = None
    processing_status: Optional[str] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    published_at: Optional[str] = None


@dataclass
class UpdateResult:
    """Result of a metadata update attempt."""
    success: bool
    video_id: Optional[str] = None
    title: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# CREDENTIALS MANAGEMENT
# ============================================================================

class YouTubeCredentials:
    """
    Manages YouTube API credentials from environment or file.
    """

    CREDENTIALS_FILE = Path.home() / ".google" / "youtube_credentials.json"
    TOKEN_FILE = Path.home() / ".google" / "youtube_token.json"

    def __init__(self):
        self.credentials: Optional[Credentials] = None
        self._load_credentials()

    def _load_credentials(self):
        """Load credentials from environment or file."""
        # Try environment variables first
        client_id = os.getenv("YOUTUBE_CLIENT_ID")
        client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
        refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")

        if all([client_id, client_secret, refresh_token]):
            logger.info("Loading YouTube credentials from environment")
            self.credentials = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
                scopes=YOUTUBE_SCOPES
            )
            return

        # Try token file (previously authenticated)
        if self.TOKEN_FILE.exists():
            logger.info(f"Loading YouTube credentials from {self.TOKEN_FILE}")
            try:
                self.credentials = Credentials.from_authorized_user_file(
                    str(self.TOKEN_FILE),
                    YOUTUBE_SCOPES
                )
                return
            except Exception as e:
                logger.warning(f"Error loading token file: {e}")

        # Try credentials file (OAuth client secrets)
        if self.CREDENTIALS_FILE.exists():
            logger.info(f"Found credentials file at {self.CREDENTIALS_FILE}")
            logger.info("Run authentication flow to generate token")
        else:
            logger.warning("No YouTube credentials found")

    def is_valid(self) -> bool:
        """Check if credentials are valid."""
        if not self.credentials:
            return False
        return self.credentials.valid or self.credentials.expired

    def refresh(self) -> bool:
        """Refresh credentials if expired."""
        if not self.credentials:
            return False

        if self.credentials.expired and self.credentials.refresh_token:
            try:
                self.credentials.refresh(Request())
                # Save refreshed token
                self._save_token()
                return True
            except Exception as e:
                logger.error(f"Error refreshing credentials: {e}")
                return False
        return True

    def _save_token(self):
        """Save credentials to token file."""
        if self.credentials:
            self.TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.TOKEN_FILE, 'w') as f:
                f.write(self.credentials.to_json())

    def run_auth_flow(self) -> bool:
        """
        Run OAuth authentication flow.

        Requires credentials file at ~/.google/youtube_credentials.json
        """
        if not self.CREDENTIALS_FILE.exists():
            logger.error(f"Credentials file not found: {self.CREDENTIALS_FILE}")
            self._print_setup_instructions()
            return False

        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.CREDENTIALS_FILE),
                YOUTUBE_SCOPES
            )
            self.credentials = flow.run_local_server(port=0)
            self._save_token()
            logger.info("Authentication successful!")
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    @staticmethod
    def _print_setup_instructions():
        """Print instructions for setting up YouTube API credentials."""
        print("""
================================================================================
YOUTUBE API SETUP INSTRUCTIONS
================================================================================

Option 1: Environment Variables (Recommended for automation)
-----------------------------------------------------------
Set these environment variables in your .env file:

    YOUTUBE_CLIENT_ID=your_client_id
    YOUTUBE_CLIENT_SECRET=your_client_secret
    YOUTUBE_REFRESH_TOKEN=your_refresh_token

To obtain these:
1. Go to https://console.cloud.google.com
2. Create a project or select existing
3. Enable YouTube Data API v3
4. Go to Credentials > Create Credentials > OAuth 2.0 Client ID
5. Application type: Desktop app
6. Download JSON and use the client_id and client_secret
7. For refresh_token, run: python -m src.youtube_uploader auth


Option 2: Credentials File
--------------------------
1. Download OAuth client secrets JSON from Google Cloud Console
2. Save to: ~/.google/youtube_credentials.json
3. Run authentication: python -m src.youtube_uploader auth
4. This creates a token file for subsequent use


Required API Scopes:
- https://www.googleapis.com/auth/youtube.upload
- https://www.googleapis.com/auth/youtube
- https://www.googleapis.com/auth/youtube.force-ssl

================================================================================
""")


# ============================================================================
# MAIN UPLOADER CLASS
# ============================================================================

class YouTubeUploader:
    """
    YouTube video uploader with support for regular videos and Shorts.

    Handles:
    - Video uploads with resumable upload protocol
    - YouTube Shorts (vertical videos under 60 seconds)
    - Metadata updates (title, description, tags)
    - Upload status checking
    """

    def __init__(self):
        """Initialize YouTube uploader with credentials."""
        if not GOOGLE_API_AVAILABLE:
            logger.error(
                "Google API libraries not installed. Run:\n"
                "pip install google-api-python-client google-auth-httplib2 "
                "google-auth-oauthlib"
            )
            self.youtube = None
            return

        self.creds = YouTubeCredentials()
        self.youtube = None

        if self.creds.is_valid():
            self._init_service()
        else:
            logger.warning("YouTube credentials not configured")
            YouTubeCredentials._print_setup_instructions()

    def _init_service(self):
        """Initialize YouTube API service."""
        try:
            # Refresh if needed
            if self.creds.credentials.expired:
                self.creds.refresh()

            self.youtube = build(
                "youtube", "v3",
                credentials=self.creds.credentials
            )
            logger.info("YouTube API service initialized")
        except Exception as e:
            logger.error(f"Error initializing YouTube service: {e}")
            self.youtube = None

    def is_ready(self) -> bool:
        """Check if uploader is ready to use."""
        return self.youtube is not None

    def authenticate(self) -> bool:
        """
        Run interactive authentication flow.

        Returns:
            True if authentication successful
        """
        if not GOOGLE_API_AVAILABLE:
            return False

        if self.creds.run_auth_flow():
            self._init_service()
            return self.is_ready()
        return False

    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        privacy: str = "private",
        category_id: str = "22",  # People & Blogs default
        notify_subscribers: bool = True,
        made_for_kids: bool = False,
        thumbnail_path: Optional[str] = None
    ) -> UploadResult:
        """
        Upload a video to YouTube.

        Args:
            video_path: Path to the video file
            title: Video title (max 100 characters)
            description: Video description (max 5000 characters)
            tags: List of tags (max 500 characters total)
            privacy: Privacy status ("public", "private", "unlisted")
            category_id: YouTube category ID (default: "22" People & Blogs)
            notify_subscribers: Whether to notify subscribers (for public videos)
            made_for_kids: COPPA compliance flag
            thumbnail_path: Path to custom thumbnail image

        Returns:
            UploadResult with video ID and status
        """
        if not self.is_ready():
            return UploadResult(
                success=False,
                error="YouTube uploader not initialized. Check credentials."
            )

        # Validate file exists
        video_file = Path(video_path)
        if not video_file.exists():
            return UploadResult(
                success=False,
                error=f"Video file not found: {video_path}"
            )

        # Validate file format
        if video_file.suffix.lower() not in SUPPORTED_VIDEO_FORMATS:
            return UploadResult(
                success=False,
                error=f"Unsupported video format: {video_file.suffix}"
            )

        # Validate title length
        if len(title) > 100:
            return UploadResult(
                success=False,
                error=f"Title too long ({len(title)} chars, max 100)"
            )

        # Validate description length
        if len(description) > 5000:
            return UploadResult(
                success=False,
                error=f"Description too long ({len(description)} chars, max 5000)"
            )

        # Resolve category ID if string name provided
        if category_id.lower() in CATEGORY_IDS:
            category_id = CATEGORY_IDS[category_id.lower()]

        # Build video metadata
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags or [],
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": made_for_kids,
            }
        }

        # Only add notifySubscribers for public videos
        if privacy == "public":
            body["status"]["notifySubscribers"] = notify_subscribers

        try:
            # Create media upload with resumable protocol
            media = MediaFileUpload(
                str(video_file),
                mimetype="video/*",
                resumable=True,
                chunksize=1024 * 1024  # 1MB chunks
            )

            # Insert video
            request = self.youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )

            # Execute with resumable upload
            response = self._resumable_upload(request)

            if response:
                video_id = response["id"]
                video_url = f"https://www.youtube.com/watch?v={video_id}"

                logger.info(f"Video uploaded successfully: {video_id}")

                # Upload thumbnail if provided
                if thumbnail_path:
                    self._upload_thumbnail(video_id, thumbnail_path)

                return UploadResult(
                    success=True,
                    video_id=video_id,
                    title=title,
                    url=video_url,
                    privacy=privacy,
                    upload_time=datetime.now().isoformat(),
                    is_short=False
                )

            return UploadResult(
                success=False,
                error="Upload failed: No response from API"
            )

        except HttpError as e:
            error_content = json.loads(e.content.decode('utf-8'))
            error_reason = error_content.get('error', {}).get('errors', [{}])[0].get('reason', 'unknown')
            logger.error(f"HTTP error during upload: {error_reason}")
            return UploadResult(
                success=False,
                error=f"API error: {error_reason}"
            )
        except Exception as e:
            logger.error(f"Error during upload: {e}")
            return UploadResult(
                success=False,
                error=str(e)
            )

    def upload_short(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        privacy: str = "private",
        notify_subscribers: bool = True
    ) -> UploadResult:
        """
        Upload a YouTube Short.

        YouTube Shorts must be:
        - Vertical video (9:16 aspect ratio recommended)
        - 60 seconds or less
        - Title should include #Shorts tag

        Args:
            video_path: Path to the video file
            title: Video title (max 100 characters, #Shorts added automatically)
            description: Video description
            tags: List of tags (Shorts tag added automatically)
            privacy: Privacy status
            notify_subscribers: Whether to notify subscribers

        Returns:
            UploadResult with video ID and status
        """
        # Add #Shorts to title if not present
        if "#shorts" not in title.lower():
            # Check length before adding
            shorts_tag = " #Shorts"
            if len(title) + len(shorts_tag) <= 100:
                title = title + shorts_tag

        # Add Shorts tag to tags list
        short_tags = list(tags or [])
        if "Shorts" not in short_tags:
            short_tags.append("Shorts")

        # Upload as regular video with Shorts metadata
        result = self.upload_video(
            video_path=video_path,
            title=title,
            description=description,
            tags=short_tags,
            privacy=privacy,
            category_id="22",  # People & Blogs
            notify_subscribers=notify_subscribers
        )

        if result.success:
            result.is_short = True
            # Shorts URL format
            result.url = f"https://www.youtube.com/shorts/{result.video_id}"

        return result

    def get_upload_status(self, video_id: str) -> Optional[VideoStatus]:
        """
        Get the upload and processing status of a video.

        Args:
            video_id: YouTube video ID

        Returns:
            VideoStatus object or None if not found
        """
        if not self.is_ready():
            logger.error("YouTube uploader not initialized")
            return None

        try:
            response = self.youtube.videos().list(
                part="snippet,status,statistics,processingDetails",
                id=video_id
            ).execute()

            if not response.get("items"):
                logger.warning(f"Video not found: {video_id}")
                return None

            video = response["items"][0]
            snippet = video.get("snippet", {})
            status = video.get("status", {})
            stats = video.get("statistics", {})
            processing = video.get("processingDetails", {})

            return VideoStatus(
                video_id=video_id,
                title=snippet.get("title"),
                description=snippet.get("description"),
                privacy_status=status.get("privacyStatus"),
                upload_status=status.get("uploadStatus"),
                failure_reason=status.get("failureReason"),
                rejection_reason=status.get("rejectionReason"),
                processing_status=processing.get("processingStatus"),
                view_count=int(stats.get("viewCount", 0)),
                like_count=int(stats.get("likeCount", 0)),
                comment_count=int(stats.get("commentCount", 0)),
                published_at=snippet.get("publishedAt")
            )

        except HttpError as e:
            logger.error(f"Error getting video status: {e}")
            return None

    def update_metadata(
        self,
        video_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category_id: Optional[str] = None,
        privacy: Optional[str] = None
    ) -> UpdateResult:
        """
        Update video metadata (title, description, tags).

        Args:
            video_id: YouTube video ID
            title: New title (optional)
            description: New description (optional)
            tags: New tags list (optional)
            category_id: New category ID (optional)
            privacy: New privacy status (optional)

        Returns:
            UpdateResult with success status
        """
        if not self.is_ready():
            return UpdateResult(
                success=False,
                error="YouTube uploader not initialized"
            )

        try:
            # Get current video data
            response = self.youtube.videos().list(
                part="snippet,status",
                id=video_id
            ).execute()

            if not response.get("items"):
                return UpdateResult(
                    success=False,
                    video_id=video_id,
                    error="Video not found"
                )

            video = response["items"][0]
            snippet = video["snippet"]
            status = video["status"]

            # Update fields if provided
            if title is not None:
                if len(title) > 100:
                    return UpdateResult(
                        success=False,
                        error=f"Title too long ({len(title)} chars, max 100)"
                    )
                snippet["title"] = title

            if description is not None:
                if len(description) > 5000:
                    return UpdateResult(
                        success=False,
                        error=f"Description too long ({len(description)} chars, max 5000)"
                    )
                snippet["description"] = description

            if tags is not None:
                snippet["tags"] = tags

            if category_id is not None:
                if category_id.lower() in CATEGORY_IDS:
                    category_id = CATEGORY_IDS[category_id.lower()]
                snippet["categoryId"] = category_id

            # Build update request
            update_body = {
                "id": video_id,
                "snippet": snippet
            }

            parts = ["snippet"]

            if privacy is not None:
                status["privacyStatus"] = privacy
                update_body["status"] = status
                parts.append("status")

            # Execute update
            result = self.youtube.videos().update(
                part=",".join(parts),
                body=update_body
            ).execute()

            logger.info(f"Video metadata updated: {video_id}")

            return UpdateResult(
                success=True,
                video_id=video_id,
                title=result["snippet"]["title"]
            )

        except HttpError as e:
            error_content = json.loads(e.content.decode('utf-8'))
            error_reason = error_content.get('error', {}).get('errors', [{}])[0].get('reason', 'unknown')
            logger.error(f"Error updating video: {error_reason}")
            return UpdateResult(
                success=False,
                video_id=video_id,
                error=f"API error: {error_reason}"
            )
        except Exception as e:
            logger.error(f"Error updating video: {e}")
            return UpdateResult(
                success=False,
                video_id=video_id,
                error=str(e)
            )

    def _resumable_upload(self, request) -> Optional[Dict[str, Any]]:
        """
        Execute resumable upload with retry logic.

        Args:
            request: YouTube API insert request

        Returns:
            API response or None on failure
        """
        response = None
        error = None
        retry = 0

        while response is None:
            try:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.info(f"Upload progress: {progress}%")
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    error = f"HTTP error {e.resp.status}, retrying..."
                    logger.warning(error)
                else:
                    raise
            except RETRY_EXCEPTIONS as e:
                error = f"Retriable error: {e}, retrying..."
                logger.warning(error)

            if error is not None:
                retry += 1
                if retry > MAX_RETRIES:
                    logger.error("Max retries exceeded")
                    return None

                # Exponential backoff
                sleep_time = 2 ** retry
                logger.info(f"Sleeping {sleep_time} seconds...")
                time.sleep(sleep_time)
                error = None

        return response

    def _upload_thumbnail(self, video_id: str, thumbnail_path: str) -> bool:
        """
        Upload custom thumbnail for a video.

        Args:
            video_id: YouTube video ID
            thumbnail_path: Path to thumbnail image

        Returns:
            True if successful
        """
        try:
            media = MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=media
            ).execute()
            logger.info(f"Thumbnail uploaded for video: {video_id}")
            return True
        except Exception as e:
            logger.warning(f"Error uploading thumbnail: {e}")
            return False


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI for YouTube uploader."""
    import argparse

    parser = argparse.ArgumentParser(
        description='YouTube Video Uploader',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Upload a video:
    python -m src.youtube_uploader upload --video video.mp4 --title "My Video"

  Upload a Short:
    python -m src.youtube_uploader upload-short --video short.mp4 --title "Quick tip"

  Check status:
    python -m src.youtube_uploader status --video-id VIDEO_ID

  Update metadata:
    python -m src.youtube_uploader update --video-id VIDEO_ID --title "New Title"

  Authenticate:
    python -m src.youtube_uploader auth
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Upload command
    upload_parser = subparsers.add_parser('upload', help='Upload a video')
    upload_parser.add_argument('--video', '-v', required=True, help='Path to video file')
    upload_parser.add_argument('--title', '-t', required=True, help='Video title')
    upload_parser.add_argument('--description', '-d', default='', help='Video description')
    upload_parser.add_argument('--tags', nargs='+', help='Tags (space-separated)')
    upload_parser.add_argument('--privacy', choices=['public', 'private', 'unlisted'],
                              default='private', help='Privacy status')
    upload_parser.add_argument('--category', default='22', help='Category ID or name')
    upload_parser.add_argument('--thumbnail', help='Path to thumbnail image')
    upload_parser.add_argument('--no-notify', action='store_true',
                              help='Do not notify subscribers')

    # Upload Short command
    short_parser = subparsers.add_parser('upload-short', help='Upload a YouTube Short')
    short_parser.add_argument('--video', '-v', required=True, help='Path to video file')
    short_parser.add_argument('--title', '-t', required=True, help='Video title')
    short_parser.add_argument('--description', '-d', default='', help='Video description')
    short_parser.add_argument('--tags', nargs='+', help='Tags (space-separated)')
    short_parser.add_argument('--privacy', choices=['public', 'private', 'unlisted'],
                              default='private', help='Privacy status')

    # Status command
    status_parser = subparsers.add_parser('status', help='Get video upload status')
    status_parser.add_argument('--video-id', '-i', required=True, help='YouTube video ID')

    # Update command
    update_parser = subparsers.add_parser('update', help='Update video metadata')
    update_parser.add_argument('--video-id', '-i', required=True, help='YouTube video ID')
    update_parser.add_argument('--title', '-t', help='New title')
    update_parser.add_argument('--description', '-d', help='New description')
    update_parser.add_argument('--tags', nargs='+', help='New tags (space-separated)')
    update_parser.add_argument('--category', help='New category ID or name')
    update_parser.add_argument('--privacy', choices=['public', 'private', 'unlisted'],
                              help='New privacy status')

    # Auth command
    subparsers.add_parser('auth', help='Run authentication flow')

    # Categories command
    subparsers.add_parser('categories', help='List available category IDs')

    args = parser.parse_args()

    if args.command == 'categories':
        print("\nYouTube Category IDs:")
        print("-" * 40)
        for name, cat_id in sorted(CATEGORY_IDS.items()):
            print(f"  {name:15} = {cat_id}")
        print("\nUse --category with either the name or ID")
        return 0

    if args.command == 'auth':
        uploader = YouTubeUploader()
        if uploader.authenticate():
            print("Authentication successful!")
            return 0
        else:
            print("Authentication failed. See instructions above.")
            return 1

    uploader = YouTubeUploader()

    if not uploader.is_ready():
        print("\nYouTube uploader not ready. Run authentication first:")
        print("  python -m src.youtube_uploader auth")
        return 1

    if args.command == 'upload':
        result = uploader.upload_video(
            video_path=args.video,
            title=args.title,
            description=args.description,
            tags=args.tags,
            privacy=args.privacy,
            category_id=args.category,
            thumbnail_path=args.thumbnail,
            notify_subscribers=not args.no_notify
        )

        if result.success:
            print(f"\nVideo uploaded successfully!")
            print(f"  Video ID: {result.video_id}")
            print(f"  Title: {result.title}")
            print(f"  Privacy: {result.privacy}")
            print(f"  URL: {result.url}")
        else:
            print(f"\nUpload failed: {result.error}")
            return 1

    elif args.command == 'upload-short':
        result = uploader.upload_short(
            video_path=args.video,
            title=args.title,
            description=args.description,
            tags=args.tags,
            privacy=args.privacy
        )

        if result.success:
            print(f"\nShort uploaded successfully!")
            print(f"  Video ID: {result.video_id}")
            print(f"  Title: {result.title}")
            print(f"  Privacy: {result.privacy}")
            print(f"  URL: {result.url}")
        else:
            print(f"\nUpload failed: {result.error}")
            return 1

    elif args.command == 'status':
        status = uploader.get_upload_status(args.video_id)

        if status:
            print(f"\nVideo Status: {args.video_id}")
            print("-" * 40)
            print(f"  Title: {status.title}")
            print(f"  Privacy: {status.privacy_status}")
            print(f"  Upload Status: {status.upload_status}")
            print(f"  Processing: {status.processing_status}")
            if status.failure_reason:
                print(f"  Failure Reason: {status.failure_reason}")
            if status.rejection_reason:
                print(f"  Rejection Reason: {status.rejection_reason}")
            print(f"  Views: {status.view_count}")
            print(f"  Likes: {status.like_count}")
            print(f"  Comments: {status.comment_count}")
            print(f"  Published: {status.published_at}")
        else:
            print(f"\nVideo not found: {args.video_id}")
            return 1

    elif args.command == 'update':
        result = uploader.update_metadata(
            video_id=args.video_id,
            title=args.title,
            description=args.description,
            tags=args.tags,
            category_id=args.category,
            privacy=args.privacy
        )

        if result.success:
            print(f"\nVideo updated successfully!")
            print(f"  Video ID: {result.video_id}")
            print(f"  Title: {result.title}")
        else:
            print(f"\nUpdate failed: {result.error}")
            return 1

    else:
        parser.print_help()

    return 0


if __name__ == '__main__':
    exit(main())
