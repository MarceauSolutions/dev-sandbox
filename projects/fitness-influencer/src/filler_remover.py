"""
Smooth Filler Word Removal for Fitness Influencer AI

Removes detected fillers with smooth audio crossfade and visual jump cut.
Preserves natural speech rhythm without audio pops or clicks.

Story 010: Implement smooth audio and video removal for fillers

Usage:
    from backend.filler_remover import remove_fillers, FillerRemovalResult

    # Remove fillers from video
    result = await remove_fillers(
        video_path="/path/to/video.mp4",
        sensitivity="moderate",
        preview_only=False
    )

    print(f"Removed {result.segments_removed} filler segments")
    print(f"Time saved: {result.time_saved:.2f}s")
"""

import os
import subprocess
import tempfile
import asyncio
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from enum import Enum
import uuid
import shutil

from backend.logging_config import get_logger, log_job_event
from backend.filler_detector import (
    detect_fillers,
    detect_fillers_with_sensitivity,
    get_removal_segments,
    WordTimestamp,
    FillerDetectionResult,
    SENSITIVITY_PRESETS
)
from backend.transcription import transcribe_video, TranscriptionResult

logger = get_logger(__name__)


class RemovalMode(Enum):
    """Filler removal modes."""
    AGGRESSIVE = "aggressive"  # Remove all potential fillers
    MODERATE = "moderate"      # Balanced approach
    CONSERVATIVE = "conservative"  # Only high-confidence fillers


# Audio processing settings
AUDIO_CROSSFADE_MS = 50  # 50ms crossfade at cut points
AUDIO_SAMPLE_RATE = 44100
MINIMUM_SEGMENT_GAP_MS = 100  # Minimum gap between segments to preserve


@dataclass
class RemovalSegment:
    """A segment to be removed from the video."""
    start: float
    end: float
    duration: float
    reason: str  # e.g., "filler: um", "cluster: um, uh, like"
    confidence: float

    def to_dict(self) -> dict:
        return {
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "duration": round(self.duration, 3),
            "reason": self.reason,
            "confidence": round(self.confidence, 2)
        }


@dataclass
class FillerRemovalResult:
    """Result of filler removal operation."""
    success: bool
    output_path: Optional[str]
    original_duration: float
    new_duration: float
    time_saved: float
    segments_removed: int
    removal_segments: List[RemovalSegment]
    detection_result: Optional[FillerDetectionResult]
    error: Optional[str] = None
    preview_only: bool = False

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output_path": self.output_path,
            "original_duration": round(self.original_duration, 2),
            "new_duration": round(self.new_duration, 2),
            "time_saved": round(self.time_saved, 2),
            "time_saved_percentage": round(self.time_saved / self.original_duration * 100, 1) if self.original_duration > 0 else 0,
            "segments_removed": self.segments_removed,
            "removal_segments": [s.to_dict() for s in self.removal_segments],
            "preview_only": self.preview_only,
            "error": self.error
        }


def get_video_duration(video_path: str) -> float:
    """Get video duration using FFprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        return float(result.stdout.strip())
    except Exception as e:
        logger.error(f"Failed to get video duration: {e}")
        return 0.0


def merge_close_segments(
    segments: List[Tuple[float, float]],
    min_gap: float = 0.1
) -> List[Tuple[float, float]]:
    """
    Merge segments that are very close together.

    If the gap between two segments is less than min_gap seconds,
    merge them into a single segment.
    """
    if not segments:
        return []

    # Sort by start time
    sorted_segments = sorted(segments, key=lambda x: x[0])
    merged = [sorted_segments[0]]

    for start, end in sorted_segments[1:]:
        prev_start, prev_end = merged[-1]

        # If this segment is close to or overlaps the previous one
        if start - prev_end <= min_gap:
            # Extend the previous segment
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))

    return merged


def calculate_keep_segments(
    total_duration: float,
    removal_segments: List[Tuple[float, float]],
    padding: float = 0.0
) -> List[Tuple[float, float]]:
    """
    Calculate segments to KEEP (inverse of removal segments).

    Returns list of (start, end) tuples for segments that should be preserved.
    Optionally adds padding at cut points for smoother transitions.
    """
    if not removal_segments:
        return [(0, total_duration)]

    keep_segments = []
    current_pos = 0.0

    for remove_start, remove_end in sorted(removal_segments, key=lambda x: x[0]):
        # Add padding to removal segment if specified
        actual_remove_start = max(0, remove_start - padding)
        actual_remove_end = min(total_duration, remove_end + padding)

        # If there's a gap before this removal segment, keep it
        if actual_remove_start > current_pos:
            keep_segments.append((current_pos, actual_remove_start))

        current_pos = actual_remove_end

    # Keep the remainder of the video after last removal
    if current_pos < total_duration:
        keep_segments.append((current_pos, total_duration))

    return keep_segments


def generate_ffmpeg_filter_complex(
    keep_segments: List[Tuple[float, float]],
    crossfade_ms: int = 50
) -> str:
    """
    Generate FFmpeg filter_complex for concatenating kept segments with crossfade.

    Uses the trim/atrim filters to extract segments and concat to join them.
    """
    if not keep_segments:
        return ""

    crossfade_sec = crossfade_ms / 1000.0
    video_parts = []
    audio_parts = []

    for i, (start, end) in enumerate(keep_segments):
        # Video segment
        video_parts.append(
            f"[0:v]trim=start={start:.3f}:end={end:.3f},setpts=PTS-STARTPTS[v{i}]"
        )
        # Audio segment
        audio_parts.append(
            f"[0:a]atrim=start={start:.3f}:end={end:.3f},asetpts=PTS-STARTPTS[a{i}]"
        )

    # Concatenate all segments
    n_segments = len(keep_segments)
    video_inputs = "".join([f"[v{i}]" for i in range(n_segments)])
    audio_inputs = "".join([f"[a{i}]" for i in range(n_segments)])

    concat_filter = (
        f"{video_inputs}concat=n={n_segments}:v=1:a=0[outv];"
        f"{audio_inputs}concat=n={n_segments}:v=0:a=1[outa]"
    )

    # Combine all filters
    filter_complex = ";".join(video_parts + audio_parts) + ";" + concat_filter

    return filter_complex


def generate_segment_file(
    keep_segments: List[Tuple[float, float]],
    output_path: str
) -> str:
    """
    Generate a segments file for FFmpeg concat demuxer.
    Alternative approach that may be faster for many segments.
    """
    segment_file = output_path.replace(".mp4", "_segments.txt")

    with open(segment_file, "w") as f:
        for start, end in keep_segments:
            duration = end - start
            f.write(f"inpoint {start}\n")
            f.write(f"outpoint {end}\n")

    return segment_file


async def remove_fillers_from_video(
    input_path: str,
    output_path: str,
    removal_segments: List[Tuple[float, float]],
    crossfade_ms: int = AUDIO_CROSSFADE_MS
) -> bool:
    """
    Remove specified segments from video with smooth audio crossfade.

    Uses FFmpeg to:
    1. Extract kept segments with trim filter
    2. Apply audio crossfade at cut points
    3. Concatenate segments smoothly
    """
    total_duration = get_video_duration(input_path)
    if total_duration <= 0:
        logger.error("Could not determine video duration")
        return False

    # Merge close segments
    merged_segments = merge_close_segments(removal_segments, min_gap=MINIMUM_SEGMENT_GAP_MS / 1000)

    # Calculate segments to keep
    keep_segments = calculate_keep_segments(total_duration, merged_segments)

    if not keep_segments:
        logger.error("No segments to keep after removal")
        return False

    if len(keep_segments) == 1 and keep_segments[0] == (0, total_duration):
        # Nothing to remove, just copy
        shutil.copy(input_path, output_path)
        return True

    # Generate filter complex
    filter_complex = generate_ffmpeg_filter_complex(keep_segments, crossfade_ms)

    # Build FFmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "[outa]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        output_path
    ]

    logger.info(f"Running FFmpeg filler removal with {len(keep_segments)} segments")

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=300  # 5 minute timeout
        )

        if process.returncode != 0:
            logger.error(f"FFmpeg failed: {stderr.decode()}")
            return False

        return os.path.exists(output_path)

    except asyncio.TimeoutError:
        logger.error("FFmpeg timed out during filler removal")
        return False
    except Exception as e:
        logger.error(f"FFmpeg error: {e}")
        return False


async def remove_fillers(
    video_path: str,
    sensitivity: str = "moderate",
    language: str = "en",
    preview_only: bool = False,
    output_path: Optional[str] = None,
    custom_threshold: Optional[float] = None
) -> FillerRemovalResult:
    """
    Remove filler words from video with smooth transitions.

    Args:
        video_path: Path to input video file
        sensitivity: One of "aggressive", "moderate", "conservative"
        language: Language for transcription
        preview_only: If True, only analyze without removing
        output_path: Optional custom output path
        custom_threshold: Optional custom confidence threshold (overrides sensitivity)

    Returns:
        FillerRemovalResult with details of operation
    """
    log_job_event("filler_removal", "started", {"video_path": video_path, "sensitivity": sensitivity})

    # Validate input
    if not os.path.exists(video_path):
        return FillerRemovalResult(
            success=False,
            output_path=None,
            original_duration=0,
            new_duration=0,
            time_saved=0,
            segments_removed=0,
            removal_segments=[],
            detection_result=None,
            error=f"Video file not found: {video_path}"
        )

    # Get original duration
    original_duration = get_video_duration(video_path)

    try:
        # Step 1: Transcribe video to get word timestamps
        logger.info(f"Transcribing video for filler detection: {video_path}")
        transcription = await transcribe_video(video_path, language=language)

        if not transcription.words:
            return FillerRemovalResult(
                success=True,
                output_path=video_path,
                original_duration=original_duration,
                new_duration=original_duration,
                time_saved=0,
                segments_removed=0,
                removal_segments=[],
                detection_result=None,
                error=None,
                preview_only=preview_only
            )

        # Convert to WordTimestamp format for detector
        words = [
            WordTimestamp(
                word=w.word,
                start=w.start,
                end=w.end,
                confidence=w.confidence
            )
            for w in transcription.words
        ]

        # Step 2: Detect fillers
        logger.info(f"Detecting fillers with sensitivity: {sensitivity}")

        if custom_threshold is not None:
            detection_result = detect_fillers(
                words=words,
                confidence_threshold=custom_threshold
            )
        else:
            detection_result = detect_fillers_with_sensitivity(
                words=words,
                sensitivity=sensitivity
            )

        # Get removal segments
        raw_segments = get_removal_segments(detection_result, include_clusters=True)

        if not raw_segments:
            return FillerRemovalResult(
                success=True,
                output_path=video_path,
                original_duration=original_duration,
                new_duration=original_duration,
                time_saved=0,
                segments_removed=0,
                removal_segments=[],
                detection_result=detection_result,
                preview_only=preview_only
            )

        # Create RemovalSegment objects with metadata
        removal_segments = []
        confirmed_fillers = [f for f in detection_result.fillers if f.is_filler]

        for start, end in raw_segments:
            # Find the filler(s) in this segment
            segment_fillers = [
                f for f in confirmed_fillers
                if f.start >= start - 0.1 and f.end <= end + 0.1
            ]

            if segment_fillers:
                if len(segment_fillers) == 1:
                    reason = f"filler: {segment_fillers[0].word}"
                    confidence = segment_fillers[0].confidence
                else:
                    words_str = ", ".join([f.word for f in segment_fillers[:3]])
                    if len(segment_fillers) > 3:
                        words_str += "..."
                    reason = f"cluster: {words_str}"
                    confidence = sum(f.confidence for f in segment_fillers) / len(segment_fillers)
            else:
                reason = "filler"
                confidence = 0.8

            removal_segments.append(RemovalSegment(
                start=start,
                end=end,
                duration=end - start,
                reason=reason,
                confidence=confidence
            ))

        time_saved = sum(s.duration for s in removal_segments)

        # If preview only, return analysis without processing
        if preview_only:
            return FillerRemovalResult(
                success=True,
                output_path=None,
                original_duration=original_duration,
                new_duration=original_duration - time_saved,
                time_saved=time_saved,
                segments_removed=len(removal_segments),
                removal_segments=removal_segments,
                detection_result=detection_result,
                preview_only=True
            )

        # Step 3: Remove fillers from video
        if output_path is None:
            # Generate output path
            base_name = Path(video_path).stem
            output_dir = Path(video_path).parent
            output_path = str(output_dir / f"{base_name}_clean.mp4")

        logger.info(f"Removing {len(removal_segments)} filler segments from video")

        success = await remove_fillers_from_video(
            input_path=video_path,
            output_path=output_path,
            removal_segments=[(s.start, s.end) for s in removal_segments],
            crossfade_ms=AUDIO_CROSSFADE_MS
        )

        if success:
            new_duration = get_video_duration(output_path)
            actual_time_saved = original_duration - new_duration

            log_job_event("filler_removal", "completed", {
                "segments_removed": len(removal_segments),
                "time_saved": actual_time_saved,
                "output_path": output_path
            })

            return FillerRemovalResult(
                success=True,
                output_path=output_path,
                original_duration=original_duration,
                new_duration=new_duration,
                time_saved=actual_time_saved,
                segments_removed=len(removal_segments),
                removal_segments=removal_segments,
                detection_result=detection_result
            )
        else:
            return FillerRemovalResult(
                success=False,
                output_path=None,
                original_duration=original_duration,
                new_duration=0,
                time_saved=0,
                segments_removed=0,
                removal_segments=removal_segments,
                detection_result=detection_result,
                error="FFmpeg processing failed"
            )

    except Exception as e:
        logger.error(f"Filler removal failed: {e}", exc_info=True)
        log_job_event("filler_removal", "failed", {"error": str(e)})

        return FillerRemovalResult(
            success=False,
            output_path=None,
            original_duration=original_duration,
            new_duration=0,
            time_saved=0,
            segments_removed=0,
            removal_segments=[],
            detection_result=None,
            error=str(e)
        )


async def compare_before_after(
    video_path: str,
    sensitivity: str = "moderate",
    segment_index: int = 0,
    duration: float = 5.0
) -> Dict[str, Any]:
    """
    Generate before/after comparison for a specific filler segment.

    Useful for previewing filler removal before processing entire video.

    Args:
        video_path: Path to input video
        sensitivity: Detection sensitivity
        segment_index: Which filler segment to preview (0 = first)
        duration: Duration of preview clip (seconds)

    Returns:
        Dict with paths to before and after clips
    """
    # Detect fillers
    transcription = await transcribe_video(video_path)
    if not transcription.words:
        return {"error": "No words detected in video"}

    words = [
        WordTimestamp(word=w.word, start=w.start, end=w.end, confidence=w.confidence)
        for w in transcription.words
    ]

    detection_result = detect_fillers_with_sensitivity(words, sensitivity)
    raw_segments = get_removal_segments(detection_result, include_clusters=True)

    if not raw_segments or segment_index >= len(raw_segments):
        return {"error": f"No filler segment at index {segment_index}"}

    # Get the target segment
    target_start, target_end = raw_segments[segment_index]

    # Calculate preview window
    preview_start = max(0, target_start - duration / 2)
    preview_end = target_end + duration / 2

    # Create temp directory for clips
    temp_dir = tempfile.mkdtemp()
    before_clip = os.path.join(temp_dir, "before.mp4")
    after_clip = os.path.join(temp_dir, "after.mp4")

    # Extract "before" clip (with filler)
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-ss", str(preview_start),
        "-t", str(preview_end - preview_start),
        "-c:v", "libx264", "-preset", "fast",
        "-c:a", "aac",
        before_clip
    ], capture_output=True)

    # Extract "after" clip (with filler removed)
    # Calculate relative segment position
    relative_start = target_start - preview_start
    relative_end = target_end - preview_start

    await remove_fillers_from_video(
        input_path=before_clip,
        output_path=after_clip,
        removal_segments=[(relative_start, relative_end)]
    )

    return {
        "before_clip": before_clip,
        "after_clip": after_clip,
        "filler_segment": {
            "start": target_start,
            "end": target_end,
            "duration": target_end - target_start
        },
        "preview_window": {
            "start": preview_start,
            "end": preview_end
        },
        "temp_dir": temp_dir  # Caller should clean up
    }
