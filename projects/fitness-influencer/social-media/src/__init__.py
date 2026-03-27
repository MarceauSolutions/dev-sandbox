"""
Social Media Automation - Multi-Platform Integration

Provides automated posting, scheduling, and analytics for:
- X (Twitter)
- YouTube (Videos and Shorts)
- TikTok (Videos)
"""

from .x_api import XClient, PostResult, RateLimiter
from .x_scheduler import PostScheduler, ScheduledPost, PostPriority, PostStatus
from .link_manager import LinkManager, TrackedLink
from .engagement_tracker import EngagementTracker, TweetMetrics, CampaignMetrics
from .youtube_uploader import (
    YouTubeUploader,
    UploadResult as YouTubeUploadResult,
    VideoStatus as YouTubeVideoStatus,
    UpdateResult,
    YouTubeCategory,
    PrivacyStatus,
    CATEGORY_IDS,
    SHORTS_MAX_DURATION_SECONDS,
)
from .tiktok_auth import TikTokAuth, TokenInfo
from .tiktok_api import TikTokAPI, PrivacyLevel, UploadResult as TikTokUploadResult
from .tiktok_scheduler import TikTokScheduler, QueuedVideo, PostingStats

__all__ = [
    # X/Twitter
    'XClient',
    'PostResult',
    'RateLimiter',
    'PostScheduler',
    'ScheduledPost',
    'PostPriority',
    'PostStatus',
    'LinkManager',
    'TrackedLink',
    'EngagementTracker',
    'TweetMetrics',
    'CampaignMetrics',
    # YouTube
    'YouTubeUploader',
    'YouTubeUploadResult',
    'YouTubeVideoStatus',
    'UpdateResult',
    'YouTubeCategory',
    'PrivacyStatus',
    'CATEGORY_IDS',
    'SHORTS_MAX_DURATION_SECONDS',
    # TikTok
    'TikTokAuth',
    'TokenInfo',
    'TikTokAPI',
    'PrivacyLevel',
    'TikTokUploadResult',
    'TikTokScheduler',
    'QueuedVideo',
    'PostingStats',
]

__version__ = '1.1.0-dev'
