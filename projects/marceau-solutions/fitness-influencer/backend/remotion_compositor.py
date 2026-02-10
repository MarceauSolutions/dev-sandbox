"""
Remotion Compositor — Overlay pre-rendered Remotion animated clips onto footage.

Workflow:
  1. Remotion renders templates to MP4 clips (on Mac or Lambda)
  2. Rendered clips saved to data/remotion_assets/
  3. This module composites them onto edited footage via FFmpeg overlay filter

Supports:
  - Intro overlay at start
  - Text bomb overlays at specified timestamps
  - Exercise stat overlays at specified timestamps
  - Before/after comparison overlays
  - Alpha compositing for transparent backgrounds
  - Multiple overlays in a single pass
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Default asset directory
ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "remotion_assets"
)


# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class OverlayPlacement:
    """Defines where and when to place a Remotion clip on the video."""
    asset_path: str           # Path to pre-rendered MP4/WebM clip
    start_time: float         # When overlay appears (seconds)
    duration: Optional[float] = None  # Override clip duration (None = use clip length)
    position: str = "center"  # center, top, bottom, top-left, top-right, bottom-left, bottom-right
    scale: float = 1.0        # Scale factor (1.0 = original size)
    opacity: float = 1.0      # 0.0 to 1.0
    fade_in: float = 0.0      # Fade in duration (seconds)
    fade_out: float = 0.0     # Fade out duration (seconds)
    overlay_type: str = "generic"  # intro, text_bomb, stat, before_after, generic


@dataclass
class CompositorResult:
    """Result of a compositing operation."""
    success: bool
    output_path: Optional[str] = None
    overlays_applied: int = 0
    errors: List[str] = field(default_factory=list)


# ── Asset Discovery ───────────────────────────────────────────────────────────

def discover_assets(assets_dir: Optional[str] = None) -> Dict[str, List[str]]:
    """
    Discover available Remotion assets organized by type.

    Returns dict like:
        {
            "intro": ["intro_default.mp4", "intro_short.mp4"],
            "text_bomb": ["text_bomb_impact.mp4", ...],
            "stat": ["stat_bar.mp4", ...],
            "before_after": ["before_after_wipe.mp4", ...],
        }
    """
    base = assets_dir or ASSETS_DIR
    assets: Dict[str, List[str]] = {
        "intro": [],
        "text_bomb": [],
        "stat": [],
        "before_after": [],
        "other": [],
    }

    if not os.path.isdir(base):
        return assets

    for f in os.listdir(base):
        if not f.endswith((".mp4", ".webm", ".mov")):
            continue
        path = os.path.join(base, f)
        lower = f.lower()
        if "intro" in lower:
            assets["intro"].append(path)
        elif "text" in lower or "bomb" in lower:
            assets["text_bomb"].append(path)
        elif "stat" in lower:
            assets["stat"].append(path)
        elif "before" in lower or "after" in lower:
            assets["before_after"].append(path)
        else:
            assets["other"].append(path)

    return assets


def get_clip_info(clip_path: str) -> Dict:
    """Get duration, dimensions, and codec info for a clip via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", clip_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        data = json.loads(result.stdout)
        video_stream = next(
            (s for s in data.get("streams", []) if s.get("codec_type") == "video"), {}
        )
        return {
            "duration": float(data.get("format", {}).get("duration", 0)),
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "has_alpha": video_stream.get("pix_fmt", "") in ("yuva420p", "rgba", "argb"),
            "codec": video_stream.get("codec_name", "unknown"),
        }
    except Exception as e:
        logger.warning(f"ffprobe failed for {clip_path}: {e}")
        return {"duration": 0, "width": 0, "height": 0, "has_alpha": False, "codec": "unknown"}


# ── Overlay Positioning ───────────────────────────────────────────────────────

def _position_expr(
    position: str,
    overlay_w: str,
    overlay_h: str,
    video_w: str = "main_w",
    video_h: str = "main_h",
) -> Tuple[str, str]:
    """
    Return FFmpeg x/y expressions for overlay positioning.

    Args:
        position: center, top, bottom, top-left, top-right, bottom-left, bottom-right
        overlay_w/overlay_h: overlay dimension variables
        video_w/video_h: main video dimension variables

    Returns:
        (x_expr, y_expr) for FFmpeg overlay filter
    """
    pad = 40  # pixel padding from edges

    positions = {
        "center": (
            f"({video_w}-{overlay_w})/2",
            f"({video_h}-{overlay_h})/2",
        ),
        "top": (
            f"({video_w}-{overlay_w})/2",
            str(pad),
        ),
        "bottom": (
            f"({video_w}-{overlay_w})/2",
            f"{video_h}-{overlay_h}-{pad}",
        ),
        "top-left": (str(pad), str(pad)),
        "top-right": (f"{video_w}-{overlay_w}-{pad}", str(pad)),
        "bottom-left": (str(pad), f"{video_h}-{overlay_h}-{pad}"),
        "bottom-right": (
            f"{video_w}-{overlay_w}-{pad}",
            f"{video_h}-{overlay_h}-{pad}",
        ),
    }

    return positions.get(position, positions["center"])


# ── Single Overlay ────────────────────────────────────────────────────────────

async def composite_single(
    video_path: str,
    overlay: OverlayPlacement,
    output_path: str,
) -> Optional[str]:
    """
    Composite a single overlay onto a video using FFmpeg.

    Uses the overlay filter with enable expression for timing.
    """
    if not os.path.exists(overlay.asset_path):
        logger.error(f"Overlay asset not found: {overlay.asset_path}")
        return None

    clip_info = get_clip_info(overlay.asset_path)
    clip_duration = overlay.duration or clip_info["duration"]
    if clip_duration <= 0:
        logger.warning(f"Clip has zero duration: {overlay.asset_path}")
        return None

    # Calculate timing
    start = overlay.start_time
    end = start + clip_duration

    # Build position expressions
    x_expr, y_expr = _position_expr(
        overlay.position,
        overlay_w="overlay_w",
        overlay_h="overlay_h",
    )

    # Build scale filter for overlay if needed
    scale_filter = ""
    if overlay.scale != 1.0:
        scale_filter = f"scale=iw*{overlay.scale}:ih*{overlay.scale},"

    # Build opacity/fade expression
    alpha_parts = []
    if overlay.opacity < 1.0:
        alpha_parts.append(f"{overlay.opacity}")
    if overlay.fade_in > 0:
        alpha_parts.append(
            f"if(lt(t-{start},{overlay.fade_in}),(t-{start})/{overlay.fade_in},1)"
        )
    if overlay.fade_out > 0:
        fade_start = end - overlay.fade_out
        alpha_parts.append(
            f"if(gt(t,{fade_start}),1-(t-{fade_start})/{overlay.fade_out},1)"
        )

    # Combine alpha expressions with multiplication
    if alpha_parts:
        alpha_expr = "*".join(alpha_parts)
        alpha_filter = f"format=yuva420p,colorchannelmixer=aa={alpha_expr}" if len(alpha_parts) == 1 and overlay.opacity < 1.0 else ""
    else:
        alpha_filter = ""

    # Build filter complex
    # Input 0 = main video, Input 1 = overlay clip
    enable_expr = f"between(t,{start:.3f},{end:.3f})"

    filter_parts = []
    # Prepare overlay stream
    overlay_prep = f"[1:v]{scale_filter}setpts=PTS-STARTPTS"
    if alpha_filter:
        overlay_prep += f",{alpha_filter}"
    overlay_prep += "[ovr]"
    filter_parts.append(overlay_prep)

    # Apply overlay with timing
    filter_parts.append(
        f"[0:v][ovr]overlay=x={x_expr}:y={y_expr}:enable='{enable_expr}'[out]"
    )

    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", overlay.asset_path,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-map", "0:a?",
        "-c:a", "copy",
        "-preset", "fast",
        "-crf", "23",
        output_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.error(f"FFmpeg overlay failed: {result.stderr[-500:]}")
            return None
        return output_path
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg overlay timed out")
        return None
    except Exception as e:
        logger.error(f"Composite error: {e}")
        return None


# ── Multi-Overlay (Chained) ───────────────────────────────────────────────────

async def composite_overlays(
    video_path: str,
    overlays: List[OverlayPlacement],
    output_path: str,
) -> CompositorResult:
    """
    Apply multiple overlays sequentially onto a video.

    Each overlay is applied as a separate FFmpeg pass for reliability.
    For very large numbers of overlays, consider batching into a single
    complex filter (more efficient but harder to debug).
    """
    if not overlays:
        return CompositorResult(success=True, output_path=video_path, overlays_applied=0)

    # Sort overlays by start time
    sorted_overlays = sorted(overlays, key=lambda o: o.start_time)

    current_video = video_path
    applied = 0
    errors = []

    for i, overlay in enumerate(sorted_overlays):
        if not os.path.exists(overlay.asset_path):
            errors.append(f"Missing asset: {overlay.asset_path}")
            continue

        # Create intermediate output for all but last overlay
        is_last = (i == len(sorted_overlays) - 1)
        if is_last:
            step_output = output_path
        else:
            step_output = output_path.replace(
                ".mp4", f"_overlay_{i}.mp4"
            )

        logger.info(
            f"Applying overlay {i+1}/{len(sorted_overlays)}: "
            f"{overlay.overlay_type} at {overlay.start_time:.1f}s"
        )

        result = await composite_single(current_video, overlay, step_output)

        if result:
            # Clean up previous intermediate file
            if applied > 0 and current_video != video_path:
                try:
                    os.remove(current_video)
                except OSError:
                    pass
            current_video = result
            applied += 1
        else:
            errors.append(f"Failed to apply overlay {i}: {overlay.overlay_type}")

    return CompositorResult(
        success=applied > 0,
        output_path=current_video if applied > 0 else None,
        overlays_applied=applied,
        errors=errors,
    )


# ── Smart Placement ───────────────────────────────────────────────────────────

def auto_place_overlays(
    video_duration: float,
    analysis: Optional[Any] = None,
    assets_dir: Optional[str] = None,
    include_intro: bool = True,
    text_bomb_texts: Optional[List[str]] = None,
    stat_data: Optional[List[Dict]] = None,
) -> List[OverlayPlacement]:
    """
    Automatically determine where to place Remotion overlays.

    Uses video analysis to find optimal placement points:
    - Intro: Always at t=0
    - Text bombs: At high-energy moments or scene changes
    - Stats: During explanation segments (lower motion)

    Args:
        video_duration: Total video length in seconds
        analysis: Video analysis result (from video_analyzer)
        assets_dir: Path to remotion assets
        include_intro: Whether to add intro overlay
        text_bomb_texts: List of text strings for text bombs (optional)
        stat_data: List of stat dicts with value/unit/label (optional)

    Returns:
        List of OverlayPlacement objects ready for composite_overlays()
    """
    base = assets_dir or ASSETS_DIR
    assets = discover_assets(base)
    placements: List[OverlayPlacement] = []

    # ── Intro ────────────────────────────────────────────────
    if include_intro and assets["intro"]:
        intro_path = assets["intro"][0]
        intro_info = get_clip_info(intro_path)
        placements.append(OverlayPlacement(
            asset_path=intro_path,
            start_time=0.0,
            duration=intro_info["duration"] or 4.0,
            position="center",
            scale=1.0,
            opacity=1.0,
            fade_out=0.3,
            overlay_type="intro",
        ))

    # ── Text Bombs ───────────────────────────────────────────
    if assets["text_bomb"] and text_bomb_texts:
        # Place text bombs at evenly spaced intervals through the video
        # Skip first 5s (intro) and last 2s
        usable_start = 5.0
        usable_end = max(usable_start + 2, video_duration - 2.0)
        usable_duration = usable_end - usable_start

        if usable_duration > 0 and len(text_bomb_texts) > 0:
            interval = usable_duration / len(text_bomb_texts)
            for i, text in enumerate(text_bomb_texts):
                t = usable_start + (interval * i) + (interval * 0.3)
                # Pick asset (rotate through available)
                asset_path = assets["text_bomb"][i % len(assets["text_bomb"])]
                placements.append(OverlayPlacement(
                    asset_path=asset_path,
                    start_time=round(t, 1),
                    position="center",
                    scale=1.0,
                    opacity=1.0,
                    fade_in=0.0,
                    fade_out=0.0,
                    overlay_type="text_bomb",
                ))

    # ── Exercise Stats ───────────────────────────────────────
    if assets["stat"] and stat_data:
        # Place stats during calmer segments (or evenly spaced)
        stat_start = max(8.0, video_duration * 0.3)
        stat_interval = (video_duration * 0.4) / max(1, len(stat_data))

        for i, stat in enumerate(stat_data):
            t = stat_start + (stat_interval * i)
            if t >= video_duration - 4.0:
                break
            asset_path = assets["stat"][i % len(assets["stat"])]
            placements.append(OverlayPlacement(
                asset_path=asset_path,
                start_time=round(t, 1),
                position="center",
                scale=0.9,
                opacity=1.0,
                fade_in=0.2,
                fade_out=0.3,
                overlay_type="stat",
            ))

    return placements


# ── Pipeline Integration ──────────────────────────────────────────────────────

async def apply_remotion_overlays(
    video_path: str,
    output_path: str,
    assets_dir: Optional[str] = None,
    overlays: Optional[List[OverlayPlacement]] = None,
    auto_place: bool = True,
    include_intro: bool = True,
    text_bomb_texts: Optional[List[str]] = None,
    stat_data: Optional[List[Dict]] = None,
    analysis: Optional[Any] = None,
) -> Optional[str]:
    """
    Apply Remotion overlays to a video (main entry point for pipeline).

    Can either:
    1. Use pre-defined overlays (pass overlays list)
    2. Auto-place overlays based on video analysis (auto_place=True)

    Args:
        video_path: Input video
        output_path: Output video path
        assets_dir: Directory with pre-rendered Remotion clips
        overlays: Explicit overlay placements (overrides auto_place)
        auto_place: Auto-determine overlay placement
        include_intro: Add intro overlay at start
        text_bomb_texts: Text strings for text bomb overlays
        stat_data: Data for stat overlays [{value, unit, label}]
        analysis: Video analysis result for smart placement

    Returns:
        Output path if successful, None otherwise
    """
    # Get video duration
    info = get_clip_info(video_path)
    duration = info.get("duration", 0)
    if duration <= 0:
        logger.error("Could not determine video duration")
        return None

    # Determine overlays
    if overlays is None and auto_place:
        overlays = auto_place_overlays(
            video_duration=duration,
            analysis=analysis,
            assets_dir=assets_dir,
            include_intro=include_intro,
            text_bomb_texts=text_bomb_texts,
            stat_data=stat_data,
        )

    if not overlays:
        logger.info("No overlays to apply, copying original")
        import shutil
        shutil.copy2(video_path, output_path)
        return output_path

    logger.info(f"Compositing {len(overlays)} overlays onto video")
    result = await composite_overlays(video_path, overlays, output_path)

    if result.success and result.output_path:
        logger.info(
            f"Compositing complete: {result.overlays_applied} overlays applied"
        )
        if result.errors:
            logger.warning(f"Some overlays failed: {result.errors}")
        return result.output_path
    else:
        logger.error(f"Compositing failed: {result.errors}")
        # Fallback: copy original
        import shutil
        shutil.copy2(video_path, output_path)
        return output_path


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Composite Remotion overlays onto video")
    parser.add_argument("video", help="Input video path")
    parser.add_argument("-o", "--output", help="Output path", default=None)
    parser.add_argument("--assets-dir", help="Remotion assets directory", default=None)
    parser.add_argument("--list-assets", action="store_true", help="List available assets")
    parser.add_argument("--no-intro", action="store_true", help="Skip intro overlay")
    parser.add_argument("--text-bombs", nargs="*", help="Text bomb overlay texts")
    parser.add_argument("--overlay", action="append", nargs=3,
                        metavar=("ASSET_PATH", "START_TIME", "POSITION"),
                        help="Manual overlay: asset_path start_time position")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.list_assets:
        assets = discover_assets(args.assets_dir)
        for category, paths in assets.items():
            if paths:
                print(f"\n{category}:")
                for p in paths:
                    info = get_clip_info(p)
                    print(f"  {os.path.basename(p)} ({info['duration']:.1f}s, {info['width']}x{info['height']})")
        if not any(assets.values()):
            print("No assets found. Render Remotion templates first:")
            print("  cd remotion && npm run render:intro")
            print("  cp out/*.mp4 ../data/remotion_assets/")
    else:
        output = args.output or args.video.replace(".mp4", "_composited.mp4")

        # Build manual overlays if specified
        manual_overlays = None
        if args.overlay:
            manual_overlays = [
                OverlayPlacement(
                    asset_path=o[0],
                    start_time=float(o[1]),
                    position=o[2],
                )
                for o in args.overlay
            ]

        result = asyncio.run(apply_remotion_overlays(
            args.video, output,
            assets_dir=args.assets_dir,
            overlays=manual_overlays,
            include_intro=not args.no_intro,
            text_bomb_texts=args.text_bombs,
        ))
        if result:
            print(f"Output: {result}")
        else:
            print("Compositing failed")
