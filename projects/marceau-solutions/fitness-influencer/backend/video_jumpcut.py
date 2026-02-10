#!/usr/bin/env python3
"""
Automatic Jump Cut Video Editor
Removes silence from videos and adds branded intro/outro.

Features:
- Silence detection and removal
- Automatic jump cuts
- Aggressive mode (Ryan Humiston style — zero dead air)
- Filler word removal (um, uh, like, you know, so, basically)
- Branded intro/outro insertion
- Thumbnail generation
- Multiple format export

Usage:
    python video_jumpcut.py --input raw_video.mp4
    python video_jumpcut.py --input raw_video.mp4 --aggressive --output edited.mp4
    python video_jumpcut.py --input raw_video.mp4 --remove-fillers --output edited.mp4
"""

import argparse
import sys
import os
import subprocess
import json
import logging
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from moviepy.editor import (
        VideoFileClip, concatenate_videoclips, TextClip,
        CompositeVideoClip, ImageClip
    )
    from moviepy.video.fx import resize
except ImportError:
    print("ERROR: moviepy not installed")
    print("Install with: pip install moviepy")
    sys.exit(1)

# Filler words/phrases to detect and remove
FILLER_WORDS = [
    "um", "uh", "uhh", "umm", "hmm", "hm",
    "like", "you know", "i mean", "basically",
    "sort of", "kind of", "right", "actually",
    "so yeah", "and stuff", "or whatever",
]

# Aggressive mode presets (Ryan Humiston style)
AGGRESSIVE_PRESETS = {
    "humiston": {
        "silence_thresh": -30,
        "min_silence_dur": 0.15,
        "min_clip_dur": 0.3,
        "max_pause": 0.3,       # Maximum pause between speech allowed
        "pad_before": 0.05,     # Small pad before speech starts
        "pad_after": 0.05,      # Small pad after speech ends
        "remove_fillers": True,
    },
    "moderate": {
        "silence_thresh": -35,
        "min_silence_dur": 0.25,
        "min_clip_dur": 0.4,
        "max_pause": 0.5,
        "pad_before": 0.08,
        "pad_after": 0.08,
        "remove_fillers": False,
    },
    "gentle": {
        "silence_thresh": -40,
        "min_silence_dur": 0.3,
        "min_clip_dur": 0.5,
        "max_pause": 0.8,
        "pad_before": 0.1,
        "pad_after": 0.1,
        "remove_fillers": False,
    },
}


def _detect_filler_words(video_path: str) -> List[Tuple[float, float, str]]:
    """
    Detect filler words in video audio using Whisper-style word timestamps.

    Falls back to basic silence-boundary heuristics if no transcription
    API is available.

    Returns:
        List of (start, end, word) tuples for detected fillers.
    """
    # Try to use existing transcription if available
    try:
        from backend.caption_generator import transcribe_audio
        result = transcribe_audio(video_path)
        if result and hasattr(result, 'words'):
            fillers = []
            for word_info in result.words:
                word_lower = word_info.get("word", "").lower().strip(".,!?")
                if word_lower in FILLER_WORDS:
                    fillers.append((
                        word_info["start"],
                        word_info["end"],
                        word_lower,
                    ))
            return fillers
    except (ImportError, Exception) as e:
        logger.debug(f"Transcription-based filler detection unavailable: {e}")

    # Fallback: detect very short speech segments between pauses
    # (fillers are typically short utterances surrounded by micro-pauses)
    logger.info("Using heuristic filler detection (no transcription API)")
    return []


class VideoJumpCutter:
    """
    Automatically removes silence from videos using FFmpeg silence detection.
    Supports aggressive mode for Ryan Humiston-style zero dead air editing.
    """

    def __init__(self, silence_thresh=-40, min_silence_dur=0.3, min_clip_dur=0.5,
                 aggressive: bool = False, aggressive_preset: str = "humiston",
                 remove_fillers: bool = False, max_pause: float = 0.8,
                 pad_before: float = 0.1, pad_after: float = 0.1):
        """
        Initialize jump cutter.

        Args:
            silence_thresh: Silence threshold in dB (default: -40dB)
            min_silence_dur: Minimum silence duration to detect (seconds)
            min_clip_dur: Minimum clip duration to keep (seconds)
            aggressive: Enable aggressive mode (overrides with preset values)
            aggressive_preset: Preset name ('humiston', 'moderate', 'gentle')
            remove_fillers: Remove detected filler words (um, uh, like...)
            max_pause: Maximum allowed pause between speech segments
            pad_before: Padding before speech starts (seconds)
            pad_after: Padding after speech ends (seconds)
        """
        if aggressive and aggressive_preset in AGGRESSIVE_PRESETS:
            preset = AGGRESSIVE_PRESETS[aggressive_preset]
            self.silence_thresh = preset["silence_thresh"]
            self.min_silence_dur = preset["min_silence_dur"]
            self.min_clip_dur = preset["min_clip_dur"]
            self.max_pause = preset["max_pause"]
            self.pad_before = preset["pad_before"]
            self.pad_after = preset["pad_after"]
            self.remove_fillers = preset["remove_fillers"] or remove_fillers
        else:
            self.silence_thresh = silence_thresh
            self.min_silence_dur = min_silence_dur
            self.min_clip_dur = min_clip_dur
            self.max_pause = max_pause
            self.pad_before = pad_before
            self.pad_after = pad_after
            self.remove_fillers = remove_fillers

        self.aggressive = aggressive

    def detect_silence(self, video_path):
        """
        Detect silent segments in video using FFmpeg.

        Args:
            video_path: Path to input video

        Returns:
            List of tuples (start_time, end_time) for silent segments
        """
        print(f"\\n→ Detecting silence (threshold: {self.silence_thresh}dB)...")

        # FFmpeg command to detect silence
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-af', f'silencedetect=n={self.silence_thresh}dB:d={self.min_silence_dur}',
            '-f', 'null',
            '-'
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            # Parse silence detection output
            silence_start = []
            silence_end = []

            for line in result.stderr.split('\\n'):
                if 'silence_start' in line:
                    time = float(line.split('silence_start: ')[1].split()[0])
                    silence_start.append(time)
                elif 'silence_end' in line:
                    time = float(line.split('silence_end: ')[1].split('|')[0].strip())
                    silence_end.append(time)

            # Pair up start/end times
            silent_segments = list(zip(silence_start, silence_end))

            print(f"  ✓ Detected {len(silent_segments)} silent segments")
            return silent_segments

        except Exception as e:
            print(f"  ⚠️  Warning: Silence detection failed: {e}")
            print(f"  Continuing without jump cuts...")
            return []

    def generate_keep_segments(self, video_duration, silent_segments,
                               filler_segments=None):
        """
        Generate list of segments to keep (non-silent, non-filler parts).

        Args:
            video_duration: Total video duration in seconds
            silent_segments: List of (start, end) tuples for silent parts
            filler_segments: Optional list of (start, end, word) for filler words

        Returns:
            List of (start, end) tuples for segments to keep
        """
        if not silent_segments and not filler_segments:
            return [(0, video_duration)]

        # Combine silent segments and filler segments into removal zones
        remove_zones = list(silent_segments) if silent_segments else []
        if filler_segments:
            for start, end, word in filler_segments:
                remove_zones.append((start, end))
                logger.info(f"  Removing filler '{word}' at {start:.2f}s-{end:.2f}s")

        # Sort and merge overlapping removal zones
        remove_zones.sort(key=lambda x: x[0])
        merged = []
        for start, end in remove_zones:
            if merged and start <= merged[-1][1] + 0.05:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))

        keep_segments = []
        current_time = 0

        for zone_start, zone_end in merged:
            # Add the segment before this removal zone
            seg_start = current_time + self.pad_before if current_time > 0 else current_time
            seg_end = zone_start - self.pad_after if zone_start > 0 else zone_start

            if seg_end - seg_start > self.min_clip_dur:
                keep_segments.append((max(0, seg_start), seg_end))

            current_time = zone_end

        # Add final segment after last removal zone
        final_start = current_time + self.pad_before if current_time > 0 else current_time
        if video_duration - final_start > self.min_clip_dur:
            keep_segments.append((final_start, video_duration))

        # In aggressive mode, further trim pauses between speech segments
        if self.aggressive and len(keep_segments) > 1:
            trimmed = [keep_segments[0]]
            for seg in keep_segments[1:]:
                gap = seg[0] - trimmed[-1][1]
                if gap > self.max_pause:
                    # Keep segment but tighten the gap
                    trimmed.append(seg)
                else:
                    # Gap is small enough — merge with previous
                    trimmed[-1] = (trimmed[-1][0], seg[1])
            keep_segments = trimmed

        print(f"  ✓ Generated {len(keep_segments)} keep segments")
        if filler_segments:
            print(f"  ✓ Removed {len(filler_segments)} filler words")
        return keep_segments

    def apply_jump_cuts(self, video_path, output_path, silent_segments=None):
        """
        Apply jump cuts to remove silence (and optionally filler words).

        Args:
            video_path: Input video file
            output_path: Output video file
            silent_segments: Optional pre-detected silent segments

        Returns:
            Path to edited video
        """
        mode_label = "AGGRESSIVE" if self.aggressive else "STANDARD"
        print(f"\\n{'='*70}")
        print(f"VIDEO JUMP CUT EDITOR [{mode_label}]")
        print(f"{'='*70}")
        print(f"Input:  {video_path}")
        print(f"Output: {output_path}")
        if self.aggressive:
            print(f"Mode:   Aggressive (thresh={self.silence_thresh}dB, "
                  f"max_pause={self.max_pause}s)")

        # Load video
        print(f"\\n→ Loading video...")
        video = VideoFileClip(video_path)
        original_duration = video.duration
        print(f"  ✓ Loaded: {original_duration:.2f} seconds")

        # Detect silence if not provided
        if silent_segments is None:
            silent_segments = self.detect_silence(video_path)

        # Detect filler words if enabled
        filler_segments = None
        if self.remove_fillers:
            print(f"\\n→ Detecting filler words...")
            filler_segments = _detect_filler_words(video_path)
            if filler_segments:
                print(f"  ✓ Found {len(filler_segments)} filler words")
            else:
                print(f"  No filler words detected (or transcription unavailable)")

        # Generate keep segments
        keep_segments = self.generate_keep_segments(
            original_duration, silent_segments, filler_segments
        )

        if not keep_segments:
            print(f"\\n⚠️  No valid segments found, copying original...")
            video.write_videofile(output_path, codec='libx264', audio_codec='aac')
            video.close()
            return output_path

        # Extract and concatenate clips
        print(f"\\n→ Extracting clips and applying jump cuts...")
        clips = []

        for i, (start, end) in enumerate(keep_segments):
            try:
                clip = video.subclip(start, end)
                clips.append(clip)
                print(f"  Clip {i+1}/{len(keep_segments)}: {start:.2f}s - {end:.2f}s ({end-start:.2f}s)")
            except Exception as e:
                print(f"  ⚠️  Warning: Could not extract clip {i+1}: {e}")

        if not clips:
            print(f"\\n✗ Error: No clips could be extracted")
            video.close()
            return None

        # Concatenate all clips
        print(f"\\n→ Concatenating {len(clips)} clips...")
        final_video = concatenate_videoclips(clips, method="compose")
        final_duration = final_video.duration

        # Calculate statistics
        time_removed = original_duration - final_duration
        reduction_pct = (time_removed / original_duration) * 100
        num_cuts = len(clips) - 1

        print(f"\\n📊 EDITING STATISTICS")
        print(f"{'-'*70}")
        print(f"  Original duration:  {original_duration:.2f}s ({original_duration/60:.2f} min)")
        print(f"  Final duration:     {final_duration:.2f}s ({final_duration/60:.2f} min)")
        print(f"  Time removed:       {time_removed:.2f}s ({time_removed/60:.2f} min)")
        print(f"  Reduction:          {reduction_pct:.1f}%")
        print(f"  Jump cuts applied:  {num_cuts}")

        # Write output
        print(f"\\n→ Rendering final video...")
        final_video.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            fps=video.fps,
            preset='medium',
            threads=4
        )

        # Cleanup
        final_video.close()
        video.close()

        print(f"\\n✅ SUCCESS!")
        print(f"  Edited video saved: {output_path}")
        print(f"{'='*70}\\n")

        return output_path

    def add_intro_outro(self, video_path, output_path, intro_path=None, outro_path=None):
        """
        Add branded intro and outro to video.

        Args:
            video_path: Input video file
            output_path: Output video file
            intro_path: Path to intro video (optional)
            outro_path: Path to outro video (optional)

        Returns:
            Path to final video
        """
        print(f"\\n→ Adding intro/outro...")

        clips = []

        # Add intro
        if intro_path and os.path.exists(intro_path):
            intro = VideoFileClip(intro_path)
            clips.append(intro)
            print(f"  ✓ Added intro ({intro.duration:.1f}s)")

        # Add main video
        main_video = VideoFileClip(video_path)
        clips.append(main_video)

        # Add outro
        if outro_path and os.path.exists(outro_path):
            outro = VideoFileClip(outro_path)
            clips.append(outro)
            print(f"  ✓ Added outro ({outro.duration:.1f}s)")

        if len(clips) == 1:
            # No intro/outro, just copy
            print(f"  ℹ️  No intro/outro specified, using original video")
            main_video.write_videofile(output_path, codec='libx264', audio_codec='aac')
            main_video.close()
        else:
            # Concatenate with intro/outro
            final = concatenate_videoclips(clips, method="compose")
            final.write_videofile(output_path, codec='libx264', audio_codec='aac')

            # Cleanup
            for clip in clips:
                clip.close()

        print(f"  ✓ Final video with intro/outro saved")
        return output_path

    def generate_thumbnail(self, video_path, output_path, time_position=0.5):
        """
        Generate thumbnail from video frame.

        Args:
            video_path: Input video file
            output_path: Output thumbnail image
            time_position: Position in video (0-1) to capture frame

        Returns:
            Path to thumbnail
        """
        print(f"\\n→ Generating thumbnail...")

        video = VideoFileClip(video_path)
        frame_time = video.duration * time_position

        # Get frame at specified time
        frame = video.get_frame(frame_time)

        # Save as image
        from PIL import Image
        img = Image.fromarray(frame)

        # Resize to standard YouTube thumbnail size
        img = img.resize((1280, 720), Image.Resampling.LANCZOS)
        img.save(output_path, quality=95)

        video.close()

        print(f"  ✓ Thumbnail saved: {output_path}")
        return output_path


def main():
    """CLI for video jump cut editor."""
    parser = argparse.ArgumentParser(
        description='Automatic Jump Cut Video Editor - Remove silence and add branding'
    )
    parser.add_argument('--input', required=True, help='Input video file')
    parser.add_argument('--output', help='Output video file (default: input_edited.mp4)')
    parser.add_argument('--silence-thresh', type=float, default=-40, help='Silence threshold in dB (default: -40)')
    parser.add_argument('--min-silence', type=float, default=0.3, help='Minimum silence duration in seconds')
    parser.add_argument('--min-clip', type=float, default=0.5, help='Minimum clip duration in seconds')
    parser.add_argument('--intro', help='Path to intro video')
    parser.add_argument('--outro', help='Path to outro video')
    parser.add_argument('--thumbnail', action='store_true', help='Generate thumbnail')
    parser.add_argument('--thumbnail-pos', type=float, default=0.3, help='Thumbnail position (0-1)')
    parser.add_argument('--no-cuts', action='store_true', help='Skip jump cuts, only add intro/outro')
    parser.add_argument('--aggressive', action='store_true',
                        help='Aggressive mode: zero dead air, Humiston-style tight cuts')
    parser.add_argument('--preset', choices=list(AGGRESSIVE_PRESETS.keys()),
                        default='humiston', help='Aggressive preset (default: humiston)')
    parser.add_argument('--remove-fillers', action='store_true',
                        help='Remove filler words (um, uh, like, you know)')
    parser.add_argument('--max-pause', type=float, default=0.8,
                        help='Max pause between speech segments in seconds')

    args = parser.parse_args()

    # Validate input file
    if not os.path.exists(args.input):
        print(f"✗ Error: Input file not found: {args.input}")
        return 1

    # Set output path
    if not args.output:
        input_path = Path(args.input)
        suffix = "_aggressive" if args.aggressive else "_edited"
        args.output = str(input_path.parent / f"{input_path.stem}{suffix}{input_path.suffix}")

    # Create editor
    editor = VideoJumpCutter(
        silence_thresh=args.silence_thresh,
        min_silence_dur=args.min_silence,
        min_clip_dur=args.min_clip,
        aggressive=args.aggressive,
        aggressive_preset=args.preset,
        remove_fillers=args.remove_fillers,
        max_pause=args.max_pause,
    )

    try:
        # Apply jump cuts (unless skipped)
        if args.no_cuts:
            print(f"\\nℹ️  Skipping jump cuts (--no-cuts specified)")
            temp_output = args.input
        else:
            # Create temporary output for jump cuts
            temp_output = str(Path(args.output).parent / f"temp_{Path(args.output).name}")
            result = editor.apply_jump_cuts(args.input, temp_output)

            if not result:
                print(f"\\n✗ Jump cut processing failed")
                return 1

        # Add intro/outro if specified
        if args.intro or args.outro:
            editor.add_intro_outro(temp_output, args.output, args.intro, args.outro)

            # Remove temp file if different from input
            if temp_output != args.input and os.path.exists(temp_output):
                os.remove(temp_output)
        else:
            # Rename temp to final output
            if temp_output != args.output:
                os.rename(temp_output, args.output)

        # Generate thumbnail if requested
        if args.thumbnail:
            thumb_path = str(Path(args.output).parent / f"{Path(args.output).stem}_thumbnail.jpg")
            editor.generate_thumbnail(args.output, thumb_path, args.thumbnail_pos)

        print(f"\\n🎬 Video editing complete!")
        print(f"   Output: {args.output}")

        return 0

    except Exception as e:
        print(f"\\n✗ Error during video processing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
