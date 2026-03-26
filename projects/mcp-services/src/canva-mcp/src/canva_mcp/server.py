#!/usr/bin/env python3
"""
Canva MCP Server

Model Context Protocol server for Canva Connect API.
Provides tools for design creation, asset management, templates, and exports.
"""

import os
import json
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .auth import CanvaAuth
from .client import CanvaClient, DesignType, ExportFormat, ExportQuality

# Initialize MCP server
mcp = Server("canva-mcp")

# Global client (initialized on first use)
_client: CanvaClient | None = None


def get_client() -> CanvaClient:
    """Get or initialize the Canva client."""
    global _client

    if _client is not None:
        return _client

    # Get credentials from environment
    client_id = os.environ.get("CANVA_CLIENT_ID")
    client_secret = os.environ.get("CANVA_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError(
            "Missing Canva credentials. Set CANVA_CLIENT_ID and CANVA_CLIENT_SECRET environment variables. "
            "Get credentials at https://www.canva.com/developers/apps"
        )

    # Token file location
    token_file = os.environ.get("CANVA_TOKEN_FILE", Path.home() / ".canva_tokens.json")

    auth = CanvaAuth(
        client_id=client_id,
        client_secret=client_secret,
        token_file=token_file,
    )

    # Check if we need to authenticate
    if not auth.is_token_valid() and not auth.refresh_token:
        # Need interactive auth - this will open browser
        auth.authenticate_interactive()

    _client = CanvaClient(auth)
    return _client


def format_result(data: Any) -> str:
    """Format API response for display."""
    if isinstance(data, dict):
        return json.dumps(data, indent=2)
    return str(data)


# ========== User Tools ==========

@mcp.tool()
async def canva_get_profile() -> str:
    """
    Get the current user's Canva profile information.

    Returns user ID, display name, and team info.
    """
    client = get_client()
    result = client.get_user_profile()
    return format_result(result)


# ========== Design Tools ==========

@mcp.tool()
async def canva_list_designs(
    query: str | None = None,
    continuation: str | None = None,
) -> str:
    """
    List user's Canva designs.

    Args:
        query: Optional search query to filter designs
        continuation: Pagination token for next page

    Returns list of designs with IDs, titles, and thumbnails.
    """
    client = get_client()
    result = client.list_designs(query=query, continuation=continuation)
    return format_result(result)


@mcp.tool()
async def canva_get_design(design_id: str) -> str:
    """
    Get details of a specific design.

    Args:
        design_id: The Canva design ID

    Returns design metadata including title, dimensions, and page count.
    """
    client = get_client()
    result = client.get_design(design_id)
    return format_result(result)


@mcp.tool()
async def canva_create_design(
    design_type: str,
    title: str | None = None,
    asset_id: str | None = None,
    width: int | None = None,
    height: int | None = None,
) -> str:
    """
    Create a new Canva design.

    Args:
        design_type: Type of design. Options: presentation, doc, whiteboard,
                    instagram_post, instagram_story, facebook_post,
                    youtube_thumbnail, poster, flyer, business_card, logo,
                    a4_document, us_letter
        title: Optional title for the design
        asset_id: Optional asset ID to use as background
        width: Custom width in pixels (for some types)
        height: Custom height in pixels (for some types)

    Returns the created design with its ID.
    """
    client = get_client()
    result = client.create_design(
        design_type=design_type,
        title=title,
        asset_id=asset_id,
        width=width,
        height=height,
    )
    return format_result(result)


@mcp.tool()
async def canva_delete_design(design_id: str) -> str:
    """
    Delete a Canva design.

    Args:
        design_id: The design ID to delete

    Returns confirmation of deletion.
    """
    client = get_client()
    result = client.delete_design(design_id)
    return f"Design {design_id} deleted successfully"


# ========== Asset Tools ==========

@mcp.tool()
async def canva_upload_asset(
    file_url: str | None = None,
    file_path: str | None = None,
    name: str | None = None,
) -> str:
    """
    Upload an asset (image, video, audio) to Canva.

    Args:
        file_url: URL of file to import (e.g., https://example.com/image.png)
        file_path: Local file path to upload
        name: Optional name for the asset

    Provide either file_url OR file_path, not both.
    Returns the uploaded asset with its ID.
    """
    client = get_client()
    result = client.upload_asset(
        file_url=file_url,
        file_path=file_path,
        name=name,
    )
    return format_result(result)


@mcp.tool()
async def canva_list_assets(
    folder_id: str | None = None,
    continuation: str | None = None,
) -> str:
    """
    List assets in the user's media library.

    Args:
        folder_id: Optional folder ID to list assets from
        continuation: Pagination token for next page

    Returns list of assets with IDs, names, and types.
    """
    client = get_client()
    result = client.list_assets(folder_id=folder_id, continuation=continuation)
    return format_result(result)


@mcp.tool()
async def canva_get_asset(asset_id: str) -> str:
    """
    Get details of a specific asset.

    Args:
        asset_id: The Canva asset ID

    Returns asset metadata including name, type, and dimensions.
    """
    client = get_client()
    result = client.get_asset(asset_id)
    return format_result(result)


@mcp.tool()
async def canva_delete_asset(asset_id: str) -> str:
    """
    Delete an asset from the media library.

    Args:
        asset_id: The asset ID to delete

    Returns confirmation of deletion.
    """
    client = get_client()
    result = client.delete_asset(asset_id)
    return f"Asset {asset_id} deleted successfully"


# ========== Folder Tools ==========

@mcp.tool()
async def canva_list_folders(
    parent_folder_id: str | None = None,
    continuation: str | None = None,
) -> str:
    """
    List folders in Canva.

    Args:
        parent_folder_id: Optional parent folder ID
        continuation: Pagination token for next page

    Returns list of folders with IDs and names.
    """
    client = get_client()
    result = client.list_folders(
        parent_folder_id=parent_folder_id,
        continuation=continuation
    )
    return format_result(result)


@mcp.tool()
async def canva_create_folder(
    name: str,
    parent_folder_id: str | None = None,
) -> str:
    """
    Create a new folder.

    Args:
        name: Folder name
        parent_folder_id: Optional parent folder ID

    Returns the created folder with its ID.
    """
    client = get_client()
    result = client.create_folder(name=name, parent_folder_id=parent_folder_id)
    return format_result(result)


@mcp.tool()
async def canva_delete_folder(folder_id: str) -> str:
    """
    Delete a folder.

    Args:
        folder_id: The folder ID to delete

    Returns confirmation of deletion.
    """
    client = get_client()
    result = client.delete_folder(folder_id)
    return f"Folder {folder_id} deleted successfully"


# ========== Brand Template Tools ==========

@mcp.tool()
async def canva_list_brand_templates(
    query: str | None = None,
    continuation: str | None = None,
) -> str:
    """
    List brand templates available to the user.

    Brand templates can be used with autofill to generate personalized designs.

    Args:
        query: Optional search query
        continuation: Pagination token for next page

    Returns list of templates with IDs, names, and thumbnails.
    """
    client = get_client()
    result = client.list_brand_templates(query=query, continuation=continuation)
    return format_result(result)


@mcp.tool()
async def canva_get_brand_template(template_id: str) -> str:
    """
    Get details of a brand template.

    Args:
        template_id: The brand template ID

    Returns template metadata.
    """
    client = get_client()
    result = client.get_brand_template(template_id)
    return format_result(result)


@mcp.tool()
async def canva_get_template_dataset(template_id: str) -> str:
    """
    Get the autofill dataset schema for a brand template.

    This shows what fields can be populated when using autofill.
    Use this to understand what data is needed for canva_autofill_template.

    Args:
        template_id: The brand template ID

    Returns the dataset schema with field names and types.
    """
    client = get_client()
    result = client.get_template_dataset(template_id)
    return format_result(result)


# ========== Autofill Tools ==========

@mcp.tool()
async def canva_autofill_template(
    template_id: str,
    data: str,
    title: str | None = None,
) -> str:
    """
    Create a design by autofilling a brand template with data.

    Perfect for generating personalized graphics for cold outreach,
    client mockups, or batch content creation.

    Args:
        template_id: Brand template ID
        data: JSON string mapping template fields to values.
              Example: {"headline": "Welcome John!", "image": "asset:abc123"}
              Use canva_get_template_dataset to see available fields.
        title: Optional title for the generated design

    Returns the generated design with its ID and edit URL.
    """
    client = get_client()

    # Parse data JSON
    try:
        data_dict = json.loads(data)
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON in data parameter: {e}"

    job = client.create_autofill_job(
        template_id=template_id,
        data=data_dict,
        title=title,
    )

    # Wait for completion
    job_id = job.get("job", {}).get("id")
    if not job_id:
        return f"Error: Failed to create autofill job: {format_result(job)}"

    result = client.wait_for_autofill(job_id)
    return format_result(result)


# ========== Export Tools ==========

@mcp.tool()
async def canva_export_design(
    design_id: str,
    format: str = "pdf",
    quality: str = "regular",
    pages: str | None = None,
) -> str:
    """
    Export a Canva design to a downloadable file.

    Args:
        design_id: The design ID to export
        format: Export format: pdf, png, jpg, gif, mp4, pptx (default: pdf)
        quality: Export quality: regular, high (default: regular)
        pages: Optional comma-separated page indices (0-indexed), e.g., "0,1,2"

    Returns download URLs for the exported file(s).
    """
    client = get_client()

    # Parse pages if provided
    page_list = None
    if pages:
        try:
            page_list = [int(p.strip()) for p in pages.split(",")]
        except ValueError:
            return f"Error: Invalid pages format. Use comma-separated integers like '0,1,2'"

    result = client.export_design(
        design_id=design_id,
        format=format,
        quality=quality,
        pages=page_list,
    )
    return format_result(result)


@mcp.tool()
async def canva_download_export(
    export_url: str,
    output_path: str,
) -> str:
    """
    Download an exported design file to local disk.

    Args:
        export_url: The URL from canva_export_design result
        output_path: Local file path to save to (e.g., /tmp/design.pdf)

    Returns the saved file path.
    """
    client = get_client()
    result = client.download_export(export_url, output_path)
    return f"Downloaded to: {result}"


# ========== Comment Tools ==========

@mcp.tool()
async def canva_list_comments(
    design_id: str,
    continuation: str | None = None,
) -> str:
    """
    List comments on a design.

    Args:
        design_id: The design ID
        continuation: Pagination token for next page

    Returns list of comments with authors and content.
    """
    client = get_client()
    result = client.list_comments(design_id=design_id, continuation=continuation)
    return format_result(result)


@mcp.tool()
async def canva_add_comment(
    design_id: str,
    message: str,
    thread_id: str | None = None,
) -> str:
    """
    Add a comment to a design.

    Args:
        design_id: The design ID
        message: Comment text
        thread_id: Optional thread ID to reply to existing comment

    Returns the created comment.
    """
    client = get_client()
    result = client.create_comment(
        design_id=design_id,
        message=message,
        thread_id=thread_id,
    )
    return format_result(result)


# ========== Auth Tool ==========

@mcp.tool()
async def canva_authenticate() -> str:
    """
    Authenticate with Canva (opens browser for OAuth).

    Use this if you need to re-authenticate or get fresh tokens.
    This will open a browser window for Canva login.

    Returns confirmation of successful authentication.
    """
    global _client

    # Force re-authentication
    client_id = os.environ.get("CANVA_CLIENT_ID")
    client_secret = os.environ.get("CANVA_CLIENT_SECRET")

    if not client_id or not client_secret:
        return (
            "Error: Missing CANVA_CLIENT_ID and CANVA_CLIENT_SECRET environment variables. "
            "Get credentials at https://www.canva.com/developers/apps"
        )

    token_file = os.environ.get("CANVA_TOKEN_FILE", Path.home() / ".canva_tokens.json")

    auth = CanvaAuth(
        client_id=client_id,
        client_secret=client_secret,
        token_file=token_file,
    )

    auth.authenticate_interactive()
    _client = CanvaClient(auth)

    return "Authentication successful! Tokens saved to ~/.canva_tokens.json"


def main():
    """Run the MCP server."""
    import asyncio
    asyncio.run(stdio_server(mcp).run())


if __name__ == "__main__":
    main()
