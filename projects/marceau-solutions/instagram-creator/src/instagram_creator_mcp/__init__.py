"""
instagram-creator-mcp: Instagram automation tools via MCP.

Tools:
- post_image: Post image to feed
- post_carousel: Post multi-image carousel
- post_reel: Post video Reel
- post_story: Post to Stories
- get_insights: Get post performance metrics
- get_account_stats: Follower count, engagement rate
- get_comments: Get comments on a post
- reply_to_comment: Reply to a comment
- schedule_post: Schedule post for future
"""

__version__ = "1.0.0"

from .server import server, main

__all__ = ["server", "main", "__version__"]
