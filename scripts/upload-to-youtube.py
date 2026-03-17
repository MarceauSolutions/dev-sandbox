#!/usr/bin/env python3
"""
upload-to-youtube.py — YouTube Upload via Data API v3

WHAT: Uploads a video to YouTube with title, description, tags
WHY:  One-command publishing from the content pipeline
INPUT: Video file path, title, description, tags
OUTPUT: YouTube video URL on success
COST: FREE (YouTube Data API quota: ~6 uploads/day on default quota)

USAGE:
  python scripts/upload-to-youtube.py \\
    --file output/processed/2026-03-17/video_processed.mp4 \\
    --title "5 Training Mistakes Killing Your Gains" \\
    --description "In this video I break down..." \\
    --tags "fitness,training,muscle building" \\
    --privacy unlisted

  python scripts/upload-to-youtube.py \\
    --file output/shorts/2026-03-17/001.mp4 \\
    --title "Quick Tip: Protein Timing #shorts" \\
    --description "Quick fitness tip" \\
    --category 17 \\
    --privacy public

DEPENDENCIES: google-api-python-client, google-auth-oauthlib
API_KEYS: YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN (in .env)
"""

import argparse
import os
import sys
import json
import time
from pathlib import Path

# Load .env
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
except ImportError:
    print("Error: Google API client not installed.")
    print("Install with: pip install google-api-python-client google-auth-oauthlib")
    sys.exit(1)


# YouTube API scopes
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# YouTube video categories (common ones)
CATEGORIES = {
    "film": 1,
    "autos": 2,
    "music": 10,
    "pets": 15,
    "sports": 17,
    "travel": 19,
    "gaming": 20,
    "people": 22,
    "comedy": 23,
    "entertainment": 24,
    "news": 25,
    "howto": 26,
    "education": 27,
    "science": 28,
}


def get_youtube_service():
    """Build authenticated YouTube API service using OAuth refresh token."""
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        missing = []
        if not client_id: missing.append("YOUTUBE_CLIENT_ID")
        if not client_secret: missing.append("YOUTUBE_CLIENT_SECRET")
        if not refresh_token: missing.append("YOUTUBE_REFRESH_TOKEN")
        print(f"Error: Missing YouTube credentials in .env: {', '.join(missing)}")
        sys.exit(1)

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=YOUTUBE_SCOPES,
    )

    # Refresh the token
    try:
        creds.refresh(Request())
    except Exception as e:
        print(f"Error refreshing YouTube token: {e}")
        print("You may need to re-authorize. Run the OAuth flow to get a new refresh token.")
        sys.exit(1)

    return build("youtube", "v3", credentials=creds)


def upload_video(
    file_path: str,
    title: str,
    description: str = "",
    tags: list = None,
    category_id: int = 17,  # Sports by default (fitness)
    privacy: str = "unlisted",
    made_for_kids: bool = False,
) -> dict:
    """
    Upload a video to YouTube.

    Args:
        file_path: Path to the video file
        title: Video title
        description: Video description
        tags: List of tags
        category_id: YouTube category ID (17=Sports)
        privacy: "public", "unlisted", or "private"
        made_for_kids: COPPA designation

    Returns:
        Dict with video_id and url on success, error on failure
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"  File: {os.path.basename(file_path)} ({file_size_mb:.1f} MB)")

    youtube = get_youtube_service()

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": str(category_id),
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": made_for_kids,
        },
    }

    # Use resumable upload for reliability
    media = MediaFileUpload(
        file_path,
        mimetype="video/*",
        resumable=True,
        chunksize=10 * 1024 * 1024,  # 10MB chunks
    )

    try:
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        print("  Uploading...")
        response = None
        retry_count = 0
        max_retries = 3

        while response is None:
            try:
                status, response = request.next_chunk()
                if status:
                    pct = int(status.progress() * 100)
                    print(f"  Progress: {pct}%")
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504] and retry_count < max_retries:
                    retry_count += 1
                    wait = 2 ** retry_count
                    print(f"  Retrying in {wait}s (attempt {retry_count}/{max_retries})...")
                    time.sleep(wait)
                else:
                    raise

        video_id = response.get("id")
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        return {
            "video_id": video_id,
            "url": video_url,
            "title": title,
            "privacy": privacy,
        }

    except HttpError as e:
        error_detail = json.loads(e.content.decode()) if e.content else {}
        error_msg = error_detail.get("error", {}).get("message", str(e))
        return {"error": f"YouTube API error: {error_msg}"}
    except Exception as e:
        return {"error": f"Upload failed: {str(e)}"}


def main():
    parser = argparse.ArgumentParser(
        description='Upload video to YouTube via Data API v3'
    )
    parser.add_argument('--file', required=True, help='Path to video file')
    parser.add_argument('--title', required=True, help='Video title')
    parser.add_argument('--description', default='', help='Video description')
    parser.add_argument('--tags', default='', help='Comma-separated tags')
    parser.add_argument('--category', type=int, default=17,
                        help='YouTube category ID (default: 17=Sports)')
    parser.add_argument('--privacy', choices=['public', 'unlisted', 'private'],
                        default='unlisted', help='Privacy status (default: unlisted)')
    parser.add_argument('--made-for-kids', action='store_true',
                        help='Mark as made for kids (COPPA)')

    args = parser.parse_args()

    # Validate
    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}")
        return 1

    tags = [t.strip() for t in args.tags.split(',') if t.strip()] if args.tags else []

    print()
    print("=" * 60)
    print("  YOUTUBE UPLOADER -- Marceau Fitness")
    print("=" * 60)
    print(f"  Title:    {args.title}")
    print(f"  Privacy:  {args.privacy}")
    print(f"  Tags:     {', '.join(tags) if tags else '(none)'}")
    print(f"  Category: {args.category}")
    print("=" * 60)
    print()

    result = upload_video(
        file_path=args.file,
        title=args.title,
        description=args.description,
        tags=tags,
        category_id=args.category,
        privacy=args.privacy,
        made_for_kids=args.made_for_kids,
    )

    if "error" in result:
        print(f"\n  FAILED: {result['error']}")
        return 1

    print()
    print("=" * 60)
    print("  UPLOAD COMPLETE")
    print("=" * 60)
    print(f"  Video ID: {result['video_id']}")
    print(f"  URL:      {result['url']}")
    print(f"  Privacy:  {result['privacy']}")
    print("=" * 60)
    print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
