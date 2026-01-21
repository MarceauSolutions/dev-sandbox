"""
Social Media Automation - Multi-Platform Integration

Provides automated posting, scheduling, and analytics for:
- X (Twitter)
- YouTube (Videos and Shorts)
"""

from .x_api import XClient, PostResult, RateLimiter
from .x_scheduler import PostScheduler, ScheduledPost, PostPriority, PostStatus
from .link_manager import LinkManager, TrackedLink
from .engagement_tracker import EngagementTracker, TweetMetrics, CampaignMetrics
from .youtube_uploader import (
    YouTubeUploader,
    UploadResult,
    VideoStatus,
    UpdateResult,
    YouTubeCategory,
    PrivacyStatus,
    CATEGORY_IDS,
    SHORTS_MAX_DURATION_SECONDS,
)

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
    'UploadResult',
    'VideoStatus',
    'UpdateResult',
    'YouTubeCategory',
    'PrivacyStatus',
    'CATEGORY_IDS',
    'SHORTS_MAX_DURATION_SECONDS',
]

__version__ = '1.0.0-dev'
