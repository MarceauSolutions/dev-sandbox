"""
Multi-Platform Export Engine for Fitness Influencer AI

Optimized export settings for TikTok, Instagram, YouTube Shorts, LinkedIn, Twitter.
Handles resolution, bitrate, codec, container, and duration limits per platform.

Story 013: Build multi-platform export presets

Usage:
    from backend.platform_exporter import export_for_platform, Platform

    # Export for TikTok
    result = await export_for_platform(
        video_path="/path/to/video.mp4",
        platform=Platform.TIKTOK
    )

    print(f"Exported: {result.output_path}")
"""

import os
import subprocess
import asyncio
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from enum import Enum
import tempfile

from backend.logging_config import get_logger, log_job_event

logger = get_logger(__name__)


class Platform(Enum):
    """Supported social media platforms."""
    TIKTOK = "tiktok"
    INSTAGRAM_REELS = "instagram_reels"
    INSTAGRAM_FEED = "instagram_feed"
    INSTAGRAM_STORY = "instagram_story"
    YOUTUBE_SHORTS = "youtube_shorts"
    YOUTUBE_LONG = "youtube_long"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    FACEBOOK_REELS = "facebook_reels"


@dataclass
class PlatformSpec:
    """Specification for a platform's video requirements."""
    name: str
    width: int
    height: int
    aspect_ratio: str
    max_duration: int  # seconds
    min_duration: int  # seconds
    fps: int
    video_codec: str
    video_bitrate: str  # e.g., "4M" for 4 Mbps
    video_bitrate_max: str  # max bitrate for VBR
    audio_codec: str
    audio_bitrate: str
    audio_sample_rate: int
    container: str  # mp4, mov
    max_file_size_mb: int
    notes: str = ""


# Platform specifications based on 2024 requirements
PLATFORM_SPECS: Dict[Platform, PlatformSpec] = {
    Platform.TIKTOK: PlatformSpec(
        name="TikTok",
        width=1080,
        height=1920,
        aspect_ratio="9:16",
        max_duration=600,  # 10 minutes
        min_duration=1,
        fps=30,
        video_codec="libx264",
        video_bitrate="3M",
        video_bitrate_max="4M",
        audio_codec="aac",
        audio_bitrate="128k",
        audio_sample_rate=44100,
        container="mp4",
        max_file_size_mb=287,
        notes="Optimal: 15-60 seconds for discovery"
    ),
    Platform.INSTAGRAM_REELS: PlatformSpec(
        name="Instagram Reels",
        width=1080,
        height=1920,
        aspect_ratio="9:16",
        max_duration=90,
        min_duration=3,
        fps=30,
        video_codec="libx264",
        video_bitrate="4M",
        video_bitrate_max="4.5M",
        audio_codec="aac",
        audio_bitrate="128k",
        audio_sample_rate=44100,
        container="mp4",
        max_file_size_mb=250,
        notes="15-30 seconds performs best"
    ),
    Platform.INSTAGRAM_FEED: PlatformSpec(
        name="Instagram Feed",
        width=1080,
        height=1350,
        aspect_ratio="4:5",
        max_duration=60,
        min_duration=3,
        fps=30,
        video_codec="libx264",
        video_bitrate="3.5M",
        video_bitrate_max="4M",
        audio_codec="aac",
        audio_bitrate="128k",
        audio_sample_rate=44100,
        container="mp4",
        max_file_size_mb=250,
        notes="Square 1:1 also supported"
    ),
    Platform.INSTAGRAM_STORY: PlatformSpec(
        name="Instagram Story",
        width=1080,
        height=1920,
        aspect_ratio="9:16",
        max_duration=60,
        min_duration=1,
        fps=30,
        video_codec="libx264",
        video_bitrate="3M",
        video_bitrate_max="4M",
        audio_codec="aac",
        audio_bitrate="128k",
        audio_sample_rate=44100,
        container="mp4",
        max_file_size_mb=250,
        notes="15-second segments auto-split"
    ),
    Platform.YOUTUBE_SHORTS: PlatformSpec(
        name="YouTube Shorts",
        width=1080,
        height=1920,
        aspect_ratio="9:16",
        max_duration=60,
        min_duration=15,
        fps=60,
        video_codec="libx264",
        video_bitrate="10M",
        video_bitrate_max="15M",
        audio_codec="aac",
        audio_bitrate="192k",
        audio_sample_rate=48000,
        container="mp4",
        max_file_size_mb=500,
        notes="Higher bitrate for YouTube quality"
    ),
    Platform.YOUTUBE_LONG: PlatformSpec(
        name="YouTube Long-Form",
        width=1920,
        height=1080,
        aspect_ratio="16:9",
        max_duration=43200,  # 12 hours
        min_duration=30,
        fps=60,
        video_codec="libx264",
        video_bitrate="12M",
        video_bitrate_max="20M",
        audio_codec="aac",
        audio_bitrate="256k",
        audio_sample_rate=48000,
        container="mp4",
        max_file_size_mb=128000,  # 128 GB
        notes="Use for tutorials, vlogs, long content"
    ),
    Platform.LINKEDIN: PlatformSpec(
        name="LinkedIn",
        width=1080,
        height=1920,
        aspect_ratio="9:16",
        max_duration=600,  # 10 minutes native, 30 min via upload
        min_duration=3,
        fps=30,
        video_codec="libx264",
        video_bitrate="5M",
        video_bitrate_max="5M",
        audio_codec="aac",
        audio_bitrate="128k",
        audio_sample_rate=44100,
        container="mp4",
        max_file_size_mb=200,
        notes="Professional tone, 30-60 seconds optimal"
    ),
    Platform.TWITTER: PlatformSpec(
        name="Twitter/X",
        width=1280,
        height=720,
        aspect_ratio="16:9",
        max_duration=140,
        min_duration=0.5,
        fps=30,
        video_codec="libx264",
        video_bitrate="5M",
        video_bitrate_max="5M",
        audio_codec="aac",
        audio_bitrate="128k",
        audio_sample_rate=44100,
        container="mp4",
        max_file_size_mb=512,
        notes="Landscape preferred, 30-45 seconds optimal"
    ),
    Platform.FACEBOOK_REELS: PlatformSpec(
        name="Facebook Reels",
        width=1080,
        height=1920,
        aspect_ratio="9:16",
        max_duration=90,
        min_duration=3,
        fps=30,
        video_codec="libx264",
        video_bitrate="4M",
        video_bitrate_max="4.5M",
        audio_codec="aac",
        audio_bitrate="128k",
        audio_sample_rate=44100,
        container="mp4",
        max_file_size_mb=250,
        notes="Similar to Instagram Reels specs"
    ),
}


@dataclass
class ExportWarning:
    """Warning about export compatibility."""
    code: str
    message: str
    severity: str  # "info", "warning", "error"


@dataclass
class ExportResult:
    """Result of platform export operation."""
    success: bool
    output_path: Optional[str]
    platform: str
    original_duration: float
    final_duration: float
    original_dimensions: Tuple[int, int]
    output_dimensions: Tuple[int, int]
    file_size_mb: float
    warnings: List[ExportWarning]
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output_path": self.output_path,
            "platform": self.platform,
            "original_duration": round(self.original_duration, 2),
            "final_duration": round(self.final_duration, 2),
            "original_dimensions": self.original_dimensions,
            "output_dimensions": self.output_dimensions,
            "file_size_mb": round(self.file_size_mb, 2),
            "warnings": [{"code": w.code, "message": w.message, "severity": w.severity} for w in self.warnings],
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
                "-show_entries", "format=duration,size",
                "-of", "json",
                video_path
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        data = json.loads(result.stdout)
        stream = data.get("streams", [{}])[0]
        format_data = data.get("format", {})

        # Parse frame rate
        fps_str = stream.get("r_frame_rate", "30/1")
        fps_parts = fps_str.split("/")
        fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 30.0

        # Get duration from stream or format
        duration = float(stream.get("duration", 0))
        if duration == 0:
            duration = float(format_data.get("duration", 0))

        # Get file size
        size_bytes = int(format_data.get("size", 0))
        size_mb = size_bytes / (1024 * 1024)

        return {
            "width": int(stream.get("width", 1920)),
            "height": int(stream.get("height", 1080)),
            "fps": fps,
            "duration": duration,
            "size_mb": size_mb
        }
    except Exception as e:
        logger.error(f"Failed to get video info: {e}")
        return {"width": 1920, "height": 1080, "fps": 30.0, "duration": 0, "size_mb": 0}


def validate_for_platform(
    video_info: Dict[str, Any],
    platform: Platform
) -> List[ExportWarning]:
    """
    Validate video against platform requirements.

    Returns list of warnings/errors for incompatibilities.
    """
    spec = PLATFORM_SPECS[platform]
    warnings = []

    duration = video_info.get("duration", 0)
    width = video_info.get("width", 0)
    height = video_info.get("height", 0)

    # Duration checks
    if duration > spec.max_duration:
        warnings.append(ExportWarning(
            code="DURATION_EXCEEDED",
            message=f"Video duration ({duration:.1f}s) exceeds {platform.value} limit ({spec.max_duration}s). Will be trimmed.",
            severity="warning"
        ))
    elif duration < spec.min_duration:
        warnings.append(ExportWarning(
            code="DURATION_TOO_SHORT",
            message=f"Video duration ({duration:.1f}s) is below {platform.value} minimum ({spec.min_duration}s).",
            severity="error"
        ))

    # Aspect ratio check
    source_ratio = width / height if height > 0 else 1.0
    target_parts = spec.aspect_ratio.split(":")
    target_ratio = float(target_parts[0]) / float(target_parts[1])

    if abs(source_ratio - target_ratio) > 0.1:
        warnings.append(ExportWarning(
            code="ASPECT_RATIO_MISMATCH",
            message=f"Source aspect ratio ({width}x{height}) differs from {spec.aspect_ratio}. Video will be cropped/letterboxed.",
            severity="info"
        ))

    # Resolution check
    if width < spec.width or height < spec.height:
        warnings.append(ExportWarning(
            code="LOW_RESOLUTION",
            message=f"Source resolution ({width}x{height}) is lower than target ({spec.width}x{spec.height}). May appear pixelated.",
            severity="warning"
        ))

    return warnings


def build_ffmpeg_command(
    input_path: str,
    output_path: str,
    spec: PlatformSpec,
    source_info: Dict[str, Any],
    trim_duration: Optional[float] = None
) -> List[str]:
    """
    Build FFmpeg command for platform export.

    Returns command as list of arguments.
    """
    source_width = source_info.get("width", 1920)
    source_height = source_info.get("height", 1080)

    # Calculate scaling/cropping to match target aspect ratio
    source_ratio = source_width / source_height
    target_ratio = spec.width / spec.height

    if abs(source_ratio - target_ratio) < 0.01:
        # Same aspect ratio - simple scale
        vf_filters = [f"scale={spec.width}:{spec.height}"]
    elif source_ratio > target_ratio:
        # Source is wider - crop width
        new_width = int(source_height * target_ratio)
        crop_x = (source_width - new_width) // 2
        vf_filters = [
            f"crop={new_width}:{source_height}:{crop_x}:0",
            f"scale={spec.width}:{spec.height}"
        ]
    else:
        # Source is taller - crop height
        new_height = int(source_width / target_ratio)
        crop_y = (source_height - new_height) // 2
        vf_filters = [
            f"crop={source_width}:{new_height}:0:{crop_y}",
            f"scale={spec.width}:{spec.height}"
        ]

    # Add FPS filter if needed
    source_fps = source_info.get("fps", 30)
    if source_fps != spec.fps:
        vf_filters.append(f"fps={spec.fps}")

    vf_string = ",".join(vf_filters)

    # Build command
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
    ]

    # Add duration trim if specified
    if trim_duration:
        cmd.extend(["-t", str(trim_duration)])

    cmd.extend([
        "-vf", vf_string,
        "-c:v", spec.video_codec,
        "-b:v", spec.video_bitrate,
        "-maxrate", spec.video_bitrate_max,
        "-bufsize", spec.video_bitrate,  # Buffer = bitrate
        "-profile:v", "high",
        "-level", "4.0",
        "-pix_fmt", "yuv420p",
        "-c:a", spec.audio_codec,
        "-b:a", spec.audio_bitrate,
        "-ar", str(spec.audio_sample_rate),
        "-ac", "2",  # Stereo
        "-movflags", "+faststart",
        output_path
    ])

    return cmd


async def export_for_platform(
    video_path: str,
    platform: Platform,
    output_path: Optional[str] = None,
    enforce_duration: bool = True
) -> ExportResult:
    """
    Export video optimized for a specific platform.

    Args:
        video_path: Path to source video
        platform: Target platform
        output_path: Optional custom output path
        enforce_duration: If True, trim video to platform's max duration

    Returns:
        ExportResult with output path and metadata
    """
    log_job_event("platform_export", "started", {
        "video_path": video_path,
        "platform": platform.value
    })

    # Validate input
    if not os.path.exists(video_path):
        return ExportResult(
            success=False,
            output_path=None,
            platform=platform.value,
            original_duration=0,
            final_duration=0,
            original_dimensions=(0, 0),
            output_dimensions=(0, 0),
            file_size_mb=0,
            warnings=[],
            error=f"Video file not found: {video_path}"
        )

    spec = PLATFORM_SPECS[platform]
    source_info = get_video_info(video_path)

    # Validate against platform requirements
    warnings = validate_for_platform(source_info, platform)

    # Check for blocking errors
    blocking_errors = [w for w in warnings if w.severity == "error"]
    if blocking_errors:
        return ExportResult(
            success=False,
            output_path=None,
            platform=platform.value,
            original_duration=source_info.get("duration", 0),
            final_duration=0,
            original_dimensions=(source_info["width"], source_info["height"]),
            output_dimensions=(spec.width, spec.height),
            file_size_mb=0,
            warnings=warnings,
            error=blocking_errors[0].message
        )

    # Generate output path
    if output_path is None:
        base_name = Path(video_path).stem
        output_dir = Path(video_path).parent
        output_path = str(output_dir / f"{base_name}_{platform.value}.mp4")

    # Calculate trim duration if needed
    trim_duration = None
    if enforce_duration and source_info.get("duration", 0) > spec.max_duration:
        trim_duration = spec.max_duration

    try:
        # Build and run FFmpeg command
        cmd = build_ffmpeg_command(
            video_path, output_path, spec, source_info, trim_duration
        )

        logger.info(f"Exporting for {platform.value}: {Path(video_path).name}")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=600  # 10 minute timeout
        )

        if process.returncode != 0:
            logger.error(f"FFmpeg failed: {stderr.decode()}")
            return ExportResult(
                success=False,
                output_path=None,
                platform=platform.value,
                original_duration=source_info.get("duration", 0),
                final_duration=0,
                original_dimensions=(source_info["width"], source_info["height"]),
                output_dimensions=(spec.width, spec.height),
                file_size_mb=0,
                warnings=warnings,
                error=f"FFmpeg error: {stderr.decode()[:200]}"
            )

        # Get output file info
        output_info = get_video_info(output_path)

        log_job_event("platform_export", "completed", {
            "platform": platform.value,
            "output_path": output_path,
            "file_size_mb": output_info.get("size_mb", 0)
        })

        return ExportResult(
            success=True,
            output_path=output_path,
            platform=platform.value,
            original_duration=source_info.get("duration", 0),
            final_duration=output_info.get("duration", 0),
            original_dimensions=(source_info["width"], source_info["height"]),
            output_dimensions=(output_info["width"], output_info["height"]),
            file_size_mb=output_info.get("size_mb", 0),
            warnings=warnings
        )

    except asyncio.TimeoutError:
        return ExportResult(
            success=False,
            output_path=None,
            platform=platform.value,
            original_duration=source_info.get("duration", 0),
            final_duration=0,
            original_dimensions=(source_info["width"], source_info["height"]),
            output_dimensions=(spec.width, spec.height),
            file_size_mb=0,
            warnings=warnings,
            error="Export timed out"
        )
    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        return ExportResult(
            success=False,
            output_path=None,
            platform=platform.value,
            original_duration=source_info.get("duration", 0),
            final_duration=0,
            original_dimensions=(source_info["width"], source_info["height"]),
            output_dimensions=(spec.width, spec.height),
            file_size_mb=0,
            warnings=warnings,
            error=str(e)
        )


async def export_for_multiple_platforms(
    video_path: str,
    platforms: List[Platform],
    max_concurrent: int = 3
) -> Dict[Platform, ExportResult]:
    """
    Export video to multiple platforms concurrently.

    Args:
        video_path: Path to source video
        platforms: List of target platforms
        max_concurrent: Maximum concurrent exports

    Returns:
        Dict mapping platform to ExportResult
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def export_with_limit(platform: Platform) -> Tuple[Platform, ExportResult]:
        async with semaphore:
            result = await export_for_platform(video_path, platform)
            return platform, result

    tasks = [export_with_limit(p) for p in platforms]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output = {}
    for result in results:
        if isinstance(result, Exception):
            continue
        platform, export_result = result
        output[platform] = export_result

    return output


def get_platform_spec(platform: Platform) -> Dict[str, Any]:
    """Get platform specification as dictionary."""
    spec = PLATFORM_SPECS[platform]
    return {
        "name": spec.name,
        "dimensions": {"width": spec.width, "height": spec.height},
        "aspect_ratio": spec.aspect_ratio,
        "duration_limits": {
            "min": spec.min_duration,
            "max": spec.max_duration
        },
        "fps": spec.fps,
        "video": {
            "codec": spec.video_codec,
            "bitrate": spec.video_bitrate,
            "bitrate_max": spec.video_bitrate_max
        },
        "audio": {
            "codec": spec.audio_codec,
            "bitrate": spec.audio_bitrate,
            "sample_rate": spec.audio_sample_rate
        },
        "max_file_size_mb": spec.max_file_size_mb,
        "notes": spec.notes
    }


def list_platforms() -> List[Dict[str, Any]]:
    """List all supported platforms with their specs."""
    return [
        {"platform": p.value, **get_platform_spec(p)}
        for p in Platform
    ]


def parse_platform(platform_str: str) -> Platform:
    """Parse platform string to enum."""
    normalized = platform_str.lower().replace("-", "_").replace(" ", "_")

    # Direct match
    for p in Platform:
        if p.value == normalized:
            return p

    # Aliases
    aliases = {
        "tiktok": Platform.TIKTOK,
        "tt": Platform.TIKTOK,
        "instagram": Platform.INSTAGRAM_REELS,
        "ig": Platform.INSTAGRAM_REELS,
        "ig_reels": Platform.INSTAGRAM_REELS,
        "reels": Platform.INSTAGRAM_REELS,
        "ig_feed": Platform.INSTAGRAM_FEED,
        "ig_story": Platform.INSTAGRAM_STORY,
        "stories": Platform.INSTAGRAM_STORY,
        "youtube": Platform.YOUTUBE_SHORTS,
        "yt": Platform.YOUTUBE_SHORTS,
        "yt_shorts": Platform.YOUTUBE_SHORTS,
        "shorts": Platform.YOUTUBE_SHORTS,
        "youtube_long": Platform.YOUTUBE_LONG,
        "yt_long": Platform.YOUTUBE_LONG,
        "linkedin": Platform.LINKEDIN,
        "li": Platform.LINKEDIN,
        "twitter": Platform.TWITTER,
        "x": Platform.TWITTER,
        "facebook": Platform.FACEBOOK_REELS,
        "fb": Platform.FACEBOOK_REELS,
        "fb_reels": Platform.FACEBOOK_REELS,
    }

    if normalized in aliases:
        return aliases[normalized]

    raise ValueError(f"Unknown platform: {platform_str}")
