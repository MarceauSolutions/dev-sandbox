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
from pydantic import BaseModel
from typing import Optional, List
import subprocess
import os
from pathlib import Path
import tempfile
import shutil

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


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """API health check and info."""
    return {
        "name": "Fitness Influencer Assistant API",
        "status": "active",
        "version": "1.0.0",
        "endpoints": {
            "video_edit": "/api/video/edit",
            "create_graphic": "/api/graphics/create",
            "email_digest": "/api/email/digest",
            "revenue_report": "/api/analytics/revenue",
            "generate_image": "/api/images/generate"
        }
    }


@app.post("/api/video/edit")
async def edit_video(
    video: UploadFile = File(...),
    config: VideoEditRequest = None
):
    """
    Edit video with automatic jump cuts.

    Upload a video file and get back an edited version with:
    - Silence removed (jump cuts)
    - Optional thumbnail generation
    """
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Save uploaded video
        input_path = temp_path / video.filename
        with open(input_path, 'wb') as f:
            shutil.copyfileobj(video.file, f)

        # Output path
        output_filename = f"edited_{video.filename}"
        output_path = temp_path / output_filename

        # Build command
        cmd = [
            "python",
            str(SCRIPTS_PATH / "video_jumpcut.py"),
            "--input", str(input_path),
            "--output", str(output_path),
        ]

        if config:
            cmd.extend([
                "--silence-thresh", str(config.silence_threshold),
                "--min-silence", str(config.min_silence_duration),
            ])
            if config.generate_thumbnail:
                cmd.append("--thumbnail")

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
            if not output_path.exists():
                raise HTTPException(
                    status_code=500,
                    detail="Output video not generated"
                )

            # Return edited video
            return FileResponse(
                output_path,
                media_type="video/mp4",
                filename=output_filename
            )

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


@app.post("/api/graphics/create")
async def create_graphic(
    request: EducationalGraphicRequest,
    background: Optional[UploadFile] = File(None)
):
    """
    Create branded educational fitness graphic.

    Generates Instagram/YouTube/TikTok graphics with:
    - Custom title
    - Key points (bullet list)
    - Marceau Solutions branding
    """
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
            "--title", request.title,
            "--points", ",".join(request.points),
            "--platform", request.platform,
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

    Returns URLs or downloads generated images.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        output_path = temp_path / "generated_image.png"

        cmd = [
            "python",
            str(SCRIPTS_PATH / "grok_image_gen.py"),
            "--prompt", request.prompt,
            "--count", str(request.count),
            "--output", str(output_path),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"Image generation failed: {result.stderr}"
                )

            # If single image, return file
            if request.count == 1 and output_path.exists():
                return FileResponse(
                    output_path,
                    media_type="image/png",
                    filename="generated_image.png"
                )

            # Multiple images - return JSON with paths
            return {
                "status": "success",
                "count": request.count,
                "cost": request.count * 0.07,
                "message": f"Generated {request.count} image(s)",
                "output": result.stdout
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error: {str(e)}"
            )


# ============================================================================
# Utility Endpoints
# ============================================================================

@app.get("/api/status")
async def status():
    """Check API and dependencies status."""

    dependencies = {
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "python": True,
        "scripts_available": {
            "video_jumpcut": (SCRIPTS_PATH / "video_jumpcut.py").exists(),
            "educational_graphics": (SCRIPTS_PATH / "educational_graphics.py").exists(),
            "gmail_monitor": (SCRIPTS_PATH / "gmail_monitor.py").exists(),
            "revenue_analytics": (SCRIPTS_PATH / "revenue_analytics.py").exists(),
            "grok_image_gen": (SCRIPTS_PATH / "grok_image_gen.py").exists(),
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
