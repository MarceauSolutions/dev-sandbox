#!/usr/bin/env python3
"""
x_api.py - X/Twitter API Wrapper with Rate Limiting

Handles authentication, posting, and rate limit management for X Free tier.

Free Tier Limits:
- 1,500 posts/month (50/day average)
- 10,000 read requests/month
- Media uploads limited

Usage:
    from x_api import XClient

    client = XClient()
    result = client.post_tweet("Hello from automation!")

Environment Variables Required:
    X_API_KEY - API Key (Consumer Key)
    X_API_SECRET - API Secret (Consumer Secret)
    X_ACCESS_TOKEN - Access Token
    X_ACCESS_TOKEN_SECRET - Access Token Secret
    X_BEARER_TOKEN - Bearer Token (for v2 API)
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from functools import wraps

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Try to import tweepy (X/Twitter SDK)
try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False
    print("Warning: tweepy not installed. Run: pip install tweepy")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RateLimitStatus:
    """Track rate limit status."""
    posts_today: int = 0
    posts_this_month: int = 0
    last_post_time: Optional[str] = None
    daily_limit: int = 50  # Free tier: ~50/day to stay under 1500/month
    monthly_limit: int = 1500
    reset_date: Optional[str] = None  # Monthly reset


@dataclass
class PostResult:
    """Result of a post attempt."""
    success: bool
    tweet_id: Optional[str] = None
    text: Optional[str] = None
    created_at: Optional[str] = None
    error: Optional[str] = None
    rate_limited: bool = False


class RateLimiter:
    """
    Rate limiter for X API Free tier.

    Enforces:
    - 50 posts/day (to stay under 1500/month)
    - Minimum 2-minute gap between posts
    - Monthly tracking with reset
    """

    RATE_LIMIT_FILE = Path(__file__).parent.parent / "output" / "rate_limit_status.json"
    MIN_POST_INTERVAL_SECONDS = 120  # 2 minutes between posts

    def __init__(self):
        self.status = self._load_status()
        self._check_monthly_reset()

    def _load_status(self) -> RateLimitStatus:
        """Load rate limit status from file."""
        if self.RATE_LIMIT_FILE.exists():
            try:
                with open(self.RATE_LIMIT_FILE) as f:
                    data = json.load(f)
                return RateLimitStatus(**data)
            except Exception as e:
                logger.warning(f"Error loading rate limit status: {e}")
        return RateLimitStatus()

    def _save_status(self):
        """Save rate limit status to file."""
        self.RATE_LIMIT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.RATE_LIMIT_FILE, 'w') as f:
            json.dump(asdict(self.status), f, indent=2)

    def _check_monthly_reset(self):
        """Reset monthly counter on 1st of month."""
        today = datetime.now().strftime("%Y-%m-01")
        if self.status.reset_date != today:
            if datetime.now().day == 1:
                logger.info("Monthly rate limit reset")
                self.status.posts_this_month = 0
            self.status.reset_date = today
            self._save_status()

    def _check_daily_reset(self):
        """Reset daily counter at midnight."""
        if self.status.last_post_time:
            last_post = datetime.fromisoformat(self.status.last_post_time)
            if last_post.date() < datetime.now().date():
                self.status.posts_today = 0

    def can_post(self) -> tuple[bool, str]:
        """
        Check if we can post based on rate limits.

        Returns:
            (can_post, reason)
        """
        self._check_daily_reset()

        # Check monthly limit
        if self.status.posts_this_month >= self.status.monthly_limit:
            return False, f"Monthly limit reached ({self.status.monthly_limit} posts)"

        # Check daily limit
        if self.status.posts_today >= self.status.daily_limit:
            return False, f"Daily limit reached ({self.status.daily_limit} posts)"

        # Check minimum interval
        if self.status.last_post_time:
            last_post = datetime.fromisoformat(self.status.last_post_time)
            elapsed = (datetime.now() - last_post).total_seconds()
            if elapsed < self.MIN_POST_INTERVAL_SECONDS:
                wait_time = self.MIN_POST_INTERVAL_SECONDS - elapsed
                return False, f"Rate limited. Wait {int(wait_time)} seconds"

        return True, "OK"

    def record_post(self):
        """Record a successful post."""
        self.status.posts_today += 1
        self.status.posts_this_month += 1
        self.status.last_post_time = datetime.now().isoformat()
        self._save_status()

    def get_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        self._check_daily_reset()
        return {
            "posts_today": self.status.posts_today,
            "posts_remaining_today": self.status.daily_limit - self.status.posts_today,
            "posts_this_month": self.status.posts_this_month,
            "posts_remaining_month": self.status.monthly_limit - self.status.posts_this_month,
            "last_post": self.status.last_post_time,
            "can_post": self.can_post()[0]
        }


def rate_limit_check(func):
    """Decorator to check rate limits before posting."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        can_post, reason = self.rate_limiter.can_post()
        if not can_post:
            logger.warning(f"Rate limited: {reason}")
            return PostResult(
                success=False,
                error=reason,
                rate_limited=True
            )
        return func(self, *args, **kwargs)
    return wrapper


class XClient:
    """
    X/Twitter API client with rate limiting.

    Supports both v1.1 and v2 API endpoints.
    """

    def __init__(self):
        """Initialize X client with credentials from environment."""
        self.api_key = os.getenv("X_API_KEY")
        self.api_secret = os.getenv("X_API_SECRET")
        self.access_token = os.getenv("X_ACCESS_TOKEN")
        self.access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")
        self.bearer_token = os.getenv("X_BEARER_TOKEN")

        self.rate_limiter = RateLimiter()
        self.client = None
        self.api_v1 = None

        self._validate_credentials()
        self._init_clients()

    def _validate_credentials(self):
        """Validate that required credentials are present."""
        missing = []
        if not self.api_key:
            missing.append("X_API_KEY")
        if not self.api_secret:
            missing.append("X_API_SECRET")
        if not self.access_token:
            missing.append("X_ACCESS_TOKEN")
        if not self.access_token_secret:
            missing.append("X_ACCESS_TOKEN_SECRET")

        if missing:
            logger.warning(f"Missing X API credentials: {', '.join(missing)}")
            logger.info("Add these to your .env file to enable posting")

    def _init_clients(self):
        """Initialize tweepy clients."""
        if not TWEEPY_AVAILABLE:
            logger.error("tweepy not available. Install with: pip install tweepy")
            return

        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            logger.warning("Credentials incomplete - client not initialized")
            return

        try:
            # v2 Client (for posting)
            self.client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                bearer_token=self.bearer_token
            )

            # v1.1 API (for media uploads)
            auth = tweepy.OAuth1UserHandler(
                self.api_key,
                self.api_secret,
                self.access_token,
                self.access_token_secret
            )
            self.api_v1 = tweepy.API(auth)

            logger.info("X API clients initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing X clients: {e}")

    def is_ready(self) -> bool:
        """Check if client is ready to post."""
        return self.client is not None

    @rate_limit_check
    def post_tweet(
        self,
        text: str,
        reply_to: Optional[str] = None,
        media_ids: Optional[List[str]] = None
    ) -> PostResult:
        """
        Post a tweet with rate limiting.

        Args:
            text: Tweet text (max 280 characters)
            reply_to: Tweet ID to reply to (optional)
            media_ids: List of media IDs to attach (optional)

        Returns:
            PostResult with success status and tweet details
        """
        if not self.is_ready():
            return PostResult(
                success=False,
                error="X client not initialized. Check credentials."
            )

        # Validate text length
        if len(text) > 280:
            return PostResult(
                success=False,
                error=f"Tweet too long ({len(text)} chars, max 280)"
            )

        try:
            # Post tweet using v2 API
            response = self.client.create_tweet(
                text=text,
                in_reply_to_tweet_id=reply_to,
                media_ids=media_ids
            )

            # Record successful post
            self.rate_limiter.record_post()

            tweet_id = response.data['id']
            logger.info(f"Tweet posted successfully: {tweet_id}")

            return PostResult(
                success=True,
                tweet_id=tweet_id,
                text=text,
                created_at=datetime.now().isoformat()
            )

        except tweepy.TweepyException as e:
            logger.error(f"Tweepy error: {e}")
            return PostResult(
                success=False,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Error posting tweet: {e}")
            return PostResult(
                success=False,
                error=str(e)
            )

    def upload_media(self, file_path: str) -> Optional[str]:
        """
        Upload media for attaching to tweets.

        Args:
            file_path: Path to image/video file

        Returns:
            Media ID if successful, None otherwise
        """
        if not self.api_v1:
            logger.error("v1.1 API not initialized for media upload")
            return None

        try:
            media = self.api_v1.media_upload(file_path)
            logger.info(f"Media uploaded: {media.media_id}")
            return str(media.media_id)
        except Exception as e:
            logger.error(f"Error uploading media: {e}")
            return None

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        return self.rate_limiter.get_status()

    def get_me(self) -> Optional[Dict[str, Any]]:
        """Get authenticated user info."""
        if not self.client:
            return None

        try:
            response = self.client.get_me(
                user_fields=['id', 'name', 'username', 'public_metrics']
            )
            if response.data:
                return {
                    'id': response.data.id,
                    'name': response.data.name,
                    'username': response.data.username,
                    'metrics': response.data.public_metrics
                }
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
        return None

    def get_tweet(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        """
        Get tweet details by ID.

        Args:
            tweet_id: Tweet ID to fetch

        Returns:
            Tweet data or None
        """
        if not self.client:
            return None

        try:
            response = self.client.get_tweet(
                tweet_id,
                tweet_fields=['created_at', 'public_metrics', 'text']
            )
            if response.data:
                return {
                    'id': response.data.id,
                    'text': response.data.text,
                    'created_at': str(response.data.created_at),
                    'metrics': response.data.public_metrics
                }
        except Exception as e:
            logger.error(f"Error getting tweet: {e}")
        return None


def main():
    """CLI for X API client."""
    import argparse

    parser = argparse.ArgumentParser(description='X/Twitter API Client')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Post command
    post_parser = subparsers.add_parser('post', help='Post a tweet')
    post_parser.add_argument('text', help='Tweet text')
    post_parser.add_argument('--reply-to', help='Tweet ID to reply to')

    # Status command
    subparsers.add_parser('status', help='Show rate limit status')

    # Me command
    subparsers.add_parser('me', help='Show authenticated user info')

    # Get tweet command
    get_parser = subparsers.add_parser('get', help='Get tweet by ID')
    get_parser.add_argument('tweet_id', help='Tweet ID')

    args = parser.parse_args()

    client = XClient()

    if args.command == 'post':
        result = client.post_tweet(args.text, reply_to=args.reply_to)
        if result.success:
            print(f"Posted successfully!")
            print(f"Tweet ID: {result.tweet_id}")
            print(f"URL: https://x.com/i/status/{result.tweet_id}")
        else:
            print(f"Failed: {result.error}")
            return 1

    elif args.command == 'status':
        status = client.get_rate_limit_status()
        print("\nRate Limit Status:")
        print(f"  Posts today: {status['posts_today']}")
        print(f"  Remaining today: {status['posts_remaining_today']}")
        print(f"  Posts this month: {status['posts_this_month']}")
        print(f"  Remaining this month: {status['posts_remaining_month']}")
        print(f"  Can post now: {'Yes' if status['can_post'] else 'No'}")

    elif args.command == 'me':
        if not client.is_ready():
            print("Client not ready. Check X API credentials in .env")
            return 1
        user = client.get_me()
        if user:
            print(f"\nAuthenticated as: @{user['username']}")
            print(f"Name: {user['name']}")
            print(f"Followers: {user['metrics'].get('followers_count', 0)}")
            print(f"Following: {user['metrics'].get('following_count', 0)}")
        else:
            print("Could not fetch user info")

    elif args.command == 'get':
        tweet = client.get_tweet(args.tweet_id)
        if tweet:
            print(f"\nTweet: {tweet['text']}")
            print(f"Created: {tweet['created_at']}")
            print(f"Likes: {tweet['metrics'].get('like_count', 0)}")
            print(f"Retweets: {tweet['metrics'].get('retweet_count', 0)}")
        else:
            print("Could not fetch tweet")

    else:
        parser.print_help()

    return 0


if __name__ == '__main__':
    exit(main())
