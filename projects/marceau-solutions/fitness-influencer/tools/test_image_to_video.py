#!/usr/bin/env python3
"""
test_image_to_video.py - Animate Still Images into Video

Take a character image and animate it into a short video using Grok Imagine.
Designed to work with character images from test_character_consistency.py.

Usage:
    python test_image_to_video.py --image output/character_01.png --prompt "person speaking to camera"
    python test_image_to_video.py --image output/character_01.png --prompt "person walking" --duration 10
    python test_image_to_video.py --image output/character_01.png --prompt "close up, talking" --aspect 9:16

Requires: XAI_API_KEY in .env
Reuses: execution/grok_video_gen.py
Research: projects/archived/automated-social-media-campaign/THE COMPLETE AI INFLUENCER SYSTEM GUIDE.pdf
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

SANDBOX_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(SANDBOX_ROOT))
sys.path.insert(0, str(SANDBOX_ROOT / "execution"))

try:
    from dotenv import load_dotenv
    load_dotenv(SANDBOX_ROOT / ".env")
except ImportError:
    pass


def check_prerequisites():
    """Check all dependencies and API keys are available."""
    print("\nPrerequisite Check: test_image_to_video.py")
    print("-" * 50)
    ok = True

    key = os.environ.get("XAI_API_KEY")
    if key:
        print(f"  XAI_API_KEY: {'*' * 6}...{key[-4:]}  ✓")
    else:
        print("  XAI_API_KEY: NOT SET  ✗")
        ok = False

    try:
        import requests  # noqa: F401
        print("  requests: installed  ✓")
    except ImportError:
        print("  requests: NOT INSTALLED  ✗")
        ok = False

    try:
        from grok_video_gen import GrokVideoGenerator  # noqa: F401
        print("  grok_video_gen: found  ✓")
    except ImportError:
        print("  grok_video_gen: NOT FOUND  ⚠ (will use direct API)")

    print(f"\n  {'ALL GOOD — ready to animate!' if ok else 'Fix issues above before running.'}")
    return ok


def animate_image(image_path: str, prompt: str, duration: int = 8,
                  aspect_ratio: str = "16:9", output_path: str = None):
    """Animate a still image into video using Grok Imagine."""

    if not os.path.exists(image_path):
        print(f"ERROR: Image not found: {image_path}")
        sys.exit(1)

    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = Path(image_path).stem
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_path = str(output_dir / f"{stem}_animated_{timestamp}.mp4")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Check API key
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        print("ERROR: XAI_API_KEY not found in .env")
        print(f"Add to: {SANDBOX_ROOT / '.env'}")
        sys.exit(1)

    print(f"\nAnimating Image to Video")
    print(f"{'='*60}")
    print(f"  Image: {image_path}")
    print(f"  Prompt: {prompt}")
    print(f"  Duration: {duration}s")
    print(f"  Aspect: {aspect_ratio}")
    print(f"  Output: {output_path}")
    print(f"  Est. cost: ${duration * 0.02:.2f}")
    print(f"{'='*60}")

    # Try to use the existing grok_video_gen.py
    try:
        from grok_video_gen import GrokVideoGenerator
        gen = GrokVideoGenerator(api_key=api_key)

        result = gen.generate(
            prompt=prompt,
            image_path=image_path,
            duration=duration,
            aspect_ratio=aspect_ratio,
            output_path=output_path
        )

        if result and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"\n  Saved: {output_path} ({file_size / 1024 / 1024:.1f} MB)")
            return output_path
        else:
            print(f"\n  Result: {result}")
            print("  Check if the API returned an error or URL.")
            return result

    except ImportError:
        print("\nWARNING: grok_video_gen.py not found, using direct API call...")
        return _direct_api_call(image_path, prompt, duration, aspect_ratio, output_path, api_key)
    except Exception as e:
        print(f"\nERROR: {e}")
        return None


def _direct_api_call(image_path, prompt, duration, aspect_ratio, output_path, api_key):
    """Direct xAI API call as fallback."""
    try:
        import requests
        import base64
    except ImportError:
        print("ERROR: requests required")
        sys.exit(1)

    # Read and encode image
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    # Determine mime type
    ext = Path(image_path).suffix.lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/png")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "grok-imagine-video",
        "prompt": prompt,
        "image_url": f"data:{mime_type};base64,{image_data}",
        "duration": duration,
        "aspect_ratio": aspect_ratio
    }

    print("  Submitting to xAI API...")
    response = requests.post(
        "https://api.x.ai/v1/video/generations",
        headers=headers,
        json=payload,
        timeout=120
    )

    if response.status_code == 200:
        result = response.json()
        video_url = result.get("url") or result.get("video_url")
        if video_url:
            video_data = requests.get(video_url, timeout=60).content
            with open(output_path, "wb") as f:
                f.write(video_data)
            file_size = os.path.getsize(output_path)
            print(f"\n  Saved: {output_path} ({file_size / 1024 / 1024:.1f} MB)")
            return output_path
        print(f"  Response: {json.dumps(result, indent=2)[:500]}")
    else:
        print(f"\nERROR: {response.status_code}")
        print(f"  {response.text[:500]}")
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Animate still character images into video",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic animation
  python test_image_to_video.py --image output/character_01.png --prompt "person speaking to camera"

  # Vertical video for TikTok/Reels
  python test_image_to_video.py --image output/character_01.png --prompt "talking head" --aspect 9:16

  # Longer duration
  python test_image_to_video.py --image output/character_01.png --prompt "workout demo" --duration 12

Workflow:
  1. Generate character with test_character_consistency.py
  2. Pick best image
  3. Animate with this script
  4. Add voice with test_voice_*.py scripts

Cost: ~$0.02/second ($0.16 for 8s, $0.24 for 12s)
        """
    )
    parser.add_argument("--image", "-i", type=str, help="Input image path")
    parser.add_argument("--prompt", "-p", type=str, help="Animation prompt")
    parser.add_argument("--duration", "-d", type=int, default=8, help="Video duration in seconds (default: 8)")
    parser.add_argument("--aspect", type=str, default="16:9",
                        choices=["16:9", "9:16", "4:3", "1:1"],
                        help="Aspect ratio (default: 16:9)")
    parser.add_argument("--output", "-o", type=str, help="Output video path")
    parser.add_argument("--check", action="store_true", help="Check prerequisites (API keys, packages)")

    args = parser.parse_args()

    if args.check:
        check_prerequisites()
        return

    if not args.image or not args.prompt:
        parser.print_help()
        print("\nERROR: --image and --prompt required")
        sys.exit(1)

    animate_image(args.image, args.prompt, duration=args.duration,
                  aspect_ratio=args.aspect, output_path=args.output)


if __name__ == "__main__":
    main()
