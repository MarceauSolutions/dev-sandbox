#!/usr/bin/env python3
"""
Assemble v4 Julia Full-Body Video — Stock Footage + Face Swap Edition.

Pipeline: Real stock footage (Pexels) + face swap (Replicate roop) + production effects.
This gives us real exercise physics with Julia's face for character consistency.

Production effects (carried from v3):
  1. Whip pan transitions at segment boundaries
  2. Flash/white burst at exercise entry points
  3. Gym-warm color grade
  4. Animated circle PiP (scales up, pulses gently)
  5. Larger, bolder captions with pink highlight on key words
  6. Vignette overlay for cinematic feel
"""
import os
import sys
import math
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), '.env'))

from moviepy import (
    VideoFileClip, AudioFileClip, CompositeVideoClip,
    CompositeAudioClip, VideoClip, concatenate_audioclips
)

BASE = Path(__file__).parent
V2_DIR = BASE.parent / 'v2'
DEMO_DIR = BASE.parent.parent  # boabfit-julia/

# ── Input Files ──────────────────────────────────────────────────────────────

TALKING_HEAD = str(V2_DIR / 'julia-omnihuman.mp4')
VOICEOVER = str(V2_DIR / 'julia-voiceover-v2.mp3')
MUSIC = str(DEMO_DIR / 'bg-beat.wav')
OUTPUT = str(BASE / 'julia-fullbody-v4.mp4')

# Exercise B-roll videos (stock footage with Julia's face swapped in)
BROLL_VIDEOS = {
    'hip-thrust': str(BASE / 'julia-hip-thrust.mp4'),
    'kickback': str(BASE / 'julia-kickback.mp4'),
    'rdl': str(BASE / 'julia-rdl.mp4'),
}

# ── Timeline ─────────────────────────────────────────────────────────────────

CAPTIONS = [
    (0.0, 2.0, "Hey girls! Welcome back."),
    (2.0, 5.0, "Today we are hitting GLUTES"),
    (5.0, 7.5, "and I promise you,"),
    (7.5, 10.0, "this routine is going to\nhave you feeling the BURN."),
    (10.0, 13.0, "Hip thrusts, kickbacks,\nand Romanian deadlifts."),
    (13.0, 15.5, "No excuses, just RESULTS."),
    (15.5, 18.5, "Grab your bands,\ngrab your weights,"),
    (18.5, 20.5, "and let's get to work."),
    (20.5, 22.8, "You ready? LET'S GO!"),
]

PINK_WORDS = {"GLUTES", "BURN", "RESULTS", "LET'S", "GO!"}

VIDEO_OVERLAYS = [
    {'start': 7.5, 'end': 10.0, 'video': 'hip-thrust', 'label': 'HIP THRUSTS'},
    {'start': 10.0, 'end': 13.0, 'video': 'kickback', 'label': 'KICKBACKS'},
    {'start': 13.0, 'end': 15.5, 'video': 'rdl', 'label': 'ROMANIAN DEADLIFTS'},
]

# ── Constants ────────────────────────────────────────────────────────────────

WIDTH, HEIGHT = 1080, 1920
FPS = 25
CIRCLE_DIAM = 240
CIRCLE_BORDER = 6
CIRCLE_X = WIDTH - CIRCLE_DIAM - 24
CIRCLE_Y = HEIGHT - CIRCLE_DIAM - 380
BRAND_PINK = (255, 105, 180)
DARK_BG = (15, 15, 15)
TRANSITION_DURATION = 0.15
FLASH_DURATION = 0.08


# ── Color Grade (Gym Warm) ───────────────────────────────────────────────────

def color_grade_gym_warm(frame):
    f = frame.astype(np.float32)
    f = (f - 128) * 1.12 + 128
    f[:, :, 0] = f[:, :, 0] * 1.06 + 4
    f[:, :, 1] = f[:, :, 1] * 1.02 + 2
    f[:, :, 2] = f[:, :, 2] * 0.94 - 3
    gray = np.mean(f, axis=2, keepdims=True)
    f = gray + (f - gray) * 1.15
    return np.clip(f, 0, 255).astype(np.uint8)


# ── Vignette ─────────────────────────────────────────────────────────────────

def build_vignette(w, h, strength=0.35):
    Y, X = np.ogrid[:h, :w]
    cx, cy = w / 2, h / 2
    r = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
    max_r = np.sqrt(cx ** 2 + cy ** 2)
    vignette = 1.0 - strength * (r / max_r) ** 2
    return vignette[:, :, np.newaxis].astype(np.float32)

VIGNETTE = build_vignette(WIDTH, HEIGHT, strength=0.3)


def apply_vignette(frame):
    return (frame.astype(np.float32) * VIGNETTE).clip(0, 255).astype(np.uint8)


# ── Circle PiP ──────────────────────────────────────────────────────────────

def build_circle_mask(diameter):
    mask = Image.new("L", (diameter, diameter), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, diameter - 1, diameter - 1], fill=255)
    return np.array(mask) / 255.0

def build_border_ring(diameter, border):
    outer = Image.new("L", (diameter, diameter), 0)
    inner = Image.new("L", (diameter, diameter), 0)
    ImageDraw.Draw(outer).ellipse([0, 0, diameter - 1, diameter - 1], fill=255)
    ImageDraw.Draw(inner).ellipse(
        [border, border, diameter - 1 - border, diameter - 1 - border], fill=255
    )
    return (np.array(outer) - np.array(inner)).clip(0, 255) / 255.0

CIRCLE_MASK = build_circle_mask(CIRCLE_DIAM)
BORDER_RING = build_border_ring(CIRCLE_DIAM, CIRCLE_BORDER)


def composite_circle_pip(bg_frame, julia_frame, scale=1.0):
    if scale <= 0.05:
        return bg_frame

    result = bg_frame.copy()
    h, w = julia_frame.shape[:2]
    sq = min(h, w)
    y0, x0 = (h - sq) // 2, (w - sq) // 2
    square = julia_frame[y0:y0 + sq, x0:x0 + sq]

    diam = max(int(CIRCLE_DIAM * scale), 4)
    pil_sq = Image.fromarray(square).resize((diam, diam), Image.LANCZOS)
    julia_arr = np.array(pil_sq).astype(float)

    cmask = np.array(build_circle_mask(diam))[:, :, np.newaxis]
    bmask = np.array(build_border_ring(diam, max(int(CIRCLE_BORDER * scale), 1)))[:, :, np.newaxis]
    border_color = np.array(BRAND_PINK, dtype=float)

    offset = int((CIRCLE_DIAM - diam) / 2)
    cy = CIRCLE_Y + offset
    cx = CIRCLE_X + offset

    if cy + diam > HEIGHT or cx + diam > WIDTH or cy < 0 or cx < 0:
        return bg_frame

    region = result[cy:cy + diam, cx:cx + diam].astype(float)
    blended = region * (1 - cmask) + julia_arr * cmask
    blended = blended * (1 - bmask) + border_color * bmask
    result[cy:cy + diam, cx:cx + diam] = blended.astype(np.uint8)
    return result


# ── Resize ───────────────────────────────────────────────────────────────────

def resize_cover(frame_or_pil, target_w, target_h):
    if isinstance(frame_or_pil, np.ndarray):
        pil_img = Image.fromarray(frame_or_pil)
    else:
        pil_img = frame_or_pil
    iw, ih = pil_img.size
    ratio = max(target_w / iw, target_h / ih)
    new_w, new_h = int(iw * ratio), int(ih * ratio)
    pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return np.array(pil_img.crop((left, top, left + target_w, top + target_h)))


# ── Transition Effects ───────────────────────────────────────────────────────

def whip_pan_blur(frame, intensity):
    if intensity <= 0.01:
        return frame
    blur_px = int(intensity * 80)
    if blur_px < 2:
        return frame
    pil = Image.fromarray(frame)
    blurred = pil.filter(ImageFilter.BoxBlur(blur_px))
    blurred = blurred.resize((int(WIDTH * (1 + intensity * 0.3)), HEIGHT), Image.BILINEAR)
    excess = blurred.size[0] - WIDTH
    blurred = blurred.crop((excess // 2, 0, excess // 2 + WIDTH, HEIGHT))
    return np.array(blurred)


def flash_overlay(frame, intensity):
    if intensity <= 0.01:
        return frame
    white = np.full_like(frame, 255)
    return ((1 - intensity) * frame.astype(float) + intensity * white.astype(float)).clip(0, 255).astype(np.uint8)


# ── Caption Rendering ────────────────────────────────────────────────────────

def get_font(size=56):
    for font_path in [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        try:
            return ImageFont.truetype(font_path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()

FONT_LARGE = get_font(58)
FONT_LABEL = get_font(42)


def render_caption_enhanced(text, width, height, progress=1.0):
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    lines = text.split('\n')
    line_heights = []
    line_widths = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=FONT_LARGE)
        line_widths.append(bbox[2] - bbox[0])
        line_heights.append(bbox[3] - bbox[1])

    base_y = int(height * 0.76)
    anim_offset = int((1 - min(progress / 0.15, 1.0)) * 30)
    alpha_mult = min(progress / 0.1, 1.0)

    y = base_y + anim_offset
    for i, line in enumerate(lines):
        lw = line_widths[i]
        x = (width - lw) // 2

        pad_x, pad_y = 22, 12
        pill_alpha = int(200 * alpha_mult)
        draw.rounded_rectangle(
            [x - pad_x, y - pad_y, x + lw + pad_x, y + line_heights[i] + pad_y],
            radius=16,
            fill=(0, 0, 0, pill_alpha)
        )

        words = line.split(' ')
        wx = x
        for word in words:
            wbbox = draw.textbbox((0, 0), word + ' ', font=FONT_LARGE)
            ww = wbbox[2] - wbbox[0]
            txt_alpha = int(255 * alpha_mult)
            is_pink = word.strip('.,!?') in PINK_WORDS

            for dx in [-2, -1, 1, 2]:
                for dy in [-2, -1, 1, 2]:
                    draw.text((wx + dx, y + dy), word, font=FONT_LARGE,
                              fill=(0, 0, 0, txt_alpha))

            if is_pink:
                draw.text((wx, y), word, font=FONT_LARGE,
                          fill=(255, 105, 180, txt_alpha))
            else:
                draw.text((wx, y), word, font=FONT_LARGE,
                          fill=(255, 255, 255, txt_alpha))
            wx += ww

        y += line_heights[i] + 8

    return np.array(img)


def render_exercise_label(label, width, height):
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    bbox = draw.textbbox((0, 0), label, font=FONT_LABEL)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    x = (width - text_w) // 2
    y = int(height * 0.07)

    pad = 18
    draw.rounded_rectangle(
        [x - pad * 2, y - pad, x + text_w + pad * 2, y + text_h + pad],
        radius=12,
        fill=(255, 105, 180, 230)
    )
    draw.text((x + 2, y + 2), label, font=FONT_LABEL, fill=(0, 0, 0, 100))
    draw.text((x, y), label, font=FONT_LABEL, fill=(255, 255, 255, 255))

    return np.array(img)


def alpha_composite_onto(base_rgb, overlay_rgba):
    if overlay_rgba.shape[2] < 4:
        return base_rgb
    alpha = overlay_rgba[:, :, 3:4].astype(float) / 255.0
    rgb = overlay_rgba[:, :, :3].astype(float)
    blended = base_rgb.astype(float) * (1 - alpha) + rgb * alpha
    return blended.astype(np.uint8)


# ── Main Assembly ────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Julia Full-Body v4 — Stock Footage + Face Swap Edition")
    print("=" * 60)
    print()

    # Load all assets
    print("Loading assets...")
    th_clip = VideoFileClip(TALKING_HEAD)
    print(f"  Talking head: {th_clip.size[0]}x{th_clip.size[1]}, {th_clip.duration:.1f}s")

    voiceover = AudioFileClip(VOICEOVER)
    print(f"  Voiceover: {voiceover.duration:.1f}s")

    broll_clips = {}
    missing = []
    for name, path in BROLL_VIDEOS.items():
        if os.path.exists(path):
            broll_clips[name] = VideoFileClip(path)
            c = broll_clips[name]
            print(f"  B-roll {name}: {c.size[0]}x{c.size[1]}, {c.duration:.1f}s")
        else:
            missing.append(name)
            print(f"  B-roll {name}: MISSING ({path})")

    if missing:
        print(f"\n  WARNING: Missing {len(missing)} B-roll clip(s): {missing}")
        print("  Run face swap first to generate these clips.")
        print("  Continuing with available clips...\n")

    bg_music = None
    if os.path.exists(MUSIC):
        bg_music = AudioFileClip(MUSIC)
        print(f"  Music: {bg_music.duration:.1f}s")

    duration = min(th_clip.duration, voiceover.duration)
    print(f"\nFinal: {duration:.1f}s @ {WIDTH}x{HEIGHT}")

    # Pre-render exercise labels
    label_cache = {}
    for overlay in VIDEO_OVERLAYS:
        label_cache[overlay['label']] = render_exercise_label(overlay['label'], WIDTH, HEIGHT)

    # Transition timestamps
    transition_times = set()
    for overlay in VIDEO_OVERLAYS:
        transition_times.add(overlay['start'])
        transition_times.add(overlay['end'])
    transition_times = sorted(transition_times)

    print(f"Transitions at: {transition_times}")
    print("Effects: whip pan + flash + color grade + vignette + animated PiP")
    print("Assembling...\n")

    # ── Frame Generator ──────────────────────────────────────────────────

    def make_frame(t):
        julia_raw = th_clip.get_frame(min(t, th_clip.duration - 0.04))

        active_overlay = None
        for overlay in VIDEO_OVERLAYS:
            if overlay['start'] <= t < overlay['end']:
                active_overlay = overlay
                break

        if active_overlay and active_overlay['video'] in broll_clips:
            broll_clip = broll_clips[active_overlay['video']]
            broll_t = (t - active_overlay['start']) % (broll_clip.duration - 0.04)
            broll_frame = broll_clip.get_frame(min(broll_t, broll_clip.duration - 0.04))
            bg = resize_cover(broll_frame, WIDTH, HEIGHT)

            time_into_overlay = t - active_overlay['start']
            pip_scale = min(time_into_overlay / 0.3, 1.0)
            if pip_scale >= 1.0:
                pip_scale = 1.0 + 0.03 * math.sin(time_into_overlay * 4)

            frame = composite_circle_pip(bg, julia_raw, scale=pip_scale)

            label = active_overlay.get('label', '')
            if label in label_cache:
                frame = alpha_composite_onto(frame, label_cache[label])
        else:
            frame = resize_cover(julia_raw, WIDTH, HEIGHT)

        for tt in transition_times:
            dt = t - tt
            if -TRANSITION_DURATION < dt < TRANSITION_DURATION:
                intensity = 1.0 - abs(dt) / TRANSITION_DURATION
                frame = whip_pan_blur(frame, intensity * 0.7)
            if 0 <= dt < FLASH_DURATION:
                flash_intensity = 1.0 - (dt / FLASH_DURATION)
                frame = flash_overlay(frame, flash_intensity * 0.6)

        frame = color_grade_gym_warm(frame)
        frame = apply_vignette(frame)

        for cap_start, cap_end, cap_text in CAPTIONS:
            if cap_start <= t < cap_end:
                progress = t - cap_start
                cap_rgba = render_caption_enhanced(cap_text, WIDTH, HEIGHT, progress)
                frame = alpha_composite_onto(frame, cap_rgba)
                break

        return frame

    # Build video
    final_video = VideoClip(make_frame, duration=duration).with_fps(FPS)

    # Audio mixing
    if bg_music:
        if bg_music.duration < duration:
            loops = int(duration / bg_music.duration) + 1
            bg_music = concatenate_audioclips([bg_music] * loops)
        bg_music = bg_music.subclipped(0, duration).with_volume_scaled(0.10)
        mixed = CompositeAudioClip([voiceover.subclipped(0, duration), bg_music])
    else:
        mixed = voiceover.subclipped(0, duration)

    final_video = final_video.with_audio(mixed)

    print(f"Exporting: {OUTPUT}")
    final_video.write_videofile(
        OUTPUT,
        fps=FPS,
        codec='libx264',
        audio_codec='aac',
        bitrate='8000k',
        preset='medium',
        logger=None
    )

    size_mb = os.path.getsize(OUTPUT) / 1024 / 1024
    print(f"\n{'=' * 60}")
    print(f"  V4 STOCK FOOTAGE + FACE SWAP — COMPLETE")
    print(f"  Output: {OUTPUT}")
    print(f"  Size: {size_mb:.1f} MB | Duration: {duration:.1f}s")
    print(f"  Resolution: {WIDTH}x{HEIGHT} | Bitrate: 8Mbps")
    print(f"")
    print(f"  Pipeline:")
    print(f"    + Real stock footage from Pexels (real physics)")
    print(f"    + Face swap via Replicate roop (Julia's face)")
    print(f"    + OmniHuman talking head in circle PiP")
    print(f"    + Whip pan transitions + white flash")
    print(f"    + Gym-warm color grade + cinematic vignette")
    print(f"    + Pink-highlighted captions with slide-up animation")
    print(f"{'=' * 60}")

    # Cleanup
    th_clip.close()
    voiceover.close()
    for clip in broll_clips.values():
        clip.close()
    if bg_music:
        bg_music.close()


if __name__ == '__main__':
    main()
