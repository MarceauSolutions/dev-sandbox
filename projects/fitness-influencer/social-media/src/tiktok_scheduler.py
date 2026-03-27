#!/usr/bin/env python3
"""
tiktok_scheduler.py - TikTok Video Scheduling and Queue Management

Manages a queue of videos for automated posting to TikTok.

Directory Structure:
    output/tiktok_videos/
    ├── video_001.mp4           # Ready to post
    ├── video_001.txt           # Caption + hashtags
    ├── video_002.mp4
    ├── video_002.txt
    └── posted/                 # Archive after posting
        ├── video_001.mp4
        └── video_001.txt

Usage:
    # Post next video from queue
    python -m src.tiktok_scheduler post

    # Post multiple videos
    python -m src.tiktok_scheduler post --count 3

    # Show queue status
    python -m src.tiktok_scheduler status

    # List videos in queue
    python -m src.tiktok_scheduler list

Cron Setup (2-3 videos/day):
    # Morning (7 AM)
    0 7 * * * cd /path/to/social-media-automation && python -m src.tiktok_scheduler post

    # Midday (12 PM)
    0 12 * * * cd /path/to/social-media-automation && python -m src.tiktok_scheduler post

    # Evening (7 PM)
    0 19 * * * cd /path/to/social-media-automation && python -m src.tiktok_scheduler post
"""

import os
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict

from dotenv import load_dotenv
load_dotenv()

from .tiktok_api import TikTokAPI, PrivacyLevel, UploadResult

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class QueuedVideo:
    """A video in the posting queue."""
    video_path: str
    caption_path: str
    caption: str
    file_size_mb: float
    queued_at: str


@dataclass
class PostingStats:
    """Statistics for TikTok posting."""
    total_queued: int
    total_posted: int
    posts_today: int
    last_post_time: Optional[str]
    videos_in_queue: List[str]


class TikTokScheduler:
    """
    TikTok Video Scheduler.

    Manages a queue of videos and automates posting to TikTok.
    """

    QUEUE_DIR = Path(__file__).parent.parent / "output" / "tiktok_videos"
    POSTED_DIR = QUEUE_DIR / "posted"
    STATS_FILE = Path(__file__).parent.parent / "output" / "tiktok_scheduler_stats.json"

    # Supported video formats
    VIDEO_EXTENSIONS = {'.mp4', '.mov', '.webm'}

    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize TikTok scheduler.

        Args:
            access_token: TikTok OAuth access token (optional, uses env var)
        """
        self.api = TikTokAPI(access_token=access_token)
        self.stats = self._load_stats()

        # Ensure directories exist
        self.QUEUE_DIR.mkdir(parents=True, exist_ok=True)
        self.POSTED_DIR.mkdir(parents=True, exist_ok=True)

    def _load_stats(self) -> Dict[str, Any]:
        """Load scheduling statistics."""
        default_stats = {
            "total_posted": 0,
            "posts_today": 0,
            "last_post_date": None,
            "last_post_time": None,
            "post_history": []
        }

        if self.STATS_FILE.exists():
            try:
                with open(self.STATS_FILE) as f:
                    stats = json.load(f)
                    # Reset daily counter if new day
                    if stats.get("last_post_date") != datetime.now().strftime("%Y-%m-%d"):
                        stats["posts_today"] = 0
                    return stats
            except Exception as e:
                logger.warning(f"Error loading stats: {e}")

        return default_stats

    def _save_stats(self):
        """Save scheduling statistics."""
        self.STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.STATS_FILE, 'w') as f:
            json.dump(self.stats, f, indent=2)

    def _record_post(self, video_name: str, success: bool, publish_id: Optional[str] = None):
        """Record a post attempt in stats."""
        now = datetime.now()

        if success:
            self.stats["total_posted"] += 1
            self.stats["posts_today"] += 1
            self.stats["last_post_date"] = now.strftime("%Y-%m-%d")
            self.stats["last_post_time"] = now.isoformat()

        self.stats["post_history"].append({
            "timestamp": now.isoformat(),
            "video": video_name,
            "success": success,
            "publish_id": publish_id
        })

        # Keep only last 100 entries
        self.stats["post_history"] = self.stats["post_history"][-100:]

        self._save_stats()

    def get_queue(self) -> List[QueuedVideo]:
        """
        Get list of videos in the queue.

        Returns:
            List of QueuedVideo objects sorted by filename
        """
        queued = []

        # Find all video files
        videos = []
        for ext in self.VIDEO_EXTENSIONS:
            videos.extend(self.QUEUE_DIR.glob(f"*{ext}"))

        for video_path in sorted(videos):
            caption_path = video_path.with_suffix(".txt")

            # Read caption
            caption = ""
            if caption_path.exists():
                try:
                    with open(caption_path) as f:
                        caption = f.read().strip()
                except Exception as e:
                    logger.warning(f"Error reading caption for {video_path.name}: {e}")

            queued.append(QueuedVideo(
                video_path=str(video_path),
                caption_path=str(caption_path) if caption_path.exists() else "",
                caption=caption,
                file_size_mb=video_path.stat().st_size / (1024 * 1024),
                queued_at=datetime.fromtimestamp(video_path.stat().st_mtime).isoformat()
            ))

        return queued

    def get_next_video(self) -> Optional[QueuedVideo]:
        """Get the next video to post."""
        queue = self.get_queue()
        return queue[0] if queue else None

    def post_next_video(
        self,
        privacy: PrivacyLevel = PrivacyLevel.SELF_ONLY,
        archive: bool = True
    ) -> Optional[UploadResult]:
        """
        Post the next video from the queue.

        Args:
            privacy: Privacy level for the video
            archive: Move to 'posted' directory after posting

        Returns:
            UploadResult or None if queue is empty
        """
        video = self.get_next_video()

        if not video:
            logger.info("No videos in queue")
            return None

        if not video.caption:
            logger.error(f"No caption found for {Path(video.video_path).name}")
            logger.info(f"Create a .txt file with the same name as the video")
            return UploadResult(
                success=False,
                error=f"Missing caption file for {Path(video.video_path).name}"
            )

        logger.info(f"Posting: {Path(video.video_path).name}")
        logger.info(f"Caption: {video.caption[:100]}...")

        # Post to TikTok
        result = self.api.post_video(
            video_path=video.video_path,
            caption=video.caption,
            privacy=privacy
        )

        # Record in stats
        self._record_post(
            video_name=Path(video.video_path).name,
            success=result.success,
            publish_id=result.publish_id
        )

        # Archive if successful and requested
        if result.success and archive:
            self._archive_video(video)

        return result

    def _archive_video(self, video: QueuedVideo):
        """Move posted video to archive directory."""
        video_path = Path(video.video_path)
        caption_path = Path(video.caption_path) if video.caption_path else None

        # Create timestamped archive path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archived_video = self.POSTED_DIR / f"{timestamp}_{video_path.name}"

        try:
            shutil.move(str(video_path), str(archived_video))
            logger.info(f"Archived video to: {archived_video}")

            if caption_path and caption_path.exists():
                archived_caption = self.POSTED_DIR / f"{timestamp}_{caption_path.name}"
                shutil.move(str(caption_path), str(archived_caption))

        except Exception as e:
            logger.error(f"Error archiving video: {e}")

    def post_from_schedule(
        self,
        count: int = 1,
        privacy: PrivacyLevel = PrivacyLevel.SELF_ONLY,
        archive: bool = True
    ) -> List[UploadResult]:
        """
        Post multiple videos from the queue.

        Args:
            count: Number of videos to post
            privacy: Privacy level for videos
            archive: Archive videos after posting

        Returns:
            List of UploadResult for each post attempt
        """
        results = []

        for i in range(count):
            result = self.post_next_video(privacy=privacy, archive=archive)
            if result:
                results.append(result)
                if not result.success:
                    logger.warning(f"Post {i+1} failed: {result.error}")
            else:
                logger.info(f"Queue empty after {i} posts")
                break

        return results

    def get_status(self) -> PostingStats:
        """Get current scheduler status."""
        queue = self.get_queue()

        return PostingStats(
            total_queued=len(queue),
            total_posted=self.stats["total_posted"],
            posts_today=self.stats["posts_today"],
            last_post_time=self.stats["last_post_time"],
            videos_in_queue=[Path(v.video_path).name for v in queue[:10]]
        )

    def add_video(
        self,
        video_path: str,
        caption: str,
        copy: bool = True
    ) -> bool:
        """
        Add a video to the queue.

        Args:
            video_path: Path to video file
            caption: Caption for the video
            copy: Copy file to queue (vs move)

        Returns:
            True if successful
        """
        source = Path(video_path)

        if not source.exists():
            logger.error(f"Video not found: {video_path}")
            return False

        if source.suffix.lower() not in self.VIDEO_EXTENSIONS:
            logger.error(f"Unsupported format: {source.suffix}")
            return False

        # Generate unique name if needed
        dest_video = self.QUEUE_DIR / source.name
        counter = 1
        while dest_video.exists():
            dest_video = self.QUEUE_DIR / f"{source.stem}_{counter}{source.suffix}"
            counter += 1

        # Copy or move video
        try:
            if copy:
                shutil.copy2(str(source), str(dest_video))
            else:
                shutil.move(str(source), str(dest_video))

            # Write caption file
            caption_path = dest_video.with_suffix(".txt")
            with open(caption_path, 'w') as f:
                f.write(caption)

            logger.info(f"Added to queue: {dest_video.name}")
            return True

        except Exception as e:
            logger.error(f"Error adding video: {e}")
            return False

    def clear_queue(self, archive: bool = True) -> int:
        """
        Clear all videos from the queue.

        Args:
            archive: Move to 'posted' instead of deleting

        Returns:
            Number of videos cleared
        """
        queue = self.get_queue()
        count = 0

        for video in queue:
            video_path = Path(video.video_path)
            caption_path = Path(video.caption_path) if video.caption_path else None

            try:
                if archive:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    archived = self.POSTED_DIR / f"cleared_{timestamp}_{video_path.name}"
                    shutil.move(str(video_path), str(archived))
                    if caption_path and caption_path.exists():
                        shutil.move(str(caption_path), str(archived.with_suffix(".txt")))
                else:
                    video_path.unlink()
                    if caption_path and caption_path.exists():
                        caption_path.unlink()

                count += 1

            except Exception as e:
                logger.error(f"Error clearing {video_path.name}: {e}")

        logger.info(f"Cleared {count} videos from queue")
        return count


def main():
    """CLI for TikTok scheduler."""
    import argparse

    parser = argparse.ArgumentParser(description='TikTok Video Scheduler')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Post command
    post_parser = subparsers.add_parser('post', help='Post video(s) from queue')
    post_parser.add_argument(
        '--count', '-n',
        type=int,
        default=1,
        help='Number of videos to post (default: 1)'
    )
    post_parser.add_argument(
        '--privacy', '-p',
        choices=['public', 'friends', 'private'],
        default='private',
        help='Privacy level (default: private)'
    )
    post_parser.add_argument(
        '--no-archive',
        action='store_true',
        help='Do not archive posted videos'
    )

    # Status command
    subparsers.add_parser('status', help='Show scheduler status')

    # List command
    list_parser = subparsers.add_parser('list', help='List videos in queue')
    list_parser.add_argument('--full', '-f', action='store_true', help='Show full details')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add video to queue')
    add_parser.add_argument('video_path', help='Path to video file')
    add_parser.add_argument('--caption', '-c', required=True, help='Video caption')
    add_parser.add_argument('--move', action='store_true', help='Move instead of copy')

    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear video queue')
    clear_parser.add_argument('--delete', action='store_true', help='Delete instead of archive')

    args = parser.parse_args()

    scheduler = TikTokScheduler()

    if args.command == 'post':
        privacy_map = {
            'public': PrivacyLevel.PUBLIC_TO_EVERYONE,
            'friends': PrivacyLevel.MUTUAL_FOLLOW_FRIENDS,
            'private': PrivacyLevel.SELF_ONLY
        }
        privacy = privacy_map[args.privacy]

        if privacy == PrivacyLevel.PUBLIC_TO_EVERYONE:
            print("\nWARNING: Public posting requires TikTok audit approval.")
            print("If not audited, videos will be posted as PRIVATE.\n")

        results = scheduler.post_from_schedule(
            count=args.count,
            privacy=privacy,
            archive=not args.no_archive
        )

        if not results:
            print("No videos in queue.")
            return 0

        success_count = sum(1 for r in results if r.success)
        print(f"\nPosted {success_count}/{len(results)} videos successfully.")

        for i, result in enumerate(results, 1):
            if result.success:
                print(f"  {i}. ✓ {result.publish_id}")
            else:
                print(f"  {i}. ✗ {result.error}")

    elif args.command == 'status':
        status = scheduler.get_status()
        print("\nTikTok Scheduler Status:")
        print("-" * 40)
        print(f"  Videos in queue: {status.total_queued}")
        print(f"  Total posted: {status.total_posted}")
        print(f"  Posts today: {status.posts_today}")
        if status.last_post_time:
            print(f"  Last post: {status.last_post_time[:19]}")
        print()

        if status.videos_in_queue:
            print("Next videos:")
            for name in status.videos_in_queue[:5]:
                print(f"  • {name}")

    elif args.command == 'list':
        queue = scheduler.get_queue()
        if not queue:
            print("Queue is empty.")
            return 0

        print(f"\nVideos in Queue ({len(queue)}):")
        print("-" * 60)

        for i, video in enumerate(queue, 1):
            name = Path(video.video_path).name
            print(f"{i}. {name}")
            if args.full:
                print(f"   Size: {video.file_size_mb:.1f} MB")
                print(f"   Caption: {video.caption[:80]}...")
                print()

    elif args.command == 'add':
        success = scheduler.add_video(
            video_path=args.video_path,
            caption=args.caption,
            copy=not args.move
        )

        if success:
            print("Video added to queue.")
        else:
            print("Failed to add video.")
            return 1

    elif args.command == 'clear':
        count = scheduler.clear_queue(archive=not args.delete)
        print(f"Cleared {count} videos from queue.")

    else:
        parser.print_help()

    return 0


if __name__ == '__main__':
    exit(main())
