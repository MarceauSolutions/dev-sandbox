"""
Pipeline Orchestrator — Chain video processing modules into automated workflows.

Presets tuned for Ryan Humiston-style fitness content:
- Rapid jump cuts, punch-in zooms, bold captions, zero dead air
- Sound effects synced to cuts, fast transitions
- Viral optimization with before/after scoring
"""

import asyncio
import json
import logging
import os
import shutil
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class StepConfig:
    """Configuration for a single pipeline step."""
    name: str
    module: str
    enabled: bool = True
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineContext:
    """Shared state passed between pipeline steps."""
    job_id: str
    input_video: str
    current_video: str
    output_dir: str
    # Analysis data (populated by analyze steps, consumed by later steps)
    analysis: Optional[Any] = None
    transcription: Optional[Dict] = None
    hook_analysis: Optional[Any] = None
    retention_prediction: Optional[Any] = None
    viral_result: Optional[Any] = None
    tracking_result: Optional[Any] = None
    # Metadata for pipeline tracking
    cut_timestamps: List[float] = field(default_factory=list)
    viral_score_before: Optional[float] = None
    viral_score_after: Optional[float] = None
    # Progress
    total_steps: int = 0
    completed_steps: int = 0
    current_step_name: str = ""
    status: str = "pending"  # pending, running, completed, failed
    error: Optional[str] = None
    start_time: float = 0.0
    end_time: float = 0.0
    step_results: Dict[str, Any] = field(default_factory=dict)

    @property
    def progress(self) -> float:
        if self.total_steps == 0:
            return 0.0
        return self.completed_steps / self.total_steps

    @property
    def elapsed_seconds(self) -> float:
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time if self.start_time else 0.0

    def to_status_dict(self) -> Dict:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "progress": round(self.progress * 100, 1),
            "current_step": self.current_step_name,
            "completed_steps": self.completed_steps,
            "total_steps": self.total_steps,
            "elapsed_seconds": round(self.elapsed_seconds, 1),
            "viral_score_before": self.viral_score_before,
            "viral_score_after": self.viral_score_after,
            "error": self.error,
        }


# ── Step Executors ────────────────────────────────────────────────────────────

async def _step_analyze(ctx: PipelineContext, params: Dict) -> PipelineContext:
    """Run video analysis (scene detection, audio energy, motion)."""
    try:
        from backend.video_analyzer import analyze_video, AnalysisConfig
    except ImportError:
        from video_analyzer import analyze_video, AnalysisConfig

    config = AnalysisConfig(
        analyze_audio=params.get("analyze_audio", True),
        analyze_motion=params.get("analyze_motion", True),
        detect_scenes=params.get("detect_scenes", True),
    )
    result = await analyze_video(ctx.current_video, config=config)
    ctx.analysis = result
    ctx.step_results["analyze"] = {
        "segments_found": len(result.segments) if hasattr(result, "segments") else 0,
        "scene_changes": len(result.scene_changes) if hasattr(result, "scene_changes") else 0,
    }
    return ctx


async def _step_jumpcut(ctx: PipelineContext, params: Dict) -> PipelineContext:
    """Apply jump cuts — remove silence and dead air."""
    try:
        from backend.video_jumpcut import VideoJumpCutter
    except ImportError:
        from video_jumpcut import VideoJumpCutter

    aggressive = params.get("aggressive", False)
    silence_thresh = params.get("silence_thresh", -35 if aggressive else -40)
    min_silence_dur = params.get("min_silence_dur", 0.2 if aggressive else 0.3)
    min_clip_dur = params.get("min_clip_dur", 0.3 if aggressive else 0.5)

    cutter = VideoJumpCutter(
        silence_thresh=silence_thresh,
        min_silence_dur=min_silence_dur,
        min_clip_dur=min_clip_dur,
    )
    output_path = os.path.join(ctx.output_dir, f"jumpcut_{ctx.job_id}.mp4")
    result = cutter.apply_jump_cuts(ctx.current_video, output_path)

    if result and os.path.exists(result):
        ctx.current_video = result
        ctx.step_results["jumpcut"] = {"output": result, "aggressive": aggressive}
    else:
        logger.warning("Jump cut produced no output, keeping original")
        ctx.step_results["jumpcut"] = {"skipped": True, "reason": "no valid segments"}
    return ctx


async def _step_punch_zoom(ctx: PipelineContext, params: Dict) -> PipelineContext:
    """Apply punch-in zoom effects at key moments."""
    try:
        from backend.punch_zoom import apply_punch_zooms
    except ImportError:
        from punch_zoom import apply_punch_zooms

    output_path = os.path.join(ctx.output_dir, f"punchzoom_{ctx.job_id}.mp4")
    result = await apply_punch_zooms(
        video_path=ctx.current_video,
        output_path=output_path,
        zoom_level=params.get("zoom_level", 1.3),
        zoom_duration=params.get("zoom_duration", 0.5),
        detection_mode=params.get("detection_mode", "audio_peaks"),
        max_zooms_per_minute=params.get("max_zooms_per_minute", 8),
        analysis=ctx.analysis,
    )
    if result and os.path.exists(result):
        ctx.current_video = result
        ctx.step_results["punch_zoom"] = {"output": result}
    else:
        ctx.step_results["punch_zoom"] = {"skipped": True}
    return ctx


async def _step_captions(ctx: PipelineContext, params: Dict) -> PipelineContext:
    """Add captions to video."""
    try:
        from backend.caption_generator import generate_captions, CaptionConfig, CaptionPosition
    except ImportError:
        from caption_generator import generate_captions, CaptionConfig, CaptionPosition

    style = params.get("style", "bold")
    position_str = params.get("position", "bottom")
    position = CaptionPosition.BOTTOM
    if position_str == "top":
        position = CaptionPosition.TOP
    elif position_str == "center":
        position = CaptionPosition.CENTER

    config = CaptionConfig(
        max_words_per_line=params.get("max_words_per_line", 5),
        word_highlight=params.get("word_highlight", True),
        position=position,
    )
    result = await generate_captions(
        ctx.current_video,
        config=config,
        transcription=ctx.transcription,
    )
    if result and hasattr(result, "captioned_video_path") and result.captioned_video_path:
        ctx.current_video = result.captioned_video_path
        # Save transcription for later steps
        if hasattr(result, "transcription") and result.transcription:
            ctx.transcription = result.transcription
        ctx.step_results["captions"] = {"output": result.captioned_video_path, "style": style}
    else:
        ctx.step_results["captions"] = {"skipped": True}
    return ctx


async def _step_reframe(ctx: PipelineContext, params: Dict) -> PipelineContext:
    """Reframe video to target aspect ratio."""
    try:
        from backend.auto_reframe import reframe_video, AspectRatio, TrackingMode
    except ImportError:
        from auto_reframe import reframe_video, AspectRatio, TrackingMode

    aspect_map = {
        "9:16": AspectRatio.PORTRAIT_9_16,
        "1:1": AspectRatio.SQUARE_1_1,
        "4:5": AspectRatio.PORTRAIT_4_5,
        "16:9": AspectRatio.LANDSCAPE_16_9,
    }
    target = aspect_map.get(params.get("aspect", "9:16"), AspectRatio.PORTRAIT_9_16)
    tracking = TrackingMode.FACE if params.get("face_tracking", True) else TrackingMode.CENTER

    output_path = os.path.join(ctx.output_dir, f"reframe_{ctx.job_id}.mp4")
    result = await reframe_video(
        ctx.current_video,
        target_aspect=target,
        tracking_mode=tracking,
        output_path=output_path,
    )
    if result and result.success:
        ctx.current_video = result.output_path
        ctx.step_results["reframe"] = {"output": result.output_path, "aspect": params.get("aspect", "9:16")}
    else:
        ctx.step_results["reframe"] = {"skipped": True}
    return ctx


async def _step_sfx(ctx: PipelineContext, params: Dict) -> PipelineContext:
    """Add sound effects synced to cuts."""
    try:
        from backend.sound_effects import apply_sound_effects
    except ImportError:
        from sound_effects import apply_sound_effects

    output_path = os.path.join(ctx.output_dir, f"sfx_{ctx.job_id}.mp4")
    result = await apply_sound_effects(
        video_path=ctx.current_video,
        output_path=output_path,
        sfx_on_cuts=params.get("sfx_on_cuts", True),
        sfx_type=params.get("sfx_type", "whoosh"),
        volume=params.get("volume", 0.3),
        cut_timestamps=ctx.cut_timestamps,
    )
    if result and os.path.exists(result):
        ctx.current_video = result
        ctx.step_results["sfx"] = {"output": result}
    else:
        ctx.step_results["sfx"] = {"skipped": True}
    return ctx


async def _step_viral_score(ctx: PipelineContext, params: Dict) -> PipelineContext:
    """Run viral detection scoring."""
    try:
        from backend.viral_detector import detect_viral_moments
    except ImportError:
        from viral_detector import detect_viral_moments

    result = await detect_viral_moments(
        ctx.current_video,
        transcription_result=ctx.transcription,
        video_analysis=ctx.analysis,
    )
    ctx.viral_result = result
    score = result.avg_score if hasattr(result, "avg_score") else 0
    # Store as before or after depending on context
    if ctx.viral_score_before is None:
        ctx.viral_score_before = score
    else:
        ctx.viral_score_after = score
    ctx.step_results["viral_score"] = {"score": score}
    return ctx


async def _step_hook_optimize(ctx: PipelineContext, params: Dict) -> PipelineContext:
    """Analyze hook quality and store improvements."""
    try:
        from backend.hook_analyzer import analyze_hook, HookConfig
    except ImportError:
        from hook_analyzer import analyze_hook, HookConfig

    config = HookConfig(
        hook_duration=params.get("hook_duration", 3.0),
        platform=params.get("platform", "tiktok"),
        generate_variants=True,
    )
    result = await analyze_hook(ctx.current_video, config=config)
    ctx.hook_analysis = result
    ctx.step_results["hook_optimize"] = {
        "score": result.score.total if hasattr(result, "score") and hasattr(result.score, "total") else 0,
        "grade": result.grade if hasattr(result, "grade") else "N/A",
        "improvements": len(result.improvements) if hasattr(result, "improvements") else 0,
    }
    return ctx


async def _step_exercise_detect(ctx: PipelineContext, params: Dict) -> PipelineContext:
    """Detect exercises in the video."""
    try:
        from backend.exercise_recognition import ExerciseRecognizer
    except ImportError:
        from exercise_recognition import ExerciseRecognizer

    recognizer = ExerciseRecognizer()
    # Exercise recognition works on video frames
    result = await recognizer.analyze_video(ctx.current_video) if hasattr(recognizer, "analyze_video") else None
    if result:
        ctx.step_results["exercise_detect"] = {"exercises_found": len(result) if isinstance(result, list) else 1}
    else:
        ctx.step_results["exercise_detect"] = {"skipped": True}
    return ctx


async def _step_overlays(ctx: PipelineContext, params: Dict) -> PipelineContext:
    """Add workout overlays (timer, rep counter)."""
    try:
        from backend.workout_overlays import add_workout_overlay
    except ImportError:
        from workout_overlays import add_workout_overlay

    output_path = os.path.join(ctx.output_dir, f"overlay_{ctx.job_id}.mp4")
    overlay_type = params.get("type", "timer")
    style = params.get("style", "modern")

    result = await add_workout_overlay(
        video_path=ctx.current_video,
        output_path=output_path,
        overlay_type=overlay_type,
        style=style,
    ) if asyncio.iscoroutinefunction(add_workout_overlay) else add_workout_overlay(
        video_path=ctx.current_video,
        output_path=output_path,
        overlay_type=overlay_type,
        style=style,
    )
    if result and os.path.exists(output_path):
        ctx.current_video = output_path
        ctx.step_results["overlays"] = {"output": output_path, "type": overlay_type}
    else:
        ctx.step_results["overlays"] = {"skipped": True}
    return ctx


async def _step_remotion_composite(ctx: PipelineContext, params: Dict) -> PipelineContext:
    """Overlay pre-rendered Remotion animated elements (intro, text bombs, stats)."""
    try:
        from backend.remotion_compositor import apply_remotion_overlays
    except ImportError:
        from remotion_compositor import apply_remotion_overlays

    output_path = os.path.join(ctx.output_dir, f"remotion_{ctx.job_id}.mp4")
    result = await apply_remotion_overlays(
        video_path=ctx.current_video,
        output_path=output_path,
        assets_dir=params.get("assets_dir"),
        include_intro=params.get("include_intro", True),
        text_bomb_texts=params.get("text_bomb_texts"),
        stat_data=params.get("stat_data"),
        analysis=ctx.analysis,
    )
    if result and os.path.exists(result):
        ctx.current_video = result
        ctx.step_results["remotion_composite"] = {"output": result}
    else:
        ctx.step_results["remotion_composite"] = {"skipped": True}
    return ctx


async def _step_transition_effects(ctx: PipelineContext, params: Dict) -> PipelineContext:
    """Apply smooth transitions at scene changes."""
    try:
        from backend.transition_engine import apply_transitions
    except ImportError:
        from transition_engine import apply_transitions

    # Get scene changes from analysis if available
    scene_changes = None
    if ctx.analysis and hasattr(ctx.analysis, "scene_changes"):
        scene_changes = [s.to_dict() for s in ctx.analysis.scene_changes]

    output_path = os.path.join(ctx.output_dir, f"transitions_{ctx.job_id}.mp4")
    result = await apply_transitions(
        video_path=ctx.current_video,
        scene_changes=scene_changes,
        platform=params.get("platform", "default"),
        output_path=output_path,
        min_gap=params.get("min_gap", 2.0),
        max_transitions=params.get("max_transitions", 20),
    )
    if result and result.transitions_applied > 0:
        ctx.current_video = result.output_path
        ctx.step_results["transition_effects"] = {
            "output": result.output_path,
            "applied": result.transitions_applied,
            "total_points": len(result.transition_points),
        }
    else:
        ctx.step_results["transition_effects"] = {"skipped": True, "reason": "no transitions needed"}
    return ctx


async def _step_color_grade(ctx: PipelineContext, params: Dict) -> PipelineContext:
    """Apply color grading preset."""
    try:
        from backend.color_grader import apply_grade
    except ImportError:
        from color_grader import apply_grade

    output_path = os.path.join(ctx.output_dir, f"graded_{ctx.job_id}.mp4")
    result = await apply_grade(
        video_path=ctx.current_video,
        preset=params.get("preset", "humiston_clean"),
        output_path=output_path,
        intensity=params.get("intensity", 1.0),
        auto_detect=params.get("auto_detect", False),
        lut_dir=params.get("lut_dir"),
    )
    if result and os.path.exists(result.output_path):
        ctx.current_video = result.output_path
        ctx.step_results["color_grade"] = {
            "output": result.output_path,
            "preset": result.preset_used,
        }
        if result.lighting_analysis:
            ctx.step_results["color_grade"]["lighting"] = result.lighting_analysis.to_dict()
    else:
        ctx.step_results["color_grade"] = {"skipped": True}
    return ctx


async def _step_viral_optimize(ctx: PipelineContext, params: Dict) -> PipelineContext:
    """Run viral optimization analysis and build fix plan."""
    try:
        from backend.viral_optimizer import analyze_and_optimize, ViralOptimizer
    except ImportError:
        from viral_optimizer import analyze_and_optimize, ViralOptimizer

    optimizer = ViralOptimizer()
    plan = await optimizer.analyze_and_optimize(
        video_path=ctx.current_video,
        transcription=ctx.transcription,
        analysis=ctx.analysis,
    )
    if plan:
        ctx.viral_score_before = plan.viral_score_before
        ctx.step_results["viral_optimize"] = {
            "score_before": plan.viral_score_before,
            "weaknesses": len(plan.weaknesses),
            "fixes_planned": len(plan.fix_steps),
            "fix_steps": [{"step": f.fix_step, "impact": f.impact_estimate} for f in plan.weaknesses[:5]],
        }
    else:
        ctx.step_results["viral_optimize"] = {"skipped": True}
    return ctx


async def _step_background_music(ctx: PipelineContext, params: Dict) -> PipelineContext:
    """Add background music with auto-duck under speech."""
    try:
        from backend.music_mixer import add_background_music
    except ImportError:
        from music_mixer import add_background_music

    output_path = os.path.join(ctx.output_dir, f"music_{ctx.job_id}.mp4")
    result = await add_background_music(
        video_path=ctx.current_video,
        output_path=output_path,
        music_path=params.get("music_path"),
        music_dir=params.get("music_dir"),
        category=params.get("category", "energetic"),
        music_volume=params.get("volume", 0.15),
        duck_mode=params.get("duck_mode", "sidechain"),
        duck_amount=params.get("duck_amount", 0.7),
        detect_bpm=params.get("detect_bpm", False),
    )
    if result.success and os.path.exists(result.output_path):
        ctx.current_video = result.output_path
        ctx.step_results["background_music"] = {
            "output": result.output_path,
            "track": result.music_track,
            "duck_mode": result.duck_mode,
            "bpm": result.detected_bpm,
        }
    else:
        ctx.step_results["background_music"] = {"skipped": True, "reason": result.error or "no music available"}
    return ctx


async def _step_broll_insert(ctx: PipelineContext, params: Dict) -> PipelineContext:
    """Detect talking-head segments and insert B-roll."""
    try:
        from backend.broll_inserter import insert_broll
    except ImportError:
        from broll_inserter import insert_broll

    output_path = os.path.join(ctx.output_dir, f"broll_{ctx.job_id}.mp4")
    result = await insert_broll(
        video_path=ctx.current_video,
        output_path=output_path,
        broll_dir=params.get("broll_dir"),
        broll_clips=params.get("broll_clips"),
        category=params.get("category"),
        max_insertions=params.get("max_insertions", 8),
        min_segment_dur=params.get("min_segment_dur", 3.0),
        insert_mode=params.get("insert_mode", "replace"),
        analysis=ctx.analysis,
    )
    if result.success and result.segments_filled > 0:
        ctx.current_video = result.output_path
        ctx.step_results["broll_insert"] = {
            "output": result.output_path,
            "detected": result.segments_detected,
            "filled": result.segments_filled,
            "insertions": result.insertions[:5],  # Limit for status payload
        }
    else:
        ctx.step_results["broll_insert"] = {
            "skipped": True,
            "detected": result.segments_detected,
            "reason": result.error or "no segments to fill",
        }
    return ctx


async def _step_form_annotations(ctx: PipelineContext, params: Dict) -> PipelineContext:
    """Add form annotation overlays."""
    # Form annotations are typically applied via the existing module
    ctx.step_results["form_annotations"] = {"skipped": True, "reason": "requires manual annotation data"}
    return ctx


async def _step_export(ctx: PipelineContext, params: Dict) -> PipelineContext:
    """Export for target platform(s)."""
    try:
        from backend.platform_exporter import export_for_platform, Platform
    except ImportError:
        from platform_exporter import export_for_platform, Platform

    platform_map = {
        "tiktok": Platform.TIKTOK,
        "youtube_shorts": Platform.YOUTUBE_SHORTS,
        "youtube": Platform.YOUTUBE_LONG,
        "instagram_reels": Platform.INSTAGRAM_REELS,
        "instagram_feed": Platform.INSTAGRAM_FEED,
        "linkedin": Platform.LINKEDIN,
        "twitter": Platform.TWITTER,
    }
    platforms = params.get("platforms", ["tiktok"])
    if isinstance(platforms, str):
        platforms = [platforms]

    exports = {}
    for p_name in platforms:
        platform = platform_map.get(p_name)
        if not platform:
            continue
        output_path = os.path.join(ctx.output_dir, f"export_{p_name}_{ctx.job_id}.mp4")
        try:
            result = await export_for_platform(ctx.current_video, platform, output_path=output_path)
            if result and result.success:
                exports[p_name] = result.output_path
        except Exception as e:
            logger.warning(f"Export to {p_name} failed: {e}")

    # Use first successful export as current video
    if exports:
        ctx.current_video = list(exports.values())[0]
    ctx.step_results["export"] = {"platforms": exports}
    return ctx


# ── Step Registry ─────────────────────────────────────────────────────────────

STEP_EXECUTORS: Dict[str, Callable] = {
    "analyze": _step_analyze,
    "jumpcut": _step_jumpcut,
    "punch_zoom": _step_punch_zoom,
    "captions": _step_captions,
    "reframe": _step_reframe,
    "sfx": _step_sfx,
    "remotion_composite": _step_remotion_composite,
    "transition_effects": _step_transition_effects,
    "color_grade": _step_color_grade,
    "viral_optimize": _step_viral_optimize,
    "viral_score": _step_viral_score,
    "hook_optimize": _step_hook_optimize,
    "exercise_detect": _step_exercise_detect,
    "overlays": _step_overlays,
    "background_music": _step_background_music,
    "broll_insert": _step_broll_insert,
    "form_annotations": _step_form_annotations,
    "export": _step_export,
}


# ── Pipeline Presets ──────────────────────────────────────────────────────────

PRESETS: Dict[str, Dict] = {
    "humiston_style": {
        "name": "Humiston Style",
        "description": "Ryan Humiston-inspired: rapid jump cuts, punch-in zooms, bold captions, animated overlays, transitions, color grading. Optimized for TikTok & YouTube Shorts.",
        "icon": "fire",
        "steps": [
            StepConfig("analyze", "analyze"),
            StepConfig("jumpcut", "jumpcut", params={"aggressive": True, "silence_thresh": -35, "min_silence_dur": 0.2}),
            StepConfig("punch_zoom", "punch_zoom", params={"zoom_level": 1.3, "max_zooms_per_minute": 8}),
            StepConfig("transition_effects", "transition_effects", params={"platform": "tiktok", "min_gap": 3.0}),
            StepConfig("captions", "captions", params={"style": "bold", "max_words_per_line": 4, "word_highlight": True}),
            StepConfig("sfx", "sfx", params={"sfx_on_cuts": True, "sfx_type": "whoosh", "volume": 0.25}),
            StepConfig("remotion_composite", "remotion_composite", params={"include_intro": True}),
            StepConfig("color_grade", "color_grade", params={"preset": "humiston_clean"}),
            StepConfig("background_music", "background_music", params={"category": "energetic", "volume": 0.12, "duck_mode": "sidechain"}, enabled=False),
            StepConfig("reframe", "reframe", params={"aspect": "9:16", "face_tracking": True}),
            StepConfig("export", "export", params={"platforms": ["tiktok", "youtube_shorts"]}),
        ],
    },
    "viral_short": {
        "name": "Viral Short",
        "description": "Optimized for maximum virality: jump cuts, reframe to 9:16, karaoke captions, hook analysis. Great for TikTok and Reels.",
        "icon": "trending",
        "steps": [
            StepConfig("analyze", "analyze"),
            StepConfig("viral_score", "viral_score"),
            StepConfig("jumpcut", "jumpcut"),
            StepConfig("reframe", "reframe", params={"aspect": "9:16"}),
            StepConfig("captions", "captions", params={"style": "karaoke", "word_highlight": True}),
            StepConfig("hook_optimize", "hook_optimize"),
            StepConfig("export", "export", params={"platforms": ["tiktok", "instagram_reels"]}),
        ],
    },
    "quick_polish": {
        "name": "Quick Polish",
        "description": "Fast cleanup: remove dead air, add minimal captions, export for multiple platforms. Under 2 minutes processing.",
        "icon": "bolt",
        "steps": [
            StepConfig("jumpcut", "jumpcut"),
            StepConfig("captions", "captions", params={"style": "minimal", "max_words_per_line": 7}),
            StepConfig("export", "export", params={"platforms": ["tiktok", "youtube", "instagram_reels"]}),
        ],
    },
    "workout_tutorial": {
        "name": "Workout Tutorial",
        "description": "Long-form workout content: exercise detection, timer overlays, rep counters, form annotations, color grading. Optimized for YouTube.",
        "icon": "dumbbell",
        "steps": [
            StepConfig("analyze", "analyze"),
            StepConfig("exercise_detect", "exercise_detect"),
            StepConfig("overlays", "overlays", params={"type": "timer", "style": "modern"}),
            StepConfig("captions", "captions", params={"style": "clean", "position": "bottom"}),
            StepConfig("form_annotations", "form_annotations"),
            StepConfig("color_grade", "color_grade", params={"preset": "clean_minimal", "auto_detect": True}),
            StepConfig("export", "export", params={"platforms": ["youtube"]}),
        ],
    },
    "long_to_shorts": {
        "name": "Long → Shorts",
        "description": "Repurpose long-form videos into viral shorts: find highlights, split into clips, reframe to 9:16, add karaoke captions.",
        "icon": "scissors",
        "steps": [
            StepConfig("analyze", "analyze"),
            StepConfig("viral_score", "viral_score"),
            StepConfig("jumpcut", "jumpcut"),
            StepConfig("reframe", "reframe", params={"aspect": "9:16", "face_tracking": True}),
            StepConfig("captions", "captions", params={"style": "karaoke", "word_highlight": True}),
            StepConfig("export", "export", params={"platforms": ["tiktok", "youtube_shorts"]}),
        ],
    },
    "maximum_viral": {
        "name": "Maximum Viral",
        "description": "Every optimization: viral analysis, jump cuts, punch zooms, transitions, animated overlays, color grade, trending captions, hook optimization, SFX. All platforms.",
        "icon": "rocket",
        "steps": [
            StepConfig("analyze", "analyze"),
            StepConfig("viral_optimize", "viral_optimize"),
            StepConfig("viral_score", "viral_score"),
            StepConfig("jumpcut", "jumpcut", params={"aggressive": True}),
            StepConfig("punch_zoom", "punch_zoom", params={"zoom_level": 1.35, "max_zooms_per_minute": 10}),
            StepConfig("transition_effects", "transition_effects", params={"platform": "tiktok", "min_gap": 2.0}),
            StepConfig("remotion_composite", "remotion_composite", params={"include_intro": True}),
            StepConfig("color_grade", "color_grade", params={"preset": "humiston_clean", "auto_detect": True}),
            StepConfig("reframe", "reframe", params={"aspect": "9:16", "face_tracking": True}),
            StepConfig("captions", "captions", params={"style": "trending", "max_words_per_line": 4, "word_highlight": True}),
            StepConfig("hook_optimize", "hook_optimize"),
            StepConfig("sfx", "sfx", params={"sfx_on_cuts": True, "sfx_type": "whoosh"}),
            StepConfig("broll_insert", "broll_insert", params={"max_insertions": 6, "min_segment_dur": 3.0}),
            StepConfig("background_music", "background_music", params={"category": "energetic", "volume": 0.12, "duck_mode": "sidechain"}),
            StepConfig("export", "export", params={"platforms": ["tiktok", "youtube_shorts", "instagram_reels", "youtube"]}),
        ],
    },
}


# ── Pipeline Engine ───────────────────────────────────────────────────────────

# In-memory job store (for status polling)
_jobs: Dict[str, PipelineContext] = {}


def get_job(job_id: str) -> Optional[PipelineContext]:
    """Get job status by ID."""
    return _jobs.get(job_id)


def list_presets() -> List[Dict]:
    """Return preset metadata for the frontend."""
    result = []
    for key, preset in PRESETS.items():
        result.append({
            "id": key,
            "name": preset["name"],
            "description": preset["description"],
            "icon": preset["icon"],
            "step_count": len([s for s in preset["steps"] if s.enabled]),
            "steps": [{"name": s.name, "module": s.module, "enabled": s.enabled} for s in preset["steps"]],
        })
    return result


async def run_pipeline(
    video_path: str,
    preset_id: str,
    output_dir: str,
    step_overrides: Optional[Dict[str, bool]] = None,
    custom_params: Optional[Dict[str, Dict]] = None,
) -> PipelineContext:
    """
    Run a pipeline preset on a video.

    Args:
        video_path: Path to input video file
        preset_id: Preset ID from PRESETS
        output_dir: Directory for intermediate and output files
        step_overrides: Optional dict of step_name → enabled (True/False) to toggle steps
        custom_params: Optional dict of step_name → params to override step config

    Returns:
        PipelineContext with results and final video path
    """
    preset = PRESETS.get(preset_id)
    if not preset:
        raise ValueError(f"Unknown preset: {preset_id}. Available: {list(PRESETS.keys())}")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Build step list with overrides
    steps = []
    for step in preset["steps"]:
        enabled = step.enabled
        if step_overrides and step.name in step_overrides:
            enabled = step_overrides[step.name]
        if not enabled:
            continue

        params = dict(step.params)
        if custom_params and step.name in custom_params:
            params.update(custom_params[step.name])

        steps.append(StepConfig(step.name, step.module, enabled=True, params=params))

    # Create context
    job_id = str(uuid.uuid4())[:8]
    ctx = PipelineContext(
        job_id=job_id,
        input_video=video_path,
        current_video=video_path,
        output_dir=output_dir,
        total_steps=len(steps),
        status="running",
        start_time=time.time(),
    )
    _jobs[job_id] = ctx

    # Execute steps
    for i, step in enumerate(steps):
        ctx.current_step_name = step.name
        logger.info(f"[{job_id}] Step {i+1}/{len(steps)}: {step.name}")

        executor = STEP_EXECUTORS.get(step.module)
        if not executor:
            logger.warning(f"[{job_id}] Unknown step module: {step.module}, skipping")
            ctx.step_results[step.name] = {"skipped": True, "reason": f"unknown module: {step.module}"}
            ctx.completed_steps += 1
            continue

        try:
            ctx = await executor(ctx, step.params)
            ctx.completed_steps += 1
            logger.info(f"[{job_id}] Step {step.name} complete ({ctx.completed_steps}/{ctx.total_steps})")
        except Exception as e:
            logger.error(f"[{job_id}] Step {step.name} failed: {e}", exc_info=True)
            ctx.step_results[step.name] = {"error": str(e)}
            ctx.completed_steps += 1
            # Continue to next step instead of failing entire pipeline

    ctx.status = "completed"
    ctx.end_time = time.time()
    ctx.current_step_name = "done"

    logger.info(
        f"[{job_id}] Pipeline complete in {ctx.elapsed_seconds:.1f}s. "
        f"Output: {ctx.current_video}"
    )
    return ctx


async def run_custom_pipeline(
    video_path: str,
    steps: List[Dict],
    output_dir: str,
) -> PipelineContext:
    """
    Run a custom pipeline with arbitrary steps.

    Args:
        video_path: Path to input video file
        steps: List of step dicts with 'name', 'module', 'params'
        output_dir: Directory for intermediate and output files

    Returns:
        PipelineContext with results
    """
    os.makedirs(output_dir, exist_ok=True)

    job_id = str(uuid.uuid4())[:8]
    step_configs = [
        StepConfig(
            name=s.get("name", s.get("module", "unknown")),
            module=s.get("module", s.get("name", "unknown")),
            params=s.get("params", {}),
        )
        for s in steps
    ]

    ctx = PipelineContext(
        job_id=job_id,
        input_video=video_path,
        current_video=video_path,
        output_dir=output_dir,
        total_steps=len(step_configs),
        status="running",
        start_time=time.time(),
    )
    _jobs[job_id] = ctx

    for i, step in enumerate(step_configs):
        ctx.current_step_name = step.name
        executor = STEP_EXECUTORS.get(step.module)
        if not executor:
            ctx.step_results[step.name] = {"skipped": True, "reason": f"unknown module: {step.module}"}
            ctx.completed_steps += 1
            continue

        try:
            ctx = await executor(ctx, step.params)
            ctx.completed_steps += 1
        except Exception as e:
            logger.error(f"[{job_id}] Step {step.name} failed: {e}", exc_info=True)
            ctx.step_results[step.name] = {"error": str(e)}
            ctx.completed_steps += 1

    ctx.status = "completed"
    ctx.end_time = time.time()
    ctx.current_step_name = "done"
    return ctx


# ── Batch Processing ─────────────────────────────────────────────────────────

@dataclass
class BatchJob:
    """Tracks a batch of pipeline runs."""
    batch_id: str
    preset_id: str
    total_videos: int
    completed: int = 0
    failed: int = 0
    jobs: List[str] = field(default_factory=list)  # List of job_ids
    status: str = "pending"  # pending, running, completed
    start_time: float = 0.0
    end_time: float = 0.0

    def to_status_dict(self) -> Dict:
        return {
            "batch_id": self.batch_id,
            "preset_id": self.preset_id,
            "status": self.status,
            "total_videos": self.total_videos,
            "completed": self.completed,
            "failed": self.failed,
            "progress": round(self.completed / self.total_videos * 100, 1) if self.total_videos else 0,
            "jobs": self.jobs,
            "elapsed_seconds": round(
                (self.end_time or time.time()) - self.start_time, 1
            ) if self.start_time else 0,
        }


_batches: Dict[str, BatchJob] = {}


def get_batch(batch_id: str) -> Optional[BatchJob]:
    """Get batch job status."""
    return _batches.get(batch_id)


async def run_batch_pipeline(
    video_paths: List[str],
    preset_id: str,
    output_dir: str,
    step_overrides: Optional[Dict[str, bool]] = None,
    custom_params: Optional[Dict[str, Dict]] = None,
) -> BatchJob:
    """
    Run a pipeline preset on multiple videos sequentially.

    Args:
        video_paths: List of input video file paths
        preset_id: Preset ID to apply to all videos
        output_dir: Base output directory (subdirs created per video)
        step_overrides: Optional step enable/disable overrides
        custom_params: Optional step parameter overrides

    Returns:
        BatchJob with overall progress and individual job IDs
    """
    batch_id = str(uuid.uuid4())[:8]
    batch = BatchJob(
        batch_id=batch_id,
        preset_id=preset_id,
        total_videos=len(video_paths),
        status="running",
        start_time=time.time(),
    )
    _batches[batch_id] = batch

    for i, video_path in enumerate(video_paths):
        video_output_dir = os.path.join(output_dir, f"video_{i}_{batch_id}")
        try:
            ctx = await run_pipeline(
                video_path=video_path,
                preset_id=preset_id,
                output_dir=video_output_dir,
                step_overrides=step_overrides,
                custom_params=custom_params,
            )
            batch.jobs.append(ctx.job_id)
            if ctx.status == "completed":
                batch.completed += 1
            else:
                batch.failed += 1
        except Exception as e:
            logger.error(f"Batch video {i} failed: {e}")
            batch.failed += 1

    batch.status = "completed"
    batch.end_time = time.time()
    return batch


# ── Export Packaging ─────────────────────────────────────────────────────────

@dataclass
class ExportPackage:
    """Platform-specific export bundle."""
    platform: str
    video_path: str
    thumbnail_path: Optional[str] = None
    description: str = ""
    hashtags: List[str] = field(default_factory=list)
    caption: str = ""

    def to_dict(self) -> Dict:
        return {
            "platform": self.platform,
            "video_path": self.video_path,
            "thumbnail_path": self.thumbnail_path,
            "description": self.description,
            "hashtags": self.hashtags,
            "caption": self.caption,
        }


async def generate_thumbnail(
    video_path: str,
    output_path: str,
    timestamp: float = 1.0,
) -> bool:
    """Extract a thumbnail frame from the video."""
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-ss", str(timestamp),
         "-frames:v", "1", "-q:v", "2", output_path],
        capture_output=True, text=True, timeout=30,
    )
    return result.returncode == 0 and os.path.exists(output_path)


async def create_export_package(
    ctx: PipelineContext,
    platforms: Optional[List[str]] = None,
) -> List[ExportPackage]:
    """
    Create platform-specific export bundles from a completed pipeline.

    Generates thumbnail, description, and hashtags for each platform.
    """
    packages = []
    if not platforms:
        platforms = ["tiktok", "youtube_shorts"]

    # Generate thumbnail
    thumb_path = os.path.join(ctx.output_dir, f"thumb_{ctx.job_id}.jpg")
    # Use a timestamp at ~25% for an interesting frame
    info_result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", ctx.current_video],
        capture_output=True, text=True, timeout=15,
    )
    duration = 5.0
    try:
        dur_data = json.loads(info_result.stdout)
        duration = float(dur_data.get("format", {}).get("duration", 5))
    except (json.JSONDecodeError, ValueError):
        pass

    thumb_ts = duration * 0.25
    has_thumb = await generate_thumbnail(ctx.current_video, thumb_path, timestamp=thumb_ts)

    # Build platform-specific metadata
    PLATFORM_HASHTAGS = {
        "tiktok": ["#fitness", "#gym", "#workout", "#fitnessmotivation", "#fyp", "#foryou", "#gymtok"],
        "youtube_shorts": ["#shorts", "#fitness", "#workout", "#gym", "#fitnessmotivation"],
        "instagram_reels": ["#fitness", "#reels", "#gym", "#workout", "#fitfam", "#gymlife"],
        "youtube": ["#fitness", "#workout", "#gym", "#tutorial"],
    }

    # Extract exercise info from pipeline results if available
    exercise_tags = []
    if "exercise_detect" in ctx.step_results:
        er = ctx.step_results["exercise_detect"]
        if not er.get("skipped") and er.get("exercises_found"):
            exercise_tags = ["#exercise"]

    for platform in platforms:
        export_result = ctx.step_results.get("export", {})
        video_path = export_result.get("platforms", {}).get(platform, ctx.current_video)

        tags = PLATFORM_HASHTAGS.get(platform, ["#fitness"])
        tags.extend(exercise_tags)

        # Build description
        viral_info = ctx.step_results.get("viral_optimize", {})
        score = viral_info.get("score_before", 0) if viral_info else 0

        description = "Fitness content"
        if score and score > 60:
            description = "High-energy fitness content"
        elif score and score > 40:
            description = "Workout tips and motivation"

        packages.append(ExportPackage(
            platform=platform,
            video_path=video_path,
            thumbnail_path=thumb_path if has_thumb else None,
            description=description,
            hashtags=tags[:15],  # Platform limits
            caption=f"{description} {' '.join(tags[:10])}",
        ))

    return packages


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Video Pipeline Orchestrator")
    parser.add_argument("video", help="Input video path")
    parser.add_argument("--preset", default="humiston_style", choices=list(PRESETS.keys()))
    parser.add_argument("--output-dir", default="./pipeline_output")
    parser.add_argument("--list-presets", action="store_true")
    args = parser.parse_args()

    if args.list_presets:
        for p in list_presets():
            print(f"\n{p['id']}:")
            print(f"  {p['name']} — {p['description']}")
            print(f"  Steps: {', '.join(s['name'] for s in p['steps'])}")
    else:
        logging.basicConfig(level=logging.INFO)
        result = asyncio.run(run_pipeline(args.video, args.preset, args.output_dir))
        print(f"\nPipeline complete:")
        print(f"  Output: {result.current_video}")
        print(f"  Time: {result.elapsed_seconds:.1f}s")
        print(f"  Viral score: {result.viral_score_before} → {result.viral_score_after}")
        print(f"  Steps: {json.dumps(result.step_results, indent=2, default=str)}")
