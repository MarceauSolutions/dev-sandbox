"""
Fitness-Influencer Tower — Analysis Routes
Extracted from main.py monolith. 15 routes.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse

router = APIRouter()


# ============================================================================
# Video Analysis Endpoints (v2.0 - Phase 5)
# ============================================================================

@router.post("/api/video/analyze")
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


@router.get("/api/video/analyze/segment-types")
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


@router.post("/api/video/viral-moments")
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


@router.get("/api/video/viral-moments/categories")
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

@router.post("/api/video/analyze-hook")
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


@router.get("/api/video/analyze-hook/platforms")
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


@router.get("/api/video/analyze-hook/improvement-types")
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

@router.post("/api/video/predict-retention")
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


@router.get("/api/video/predict-retention/benchmarks")
async def get_retention_benchmarks():
    """
    Get platform retention benchmarks.

    Shows what retention percentages are considered good/excellent for each platform.
    """
    from backend.retention_predictor import get_platform_benchmarks

    return {
        "benchmarks": get_platform_benchmarks()
    }


@router.get("/api/video/predict-retention/improvement-types")
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
# Exercise Recognition Endpoints (v2.0 - Phase 6)
# ============================================================================

@router.post("/api/video/detect-exercise")
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


@router.get("/api/video/detect-exercise/exercises")
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


@router.get("/api/video/detect-exercise/categories")
async def get_exercise_categories():
    """
    Get exercise categories.

    Categories: legs, back, chest, shoulders, arms, core, glutes, full_body
    """
    from backend.exercise_recognition import get_exercise_categories

    return {
        "categories": get_exercise_categories()
    }


@router.get("/api/video/detect-exercise/exercise/{exercise_id}")
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


@router.get("/api/video/detect-exercise/category/{category}")
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


