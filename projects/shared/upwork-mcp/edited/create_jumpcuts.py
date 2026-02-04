#!/usr/bin/env python3
"""
Create jump cuts by removing silent portions from video.
Parses ffmpeg silencedetect output and generates segment file.
"""

import re
import subprocess
import os

def parse_silence_file(filepath):
    """Parse silencedetect output to get silence intervals."""
    silences = []
    current_start = None

    with open(filepath, 'r') as f:
        for line in f:
            # Match silence_start
            start_match = re.search(r'silence_start:\s*([\d.]+)', line)
            if start_match:
                current_start = float(start_match.group(1))

            # Match silence_end
            end_match = re.search(r'silence_end:\s*([\d.]+)', line)
            if end_match and current_start is not None:
                silences.append((current_start, float(end_match.group(1))))
                current_start = None

    return silences

def get_speaking_segments(silences, video_duration, min_duration=0.15, padding=0.15):
    """
    Convert silence intervals to speaking intervals, filtering short segments.

    Args:
        padding: Seconds to add before/after each segment to preserve word edges
    """
    segments = []
    current_pos = 0.0

    for silence_start, silence_end in silences:
        if silence_start > current_pos:
            duration = silence_start - current_pos
            # Only keep segments longer than min_duration
            if duration >= min_duration:
                # Add padding: start earlier, end later (but clamp to bounds)
                padded_start = max(0, current_pos - padding)
                padded_end = min(silence_start + padding, video_duration)
                segments.append((padded_start, padded_end))
        current_pos = silence_end

    # Add final segment if there's speaking after last silence
    if current_pos < video_duration:
        duration = video_duration - current_pos
        if duration >= min_duration:
            padded_start = max(0, current_pos - padding)
            segments.append((padded_start, video_duration))

    return segments

def main():
    # Use the properly combined file
    input_file = 'combined_proper.mp4'
    silence_file = 'silence_proper.txt'
    output_file = 'upwork_profile_final.mp4'

    # Parse silence file
    silences = parse_silence_file(silence_file)
    print(f"Found {len(silences)} silence segments")

    # Get video duration
    result = subprocess.run([
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', input_file
    ], capture_output=True, text=True)
    video_duration = float(result.stdout.strip())
    print(f"Video duration: {video_duration:.2f}s")

    # Get speaking segments with padding to preserve word beginnings/endings
    # padding=0.25 adds 250ms buffer before and after each segment
    segments = get_speaking_segments(silences, video_duration, min_duration=0.2, padding=0.25)

    # Manual adjustments for specific segments that need more time
    # Extend segment 4 (index 3) to capture "SKUs" - add 0.5s to end
    # Extend segment 5 (index 4) to capture "help" - add 0.5s to end
    adjusted_segments = []
    for i, (start, end) in enumerate(segments):
        if i == 3:  # Segment 4 - "SKUs" clip
            end = min(end + 0.5, video_duration)
        elif i == 4:  # Segment 5 - CTA "help" clip
            end = min(end + 0.5, video_duration)
        adjusted_segments.append((start, end))
    segments = adjusted_segments

    print(f"Found {len(segments)} speaking segments (after filtering)")

    # Calculate total speaking time
    total_speaking = sum(end - start for start, end in segments)
    removed = video_duration - total_speaking
    print(f"Speaking time: {total_speaking:.2f}s")
    print(f"Silence to remove: {removed:.2f}s ({removed/video_duration*100:.1f}%)")

    print(f"\nSegments to keep:")
    for i, (start, end) in enumerate(segments):
        print(f"  {i+1}. {start:.2f}s - {end:.2f}s ({end-start:.2f}s)")

    # Use segment approach: extract each segment and concatenate
    print("\nExtracting segments...")

    segment_files = []
    for i, (start, end) in enumerate(segments):
        segment_file = f'segment_{i:03d}.mp4'
        segment_files.append(segment_file)

        cmd = [
            'ffmpeg', '-y', '-ss', str(start), '-i', input_file,
            '-t', str(end - start),
            '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '18',
            '-c:a', 'aac', '-b:a', '192k',
            '-avoid_negative_ts', 'make_zero',
            segment_file
        ]
        subprocess.run(cmd, capture_output=True)
        print(f"  Extracted segment {i+1}/{len(segments)}")

    # Create concat list
    print("\nConcatenating segments...")
    with open('segments_list.txt', 'w') as f:
        for sf in segment_files:
            f.write(f"file '{sf}'\n")

    # Concatenate
    cmd = [
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
        '-i', 'segments_list.txt',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-c:a', 'aac', '-b:a', '192k',
        output_file
    ]
    subprocess.run(cmd, capture_output=True)

    # Clean up segment files
    print("Cleaning up temporary files...")
    for sf in segment_files:
        if os.path.exists(sf):
            os.remove(sf)
    if os.path.exists('segments_list.txt'):
        os.remove('segments_list.txt')

    # Get final duration
    result = subprocess.run([
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', output_file
    ], capture_output=True, text=True)
    final_duration = float(result.stdout.strip())

    print(f"\n{'='*50}")
    print(f"DONE!")
    print(f"{'='*50}")
    print(f"Original: {video_duration:.2f}s ({video_duration/60:.1f} min)")
    print(f"Final: {final_duration:.2f}s ({final_duration/60:.1f} min)")
    print(f"Removed: {video_duration - final_duration:.2f}s ({(video_duration - final_duration)/video_duration*100:.1f}%)")
    print(f"\nOutput: {output_file}")

if __name__ == '__main__':
    main()
