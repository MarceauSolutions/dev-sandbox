"""
Fitness-Influencer Tower — Overlay Routes
Extracted from main.py monolith. 8 routes.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse

router = APIRouter()


# ============================================================================
# Workout Overlay Endpoints (v2.0 - Phase 6)
# ============================================================================

@router.post("/api/video/add-workout-overlay")
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


@router.get("/api/video/add-workout-overlay/presets")
async def get_workout_presets():
    """
    Get available workout timer presets.

    Each preset includes work/rest durations and total rounds.
    """
    from backend.workout_overlays import get_presets

    return {
        "presets": get_presets()
    }


@router.get("/api/video/add-workout-overlay/styles")
async def get_workout_overlay_styles():
    """
    Get available overlay styles.

    Each style includes font, colors, and visual settings.
    """
    from backend.workout_overlays import get_styles

    return {
        "styles": get_styles()
    }


@router.get("/api/video/add-workout-overlay/timer-types")
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

@router.post("/api/video/add-form-annotations")
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


@router.get("/api/video/add-form-annotations/types")
async def get_annotation_types():
    """
    Get available annotation types.

    Each type includes description and required parameters.
    """
    from backend.form_annotations import get_annotation_types

    return {
        "annotation_types": get_annotation_types()
    }


@router.get("/api/video/add-form-annotations/colors")
async def get_annotation_colors():
    """
    Get available preset colors for annotations.
    """
    from backend.form_annotations import get_colors

    return {
        "colors": get_colors()
    }


@router.post("/api/video/add-slow-motion")
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


