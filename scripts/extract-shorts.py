#!/usr/bin/env python3
"""
extract-shorts.py — Extract YouTube Shorts from Processed Videos

WHAT: Splits a video into 15-60 second segments for YouTube Shorts / TikTok / Reels
WHY:  Maximize content output from a single long-form video
INPUT: A processed video file (MP4)
OUTPUT: Segments in output/shorts/[date]/ named 001.mp4, 002.mp4, etc.
COST: FREE (FFmpeg only)

USAGE:
  python scripts/extract-shorts.py --input output/processed/2026-03-17/video_processed.mp4
  python scripts/extract-shorts.py --input video.mp4 --duration 30
  python scripts/extract-shorts.py --input video.mp4 --output ~/Desktop/shorts
  python scripts/extract-shorts.py --input video.mp4 --split-at-silence
"""

import argparse
import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import date


def get_video_duration(path: str) -> float:
    """Get video duration in seconds via ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Error getting duration: {e}")
        return 0.0


def detect_silence_points(path: str, threshold_db: float = -35, min_dur: float = 0.3) -> list:
    """
    Detect silence points in video. Returns list of timestamps (seconds)
    where silence starts — these are natural split points.
    """
    cmd = [
        "ffmpeg", "-i", path,
        "-af", f"silencedetect=n={threshold_db}dB:d={min_dur}",
        "-f", "null", "-"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        points = []
        for line in result.stderr.split('\n'):
            if 'silence_start' in line:
                try:
                    t = float(line.split('silence_start: ')[1].split()[0])
                    points.append(t)
                except (IndexError, ValueError):
                    pass
        return points
    except Exception as e:
        print(f"  Warning: silence detection failed: {e}")
        return []


def split_at_fixed_intervals(
    input_path: str,
    output_dir: str,
    segment_duration: float = 45.0,
    min_duration: float = 15.0,
    max_duration: float = 60.0,
) -> list:
    """Split video into fixed-length segments."""
    total = get_video_duration(input_path)
    if total <= 0:
        print("Error: could not determine video duration")
        return []

    segments = []
    current = 0.0
    idx = 1

    while current < total:
        remaining = total - current
        dur = min(segment_duration, remaining)

        # Skip segments shorter than minimum
        if dur < min_duration:
            break

        # Cap at max duration
        dur = min(dur, max_duration)

        output_file = os.path.join(output_dir, f"{idx:03d}.mp4")

        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{current:.3f}",
            "-i", input_path,
            "-t", f"{dur:.3f}",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            # Vertical crop for Shorts (9:16) — center crop from landscape
            # Only apply if the video is landscape
            output_file
        ]

        print(f"  Segment {idx:03d}: {current:.1f}s - {current + dur:.1f}s ({dur:.1f}s)")

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and os.path.exists(output_file):
            segments.append({
                "file": output_file,
                "start": current,
                "end": current + dur,
                "duration": dur,
            })
            idx += 1
        else:
            print(f"  Warning: failed to extract segment {idx}")
            if result.stderr:
                # Print last line of stderr for debugging
                err_lines = result.stderr.strip().split('\n')
                print(f"    {err_lines[-1]}")

        current += dur

    return segments


def split_at_silence(
    input_path: str,
    output_dir: str,
    target_duration: float = 45.0,
    min_duration: float = 15.0,
    max_duration: float = 60.0,
) -> list:
    """
    Split video at natural pause points (silence).
    Falls back to fixed intervals if no silence detected.
    """
    total = get_video_duration(input_path)
    if total <= 0:
        print("Error: could not determine video duration")
        return []

    print("  Detecting natural pause points...")
    silence_points = detect_silence_points(input_path)

    if not silence_points:
        print("  No silence points found, falling back to fixed intervals")
        return split_at_fixed_intervals(
            input_path, output_dir, target_duration, min_duration, max_duration
        )

    print(f"  Found {len(silence_points)} pause points")

    # Build segments by grouping silence points to stay near target_duration
    segments = []
    current_start = 0.0
    idx = 1

    for sp in silence_points:
        segment_len = sp - current_start

        # If this segment is long enough, cut here
        if segment_len >= min_duration:
            # If it's getting too long, force a cut
            if segment_len >= max_duration:
                # Cut at max_duration
                cut_point = current_start + max_duration
                output_file = os.path.join(output_dir, f"{idx:03d}.mp4")
                dur = max_duration

                cmd = [
                    "ffmpeg", "-y",
                    "-ss", f"{current_start:.3f}",
                    "-i", input_path,
                    "-t", f"{dur:.3f}",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                    "-c:a", "aac", "-b:a", "128k",
                    "-movflags", "+faststart",
                    output_file
                ]

                print(f"  Segment {idx:03d}: {current_start:.1f}s - {cut_point:.1f}s ({dur:.1f}s)")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode == 0 and os.path.exists(output_file):
                    segments.append({
                        "file": output_file,
                        "start": current_start,
                        "end": cut_point,
                        "duration": dur,
                    })
                    idx += 1
                current_start = cut_point

            elif segment_len >= target_duration * 0.8:
                # Close enough to target, cut at this silence point
                output_file = os.path.join(output_dir, f"{idx:03d}.mp4")
                dur = sp - current_start

                cmd = [
                    "ffmpeg", "-y",
                    "-ss", f"{current_start:.3f}",
                    "-i", input_path,
                    "-t", f"{dur:.3f}",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                    "-c:a", "aac", "-b:a", "128k",
                    "-movflags", "+faststart",
                    output_file
                ]

                print(f"  Segment {idx:03d}: {current_start:.1f}s - {sp:.1f}s ({dur:.1f}s)")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode == 0 and os.path.exists(output_file):
                    segments.append({
                        "file": output_file,
                        "start": current_start,
                        "end": sp,
                        "duration": dur,
                    })
                    idx += 1
                current_start = sp

    # Handle remaining content
    remaining = total - current_start
    if remaining >= min_duration:
        dur = min(remaining, max_duration)
        output_file = os.path.join(output_dir, f"{idx:03d}.mp4")

        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{current_start:.3f}",
            "-i", input_path,
            "-t", f"{dur:.3f}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            output_file
        ]

        print(f"  Segment {idx:03d}: {current_start:.1f}s - {current_start + dur:.1f}s ({dur:.1f}s)")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and os.path.exists(output_file):
            segments.append({
                "file": output_file,
                "start": current_start,
                "end": current_start + dur,
                "duration": dur,
            })

    return segments


def main():
    parser = argparse.ArgumentParser(
        description='Extract YouTube Shorts segments from processed video'
    )
    parser.add_argument('--input', required=True, help='Input video file')
    parser.add_argument('--output', help='Output directory (default: output/shorts/[date])')
    parser.add_argument('--duration', type=float, default=45,
                        help='Target segment duration in seconds (default: 45)')
    parser.add_argument('--min-duration', type=float, default=15,
                        help='Minimum segment duration (default: 15)')
    parser.add_argument('--max-duration', type=float, default=60,
                        help='Maximum segment duration (default: 60)')
    parser.add_argument('--split-at-silence', action='store_true',
                        help='Split at natural pauses instead of fixed intervals')

    args = parser.parse_args()

    # Validate input
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        return 1

    # Set output directory
    if args.output:
        output_dir = args.output
    else:
        project_root = Path(__file__).resolve().parent.parent
        output_dir = str(project_root / "output" / "shorts" / date.today().isoformat())

    os.makedirs(output_dir, exist_ok=True)

    # Get video info
    total_duration = get_video_duration(args.input)
    input_name = os.path.basename(args.input)

    print()
    print("=" * 60)
    print("  SHORTS EXTRACTOR -- Marceau Fitness")
    print("=" * 60)
    print(f"  Input:      {input_name}")
    print(f"  Duration:   {total_duration:.1f}s ({total_duration / 60:.1f} min)")
    print(f"  Target:     {args.duration}s segments")
    print(f"  Range:      {args.min_duration}s - {args.max_duration}s")
    print(f"  Method:     {'Silence detection' if args.split_at_silence else 'Fixed intervals'}")
    print(f"  Output:     {output_dir}")
    print("=" * 60)
    print()

    # Split video
    if args.split_at_silence:
        segments = split_at_silence(
            args.input, output_dir,
            target_duration=args.duration,
            min_duration=args.min_duration,
            max_duration=args.max_duration,
        )
    else:
        segments = split_at_fixed_intervals(
            args.input, output_dir,
            segment_duration=args.duration,
            min_duration=args.min_duration,
            max_duration=args.max_duration,
        )

    # Summary
    print()
    print("=" * 60)
    print("  EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"  Segments created: {len(segments)}")
    if segments:
        total_seg_dur = sum(s['duration'] for s in segments)
        print(f"  Total content:    {total_seg_dur:.1f}s ({total_seg_dur / 60:.1f} min)")
        print(f"  Output dir:       {output_dir}")
        print()
        print("  Files:")
        for s in segments:
            print(f"    {os.path.basename(s['file'])}  ({s['duration']:.1f}s)")
    print("=" * 60)
    print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
