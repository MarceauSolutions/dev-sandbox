"""
fitness-influencer-mcp: Fitness content creator tools via MCP.

Version 1.2.0 adds:
- Comment Auto-Categorizer: Automatically categorize comments/DMs
- Cross-Platform Content Optimizer: Optimize content for each platform
- Content Calendar Generator: Generate balanced posting schedules
"""

__version__ = "1.2.0"

from .server import server, main
from .comment_categorizer import CommentCategorizer, categorize_comments
from .cross_platform_optimizer import CrossPlatformOptimizer, optimize_content
from .content_calendar import ContentCalendarGenerator, generate_content_calendar

__all__ = [
    "server",
    "main",
    "CommentCategorizer",
    "categorize_comments",
    "CrossPlatformOptimizer",
    "optimize_content",
    "ContentCalendarGenerator",
    "generate_content_calendar",
]
