#!/usr/bin/env python3
"""
Background Worker for Fitness Influencer AI v2.0

Processes jobs from the Redis queue using RQ workers.
Each job type routes to appropriate processing functions.

Usage:
    # Start worker (processes all queues)
    rq worker high default low --url redis://localhost:6379

    # Or use the run command
    python backend/worker.py
"""

import os
import sys
import logging
import traceback
from typing import Dict, Any, Optional, Callable
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.task_queue import (
    get_queue,
    JobType,
    JobStatus,
    ESTIMATED_TIMES
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Job Processors
# ============================================================================

def process_video_caption(job_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process video captioning job.

    Expected params:
        - video_url: str
        - style: str (trending, glow, minimal, etc.)
        - position: str (top, center, bottom)
        - language: str (en, es, pt, auto)
        - word_highlight: bool
        - max_words_per_line: int
    """
    queue = get_queue()
    queue.update_progress(job_id, 10)

    video_url = params.get("video_url")
    style = params.get("style", "trending")
    position = params.get("position", "bottom")

    logger.info(f"Processing caption job {job_id}: {video_url}")

    # TODO: Implement actual captioning logic in Story 005-008
    # For now, return mock result
    queue.update_progress(job_id, 50)

    # Simulate processing time
    import time
    time.sleep(2)

    queue.update_progress(job_id, 90)

    result = {
        "video_url": video_url,
        "captioned_video_url": f"/static/videos/{job_id}_captioned.mp4",
        "srt_url": f"/static/captions/{job_id}.srt",
        "style": style,
        "position": position,
        "word_count": 0,
        "processing_time": 2.0
    }

    return result


def process_video_filler_removal(job_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process filler word removal job.

    Expected params:
        - video_url: str
        - sensitivity: str (aggressive, moderate, conservative)
        - language: str (en, es, pt, auto)
        - preview_only: bool
    """
    import asyncio
    from backend.filler_remover import remove_fillers

    queue = get_queue()
    queue.update_progress(job_id, 10)

    video_url = params.get("video_url")
    sensitivity = params.get("sensitivity", "moderate")
    language = params.get("language", "en")
    preview_only = params.get("preview_only", False)

    logger.info(f"Processing filler removal job {job_id}: {video_url}")

    # Download video if URL provided
    video_path = video_url
    temp_video = None

    if video_url.startswith("http"):
        import tempfile
        import urllib.request
        temp_video = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        urllib.request.urlretrieve(video_url, temp_video.name)
        video_path = temp_video.name
        queue.update_progress(job_id, 20)

    try:
        # Run async filler removal in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        queue.update_progress(job_id, 30)

        result = loop.run_until_complete(
            remove_fillers(
                video_path=video_path,
                sensitivity=sensitivity,
                language=language,
                preview_only=preview_only
            )
        )

        loop.close()

        queue.update_progress(job_id, 90)

        if result.success:
            return {
                "video_url": video_url,
                "edited_video_url": result.output_path or video_url,
                "fillers_removed": result.segments_removed,
                "time_saved": result.time_saved,
                "original_duration": result.original_duration,
                "new_duration": result.new_duration,
                "sensitivity": sensitivity,
                "removal_segments": [s.to_dict() for s in result.removal_segments],
                "preview_only": preview_only
            }
        else:
            raise Exception(result.error or "Filler removal failed")

    finally:
        # Clean up temp video if downloaded
        if temp_video:
            import os
            os.unlink(temp_video.name)


def process_video_reframe(job_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process video reframe/auto-crop job.

    Expected params:
        - video_url: str
        - target_aspect: str (9:16, 1:1, 4:5, 16:9)
        - tracking_mode: str (face, body, auto, center)
        - smoothing: float (0.1-1.0)
        - safe_zone_margin: float
    """
    import asyncio
    from backend.auto_reframe import (
        reframe_video,
        parse_aspect_ratio,
        TrackingMode
    )

    queue = get_queue()
    queue.update_progress(job_id, 10)

    video_url = params.get("video_url")
    target_aspect_str = params.get("target_aspect", "9:16")
    tracking_mode_str = params.get("tracking_mode", "center")
    smoothing = params.get("smoothing", 0.8)
    safe_zone_margin = params.get("safe_zone_margin", 0.1)

    logger.info(f"Processing reframe job {job_id}: {video_url} -> {target_aspect_str}")

    # Download video if URL provided
    video_path = video_url
    temp_video = None

    if video_url.startswith("http"):
        import tempfile
        import urllib.request
        temp_video = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        urllib.request.urlretrieve(video_url, temp_video.name)
        video_path = temp_video.name
        queue.update_progress(job_id, 20)

    try:
        # Parse parameters
        target_aspect = parse_aspect_ratio(target_aspect_str)

        tracking_mode_map = {
            "face": TrackingMode.FACE,
            "body": TrackingMode.BODY,
            "auto": TrackingMode.AUTO,
            "center": TrackingMode.CENTER,
        }
        tracking_mode = tracking_mode_map.get(tracking_mode_str.lower(), TrackingMode.CENTER)

        # Run async reframe in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        queue.update_progress(job_id, 30)

        result = loop.run_until_complete(
            reframe_video(
                video_path=video_path,
                target_aspect=target_aspect,
                tracking_mode=tracking_mode,
                smoothing=smoothing,
                safe_zone_margin=safe_zone_margin
            )
        )

        loop.close()

        queue.update_progress(job_id, 90)

        if result.success:
            return {
                "video_url": video_url,
                "reframed_video_url": result.output_path,
                "original_aspect": result.original_aspect,
                "target_aspect": result.target_aspect,
                "original_dimensions": result.original_dimensions,
                "output_dimensions": result.output_dimensions,
                "tracking_mode": result.tracking_mode,
                "frames_analyzed": result.frames_analyzed,
                "processing_time": result.processing_time
            }
        else:
            raise Exception(result.error or "Reframe failed")

    finally:
        # Clean up temp video if downloaded
        if temp_video:
            import os
            os.unlink(temp_video.name)


def process_video_export(job_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process multi-platform export job with real platform encoding.

    Expected params:
        - video_url: str OR video_path: str
        - platforms: list[str] (tiktok, instagram_reels, youtube_shorts, linkedin, twitter)
        - include_captions: bool (optional, default False)
        - generate_descriptions: bool (optional, default True)
        - hashtag_count: int (optional)
        - transcription_text: str (optional, for metadata generation)
        - category: str (optional, workout/nutrition/motivation/etc)
        - webhook_url: str (optional, for completion notification)
    """
    import asyncio
    import tempfile
    import urllib.request
    import httpx
    from backend.platform_exporter import (
        export_for_multiple_platforms,
        parse_platform,
        Platform
    )
    from backend.content_metadata import generate_metadata

    queue = get_queue()
    queue.update_progress(job_id, 5)

    video_url = params.get("video_url") or params.get("video_path")
    platform_strs = params.get("platforms", ["tiktok", "instagram_reels", "youtube_shorts"])
    generate_descriptions = params.get("generate_descriptions", True)
    hashtag_count = params.get("hashtag_count")
    transcription_text = params.get("transcription_text", "")
    category = params.get("category")
    webhook_url = params.get("webhook_url")

    logger.info(f"Processing export job {job_id}: {video_url} -> {platform_strs}")

    # Parse platforms
    platforms = []
    for ps in platform_strs:
        try:
            platforms.append(parse_platform(ps))
        except ValueError as e:
            logger.warning(f"Skipping unknown platform: {ps}")

    if not platforms:
        raise ValueError("No valid platforms specified")

    queue.update_progress(job_id, 10)

    # Download video if URL provided
    video_path = video_url
    temp_video = None

    if video_url and video_url.startswith("http"):
        temp_video = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        urllib.request.urlretrieve(video_url, temp_video.name)
        video_path = temp_video.name
        queue.update_progress(job_id, 20)

    try:
        # Run async export in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Export to all platforms in parallel
        queue.update_progress(job_id, 30)

        export_results = loop.run_until_complete(
            export_for_multiple_platforms(
                video_path=video_path,
                platforms=platforms,
                max_concurrent=3
            )
        )

        queue.update_progress(job_id, 70)

        # Generate metadata for each platform
        exports = {}
        successful_exports = 0
        failed_exports = 0

        for platform, export_result in export_results.items():
            platform_data = {
                "success": export_result.success,
                "video_url": export_result.output_path,
                "original_duration": export_result.original_duration,
                "final_duration": export_result.final_duration,
                "file_size_mb": export_result.file_size_mb,
                "warnings": [w.message for w in export_result.warnings],
                "error": export_result.error
            }

            if export_result.success:
                successful_exports += 1

                # Generate metadata if requested
                if generate_descriptions and transcription_text:
                    metadata = loop.run_until_complete(
                        generate_metadata(
                            transcription_text=transcription_text,
                            platform=platform,
                            category=category,
                            hashtag_count=hashtag_count
                        )
                    )
                    platform_data.update({
                        "description": metadata.description,
                        "hashtags": metadata.hashtags,
                        "hashtag_string": metadata.hashtag_string,
                        "keywords": metadata.keywords,
                        "category": metadata.category
                    })
                else:
                    # Basic metadata without transcription
                    platform_data.update({
                        "description": "",
                        "hashtags": [],
                        "hashtag_string": "",
                        "keywords": [],
                        "category": category or "workout"
                    })
            else:
                failed_exports += 1

            exports[platform.value] = platform_data

        loop.close()

        queue.update_progress(job_id, 90)

        # Send webhook notification if configured
        if webhook_url:
            try:
                with httpx.Client(timeout=10) as client:
                    client.post(webhook_url, json={
                        "job_id": job_id,
                        "status": "completed",
                        "successful_exports": successful_exports,
                        "failed_exports": failed_exports,
                        "platforms": list(exports.keys())
                    })
            except Exception as e:
                logger.warning(f"Webhook notification failed: {e}")

        result = {
            "video_url": video_url,
            "exports": exports,
            "platforms_exported": successful_exports,
            "platforms_failed": failed_exports,
            "total_platforms": len(platforms)
        }

        return result

    finally:
        # Clean up temp video if downloaded
        if temp_video:
            import os
            try:
                os.unlink(temp_video.name)
            except:
                pass


def process_video_jumpcut(job_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process video jump cut (silence removal) job.

    Expected params:
        - video_url: str OR video_path: str
        - silence_threshold: float (default -40)
        - min_silence_duration: float (default 0.3)
        - generate_thumbnail: bool
    """
    queue = get_queue()
    queue.update_progress(job_id, 10)

    video_url = params.get("video_url") or params.get("video_path")
    silence_threshold = params.get("silence_threshold", -40)

    logger.info(f"Processing jumpcut job {job_id}: {video_url}")

    # Import existing jumpcut module
    try:
        from backend.video_jumpcut import VideoJumpCutter

        # Download video if URL
        import tempfile
        import requests

        if video_url.startswith("http"):
            queue.update_progress(job_id, 20)
            # Download to temp file
            response = requests.get(video_url, stream=True)
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                input_path = f.name
        else:
            input_path = video_url

        queue.update_progress(job_id, 30)

        # Process
        output_dir = os.path.join(os.path.dirname(__file__), "static", "videos")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{job_id}_edited.mp4")

        cutter = VideoJumpCutter(
            silence_thresh=silence_threshold,
            min_silence_duration=params.get("min_silence_duration", 0.3)
        )

        queue.update_progress(job_id, 50)
        stats = cutter.apply_jump_cuts(input_path, output_path)
        queue.update_progress(job_id, 80)

        # Generate thumbnail if requested
        thumbnail_url = None
        if params.get("generate_thumbnail", True):
            thumb_path = os.path.join(output_dir, f"{job_id}_thumb.jpg")
            cutter.generate_thumbnail(output_path, thumb_path)
            thumbnail_url = f"/static/videos/{job_id}_thumb.jpg"

        queue.update_progress(job_id, 90)

        result = {
            "video_url": video_url,
            "edited_video_url": f"/static/videos/{job_id}_edited.mp4",
            "thumbnail_url": thumbnail_url,
            "original_duration": stats.get("original_duration", 0),
            "final_duration": stats.get("final_duration", 0),
            "cuts_made": stats.get("cuts_made", 0),
            "time_saved": stats.get("time_saved", 0),
            "size_reduction_percent": stats.get("size_reduction_percent", 0)
        }

    except Exception as e:
        logger.error(f"Jump cut processing failed: {e}")
        raise

    return result


def process_long_to_shorts(job_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process long-form to shorts extraction job.

    Expected params:
        - video_url: str
        - target_duration: list[int] (e.g., [15, 30, 60])
        - max_clips: int
        - min_viral_score: int
        - include_hooks: bool
        - fitness_focus: bool
    """
    queue = get_queue()
    queue.update_progress(job_id, 10)

    video_url = params.get("video_url")
    max_clips = params.get("max_clips", 10)

    logger.info(f"Processing long-to-shorts job {job_id}: {video_url}")

    # TODO: Implement in Story 017-020
    queue.update_progress(job_id, 50)

    import time
    time.sleep(3)

    queue.update_progress(job_id, 90)

    # Mock clips
    clips = []
    for i in range(min(max_clips, 5)):
        clips.append({
            "clip_url": f"/static/videos/{job_id}_clip_{i}.mp4",
            "start_time": i * 60,
            "duration": 30,
            "viral_score": 75 + i * 5,
            "hook_text": f"Check this out! Clip {i+1}"
        })

    result = {
        "video_url": video_url,
        "clips": clips,
        "total_clips": len(clips),
        "average_viral_score": sum(c["viral_score"] for c in clips) / len(clips) if clips else 0
    }

    return result


def process_image_generation(job_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process AI image generation job.

    Expected params:
        - prompt: str
        - count: int
        - style: str (optional)
    """
    queue = get_queue()
    queue.update_progress(job_id, 10)

    prompt = params.get("prompt")
    count = params.get("count", 1)

    logger.info(f"Processing image generation job {job_id}: {prompt[:50]}...")

    try:
        from backend.grok_image_gen import GrokImageGenerator

        generator = GrokImageGenerator()
        queue.update_progress(job_id, 30)

        images = generator.generate_image(prompt, count=count)
        queue.update_progress(job_id, 90)

        result = {
            "prompt": prompt,
            "images": images if isinstance(images, list) else [images],
            "count": len(images) if isinstance(images, list) else 1,
            "cost": 0.07 * count
        }

    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        result = {
            "prompt": prompt,
            "images": [],
            "count": 0,
            "error": str(e)
        }

    return result


def process_transcription(job_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process audio transcription job.

    Expected params:
        - video_url: str OR audio_url: str
        - language: str (en, es, pt, auto)
        - word_timestamps: bool
    """
    queue = get_queue()
    queue.update_progress(job_id, 10)

    video_url = params.get("video_url") or params.get("audio_url")
    language = params.get("language", "en")

    logger.info(f"Processing transcription job {job_id}: {video_url}")

    # TODO: Implement in Story 005
    queue.update_progress(job_id, 50)

    import time
    time.sleep(2)

    queue.update_progress(job_id, 90)

    result = {
        "video_url": video_url,
        "transcript": "Sample transcript text...",
        "words": [],
        "language": language,
        "duration": 0.0
    }

    return result


# ============================================================================
# Job Router
# ============================================================================

# Map job types to processor functions
JOB_PROCESSORS: Dict[str, Callable] = {
    JobType.VIDEO_CAPTION.value: process_video_caption,
    JobType.VIDEO_FILLER_REMOVAL.value: process_video_filler_removal,
    JobType.VIDEO_REFRAME.value: process_video_reframe,
    JobType.VIDEO_EXPORT.value: process_video_export,
    JobType.VIDEO_JUMPCUT.value: process_video_jumpcut,
    JobType.LONG_TO_SHORTS.value: process_long_to_shorts,
    JobType.IMAGE_GENERATION.value: process_image_generation,
    JobType.TRANSCRIPTION.value: process_transcription,
}


def process_job(job_id: str, job_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main job processing function called by RQ worker.

    Routes to appropriate processor based on job type.
    """
    queue = get_queue()
    logger.info(f"Starting job {job_id} of type {job_type}")

    try:
        # Get processor for job type
        processor = JOB_PROCESSORS.get(job_type)
        if not processor:
            raise ValueError(f"Unknown job type: {job_type}")

        # Process the job
        result = processor(job_id, params)

        # Mark as complete
        queue.complete_job(job_id, result)
        logger.info(f"Completed job {job_id}")

        return result

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Job {job_id} failed: {error_msg}")
        logger.error(traceback.format_exc())

        queue.fail_job(job_id, error_msg)
        raise


# ============================================================================
# Worker Runner
# ============================================================================

def run_worker():
    """Start the RQ worker."""
    try:
        from redis import Redis
        from rq import Worker, Queue

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_conn = Redis.from_url(redis_url)

        # Listen to all queues
        queues = [
            Queue("high", connection=redis_conn),
            Queue("default", connection=redis_conn),
            Queue("low", connection=redis_conn),
        ]

        logger.info(f"Starting worker listening to queues: high, default, low")
        worker = Worker(queues, connection=redis_conn)
        worker.work()

    except ImportError:
        logger.error("Redis/RQ not installed. Run: pip install redis rq")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Worker failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_worker()
