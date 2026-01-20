"""
TikTok Content Posting API wrapper.

Requires:
- TikTok Developer Account
- App with Content Posting API access
- OAuth 2.0 authorization

Note: TikTok's Content Posting API uses a two-step process:
1. Initialize upload and get upload URL
2. Upload video to the URL
3. Publish the video
"""

import os
import json
import requests
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class VideoMetadata:
    """Video metadata for posting."""
    title: str  # Max 150 chars
    privacy_level: str = "SELF_ONLY"  # SELF_ONLY, MUTUAL_FOLLOW_FRIENDS, FOLLOWER_OF_CREATOR, PUBLIC_TO_EVERYONE
    disable_duet: bool = False
    disable_stitch: bool = False
    disable_comment: bool = False
    video_cover_timestamp_ms: int = 0  # Cover frame timestamp


@dataclass
class VideoStats:
    """Video statistics."""
    video_id: str
    title: str
    views: int
    likes: int
    comments: int
    shares: int
    create_time: str


class TikTokAPI:
    """TikTok Content Posting API client."""

    BASE_URL = "https://open.tiktokapis.com/v2"
    AUTH_URL = "https://www.tiktok.com/v2/auth/authorize"
    TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"

    def __init__(
        self,
        client_key: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None
    ):
        """
        Initialize TikTok API client.

        Args:
            client_key: TikTok app client key
            client_secret: TikTok app client secret
            access_token: User access token
            refresh_token: Refresh token for token renewal
        """
        self.client_key = client_key or os.getenv('TIKTOK_CLIENT_KEY')
        self.client_secret = client_secret or os.getenv('TIKTOK_CLIENT_SECRET')
        self.access_token = access_token or os.getenv('TIKTOK_ACCESS_TOKEN')
        self.refresh_token = refresh_token or os.getenv('TIKTOK_REFRESH_TOKEN')

        if not self.access_token:
            raise ValueError(
                "TikTok access token required. Set TIKTOK_ACCESS_TOKEN env var."
            )

    def _headers(self) -> Dict[str, str]:
        """Get request headers with authorization."""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make API request."""
        url = f"{self.BASE_URL}/{endpoint}"

        if method == 'GET':
            response = requests.get(url, headers=self._headers(), params=params)
        elif method == 'POST':
            response = requests.post(url, headers=self._headers(), json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")

        result = response.json()

        if 'error' in result:
            raise Exception(f"TikTok API error: {result['error']}")

        return result

    def refresh_access_token(self) -> Dict[str, Any]:
        """Refresh the access token using refresh token."""
        if not self.refresh_token:
            raise ValueError("No refresh token available")

        response = requests.post(
            self.TOKEN_URL,
            data={
                'client_key': self.client_key,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
            }
        )

        result = response.json()

        if 'access_token' in result:
            self.access_token = result['access_token']
            if 'refresh_token' in result:
                self.refresh_token = result['refresh_token']

        return result

    def get_user_info(self) -> Dict[str, Any]:
        """Get authenticated user information."""
        result = self._make_request(
            'GET',
            'user/info/',
            params={'fields': 'open_id,union_id,avatar_url,display_name,bio_description,profile_deep_link,is_verified,follower_count,following_count,likes_count,video_count'}
        )

        user = result.get('data', {}).get('user', {})
        return {
            'user_id': user.get('open_id'),
            'display_name': user.get('display_name'),
            'bio': user.get('bio_description'),
            'followers': user.get('follower_count', 0),
            'following': user.get('following_count', 0),
            'likes': user.get('likes_count', 0),
            'videos': user.get('video_count', 0),
            'verified': user.get('is_verified', False),
            'profile_url': user.get('profile_deep_link'),
        }

    def post_video(
        self,
        video_path: str,
        metadata: VideoMetadata
    ) -> Dict[str, Any]:
        """
        Post a video to TikTok.

        Args:
            video_path: Path to video file
            metadata: Video metadata

        Returns:
            Post response with publish ID
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")

        video_size = os.path.getsize(video_path)

        # Step 1: Initialize upload
        init_response = self._make_request(
            'POST',
            'post/publish/video/init/',
            data={
                'post_info': {
                    'title': metadata.title[:150],
                    'privacy_level': metadata.privacy_level,
                    'disable_duet': metadata.disable_duet,
                    'disable_stitch': metadata.disable_stitch,
                    'disable_comment': metadata.disable_comment,
                    'video_cover_timestamp_ms': metadata.video_cover_timestamp_ms,
                },
                'source_info': {
                    'source': 'FILE_UPLOAD',
                    'video_size': video_size,
                    'chunk_size': video_size,  # Single chunk upload
                    'total_chunk_count': 1,
                }
            }
        )

        publish_id = init_response['data']['publish_id']
        upload_url = init_response['data']['upload_url']

        # Step 2: Upload video
        with open(video_path, 'rb') as video_file:
            video_data = video_file.read()

        upload_headers = {
            'Content-Type': 'video/mp4',
            'Content-Range': f'bytes 0-{video_size-1}/{video_size}',
        }

        upload_response = requests.put(
            upload_url,
            headers=upload_headers,
            data=video_data
        )

        if upload_response.status_code not in [200, 201]:
            raise Exception(f"Video upload failed: {upload_response.text}")

        # Step 3: Wait for processing and get status
        status = self._wait_for_publish(publish_id)

        return {
            'success': True,
            'publish_id': publish_id,
            'status': status,
            'title': metadata.title,
        }

    def post_video_from_url(
        self,
        video_url: str,
        metadata: VideoMetadata
    ) -> Dict[str, Any]:
        """
        Post a video from a public URL.

        Args:
            video_url: Public URL of the video
            metadata: Video metadata

        Returns:
            Post response with publish ID
        """
        # Initialize upload with URL source
        init_response = self._make_request(
            'POST',
            'post/publish/video/init/',
            data={
                'post_info': {
                    'title': metadata.title[:150],
                    'privacy_level': metadata.privacy_level,
                    'disable_duet': metadata.disable_duet,
                    'disable_stitch': metadata.disable_stitch,
                    'disable_comment': metadata.disable_comment,
                },
                'source_info': {
                    'source': 'PULL_FROM_URL',
                    'video_url': video_url,
                }
            }
        )

        publish_id = init_response['data']['publish_id']

        # Wait for processing
        status = self._wait_for_publish(publish_id)

        return {
            'success': True,
            'publish_id': publish_id,
            'status': status,
            'title': metadata.title,
        }

    def _wait_for_publish(self, publish_id: str, max_wait: int = 120) -> str:
        """Wait for video to finish publishing."""
        start_time = time.time()

        while time.time() - start_time < max_wait:
            status_response = self._make_request(
                'POST',
                'post/publish/status/fetch/',
                data={'publish_id': publish_id}
            )

            status = status_response['data']['status']

            if status == 'PUBLISH_COMPLETE':
                return status
            elif status in ['FAILED', 'PUBLISH_FAILED']:
                error = status_response['data'].get('fail_reason', 'Unknown error')
                raise Exception(f"Publish failed: {error}")

            time.sleep(5)

        return 'PROCESSING'

    def get_video_list(self, max_count: int = 20) -> List[Dict[str, Any]]:
        """Get list of user's videos."""
        result = self._make_request(
            'POST',
            'video/list/',
            data={
                'max_count': max_count,
                'fields': 'id,title,video_description,duration,cover_image_url,share_url,view_count,like_count,comment_count,share_count,create_time'
            }
        )

        videos = []
        for video in result.get('data', {}).get('videos', []):
            videos.append({
                'video_id': video.get('id'),
                'title': video.get('title', ''),
                'description': video.get('video_description', ''),
                'duration': video.get('duration', 0),
                'cover_url': video.get('cover_image_url', ''),
                'share_url': video.get('share_url', ''),
                'views': video.get('view_count', 0),
                'likes': video.get('like_count', 0),
                'comments': video.get('comment_count', 0),
                'shares': video.get('share_count', 0),
                'created_at': video.get('create_time', ''),
            })

        return videos

    def get_video_stats(self, video_id: str) -> VideoStats:
        """Get statistics for a specific video."""
        result = self._make_request(
            'POST',
            'video/query/',
            data={
                'filters': {'video_ids': [video_id]},
                'fields': 'id,title,view_count,like_count,comment_count,share_count,create_time'
            }
        )

        video = result.get('data', {}).get('videos', [{}])[0]

        return VideoStats(
            video_id=video_id,
            title=video.get('title', ''),
            views=video.get('view_count', 0),
            likes=video.get('like_count', 0),
            comments=video.get('comment_count', 0),
            shares=video.get('share_count', 0),
            create_time=video.get('create_time', '')
        )

    def get_comments(
        self,
        video_id: str,
        max_count: int = 50
    ) -> List[Dict[str, Any]]:
        """Get comments on a video."""
        result = self._make_request(
            'POST',
            'video/comment/list/',
            data={
                'video_id': video_id,
                'max_count': max_count,
                'fields': 'id,text,create_time,like_count,user'
            }
        )

        comments = []
        for comment in result.get('data', {}).get('comments', []):
            user = comment.get('user', {})
            comments.append({
                'comment_id': comment.get('id'),
                'text': comment.get('text', ''),
                'created_at': comment.get('create_time', ''),
                'likes': comment.get('like_count', 0),
                'username': user.get('display_name', ''),
            })

        return comments

    def reply_to_comment(
        self,
        video_id: str,
        comment_id: str,
        text: str
    ) -> Dict[str, Any]:
        """Reply to a comment."""
        result = self._make_request(
            'POST',
            'video/comment/reply/',
            data={
                'video_id': video_id,
                'comment_id': comment_id,
                'text': text,
            }
        )

        return {
            'success': True,
            'reply_id': result.get('data', {}).get('comment_id'),
        }
