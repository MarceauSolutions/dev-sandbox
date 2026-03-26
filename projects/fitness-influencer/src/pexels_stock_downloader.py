#!/usr/bin/env python3
"""
Pexels Stock Video Downloader.

Search and download free stock videos from Pexels for use in video pipelines.
Requires PEXELS_API_KEY in .env (free at https://www.pexels.com/api/).

Usage:
    python execution/pexels_stock_downloader.py search "woman hip thrust gym" --orientation portrait
    python execution/pexels_stock_downloader.py download <video_id> output.mp4
"""
import os
import sys
import json
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

PEXELS_API_KEY = os.getenv('PEXELS_API_KEY', '')
BASE_URL = 'https://api.pexels.com'


def search_videos(query: str, orientation: str = 'portrait', per_page: int = 5, page: int = 1) -> dict:
    """Search Pexels for videos matching query."""
    if not PEXELS_API_KEY:
        raise ValueError("PEXELS_API_KEY not set. Get a free key at https://www.pexels.com/api/")

    resp = requests.get(
        f'{BASE_URL}/videos/search',
        headers={'Authorization': PEXELS_API_KEY},
        params={
            'query': query,
            'orientation': orientation,
            'per_page': per_page,
            'page': page,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def download_video(video_url: str, output_path: str) -> str:
    """Download a video file from URL to local path."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(video_url, stream=True, timeout=120)
    resp.raise_for_status()
    with open(output_path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"  Downloaded: {output_path} ({size_mb:.1f} MB)")
    return output_path


def get_best_video_file(video_data: dict, quality: str = 'hd', max_width: int = 1080) -> dict | None:
    """Pick the best video file from Pexels video data.

    Prefers portrait orientation, HD quality, manageable file size.
    """
    files = video_data.get('video_files', [])
    if not files:
        return None

    # Sort by quality preference: prefer HD, portrait, reasonable resolution
    scored = []
    for f in files:
        score = 0
        w = f.get('width', 0)
        h = f.get('height', 0)
        q = f.get('quality', '')

        # Prefer portrait (h > w)
        if h > w:
            score += 10
        # Prefer HD
        if q == 'hd':
            score += 5
        elif q == 'sd':
            score += 1
        # Prefer width close to target
        if 0 < w <= max_width:
            score += 3
        # Penalize very large files
        if w > 1920:
            score -= 5

        scored.append((score, f))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1] if scored else files[0]


def search_and_download(query: str, output_path: str, orientation: str = 'portrait') -> str | None:
    """One-shot: search for a video and download the best match."""
    print(f"Searching Pexels: '{query}' ({orientation})...")
    results = search_videos(query, orientation=orientation, per_page=10)

    videos = results.get('videos', [])
    if not videos:
        print(f"  No results found for '{query}'")
        return None

    # Pick first result (most relevant)
    video = videos[0]
    print(f"  Found: '{video.get('url', '')}' ({video.get('duration', 0)}s)")

    best_file = get_best_video_file(video)
    if not best_file:
        print("  No suitable video file found")
        return None

    w, h = best_file.get('width', 0), best_file.get('height', 0)
    print(f"  Quality: {best_file.get('quality', '?')} | {w}x{h}")

    return download_video(best_file['link'], output_path)


def list_results(query: str, orientation: str = 'portrait', per_page: int = 5):
    """Search and display results for manual selection."""
    results = search_videos(query, orientation=orientation, per_page=per_page)
    videos = results.get('videos', [])
    print(f"\nPexels results for '{query}' ({len(videos)} found):\n")
    for i, v in enumerate(videos):
        dur = v.get('duration', 0)
        w = v.get('width', 0)
        h = v.get('height', 0)
        url = v.get('url', '')
        vid = v.get('id', '')
        files = v.get('video_files', [])
        best = get_best_video_file(v)
        bw = best.get('width', 0) if best else 0
        bh = best.get('height', 0) if best else 0
        print(f"  [{i+1}] ID:{vid} | {dur}s | {w}x{h} | best: {bw}x{bh}")
        print(f"       {url}")
    return videos


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pexels Stock Video Downloader')
    sub = parser.add_subparsers(dest='cmd')

    sp_search = sub.add_parser('search', help='Search for videos')
    sp_search.add_argument('query', help='Search query')
    sp_search.add_argument('--orientation', default='portrait', choices=['portrait', 'landscape', 'square'])
    sp_search.add_argument('--per-page', type=int, default=5)

    sp_dl = sub.add_parser('download', help='Search and download best match')
    sp_dl.add_argument('query', help='Search query')
    sp_dl.add_argument('output', help='Output file path')
    sp_dl.add_argument('--orientation', default='portrait', choices=['portrait', 'landscape', 'square'])

    args = parser.parse_args()

    if args.cmd == 'search':
        list_results(args.query, orientation=args.orientation, per_page=args.per_page)
    elif args.cmd == 'download':
        search_and_download(args.query, args.output, orientation=args.orientation)
    else:
        parser.print_help()
