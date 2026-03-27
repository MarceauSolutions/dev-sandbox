"""
Fitness-Influencer Tower — Content Routes
Extracted from main.py monolith. 22 routes.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse

router = APIRouter()


# ============================================================================
# Content Calendar & Strategy Endpoints
# ============================================================================

@router.get("/api/content/calendar/today")
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


@router.get("/api/content/calendar/{day}")
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


@router.get("/api/content/calendar/week/plan")
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


@router.get("/api/content/calendar/captions/{day}")
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


@router.post("/api/video/remove-fillers")
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


@router.post("/api/video/detect-fillers")
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
# Original Endpoints
# ============================================================================

@router.post("/api/ai/chat")
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


@router.post("/api/video/edit")
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


@router.post("/api/video/generate")
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


@router.post("/api/video/status")
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


@router.get("/api/video/stats")
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


@router.get("/api/video/providers")
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


@router.post("/api/brand/research")
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


@router.get("/api/brand/profile/{handle}")
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


@router.get("/api/brand/list")
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


@router.delete("/api/brand/profile/{handle}")
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


@router.post("/api/graphics/create")
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


@router.post("/api/graphics/create-with-background")
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


@router.post("/api/email/digest")
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


@router.post("/api/analytics/revenue")
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


@router.post("/api/images/generate")
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


@router.post("/api/ads/create")
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
# Utility Endpoints
# ============================================================================

