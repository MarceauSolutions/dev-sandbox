"""
Filler Word Detection Engine for Fitness Influencer AI

Detects verbal fillers (um, uh, like, you know, so, basically, actually) using
transcription with context awareness. Distinguishes intentional vs filler usage.

Story 009: Build filler word detection engine
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple, Set
import logging

logger = logging.getLogger(__name__)


class FillerCategory(Enum):
    """Categories of filler words."""
    HESITATION = "hesitation"  # um, uh, er
    DISCOURSE_MARKER = "discourse_marker"  # like, so, well
    HEDGE = "hedge"  # basically, actually, honestly
    TAG = "tag"  # you know, right, I mean
    REPETITION = "repetition"  # repeated words


@dataclass
class FillerPattern:
    """Definition of a filler word pattern."""
    words: List[str]  # Words that form this filler (e.g., ["you", "know"])
    category: FillerCategory
    base_confidence: float = 0.9  # Starting confidence before context analysis
    context_patterns: Dict[str, float] = field(default_factory=dict)  # Pattern → confidence modifier


# Define filler patterns with context awareness
FILLER_PATTERNS: Dict[str, FillerPattern] = {
    # Pure hesitation fillers - almost always removable
    "um": FillerPattern(
        words=["um"],
        category=FillerCategory.HESITATION,
        base_confidence=0.95
    ),
    "uh": FillerPattern(
        words=["uh"],
        category=FillerCategory.HESITATION,
        base_confidence=0.95
    ),
    "er": FillerPattern(
        words=["er"],
        category=FillerCategory.HESITATION,
        base_confidence=0.90
    ),
    "ah": FillerPattern(
        words=["ah"],
        category=FillerCategory.HESITATION,
        base_confidence=0.85  # Lower - could be exclamation
    ),

    # Discourse markers - context-dependent
    "like": FillerPattern(
        words=["like"],
        category=FillerCategory.DISCOURSE_MARKER,
        base_confidence=0.70,  # Often intentional
        context_patterns={
            r"^like\s*,": 0.9,  # "Like, this is..." - filler
            r",\s*like\s*,": 0.85,  # ", like," - filler
            r"it's\s+like": -0.5,  # "it's like" - comparison, keep
            r"looks?\s+like": -0.6,  # "looks like" - comparison
            r"feel\s+like": -0.5,  # "feel like" - intentional
            r"like\s+\d": -0.7,  # "like 5" - approximation
            r"like\s+this": -0.6,  # "like this" - demonstration
            r"like\s+a": -0.4,  # "like a" - simile
        }
    ),
    "so": FillerPattern(
        words=["so"],
        category=FillerCategory.DISCOURSE_MARKER,
        base_confidence=0.60,  # Often intentional connector
        context_patterns={
            r"^so\s*,": 0.8,  # "So, yeah" - filler starter
            r"^so\s+um": 0.9,  # "So um" - definitely filler
            r"^so\s+uh": 0.9,  # "So uh" - definitely filler
            r"so\s+that": -0.7,  # "so that" - connector
            r"so\s+much": -0.6,  # "so much" - intensifier
            r"so\s+far": -0.6,  # "so far" - phrase
            r"and\s+so": -0.4,  # "and so" - connector
            r"so\s+you": -0.3,  # "so you can" - explanation
        }
    ),
    "well": FillerPattern(
        words=["well"],
        category=FillerCategory.DISCOURSE_MARKER,
        base_confidence=0.65,
        context_patterns={
            r"^well\s*,": 0.8,  # "Well, I think" - filler
            r"as\s+well": -0.8,  # "as well" - phrase
            r"very\s+well": -0.8,  # "very well" - adverb
            r"well\s+done": -0.7,  # "well done" - phrase
            r"do\s+well": -0.7,  # "do well" - phrase
        }
    ),

    # Hedge words - often removable without losing meaning
    "basically": FillerPattern(
        words=["basically"],
        category=FillerCategory.HEDGE,
        base_confidence=0.80,
        context_patterns={
            r"^basically\s*,": 0.9,  # Sentence starter - filler
            r"is\s+basically": 0.7,  # "is basically" - often filler
        }
    ),
    "actually": FillerPattern(
        words=["actually"],
        category=FillerCategory.HEDGE,
        base_confidence=0.70,
        context_patterns={
            r"^actually\s*,": 0.85,  # Sentence starter - likely filler
            r"but\s+actually": -0.3,  # Contrast - intentional
            r"not\s+actually": -0.5,  # Negation - intentional
        }
    ),
    "honestly": FillerPattern(
        words=["honestly"],
        category=FillerCategory.HEDGE,
        base_confidence=0.75,
        context_patterns={
            r"^honestly\s*,": 0.85,  # Sentence starter - filler
        }
    ),
    "literally": FillerPattern(
        words=["literally"],
        category=FillerCategory.HEDGE,
        base_confidence=0.65,  # Often used for emphasis
        context_patterns={
            r"literally\s+just": 0.7,  # "literally just" - filler emphasis
            r"literally\s+the": 0.6,  # "literally the" - filler emphasis
        }
    ),
    "just": FillerPattern(
        words=["just"],
        category=FillerCategory.HEDGE,
        base_confidence=0.50,  # Very context-dependent
        context_patterns={
            r"just\s+like": 0.3,  # "just like" - could be filler
            r"i\s+just": 0.4,  # "I just want" - sometimes filler
            r"just\s+now": -0.6,  # Time reference
            r"just\s+a": -0.3,  # "just a second" - meaningful
        }
    ),

    # Tag fillers - multi-word patterns
    "you_know": FillerPattern(
        words=["you", "know"],
        category=FillerCategory.TAG,
        base_confidence=0.85,
        context_patterns={
            r"you\s+know\s*,": 0.9,  # "you know," - definite filler
            r",\s*you\s+know": 0.9,  # ", you know" - definite filler
            r"if\s+you\s+know": -0.6,  # "if you know" - conditional
            r"do\s+you\s+know": -0.7,  # Question - intentional
        }
    ),
    "i_mean": FillerPattern(
        words=["i", "mean"],
        category=FillerCategory.TAG,
        base_confidence=0.80,
        context_patterns={
            r"^i\s+mean\s*,": 0.9,  # Sentence starter - filler
            r",\s*i\s+mean": 0.85,  # Mid-sentence - filler
            r"what\s+i\s+mean": -0.7,  # "what I mean" - explanation
        }
    ),
    "right": FillerPattern(
        words=["right"],
        category=FillerCategory.TAG,
        base_confidence=0.60,
        context_patterns={
            r",\s*right\s*\?": 0.8,  # ", right?" - tag question
            r",\s*right\s*,": 0.75,  # ", right," - filler
            r"right\s+now": -0.8,  # "right now" - phrase
            r"right\s+here": -0.7,  # "right here" - phrase
            r"that's\s+right": -0.6,  # Affirmation
        }
    ),
    "you_know_what_i_mean": FillerPattern(
        words=["you", "know", "what", "i", "mean"],
        category=FillerCategory.TAG,
        base_confidence=0.95  # Almost always filler
    ),
    "kind_of": FillerPattern(
        words=["kind", "of"],
        category=FillerCategory.HEDGE,
        base_confidence=0.60,
        context_patterns={
            r"kind\s+of\s+like": 0.7,  # "kind of like" - hedging
            r"what\s+kind\s+of": -0.8,  # Question - intentional
            r"this\s+kind\s+of": -0.5,  # "this kind of" - classification
        }
    ),
    "sort_of": FillerPattern(
        words=["sort", "of"],
        category=FillerCategory.HEDGE,
        base_confidence=0.65,
        context_patterns={
            r"sort\s+of\s+like": 0.7,  # Hedging
            r"what\s+sort\s+of": -0.7,  # Question
        }
    ),
}


@dataclass
class FillerWord:
    """A detected filler word with metadata."""
    word: str
    start: float  # Start time in seconds
    end: float  # End time in seconds
    confidence: float  # 0.0 - 1.0 confidence it's a filler
    is_filler: bool  # Final determination based on threshold
    category: FillerCategory
    pattern_id: str  # Which pattern matched
    context_before: str = ""  # Words before for context
    context_after: str = ""  # Words after for context

    def to_dict(self) -> dict:
        return {
            "word": self.word,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
            "is_filler": self.is_filler,
            "category": self.category.value,
            "pattern_id": self.pattern_id,
            "context_before": self.context_before,
            "context_after": self.context_after
        }


@dataclass
class FillerCluster:
    """A cluster of consecutive filler words."""
    fillers: List[FillerWord]
    start: float
    end: float
    total_duration: float

    def to_dict(self) -> dict:
        return {
            "fillers": [f.to_dict() for f in self.fillers],
            "start": self.start,
            "end": self.end,
            "total_duration": self.total_duration,
            "filler_count": len(self.fillers)
        }


@dataclass
class FillerDetectionResult:
    """Result of filler detection analysis."""
    fillers: List[FillerWord]
    clusters: List[FillerCluster]
    total_filler_count: int
    filler_duration: float  # Total time spent on fillers
    total_duration: float  # Total audio duration
    filler_percentage: float  # Filler time / total time
    words_analyzed: int

    def to_dict(self) -> dict:
        return {
            "fillers": [f.to_dict() for f in self.fillers],
            "clusters": [c.to_dict() for c in self.clusters],
            "total_filler_count": self.total_filler_count,
            "filler_duration": round(self.filler_duration, 2),
            "total_duration": round(self.total_duration, 2),
            "filler_percentage": round(self.filler_percentage, 2),
            "words_analyzed": self.words_analyzed,
            "summary": {
                "hesitations": len([f for f in self.fillers if f.category == FillerCategory.HESITATION]),
                "discourse_markers": len([f for f in self.fillers if f.category == FillerCategory.DISCOURSE_MARKER]),
                "hedges": len([f for f in self.fillers if f.category == FillerCategory.HEDGE]),
                "tags": len([f for f in self.fillers if f.category == FillerCategory.TAG]),
            }
        }


@dataclass
class WordTimestamp:
    """Word with timing information from transcription."""
    word: str
    start: float
    end: float
    confidence: float = 1.0


def get_context_window(
    words: List[WordTimestamp],
    index: int,
    window_size: int = 3
) -> Tuple[str, str]:
    """Get context words before and after the target word."""
    before_words = []
    after_words = []

    # Get words before
    for i in range(max(0, index - window_size), index):
        before_words.append(words[i].word.lower())

    # Get words after
    for i in range(index + 1, min(len(words), index + 1 + window_size)):
        after_words.append(words[i].word.lower())

    return " ".join(before_words), " ".join(after_words)


def match_multi_word_pattern(
    words: List[WordTimestamp],
    start_index: int,
    pattern_words: List[str]
) -> Optional[Tuple[int, List[WordTimestamp]]]:
    """
    Try to match a multi-word pattern starting at the given index.
    Returns (end_index, matched_words) if successful, None otherwise.
    """
    if start_index + len(pattern_words) > len(words):
        return None

    matched = []
    for i, pattern_word in enumerate(pattern_words):
        word = words[start_index + i]
        if word.word.lower().strip(".,!?") != pattern_word.lower():
            return None
        matched.append(word)

    return start_index + len(pattern_words) - 1, matched


def calculate_confidence(
    pattern: FillerPattern,
    context_before: str,
    context_after: str,
    word_text: str
) -> float:
    """
    Calculate confidence score based on pattern and context.
    Context patterns can increase or decrease confidence.
    """
    confidence = pattern.base_confidence

    # Build context string for pattern matching
    full_context = f"{context_before} {word_text} {context_after}".lower()

    # Apply context pattern modifiers
    for regex_pattern, modifier in pattern.context_patterns.items():
        if re.search(regex_pattern, full_context, re.IGNORECASE):
            confidence += modifier

    # Clamp to valid range
    return max(0.0, min(1.0, confidence))


def detect_fillers(
    words: List[WordTimestamp],
    confidence_threshold: float = 0.8,
    categories: Optional[List[FillerCategory]] = None,
    cluster_gap_threshold: float = 0.5
) -> FillerDetectionResult:
    """
    Detect filler words in a list of timestamped words.

    Args:
        words: List of WordTimestamp objects from transcription
        confidence_threshold: Minimum confidence to mark as filler (0.0-1.0)
        categories: Optional list of categories to detect (default: all)
        cluster_gap_threshold: Max gap between fillers to be considered a cluster

    Returns:
        FillerDetectionResult with all detected fillers and analysis
    """
    if not words:
        return FillerDetectionResult(
            fillers=[],
            clusters=[],
            total_filler_count=0,
            filler_duration=0.0,
            total_duration=0.0,
            filler_percentage=0.0,
            words_analyzed=0
        )

    # Filter patterns by category if specified
    active_patterns = FILLER_PATTERNS
    if categories:
        active_patterns = {
            k: v for k, v in FILLER_PATTERNS.items()
            if v.category in categories
        }

    detected_fillers: List[FillerWord] = []
    processed_indices: Set[int] = set()

    i = 0
    while i < len(words):
        if i in processed_indices:
            i += 1
            continue

        word = words[i]
        word_lower = word.word.lower().strip(".,!?")

        # Try to match patterns
        matched = False

        for pattern_id, pattern in active_patterns.items():
            if len(pattern.words) == 1:
                # Single word pattern
                if word_lower == pattern.words[0].lower():
                    context_before, context_after = get_context_window(words, i)
                    confidence = calculate_confidence(
                        pattern, context_before, context_after, word_lower
                    )

                    filler = FillerWord(
                        word=word.word,
                        start=word.start,
                        end=word.end,
                        confidence=confidence,
                        is_filler=confidence >= confidence_threshold,
                        category=pattern.category,
                        pattern_id=pattern_id,
                        context_before=context_before,
                        context_after=context_after
                    )
                    detected_fillers.append(filler)
                    processed_indices.add(i)
                    matched = True
                    break
            else:
                # Multi-word pattern
                match_result = match_multi_word_pattern(words, i, pattern.words)
                if match_result:
                    end_idx, matched_words = match_result
                    context_before, _ = get_context_window(words, i)
                    _, context_after = get_context_window(words, end_idx)

                    combined_text = " ".join([w.word for w in matched_words])
                    confidence = calculate_confidence(
                        pattern, context_before, context_after, combined_text
                    )

                    filler = FillerWord(
                        word=combined_text,
                        start=matched_words[0].start,
                        end=matched_words[-1].end,
                        confidence=confidence,
                        is_filler=confidence >= confidence_threshold,
                        category=pattern.category,
                        pattern_id=pattern_id,
                        context_before=context_before,
                        context_after=context_after
                    )
                    detected_fillers.append(filler)

                    # Mark all matched indices as processed
                    for idx in range(i, end_idx + 1):
                        processed_indices.add(idx)

                    matched = True
                    break

        i += 1

    # Detect repetition fillers (same word repeated)
    for i in range(len(words) - 1):
        if i in processed_indices:
            continue

        word = words[i]
        next_word = words[i + 1]

        # Check for immediate repetition
        if (word.word.lower().strip(".,!?") == next_word.word.lower().strip(".,!?") and
            next_word.start - word.end < 0.3):  # Gap less than 300ms

            # The repeated word is likely a filler
            context_before, context_after = get_context_window(words, i + 1)

            filler = FillerWord(
                word=next_word.word,
                start=next_word.start,
                end=next_word.end,
                confidence=0.85,
                is_filler=0.85 >= confidence_threshold,
                category=FillerCategory.REPETITION,
                pattern_id="repetition",
                context_before=context_before,
                context_after=context_after
            )
            detected_fillers.append(filler)

    # Sort by start time
    detected_fillers.sort(key=lambda f: f.start)

    # Filter to only confirmed fillers
    confirmed_fillers = [f for f in detected_fillers if f.is_filler]

    # Detect clusters
    clusters = detect_filler_clusters(confirmed_fillers, cluster_gap_threshold)

    # Calculate statistics
    total_duration = words[-1].end if words else 0.0
    filler_duration = sum(f.end - f.start for f in confirmed_fillers)
    filler_percentage = (filler_duration / total_duration * 100) if total_duration > 0 else 0.0

    return FillerDetectionResult(
        fillers=detected_fillers,  # Include all detected, not just confirmed
        clusters=clusters,
        total_filler_count=len(confirmed_fillers),
        filler_duration=filler_duration,
        total_duration=total_duration,
        filler_percentage=filler_percentage,
        words_analyzed=len(words)
    )


def detect_filler_clusters(
    fillers: List[FillerWord],
    gap_threshold: float = 0.5
) -> List[FillerCluster]:
    """
    Identify clusters of consecutive filler words.
    A cluster is defined as fillers separated by less than gap_threshold seconds.
    """
    if not fillers:
        return []

    clusters = []
    current_cluster = [fillers[0]]

    for i in range(1, len(fillers)):
        prev_filler = fillers[i - 1]
        curr_filler = fillers[i]

        # Check if this filler is close enough to the previous one
        gap = curr_filler.start - prev_filler.end

        if gap <= gap_threshold:
            current_cluster.append(curr_filler)
        else:
            # Save current cluster if it has multiple fillers
            if len(current_cluster) >= 2:
                clusters.append(FillerCluster(
                    fillers=current_cluster,
                    start=current_cluster[0].start,
                    end=current_cluster[-1].end,
                    total_duration=current_cluster[-1].end - current_cluster[0].start
                ))
            current_cluster = [curr_filler]

    # Don't forget the last cluster
    if len(current_cluster) >= 2:
        clusters.append(FillerCluster(
            fillers=current_cluster,
            start=current_cluster[0].start,
            end=current_cluster[-1].end,
            total_duration=current_cluster[-1].end - current_cluster[0].start
        ))

    return clusters


def get_removal_segments(
    result: FillerDetectionResult,
    include_clusters: bool = True,
    min_confidence: float = 0.8
) -> List[Tuple[float, float]]:
    """
    Get time segments to remove based on filler detection.

    Args:
        result: FillerDetectionResult from detect_fillers()
        include_clusters: If True, treat clusters as single segments
        min_confidence: Minimum confidence threshold

    Returns:
        List of (start, end) tuples representing segments to remove
    """
    segments = []

    # Get confirmed fillers above threshold
    confirmed = [f for f in result.fillers if f.is_filler and f.confidence >= min_confidence]

    if include_clusters and result.clusters:
        # Use cluster boundaries for clustered fillers
        cluster_starts = {c.start for c in result.clusters}
        cluster_ends = {c.end for c in result.clusters}
        cluster_filler_starts = set()

        for cluster in result.clusters:
            for f in cluster.fillers:
                cluster_filler_starts.add(f.start)
            segments.append((cluster.start, cluster.end))

        # Add non-clustered fillers
        for filler in confirmed:
            if filler.start not in cluster_filler_starts:
                segments.append((filler.start, filler.end))
    else:
        # Just use individual filler segments
        for filler in confirmed:
            segments.append((filler.start, filler.end))

    # Sort and merge overlapping segments
    segments.sort(key=lambda x: x[0])
    merged = []

    for start, end in segments:
        if merged and start <= merged[-1][1]:
            # Overlapping - extend the previous segment
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    return merged


# Sensitivity mode presets
SENSITIVITY_PRESETS = {
    "aggressive": {
        "confidence_threshold": 0.5,
        "categories": None,  # All categories
        "cluster_gap_threshold": 0.8
    },
    "moderate": {
        "confidence_threshold": 0.7,
        "categories": None,
        "cluster_gap_threshold": 0.5
    },
    "conservative": {
        "confidence_threshold": 0.85,
        "categories": [FillerCategory.HESITATION, FillerCategory.TAG],
        "cluster_gap_threshold": 0.3
    }
}


def detect_fillers_with_sensitivity(
    words: List[WordTimestamp],
    sensitivity: str = "moderate"
) -> FillerDetectionResult:
    """
    Detect fillers using a predefined sensitivity preset.

    Args:
        words: List of WordTimestamp objects
        sensitivity: One of "aggressive", "moderate", "conservative"

    Returns:
        FillerDetectionResult
    """
    if sensitivity not in SENSITIVITY_PRESETS:
        raise ValueError(f"Unknown sensitivity: {sensitivity}. Use: aggressive, moderate, conservative")

    preset = SENSITIVITY_PRESETS[sensitivity]
    return detect_fillers(
        words=words,
        confidence_threshold=preset["confidence_threshold"],
        categories=preset["categories"],
        cluster_gap_threshold=preset["cluster_gap_threshold"]
    )
