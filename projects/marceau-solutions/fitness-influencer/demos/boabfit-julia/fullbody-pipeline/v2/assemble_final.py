#!/usr/bin/env python3
"""Assemble final Julia full-body video with captions + background music."""
import os
import sys
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), '.env'))

from moviepy import (
    VideoFileClip, AudioFileClip, CompositeVideoClip,
    CompositeAudioClip, TextClip, VideoClip
)

BASE = Path(__file__).parent
DEMO_DIR = BASE.parent.parent  # boabfit-julia/

# Input files
VIDEO_PATH = str(BASE / 'julia-omnihuman.mp4')
AUDIO_PATH = str(BASE / 'julia-voiceover-v2.mp3')
MUSIC_PATH = str(DEMO_DIR / 'bg-beat.wav')
OUTPUT_PATH = str(BASE / 'julia-fullbody-final-v2.mp4')

# Caption data — timed to the voiceover
CAPTIONS = [
    (0.0, 2.0, "Hey girls! Welcome back."),
    (2.0, 5.0, "Today we are hitting glutes"),
    (5.0, 7.5, "and I promise you,"),
    (7.5, 10.0, "this routine is going to\nhave you feeling the BURN."),
    (10.0, 13.0, "Hip thrusts, kickbacks,\nand Romanian deadlifts."),
    (13.0, 15.5, "No excuses, just results."),
    (15.5, 18.5, "Grab your bands,\ngrab your weights,"),
    (18.5, 20.5, "and let's get to work."),
    (20.5, 22.8, "You ready? LET'S GO!"),
]

# Brand colors
BRAND_PINK = (255, 105, 180)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


def create_caption_frame(text, width, height):
    """Create a caption overlay frame using Pillow."""
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Try to get a bold font
    font_size = 48
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", font_size)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()

    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Center horizontally, position at ~75% height
    x = (width - text_w) // 2
    y = int(height * 0.75)

    # Draw background pill
    padding = 16
    pill_x0 = x - padding
    pill_y0 = y - padding
    pill_x1 = x + text_w + padding
    pill_y1 = y + text_h + padding
    draw.rounded_rectangle(
        [pill_x0, pill_y0, pill_x1, pill_y1],
        radius=12,
        fill=(0, 0, 0, 180)
    )

    # Draw text with outline for readability
    for dx in [-2, -1, 0, 1, 2]:
        for dy in [-2, -1, 0, 1, 2]:
            if dx == 0 and dy == 0:
                continue
            draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0, 255))
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

    return np.array(img)


def main():
    print("=== Julia Full-Body Video Assembly v2 ===\n")

    # Load video
    print(f"Loading video: {VIDEO_PATH}")
    video = VideoFileClip(VIDEO_PATH)
    w, h = video.size
    duration = video.duration
    print(f"  {w}x{h}, {duration:.1f}s, {video.fps}fps")

    # Load voiceover
    print(f"Loading voiceover: {AUDIO_PATH}")
    voiceover = AudioFileClip(AUDIO_PATH)
    print(f"  {voiceover.duration:.1f}s")

    # Load background music (if exists)
    bg_music = None
    if os.path.exists(MUSIC_PATH):
        print(f"Loading background music: {MUSIC_PATH}")
        bg_music = AudioFileClip(MUSIC_PATH)
        # Loop music to match video duration and reduce volume
        if bg_music.duration < duration:
            loops_needed = int(duration / bg_music.duration) + 1
            from moviepy import concatenate_audioclips
            bg_music = concatenate_audioclips([bg_music] * loops_needed)
        bg_music = bg_music.subclipped(0, min(duration, voiceover.duration))
        bg_music = bg_music.with_volume_scaled(0.08)  # Very quiet behind voice
        print(f"  Music ducked to 8% volume")

    # Pre-render caption frames
    print("Pre-rendering captions...")
    caption_frames = {}
    for start, end, text in CAPTIONS:
        caption_frames[(start, end)] = create_caption_frame(text, w, h)
        print(f"  [{start:.1f}-{end:.1f}] {text[:40]}...")

    # Build composite with captions burned in
    def make_frame(t):
        base = video.get_frame(min(t, duration - 0.04))

        # Find active caption
        for (start, end), cap_frame in caption_frames.items():
            if start <= t < end:
                # Composite RGBA caption onto RGB video
                alpha = cap_frame[:, :, 3:4].astype(float) / 255.0
                rgb = cap_frame[:, :, :3].astype(float)
                base_f = base.astype(float)

                # Resize caption if needed
                if cap_frame.shape[0] != base.shape[0] or cap_frame.shape[1] != base.shape[1]:
                    from PIL import Image as PILImage
                    cap_pil = PILImage.fromarray(cap_frame)
                    cap_pil = cap_pil.resize((base.shape[1], base.shape[0]), PILImage.LANCZOS)
                    cap_frame = np.array(cap_pil)
                    alpha = cap_frame[:, :, 3:4].astype(float) / 255.0
                    rgb = cap_frame[:, :, :3].astype(float)

                blended = base_f * (1 - alpha) + rgb * alpha
                return blended.astype(np.uint8)

        return base

    use_duration = min(duration, voiceover.duration)
    final_video = VideoClip(make_frame, duration=use_duration).with_fps(video.fps)

    # Mix audio
    if bg_music:
        mixed_audio = CompositeAudioClip([voiceover.subclipped(0, use_duration), bg_music])
    else:
        mixed_audio = voiceover.subclipped(0, use_duration)

    final_video = final_video.with_audio(mixed_audio)

    # Export
    print(f"\nExporting to: {OUTPUT_PATH}")
    final_video.write_videofile(
        OUTPUT_PATH,
        fps=25,
        codec='libx264',
        audio_codec='aac',
        bitrate='5000k',
        preset='medium',
        logger=None
    )

    size_mb = os.path.getsize(OUTPUT_PATH) / 1024 / 1024
    print(f"\n{'=' * 50}")
    print(f"  DONE!")
    print(f"  Output: {OUTPUT_PATH}")
    print(f"  Size: {size_mb:.1f} MB")
    print(f"  Duration: {use_duration:.1f}s")
    print(f"{'=' * 50}")

    video.close()
    voiceover.close()
    if bg_music:
        bg_music.close()


if __name__ == '__main__':
    main()
