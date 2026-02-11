#!/usr/bin/env python3
"""
generate_viral_reel.py — Viral fitness reel generator.

Architecture: Continuous talking head as base video with B-roll overlays
at explicit timestamps. Mandatory post-processors run automatically
(transitions, captions, background music, SFX).

Usage:
    # Standard run with approved assets (free, ~2 min)
    python generate_viral_reel.py --recipe recipe.json \\
      --talking-head talking-head-v2.mp4 \\
      --voiceover voiceover-v2.mp3

    # Generate everything from scratch (~$2.86)
    python generate_viral_reel.py --recipe recipe.json

    # Cost estimate only
    python generate_viral_reel.py --recipe recipe.json --cost

Requires: ELEVENLABS_API_KEY, REPLICATE_API_TOKEN in .env (only for generation)
"""

import argparse
import asyncio
import base64
import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

# ── Setup ────────────────────────────────────────────────────────────────────

SANDBOX_ROOT = Path(__file__).resolve().parents[4]
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

sys.path.insert(0, str(SANDBOX_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(SANDBOX_ROOT / ".env")
except ImportError:
    pass

# Constants
WIDTH, HEIGHT = 1080, 1920
FPS = 25
CIRCLE_DIAM = 180
CIRCLE_BORDER = 4
CIRCLE_X = WIDTH - CIRCLE_DIAM - 40
CIRCLE_Y = HEIGHT - CIRCLE_DIAM - 300
BRAND_COLOR = (255, 105, 180)

OMNIHUMAN_VERSION = "566f1b03016969ac39e242c1ae4a39034686ca8850fc3dba83dceaceb96f74b2"
ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"
REPLICATE_API_BASE = "https://api.replicate.com/v1"


# ── Circle Compositing ───────────────────────────────────────────────────────

def _build_circle_mask(diameter):
    mask = Image.new("L", (diameter, diameter), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, diameter - 1, diameter - 1], fill=255)
    return np.array(mask) / 255.0


def _build_border_mask(diameter, border):
    outer = Image.new("L", (diameter, diameter), 0)
    inner = Image.new("L", (diameter, diameter), 0)
    ImageDraw.Draw(outer).ellipse([0, 0, diameter - 1, diameter - 1], fill=255)
    ImageDraw.Draw(inner).ellipse(
        [border, border, diameter - 1 - border, diameter - 1 - border], fill=255
    )
    return (np.array(outer) - np.array(inner)).clip(0, 255) / 255.0


CIRCLE_MASK = _build_circle_mask(CIRCLE_DIAM)
BORDER_MASK = _build_border_mask(CIRCLE_DIAM, CIRCLE_BORDER)


def circle_composite(bg_frame, julia_frame):
    """Overlay Julia in a circle with pink border on the background."""
    result = bg_frame.copy()
    h, w = julia_frame.shape[:2]

    sq = min(h, w)
    y0, x0 = (h - sq) // 2, (w - sq) // 2
    square = julia_frame[y0:y0 + sq, x0:x0 + sq]

    pil_sq = Image.fromarray(square).resize((CIRCLE_DIAM, CIRCLE_DIAM), Image.LANCZOS)
    julia_arr = np.array(pil_sq)

    alpha = CIRCLE_MASK[:, :, np.newaxis]
    border_alpha = BORDER_MASK[:, :, np.newaxis]
    border_color = np.array(BRAND_COLOR, dtype=np.uint8)

    region = result[CIRCLE_Y:CIRCLE_Y + CIRCLE_DIAM, CIRCLE_X:CIRCLE_X + CIRCLE_DIAM]
    blended = region * (1 - alpha) + julia_arr * alpha
    blended = blended * (1 - border_alpha) + border_color * border_alpha
    result[CIRCLE_Y:CIRCLE_Y + CIRCLE_DIAM, CIRCLE_X:CIRCLE_X + CIRCLE_DIAM] = blended.astype(np.uint8)
    return result


# ── Image Processing ─────────────────────────────────────────────────────────

def resize_cover(pil_img, target_w, target_h):
    """Resize image to cover the target area (crop excess)."""
    iw, ih = pil_img.size
    ratio = max(target_w / iw, target_h / ih)
    new_w, new_h = int(iw * ratio), int(ih * ratio)
    pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return np.array(pil_img.crop((left, top, left + target_w, top + target_h)))


def resize_contain(pil_img, target_w, target_h):
    """Resize image to fit within target area (letterbox, no crop)."""
    iw, ih = pil_img.size
    ratio = min(target_w / iw, target_h / ih)
    new_w, new_h = int(iw * ratio), int(ih * ratio)
    pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)
    bg = np.zeros((target_h, target_w, 3), dtype=np.uint8) + 20  # near-black
    y0 = (target_h - new_h) // 2
    x0 = (target_w - new_w) // 2
    bg[y0:y0 + new_h, x0:x0 + new_w] = np.array(pil_img)
    return bg


# ── Voiceover Generation ─────────────────────────────────────────────────────

def generate_voiceover(script, voice_id, output_path, stability=0.30, similarity=0.75):
    """Generate voiceover from script text using ElevenLabs."""
    import requests

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY not set in .env")
        sys.exit(1)

    chars = len(script)
    cost = (chars / 1000) * 0.30
    print(f"\n  [Voiceover] ElevenLabs")
    print(f"    Characters: {chars}  |  Est. cost: ${cost:.4f}")

    response = requests.post(
        f"{ELEVENLABS_API_BASE}/text-to-speech/{voice_id}",
        headers={"xi-api-key": api_key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
        json={
            "text": script,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": stability, "similarity_boost": similarity},
        },
        timeout=60,
    )

    if response.status_code == 200:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"    Saved: {output_path} ({os.path.getsize(output_path) / 1024:.1f} KB)")
        return output_path
    else:
        print(f"    ERROR: {response.status_code} - {response.text[:300]}")
        sys.exit(1)


# ── Talking Head Generation ──────────────────────────────────────────────────

def generate_talking_head(headshot_path, audio_path, output_path):
    """Generate talking head video using OmniHuman 1.5 via Replicate."""
    import requests

    token = os.environ.get("REPLICATE_API_TOKEN")
    if not token:
        print("ERROR: REPLICATE_API_TOKEN not set in .env")
        sys.exit(1)

    print(f"\n  [Talking Head] OmniHuman 1.5 via Replicate")
    print(f"    Est. cost: ~$2.80")

    with open(headshot_path, "rb") as f:
        img_data = f.read()
    with open(audio_path, "rb") as f:
        audio_data = f.read()

    ext = Path(headshot_path).suffix.lower()
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(ext, "image/png")

    payload = {
        "version": OMNIHUMAN_VERSION,
        "input": {
            "image": f"data:{mime};base64,{base64.b64encode(img_data).decode()}",
            "audio": f"data:audio/mpeg;base64,{base64.b64encode(audio_data).decode()}",
        },
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    resp = requests.post(f"{REPLICATE_API_BASE}/predictions", headers=headers, json=payload, timeout=60)
    if resp.status_code not in (200, 201):
        print(f"    ERROR: {resp.status_code} - {resp.text[:300]}")
        sys.exit(1)

    prediction_id = resp.json()["id"]
    print(f"    Prediction: {prediction_id} — polling (3-8 min)...")

    for i in range(120):
        time.sleep(5)
        sr = requests.get(
            f"{REPLICATE_API_BASE}/predictions/{prediction_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        if sr.status_code != 200:
            continue
        status = sr.json()
        state = status.get("status")
        if state == "succeeded":
            output = status.get("output")
            video_url = output if isinstance(output, str) else (output[0] if isinstance(output, list) else None)
            if not video_url:
                print(f"    ERROR: No video URL: {output}")
                sys.exit(1)
            video_data = requests.get(video_url, timeout=120).content
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(video_data)
            print(f"    Saved: {output_path} ({os.path.getsize(output_path) / 1024 / 1024:.1f} MB)")
            return output_path
        elif state in ("failed", "canceled"):
            print(f"    ERROR: {state}: {status.get('error', 'Unknown')}")
            sys.exit(1)
        print(f"    {state} ({(i+1)*5}s)...", end="\r")

    print("\n    ERROR: Timed out after 10 minutes")
    sys.exit(1)


# ── Step 1: Assembly ─────────────────────────────────────────────────────────

def assemble_reel(recipe, talking_head_path, voiceover_path, output_path):
    """Assemble reel: continuous talking head base with B-roll overlays at timestamps."""
    from moviepy import VideoFileClip, AudioFileClip, VideoClip

    print(f"\n  [Step 1: Assembly]")

    base_dir = Path(recipe.get("_base_dir", "."))
    overlays = recipe.get("overlays", [])

    # Validate: each image used exactly once
    images_used = [o["image"] for o in overlays]
    if len(images_used) != len(set(images_used)):
        dupes = [img for img in images_used if images_used.count(img) > 1]
        print(f"    WARNING: Duplicate images in recipe: {set(dupes)}")

    # Load talking head and voiceover
    th = VideoFileClip(talking_head_path)
    vo = AudioFileClip(voiceover_path)
    duration = min(th.duration, vo.duration)

    print(f"    Talking head: {th.duration:.1f}s | Voiceover: {vo.duration:.1f}s")
    print(f"    Overlays: {len(overlays)} | Duration: {duration:.1f}s")

    # Pre-load all B-roll images
    broll_frames = {}
    for overlay in overlays:
        img_path = str(base_dir / overlay["image"])
        if not os.path.exists(img_path):
            print(f"    WARNING: Missing image: {img_path}")
            continue
        pil_img = Image.open(img_path).convert("RGB")
        mode = overlay.get("mode", "cover")
        if mode == "contain":
            broll_frames[overlay["image"]] = resize_contain(pil_img, WIDTH, HEIGHT)
        else:
            broll_frames[overlay["image"]] = resize_cover(pil_img, WIDTH, HEIGHT)
        print(f"    Loaded: {overlay['image']} ({mode})")

    # Build frame generator
    def make_frame(t):
        julia_frame = th.get_frame(min(t, th.duration - 0.04))

        # Check if we're in an overlay window
        for overlay in overlays:
            if overlay["start"] <= t < overlay["end"]:
                img_key = overlay["image"]
                if img_key in broll_frames:
                    bg = broll_frames[img_key].copy()
                    return circle_composite(bg, julia_frame)

        # Default: full-frame Julia (cover mode)
        return resize_cover(Image.fromarray(julia_frame), WIDTH, HEIGHT)

    # Create video clip from frame function
    final = VideoClip(make_frame, duration=duration).with_fps(FPS)

    # Attach voiceover
    vo_trimmed = vo.subclipped(0, duration)
    final = final.with_audio(vo_trimmed)

    # Write output
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    print(f"    Writing: {output_path}")
    final.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        bitrate="5000k",
        preset="medium",
        logger=None,
    )

    # Cleanup
    th.close()
    vo.close()

    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"    Done: {output_path} ({size_mb:.1f} MB)")
    return output_path


# ── Step 2: Transitions ──────────────────────────────────────────────────────

async def apply_transitions_step(video_path, recipe, output_path):
    """Apply transitions at overlay boundaries."""
    try:
        from backend.transition_engine import apply_transitions, TransitionPoint, TransitionType
    except ImportError:
        print("    WARNING: transition_engine not available, skipping transitions")
        return video_path

    overlays = recipe.get("overlays", [])
    style = recipe.get("style", {})
    platform = style.get("platform", "instagram_reels")

    # Resolve transition type string to enum
    transition_str = style.get("transition", "whip_pan").upper()
    try:
        transition_type = TransitionType[transition_str]
    except KeyError:
        transition_type = TransitionType.WHIP_PAN

    # Build transition points at overlay boundaries
    transition_points = []
    for overlay in overlays:
        transition_points.append(TransitionPoint(
            timestamp=overlay["start"],
            transition_type=transition_type,
            duration=style.get("transition_duration", 0.25),
        ))
        transition_points.append(TransitionPoint(
            timestamp=overlay["end"],
            transition_type=transition_type,
            duration=style.get("transition_duration", 0.25),
        ))

    print(f"    Applying {len(transition_points)} transitions ({platform})...")
    result = await apply_transitions(
        video_path=video_path,
        transition_points=transition_points,
        platform=platform,
        output_path=output_path,
    )
    print(f"    Applied: {result.transitions_applied} transitions")
    return result.output_path


# ── Step 3: Background Music ─────────────────────────────────────────────────

async def apply_music_step(video_path, recipe, output_path):
    """Add background music with sidechain ducking."""
    try:
        from backend.music_mixer import add_background_music
    except ImportError:
        print("    WARNING: music_mixer not available, skipping background music")
        return video_path

    style = recipe.get("style", {})
    category = style.get("music_category", "energetic")
    volume = style.get("music_volume", 0.12)

    print(f"    Adding background music (category: {category}, volume: {volume})...")
    result = await add_background_music(
        video_path=video_path,
        output_path=output_path,
        category=category,
        music_volume=volume,
        duck_mode="sidechain",
        duck_amount=0.7,
    )
    if result.success:
        print(f"    Music added: {result.music_track or 'auto-selected'}")
        return result.output_path
    else:
        print(f"    WARNING: Music failed: {result.error}")
        return video_path


# ── Step 4: Sound Effects ────────────────────────────────────────────────────

async def apply_sfx_step(video_path, recipe, output_path):
    """Add sound effects at transition points."""
    try:
        from backend.sound_effects import apply_sound_effects, plan_sfx_placement
    except ImportError:
        print("    WARNING: sound_effects not available, skipping SFX")
        return video_path

    overlays = recipe.get("overlays", [])

    # SFX at each overlay boundary (whoosh on transitions)
    cut_points = []
    for overlay in overlays:
        cut_points.append(overlay["start"])
        cut_points.append(overlay["end"])

    placements = plan_sfx_placement(
        video_path=video_path,
        cut_points=cut_points,
        min_gap=0.5,
    )

    print(f"    Adding {len(placements)} sound effects...")
    result = await apply_sound_effects(
        video_path=video_path,
        output_path=output_path,
        placements=placements,
    )
    if result:
        print(f"    SFX applied")
        return result
    else:
        print(f"    WARNING: SFX failed")
        return video_path


# ── Step 5: Captions ─────────────────────────────────────────────────────────

async def apply_captions_step(video_path, recipe, output_path):
    """Add karaoke-style captions synced to voiceover."""
    try:
        from backend.caption_generator import generate_captions, CaptionConfig
    except ImportError:
        print("    WARNING: caption_generator not available, skipping captions")
        return video_path

    style = recipe.get("style", {})
    caption_style = style.get("caption_style", "trending")

    config = CaptionConfig(
        style=caption_style,
        max_words_per_line=7,
        word_highlight=True,
    )

    print(f"    Generating captions (style: {caption_style})...")
    result = await generate_captions(video_path=video_path, config=config)

    if result.captioned_video_path:
        print(f"    Captions applied: {len(result.lines)} lines")
        # Copy to our output path
        if result.captioned_video_path != output_path:
            import shutil
            shutil.copy2(result.captioned_video_path, output_path)
        return output_path
    else:
        print(f"    WARNING: Caption generation failed")
        return video_path


# ── Post-Processing Pipeline ─────────────────────────────────────────────────

async def run_post_processors(assembled_path, recipe, output_dir):
    """Run all post-processors in sequence. Each one is mandatory but gracefully
    degrades if the module isn't available or fails."""

    steps = [
        ("Step 2: Transitions", apply_transitions_step, "step2_transitions.mp4"),
        ("Step 3: Background Music", apply_music_step, "step3_music.mp4"),
        ("Step 4: Sound Effects", apply_sfx_step, "step4_sfx.mp4"),
        ("Step 5: Captions", apply_captions_step, "step5_captions.mp4"),
    ]

    current_path = assembled_path
    for step_name, step_fn, step_file in steps:
        print(f"\n  [{step_name}]")
        step_output = str(output_dir / step_file)
        try:
            result_path = await step_fn(current_path, recipe, step_output)
            if result_path and os.path.exists(result_path):
                current_path = result_path
            else:
                print(f"    Continuing with previous output")
        except Exception as e:
            print(f"    WARNING: {step_name} failed: {e}")
            traceback.print_exc()
            print(f"    Continuing with previous output")

    return current_path


# ── Cost Estimate ────────────────────────────────────────────────────────────

def estimate_cost(recipe):
    """Estimate total cost for generating this reel from scratch."""
    vo_cost = 0.08  # ~260 chars at $0.30/1000
    th_cost = 2.80  # OmniHuman 1.5 flat rate

    print(f"\nCost Estimate (generate from scratch):")
    print(f"  Voiceover (ElevenLabs):  ${vo_cost:.2f}")
    print(f"  Talking Head (OmniHuman): ${th_cost:.2f}")
    print(f"  Assembly (MoviePy):       $0.00")
    print(f"  Transitions:              $0.00")
    print(f"  Background Music:         $0.00")
    print(f"  Sound Effects:            $0.00")
    print(f"  Captions:                 $0.00")
    print(f"  {'─' * 30}")
    print(f"  Total: ${vo_cost + th_cost:.2f}")
    print(f"\nWith approved assets (--talking-head + --voiceover): $0.00")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate viral fitness reels (continuous talking head + B-roll overlays)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard run with approved assets (FREE, ~2 min)
  python generate_viral_reel.py --recipe recipe.json \\
    --talking-head talking-head-v2.mp4 \\
    --voiceover voiceover-v2.mp3

  # Generate everything from scratch (~$2.86)
  python generate_viral_reel.py --recipe recipe.json

  # Cost estimate only
  python generate_viral_reel.py --recipe recipe.json --cost

Architecture:
  1. ASSEMBLY: Talking head plays continuously. B-roll overlays at timestamps.
     Julia goes to pink circle during B-roll. Each image used exactly once.
  2. TRANSITIONS: Whip pan/flash at every overlay boundary.
  3. BACKGROUND MUSIC: Energetic track, sidechain-ducked under voiceover.
  4. SOUND EFFECTS: Whoosh on transitions, impact on text.
  5. CAPTIONS: Karaoke-style word highlighting synced to voiceover.

All post-processors run by default. If one fails, it logs and continues.
        """,
    )
    parser.add_argument("--recipe", "-r", required=True, help="Path to recipe JSON")
    parser.add_argument("--output", "-o", help="Output video path")
    parser.add_argument("--talking-head", help="Path to existing talking head MP4")
    parser.add_argument("--voiceover", help="Path to existing voiceover MP3")
    parser.add_argument("--cost", action="store_true", help="Estimate cost only")

    args = parser.parse_args()

    # Load recipe
    recipe_path = Path(args.recipe)
    if not recipe_path.exists():
        print(f"ERROR: Recipe not found: {recipe_path}")
        sys.exit(1)

    with open(recipe_path) as f:
        recipe = json.load(f)
    recipe["_base_dir"] = str(recipe_path.parent)

    if args.cost:
        estimate_cost(recipe)
        return

    # Setup output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    brand = recipe.get("brand", "reel").lower()
    output_dir = recipe_path.parent / "output" / f"{brand}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not args.output:
        args.output = str(output_dir / f"{brand}-viral-reel-{timestamp}.mp4")

    n_overlays = len(recipe.get("overlays", []))
    print(f"\n{'=' * 60}")
    print(f"  Viral Reel Generator")
    print(f"  Brand: {recipe.get('brand', '?')}")
    print(f"  Overlays: {n_overlays}")
    print(f"  Output: {args.output}")
    print(f"{'=' * 60}")

    # Resolve voiceover
    if args.voiceover:
        voiceover_path = args.voiceover
        print(f"\n  [Voiceover] Using existing: {voiceover_path}")
    else:
        voice_id = recipe.get("influencer", {}).get("voice_id", "")
        if not voice_id:
            print("ERROR: No voice_id in recipe and no --voiceover provided")
            sys.exit(1)
        # Need a script — for now require --voiceover with overlay-based recipes
        print("ERROR: Overlay-based recipes require --voiceover (no inline scripts)")
        print("Generate voiceover separately with ElevenLabs first.")
        sys.exit(1)

    # Resolve talking head
    if args.talking_head:
        talking_head_path = args.talking_head
        print(f"  [Talking Head] Using existing: {talking_head_path}")
    else:
        headshot = recipe.get("influencer", {}).get("headshot", "")
        if not headshot:
            print("ERROR: No headshot in recipe and no --talking-head provided")
            sys.exit(1)
        headshot_path = str(Path(recipe["_base_dir"]) / headshot) if not os.path.isabs(headshot) else headshot
        if not os.path.exists(headshot_path):
            print(f"ERROR: Headshot not found: {headshot_path}")
            sys.exit(1)
        th_output = str(output_dir / "talking_head.mp4")
        talking_head_path = generate_talking_head(headshot_path, voiceover_path, th_output)

    # Validate inputs exist
    for label, path in [("Voiceover", voiceover_path), ("Talking head", talking_head_path)]:
        if not os.path.exists(path):
            print(f"ERROR: {label} not found: {path}")
            sys.exit(1)

    # Step 1: Assembly
    assembled_path = str(output_dir / "step1_assembly.mp4")
    assemble_reel(recipe, talking_head_path, voiceover_path, assembled_path)

    # Steps 2-5: Post-processors (mandatory, graceful degradation)
    final_path = asyncio.run(run_post_processors(assembled_path, recipe, output_dir))

    # Copy final to output path
    if final_path != args.output:
        import shutil
        shutil.copy2(final_path, args.output)

    size_mb = os.path.getsize(args.output) / 1024 / 1024
    print(f"\n{'=' * 60}")
    print(f"  Reel Complete!")
    print(f"  Output: {args.output} ({size_mb:.1f} MB)")
    print(f"  Voiceover: {voiceover_path}")
    print(f"  Talking Head: {talking_head_path}")
    print(f"{'=' * 60}")

    return args.output


if __name__ == "__main__":
    main()
