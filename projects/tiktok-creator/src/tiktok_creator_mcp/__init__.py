"""
tiktok-creator-mcp: TikTok automation tools via MCP.

Tools:
- post_video: Upload video to TikTok
- get_video_insights: Get video performance metrics
- get_account_stats: Follower count, video count
- get_comments: Get comments on a video
- reply_to_comment: Reply to a comment
"""

__version__ = "1.0.0"

from .server import server, main

__all__ = ["server", "main", "__version__"]
