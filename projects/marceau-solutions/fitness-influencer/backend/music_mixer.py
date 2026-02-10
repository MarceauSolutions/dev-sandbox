"""
Music Mixer — Background music with auto-duck, beat-sync, and volume management.

Features:
- Add royalty-free background music tracks
- Auto-duck music under speech (sidechain compression via FFmpeg)
- Beat detection for sync cuts to music tempo
- Volume normalization and balancing
- Music library management with categories

Implementation: FFmpeg loudnorm, sidechaincompress, ebur128 audio filters
"""

import asyncio
import json
import logging
import math
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ── Enums & Config ────────────────────────────────────────────────────────────

class MusicCategory(str, Enum):
    ENERGETIC = "energetic"
    MOTIVATIONAL = "motivational"
    INTENSE = "intense"
    CHILL = "chill"
    UPBEAT = "upbeat"
    CINEMATIC = "cinematic"


class DuckMode(str, Enum):
    SIDECHAIN = "sidechain"       # FFmpeg sidechaincompress — true ducking
    VOLUME_ENVELOPE = "envelope"   # Volume keyframes from silence detection
    NONE = "none"                  # No ducking, constant volume


@dataclass
class BeatInfo:
    """Detected beat from audio analysis."""
    timestamp: float
    strength: float  # 0-1 normalized
    bpm: float = 0.0


@dataclass
class MusicTrack:
    """Metadata for a music file in the library."""
    path: str
    name: str
    category: MusicCategory
    duration: float = 0.0
    bpm: float = 0.0
    tags: List[str] = field(default_factory=list)


@dataclass
class MixResult:
    """Result of mixing music into a video."""
    success: bool
    output_path: str
    music_track: Optional[str] = None
    duck_mode: str = "none"
    music_volume: float = 0.0
    detected_bpm: float = 0.0
    beat_count: int = 0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output_path": self.output_path,
            "music_track": self.music_track,
            "duck_mode": self.duck_mode,
            "music_volume": self.music_volume,
            "detected_bpm": self.detected_bpm,
            "beat_count": self.beat_count,
            "error": self.error,
        }


# ── Audio Utilities ───────────────────────────────────────────────────────────

def _run_ffmpeg(args: List[str], timeout: int = 300) -> subprocess.CompletedProcess:
    """Run an FFmpeg command and return the result."""
    cmd = ["ffmpeg", "-y"] + args
    logger.debug(f"FFmpeg: {' '.join(cmd)}")
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _run_ffprobe(args: List[str]) -> subprocess.CompletedProcess:
    """Run ffprobe and return result."""
    cmd = ["ffprobe"] + args
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def get_audio_duration(path: str) -> float:
    """Get duration of an audio/video file in seconds."""
    result = _run_ffprobe([
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        path,
    ])
    if result.returncode == 0:
        data = json.loads(result.stdout)
        return float(data.get("format", {}).get("duration", 0))
    return 0.0


def get_audio_loudness(path: str) -> Dict[str, float]:
    """Analyze loudness using EBU R128 (FFmpeg ebur128 filter)."""
    result = _run_ffmpeg([
        "-i", path,
        "-af", "ebur128=peak=true",
        "-f", "null", "-",
    ])
    # Parse ebur128 output from stderr
    stats = {"integrated": -24.0, "true_peak": -1.0, "lra": 10.0}
    stderr = result.stderr or ""
    for line in stderr.split("\n"):
        if "I:" in line and "LUFS" in line:
            match = re.search(r"I:\s*([-\d.]+)", line)
            if match:
                stats["integrated"] = float(match.group(1))
        if "Peak:" in line or "True peak" in line.lower():
            match = re.search(r"([-\d.]+)\s*dB", line)
            if match:
                stats["true_peak"] = float(match.group(1))
        if "LRA:" in line:
            match = re.search(r"LRA:\s*([-\d.]+)", line)
            if match:
                stats["lra"] = float(match.group(1))
    return stats


# ── Beat Detection ────────────────────────────────────────────────────────────

async def detect_beats(
    audio_path: str,
    min_bpm: float = 60,
    max_bpm: float = 200,
) -> Tuple[List[BeatInfo], float]:
    """
    Detect beats in audio using FFmpeg onset detection.

    Returns (beat_list, estimated_bpm).
    Uses astats filter for energy-based onset detection.
    """
    # Extract audio energy at high resolution using FFmpeg
    result = _run_ffprobe([
        "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "format=duration",
        "-of", "json",
        audio_path,
    ])
    duration = 0.0
    if result.returncode == 0:
        data = json.loads(result.stdout)
        duration = float(data.get("format", {}).get("duration", 0))

    if duration <= 0:
        return [], 0.0

    # Use FFmpeg to detect audio onsets via volume-based peak detection
    # Extract volume levels at high resolution
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        result = _run_ffmpeg([
            "-i", audio_path,
            "-af", "astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level:file=" + tmp_path,
            "-f", "null", "-",
        ])

        if not os.path.exists(tmp_path):
            return [], 0.0

        # Parse RMS levels to find beats (energy peaks)
        timestamps = []
        levels = []
        with open(tmp_path) as f:
            current_ts = 0.0
            for line in f:
                line = line.strip()
                if line.startswith("frame:"):
                    # Extract pts_time
                    match = re.search(r"pts_time:([\d.]+)", line)
                    if match:
                        current_ts = float(match.group(1))
                elif "lavfi.astats.Overall.RMS_level" in line:
                    match = re.search(r"=([-\d.]+)", line)
                    if match:
                        val = float(match.group(1))
                        if val > -100:  # Skip silence
                            timestamps.append(current_ts)
                            levels.append(val)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    if len(timestamps) < 4:
        return [], 0.0

    # Normalize levels to 0-1
    min_level = min(levels)
    max_level = max(levels)
    level_range = max_level - min_level if max_level > min_level else 1.0
    normalized = [(l - min_level) / level_range for l in levels]

    # Find peaks (local maxima above threshold)
    threshold = 0.6
    min_gap = 60.0 / max_bpm  # Minimum time between beats
    beats = []
    last_beat_ts = -999

    for i in range(1, len(normalized) - 1):
        if (normalized[i] > normalized[i - 1] and
                normalized[i] >= normalized[i + 1] and
                normalized[i] > threshold and
                timestamps[i] - last_beat_ts >= min_gap):
            beats.append(BeatInfo(
                timestamp=timestamps[i],
                strength=normalized[i],
            ))
            last_beat_ts = timestamps[i]

    # Estimate BPM from beat intervals
    bpm = 0.0
    if len(beats) >= 3:
        intervals = [beats[i + 1].timestamp - beats[i].timestamp for i in range(len(beats) - 1)]
        # Filter outliers
        intervals = [iv for iv in intervals if 60.0 / max_bpm <= iv <= 60.0 / min_bpm]
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            bpm = 60.0 / avg_interval if avg_interval > 0 else 0.0
            # Update beats with BPM
            for b in beats:
                b.bpm = round(bpm, 1)

    return beats, round(bpm, 1)


# ── Speech Detection ──────────────────────────────────────────────────────────

async def detect_speech_segments(
    video_path: str,
    silence_thresh_db: float = -35,
    min_speech_dur: float = 0.3,
) -> List[Tuple[float, float]]:
    """
    Detect speech segments by inverting silence detection.

    Returns list of (start, end) tuples for speech segments.
    """
    result = _run_ffmpeg([
        "-i", video_path,
        "-af", f"silencedetect=noise={silence_thresh_db}dB:d={min_speech_dur}",
        "-f", "null", "-",
    ])

    stderr = result.stderr or ""
    duration = get_audio_duration(video_path)

    # Parse silence start/end from FFmpeg output
    silence_segments = []
    current_start = None
    for line in stderr.split("\n"):
        if "silence_start:" in line:
            match = re.search(r"silence_start:\s*([\d.]+)", line)
            if match:
                current_start = float(match.group(1))
        elif "silence_end:" in line and current_start is not None:
            match = re.search(r"silence_end:\s*([\d.]+)", line)
            if match:
                silence_segments.append((current_start, float(match.group(1))))
                current_start = None

    # Invert silence segments to get speech segments
    speech_segments = []
    prev_end = 0.0
    for s_start, s_end in silence_segments:
        if s_start > prev_end + 0.1:
            speech_segments.append((prev_end, s_start))
        prev_end = s_end
    if prev_end < duration - 0.1:
        speech_segments.append((prev_end, duration))

    return speech_segments


# ── Music Library ─────────────────────────────────────────────────────────────

def scan_music_library(library_dir: str) -> List[MusicTrack]:
    """
    Scan a directory for music files organized by category.

    Expected structure:
        data/music/
        ├── energetic/
        │   ├── track1.mp3
        │   └── track2.wav
        ├── motivational/
        └── intense/
    """
    tracks = []
    library_path = Path(library_dir)
    if not library_path.exists():
        return tracks

    audio_exts = {".mp3", ".wav", ".ogg", ".m4a", ".aac", ".flac"}

    for cat_dir in library_path.iterdir():
        if not cat_dir.is_dir():
            continue
        try:
            category = MusicCategory(cat_dir.name.lower())
        except ValueError:
            category = MusicCategory.ENERGETIC  # Default

        for audio_file in cat_dir.iterdir():
            if audio_file.suffix.lower() in audio_exts:
                dur = get_audio_duration(str(audio_file))
                tracks.append(MusicTrack(
                    path=str(audio_file),
                    name=audio_file.stem,
                    category=category,
                    duration=dur,
                ))

    return tracks


def select_track(
    tracks: List[MusicTrack],
    category: Optional[MusicCategory] = None,
    min_duration: float = 0,
) -> Optional[MusicTrack]:
    """Select a track from the library matching criteria."""
    candidates = tracks
    if category:
        candidates = [t for t in candidates if t.category == category]
    if min_duration > 0:
        candidates = [t for t in candidates if t.duration >= min_duration]
    if not candidates:
        return None
    # Return longest matching track (covers full video)
    return max(candidates, key=lambda t: t.duration)


# ── Core Mixing Functions ─────────────────────────────────────────────────────

async def mix_music_sidechain(
    video_path: str,
    music_path: str,
    output_path: str,
    music_volume: float = 0.15,
    duck_amount: float = 0.7,
    attack: float = 0.01,
    release: float = 0.5,
) -> bool:
    """
    Mix music into video with sidechain compression (auto-duck under speech).

    The speech audio drives the compressor to reduce music volume when someone talks.

    Args:
        video_path: Input video with speech audio
        music_path: Background music file
        output_path: Output video path
        music_volume: Base music volume (0-1)
        duck_amount: How much to duck (0=none, 1=full mute)
        attack: Duck attack time in seconds
        release: Duck release time in seconds
    """
    video_dur = get_audio_duration(video_path)

    # Build FFmpeg filter complex:
    # [0:a] = video's speech audio (sidechain signal)
    # [1:a] = music audio (to be compressed)
    # sidechaincompress ducks music when speech is present
    threshold = 0.02  # Low threshold to catch all speech
    ratio = max(2, int(duck_amount * 20))  # 2:1 to 20:1 based on duck_amount

    filter_complex = (
        f"[1:a]aloop=loop=-1:size=2e+09,atrim=duration={video_dur},"
        f"volume={music_volume}[music];"
        f"[0:a][music]sidechaincompress="
        f"threshold={threshold}:ratio={ratio}:"
        f"attack={attack}:release={release}:"
        f"level_sc=1:mix=0.95[ducked];"
        f"[0:a][ducked]amix=inputs=2:duration=shortest:weights=1 0.9[out]"
    )

    result = _run_ffmpeg([
        "-i", video_path,
        "-i", music_path,
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[out]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path,
    ])

    if result.returncode != 0:
        logger.error(f"Sidechain mix failed: {result.stderr}")
        return False
    return os.path.exists(output_path)


async def mix_music_envelope(
    video_path: str,
    music_path: str,
    output_path: str,
    music_volume: float = 0.15,
    speech_segments: Optional[List[Tuple[float, float]]] = None,
    duck_volume: float = 0.05,
    fade_dur: float = 0.3,
) -> bool:
    """
    Mix music with volume envelope ducking based on speech segments.

    Falls back to this when sidechaincompress isn't available or
    when you want more predictable ducking behavior.
    """
    video_dur = get_audio_duration(video_path)

    if speech_segments is None:
        speech_segments = await detect_speech_segments(video_path)

    # Build volume keyframes for music track
    # Default: music at full volume, duck during speech
    volume_parts = [f"volume={music_volume}"]

    if speech_segments:
        # Create volume filter with enable expressions for ducking
        enables = []
        for start, end in speech_segments:
            enables.append(
                f"volume=enable='between(t,{start:.2f},{end:.2f})':"
                f"volume={duck_volume / music_volume if music_volume > 0 else 0}"
            )

        # Use a simpler approach: generate the music at base volume,
        # then apply ducking via afade at speech boundaries
        fade_filters = []
        for start, end in speech_segments:
            fade_filters.append(f"afade=t=out:st={max(0, start - fade_dur):.2f}:d={fade_dur}")
            fade_filters.append(f"afade=t=in:st={end:.2f}:d={fade_dur}")

    # Simpler approach: use volume with enable for speech ducking
    duck_ratio = duck_volume / music_volume if music_volume > 0 else 0
    duck_enables = ":".join(
        f"between(t\\,{s:.2f}\\,{e:.2f})" for s, e in speech_segments
    ) if speech_segments else ""

    if duck_enables:
        music_filter = (
            f"aloop=loop=-1:size=2e+09,atrim=duration={video_dur},"
            f"volume={music_volume},"
            f"volume=enable='{duck_enables}':volume={duck_ratio}"
        )
    else:
        music_filter = (
            f"aloop=loop=-1:size=2e+09,atrim=duration={video_dur},"
            f"volume={music_volume}"
        )

    filter_complex = (
        f"[1:a]{music_filter}[music];"
        f"[0:a][music]amix=inputs=2:duration=shortest:weights=1 0.9[out]"
    )

    result = _run_ffmpeg([
        "-i", video_path,
        "-i", music_path,
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[out]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path,
    ])

    if result.returncode != 0:
        logger.error(f"Envelope mix failed: {result.stderr}")
        return False
    return os.path.exists(output_path)


async def mix_music_simple(
    video_path: str,
    music_path: str,
    output_path: str,
    music_volume: float = 0.12,
) -> bool:
    """Simple music overlay at constant volume. No ducking."""
    video_dur = get_audio_duration(video_path)

    filter_complex = (
        f"[1:a]aloop=loop=-1:size=2e+09,atrim=duration={video_dur},"
        f"volume={music_volume}[music];"
        f"[0:a][music]amix=inputs=2:duration=shortest:weights=1 0.9[out]"
    )

    result = _run_ffmpeg([
        "-i", video_path,
        "-i", music_path,
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[out]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path,
    ])

    if result.returncode != 0:
        logger.error(f"Simple mix failed: {result.stderr}")
        return False
    return os.path.exists(output_path)


# ── Main Public API ───────────────────────────────────────────────────────────

async def add_background_music(
    video_path: str,
    output_path: str,
    music_path: Optional[str] = None,
    music_dir: Optional[str] = None,
    category: Optional[str] = None,
    music_volume: float = 0.15,
    duck_mode: str = "sidechain",
    duck_amount: float = 0.7,
    detect_bpm: bool = False,
) -> MixResult:
    """
    Add background music to a video with automatic speech ducking.

    Args:
        video_path: Input video path
        output_path: Output video path
        music_path: Direct path to music file (overrides library selection)
        music_dir: Path to music library directory
        category: Music category to select from library
        music_volume: Base music volume (0.0 - 1.0, default 0.15)
        duck_mode: "sidechain", "envelope", or "none"
        duck_amount: How aggressively to duck (0-1)
        detect_bpm: Whether to run beat detection

    Returns:
        MixResult with output path and metadata
    """
    # Resolve music file
    track_path = music_path
    track_name = None

    if not track_path and music_dir:
        cat = MusicCategory(category) if category else MusicCategory.ENERGETIC
        video_dur = get_audio_duration(video_path)
        tracks = scan_music_library(music_dir)
        selected = select_track(tracks, category=cat, min_duration=video_dur * 0.5)
        if selected:
            track_path = selected.path
            track_name = selected.name

    if not track_path or not os.path.exists(track_path):
        return MixResult(
            success=False,
            output_path=output_path,
            error="No music file found. Provide music_path or populate music_dir.",
        )

    if not track_name:
        track_name = Path(track_path).stem

    # Detect BPM if requested
    bpm = 0.0
    beat_count = 0
    if detect_bpm:
        beats, bpm = await detect_beats(track_path)
        beat_count = len(beats)

    # Apply mixing based on duck mode
    mode = DuckMode(duck_mode) if duck_mode in [m.value for m in DuckMode] else DuckMode.SIDECHAIN

    if mode == DuckMode.SIDECHAIN:
        success = await mix_music_sidechain(
            video_path, track_path, output_path,
            music_volume=music_volume,
            duck_amount=duck_amount,
        )
        # Fallback to envelope if sidechain fails
        if not success:
            logger.warning("Sidechain failed, falling back to envelope ducking")
            mode = DuckMode.VOLUME_ENVELOPE
            success = await mix_music_envelope(
                video_path, track_path, output_path,
                music_volume=music_volume,
            )
    elif mode == DuckMode.VOLUME_ENVELOPE:
        success = await mix_music_envelope(
            video_path, track_path, output_path,
            music_volume=music_volume,
        )
    else:
        success = await mix_music_simple(
            video_path, track_path, output_path,
            music_volume=music_volume,
        )

    return MixResult(
        success=success,
        output_path=output_path if success else "",
        music_track=track_name,
        duck_mode=mode.value,
        music_volume=music_volume,
        detected_bpm=bpm,
        beat_count=beat_count,
        error=None if success else "Music mixing failed",
    )


async def get_beat_timestamps(
    audio_path: str,
    min_bpm: float = 80,
    max_bpm: float = 180,
) -> Dict[str, Any]:
    """
    Public API to get beat timestamps for beat-sync editing.

    Returns dict with beats list and BPM for use in cut synchronization.
    """
    beats, bpm = await detect_beats(audio_path, min_bpm=min_bpm, max_bpm=max_bpm)
    return {
        "bpm": bpm,
        "beat_count": len(beats),
        "beats": [{"timestamp": b.timestamp, "strength": b.strength} for b in beats],
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Music Mixer — Add background music with auto-duck")
    parser.add_argument("video", help="Input video path")
    parser.add_argument("--music", help="Music file path")
    parser.add_argument("--music-dir", help="Music library directory")
    parser.add_argument("--category", default="energetic", choices=[c.value for c in MusicCategory])
    parser.add_argument("--volume", type=float, default=0.15, help="Music volume (0-1)")
    parser.add_argument("--duck-mode", default="sidechain", choices=[m.value for m in DuckMode])
    parser.add_argument("--output", default="output_with_music.mp4")
    parser.add_argument("--detect-bpm", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    result = asyncio.run(add_background_music(
        video_path=args.video,
        output_path=args.output,
        music_path=args.music,
        music_dir=args.music_dir,
        category=args.category,
        music_volume=args.volume,
        duck_mode=args.duck_mode,
        detect_bpm=args.detect_bpm,
    ))

    print(f"\nMusic Mix Result:")
    print(f"  Success: {result.success}")
    print(f"  Output: {result.output_path}")
    print(f"  Track: {result.music_track}")
    print(f"  Duck mode: {result.duck_mode}")
    if result.detected_bpm:
        print(f"  BPM: {result.detected_bpm} ({result.beat_count} beats)")
    if result.error:
        print(f"  Error: {result.error}")
