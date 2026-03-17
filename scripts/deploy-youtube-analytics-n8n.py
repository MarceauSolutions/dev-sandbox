#!/usr/bin/env python3
"""
Deploy YouTube Analytics Collector n8n Workflow

WHAT: Creates and activates an n8n workflow that collects YouTube analytics weekly
WHY: Automated tracking of subscriber count, views, recent video performance
WHEN: Runs every Sunday 8pm ET via n8n cron trigger
OUTPUT: Logs data to Scorecard Google Sheet Content Calendar tab

QUICK USAGE:
    python scripts/deploy-youtube-analytics-n8n.py

Created: 2026-03-17
"""

import os
import sys
import json
import requests
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

N8N_API_KEY = os.getenv("N8N_API_KEY")
N8N_BASE = "https://n8n.marceausolutions.com/api/v1"
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

# n8n credential IDs
TELEGRAM_CRED = {"telegramApi": {"id": "RlAwU3xzcX4hifgj", "name": "Clawdbot Telegram"}}
SHEETS_CRED = {"googleSheetsOAuth2Api": {"id": "mywn8S0xjRx9YM9K", "name": "Google Sheets account 4"}}

SCORECARD_SHEET_ID = os.getenv("SCORECARD_SPREADSHEET_ID", "1Y5PwloUBbHM8AeiL032_zWy9jjo9vwhyRZkl7qaKw5o")
TELEGRAM_CHAT_ID = "5692454753"


def build_workflow() -> dict:
    """Build the n8n workflow JSON."""

    # n8n 6-field cron: sec min hour dom mon dow
    # Sunday 8pm ET = 0 0 20 * * 0 (in ET; n8n runs in UTC on EC2, 8pm ET = midnight UTC Mon)
    # EC2 is UTC, so 8pm ET = 00:00 UTC (next day) during EDT, or 01:00 UTC during EST
    # March = EDT, so 8pm ET = 00:00 UTC Monday. But we want Sunday 8pm ET.
    # Sunday 8pm EDT = Monday 00:00 UTC
    # Use cron: 0 0 0 * * 1 (Monday 00:00 UTC = Sunday 8pm ET during EDT)

    workflow = {
        "name": "YouTube Analytics Collector",
        "nodes": [
            {
                "parameters": {
                    "rule": {
                        "interval": [
                            {
                                "field": "cronExpression",
                                "expression": "0 0 0 * * 1"
                            }
                        ]
                    }
                },
                "id": "yt-cron-trigger",
                "name": "Weekly Cron",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.2,
                "position": [220, 300]
            },
            {
                "parameters": {
                    "url": "https://www.googleapis.com/youtube/v3/channels",
                    "sendQuery": True,
                    "queryParameters": {
                        "parameters": [
                            {"name": "part", "value": "statistics,snippet"},
                            {"name": "mine", "value": "true"},
                            {"name": "key", "value": YOUTUBE_API_KEY}
                        ]
                    },
                    "options": {}
                },
                "id": "yt-channel-stats",
                "name": "Get Channel Stats",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [440, 200],
                "notesInFlow": True,
                "notes": "Fetches subscriber count, total views from YouTube Data API"
            },
            {
                "parameters": {
                    "url": "https://www.googleapis.com/youtube/v3/search",
                    "sendQuery": True,
                    "queryParameters": {
                        "parameters": [
                            {"name": "part", "value": "snippet"},
                            {"name": "channelId", "value": "={{ $json.items[0].id }}"},
                            {"name": "order", "value": "date"},
                            {"name": "maxResults", "value": "5"},
                            {"name": "type", "value": "video"},
                            {"name": "key", "value": YOUTUBE_API_KEY}
                        ]
                    },
                    "options": {}
                },
                "id": "yt-recent-videos",
                "name": "Get Recent Videos",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [660, 200]
            },
            {
                "parameters": {
                    "url": "=https://www.googleapis.com/youtube/v3/videos",
                    "sendQuery": True,
                    "queryParameters": {
                        "parameters": [
                            {"name": "part", "value": "statistics"},
                            {"name": "id", "value": "={{ $json.items.map(i => i.id.videoId).join(',') }}"},
                            {"name": "key", "value": YOUTUBE_API_KEY}
                        ]
                    },
                    "options": {}
                },
                "id": "yt-video-stats",
                "name": "Get Video Stats",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [880, 200]
            },
            {
                "parameters": {
                    "jsCode": """
// Combine channel stats and video stats
const channelData = $('Get Channel Stats').first().json;
const videoData = $('Get Video Stats').first().json;
const recentVideos = $('Get Recent Videos').first().json;

const channel = channelData.items ? channelData.items[0] : null;
const stats = channel ? channel.statistics : {};

// Sum recent video views
let recentViews = 0;
let videoSummary = [];
if (videoData.items) {
    for (const v of videoData.items) {
        const views = parseInt(v.statistics.viewCount || '0');
        recentViews += views;
        videoSummary.push(`${views} views`);
    }
}

const now = new Date().toISOString().split('T')[0];
const weekNum = Math.ceil((new Date() - new Date('2026-03-17')) / (7 * 24 * 60 * 60 * 1000)) + 1;

return [{
    json: {
        date: now,
        week_number: weekNum,
        subscriber_count: parseInt(stats.subscriberCount || '0'),
        total_views: parseInt(stats.viewCount || '0'),
        total_videos: parseInt(stats.videoCount || '0'),
        recent_5_video_views: recentViews,
        video_summary: videoSummary.join(', '),
        channel_name: channel ? channel.snippet.title : 'Unknown'
    }
}];
"""
                },
                "id": "yt-code-combine",
                "name": "Combine Stats",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [1100, 300]
            },
            {
                "parameters": {
                    "documentId": {
                        "__rl": True,
                        "mode": "id",
                        "value": SCORECARD_SHEET_ID
                    },
                    "sheetName": {
                        "__rl": True,
                        "mode": "id",
                        "value": "gid=0"
                    },
                    "columns": {
                        "mappingMode": "defineBelow",
                        "value": {
                            "Week_Number": "={{ $json.week_number }}",
                            "Video_Topic": "=YT Analytics: {{ $json.subscriber_count }} subs, {{ $json.total_views }} total views",
                            "Video_Type": "Analytics",
                            "Published": "TRUE",
                            "Published_Date": "={{ $json.date }}",
                            "Notes": "=Recent 5 video views: {{ $json.recent_5_video_views }}. {{ $json.video_summary }}"
                        }
                    },
                    "options": {}
                },
                "id": "yt-sheets-log",
                "name": "Log to Scorecard",
                "type": "n8n-nodes-base.googleSheets",
                "typeVersion": 4.5,
                "position": [1320, 200],
                "credentials": SHEETS_CRED
            },
            {
                "parameters": {
                    "chatId": TELEGRAM_CHAT_ID,
                    "text": "=📊 **YouTube Weekly Analytics**\n\nChannel: {{ $json.channel_name }}\nSubscribers: {{ $json.subscriber_count }}\nTotal Views: {{ $json.total_views }}\nTotal Videos: {{ $json.total_videos }}\nRecent 5 Video Views: {{ $json.recent_5_video_views }}\n\n_Week {{ $json.week_number }} — {{ $json.date }}_",
                    "additionalFields": {
                        "parse_mode": "Markdown"
                    }
                },
                "id": "yt-telegram-notify",
                "name": "Notify Telegram",
                "type": "n8n-nodes-base.telegram",
                "typeVersion": 1.2,
                "position": [1320, 420],
                "credentials": TELEGRAM_CRED
            }
        ],
        "connections": {
            "Weekly Cron": {
                "main": [[
                    {"node": "Get Channel Stats", "type": "main", "index": 0}
                ]]
            },
            "Get Channel Stats": {
                "main": [[
                    {"node": "Get Recent Videos", "type": "main", "index": 0}
                ]]
            },
            "Get Recent Videos": {
                "main": [[
                    {"node": "Get Video Stats", "type": "main", "index": 0}
                ]]
            },
            "Get Video Stats": {
                "main": [[
                    {"node": "Combine Stats", "type": "main", "index": 0}
                ]]
            },
            "Combine Stats": {
                "main": [[
                    {"node": "Log to Scorecard", "type": "main", "index": 0},
                    {"node": "Notify Telegram", "type": "main", "index": 0}
                ]]
            }
        },
        "settings": {
            "executionOrder": "v1"
        },
    }

    return workflow


def deploy():
    """Deploy workflow to n8n."""
    if not N8N_API_KEY:
        print("ERROR: N8N_API_KEY not set in .env")
        sys.exit(1)

    headers = {
        "X-N8N-API-KEY": N8N_API_KEY,
        "Content-Type": "application/json",
    }

    workflow = build_workflow()

    # Check if workflow already exists
    print("Checking for existing YouTube Analytics workflow...")
    resp = requests.get(f"{N8N_BASE}/workflows", headers=headers)
    if resp.status_code == 200:
        existing = resp.json()
        for wf in existing.get("data", []):
            if wf.get("name") == "YouTube Analytics Collector":
                print(f"Found existing workflow ID {wf['id']}. Updating...")
                # Update existing
                resp = requests.put(
                    f"{N8N_BASE}/workflows/{wf['id']}",
                    headers=headers,
                    json=workflow
                )
                if resp.status_code == 200:
                    wf_id = wf['id']
                    print(f"Updated workflow {wf_id}")
                    # Activate
                    activate_resp = requests.post(
                        f"{N8N_BASE}/workflows/{wf_id}/activate",
                        headers=headers
                    )
                    if activate_resp.status_code == 200:
                        print(f"Activated workflow {wf_id}")
                    else:
                        print(f"Activation response: {activate_resp.status_code} {activate_resp.text}")
                    return wf_id
                else:
                    print(f"Update failed: {resp.status_code} {resp.text}")

    # Create new workflow
    print("Creating new workflow...")
    resp = requests.post(f"{N8N_BASE}/workflows", headers=headers, json=workflow)

    if resp.status_code in (200, 201):
        wf_data = resp.json()
        wf_id = wf_data.get("id")
        print(f"Created workflow: {wf_id}")

        # Activate
        activate_resp = requests.post(
            f"{N8N_BASE}/workflows/{wf_id}/activate",
            headers=headers
        )
        if activate_resp.status_code == 200:
            print(f"Activated workflow {wf_id}")
        else:
            print(f"Activation response: {activate_resp.status_code} {activate_resp.text}")

        print(f"\nWorkflow URL: https://n8n.marceausolutions.com/workflow/{wf_id}")
        return wf_id
    else:
        print(f"Create failed: {resp.status_code}")
        print(resp.text)
        sys.exit(1)


def main():
    print("=" * 60)
    print("  DEPLOY: YouTube Analytics Collector → n8n")
    print("=" * 60)

    if not YOUTUBE_API_KEY:
        print("\nWARNING: YOUTUBE_API_KEY not found in .env")
        print("The workflow will be created but API calls will fail until the key is added.")
        print("Add YOUTUBE_API_KEY to .env and update the workflow HTTP nodes.\n")

    wf_id = deploy()

    print("\nDone!")
    print(f"Schedule: Sunday 8pm ET (Monday 00:00 UTC)")
    print(f"Logs to: Scorecard Sheet > Content Calendar tab")
    print(f"Notifies: Telegram chat {TELEGRAM_CHAT_ID}")


if __name__ == "__main__":
    main()
