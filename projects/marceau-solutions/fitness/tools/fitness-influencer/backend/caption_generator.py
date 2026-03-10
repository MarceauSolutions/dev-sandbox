#!/usr/bin/env python3
"""
Word-Level Caption Generator for Fitness Influencer AI v2.0

Generate karaoke-style captions with word highlighting synced to audio.

Features:
    - Word-by-word highlighting as spoken
    - Configurable words per line (default 7)
    - Auto line-break at punctuation and pauses
    - Multiple output formats (embedded, SRT, VTT)
    - Style presets and customization

Usage:
    from backend.caption_generator import generate_captions, CaptionConfig

    config = CaptionConfig(
        style="trending",
        max_words_per_line=7,
        position="bottom"
    )
    result = await generate_captions("/path/to/video.mp4", config)

    # Access outputs
    print(result.captioned_video_path)
    print(result.srt_content)
    print(result.vtt_content)
"""

import os
import subprocess
import tempfile
import asyncio
import math
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum

from backend.logging_config import get_logger
from backend.transcription import (
    TranscriptionResult,
    WordTimestamp,
    transcribe_video,
    format_timestamp,
    format_vtt_timestamp
)

logger = get_logger(__name__)


# ============================================================================
# Configuration
# ============================================================================

class CaptionPosition(str, Enum):
    """Caption position on video."""
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"


@dataclass
class PositionConfig:
    """Advanced position configuration with pixel offset support."""
    vertical: CaptionPosition = CaptionPosition.BOTTOM
    vertical_offset: int = 50  # Pixels from edge
    horizontal_offset: int = 0  # Pixels from center (+ = right, - = left)

    @classmethod
    def from_string(cls, position: str) -> 'PositionConfig':
        """Parse position from string (e.g., 'bottom+20' or 'center')."""
        import re

        # Check for offset format: "position+offset" or "position-offset"
        match = re.match(r'^(top|center|bottom)([+-]\d+)?$', position.lower())
        if match:
            pos_str = match.group(1)
            offset_str = match.group(2)

            pos = CaptionPosition(pos_str)
            offset = int(offset_str) if offset_str else 50

            # Adjust offset sign based on position
            if pos == CaptionPosition.TOP:
                offset = abs(offset)  # Offset from top edge
            elif pos == CaptionPosition.BOTTOM:
                offset = abs(offset)  # Offset from bottom edge

            return cls(vertical=pos, vertical_offset=offset)

        # Default
        try:
            pos = CaptionPosition(position.lower())
            return cls(vertical=pos)
        except ValueError:
            return cls()

    def get_ass_alignment(self) -> int:
        """Get ASS alignment value for this position."""
        return {
            CaptionPosition.BOTTOM: 2,  # Bottom center
            CaptionPosition.CENTER: 5,  # Middle center
            CaptionPosition.TOP: 8      # Top center
        }.get(self.vertical, 2)

    def get_margin_v(self) -> int:
        """Get vertical margin in pixels."""
        return self.vertical_offset


class HighlightStyle(str, Enum):
    """Word highlight animation style."""
    NONE = "none"          # No highlighting
    COLOR = "color"        # Change color when spoken
    UNDERLINE = "underline"  # Underline when spoken
    BOLD = "bold"          # Bold when spoken
    SCALE = "scale"        # Scale up when spoken


@dataclass
class CaptionStyle:
    """Caption visual styling."""
    font_family: str = "Arial"
    font_size: int = 48
    font_color: str = "#FFFFFF"
    outline_color: str = "#000000"
    outline_width: int = 2
    shadow_color: Optional[str] = None
    shadow_offset: int = 0
    background_color: Optional[str] = None
    background_opacity: float = 0.0
    highlight_color: str = "#FFFF00"  # Color for current word
    highlight_style: HighlightStyle = HighlightStyle.COLOR

    def to_ass_style(self) -> str:
        """Convert to ASS subtitle style string."""
        # ASS uses BGR color format
        font_color_bgr = self._hex_to_ass_color(self.font_color)
        outline_color_bgr = self._hex_to_ass_color(self.outline_color)

        style_parts = [
            f"Fontname={self.font_family}",
            f"Fontsize={self.font_size}",
            f"PrimaryColour={font_color_bgr}",
            f"OutlineColour={outline_color_bgr}",
            f"Outline={self.outline_width}",
            f"Shadow={self.shadow_offset}",
            "Bold=0",
            "Alignment=2",  # Center bottom
            "MarginV=50"
        ]

        return ",".join(style_parts)

    @staticmethod
    def _hex_to_ass_color(hex_color: str) -> str:
        """Convert hex color to ASS format (&HAABBGGRR)."""
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return f"&H00{b:02X}{g:02X}{r:02X}"


@dataclass
class CaptionConfig:
    """Configuration for caption generation."""
    style: str = "trending"  # Style preset name or "custom"
    max_words_per_line: int = 7
    position: CaptionPosition = CaptionPosition.BOTTOM
    position_config: Optional[PositionConfig] = None  # Advanced position with offset
    language: Optional[str] = None  # Force language for transcription
    word_highlight: bool = True
    highlight_style: HighlightStyle = HighlightStyle.COLOR
    custom_style: Optional[CaptionStyle] = None
    break_on_punctuation: bool = True
    min_pause_for_break: float = 0.5  # Seconds of pause to trigger line break

    def get_effective_position(self) -> PositionConfig:
        """Get the effective position config."""
        if self.position_config:
            return self.position_config
        return PositionConfig(vertical=self.position)


@dataclass
class CaptionLine:
    """A line of caption with timing."""
    text: str
    words: List[WordTimestamp]
    start: float
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "duration": round(self.duration, 3),
            "words": [
                {"word": w.word, "start": round(w.start, 3), "end": round(w.end, 3)}
                for w in self.words
            ]
        }


@dataclass
class CaptionResult:
    """Result of caption generation."""
    captioned_video_path: Optional[str] = None
    srt_content: str = ""
    vtt_content: str = ""
    ass_content: str = ""
    lines: List[CaptionLine] = field(default_factory=list)
    transcription: Optional[TranscriptionResult] = None
    config: Optional[CaptionConfig] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "captioned_video_path": self.captioned_video_path,
            "lines": [line.to_dict() for line in self.lines],
            "line_count": len(self.lines),
            "word_count": sum(len(line.words) for line in self.lines),
            "duration": self.transcription.duration if self.transcription else 0,
            "language": self.transcription.language if self.transcription else None,
            "has_srt": bool(self.srt_content),
            "has_vtt": bool(self.vtt_content),
            "metadata": self.metadata
        }


# ============================================================================
# Caption Line Segmentation
# ============================================================================

def segment_into_lines(
    words: List[WordTimestamp],
    max_words: int = 7,
    break_on_punctuation: bool = True,
    min_pause: float = 0.5
) -> List[CaptionLine]:
    """
    Segment word timestamps into caption lines.

    Rules:
    1. Maximum max_words per line
    2. Break at sentence-ending punctuation (.!?)
    3. Break at pauses longer than min_pause
    4. Prefer breaks at commas and clause boundaries

    Args:
        words: List of WordTimestamp from transcription
        max_words: Maximum words per line
        break_on_punctuation: Break at punctuation marks
        min_pause: Minimum pause (seconds) to trigger line break

    Returns:
        List of CaptionLine
    """
    if not words:
        return []

    lines = []
    current_words = []
    current_start = None

    punctuation_breaks = ".!?;"  # Strong break points
    weak_breaks = ",:"  # Weak break points (prefer if near limit)

    for i, word in enumerate(words):
        # Start new line if needed
        if current_start is None:
            current_start = word.start

        current_words.append(word)

        # Determine if we should break
        should_break = False
        break_reason = None

        # Check max words
        if len(current_words) >= max_words:
            should_break = True
            break_reason = "max_words"

        # Check punctuation breaks
        elif break_on_punctuation:
            word_text = word.word.strip()
            if any(word_text.endswith(p) for p in punctuation_breaks):
                should_break = True
                break_reason = "punctuation"
            elif len(current_words) >= max_words - 2:
                # Near limit, check for weak breaks
                if any(word_text.endswith(p) for p in weak_breaks):
                    should_break = True
                    break_reason = "weak_punctuation"

        # Check pause duration
        if not should_break and i < len(words) - 1:
            next_word = words[i + 1]
            pause = next_word.start - word.end
            if pause >= min_pause:
                should_break = True
                break_reason = "pause"

        # Create line if breaking
        if should_break and current_words:
            text = " ".join(w.word for w in current_words)
            lines.append(CaptionLine(
                text=text.strip(),
                words=current_words.copy(),
                start=current_start,
                end=current_words[-1].end
            ))
            current_words = []
            current_start = None

    # Handle remaining words
    if current_words:
        text = " ".join(w.word for w in current_words)
        lines.append(CaptionLine(
            text=text.strip(),
            words=current_words,
            start=current_start,
            end=current_words[-1].end
        ))

    return lines


# ============================================================================
# Subtitle Format Generation
# ============================================================================

def generate_srt_from_lines(lines: List[CaptionLine]) -> str:
    """Generate SRT subtitle content from caption lines."""
    srt_entries = []

    for i, line in enumerate(lines, 1):
        start_time = format_timestamp(line.start)
        end_time = format_timestamp(line.end)

        srt_entries.append(f"{i}")
        srt_entries.append(f"{start_time} --> {end_time}")
        srt_entries.append(line.text)
        srt_entries.append("")

    return "\n".join(srt_entries)


def generate_vtt_from_lines(lines: List[CaptionLine]) -> str:
    """Generate VTT subtitle content from caption lines."""
    vtt_entries = ["WEBVTT", ""]

    for line in lines:
        start_time = format_vtt_timestamp(line.start)
        end_time = format_vtt_timestamp(line.end)

        vtt_entries.append(f"{start_time} --> {end_time}")
        vtt_entries.append(line.text)
        vtt_entries.append("")

    return "\n".join(vtt_entries)


def generate_ass_from_lines(
    lines: List[CaptionLine],
    style: CaptionStyle,
    word_highlight: bool = True,
    position: CaptionPosition = CaptionPosition.BOTTOM,
    position_config: Optional[PositionConfig] = None
) -> str:
    """
    Generate ASS subtitle with word-level highlighting.

    ASS format supports per-character styling and timing,
    enabling karaoke-style word highlighting.
    """
    # ASS header
    ass_content = [
        "[Script Info]",
        "Title: Generated Captions",
        "ScriptType: v4.00+",
        "PlayResX: 1920",
        "PlayResY: 1080",
        "Timer: 100.0000",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
    ]

    # Calculate alignment and margin based on position
    if position_config:
        alignment = position_config.get_ass_alignment()
        margin_v = position_config.get_margin_v()
    else:
        alignment = {
            CaptionPosition.BOTTOM: 2,  # Bottom center
            CaptionPosition.CENTER: 5,  # Middle center
            CaptionPosition.TOP: 8      # Top center
        }.get(position, 2)
        margin_v = 50  # Default margin

    # Default style
    primary_color = style._hex_to_ass_color(style.font_color)
    highlight_color = style._hex_to_ass_color(style.highlight_color)
    outline_color = style._hex_to_ass_color(style.outline_color)

    ass_content.append(
        f"Style: Default,{style.font_family},{style.font_size},"
        f"{primary_color},&H000000FF,{outline_color},&H00000000,"
        f"0,0,0,0,100,100,0,0,1,{style.outline_width},{style.shadow_offset},"
        f"{alignment},10,10,{margin_v},1"
    )

    # Highlight style for active words
    ass_content.append(
        f"Style: Highlight,{style.font_family},{style.font_size},"
        f"{highlight_color},&H000000FF,{outline_color},&H00000000,"
        f"1,0,0,0,100,100,0,0,1,{style.outline_width},{style.shadow_offset},"
        f"{alignment},10,10,{margin_v},1"
    )

    ass_content.extend([
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
    ])

    # Generate dialogue lines
    for line in lines:
        start_time = _format_ass_time(line.start)
        end_time = _format_ass_time(line.end)

        if word_highlight and line.words:
            # Generate karaoke-style highlighting
            karaoke_text = _generate_karaoke_text(
                line.words,
                style,
                line.start
            )
            ass_content.append(
                f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{karaoke_text}"
            )
        else:
            # Simple text without highlighting
            ass_content.append(
                f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{line.text}"
            )

    return "\n".join(ass_content)


def _format_ass_time(seconds: float) -> str:
    """Format seconds as ASS time (H:MM:SS.cc)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centisecs = int((seconds % 1) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"


def _generate_karaoke_text(
    words: List[WordTimestamp],
    style: CaptionStyle,
    line_start: float
) -> str:
    """
    Generate ASS karaoke tags for word-level highlighting.

    Uses \\k tags for timing and \\c for color changes.
    """
    parts = []

    for i, word in enumerate(words):
        # Calculate duration in centiseconds for this word
        duration_cs = int((word.end - word.start) * 100)

        # Time since line start for highlighting timing
        word_offset_cs = int((word.start - line_start) * 100)

        # Use karaoke timing tag
        # \\kf = smooth fill, \\k = instant fill
        highlight_color = style._hex_to_ass_color(style.highlight_color)
        normal_color = style._hex_to_ass_color(style.font_color)

        # Build text with karaoke effect
        parts.append(f"{{\\kf{duration_cs}}}{word.word}")

        # Add space between words
        if i < len(words) - 1:
            parts.append(" ")

    return "".join(parts)


# ============================================================================
# Video Embedding
# ============================================================================

async def embed_captions_in_video(
    video_path: str,
    ass_content: str,
    output_path: Optional[str] = None
) -> str:
    """
    Embed ASS subtitles into video using FFmpeg.

    Args:
        video_path: Path to input video
        ass_content: ASS subtitle content
        output_path: Path for output video (optional, creates temp file)

    Returns:
        Path to captioned video
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    # Create temp file for ASS subtitles
    temp_dir = tempfile.mkdtemp()
    ass_path = Path(temp_dir) / "captions.ass"
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    # Output path
    if output_path:
        output_path = Path(output_path)
    else:
        output_path = Path(temp_dir) / f"captioned_{video_path.name}"

    # FFmpeg command to burn in subtitles
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vf", f"ass={str(ass_path)}",
        "-c:a", "copy",
        "-y",
        str(output_path)
    ]

    logger.info(
        "Embedding captions in video",
        extra={
            "metadata": {
                "input": str(video_path),
                "output": str(output_path)
            }
        }
    )

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg error: {stderr.decode()}")

        return str(output_path)

    except Exception as e:
        logger.error(f"Caption embedding failed: {e}")
        raise


# ============================================================================
# Main Caption Generation
# ============================================================================

async def generate_captions(
    video_path: str,
    config: Optional[CaptionConfig] = None,
    transcription: Optional[TranscriptionResult] = None
) -> CaptionResult:
    """
    Generate captions for a video with word-level highlighting.

    Args:
        video_path: Path to input video
        config: Caption configuration (optional)
        transcription: Pre-computed transcription (optional)

    Returns:
        CaptionResult with all outputs
    """
    config = config or CaptionConfig()
    video_path = Path(video_path)

    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    logger.info(
        "Generating captions",
        extra={
            "metadata": {
                "video": str(video_path),
                "style": config.style,
                "max_words_per_line": config.max_words_per_line,
                "word_highlight": config.word_highlight
            }
        }
    )

    # Get or generate transcription
    if transcription is None:
        transcription = await transcribe_video(str(video_path), config.language)

    # Segment into caption lines
    lines = segment_into_lines(
        words=transcription.words,
        max_words=config.max_words_per_line,
        break_on_punctuation=config.break_on_punctuation,
        min_pause=config.min_pause_for_break
    )

    # Get style
    style = config.custom_style or get_default_style()

    # Generate subtitle formats
    srt_content = generate_srt_from_lines(lines)
    vtt_content = generate_vtt_from_lines(lines)
    ass_content = generate_ass_from_lines(
        lines=lines,
        style=style,
        word_highlight=config.word_highlight,
        position=config.position,
        position_config=config.get_effective_position()
    )

    # Embed captions in video
    captioned_video_path = await embed_captions_in_video(
        str(video_path),
        ass_content
    )

    result = CaptionResult(
        captioned_video_path=captioned_video_path,
        srt_content=srt_content,
        vtt_content=vtt_content,
        ass_content=ass_content,
        lines=lines,
        transcription=transcription,
        config=config,
        metadata={
            "line_count": len(lines),
            "word_count": len(transcription.words),
            "duration": transcription.duration,
            "language": transcription.language
        }
    )

    logger.info(
        "Caption generation complete",
        extra={
            "metadata": {
                "lines": len(lines),
                "words": len(transcription.words),
                "output": captioned_video_path
            }
        }
    )

    return result


def get_default_style() -> CaptionStyle:
    """Get the default caption style."""
    return CaptionStyle(
        font_family="Arial",
        font_size=48,
        font_color="#FFFFFF",
        outline_color="#000000",
        outline_width=2,
        highlight_color="#FFFF00"
    )


# ============================================================================
# Utility Functions
# ============================================================================

def validate_word_sync(lines: List[CaptionLine], tolerance_ms: float = 50) -> List[Dict]:
    """
    Validate that word timings are within acceptable tolerance.

    Returns list of any words that exceed the tolerance.
    """
    issues = []

    for line in lines:
        for i, word in enumerate(line.words):
            # Check for negative duration
            if word.end <= word.start:
                issues.append({
                    "word": word.word,
                    "issue": "negative_duration",
                    "start": word.start,
                    "end": word.end
                })

            # Check for gaps between words
            if i > 0:
                prev_word = line.words[i - 1]
                gap = (word.start - prev_word.end) * 1000  # Convert to ms

                if gap > tolerance_ms:
                    issues.append({
                        "word": word.word,
                        "issue": "large_gap",
                        "gap_ms": gap,
                        "after": prev_word.word
                    })

    return issues


def estimate_reading_speed(lines: List[CaptionLine]) -> Dict[str, float]:
    """
    Estimate reading speed for caption lines.

    Returns words per minute and characters per second.
    """
    if not lines:
        return {"wpm": 0, "cps": 0}

    total_words = sum(len(line.words) for line in lines)
    total_chars = sum(len(line.text) for line in lines)
    total_duration = lines[-1].end - lines[0].start

    if total_duration <= 0:
        return {"wpm": 0, "cps": 0}

    wpm = (total_words / total_duration) * 60
    cps = total_chars / total_duration

    return {
        "wpm": round(wpm, 1),
        "cps": round(cps, 1),
        "avg_words_per_line": round(total_words / len(lines), 1),
        "avg_line_duration": round(total_duration / len(lines), 2)
    }
