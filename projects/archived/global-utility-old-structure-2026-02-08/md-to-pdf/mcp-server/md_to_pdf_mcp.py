#!/usr/bin/env python3
"""
Markdown to PDF MCP Server

MCP (Model Context Protocol) server that provides markdown to PDF conversion
with interactive table of contents and professional styling.

Registry: io.github.williammarceaujr/md-to-pdf
"""

import asyncio
import base64
import json
import logging
import os
import sys
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# Add parent src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
    )
except ImportError:
    print("Error: MCP SDK not installed. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

try:
    from md_to_pdf import generate_pdf, extract_headers, generate_toc, DEFAULT_CSS
except ImportError as e:
    print(f"Error importing md_to_pdf module: {e}", file=sys.stderr)
    sys.exit(1)


# Server instance
server = Server("md-to-pdf")


@server.list_tools()
async def list_tools():
    """List available tools."""
    return [
        Tool(
            name="convert_markdown_to_pdf",
            description="""Convert markdown content to a professional PDF document.

Features:
- Automatic table of contents with clickable links
- Professional styling with customizable CSS
- Support for tables, code blocks, blockquotes
- Syntax highlighting for code
- Page breaks and proper pagination

Returns the PDF as base64-encoded data.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "markdown_content": {
                        "type": "string",
                        "description": "The markdown content to convert to PDF"
                    },
                    "include_toc": {
                        "type": "boolean",
                        "description": "Whether to include a table of contents (default: true)",
                        "default": True
                    },
                    "custom_css": {
                        "type": "string",
                        "description": "Optional custom CSS to override default styling"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Suggested filename for the PDF (default: document.pdf)",
                        "default": "document.pdf"
                    }
                },
                "required": ["markdown_content"]
            }
        ),
        Tool(
            name="extract_toc",
            description="""Extract table of contents structure from markdown content.

Returns a list of headers with their levels, text, and anchor IDs.
Useful for previewing document structure before conversion.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "markdown_content": {
                        "type": "string",
                        "description": "The markdown content to extract headers from"
                    }
                },
                "required": ["markdown_content"]
            }
        ),
        Tool(
            name="get_default_styles",
            description="""Get the default CSS styles used for PDF generation.

Returns the CSS that controls:
- Page layout and margins
- Typography and fonts
- Table styling
- Code block appearance
- Table of contents formatting

Use this to understand or customize the styling.""",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""

    if name == "convert_markdown_to_pdf":
        return await handle_convert(arguments)

    elif name == "extract_toc":
        return await handle_extract_toc(arguments)

    elif name == "get_default_styles":
        return await handle_get_styles(arguments)

    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]


async def handle_convert(arguments: dict):
    """Handle markdown to PDF conversion."""
    markdown_content = arguments.get("markdown_content", "")
    include_toc = arguments.get("include_toc", True)
    custom_css = arguments.get("custom_css")
    filename = arguments.get("filename", "document.pdf")

    if not markdown_content:
        return [TextContent(
            type="text",
            text="Error: markdown_content is required"
        )]

    # Set library path for WeasyPrint dependencies (macOS)
    if sys.platform == "darwin":
        os.environ["DYLD_LIBRARY_PATH"] = f"/opt/homebrew/lib:{os.environ.get('DYLD_LIBRARY_PATH', '')}"

    # Create temporary file for PDF output
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_path = tmp_file.name

    try:
        # Generate PDF
        css_content = custom_css if custom_css else None
        success = generate_pdf(
            markdown_content,
            tmp_path,
            css_content=css_content,
            include_toc=include_toc
        )

        if not success:
            return [TextContent(
                type="text",
                text="Error: Failed to generate PDF"
            )]

        # Read PDF and encode as base64
        with open(tmp_path, "rb") as f:
            pdf_data = base64.b64encode(f.read()).decode("utf-8")

        # Get file size
        file_size = os.path.getsize(tmp_path)

        # Extract TOC for summary
        headers = extract_headers(markdown_content)

        return [TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "filename": filename,
                "size_bytes": file_size,
                "toc_entries": len(headers),
                "include_toc": include_toc,
                "pdf_base64": pdf_data
            }, indent=2)
        )]

    except Exception as e:
        logger.error("Error generating PDF: %s", e, exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error generating PDF: {str(e)}"
        )]

    finally:
        # Cleanup temp file
        try:
            os.unlink(tmp_path)
        except OSError as e:
            logger.debug("Failed to clean up temp file %s: %s", tmp_path, e)


async def handle_extract_toc(arguments: dict):
    """Handle TOC extraction."""
    markdown_content = arguments.get("markdown_content", "")

    if not markdown_content:
        return [TextContent(
            type="text",
            text="Error: markdown_content is required"
        )]

    headers = extract_headers(markdown_content)

    return [TextContent(
        type="text",
        text=json.dumps({
            "total_headers": len(headers),
            "headers": headers
        }, indent=2)
    )]


async def handle_get_styles(arguments: dict):
    """Return default CSS styles."""
    return [TextContent(
        type="text",
        text=json.dumps({
            "description": "Default CSS styles for PDF generation",
            "css": DEFAULT_CSS
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
