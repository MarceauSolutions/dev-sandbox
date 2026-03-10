"""
Transition Engine — Smooth transitions between cuts
=====================================================
Crossfade, zoom-through, whip pan, flash, swipe transitions.
Platform-aware: TikTok → fast (0.2s), YouTube → medium (0.5s).
Auto-place at scene changes detected by video_analyzer.
Uses FFmpeg xfade filter + custom filter chains.
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ── Enums ──────────────────────────────────────────────────────────

class TransitionType(Enum):
    """Available transition effects."""
    CROSSFADE = "crossfade"        # Classic dissolve
    ZOOM_THROUGH = "zoom_through"  # Zoom into first, out of second
    WHIP_PAN = "whip_pan"          # Fast horizontal blur
    FLASH = "flash"                # White flash between clips
    SWIPE_LEFT = "swipe_left"      # Left swipe
    SWIPE_RIGHT = "swipe_right"    # Right swipe
    SWIPE_UP = "swipe_up"          # Upward swipe
    SWIPE_DOWN = "swipe_down"      # Downward swipe
    FADE_BLACK = "fade_black"      # Fade to/from black
    WIPE_LEFT = "wipe_left"        # Hard wipe left
    WIPE_RIGHT = "wipe_right"      # Hard wipe right
    SLIDE_LEFT = "slide_left"      # Slide left (FFmpeg xfade)
    SLIDE_RIGHT = "slide_right"    # Slide right (FFmpeg xfade)
    NONE = "none"                  # Hard cut (no transition)


class Platform(Enum):
    """Platform presets for transition timing."""
    TIKTOK = "tiktok"
    YOUTUBE_SHORTS = "youtube_shorts"
    INSTAGRAM_REELS = "instagram_reels"
    YOUTUBE = "youtube"
    DEFAULT = "default"


# ── Platform Configs ───────────────────────────────────────────────

PLATFORM_CONFIGS: Dict[str, Dict[str, Any]] = {
    "tiktok": {
        "default_duration": 0.2,
        "max_duration": 0.4,
        "preferred_types": [
            TransitionType.WHIP_PAN,
            TransitionType.FLASH,
            TransitionType.SWIPE_LEFT,
            TransitionType.ZOOM_THROUGH,
        ],
        "energy": "high",
    },
    "youtube_shorts": {
        "default_duration": 0.25,
        "max_duration": 0.5,
        "preferred_types": [
            TransitionType.WHIP_PAN,
            TransitionType.FLASH,
            TransitionType.CROSSFADE,
            TransitionType.SWIPE_LEFT,
        ],
        "energy": "high",
    },
    "instagram_reels": {
        "default_duration": 0.25,
        "max_duration": 0.4,
        "preferred_types": [
            TransitionType.SWIPE_LEFT,
            TransitionType.FLASH,
            TransitionType.CROSSFADE,
            TransitionType.ZOOM_THROUGH,
        ],
        "energy": "high",
    },
    "youtube": {
        "default_duration": 0.5,
        "max_duration": 1.0,
        "preferred_types": [
            TransitionType.CROSSFADE,
            TransitionType.FADE_BLACK,
            TransitionType.WIPE_LEFT,
            TransitionType.SLIDE_LEFT,
        ],
        "energy": "medium",
    },
    "default": {
        "default_duration": 0.3,
        "max_duration": 0.6,
        "preferred_types": [
            TransitionType.CROSSFADE,
            TransitionType.WHIP_PAN,
            TransitionType.FLASH,
            TransitionType.SWIPE_LEFT,
        ],
        "energy": "medium",
    },
}


# ── Data Classes ───────────────────────────────────────────────────

@dataclass
class TransitionPoint:
    """A point where a transition should be applied."""
    timestamp: float           # Time in source video (seconds)
    transition_type: TransitionType = TransitionType.CROSSFADE
    duration: float = 0.3      # Transition duration in seconds
    confidence: float = 1.0    # Scene change confidence (from analyzer)
    reason: str = ""           # Why this transition was chosen

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": round(self.timestamp, 2),
            "transition_type": self.transition_type.value,
            "duration": round(self.duration, 2),
            "confidence": round(self.confidence, 3),
            "reason": self.reason,
        }


@dataclass
class TransitionResult:
    """Result of applying transitions to a video."""
    output_path: str
    transitions_applied: int
    transition_points: List[TransitionPoint]
    duration_original: float = 0.0
    duration_output: float = 0.0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "output_path": self.output_path,
            "transitions_applied": self.transitions_applied,
            "transition_points": [t.to_dict() for t in self.transition_points],
            "duration_original": round(self.duration_original, 2),
            "duration_output": round(self.duration_output, 2),
            "errors": self.errors,
        }


# ── FFmpeg Helpers ─────────────────────────────────────────────────

def _get_duration(video_path: str) -> float:
    """Get video duration via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "json", video_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        info = json.loads(result.stdout)
        return float(info["format"]["duration"])
    except Exception:
        return 0.0


def _get_video_info(video_path: str) -> Dict[str, Any]:
    """Get video width, height, fps."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "stream=width,height,r_frame_rate,codec_name",
        "-select_streams", "v:0",
        "-of", "json", video_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        info = json.loads(result.stdout)
        stream = info["streams"][0]
        # Parse frame rate like "30/1" or "30000/1001"
        r = stream.get("r_frame_rate", "30/1")
        num, den = r.split("/")
        fps = float(num) / float(den) if float(den) > 0 else 30.0
        return {
            "width": int(stream.get("width", 1080)),
            "height": int(stream.get("height", 1920)),
            "fps": fps,
            "codec": stream.get("codec_name", "h264"),
        }
    except Exception:
        return {"width": 1080, "height": 1920, "fps": 30.0, "codec": "h264"}


# ── XFADE Transition Map ──────────────────────────────────────────
# Maps TransitionType to FFmpeg xfade transition names

XFADE_MAP = {
    TransitionType.CROSSFADE: "fade",
    TransitionType.FADE_BLACK: "fadeblack",
    TransitionType.WIPE_LEFT: "wipeleft",
    TransitionType.WIPE_RIGHT: "wiperight",
    TransitionType.SLIDE_LEFT: "slideleft",
    TransitionType.SLIDE_RIGHT: "slideright",
    TransitionType.SWIPE_LEFT: "slideleft",
    TransitionType.SWIPE_RIGHT: "slideright",
    TransitionType.SWIPE_UP: "slideup",
    TransitionType.SWIPE_DOWN: "slidedown",
}


# ── Core Engine ────────────────────────────────────────────────────

def _select_transition_type(
    confidence: float,
    index: int,
    total: int,
    platform_config: Dict[str, Any],
) -> TransitionType:
    """Select an appropriate transition type based on context."""
    preferred = platform_config["preferred_types"]
    energy = platform_config["energy"]

    # High confidence scene changes get more dramatic transitions
    if confidence > 0.7 and energy == "high":
        dramatic = [
            TransitionType.WHIP_PAN,
            TransitionType.FLASH,
            TransitionType.ZOOM_THROUGH,
        ]
        for t in dramatic:
            if t in preferred:
                return t

    # Cycle through preferred transitions to add variety
    return preferred[index % len(preferred)]


def _split_video_at_points(
    video_path: str,
    split_points: List[float],
    output_dir: str,
) -> List[str]:
    """Split a video at specific timestamps into segments."""
    duration = _get_duration(video_path)
    if duration <= 0:
        return []

    segments = []
    points = [0.0] + sorted(split_points) + [duration]

    for i in range(len(points) - 1):
        start = points[i]
        end = points[i + 1]
        seg_duration = end - start

        if seg_duration < 0.1:
            continue

        seg_path = os.path.join(output_dir, f"segment_{i:04d}.mp4")
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-i", video_path,
            "-t", str(seg_duration),
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac",
            "-avoid_negative_ts", "make_zero",
            seg_path,
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=120)
            if os.path.exists(seg_path) and os.path.getsize(seg_path) > 0:
                segments.append(seg_path)
        except Exception as e:
            logger.warning(f"Failed to split segment {i}: {e}")

    return segments


def _apply_xfade_pair(
    seg_a: str,
    seg_b: str,
    output_path: str,
    transition_name: str,
    duration: float,
) -> bool:
    """Apply xfade transition between two segments."""
    dur_a = _get_duration(seg_a)
    if dur_a <= 0:
        return False

    # xfade offset = duration of first clip minus transition duration
    offset = max(0.0, dur_a - duration)

    cmd = [
        "ffmpeg", "-y",
        "-i", seg_a,
        "-i", seg_b,
        "-filter_complex",
        (
            f"[0:v][1:v]xfade=transition={transition_name}"
            f":duration={duration}:offset={offset}[v];"
            f"[0:a][1:a]acrossfade=d={duration}[a]"
        ),
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "fast",
        "-c:a", "aac",
        output_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            # Fallback: try without audio crossfade (in case of mono/stereo mismatch)
            cmd_no_audio = [
                "ffmpeg", "-y",
                "-i", seg_a,
                "-i", seg_b,
                "-filter_complex",
                (
                    f"[0:v][1:v]xfade=transition={transition_name}"
                    f":duration={duration}:offset={offset}[v];"
                    f"[0:a][1:a]concat=n=2:v=0:a=1[a]"
                ),
                "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-preset", "fast",
                "-c:a", "aac",
                output_path,
            ]
            result = subprocess.run(
                cmd_no_audio, capture_output=True, text=True, timeout=120
            )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"xfade failed: {e}")
        return False


def _apply_custom_transition(
    seg_a: str,
    seg_b: str,
    output_path: str,
    transition_type: TransitionType,
    duration: float,
) -> bool:
    """Apply custom transitions (whip pan, flash, zoom) that need special filters."""
    dur_a = _get_duration(seg_a)
    info = _get_video_info(seg_a)
    w, h = info["width"], info["height"]

    if transition_type == TransitionType.WHIP_PAN:
        return _apply_whip_pan(seg_a, seg_b, output_path, duration, w, h, dur_a)
    elif transition_type == TransitionType.FLASH:
        return _apply_flash(seg_a, seg_b, output_path, duration, dur_a)
    elif transition_type == TransitionType.ZOOM_THROUGH:
        return _apply_zoom_through(seg_a, seg_b, output_path, duration, w, h, dur_a)
    else:
        # Fallback to crossfade
        return _apply_xfade_pair(seg_a, seg_b, output_path, "fade", duration)


def _apply_whip_pan(
    seg_a: str, seg_b: str, output_path: str,
    duration: float, w: int, h: int, dur_a: float,
) -> bool:
    """Whip pan: motion blur the end of A and start of B, concatenate."""
    half = duration / 2
    blur_frames = max(2, int(half * 30))

    # Strategy: Add horizontal motion blur to tail of A and head of B,
    # then concatenate with a very short crossfade
    filter_complex = (
        # Blur the last frames of clip A (horizontal smear)
        f"[0:v]split[a_main][a_tail];"
        f"[a_tail]trim=start={max(0, dur_a - half)}:duration={half},"
        f"setpts=PTS-STARTPTS,"
        f"boxblur=luma_radius={min(40, w // 20)}:luma_power=2[a_blur];"
        f"[a_main]trim=0:{max(0.1, dur_a - half)},setpts=PTS-STARTPTS[a_cut];"
        # Blur the first frames of clip B
        f"[1:v]split[b_head][b_main];"
        f"[b_head]trim=0:{half},setpts=PTS-STARTPTS,"
        f"boxblur=luma_radius={min(40, w // 20)}:luma_power=2[b_blur];"
        f"[b_main]trim=start={half},setpts=PTS-STARTPTS[b_cut];"
        # Concatenate: A clean → A blur → B blur → B clean
        f"[a_cut][a_blur][b_blur][b_cut]concat=n=4:v=1:a=0[v];"
        # Audio: simple concat
        f"[0:a][1:a]concat=n=2:v=0:a=1[a]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", seg_a, "-i", seg_b,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "fast",
        "-c:a", "aac",
        output_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            logger.warning(f"Whip pan failed, falling back to slide: {result.stderr[:200]}")
            return _apply_xfade_pair(seg_a, seg_b, output_path, "slideleft", duration)
        return True
    except Exception as e:
        logger.error(f"Whip pan error: {e}")
        return _apply_xfade_pair(seg_a, seg_b, output_path, "slideleft", duration)


def _apply_flash(
    seg_a: str, seg_b: str, output_path: str,
    duration: float, dur_a: float,
) -> bool:
    """Flash: brief white frame between clips with fade in/out."""
    flash_dur = min(duration, 0.15)
    fade_dur = (duration - flash_dur) / 2

    # Use fadeout on A, white frame, fadein on B via concat
    filter_complex = (
        # Fade out end of A to white
        f"[0:v]fade=type=out:start_time={max(0, dur_a - fade_dur)}"
        f":duration={fade_dur}:color=white[a_fade];"
        # Fade in start of B from white
        f"[1:v]fade=type=in:start_time=0"
        f":duration={fade_dur}:color=white[b_fade];"
        # Concat
        f"[a_fade][b_fade]concat=n=2:v=1:a=0[v];"
        f"[0:a][1:a]concat=n=2:v=0:a=1[a]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", seg_a, "-i", seg_b,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "fast",
        "-c:a", "aac",
        output_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            logger.warning(f"Flash failed, falling back to fadeblack: {result.stderr[:200]}")
            return _apply_xfade_pair(seg_a, seg_b, output_path, "fadeblack", duration)
        return True
    except Exception as e:
        logger.error(f"Flash error: {e}")
        return _apply_xfade_pair(seg_a, seg_b, output_path, "fadeblack", duration)


def _apply_zoom_through(
    seg_a: str, seg_b: str, output_path: str,
    duration: float, w: int, h: int, dur_a: float,
) -> bool:
    """Zoom through: zoom into end of A, zoom out from start of B."""
    half = duration / 2

    # Zoom into center of last frames of A, zoom out from center of first frames of B
    filter_complex = (
        # A: zoom in on the last `half` seconds
        f"[0:v]split[a_main][a_zoom];"
        f"[a_zoom]trim=start={max(0, dur_a - half)}:duration={half},"
        f"setpts=PTS-STARTPTS,"
        f"zoompan=z='min(zoom+0.08,2.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        f":d=1:s={w}x{h}:fps=30[a_z];"
        f"[a_main]trim=0:{max(0.1, dur_a - half)},setpts=PTS-STARTPTS[a_cut];"
        # B: zoom out on the first `half` seconds
        f"[1:v]split[b_zoom][b_main];"
        f"[b_zoom]trim=0:{half},setpts=PTS-STARTPTS,"
        f"zoompan=z='if(eq(on,1),2.0,max(zoom-0.08,1.0))'"
        f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        f":d=1:s={w}x{h}:fps=30[b_z];"
        f"[b_main]trim=start={half},setpts=PTS-STARTPTS[b_cut];"
        # Concat
        f"[a_cut][a_z][b_z][b_cut]concat=n=4:v=1:a=0[v];"
        f"[0:a][1:a]concat=n=2:v=0:a=1[a]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", seg_a, "-i", seg_b,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "fast",
        "-c:a", "aac",
        output_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            logger.warning(f"Zoom through failed, falling back to fade: {result.stderr[:200]}")
            return _apply_xfade_pair(seg_a, seg_b, output_path, "fade", duration)
        return True
    except Exception as e:
        logger.error(f"Zoom through error: {e}")
        return _apply_xfade_pair(seg_a, seg_b, output_path, "fade", duration)


# ── Public API ─────────────────────────────────────────────────────

def plan_transitions(
    scene_changes: List[Dict[str, Any]],
    platform: str = "default",
    min_gap: float = 2.0,
    max_transitions: int = 20,
) -> List[TransitionPoint]:
    """
    Plan transitions from scene change data.

    Args:
        scene_changes: List of {"timestamp": float, "confidence": float} dicts
            (from video_analyzer.detect_scenes)
        platform: Platform name for timing/style presets
        min_gap: Minimum gap between transitions (seconds)
        max_transitions: Cap on number of transitions

    Returns:
        List of TransitionPoint with type and duration assigned.
    """
    config = PLATFORM_CONFIGS.get(platform, PLATFORM_CONFIGS["default"])
    default_dur = config["default_duration"]
    max_dur = config["max_duration"]

    # Sort by timestamp
    sorted_changes = sorted(scene_changes, key=lambda s: s["timestamp"])

    # Filter: enforce minimum gap between transitions
    filtered = []
    last_ts = -min_gap
    for sc in sorted_changes:
        ts = sc["timestamp"]
        if ts - last_ts >= min_gap:
            filtered.append(sc)
            last_ts = ts

    # Cap at max
    if len(filtered) > max_transitions:
        # Keep the highest confidence ones
        filtered.sort(key=lambda s: s.get("confidence", 0.5), reverse=True)
        filtered = filtered[:max_transitions]
        filtered.sort(key=lambda s: s["timestamp"])

    # Assign types and durations
    points = []
    for i, sc in enumerate(filtered):
        conf = sc.get("confidence", 0.5)

        # Higher confidence → longer duration (more dramatic)
        dur = default_dur + (max_dur - default_dur) * conf
        dur = min(dur, max_dur)

        t_type = _select_transition_type(conf, i, len(filtered), config)

        points.append(TransitionPoint(
            timestamp=sc["timestamp"],
            transition_type=t_type,
            duration=round(dur, 2),
            confidence=conf,
            reason=f"Scene change (conf={conf:.2f}) → {t_type.value}",
        ))

    return points


async def apply_transitions(
    video_path: str,
    transition_points: Optional[List[TransitionPoint]] = None,
    scene_changes: Optional[List[Dict[str, Any]]] = None,
    platform: str = "default",
    output_path: Optional[str] = None,
    min_gap: float = 2.0,
    max_transitions: int = 20,
) -> TransitionResult:
    """
    Apply transitions at specified points or auto-detect from scene changes.

    Args:
        video_path: Input video file path.
        transition_points: Pre-planned transitions (takes priority).
        scene_changes: Scene change data for auto-planning.
        platform: Platform for timing presets.
        output_path: Output file path (auto-generated if None).
        min_gap: Minimum seconds between transitions.
        max_transitions: Maximum number of transitions.

    Returns:
        TransitionResult with output path and details.
    """
    if not os.path.exists(video_path):
        return TransitionResult(
            output_path="",
            transitions_applied=0,
            transition_points=[],
            errors=[f"Input file not found: {video_path}"],
        )

    # Plan transitions if not provided
    if transition_points is None:
        if scene_changes is None:
            # Try to detect scenes
            try:
                from video_analyzer import detect_scenes
                detected = await detect_scenes(video_path)
                scene_changes = [s.to_dict() for s in detected]
            except ImportError:
                try:
                    from backend.video_analyzer import detect_scenes
                    detected = await detect_scenes(video_path)
                    scene_changes = [s.to_dict() for s in detected]
                except Exception as e:
                    return TransitionResult(
                        output_path="",
                        transitions_applied=0,
                        transition_points=[],
                        errors=[f"Cannot detect scenes: {e}"],
                    )

        transition_points = plan_transitions(
            scene_changes, platform, min_gap, max_transitions
        )

    if not transition_points:
        # No transitions needed — copy input
        if output_path is None:
            base, ext = os.path.splitext(video_path)
            output_path = f"{base}_transitions{ext}"
        import shutil
        shutil.copy2(video_path, output_path)
        return TransitionResult(
            output_path=output_path,
            transitions_applied=0,
            transition_points=[],
            duration_original=_get_duration(video_path),
            duration_output=_get_duration(video_path),
        )

    # Generate output path
    if output_path is None:
        base, ext = os.path.splitext(video_path)
        output_path = f"{base}_transitions{ext}"

    original_dur = _get_duration(video_path)
    errors = []

    # Create temp directory for segments
    with tempfile.TemporaryDirectory(prefix="transition_") as tmp_dir:
        # Split video at transition points
        split_times = [tp.timestamp for tp in transition_points]
        logger.info(f"Splitting video at {len(split_times)} points")
        segments = await asyncio.get_event_loop().run_in_executor(
            None, _split_video_at_points, video_path, split_times, tmp_dir
        )

        if len(segments) < 2:
            errors.append("Not enough segments to apply transitions")
            import shutil
            shutil.copy2(video_path, output_path)
            return TransitionResult(
                output_path=output_path,
                transitions_applied=0,
                transition_points=transition_points,
                duration_original=original_dur,
                duration_output=original_dur,
                errors=errors,
            )

        # Apply transitions sequentially between adjacent segments
        applied = 0
        current = segments[0]

        for i, tp in enumerate(transition_points):
            if i + 1 >= len(segments):
                break

            next_seg = segments[i + 1]
            merged = os.path.join(tmp_dir, f"merged_{i:04d}.mp4")

            xfade_name = XFADE_MAP.get(tp.transition_type)

            if xfade_name:
                # Use built-in xfade filter
                success = await asyncio.get_event_loop().run_in_executor(
                    None, _apply_xfade_pair,
                    current, next_seg, merged, xfade_name, tp.duration,
                )
            else:
                # Use custom transition (whip pan, flash, zoom)
                success = await asyncio.get_event_loop().run_in_executor(
                    None, _apply_custom_transition,
                    current, next_seg, merged, tp.transition_type, tp.duration,
                )

            if success and os.path.exists(merged) and os.path.getsize(merged) > 0:
                current = merged
                applied += 1
                logger.info(
                    f"Applied {tp.transition_type.value} at {tp.timestamp:.1f}s "
                    f"({applied}/{len(transition_points)})"
                )
            else:
                errors.append(
                    f"Failed {tp.transition_type.value} at {tp.timestamp:.1f}s"
                )
                # Fallback: concatenate without transition
                concat_path = os.path.join(tmp_dir, f"concat_{i:04d}.mp4")
                concat_list = os.path.join(tmp_dir, f"concat_{i:04d}.txt")
                with open(concat_list, "w") as f:
                    f.write(f"file '{current}'\nfile '{next_seg}'\n")
                cmd = [
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                    "-i", concat_list,
                    "-c", "copy", concat_path,
                ]
                subprocess.run(cmd, capture_output=True, timeout=120)
                if os.path.exists(concat_path):
                    current = concat_path

        # Copy final result to output
        import shutil
        shutil.copy2(current, output_path)

    output_dur = _get_duration(output_path)

    logger.info(
        f"Transitions complete: {applied}/{len(transition_points)} applied, "
        f"{original_dur:.1f}s → {output_dur:.1f}s"
    )

    return TransitionResult(
        output_path=output_path,
        transitions_applied=applied,
        transition_points=transition_points,
        duration_original=original_dur,
        duration_output=output_dur,
        errors=errors,
    )


# ── CLI ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Transition Engine")
    parser.add_argument("video", help="Input video path")
    parser.add_argument("-o", "--output", help="Output video path")
    parser.add_argument(
        "-p", "--platform",
        choices=list(PLATFORM_CONFIGS.keys()),
        default="default",
        help="Platform preset for timing/style",
    )
    parser.add_argument(
        "-t", "--type",
        choices=[t.value for t in TransitionType],
        help="Force a specific transition type for all points",
    )
    parser.add_argument(
        "--min-gap", type=float, default=2.0,
        help="Minimum gap between transitions (seconds)",
    )
    parser.add_argument(
        "--max", type=int, default=20,
        help="Maximum number of transitions",
    )
    parser.add_argument(
        "--at", type=float, nargs="+",
        help="Manual transition timestamps (seconds)",
    )
    parser.add_argument("--json", action="store_true", help="JSON output")

    args = parser.parse_args()

    async def main():
        points = None
        scene_data = None

        if args.at:
            # Manual timestamps
            forced_type = (
                TransitionType(args.type)
                if args.type
                else TransitionType.CROSSFADE
            )
            config = PLATFORM_CONFIGS.get(args.platform, PLATFORM_CONFIGS["default"])
            points = [
                TransitionPoint(
                    timestamp=t,
                    transition_type=forced_type,
                    duration=config["default_duration"],
                    reason="manual",
                )
                for t in args.at
            ]

        result = await apply_transitions(
            video_path=args.video,
            transition_points=points,
            scene_changes=scene_data,
            platform=args.platform,
            output_path=args.output,
            min_gap=args.min_gap,
            max_transitions=args.max,
        )

        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(f"\nTransition Engine Results")
            print(f"{'=' * 40}")
            print(f"Output:      {result.output_path}")
            print(f"Applied:     {result.transitions_applied}/{len(result.transition_points)}")
            print(f"Duration:    {result.duration_original:.1f}s → {result.duration_output:.1f}s")
            if result.errors:
                print(f"\nWarnings:")
                for e in result.errors:
                    print(f"  - {e}")
            print(f"\nTransitions:")
            for tp in result.transition_points:
                print(f"  {tp.timestamp:6.1f}s  {tp.transition_type.value:<14s}  {tp.duration:.2f}s  {tp.reason}")

    asyncio.run(main())
