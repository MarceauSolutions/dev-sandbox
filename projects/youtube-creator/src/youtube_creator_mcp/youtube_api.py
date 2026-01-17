"""
YouTube Data API v3 wrapper for video uploads and management.

Requires:
- YouTube Data API v3 enabled
- OAuth 2.0 credentials
- youtube.upload scope for uploads
- youtube.readonly scope for analytics
"""

import os
import json
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict

# Google API imports
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False


SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/yt-analytics.readonly'
]


@dataclass
class VideoMetadata:
    """Video metadata for upload."""
    title: str
    description: str
    tags: List[str]
    category_id: str = "22"  # People & Blogs
    privacy_status: str = "private"  # private, unlisted, public
    made_for_kids: bool = False

    # Optional
    playlist_id: Optional[str] = None
    scheduled_publish_time: Optional[str] = None  # ISO 8601 format
    thumbnail_path: Optional[str] = None


@dataclass
class VideoStats:
    """Video statistics."""
    video_id: str
    title: str
    views: int
    likes: int
    comments: int
    shares: int
    watch_time_minutes: float
    average_view_duration: float
    subscriber_gain: int


class YouTubeAPI:
    """YouTube Data API v3 client."""

    # Category IDs for YouTube
    CATEGORIES = {
        "film_animation": "1",
        "autos_vehicles": "2",
        "music": "10",
        "pets_animals": "15",
        "sports": "17",
        "travel_events": "19",
        "gaming": "20",
        "people_blogs": "22",
        "comedy": "23",
        "entertainment": "24",
        "news_politics": "25",
        "howto_style": "26",
        "education": "27",
        "science_tech": "28",
        "nonprofits": "29",
    }

    def __init__(self, credentials_path: Optional[str] = None, token_path: Optional[str] = None):
        """
        Initialize YouTube API client.

        Args:
            credentials_path: Path to OAuth client secrets JSON
            token_path: Path to store/load token pickle
        """
        if not GOOGLE_API_AVAILABLE:
            raise ImportError(
                "Google API libraries not installed. Run: "
                "pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )

        self.credentials_path = credentials_path or os.getenv(
            'YOUTUBE_CREDENTIALS_PATH',
            os.path.expanduser('~/.google/youtube_credentials.json')
        )
        self.token_path = token_path or os.getenv(
            'YOUTUBE_TOKEN_PATH',
            os.path.expanduser('~/.google/youtube_token.pickle')
        )

        self.credentials = None
        self.youtube = None
        self.youtube_analytics = None

    def authenticate(self) -> bool:
        """
        Authenticate with YouTube API using OAuth 2.0.

        Returns:
            True if authentication successful
        """
        # Load existing token
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                self.credentials = pickle.load(token)

        # Refresh or get new credentials
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"OAuth credentials not found at {self.credentials_path}. "
                        "Download from Google Cloud Console > APIs & Services > Credentials"
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                self.credentials = flow.run_local_server(port=0)

            # Save token for next run
            Path(self.token_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, 'wb') as token:
                pickle.dump(self.credentials, token)

        # Build service clients
        self.youtube = build('youtube', 'v3', credentials=self.credentials)
        self.youtube_analytics = build('youtubeAnalytics', 'v2', credentials=self.credentials)

        return True

    def upload_video(
        self,
        video_path: str,
        metadata: VideoMetadata,
        notify_subscribers: bool = True
    ) -> Dict[str, Any]:
        """
        Upload a video to YouTube.

        Args:
            video_path: Path to video file
            metadata: Video metadata
            notify_subscribers: Whether to notify subscribers

        Returns:
            Upload response with video ID
        """
        if not self.youtube:
            self.authenticate()

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")

        body = {
            'snippet': {
                'title': metadata.title,
                'description': metadata.description,
                'tags': metadata.tags,
                'categoryId': metadata.category_id,
            },
            'status': {
                'privacyStatus': metadata.privacy_status,
                'selfDeclaredMadeForKids': metadata.made_for_kids,
                'notifySubscribers': notify_subscribers,
            }
        }

        # Add scheduled publish time if provided
        if metadata.scheduled_publish_time:
            body['status']['publishAt'] = metadata.scheduled_publish_time
            body['status']['privacyStatus'] = 'private'  # Must be private for scheduling

        # Upload video
        media = MediaFileUpload(
            video_path,
            chunksize=1024*1024,
            resumable=True,
            mimetype='video/*'
        )

        request = self.youtube.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Upload progress: {int(status.progress() * 100)}%")

        video_id = response['id']

        # Set thumbnail if provided
        if metadata.thumbnail_path and os.path.exists(metadata.thumbnail_path):
            self.set_thumbnail(video_id, metadata.thumbnail_path)

        # Add to playlist if specified
        if metadata.playlist_id:
            self.add_to_playlist(video_id, metadata.playlist_id)

        return {
            'success': True,
            'video_id': video_id,
            'url': f'https://youtube.com/watch?v={video_id}',
            'title': metadata.title,
            'privacy': metadata.privacy_status,
        }

    def upload_short(
        self,
        video_path: str,
        metadata: VideoMetadata
    ) -> Dict[str, Any]:
        """
        Upload a YouTube Short (vertical video <60s).

        Args:
            video_path: Path to vertical video file
            metadata: Video metadata

        Returns:
            Upload response with video ID
        """
        # Add #Shorts to title/description for algorithm
        if '#Shorts' not in metadata.title and '#shorts' not in metadata.title.lower():
            metadata.title = f"{metadata.title} #Shorts"

        if '#Shorts' not in metadata.description:
            metadata.description = f"{metadata.description}\n\n#Shorts"

        return self.upload_video(video_path, metadata, notify_subscribers=False)

    def set_thumbnail(self, video_id: str, thumbnail_path: str) -> Dict[str, Any]:
        """Set custom thumbnail for a video."""
        if not self.youtube:
            self.authenticate()

        media = MediaFileUpload(thumbnail_path, mimetype='image/jpeg')
        response = self.youtube.thumbnails().set(
            videoId=video_id,
            media_body=media
        ).execute()

        return {'success': True, 'thumbnail_url': response['items'][0]['default']['url']}

    def update_metadata(
        self,
        video_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        privacy_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update video metadata."""
        if not self.youtube:
            self.authenticate()

        # Get current video data
        video = self.youtube.videos().list(
            part='snippet,status',
            id=video_id
        ).execute()

        if not video['items']:
            raise ValueError(f"Video not found: {video_id}")

        current = video['items'][0]
        snippet = current['snippet']
        status = current['status']

        # Update fields
        if title:
            snippet['title'] = title
        if description:
            snippet['description'] = description
        if tags:
            snippet['tags'] = tags
        if privacy_status:
            status['privacyStatus'] = privacy_status

        response = self.youtube.videos().update(
            part='snippet,status',
            body={
                'id': video_id,
                'snippet': snippet,
                'status': status,
            }
        ).execute()

        return {
            'success': True,
            'video_id': video_id,
            'title': response['snippet']['title'],
        }

    def get_video_analytics(
        self,
        video_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> VideoStats:
        """
        Get analytics for a specific video.

        Args:
            video_id: YouTube video ID
            start_date: Start date (YYYY-MM-DD), defaults to 30 days ago
            end_date: End date (YYYY-MM-DD), defaults to today
        """
        if not self.youtube_analytics:
            self.authenticate()

        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # Get video title
        video = self.youtube.videos().list(
            part='snippet',
            id=video_id
        ).execute()

        title = video['items'][0]['snippet']['title'] if video['items'] else 'Unknown'

        # Get analytics
        response = self.youtube_analytics.reports().query(
            ids='channel==MINE',
            startDate=start_date,
            endDate=end_date,
            metrics='views,likes,comments,shares,estimatedMinutesWatched,averageViewDuration,subscribersGained',
            filters=f'video=={video_id}'
        ).execute()

        row = response.get('rows', [[0]*7])[0]

        return VideoStats(
            video_id=video_id,
            title=title,
            views=int(row[0]),
            likes=int(row[1]),
            comments=int(row[2]),
            shares=int(row[3]),
            watch_time_minutes=float(row[4]),
            average_view_duration=float(row[5]),
            subscriber_gain=int(row[6])
        )

    def get_channel_stats(self) -> Dict[str, Any]:
        """Get channel statistics."""
        if not self.youtube:
            self.authenticate()

        response = self.youtube.channels().list(
            part='snippet,statistics',
            mine=True
        ).execute()

        if not response['items']:
            raise ValueError("No channel found for authenticated user")

        channel = response['items'][0]
        stats = channel['statistics']

        return {
            'channel_id': channel['id'],
            'title': channel['snippet']['title'],
            'subscribers': int(stats.get('subscriberCount', 0)),
            'total_views': int(stats.get('viewCount', 0)),
            'video_count': int(stats.get('videoCount', 0)),
        }

    def add_to_playlist(self, video_id: str, playlist_id: str) -> Dict[str, Any]:
        """Add video to a playlist."""
        if not self.youtube:
            self.authenticate()

        response = self.youtube.playlistItems().insert(
            part='snippet',
            body={
                'snippet': {
                    'playlistId': playlist_id,
                    'resourceId': {
                        'kind': 'youtube#video',
                        'videoId': video_id,
                    }
                }
            }
        ).execute()

        return {'success': True, 'playlist_item_id': response['id']}

    def get_comments(
        self,
        video_id: str,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """Get comments on a video."""
        if not self.youtube:
            self.authenticate()

        response = self.youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            maxResults=min(max_results, 100),
            order='relevance'
        ).execute()

        comments = []
        for item in response.get('items', []):
            comment = item['snippet']['topLevelComment']['snippet']
            comments.append({
                'comment_id': item['id'],
                'author': comment['authorDisplayName'],
                'text': comment['textDisplay'],
                'likes': comment['likeCount'],
                'published_at': comment['publishedAt'],
            })

        return comments

    def reply_to_comment(self, comment_id: str, text: str) -> Dict[str, Any]:
        """Reply to a comment."""
        if not self.youtube:
            self.authenticate()

        response = self.youtube.comments().insert(
            part='snippet',
            body={
                'snippet': {
                    'parentId': comment_id,
                    'textOriginal': text,
                }
            }
        ).execute()

        return {
            'success': True,
            'reply_id': response['id'],
            'text': text,
        }

    def list_playlists(self) -> List[Dict[str, Any]]:
        """List channel playlists."""
        if not self.youtube:
            self.authenticate()

        response = self.youtube.playlists().list(
            part='snippet,contentDetails',
            mine=True,
            maxResults=50
        ).execute()

        playlists = []
        for item in response.get('items', []):
            playlists.append({
                'playlist_id': item['id'],
                'title': item['snippet']['title'],
                'description': item['snippet']['description'],
                'video_count': item['contentDetails']['itemCount'],
            })

        return playlists

    def create_playlist(
        self,
        title: str,
        description: str = "",
        privacy_status: str = "private"
    ) -> Dict[str, Any]:
        """Create a new playlist."""
        if not self.youtube:
            self.authenticate()

        response = self.youtube.playlists().insert(
            part='snippet,status',
            body={
                'snippet': {
                    'title': title,
                    'description': description,
                },
                'status': {
                    'privacyStatus': privacy_status,
                }
            }
        ).execute()

        return {
            'success': True,
            'playlist_id': response['id'],
            'title': title,
        }
