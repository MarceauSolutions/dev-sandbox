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

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import subprocess
import os
from pathlib import Path
import tempfile
import shutil
import uuid
import time

# Structured logging (v2.0)
from backend.logging_config import setup_logging, get_logger
from backend.middleware import setup_middleware

# Rate limiting (v2.0)
from backend.rate_limiter import (
    limiter,
    rate_limit_exceeded_handler,
    check_quota,
    get_quota_status,
    require_quota,
    get_rate_limit_headers,
    Tier
)
from slowapi.errors import RateLimitExceeded

# Gamification routes (v2.0)
from backend.gamification_routes import router as gamification_router

# Task management routes (v2.0)
from backend.tasks_routes import router as tasks_router

# SMS routes — hybrid n8n + Python (v2.1)
from backend.sms_routes import router as sms_router

# Collaborator management routes (v2.1)
from backend.collaborators_routes import router as collaborators_router

# Initialize structured JSON logging
setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="Fitness Influencer Assistant API",
    description="AI-powered fitness content creation and automation",
    version="2.0.0"
)

# Add rate limiter to app state and register error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Enable CORS for Replit app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Replit app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add structured logging and performance monitoring middleware (v2.0)
setup_middleware(app)

# Include gamification routes (v2.0)
app.include_router(gamification_router)

# Include task management routes (v2.0)
app.include_router(tasks_router)

# Include SMS routes — hybrid n8n + Python (v2.1)
app.include_router(sms_router)

# Include collaborator management routes (v2.1)
app.include_router(collaborators_router)

# Base path for execution scripts
SCRIPTS_PATH = Path(__file__).parent
PROJECT_PATH = SCRIPTS_PATH.parent  # fitness-influencer root

# Create static directory for processed videos
STATIC_PATH = SCRIPTS_PATH / "static"
VIDEOS_PATH = STATIC_PATH / "videos"
VIDEOS_PATH.mkdir(parents=True, exist_ok=True)

# Frontend path for HTML files
FRONTEND_PATH = PROJECT_PATH / "frontend"

# Mount static files for video downloads
app.mount("/static", StaticFiles(directory=str(STATIC_PATH)), name="static")

# Mount frontend assets (CSS, JS) for dashboard
app.mount("/frontend", StaticFiles(directory=str(FRONTEND_PATH)), name="frontend")


# ============================================================================
# Frontend Routes
# ============================================================================

@app.get("/dashboard")
async def dashboard_page():
    """Serve the main dashboard SPA."""
    dashboard_html = FRONTEND_PATH / "index.html"
    if dashboard_html.exists():
        return FileResponse(dashboard_html, media_type="text/html")
    raise HTTPException(status_code=404, detail="Dashboard not found")


@app.get("/gamification")
async def gamification_page():
    """Serve the gamification dashboard HTML page."""
    gamification_html = FRONTEND_PATH / "gamification.html"
    if gamification_html.exists():
        return FileResponse(gamification_html, media_type="text/html")
    raise HTTPException(status_code=404, detail="Gamification page not found")


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
    force_method: Optional[str] = None  # 'moviepy', 'creatomate', or None (auto)
    quality_tier: Optional[str] = None  # 'free', 'budget', 'standard', 'premium', or None (auto)


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
# Job Queue Models (v2.0)
# ============================================================================

class JobSubmitRequest(BaseModel):
    """Request model for submitting a background job."""
    job_type: str  # video_caption, video_filler_removal, video_reframe, video_export, etc.
    params: Dict[str, Any]
    user_id: Optional[str] = None
    priority: Optional[int] = 5  # 1=highest, 10=lowest

class JobStatusResponse(BaseModel):
    """Response model for job status."""
    job_id: str
    status: str  # queued, processing, complete, failed, cancelled
    progress: int  # 0-100
    estimated_remaining: int  # seconds
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class JobSubmitResponse(BaseModel):
    """Response model for job submission."""
    job_id: str
    status: str
    job_type: str
    created_at: str
    estimated_time: int  # seconds
    poll_url: str

class VideoCaptionRequest(BaseModel):
    """
    Request model for video captioning job with full customization.

    Supports:
    - Style presets: trending, glow, minimal, bold, clean, neon, subtitle, fitness, professional, dramatic
    - Position with offset: 'bottom', 'center', 'top', or 'bottom+20' for pixel offset
    - Custom fonts and colors (hex or named colors like 'white', 'neon_green')
    - Word highlighting styles: color, underline, bold, scale, none
    """
    video_url: str
    style: Optional[str] = "trending"  # trending, glow, minimal, bold, clean, neon, etc.
    position: Optional[str] = "bottom"  # top, center, bottom (with optional offset like 'bottom+20')
    language: Optional[str] = "en"  # en, es, pt, auto
    word_highlight: Optional[bool] = True
    max_words_per_line: Optional[int] = 7

    # Custom font settings
    custom_font: Optional[str] = None  # e.g., "Arial", "Impact", "Roboto"
    font_size: Optional[int] = None  # 24-72pt range

    # Custom color settings (hex or named colors)
    font_color: Optional[str] = None  # e.g., "#FFFFFF" or "white"
    outline_color: Optional[str] = None  # e.g., "#000000" or "black"
    outline_width: Optional[int] = None  # 0-5 pixels
    shadow_color: Optional[str] = None  # e.g., "#000000" or None
    shadow_offset: Optional[int] = None  # 0-10 pixels
    highlight_color: Optional[str] = None  # Color for active word highlighting

    # Background settings
    background_color: Optional[str] = None  # e.g., "#000000" for subtitle-style
    background_opacity: Optional[float] = None  # 0.0-1.0

class VideoReframeRequest(BaseModel):
    """Request model for video reframe job."""
    video_url: str
    target_aspect: Optional[str] = "9:16"  # 9:16, 1:1, 4:5, 16:9
    tracking_mode: Optional[str] = "auto"  # face, body, auto
    smoothing: Optional[float] = 0.8  # 0.1-1.0
    safe_zone_margin: Optional[float] = 0.1

class VideoExportRequest(BaseModel):
    """
    Request model for multi-platform export with metadata generation.

    Features:
    - Export to multiple platforms in parallel (TikTok, Instagram, YouTube, etc.)
    - Platform-optimized encoding (resolution, bitrate, codec)
    - Auto-generate hashtags and descriptions from transcription
    - Webhook notification on completion
    """
    video_url: str
    platforms: List[str] = ["tiktok", "instagram_reels", "youtube_shorts"]
    include_captions: Optional[bool] = False
    generate_descriptions: Optional[bool] = True
    hashtag_count: Optional[int] = None  # Uses platform-optimal count if not specified
    transcription_text: Optional[str] = None  # For metadata generation
    category: Optional[str] = None  # workout, nutrition, motivation, transformation, tutorial, tips, challenge
    webhook_url: Optional[str] = None  # URL to POST completion notification


class BatchExportRequest(BaseModel):
    """
    Request model for exporting multiple videos to multiple platforms.

    Useful for batch processing content across all platforms at once.
    """
    videos: List[Dict[str, Any]]  # List of {video_url, transcription_text, category}
    platforms: List[str] = ["tiktok", "instagram_reels", "youtube_shorts"]
    generate_descriptions: Optional[bool] = True
    webhook_url: Optional[str] = None

class FillerRemovalRequest(BaseModel):
    """Request model for filler word removal."""
    video_url: str
    sensitivity: Optional[str] = "moderate"  # aggressive, moderate, conservative


class FillerDetectionRequest(BaseModel):
    """Request model for filler word detection (analysis only, no removal)."""
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    sensitivity: Optional[str] = "moderate"  # aggressive, moderate, conservative
    confidence_threshold: Optional[float] = None  # Override default (0.5-0.95)
    include_clusters: Optional[bool] = True  # Include filler clusters in response
    language: Optional[str] = "en"  # Transcription language
    fillers_to_remove: Optional[List[str]] = ["um", "uh", "like", "you know"]
    preserve_rhythm: Optional[bool] = True


class VideoAnalyzeRequest(BaseModel):
    """
    Request model for long-form video analysis.

    Analyzes videos to identify structure, key moments, and potential clips.
    Optimized for 10-60 minute videos with < 2 minute processing.
    """
    video_url: str
    analyze_audio: Optional[bool] = True  # Analyze audio energy peaks/valleys
    analyze_motion: Optional[bool] = True  # Detect high-motion segments
    detect_scenes: Optional[bool] = True  # Identify scene/shot changes
    extract_keywords: Optional[bool] = True  # Extract keywords from transcription
    min_segment_duration: Optional[float] = 5.0  # Min clip duration (seconds)
    max_segment_duration: Optional[float] = 60.0  # Max clip duration (seconds)
    transcription_text: Optional[str] = None  # Pre-transcribed text (speeds up analysis)
    word_timestamps: Optional[List[Dict[str, Any]]] = None  # Word-level timestamps
    top_segments_count: Optional[int] = 20  # Number of top segments to return


class ViralDetectionRequest(BaseModel):
    """
    Request model for viral moment detection.

    Identifies the best clips from long-form content with viral scoring.
    """
    video_url: str
    top_count: Optional[int] = 10  # Number of viral moments to return
    min_score: Optional[float] = 40.0  # Minimum viral score (0-100)
    min_duration: Optional[float] = 15.0  # Minimum clip duration (seconds)
    max_duration: Optional[float] = 60.0  # Maximum clip duration (seconds)
    preserve_sentences: Optional[bool] = True  # Don't cut mid-sentence
    transcription_text: Optional[str] = None  # Pre-transcribed text
    word_timestamps: Optional[List[Dict[str, Any]]] = None  # Word-level timestamps
    # Scoring weights (must sum to ~1.0)
    weight_hook: Optional[float] = 0.25
    weight_audio: Optional[float] = 0.15
    weight_visual: Optional[float] = 0.15
    weight_keywords: Optional[float] = 0.15
    weight_emotion: Optional[float] = 0.15
    weight_fitness: Optional[float] = 0.15


class HookAnalysisRequest(BaseModel):
    """
    Request model for hook analysis and optimization.

    Analyzes the first 3 seconds of a video for hook effectiveness,
    provides improvement suggestions, and generates alternative variants.
    """
    video_url: str
    platform: Optional[str] = "tiktok"  # tiktok, instagram_reels, youtube_shorts
    hook_duration: Optional[float] = 3.0  # Duration to analyze (seconds)
    generate_variants: Optional[bool] = True  # Generate alternative hook variants
    variant_count: Optional[int] = 3  # Number of variants to generate
    include_ab_test_setup: Optional[bool] = False  # Include A/B test framework
    transcription_text: Optional[str] = None  # Pre-transcribed text
    word_timestamps: Optional[List[Dict[str, Any]]] = None  # Word-level timestamps


class RetentionPredictionRequest(BaseModel):
    """
    Request model for retention curve prediction.

    Predicts audience retention before publishing, identifies drop-off points,
    and provides improvement suggestions.
    """
    video_url: str
    platform: Optional[str] = "tiktok"  # tiktok, instagram_reels, youtube_shorts, youtube
    sample_interval: Optional[float] = 1.0  # Sample every N seconds
    include_hook_analysis: Optional[bool] = True  # Include hook scoring
    cliff_threshold: Optional[float] = 10.0  # Drop % to flag as cliff
    generate_suggestions: Optional[bool] = True  # Generate improvement tips
    transcription_text: Optional[str] = None  # Pre-transcribed text
    word_timestamps: Optional[List[Dict[str, Any]]] = None  # Word-level timestamps


class WorkoutOverlayRequest(BaseModel):
    """
    Request model for workout timer overlay.

    Adds HIIT timers, rep counters, and interval indicators to videos.
    """
    video_url: str
    timer_type: Optional[str] = "interval"  # countdown, countup, interval, rep_counter
    preset: Optional[str] = None  # hiit, tabata, emom, amrap, strength, yoga, cardio, plank

    # Custom timer settings (used if no preset)
    duration: Optional[float] = 60.0  # Total duration in seconds
    work_duration: Optional[float] = 45.0  # Work interval (for interval type)
    rest_duration: Optional[float] = 15.0  # Rest interval (for interval type)
    rounds: Optional[int] = 1  # Number of rounds

    # Rep counter settings
    total_reps: Optional[int] = 10
    auto_increment: Optional[bool] = False

    # Visual settings
    position: Optional[str] = "top_right"  # top_left, top_right, bottom_left, bottom_right, center
    style: Optional[str] = "bold"  # minimal, bold, neon, digital

    # Display settings
    show_round_number: Optional[bool] = True
    show_work_rest_label: Optional[bool] = True

    # Audio settings
    enable_audio_cues: Optional[bool] = False


class AnnotationItem(BaseModel):
    """Single annotation item."""
    type: str  # arrow, circle, line, text, highlight_box
    start_time: Optional[float] = 0.0
    end_time: Optional[float] = None

    # Arrow/Line coordinates
    start: Optional[List[int]] = None  # [x, y]
    end: Optional[List[int]] = None  # [x, y]

    # Circle coordinates
    center: Optional[List[int]] = None  # [x, y]
    radius: Optional[int] = 50

    # Text/Label
    position: Optional[List[int]] = None  # [x, y]
    text: Optional[str] = None
    font_size: Optional[int] = 32

    # Highlight box
    top_left: Optional[List[int]] = None  # [x, y]
    bottom_right: Optional[List[int]] = None  # [x, y]

    # Common styling
    color: Optional[str] = "#FF0000"
    thickness: Optional[int] = 3
    pulsing: Optional[bool] = False
    animated: Optional[bool] = False
    label: Optional[str] = None
    background: Optional[str] = None
    background_opacity: Optional[float] = 0.7


class FormAnnotationsRequest(BaseModel):
    """
    Request model for form annotations.

    Adds arrows, circles, text labels, and highlight boxes to videos
    for exercise form instruction.
    """
    video_url: str
    annotations: List[AnnotationItem]
    slow_motion_segments: Optional[List[Dict[str, Any]]] = None
    preserve_audio: Optional[bool] = True


class ExerciseRecognitionRequest(BaseModel):
    """
    Request model for exercise recognition.

    Detects exercise type from video using pose estimation.
    """
    video_url: str
    min_confidence: Optional[float] = 0.7
    enable_rep_counting: Optional[bool] = True
    enable_form_analysis: Optional[bool] = True
    sample_interval: Optional[int] = 5  # Process every Nth frame


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """API health check and info."""
    return {
        "name": "Fitness Influencer Assistant API",
        "status": "active",
        "version": "2.0.0",
        "ai_providers": {
            "anthropic": bool(os.getenv('ANTHROPIC_API_KEY')),
            "xai": bool(os.getenv('XAI_API_KEY')),
            "shotstack": bool(os.getenv('SHOTSTACK_API_KEY'))
        },
        "endpoints": {
            "ai_chat": "/api/ai/chat",
            "video_edit": "/api/video/edit",
            "video_generate": "/api/video/generate (hybrid: MoviePy free → Creatomate paid)",
            "video_stats": "/api/video/stats",
            "video_providers": "/api/video/providers",
            "create_graphic": "/api/graphics/create",
            "email_digest": "/api/email/digest",
            "revenue_report": "/api/analytics/revenue",
            "generate_image": "/api/images/generate"
        },
        "v2_endpoints": {
            "job_submit": "/api/jobs/submit",
            "job_status": "/api/jobs/{job_id}/status",
            "job_cancel": "/api/jobs/{job_id}/cancel",
            "job_list": "/api/jobs",
            "video_caption": "/api/video/caption",
            "video_reframe": "/api/video/reframe",
            "video_export": "/api/video/export",
            "video_export_batch": "/api/video/export/batch",
            "video_export_platforms": "/api/video/export/platforms",
            "video_remove_fillers": "/api/video/remove-fillers",
            "video_detect_fillers": "/api/video/detect-fillers",
            "video_analyze": "/api/video/analyze",
            "video_viral_moments": "/api/video/viral-moments",
            "video_analyze_hook": "/api/video/analyze-hook",
            "video_predict_retention": "/api/video/predict-retention",
            "video_workout_overlay": "/api/video/add-workout-overlay",
            "video_form_annotations": "/api/video/add-form-annotations",
            "video_detect_exercise": "/api/video/detect-exercise",
            "content_metadata": "/api/content/metadata",
            "quota_status": "/api/quota/status",
            "quota_tiers": "/api/quota/tiers",
            "transcription": "/api/transcription"
        }
    }


# ============================================================================
# Background Job Endpoints (v2.0)
# ============================================================================

@app.post("/api/jobs/submit", response_model=JobSubmitResponse)
async def submit_job(request: JobSubmitRequest):
    """
    Submit a background job for async processing.

    Supported job types:
    - video_caption: Add captions to video
    - video_filler_removal: Remove filler words
    - video_reframe: Auto-reframe for different aspect ratios
    - video_export: Multi-platform export
    - video_jumpcut: Remove silence (jump cuts)
    - long_to_shorts: Extract clips from long-form
    - image_generation: Generate AI images
    - transcription: Transcribe video/audio

    Returns job_id for polling status.
    """
    from task_queue import get_queue, JobType

    queue = get_queue()

    # Validate job type
    valid_types = [t.value for t in JobType]
    if request.job_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid job_type. Must be one of: {valid_types}"
        )

    result = queue.submit_job(
        job_type=request.job_type,
        params=request.params,
        user_id=request.user_id,
        priority=request.priority or 5
    )

    return JobSubmitResponse(
        job_id=result.job_id,
        status=result.status,
        job_type=result.job_type,
        created_at=result.created_at,
        estimated_time=result.estimated_time,
        poll_url=f"/api/jobs/{result.job_id}/status"
    )


@app.get("/api/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get the status of a background job.

    Poll this endpoint until status is 'complete' or 'failed'.
    """
    from task_queue import get_queue

    queue = get_queue()
    status = queue.get_status(job_id)

    if not status:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=status.job_id,
        status=status.status,
        progress=status.progress,
        estimated_remaining=status.estimated_remaining,
        result=status.result,
        error=status.error
    )


@app.post("/api/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """
    Cancel a queued job.

    Only queued jobs can be cancelled. Processing jobs cannot be cancelled.
    """
    from task_queue import get_queue

    queue = get_queue()
    success = queue.cancel_job(job_id)

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Job not found or cannot be cancelled (may be processing)"
        )

    return {"status": "cancelled", "job_id": job_id}


@app.get("/api/jobs")
async def list_jobs(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """
    List background jobs with optional filtering.

    Query params:
    - user_id: Filter by user
    - status: Filter by status (queued, processing, complete, failed, cancelled)
    - limit: Max jobs to return (default 50)
    """
    from task_queue import get_queue

    queue = get_queue()
    jobs = queue.list_jobs(user_id=user_id, status=status, limit=limit)

    return {"jobs": jobs, "count": len(jobs)}


@app.post("/api/video/caption")
async def caption_video(request: Request, body: VideoCaptionRequest):
    """
    Add captions to a video (async).

    Submits job to background queue and returns job_id for polling.

    Supports full customization:
    - Position: 'top', 'center', 'bottom' with optional pixel offset (e.g., 'bottom+20')
    - Font: custom_font (24-72pt), font_size
    - Colors: font_color, outline_color, shadow_color, highlight_color (hex or named)
    - Outline: outline_width (0-5px)
    - Shadow: shadow_offset (0-10px)
    - Background: background_color, background_opacity (0-1)

    Returns job_id for async processing. Completed job returns:
    - video_url: URL of captioned video
    - srt_url: URL of SRT subtitle file
    """
    from backend.caption_styles import validate_custom_style, normalize_style_params
    from backend.task_queue import get_queue, JobType

    # Check quota
    await check_quota(request, "caption_jobs")

    # Build params dict for validation
    params = body.model_dump()

    # Validate custom style parameters if any custom settings provided
    has_custom = any([
        body.custom_font, body.font_size, body.font_color, body.outline_color,
        body.outline_width is not None, body.shadow_color, body.shadow_offset is not None,
        body.highlight_color, body.background_color, body.background_opacity is not None
    ])

    if has_custom:
        # Build style dict for validation
        style_dict = {
            "font_size": body.font_size or 48,
            "font_color": body.font_color,
            "outline_color": body.outline_color,
            "outline_width": body.outline_width or 2,
            "shadow_color": body.shadow_color,
            "shadow_offset": body.shadow_offset or 0,
            "highlight_color": body.highlight_color,
            "background_color": body.background_color,
            "background_opacity": body.background_opacity or 0.0,
            "position": body.position
        }

        # Validate
        errors = validate_custom_style(style_dict, min_font_size=24, max_font_size=72)
        if errors:
            raise HTTPException(
                status_code=400,
                detail={"errors": errors, "message": "Invalid caption style parameters"}
            )

        # Normalize colors (convert named colors to hex)
        normalized = normalize_style_params(style_dict)
        params.update(normalized)

    queue = get_queue()
    result = queue.submit_job(
        job_type=JobType.VIDEO_CAPTION.value,
        params=params
    )

    return {
        "job_id": result.job_id,
        "status": result.status,
        "estimated_time": result.estimated_time,
        "style": body.style,
        "position": body.position,
        "word_highlight": body.word_highlight,
        "has_custom_style": has_custom,
        "poll_url": f"/api/jobs/{result.job_id}/status",
        "message": "Caption job submitted. Poll the status URL for progress."
    }


@app.post("/api/video/reframe")
async def reframe_video(request: VideoReframeRequest):
    """
    Auto-reframe video for different aspect ratios (async).

    Uses face/body tracking to keep subjects centered.
    """
    from task_queue import get_queue, JobType

    queue = get_queue()
    result = queue.submit_job(
        job_type=JobType.VIDEO_REFRAME.value,
        params=request.model_dump()
    )

    return {
        "job_id": result.job_id,
        "status": result.status,
        "estimated_time": result.estimated_time,
        "poll_url": f"/api/jobs/{result.job_id}/status"
    }


@app.post("/api/video/export")
async def export_video(request: VideoExportRequest):
    """
    Export video to multiple platforms (async).

    Creates optimized versions for TikTok, Instagram, YouTube Shorts, etc.
    Includes platform-specific encoding and optional metadata generation.

    Platforms supported:
    - tiktok, tt: TikTok (9:16, 30fps, 3Mbps)
    - instagram_reels, ig, reels: Instagram Reels (9:16, 30fps, 4Mbps)
    - instagram_feed, ig_feed: Instagram Feed (4:5, 30fps, 3.5Mbps)
    - instagram_story, ig_story: Instagram Story (9:16, 30fps, 3Mbps)
    - youtube_shorts, yt, shorts: YouTube Shorts (9:16, 60fps, 10Mbps)
    - youtube_long, yt_long: YouTube Long-form (16:9, 60fps, 12Mbps)
    - linkedin, li: LinkedIn (9:16, 30fps, 5Mbps)
    - twitter, x: Twitter/X (16:9, 30fps, 5Mbps)
    - facebook_reels, fb: Facebook Reels (9:16, 30fps, 4Mbps)
    """
    from backend.task_queue import get_queue, JobType

    queue = get_queue()
    result = queue.submit_job(
        job_type=JobType.VIDEO_EXPORT.value,
        params=request.model_dump()
    )

    return {
        "job_id": result.job_id,
        "status": result.status,
        "estimated_time": result.estimated_time,
        "platforms": request.platforms,
        "poll_url": f"/api/jobs/{result.job_id}/status"
    }


@app.get("/api/video/export/platforms")
async def list_export_platforms():
    """
    List all supported export platforms with their specifications.

    Returns resolution, aspect ratio, duration limits, codec settings, etc.
    """
    from backend.platform_exporter import list_platforms

    return {
        "platforms": list_platforms()
    }


@app.get("/api/video/export/platforms/{platform}")
async def get_platform_spec(platform: str):
    """
    Get detailed specification for a specific platform.
    """
    from backend.platform_exporter import parse_platform, get_platform_spec

    try:
        platform_enum = parse_platform(platform)
        spec = get_platform_spec(platform_enum)
        return {"platform": platform, "spec": spec}
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown platform: {platform}. Use /api/video/export/platforms to list valid platforms."
        )


@app.post("/api/video/export/batch")
async def batch_export_videos(request: BatchExportRequest):
    """
    Batch export multiple videos to multiple platforms.

    Submits separate jobs for each video and returns all job IDs.
    Use /api/jobs/{job_id}/status to poll individual job status.
    """
    from backend.task_queue import get_queue, JobType

    queue = get_queue()
    jobs = []

    for video in request.videos:
        params = {
            "video_url": video.get("video_url"),
            "platforms": request.platforms,
            "generate_descriptions": request.generate_descriptions,
            "transcription_text": video.get("transcription_text", ""),
            "category": video.get("category"),
            "webhook_url": request.webhook_url
        }

        result = queue.submit_job(
            job_type=JobType.VIDEO_EXPORT.value,
            params=params
        )

        jobs.append({
            "job_id": result.job_id,
            "video_url": video.get("video_url"),
            "status": result.status,
            "estimated_time": result.estimated_time,
            "poll_url": f"/api/jobs/{result.job_id}/status"
        })

    return {
        "total_jobs": len(jobs),
        "platforms": request.platforms,
        "jobs": jobs
    }


@app.post("/api/content/metadata")
@limiter.limit("60/minute")
async def generate_content_metadata(
    request: Request,
    transcription_text: str = Form(...),
    platform: str = Form("tiktok"),
    category: Optional[str] = Form(None),
    hashtag_count: Optional[int] = Form(None)
):
    """
    Generate platform-optimized metadata (hashtags, descriptions) from transcription.

    Uses AI to extract keywords and generate engaging descriptions.
    """
    from backend.content_metadata import generate_metadata
    from backend.platform_exporter import parse_platform

    try:
        platform_enum = parse_platform(platform)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown platform: {platform}"
        )

    metadata = await generate_metadata(
        transcription_text=transcription_text,
        platform=platform_enum,
        category=category,
        hashtag_count=hashtag_count
    )

    return metadata.to_dict()


# ============================================================================
# Content Calendar & Strategy Endpoints
# ============================================================================

@app.get("/api/content/calendar/today")
@limiter.limit("120/minute")
async def get_today_content(request: Request):
    """
    Get content strategy for today.

    Returns the recommended topic, hook, format, and filming tips for today.
    Use this to know what content to film right now.
    """
    from backend.content_calendar import get_today_content, generate_caption

    content = get_today_content()
    if not content:
        raise HTTPException(status_code=404, detail="No content strategy for today")

    # Also include pre-generated captions
    captions = generate_caption(content.day.lower())

    return {
        "day": content.day,
        "theme": content.theme,
        "topic": content.topic,
        "hook": content.hook,
        "format": content.format,
        "viral_angle": content.viral_angle,
        "filming_tips": content.filming_tips,
        "hashtag_strategy": content.hashtag_strategy,
        "captions": captions
    }


@app.get("/api/content/calendar/{day}")
@limiter.limit("120/minute")
async def get_day_content(request: Request, day: str):
    """
    Get content strategy for a specific day.

    Args:
        day: Day of week (monday, tuesday, etc.)

    Returns the recommended topic, hook, format, and filming tips.
    """
    from backend.content_calendar import get_day_content, generate_caption

    content = get_day_content(day)
    if not content:
        valid_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        raise HTTPException(
            status_code=404,
            detail=f"No content strategy for '{day}'. Valid days: {', '.join(valid_days)}"
        )

    captions = generate_caption(day.lower())

    return {
        "day": content.day,
        "theme": content.theme,
        "topic": content.topic,
        "hook": content.hook,
        "format": content.format,
        "viral_angle": content.viral_angle,
        "filming_tips": content.filming_tips,
        "hashtag_strategy": content.hashtag_strategy,
        "captions": captions
    }


@app.get("/api/content/calendar/week/plan")
@limiter.limit("60/minute")
async def get_weekly_plan(request: Request, start_date: Optional[str] = None):
    """
    Get full weekly content plan.

    Args:
        start_date: Start date (YYYY-MM-DD), defaults to next Monday

    Returns complete weekly content plan with all days, themes, and estimated hours.
    """
    from backend.content_calendar import get_weekly_plan
    from datetime import datetime

    parsed_date = None
    if start_date:
        try:
            parsed_date = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format: {start_date}. Use YYYY-MM-DD"
            )

    plan = get_weekly_plan(parsed_date)

    return {
        "week_start": plan.week_start,
        "week_end": plan.week_end,
        "total_content_pieces": plan.total_pieces,
        "estimated_hours": plan.estimated_hours,
        "days": [
            {
                "day": d.day,
                "theme": d.theme,
                "topic": d.topic,
                "hook": d.hook,
                "format": d.format,
                "viral_angle": d.viral_angle,
                "filming_tips": d.filming_tips,
                "hashtag_strategy": d.hashtag_strategy
            }
            for d in plan.days
        ]
    }


@app.get("/api/content/calendar/captions/{day}")
@limiter.limit("120/minute")
async def generate_captions(request: Request, day: str, custom_topic: Optional[str] = None):
    """
    Generate platform-specific captions for a day's content.

    Args:
        day: Day of week
        custom_topic: Optional custom topic to override the default

    Returns captions formatted for TikTok, Instagram Reel, YouTube Short, etc.
    """
    from backend.content_calendar import generate_caption

    captions = generate_caption(day, custom_topic)

    if "error" in captions:
        valid_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        raise HTTPException(
            status_code=404,
            detail=f"No content strategy for '{day}'. Valid days: {', '.join(valid_days)}"
        )

    return captions


@app.post("/api/video/remove-fillers")
async def remove_fillers(request: FillerRemovalRequest):
    """
    Remove filler words from video (async).

    Detects and removes um, uh, like, you know, etc. with smooth transitions.
    """
    from task_queue import get_queue, JobType

    queue = get_queue()
    result = queue.submit_job(
        job_type=JobType.VIDEO_FILLER_REMOVAL.value,
        params=request.model_dump()
    )

    return {
        "job_id": result.job_id,
        "status": result.status,
        "estimated_time": result.estimated_time,
        "sensitivity": request.sensitivity,
        "poll_url": f"/api/jobs/{result.job_id}/status"
    }


@app.post("/api/video/detect-fillers")
@limiter.limit("30/minute")
async def detect_fillers_endpoint(request: Request, body: FillerDetectionRequest):
    """
    Detect filler words in video or audio (analysis only).

    Returns detailed analysis of filler words including:
    - Each filler word with timestamp and confidence
    - Filler clusters (consecutive fillers)
    - Summary statistics (filler %, count by category)
    - Removal segments for preview

    Sensitivity modes:
    - aggressive: Remove most potential fillers (confidence >= 0.5)
    - moderate: Balanced approach (confidence >= 0.7)
    - conservative: Only high-confidence fillers (confidence >= 0.85)
    """
    from backend.transcription import transcribe_video, transcribe_audio, WordTimestamp as TranscriptionWord
    from backend.filler_detector import (
        detect_fillers,
        detect_fillers_with_sensitivity,
        get_removal_segments,
        WordTimestamp,
        SENSITIVITY_PRESETS
    )

    # Validate input
    if not body.video_url and not body.audio_url:
        raise HTTPException(
            status_code=400,
            detail="Either video_url or audio_url is required"
        )

    # Check quota
    if not await check_quota(request, "caption"):
        raise HTTPException(
            status_code=429,
            detail="Quota exceeded for caption/transcription operations"
        )

    try:
        # Step 1: Transcribe to get word-level timestamps
        if body.video_url:
            transcription = await transcribe_video(
                video_url=body.video_url,
                language=body.language or "en"
            )
        else:
            transcription = await transcribe_audio(
                audio_url=body.audio_url,
                language=body.language or "en"
            )

        if not transcription.words:
            return {
                "success": True,
                "message": "No words detected in audio",
                "fillers": [],
                "clusters": [],
                "statistics": {
                    "total_filler_count": 0,
                    "filler_percentage": 0,
                    "words_analyzed": 0
                }
            }

        # Convert transcription words to filler detector format
        words = [
            WordTimestamp(
                word=w.word,
                start=w.start,
                end=w.end,
                confidence=w.confidence
            )
            for w in transcription.words
        ]

        # Step 2: Detect fillers
        if body.confidence_threshold is not None:
            # Use custom threshold
            result = detect_fillers(
                words=words,
                confidence_threshold=max(0.5, min(0.95, body.confidence_threshold))
            )
        else:
            # Use sensitivity preset
            result = detect_fillers_with_sensitivity(
                words=words,
                sensitivity=body.sensitivity or "moderate"
            )

        # Step 3: Get removal segments for preview
        removal_segments = get_removal_segments(
            result,
            include_clusters=body.include_clusters
        )

        return {
            "success": True,
            "sensitivity": body.sensitivity,
            "confidence_threshold": body.confidence_threshold or SENSITIVITY_PRESETS.get(
                body.sensitivity, SENSITIVITY_PRESETS["moderate"]
            )["confidence_threshold"],
            "fillers": [f.to_dict() for f in result.fillers if f.is_filler],
            "all_detected": [f.to_dict() for f in result.fillers],  # Includes below-threshold
            "clusters": [c.to_dict() for c in result.clusters],
            "removal_segments": [
                {"start": s, "end": e, "duration": round(e - s, 2)}
                for s, e in removal_segments
            ],
            "statistics": {
                "total_filler_count": result.total_filler_count,
                "filler_duration": round(result.filler_duration, 2),
                "total_duration": round(result.total_duration, 2),
                "filler_percentage": round(result.filler_percentage, 2),
                "words_analyzed": result.words_analyzed,
                "removal_time_saved": round(sum(e - s for s, e in removal_segments), 2)
            },
            "summary": result.to_dict()["summary"],
            "transcription": {
                "text": transcription.text,
                "language": transcription.language,
                "duration": transcription.duration
            }
        }

    except Exception as e:
        logger.error(f"Filler detection failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Filler detection failed: {str(e)}"
        )


# ============================================================================
# Video Analysis Endpoints (v2.0 - Phase 5)
# ============================================================================

@app.post("/api/video/analyze")
@limiter.limit("10/minute")
async def analyze_video_endpoint(request: Request, body: VideoAnalyzeRequest):
    """
    Analyze a long-form video for key moments and potential clips.

    Features:
    - Audio energy analysis (peaks and valleys)
    - Motion/action intensity detection
    - Scene change detection
    - Keyword extraction from transcription
    - Scored segments ranked by viral potential

    Optimized for 10-60 minute videos with < 2 minute processing.

    Returns:
    - top_segments: Best clips ranked by score (0-100)
    - timeline: Audio peaks, scene changes, keyword clusters
    - summary: Overall statistics

    Use cases:
    - Long-to-shorts extraction
    - Viral moment detection
    - Content repurposing
    """
    from backend.video_analyzer import (
        analyze_video,
        AnalysisConfig,
        get_video_duration
    )
    import tempfile
    import urllib.request
    import httpx

    # Check quota
    if not await check_quota(request, "video"):
        raise HTTPException(
            status_code=429,
            detail="Quota exceeded for video operations"
        )

    try:
        # Download video if URL provided
        video_path = None
        cleanup_video = False

        if body.video_url.startswith("http"):
            # Download video to temp file
            temp_dir = tempfile.mkdtemp()
            video_path = f"{temp_dir}/video.mp4"
            cleanup_video = True

            logger.info(f"Downloading video for analysis: {body.video_url[:50]}...")

            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.get(body.video_url, follow_redirects=True)
                response.raise_for_status()

                with open(video_path, 'wb') as f:
                    f.write(response.content)

        else:
            video_path = body.video_url

        # Check video exists
        from pathlib import Path
        if not Path(video_path).exists():
            raise HTTPException(
                status_code=404,
                detail=f"Video file not found: {video_path}"
            )

        # Get duration first
        duration = await get_video_duration(video_path)
        if duration <= 0:
            raise HTTPException(
                status_code=400,
                detail="Could not determine video duration"
            )

        # Build analysis config
        config = AnalysisConfig(
            analyze_audio=body.analyze_audio,
            analyze_motion=body.analyze_motion,
            detect_scenes=body.detect_scenes,
            extract_keywords=body.extract_keywords,
            min_segment_duration=body.min_segment_duration,
            max_segment_duration=body.max_segment_duration
        )

        # Prepare transcription data if provided
        transcription_result = None
        if body.transcription_text or body.word_timestamps:
            transcription_result = {
                "text": body.transcription_text or "",
                "words": body.word_timestamps or []
            }

        # Run analysis
        result = await analyze_video(
            video_path=video_path,
            transcription_result=transcription_result,
            config=config
        )

        # Cleanup temp video
        if cleanup_video and video_path:
            try:
                Path(video_path).unlink(missing_ok=True)
                Path(video_path).parent.rmdir()
            except Exception:
                pass

        # Build response with limited top segments
        response_data = result.to_dict()

        # Limit top_segments to requested count
        if len(response_data.get("top_segments", [])) > body.top_segments_count:
            response_data["top_segments"] = response_data["top_segments"][:body.top_segments_count]

        return {
            "success": True,
            **response_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Video analysis failed: {str(e)}"
        )


@app.get("/api/video/analyze/segment-types")
async def get_segment_types():
    """
    Get available segment types for video analysis.

    Segment types help categorize moments in videos.
    """
    from backend.video_analyzer import SegmentType

    return {
        "segment_types": [
            {"value": st.value, "description": get_segment_type_description(st)}
            for st in SegmentType
        ]
    }


def get_segment_type_description(segment_type) -> str:
    """Get human-readable description for segment type."""
    from backend.video_analyzer import SegmentType

    descriptions = {
        SegmentType.INTRO: "Opening segment, typically lower energy",
        SegmentType.MAIN_CONTENT: "Primary content delivery",
        SegmentType.DEMONSTRATION: "Exercise or technique demonstration",
        SegmentType.TRANSITION: "Transition between topics",
        SegmentType.CLIMAX: "High energy moment, potential viral clip",
        SegmentType.CONCLUSION: "Closing segment",
        SegmentType.UNKNOWN: "Unclassified segment"
    }
    return descriptions.get(segment_type, "Unknown segment type")


@app.post("/api/video/viral-moments")
@limiter.limit("10/minute")
async def detect_viral_moments_endpoint(request: Request, body: ViralDetectionRequest):
    """
    Detect viral moments in a video for content repurposing.

    Identifies the best clips from long-form content using:
    - Hook strength analysis (first 3 seconds impact)
    - Audio energy levels
    - Visual variety (scene changes, motion)
    - Keyword density
    - Emotional marker detection
    - Fitness-specific content boosters

    Returns scored moments (0-100) with categories:
    - hook: Strong opening hook
    - transformation: Before/after, progress content
    - demonstration: Exercise/technique demos
    - climax: High energy moments
    - educational: Teaching content

    Use cases:
    - Long-to-shorts extraction
    - Highlight reel creation
    - Content repurposing
    """
    from backend.viral_detector import (
        detect_viral_moments,
        ViralConfig
    )
    import tempfile
    import httpx

    # Check quota
    if not await check_quota(request, "video"):
        raise HTTPException(
            status_code=429,
            detail="Quota exceeded for video operations"
        )

    try:
        # Download video if URL provided
        video_path = None
        cleanup_video = False

        if body.video_url.startswith("http"):
            # Download video to temp file
            temp_dir = tempfile.mkdtemp()
            video_path = f"{temp_dir}/video.mp4"
            cleanup_video = True

            logger.info(f"Downloading video for viral detection: {body.video_url[:50]}...")

            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.get(body.video_url, follow_redirects=True)
                response.raise_for_status()

                with open(video_path, 'wb') as f:
                    f.write(response.content)

        else:
            video_path = body.video_url

        # Check video exists
        from pathlib import Path
        if not Path(video_path).exists():
            raise HTTPException(
                status_code=404,
                detail=f"Video file not found: {video_path}"
            )

        # Build config
        config = ViralConfig(
            min_duration=body.min_duration,
            max_duration=body.max_duration,
            top_count=body.top_count,
            min_score=body.min_score,
            preserve_sentences=body.preserve_sentences,
            weights={
                "hook_strength": body.weight_hook,
                "audio_energy": body.weight_audio,
                "visual_variety": body.weight_visual,
                "keyword_density": body.weight_keywords,
                "emotional_markers": body.weight_emotion,
                "fitness_relevance": body.weight_fitness
            }
        )

        # Prepare transcription data if provided
        transcription_result = None
        if body.transcription_text or body.word_timestamps:
            transcription_result = {
                "text": body.transcription_text or "",
                "words": body.word_timestamps or []
            }

        # Run viral detection
        result = await detect_viral_moments(
            video_path=video_path,
            transcription_result=transcription_result,
            config=config
        )

        # Cleanup temp video
        if cleanup_video and video_path:
            try:
                Path(video_path).unlink(missing_ok=True)
                Path(video_path).parent.rmdir()
            except Exception:
                pass

        return {
            "success": True,
            **result.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Viral detection failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Viral detection failed: {str(e)}"
        )


@app.get("/api/video/viral-moments/categories")
async def get_viral_categories():
    """
    Get available viral moment categories.

    Categories help identify the type of viral content.
    """
    from backend.viral_detector import ViralCategory

    category_descriptions = {
        ViralCategory.HOOK: "Strong opening hook that grabs attention",
        ViralCategory.TRANSFORMATION: "Before/after or progress content",
        ViralCategory.DEMONSTRATION: "Exercise or technique demonstration",
        ViralCategory.REACTION: "Emotional reaction shot",
        ViralCategory.CLIMAX: "Peak energy moment",
        ViralCategory.CONTROVERSY: "Contrarian or debate-worthy content",
        ViralCategory.EDUCATIONAL: "Teaching or informational moment",
        ViralCategory.INSPIRATIONAL: "Motivational content"
    }

    return {
        "categories": [
            {"value": cat.value, "description": desc}
            for cat, desc in category_descriptions.items()
        ]
    }


# ============================================================================
# Hook Analysis Endpoints (v2.0 - Phase 5)
# ============================================================================

@app.post("/api/video/analyze-hook")
@limiter.limit("20/minute")
async def analyze_hook_endpoint(request: Request, body: HookAnalysisRequest):
    """
    Analyze and optimize video hook (first 3 seconds).

    Returns:
    - Hook score (0-100) with component breakdown
    - Grade (A-F) based on hook effectiveness
    - Improvement suggestions prioritized by impact
    - Alternative hook variants with text overlays
    - Platform-specific optimization tips

    Scoring components:
    - action: Movement and activity in first frame
    - curiosity: Curiosity gap, question, mystery
    - emotion: Emotional impact and connection
    - audio_impact: Sound, music, voice effectiveness
    - visual_variety: Scene interest and contrast
    - text_hook: Text overlay effectiveness

    Use cases:
    - Pre-publish hook validation
    - A/B test variant generation
    - Hook improvement recommendations
    """
    from backend.hook_analyzer import (
        analyze_hook,
        HookConfig,
        PLATFORM_HOOK_TIPS
    )
    import tempfile
    import httpx

    # Check quota
    if not await check_quota(request, "video"):
        raise HTTPException(
            status_code=429,
            detail="Quota exceeded for video operations"
        )

    try:
        # Download video if URL provided
        video_path = None
        cleanup_video = False

        if body.video_url.startswith("http"):
            # Download video to temp file
            temp_dir = tempfile.mkdtemp()
            video_path = f"{temp_dir}/video.mp4"
            cleanup_video = True

            logger.info(f"Downloading video for hook analysis: {body.video_url[:50]}...")

            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.get(body.video_url, follow_redirects=True)
                response.raise_for_status()

                with open(video_path, 'wb') as f:
                    f.write(response.content)

        else:
            video_path = body.video_url

        # Check video exists
        from pathlib import Path
        if not Path(video_path).exists():
            raise HTTPException(
                status_code=404,
                detail=f"Video file not found: {video_path}"
            )

        # Build config
        config = HookConfig(
            hook_duration=body.hook_duration,
            platform=body.platform,
            generate_variants=body.generate_variants,
            variant_count=body.variant_count,
            include_ab_test_setup=body.include_ab_test_setup
        )

        # Prepare transcription data if provided
        transcription_result = None
        if body.transcription_text or body.word_timestamps:
            transcription_result = {
                "text": body.transcription_text or "",
                "words": body.word_timestamps or []
            }

        # Run hook analysis
        result = await analyze_hook(
            video_path=video_path,
            transcription_result=transcription_result,
            config=config
        )

        # Cleanup temp video
        if cleanup_video and video_path:
            try:
                Path(video_path).unlink(missing_ok=True)
                Path(video_path).parent.rmdir()
            except Exception:
                pass

        # Add platform tips to response
        platform_tips = PLATFORM_HOOK_TIPS.get(body.platform, PLATFORM_HOOK_TIPS["tiktok"])

        return {
            "success": True,
            "platform": body.platform,
            "platform_tips": platform_tips,
            **result.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hook analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Hook analysis failed: {str(e)}"
        )


@app.get("/api/video/analyze-hook/platforms")
async def get_hook_platforms():
    """
    Get available platforms for hook optimization.

    Each platform has different hook best practices.
    """
    from backend.hook_analyzer import PLATFORM_HOOK_TIPS

    return {
        "platforms": [
            {
                "value": platform,
                "ideal_duration": tips["ideal_duration"],
                "text_overlay_recommended": tips["text_overlay"],
                "music_important": tips["music_important"],
                "face_visible_recommended": tips["face_visible"],
                "tips": tips["tips"]
            }
            for platform, tips in PLATFORM_HOOK_TIPS.items()
        ]
    }


@app.get("/api/video/analyze-hook/improvement-types")
async def get_hook_improvement_types():
    """
    Get available hook improvement types.

    Improvement types categorize the suggested changes.
    """
    from backend.hook_analyzer import HookImprovementType

    improvement_descriptions = {
        HookImprovementType.REORDER_SHOTS: "Rearrange shots for better pacing",
        HookImprovementType.ADD_TEXT_OVERLAY: "Add text hook overlay in first 0.5 seconds",
        HookImprovementType.CHANGE_MUSIC: "Use trending or more impactful music",
        HookImprovementType.ADD_VISUAL_EFFECT: "Add zoom, flash, or motion effect",
        HookImprovementType.CHANGE_OPENING_SHOT: "Replace opening shot with more action",
        HookImprovementType.ADD_PATTERN_INTERRUPT: "Start with unexpected element",
        HookImprovementType.INCREASE_ENERGY: "Boost energy in voice or visuals",
        HookImprovementType.ADD_CURIOSITY_GAP: "Create mystery or question"
    }

    return {
        "improvement_types": [
            {"value": imp_type.value, "description": desc}
            for imp_type, desc in improvement_descriptions.items()
        ]
    }


# ============================================================================
# Retention Prediction Endpoints (v2.0 - Phase 5)
# ============================================================================

@app.post("/api/video/predict-retention")
@limiter.limit("10/minute")
async def predict_retention_endpoint(request: Request, body: RetentionPredictionRequest):
    """
    Predict audience retention curve before publishing.

    Returns:
    - Retention curve (% at each timestamp)
    - Cliff moments (>10% sudden drops)
    - Platform benchmark comparison
    - Improvement suggestions for each cliff
    - Overall grade (A-F)

    Platform benchmarks:
    - TikTok: 50% = good, 60% = excellent
    - Instagram Reels: 40% = good, 55% = excellent
    - YouTube Shorts: 45% = good, 55% = excellent
    - YouTube: 40% = good, 50% = excellent

    Use cases:
    - Pre-publish quality check
    - Identify weak points for editing
    - Compare against platform standards
    - A/B test validation
    """
    from backend.retention_predictor import (
        predict_retention,
        RetentionConfig
    )
    import tempfile
    import httpx

    # Check quota
    if not await check_quota(request, "video"):
        raise HTTPException(
            status_code=429,
            detail="Quota exceeded for video operations"
        )

    try:
        # Download video if URL provided
        video_path = None
        cleanup_video = False

        if body.video_url.startswith("http"):
            # Download video to temp file
            temp_dir = tempfile.mkdtemp()
            video_path = f"{temp_dir}/video.mp4"
            cleanup_video = True

            logger.info(f"Downloading video for retention prediction: {body.video_url[:50]}...")

            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.get(body.video_url, follow_redirects=True)
                response.raise_for_status()

                with open(video_path, 'wb') as f:
                    f.write(response.content)

        else:
            video_path = body.video_url

        # Check video exists
        from pathlib import Path
        if not Path(video_path).exists():
            raise HTTPException(
                status_code=404,
                detail=f"Video file not found: {video_path}"
            )

        # Build config
        config = RetentionConfig(
            platform=body.platform,
            sample_interval=body.sample_interval,
            include_hook_analysis=body.include_hook_analysis,
            cliff_threshold=body.cliff_threshold,
            generate_suggestions=body.generate_suggestions
        )

        # Prepare transcription data if provided
        transcription_result = None
        if body.transcription_text or body.word_timestamps:
            transcription_result = {
                "text": body.transcription_text or "",
                "words": body.word_timestamps or []
            }

        # Run retention prediction
        result = await predict_retention(
            video_path=video_path,
            transcription_result=transcription_result,
            config=config
        )

        # Cleanup temp video
        if cleanup_video and video_path:
            try:
                Path(video_path).unlink(missing_ok=True)
                Path(video_path).parent.rmdir()
            except Exception:
                pass

        return {
            "success": True,
            **result.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Retention prediction failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Retention prediction failed: {str(e)}"
        )


@app.get("/api/video/predict-retention/benchmarks")
async def get_retention_benchmarks():
    """
    Get platform retention benchmarks.

    Shows what retention percentages are considered good/excellent for each platform.
    """
    from backend.retention_predictor import get_platform_benchmarks

    return {
        "benchmarks": get_platform_benchmarks()
    }


@app.get("/api/video/predict-retention/improvement-types")
async def get_retention_improvement_types():
    """
    Get available retention improvement suggestion types.

    Each type includes description and specific suggestions.
    """
    from backend.retention_predictor import get_improvement_types

    return {
        "improvement_types": get_improvement_types()
    }


# ============================================================================
# Workout Overlay Endpoints (v2.0 - Phase 6)
# ============================================================================

@app.post("/api/video/add-workout-overlay")
@limiter.limit("10/minute")
async def add_workout_overlay_endpoint(request: Request, body: WorkoutOverlayRequest):
    """
    Add workout timer overlay to video.

    Timer types:
    - countdown: Count down from duration to zero
    - countup: Count up from zero
    - interval: Alternating work/rest intervals (HIIT style)
    - rep_counter: Display rep count

    Presets:
    - hiit: 45s work / 15s rest
    - tabata: 20s work / 10s rest x 8 rounds
    - emom: 50s work / 10s rest (Every Minute On the Minute)
    - strength: 45s work / 90s rest (longer rest for heavy lifts)
    - yoga: 30s hold / 5s transition
    - cardio: 30s on / 30s off
    - plank: 60s hold / 30s rest

    Styles: minimal, bold, neon, digital
    Positions: top_left, top_right, bottom_left, bottom_right, center
    """
    from backend.workout_overlays import (
        add_timer_overlay,
        TimerConfig,
        TimerType,
        OverlayPosition,
        OverlayStyle
    )
    import tempfile
    import httpx

    # Check quota
    if not await check_quota(request, "video"):
        raise HTTPException(
            status_code=429,
            detail="Quota exceeded for video operations"
        )

    try:
        # Download video if URL provided
        video_path = None
        cleanup_video = False

        if body.video_url.startswith("http"):
            # Download video to temp file
            temp_dir = tempfile.mkdtemp()
            video_path = f"{temp_dir}/video.mp4"
            cleanup_video = True

            logger.info(f"Downloading video for workout overlay: {body.video_url[:50]}...")

            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.get(body.video_url, follow_redirects=True)
                response.raise_for_status()

                with open(video_path, 'wb') as f:
                    f.write(response.content)

        else:
            video_path = body.video_url

        # Check video exists
        from pathlib import Path
        if not Path(video_path).exists():
            raise HTTPException(
                status_code=404,
                detail=f"Video file not found: {video_path}"
            )

        # Parse enums
        try:
            timer_type = TimerType(body.timer_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid timer_type: {body.timer_type}. Valid options: {[t.value for t in TimerType]}"
            )

        try:
            position = OverlayPosition(body.position)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid position: {body.position}. Valid options: {[p.value for p in OverlayPosition]}"
            )

        try:
            style = OverlayStyle(body.style)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid style: {body.style}. Valid options: {[s.value for s in OverlayStyle]}"
            )

        # Build config
        config = TimerConfig(
            timer_type=timer_type,
            preset=body.preset,
            duration=body.duration,
            work_duration=body.work_duration,
            rest_duration=body.rest_duration,
            rounds=body.rounds,
            total_reps=body.total_reps,
            auto_increment=body.auto_increment,
            position=position,
            style=style,
            show_round_number=body.show_round_number,
            show_work_rest_label=body.show_work_rest_label,
            enable_audio_cues=body.enable_audio_cues
        )

        # Add overlay
        result = await add_timer_overlay(
            video_path=video_path,
            config=config
        )

        # Cleanup temp video (keep output)
        if cleanup_video and video_path:
            try:
                Path(video_path).unlink(missing_ok=True)
            except Exception:
                pass

        return {
            "success": result.success,
            **result.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workout overlay failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Workout overlay failed: {str(e)}"
        )


@app.get("/api/video/add-workout-overlay/presets")
async def get_workout_presets():
    """
    Get available workout timer presets.

    Each preset includes work/rest durations and total rounds.
    """
    from backend.workout_overlays import get_presets

    return {
        "presets": get_presets()
    }


@app.get("/api/video/add-workout-overlay/styles")
async def get_workout_overlay_styles():
    """
    Get available overlay styles.

    Each style includes font, colors, and visual settings.
    """
    from backend.workout_overlays import get_styles

    return {
        "styles": get_styles()
    }


@app.get("/api/video/add-workout-overlay/timer-types")
async def get_workout_timer_types():
    """
    Get available timer types.

    Timer types: countdown, countup, interval, rep_counter
    """
    from backend.workout_overlays import get_timer_types

    return {
        "timer_types": get_timer_types()
    }


# ============================================================================
# Form Annotation Endpoints (v2.0 - Phase 6)
# ============================================================================

@app.post("/api/video/add-form-annotations")
@limiter.limit("10/minute")
async def add_form_annotations_endpoint(request: Request, body: FormAnnotationsRequest):
    """
    Add form annotations to video for exercise instruction.

    Annotation types:
    - arrow: Points from start to end coordinates, with optional label
    - circle: Highlights an area (can be pulsing)
    - line: Straight line between two points
    - text: Floating text label with optional background
    - highlight_box: Rectangular highlight region

    Each annotation can have:
    - start_time/end_time: When to show the annotation
    - color: Hex color code
    - pulsing/animated: Animation effects
    - label: Associated text label
    """
    from backend.form_annotations import (
        add_annotations,
        AnnotationConfig,
        Arrow,
        Circle,
        Line,
        TextLabel,
        HighlightBox
    )
    import tempfile
    import httpx

    # Check quota
    if not await check_quota(request, "video"):
        raise HTTPException(
            status_code=429,
            detail="Quota exceeded for video operations"
        )

    try:
        # Download video if URL provided
        video_path = None
        cleanup_video = False

        if body.video_url.startswith("http"):
            temp_dir = tempfile.mkdtemp()
            video_path = f"{temp_dir}/video.mp4"
            cleanup_video = True

            logger.info(f"Downloading video for form annotations: {body.video_url[:50]}...")

            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.get(body.video_url, follow_redirects=True)
                response.raise_for_status()

                with open(video_path, 'wb') as f:
                    f.write(response.content)
        else:
            video_path = body.video_url

        from pathlib import Path
        if not Path(video_path).exists():
            raise HTTPException(
                status_code=404,
                detail=f"Video file not found: {video_path}"
            )

        # Convert annotation items to annotation objects
        annotations = []
        for item in body.annotations:
            if item.type == "arrow":
                if not item.start or not item.end:
                    continue
                annotations.append(Arrow(
                    start=tuple(item.start),
                    end=tuple(item.end),
                    color=item.color or "#FF0000",
                    thickness=item.thickness or 4,
                    animated=item.animated or False,
                    label=item.label,
                    start_time=item.start_time or 0,
                    end_time=item.end_time
                ))
            elif item.type == "circle":
                if not item.center:
                    continue
                annotations.append(Circle(
                    center=tuple(item.center),
                    radius=item.radius or 50,
                    color=item.color or "#00FF00",
                    thickness=item.thickness or 3,
                    pulsing=item.pulsing or False,
                    start_time=item.start_time or 0,
                    end_time=item.end_time
                ))
            elif item.type == "line":
                if not item.start or not item.end:
                    continue
                annotations.append(Line(
                    start=tuple(item.start),
                    end=tuple(item.end),
                    color=item.color or "#FFFF00",
                    thickness=item.thickness or 3,
                    start_time=item.start_time or 0,
                    end_time=item.end_time
                ))
            elif item.type == "text":
                if not item.position or not item.text:
                    continue
                annotations.append(TextLabel(
                    position=tuple(item.position),
                    text=item.text,
                    color=item.color or "#FFFFFF",
                    font_size=item.font_size or 32,
                    background=item.background,
                    background_opacity=item.background_opacity or 0.7,
                    start_time=item.start_time or 0,
                    end_time=item.end_time
                ))
            elif item.type == "highlight_box":
                if not item.top_left or not item.bottom_right:
                    continue
                annotations.append(HighlightBox(
                    top_left=tuple(item.top_left),
                    bottom_right=tuple(item.bottom_right),
                    color=item.color or "#FFFF00",
                    thickness=item.thickness or 3,
                    pulsing=item.pulsing or False,
                    start_time=item.start_time or 0,
                    end_time=item.end_time
                ))

        if not annotations:
            raise HTTPException(
                status_code=400,
                detail="No valid annotations provided"
            )

        # Add annotations
        config = AnnotationConfig(preserve_audio=body.preserve_audio)
        result = await add_annotations(
            video_path=video_path,
            annotations=annotations,
            config=config
        )

        # Cleanup
        if cleanup_video and video_path:
            try:
                Path(video_path).unlink(missing_ok=True)
            except Exception:
                pass

        return {
            "success": result.success,
            **result.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Form annotations failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Form annotations failed: {str(e)}"
        )


@app.get("/api/video/add-form-annotations/types")
async def get_annotation_types():
    """
    Get available annotation types.

    Each type includes description and required parameters.
    """
    from backend.form_annotations import get_annotation_types

    return {
        "annotation_types": get_annotation_types()
    }


@app.get("/api/video/add-form-annotations/colors")
async def get_annotation_colors():
    """
    Get available preset colors for annotations.
    """
    from backend.form_annotations import get_colors

    return {
        "colors": get_colors()
    }


@app.post("/api/video/add-slow-motion")
@limiter.limit("10/minute")
async def add_slow_motion_endpoint(
    request: Request,
    video_url: str = Form(...),
    start_time: float = Form(...),
    end_time: float = Form(...),
    speed: float = Form(0.5),
    preserve_audio: bool = Form(False)
):
    """
    Add slow motion effect to a video segment.

    Speeds:
    - 0.25: Quarter speed (very slow)
    - 0.5: Half speed (standard slow-mo)
    - 0.75: Three-quarter speed (slight slow)
    """
    from backend.form_annotations import add_slow_motion
    import tempfile
    import httpx

    if not await check_quota(request, "video"):
        raise HTTPException(
            status_code=429,
            detail="Quota exceeded for video operations"
        )

    try:
        # Download video if URL
        video_path = None
        cleanup_video = False

        if video_url.startswith("http"):
            temp_dir = tempfile.mkdtemp()
            video_path = f"{temp_dir}/video.mp4"
            cleanup_video = True

            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.get(video_url, follow_redirects=True)
                response.raise_for_status()

                with open(video_path, 'wb') as f:
                    f.write(response.content)
        else:
            video_path = video_url

        from pathlib import Path
        if not Path(video_path).exists():
            raise HTTPException(
                status_code=404,
                detail=f"Video file not found: {video_path}"
            )

        result = await add_slow_motion(
            video_path=video_path,
            start_time=start_time,
            end_time=end_time,
            speed=speed,
            preserve_audio=preserve_audio
        )

        if cleanup_video and video_path:
            try:
                Path(video_path).unlink(missing_ok=True)
            except Exception:
                pass

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Slow motion failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Slow motion failed: {str(e)}"
        )


# ============================================================================
# Exercise Recognition Endpoints (v2.0 - Phase 6)
# ============================================================================

@app.post("/api/video/detect-exercise")
@limiter.limit("10/minute")
async def detect_exercise_endpoint(request: Request, body: ExerciseRecognitionRequest):
    """
    Detect exercise type from video using pose estimation.

    Supports 20+ exercises including:
    - Squat, Deadlift, Bench Press, Overhead Press
    - Pull-Up, Bent Over Row, Lat Pulldown
    - Lunge, Leg Press, Hip Thrust
    - Push-Up, Dips, Plank
    - Bicep Curl, Tricep Extension, Lateral Raise
    - Burpee, Mountain Climber, and more

    Returns exercise identification, rep count estimate, form analysis,
    and recommendations for complementary exercises.
    """
    from backend.exercise_recognition import (
        detect_exercise,
        ExerciseRecognitionConfig
    )
    import tempfile
    import httpx

    if not await check_quota(request, "video"):
        raise HTTPException(
            status_code=429,
            detail="Quota exceeded for video operations"
        )

    try:
        # Download video if URL
        video_path = None
        cleanup_video = False

        if body.video_url.startswith("http"):
            temp_dir = tempfile.mkdtemp()
            video_path = f"{temp_dir}/video.mp4"
            cleanup_video = True

            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.get(body.video_url, follow_redirects=True)
                response.raise_for_status()

                with open(video_path, 'wb') as f:
                    f.write(response.content)
        else:
            video_path = body.video_url

        from pathlib import Path
        if not Path(video_path).exists():
            raise HTTPException(
                status_code=404,
                detail=f"Video file not found: {video_path}"
            )

        # Configure recognition
        config = ExerciseRecognitionConfig(
            min_confidence=body.min_confidence,
            enable_rep_counting=body.enable_rep_counting,
            enable_form_analysis=body.enable_form_analysis,
            sample_interval=body.sample_interval
        )

        # Detect exercise
        result = await detect_exercise(video_path, config)

        # Cleanup
        if cleanup_video and video_path:
            try:
                Path(video_path).unlink(missing_ok=True)
            except Exception:
                pass

        return {
            "success": result.success,
            "detected_exercise": result.detected_exercise,
            "exercise_name": result.exercise_name,
            "confidence": result.confidence,
            "category": result.category,
            "muscle_groups": result.muscle_groups,
            "rep_count_estimate": result.rep_count_estimate,
            "avg_rep_duration": result.avg_rep_duration,
            "description": result.description,
            "recommendations": result.recommendations,
            "complementary_exercises": result.complementary_exercises,
            "form_score": result.form_score,
            "form_observations": result.form_observations,
            "processing_time": result.processing_time,
            "frames_analyzed": result.frames_analyzed,
            "error": result.error
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Exercise detection failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Exercise detection failed: {str(e)}"
        )


@app.get("/api/video/detect-exercise/exercises")
async def get_supported_exercises():
    """
    Get list of all supported exercises.

    Returns exercise details including:
    - name, category, muscle groups
    - equipment options
    - difficulty level
    - form cues
    - complementary exercises
    """
    from backend.exercise_recognition import get_supported_exercises

    exercises = get_supported_exercises()

    return {
        "total": len(exercises),
        "exercises": exercises
    }


@app.get("/api/video/detect-exercise/categories")
async def get_exercise_categories():
    """
    Get exercise categories.

    Categories: legs, back, chest, shoulders, arms, core, glutes, full_body
    """
    from backend.exercise_recognition import get_exercise_categories

    return {
        "categories": get_exercise_categories()
    }


@app.get("/api/video/detect-exercise/exercise/{exercise_id}")
async def get_exercise_details(exercise_id: str):
    """
    Get detailed information about a specific exercise.

    Includes form cues, target muscles, equipment options,
    and complementary exercises.
    """
    from backend.exercise_recognition import get_exercise_by_id

    exercise = get_exercise_by_id(exercise_id)

    if not exercise:
        raise HTTPException(
            status_code=404,
            detail=f"Exercise not found: {exercise_id}"
        )

    return {
        "exercise": exercise
    }


@app.get("/api/video/detect-exercise/category/{category}")
async def get_exercises_by_category(category: str):
    """
    Get exercises in a specific category.

    Categories: legs, back, chest, shoulders, arms, core, glutes, full_body
    """
    from backend.exercise_recognition import get_exercises_by_category, get_exercise_categories

    valid_categories = get_exercise_categories()
    if category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category: {category}. Valid: {', '.join(valid_categories)}"
        )

    exercises = get_exercises_by_category(category)

    return {
        "category": category,
        "count": len(exercises),
        "exercises": exercises
    }


# ============================================================================
# Rate Limiting and Quota Endpoints (v2.0)
# ============================================================================

@app.get("/api/quota/status")
@limiter.limit("60/minute")
async def get_user_quota_status(request: Request):
    """
    Get current quota status for the authenticated user.

    Returns usage counts, limits, and reset time for all quota types.
    Rate limit headers included in response.
    """
    status = await get_quota_status(request)

    # Build response with headers
    response = JSONResponse(content=status)

    # Add rate limit headers
    headers = get_rate_limit_headers(request)
    for key, value in headers.items():
        response.headers[key] = value

    return response


@app.get("/api/quota/tiers")
async def get_quota_tiers():
    """
    Get available subscription tiers and their limits.

    Returns all tiers with their quota limits and rate limits.
    """
    from backend.rate_limiter import TIER_QUOTAS, TIER_RATE_LIMITS

    tiers = {}
    for tier_name in [Tier.FREE, Tier.PRO, Tier.ENTERPRISE]:
        tiers[tier_name] = {
            "quotas": TIER_QUOTAS[tier_name],
            "rate_limit": TIER_RATE_LIMITS[tier_name]
        }

    return {
        "tiers": tiers,
        "current_tier_header": "X-User-Tier",
        "upgrade_url": "/api/upgrade"
    }


# ============================================================================
# Transcription Endpoints (v2.0)
# ============================================================================

class TranscriptionRequest(BaseModel):
    """Request model for transcription."""
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    language: Optional[str] = "auto"  # en, es, pt, auto
    output_format: Optional[str] = "json"  # json, srt, vtt

@app.post("/api/transcription")
@limiter.limit("30/minute")
async def transcribe_media(request: Request, body: TranscriptionRequest):
    """
    Transcribe audio or video with word-level timestamps.

    Supports:
    - Multiple languages (en, es, pt, auto-detect)
    - Word-level timestamps for caption sync
    - Output formats: JSON, SRT, VTT

    Returns transcription with timing for each word.
    """
    from backend.transcription import transcribe_video, transcribe_audio, generate_srt, generate_vtt

    # Check quota
    await check_quota(request, "transcription_jobs")

    # Validate input
    if not body.video_url and not body.audio_url:
        raise HTTPException(
            status_code=400,
            detail="Either video_url or audio_url is required"
        )

    try:
        # Download file if URL provided
        source_url = body.video_url or body.audio_url
        is_video = body.video_url is not None

        # For now, assume local file paths
        # TODO: Add URL download support
        if is_video:
            result = await transcribe_video(source_url, body.language)
        else:
            result = await transcribe_audio(source_url, body.language)

        # Format output
        if body.output_format == "srt":
            return {
                "format": "srt",
                "content": generate_srt(result),
                "language": result.language,
                "duration": result.duration,
                "word_count": len(result.words)
            }
        elif body.output_format == "vtt":
            return {
                "format": "vtt",
                "content": generate_vtt(result),
                "language": result.language,
                "duration": result.duration,
                "word_count": len(result.words)
            }
        else:
            return result.to_dict()

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Transcription failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


# ============================================================================
# Caption Style Endpoints (v2.0)
# ============================================================================

@app.get("/api/captions/styles")
async def get_caption_styles():
    """
    Get all available caption style templates.

    Returns 10 pre-built styles with previews and metadata.
    """
    from backend.caption_styles import list_styles

    return {
        "styles": list_styles(),
        "count": len(list_styles())
    }


@app.get("/api/captions/styles/{style_name}")
async def get_caption_style_detail(style_name: str):
    """
    Get details for a specific caption style.

    Args:
        style_name: Style name (trending, glow, minimal, etc.)
    """
    from backend.caption_styles import get_style

    style = get_style(style_name)
    if not style:
        raise HTTPException(
            status_code=404,
            detail=f"Style '{style_name}' not found. Use GET /api/captions/styles for available styles."
        )

    return style.to_dict()


@app.get("/api/captions/styles/platform/{platform}")
async def get_styles_for_platform(platform: str):
    """
    Get caption styles recommended for a specific platform.

    Args:
        platform: Platform name (tiktok, instagram, youtube, linkedin)
    """
    from backend.caption_styles import get_styles_for_platform as get_platform_styles

    styles = get_platform_styles(platform)
    return {
        "platform": platform,
        "styles": styles,
        "count": len(styles)
    }


class CustomStyleRequest(BaseModel):
    """Request model for creating custom caption style."""
    name: Optional[str] = "custom"
    font_family: Optional[str] = "Arial"
    font_size: Optional[int] = 48
    font_color: Optional[str] = "#FFFFFF"
    outline_color: Optional[str] = "#000000"
    outline_width: Optional[int] = 2
    shadow_color: Optional[str] = None
    shadow_offset: Optional[int] = 0
    background_color: Optional[str] = None
    background_opacity: Optional[float] = 0.0
    highlight_color: Optional[str] = "#FFFF00"
    highlight_style: Optional[str] = "color"
    animation: Optional[str] = "none"
    position: Optional[str] = "bottom"


@app.post("/api/captions/styles/custom")
async def create_custom_caption_style(body: CustomStyleRequest):
    """
    Create a custom caption style.

    Validates parameters and returns the custom style definition.
    """
    from backend.caption_styles import create_custom_style, validate_custom_style

    # Validate
    errors = validate_custom_style(body.model_dump())
    if errors:
        raise HTTPException(
            status_code=400,
            detail={"errors": errors}
        )

    # Create custom style
    style = create_custom_style(**body.model_dump())
    return style.to_dict()


@app.get("/api/captions/fonts")
async def get_available_fonts():
    """
    Get list of available fonts for caption styling.
    """
    from backend.caption_styles import list_available_fonts

    fonts = list_available_fonts()
    return {
        "fonts": fonts,
        "count": len(fonts)
    }


@app.post("/api/captions/recommend")
async def recommend_caption_style(
    platform: Optional[str] = None,
    content_type: Optional[str] = None,
    brand_color: Optional[str] = None
):
    """
    Get style recommendations based on context.

    Args:
        platform: Target platform (tiktok, instagram, youtube, linkedin)
        content_type: Content type (fitness, tutorial, vlog, professional)
        brand_color: Brand color to match (hex)
    """
    from backend.caption_styles import recommend_style

    recommendations = recommend_style(
        platform=platform,
        content_type=content_type,
        brand_color=brand_color
    )

    return {
        "recommendations": recommendations,
        "count": len(recommendations)
    }


# ============================================================================
# Original Endpoints
# ============================================================================

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
    Generate a video ad from images using the hybrid video router.

    Intelligent routing: MoviePy (free, local) → Creatomate (paid, cloud fallback).
    Tracks costs, success rates, and provider performance automatically.

    Supports force_method override and quality_tier selection.

    Returns:
    - video_url or video_path: The generated video
    - method: Which provider was used
    - cost: Actual cost for this generation
    """
    from backend.intelligent_video_router import IntelligentVideoRouter

    try:
        router = IntelligentVideoRouter(
            log_dir=str(Path(__file__).parent.parent / "data" / "video_logs")
        )

        result = router.create_video(
            image_urls=request.image_urls,
            headline=request.headline,
            cta_text=request.cta_text,
            duration=request.duration,
            music_style=request.music_style,
            force_method=request.force_method
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Video generation failed")
            )

        return {
            "success": True,
            "video_url": result.get("video_url"),
            "video_path": result.get("video_path"),
            "method": result.get("method", "unknown"),
            "cost": result.get("cost", 0),
            "message": f"Video generated via {result.get('method', 'hybrid router')}"
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


@app.get("/api/video/stats")
async def get_video_stats(days: int = 30):
    """
    Get video generation statistics from the hybrid router.

    Returns cost breakdown, success rates, and provider performance
    over the specified time period.
    """
    from backend.intelligent_video_router import IntelligentVideoRouter

    try:
        router = IntelligentVideoRouter(
            log_dir=str(Path(__file__).parent.parent / "data" / "video_logs")
        )
        stats = router.get_statistics(days=days)
        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching stats: {str(e)}"
        )


@app.get("/api/video/providers")
async def get_video_providers():
    """
    Get available video generation providers and their status.

    Shows each provider's cost, tier, and current availability.
    """
    providers = [
        {
            "id": "moviepy",
            "name": "MoviePy (Local)",
            "tier": "free",
            "cost_per_video": 0,
            "description": "Local video generation using MoviePy. Free but 70-85% success rate.",
            "requires_api_key": False,
            "available": True
        },
        {
            "id": "creatomate",
            "name": "Creatomate (Cloud)",
            "tier": "standard",
            "cost_per_video": 0.05,
            "description": "Cloud-based video generation. Reliable fallback at $0.05/video.",
            "requires_api_key": True,
            "available": bool(os.getenv("CREATOMATE_API_KEY"))
        },
        {
            "id": "shotstack",
            "name": "Shotstack (Legacy)",
            "tier": "standard",
            "cost_per_video": 0.05,
            "description": "Legacy cloud video generation. Available as direct override.",
            "requires_api_key": True,
            "available": bool(os.getenv("SHOTSTACK_API_KEY"))
        }
    ]

    return {
        "success": True,
        "providers": providers,
        "routing": {
            "strategy": "MoviePy first (free) → Creatomate fallback (paid)",
            "override": "Use force_method parameter to select a specific provider"
        }
    }


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

# NOTE: /api/sms/optin is now handled by sms_routes.py (hybrid n8n + Python)
# Migrated 2026-02-10: SMS sending goes through n8n on EC2 instead of direct Twilio calls

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

# ============================================================================
# Video Pipeline Endpoints (Editor)
# ============================================================================

@app.get("/api/video/pipeline/presets")
async def get_pipeline_presets():
    """List all available pipeline presets with descriptions."""
    from backend.pipeline_orchestrator import list_presets
    return {"presets": list_presets()}


@app.post("/api/video/pipeline/run")
async def run_pipeline(
    video: UploadFile = File(...),
    preset: str = Form("humiston_style"),
    step_overrides: Optional[str] = Form(None),
):
    """
    Start a video editing pipeline.

    Upload a video and select a preset. Returns a job_id for polling progress.

    - **video**: Raw video file (mp4, mov, avi)
    - **preset**: Pipeline preset name (humiston_style, viral_short, etc.)
    - **step_overrides**: Optional JSON string of step enable/disable overrides
      e.g. '{"sfx": false, "captions": false}'
    """
    import asyncio
    from backend.pipeline_orchestrator import run_pipeline as _run_pipeline, list_presets, PRESETS

    # Validate preset
    if preset not in PRESETS:
        valid = [p["id"] for p in list_presets()]
        raise HTTPException(400, f"Invalid preset '{preset}'. Valid: {valid}")

    # Validate file type
    allowed = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    ext = Path(video.filename).suffix.lower() if video.filename else ".mp4"
    if ext not in allowed:
        raise HTTPException(400, f"Unsupported format '{ext}'. Allowed: {allowed}")

    # Save uploaded video
    job_id = str(uuid.uuid4())[:8]
    upload_dir = VIDEOS_PATH / f"pipeline_{job_id}"
    upload_dir.mkdir(parents=True, exist_ok=True)
    input_path = upload_dir / f"input{ext}"

    with open(input_path, "wb") as f:
        content = await video.read()
        f.write(content)

    # Parse step overrides
    overrides = None
    if step_overrides:
        try:
            import json as _json
            overrides = _json.loads(step_overrides)
        except Exception:
            raise HTTPException(400, "step_overrides must be valid JSON")

    # Run pipeline in background
    async def _background():
        try:
            await _run_pipeline(
                video_path=str(input_path),
                preset_id=preset,
                output_dir=str(upload_dir),
                step_overrides=overrides,
            )
        except Exception as e:
            logger.error(f"Pipeline {job_id} failed: {e}")

    asyncio.create_task(_background())

    return {
        "job_id": job_id,
        "preset": preset,
        "status": "running",
        "poll_url": f"/api/video/pipeline/status/{job_id}",
        "message": "Pipeline started. Poll the status URL for progress.",
    }


@app.get("/api/video/pipeline/status/{job_id}")
async def get_pipeline_status(job_id: str):
    """
    Poll pipeline progress.

    Returns current step, overall progress, and output URLs when complete.
    """
    from backend.pipeline_orchestrator import get_job

    ctx = get_job(job_id)
    if not ctx:
        raise HTTPException(404, f"Pipeline job '{job_id}' not found")

    result = {
        "job_id": ctx.job_id,
        "status": ctx.status,
        "current_step": ctx.current_step,
        "total_steps": ctx.total_steps,
        "progress": ctx.progress,
        "steps_completed": ctx.steps_completed,
        "steps_failed": ctx.steps_failed,
        "error": ctx.error,
    }

    if ctx.status == "complete" and ctx.current_video:
        # Build download URL
        rel_path = Path(ctx.current_video).relative_to(STATIC_PATH)
        result["output_url"] = f"/static/{rel_path}"
        result["output_path"] = ctx.current_video

    return result


@app.post("/api/video/pipeline/custom")
async def run_custom_pipeline(
    video: UploadFile = File(...),
    steps: str = Form(...),
):
    """
    Run a custom pipeline with manually specified steps.

    - **video**: Raw video file
    - **steps**: JSON array of step configs, e.g.:
      '[{"name": "jumpcut", "params": {"aggressive": true}},
        {"name": "punch_zoom", "params": {"zoom_level": 1.4}}]'
    """
    import asyncio
    from backend.pipeline_orchestrator import run_custom_pipeline as _run_custom, StepConfig

    # Parse steps JSON
    try:
        import json as _json
        steps_data = _json.loads(steps)
    except Exception:
        raise HTTPException(400, "steps must be valid JSON array")

    if not isinstance(steps_data, list) or not steps_data:
        raise HTTPException(400, "steps must be a non-empty JSON array")

    # Build StepConfig list
    step_configs = []
    for s in steps_data:
        if not isinstance(s, dict) or "name" not in s:
            raise HTTPException(400, "Each step must have a 'name' field")
        step_configs.append(StepConfig(
            name=s["name"],
            module=s.get("module", s["name"]),
            enabled=s.get("enabled", True),
            params=s.get("params", {}),
        ))

    # Save uploaded video
    job_id = str(uuid.uuid4())[:8]
    upload_dir = VIDEOS_PATH / f"pipeline_{job_id}"
    upload_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(video.filename).suffix.lower() if video.filename else ".mp4"
    input_path = upload_dir / f"input{ext}"

    with open(input_path, "wb") as f:
        content = await video.read()
        f.write(content)

    async def _background():
        try:
            await _run_custom(
                video_path=str(input_path),
                steps=step_configs,
                output_dir=str(upload_dir),
            )
        except Exception as e:
            logger.error(f"Custom pipeline {job_id} failed: {e}")

    asyncio.create_task(_background())

    return {
        "job_id": job_id,
        "preset": "custom",
        "steps": [s.name for s in step_configs],
        "status": "running",
        "poll_url": f"/api/video/pipeline/status/{job_id}",
        "message": "Custom pipeline started. Poll the status URL for progress.",
    }


# ── Phase 3: Viral Intelligence + Color Grading + Transitions ────────────────

@app.get("/api/video/color-presets")
async def get_color_presets():
    """List available color grading presets."""
    from backend.color_grader import list_presets as _list_color_presets
    return {"presets": _list_color_presets()}


@app.post("/api/video/color-grade")
async def color_grade_video(
    video: UploadFile = File(...),
    preset: str = Form("humiston_clean"),
    intensity: float = Form(1.0),
    auto_detect: bool = Form(False),
):
    """Apply color grading to a video."""
    from backend.color_grader import apply_grade

    job_id = str(uuid.uuid4())[:8]
    upload_dir = VIDEOS_PATH / f"grade_{job_id}"
    upload_dir.mkdir(parents=True, exist_ok=True)

    input_path = upload_dir / video.filename
    with open(input_path, "wb") as f:
        shutil.copyfileobj(video.file, f)

    output_path = upload_dir / f"graded_{video.filename}"

    result = await apply_grade(
        video_path=str(input_path),
        preset=preset,
        output_path=str(output_path),
        intensity=intensity,
        auto_detect=auto_detect,
    )

    return {
        "job_id": job_id,
        **result.to_dict(),
        "download_url": f"/api/video/download/{job_id}/graded_{video.filename}",
    }


@app.post("/api/video/viral-analyze")
async def viral_analyze_video(
    video: UploadFile = File(...),
):
    """Run viral optimization analysis on a video, get improvement plan."""
    from backend.viral_optimizer import ViralOptimizer

    job_id = str(uuid.uuid4())[:8]
    upload_dir = VIDEOS_PATH / f"viral_{job_id}"
    upload_dir.mkdir(parents=True, exist_ok=True)

    input_path = upload_dir / video.filename
    with open(input_path, "wb") as f:
        shutil.copyfileobj(video.file, f)

    optimizer = ViralOptimizer()
    plan = await optimizer.analyze_and_optimize(video_path=str(input_path))

    if plan:
        return {
            "job_id": job_id,
            "viral_score_before": plan.viral_score_before,
            "weaknesses": [w.to_dict() for w in plan.weaknesses],
            "fix_steps": [
                {"step": f.fix_step, "params": f.fix_params, "impact": f.impact_estimate}
                for f in plan.weaknesses
            ],
        }
    return {"job_id": job_id, "error": "Analysis could not complete"}


@app.get("/api/video/transition-types")
async def get_transition_types():
    """List available transition types and platform presets."""
    from backend.transition_engine import TransitionType, PLATFORM_CONFIGS
    return {
        "types": [t.value for t in TransitionType if t != TransitionType.NONE],
        "platforms": {
            k: {"default_duration": v["default_duration"], "energy": v["energy"]}
            for k, v in PLATFORM_CONFIGS.items()
        },
    }


# ============================================================================
# Phase 4: Music, B-Roll, Batch Processing, Export Packaging
# ============================================================================

@app.post("/api/video/add-music")
@limiter.limit("10/minute")
async def add_music_to_video(
    request: Request,
    video: UploadFile = File(...),
    music: Optional[UploadFile] = File(None),
    category: str = Form("energetic"),
    volume: float = Form(0.15),
    duck_mode: str = Form("sidechain"),
    detect_bpm: bool = Form(False),
):
    """
    Add background music to a video with automatic speech ducking.

    Supports sidechain compression (music auto-ducks under speech),
    envelope ducking, or constant volume mixing.
    """
    from backend.music_mixer import add_background_music

    # Save uploaded video
    video_dir = tempfile.mkdtemp(dir=str(VIDEOS_PATH))
    video_path = os.path.join(video_dir, video.filename or "input.mp4")
    with open(video_path, "wb") as f:
        content = await video.read()
        f.write(content)

    # Save music file if provided
    music_path = None
    if music:
        music_path = os.path.join(video_dir, music.filename or "music.mp3")
        with open(music_path, "wb") as f:
            content = await music.read()
            f.write(content)

    output_path = os.path.join(video_dir, "output_with_music.mp4")
    music_dir = str(PROJECT_PATH / "data" / "music")

    result = await add_background_music(
        video_path=video_path,
        output_path=output_path,
        music_path=music_path,
        music_dir=music_dir if not music_path else None,
        category=category,
        music_volume=min(max(volume, 0.0), 1.0),
        duck_mode=duck_mode,
        detect_bpm=detect_bpm,
    )

    if result.success:
        return {
            "success": True,
            "download_url": f"/static/videos/{Path(video_dir).name}/output_with_music.mp4",
            "music_track": result.music_track,
            "duck_mode": result.duck_mode,
            "bpm": result.detected_bpm,
            "beat_count": result.beat_count,
        }
    raise HTTPException(status_code=500, detail=result.error or "Music mixing failed")


@app.get("/api/video/music-categories")
async def get_music_categories():
    """List available music categories and library contents."""
    from backend.music_mixer import MusicCategory, scan_music_library

    music_dir = str(PROJECT_PATH / "data" / "music")
    tracks = scan_music_library(music_dir)

    categories = {}
    for cat in MusicCategory:
        cat_tracks = [t for t in tracks if t.category == cat]
        categories[cat.value] = {
            "name": cat.value.replace("_", " ").title(),
            "track_count": len(cat_tracks),
            "tracks": [{"name": t.name, "duration": round(t.duration, 1)} for t in cat_tracks],
        }

    return {"categories": categories, "total_tracks": len(tracks)}


@app.post("/api/video/detect-beats")
@limiter.limit("10/minute")
async def detect_video_beats(
    request: Request,
    video: UploadFile = File(...),
):
    """Detect beat timestamps and BPM in a video's audio track."""
    from backend.music_mixer import get_beat_timestamps

    video_dir = tempfile.mkdtemp(dir=str(VIDEOS_PATH))
    video_path = os.path.join(video_dir, video.filename or "input.mp4")
    with open(video_path, "wb") as f:
        content = await video.read()
        f.write(content)

    result = await get_beat_timestamps(video_path)
    return result


@app.post("/api/video/detect-talking-head")
@limiter.limit("10/minute")
async def detect_talking_head(
    request: Request,
    video: UploadFile = File(...),
    min_duration: float = Form(3.0),
):
    """Detect talking-head segments with low visual variety."""
    from backend.broll_inserter import detect_talking_head_segments

    video_dir = tempfile.mkdtemp(dir=str(VIDEOS_PATH))
    video_path = os.path.join(video_dir, video.filename or "input.mp4")
    with open(video_path, "wb") as f:
        content = await video.read()
        f.write(content)

    segments = await detect_talking_head_segments(video_path, min_duration=min_duration)
    return {
        "segments": [
            {
                "start": s.start,
                "end": s.end,
                "duration": round(s.duration, 2),
                "motion_score": round(s.motion_score, 3),
                "is_candidate": s.is_good_candidate,
            }
            for s in segments
        ],
        "total": len(segments),
        "candidates": sum(1 for s in segments if s.is_good_candidate),
    }


@app.post("/api/video/insert-broll")
@limiter.limit("5/minute")
async def insert_broll_endpoint(
    request: Request,
    video: UploadFile = File(...),
    category: Optional[str] = Form(None),
    max_insertions: int = Form(8),
    min_duration: float = Form(3.0),
):
    """Detect talking-head segments and auto-insert B-roll clips."""
    from backend.broll_inserter import insert_broll

    video_dir = tempfile.mkdtemp(dir=str(VIDEOS_PATH))
    video_path = os.path.join(video_dir, video.filename or "input.mp4")
    with open(video_path, "wb") as f:
        content = await video.read()
        f.write(content)

    output_path = os.path.join(video_dir, "output_with_broll.mp4")
    broll_dir = str(PROJECT_PATH / "data" / "broll")

    result = await insert_broll(
        video_path=video_path,
        output_path=output_path,
        broll_dir=broll_dir,
        category=category,
        max_insertions=max_insertions,
        min_segment_dur=min_duration,
    )

    if result.success:
        return {
            "success": True,
            "download_url": f"/static/videos/{Path(video_dir).name}/output_with_broll.mp4" if result.segments_filled > 0 else None,
            "segments_detected": result.segments_detected,
            "segments_filled": result.segments_filled,
            "insertions": result.insertions,
        }
    raise HTTPException(status_code=500, detail=result.error or "B-roll insertion failed")


@app.get("/api/video/broll-categories")
async def get_broll_categories():
    """List available B-roll categories and clips."""
    from backend.broll_inserter import BRollCategory, scan_broll_library

    broll_dir = str(PROJECT_PATH / "data" / "broll")
    clips = scan_broll_library(broll_dir)

    categories = {}
    for cat in BRollCategory:
        cat_clips = [c for c in clips if c.category == cat]
        categories[cat.value] = {
            "name": cat.value.replace("_", " ").title(),
            "clip_count": len(cat_clips),
            "clips": [{"name": c.name, "duration": round(c.duration, 1)} for c in cat_clips],
        }

    return {"categories": categories, "total_clips": len(clips)}


@app.post("/api/video/pipeline/batch")
@limiter.limit("3/minute")
async def run_batch_pipeline_endpoint(
    request: Request,
    videos: List[UploadFile] = File(...),
    preset: str = Form("humiston_style"),
):
    """
    Process multiple videos with the same preset.

    Returns a batch_id for tracking overall progress.
    """
    from backend.pipeline_orchestrator import run_batch_pipeline, PRESETS

    if preset not in PRESETS:
        raise HTTPException(status_code=400, detail=f"Unknown preset: {preset}")

    if len(videos) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 videos per batch")

    batch_dir = tempfile.mkdtemp(dir=str(VIDEOS_PATH))
    video_paths = []

    for i, video in enumerate(videos):
        video_path = os.path.join(batch_dir, f"video_{i}_{video.filename or 'input.mp4'}")
        with open(video_path, "wb") as f:
            content = await video.read()
            f.write(content)
        video_paths.append(video_path)

    output_dir = os.path.join(batch_dir, "output")

    # Run batch in background (async)
    batch = await run_batch_pipeline(
        video_paths=video_paths,
        preset_id=preset,
        output_dir=output_dir,
    )

    return batch.to_status_dict()


@app.get("/api/video/pipeline/batch/{batch_id}")
async def get_batch_status(batch_id: str):
    """Get status of a batch pipeline run."""
    from backend.pipeline_orchestrator import get_batch

    batch = get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")
    return batch.to_status_dict()


@app.post("/api/video/pipeline/package/{job_id}")
async def create_package(job_id: str, platforms: Optional[str] = Form(None)):
    """
    Create export package for a completed pipeline job.

    Returns video + thumbnail + description + hashtags per platform.
    """
    from backend.pipeline_orchestrator import get_job, create_export_package

    ctx = get_job(job_id)
    if not ctx:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    if ctx.status != "completed":
        raise HTTPException(status_code=400, detail=f"Job {job_id} is not completed (status: {ctx.status})")

    platform_list = platforms.split(",") if platforms else ["tiktok", "youtube_shorts"]
    packages = await create_export_package(ctx, platforms=platform_list)

    return {
        "job_id": job_id,
        "packages": [p.to_dict() for p in packages],
    }


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
