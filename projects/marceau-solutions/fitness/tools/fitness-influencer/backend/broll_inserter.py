"""
B-Roll Inserter — Detect talking-head segments and insert B-roll footage.

Features:
- Detect low-visual-variety segments (talking head only)
- Insert B-roll clips from local library at optimal timestamps
- Optionally generate AI B-roll via multi_provider_video_router
- Cross-dissolve transitions for smooth insertion
- Category-aware: gym_equipment, exercises, lifestyle, etc.

Implementation: FFmpeg concat, overlay, and filter_complex chains
"""

import asyncio
import json
import logging
import os
import random
import subprocess
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ── Enums & Data Classes ─────────────────────────────────────────────────────

class BRollCategory(str, Enum):
    GYM_EQUIPMENT = "gym_equipment"
    EXERCISES = "exercises"
    LIFESTYLE = "lifestyle"
    FOOD_NUTRITION = "food_nutrition"
    OUTDOORS = "outdoors"
    CLOSE_UP = "close_up"
    GENERIC = "generic"


class InsertMode(str, Enum):
    OVERLAY = "overlay"        # Picture-in-picture (small B-roll corner)
    REPLACE = "replace"        # Full replace talking head segment
    SPLIT_SCREEN = "split"     # Side-by-side with talking head


@dataclass
class TalkingHeadSegment:
    """A segment detected as low visual variety (talking head)."""
    start: float
    end: float
    duration: float
    motion_score: float    # 0-1, low = static
    face_coverage: float   # 0-1, how much of frame is face
    confidence: float      # 0-1

    @property
    def is_good_candidate(self) -> bool:
        """Whether this segment is a good candidate for B-roll."""
        return self.duration >= 2.0 and self.motion_score < 0.3


@dataclass
class BRollClip:
    """A B-roll clip from the library."""
    path: str
    name: str
    category: BRollCategory
    duration: float
    width: int = 0
    height: int = 0
    tags: List[str] = field(default_factory=list)


@dataclass
class BRollInsertion:
    """A planned B-roll insertion."""
    segment_start: float
    segment_end: float
    clip_path: str
    clip_name: str
    insert_mode: InsertMode
    transition_dur: float = 0.3


@dataclass
class InsertResult:
    """Result of B-roll insertion."""
    success: bool
    output_path: str
    segments_detected: int
    segments_filled: int
    insertions: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output_path": self.output_path,
            "segments_detected": self.segments_detected,
            "segments_filled": self.segments_filled,
            "insertions": self.insertions,
            "error": self.error,
        }


# ── FFmpeg Utilities ──────────────────────────────────────────────────────────

def _run_ffmpeg(args: List[str], timeout: int = 300) -> subprocess.CompletedProcess:
    cmd = ["ffmpeg", "-y"] + args
    logger.debug(f"FFmpeg: {' '.join(cmd)}")
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def _run_ffprobe(args: List[str]) -> subprocess.CompletedProcess:
    cmd = ["ffprobe"] + args
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def _get_video_info(path: str) -> Dict[str, Any]:
    """Get video dimensions, duration, fps."""
    result = _run_ffprobe([
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,duration",
        "-show_entries", "format=duration",
        "-of", "json",
        path,
    ])
    if result.returncode != 0:
        return {"width": 0, "height": 0, "fps": 30, "duration": 0}

    data = json.loads(result.stdout)
    stream = data.get("streams", [{}])[0] if data.get("streams") else {}
    fmt = data.get("format", {})

    # Parse frame rate
    fps_str = stream.get("r_frame_rate", "30/1")
    try:
        num, den = fps_str.split("/")
        fps = float(num) / float(den) if float(den) > 0 else 30
    except (ValueError, ZeroDivisionError):
        fps = 30

    duration = float(stream.get("duration", 0) or fmt.get("duration", 0))

    return {
        "width": int(stream.get("width", 0)),
        "height": int(stream.get("height", 0)),
        "fps": fps,
        "duration": duration,
    }


# ── Talking-Head Detection ────────────────────────────────────────────────────

async def detect_talking_head_segments(
    video_path: str,
    min_duration: float = 3.0,
    motion_threshold: float = 0.25,
    sample_interval: float = 1.0,
    analysis: Optional[Any] = None,
) -> List[TalkingHeadSegment]:
    """
    Detect segments that are primarily talking head with low visual variety.

    Uses motion analysis to find static segments where the frame barely changes.
    If analysis (VideoAnalysisResult) is provided, uses pre-computed motion data.
    """
    # If we have pre-computed analysis, use motion points
    if analysis and hasattr(analysis, "motion_points") and analysis.motion_points:
        return _detect_from_analysis(analysis, min_duration, motion_threshold)

    # Otherwise, analyze motion from video using FFmpeg
    return await _detect_from_ffmpeg(video_path, min_duration, motion_threshold, sample_interval)


def _detect_from_analysis(
    analysis: Any,
    min_duration: float,
    motion_threshold: float,
) -> List[TalkingHeadSegment]:
    """Detect talking head segments from pre-computed VideoAnalysisResult."""
    motion_points = analysis.motion_points
    if not motion_points:
        return []

    segments = []
    current_start = None
    current_motions = []

    for mp in motion_points:
        ts = mp.timestamp if hasattr(mp, "timestamp") else mp.get("timestamp", 0)
        intensity = mp.intensity if hasattr(mp, "intensity") else mp.get("intensity", 0)

        if intensity < motion_threshold:
            if current_start is None:
                current_start = ts
            current_motions.append(intensity)
        else:
            if current_start is not None:
                duration = ts - current_start
                if duration >= min_duration:
                    avg_motion = sum(current_motions) / len(current_motions) if current_motions else 0
                    segments.append(TalkingHeadSegment(
                        start=current_start,
                        end=ts,
                        duration=duration,
                        motion_score=avg_motion,
                        face_coverage=0.5,  # Estimate without face detection
                        confidence=0.7,
                    ))
                current_start = None
                current_motions = []

    # Handle final segment
    if current_start is not None:
        end_ts = motion_points[-1].timestamp if hasattr(motion_points[-1], "timestamp") else motion_points[-1].get("timestamp", 0)
        duration = end_ts - current_start
        if duration >= min_duration:
            avg_motion = sum(current_motions) / len(current_motions) if current_motions else 0
            segments.append(TalkingHeadSegment(
                start=current_start,
                end=end_ts,
                duration=duration,
                motion_score=avg_motion,
                face_coverage=0.5,
                confidence=0.7,
            ))

    return segments


async def _detect_from_ffmpeg(
    video_path: str,
    min_duration: float,
    motion_threshold: float,
    sample_interval: float,
) -> List[TalkingHeadSegment]:
    """Detect low-motion segments using FFmpeg frame difference analysis."""
    info = _get_video_info(video_path)
    duration = info["duration"]
    if duration <= 0:
        return []

    # Use FFmpeg to compute frame differences (motion detection)
    # mpdecimate filter detects near-duplicate frames
    with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Use signalstats to get frame-by-frame visual change metrics
        result = _run_ffmpeg([
            "-i", video_path,
            "-vf", f"fps=1/{sample_interval},signalstats=stat=tout+vrep,metadata=print:file={tmp_path}",
            "-f", "null", "-",
        ], timeout=600)

        if not os.path.exists(tmp_path):
            return []

        # Parse VREP (visual repetition) — high VREP = low motion = talking head
        timestamps = []
        vrep_values = []
        current_ts = 0.0

        with open(tmp_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("frame:"):
                    import re
                    match = re.search(r"pts_time:([\d.]+)", line)
                    if match:
                        current_ts = float(match.group(1))
                elif "lavfi.signalstats.VREP" in line:
                    import re
                    match = re.search(r"=([\d.]+)", line)
                    if match:
                        vrep = float(match.group(1))
                        timestamps.append(current_ts)
                        # VREP is 0-100; normalize to 0-1 and invert for motion
                        vrep_values.append(vrep / 100.0)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    if not timestamps:
        return []

    # Find contiguous low-motion segments
    # High VREP = frames are repetitive = low motion
    segments = []
    current_start = None
    current_vreps = []

    for ts, vrep in zip(timestamps, vrep_values):
        # VREP > threshold means high repetition = low motion
        if vrep > (1.0 - motion_threshold):
            if current_start is None:
                current_start = ts
            current_vreps.append(1.0 - vrep)  # Convert to motion score
        else:
            if current_start is not None:
                seg_duration = ts - current_start
                if seg_duration >= min_duration:
                    avg_motion = sum(current_vreps) / len(current_vreps) if current_vreps else 0
                    segments.append(TalkingHeadSegment(
                        start=current_start,
                        end=ts,
                        duration=seg_duration,
                        motion_score=avg_motion,
                        face_coverage=0.5,
                        confidence=0.6,
                    ))
                current_start = None
                current_vreps = []

    # Final segment
    if current_start is not None:
        seg_duration = duration - current_start
        if seg_duration >= min_duration:
            avg_motion = sum(current_vreps) / len(current_vreps) if current_vreps else 0
            segments.append(TalkingHeadSegment(
                start=current_start,
                end=duration,
                duration=seg_duration,
                motion_score=avg_motion,
                face_coverage=0.5,
                confidence=0.6,
            ))

    return segments


# ── B-Roll Library ────────────────────────────────────────────────────────────

def scan_broll_library(library_dir: str) -> List[BRollClip]:
    """
    Scan directory for B-roll clips organized by category.

    Expected structure:
        data/broll/
        ├── gym_equipment/
        │   ├── dumbbells.mp4
        │   └── cable_machine.mp4
        ├── exercises/
        ├── lifestyle/
        └── close_up/
    """
    clips = []
    library_path = Path(library_dir)
    if not library_path.exists():
        return clips

    video_exts = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

    for cat_dir in library_path.iterdir():
        if not cat_dir.is_dir():
            continue
        try:
            category = BRollCategory(cat_dir.name.lower())
        except ValueError:
            category = BRollCategory.GENERIC

        for video_file in cat_dir.iterdir():
            if video_file.suffix.lower() in video_exts:
                info = _get_video_info(str(video_file))
                clips.append(BRollClip(
                    path=str(video_file),
                    name=video_file.stem,
                    category=category,
                    duration=info["duration"],
                    width=info["width"],
                    height=info["height"],
                ))

    return clips


def select_broll_clips(
    clips: List[BRollClip],
    segments: List[TalkingHeadSegment],
    category: Optional[BRollCategory] = None,
    max_reuse: int = 2,
) -> List[BRollInsertion]:
    """
    Match B-roll clips to talking-head segments.

    Selects clips that fit the segment duration, avoiding overuse.
    """
    candidates = clips
    if category:
        cat_clips = [c for c in candidates if c.category == category]
        if cat_clips:
            candidates = cat_clips

    if not candidates:
        return []

    insertions = []
    usage_count: Dict[str, int] = {}

    for seg in segments:
        if not seg.is_good_candidate:
            continue

        # Find clips that fit within the segment (or can be trimmed)
        available = [
            c for c in candidates
            if usage_count.get(c.path, 0) < max_reuse
        ]
        if not available:
            available = candidates  # Reset if all exhausted

        # Prefer clips shorter than segment
        fitting = [c for c in available if c.duration <= seg.duration + 1.0]
        if not fitting:
            fitting = available

        # Random selection for variety
        clip = random.choice(fitting)
        usage_count[clip.path] = usage_count.get(clip.path, 0) + 1

        insertions.append(BRollInsertion(
            segment_start=seg.start,
            segment_end=seg.end,
            clip_path=clip.path,
            clip_name=clip.name,
            insert_mode=InsertMode.REPLACE,
            transition_dur=0.3,
        ))

    return insertions


# ── B-Roll Insertion via FFmpeg ───────────────────────────────────────────────

async def apply_broll_insertions(
    video_path: str,
    insertions: List[BRollInsertion],
    output_path: str,
) -> bool:
    """
    Apply B-roll insertions to video using FFmpeg segment concatenation.

    Splits original video at insertion points, replaces segments with B-roll,
    and concatenates everything back together with cross-dissolve transitions.
    """
    if not insertions:
        return False

    info = _get_video_info(video_path)
    video_dur = info["duration"]
    width, height = info["width"], info["height"]

    # Sort insertions by time
    sorted_ins = sorted(insertions, key=lambda i: i.segment_start)

    # Build segment list: original + B-roll interleaved
    segments = []
    temp_files = []
    current_pos = 0.0

    try:
        for ins in sorted_ins:
            # Original segment before B-roll
            if ins.segment_start > current_pos + 0.1:
                seg_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
                temp_files.append(seg_file)
                result = _run_ffmpeg([
                    "-i", video_path,
                    "-ss", f"{current_pos:.3f}",
                    "-to", f"{ins.segment_start:.3f}",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                    "-c:a", "aac", "-b:a", "128k",
                    seg_file,
                ])
                if result.returncode == 0 and os.path.exists(seg_file):
                    segments.append(seg_file)

            # B-roll segment (scaled to match main video dimensions, trimmed to fit)
            broll_dur = ins.segment_end - ins.segment_start
            broll_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
            temp_files.append(broll_file)

            # Get audio from original video for this segment (keep speech)
            result = _run_ffmpeg([
                "-i", ins.clip_path,
                "-i", video_path,
                "-filter_complex",
                f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={info['fps']}[bv];"
                f"[1:a]atrim={ins.segment_start:.3f}:{ins.segment_end:.3f},asetpts=PTS-STARTPTS[ba]",
                "-map", "[bv]",
                "-map", "[ba]",
                "-t", f"{broll_dur:.3f}",
                "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                "-c:a", "aac", "-b:a", "128k",
                broll_file,
            ])
            if result.returncode == 0 and os.path.exists(broll_file):
                segments.append(broll_file)

            current_pos = ins.segment_end

        # Final segment after last B-roll
        if current_pos < video_dur - 0.1:
            seg_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
            temp_files.append(seg_file)
            result = _run_ffmpeg([
                "-i", video_path,
                "-ss", f"{current_pos:.3f}",
                "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                "-c:a", "aac", "-b:a", "128k",
                seg_file,
            ])
            if result.returncode == 0 and os.path.exists(seg_file):
                segments.append(seg_file)

        if not segments:
            return False

        # Concatenate all segments
        concat_file = tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w")
        temp_files.append(concat_file.name)
        for seg in segments:
            concat_file.write(f"file '{seg}'\n")
        concat_file.close()

        result = _run_ffmpeg([
            "-f", "concat", "-safe", "0",
            "-i", concat_file.name,
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "aac", "-b:a", "192k",
            output_path,
        ])

        return result.returncode == 0 and os.path.exists(output_path)

    finally:
        for tf in temp_files:
            try:
                if os.path.exists(tf):
                    os.unlink(tf)
            except OSError:
                pass


# ── Main Public API ───────────────────────────────────────────────────────────

async def insert_broll(
    video_path: str,
    output_path: str,
    broll_dir: Optional[str] = None,
    broll_clips: Optional[List[str]] = None,
    category: Optional[str] = None,
    max_insertions: int = 10,
    min_segment_dur: float = 3.0,
    insert_mode: str = "replace",
    analysis: Optional[Any] = None,
) -> InsertResult:
    """
    Detect talking-head segments and insert B-roll footage.

    Args:
        video_path: Input video path
        output_path: Output video path
        broll_dir: Path to B-roll library directory
        broll_clips: Direct list of B-roll clip paths (overrides library)
        category: B-roll category to prefer
        max_insertions: Maximum number of B-roll insertions
        min_segment_dur: Minimum talking-head segment duration to fill
        insert_mode: "replace", "overlay", or "split"
        analysis: Pre-computed VideoAnalysisResult

    Returns:
        InsertResult with details of what was inserted
    """
    # Step 1: Detect talking-head segments
    segments = await detect_talking_head_segments(
        video_path,
        min_duration=min_segment_dur,
        analysis=analysis,
    )

    if not segments:
        return InsertResult(
            success=True,
            output_path=video_path,
            segments_detected=0,
            segments_filled=0,
            error=None,
        )

    # Limit to max_insertions best candidates
    candidates = [s for s in segments if s.is_good_candidate]
    candidates.sort(key=lambda s: s.duration, reverse=True)
    candidates = candidates[:max_insertions]

    # Step 2: Get B-roll clips
    clips = []
    if broll_clips:
        for clip_path in broll_clips:
            if os.path.exists(clip_path):
                info = _get_video_info(clip_path)
                clips.append(BRollClip(
                    path=clip_path,
                    name=Path(clip_path).stem,
                    category=BRollCategory.GENERIC,
                    duration=info["duration"],
                    width=info["width"],
                    height=info["height"],
                ))
    elif broll_dir:
        clips = scan_broll_library(broll_dir)

    if not clips:
        return InsertResult(
            success=False,
            output_path=output_path,
            segments_detected=len(segments),
            segments_filled=0,
            error="No B-roll clips available. Provide broll_dir or broll_clips.",
        )

    # Step 3: Match clips to segments
    cat = BRollCategory(category) if category and category in [c.value for c in BRollCategory] else None
    insertions = select_broll_clips(clips, candidates, category=cat)

    if not insertions:
        return InsertResult(
            success=True,
            output_path=video_path,
            segments_detected=len(segments),
            segments_filled=0,
        )

    # Step 4: Apply insertions
    success = await apply_broll_insertions(video_path, insertions, output_path)

    return InsertResult(
        success=success,
        output_path=output_path if success else video_path,
        segments_detected=len(segments),
        segments_filled=len(insertions),
        insertions=[
            {
                "start": ins.segment_start,
                "end": ins.segment_end,
                "clip": ins.clip_name,
                "mode": ins.insert_mode.value,
            }
            for ins in insertions
        ],
        error=None if success else "B-roll insertion failed during FFmpeg processing",
    )


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="B-Roll Inserter — Auto-detect and fill talking-head segments")
    parser.add_argument("video", help="Input video path")
    parser.add_argument("--broll-dir", help="B-roll library directory")
    parser.add_argument("--category", default=None, choices=[c.value for c in BRollCategory])
    parser.add_argument("--max-insertions", type=int, default=10)
    parser.add_argument("--min-duration", type=float, default=3.0)
    parser.add_argument("--output", default="output_with_broll.mp4")
    parser.add_argument("--detect-only", action="store_true", help="Only detect segments, don't insert")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.detect_only:
        segments = asyncio.run(detect_talking_head_segments(
            args.video,
            min_duration=args.min_duration,
        ))
        print(f"\nDetected {len(segments)} talking-head segments:")
        for seg in segments:
            print(f"  {seg.start:.1f}s - {seg.end:.1f}s ({seg.duration:.1f}s) "
                  f"motion={seg.motion_score:.2f} candidate={seg.is_good_candidate}")
    else:
        result = asyncio.run(insert_broll(
            video_path=args.video,
            output_path=args.output,
            broll_dir=args.broll_dir,
            category=args.category,
            max_insertions=args.max_insertions,
            min_segment_dur=args.min_duration,
        ))
        print(f"\nB-Roll Insert Result:")
        print(f"  Success: {result.success}")
        print(f"  Segments detected: {result.segments_detected}")
        print(f"  Segments filled: {result.segments_filled}")
        if result.insertions:
            for ins in result.insertions:
                print(f"    {ins['start']:.1f}s-{ins['end']:.1f}s → {ins['clip']} ({ins['mode']})")
        if result.error:
            print(f"  Error: {result.error}")
