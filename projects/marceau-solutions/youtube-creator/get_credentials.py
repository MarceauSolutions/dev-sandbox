#!/usr/bin/env python3
"""
YouTube OAuth Credential Generator

Run this script to get your YOUTUBE_REFRESH_TOKEN.
It will open a browser for Google authentication.
"""

from google_auth_oauthlib.flow import InstalledAppFlow
import os

# Scopes needed for YouTube API
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'https://www.googleapis.com/auth/yt-analytics.readonly'
]

# Path to your client secret file
CLIENT_SECRET_FILE = 'client_secret_915754256960-qoa6vh953aolba3emq7h2j29gogtmul5.apps.googleusercontent.com.json'

def main():
    # Check if client secret file exists
    if not os.path.exists(CLIENT_SECRET_FILE):
        print(f"ERROR: {CLIENT_SECRET_FILE} not found!")
        print("Download it from Google Cloud Console -> APIs & Services -> Credentials")
        return

    print("Starting OAuth flow...")
    print("A browser window will open for Google authentication.")
    print()

    # Run the OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    credentials = flow.run_local_server(port=8080)

    print("\n" + "="*60)
    print("SUCCESS! Here are your credentials:")
    print("="*60)
    print()
    print("Add these to your .env file or environment:")
    print()
    print(f'YOUTUBE_CLIENT_ID="{credentials.client_id}"')
    print(f'YOUTUBE_CLIENT_SECRET="{credentials.client_secret}"')
    print(f'YOUTUBE_REFRESH_TOKEN="{credentials.refresh_token}"')
    print()
    print("="*60)


if __name__ == "__main__":
    main()
