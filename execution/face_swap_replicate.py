#!/usr/bin/env python3
"""
Face Swap via Replicate (roop_face_swap).

Swaps a face from a source image onto a target video using arabyai-replicate/roop_face_swap.
Processes frame-by-frame server-side, returns face-swapped video.

Cost: ~$0.12/run (~4min for 10s video)

Usage:
    python execution/face_swap_replicate.py --face julia.png --video stock.mp4 --output julia-swapped.mp4
    python execution/face_swap_replicate.py --face julia.png --video stock.mp4 --cost  # estimate only
"""
import os
import sys
import json
import time
import base64
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN', '')
MODEL_VERSION = '11b6bf0f4e14d808f655e87e5448233cceff10a45f659d71539cafb7163b2e84'
COST_PER_RUN = 0.12  # approximate


def file_to_data_uri(path: str) -> str:
    """Convert a local file to a data URI for Replicate input."""
    ext = Path(path).suffix.lower()
    mime_map = {
        '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
        '.webp': 'image/webp', '.mp4': 'video/mp4', '.mov': 'video/quicktime',
        '.avi': 'video/x-msvideo', '.webm': 'video/webm',
    }
    mime = mime_map.get(ext, 'application/octet-stream')
    with open(path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    return f'data:{mime};base64,{b64}'


def swap_face(face_image_path: str, target_video_path: str, output_path: str,
              poll_interval: int = 10, timeout: int = 600) -> str:
    """Run face swap on Replicate.

    Args:
        face_image_path: Path to source face image (Julia's headshot)
        target_video_path: Path to target video (stock exercise footage)
        output_path: Where to save the face-swapped video
        poll_interval: Seconds between status checks
        timeout: Max seconds to wait

    Returns:
        Path to output video
    """
    if not REPLICATE_API_TOKEN:
        raise ValueError("REPLICATE_API_TOKEN not set in .env")

    headers = {
        'Authorization': f'Bearer {REPLICATE_API_TOKEN}',
        'Content-Type': 'application/json',
    }

    print(f"Face swap: {Path(face_image_path).name} -> {Path(target_video_path).name}")
    print(f"  Estimated cost: ~${COST_PER_RUN:.2f}")

    # Convert files to data URIs
    print("  Encoding files...")
    swap_image_uri = file_to_data_uri(face_image_path)
    target_video_uri = file_to_data_uri(target_video_path)

    # Create prediction
    print("  Submitting to Replicate...")
    resp = requests.post(
        'https://api.replicate.com/v1/predictions',
        headers=headers,
        json={
            'version': MODEL_VERSION,
            'input': {
                'swap_image': swap_image_uri,
                'target_video': target_video_uri,
            },
        },
        timeout=60,
    )
    resp.raise_for_status()
    prediction = resp.json()
    pred_id = prediction['id']
    print(f"  Prediction ID: {pred_id}")

    # Poll for completion
    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            raise TimeoutError(f"Face swap timed out after {timeout}s")

        time.sleep(poll_interval)
        status_resp = requests.get(
            f'https://api.replicate.com/v1/predictions/{pred_id}',
            headers={'Authorization': f'Bearer {REPLICATE_API_TOKEN}'},
            timeout=30,
        )
        status_resp.raise_for_status()
        status = status_resp.json()

        state = status.get('status', 'unknown')
        print(f"  [{int(elapsed)}s] Status: {state}")

        if state == 'succeeded':
            output_url = status.get('output', '')
            if not output_url:
                raise RuntimeError("No output URL in successful prediction")

            # Download result
            print(f"  Downloading result...")
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            dl = requests.get(output_url, stream=True, timeout=120)
            dl.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in dl.iter_content(chunk_size=8192):
                    f.write(chunk)

            size_mb = os.path.getsize(output_path) / 1024 / 1024
            metrics = status.get('metrics', {})
            predict_time = metrics.get('predict_time', 0)
            print(f"  Done! {output_path} ({size_mb:.1f} MB, {predict_time:.0f}s processing)")
            return output_path

        elif state == 'failed':
            error = status.get('error', 'Unknown error')
            raise RuntimeError(f"Face swap failed: {error}")

        elif state == 'canceled':
            raise RuntimeError("Face swap was canceled")


def estimate_cost(n_videos: int = 1):
    """Print cost estimate without running."""
    total = COST_PER_RUN * n_videos
    print(f"Cost estimate: {n_videos} video(s) x ${COST_PER_RUN:.2f} = ${total:.2f}")
    print(f"Model: arabyai-replicate/roop_face_swap")
    print(f"Processing: ~4 min per 10s video (frame-by-frame)")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Face Swap via Replicate')
    parser.add_argument('--face', required=True, help='Source face image (e.g., julia.png)')
    parser.add_argument('--video', required=True, help='Target video (e.g., stock-hip-thrust.mp4)')
    parser.add_argument('--output', default=None, help='Output path (default: <video>-swapped.mp4)')
    parser.add_argument('--cost', action='store_true', help='Print cost estimate only')
    parser.add_argument('--timeout', type=int, default=600, help='Max wait time in seconds')
    args = parser.parse_args()

    if args.cost:
        estimate_cost(1)
        sys.exit(0)

    output = args.output or str(Path(args.video).with_suffix('')) + '-swapped.mp4'
    swap_face(args.face, args.video, output, timeout=args.timeout)
