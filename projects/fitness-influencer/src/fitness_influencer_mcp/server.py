#!/usr/bin/env python3
"""
Fitness Influencer Operations MCP Server

MCP (Model Context Protocol) server that provides fitness content creator tools
including video editing, AI image generation, analytics, and content planning.

Registry: io.github.williammarceaujr/fitness-influencer
"""

import asyncio
import json
import os
import sys
from pathlib import Path

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
    )
except ImportError:
    print("Error: MCP SDK not installed. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Server instance
server = Server("fitness-influencer")


@server.list_tools()
async def list_tools():
    """List available tools."""
    return [
        # Video Operations
        Tool(
            name="create_jump_cut_video",
            description="""Automatically remove silence from videos using FFmpeg silence detection.

Creates professional jump cuts to maintain viewer engagement.
Typical time savings: 10-15 minute raw video → 8 minute edited.

Cost: FREE (uses FFmpeg locally)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_video_path": {
                        "type": "string",
                        "description": "Path to input video file (MP4/MOV/AVI)"
                    },
                    "output_video_path": {
                        "type": "string",
                        "description": "Path for output edited video"
                    },
                    "silence_threshold": {
                        "type": "number",
                        "description": "Silence threshold in dB (default: -40)",
                        "default": -40
                    },
                    "min_silence_duration": {
                        "type": "number",
                        "description": "Minimum silence duration to cut (seconds)",
                        "default": 0.3
                    },
                    "generate_thumbnail": {
                        "type": "boolean",
                        "description": "Generate thumbnail from best frame",
                        "default": False
                    }
                },
                "required": ["input_video_path"]
            }
        ),
        Tool(
            name="add_video_branding",
            description="""Add branded intro and outro to videos.

Professional polish for consistent channel branding.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_path": {
                        "type": "string",
                        "description": "Path to video file"
                    },
                    "intro_path": {
                        "type": "string",
                        "description": "Path to intro video (optional)"
                    },
                    "outro_path": {
                        "type": "string",
                        "description": "Path to outro video (optional)"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Output video path"
                    }
                },
                "required": ["video_path", "output_path"]
            }
        ),

        # AI Content Generation
        Tool(
            name="generate_fitness_image",
            description="""Generate AI fitness images using Grok/xAI Aurora model.

Creates photorealistic fitness images from text prompts.
Great for thumbnails, social media, and marketing.

Cost: $0.07 per image""",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Text description of desired image"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of images to generate (1-10)",
                        "default": 1
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Path to save image(s) (optional, returns URLs if not specified)"
                    }
                },
                "required": ["prompt"]
            }
        ),

        # Content Planning
        Tool(
            name="generate_workout_plan",
            description="""Generate customized workout plans based on goals and experience.

Creates structured workout splits with exercises, sets, reps, and rest periods.
Export as markdown or JSON.

Cost: FREE""",
            inputSchema={
                "type": "object",
                "properties": {
                    "goal": {
                        "type": "string",
                        "description": "Fitness goal: muscle_gain, strength, endurance"
                    },
                    "experience": {
                        "type": "string",
                        "description": "Experience level: beginner, intermediate, advanced"
                    },
                    "days_per_week": {
                        "type": "integer",
                        "description": "Training days per week (3-6)",
                        "minimum": 3,
                        "maximum": 6
                    },
                    "equipment": {
                        "type": "string",
                        "description": "Equipment available: full_gym, home_gym, minimal"
                    }
                },
                "required": ["goal", "experience", "days_per_week", "equipment"]
            }
        ),

        # Analytics
        Tool(
            name="get_revenue_report",
            description="""Generate revenue and expense analytics from Google Sheets.

Tracks revenue by source (sponsorships, courses, affiliate) and expenses by category.
Calculates month-over-month growth and profit margins.

Requires: Google Sheets API credentials""",
            inputSchema={
                "type": "object",
                "properties": {
                    "sheet_id": {
                        "type": "string",
                        "description": "Google Sheets ID containing financial data"
                    },
                    "month": {
                        "type": "string",
                        "description": "Month to analyze (YYYY-MM format, defaults to current)"
                    }
                },
                "required": ["sheet_id"]
            }
        ),
        Tool(
            name="analyze_content_engagement",
            description="""Analyze content engagement metrics (placeholder for future integration).

Returns engagement analysis for fitness content.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "content_type": {
                        "type": "string",
                        "description": "Type of content: video, post, story"
                    },
                    "platform": {
                        "type": "string",
                        "description": "Platform: youtube, instagram, tiktok"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Days to analyze",
                        "default": 30
                    }
                }
            }
        ),

        # NEW v1.2.0 Tools - Comment Management & Content Planning
        Tool(
            name="categorize_comments",
            description="""Auto-categorize comments and DMs for efficient management.

Categories: FAQ, SPAM, COLLAB_REQUEST, FAN_MESSAGE, BRAND_INQUIRY, SUPPORT, NEGATIVE

Returns categorized comments with suggested actions and auto-reply templates.
Helps manage high-volume engagement at scale.

Cost: FREE""",
            inputSchema={
                "type": "object",
                "properties": {
                    "comments": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of comment/DM text strings to categorize"
                    },
                    "include_auto_replies": {
                        "type": "boolean",
                        "description": "Include suggested auto-reply templates",
                        "default": True
                    }
                },
                "required": ["comments"]
            }
        ),
        Tool(
            name="optimize_for_platforms",
            description="""Optimize content for multiple social media platforms.

Analyzes your content and generates platform-specific recommendations for:
- TikTok, Instagram (Feed, Reels, Stories), YouTube (Standard, Shorts)
- Twitter/X, Threads, LinkedIn

Returns: aspect ratios, caption lengths, hashtag counts, posting times, and platform tips.

Cost: FREE""",
            inputSchema={
                "type": "object",
                "properties": {
                    "content_type": {
                        "type": "string",
                        "description": "Type: video, image, or carousel"
                    },
                    "caption": {
                        "type": "string",
                        "description": "Original caption text"
                    },
                    "video_duration": {
                        "type": "integer",
                        "description": "Video duration in seconds (if applicable)"
                    },
                    "hashtags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of hashtags to use"
                    },
                    "platforms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Target platforms (defaults to all)"
                    }
                },
                "required": ["content_type", "caption"]
            }
        ),
        Tool(
            name="generate_content_calendar",
            description="""Generate a balanced content calendar to prevent burnout.

Creates a 30-day content plan with:
- Balanced effort distribution (low/medium/high effort posts)
- Platform variety
- Holiday-aware scheduling
- Rest day support
- Workload assessment and recommendations

Helps maintain consistent posting without burnout.

Cost: FREE""",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to plan (default: 30)",
                        "default": 30
                    },
                    "posts_per_day": {
                        "type": "integer",
                        "description": "Target posts per day (1-4)",
                        "default": 2
                    },
                    "platforms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Platforms to include (defaults to all major platforms)"
                    },
                    "content_focus": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Categories to focus on: workout, nutrition, motivation, lifestyle, education"
                    },
                    "rest_days": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Days of week to skip (e.g., ['Sunday'])"
                    }
                }
            }
        ),

        # Video Blueprint Generator
        Tool(
            name="generate_video_blueprint",
            description="""Generate viral video templates with segment-by-segment scripts.

Creates structured video blueprints with:
- Hook, talking head, B-roll, CTA segments
- Script suggestions for each segment
- Visual hints for what to film
- Platform-optimized timing
- Hashtag recommendations

Styles: educational, transformation, day_in_life, before_after, workout_demo
Platforms: tiktok, instagram_reels, youtube_shorts, youtube

Returns interactive timeline HTML for visualization.

Cost: FREE (uses local templates or Claude API if available)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Video topic (e.g., '5 best exercises for abs')"
                    },
                    "style": {
                        "type": "string",
                        "enum": ["educational", "transformation", "day_in_life", "before_after", "workout_demo"],
                        "description": "Template style",
                        "default": "educational"
                    },
                    "duration": {
                        "type": "integer",
                        "description": "Target duration in seconds (30-180)",
                        "minimum": 30,
                        "maximum": 180,
                        "default": 60
                    },
                    "platform": {
                        "type": "string",
                        "enum": ["tiktok", "instagram_reels", "youtube_shorts", "youtube"],
                        "description": "Target platform",
                        "default": "instagram_reels"
                    },
                    "output_html": {
                        "type": "string",
                        "description": "Path to save interactive HTML visualization (optional)"
                    }
                },
                "required": ["topic"]
            }
        ),

        # COGS Tracking
        Tool(
            name="get_cogs_report",
            description="""Get Cost of Goods Sold (COGS) report for AI API usage.

Tracks API costs and calculates gross margins for:
- AI Image Generation (Grok): $0.07/image
- Video Generation (Shotstack): $0.06/video
- Video Ads (Bundle): $0.20/ad

Returns costs, revenue, gross margins, and alerts.
Target margin: 60%+

Cost: FREE (internal tracking)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["daily", "monthly"],
                        "description": "Report period",
                        "default": "daily"
                    },
                    "generate_dashboard": {
                        "type": "boolean",
                        "description": "Generate HTML dashboard file",
                        "default": False
                    }
                }
            }
        ),
        Tool(
            name="log_api_usage",
            description="""Log an API usage transaction for COGS tracking.

Services:
- grok_image: AI image generation ($0.07 cost, $0.25 revenue)
- shotstack_video: Video generation ($0.06 cost, $0.35 revenue)
- video_ad: Complete video ad ($0.20 cost, $1.00 revenue)
- claude_api: Claude API call ($0.002 cost, included in subscription)

Use this to track pay-per-use API consumption.

Cost: FREE (internal tracking)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "enum": ["grok_image", "shotstack_video", "video_ad", "claude_api"],
                        "description": "Service type"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Number of items (e.g., number of images)",
                        "default": 1
                    }
                },
                "required": ["service", "user_id"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""

    try:
        if name == "create_jump_cut_video":
            return await handle_jump_cut(arguments)

        elif name == "add_video_branding":
            return await handle_video_branding(arguments)

        elif name == "generate_fitness_image":
            return await handle_image_generation(arguments)

        elif name == "generate_workout_plan":
            return await handle_workout_plan(arguments)

        elif name == "get_revenue_report":
            return await handle_revenue_report(arguments)

        elif name == "analyze_content_engagement":
            return await handle_engagement_analysis(arguments)

        elif name == "categorize_comments":
            return await handle_categorize_comments(arguments)

        elif name == "optimize_for_platforms":
            return await handle_optimize_platforms(arguments)

        elif name == "generate_content_calendar":
            return await handle_content_calendar(arguments)

        elif name == "generate_video_blueprint":
            return await handle_video_blueprint(arguments)

        elif name == "get_cogs_report":
            return await handle_cogs_report(arguments)

        elif name == "log_api_usage":
            return await handle_log_api_usage(arguments)

        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name,
                "hint": "Check that required dependencies and API keys are configured"
            }, indent=2)
        )]


async def handle_jump_cut(arguments: dict):
    """Handle video jump cut processing."""
    try:
        from .video_jumpcut import VideoJumpCutter
    except ImportError as e:
        return [TextContent(
            type="text",
            text=f"Error: Could not import video_jumpcut module: {e}"
        )]

    input_path = arguments.get("input_video_path")
    if not input_path:
        return [TextContent(type="text", text="Error: input_video_path is required")]

    if not os.path.exists(input_path):
        return [TextContent(type="text", text=f"Error: Input file not found: {input_path}")]

    # Determine output path
    output_path = arguments.get("output_video_path")
    if not output_path:
        input_p = Path(input_path)
        output_path = str(input_p.parent / f"{input_p.stem}_edited{input_p.suffix}")

    editor = VideoJumpCutter(
        silence_thresh=arguments.get("silence_threshold", -40),
        min_silence_dur=arguments.get("min_silence_duration", 0.3)
    )

    # Run in executor to avoid blocking
    result = await asyncio.get_event_loop().run_in_executor(
        None,
        editor.apply_jump_cuts,
        input_path,
        output_path
    )

    if result:
        response = {
            "success": True,
            "output_path": result,
            "message": "Jump cuts applied successfully"
        }

        # Generate thumbnail if requested
        if arguments.get("generate_thumbnail"):
            thumb_path = str(Path(output_path).parent / f"{Path(output_path).stem}_thumbnail.jpg")
            editor.generate_thumbnail(result, thumb_path)
            response["thumbnail_path"] = thumb_path

        return [TextContent(type="text", text=json.dumps(response, indent=2))]
    else:
        return [TextContent(type="text", text="Error: Jump cut processing failed")]


async def handle_video_branding(arguments: dict):
    """Handle adding intro/outro to video."""
    try:
        from .video_jumpcut import VideoJumpCutter
    except ImportError as e:
        return [TextContent(
            type="text",
            text=f"Error: Could not import video_jumpcut module: {e}"
        )]

    video_path = arguments.get("video_path")
    output_path = arguments.get("output_path")

    if not video_path or not output_path:
        return [TextContent(type="text", text="Error: video_path and output_path are required")]

    editor = VideoJumpCutter()

    result = await asyncio.get_event_loop().run_in_executor(
        None,
        editor.add_intro_outro,
        video_path,
        output_path,
        arguments.get("intro_path"),
        arguments.get("outro_path")
    )

    return [TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "output_path": result,
            "message": "Branding added successfully"
        }, indent=2)
    )]


async def handle_image_generation(arguments: dict):
    """Handle AI image generation."""
    try:
        from .grok_image_gen import GrokImageGenerator
    except ImportError as e:
        return [TextContent(
            type="text",
            text=f"Error: Could not import grok_image_gen module: {e}"
        )]

    prompt = arguments.get("prompt")
    if not prompt:
        return [TextContent(type="text", text="Error: prompt is required")]

    generator = GrokImageGenerator()

    count = arguments.get("count", 1)
    output_path = arguments.get("output_path")

    results = await asyncio.get_event_loop().run_in_executor(
        None,
        generator.generate_image,
        prompt,
        count,
        output_path
    )

    if results:
        usage = generator.get_usage_summary()
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "images": results,
                "count": len(results),
                "cost": f"${usage['total_cost']:.2f}"
            }, indent=2)
        )]
    else:
        return [TextContent(type="text", text="Error: Image generation failed")]


async def handle_workout_plan(arguments: dict):
    """Handle workout plan generation."""
    try:
        from .workout_plan_generator import WorkoutPlanGenerator
    except ImportError as e:
        return [TextContent(
            type="text",
            text=f"Error: Could not import workout_plan_generator module: {e}"
        )]

    required = ["goal", "experience", "days_per_week", "equipment"]
    for field in required:
        if field not in arguments:
            return [TextContent(type="text", text=f"Error: {field} is required")]

    generator = WorkoutPlanGenerator()

    plan = generator.generate_plan(
        goal=arguments["goal"],
        experience=arguments["experience"],
        days_per_week=arguments["days_per_week"],
        equipment=arguments["equipment"]
    )

    # Export to files
    filename = f"workout_{arguments['goal']}_{arguments['experience']}"
    md_path = generator.export_markdown(plan, filename)
    json_path = generator.export_json(plan, filename)

    return [TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "plan": plan,
            "exports": {
                "markdown": str(md_path),
                "json": str(json_path)
            }
        }, indent=2, default=str)
    )]


async def handle_revenue_report(arguments: dict):
    """Handle revenue analytics."""
    try:
        from .revenue_analytics import RevenueAnalytics
    except ImportError as e:
        return [TextContent(
            type="text",
            text=f"Error: Could not import revenue_analytics module: {e}"
        )]

    sheet_id = arguments.get("sheet_id")
    if not sheet_id:
        return [TextContent(type="text", text="Error: sheet_id is required")]

    analytics = RevenueAnalytics(sheet_id=sheet_id)

    # Authenticate
    service = analytics.authenticate()
    if not service:
        return [TextContent(
            type="text",
            text="Error: Google Sheets authentication failed. Check credentials."
        )]

    month = arguments.get("month")
    report = analytics.generate_report(month_str=month)

    if report:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "report": report
            }, indent=2)
        )]
    else:
        return [TextContent(type="text", text="Error: Could not generate report")]


async def handle_engagement_analysis(arguments: dict):
    """Handle engagement analysis (placeholder)."""
    # This is a placeholder for future social media API integrations
    return [TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "message": "Engagement analysis placeholder",
            "note": "Full implementation requires YouTube/Instagram/TikTok API integration",
            "request": arguments
        }, indent=2)
    )]


async def handle_categorize_comments(arguments: dict):
    """Handle comment categorization."""
    try:
        from .comment_categorizer import CommentCategorizer
    except ImportError as e:
        return [TextContent(
            type="text",
            text=f"Error: Could not import comment_categorizer module: {e}"
        )]

    comments = arguments.get("comments")
    if not comments:
        return [TextContent(type="text", text="Error: comments array is required")]

    if not isinstance(comments, list):
        return [TextContent(type="text", text="Error: comments must be an array of strings")]

    categorizer = CommentCategorizer()
    include_replies = arguments.get("include_auto_replies", True)

    results = categorizer.categorize_batch(comments, include_auto_replies=include_replies)

    return [TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "total_comments": len(comments),
            "results": results
        }, indent=2)
    )]


async def handle_optimize_platforms(arguments: dict):
    """Handle cross-platform content optimization."""
    try:
        from .cross_platform_optimizer import CrossPlatformOptimizer
    except ImportError as e:
        return [TextContent(
            type="text",
            text=f"Error: Could not import cross_platform_optimizer module: {e}"
        )]

    content_type = arguments.get("content_type")
    caption = arguments.get("caption")

    if not content_type or not caption:
        return [TextContent(type="text", text="Error: content_type and caption are required")]

    optimizer = CrossPlatformOptimizer()

    results = optimizer.optimize_for_all_platforms(
        content_type=content_type,
        original_caption=caption,
        video_duration=arguments.get("video_duration"),
        hashtags=arguments.get("hashtags"),
        platforms=arguments.get("platforms")
    )

    return [TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "optimization": results
        }, indent=2)
    )]


async def handle_content_calendar(arguments: dict):
    """Handle content calendar generation."""
    try:
        from .content_calendar import ContentCalendarGenerator
    except ImportError as e:
        return [TextContent(
            type="text",
            text=f"Error: Could not import content_calendar module: {e}"
        )]

    generator = ContentCalendarGenerator()

    calendar = generator.generate_calendar(
        days=arguments.get("days", 30),
        posts_per_day=arguments.get("posts_per_day", 2),
        platforms=arguments.get("platforms"),
        content_focus=arguments.get("content_focus"),
        rest_days=arguments.get("rest_days")
    )

    return [TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "calendar": calendar
        }, indent=2)
    )]


async def handle_video_blueprint(arguments: dict):
    """Handle video blueprint generation."""
    # Import from parent src directory
    try:
        import sys
        from pathlib import Path
        parent_src = Path(__file__).parent.parent
        if str(parent_src) not in sys.path:
            sys.path.insert(0, str(parent_src))
        from video_template_framework import VideoTemplateGenerator, generate_timeline_html
    except ImportError as e:
        return [TextContent(
            type="text",
            text=f"Error: Could not import video_template_framework module: {e}"
        )]

    topic = arguments.get("topic")
    if not topic:
        return [TextContent(type="text", text="Error: topic is required")]

    generator = VideoTemplateGenerator()

    template = generator.generate_template(
        topic=topic,
        style=arguments.get("style", "educational"),
        target_duration=arguments.get("duration", 60),
        platform=arguments.get("platform", "instagram_reels")
    )

    # Generate HTML visualization
    html = generate_timeline_html(template)

    # Save HTML if output path specified
    output_html = arguments.get("output_html")
    if output_html:
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{template.get('name', 'Video Blueprint')}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="background:#0f0f1a; padding:40px; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
    {html}
</body>
</html>"""
        with open(output_html, "w") as f:
            f.write(full_html)
        template["html_saved_to"] = output_html

    return [TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "template": template,
            "html_preview": html[:500] + "..." if len(html) > 500 else html
        }, indent=2)
    )]


async def handle_cogs_report(arguments: dict):
    """Handle COGS report generation."""
    try:
        import sys
        from pathlib import Path
        parent_src = Path(__file__).parent.parent
        if str(parent_src) not in sys.path:
            sys.path.insert(0, str(parent_src))
        from cogs_tracker import COGSTracker
    except ImportError as e:
        return [TextContent(
            type="text",
            text=f"Error: Could not import cogs_tracker module: {e}"
        )]

    tracker = COGSTracker()

    period = arguments.get("period", "daily")

    if period == "daily":
        report = tracker.get_daily_report()
    else:
        report = tracker.get_monthly_report()

    result = {
        "success": True,
        "report": report
    }

    # Generate dashboard if requested
    if arguments.get("generate_dashboard", False):
        dashboard_path = tracker.export_html_dashboard()
        result["dashboard_path"] = dashboard_path

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def handle_log_api_usage(arguments: dict):
    """Handle logging API usage for COGS tracking."""
    try:
        import sys
        from pathlib import Path
        parent_src = Path(__file__).parent.parent
        if str(parent_src) not in sys.path:
            sys.path.insert(0, str(parent_src))
        from cogs_tracker import COGSTracker
    except ImportError as e:
        return [TextContent(
            type="text",
            text=f"Error: Could not import cogs_tracker module: {e}"
        )]

    service = arguments.get("service")
    user_id = arguments.get("user_id")

    if not service or not user_id:
        return [TextContent(type="text", text="Error: service and user_id are required")]

    tracker = COGSTracker()

    txn = tracker.log_transaction(
        service=service,
        user_id=user_id,
        quantity=arguments.get("quantity", 1)
    )

    return [TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "transaction": {
                "service": txn.service,
                "user_id": txn.user_id,
                "quantity": txn.quantity,
                "cost": round(txn.cost, 2),
                "revenue": round(txn.revenue, 2),
                "timestamp": txn.timestamp.isoformat()
            }
        }, indent=2)
    )]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
