#!/usr/bin/env python3
"""
test_face_restore.py - Face Restoration & Enhancement (Replicate)

Enhance AI-generated face images using GFPGAN or Real-ESRGAN.
Use standalone or as a post-processing step after character generation.

Usage:
    python test_face_restore.py --image blurry_face.png
    python test_face_restore.py --image low_res.png --model realesrgan --scale 4
    python test_face_restore.py --image face.png --compare-all
    python test_face_restore.py --batch output/consistency_*/
    python test_face_restore.py --cost --count 10

Requires: REPLICATE_API_TOKEN in .env
"""

import argparse
import os
import sys
import glob as glob_module
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
    "gfpgan": {
        "id": "tencentarc/gfpgan:0fbacf7a",
        "name": "GFPGAN v1.4",
        "cost_per_run": 0.005,
        "description": "Face-specific restoration — best for AI-generated faces",
        "supports_scale": False,
    },
    "realesrgan": {
        "id": "xinntao/realesrgan:1b976a4d",
        "name": "Real-ESRGAN",
        "cost_per_run": 0.01,
        "description": "General image upscaling — faces + backgrounds",
        "supports_scale": True,
    },
}

DEFAULT_MODEL = "gfpgan"


def get_api_token():
    token = os.environ.get("REPLICATE_API_TOKEN")
    if not token:
        print("ERROR: REPLICATE_API_TOKEN not found in .env")
        print(f"Add to: {SANDBOX_ROOT / '.env'}")
        print("Get token at: https://replicate.com/account/api-tokens")
        sys.exit(1)
    return token


def list_models():
    """List available face restoration models."""
    print("\nAvailable Face Restoration Models:")
    print("-" * 70)
    for key, m in MODELS.items():
        scale_info = " (supports --scale)" if m["supports_scale"] else ""
        print(f"  {key:12s}  {m['name']:15s}  ~${m['cost_per_run']:.3f}/img{scale_info}")
        print(f"               {m['description']}")
    print(f"\nDefault: {DEFAULT_MODEL}")


def estimate_cost(count: int):
    """Estimate cost for face restoration."""
    print(f"\nCost Estimates for {count} images:")
    print("-" * 50)
    for key, m in MODELS.items():
        cost = count * m["cost_per_run"]
        print(f"  {m['name']:15s}  ${cost:.4f}  (${m['cost_per_run']:.3f}/img)")


def restore_face(image_path: str, model_key: str = DEFAULT_MODEL,
                 scale: int = 2, output_path: str = None):
    """Restore/enhance a face image."""
    if model_key not in MODELS:
        print(f"ERROR: Unknown model '{model_key}'. Use --list-models")
        sys.exit(1)

    if not os.path.exists(image_path):
        print(f"ERROR: Image not found: {image_path}")
        sys.exit(1)

    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = Path(image_path).stem
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_path = str(output_dir / f"{stem}_restored_{model_key}_{timestamp}.png")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    get_api_token()

    model = MODELS[model_key]

    print(f"\n  [{model['name']}] {Path(image_path).name}", end=" → ")

    try:
        import replicate
        import requests
    except ImportError:
        print("ERROR: replicate and requests required. Run: pip install replicate requests")
        sys.exit(1)

    # Build input payload
    input_payload = {"img": open(image_path, "rb")}

    if model_key == "realesrgan" and scale:
        input_payload["scale"] = scale

    if model_key == "gfpgan":
        input_payload["version"] = "v1.4"

    try:
        output = replicate.run(model["id"], input=input_payload)

        # Extract output URL
        image_url = None
        if isinstance(output, str):
            image_url = output
        elif hasattr(output, 'url'):
            image_url = output.url
        elif isinstance(output, dict):
            image_url = output.get("url") or output.get("output") or output.get("image")
        elif isinstance(output, list) and output:
            image_url = output[0] if isinstance(output[0], str) else output[0].get("url")

        if not image_url:
            print(f"FAILED (unexpected output: {type(output)})")
            return None

        # Download result
        image_data = requests.get(image_url, timeout=120).content
        with open(output_path, "wb") as f:
            f.write(image_data)

        file_size = os.path.getsize(output_path)
        print(f"{Path(output_path).name} ({file_size / 1024:.0f} KB)")
        return output_path

    except Exception as e:
        print(f"ERROR: {e}")
        return None
    finally:
        fh = input_payload.get("img")
        if hasattr(fh, "close"):
            fh.close()


def compare_all(image_path: str, scale: int = 2):
    """Run all models for side-by-side comparison."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = Path(image_path).stem
    output_dir = Path(__file__).parent / "output" / f"restore_compare_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nFace Restoration Comparison")
    print(f"{'='*60}")
    print(f"  Input: {image_path}")
    print(f"  Output: {output_dir}")
    print(f"{'='*60}")

    results = []
    total_cost = 0.0

    for key, model in MODELS.items():
        output_path = str(output_dir / f"{stem}_{key}.png")
        result = restore_face(image_path, model_key=key, scale=scale,
                              output_path=output_path)
        if result:
            results.append({"model": key, "name": model["name"], "path": result})
            total_cost += model["cost_per_run"]

    print(f"\n{'='*60}")
    print(f"Comparison Complete")
    print(f"  Generated: {len(results)}/{len(MODELS)}")
    print(f"  Est. total cost: ${total_cost:.4f}")
    print(f"  Output: {output_dir}")
    print(f"\nCompare outputs side-by-side to evaluate quality.")
    return results


def batch_restore(pattern: str, model_key: str = DEFAULT_MODEL, scale: int = 2):
    """Restore all images matching a glob pattern."""
    image_extensions = {".png", ".jpg", ".jpeg", ".webp"}

    # Expand pattern
    if os.path.isdir(pattern):
        files = []
        for ext in image_extensions:
            files.extend(glob_module.glob(os.path.join(pattern, f"*{ext}")))
    else:
        files = glob_module.glob(pattern)
        files = [f for f in files if Path(f).suffix.lower() in image_extensions]

    if not files:
        print(f"ERROR: No image files found matching: {pattern}")
        sys.exit(1)

    files.sort()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent / "output" / f"batch_restore_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    model = MODELS[model_key]
    est_cost = len(files) * model["cost_per_run"]

    print(f"\nBatch Face Restoration")
    print(f"{'='*60}")
    print(f"  Model: {model['name']}")
    print(f"  Files: {len(files)}")
    print(f"  Output: {output_dir}")
    print(f"  Est. cost: ${est_cost:.4f}")
    print(f"{'='*60}")

    results = []
    for f in files:
        stem = Path(f).stem
        output_path = str(output_dir / f"{stem}_restored.png")
        result = restore_face(f, model_key=model_key, scale=scale,
                              output_path=output_path)
        if result:
            results.append(result)

    print(f"\n{'='*60}")
    print(f"Batch Complete: {len(results)}/{len(files)} restored")
    print(f"  Output: {output_dir}")
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Face restoration and enhancement via Replicate (GFPGAN / Real-ESRGAN)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Restore a face image (default: GFPGAN)
  python test_face_restore.py --image blurry_face.png

  # Upscale with Real-ESRGAN (4x)
  python test_face_restore.py --image low_res.png --model realesrgan --scale 4

  # Compare GFPGAN vs Real-ESRGAN
  python test_face_restore.py --image face.png --compare-all

  # Batch restore a directory of images
  python test_face_restore.py --batch output/consistency_20260209/

  # Batch with glob pattern
  python test_face_restore.py --batch "output/seed_*.png"

  # Estimate cost for 10 images
  python test_face_restore.py --cost --count 10

Models:
  gfpgan       GFPGAN v1.4     ~$0.005/img  Face-specific (default)
  realesrgan   Real-ESRGAN     ~$0.010/img  General upscaling (--scale)

Workflow:
  1. Generate character with test_character_consistency.py
  2. (Optional) Find best seed with test_seed_bracketing.py
  3. Enhance face with this script
  4. Animate with test_talking_head.py or test_image_to_video.py
        """
    )
    parser.add_argument("--image", "-i", type=str, help="Input image path")
    parser.add_argument("--model", "-m", type=str, default=DEFAULT_MODEL,
                        choices=list(MODELS.keys()),
                        help=f"Restoration model (default: {DEFAULT_MODEL})")
    parser.add_argument("--scale", type=int, default=2,
                        help="Upscale factor for Real-ESRGAN (default: 2)")
    parser.add_argument("--output", "-o", type=str, help="Output image path")
    parser.add_argument("--compare-all", action="store_true",
                        help="Run all models for comparison")
    parser.add_argument("--batch", type=str,
                        help="Batch restore: directory path or glob pattern")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    parser.add_argument("--cost", action="store_true", help="Estimate cost")
    parser.add_argument("--count", type=int, default=10,
                        help="Number of images (for cost estimate)")

    args = parser.parse_args()

    if args.list_models:
        list_models()
        return

    if args.cost:
        estimate_cost(args.count)
        return

    if args.batch:
        batch_restore(args.batch, model_key=args.model, scale=args.scale)
        return

    if not args.image:
        parser.print_help()
        print("\nERROR: --image, --batch, or --compare-all required")
        sys.exit(1)

    if args.compare_all:
        compare_all(args.image, scale=args.scale)
    else:
        restore_face(args.image, model_key=args.model, scale=args.scale,
                     output_path=args.output)


if __name__ == "__main__":
    main()
