#!/usr/bin/env python3
"""
Hook Analyzer and Optimizer for Fitness Influencer AI v2.0

Analyzes the first 3 seconds of video for hook effectiveness,
provides improvement suggestions, and generates alternative hook variants.

Features:
    - Hook score (0-100) based on action, curiosity, emotion, audio impact
    - Improvement suggestions (reorder, text overlay, music)
    - 3 alternative hook variant generation
    - A/B test tracking for hook performance
    - Platform-specific hook optimization

Usage:
    from backend.hook_analyzer import analyze_hook, HookConfig

    result = await analyze_hook(
        video_path="/path/to/video.mp4",
        transcription_result=transcription
    )

    print(f"Hook Score: {result.score}/100")
    for variant in result.variants:
        print(f"Alternative: {variant.description}")
"""

import asyncio
import re
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from backend.logging_config import get_logger, log_job_event
from backend.video_analyzer import (
    analyze_video,
    AnalysisConfig,
    get_video_duration,
    format_duration
)
from backend.viral_detector import (
    analyze_hook_strength,
    detect_emotional_markers,
    EMOTIONAL_MARKERS,
    HOOK_PATTERNS
)

logger = get_logger(__name__)


# ============================================================================
# Configuration
# ============================================================================

# Hook duration
HOOK_DURATION = 3.0  # First 3 seconds

# Platform-specific hook best practices
PLATFORM_HOOK_TIPS = {
    "tiktok": {
        "ideal_duration": 1.5,
        "text_overlay": True,
        "music_important": True,
        "face_visible": True,
        "tips": [
            "First frame should be visually striking",
            "Use trending sounds for algorithm boost",
            "Text hook should appear in first 0.5 seconds",
            "Movement in first frame increases watch time"
        ]
    },
    "instagram_reels": {
        "ideal_duration": 2.0,
        "text_overlay": True,
        "music_important": True,
        "face_visible": True,
        "tips": [
            "Polished aesthetic matters more than TikTok",
            "Use on-brand music",
            "Caption hook is crucial (shown below video)",
            "Bright, well-lit first frame"
        ]
    },
    "youtube_shorts": {
        "ideal_duration": 2.0,
        "text_overlay": True,
        "music_important": False,
        "face_visible": True,
        "tips": [
            "Pattern interrupt works well",
            "Educational hooks perform better",
            "Less reliance on trending audio",
            "Clear value proposition in first 2 seconds"
        ]
    },
    "youtube_long": {
        "ideal_duration": 3.0,
        "text_overlay": False,
        "music_important": False,
        "face_visible": True,
        "tips": [
            "Address the viewer directly",
            "Preview what they'll learn",
            "Show energy and enthusiasm",
            "Pattern interrupt or curiosity gap"
        ]
    }
}

# Hook improvement categories
class HookImprovementType(str, Enum):
    REORDER_SHOTS = "reorder_shots"
    ADD_TEXT_OVERLAY = "add_text_overlay"
    CHANGE_MUSIC = "change_music"
    ADD_VISUAL_EFFECT = "add_visual_effect"
    CHANGE_OPENING_SHOT = "change_opening_shot"
    ADD_PATTERN_INTERRUPT = "add_pattern_interrupt"
    INCREASE_ENERGY = "increase_energy"
    ADD_CURIOSITY_GAP = "add_curiosity_gap"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class HookScore:
    """Detailed hook scoring breakdown."""
    total: float  # 0-100 overall score

    # Component scores (0-1 normalized)
    action: float = 0.0      # Movement, activity in first frame
    curiosity: float = 0.0   # Curiosity gap, question, mystery
    emotion: float = 0.0     # Emotional impact, connection
    audio_impact: float = 0.0  # Sound/music/voice impact
    visual_variety: float = 0.0  # Scene interest, contrast
    text_hook: float = 0.0   # Text overlay effectiveness

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": round(self.total, 1),
            "components": {
                "action": round(self.action, 3),
                "curiosity": round(self.curiosity, 3),
                "emotion": round(self.emotion, 3),
                "audio_impact": round(self.audio_impact, 3),
                "visual_variety": round(self.visual_variety, 3),
                "text_hook": round(self.text_hook, 3)
            }
        }


@dataclass
class HookImprovement:
    """A suggested improvement for the hook."""
    type: HookImprovementType
    priority: int  # 1 = highest priority
    description: str
    expected_impact: str  # "low", "medium", "high"
    implementation_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "priority": self.priority,
            "description": self.description,
            "expected_impact": self.expected_impact,
            "implementation_notes": self.implementation_notes
        }


@dataclass
class HookVariant:
    """An alternative hook variant suggestion."""
    id: str
    description: str
    hook_type: str  # "question", "statement", "pattern_interrupt", "story", "statistic"
    text_overlay: Optional[str] = None
    music_suggestion: Optional[str] = None
    shot_order: Optional[List[str]] = None
    estimated_improvement: float = 0.0  # Predicted % improvement

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "hook_type": self.hook_type,
            "text_overlay": self.text_overlay,
            "music_suggestion": self.music_suggestion,
            "shot_order": self.shot_order,
            "estimated_improvement": round(self.estimated_improvement, 1)
        }


@dataclass
class ABTestRecord:
    """Record of A/B test for hook variants."""
    test_id: str
    video_id: str
    created_at: str
    variants: List[Dict[str, Any]]  # variant_id, views, watch_time, engagement
    status: str = "active"  # active, completed, paused
    winner_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "video_id": self.video_id,
            "created_at": self.created_at,
            "status": self.status,
            "variants": self.variants,
            "winner_id": self.winner_id
        }


@dataclass
class HookConfig:
    """Configuration for hook analysis."""
    hook_duration: float = HOOK_DURATION
    platform: str = "tiktok"
    generate_variants: bool = True
    variant_count: int = 3
    include_ab_test_setup: bool = False


@dataclass
class HookAnalysisResult:
    """Complete hook analysis result."""
    video_path: str
    hook_duration: float

    # Scoring
    score: HookScore
    grade: str  # A, B, C, D, F

    # Analysis
    transcript_snippet: str
    detected_patterns: List[str]
    emotional_words: List[str]

    # Improvements
    improvements: List[HookImprovement]

    # Variants
    variants: List[HookVariant]

    # Platform recommendations
    platform: str
    platform_tips: List[str]

    # A/B test setup (optional)
    ab_test: Optional[ABTestRecord] = None

    # Processing
    processing_time_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "video_path": self.video_path,
            "hook_duration": self.hook_duration,
            "score": self.score.to_dict(),
            "grade": self.grade,
            "transcript_snippet": self.transcript_snippet[:200] if self.transcript_snippet else "",
            "detected_patterns": self.detected_patterns,
            "emotional_words": self.emotional_words[:10],
            "improvements": [i.to_dict() for i in self.improvements],
            "variants": [v.to_dict() for v in self.variants],
            "platform": self.platform,
            "platform_tips": self.platform_tips,
            "ab_test": self.ab_test.to_dict() if self.ab_test else None,
            "processing_time_seconds": round(self.processing_time_seconds, 2)
        }


# ============================================================================
# Scoring Functions
# ============================================================================

def score_hook_action(
    motion_intensity: float,
    scene_changes: int,
    has_face: bool = False
) -> float:
    """
    Score the action/movement in the hook.

    High action = grabbing attention immediately.
    """
    score = 0.0

    # Motion contributes most
    score += motion_intensity * 0.5

    # Scene changes add variety
    if scene_changes == 1:
        score += 0.2  # One cut is good
    elif scene_changes >= 2:
        score += 0.3  # Multiple cuts = dynamic

    # Face visibility helps connection
    if has_face:
        score += 0.2

    return min(1.0, score)


def score_hook_curiosity(
    text: str,
    patterns_found: List[str]
) -> float:
    """
    Score the curiosity-inducing elements.

    Questions, mysteries, and open loops.
    """
    if not text:
        return 0.0

    score = 0.0
    text_lower = text.lower()

    # Patterns found boost score
    score += len(patterns_found) * 0.15

    # Question marks are powerful
    if "?" in text:
        score += 0.2

    # Open loops / incomplete statements
    open_loop_words = ["what if", "imagine", "secret", "nobody", "hidden", "revealed"]
    for word in open_loop_words:
        if word in text_lower:
            score += 0.1

    # Numbers create specificity
    if re.search(r'\d+', text):
        score += 0.1

    return min(1.0, score)


def score_hook_emotion(
    text: str,
    emotional_words: List[str],
    audio_energy: float
) -> float:
    """
    Score the emotional impact of the hook.
    """
    score = 0.0

    # Emotional words presence
    if emotional_words:
        score += min(0.4, len(emotional_words) * 0.1)

    # Audio energy adds emotional weight
    score += audio_energy * 0.3

    # Direct address ("you") creates connection
    if text and re.search(r'\byou(r)?\b', text.lower()):
        score += 0.15

    # Urgency words
    urgency = ["now", "today", "stop", "wait", "don't"]
    for word in urgency:
        if text and word in text.lower():
            score += 0.1
            break

    return min(1.0, score)


def score_hook_audio(
    audio_energy: float,
    has_voice: bool = True,
    has_music: bool = False
) -> float:
    """
    Score the audio impact of the hook.
    """
    score = 0.0

    # Base energy level
    score += audio_energy * 0.4

    # Voice engagement
    if has_voice:
        score += 0.3

    # Music presence (platform-dependent)
    if has_music:
        score += 0.2

    # Strong opening audio (high energy start)
    if audio_energy > 0.7:
        score += 0.1

    return min(1.0, score)


def calculate_hook_score(
    motion_intensity: float,
    scene_changes: int,
    audio_energy: float,
    text: str,
    patterns_found: List[str],
    emotional_words: List[str]
) -> HookScore:
    """
    Calculate comprehensive hook score.
    """
    action = score_hook_action(motion_intensity, scene_changes)
    curiosity = score_hook_curiosity(text, patterns_found)
    emotion = score_hook_emotion(text, emotional_words, audio_energy)
    audio_impact = score_hook_audio(audio_energy)

    # Visual variety from scene changes
    visual_variety = min(1.0, scene_changes / 2)

    # Text hook (if text present in first second)
    text_hook = 0.5 if text and len(text.split()) >= 3 else 0.0

    # Weighted total
    total = (
        action * 0.20 +
        curiosity * 0.25 +
        emotion * 0.20 +
        audio_impact * 0.15 +
        visual_variety * 0.10 +
        text_hook * 0.10
    ) * 100

    return HookScore(
        total=total,
        action=action,
        curiosity=curiosity,
        emotion=emotion,
        audio_impact=audio_impact,
        visual_variety=visual_variety,
        text_hook=text_hook
    )


def get_grade(score: float) -> str:
    """Convert score to letter grade."""
    if score >= 90:
        return "A+"
    elif score >= 80:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 60:
        return "C"
    elif score >= 50:
        return "D"
    else:
        return "F"


# ============================================================================
# Improvement Generation
# ============================================================================

def generate_improvements(
    score: HookScore,
    platform: str,
    text: str
) -> List[HookImprovement]:
    """
    Generate specific improvements based on weak areas.
    """
    improvements = []
    priority = 1

    platform_config = PLATFORM_HOOK_TIPS.get(platform, PLATFORM_HOOK_TIPS["tiktok"])

    # Low action score
    if score.action < 0.5:
        improvements.append(HookImprovement(
            type=HookImprovementType.ADD_PATTERN_INTERRUPT,
            priority=priority,
            description="Start with immediate movement or action",
            expected_impact="high",
            implementation_notes="Consider starting mid-action rather than static setup"
        ))
        priority += 1

    # Low curiosity score
    if score.curiosity < 0.5:
        improvements.append(HookImprovement(
            type=HookImprovementType.ADD_CURIOSITY_GAP,
            priority=priority,
            description="Add a question or incomplete statement",
            expected_impact="high",
            implementation_notes="Start with 'What if...' or 'The problem with...' to create intrigue"
        ))
        priority += 1

    # Low emotion score
    if score.emotion < 0.5:
        improvements.append(HookImprovement(
            type=HookImprovementType.INCREASE_ENERGY,
            priority=priority,
            description="Increase emotional intensity",
            expected_impact="medium",
            implementation_notes="Use more expressive delivery or add emotional words"
        ))
        priority += 1

    # Low audio impact
    if score.audio_impact < 0.5:
        if platform_config["music_important"]:
            improvements.append(HookImprovement(
                type=HookImprovementType.CHANGE_MUSIC,
                priority=priority,
                description="Add or change background music",
                expected_impact="medium",
                implementation_notes=f"For {platform}, trending audio can significantly boost reach"
            ))
            priority += 1

    # Low text hook score
    if score.text_hook < 0.5 and platform_config["text_overlay"]:
        improvements.append(HookImprovement(
            type=HookImprovementType.ADD_TEXT_OVERLAY,
            priority=priority,
            description="Add text overlay in first 0.5 seconds",
            expected_impact="high",
            implementation_notes="Bold, contrasting text that states the value proposition"
        ))
        priority += 1

    # Low visual variety
    if score.visual_variety < 0.5:
        improvements.append(HookImprovement(
            type=HookImprovementType.CHANGE_OPENING_SHOT,
            priority=priority,
            description="Use a more visually striking opening shot",
            expected_impact="medium",
            implementation_notes="Consider face close-up or action shot instead of wide"
        ))
        priority += 1

    # Sort by priority
    improvements.sort(key=lambda x: x.priority)

    return improvements[:5]  # Top 5 improvements


# ============================================================================
# Variant Generation
# ============================================================================

def generate_hook_variants(
    original_text: str,
    topic: str,
    score: HookScore,
    count: int = 3
) -> List[HookVariant]:
    """
    Generate alternative hook variants.
    """
    variants = []

    # Extract topic if not provided
    if not topic and original_text:
        words = original_text.split()[:5]
        topic = " ".join(words)

    # Variant 1: Question Hook
    variants.append(HookVariant(
        id=str(uuid.uuid4())[:8],
        description="Open with a compelling question",
        hook_type="question",
        text_overlay=f"Are you making this {topic or 'fitness'} mistake?",
        music_suggestion="Trending audio with build-up",
        shot_order=["close-up face", "reveal shot", "action"],
        estimated_improvement=15.0
    ))

    # Variant 2: Statement/Fact Hook
    variants.append(HookVariant(
        id=str(uuid.uuid4())[:8],
        description="Start with a bold statement or statistic",
        hook_type="statistic",
        text_overlay=f"90% of people get {topic or 'this'} wrong",
        music_suggestion="Dramatic intro sound",
        shot_order=["text reveal", "face reaction", "demonstration"],
        estimated_improvement=12.0
    ))

    # Variant 3: Pattern Interrupt
    variants.append(HookVariant(
        id=str(uuid.uuid4())[:8],
        description="Pattern interrupt with unexpected element",
        hook_type="pattern_interrupt",
        text_overlay="STOP scrolling if you want to...",
        music_suggestion="Sudden sound effect + beat drop",
        shot_order=["action mid-movement", "pause", "direct address"],
        estimated_improvement=18.0
    ))

    # Variant 4: Story Hook (if count > 3)
    if count > 3:
        variants.append(HookVariant(
            id=str(uuid.uuid4())[:8],
            description="Personal story opening",
            hook_type="story",
            text_overlay=None,
            music_suggestion="Emotional background music",
            shot_order=["face close-up", "b-roll flashback", "present day"],
            estimated_improvement=10.0
        ))

    return variants[:count]


# ============================================================================
# A/B Test Setup
# ============================================================================

# In-memory storage for A/B tests (would use database in production)
_ab_tests: Dict[str, ABTestRecord] = {}


def create_ab_test(
    video_id: str,
    variants: List[HookVariant]
) -> ABTestRecord:
    """
    Create a new A/B test for hook variants.
    """
    test_id = str(uuid.uuid4())[:12]

    variant_records = [
        {
            "variant_id": v.id,
            "description": v.description,
            "views": 0,
            "avg_watch_time": 0.0,
            "engagement_rate": 0.0,
            "conversions": 0
        }
        for v in variants
    ]

    # Add original as control
    variant_records.insert(0, {
        "variant_id": "original",
        "description": "Original hook (control)",
        "views": 0,
        "avg_watch_time": 0.0,
        "engagement_rate": 0.0,
        "conversions": 0
    })

    test = ABTestRecord(
        test_id=test_id,
        video_id=video_id,
        created_at=datetime.utcnow().isoformat(),
        variants=variant_records,
        status="active"
    )

    _ab_tests[test_id] = test

    return test


def record_ab_test_result(
    test_id: str,
    variant_id: str,
    views: int = 1,
    watch_time: float = 0.0,
    engagement: bool = False
):
    """
    Record a result for an A/B test variant.
    """
    if test_id not in _ab_tests:
        return None

    test = _ab_tests[test_id]

    for variant in test.variants:
        if variant["variant_id"] == variant_id:
            variant["views"] += views
            if watch_time > 0:
                # Running average
                old_avg = variant["avg_watch_time"]
                old_count = variant["views"] - views
                variant["avg_watch_time"] = (old_avg * old_count + watch_time) / variant["views"]
            if engagement:
                variant["conversions"] += 1
                variant["engagement_rate"] = variant["conversions"] / variant["views"]
            break

    return test


def get_ab_test(test_id: str) -> Optional[ABTestRecord]:
    """Get A/B test by ID."""
    return _ab_tests.get(test_id)


def list_ab_tests(video_id: Optional[str] = None) -> List[ABTestRecord]:
    """List all A/B tests, optionally filtered by video."""
    if video_id:
        return [t for t in _ab_tests.values() if t.video_id == video_id]
    return list(_ab_tests.values())


# ============================================================================
# Main Analysis Function
# ============================================================================

async def analyze_hook(
    video_path: str,
    transcription_result: Optional[Dict[str, Any]] = None,
    config: Optional[HookConfig] = None
) -> HookAnalysisResult:
    """
    Analyze the first 3 seconds (hook) of a video.

    Args:
        video_path: Path to video file
        transcription_result: Optional transcription with word timestamps
        config: Hook analysis configuration

    Returns:
        HookAnalysisResult with scores, improvements, and variants
    """
    import time
    start_time = time.time()

    if config is None:
        config = HookConfig()

    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    duration = await get_video_duration(str(video_path))
    hook_end = min(config.hook_duration, duration)

    logger.info(
        f"Analyzing hook: {video_path.name}",
        extra={"metadata": {"hook_duration": hook_end, "platform": config.platform}}
    )

    # Run video analysis for hook segment
    analysis_config = AnalysisConfig(
        analyze_audio=True,
        analyze_motion=True,
        detect_scenes=True,
        extract_keywords=transcription_result is not None,
        min_segment_duration=hook_end,
        max_segment_duration=hook_end + 1
    )

    video_analysis = await analyze_video(
        str(video_path),
        transcription_result=transcription_result,
        config=analysis_config
    )

    # Extract hook segment data
    hook_motion = 0.5
    hook_audio = 0.5
    scene_changes = 0

    for point in video_analysis.motion_points:
        if point.timestamp <= hook_end:
            hook_motion = max(hook_motion, point.intensity)

    for point in video_analysis.audio_energy:
        if point.timestamp <= hook_end:
            hook_audio = max(hook_audio, point.energy)

    for sc in video_analysis.scene_changes:
        if sc.timestamp <= hook_end:
            scene_changes += 1

    # Get hook text from transcription
    hook_text = ""
    if transcription_result:
        words = transcription_result.get("words", [])
        hook_words = [w.get("word", "") for w in words if w.get("start", 0) <= hook_end]
        hook_text = " ".join(hook_words)

    # Analyze hook patterns
    hook_strength, patterns_found = analyze_hook_strength(hook_text)
    emotion_score, emotional_words = detect_emotional_markers(hook_text)

    # Calculate comprehensive score
    score = calculate_hook_score(
        motion_intensity=hook_motion,
        scene_changes=scene_changes,
        audio_energy=hook_audio,
        text=hook_text,
        patterns_found=patterns_found,
        emotional_words=emotional_words
    )

    grade = get_grade(score.total)

    # Generate improvements
    improvements = generate_improvements(score, config.platform, hook_text)

    # Generate variants
    variants = []
    if config.generate_variants:
        topic = extract_topic(hook_text)
        variants = generate_hook_variants(
            original_text=hook_text,
            topic=topic,
            score=score,
            count=config.variant_count
        )

    # Set up A/B test if requested
    ab_test = None
    if config.include_ab_test_setup and variants:
        video_id = str(uuid.uuid4())[:12]
        ab_test = create_ab_test(video_id, variants)

    # Get platform tips
    platform_config = PLATFORM_HOOK_TIPS.get(config.platform, PLATFORM_HOOK_TIPS["tiktok"])
    platform_tips = platform_config.get("tips", [])

    processing_time = time.time() - start_time

    logger.info(
        f"Hook analysis complete",
        extra={
            "metadata": {
                "score": round(score.total, 1),
                "grade": grade,
                "improvements": len(improvements),
                "variants": len(variants),
                "processing_time": round(processing_time, 2)
            }
        }
    )

    log_job_event(
        job_id="hook_analysis",
        event="completed",
        job_type="hook_analysis",
        score=score.total,
        grade=grade,
        processing_time=processing_time
    )

    return HookAnalysisResult(
        video_path=str(video_path),
        hook_duration=hook_end,
        score=score,
        grade=grade,
        transcript_snippet=hook_text,
        detected_patterns=patterns_found,
        emotional_words=emotional_words,
        improvements=improvements,
        variants=variants,
        platform=config.platform,
        platform_tips=platform_tips,
        ab_test=ab_test,
        processing_time_seconds=processing_time
    )


def extract_topic(text: str) -> str:
    """Extract main topic from hook text."""
    if not text:
        return "fitness"

    # Remove common words
    stop_words = {"the", "a", "an", "is", "are", "to", "in", "on", "at", "for", "this", "that"}
    words = [w for w in text.lower().split() if w not in stop_words and len(w) > 3]

    if words:
        return words[0]
    return "fitness"


# ============================================================================
# Convenience Functions
# ============================================================================

async def quick_hook_score(
    video_path: str,
    transcription_result: Optional[Dict[str, Any]] = None
) -> float:
    """
    Get quick hook score (0-100) for a video.

    Convenience function for fast scoring.
    """
    config = HookConfig(generate_variants=False, include_ab_test_setup=False)
    result = await analyze_hook(video_path, transcription_result, config)
    return result.score.total


async def get_hook_improvements(
    video_path: str,
    platform: str = "tiktok",
    transcription_result: Optional[Dict[str, Any]] = None
) -> List[HookImprovement]:
    """
    Get improvement suggestions for a hook.

    Convenience function for quick improvements.
    """
    config = HookConfig(platform=platform, generate_variants=False)
    result = await analyze_hook(video_path, transcription_result, config)
    return result.improvements


async def compare_hooks(
    video_paths: List[str],
    transcription_results: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Compare hooks across multiple videos.

    Useful for choosing the best version.
    """
    results = []

    for i, path in enumerate(video_paths):
        trans = transcription_results[i] if transcription_results and i < len(transcription_results) else None

        result = await analyze_hook(path, trans)
        results.append({
            "video_path": path,
            "score": result.score.total,
            "grade": result.grade,
            "summary": {
                "action": result.score.action,
                "curiosity": result.score.curiosity,
                "emotion": result.score.emotion,
                "audio": result.score.audio_impact
            }
        })

    # Sort by score
    results.sort(key=lambda x: x["score"], reverse=True)

    return results
