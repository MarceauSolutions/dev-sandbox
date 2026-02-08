"""
fitness-influencer-mcp: Fitness content creator tools via MCP.

Version 2.0.0 - Major Release (2026-02-07):
- Background Task Queue: Async job processing with Redis + RQ
- Word-Level Captions: 10 karaoke styles with smart line breaking
- Filler Word Removal: Context-aware detection and smooth removal
- Auto-Reframe: Aspect ratio conversion with face/body tracking
- Multi-Platform Export: Optimized encoding for 9 platforms
- Long-Form Video Analyzer: Segment scoring and scene detection
- Viral Moment Detection: Top clips with viral scoring
- Hook Analyzer: 6-component effectiveness breakdown
- Retention Predictor: Audience drop-off prediction with cliff detection
- Workout Timer Overlays: HIIT, Tabata, EMOM, AMRAP presets
- Form Annotations: Arrows, circles, text with slow-motion
- Exercise Recognition: 20+ exercises with rep counting and form analysis

Version 1.3.0 added:
- Video Blueprint Generator: Create viral video templates with segment-by-segment scripts

Version 1.2.0 added:
- Comment Auto-Categorizer: Automatically categorize comments/DMs
- Cross-Platform Content Optimizer: Optimize content for each platform
- Content Calendar Generator: Generate balanced posting schedules
"""

__version__ = "2.0.0"

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
