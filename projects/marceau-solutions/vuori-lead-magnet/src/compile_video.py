#!/usr/bin/env python3
"""
Vuori Lead Magnet Video Compiler

Compiles talking head footage with screen recordings into a polished
lead magnet video with transitions, background music, and enhancements.
"""

import os
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from moviepy import (
    VideoFileClip,
    AudioFileClip,
    CompositeVideoClip,
    CompositeAudioClip,
    concatenate_videoclips,
    concatenate_audioclips,
    vfx,
    afx
)
import numpy as np


# Configuration
RECORDINGS_DIR = Path(__file__).parent.parent / "recordings"
OUTPUT_DIR = Path(__file__).parent.parent / "output"
ASSETS_DIR = Path(__file__).parent.parent / "assets"

# Video settings
OUTPUT_WIDTH = 1920
OUTPUT_HEIGHT = 1080
FPS = 30

# Timing configuration based on script
# Total script: ~30 seconds
# Hook.mov is 8.1 seconds - this is the talking head
SCRIPT_SECTIONS = [
    {"name": "hook", "start": 0, "end": 3, "screen_clip": None},  # Face only
    {"name": "problem_spreadsheet", "start": 3, "end": 8, "screen_clip": "01-messy-spreadsheet.mov"},
    {"name": "social_proof", "start": 8, "end": 15, "screen_clip": "02-stats-slide.mov"},
    {"name": "solution_overview", "start": 15, "end": 17, "screen_clip": "03-dashboard-overview.mov"},
    {"name": "solution_stats", "start": 17, "end": 19, "screen_clip": "04-dashboard-stats.mov"},
    {"name": "solution_queue", "start": 19, "end": 21, "screen_clip": "06-dashboard-queue.mov"},
    {"name": "solution_pipeline", "start": 21, "end": 25, "screen_clip": "05-dashboard-pipeline.mov"},
    {"name": "cta_activity", "start": 25, "end": 28, "screen_clip": "07-dashboard-activity.mov"},
    {"name": "cta_close", "start": 28, "end": 30, "screen_clip": "03-dashboard-overview.mov"},  # or logo
]


def ensure_output_dir():
    """Create output directory if it doesn't exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_clip(filename: str, start: float = 0, duration: float = None) -> VideoFileClip:
    """Load a video clip with optional trimming."""
    filepath = RECORDINGS_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Clip not found: {filepath}")

    clip = VideoFileClip(str(filepath))

    if duration:
        clip = clip.subclipped(start, start + duration)

    return clip


def resize_to_fit(clip: VideoFileClip, target_width: int, target_height: int) -> VideoFileClip:
    """Resize clip to fit within target dimensions while maintaining aspect ratio."""
    clip_ratio = clip.w / clip.h
    target_ratio = target_width / target_height

    if clip_ratio > target_ratio:
        # Clip is wider - fit to width
        new_width = target_width
        new_height = int(target_width / clip_ratio)
    else:
        # Clip is taller - fit to height
        new_height = target_height
        new_width = int(target_height * clip_ratio)

    return clip.resized((new_width, new_height))


def add_fade_transition(clip: VideoFileClip, fade_duration: float = 0.3) -> VideoFileClip:
    """Add fade in/out transitions to a clip."""
    return clip.with_effects([
        vfx.FadeIn(fade_duration),
        vfx.FadeOut(fade_duration)
    ])


def add_transition(clip: VideoFileClip, transition_type: str = "none", duration: float = 0.2) -> VideoFileClip:
    """
    Add varied transitions to clips for visual interest.
    Using very short fades to avoid black frames.

    Transition types:
    - none: No transition (hard cut)
    - fade_in: Fade in only (no fade out)
    - fade_out: Fade out only (no fade in)
    - soft: Very subtle fade in/out
    """
    if transition_type == "none":
        # Hard cut - no transition
        return clip

    elif transition_type == "fade_in":
        # Only fade in, hard cut out
        return clip.with_effects([vfx.FadeIn(duration)])

    elif transition_type == "fade_out":
        # Hard cut in, fade out
        return clip.with_effects([vfx.FadeOut(duration)])

    elif transition_type == "soft":
        # Very subtle fade both ways
        return clip.with_effects([
            vfx.FadeIn(duration * 0.5),
            vfx.FadeOut(duration * 0.5)
        ])

    else:
        # Default to no transition
        return clip


def enhance_brightness_contrast(clip: VideoFileClip, brightness: float = 1.1, contrast: float = 1.1) -> VideoFileClip:
    """Apply brightness and contrast enhancement."""
    def adjust(frame):
        # Convert to float for processing
        frame = frame.astype(np.float32)

        # Apply brightness
        frame = frame * brightness

        # Apply contrast (around middle gray)
        frame = (frame - 128) * contrast + 128

        # Clip to valid range
        frame = np.clip(frame, 0, 255)

        return frame.astype(np.uint8)

    return clip.image_transform(adjust)


def create_picture_in_picture(
    main_clip: VideoFileClip,
    pip_clip: VideoFileClip,
    pip_position: str = "bottom-right",
    pip_scale: float = 0.25
) -> CompositeVideoClip:
    """
    Create picture-in-picture effect.

    Args:
        main_clip: The main/background video
        pip_clip: The smaller overlay video
        pip_position: Position of PiP (bottom-right, bottom-left, top-right, top-left)
        pip_scale: Scale of PiP relative to main video width
    """
    # Resize PiP
    pip_width = int(main_clip.w * pip_scale)
    pip_height = int(pip_clip.h * (pip_width / pip_clip.w))
    pip_resized = pip_clip.resized((pip_width, pip_height))

    # Calculate position
    margin = 20
    positions = {
        "bottom-right": (main_clip.w - pip_width - margin, main_clip.h - pip_height - margin),
        "bottom-left": (margin, main_clip.h - pip_height - margin),
        "top-right": (main_clip.w - pip_width - margin, margin),
        "top-left": (margin, margin),
    }

    pos = positions.get(pip_position, positions["bottom-right"])
    pip_positioned = pip_resized.with_position(pos)

    return CompositeVideoClip([main_clip, pip_positioned])


def compile_simple_version():
    """
    Create a simple compiled version: talking head with screen recordings
    interspersed based on the script timing.
    """
    print("Loading talking head clip...")
    talking_head = load_clip("Hook.mov")
    talking_head_audio = talking_head.audio

    # Get actual duration
    th_duration = talking_head.duration
    print(f"Talking head duration: {th_duration:.2f}s")

    # Resize talking head to output resolution
    talking_head = resize_to_fit(talking_head, OUTPUT_WIDTH, OUTPUT_HEIGHT)

    # Apply slight enhancement to talking head
    talking_head = enhance_brightness_contrast(talking_head, brightness=1.05, contrast=1.05)

    # For this simple version, we'll create a sequence where:
    # 1. Show talking head for hook (first 3 seconds)
    # 2. Show screen recordings with voice continuing
    # Since Hook.mov is only 8.1 seconds, we'll use it as the base
    # and create a picture-in-picture or cutaway style

    clips = []

    # Section 1: Pure talking head (0-3s)
    hook_section = talking_head.subclipped(0, min(3, th_duration))
    hook_section = add_fade_transition(hook_section, 0.5)
    clips.append(hook_section)

    # For remaining sections, we need screen recordings
    # Load and prepare screen clips
    screen_clips_info = [
        ("01-messy-spreadsheet.mov", 5),   # Problem section
        ("02-stats-slide.mov", 7),          # Social proof
        ("03-dashboard-overview.mov", 2),   # Solution overview
        ("04-dashboard-stats.mov", 2),      # Stats
        ("06-dashboard-queue.mov", 2),      # Queue
        ("05-dashboard-pipeline.mov", 4),   # Pipeline
        ("07-dashboard-activity.mov", 3),   # Activity
        ("03-dashboard-overview.mov", 2),   # Close
    ]

    for clip_name, duration in screen_clips_info:
        print(f"Processing {clip_name}...")
        try:
            screen_clip = load_clip(clip_name)
            # Trim to needed duration
            actual_duration = min(duration, screen_clip.duration)
            screen_clip = screen_clip.subclipped(0, actual_duration)
            # Resize to output resolution
            screen_clip = resize_to_fit(screen_clip, OUTPUT_WIDTH, OUTPUT_HEIGHT)
            # Center on black background if needed
            screen_clip = screen_clip.with_position("center")
            # Add transition
            screen_clip = add_fade_transition(screen_clip, 0.3)
            clips.append(screen_clip)
        except FileNotFoundError as e:
            print(f"Warning: {e}")
            continue

    print("Concatenating clips...")
    final_video = concatenate_videoclips(clips, method="compose")

    # Add the original audio from talking head, extended with silence or looped
    # For now, use the talking head audio for its duration
    if talking_head_audio:
        # Create audio that spans the full video
        # For sections beyond the talking head, we'll have silence (screen recording ambient)
        final_video = final_video.with_audio(talking_head_audio)

    return final_video


def compile_pip_version():
    """
    Create a picture-in-picture version where talking head appears
    in corner while screen recordings play.
    """
    print("Loading clips for PiP version...")

    talking_head = load_clip("Hook.mov")
    talking_head_audio = talking_head.audio
    th_duration = talking_head.duration

    # Resize talking head
    talking_head = resize_to_fit(talking_head, OUTPUT_WIDTH, OUTPUT_HEIGHT)
    talking_head = enhance_brightness_contrast(talking_head, brightness=1.05, contrast=1.05)

    # For PiP: screen recording is main, talking head is small overlay
    # Since Hook.mov is 8.1s, we'll create a video of that length

    # Load messy spreadsheet as background for problem section
    print("Loading screen clips...")
    screen_bg = load_clip("01-messy-spreadsheet.mov")
    screen_bg = resize_to_fit(screen_bg, OUTPUT_WIDTH, OUTPUT_HEIGHT)
    screen_bg = screen_bg.subclipped(0, min(th_duration, screen_bg.duration))

    # Create PiP composite
    pip_talking_head = talking_head.subclipped(0, min(th_duration, screen_bg.duration))
    pip_talking_head = pip_talking_head.resized(0.3)  # 30% size
    pip_talking_head = pip_talking_head.with_position(("right", "bottom"))

    final_video = CompositeVideoClip([screen_bg, pip_talking_head])

    if talking_head_audio:
        final_video = final_video.with_audio(talking_head_audio)

    return final_video


def compile_full_version():
    """
    Create the full production version with PICTURE-IN-PICTURE style:
    - Screen recordings are FULL SCREEN (main video)
    - Talking head is a small overlay in bottom-right corner
    - Audio comes from talking head videos (original, unprocessed)

    Structure:
    1. HOOK - Messy spreadsheet + talking head PiP
    2. PROBLEM - Messy spreadsheet + talking head PiP
    3. SOCIAL PROOF - Stats slide + talking head PiP
    4. SOLUTION - Dashboard tour + talking head PiP
    5. CTA - Dashboard activity + talking head PiP
    """
    print("=" * 60)
    print("COMPILING PICTURE-IN-PICTURE VERSION")
    print("=" * 60)

    # PiP settings
    PIP_SCALE = 0.35  # 35% of screen width (bigger)
    PIP_MARGIN = 30   # Pixels from edge
    PIP_POSITION = "bottom-left"

    # Custom trim settings per clip - (start_trim, end_trim)
    # Adjusted based on feedback: problem needs more at end, social_proof needs less at start
    TRIM_SETTINGS = {
        "hook": (1.5, 2.0),           # Standard trim
        "problem": (1.5, 1.5),        # Less trim at end (was cutting off too early)
        "social_proof": (1.0, 2.0),   # Less trim at start (was cutting too much)
        "solution": (1.5, 2.0),       # Standard trim
        "cta": (1.5, 2.0),            # Standard trim
    }

    # Load all talking head segments (keep ORIGINAL audio - no enhancement)
    print("\n[1/5] Loading talking head footage (original audio)...")
    print("  Using custom trim settings per clip")
    talking_heads = {}
    th_files = [
        ("Hook_cleaned.mov", "hook"),
        ("Problem_cleaned.mov", "problem"),
        ("Social Proof_cleaned.mov", "social_proof"),
        ("Solution_cleaned.mov", "solution"),
        ("CTA_cleaned.mov", "cta"),
    ]

    for filename, key in th_files:
        try:
            clip = load_clip(filename)
            original_duration = clip.duration

            # Get custom trim for this clip
            trim_start, trim_end = TRIM_SETTINGS.get(key, (1.5, 2.0))

            # Trim the beginning and end to remove record start/stop
            trim_end_time = max(trim_start + 1, clip.duration - trim_end)  # Ensure at least 1s remains
            clip = clip.subclipped(trim_start, trim_end_time)

            # Keep ORIGINAL audio without any processing (also trimmed)
            audio = clip.audio
            # Light enhancement on video only (not audio)
            clip = enhance_brightness_contrast(clip, brightness=1.05, contrast=1.02)
            talking_heads[key] = {"clip": clip, "audio": audio, "duration": clip.duration}
            print(f"  Loaded: {filename} ({original_duration:.2f}s → {clip.duration:.2f}s) [trim: {trim_start}s start, {trim_end}s end]")
        except FileNotFoundError:
            print(f"  Missing: {filename}")

    # Load all screen recordings
    print("\n[2/5] Loading screen recordings...")
    screen_clips = {}
    screen_files = [
        "01-messy-spreadsheet.mov",
        "02-stats-slide.mov",
        "03-dashboard-overview.mov",
        "04-dashboard-stats.mov",
        "05-dashboard-pipeline.mov",
        "06-dashboard-queue.mov",
        "07-dashboard-activity.mov",
    ]

    for filename in screen_files:
        try:
            clip = load_clip(filename)
            clip = resize_to_fit(clip, OUTPUT_WIDTH, OUTPUT_HEIGHT)
            screen_clips[filename] = clip
            print(f"  Loaded: {filename} ({clip.duration:.2f}s)")
        except FileNotFoundError:
            print(f"  Missing: {filename}")

    def create_pip_composite(screen_clip, th_clip, duration):
        """Create a PiP composite with screen as main and talking head in corner."""
        # Ensure screen clip is long enough (loop if needed)
        if screen_clip.duration < duration:
            # Loop the screen clip
            loops_needed = int(duration / screen_clip.duration) + 1
            screen_clip = concatenate_videoclips([screen_clip] * loops_needed)
        screen_clip = screen_clip.subclipped(0, duration)

        # Resize screen to full output size
        screen_clip = screen_clip.resized((OUTPUT_WIDTH, OUTPUT_HEIGHT))

        # Resize talking head for PiP
        pip_width = int(OUTPUT_WIDTH * PIP_SCALE)
        pip_height = int(th_clip.h * (pip_width / th_clip.w))
        th_pip = th_clip.subclipped(0, duration).resized((pip_width, pip_height))

        # Position in bottom-left
        x_pos = PIP_MARGIN
        y_pos = OUTPUT_HEIGHT - pip_height - PIP_MARGIN
        th_pip = th_pip.with_position((x_pos, y_pos))

        # Composite
        composite = CompositeVideoClip([screen_clip, th_pip], size=(OUTPUT_WIDTH, OUTPUT_HEIGHT))
        return composite

    # Build the video sequence
    print("\n[3/5] Building PiP video sequence...")
    video_segments = []
    audio_segments = []

    # Section mapping: which screen recording matches each talking head section
    # Using different transitions for variety: fade_in, fade_out, soft, none
    section_config = [
        ("hook", "01-messy-spreadsheet.mov", "HOOK: Spreadsheet chaos", "fade_in"),
        ("problem", "01-messy-spreadsheet.mov", "PROBLEM: Spreadsheet chaos", "none"),
        ("social_proof", "02-stats-slide.mov", "SOCIAL PROOF: Stats slide", "fade_in"),
        ("solution", "03-dashboard-overview.mov", "SOLUTION: Dashboard overview", "none"),
        ("cta", "07-dashboard-activity.mov", "CTA: Activity feed", "fade_out"),
    ]

    for th_key, screen_name, description, transition in section_config:
        if th_key not in talking_heads:
            print(f"  SKIPPED: {description} (missing talking head)")
            continue

        th = talking_heads[th_key]
        duration = th["duration"]

        # For SOLUTION section, show fewer but LONGER dashboard clips
        # This allows time to see the hover effects properly
        if th_key == "solution":
            # Dashboard tour: use just 2 clips with longer duration each
            # This gives time to show hover effects on stat cards, queue, pipeline
            dashboard_screens = [
                ("03-dashboard-overview.mov", 0.55, "fade_in"),   # Fade in to overview
                ("05-dashboard-pipeline.mov", 0.45, "none"),      # Hard cut to pipeline
            ]

            th_clip = th["clip"]
            current_pos = 0

            for screen_file, portion, dash_transition in dashboard_screens:
                if screen_file in screen_clips:
                    seg_duration = duration * portion
                    screen = screen_clips[screen_file]
                    th_segment = th_clip.subclipped(current_pos, min(current_pos + seg_duration, th_clip.duration))

                    pip_seg = create_pip_composite(screen, th_segment, seg_duration)
                    # Use varied transitions within dashboard section
                    pip_seg = add_transition(pip_seg, dash_transition, 0.2)
                    video_segments.append(pip_seg)
                    current_pos += seg_duration
                    print(f"    Dashboard clip: {screen_file} ({seg_duration:.1f}s) [{dash_transition}]")

            if th["audio"]:
                audio_segments.append(th["audio"])
            print(f"  {description} ({duration:.1f}s) - Dashboard tour (2 clips)")

        else:
            # Standard PiP for other sections with unique transitions
            if screen_name in screen_clips:
                screen = screen_clips[screen_name]
                th_clip = th["clip"]

                pip_composite = create_pip_composite(screen, th_clip, duration)
                pip_composite = add_transition(pip_composite, transition, 0.2)
                video_segments.append(pip_composite)

                if th["audio"]:
                    audio_segments.append(th["audio"])
                print(f"  {description} ({duration:.1f}s) [{transition}]")
            else:
                print(f"  SKIPPED: {description} (missing screen: {screen_name})")

    # Concatenate video
    print("\n[4/5] Concatenating video clips...")
    final_video = concatenate_videoclips(video_segments, method="compose")
    print(f"  Video duration: {final_video.duration:.2f}s")

    # Concatenate audio and boost volume significantly
    print("\n[5/5] Attaching audio (volume boosted)...")
    if audio_segments:
        final_audio = concatenate_audioclips(audio_segments)
        # Boost volume by 2.5x (much louder voice)
        final_audio = final_audio.with_effects([afx.MultiplyVolume(2.5)])
        final_video = final_video.with_audio(final_audio)
        print(f"  Audio duration: {final_audio.duration:.2f}s")
        print("  Volume boosted: 2.5x (louder voice)")

    print(f"\n  TOTAL DURATION: {final_video.duration:.2f}s")

    return final_video


def compile_hook_only_version():
    """
    Create a polished short version using only the Hook.mov with synced audio.
    This is the complete hook section with talking head + quick demo glimpse.
    """
    print("=" * 60)
    print("COMPILING HOOK-ONLY VERSION (8 seconds)")
    print("=" * 60)

    # Load talking head - this has the actual audio
    print("\n[1/4] Loading talking head footage...")
    talking_head = load_clip("Hook.mov")
    talking_head_audio = talking_head.audio
    th_duration = talking_head.duration
    print(f"  Duration: {th_duration:.2f}s")

    # Resize and enhance
    talking_head = resize_to_fit(talking_head, OUTPUT_WIDTH, OUTPUT_HEIGHT)
    talking_head = enhance_brightness_contrast(talking_head, brightness=1.08, contrast=1.05)

    # Load screen recordings for quick cuts
    print("\n[2/4] Loading screen clips for B-roll...")
    screen_clips = {}
    screen_files = ["01-messy-spreadsheet.mov", "03-dashboard-overview.mov"]

    for filename in screen_files:
        try:
            clip = load_clip(filename)
            clip = resize_to_fit(clip, OUTPUT_WIDTH, OUTPUT_HEIGHT)
            clip = enhance_brightness_contrast(clip, brightness=1.02, contrast=1.03)
            screen_clips[filename] = clip
            print(f"  Loaded: {filename}")
        except FileNotFoundError:
            print(f"  Missing: {filename}")

    # Build sequence that matches the 8-second audio
    print("\n[3/4] Building video sequence...")
    clips = []

    # Structure for 8 seconds:
    # 0-3s: Talking head (hook question)
    # 3-5s: Quick messy spreadsheet glimpse
    # 5-6.5s: Dashboard glimpse (the solution)
    # 6.5-8s: Return to talking head (smile)

    # Section 1: Talking head hook (0-3s)
    hook = talking_head.subclipped(0, 3)
    hook = add_fade_transition(hook, 0.3)
    clips.append(hook)
    print("  Added: Hook talking head (0-3s)")

    # Section 2: Quick spreadsheet chaos (3-5s)
    if "01-messy-spreadsheet.mov" in screen_clips:
        chaos = screen_clips["01-messy-spreadsheet.mov"].subclipped(2, 4)
        chaos = add_fade_transition(chaos, 0.2)
        clips.append(chaos)
        print("  Added: Spreadsheet chaos (3-5s)")

    # Section 3: Dashboard solution glimpse (5-6.5s)
    if "03-dashboard-overview.mov" in screen_clips:
        solution = screen_clips["03-dashboard-overview.mov"].subclipped(0, 1.5)
        solution = add_fade_transition(solution, 0.2)
        clips.append(solution)
        print("  Added: Dashboard solution (5-6.5s)")

    # Section 4: Return to talking head with smile (6.5-8s)
    close = talking_head.subclipped(6.5, th_duration)
    close = add_fade_transition(close, 0.3)
    clips.append(close)
    print("  Added: Closing smile (6.5-8s)")

    # Concatenate
    print("\n[4/4] Concatenating and adding audio...")
    final_video = concatenate_videoclips(clips, method="compose")

    # Use the original audio which covers the full 8 seconds
    if talking_head_audio:
        final_video = final_video.with_audio(talking_head_audio)
        print(f"  Audio synced ({talking_head_audio.duration:.2f}s)")

    print(f"  Final duration: {final_video.duration:.2f}s")

    return final_video


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Compile Vuori lead magnet video")
    parser.add_argument(
        "--version",
        choices=["simple", "pip", "full", "hook"],
        default="full",
        help="Which version to compile (default: full)"
    )
    parser.add_argument(
        "--output",
        default="vuori-lead-magnet-final.mp4",
        help="Output filename"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Generate low-res preview (faster)"
    )

    args = parser.parse_args()

    ensure_output_dir()

    print("\n" + "=" * 60)
    print("VUORI LEAD MAGNET VIDEO COMPILER")
    print("=" * 60)
    print(f"Version: {args.version}")
    print(f"Output: {args.output}")
    print(f"Preview mode: {args.preview}")
    print("=" * 60 + "\n")

    # Compile based on version
    if args.version == "simple":
        final_video = compile_simple_version()
    elif args.version == "pip":
        final_video = compile_pip_version()
    elif args.version == "hook":
        final_video = compile_hook_only_version()
    else:
        final_video = compile_full_version()

    # Export settings
    output_path = OUTPUT_DIR / args.output

    if args.preview:
        # Low-res preview
        print("\nExporting preview version...")
        final_video = final_video.resized(0.5)
        final_video.write_videofile(
            str(output_path),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=4
        )
    else:
        # Full quality export
        print("\nExporting full quality version...")
        final_video.write_videofile(
            str(output_path),
            fps=FPS,
            codec="libx264",
            audio_codec="aac",
            bitrate="8000k",
            preset="medium",
            threads=4
        )

    print("\n" + "=" * 60)
    print("EXPORT COMPLETE!")
    print(f"Output: {output_path}")
    print("=" * 60 + "\n")

    # Cleanup
    final_video.close()


if __name__ == "__main__":
    main()
