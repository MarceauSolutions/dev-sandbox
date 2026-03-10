#!/usr/bin/env python3
"""
Retention Curve Predictor for Fitness Influencer AI v2.0

Predicts audience retention before publishing. Identifies drop-off points
and suggests edits to improve viewer retention.

Features:
    - Retention curve prediction (0-100% at each timestamp)
    - Cliff detection (>10% sudden drops)
    - Platform benchmarks comparison (TikTok, YouTube, Instagram)
    - Improvement suggestions for each cliff moment
    - Integration with video analyzer and hook analyzer

Usage:
    from backend.retention_predictor import predict_retention, RetentionConfig

    result = await predict_retention(
        video_path="/path/to/video.mp4",
        transcription_result=transcription
    )

    print(f"Overall Score: {result.overall_score}/100")
    for cliff in result.cliffs:
        print(f"Cliff at {cliff.timestamp}s: {cliff.drop_percent}% drop")
"""

import asyncio
import math
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from backend.logging_config import get_logger, log_job_event
from backend.video_analyzer import (
    analyze_video,
    AnalysisConfig,
    VideoAnalysisResult,
    get_video_duration,
    format_duration
)
from backend.hook_analyzer import (
    analyze_hook,
    HookConfig,
    HookAnalysisResult
)

logger = get_logger(__name__)


# ============================================================================
# Configuration
# ============================================================================

# Platform retention benchmarks (% at end of video considered "good")
PLATFORM_BENCHMARKS = {
    "tiktok": {
        "excellent": 60,
        "good": 50,
        "average": 35,
        "poor": 20,
        "video_length_sweet_spot": (15, 60),  # seconds
        "description": "TikTok viewers expect fast-paced, high-energy content"
    },
    "instagram_reels": {
        "excellent": 55,
        "good": 40,
        "average": 30,
        "poor": 15,
        "video_length_sweet_spot": (15, 90),  # seconds
        "description": "Instagram Reels viewers prefer polished, aesthetic content"
    },
    "youtube_shorts": {
        "excellent": 55,
        "good": 45,
        "average": 35,
        "poor": 20,
        "video_length_sweet_spot": (30, 60),  # seconds
        "description": "YouTube Shorts viewers expect informative, value-packed content"
    },
    "youtube": {
        "excellent": 50,
        "good": 40,
        "average": 30,
        "poor": 15,
        "video_length_sweet_spot": (480, 1200),  # 8-20 minutes
        "description": "YouTube viewers expect structured, in-depth content"
    }
}

# Cliff threshold (percentage drop to flag as significant)
CLIFF_THRESHOLD = 10.0

# Retention decay factors by content type
CONTENT_DECAY_FACTORS = {
    "intro": 0.85,          # Intros tend to lose viewers
    "main_content": 1.02,   # Good content retains/gains
    "demonstration": 1.05,  # Demos often boost retention
    "transition": 0.90,     # Transitions lose some viewers
    "climax": 1.08,         # High energy retains viewers
    "conclusion": 0.75,     # Conclusions see drop-off
    "unknown": 0.95         # Default slight decay
}

# Improvement suggestion templates
IMPROVEMENT_SUGGESTIONS = {
    "slow_intro": {
        "description": "Slow or boring introduction",
        "suggestions": [
            "Start with your most engaging moment (pattern interrupt)",
            "Add text hook overlay in first 0.5 seconds",
            "Cut the first 2-3 seconds and start with action",
            "Lead with a question or bold statement"
        ]
    },
    "low_energy": {
        "description": "Low energy section causing viewer fatigue",
        "suggestions": [
            "Add jump cuts to increase pacing",
            "Add background music or increase audio energy",
            "Insert B-roll footage to add visual variety",
            "Consider removing or shortening this section"
        ]
    },
    "long_talking": {
        "description": "Extended talking without visual variety",
        "suggestions": [
            "Add text overlays to highlight key points",
            "Insert relevant B-roll or demonstrations",
            "Break into multiple shorter segments",
            "Add zoom effects or camera movements"
        ]
    },
    "transition_drop": {
        "description": "Poor transition causing viewer drop-off",
        "suggestions": [
            "Use jump cut instead of fade transition",
            "Add transitional text or graphic",
            "Tighten the edit to remove dead space",
            "Preview next segment before transitioning"
        ]
    },
    "conclusion_falloff": {
        "description": "Viewers leaving before call-to-action",
        "suggestions": [
            "Move CTA earlier in the video",
            "Add visual interest to ending",
            "Tease upcoming content to retain viewers",
            "Add end screen with clickable elements"
        ]
    },
    "pacing_issue": {
        "description": "Inconsistent pacing causing attention drift",
        "suggestions": [
            "Standardize clip lengths (2-4 seconds)",
            "Add more frequent scene changes",
            "Remove filler words and pauses",
            "Match audio peaks with visual cuts"
        ]
    },
    "content_gap": {
        "description": "Content not meeting viewer expectations",
        "suggestions": [
            "Ensure hook promise is delivered quickly",
            "Add more value in this section",
            "Consider restructuring content order",
            "Add payoff moment to maintain interest"
        ]
    }
}


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class RetentionPoint:
    """A point on the retention curve."""
    timestamp: float  # seconds
    retention_percent: float  # 0-100
    segment_type: str = "unknown"  # From video analysis
    energy_level: float = 0.5  # Normalized 0-1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": round(self.timestamp, 2),
            "timestamp_formatted": format_duration(self.timestamp),
            "retention_percent": round(self.retention_percent, 1),
            "segment_type": self.segment_type,
            "energy_level": round(self.energy_level, 3)
        }


@dataclass
class RetentionCliff:
    """A significant drop in retention."""
    timestamp: float  # When the cliff starts
    drop_percent: float  # How much retention dropped (positive number)
    before_retention: float  # Retention before cliff
    after_retention: float  # Retention after cliff
    cause: str  # Predicted cause
    suggestions: List[str]  # Improvement suggestions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": round(self.timestamp, 2),
            "timestamp_formatted": format_duration(self.timestamp),
            "drop_percent": round(self.drop_percent, 1),
            "before_retention": round(self.before_retention, 1),
            "after_retention": round(self.after_retention, 1),
            "cause": self.cause,
            "suggestions": self.suggestions
        }


@dataclass
class PlatformComparison:
    """Comparison against platform benchmarks."""
    platform: str
    final_retention: float
    benchmark_good: float
    benchmark_excellent: float
    rating: str  # excellent, good, average, poor
    vs_benchmark: float  # Difference from "good" benchmark
    sweet_spot_match: bool  # Is video length in ideal range

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "final_retention": round(self.final_retention, 1),
            "benchmark_good": self.benchmark_good,
            "benchmark_excellent": self.benchmark_excellent,
            "rating": self.rating,
            "vs_benchmark": round(self.vs_benchmark, 1),
            "sweet_spot_match": self.sweet_spot_match
        }


@dataclass
class RetentionConfig:
    """Configuration for retention prediction."""
    platform: str = "tiktok"
    sample_interval: float = 1.0  # Sample every N seconds
    include_hook_analysis: bool = True
    cliff_threshold: float = CLIFF_THRESHOLD
    generate_suggestions: bool = True


@dataclass
class RetentionPrediction:
    """Complete retention prediction result."""
    video_path: str
    duration: float
    platform: str

    # The retention curve
    curve: List[RetentionPoint]

    # Key metrics
    overall_score: float  # 0-100 based on area under curve
    final_retention: float  # % retained at end
    average_retention: float  # Average across video

    # Cliffs (drop-off points)
    cliffs: List[RetentionCliff]

    # Platform comparison
    platform_comparison: PlatformComparison

    # Hook analysis integration
    hook_score: Optional[float] = None
    hook_impact: str = "unknown"  # positive, neutral, negative

    # Overall grade
    grade: str = "C"

    # Processing metadata
    analyzed_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "video_path": self.video_path,
            "duration": round(self.duration, 2),
            "duration_formatted": format_duration(self.duration),
            "platform": self.platform,

            "curve": [p.to_dict() for p in self.curve],
            "curve_summary": {
                "points": len(self.curve),
                "min_retention": round(min(p.retention_percent for p in self.curve), 1) if self.curve else 0,
                "max_retention": 100.0,
                "average_retention": round(self.average_retention, 1)
            },

            "overall_score": round(self.overall_score, 1),
            "final_retention": round(self.final_retention, 1),
            "average_retention": round(self.average_retention, 1),

            "cliffs": [c.to_dict() for c in self.cliffs],
            "cliff_count": len(self.cliffs),

            "platform_comparison": self.platform_comparison.to_dict(),

            "hook_score": round(self.hook_score, 1) if self.hook_score else None,
            "hook_impact": self.hook_impact,

            "grade": self.grade,
            "analyzed_at": self.analyzed_at
        }


# ============================================================================
# Core Functions
# ============================================================================

async def predict_retention(
    video_path: str,
    transcription_result: Optional[Dict[str, Any]] = None,
    video_analysis: Optional[VideoAnalysisResult] = None,
    hook_analysis: Optional[HookAnalysisResult] = None,
    config: Optional[RetentionConfig] = None
) -> RetentionPrediction:
    """
    Predict audience retention curve for a video.

    Analyzes video structure, pacing, and content to predict where
    viewers are likely to drop off and why.

    Args:
        video_path: Path to video file
        transcription_result: Optional pre-transcribed content
        video_analysis: Optional pre-computed video analysis
        hook_analysis: Optional pre-computed hook analysis
        config: Retention prediction configuration

    Returns:
        RetentionPrediction with curve, cliffs, and suggestions
    """
    config = config or RetentionConfig()

    logger.info(f"Predicting retention for: {video_path}")

    # Get video duration
    duration = await get_video_duration(video_path)
    if duration <= 0:
        raise ValueError(f"Invalid video duration: {duration}")

    logger.info(f"Video duration: {format_duration(duration)}")

    # Run video analysis if not provided
    if video_analysis is None:
        analysis_config = AnalysisConfig(
            analyze_audio=True,
            analyze_motion=True,
            detect_scenes=True,
            extract_keywords=False  # Not needed for retention
        )
        video_analysis = await analyze_video(
            video_path=video_path,
            transcription_result=transcription_result,
            config=analysis_config
        )

    # Run hook analysis if requested and not provided
    hook_score = None
    if config.include_hook_analysis and hook_analysis is None:
        try:
            hook_config = HookConfig(
                platform=config.platform,
                generate_variants=False  # Just need the score
            )
            hook_analysis = await analyze_hook(
                video_path=video_path,
                transcription_result=transcription_result,
                config=hook_config
            )
            hook_score = hook_analysis.score.total
        except Exception as e:
            logger.warning(f"Hook analysis failed, continuing without: {e}")
    elif hook_analysis:
        hook_score = hook_analysis.score.total

    # Build retention curve
    curve = await _build_retention_curve(
        video_analysis=video_analysis,
        duration=duration,
        hook_score=hook_score,
        sample_interval=config.sample_interval
    )

    # Detect cliffs
    cliffs = _detect_cliffs(
        curve=curve,
        video_analysis=video_analysis,
        threshold=config.cliff_threshold,
        generate_suggestions=config.generate_suggestions
    )

    # Calculate metrics
    overall_score, final_retention, average_retention = _calculate_metrics(curve)

    # Compare against platform benchmarks
    platform_comparison = _compare_to_benchmarks(
        final_retention=final_retention,
        duration=duration,
        platform=config.platform
    )

    # Determine hook impact
    hook_impact = _assess_hook_impact(curve, hook_score)

    # Calculate grade
    grade = _calculate_grade(overall_score, platform_comparison.rating)

    result = RetentionPrediction(
        video_path=video_path,
        duration=duration,
        platform=config.platform,
        curve=curve,
        overall_score=overall_score,
        final_retention=final_retention,
        average_retention=average_retention,
        cliffs=cliffs,
        platform_comparison=platform_comparison,
        hook_score=hook_score,
        hook_impact=hook_impact,
        grade=grade,
        analyzed_at=datetime.utcnow().isoformat()
    )

    logger.info(
        f"Retention prediction complete: "
        f"score={overall_score:.1f}, grade={grade}, "
        f"cliffs={len(cliffs)}, final={final_retention:.1f}%"
    )

    return result


async def _build_retention_curve(
    video_analysis: VideoAnalysisResult,
    duration: float,
    hook_score: Optional[float],
    sample_interval: float
) -> List[RetentionPoint]:
    """
    Build predicted retention curve based on video analysis.

    Uses a model based on:
    - Hook strength (first 3 seconds)
    - Segment types (intro, main content, etc.)
    - Audio energy levels
    - Scene changes (variety)
    - Pacing patterns
    """
    curve = []
    current_retention = 100.0

    # Initial hook impact (first 3 seconds)
    if hook_score is not None:
        # Strong hooks retain more viewers initially
        # Weak hooks (<50) cause immediate drop
        if hook_score >= 80:
            initial_drop = 2.0  # Excellent hook
        elif hook_score >= 65:
            initial_drop = 5.0  # Good hook
        elif hook_score >= 50:
            initial_drop = 10.0  # Average hook
        else:
            initial_drop = 18.0  # Weak hook - significant early drop
    else:
        initial_drop = 8.0  # Default moderate drop

    # Apply initial hook impact
    current_retention = 100.0 - initial_drop

    # Build segment map for quick lookup
    segment_map = {}
    for segment in video_analysis.segments:
        start_sec = int(segment.start_time)
        end_sec = int(segment.end_time)
        for sec in range(start_sec, end_sec + 1):
            segment_map[sec] = {
                "type": segment.segment_type.value if hasattr(segment.segment_type, 'value') else str(segment.segment_type),
                "energy": segment.combined_score / 100.0 if segment.combined_score else 0.5
            }

    # Build audio energy map
    energy_map = {}
    for peak in video_analysis.audio_peaks:
        sec = int(peak.timestamp)
        energy_map[sec] = peak.energy

    # Generate curve points
    timestamp = 0.0
    while timestamp <= duration:
        sec = int(timestamp)

        # Get segment info at this timestamp
        segment_info = segment_map.get(sec, {"type": "unknown", "energy": 0.5})
        segment_type = segment_info["type"]
        energy_level = energy_map.get(sec, segment_info["energy"])

        if timestamp > 0:
            # Apply decay factor based on content type
            base_decay = CONTENT_DECAY_FACTORS.get(segment_type, 0.95)

            # Energy modifier (high energy retains, low energy loses)
            energy_modifier = 0.98 + (energy_level * 0.04)  # Range: 0.98 - 1.02

            # Scene change bonus (variety helps retention)
            scene_change_bonus = 1.0
            for scene in video_analysis.scene_changes:
                if abs(scene.timestamp - timestamp) < sample_interval:
                    scene_change_bonus = 1.01  # Small boost for variety
                    break

            # Time decay (natural drop-off over time)
            # Faster at start, slower later (logarithmic)
            time_decay = 1.0 - (0.05 / (1 + math.log1p(timestamp / 10)))

            # Calculate new retention
            decay_factor = base_decay * energy_modifier * scene_change_bonus * time_decay
            current_retention = max(5.0, current_retention * decay_factor)

        curve.append(RetentionPoint(
            timestamp=timestamp,
            retention_percent=current_retention,
            segment_type=segment_type,
            energy_level=energy_level
        ))

        timestamp += sample_interval

    return curve


def _detect_cliffs(
    curve: List[RetentionPoint],
    video_analysis: VideoAnalysisResult,
    threshold: float,
    generate_suggestions: bool
) -> List[RetentionCliff]:
    """Detect significant drop-off points in retention curve."""
    cliffs = []

    for i in range(1, len(curve)):
        prev_point = curve[i - 1]
        curr_point = curve[i]

        drop = prev_point.retention_percent - curr_point.retention_percent

        if drop >= threshold:
            # Determine cause based on segment type and context
            cause, suggestion_key = _diagnose_cliff_cause(
                timestamp=curr_point.timestamp,
                segment_type=curr_point.segment_type,
                energy_level=curr_point.energy_level,
                drop_percent=drop,
                video_analysis=video_analysis
            )

            suggestions = []
            if generate_suggestions and suggestion_key in IMPROVEMENT_SUGGESTIONS:
                suggestions = IMPROVEMENT_SUGGESTIONS[suggestion_key]["suggestions"]

            cliffs.append(RetentionCliff(
                timestamp=prev_point.timestamp,
                drop_percent=drop,
                before_retention=prev_point.retention_percent,
                after_retention=curr_point.retention_percent,
                cause=cause,
                suggestions=suggestions
            ))

    return cliffs


def _diagnose_cliff_cause(
    timestamp: float,
    segment_type: str,
    energy_level: float,
    drop_percent: float,
    video_analysis: VideoAnalysisResult
) -> Tuple[str, str]:
    """
    Diagnose the cause of a retention cliff.

    Returns:
        Tuple of (human-readable cause, suggestion_key)
    """
    # First 5 seconds - likely hook issue
    if timestamp < 5:
        return "Weak hook not engaging viewers", "slow_intro"

    # Transition segment
    if segment_type == "transition":
        return "Poor transition causing viewer drop-off", "transition_drop"

    # Conclusion/ending
    if segment_type == "conclusion":
        return "Viewers leaving before end/CTA", "conclusion_falloff"

    # Low energy section
    if energy_level < 0.3:
        return "Low energy section causing viewer fatigue", "low_energy"

    # Intro dragging on
    if segment_type == "intro" and timestamp > 10:
        return "Extended introduction losing viewer interest", "slow_intro"

    # Large drop (>15%) suggests content mismatch
    if drop_percent > 15:
        return "Content not meeting viewer expectations", "content_gap"

    # Default to pacing issue
    return "Pacing issue causing attention drift", "pacing_issue"


def _calculate_metrics(curve: List[RetentionPoint]) -> Tuple[float, float, float]:
    """
    Calculate overall metrics from retention curve.

    Returns:
        Tuple of (overall_score, final_retention, average_retention)
    """
    if not curve:
        return 0.0, 0.0, 0.0

    # Final retention (last point)
    final_retention = curve[-1].retention_percent

    # Average retention (mean of all points)
    average_retention = sum(p.retention_percent for p in curve) / len(curve)

    # Overall score: weighted combination
    # Area under curve (integral approximation) normalized to 0-100
    area = 0.0
    for i in range(1, len(curve)):
        width = curve[i].timestamp - curve[i-1].timestamp
        height = (curve[i].retention_percent + curve[i-1].retention_percent) / 2
        area += width * height

    max_area = curve[-1].timestamp * 100  # Perfect retention
    area_score = (area / max_area) * 100 if max_area > 0 else 0

    # Overall score: 40% area, 30% final, 30% average
    overall_score = (area_score * 0.4) + (final_retention * 0.3) + (average_retention * 0.3)

    return overall_score, final_retention, average_retention


def _compare_to_benchmarks(
    final_retention: float,
    duration: float,
    platform: str
) -> PlatformComparison:
    """Compare retention against platform benchmarks."""
    benchmark = PLATFORM_BENCHMARKS.get(platform, PLATFORM_BENCHMARKS["tiktok"])

    # Determine rating
    if final_retention >= benchmark["excellent"]:
        rating = "excellent"
    elif final_retention >= benchmark["good"]:
        rating = "good"
    elif final_retention >= benchmark["average"]:
        rating = "average"
    else:
        rating = "poor"

    # Check video length sweet spot
    sweet_spot = benchmark["video_length_sweet_spot"]
    sweet_spot_match = sweet_spot[0] <= duration <= sweet_spot[1]

    return PlatformComparison(
        platform=platform,
        final_retention=final_retention,
        benchmark_good=benchmark["good"],
        benchmark_excellent=benchmark["excellent"],
        rating=rating,
        vs_benchmark=final_retention - benchmark["good"],
        sweet_spot_match=sweet_spot_match
    )


def _assess_hook_impact(
    curve: List[RetentionPoint],
    hook_score: Optional[float]
) -> str:
    """Assess the impact of the hook on overall retention."""
    if hook_score is None:
        return "unknown"

    # Look at retention at 5 second mark
    retention_at_5s = 100.0
    for point in curve:
        if point.timestamp >= 5:
            retention_at_5s = point.retention_percent
            break

    # Strong hook (>75) should retain >85% at 5s
    if hook_score >= 75:
        if retention_at_5s >= 85:
            return "positive"
        else:
            return "neutral"  # Hook score doesn't match retention

    # Average hook (50-75) should retain >75% at 5s
    elif hook_score >= 50:
        if retention_at_5s >= 75:
            return "positive"
        else:
            return "negative"

    # Weak hook (<50) likely causing issues
    else:
        if retention_at_5s < 70:
            return "negative"
        else:
            return "neutral"


def _calculate_grade(overall_score: float, benchmark_rating: str) -> str:
    """Calculate overall grade combining score and benchmark."""
    # Score-based grade
    if overall_score >= 85:
        score_grade = "A"
    elif overall_score >= 70:
        score_grade = "B"
    elif overall_score >= 55:
        score_grade = "C"
    elif overall_score >= 40:
        score_grade = "D"
    else:
        score_grade = "F"

    # Adjust based on benchmark rating
    grade_order = ["F", "D", "C", "B", "A"]
    score_index = grade_order.index(score_grade)

    if benchmark_rating == "excellent":
        score_index = min(score_index + 1, 4)  # Boost grade
    elif benchmark_rating == "poor":
        score_index = max(score_index - 1, 0)  # Lower grade

    return grade_order[score_index]


# ============================================================================
# Utility Functions
# ============================================================================

def get_platform_benchmarks() -> Dict[str, Any]:
    """Get all platform benchmarks for reference."""
    return {
        platform: {
            "excellent": data["excellent"],
            "good": data["good"],
            "average": data["average"],
            "poor": data["poor"],
            "video_length_sweet_spot": {
                "min_seconds": data["video_length_sweet_spot"][0],
                "max_seconds": data["video_length_sweet_spot"][1]
            },
            "description": data["description"]
        }
        for platform, data in PLATFORM_BENCHMARKS.items()
    }


def get_improvement_types() -> Dict[str, Dict[str, Any]]:
    """Get all improvement suggestion types."""
    return {
        key: {
            "description": data["description"],
            "suggestion_count": len(data["suggestions"]),
            "suggestions": data["suggestions"]
        }
        for key, data in IMPROVEMENT_SUGGESTIONS.items()
    }


async def compare_retention_curves(
    curve_a: List[RetentionPoint],
    curve_b: List[RetentionPoint]
) -> Dict[str, Any]:
    """
    Compare two retention curves (e.g., for A/B testing).

    Returns comparison metrics including which performs better.
    """
    def calc_metrics(curve):
        if not curve:
            return {"final": 0, "average": 0, "area": 0}
        final = curve[-1].retention_percent
        avg = sum(p.retention_percent for p in curve) / len(curve)
        area = sum(
            (curve[i].timestamp - curve[i-1].timestamp) *
            (curve[i].retention_percent + curve[i-1].retention_percent) / 2
            for i in range(1, len(curve))
        )
        return {"final": final, "average": avg, "area": area}

    metrics_a = calc_metrics(curve_a)
    metrics_b = calc_metrics(curve_b)

    # Determine winner
    score_a = metrics_a["final"] * 0.4 + metrics_a["average"] * 0.3 + (metrics_a["area"] / max(metrics_a["area"], metrics_b["area"], 1)) * 30
    score_b = metrics_b["final"] * 0.4 + metrics_b["average"] * 0.3 + (metrics_b["area"] / max(metrics_a["area"], metrics_b["area"], 1)) * 30

    return {
        "curve_a": metrics_a,
        "curve_b": metrics_b,
        "winner": "A" if score_a > score_b else "B" if score_b > score_a else "tie",
        "score_difference": abs(score_a - score_b),
        "improvement_percent": round(((max(score_a, score_b) / min(score_a, score_b)) - 1) * 100, 1) if min(score_a, score_b) > 0 else 0
    }


# ============================================================================
# CLI for testing
# ============================================================================

if __name__ == "__main__":
    import sys

    async def main():
        if len(sys.argv) < 2:
            print("Usage: python retention_predictor.py <video_path> [platform]")
            sys.exit(1)

        video_path = sys.argv[1]
        platform = sys.argv[2] if len(sys.argv) > 2 else "tiktok"

        config = RetentionConfig(
            platform=platform,
            sample_interval=1.0,
            include_hook_analysis=True
        )

        result = await predict_retention(
            video_path=video_path,
            config=config
        )

        print(f"\n{'='*60}")
        print(f"RETENTION PREDICTION: {video_path}")
        print(f"{'='*60}")
        print(f"Duration: {format_duration(result.duration)}")
        print(f"Platform: {result.platform}")
        print(f"Grade: {result.grade}")
        print(f"Overall Score: {result.overall_score:.1f}/100")
        print(f"Final Retention: {result.final_retention:.1f}%")
        print(f"Average Retention: {result.average_retention:.1f}%")

        if result.hook_score:
            print(f"\nHook Score: {result.hook_score:.1f}/100")
            print(f"Hook Impact: {result.hook_impact}")

        print(f"\n--- Platform Comparison ({platform}) ---")
        pc = result.platform_comparison
        print(f"Rating: {pc.rating.upper()}")
        print(f"vs Good Benchmark: {pc.vs_benchmark:+.1f}%")
        print(f"Video Length Sweet Spot: {'Yes' if pc.sweet_spot_match else 'No'}")

        if result.cliffs:
            print(f"\n--- Retention Cliffs ({len(result.cliffs)}) ---")
            for i, cliff in enumerate(result.cliffs, 1):
                print(f"\n{i}. At {format_duration(cliff.timestamp)}: {cliff.drop_percent:.1f}% drop")
                print(f"   Cause: {cliff.cause}")
                if cliff.suggestions:
                    print(f"   Suggestions:")
                    for s in cliff.suggestions[:2]:
                        print(f"     - {s}")
        else:
            print("\n--- No significant retention cliffs detected ---")

        print(f"\n{'='*60}")

    asyncio.run(main())
