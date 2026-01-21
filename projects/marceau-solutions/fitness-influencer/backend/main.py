#!/usr/bin/env python3
"""
Fitness Assistant API Wrapper
FastAPI server to expose fitness influencer tools as REST endpoints.

This allows your Replit app to interact with the assistant via HTTP requests.

Usage:
    pip install fastapi uvicorn python-multipart
    python execution/fitness_assistant_api.py

    # Or with uvicorn:
    uvicorn execution.fitness_assistant_api:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
import subprocess
import os
from pathlib import Path
import tempfile
import shutil
import uuid
import time

app = FastAPI(
    title="Fitness Influencer Assistant API",
    description="AI-powered fitness content creation and automation",
    version="1.0.0"
)

# Enable CORS for Replit app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Replit app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base path for execution scripts
SCRIPTS_PATH = Path(__file__).parent

# Create static directory for processed videos
STATIC_PATH = SCRIPTS_PATH / "static"
VIDEOS_PATH = STATIC_PATH / "videos"
VIDEOS_PATH.mkdir(parents=True, exist_ok=True)

# Mount static files for video downloads
app.mount("/static", StaticFiles(directory=str(STATIC_PATH)), name="static")


# ============================================================================
# Request/Response Models
# ============================================================================

class VideoEditRequest(BaseModel):
    """Request model for video editing."""
    silence_threshold: Optional[float] = -40
    min_silence_duration: Optional[float] = 0.3
    generate_thumbnail: Optional[bool] = True


class EducationalGraphicRequest(BaseModel):
    """Request model for educational graphics."""
    title: str
    points: List[str]
    platform: Optional[str] = "instagram_post"


class EmailDigestRequest(BaseModel):
    """Request model for email digest."""
    hours_back: Optional[int] = 24


class RevenueReportRequest(BaseModel):
    """Request model for revenue analytics."""
    sheet_id: str
    month: Optional[str] = None  # YYYY-MM format


class GrokImageRequest(BaseModel):
    """Request model for AI image generation."""
    prompt: str
    count: Optional[int] = 1


class AdCreationRequest(BaseModel):
    """Request model for ad creation workflow."""
    ad_type: str  # 'video_ad', 'image_ad', 'carousel_ad'
    title: Optional[str] = None
    tagline: Optional[str] = None
    call_to_action: Optional[str] = "Learn More"
    platform: Optional[str] = "instagram_post"
    generate_background: Optional[bool] = False
    background_prompt: Optional[str] = None
    edit_video: Optional[bool] = True
    silence_threshold: Optional[float] = -40


class AIRequest(BaseModel):
    """Request model for AI arbitrated requests."""
    message: str
    context: Optional[dict] = None


class VideoGenerateRequest(BaseModel):
    """Request model for video generation from images."""
    image_urls: List[str]
    headline: Optional[str] = "Transform Your Body"
    cta_text: Optional[str] = "Start Your Journey"
    duration: Optional[float] = 15.0
    music_style: Optional[str] = "energetic"  # energetic, motivational, upbeat


class VideoStatusRequest(BaseModel):
    """Request model for checking video render status."""
    render_id: str


class BrandResearchRequest(BaseModel):
    """Request model for brand research."""
    handle: str  # Social media handle (e.g., "boabfit", "@boabfit")
    platforms: Optional[List[str]] = None  # Default: instagram, tiktok


class BrandProfileRequest(BaseModel):
    """Request model for getting a stored brand profile."""
    handle: str


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """API health check and info."""
    return {
        "name": "Fitness Influencer Assistant API",
        "status": "active",
        "version": "2.1.0",
        "ai_providers": {
            "anthropic": bool(os.getenv('ANTHROPIC_API_KEY')),
            "xai": bool(os.getenv('XAI_API_KEY')),
            "shotstack": bool(os.getenv('SHOTSTACK_API_KEY'))
        },
        "endpoints": {
            "ai_chat": "/api/ai/chat",
            "video_edit": "/api/video/edit",
            "video_generate": "/api/video/generate",
            "create_graphic": "/api/graphics/create",
            "email_digest": "/api/email/digest",
            "revenue_report": "/api/analytics/revenue",
            "generate_image": "/api/images/generate"
        }
    }


@app.post("/api/ai/chat")
async def ai_chat(request: AIRequest):
    """
    Intelligent AI endpoint with dual-AI arbitration.

    Both Claude and Grok vote on who should handle the request,
    then the winner executes the task. This prevents self-serving bias.

    Returns the response along with arbitration details and costs.
    """
    from ai_arbitrator import process_with_arbitration

    try:
        result = await process_with_arbitration(request.message)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "content": None
        }


@app.post("/api/video/edit")
async def edit_video(
    video: UploadFile = File(...),
    silence_threshold: float = Form(-40.0),
    min_silence_duration: float = Form(0.5)
):
    """
    Edit video with automatic jump cuts.

    Upload a video file and get back an edited version with:
    - Silence removed (jump cuts)
    - Download URL for processed video

    Returns JSON with download URL, processing stats, and metadata.
    """
    start_time = time.time()

    # Create temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Save uploaded video
        input_path = temp_path / video.filename
        with open(input_path, 'wb') as f:
            shutil.copyfileobj(video.file, f)

        # Generate unique filename for output
        video_id = str(uuid.uuid4())
        file_extension = Path(video.filename).suffix or '.mp4'
        output_filename = f"{video_id}{file_extension}"
        final_output_path = VIDEOS_PATH / output_filename
        temp_output_path = temp_path / output_filename

        # Build command
        cmd = [
            "python",
            str(SCRIPTS_PATH / "video_jumpcut.py"),
            "--input", str(input_path),
            "--output", str(temp_output_path),
            "--silence-thresh", str(silence_threshold),
            "--min-silence", str(min_silence_duration),
        ]

        # Execute
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            if result.returncode != 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"Video editing failed: {result.stderr}"
                )

            # Check if output exists
            if not temp_output_path.exists():
                raise HTTPException(
                    status_code=500,
                    detail="Output video not generated"
                )

            # Move processed video to static directory
            shutil.copy2(temp_output_path, final_output_path)

            # Calculate processing time
            processing_time = round(time.time() - start_time, 2)

            # Get file sizes
            original_size = input_path.stat().st_size
            processed_size = final_output_path.stat().st_size

            # Extract stats from output (if available)
            cuts_made = 0
            for line in result.stdout.split('\n'):
                if 'cuts' in line.lower() or 'removed' in line.lower():
                    # Try to extract number from output
                    import re
                    match = re.search(r'(\d+)', line)
                    if match:
                        cuts_made = int(match.group(1))

            # Build download URL
            # Railway provides PORT env var and deploys to web-production-44ade.up.railway.app
            base_url = os.getenv('BASE_URL', 'https://web-production-44ade.up.railway.app')
            download_url = f"{base_url}/static/videos/{output_filename}"

            return {
                "success": True,
                "message": "Video processed successfully",
                "video_id": video_id,
                "output_url": download_url,
                "filename": output_filename,
                "stats": {
                    "original_filename": video.filename,
                    "original_size_mb": round(original_size / (1024 * 1024), 2),
                    "processed_size_mb": round(processed_size / (1024 * 1024), 2),
                    "size_reduction_percent": round((1 - processed_size / original_size) * 100, 1) if original_size > 0 else 0,
                    "cuts_made": cuts_made,
                    "processing_time_seconds": processing_time,
                    "silence_threshold_db": silence_threshold,
                    "min_silence_duration": min_silence_duration
                }
            }

        except subprocess.TimeoutExpired:
            raise HTTPException(
                status_code=504,
                detail="Video processing timeout (>10 minutes)"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error: {str(e)}"
            )


@app.post("/api/video/generate")
async def generate_video(request: VideoGenerateRequest):
    """
    Generate a video ad from images using Shotstack.

    Takes AI-generated images (from Grok) and creates a professional
    video with transitions, music, and text overlays.

    Returns:
    - video_url: Direct download link for the generated video
    - render_id: ID to check status if still processing
    - cost: Approximate cost (~$0.05-0.10)
    """
    from shotstack_video import ShotstackVideo

    try:
        api = ShotstackVideo()

        if not api.api_key:
            raise HTTPException(
                status_code=500,
                detail="SHOTSTACK_API_KEY not configured. Get one at https://dashboard.shotstack.io/"
            )

        result = await api.create_fitness_video(
            image_urls=request.image_urls,
            headline=request.headline,
            cta_text=request.cta_text,
            duration=request.duration,
            music_style=request.music_style
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Video generation failed")
            )

        return {
            "success": True,
            "video_url": result.get("video_url"),
            "render_id": result.get("render_id"),
            "status": result.get("status"),
            "cost": result.get("cost", 0.05),
            "message": "Video generated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating video: {str(e)}"
        )


@app.post("/api/video/status")
async def check_video_status(request: VideoStatusRequest):
    """
    Check the status of a video render.

    Use this if the video generation is still processing.
    Returns the video URL once complete.
    """
    from shotstack_video import ShotstackVideo

    try:
        api = ShotstackVideo()

        if not api.api_key:
            raise HTTPException(
                status_code=500,
                detail="SHOTSTACK_API_KEY not configured"
            )

        result = api.check_status(request.render_id)

        return {
            "success": result.get("success"),
            "status": result.get("status"),
            "video_url": result.get("video_url"),
            "render_id": request.render_id,
            "error": result.get("error")
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking status: {str(e)}"
        )


@app.post("/api/brand/research")
async def research_brand(request: BrandResearchRequest):
    """
    Research a fitness influencer's brand from their social media.

    Analyzes public profiles to extract:
    - Brand voice and personality
    - Visual style and color palette
    - Content themes and topics
    - Target audience
    - Recommendations for ads

    Returns a comprehensive brand profile that can be used
    to personalize future content creation.
    """
    from brand_research import research_brand as do_research, format_brand_profile_for_display

    try:
        profile = await do_research(
            handle=request.handle,
            platforms=request.platforms
        )

        return {
            "success": True,
            "handle": request.handle,
            "profile": profile,
            "formatted": format_brand_profile_for_display(profile),
            "message": f"Brand profile created for @{request.handle}"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error researching brand: {str(e)}"
        )


@app.get("/api/brand/profile/{handle}")
async def get_brand_profile(handle: str):
    """
    Get an existing brand profile.

    Returns the stored brand profile for a handle,
    or 404 if not found.
    """
    from brand_research import get_brand_profile as get_profile, format_brand_profile_for_display

    profile = get_profile(handle)

    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"No brand profile found for @{handle}. Use /api/brand/research to create one."
        )

    return {
        "success": True,
        "handle": handle,
        "profile": profile,
        "formatted": format_brand_profile_for_display(profile)
    }


@app.get("/api/brand/list")
async def list_brand_profiles():
    """List all stored brand profiles."""
    from brand_research import get_researcher

    researcher = get_researcher()
    profiles = researcher.list_profiles()

    return {
        "success": True,
        "count": len(profiles),
        "profiles": profiles
    }


@app.delete("/api/brand/profile/{handle}")
async def delete_brand_profile(handle: str):
    """Delete a brand profile."""
    from brand_research import get_researcher

    researcher = get_researcher()
    deleted = researcher.delete_profile(handle)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"No brand profile found for @{handle}"
        )

    return {
        "success": True,
        "message": f"Brand profile for @{handle} deleted"
    }


@app.post("/api/graphics/create")
async def create_graphic(request: EducationalGraphicRequest):
    """
    Create branded educational fitness graphic (JSON body).

    Generates Instagram/YouTube/TikTok graphics with:
    - Custom title
    - Key points (bullet list)
    - Marceau Solutions branding
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        output_path = temp_path / "fitness_graphic.jpg"

        # Build command
        cmd = [
            "python",
            str(SCRIPTS_PATH / "educational_graphics.py"),
            "--title", request.title,
            "--points", ",".join(request.points),
            "--platform", request.platform,
            "--output", str(output_path),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"Graphic generation failed: {result.stderr}"
                )

            # Return graphic as base64 or file response
            import base64
            with open(output_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()

            return {
                "success": True,
                "message": "Graphic created successfully",
                "image_data": f"data:image/jpeg;base64,{image_data}",
                "platform": request.platform
            }

        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=504, detail="Graphic generation timeout")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/api/graphics/create-with-background")
async def create_graphic_with_background(
    title: str = Form(...),
    points: str = Form(...),
    platform: str = Form("instagram_post"),
    background: Optional[UploadFile] = File(None)
):
    """
    Create branded educational fitness graphic with optional background image (multipart form).

    Generates Instagram/YouTube/TikTok graphics with:
    - Custom title
    - Key points (bullet list)
    - Marceau Solutions branding
    - Optional custom background
    """
    # Parse points from comma-separated string
    points_list = [p.strip() for p in points.split(",")]

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Save background if provided
        bg_path = None
        if background:
            bg_path = temp_path / background.filename
            with open(bg_path, 'wb') as f:
                shutil.copyfileobj(background.file, f)

        # Output path
        output_path = temp_path / "fitness_graphic.jpg"

        # Build command
        cmd = [
            "python",
            str(SCRIPTS_PATH / "educational_graphics.py"),
            "--title", title,
            "--points", ",".join(points_list),
            "--platform", platform,
            "--output", str(output_path),
        ]

        if bg_path:
            cmd.extend(["--background", str(bg_path)])

        # Execute
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"Graphic generation failed: {result.stderr}"
                )

            # Return graphic
            return FileResponse(
                output_path,
                media_type="image/jpeg",
                filename="fitness_graphic.jpg"
            )

        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=504, detail="Graphic generation timeout")
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error: {str(e)}"
            )


@app.post("/api/email/digest")
async def email_digest(request: EmailDigestRequest):
    """
    Generate email digest with categorization.

    Returns JSON with:
    - Total email count
    - Categorized emails (urgent, business, customer, etc.)
    - Suggested actions
    """
    cmd = [
        "python",
        str(SCRIPTS_PATH / "gmail_monitor.py"),
        "--hours", str(request.hours_back),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Email digest failed: {result.stderr}"
            )

        # Parse output (simplified - in production, modify gmail_monitor.py to output JSON)
        return {
            "status": "success",
            "hours_analyzed": request.hours_back,
            "output": result.stdout,
            "message": "Email digest generated successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


@app.post("/api/analytics/revenue")
async def revenue_report(request: RevenueReportRequest):
    """
    Generate revenue and expense report.

    Returns JSON with:
    - Revenue by source
    - Expenses by category
    - Profit margins
    - Month-over-month growth
    """
    cmd = [
        "python",
        str(SCRIPTS_PATH / "revenue_analytics.py"),
        "--sheet-id", request.sheet_id,
    ]

    if request.month:
        cmd.extend(["--month", request.month])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Revenue report failed: {result.stderr}"
            )

        return {
            "status": "success",
            "month": request.month,
            "output": result.stdout,
            "message": "Revenue report generated successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


@app.post("/api/images/generate")
async def generate_image(request: GrokImageRequest):
    """
    Generate AI images using Grok.

    Returns URLs of generated images.
    """
    import requests as http_requests

    # Generate directly using xAI API instead of subprocess
    api_key = os.getenv('XAI_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="XAI_API_KEY not configured")

    try:
        response = http_requests.post(
            "https://api.x.ai/v1/images/generations",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "prompt": request.prompt,
                "n": request.count,
                "model": "grok-2-image-1212"
            },
            timeout=60
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"xAI API error: {response.text}"
            )

        data = response.json()
        images = data.get('data', [])
        image_urls = [img.get('url') for img in images if img.get('url')]

        return {
            "status": "success",
            "count": len(image_urls),
            "cost": len(image_urls) * 0.07,
            "message": f"Generated {len(image_urls)} image(s)",
            "urls": image_urls,
            "output_url": image_urls[0] if image_urls else None
        }

    except http_requests.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Request failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


@app.post("/api/ads/create")
async def create_advertisement(
    video: Optional[UploadFile] = File(None),
    images: Optional[List[UploadFile]] = File(None),
    title: str = Form(None),
    tagline: str = Form(None),
    call_to_action: str = Form("Learn More"),
    platform: str = Form("instagram_post"),
    generate_background: bool = Form(False),
    background_prompt: str = Form(None),
    edit_video: bool = Form(True),
    silence_threshold: float = Form(-40.0)
):
    """
    Complete ad creation workflow.

    Orchestrates multiple steps to create a polished advertisement:
    1. Edit video with jump cuts (if video provided)
    2. Generate AI background (if requested)
    3. Create branded graphics/overlays
    4. Combine assets into final ad

    Supports:
    - Video ads (with or without editing)
    - Image ads (static or carousel)
    - Platform optimization (Instagram, YouTube, TikTok)

    Returns:
    - Download URLs for all generated assets
    - Processing stats and metadata
    """
    start_time = time.time()
    results = {
        "success": True,
        "assets": {},
        "stats": {},
        "downloads": []
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # STEP 1: Video Processing (if video provided)
        if video:
            print(f"→ Processing video: {video.filename}")

            # Save uploaded video
            input_video_path = temp_path / video.filename
            with open(input_video_path, 'wb') as f:
                shutil.copyfileobj(video.file, f)

            if edit_video:
                # Edit with jump cuts
                video_id = str(uuid.uuid4())
                file_extension = Path(video.filename).suffix or '.mp4'
                edited_filename = f"ad_video_{video_id}{file_extension}"
                edited_video_path = temp_path / edited_filename

                cmd = [
                    "python",
                    str(SCRIPTS_PATH / "video_jumpcut.py"),
                    "--input", str(input_video_path),
                    "--output", str(edited_video_path),
                    "--silence-thresh", str(silence_threshold),
                    "--min-silence", "0.5"
                ]

                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

                    if result.returncode == 0 and edited_video_path.exists():
                        # Copy to static directory
                        final_video_path = VIDEOS_PATH / edited_filename
                        shutil.copy2(edited_video_path, final_video_path)

                        base_url = os.getenv('BASE_URL', 'https://web-production-44ade.up.railway.app')
                        video_url = f"{base_url}/static/videos/{edited_filename}"

                        results["assets"]["edited_video"] = {
                            "url": video_url,
                            "filename": edited_filename,
                            "size_mb": round(final_video_path.stat().st_size / (1024 * 1024), 2)
                        }
                        results["downloads"].append({
                            "type": "video",
                            "name": "Edited Video",
                            "url": video_url
                        })

                        print(f"  ✓ Video edited and saved")
                    else:
                        print(f"  ⚠ Video editing failed, using original")
                        # Use original video
                        final_video_path = VIDEOS_PATH / video.filename
                        shutil.copy2(input_video_path, final_video_path)

                except subprocess.TimeoutExpired:
                    print(f"  ⚠ Video editing timeout, using original")
                    final_video_path = VIDEOS_PATH / video.filename
                    shutil.copy2(input_video_path, final_video_path)
            else:
                # Use original video without editing
                final_video_path = VIDEOS_PATH / video.filename
                shutil.copy2(input_video_path, final_video_path)

                base_url = os.getenv('BASE_URL', 'https://web-production-44ade.up.railway.app')
                video_url = f"{base_url}/static/videos/{video.filename}"

                results["assets"]["original_video"] = {
                    "url": video_url,
                    "filename": video.filename
                }
                results["downloads"].append({
                    "type": "video",
                    "name": "Original Video",
                    "url": video_url
                })

        # STEP 2: Generate AI Background (if requested)
        if generate_background and background_prompt:
            print(f"→ Generating AI background: {background_prompt}")

            bg_filename = f"ad_background_{uuid.uuid4()}.png"
            bg_path = temp_path / bg_filename

            cmd = [
                "python",
                str(SCRIPTS_PATH / "grok_image_gen.py"),
                "--prompt", background_prompt,
                "--count", "1",
                "--output", str(bg_path)
            ]

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

                if result.returncode == 0 and bg_path.exists():
                    # Create images directory if doesn't exist
                    images_path = STATIC_PATH / "images"
                    images_path.mkdir(exist_ok=True)

                    final_bg_path = images_path / bg_filename
                    shutil.copy2(bg_path, final_bg_path)

                    base_url = os.getenv('BASE_URL', 'https://web-production-44ade.up.railway.app')
                    bg_url = f"{base_url}/static/images/{bg_filename}"

                    results["assets"]["ai_background"] = {
                        "url": bg_url,
                        "filename": bg_filename,
                        "cost": 0.07
                    }
                    results["downloads"].append({
                        "type": "image",
                        "name": "AI Background",
                        "url": bg_url
                    })

                    print(f"  ✓ Background generated (cost: $0.07)")
                else:
                    print(f"  ⚠ Background generation failed")

            except subprocess.TimeoutExpired:
                print(f"  ⚠ Background generation timeout")

        # STEP 3: Create Branded Graphic/Overlay (if title provided)
        if title:
            print(f"→ Creating branded graphic: {title}")

            graphic_filename = f"ad_graphic_{uuid.uuid4()}.png"
            graphic_path = temp_path / graphic_filename

            # Prepare points for graphic
            points = []
            if tagline:
                points.append(tagline)
            if call_to_action:
                points.append(f"👉 {call_to_action}")

            # Default points if none provided
            if not points:
                points = ["Professional Results", "Fast Turnaround", "Get Started Today"]

            # Build command
            cmd = [
                "python",
                str(SCRIPTS_PATH / "educational_graphics.py"),
                "--title", title,
                "--points", ",".join(points),
                "--output", str(graphic_path),
                "--platform", platform
            ]

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                if result.returncode == 0 and graphic_path.exists():
                    images_path = STATIC_PATH / "images"
                    images_path.mkdir(exist_ok=True)

                    final_graphic_path = images_path / graphic_filename
                    shutil.copy2(graphic_path, final_graphic_path)

                    base_url = os.getenv('BASE_URL', 'https://web-production-44ade.up.railway.app')
                    graphic_url = f"{base_url}/static/images/{graphic_filename}"

                    results["assets"]["branded_graphic"] = {
                        "url": graphic_url,
                        "filename": graphic_filename,
                        "platform": platform
                    }
                    results["downloads"].append({
                        "type": "image",
                        "name": "Branded Graphic",
                        "url": graphic_url
                    })

                    print(f"  ✓ Graphic created for {platform}")
                else:
                    print(f"  ⚠ Graphic creation failed")

            except subprocess.TimeoutExpired:
                print(f"  ⚠ Graphic creation timeout")

        # STEP 4: Process additional images
        if images:
            print(f"→ Processing {len(images)} additional image(s)")

            images_path = STATIC_PATH / "images"
            images_path.mkdir(exist_ok=True)

            for i, img in enumerate(images):
                img_filename = f"ad_image_{i}_{uuid.uuid4()}{Path(img.filename).suffix}"
                img_path = images_path / img_filename

                with open(img_path, 'wb') as f:
                    shutil.copyfileobj(img.file, f)

                base_url = os.getenv('BASE_URL', 'https://web-production-44ade.up.railway.app')
                img_url = f"{base_url}/static/images/{img_filename}"

                results["downloads"].append({
                    "type": "image",
                    "name": f"Image {i+1}",
                    "url": img_url
                })

            print(f"  ✓ {len(images)} image(s) processed")

        # Calculate total processing time
        processing_time = round(time.time() - start_time, 2)
        results["stats"]["processing_time_seconds"] = processing_time
        results["stats"]["total_assets"] = len(results["downloads"])

        # Calculate costs
        total_cost = 0
        if "ai_background" in results["assets"]:
            total_cost += results["assets"]["ai_background"]["cost"]
        results["stats"]["total_cost"] = total_cost

        print(f"\n✅ Ad creation complete!")
        print(f"   Processing time: {processing_time}s")
        print(f"   Total assets: {len(results['downloads'])}")
        print(f"   Total cost: ${total_cost:.2f}\n")

        return results


# ============================================================================
# Lead Capture & Opt-In Endpoints
# ============================================================================

class LeadSubmission(BaseModel):
    firstName: str
    lastName: str
    businessName: str
    email: str
    phone: str
    projectDescription: str
    smsOptIn: bool
    emailOptIn: bool
    termsAgreement: bool
    timestamp: str
    source: str

class SMSOptIn(BaseModel):
    phone: str
    firstName: str
    lastName: str
    timestamp: str

class EmailOptIn(BaseModel):
    email: str
    firstName: str
    lastName: str
    businessName: str
    timestamp: str

@app.post("/api/leads/submit")
async def submit_lead(lead: LeadSubmission):
    """
    Submit lead capture form data to Google Sheets.
    This endpoint stores form submissions for follow-up.

    Supports credentials via:
    1. GOOGLE_TOKEN_JSON environment variable (base64 encoded token.json content)
    2. Local token.json file
    """
    try:
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        import json
        import base64

        creds = None

        # Method 1: Try loading from environment variable (for Railway deployment)
        token_json_env = os.getenv('GOOGLE_TOKEN_JSON')
        if token_json_env:
            try:
                # Decode base64 if it looks encoded, otherwise use as-is
                if not token_json_env.startswith('{'):
                    token_data = base64.b64decode(token_json_env).decode('utf-8')
                else:
                    token_data = token_json_env
                token_dict = json.loads(token_data)
                creds = Credentials.from_authorized_user_info(token_dict)
            except Exception as e:
                print(f"Failed to load credentials from env: {e}")

        # Method 2: Fall back to local file
        if not creds:
            token_path = SCRIPTS_PATH / "token.json"
            if token_path.exists():
                creds = Credentials.from_authorized_user_file(str(token_path))

        if not creds:
            return {
                "success": False,
                "error": "Google OAuth not configured. Please set up credentials first.",
                "data": lead.dict()
            }

        service = build('sheets', 'v4', credentials=creds)

        # TODO: Replace with your actual Google Sheets ID
        # For now, return success with data
        spreadsheet_id = os.getenv('LEADS_SHEET_ID', 'CONFIGURE_ME')

        if spreadsheet_id == 'CONFIGURE_ME':
            # Store locally for now
            print(f"📝 Lead Captured: {lead.firstName} {lead.lastName} - {lead.businessName}")
            print(f"   Email: {lead.email} | Phone: {lead.phone}")
            print(f"   SMS Opt-In: {lead.smsOptIn} | Email Opt-In: {lead.emailOptIn}")

            return {
                "success": True,
                "message": "Lead captured (Google Sheets pending configuration)",
                "data": lead.dict()
            }

        # Prepare row data
        row_data = [
            lead.timestamp,
            lead.firstName,
            lead.lastName,
            lead.businessName,
            lead.email,
            lead.phone,
            lead.projectDescription,
            "Yes" if lead.smsOptIn else "No",
            "Yes" if lead.emailOptIn else "No",
            lead.source
        ]

        # Append to sheet (use LEADS_SHEET_NAME env var or default to Sheet1)
        sheet_name = os.getenv('LEADS_SHEET_NAME', 'Sheet1')
        body = {'values': [row_data]}
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=f'{sheet_name}!A:J',
            valueInputOption='RAW',
            body=body
        ).execute()

        return {
            "success": True,
            "message": "Lead submitted to Google Sheets",
            "data": lead.dict()
        }

    except Exception as e:
        print(f"Error submitting lead: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": lead.dict()
        }

@app.post("/api/sms/optin")
async def sms_optin(opt_in: SMSOptIn):
    """
    Handle SMS opt-in webhook.
    Sends welcome SMS via Twilio and stores consent record.
    """
    try:
        from twilio.rest import Client
        import os

        # Twilio credentials from environment variables
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        from_number = os.getenv('TWILIO_PHONE_NUMBER', '+18552399364')

        if not account_sid or not auth_token:
            print(f"⚠️  SMS Opt-In (Twilio not configured): {opt_in.firstName} {opt_in.lastName} - {opt_in.phone}")
            return {
                "success": False,
                "message": "Twilio credentials not configured",
                "data": opt_in.dict()
            }

        # Initialize Twilio client
        client = Client(account_sid, auth_token)

        # Send welcome message
        welcome_message = f"""Hi {opt_in.firstName}! 👋

Welcome to Marceau Solutions AI Automation.

We're excited to help you scale your fitness business with cutting-edge AI tools.

Reply STOP to opt-out anytime.

- Marceau Solutions Team"""

        message = client.messages.create(
            body=welcome_message,
            from_=from_number,
            to=opt_in.phone
        )

        print(f"📱 SMS Opt-In Success: {opt_in.firstName} {opt_in.lastName} - {opt_in.phone}")
        print(f"   Message SID: {message.sid}")

        return {
            "success": True,
            "message": "Welcome SMS sent",
            "message_sid": message.sid,
            "data": opt_in.dict()
        }

    except Exception as e:
        print(f"Error sending SMS: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": opt_in.dict()
        }

@app.post("/api/email/optin")
async def email_optin(opt_in: EmailOptIn):
    """
    Handle email opt-in webhook.
    Sends welcome email and adds to email list.

    Supports:
    - SendGrid API (preferred, set SENDGRID_API_KEY)
    - SMTP (fallback, set SMTP_USERNAME and SMTP_PASSWORD)
    """
    try:
        import os

        sendgrid_api_key = os.getenv('SENDGRID_API_KEY', '').strip()
        sender_name = os.getenv('SENDER_NAME', 'Marceau Solutions')
        sender_email = os.getenv('SENDER_EMAIL', 'wmarceau@marceausolutions.com')

        # Build email HTML content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #FFD700;">Welcome, {opt_in.firstName}!</h1>
                <p>Thank you for joining Marceau Solutions.</p>
                <p>We're excited to help <strong>{opt_in.businessName}</strong> scale with AI automation.</p>

                <h2 style="color: #000;">What's Next?</h2>
                <ul>
                    <li>Schedule your free consultation call</li>
                    <li>Get access to our AI tools dashboard</li>
                    <li>Receive exclusive tips and strategies</li>
                </ul>

                <p>Stay tuned for updates, special offers, and fitness industry insights!</p>

                <p style="margin-top: 30px;">
                    Best,<br>
                    <strong>The Marceau Solutions Team</strong>
                </p>
            </div>
        </body>
        </html>
        """

        # Try SendGrid first (preferred for cloud environments)
        if sendgrid_api_key:
            import httpx

            print(f"📧 Sending via SendGrid to: {opt_in.email}")

            response = httpx.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {sendgrid_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "personalizations": [{"to": [{"email": opt_in.email}]}],
                    "from": {"email": sender_email, "name": sender_name},
                    "subject": f"Welcome to Marceau Solutions, {opt_in.firstName}!",
                    "content": [{"type": "text/html", "value": html_content}]
                },
                timeout=30.0
            )

            if response.status_code in [200, 201, 202]:
                print(f"📧 Email Opt-In Success (SendGrid): {opt_in.firstName} {opt_in.lastName} - {opt_in.email}")
                return {
                    "success": True,
                    "message": "Welcome email sent via SendGrid",
                    "data": opt_in.dict()
                }
            else:
                print(f"SendGrid error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"SendGrid API error: {response.status_code}",
                    "data": opt_in.dict()
                }

        # Fallback to SMTP
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com').strip()
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_user = os.getenv('SMTP_USERNAME', '').strip()
        smtp_pass = os.getenv('SMTP_PASSWORD', '').strip()

        if not smtp_user or not smtp_pass:
            print(f"📧 Email Opt-In (no email provider configured): {opt_in.firstName} {opt_in.lastName} - {opt_in.email}")
            return {
                "success": False,
                "message": "No email provider configured. Set SENDGRID_API_KEY or SMTP credentials.",
                "data": opt_in.dict()
            }

        # Debug: log SMTP config (without password)
        print(f"📧 Connecting to SMTP: host={repr(smtp_host)}, port={smtp_port}, user={smtp_user}")

        # Create welcome email using the html_content defined above
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Welcome to Marceau Solutions, {opt_in.firstName}!"
        msg['From'] = f"{sender_name} <{sender_email}>"
        msg['To'] = opt_in.email
        msg.attach(MIMEText(html_content, 'html'))

        # Send email with timeout and better error handling
        import socket
        socket.setdefaulttimeout(30)  # 30 second timeout

        try:
            # Use SMTP_SSL for port 465, STARTTLS for port 587
            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
                server.ehlo()
                server.starttls()
                server.ehlo()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()
        except smtplib.SMTPAuthenticationError as auth_err:
            print(f"SMTP Authentication failed: {auth_err}")
            return {
                "success": False,
                "error": "SMTP authentication failed. Please use a Gmail App Password.",
                "data": opt_in.dict()
            }
        except socket.gaierror as dns_err:
            print(f"DNS resolution failed for {smtp_host}: {dns_err}")
            return {
                "success": False,
                "error": f"Could not resolve SMTP server: {smtp_host}",
                "data": opt_in.dict()
            }
        except OSError as net_err:
            print(f"Network error connecting to SMTP: {net_err}")
            return {
                "success": False,
                "error": f"Network error: {net_err}. Try using an email service like SendGrid instead of SMTP.",
                "data": opt_in.dict()
            }

        print(f"📧 Email Opt-In Success: {opt_in.firstName} {opt_in.lastName} - {opt_in.email}")

        return {
            "success": True,
            "message": "Welcome email sent",
            "data": opt_in.dict()
        }

    except Exception as e:
        print(f"Error sending email: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": opt_in.dict()
        }


# ============================================================================
# User OAuth Endpoints (Gmail/Sheets/Calendar Access)
# ============================================================================

class OAuthStartRequest(BaseModel):
    """Request to start OAuth flow."""
    email: str

class UserDataRequest(BaseModel):
    """Request for user-specific data."""
    user_id: str

class UserSheetsRequest(BaseModel):
    """Request for user's spreadsheet data."""
    user_id: str
    spreadsheet_id: str
    range_name: Optional[str] = "Sheet1!A:Z"

@app.post("/api/oauth/start")
async def start_oauth(request: OAuthStartRequest):
    """
    Start OAuth flow for a user to connect their Google account.

    Returns an authorization URL that the user should visit to grant access.
    After granting access, they'll be redirected back to /api/oauth/callback.
    """
    try:
        from user_oauth import create_authorization_url

        result = create_authorization_url(request.email)

        return {
            "success": True,
            "authorization_url": result['url'],
            "user_id": result['user_id'],
            "message": "Redirect user to authorization_url to connect their Google account"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/oauth/callback")
async def oauth_callback(code: str, state: str):
    """
    Handle OAuth callback from Google.

    This endpoint receives the authorization code after user grants access.
    It exchanges the code for tokens and stores them securely.
    """
    from fastapi.responses import HTMLResponse

    try:
        from user_oauth import handle_oauth_callback

        result = handle_oauth_callback(code, state)

        # Return a nice HTML page for the user
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Connected Successfully</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                       display: flex; justify-content: center; align-items: center; height: 100vh;
                       margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
                .card {{ background: white; padding: 40px; border-radius: 16px; text-align: center;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.2); max-width: 400px; }}
                h1 {{ color: #22c55e; margin-bottom: 10px; }}
                p {{ color: #6b7280; }}
                .user-id {{ background: #f3f4f6; padding: 10px; border-radius: 8px;
                           font-family: monospace; margin: 20px 0; }}
                .close-btn {{ background: #667eea; color: white; padding: 12px 24px;
                             border: none; border-radius: 8px; cursor: pointer; font-size: 16px; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>✅ Connected!</h1>
                <p>Your Google account has been successfully connected.</p>
                <p><strong>Email:</strong> {result['email']}</p>
                <div class="user-id">User ID: {result['user_id']}</div>
                <p>You can now use the AI assistant to access your Gmail and Google Sheets.</p>
                <button class="close-btn" onclick="window.close()">Close Window</button>
            </div>
        </body>
        </html>
        """

        return HTMLResponse(content=html_content)

    except Exception as e:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Connection Failed</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                       display: flex; justify-content: center; align-items: center; height: 100vh;
                       margin: 0; background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }}
                .card {{ background: white; padding: 40px; border-radius: 16px; text-align: center;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.2); max-width: 400px; }}
                h1 {{ color: #ef4444; margin-bottom: 10px; }}
                p {{ color: #6b7280; }}
                .error {{ background: #fef2f2; color: #dc2626; padding: 10px; border-radius: 8px;
                         font-family: monospace; margin: 20px 0; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>❌ Connection Failed</h1>
                <p>There was an error connecting your Google account.</p>
                <div class="error">{str(e)}</div>
                <p>Please try again or contact support.</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=400)

@app.get("/api/oauth/status/{user_id}")
async def oauth_status(user_id: str):
    """Check if a user has connected their Google account."""
    try:
        from user_oauth import is_user_connected, get_token_path
        import json

        connected = is_user_connected(user_id)

        result = {
            "user_id": user_id,
            "connected": connected
        }

        if connected:
            token_path = get_token_path(user_id)
            with open(token_path, 'r') as f:
                data = json.load(f)
            result["email"] = data.get("user_email")
            result["connected_at"] = data.get("connected_at")
            result["scopes"] = data.get("scopes", [])

        return result

    except Exception as e:
        return {"user_id": user_id, "connected": False, "error": str(e)}

@app.delete("/api/oauth/disconnect/{user_id}")
async def oauth_disconnect(user_id: str):
    """Disconnect a user's Google account."""
    try:
        from user_oauth import disconnect_user

        disconnected = disconnect_user(user_id)

        return {
            "success": True,
            "user_id": user_id,
            "disconnected": disconnected,
            "message": "Account disconnected" if disconnected else "Account was not connected"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/oauth/users")
async def list_oauth_users():
    """List all connected users (admin endpoint)."""
    try:
        from user_oauth import list_connected_users

        users = list_connected_users()

        return {
            "success": True,
            "count": len(users),
            "users": users
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/user/email-digest")
async def user_email_digest(request: UserDataRequest):
    """
    Get email digest for a connected user.

    Requires the user to have connected their Google account first.
    """
    try:
        from user_oauth import get_user_email_digest, is_user_connected

        if not is_user_connected(request.user_id):
            return {
                "success": False,
                "error": "User not connected. Please connect Google account first.",
                "connect_url": "/api/oauth/start"
            }

        digest = get_user_email_digest(request.user_id, hours_back=24)

        return {
            "success": True,
            "user_id": request.user_id,
            "digest": digest
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/user/sheets-data")
async def user_sheets_data(request: UserSheetsRequest):
    """
    Get spreadsheet data for a connected user.

    Requires the user to have connected their Google account first.
    """
    try:
        from user_oauth import get_user_sheets_data, is_user_connected

        if not is_user_connected(request.user_id):
            return {
                "success": False,
                "error": "User not connected. Please connect Google account first.",
                "connect_url": "/api/oauth/start"
            }

        data = get_user_sheets_data(
            request.user_id,
            request.spreadsheet_id,
            request.range_name
        )

        return {
            "success": True,
            "user_id": request.user_id,
            "data": data
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# Utility Endpoints
# ============================================================================

@app.get("/api/status")
async def status():
    """Check API and dependencies status."""

    # Check for ffmpeg in multiple locations
    ffmpeg_available = False
    ffmpeg_path = None

    # Check common locations
    for path in ["/nix/store", "/usr/bin", "/usr/local/bin"]:
        result = subprocess.run(["find", path, "-name", "ffmpeg", "-type", "f"],
                              capture_output=True, text=True, timeout=5)
        if result.stdout.strip():
            ffmpeg_available = True
            ffmpeg_path = result.stdout.strip().split('\n')[0]
            break

    # Fallback to shutil.which
    if not ffmpeg_available:
        ffmpeg_available = shutil.which("ffmpeg") is not None
        if ffmpeg_available:
            ffmpeg_path = shutil.which("ffmpeg")

    dependencies = {
        "ffmpeg": ffmpeg_available,
        "ffmpeg_path": ffmpeg_path,
        "python": True,
        "scripts_available": {
            "video_jumpcut": (SCRIPTS_PATH / "video_jumpcut.py").exists(),
            "educational_graphics": (SCRIPTS_PATH / "educational_graphics.py").exists(),
            "gmail_monitor": (SCRIPTS_PATH / "gmail_monitor.py").exists(),
            "revenue_analytics": (SCRIPTS_PATH / "revenue_analytics.py").exists(),
            "grok_image_gen": (SCRIPTS_PATH / "grok_image_gen.py").exists(),
            "shotstack_video": (SCRIPTS_PATH / "shotstack_video.py").exists(),
        },
        "api_keys": {
            "anthropic": bool(os.getenv('ANTHROPIC_API_KEY')),
            "xai": bool(os.getenv('XAI_API_KEY')),
            "shotstack": bool(os.getenv('SHOTSTACK_API_KEY')),
        }
    }

    all_ready = all(dependencies["scripts_available"].values())

    return {
        "api_status": "healthy",
        "dependencies": dependencies,
        "ready": all_ready and dependencies["ffmpeg"]
    }


if __name__ == "__main__":
    import uvicorn

    print("="*70)
    print("FITNESS INFLUENCER ASSISTANT API")
    print("="*70)
    print("\nStarting server...")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/api/status")
    print("\nPress CTRL+C to stop")
    print("="*70 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
