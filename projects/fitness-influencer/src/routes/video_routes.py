"""
Fitness-Influencer Tower — Video Routes
Extracted from main.py monolith. 36 routes.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse

router = APIRouter()


# ============================================================================
# Background Job Endpoints (v2.0)
# ============================================================================

@router.post("/api/jobs/submit", response_model=JobSubmitResponse)
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


@router.get("/api/jobs/{job_id}/status", response_model=JobStatusResponse)
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


@router.post("/api/jobs/{job_id}/cancel")
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


@router.get("/api/jobs")
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


@router.post("/api/video/caption")
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


@router.post("/api/video/reframe")
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


@router.post("/api/video/export")
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


@router.get("/api/video/export/platforms")
async def list_export_platforms():
    """
    List all supported export platforms with their specifications.

    Returns resolution, aspect ratio, duration limits, codec settings, etc.
    """
    from backend.platform_exporter import list_platforms

    return {
        "platforms": list_platforms()
    }


@router.get("/api/video/export/platforms/{platform}")
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


@router.post("/api/video/export/batch")
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


@router.post("/api/content/metadata")
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
# Transcription Endpoints (v2.0)
# ============================================================================

class TranscriptionRequest(BaseModel):
    """Request model for transcription."""
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    language: Optional[str] = "auto"  # en, es, pt, auto
    output_format: Optional[str] = "json"  # json, srt, vtt

@router.post("/api/transcription")
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

@router.get("/api/captions/styles")
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


@router.get("/api/captions/styles/{style_name}")
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


@router.get("/api/captions/styles/platform/{platform}")
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


@router.post("/api/captions/styles/custom")
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


@router.get("/api/captions/fonts")
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


@router.post("/api/captions/recommend")
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
# Video Pipeline Endpoints (Editor)
# ============================================================================

@router.get("/api/video/pipeline/presets")
async def get_pipeline_presets():
    """List all available pipeline presets with descriptions."""
    from backend.pipeline_orchestrator import list_presets
    return {"presets": list_presets()}


@router.post("/api/video/pipeline/run")
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


@router.get("/api/video/pipeline/status/{job_id}")
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


@router.post("/api/video/pipeline/custom")
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

@router.get("/api/video/color-presets")
async def get_color_presets():
    """List available color grading presets."""
    from backend.color_grader import list_presets as _list_color_presets
    return {"presets": _list_color_presets()}


@router.post("/api/video/color-grade")
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


@router.post("/api/video/viral-analyze")
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


@router.get("/api/video/transition-types")
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

@router.post("/api/video/add-music")
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


@router.get("/api/video/music-categories")
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


@router.post("/api/video/detect-beats")
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


@router.post("/api/video/detect-talking-head")
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


@router.post("/api/video/insert-broll")
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


@router.get("/api/video/broll-categories")
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


@router.post("/api/video/pipeline/batch")
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


@router.get("/api/video/pipeline/batch/{batch_id}")
async def get_batch_status(batch_id: str):
    """Get status of a batch pipeline run."""
    from backend.pipeline_orchestrator import get_batch

    batch = get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")
    return batch.to_status_dict()


@router.post("/api/video/pipeline/package/{job_id}")
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


@router.get("/api/status")
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
