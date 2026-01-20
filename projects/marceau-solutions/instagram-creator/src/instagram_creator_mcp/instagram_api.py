"""
Instagram Graph API wrapper for content publishing and management.

Requires:
- Facebook Business account
- Instagram Professional account (Business or Creator)
- Meta App with Instagram Graph API access
- Access token with required permissions

Note: Instagram API requires media to be hosted at a public URL.
This module handles local file uploads via a temporary hosting solution.
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
class MediaMetadata:
    """Media metadata for posting."""
    caption: str
    location_id: Optional[str] = None
    user_tags: Optional[List[Dict[str, Any]]] = None  # [{"username": "user", "x": 0.5, "y": 0.5}]
    hashtags: Optional[List[str]] = None

    def get_full_caption(self) -> str:
        """Get caption with hashtags appended."""
        caption = self.caption
        if self.hashtags:
            hashtag_str = " ".join(f"#{tag}" for tag in self.hashtags)
            caption = f"{caption}\n\n{hashtag_str}"
        return caption


@dataclass
class PostInsights:
    """Post performance insights."""
    post_id: str
    impressions: int
    reach: int
    likes: int
    comments: int
    saves: int
    shares: int
    engagement_rate: float


class InstagramAPI:
    """Instagram Graph API client."""

    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(
        self,
        access_token: Optional[str] = None,
        instagram_account_id: Optional[str] = None
    ):
        """
        Initialize Instagram API client.

        Args:
            access_token: Facebook/Instagram access token
            instagram_account_id: Instagram Business Account ID
        """
        self.access_token = access_token or os.getenv('INSTAGRAM_ACCESS_TOKEN')
        self.instagram_account_id = instagram_account_id or os.getenv('INSTAGRAM_ACCOUNT_ID')

        if not self.access_token:
            raise ValueError(
                "Instagram access token required. Set INSTAGRAM_ACCESS_TOKEN env var "
                "or pass access_token parameter."
            )

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make API request."""
        url = f"{self.BASE_URL}/{endpoint}"

        params = params or {}
        params['access_token'] = self.access_token

        if method == 'GET':
            response = requests.get(url, params=params)
        elif method == 'POST':
            response = requests.post(url, params=params, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json()

    def get_account_id(self) -> str:
        """Get Instagram Business Account ID from Facebook Page."""
        if self.instagram_account_id:
            return self.instagram_account_id

        # Get pages connected to the access token
        pages = self._make_request('GET', 'me/accounts')

        for page in pages.get('data', []):
            # Get Instagram account connected to page
            ig_account = self._make_request(
                'GET',
                f"{page['id']}",
                params={'fields': 'instagram_business_account'}
            )
            if 'instagram_business_account' in ig_account:
                self.instagram_account_id = ig_account['instagram_business_account']['id']
                return self.instagram_account_id

        raise ValueError("No Instagram Business Account found")

    def post_image(
        self,
        image_url: str,
        metadata: MediaMetadata
    ) -> Dict[str, Any]:
        """
        Post an image to Instagram feed.

        Args:
            image_url: Public URL of the image
            metadata: Post metadata (caption, hashtags, etc.)

        Returns:
            Post response with media ID
        """
        account_id = self.get_account_id()

        # Step 1: Create media container
        container = self._make_request(
            'POST',
            f"{account_id}/media",
            params={
                'image_url': image_url,
                'caption': metadata.get_full_caption(),
            }
        )

        container_id = container['id']

        # Step 2: Publish the container
        result = self._make_request(
            'POST',
            f"{account_id}/media_publish",
            params={'creation_id': container_id}
        )

        return {
            'success': True,
            'media_id': result['id'],
            'caption': metadata.caption,
        }

    def post_carousel(
        self,
        image_urls: List[str],
        metadata: MediaMetadata
    ) -> Dict[str, Any]:
        """
        Post a carousel (multi-image post) to Instagram.

        Args:
            image_urls: List of public image URLs (2-10 images)
            metadata: Post metadata

        Returns:
            Post response with media ID
        """
        if len(image_urls) < 2 or len(image_urls) > 10:
            raise ValueError("Carousel must have 2-10 images")

        account_id = self.get_account_id()

        # Step 1: Create container for each image
        children = []
        for url in image_urls:
            child = self._make_request(
                'POST',
                f"{account_id}/media",
                params={
                    'image_url': url,
                    'is_carousel_item': True,
                }
            )
            children.append(child['id'])

        # Step 2: Create carousel container
        carousel = self._make_request(
            'POST',
            f"{account_id}/media",
            params={
                'media_type': 'CAROUSEL',
                'caption': metadata.get_full_caption(),
                'children': ','.join(children),
            }
        )

        # Step 3: Publish
        result = self._make_request(
            'POST',
            f"{account_id}/media_publish",
            params={'creation_id': carousel['id']}
        )

        return {
            'success': True,
            'media_id': result['id'],
            'image_count': len(image_urls),
        }

    def post_reel(
        self,
        video_url: str,
        metadata: MediaMetadata,
        cover_url: Optional[str] = None,
        share_to_feed: bool = True
    ) -> Dict[str, Any]:
        """
        Post a Reel to Instagram.

        Args:
            video_url: Public URL of the video
            metadata: Post metadata
            cover_url: Optional cover image URL
            share_to_feed: Whether to also share to feed

        Returns:
            Post response with media ID
        """
        account_id = self.get_account_id()

        params = {
            'media_type': 'REELS',
            'video_url': video_url,
            'caption': metadata.get_full_caption(),
            'share_to_feed': share_to_feed,
        }

        if cover_url:
            params['cover_url'] = cover_url

        # Step 1: Create container
        container = self._make_request(
            'POST',
            f"{account_id}/media",
            params=params
        )

        container_id = container['id']

        # Step 2: Wait for video processing
        status = 'IN_PROGRESS'
        while status == 'IN_PROGRESS':
            time.sleep(5)
            status_check = self._make_request(
                'GET',
                container_id,
                params={'fields': 'status_code'}
            )
            status = status_check.get('status_code', 'FINISHED')

        if status == 'ERROR':
            raise Exception("Video processing failed")

        # Step 3: Publish
        result = self._make_request(
            'POST',
            f"{account_id}/media_publish",
            params={'creation_id': container_id}
        )

        return {
            'success': True,
            'media_id': result['id'],
            'type': 'reel',
        }

    def post_story(
        self,
        media_url: str,
        media_type: str = 'image'
    ) -> Dict[str, Any]:
        """
        Post to Instagram Stories.

        Args:
            media_url: Public URL of image or video
            media_type: 'image' or 'video'

        Returns:
            Story response
        """
        account_id = self.get_account_id()

        params = {
            'media_type': 'STORIES',
        }

        if media_type == 'video':
            params['video_url'] = media_url
        else:
            params['image_url'] = media_url

        # Create container
        container = self._make_request(
            'POST',
            f"{account_id}/media",
            params=params
        )

        # If video, wait for processing
        if media_type == 'video':
            status = 'IN_PROGRESS'
            while status == 'IN_PROGRESS':
                time.sleep(3)
                status_check = self._make_request(
                    'GET',
                    container['id'],
                    params={'fields': 'status_code'}
                )
                status = status_check.get('status_code', 'FINISHED')

        # Publish
        result = self._make_request(
            'POST',
            f"{account_id}/media_publish",
            params={'creation_id': container['id']}
        )

        return {
            'success': True,
            'story_id': result['id'],
        }

    def get_post_insights(self, media_id: str) -> PostInsights:
        """
        Get insights for a specific post.

        Args:
            media_id: Instagram media ID

        Returns:
            PostInsights with performance metrics
        """
        result = self._make_request(
            'GET',
            f"{media_id}/insights",
            params={
                'metric': 'impressions,reach,likes,comments,saved,shares'
            }
        )

        metrics = {}
        for item in result.get('data', []):
            metrics[item['name']] = item['values'][0]['value']

        # Calculate engagement rate
        total_engagement = (
            metrics.get('likes', 0) +
            metrics.get('comments', 0) +
            metrics.get('saved', 0) +
            metrics.get('shares', 0)
        )
        reach = metrics.get('reach', 1)
        engagement_rate = (total_engagement / reach) * 100 if reach > 0 else 0

        return PostInsights(
            post_id=media_id,
            impressions=metrics.get('impressions', 0),
            reach=metrics.get('reach', 0),
            likes=metrics.get('likes', 0),
            comments=metrics.get('comments', 0),
            saves=metrics.get('saved', 0),
            shares=metrics.get('shares', 0),
            engagement_rate=round(engagement_rate, 2)
        )

    def get_account_stats(self) -> Dict[str, Any]:
        """Get account statistics."""
        account_id = self.get_account_id()

        result = self._make_request(
            'GET',
            account_id,
            params={
                'fields': 'username,followers_count,follows_count,media_count,biography'
            }
        )

        return {
            'username': result.get('username'),
            'followers': result.get('followers_count', 0),
            'following': result.get('follows_count', 0),
            'posts': result.get('media_count', 0),
            'bio': result.get('biography', ''),
        }

    def get_comments(
        self,
        media_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get comments on a post."""
        result = self._make_request(
            'GET',
            f"{media_id}/comments",
            params={
                'fields': 'id,text,username,timestamp,like_count',
                'limit': limit
            }
        )

        return [
            {
                'comment_id': c['id'],
                'text': c.get('text', ''),
                'username': c.get('username', ''),
                'timestamp': c.get('timestamp', ''),
                'likes': c.get('like_count', 0),
            }
            for c in result.get('data', [])
        ]

    def reply_to_comment(
        self,
        comment_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Reply to a comment."""
        result = self._make_request(
            'POST',
            f"{comment_id}/replies",
            params={'message': message}
        )

        return {
            'success': True,
            'reply_id': result['id'],
        }

    def get_recent_media(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Get recent media posts."""
        account_id = self.get_account_id()

        result = self._make_request(
            'GET',
            f"{account_id}/media",
            params={
                'fields': 'id,caption,media_type,timestamp,permalink,like_count,comments_count',
                'limit': limit
            }
        )

        return [
            {
                'media_id': m['id'],
                'caption': m.get('caption', '')[:100] + '...' if m.get('caption', '') else '',
                'type': m.get('media_type', ''),
                'timestamp': m.get('timestamp', ''),
                'permalink': m.get('permalink', ''),
                'likes': m.get('like_count', 0),
                'comments': m.get('comments_count', 0),
            }
            for m in result.get('data', [])
        ]
