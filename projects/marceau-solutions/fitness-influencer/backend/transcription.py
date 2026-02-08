#!/usr/bin/env python3
"""
Transcription Service for Fitness Influencer AI v2.0

OpenAI Whisper integration with word-level timestamps for caption sync.

Features:
    - Word-level timestamps for karaoke-style captions
    - Multi-language support (en, es, pt, auto-detect)
    - Audio extraction from video (FFmpeg)
    - Chunked transcription for long files
    - Cost tracking per transcription
    - Local Whisper fallback

Usage:
    from backend.transcription import transcribe_audio, transcribe_video

    # Transcribe audio file
    result = await transcribe_audio("/path/to/audio.mp3", language="en")

    # Transcribe video (auto-extracts audio)
    result = await transcribe_video("/path/to/video.mp4")

    # Access word-level timestamps
    for word in result.words:
        print(f"{word.word}: {word.start:.2f}s - {word.end:.2f}s")
"""

import os
import subprocess
import tempfile
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any, Literal
from dataclasses import dataclass, field
from datetime import datetime
import json

from backend.logging_config import get_logger, log_job_event

logger = get_logger(__name__)

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")

# File limits
MAX_FILE_SIZE_MB = 25
CHUNK_DURATION_SECONDS = 600  # 10 minutes per chunk

# Supported languages
SUPPORTED_LANGUAGES = ["en", "es", "pt", "fr", "de", "it", "ja", "ko", "zh", "auto"]

# Cost tracking (per minute of audio)
WHISPER_COST_PER_MINUTE = 0.006  # $0.006 per minute


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class WordTimestamp:
    """Word with timing information."""
    word: str
    start: float  # Start time in seconds
    end: float    # End time in seconds
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "word": self.word,
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "confidence": round(self.confidence, 3)
        }


@dataclass
class TranscriptionSegment:
    """Segment of transcription (sentence or phrase)."""
    text: str
    start: float
    end: float
    words: List[WordTimestamp] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "words": [w.to_dict() for w in self.words]
        }


@dataclass
class TranscriptionResult:
    """Full transcription result with metadata."""
    text: str
    language: str
    duration: float  # Audio duration in seconds
    segments: List[TranscriptionSegment]
    words: List[WordTimestamp]
    cost: float = 0.0
    model: str = WHISPER_MODEL
    is_fallback: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "language": self.language,
            "duration": round(self.duration, 2),
            "segments": [s.to_dict() for s in self.segments],
            "words": [w.to_dict() for w in self.words],
            "word_count": len(self.words),
            "cost": round(self.cost, 4),
            "model": self.model,
            "is_fallback": self.is_fallback,
            "metadata": self.metadata
        }


# ============================================================================
# Audio Extraction
# ============================================================================

async def extract_audio_from_video(
    video_path: str,
    output_format: str = "mp3"
) -> str:
    """
    Extract audio from video file using FFmpeg.

    Args:
        video_path: Path to video file
        output_format: Output audio format (mp3, wav, m4a)

    Returns:
        Path to extracted audio file
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Create temp file for audio
    temp_dir = tempfile.mkdtemp()
    audio_path = Path(temp_dir) / f"audio.{output_format}"

    # FFmpeg command to extract audio
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vn",  # No video
        "-acodec", "libmp3lame" if output_format == "mp3" else "copy",
        "-ar", "16000",  # 16kHz sample rate (optimal for Whisper)
        "-ac", "1",  # Mono
        "-y",  # Overwrite
        str(audio_path)
    ]

    logger.info(
        f"Extracting audio from video",
        extra={
            "metadata": {
                "video_path": str(video_path),
                "output_path": str(audio_path)
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

        return str(audio_path)

    except Exception as e:
        logger.error(f"Audio extraction failed: {e}")
        raise


async def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file in seconds using FFprobe."""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "json",
        str(audio_path)
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, _ = await process.communicate()

    try:
        data = json.loads(stdout.decode())
        return float(data["format"]["duration"])
    except (json.JSONDecodeError, KeyError):
        return 0.0


async def get_file_size_mb(file_path: str) -> float:
    """Get file size in megabytes."""
    return Path(file_path).stat().st_size / (1024 * 1024)


# ============================================================================
# Whisper API Transcription
# ============================================================================

async def transcribe_with_whisper_api(
    audio_path: str,
    language: Optional[str] = None,
    response_format: str = "verbose_json"
) -> Dict[str, Any]:
    """
    Transcribe audio using OpenAI Whisper API.

    Args:
        audio_path: Path to audio file
        language: Language code (en, es, pt, etc.) or None for auto-detect
        response_format: API response format

    Returns:
        Raw API response
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    import httpx

    # Prepare request
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    # Read audio file
    with open(audio_path, "rb") as f:
        audio_data = f.read()

    # Build form data
    files = {
        "file": (Path(audio_path).name, audio_data, "audio/mpeg"),
    }
    data = {
        "model": WHISPER_MODEL,
        "response_format": response_format,
        "timestamp_granularities[]": "word",  # Request word-level timestamps
    }

    if language and language != "auto":
        data["language"] = language

    logger.info(
        "Calling Whisper API",
        extra={
            "metadata": {
                "file": Path(audio_path).name,
                "language": language or "auto"
            }
        }
    )

    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()
        return response.json()


async def transcribe_chunk(
    audio_path: str,
    chunk_start: float,
    chunk_end: float,
    language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transcribe a chunk of audio.

    Extracts portion of audio file and transcribes it.
    """
    # Extract chunk using FFmpeg
    temp_dir = tempfile.mkdtemp()
    chunk_path = Path(temp_dir) / "chunk.mp3"

    cmd = [
        "ffmpeg",
        "-i", str(audio_path),
        "-ss", str(chunk_start),
        "-t", str(chunk_end - chunk_start),
        "-y",
        str(chunk_path)
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()

    # Transcribe chunk
    result = await transcribe_with_whisper_api(str(chunk_path), language)

    # Adjust timestamps to account for chunk offset
    if "words" in result:
        for word in result["words"]:
            word["start"] += chunk_start
            word["end"] += chunk_start

    if "segments" in result:
        for segment in result["segments"]:
            segment["start"] += chunk_start
            segment["end"] += chunk_start

    # Cleanup
    chunk_path.unlink(missing_ok=True)

    return result


# ============================================================================
# Local Whisper Fallback
# ============================================================================

async def transcribe_with_local_whisper(
    audio_path: str,
    language: Optional[str] = None,
    model_size: str = "base"
) -> Dict[str, Any]:
    """
    Transcribe using local Whisper model (fallback).

    Requires: pip install openai-whisper

    Args:
        audio_path: Path to audio file
        language: Language code
        model_size: Whisper model size (tiny, base, small, medium, large)

    Returns:
        Transcription result in API-compatible format
    """
    logger.info(
        "Using local Whisper fallback",
        extra={"metadata": {"model_size": model_size}}
    )

    try:
        import whisper

        # Load model
        model = whisper.load_model(model_size)

        # Transcribe with word timestamps
        result = model.transcribe(
            audio_path,
            language=language if language != "auto" else None,
            word_timestamps=True
        )

        # Convert to API-compatible format
        words = []
        for segment in result.get("segments", []):
            for word_info in segment.get("words", []):
                words.append({
                    "word": word_info["word"].strip(),
                    "start": word_info["start"],
                    "end": word_info["end"]
                })

        return {
            "text": result["text"],
            "language": result.get("language", language or "en"),
            "duration": result.get("duration", 0),
            "words": words,
            "segments": result.get("segments", [])
        }

    except ImportError:
        logger.error("Local Whisper not available: pip install openai-whisper")
        raise
    except Exception as e:
        logger.error(f"Local Whisper failed: {e}")
        raise


# ============================================================================
# Main Transcription Functions
# ============================================================================

async def transcribe_audio(
    audio_path: str,
    language: Optional[str] = None,
    use_chunking: bool = True,
    fallback_to_local: bool = True
) -> TranscriptionResult:
    """
    Transcribe audio file with word-level timestamps.

    Args:
        audio_path: Path to audio file (mp3, wav, m4a, etc.)
        language: Language code (en, es, pt, auto) or None for auto-detect
        use_chunking: Split long files into chunks
        fallback_to_local: Use local Whisper if API fails

    Returns:
        TranscriptionResult with full text, segments, and word timestamps
    """
    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Validate language
    if language and language not in SUPPORTED_LANGUAGES:
        logger.warning(f"Unsupported language '{language}', using auto-detect")
        language = None

    # Get audio info
    duration = await get_audio_duration(str(audio_path))
    file_size_mb = await get_file_size_mb(str(audio_path))

    logger.info(
        "Starting transcription",
        extra={
            "metadata": {
                "file": audio_path.name,
                "duration": duration,
                "size_mb": round(file_size_mb, 2),
                "language": language or "auto"
            }
        }
    )

    is_fallback = False
    raw_result = None

    try:
        # Check if chunking needed
        if use_chunking and (file_size_mb > MAX_FILE_SIZE_MB or duration > CHUNK_DURATION_SECONDS):
            # Transcribe in chunks
            logger.info(f"Using chunked transcription ({duration / 60:.1f} minutes)")
            raw_result = await transcribe_chunked(str(audio_path), duration, language)
        else:
            # Single transcription
            raw_result = await transcribe_with_whisper_api(str(audio_path), language)

    except Exception as e:
        logger.warning(f"Whisper API failed: {e}")

        if fallback_to_local:
            try:
                raw_result = await transcribe_with_local_whisper(str(audio_path), language)
                is_fallback = True
            except Exception as local_e:
                logger.error(f"Local Whisper also failed: {local_e}")
                raise

    # Parse result into structured format
    return parse_transcription_result(raw_result, duration, is_fallback)


async def transcribe_chunked(
    audio_path: str,
    total_duration: float,
    language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transcribe long audio by splitting into chunks.

    Args:
        audio_path: Path to audio file
        total_duration: Total audio duration
        language: Language code

    Returns:
        Combined transcription result
    """
    chunks = []
    chunk_start = 0.0

    while chunk_start < total_duration:
        chunk_end = min(chunk_start + CHUNK_DURATION_SECONDS, total_duration)

        logger.info(
            f"Transcribing chunk {len(chunks) + 1}",
            extra={
                "metadata": {
                    "start": chunk_start,
                    "end": chunk_end
                }
            }
        )

        chunk_result = await transcribe_chunk(audio_path, chunk_start, chunk_end, language)
        chunks.append(chunk_result)

        chunk_start = chunk_end

    # Combine chunks
    combined_text = " ".join(c.get("text", "") for c in chunks)
    combined_words = []
    combined_segments = []

    for chunk in chunks:
        combined_words.extend(chunk.get("words", []))
        combined_segments.extend(chunk.get("segments", []))

    return {
        "text": combined_text,
        "language": chunks[0].get("language", "en") if chunks else "en",
        "duration": total_duration,
        "words": combined_words,
        "segments": combined_segments
    }


async def transcribe_video(
    video_path: str,
    language: Optional[str] = None,
    cleanup_audio: bool = True
) -> TranscriptionResult:
    """
    Transcribe video by extracting and transcribing audio.

    Args:
        video_path: Path to video file
        language: Language code
        cleanup_audio: Delete extracted audio after transcription

    Returns:
        TranscriptionResult with word-level timestamps
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Extract audio
    audio_path = await extract_audio_from_video(str(video_path))

    try:
        # Transcribe
        result = await transcribe_audio(audio_path, language)
        result.metadata["source_video"] = str(video_path)
        return result

    finally:
        # Cleanup
        if cleanup_audio and Path(audio_path).exists():
            Path(audio_path).unlink(missing_ok=True)
            Path(audio_path).parent.rmdir()


# ============================================================================
# Result Parsing
# ============================================================================

def parse_transcription_result(
    raw_result: Dict[str, Any],
    duration: float,
    is_fallback: bool = False
) -> TranscriptionResult:
    """
    Parse raw API/local result into structured TranscriptionResult.
    """
    # Parse words
    words = []
    for word_data in raw_result.get("words", []):
        words.append(WordTimestamp(
            word=word_data.get("word", "").strip(),
            start=float(word_data.get("start", 0)),
            end=float(word_data.get("end", 0)),
            confidence=float(word_data.get("probability", 1.0))
        ))

    # Parse segments
    segments = []
    for seg_data in raw_result.get("segments", []):
        seg_words = []

        # Try to match words to segments
        seg_start = float(seg_data.get("start", 0))
        seg_end = float(seg_data.get("end", 0))

        for word in words:
            if seg_start <= word.start <= seg_end:
                seg_words.append(word)

        segments.append(TranscriptionSegment(
            text=seg_data.get("text", "").strip(),
            start=seg_start,
            end=seg_end,
            words=seg_words
        ))

    # Calculate cost
    cost = (duration / 60) * WHISPER_COST_PER_MINUTE

    # Log completion
    log_job_event(
        job_id="transcription",
        event="completed",
        job_type="transcription",
        duration_seconds=duration,
        word_count=len(words),
        cost=cost,
        is_fallback=is_fallback
    )

    return TranscriptionResult(
        text=raw_result.get("text", ""),
        language=raw_result.get("language", "en"),
        duration=duration,
        segments=segments,
        words=words,
        cost=cost,
        model="local" if is_fallback else WHISPER_MODEL,
        is_fallback=is_fallback
    )


# ============================================================================
# Utility Functions
# ============================================================================

def format_timestamp(seconds: float) -> str:
    """
    Format seconds as SRT timestamp (HH:MM:SS,mmm).
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_vtt_timestamp(seconds: float) -> str:
    """
    Format seconds as VTT timestamp (HH:MM:SS.mmm).
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def generate_srt(result: TranscriptionResult, max_words_per_line: int = 7) -> str:
    """
    Generate SRT subtitle file from transcription.

    Args:
        result: TranscriptionResult
        max_words_per_line: Maximum words per subtitle line

    Returns:
        SRT file content as string
    """
    srt_lines = []
    subtitle_num = 1

    # Group words into subtitle blocks
    current_words = []
    current_start = None

    for word in result.words:
        if current_start is None:
            current_start = word.start

        current_words.append(word)

        # Check if we should create a new subtitle
        if len(current_words) >= max_words_per_line:
            text = " ".join(w.word for w in current_words)
            end_time = current_words[-1].end

            srt_lines.append(f"{subtitle_num}")
            srt_lines.append(f"{format_timestamp(current_start)} --> {format_timestamp(end_time)}")
            srt_lines.append(text)
            srt_lines.append("")

            subtitle_num += 1
            current_words = []
            current_start = None

    # Handle remaining words
    if current_words:
        text = " ".join(w.word for w in current_words)
        end_time = current_words[-1].end

        srt_lines.append(f"{subtitle_num}")
        srt_lines.append(f"{format_timestamp(current_start)} --> {format_timestamp(end_time)}")
        srt_lines.append(text)
        srt_lines.append("")

    return "\n".join(srt_lines)


def generate_vtt(result: TranscriptionResult, max_words_per_line: int = 7) -> str:
    """
    Generate VTT subtitle file from transcription.

    Args:
        result: TranscriptionResult
        max_words_per_line: Maximum words per subtitle line

    Returns:
        VTT file content as string
    """
    vtt_lines = ["WEBVTT", ""]

    current_words = []
    current_start = None

    for word in result.words:
        if current_start is None:
            current_start = word.start

        current_words.append(word)

        if len(current_words) >= max_words_per_line:
            text = " ".join(w.word for w in current_words)
            end_time = current_words[-1].end

            vtt_lines.append(f"{format_vtt_timestamp(current_start)} --> {format_vtt_timestamp(end_time)}")
            vtt_lines.append(text)
            vtt_lines.append("")

            current_words = []
            current_start = None

    if current_words:
        text = " ".join(w.word for w in current_words)
        end_time = current_words[-1].end

        vtt_lines.append(f"{format_vtt_timestamp(current_start)} --> {format_vtt_timestamp(end_time)}")
        vtt_lines.append(text)
        vtt_lines.append("")

    return "\n".join(vtt_lines)
