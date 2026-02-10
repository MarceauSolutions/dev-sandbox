"""
Sound Effects Engine — Auto-sync SFX to cuts, zooms, and text appearances.

Provides a library of fitness-appropriate sound effects (whoosh, impact, pop,
swoosh, bass hit) and auto-places them at transitions detected in the video
timeline. Uses FFmpeg audio filters for mixing.
"""

import asyncio
import json
import logging
import os
import random
import struct
import subprocess
import math
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── SFX Categories ────────────────────────────────────────────────────────────

SFX_CATEGORIES = {
    "whoosh": {
        "description": "Quick air sweep for transitions and cuts",
        "use_at": ["jump_cut", "transition", "swipe"],
        "volume": -8,  # dB relative to main audio
    },
    "impact": {
        "description": "Heavy hit for text bombs and emphasis moments",
        "use_at": ["text_appear", "punch_zoom", "emphasis"],
        "volume": -6,
    },
    "pop": {
        "description": "Light pop for subtle transitions and UI elements",
        "use_at": ["jump_cut", "subtitle_appear"],
        "volume": -10,
    },
    "swoosh": {
        "description": "Smooth sweep for scene transitions",
        "use_at": ["scene_change", "transition"],
        "volume": -8,
    },
    "bass_hit": {
        "description": "Deep bass for dramatic reveals and intros",
        "use_at": ["intro", "reveal", "punch_zoom"],
        "volume": -4,
    },
    "click": {
        "description": "Sharp click for counter ticks and rep counts",
        "use_at": ["counter_tick", "rep_count"],
        "volume": -12,
    },
    "rise": {
        "description": "Rising tone for building anticipation",
        "use_at": ["buildup", "transition"],
        "volume": -10,
    },
}


def _generate_tone(frequency: float, duration: float, sample_rate: int = 44100,
                   fade_ms: float = 10) -> bytes:
    """Generate a simple sine wave tone as raw PCM bytes."""
    num_samples = int(sample_rate * duration)
    fade_samples = int(sample_rate * fade_ms / 1000)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        amplitude = math.sin(2 * math.pi * frequency * t)
        # Apply fade in/out
        if i < fade_samples:
            amplitude *= i / fade_samples
        elif i > num_samples - fade_samples:
            amplitude *= (num_samples - i) / fade_samples
        sample = int(amplitude * 32767)
        samples.append(struct.pack('<h', max(-32768, min(32767, sample))))
    return b''.join(samples)


def _generate_noise_burst(duration: float, sample_rate: int = 44100) -> bytes:
    """Generate a short noise burst (for whoosh/swoosh effects)."""
    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        envelope = 1.0
        # Quick attack, longer decay
        attack = int(num_samples * 0.1)
        if i < attack:
            envelope = i / attack
        else:
            envelope = max(0, 1.0 - (i - attack) / (num_samples - attack))
        sample = int(random.uniform(-1, 1) * envelope * 16384)
        samples.append(struct.pack('<h', max(-32768, min(32767, sample))))
    return b''.join(samples)


def generate_sfx_file(sfx_type: str, output_path: str, sample_rate: int = 44100) -> Optional[str]:
    """
    Generate a synthetic SFX WAV file.

    For production use, replace these with real SFX samples in data/sfx/.
    These synthetic versions work as functional placeholders.
    """
    duration_map = {
        "whoosh": 0.3,
        "impact": 0.15,
        "pop": 0.08,
        "swoosh": 0.4,
        "bass_hit": 0.25,
        "click": 0.05,
        "rise": 0.5,
    }
    duration = duration_map.get(sfx_type, 0.2)

    try:
        if sfx_type == "whoosh":
            pcm = _generate_noise_burst(duration, sample_rate)
        elif sfx_type == "impact":
            # Low frequency burst
            pcm = _generate_tone(60, duration, sample_rate, fade_ms=5)
        elif sfx_type == "pop":
            pcm = _generate_tone(800, duration, sample_rate, fade_ms=3)
        elif sfx_type == "swoosh":
            pcm = _generate_noise_burst(duration, sample_rate)
        elif sfx_type == "bass_hit":
            pcm = _generate_tone(40, duration, sample_rate, fade_ms=8)
        elif sfx_type == "click":
            pcm = _generate_tone(2000, duration, sample_rate, fade_ms=2)
        elif sfx_type == "rise":
            # Frequency sweep from low to high
            num_samples = int(sample_rate * duration)
            fade_samples = int(sample_rate * 0.01)
            samples = []
            for i in range(num_samples):
                t = i / sample_rate
                freq = 200 + (2000 * (i / num_samples))
                amplitude = math.sin(2 * math.pi * freq * t)
                env = i / num_samples  # Rising envelope
                if i < fade_samples:
                    env *= i / fade_samples
                sample = int(amplitude * env * 24000)
                samples.append(struct.pack('<h', max(-32768, min(32767, sample))))
            pcm = b''.join(samples)
        else:
            pcm = _generate_tone(440, duration, sample_rate)

        # Write WAV file
        _write_wav(output_path, pcm, sample_rate)
        return output_path
    except Exception as e:
        logger.error(f"Failed to generate SFX '{sfx_type}': {e}")
        return None


def _write_wav(path: str, pcm_data: bytes, sample_rate: int = 44100,
               channels: int = 1, bits_per_sample: int = 16):
    """Write raw PCM data as a WAV file."""
    data_size = len(pcm_data)
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8

    with open(path, 'wb') as f:
        # RIFF header
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + data_size))
        f.write(b'WAVE')
        # fmt chunk
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))  # chunk size
        f.write(struct.pack('<H', 1))   # PCM format
        f.write(struct.pack('<H', channels))
        f.write(struct.pack('<I', sample_rate))
        f.write(struct.pack('<I', byte_rate))
        f.write(struct.pack('<H', block_align))
        f.write(struct.pack('<H', bits_per_sample))
        # data chunk
        f.write(b'data')
        f.write(struct.pack('<I', data_size))
        f.write(pcm_data)


def _get_sfx_path(sfx_type: str, sfx_dir: str) -> Optional[str]:
    """
    Get path to an SFX file. Checks for real samples first,
    falls back to generating synthetic ones.
    """
    sfx_dir_path = Path(sfx_dir)
    sfx_dir_path.mkdir(parents=True, exist_ok=True)

    # Check for real samples (WAV or MP3)
    for ext in (".wav", ".mp3", ".ogg"):
        candidate = sfx_dir_path / f"{sfx_type}{ext}"
        if candidate.exists():
            return str(candidate)

    # Check for numbered variants (e.g., whoosh_1.wav, whoosh_2.wav)
    variants = list(sfx_dir_path.glob(f"{sfx_type}_*.*"))
    if variants:
        return str(random.choice(variants))

    # Generate synthetic fallback
    synthetic_path = sfx_dir_path / f"{sfx_type}_synthetic.wav"
    if synthetic_path.exists():
        return str(synthetic_path)

    logger.info(f"No real SFX found for '{sfx_type}', generating synthetic")
    result = generate_sfx_file(sfx_type, str(synthetic_path))
    return result


# ── SFX Placement Logic ──────────────────────────────────────────────────────

def _detect_cut_points(video_path: str, threshold: float = 0.3) -> List[float]:
    """Detect cut/transition points in video via scene detection."""
    cmd = [
        "ffmpeg", "-i", video_path, "-vf",
        f"select='gt(scene,{threshold})',showinfo",
        "-f", "null", "-"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        timestamps = []
        for line in result.stderr.split("\n"):
            if "pts_time:" in line:
                try:
                    ts = float(line.split("pts_time:")[1].split(" ")[0])
                    timestamps.append(ts)
                except (ValueError, IndexError):
                    continue
        return timestamps
    except Exception as e:
        logger.warning(f"Cut detection failed: {e}")
        return []


def _detect_silence_boundaries(video_path: str, noise_db: float = -30,
                                min_silence: float = 0.3) -> List[Tuple[float, float]]:
    """Detect silence regions (start, end) — the ends are where cuts happen."""
    cmd = [
        "ffmpeg", "-i", video_path, "-af",
        f"silencedetect=noise={noise_db}dB:d={min_silence}",
        "-f", "null", "-"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        regions = []
        start = None
        for line in result.stderr.split("\n"):
            if "silence_start:" in line:
                try:
                    start = float(line.split("silence_start:")[1].strip().split(" ")[0])
                except (ValueError, IndexError):
                    start = None
            elif "silence_end:" in line and start is not None:
                try:
                    end = float(line.split("silence_end:")[1].split("|")[0].strip())
                    regions.append((start, end))
                except (ValueError, IndexError):
                    pass
                start = None
        return regions
    except Exception as e:
        logger.warning(f"Silence detection failed: {e}")
        return []


def plan_sfx_placement(
    video_path: str,
    zoom_moments: Optional[List[float]] = None,
    text_moments: Optional[List[float]] = None,
    cut_points: Optional[List[float]] = None,
    min_gap: float = 0.5,
) -> List[Dict[str, Any]]:
    """
    Plan where to place SFX based on detected events.

    Returns list of: {"timestamp": float, "sfx_type": str, "volume_db": int}
    """
    placements = []

    # Auto-detect cuts if not provided
    if cut_points is None:
        silence_regions = _detect_silence_boundaries(video_path)
        cut_points = [end for _, end in silence_regions]

    # Place whoosh/pop at cut points
    for ts in (cut_points or []):
        sfx = random.choice(["whoosh", "pop"])
        placements.append({
            "timestamp": ts,
            "sfx_type": sfx,
            "volume_db": SFX_CATEGORIES[sfx]["volume"],
            "reason": "jump_cut",
        })

    # Place impact/bass at zoom moments
    for ts in (zoom_moments or []):
        sfx = random.choice(["impact", "bass_hit"])
        placements.append({
            "timestamp": ts,
            "sfx_type": sfx,
            "volume_db": SFX_CATEGORIES[sfx]["volume"],
            "reason": "punch_zoom",
        })

    # Place impact at text appearances
    for ts in (text_moments or []):
        placements.append({
            "timestamp": ts,
            "sfx_type": "impact",
            "volume_db": SFX_CATEGORIES["impact"]["volume"],
            "reason": "text_appear",
        })

    # Sort by timestamp
    placements.sort(key=lambda x: x["timestamp"])

    # Enforce minimum gap between SFX
    filtered = []
    for p in placements:
        if not filtered or (p["timestamp"] - filtered[-1]["timestamp"]) >= min_gap:
            filtered.append(p)

    return filtered


# ── FFmpeg Audio Mixing ──────────────────────────────────────────────────────

def _get_duration(video_path: str) -> float:
    """Get video/audio duration via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", video_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
        return float(data.get("format", {}).get("duration", 0))
    except Exception:
        return 0


async def apply_sound_effects(
    video_path: str,
    output_path: str,
    placements: Optional[List[Dict]] = None,
    zoom_moments: Optional[List[float]] = None,
    text_moments: Optional[List[float]] = None,
    sfx_dir: Optional[str] = None,
    master_volume: float = 1.0,
) -> Optional[str]:
    """
    Mix sound effects into video at specified timestamps.

    Args:
        video_path: Input video path
        output_path: Output video path
        placements: Pre-planned SFX placements (from plan_sfx_placement)
        zoom_moments: Timestamps of punch zooms (auto-assigns impact SFX)
        text_moments: Timestamps of text appearances (auto-assigns impact SFX)
        sfx_dir: Directory containing SFX files
        master_volume: Overall SFX volume multiplier (0.0 - 2.0)

    Returns:
        Output path if successful, None otherwise
    """
    if sfx_dir is None:
        sfx_dir = str(Path(video_path).parent.parent / "data" / "sfx")

    # Plan placements if not provided
    if placements is None:
        placements = plan_sfx_placement(
            video_path,
            zoom_moments=zoom_moments,
            text_moments=text_moments,
        )

    if not placements:
        logger.info("No SFX placements, copying original")
        import shutil
        shutil.copy2(video_path, output_path)
        return output_path

    logger.info(f"Applying {len(placements)} sound effects")

    # Resolve SFX file paths
    sfx_files = {}
    for p in placements:
        sfx_type = p["sfx_type"]
        if sfx_type not in sfx_files:
            path = _get_sfx_path(sfx_type, sfx_dir)
            if path:
                sfx_files[sfx_type] = path
            else:
                logger.warning(f"Could not find/generate SFX: {sfx_type}")

    # Filter placements to only those with available SFX
    valid_placements = [p for p in placements if p["sfx_type"] in sfx_files]

    if not valid_placements:
        logger.warning("No valid SFX files available, copying original")
        import shutil
        shutil.copy2(video_path, output_path)
        return output_path

    # Build FFmpeg complex filter for mixing
    # Strategy: Create a silence base, overlay each SFX at its timestamp,
    # then mix with original audio
    duration = _get_duration(video_path)
    if duration <= 0:
        logger.error("Could not determine video duration")
        return None

    # Build filter_complex
    inputs = ["-i", video_path]  # Input 0: original video
    filter_parts = []
    amix_inputs = ["[0:a]"]  # Start with original audio

    for idx, p in enumerate(valid_placements):
        sfx_path = sfx_files[p["sfx_type"]]
        input_idx = idx + 1
        inputs.extend(["-i", sfx_path])

        # Calculate volume adjustment
        vol_db = p.get("volume_db", -8)
        if master_volume != 1.0:
            vol_db += 20 * math.log10(max(0.01, master_volume))

        # Delay SFX to correct timestamp and adjust volume
        delay_ms = int(p["timestamp"] * 1000)
        filter_parts.append(
            f"[{input_idx}:a]volume={vol_db}dB,"
            f"adelay={delay_ms}|{delay_ms},"
            f"apad=whole_dur={duration}[sfx{idx}]"
        )
        amix_inputs.append(f"[sfx{idx}]")

    # Mix all audio streams
    n_inputs = len(amix_inputs)
    filter_parts.append(
        f"{''.join(amix_inputs)}amix=inputs={n_inputs}:"
        f"duration=first:dropout_transition=2[aout]"
    )

    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            logger.error(f"FFmpeg SFX mix failed: {result.stderr[-500:]}")
            # Fallback: copy original
            import shutil
            shutil.copy2(video_path, output_path)
            return output_path
        logger.info(f"SFX applied successfully: {output_path}")
        return output_path
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg SFX mix timed out")
        return None
    except Exception as e:
        logger.error(f"SFX mix error: {e}")
        return None


def generate_all_synthetic_sfx(sfx_dir: str) -> Dict[str, str]:
    """Generate all synthetic SFX files for the library. Run once to bootstrap."""
    sfx_dir_path = Path(sfx_dir)
    sfx_dir_path.mkdir(parents=True, exist_ok=True)
    results = {}
    for sfx_type in SFX_CATEGORIES:
        output = sfx_dir_path / f"{sfx_type}_synthetic.wav"
        if not output.exists():
            path = generate_sfx_file(sfx_type, str(output))
            if path:
                results[sfx_type] = path
                logger.info(f"Generated: {sfx_type} → {path}")
        else:
            results[sfx_type] = str(output)
    return results


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Apply sound effects to video")
    parser.add_argument("video", nargs="?", help="Input video path")
    parser.add_argument("-o", "--output", help="Output path", default=None)
    parser.add_argument("--sfx-dir", help="SFX directory", default=None)
    parser.add_argument("--volume", type=float, default=1.0, help="Master volume (0.0-2.0)")
    parser.add_argument("--generate-sfx", action="store_true",
                        help="Generate synthetic SFX library")
    parser.add_argument("--list-sfx", action="store_true",
                        help="List available SFX categories")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.list_sfx:
        print("\nAvailable SFX Categories:")
        print("-" * 60)
        for name, info in SFX_CATEGORIES.items():
            print(f"  {name:12s}  {info['description']}")
            print(f"  {'':12s}  Use at: {', '.join(info['use_at'])}")
            print(f"  {'':12s}  Volume: {info['volume']} dB")
            print()
    elif args.generate_sfx:
        sfx_dir = args.sfx_dir or "data/sfx"
        results = generate_all_synthetic_sfx(sfx_dir)
        print(f"\nGenerated {len(results)} SFX files in {sfx_dir}/")
        for name, path in results.items():
            print(f"  {name}: {path}")
    elif args.video:
        output = args.output or args.video.replace(".mp4", "_sfx.mp4")
        result = asyncio.run(apply_sound_effects(
            args.video, output,
            sfx_dir=args.sfx_dir,
            master_volume=args.volume,
        ))
        if result:
            print(f"Output: {result}")
        else:
            print("Failed to apply sound effects")
    else:
        parser.print_help()
