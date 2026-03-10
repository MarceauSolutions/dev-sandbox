#!/usr/bin/env python3
"""
Viral Moment Detection for Fitness Influencer AI v2.0

Scores video segments for viral potential and identifies the best clips
from long-form content using engagement prediction algorithms.

Features:
    - Viral score (0-100) based on multiple factors
    - Hook strength detection
    - Audio energy analysis
    - Visual variety scoring
    - Keyword density integration
    - Emotional marker detection
    - Fitness-specific boosters
    - Context-aware clip boundaries

Usage:
    from backend.viral_detector import detect_viral_moments, ViralConfig

    result = await detect_viral_moments(
        video_path="/path/to/video.mp4",
        transcription_result=transcription,
        top_count=10
    )

    for moment in result.moments:
        print(f"Viral Score: {moment.score:.1f} | {moment.start:.1f}s - {moment.end:.1f}s")
"""

import asyncio
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from backend.logging_config import get_logger, log_job_event
from backend.video_analyzer import (
    analyze_video,
    AnalysisConfig,
    ScoredSegment,
    VideoAnalysisResult,
    format_duration,
    FITNESS_KEYWORDS,
    get_video_duration
)

logger = get_logger(__name__)


# ============================================================================
# Configuration
# ============================================================================

# Clip duration constraints
MIN_CLIP_DURATION = 15.0  # Minimum clip duration in seconds
MAX_CLIP_DURATION = 60.0  # Maximum clip duration in seconds
IDEAL_CLIP_DURATION = 30.0  # Ideal clip duration for short-form

# Viral scoring weights
DEFAULT_WEIGHTS = {
    "hook_strength": 0.25,      # First 3 seconds impact
    "audio_energy": 0.15,       # Overall audio energy
    "visual_variety": 0.15,     # Scene changes, motion
    "keyword_density": 0.15,    # Speaking engagement
    "emotional_markers": 0.15,  # Emotional words/phrases
    "fitness_relevance": 0.15   # Fitness-specific content
}

# Emotional markers that boost viral potential
EMOTIONAL_MARKERS = {
    # Excitement
    "amazing", "incredible", "insane", "crazy", "unbelievable",
    "mind-blowing", "game-changer", "life-changing", "transformed",

    # Urgency
    "now", "today", "immediately", "right now", "asap",
    "before it's too late", "don't wait",

    # Pain points
    "struggle", "problem", "mistake", "wrong", "failing",
    "frustrated", "tired of", "sick of", "hate",

    # Success
    "success", "finally", "achieved", "results", "breakthrough",
    "changed my life", "works", "effective",

    # Curiosity
    "secret", "hidden", "unknown", "revealed", "discover",
    "truth", "nobody tells you", "what they don't want you to know",

    # Social proof
    "everyone", "millions", "viral", "trending", "popular",
    "expert", "professional", "proven"
}

# Hook patterns that indicate strong openings
HOOK_PATTERNS = [
    r"^(stop|wait|hold on|don't|never|always)",
    r"^(here's|this is|watch this|look at)",
    r"^(the secret|the truth|the reason|the problem)",
    r"^(you're|you've been|if you)",
    r"^(what if|how to|why you)",
    r"^(i was|i used to|i finally)",
    r"\d+ (ways|tips|secrets|mistakes|things)",
]

# Fitness transformation markers
FITNESS_TRANSFORMATION_MARKERS = {
    "before and after", "transformation", "progress", "results",
    "lost pounds", "gained muscle", "body recomp", "physique",
    "journey", "week challenge", "day challenge", "month",
    "pounds down", "inches", "body fat", "lean", "shredded"
}


# ============================================================================
# Enums and Data Classes
# ============================================================================

class ViralCategory(str, Enum):
    """Category of viral potential."""
    HOOK = "hook"                      # Strong opening hook
    TRANSFORMATION = "transformation"   # Before/after, progress
    DEMONSTRATION = "demonstration"     # Exercise form, technique
    REACTION = "reaction"               # Emotional reaction shot
    CLIMAX = "climax"                   # Peak energy moment
    CONTROVERSY = "controversy"         # Contrarian or debate-worthy
    EDUCATIONAL = "educational"         # Teaching moment
    INSPIRATIONAL = "inspirational"     # Motivational content


@dataclass
class ViralMoment:
    """A detected viral moment with scoring breakdown."""
    start: float
    end: float
    score: float  # 0-100 overall viral score

    # Component scores (0-1 normalized)
    hook_strength: float = 0.0
    audio_energy: float = 0.0
    visual_variety: float = 0.0
    keyword_density: float = 0.0
    emotional_markers: float = 0.0
    fitness_relevance: float = 0.0

    # Context
    category: ViralCategory = ViralCategory.EDUCATIONAL
    transcript_snippet: str = ""
    keywords: List[str] = field(default_factory=list)
    emotional_words: List[str] = field(default_factory=list)

    # Confidence
    confidence: float = 0.8
    recommendation: str = ""

    @property
    def duration(self) -> float:
        return self.end - self.start

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start": round(self.start, 2),
            "end": round(self.end, 2),
            "duration": round(self.duration, 2),
            "start_formatted": format_duration(self.start),
            "end_formatted": format_duration(self.end),
            "score": round(self.score, 1),
            "category": self.category.value,
            "components": {
                "hook_strength": round(self.hook_strength, 3),
                "audio_energy": round(self.audio_energy, 3),
                "visual_variety": round(self.visual_variety, 3),
                "keyword_density": round(self.keyword_density, 3),
                "emotional_markers": round(self.emotional_markers, 3),
                "fitness_relevance": round(self.fitness_relevance, 3)
            },
            "transcript_snippet": self.transcript_snippet[:300] if self.transcript_snippet else "",
            "keywords": self.keywords[:10],
            "emotional_words": self.emotional_words[:5],
            "confidence": round(self.confidence, 2),
            "recommendation": self.recommendation
        }


@dataclass
class ViralConfig:
    """Configuration for viral moment detection."""
    min_duration: float = MIN_CLIP_DURATION
    max_duration: float = MAX_CLIP_DURATION
    top_count: int = 10
    min_score: float = 40.0  # Minimum score to include

    # Scoring weights
    weights: Dict[str, float] = field(default_factory=lambda: DEFAULT_WEIGHTS.copy())

    # Context preservation
    preserve_sentences: bool = True  # Don't cut mid-sentence
    buffer_seconds: float = 0.5  # Buffer before/after clip

    # Analysis options
    analyze_hooks: bool = True
    detect_emotions: bool = True
    boost_transformations: bool = True


@dataclass
class ViralDetectionResult:
    """Complete viral moment detection result."""
    video_path: str
    duration: float
    moments: List[ViralMoment]

    # Statistics
    avg_score: float = 0.0
    highest_score: float = 0.0
    total_viral_time: float = 0.0
    viral_percentage: float = 0.0

    # Categories breakdown
    category_counts: Dict[str, int] = field(default_factory=dict)

    # Processing
    processing_time_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "video_path": self.video_path,
            "duration": round(self.duration, 2),
            "duration_formatted": format_duration(self.duration),
            "moments": [m.to_dict() for m in self.moments],
            "statistics": {
                "moment_count": len(self.moments),
                "avg_score": round(self.avg_score, 1),
                "highest_score": round(self.highest_score, 1),
                "total_viral_time": round(self.total_viral_time, 2),
                "viral_percentage": round(self.viral_percentage, 2)
            },
            "category_breakdown": self.category_counts,
            "processing_time_seconds": round(self.processing_time_seconds, 2)
        }


# ============================================================================
# Hook Analysis
# ============================================================================

def analyze_hook_strength(
    text: str,
    word_timestamps: Optional[List[Dict[str, Any]]] = None,
    segment_start: float = 0.0
) -> Tuple[float, List[str]]:
    """
    Analyze the hook strength of the first few seconds.

    Strong hooks:
    - Start with attention-grabbing words (Stop, Wait, Here's)
    - Use numbers (5 ways, 10 mistakes)
    - Address viewer directly (You're, If you)
    - Create curiosity (Secret, Truth, Why)

    Returns:
        - hook_strength: 0-1 normalized score
        - patterns_matched: List of matched patterns
    """
    if not text:
        return 0.0, []

    text_lower = text.lower().strip()
    patterns_matched = []
    score = 0.0

    # Check hook patterns
    for pattern in HOOK_PATTERNS:
        if re.search(pattern, text_lower):
            patterns_matched.append(pattern)
            score += 0.15

    # Check for numbers (strong engagement)
    if re.search(r'\d+', text_lower):
        score += 0.1
        patterns_matched.append("number")

    # Check for question (creates curiosity)
    if "?" in text:
        score += 0.1
        patterns_matched.append("question")

    # Check for direct address (you, your)
    if re.search(r'\byou(r)?\b', text_lower):
        score += 0.1
        patterns_matched.append("direct_address")

    # Check for emotional opener
    emotional_openers = ["can't believe", "shocked", "finally", "secret"]
    for opener in emotional_openers:
        if opener in text_lower:
            score += 0.1
            patterns_matched.append(f"emotional:{opener}")

    # Normalize to 0-1
    return min(1.0, score), patterns_matched


# ============================================================================
# Emotional Analysis
# ============================================================================

def detect_emotional_markers(
    text: str,
    word_timestamps: Optional[List[Dict[str, Any]]] = None
) -> Tuple[float, List[str]]:
    """
    Detect emotional markers in text.

    Returns:
        - emotional_score: 0-1 normalized score
        - emotional_words: List of detected emotional words
    """
    if not text:
        return 0.0, []

    text_lower = text.lower()
    emotional_words = []

    for marker in EMOTIONAL_MARKERS:
        if marker in text_lower:
            emotional_words.append(marker)

    # Score based on density
    word_count = len(text.split())
    if word_count == 0:
        return 0.0, emotional_words

    # Emotional density (more = higher score, cap at ~10%)
    density = len(emotional_words) / word_count
    score = min(1.0, density * 10)

    return score, emotional_words


def detect_fitness_transformation(text: str) -> Tuple[float, List[str]]:
    """
    Detect fitness transformation content.

    Returns:
        - transformation_score: 0-1 normalized
        - markers: List of detected markers
    """
    if not text:
        return 0.0, []

    text_lower = text.lower()
    markers = []

    for marker in FITNESS_TRANSFORMATION_MARKERS:
        if marker in text_lower:
            markers.append(marker)

    # More markers = higher score
    score = min(1.0, len(markers) * 0.2)

    return score, markers


# ============================================================================
# Category Classification
# ============================================================================

def classify_moment(
    segment: ScoredSegment,
    hook_strength: float,
    emotional_score: float,
    transformation_score: float
) -> ViralCategory:
    """
    Classify the type of viral moment.

    Uses component scores to determine the most likely category.
    """
    # Strong hook at start of segment
    if hook_strength > 0.6:
        return ViralCategory.HOOK

    # Transformation content
    if transformation_score > 0.4:
        return ViralCategory.TRANSFORMATION

    # High energy climax
    if segment.audio_energy > 0.7 and segment.motion_intensity > 0.6:
        return ViralCategory.CLIMAX

    # Demonstration (high fitness relevance, moderate motion)
    if segment.fitness_relevance > 0.5 and segment.motion_intensity > 0.4:
        return ViralCategory.DEMONSTRATION

    # Strong emotional content
    if emotional_score > 0.5:
        return ViralCategory.REACTION

    # Educational by default
    return ViralCategory.EDUCATIONAL


# ============================================================================
# Viral Score Calculation
# ============================================================================

def calculate_viral_score(
    segment: ScoredSegment,
    hook_strength: float,
    emotional_score: float,
    transformation_score: float,
    weights: Dict[str, float]
) -> float:
    """
    Calculate overall viral score for a segment.

    Combines multiple factors with configurable weights.
    """
    # Normalize visual variety from scene changes
    # 1-3 scene changes is ideal, more can be jarring
    visual_variety = min(1.0, segment.scene_changes / 3)

    # Calculate weighted score
    score = (
        weights["hook_strength"] * hook_strength +
        weights["audio_energy"] * segment.audio_energy +
        weights["visual_variety"] * visual_variety +
        weights["keyword_density"] * segment.keyword_density +
        weights["emotional_markers"] * emotional_score +
        weights["fitness_relevance"] * segment.fitness_relevance
    ) * 100

    # Bonus for transformation content
    if transformation_score > 0.3:
        score *= (1 + transformation_score * 0.2)

    # Duration penalty for too long/short
    duration = segment.duration
    if duration < MIN_CLIP_DURATION:
        score *= 0.7
    elif duration > MAX_CLIP_DURATION:
        score *= 0.85
    elif MIN_CLIP_DURATION <= duration <= IDEAL_CLIP_DURATION + 10:
        score *= 1.1  # Slight bonus for ideal length

    return min(100, score)


def generate_recommendation(moment: ViralMoment) -> str:
    """
    Generate actionable recommendation for the viral moment.
    """
    recommendations = []

    # Based on category
    category_recs = {
        ViralCategory.HOOK: "Strong opening hook - use for intro or teaser",
        ViralCategory.TRANSFORMATION: "Transformation content - perfect for before/after compilation",
        ViralCategory.DEMONSTRATION: "Exercise demonstration - great for educational content",
        ViralCategory.CLIMAX: "High energy moment - use for highlight reel",
        ViralCategory.REACTION: "Emotional content - connects with audience",
        ViralCategory.INSPIRATIONAL: "Motivational moment - share for engagement"
    }
    recommendations.append(category_recs.get(moment.category, "Educational content"))

    # Based on weak areas
    if moment.hook_strength < 0.3:
        recommendations.append("Consider adding a stronger text hook overlay")
    if moment.audio_energy < 0.3:
        recommendations.append("May benefit from background music")
    if moment.visual_variety < 0.3:
        recommendations.append("Consider adding b-roll or zoom effects")

    return " | ".join(recommendations)


# ============================================================================
# Sentence Boundary Detection
# ============================================================================

def find_sentence_boundary(
    word_timestamps: List[Dict[str, Any]],
    target_time: float,
    direction: str = "before"
) -> float:
    """
    Find the nearest sentence boundary to a target time.

    Prevents cutting mid-sentence for cleaner clips.

    Args:
        word_timestamps: List of words with timestamps
        target_time: Target timestamp
        direction: 'before' or 'after' the target

    Returns:
        Adjusted timestamp at sentence boundary
    """
    if not word_timestamps:
        return target_time

    sentence_endings = {'.', '!', '?'}

    if direction == "before":
        # Find last sentence ending before target
        last_boundary = 0.0
        for word_data in word_timestamps:
            word = word_data.get("word", "")
            end_time = word_data.get("end", 0)

            if end_time > target_time:
                break

            if any(word.endswith(p) for p in sentence_endings):
                last_boundary = end_time

        return last_boundary if last_boundary > 0 else target_time

    else:  # after
        # Find first sentence ending after target
        for word_data in word_timestamps:
            word = word_data.get("word", "")
            end_time = word_data.get("end", 0)

            if end_time < target_time:
                continue

            if any(word.endswith(p) for p in sentence_endings):
                return end_time

        return target_time


def adjust_clip_boundaries(
    start: float,
    end: float,
    word_timestamps: Optional[List[Dict[str, Any]]],
    config: ViralConfig
) -> Tuple[float, float]:
    """
    Adjust clip boundaries to respect sentence boundaries and duration limits.
    """
    if not config.preserve_sentences or not word_timestamps:
        return start, end

    # Adjust start to nearest sentence boundary
    adjusted_start = find_sentence_boundary(word_timestamps, start, "before")
    if adjusted_start < start - 2.0:  # Don't go back more than 2 seconds
        adjusted_start = start

    # Adjust end to nearest sentence boundary
    adjusted_end = find_sentence_boundary(word_timestamps, end, "after")
    if adjusted_end > end + 2.0:  # Don't go forward more than 2 seconds
        adjusted_end = end

    # Apply buffer
    adjusted_start = max(0, adjusted_start - config.buffer_seconds)
    adjusted_end = adjusted_end + config.buffer_seconds

    # Enforce duration limits
    duration = adjusted_end - adjusted_start
    if duration < config.min_duration:
        # Extend end if possible
        adjusted_end = adjusted_start + config.min_duration
    elif duration > config.max_duration:
        # Truncate end
        adjusted_end = adjusted_start + config.max_duration

    return adjusted_start, adjusted_end


# ============================================================================
# Main Detection Function
# ============================================================================

async def detect_viral_moments(
    video_path: str,
    transcription_result: Optional[Dict[str, Any]] = None,
    config: Optional[ViralConfig] = None,
    video_analysis: Optional[VideoAnalysisResult] = None
) -> ViralDetectionResult:
    """
    Detect viral moments in a video.

    Args:
        video_path: Path to video file
        transcription_result: Optional transcription with word timestamps
        config: Viral detection configuration
        video_analysis: Pre-computed video analysis (optional, will run if not provided)

    Returns:
        ViralDetectionResult with scored moments
    """
    import time
    start_time = time.time()

    if config is None:
        config = ViralConfig()

    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    logger.info(
        f"Detecting viral moments: {video_path.name}",
        extra={"metadata": {"config": {"top_count": config.top_count}}}
    )

    # Run video analysis if not provided
    if video_analysis is None:
        analysis_config = AnalysisConfig(
            analyze_audio=True,
            analyze_motion=True,
            detect_scenes=True,
            extract_keywords=transcription_result is not None,
            min_segment_duration=config.min_duration,
            max_segment_duration=config.max_duration
        )
        video_analysis = await analyze_video(
            str(video_path),
            transcription_result=transcription_result,
            config=analysis_config
        )

    # Get word timestamps for boundary detection
    word_timestamps = transcription_result.get("words", []) if transcription_result else []
    full_text = transcription_result.get("text", "") if transcription_result else ""

    # Process each segment into viral moment
    viral_moments = []

    for segment in video_analysis.segments:
        # Get transcript for this segment
        segment_text = extract_segment_text(
            full_text, word_timestamps, segment.start, segment.end
        )

        # Analyze hook (first 3 seconds of segment)
        hook_text = extract_segment_text(
            full_text, word_timestamps, segment.start, segment.start + 3
        )
        hook_strength, hook_patterns = analyze_hook_strength(hook_text, word_timestamps, segment.start)

        # Analyze emotions
        emotional_score, emotional_words = detect_emotional_markers(segment_text)

        # Detect transformation content
        transformation_score, transformation_markers = detect_fitness_transformation(segment_text)

        # Calculate viral score
        viral_score = calculate_viral_score(
            segment,
            hook_strength,
            emotional_score,
            transformation_score,
            config.weights
        )

        # Skip low-scoring segments
        if viral_score < config.min_score:
            continue

        # Classify moment category
        category = classify_moment(segment, hook_strength, emotional_score, transformation_score)

        # Adjust boundaries for clean cuts
        adjusted_start, adjusted_end = adjust_clip_boundaries(
            segment.start, segment.end, word_timestamps, config
        )

        # Create viral moment
        moment = ViralMoment(
            start=adjusted_start,
            end=adjusted_end,
            score=viral_score,
            hook_strength=hook_strength,
            audio_energy=segment.audio_energy,
            visual_variety=min(1.0, segment.scene_changes / 3),
            keyword_density=segment.keyword_density,
            emotional_markers=emotional_score,
            fitness_relevance=segment.fitness_relevance,
            category=category,
            transcript_snippet=segment_text,
            keywords=segment.keywords,
            emotional_words=emotional_words,
            confidence=0.7 + (viral_score / 300)  # Higher score = higher confidence
        )

        # Generate recommendation
        moment.recommendation = generate_recommendation(moment)

        viral_moments.append(moment)

    # Sort by score and take top N
    viral_moments.sort(key=lambda m: m.score, reverse=True)
    top_moments = viral_moments[:config.top_count]

    # Remove overlapping moments (keep higher scored)
    top_moments = remove_overlapping_moments(top_moments)

    # Calculate statistics
    if top_moments:
        avg_score = sum(m.score for m in top_moments) / len(top_moments)
        highest_score = max(m.score for m in top_moments)
        total_viral_time = sum(m.duration for m in top_moments)
        viral_percentage = (total_viral_time / video_analysis.duration) * 100
    else:
        avg_score = 0
        highest_score = 0
        total_viral_time = 0
        viral_percentage = 0

    # Category breakdown
    category_counts = {}
    for moment in top_moments:
        cat = moment.category.value
        category_counts[cat] = category_counts.get(cat, 0) + 1

    processing_time = time.time() - start_time

    logger.info(
        f"Viral detection complete",
        extra={
            "metadata": {
                "moments_found": len(top_moments),
                "highest_score": round(highest_score, 1),
                "processing_time": round(processing_time, 2)
            }
        }
    )

    log_job_event(
        job_id="viral_detection",
        event="completed",
        job_type="viral_detection",
        moments_found=len(top_moments),
        highest_score=highest_score,
        processing_time=processing_time
    )

    return ViralDetectionResult(
        video_path=str(video_path),
        duration=video_analysis.duration,
        moments=top_moments,
        avg_score=avg_score,
        highest_score=highest_score,
        total_viral_time=total_viral_time,
        viral_percentage=viral_percentage,
        category_counts=category_counts,
        processing_time_seconds=processing_time
    )


def remove_overlapping_moments(moments: List[ViralMoment]) -> List[ViralMoment]:
    """
    Remove overlapping moments, keeping the higher-scored one.

    Moments should already be sorted by score (highest first).
    """
    if len(moments) <= 1:
        return moments

    kept_moments = []

    for moment in moments:
        overlaps = False
        for kept in kept_moments:
            # Check for overlap
            if moment.start < kept.end and moment.end > kept.start:
                overlaps = True
                break

        if not overlaps:
            kept_moments.append(moment)

    return kept_moments


def extract_segment_text(
    full_text: str,
    word_timestamps: List[Dict[str, Any]],
    start: float,
    end: float
) -> str:
    """
    Extract text for a specific time segment.
    """
    if not word_timestamps:
        return ""

    words = []
    for word_data in word_timestamps:
        word_start = word_data.get("start", 0)
        word_end = word_data.get("end", 0)

        # Word is within segment
        if word_start >= start and word_end <= end:
            words.append(word_data.get("word", ""))

    return " ".join(words)


# ============================================================================
# Convenience Functions
# ============================================================================

async def get_best_clips(
    video_path: str,
    count: int = 5,
    transcription_result: Optional[Dict[str, Any]] = None
) -> List[ViralMoment]:
    """
    Get the N best viral clips from a video.

    Convenience function for quick extraction.
    """
    config = ViralConfig(top_count=count)
    result = await detect_viral_moments(
        video_path,
        transcription_result=transcription_result,
        config=config
    )
    return result.moments


async def score_clip(
    video_path: str,
    start: float,
    end: float,
    transcription_result: Optional[Dict[str, Any]] = None
) -> ViralMoment:
    """
    Score a specific clip for viral potential.

    Useful for manually selected clips.
    """
    from backend.video_analyzer import analyze_video, AnalysisConfig

    # Analyze just the clip portion
    config = AnalysisConfig(
        analyze_audio=True,
        analyze_motion=True,
        detect_scenes=True,
        min_segment_duration=end - start,
        max_segment_duration=end - start + 1
    )

    analysis = await analyze_video(
        video_path,
        transcription_result=transcription_result,
        config=config
    )

    if not analysis.segments:
        return ViralMoment(
            start=start,
            end=end,
            score=0,
            recommendation="Unable to analyze clip"
        )

    # Find the segment covering this clip
    for segment in analysis.segments:
        if segment.start <= start and segment.end >= end:
            # Get clip text
            full_text = transcription_result.get("text", "") if transcription_result else ""
            word_timestamps = transcription_result.get("words", []) if transcription_result else []
            segment_text = extract_segment_text(full_text, word_timestamps, start, end)

            # Analyze
            hook_strength, _ = analyze_hook_strength(segment_text[:100])
            emotional_score, emotional_words = detect_emotional_markers(segment_text)
            transformation_score, _ = detect_fitness_transformation(segment_text)

            viral_score = calculate_viral_score(
                segment,
                hook_strength,
                emotional_score,
                transformation_score,
                DEFAULT_WEIGHTS
            )

            category = classify_moment(segment, hook_strength, emotional_score, transformation_score)

            moment = ViralMoment(
                start=start,
                end=end,
                score=viral_score,
                hook_strength=hook_strength,
                audio_energy=segment.audio_energy,
                visual_variety=min(1.0, segment.scene_changes / 3),
                keyword_density=segment.keyword_density,
                emotional_markers=emotional_score,
                fitness_relevance=segment.fitness_relevance,
                category=category,
                transcript_snippet=segment_text,
                keywords=segment.keywords,
                emotional_words=emotional_words
            )
            moment.recommendation = generate_recommendation(moment)

            return moment

    return ViralMoment(
        start=start,
        end=end,
        score=0,
        recommendation="Clip not found in analysis"
    )
