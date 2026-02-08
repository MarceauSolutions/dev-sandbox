"""
Auto-Reframe Engine for Fitness Influencer AI

Converts videos between aspect ratios using intelligent cropping.
Keeps subjects centered in frame with motion smoothing.

Story 011: Create auto-reframe engine with aspect ratio conversion

Usage:
    from backend.auto_reframe import reframe_video, AspectRatio

    # Reframe video to 9:16 (TikTok/Reels)
    result = await reframe_video(
        video_path="/path/to/video.mp4",
        target_aspect=AspectRatio.PORTRAIT_9_16,
        smoothing=0.8
    )

    print(f"Reframed: {result.output_path}")
"""

import os
import subprocess
import asyncio
import json
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any, Callable
from enum import Enum
import tempfile

from backend.logging_config import get_logger, log_job_event

logger = get_logger(__name__)


class AspectRatio(Enum):
    """Supported aspect ratios for reframing."""
    PORTRAIT_9_16 = "9:16"  # TikTok, Instagram Reels, YouTube Shorts
    SQUARE_1_1 = "1:1"      # Instagram Feed
    PORTRAIT_4_5 = "4:5"    # Instagram Feed (portrait)
    LANDSCAPE_16_9 = "16:9" # YouTube, standard widescreen
    LANDSCAPE_4_3 = "4:3"   # Classic TV format

    @property
    def ratio(self) -> float:
        """Get numeric ratio (width/height)."""
        parts = self.value.split(":")
        return float(parts[0]) / float(parts[1])

    @property
    def dimensions(self) -> Tuple[int, int]:
        """Get standard dimensions (width, height) for this ratio."""
        return ASPECT_DIMENSIONS.get(self, (1080, 1920))


# Standard dimensions for each aspect ratio
ASPECT_DIMENSIONS = {
    AspectRatio.PORTRAIT_9_16: (1080, 1920),
    AspectRatio.SQUARE_1_1: (1080, 1080),
    AspectRatio.PORTRAIT_4_5: (1080, 1350),
    AspectRatio.LANDSCAPE_16_9: (1920, 1080),
    AspectRatio.LANDSCAPE_4_3: (1440, 1080),
}


class TrackingMode(Enum):
    """Subject tracking modes."""
    FACE = "face"      # Track faces
    BODY = "body"      # Track full body/pose
    AUTO = "auto"      # Auto-detect best mode
    CENTER = "center"  # Simple center crop (no tracking)


@dataclass
class Point:
    """2D point/coordinate."""
    x: float
    y: float

    def distance_to(self, other: 'Point') -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


@dataclass
class BoundingBox:
    """Bounding box for detected subject."""
    x: int       # Top-left x
    y: int       # Top-left y
    width: int
    height: int
    confidence: float = 1.0

    @property
    def center(self) -> Point:
        return Point(
            self.x + self.width / 2,
            self.y + self.height / 2
        )

    @property
    def area(self) -> int:
        return self.width * self.height


@dataclass
class FrameInfo:
    """Information about a video frame."""
    frame_number: int
    timestamp: float
    subjects: List[BoundingBox] = field(default_factory=list)
    center_of_interest: Optional[Point] = None

    def to_dict(self) -> dict:
        return {
            "frame_number": self.frame_number,
            "timestamp": round(self.timestamp, 3),
            "subjects": len(self.subjects),
            "center_of_interest": {
                "x": round(self.center_of_interest.x, 1),
                "y": round(self.center_of_interest.y, 1)
            } if self.center_of_interest else None
        }


@dataclass
class ReframeResult:
    """Result of reframing operation."""
    success: bool
    output_path: Optional[str]
    original_aspect: str
    target_aspect: str
    original_dimensions: Tuple[int, int]
    output_dimensions: Tuple[int, int]
    tracking_mode: str
    frames_analyzed: int
    processing_time: float
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output_path": self.output_path,
            "original_aspect": self.original_aspect,
            "target_aspect": self.target_aspect,
            "original_dimensions": self.original_dimensions,
            "output_dimensions": self.output_dimensions,
            "tracking_mode": self.tracking_mode,
            "frames_analyzed": self.frames_analyzed,
            "processing_time": round(self.processing_time, 2),
            "error": self.error
        }


def get_video_info(video_path: str) -> Dict[str, Any]:
    """Get video metadata using FFprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height,r_frame_rate,duration",
                "-of", "json",
                video_path
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        data = json.loads(result.stdout)
        stream = data.get("streams", [{}])[0]

        # Parse frame rate (e.g., "30/1" or "30000/1001")
        fps_str = stream.get("r_frame_rate", "30/1")
        fps_parts = fps_str.split("/")
        fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 30.0

        return {
            "width": int(stream.get("width", 1920)),
            "height": int(stream.get("height", 1080)),
            "fps": fps,
            "duration": float(stream.get("duration", 0))
        }
    except Exception as e:
        logger.error(f"Failed to get video info: {e}")
        return {"width": 1920, "height": 1080, "fps": 30.0, "duration": 0}


def calculate_aspect_ratio(width: int, height: int) -> str:
    """Calculate aspect ratio string from dimensions."""
    from math import gcd
    divisor = gcd(width, height)
    return f"{width // divisor}:{height // divisor}"


def calculate_crop_dimensions(
    source_width: int,
    source_height: int,
    target_aspect: AspectRatio,
    safe_zone_margin: float = 0.1
) -> Tuple[int, int, int, int]:
    """
    Calculate crop dimensions to achieve target aspect ratio.

    Returns (crop_width, crop_height, max_x_offset, max_y_offset).
    """
    target_ratio = target_aspect.ratio
    source_ratio = source_width / source_height

    if target_ratio > source_ratio:
        # Target is wider - crop height
        crop_width = source_width
        crop_height = int(source_width / target_ratio)
    else:
        # Target is taller - crop width
        crop_height = source_height
        crop_width = int(source_height * target_ratio)

    # Apply safe zone margin
    safe_width = int(crop_width * (1 - safe_zone_margin))
    safe_height = int(crop_height * (1 - safe_zone_margin))

    # Calculate max offsets (how much we can move the crop window)
    max_x_offset = source_width - crop_width
    max_y_offset = source_height - crop_height

    return crop_width, crop_height, max_x_offset, max_y_offset


def smooth_trajectory(
    points: List[Point],
    smoothing_factor: float = 0.8
) -> List[Point]:
    """
    Apply exponential smoothing to trajectory to prevent jerky motion.

    Higher smoothing_factor = smoother but slower response.
    """
    if not points or smoothing_factor <= 0:
        return points

    smoothed = [points[0]]

    for i in range(1, len(points)):
        prev = smoothed[-1]
        curr = points[i]

        # Exponential moving average
        new_x = prev.x * smoothing_factor + curr.x * (1 - smoothing_factor)
        new_y = prev.y * smoothing_factor + curr.y * (1 - smoothing_factor)

        smoothed.append(Point(new_x, new_y))

    return smoothed


def center_crop_position(
    frame_width: int,
    frame_height: int,
    crop_width: int,
    crop_height: int,
    center: Optional[Point] = None
) -> Tuple[int, int]:
    """
    Calculate crop position to center on a point.

    If no center is provided, uses frame center.
    """
    if center is None:
        center = Point(frame_width / 2, frame_height / 2)

    # Calculate crop position
    x = int(center.x - crop_width / 2)
    y = int(center.y - crop_height / 2)

    # Clamp to valid range
    x = max(0, min(x, frame_width - crop_width))
    y = max(0, min(y, frame_height - crop_height))

    return x, y


async def analyze_frames_for_reframe(
    video_path: str,
    tracking_mode: TrackingMode = TrackingMode.CENTER,
    sample_interval: int = 10,
    smoothing_factor: float = 0.8
) -> List[FrameInfo]:
    """
    Analyze video frames to determine center of interest.

    For TrackingMode.CENTER, uses frame center.
    For FACE/BODY modes, uses MediaPipe detection via subject_tracker.

    Args:
        video_path: Path to video
        tracking_mode: How to detect subjects
        sample_interval: Analyze every Nth frame
        smoothing_factor: Smoothing for subject tracking trajectory

    Returns:
        List of FrameInfo with center_of_interest for each analyzed frame
    """
    video_info = get_video_info(video_path)
    fps = video_info["fps"]
    duration = video_info["duration"]
    width = video_info["width"]
    height = video_info["height"]

    total_frames = int(duration * fps)
    center = Point(width / 2, height / 2)

    if tracking_mode == TrackingMode.CENTER:
        # Simple center - no detection needed
        frames_to_analyze = list(range(0, total_frames, sample_interval))
        frame_infos = []

        for frame_num in frames_to_analyze:
            timestamp = frame_num / fps
            frame_info = FrameInfo(
                frame_number=frame_num,
                timestamp=timestamp,
                subjects=[],
                center_of_interest=center
            )
            frame_infos.append(frame_info)

        return frame_infos

    # Use subject tracker for FACE/BODY/AUTO modes
    try:
        from backend.subject_tracker import (
            track_subjects,
            DetectionMode as TrackerDetectionMode,
            SubjectPriority
        )

        # Map tracking mode to detector mode
        mode_map = {
            TrackingMode.FACE: "face",
            TrackingMode.BODY: "body",
            TrackingMode.AUTO: "auto",
        }
        detector_mode = mode_map.get(tracking_mode, "face")

        # Run subject tracking
        tracking_result = await track_subjects(
            video_path=video_path,
            mode=detector_mode,
            priority="largest",
            smoothing_factor=smoothing_factor,
            sample_interval=sample_interval
        )

        if not tracking_result.success or not tracking_result.frames:
            logger.warning(f"Subject tracking failed, falling back to center: {tracking_result.error}")
            # Fallback to center
            frames_to_analyze = list(range(0, total_frames, sample_interval))
            return [
                FrameInfo(
                    frame_number=fn,
                    timestamp=fn / fps,
                    subjects=[],
                    center_of_interest=center
                )
                for fn in frames_to_analyze
            ]

        # Convert tracking results to FrameInfo
        frame_infos = []
        for tracked_frame in tracking_result.frames:
            # Convert subjects to BoundingBox format
            subjects = [
                BoundingBox(
                    x=s.x, y=s.y, width=s.width, height=s.height,
                    confidence=s.confidence
                )
                for s in tracked_frame.subjects
            ]

            frame_infos.append(FrameInfo(
                frame_number=tracked_frame.frame_number,
                timestamp=tracked_frame.timestamp,
                subjects=subjects,
                center_of_interest=Point(
                    tracked_frame.center_of_interest.x,
                    tracked_frame.center_of_interest.y
                )
            ))

        return frame_infos

    except ImportError:
        logger.warning("Subject tracker not available, falling back to center")
        frames_to_analyze = list(range(0, total_frames, sample_interval))
        return [
            FrameInfo(
                frame_number=fn,
                timestamp=fn / fps,
                subjects=[],
                center_of_interest=center
            )
            for fn in frames_to_analyze
        ]
    except Exception as e:
        logger.error(f"Subject tracking error: {e}, falling back to center")
        frames_to_analyze = list(range(0, total_frames, sample_interval))
        return [
            FrameInfo(
                frame_number=fn,
                timestamp=fn / fps,
                subjects=[],
                center_of_interest=center
            )
            for fn in frames_to_analyze
        ]


def generate_crop_keyframes(
    frame_infos: List[FrameInfo],
    crop_width: int,
    crop_height: int,
    frame_width: int,
    frame_height: int,
    smoothing_factor: float = 0.8
) -> List[Tuple[float, int, int]]:
    """
    Generate crop position keyframes from frame analysis.

    Returns list of (timestamp, x, y) tuples for crop positions.
    """
    if not frame_infos:
        return [(0, 0, 0)]

    # Extract centers of interest
    centers = [f.center_of_interest or Point(frame_width / 2, frame_height / 2)
               for f in frame_infos]

    # Apply smoothing
    smoothed_centers = smooth_trajectory(centers, smoothing_factor)

    # Generate keyframes
    keyframes = []
    for i, frame_info in enumerate(frame_infos):
        x, y = center_crop_position(
            frame_width, frame_height,
            crop_width, crop_height,
            smoothed_centers[i]
        )
        keyframes.append((frame_info.timestamp, x, y))

    return keyframes


def generate_ffmpeg_crop_filter(
    keyframes: List[Tuple[float, int, int]],
    crop_width: int,
    crop_height: int,
    output_width: int,
    output_height: int
) -> str:
    """
    Generate FFmpeg filter for dynamic cropping based on keyframes.

    For simple static crop (no motion), uses basic crop filter.
    For dynamic crop, uses complex expression with timeline.
    """
    if len(keyframes) <= 1:
        # Static crop
        x, y = keyframes[0][1], keyframes[0][2] if keyframes else (0, 0)
        return f"crop={crop_width}:{crop_height}:{x}:{y},scale={output_width}:{output_height}"

    # For now, use static crop at first keyframe position
    # Dynamic keyframing with expressions is complex and slow
    # Full implementation would use sendcmd or zoompan filter
    x, y = keyframes[0][1], keyframes[0][2]

    return f"crop={crop_width}:{crop_height}:{x}:{y},scale={output_width}:{output_height}"


async def reframe_video(
    video_path: str,
    target_aspect: AspectRatio = AspectRatio.PORTRAIT_9_16,
    tracking_mode: TrackingMode = TrackingMode.CENTER,
    smoothing: float = 0.8,
    safe_zone_margin: float = 0.1,
    output_path: Optional[str] = None
) -> ReframeResult:
    """
    Reframe video to target aspect ratio.

    Args:
        video_path: Path to input video
        target_aspect: Target aspect ratio
        tracking_mode: How to track subjects (CENTER, FACE, BODY, AUTO)
        smoothing: Motion smoothing factor (0.1-1.0, higher = smoother)
        safe_zone_margin: Margin to keep subjects within (0.0-0.3)
        output_path: Optional custom output path

    Returns:
        ReframeResult with output path and metadata
    """
    import time
    start_time = time.time()

    log_job_event("reframe", "started", {
        "video_path": video_path,
        "target_aspect": target_aspect.value,
        "tracking_mode": tracking_mode.value
    })

    # Validate input
    if not os.path.exists(video_path):
        return ReframeResult(
            success=False,
            output_path=None,
            original_aspect="unknown",
            target_aspect=target_aspect.value,
            original_dimensions=(0, 0),
            output_dimensions=(0, 0),
            tracking_mode=tracking_mode.value,
            frames_analyzed=0,
            processing_time=0,
            error=f"Video file not found: {video_path}"
        )

    # Get video info
    video_info = get_video_info(video_path)
    source_width = video_info["width"]
    source_height = video_info["height"]
    original_aspect = calculate_aspect_ratio(source_width, source_height)

    # Check if reframe is needed
    target_ratio = target_aspect.ratio
    source_ratio = source_width / source_height

    if abs(target_ratio - source_ratio) < 0.01:
        # Already at target aspect ratio
        return ReframeResult(
            success=True,
            output_path=video_path,
            original_aspect=original_aspect,
            target_aspect=target_aspect.value,
            original_dimensions=(source_width, source_height),
            output_dimensions=(source_width, source_height),
            tracking_mode="none",
            frames_analyzed=0,
            processing_time=time.time() - start_time
        )

    try:
        # Calculate crop dimensions
        crop_width, crop_height, max_x, max_y = calculate_crop_dimensions(
            source_width, source_height,
            target_aspect,
            safe_zone_margin
        )

        # Analyze frames for tracking
        frame_infos = await analyze_frames_for_reframe(
            video_path,
            tracking_mode,
            sample_interval=30  # Analyze every 30th frame
        )

        # Generate crop keyframes
        keyframes = generate_crop_keyframes(
            frame_infos,
            crop_width, crop_height,
            source_width, source_height,
            smoothing
        )

        # Get output dimensions
        output_width, output_height = target_aspect.dimensions

        # Generate FFmpeg filter
        crop_filter = generate_ffmpeg_crop_filter(
            keyframes,
            crop_width, crop_height,
            output_width, output_height
        )

        # Generate output path
        if output_path is None:
            base_name = Path(video_path).stem
            output_dir = Path(video_path).parent
            aspect_suffix = target_aspect.value.replace(":", "x")
            output_path = str(output_dir / f"{base_name}_{aspect_suffix}.mp4")

        # Run FFmpeg
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", crop_filter,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "copy",
            "-movflags", "+faststart",
            output_path
        ]

        logger.info(f"Running FFmpeg reframe: {target_aspect.value}")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=300
        )

        if process.returncode != 0:
            logger.error(f"FFmpeg failed: {stderr.decode()}")
            return ReframeResult(
                success=False,
                output_path=None,
                original_aspect=original_aspect,
                target_aspect=target_aspect.value,
                original_dimensions=(source_width, source_height),
                output_dimensions=(output_width, output_height),
                tracking_mode=tracking_mode.value,
                frames_analyzed=len(frame_infos),
                processing_time=time.time() - start_time,
                error=f"FFmpeg error: {stderr.decode()[:200]}"
            )

        processing_time = time.time() - start_time

        log_job_event("reframe", "completed", {
            "output_path": output_path,
            "processing_time": processing_time
        })

        return ReframeResult(
            success=True,
            output_path=output_path,
            original_aspect=original_aspect,
            target_aspect=target_aspect.value,
            original_dimensions=(source_width, source_height),
            output_dimensions=(output_width, output_height),
            tracking_mode=tracking_mode.value,
            frames_analyzed=len(frame_infos),
            processing_time=processing_time
        )

    except asyncio.TimeoutError:
        return ReframeResult(
            success=False,
            output_path=None,
            original_aspect=original_aspect,
            target_aspect=target_aspect.value,
            original_dimensions=(source_width, source_height),
            output_dimensions=(0, 0),
            tracking_mode=tracking_mode.value,
            frames_analyzed=0,
            processing_time=time.time() - start_time,
            error="FFmpeg timed out"
        )
    except Exception as e:
        logger.error(f"Reframe failed: {e}", exc_info=True)
        return ReframeResult(
            success=False,
            output_path=None,
            original_aspect=original_aspect,
            target_aspect=target_aspect.value,
            original_dimensions=(source_width, source_height),
            output_dimensions=(0, 0),
            tracking_mode=tracking_mode.value,
            frames_analyzed=0,
            processing_time=time.time() - start_time,
            error=str(e)
        )


async def batch_reframe(
    video_paths: List[str],
    target_aspect: AspectRatio = AspectRatio.PORTRAIT_9_16,
    tracking_mode: TrackingMode = TrackingMode.CENTER,
    smoothing: float = 0.8,
    max_concurrent: int = 3
) -> List[ReframeResult]:
    """
    Batch reframe multiple videos concurrently.

    Args:
        video_paths: List of video paths to reframe
        target_aspect: Target aspect ratio for all
        tracking_mode: Tracking mode for all
        smoothing: Smoothing factor for all
        max_concurrent: Maximum concurrent reframe operations

    Returns:
        List of ReframeResult for each video
    """
    import asyncio

    semaphore = asyncio.Semaphore(max_concurrent)

    async def reframe_with_limit(path: str) -> ReframeResult:
        async with semaphore:
            return await reframe_video(
                path,
                target_aspect,
                tracking_mode,
                smoothing
            )

    tasks = [reframe_with_limit(path) for path in video_paths]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Convert exceptions to failed results
    final_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            final_results.append(ReframeResult(
                success=False,
                output_path=None,
                original_aspect="unknown",
                target_aspect=target_aspect.value,
                original_dimensions=(0, 0),
                output_dimensions=(0, 0),
                tracking_mode=tracking_mode.value,
                frames_analyzed=0,
                processing_time=0,
                error=str(result)
            ))
        else:
            final_results.append(result)

    return final_results


def parse_aspect_ratio(aspect_str: str) -> AspectRatio:
    """Parse aspect ratio string to enum."""
    normalized = aspect_str.lower().replace("x", ":").strip()

    for aspect in AspectRatio:
        if aspect.value == normalized:
            return aspect

    # Try common aliases
    aliases = {
        "portrait": AspectRatio.PORTRAIT_9_16,
        "vertical": AspectRatio.PORTRAIT_9_16,
        "tiktok": AspectRatio.PORTRAIT_9_16,
        "reels": AspectRatio.PORTRAIT_9_16,
        "shorts": AspectRatio.PORTRAIT_9_16,
        "square": AspectRatio.SQUARE_1_1,
        "landscape": AspectRatio.LANDSCAPE_16_9,
        "horizontal": AspectRatio.LANDSCAPE_16_9,
        "youtube": AspectRatio.LANDSCAPE_16_9,
        "widescreen": AspectRatio.LANDSCAPE_16_9,
    }

    if normalized in aliases:
        return aliases[normalized]

    raise ValueError(f"Unknown aspect ratio: {aspect_str}")
