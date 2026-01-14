#!/usr/bin/env python3
"""
Fitness Influencer Operations MCP Server

MCP (Model Context Protocol) server that provides fitness content creator tools
including video editing, AI image generation, analytics, and content planning.

Registry: io.github.williammarceaujr/fitness-influencer
"""

import asyncio
import base64
import json
import os
import sys
from pathlib import Path

# Add parent src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

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
        from video_jumpcut import VideoJumpCutter
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
        from video_jumpcut import VideoJumpCutter
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
        from grok_image_gen import GrokImageGenerator
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
        from workout_plan_generator import WorkoutPlanGenerator
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
        from revenue_analytics import RevenueAnalytics
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
