"""
Instagram Creator MCP Server

Provides tools for Instagram content publishing via MCP protocol.
"""

import os
import json
import asyncio
from typing import Optional, Any
from dataclasses import asdict

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

from .instagram_api import InstagramAPI, MediaMetadata


# Initialize server
server = Server("instagram-creator-mcp")

# Lazy-loaded API client
_instagram_api: Optional[InstagramAPI] = None


def get_instagram_api() -> InstagramAPI:
    """Get or create Instagram API client."""
    global _instagram_api
    if _instagram_api is None:
        _instagram_api = InstagramAPI()
    return _instagram_api


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available Instagram tools."""
    return [
        Tool(
            name="post_image",
            description="Post an image to Instagram feed",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_url": {
                        "type": "string",
                        "description": "Public URL of the image to post"
                    },
                    "caption": {
                        "type": "string",
                        "description": "Post caption"
                    },
                    "hashtags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Hashtags to add (without # symbol)"
                    },
                    "location_id": {
                        "type": "string",
                        "description": "Optional Facebook Place ID for location tag"
                    }
                },
                "required": ["image_url", "caption"]
            }
        ),
        Tool(
            name="post_carousel",
            description="Post a carousel (2-10 images) to Instagram feed",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of public image URLs (2-10 images)"
                    },
                    "caption": {
                        "type": "string",
                        "description": "Post caption"
                    },
                    "hashtags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Hashtags to add"
                    }
                },
                "required": ["image_urls", "caption"]
            }
        ),
        Tool(
            name="post_reel",
            description="Post a video Reel to Instagram",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_url": {
                        "type": "string",
                        "description": "Public URL of the video"
                    },
                    "caption": {
                        "type": "string",
                        "description": "Reel caption"
                    },
                    "hashtags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Hashtags to add"
                    },
                    "cover_url": {
                        "type": "string",
                        "description": "Optional cover image URL"
                    },
                    "share_to_feed": {
                        "type": "boolean",
                        "description": "Also share to main feed",
                        "default": True
                    }
                },
                "required": ["video_url", "caption"]
            }
        ),
        Tool(
            name="post_story",
            description="Post an image or video to Instagram Stories",
            inputSchema={
                "type": "object",
                "properties": {
                    "media_url": {
                        "type": "string",
                        "description": "Public URL of image or video"
                    },
                    "media_type": {
                        "type": "string",
                        "enum": ["image", "video"],
                        "description": "Type of media",
                        "default": "image"
                    }
                },
                "required": ["media_url"]
            }
        ),
        Tool(
            name="get_post_insights",
            description="Get performance metrics for a post (impressions, reach, engagement)",
            inputSchema={
                "type": "object",
                "properties": {
                    "media_id": {
                        "type": "string",
                        "description": "Instagram media ID"
                    }
                },
                "required": ["media_id"]
            }
        ),
        Tool(
            name="get_account_stats",
            description="Get account statistics (followers, following, post count)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_recent_posts",
            description="Get recent posts from the account",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of posts to return",
                        "default": 25
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_comments",
            description="Get comments on a post",
            inputSchema={
                "type": "object",
                "properties": {
                    "media_id": {
                        "type": "string",
                        "description": "Instagram media ID"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum comments to return",
                        "default": 50
                    }
                },
                "required": ["media_id"]
            }
        ),
        Tool(
            name="reply_to_comment",
            description="Reply to a comment on a post",
            inputSchema={
                "type": "object",
                "properties": {
                    "comment_id": {
                        "type": "string",
                        "description": "Comment ID to reply to"
                    },
                    "message": {
                        "type": "string",
                        "description": "Reply message"
                    }
                },
                "required": ["comment_id", "message"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        api = get_instagram_api()

        if name == "post_image":
            metadata = MediaMetadata(
                caption=arguments['caption'],
                hashtags=arguments.get('hashtags'),
                location_id=arguments.get('location_id')
            )
            result = api.post_image(arguments['image_url'], metadata)

        elif name == "post_carousel":
            metadata = MediaMetadata(
                caption=arguments['caption'],
                hashtags=arguments.get('hashtags')
            )
            result = api.post_carousel(arguments['image_urls'], metadata)

        elif name == "post_reel":
            metadata = MediaMetadata(
                caption=arguments['caption'],
                hashtags=arguments.get('hashtags')
            )
            result = api.post_reel(
                video_url=arguments['video_url'],
                metadata=metadata,
                cover_url=arguments.get('cover_url'),
                share_to_feed=arguments.get('share_to_feed', True)
            )

        elif name == "post_story":
            result = api.post_story(
                media_url=arguments['media_url'],
                media_type=arguments.get('media_type', 'image')
            )

        elif name == "get_post_insights":
            insights = api.get_post_insights(arguments['media_id'])
            result = asdict(insights)

        elif name == "get_account_stats":
            result = api.get_account_stats()

        elif name == "get_recent_posts":
            result = {
                "posts": api.get_recent_media(arguments.get('limit', 25))
            }

        elif name == "get_comments":
            result = {
                "media_id": arguments['media_id'],
                "comments": api.get_comments(
                    arguments['media_id'],
                    arguments.get('limit', 50)
                )
            }

        elif name == "reply_to_comment":
            result = api.reply_to_comment(
                arguments['comment_id'],
                arguments['message']
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
