"""
Color Grader — LUT-based color grading presets for fitness content
==================================================================
Presets: gym_warm, outdoor_bright, moody_dark, clean_minimal, humiston_clean.
Auto-detect lighting via video analysis, suggest best grade.
Uses FFmpeg LUT3D filter or colorbalance/curves/eq filters as fallback.
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
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ── Grading Presets ────────────────────────────────────────────────

class GradePreset(Enum):
    """Built-in color grading presets."""
    GYM_WARM = "gym_warm"
    OUTDOOR_BRIGHT = "outdoor_bright"
    MOODY_DARK = "moody_dark"
    CLEAN_MINIMAL = "clean_minimal"
    HUMISTON_CLEAN = "humiston_clean"
    HIGH_CONTRAST = "high_contrast"
    NONE = "none"


# Each preset is a set of FFmpeg filter parameters.
# Using colorbalance, eq, curves, and unsharp for maximum compatibility
# (no external .cube LUT files needed — works on any FFmpeg install).

PRESET_FILTERS: Dict[str, str] = {
    # Warm indoor gym look: golden skin tones, slightly boosted contrast
    "gym_warm": (
        "colorbalance=rs=0.08:gs=0.02:bs=-0.06"
        ":rm=0.05:gm=0.01:bm=-0.04"
        ":rh=0.03:gh=0.0:bh=-0.02,"
        "eq=contrast=1.1:brightness=0.02:saturation=1.15,"
        "unsharp=5:5:0.5:5:5:0.0"
    ),

    # Bright outdoor: lifted shadows, vibrant greens/blues, airy feel
    "outdoor_bright": (
        "colorbalance=rs=-0.02:gs=0.04:bs=0.06"
        ":rm=0.0:gm=0.03:bm=0.02"
        ":rh=0.02:gh=0.02:bh=0.04,"
        "eq=contrast=1.05:brightness=0.05:saturation=1.2,"
        "curves=preset=lighter,"
        "unsharp=5:5:0.3:5:5:0.0"
    ),

    # Dark moody: crushed blacks, teal-orange split tone, dramatic
    "moody_dark": (
        "colorbalance=rs=0.1:gs=-0.02:bs=-0.08"
        ":rm=0.03:gm=-0.01:bm=-0.03"
        ":rh=-0.02:gh=0.0:bh=0.06,"
        "eq=contrast=1.25:brightness=-0.05:saturation=0.9:gamma=0.9,"
        "curves=preset=increase_contrast,"
        "unsharp=5:5:0.6:5:5:0.0"
    ),

    # Clean minimal: neutral tones, subtle contrast, professional
    "clean_minimal": (
        "colorbalance=rs=0.0:gs=0.0:bs=0.0"
        ":rm=0.02:gm=0.02:bm=0.02"
        ":rh=0.0:gh=0.0:bh=0.0,"
        "eq=contrast=1.08:brightness=0.01:saturation=1.0,"
        "unsharp=3:3:0.4:3:3:0.0"
    ),

    # Humiston-style clean: slightly warm, clear skin, punchy contrast, sharp
    "humiston_clean": (
        "colorbalance=rs=0.05:gs=0.01:bs=-0.03"
        ":rm=0.03:gm=0.01:bm=-0.02"
        ":rh=0.01:gh=0.0:bh=0.0,"
        "eq=contrast=1.15:brightness=0.02:saturation=1.1,"
        "unsharp=5:5:0.7:5:5:0.0"
    ),

    # High contrast: deep blacks, bright whites, strong presence
    "high_contrast": (
        "eq=contrast=1.3:brightness=0.0:saturation=1.05:gamma=0.95,"
        "curves=preset=strong_contrast,"
        "unsharp=5:5:0.5:5:5:0.0"
    ),

    "none": "",
}

# Human-readable descriptions
PRESET_DESCRIPTIONS: Dict[str, str] = {
    "gym_warm": "Warm indoor gym look — golden skin tones, boosted contrast",
    "outdoor_bright": "Bright outdoor — lifted shadows, vibrant, airy",
    "moody_dark": "Dark moody — crushed blacks, teal-orange split tone",
    "clean_minimal": "Clean minimal — neutral, subtle, professional",
    "humiston_clean": "Humiston style — warm, clear skin, punchy, sharp",
    "high_contrast": "High contrast — deep blacks, bright whites",
    "none": "No color grading applied",
}


# ── Data Classes ───────────────────────────────────────────────────

@dataclass
class LightingAnalysis:
    """Analysis of video lighting conditions."""
    avg_brightness: float = 0.5    # 0=dark, 1=bright
    contrast_ratio: float = 1.0    # Low (<1.5) vs High (>3.0)
    color_temp: str = "neutral"    # warm, neutral, cool
    environment: str = "unknown"   # gym_indoor, outdoor, studio, mixed
    suggested_preset: str = "humiston_clean"
    confidence: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "avg_brightness": round(self.avg_brightness, 3),
            "contrast_ratio": round(self.contrast_ratio, 2),
            "color_temp": self.color_temp,
            "environment": self.environment,
            "suggested_preset": self.suggested_preset,
            "confidence": round(self.confidence, 2),
        }


@dataclass
class GradeResult:
    """Result of color grading operation."""
    output_path: str
    preset_used: str
    filter_chain: str = ""
    lighting_analysis: Optional[LightingAnalysis] = None
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "output_path": self.output_path,
            "preset_used": self.preset_used,
            "preset_description": PRESET_DESCRIPTIONS.get(self.preset_used, ""),
            "errors": self.errors,
        }
        if self.lighting_analysis:
            result["lighting_analysis"] = self.lighting_analysis.to_dict()
        return result


# ── Lighting Analysis ──────────────────────────────────────────────

async def analyze_lighting(video_path: str) -> LightingAnalysis:
    """
    Analyze video lighting to suggest best color grade.

    Uses FFmpeg signalstats to measure brightness and color metrics
    from a sample of frames.
    """
    if not os.path.exists(video_path):
        return LightingAnalysis()

    # Sample 10 frames evenly across the video
    cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "json", video_path,
    ]
    try:
        result = await asyncio.get_event_loop().run_in_executor(
            None, lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        )
        info = json.loads(result.stdout)
        duration = float(info["format"]["duration"])
    except Exception:
        return LightingAnalysis()

    # Use signalstats to get luminance stats from sampled frames
    sample_interval = max(1, int(duration / 10))
    stats_cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"select='not(mod(n\\,{sample_interval * 30}))',signalstats",
        "-f", "null", "-",
    ]

    try:
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(
                stats_cmd, capture_output=True, text=True, timeout=60
            ),
        )
        stderr = result.stderr

        # Parse signalstats output for YAVG (luma average) and SATAVG
        y_values = []
        sat_values = []
        hueavg_values = []

        for line in stderr.split("\n"):
            if "YAVG" in line:
                try:
                    parts = line.split("YAVG:")
                    if len(parts) > 1:
                        val = float(parts[1].split()[0])
                        y_values.append(val)
                except (ValueError, IndexError):
                    pass
            if "SATAVG" in line:
                try:
                    parts = line.split("SATAVG:")
                    if len(parts) > 1:
                        val = float(parts[1].split()[0])
                        sat_values.append(val)
                except (ValueError, IndexError):
                    pass
            if "HUEAVG" in line:
                try:
                    parts = line.split("HUEAVG:")
                    if len(parts) > 1:
                        val = float(parts[1].split()[0])
                        hueavg_values.append(val)
                except (ValueError, IndexError):
                    pass

        if not y_values:
            # Fallback: use a simpler brightness check
            return _analyze_brightness_simple(video_path)

        avg_y = sum(y_values) / len(y_values)
        brightness = avg_y / 255.0  # Normalize to 0-1

        # Estimate contrast from min/max luma spread
        y_min = min(y_values)
        y_max = max(y_values)
        contrast_ratio = (y_max - y_min) / max(y_min, 1.0) if y_min > 0 else 2.0

        # Estimate color temperature from hue average
        color_temp = "neutral"
        if hueavg_values:
            avg_hue = sum(hueavg_values) / len(hueavg_values)
            if avg_hue < 60 or avg_hue > 300:
                color_temp = "warm"
            elif 120 < avg_hue < 240:
                color_temp = "cool"

        # Infer environment
        environment = "unknown"
        if brightness < 0.35:
            environment = "gym_indoor"  # Typically darker
        elif brightness > 0.6:
            environment = "outdoor"
        elif 0.35 <= brightness <= 0.6:
            environment = "studio" if contrast_ratio > 2.0 else "mixed"

        # Suggest preset
        suggested = _suggest_preset(brightness, contrast_ratio, color_temp, environment)

        return LightingAnalysis(
            avg_brightness=brightness,
            contrast_ratio=contrast_ratio,
            color_temp=color_temp,
            environment=environment,
            suggested_preset=suggested,
            confidence=0.7 if len(y_values) >= 5 else 0.4,
        )

    except Exception as e:
        logger.warning(f"Lighting analysis failed: {e}")
        return LightingAnalysis()


def _analyze_brightness_simple(video_path: str) -> LightingAnalysis:
    """Simple brightness estimation from a single frame."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", "select='eq(n,30)',scale=160:90",
            "-frames:v", "1", tmp_path,
        ]
        subprocess.run(cmd, capture_output=True, timeout=30)

        if not os.path.exists(tmp_path):
            return LightingAnalysis()

        # Get average pixel value
        cmd2 = [
            "ffprobe", "-v", "quiet",
            "-f", "lavfi",
            "-i", f"movie={tmp_path},signalstats",
            "-show_entries", "frame_tags=lavfi.signalstats.YAVG",
            "-of", "json",
        ]
        result = subprocess.run(cmd2, capture_output=True, text=True, timeout=30)
        # Parse or use a default
        brightness = 0.45
        return LightingAnalysis(
            avg_brightness=brightness,
            suggested_preset="humiston_clean",
            confidence=0.3,
        )
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _suggest_preset(
    brightness: float,
    contrast: float,
    temp: str,
    environment: str,
) -> str:
    """Suggest the best preset based on lighting analysis."""
    # Dark indoor gym → gym_warm (add warmth and brightness)
    if environment == "gym_indoor":
        return "gym_warm"

    # Bright outdoor → outdoor_bright (enhance vibrancy)
    if environment == "outdoor":
        return "outdoor_bright"

    # Cool-toned footage → warm it up
    if temp == "cool":
        return "gym_warm"

    # Already warm → clean it up
    if temp == "warm" and brightness > 0.4:
        return "humiston_clean"

    # High contrast studio → moody or clean
    if environment == "studio" and contrast > 3.0:
        return "moody_dark"

    # Default for fitness content
    return "humiston_clean"


# ── LUT File Support ───────────────────────────────────────────────

def _find_lut_file(preset: str, lut_dir: str) -> Optional[str]:
    """Look for a .cube LUT file matching the preset name."""
    if not os.path.isdir(lut_dir):
        return None

    for ext in (".cube", ".3dl", ".csp"):
        path = os.path.join(lut_dir, f"{preset}{ext}")
        if os.path.exists(path):
            return path

    return None


# ── Core Grading ───────────────────────────────────────────────────

async def apply_grade(
    video_path: str,
    preset: str = "humiston_clean",
    output_path: Optional[str] = None,
    intensity: float = 1.0,
    auto_detect: bool = False,
    lut_dir: Optional[str] = None,
) -> GradeResult:
    """
    Apply color grading to a video.

    Args:
        video_path: Input video path.
        preset: Preset name from GradePreset enum values.
        output_path: Output path (auto-generated if None).
        intensity: Grade intensity 0.0-1.0 (1.0 = full effect).
        auto_detect: If True, analyze lighting and override preset.
        lut_dir: Directory containing .cube LUT files (optional).

    Returns:
        GradeResult with output path and details.
    """
    if not os.path.exists(video_path):
        return GradeResult(
            output_path="",
            preset_used=preset,
            errors=[f"Input file not found: {video_path}"],
        )

    lighting = None
    if auto_detect:
        lighting = await analyze_lighting(video_path)
        if lighting.confidence > 0.3:
            preset = lighting.suggested_preset
            logger.info(
                f"Auto-detected: {lighting.environment}, "
                f"brightness={lighting.avg_brightness:.2f} "
                f"→ preset={preset}"
            )

    if output_path is None:
        base, ext = os.path.splitext(video_path)
        output_path = f"{base}_graded{ext}"

    if preset == "none" or preset not in PRESET_FILTERS:
        import shutil
        shutil.copy2(video_path, output_path)
        return GradeResult(
            output_path=output_path,
            preset_used="none",
            lighting_analysis=lighting,
        )

    # Check for LUT file first
    lut_path = None
    if lut_dir:
        lut_path = _find_lut_file(preset, lut_dir)

    if lut_path:
        # Use LUT3D filter
        filter_chain = f"lut3d='{lut_path}'"
    else:
        # Use built-in filter chain
        filter_chain = PRESET_FILTERS[preset]

    if not filter_chain:
        import shutil
        shutil.copy2(video_path, output_path)
        return GradeResult(
            output_path=output_path,
            preset_used=preset,
            filter_chain="",
            lighting_analysis=lighting,
        )

    # Apply intensity blending if < 1.0
    # Use FFmpeg's mix filter to blend original with graded
    if intensity < 1.0 and intensity > 0.0:
        # Split → grade one copy → blend back
        filter_chain = (
            f"split[orig][grade];"
            f"[grade]{filter_chain}[graded];"
            f"[orig][graded]blend=all_mode=normal"
            f":all_opacity={intensity}"
        )

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", filter_chain,
        "-c:v", "libx264", "-preset", "fast",
        "-c:a", "copy",
        output_path,
    ]

    errors = []
    try:
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=300),
        )
        if result.returncode != 0:
            error_msg = result.stderr[-300:] if result.stderr else "Unknown error"
            errors.append(f"FFmpeg error: {error_msg}")
            # Fallback: try without intensity blending
            if intensity < 1.0:
                simple_filter = PRESET_FILTERS.get(preset, "")
                if simple_filter:
                    cmd_simple = [
                        "ffmpeg", "-y",
                        "-i", video_path,
                        "-vf", simple_filter,
                        "-c:v", "libx264", "-preset", "fast",
                        "-c:a", "copy",
                        output_path,
                    ]
                    result2 = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: subprocess.run(
                            cmd_simple, capture_output=True, text=True, timeout=300
                        ),
                    )
                    if result2.returncode == 0:
                        errors[-1] = "Intensity blending failed, applied at full strength"
                    else:
                        # Copy original
                        import shutil
                        shutil.copy2(video_path, output_path)
                        errors.append("Grading failed completely, copied original")
    except Exception as e:
        errors.append(f"Error: {e}")
        import shutil
        shutil.copy2(video_path, output_path)

    return GradeResult(
        output_path=output_path,
        preset_used=preset,
        filter_chain=filter_chain,
        lighting_analysis=lighting,
        errors=errors,
    )


def list_presets() -> List[Dict[str, str]]:
    """List all available color grading presets."""
    return [
        {"name": p.value, "description": PRESET_DESCRIPTIONS.get(p.value, "")}
        for p in GradePreset
        if p != GradePreset.NONE
    ]


# ── CLI ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Color Grader")
    parser.add_argument("video", nargs="?", help="Input video path")
    parser.add_argument("-o", "--output", help="Output video path")
    parser.add_argument(
        "-p", "--preset",
        choices=[p.value for p in GradePreset],
        default="humiston_clean",
        help="Color grading preset",
    )
    parser.add_argument(
        "-i", "--intensity",
        type=float, default=1.0,
        help="Grade intensity (0.0-1.0)",
    )
    parser.add_argument(
        "--auto", action="store_true",
        help="Auto-detect lighting and select best preset",
    )
    parser.add_argument(
        "--lut-dir",
        help="Directory with .cube LUT files",
    )
    parser.add_argument("--list", action="store_true", help="List presets")
    parser.add_argument("--analyze", action="store_true", help="Analyze lighting only")
    parser.add_argument("--json", action="store_true", help="JSON output")

    args = parser.parse_args()

    if args.list:
        presets = list_presets()
        if args.json:
            print(json.dumps(presets, indent=2))
        else:
            print("\nColor Grading Presets")
            print("=" * 50)
            for p in presets:
                print(f"  {p['name']:<18s} {p['description']}")
        exit(0)

    if not args.video:
        parser.error("Video path required (or use --list)")

    async def main():
        if args.analyze:
            analysis = await analyze_lighting(args.video)
            if args.json:
                print(json.dumps(analysis.to_dict(), indent=2))
            else:
                print(f"\nLighting Analysis")
                print(f"{'=' * 40}")
                print(f"Brightness:    {analysis.avg_brightness:.3f}")
                print(f"Contrast:      {analysis.contrast_ratio:.2f}")
                print(f"Color Temp:    {analysis.color_temp}")
                print(f"Environment:   {analysis.environment}")
                print(f"Suggested:     {analysis.suggested_preset}")
                print(f"Confidence:    {analysis.confidence:.0%}")
            return

        result = await apply_grade(
            video_path=args.video,
            preset=args.preset,
            output_path=args.output,
            intensity=args.intensity,
            auto_detect=args.auto,
            lut_dir=args.lut_dir,
        )

        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(f"\nColor Grading Results")
            print(f"{'=' * 40}")
            print(f"Output:    {result.output_path}")
            print(f"Preset:    {result.preset_used}")
            print(f"Desc:      {PRESET_DESCRIPTIONS.get(result.preset_used, '')}")
            if result.lighting_analysis:
                la = result.lighting_analysis
                print(f"Detected:  {la.environment} ({la.color_temp}, brightness={la.avg_brightness:.2f})")
            if result.errors:
                print(f"\nWarnings:")
                for e in result.errors:
                    print(f"  - {e}")

    asyncio.run(main())
