"""
TikTok Creator MCP Server

Provides tools for TikTok video publishing via MCP protocol.
"""

import os
import json
import asyncio
from typing import Optional, Any
from dataclasses import asdict

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

from .tiktok_api import TikTokAPI, VideoMetadata


# Initialize server
server = Server("tiktok-creator-mcp")

# Lazy-loaded API client
_tiktok_api: Optional[TikTokAPI] = None


def get_tiktok_api() -> TikTokAPI:
    """Get or create TikTok API client."""
    global _tiktok_api
    if _tiktok_api is None:
        _tiktok_api = TikTokAPI()
    return _tiktok_api


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available TikTok tools."""
    return [
        Tool(
            name="post_video",
            description="Post a video to TikTok from a local file",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_path": {
                        "type": "string",
                        "description": "Path to video file"
                    },
                    "title": {
                        "type": "string",
                        "description": "Video title/caption (max 150 chars)"
                    },
                    "privacy": {
                        "type": "string",
                        "enum": ["SELF_ONLY", "MUTUAL_FOLLOW_FRIENDS", "FOLLOWER_OF_CREATOR", "PUBLIC_TO_EVERYONE"],
                        "description": "Privacy level",
                        "default": "PUBLIC_TO_EVERYONE"
                    },
                    "disable_duet": {
                        "type": "boolean",
                        "description": "Disable duets",
                        "default": False
                    },
                    "disable_stitch": {
                        "type": "boolean",
                        "description": "Disable stitch",
                        "default": False
                    },
                    "disable_comment": {
                        "type": "boolean",
                        "description": "Disable comments",
                        "default": False
                    }
                },
                "required": ["video_path", "title"]
            }
        ),
        Tool(
            name="post_video_from_url",
            description="Post a video to TikTok from a public URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_url": {
                        "type": "string",
                        "description": "Public URL of the video"
                    },
                    "title": {
                        "type": "string",
                        "description": "Video title/caption (max 150 chars)"
                    },
                    "privacy": {
                        "type": "string",
                        "enum": ["SELF_ONLY", "MUTUAL_FOLLOW_FRIENDS", "FOLLOWER_OF_CREATOR", "PUBLIC_TO_EVERYONE"],
                        "default": "PUBLIC_TO_EVERYONE"
                    },
                    "disable_duet": {
                        "type": "boolean",
                        "default": False
                    },
                    "disable_stitch": {
                        "type": "boolean",
                        "default": False
                    },
                    "disable_comment": {
                        "type": "boolean",
                        "default": False
                    }
                },
                "required": ["video_url", "title"]
            }
        ),
        Tool(
            name="get_video_stats",
            description="Get performance statistics for a video",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {
                        "type": "string",
                        "description": "TikTok video ID"
                    }
                },
                "required": ["video_id"]
            }
        ),
        Tool(
            name="get_account_stats",
            description="Get account statistics (followers, likes, video count)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_video_list",
            description="Get list of your TikTok videos",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_count": {
                        "type": "integer",
                        "description": "Maximum videos to return",
                        "default": 20
                    }
                },
                "required": []
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
                        "description": "TikTok video ID"
                    },
                    "max_count": {
                        "type": "integer",
                        "description": "Maximum comments to return",
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
                    "video_id": {
                        "type": "string",
                        "description": "Video ID the comment is on"
                    },
                    "comment_id": {
                        "type": "string",
                        "description": "Comment ID to reply to"
                    },
                    "text": {
                        "type": "string",
                        "description": "Reply text"
                    }
                },
                "required": ["video_id", "comment_id", "text"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        api = get_tiktok_api()

        if name == "post_video":
            metadata = VideoMetadata(
                title=arguments['title'],
                privacy_level=arguments.get('privacy', 'PUBLIC_TO_EVERYONE'),
                disable_duet=arguments.get('disable_duet', False),
                disable_stitch=arguments.get('disable_stitch', False),
                disable_comment=arguments.get('disable_comment', False),
            )
            result = api.post_video(arguments['video_path'], metadata)

        elif name == "post_video_from_url":
            metadata = VideoMetadata(
                title=arguments['title'],
                privacy_level=arguments.get('privacy', 'PUBLIC_TO_EVERYONE'),
                disable_duet=arguments.get('disable_duet', False),
                disable_stitch=arguments.get('disable_stitch', False),
                disable_comment=arguments.get('disable_comment', False),
            )
            result = api.post_video_from_url(arguments['video_url'], metadata)

        elif name == "get_video_stats":
            stats = api.get_video_stats(arguments['video_id'])
            result = asdict(stats)

        elif name == "get_account_stats":
            result = api.get_user_info()

        elif name == "get_video_list":
            result = {
                "videos": api.get_video_list(arguments.get('max_count', 20))
            }

        elif name == "get_comments":
            result = {
                "video_id": arguments['video_id'],
                "comments": api.get_comments(
                    arguments['video_id'],
                    arguments.get('max_count', 50)
                )
            }

        elif name == "reply_to_comment":
            result = api.reply_to_comment(
                arguments['video_id'],
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
