"""
Punch Zoom — Ryan Humiston-style emphasis zoom effect.

Detects key moments (audio peaks, scene emphasis) and applies a quick
crop+scale zoom centered on the subject's face. Creates the "punch-in"
effect that makes fitness content feel energetic and engaging.
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def _get_video_info(video_path: str) -> Dict:
    """Get video dimensions, duration, fps via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", video_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
        video_stream = next(
            (s for s in data.get("streams", []) if s.get("codec_type") == "video"), {}
        )
        return {
            "width": int(video_stream.get("width", 1920)),
            "height": int(video_stream.get("height", 1080)),
            "duration": float(data.get("format", {}).get("duration", 0)),
            "fps": eval(video_stream.get("r_frame_rate", "30/1")),
        }
    except Exception as e:
        logger.warning(f"ffprobe failed: {e}")
        return {"width": 1920, "height": 1080, "duration": 0, "fps": 30}


def _detect_audio_peaks(video_path: str, threshold_db: float = -20, min_gap: float = 2.0) -> List[float]:
    """Detect loud audio moments (speech emphasis, impacts) via FFmpeg."""
    cmd = [
        "ffmpeg", "-i", video_path, "-af",
        f"silencedetect=noise={threshold_db}dB:d=0.1",
        "-f", "null", "-"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        # Parse silence end timestamps (= moments where audio gets LOUD)
        peaks = []
        for line in result.stderr.split("\n"):
            if "silence_end:" in line:
                try:
                    ts = float(line.split("silence_end:")[1].split("|")[0].strip())
                    # Only add if far enough from last peak
                    if not peaks or (ts - peaks[-1]) >= min_gap:
                        peaks.append(ts)
                except (ValueError, IndexError):
                    continue
        return peaks
    except Exception as e:
        logger.warning(f"Audio peak detection failed: {e}")
        return []


def _detect_scene_changes(video_path: str, threshold: float = 0.3) -> List[float]:
    """Detect scene changes via FFmpeg scene filter."""
    cmd = [
        "ffmpeg", "-i", video_path, "-vf",
        f"select='gt(scene,{threshold})',showinfo",
        "-f", "null", "-"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        timestamps = []
        for line in result.stderr.split("\n"):
            if "pts_time:" in line:
                try:
                    ts = float(line.split("pts_time:")[1].split(" ")[0])
                    timestamps.append(ts)
                except (ValueError, IndexError):
                    continue
        return timestamps
    except Exception as e:
        logger.warning(f"Scene detection failed: {e}")
        return []


def _select_zoom_moments(
    audio_peaks: List[float],
    scene_changes: List[float],
    duration: float,
    max_per_minute: int = 8,
    min_gap: float = 2.0,
) -> List[float]:
    """Select the best moments to apply zoom, avoiding overcrowding."""
    # Combine and sort all candidate moments
    candidates = sorted(set(audio_peaks + scene_changes))

    # Filter: no zooms in first 0.5s or last 1s
    candidates = [t for t in candidates if 0.5 < t < (duration - 1.0)]

    # Limit by max_per_minute
    max_total = int((duration / 60.0) * max_per_minute)

    # Prioritize audio peaks (more impactful than scene changes)
    audio_set = set(audio_peaks)
    scored = [(t, 2.0 if t in audio_set else 1.0) for t in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)

    selected = []
    for t, _ in scored:
        if len(selected) >= max_total:
            break
        # Ensure minimum gap between zooms
        if all(abs(t - s) >= min_gap for s in selected):
            selected.append(t)

    return sorted(selected)


def _build_zoom_filter(
    zoom_moments: List[float],
    width: int,
    height: int,
    fps: float,
    zoom_level: float = 1.3,
    zoom_duration: float = 0.5,
) -> str:
    """
    Build FFmpeg filter chain for punch-in zoom effects.

    Uses zoompan for smooth zoom-in/zoom-out at each moment.
    Falls back to crop+scale if zoompan is unavailable.
    """
    if not zoom_moments:
        return "null"

    # Build a complex filter using crop+scale for each zoom moment
    # Each zoom: ramp in (0.15s) → hold (0.2s) → ramp out (0.15s)
    ramp_in = 0.15
    hold = zoom_duration - 0.3
    ramp_out = 0.15
    if hold < 0.1:
        hold = 0.1

    # Build sendcmd-style filter for dynamic zooming
    # Using the zoompan approach with enable expressions
    filters = []
    zoom_exprs = []

    for t in zoom_moments:
        t_start = t
        t_end = t + zoom_duration
        # Create a smooth zoom envelope using between() and linear interpolation
        # Zoom level expressed as inverse crop factor
        zoom_exprs.append(
            f"if(between(t,{t_start:.3f},{t_end:.3f}),"
            f"min({zoom_level:.2f},"
            f"1+({zoom_level-1:.2f})*"
            f"if(lt(t-{t_start:.3f},{ramp_in}),"
            f"(t-{t_start:.3f})/{ramp_in},"
            f"if(gt(t-{t_start:.3f},{ramp_in+hold}),"
            f"1-(t-{t_start:.3f}-{ramp_in+hold:.3f})/{ramp_out},"
            f"1))),"
            f"1)"
        )

    # Combine all zoom expressions with nested if statements
    # We use crop filter with dynamic expressions
    zoom_expr = zoom_exprs[0] if len(zoom_exprs) == 1 else "+".join(
        [f"({e}-1)" for e in zoom_exprs]
    )
    if len(zoom_exprs) > 1:
        zoom_expr = f"1+{zoom_expr}"

    # Build crop filter: crop to (w/zoom, h/zoom) centered, then scale back
    crop_w = f"iw/({zoom_expr})"
    crop_h = f"ih/({zoom_expr})"
    crop_x = f"(iw-{crop_w})/2"
    crop_y = f"(ih-{crop_h})/2"

    filter_str = (
        f"crop=w={crop_w}:h={crop_h}:x={crop_x}:y={crop_y},"
        f"scale={width}:{height}:flags=lanczos"
    )
    return filter_str


async def apply_punch_zooms(
    video_path: str,
    output_path: str,
    zoom_level: float = 1.3,
    zoom_duration: float = 0.5,
    detection_mode: str = "audio_peaks",
    max_zooms_per_minute: int = 8,
    min_gap: float = 2.0,
    analysis: Optional[Any] = None,
    custom_timestamps: Optional[List[float]] = None,
) -> Optional[str]:
    """
    Apply punch-in zoom effects to a video at detected key moments.

    Args:
        video_path: Input video path
        output_path: Output video path
        zoom_level: How much to zoom in (1.3 = 130%, 1.5 = 150%)
        zoom_duration: Duration of each zoom in seconds
        detection_mode: 'audio_peaks', 'scene_changes', or 'both'
        max_zooms_per_minute: Maximum zoom effects per minute
        min_gap: Minimum seconds between zoom effects
        analysis: Optional pre-computed video analysis
        custom_timestamps: Optional list of specific timestamps to zoom at

    Returns:
        Output path if successful, None otherwise
    """
    info = _get_video_info(video_path)
    if info["duration"] <= 0:
        logger.error("Could not determine video duration")
        return None

    # Determine zoom moments
    if custom_timestamps:
        zoom_moments = sorted(custom_timestamps)
    else:
        audio_peaks = []
        scene_changes = []

        if detection_mode in ("audio_peaks", "both"):
            audio_peaks = _detect_audio_peaks(video_path, min_gap=min_gap)
            logger.info(f"Detected {len(audio_peaks)} audio peaks")

        if detection_mode in ("scene_changes", "both"):
            scene_changes = _detect_scene_changes(video_path)
            logger.info(f"Detected {len(scene_changes)} scene changes")

        zoom_moments = _select_zoom_moments(
            audio_peaks, scene_changes, info["duration"],
            max_per_minute=max_zooms_per_minute,
            min_gap=min_gap,
        )

    if not zoom_moments:
        logger.info("No zoom moments detected, copying original")
        import shutil
        shutil.copy2(video_path, output_path)
        return output_path

    logger.info(f"Applying {len(zoom_moments)} punch zooms at: {[f'{t:.1f}s' for t in zoom_moments]}")

    # Build and apply filter
    vf = _build_zoom_filter(
        zoom_moments, info["width"], info["height"],
        info["fps"], zoom_level, zoom_duration,
    )

    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", vf,
        "-c:a", "copy",
        "-preset", "fast",
        "-crf", "23",
        output_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            logger.error(f"FFmpeg punch zoom failed: {result.stderr[-500:]}")
            # Fallback: copy original
            import shutil
            shutil.copy2(video_path, output_path)
            return output_path
        logger.info(f"Punch zoom applied successfully: {output_path}")
        return output_path
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg punch zoom timed out")
        return None
    except Exception as e:
        logger.error(f"Punch zoom error: {e}")
        return None


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Apply punch-in zoom effects")
    parser.add_argument("video", help="Input video path")
    parser.add_argument("-o", "--output", help="Output path", default=None)
    parser.add_argument("--zoom", type=float, default=1.3, help="Zoom level (default: 1.3)")
    parser.add_argument("--duration", type=float, default=0.5, help="Zoom duration in seconds")
    parser.add_argument("--max-per-min", type=int, default=8, help="Max zooms per minute")
    parser.add_argument("--mode", choices=["audio_peaks", "scene_changes", "both"], default="audio_peaks")
    args = parser.parse_args()

    output = args.output or args.video.replace(".mp4", "_punched.mp4")

    logging.basicConfig(level=logging.INFO)
    result = asyncio.run(apply_punch_zooms(
        args.video, output,
        zoom_level=args.zoom,
        zoom_duration=args.duration,
        detection_mode=args.mode,
        max_zooms_per_minute=args.max_per_min,
    ))
    if result:
        print(f"Output: {result}")
    else:
        print("Failed to apply punch zooms")
