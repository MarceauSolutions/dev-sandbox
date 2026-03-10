"""
youtube-creator-mcp: YouTube automation tools via MCP.

Tools:
- upload_video: Upload video to YouTube
- upload_short: Upload YouTube Short (vertical, <60s)
- update_metadata: Update title/description/tags
- get_analytics: Get video performance metrics
- get_channel_stats: Subscriber count, total views
- schedule_video: Schedule for future publish
- manage_playlists: Add/remove from playlists
- get_comments: Retrieve video comments
- reply_to_comment: Post reply to comment
"""

__version__ = "1.0.0"

from .server import server, main

__all__ = ["server", "main", "__version__"]
