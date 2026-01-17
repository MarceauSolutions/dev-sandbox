"""
YouTube Creator MCP Server

Provides tools for YouTube video management via MCP protocol.
"""

import os
import json
import asyncio
from typing import Optional, Any
from dataclasses import asdict

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

from .youtube_api import YouTubeAPI, VideoMetadata, GOOGLE_API_AVAILABLE


# Initialize server
server = Server("youtube-creator-mcp")

# Lazy-loaded API client
_youtube_api: Optional[YouTubeAPI] = None


def get_youtube_api() -> YouTubeAPI:
    """Get or create YouTube API client."""
    global _youtube_api
    if _youtube_api is None:
        _youtube_api = YouTubeAPI()
    return _youtube_api


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available YouTube tools."""
    return [
        Tool(
            name="upload_video",
            description="Upload a video to YouTube with title, description, and tags",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_path": {
                        "type": "string",
                        "description": "Path to the video file"
                    },
                    "title": {
                        "type": "string",
                        "description": "Video title (max 100 chars)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Video description"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Video tags for searchability"
                    },
                    "privacy": {
                        "type": "string",
                        "enum": ["private", "unlisted", "public"],
                        "description": "Video privacy setting",
                        "default": "private"
                    },
                    "category": {
                        "type": "string",
                        "description": "Video category (e.g., 'education', 'howto_style', 'entertainment')",
                        "default": "people_blogs"
                    },
                    "thumbnail_path": {
                        "type": "string",
                        "description": "Optional path to custom thumbnail image"
                    },
                    "playlist_id": {
                        "type": "string",
                        "description": "Optional playlist ID to add video to"
                    }
                },
                "required": ["video_path", "title", "description", "tags"]
            }
        ),
        Tool(
            name="upload_short",
            description="Upload a YouTube Short (vertical video under 60 seconds)",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_path": {
                        "type": "string",
                        "description": "Path to vertical video file (<60s)"
                    },
                    "title": {
                        "type": "string",
                        "description": "Short title (will auto-add #Shorts)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Short description"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for discoverability"
                    },
                    "privacy": {
                        "type": "string",
                        "enum": ["private", "unlisted", "public"],
                        "default": "private"
                    }
                },
                "required": ["video_path", "title", "description", "tags"]
            }
        ),
        Tool(
            name="update_video_metadata",
            description="Update title, description, or tags of an existing video",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {
                        "type": "string",
                        "description": "YouTube video ID"
                    },
                    "title": {
                        "type": "string",
                        "description": "New title (optional)"
                    },
                    "description": {
                        "type": "string",
                        "description": "New description (optional)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New tags (optional)"
                    },
                    "privacy": {
                        "type": "string",
                        "enum": ["private", "unlisted", "public"],
                        "description": "New privacy setting (optional)"
                    }
                },
                "required": ["video_id"]
            }
        ),
        Tool(
            name="get_video_analytics",
            description="Get performance metrics for a video (views, likes, watch time)",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {
                        "type": "string",
                        "description": "YouTube video ID"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD), defaults to 30 days ago"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD), defaults to today"
                    }
                },
                "required": ["video_id"]
            }
        ),
        Tool(
            name="get_channel_stats",
            description="Get channel statistics (subscribers, total views, video count)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="schedule_video",
            description="Upload and schedule a video for future publication",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_path": {
                        "type": "string",
                        "description": "Path to video file"
                    },
                    "title": {
                        "type": "string",
                        "description": "Video title"
                    },
                    "description": {
                        "type": "string",
                        "description": "Video description"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "publish_at": {
                        "type": "string",
                        "description": "ISO 8601 datetime for scheduled publish (e.g., 2026-01-20T14:00:00Z)"
                    },
                    "thumbnail_path": {
                        "type": "string",
                        "description": "Optional thumbnail image path"
                    }
                },
                "required": ["video_path", "title", "description", "tags", "publish_at"]
            }
        ),
        Tool(
            name="add_to_playlist",
            description="Add a video to a playlist",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {
                        "type": "string",
                        "description": "YouTube video ID"
                    },
                    "playlist_id": {
                        "type": "string",
                        "description": "Playlist ID to add video to"
                    }
                },
                "required": ["video_id", "playlist_id"]
            }
        ),
        Tool(
            name="list_playlists",
            description="List all playlists on the channel",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="create_playlist",
            description="Create a new playlist",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Playlist title"
                    },
                    "description": {
                        "type": "string",
                        "description": "Playlist description"
                    },
                    "privacy": {
                        "type": "string",
                        "enum": ["private", "unlisted", "public"],
                        "default": "private"
                    }
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="get_comments",
            description="Get comments on a video",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {
                        "type": "string",
                        "description": "YouTube video ID"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum comments to return (max 100)",
                        "default": 50
                    }
                },
                "required": ["video_id"]
            }
        ),
        Tool(
            name="reply_to_comment",
            description="Reply to a comment on a video",
            inputSchema={
                "type": "object",
                "properties": {
                    "comment_id": {
                        "type": "string",
                        "description": "Comment ID to reply to"
                    },
                    "text": {
                        "type": "string",
                        "description": "Reply text"
                    }
                },
                "required": ["comment_id", "text"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""

    if not GOOGLE_API_AVAILABLE:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": "Google API libraries not installed",
                "fix": "pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            })
        )]

    try:
        api = get_youtube_api()

        if name == "upload_video":
            category_id = YouTubeAPI.CATEGORIES.get(
                arguments.get('category', 'people_blogs'),
                "22"
            )
            metadata = VideoMetadata(
                title=arguments['title'],
                description=arguments['description'],
                tags=arguments['tags'],
                category_id=category_id,
                privacy_status=arguments.get('privacy', 'private'),
                thumbnail_path=arguments.get('thumbnail_path'),
                playlist_id=arguments.get('playlist_id'),
            )
            result = api.upload_video(arguments['video_path'], metadata)

        elif name == "upload_short":
            metadata = VideoMetadata(
                title=arguments['title'],
                description=arguments['description'],
                tags=arguments['tags'],
                privacy_status=arguments.get('privacy', 'private'),
            )
            result = api.upload_short(arguments['video_path'], metadata)

        elif name == "update_video_metadata":
            result = api.update_metadata(
                video_id=arguments['video_id'],
                title=arguments.get('title'),
                description=arguments.get('description'),
                tags=arguments.get('tags'),
                privacy_status=arguments.get('privacy')
            )

        elif name == "get_video_analytics":
            stats = api.get_video_analytics(
                video_id=arguments['video_id'],
                start_date=arguments.get('start_date'),
                end_date=arguments.get('end_date')
            )
            result = asdict(stats)

        elif name == "get_channel_stats":
            result = api.get_channel_stats()

        elif name == "schedule_video":
            metadata = VideoMetadata(
                title=arguments['title'],
                description=arguments['description'],
                tags=arguments['tags'],
                privacy_status='private',
                scheduled_publish_time=arguments['publish_at'],
                thumbnail_path=arguments.get('thumbnail_path'),
            )
            result = api.upload_video(arguments['video_path'], metadata)
            result['scheduled_for'] = arguments['publish_at']

        elif name == "add_to_playlist":
            result = api.add_to_playlist(
                arguments['video_id'],
                arguments['playlist_id']
            )

        elif name == "list_playlists":
            result = {"playlists": api.list_playlists()}

        elif name == "create_playlist":
            result = api.create_playlist(
                title=arguments['title'],
                description=arguments.get('description', ''),
                privacy_status=arguments.get('privacy', 'private')
            )

        elif name == "get_comments":
            result = {
                "video_id": arguments['video_id'],
                "comments": api.get_comments(
                    arguments['video_id'],
                    arguments.get('max_results', 50)
                )
            }

        elif name == "reply_to_comment":
            result = api.reply_to_comment(
                arguments['comment_id'],
                arguments['text']
            )

        else:
            result = {"error": f"Unknown tool: {name}"}

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e), "tool": name})
        )]


async def run_server():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def main():
    """Entry point."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
