#!/usr/bin/env python3
"""
test_lipsync.py - Lip Sync Model Testing (fal.ai)

Test multiple lip sync models to sync audio to video/image.
Compare quality across Lipsync 1.9, 2.0, MuseTalk, and LatentSync.

Usage:
    python test_lipsync.py --video face.mp4 --audio speech.mp3
    python test_lipsync.py --video face.mp4 --audio speech.mp3 --model musetalk
    python test_lipsync.py --image face.png --audio speech.mp3 --model musetalk
    python test_lipsync.py --video face.mp4 --audio speech.mp3 --compare-all
    python test_lipsync.py --cost --duration 30

Requires: FAL_API_KEY in .env
"""

import argparse
import os
import sys
import time
from pathlib import Path
from datetime import datetime

SANDBOX_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(SANDBOX_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(SANDBOX_ROOT / ".env")
except ImportError:
    pass


FAL_API_BASE = "https://queue.fal.run"

MODELS = {
    "sync19": {
        "id": "fal-ai/sync-lipsync",
        "name": "Lipsync 1.9",
        "cost_per_min": 0.70,
        "input": "video+audio",
        "description": "Best value lip sync — video + audio input"
    },
    "sync20": {
        "id": "fal-ai/sync-lipsync/v2",
        "name": "Lipsync 2.0",
        "cost_per_min": 3.00,
        "input": "video+audio",
        "description": "Higher quality lip sync — video + audio input"
    },
    "musetalk": {
        "id": "fal-ai/musetalk",
        "name": "MuseTalk",
        "cost_per_min": 0.50,
        "input": "image+audio",
        "description": "Audio-driven lip sync from single image"
    },
    "latentsync": {
        "id": "fal-ai/latentsync",
        "name": "LatentSync",
        "cost_per_min": 0.50,
        "input": "video+audio",
        "description": "Latest generation lip sync model"
    },
}

DEFAULT_MODEL = "sync19"


def get_api_key():
    key = os.environ.get("FAL_API_KEY")
    if not key:
        print("ERROR: FAL_API_KEY not found in .env")
        print(f"Add to: {SANDBOX_ROOT / '.env'}")
        print("Get key at: https://fal.ai/")
        sys.exit(1)
    return key


def list_models():
    """List available lip sync models."""
    print("\nAvailable Lip Sync Models:")
    print("-" * 70)
    for key, m in MODELS.items():
        print(f"  {key:12s}  {m['name']:15s}  ${m['cost_per_min']:.2f}/min  [{m['input']}]")
        print(f"               {m['description']}")
    print(f"\nDefault: {DEFAULT_MODEL}")


def estimate_cost(duration_sec: float):
    """Estimate cost for each model."""
    minutes = duration_sec / 60
    print(f"\nCost Estimates for {duration_sec:.0f}s video:")
    print("-" * 50)
    for key, m in MODELS.items():
        cost = minutes * m["cost_per_min"]
        print(f"  {m['name']:15s}  ${cost:.4f}  (${m['cost_per_min']:.2f}/min)")


def _upload_file(file_path: str, api_key: str) -> str:
    """Upload a local file to fal.ai and return the URL."""
    try:
        import requests
    except ImportError:
        print("ERROR: requests required. Run: pip install requests")
        sys.exit(1)

    headers = {"Authorization": f"Key {api_key}"}

    # Determine content type
    ext = Path(file_path).suffix.lower()
    content_types = {
        ".mp4": "video/mp4", ".mp3": "audio/mpeg", ".wav": "audio/wav",
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".webp": "image/webp", ".webm": "video/webm",
    }
    content_type = content_types.get(ext, "application/octet-stream")

    with open(file_path, "rb") as f:
        resp = requests.post(
            "https://fal.run/fal-ai/file-upload",
            headers={**headers, "Content-Type": content_type},
            data=f,
            timeout=120
        )

    if resp.status_code == 200:
        result = resp.json()
        return result.get("url") or result.get("file_url")
    else:
        # Fallback: try the REST upload endpoint
        with open(file_path, "rb") as f:
            resp = requests.post(
                "https://rest.alpha.fal.ai/storage/upload",
                headers=headers,
                files={"file": (os.path.basename(file_path), f, content_type)},
                timeout=120
            )
        if resp.status_code == 200:
            result = resp.json()
            return result.get("url") or result.get("file_url")

    print(f"  WARNING: File upload returned {resp.status_code}, trying with local path")
    return None


def _submit_and_poll(model_id: str, payload: dict, api_key: str,
                     output_path: str, timeout_sec: int = 300) -> str:
    """Submit to fal.ai queue and poll for result."""
    try:
        import requests
    except ImportError:
        print("ERROR: requests required")
        sys.exit(1)

    headers = {
        "Authorization": f"Key {api_key}",
        "Content-Type": "application/json"
    }

    # Submit
    response = requests.post(
        f"{FAL_API_BASE}/{model_id}",
        headers=headers,
        json=payload,
        timeout=60
    )

    if response.status_code == 200:
        result = response.json()
        return _extract_video(result, output_path)

    # Queue-based response
    result = response.json()
    request_id = result.get("request_id")
    if not request_id:
        print(f"  ERROR: No request_id. Status: {response.status_code}")
        print(f"  Response: {response.text[:500]}")
        return None

    # Poll
    status_url = f"{FAL_API_BASE}/{model_id}/requests/{request_id}/status"
    result_url = f"{FAL_API_BASE}/{model_id}/requests/{request_id}"

    print("  Queued, polling for result...")
    max_polls = timeout_sec // 3
    for i in range(max_polls):
        time.sleep(3)
        resp = requests.get(status_url, headers={"Authorization": f"Key {api_key}"}, timeout=30)
        if resp.status_code == 200:
            status = resp.json()
            st = status.get("status", "unknown")
            if st == "COMPLETED":
                result_resp = requests.get(
                    result_url,
                    headers={"Authorization": f"Key {api_key}"},
                    timeout=30
                )
                if result_resp.status_code == 200:
                    return _extract_video(result_resp.json(), output_path)
            elif st in ("FAILED", "CANCELLED"):
                print(f"\n  ERROR: Generation {st}: {status}")
                return None
            print(f"  Status: {st} ({(i+1)*3}s)...", end="\r")

    print("\n  ERROR: Timed out waiting for result")
    return None


def _extract_video(result: dict, output_path: str) -> str:
    """Extract video from fal.ai result and save to disk."""
    import requests

    video_url = (result.get("video", {}).get("url")
                 or result.get("video_url")
                 or result.get("output", {}).get("url")
                 or result.get("output_url")
                 or result.get("url"))

    if not video_url:
        # Try nested output
        output = result.get("output")
        if isinstance(output, str) and output.startswith("http"):
            video_url = output
        elif isinstance(output, list) and output:
            video_url = output[0] if isinstance(output[0], str) else output[0].get("url")

    if not video_url:
        print(f"  WARNING: No video URL in response")
        print(f"  Keys: {list(result.keys())}")
        return None

    video_data = requests.get(video_url, timeout=120).content
    with open(output_path, "wb") as f:
        f.write(video_data)

    file_size = os.path.getsize(output_path)
    print(f"\n  Saved: {output_path} ({file_size / 1024 / 1024:.1f} MB)")
    return output_path


def run_lipsync(video_path: str = None, image_path: str = None,
                audio_path: str = None, model_key: str = DEFAULT_MODEL,
                output_path: str = None):
    """Run lip sync with specified model."""
    if model_key not in MODELS:
        print(f"ERROR: Unknown model '{model_key}'. Use --list-models")
        sys.exit(1)

    model = MODELS[model_key]

    if not audio_path or not os.path.exists(audio_path):
        print(f"ERROR: Audio file required: {audio_path}")
        sys.exit(1)

    if not video_path and not image_path:
        print("ERROR: --video or --image required")
        sys.exit(1)

    input_path = video_path or image_path
    if not os.path.exists(input_path):
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_path = str(output_dir / f"lipsync_{model_key}_{timestamp}.mp4")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    api_key = get_api_key()

    print(f"\nLip Sync Generation")
    print(f"{'='*60}")
    print(f"  Model: {model['name']} ({model_key})")
    print(f"  Input: {input_path}")
    print(f"  Audio: {audio_path}")
    print(f"  Output: {output_path}")
    print(f"  Cost: ~${model['cost_per_min']:.2f}/min")
    print(f"{'='*60}")

    # Upload files to fal.ai
    print("  Uploading input file...")
    input_url = _upload_file(input_path, api_key)
    print("  Uploading audio file...")
    audio_url = _upload_file(audio_path, api_key)

    # Build payload based on model
    if model_key in ("sync19", "sync20"):
        payload = {"video_url": input_url or input_path, "audio_url": audio_url or audio_path}
    elif model_key == "musetalk":
        if image_path:
            payload = {"image_url": input_url or input_path, "audio_url": audio_url or audio_path}
        else:
            payload = {"video_url": input_url or input_path, "audio_url": audio_url or audio_path}
    elif model_key == "latentsync":
        payload = {"video_url": input_url or input_path, "audio_url": audio_url or audio_path}
    else:
        payload = {"video_url": input_url or input_path, "audio_url": audio_url or audio_path}

    print("  Submitting to fal.ai...")
    return _submit_and_poll(model["id"], payload, api_key, output_path)


def compare_all(video_path: str = None, image_path: str = None,
                audio_path: str = None):
    """Run all compatible models for side-by-side comparison."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent / "output" / f"lipsync_compare_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nLip Sync Model Comparison")
    print(f"{'='*60}")
    print(f"  Output dir: {output_dir}")
    print(f"{'='*60}")

    results = []
    total_cost = 0.0

    for key, model in MODELS.items():
        # Skip image-only models if we have video, and vice versa
        if model["input"] == "image+audio" and not image_path and video_path:
            print(f"\n  Skipping {model['name']} (requires image input, got video)")
            continue

        output_path = str(output_dir / f"{key}.mp4")
        print(f"\n--- {model['name']} ---")

        result = run_lipsync(
            video_path=video_path, image_path=image_path,
            audio_path=audio_path, model_key=key, output_path=output_path
        )

        if result:
            results.append({"model": key, "name": model["name"], "path": result})
            total_cost += model["cost_per_min"] * 0.5  # Estimate 30s

    print(f"\n{'='*60}")
    print(f"Comparison Complete")
    print(f"  Generated: {len(results)}/{len(MODELS)}")
    print(f"  Est. total cost: ${total_cost:.4f}")
    print(f"  Output: {output_dir}")
    print(f"\nReview outputs side-by-side to compare quality.")
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Test lip sync models via fal.ai",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Lip sync video with new audio (default: Lipsync 1.9)
  python test_lipsync.py --video face.mp4 --audio speech.mp3

  # Use MuseTalk (works from single image)
  python test_lipsync.py --image face.png --audio speech.mp3 --model musetalk

  # Compare all models
  python test_lipsync.py --video face.mp4 --audio speech.mp3 --compare-all

  # Estimate costs
  python test_lipsync.py --cost --duration 30

Models:
  sync19      Lipsync 1.9      $0.70/min  video+audio  (best value)
  sync20      Lipsync 2.0      $3.00/min  video+audio  (highest quality)
  musetalk    MuseTalk         $0.50/min  image+audio  (single image)
  latentsync  LatentSync       $0.50/min  video+audio  (latest gen)
        """
    )
    parser.add_argument("--video", "-v", type=str, help="Input video file")
    parser.add_argument("--image", "-i", type=str, help="Input image file (for MuseTalk)")
    parser.add_argument("--audio", "-a", type=str, help="Audio file to sync")
    parser.add_argument("--model", "-m", type=str, default=DEFAULT_MODEL,
                        choices=list(MODELS.keys()),
                        help=f"Lip sync model (default: {DEFAULT_MODEL})")
    parser.add_argument("--output", "-o", type=str, help="Output video path")
    parser.add_argument("--compare-all", action="store_true",
                        help="Run all models for comparison")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    parser.add_argument("--cost", action="store_true", help="Estimate cost")
    parser.add_argument("--duration", type=float, default=30,
                        help="Video duration in seconds (for cost estimate)")

    args = parser.parse_args()

    if args.list_models:
        list_models()
        return

    if args.cost:
        estimate_cost(args.duration)
        return

    if not args.audio:
        parser.print_help()
        print("\nERROR: --audio required")
        sys.exit(1)

    if not args.video and not args.image:
        parser.print_help()
        print("\nERROR: --video or --image required")
        sys.exit(1)

    if args.compare_all:
        compare_all(video_path=args.video, image_path=args.image,
                     audio_path=args.audio)
    else:
        run_lipsync(video_path=args.video, image_path=args.image,
                    audio_path=args.audio, model_key=args.model,
                    output_path=args.output)


if __name__ == "__main__":
    main()
