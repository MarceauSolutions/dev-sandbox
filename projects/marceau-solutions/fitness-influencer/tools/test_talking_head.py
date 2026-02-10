#!/usr/bin/env python3
"""
test_talking_head.py - Talking Head Generation (SadTalker via Replicate)

Generate a full talking head video from a single face image + audio.
SadTalker animates the face with realistic head movement and lip sync.

Usage:
    python test_talking_head.py --image face.png --audio speech.mp3
    python test_talking_head.py --image face.png --audio speech.mp3 --enhance
    python test_talking_head.py --image face.png --audio speech.mp3 --expression-scale 1.5
    python test_talking_head.py --cost --duration 10
    python test_talking_head.py --list-models

Requires: REPLICATE_API_TOKEN in .env
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

SANDBOX_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(SANDBOX_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(SANDBOX_ROOT / ".env")
except ImportError:
    pass


MODELS = {
    "sadtalker": {
        "id": "cjwbw/sadtalker:a519cc0c",
        "name": "SadTalker",
        "cost_per_run": 0.05,
        "description": "Audio-driven talking head from single image (head movement + lip sync)"
    },
}

DEFAULT_MODEL = "sadtalker"


def get_api_token():
    token = os.environ.get("REPLICATE_API_TOKEN")
    if not token:
        print("ERROR: REPLICATE_API_TOKEN not found in .env")
        print(f"Add to: {SANDBOX_ROOT / '.env'}")
        print("Get token at: https://replicate.com/account/api-tokens")
        sys.exit(1)
    return token


def list_models():
    """List available talking head models."""
    print("\nAvailable Talking Head Models:")
    print("-" * 70)
    for key, m in MODELS.items():
        print(f"  {key:12s}  {m['name']:15s}  ~${m['cost_per_run']:.2f}/run")
        print(f"               {m['description']}")
    print(f"\nDefault: {DEFAULT_MODEL}")


def estimate_cost(duration_sec: float):
    """Estimate cost for talking head generation."""
    print(f"\nCost Estimates for ~{duration_sec:.0f}s talking head:")
    print("-" * 50)
    for key, m in MODELS.items():
        # SadTalker cost scales roughly with audio length
        cost = m["cost_per_run"] * max(1, duration_sec / 10)
        print(f"  {m['name']:15s}  ~${cost:.4f}  (~${m['cost_per_run']:.2f} base)")
    print("\nNote: Actual cost depends on audio length and Replicate compute time.")


def run_talking_head(image_path: str, audio_path: str,
                     model_key: str = DEFAULT_MODEL,
                     enhance: bool = False,
                     expression_scale: float = 1.0,
                     still_mode: bool = False,
                     preprocess: str = "crop",
                     output_path: str = None):
    """Generate talking head video from image + audio."""
    if model_key not in MODELS:
        print(f"ERROR: Unknown model '{model_key}'. Use --list-models")
        sys.exit(1)

    if not image_path or not os.path.exists(image_path):
        print(f"ERROR: Image file not found: {image_path}")
        sys.exit(1)

    if not audio_path or not os.path.exists(audio_path):
        print(f"ERROR: Audio file not found: {audio_path}")
        sys.exit(1)

    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_path = str(output_dir / f"talking_head_{model_key}_{timestamp}.mp4")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Verify API token
    get_api_token()

    model = MODELS[model_key]
    enhancer_name = "gfpgan" if enhance else None

    print(f"\nTalking Head Generation")
    print(f"{'='*60}")
    print(f"  Model: {model['name']} ({model_key})")
    print(f"  Image: {image_path}")
    print(f"  Audio: {audio_path}")
    print(f"  Enhance: {enhancer_name or 'none'}")
    print(f"  Expression scale: {expression_scale}")
    print(f"  Still mode: {still_mode}")
    print(f"  Preprocess: {preprocess}")
    print(f"  Output: {output_path}")
    print(f"  Est. cost: ~${model['cost_per_run']:.2f}")
    print(f"{'='*60}")

    try:
        import replicate
    except ImportError:
        print("ERROR: replicate package required. Run: pip install replicate")
        sys.exit(1)

    # Build input payload
    input_payload = {
        "source_image": open(image_path, "rb"),
        "driven_audio": open(audio_path, "rb"),
        "preprocess": preprocess,
        "expression_scale": expression_scale,
        "still": still_mode,
    }

    if enhancer_name:
        input_payload["enhancer"] = enhancer_name

    print("  Submitting to Replicate...")
    print("  (This may take 1-5 minutes depending on audio length)")

    try:
        output = replicate.run(
            model["id"],
            input=input_payload
        )

        # SadTalker returns a URL string
        video_url = None
        if isinstance(output, str):
            video_url = output
        elif hasattr(output, 'url'):
            video_url = output.url
        elif isinstance(output, dict):
            video_url = output.get("url") or output.get("video") or output.get("output")
        elif isinstance(output, list) and output:
            video_url = output[0] if isinstance(output[0], str) else output[0].get("url")

        if not video_url:
            print(f"  WARNING: Unexpected output format: {type(output)}")
            print(f"  Output: {str(output)[:500]}")
            return None

        # Download video
        import requests
        print("  Downloading result...")
        video_data = requests.get(video_url, timeout=120).content
        with open(output_path, "wb") as f:
            f.write(video_data)

        file_size = os.path.getsize(output_path)
        print(f"\n  Saved: {output_path} ({file_size / 1024 / 1024:.1f} MB)")
        return output_path

    except Exception as e:
        print(f"\n  ERROR: {e}")
        return None
    finally:
        # Close file handles
        for key in ("source_image", "driven_audio"):
            fh = input_payload.get(key)
            if hasattr(fh, "close"):
                fh.close()


def main():
    parser = argparse.ArgumentParser(
        description="Generate talking head video from image + audio (SadTalker)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic talking head from image + audio
  python test_talking_head.py --image face.png --audio speech.mp3

  # With face enhancement (GFPGAN built-in)
  python test_talking_head.py --image face.png --audio speech.mp3 --enhance

  # More expressive head movement
  python test_talking_head.py --image face.png --audio speech.mp3 --expression-scale 1.5

  # Minimal head movement (just lip sync)
  python test_talking_head.py --image face.png --audio speech.mp3 --still

  # Full frame processing (no crop)
  python test_talking_head.py --image face.png --audio speech.mp3 --preprocess full

  # Estimate cost
  python test_talking_head.py --cost --duration 10

Workflow:
  1. Generate character with test_character_consistency.py
  2. Generate voice with test_voice_*.py scripts
  3. Create talking head with this script
  4. (Optional) Enhance with test_face_restore.py

Preprocess modes:
  crop     Crop face region (default, best for close-ups)
  resize   Resize image to fit model input
  full     Full frame (preserves background, may reduce quality)

Cost: ~$0.05/run (varies with audio length)
        """
    )
    parser.add_argument("--image", "-i", type=str, help="Input face image (PNG/JPG)")
    parser.add_argument("--audio", "-a", type=str, help="Input audio file (MP3/WAV)")
    parser.add_argument("--model", "-m", type=str, default=DEFAULT_MODEL,
                        choices=list(MODELS.keys()),
                        help=f"Model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--output", "-o", type=str, help="Output video path")
    parser.add_argument("--enhance", action="store_true",
                        help="Enable GFPGAN face enhancement (built into SadTalker)")
    parser.add_argument("--expression-scale", type=float, default=1.0,
                        help="Expression intensity (default: 1.0, try 1.5 for more movement)")
    parser.add_argument("--still", action="store_true",
                        help="Reduce head movement (lip sync only)")
    parser.add_argument("--preprocess", type=str, default="crop",
                        choices=["crop", "resize", "full"],
                        help="Face preprocessing mode (default: crop)")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    parser.add_argument("--cost", action="store_true", help="Estimate cost")
    parser.add_argument("--duration", type=float, default=10,
                        help="Audio duration in seconds (for cost estimate)")

    args = parser.parse_args()

    if args.list_models:
        list_models()
        return

    if args.cost:
        estimate_cost(args.duration)
        return

    if not args.image:
        parser.print_help()
        print("\nERROR: --image required")
        sys.exit(1)

    if not args.audio:
        parser.print_help()
        print("\nERROR: --audio required")
        sys.exit(1)

    run_talking_head(
        image_path=args.image,
        audio_path=args.audio,
        model_key=args.model,
        enhance=args.enhance,
        expression_scale=args.expression_scale,
        still_mode=args.still,
        preprocess=args.preprocess,
        output_path=args.output
    )


if __name__ == "__main__":
    main()
