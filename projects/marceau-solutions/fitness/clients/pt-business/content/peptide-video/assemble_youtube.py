#!/usr/bin/env python3
"""
assemble_youtube.py - Assemble Peptide YouTube Video from Raw Assets

Assembles the full peptide education YouTube video from raw section MOVs,
B-roll clips, and graphic overlays. No Premiere Pro needed.

Pipeline:
  Phase 0: Compress raw MOVs to H.264 MP4 (12GB → ~1GB)
  Phase 1: Jump cut silence removal (tightens pacing)
  Phase 2: Concatenate all sections into base video
  Phase 3: Overlay B-roll at specific timestamps (voice continues)
  Phase 4: Apply graphic overlays (lower thirds, headers, stats)
  Phase 5: Audio normalization + final export

Usage:
    python assemble_youtube.py --quick       # Phases 0+2+3 (fast, ~30 min)
    python assemble_youtube.py --full        # All phases (best quality, ~60+ min)
    python assemble_youtube.py --phase 0     # Compress only
    python assemble_youtube.py --phase 2     # Concat only (requires phase 0)
    python assemble_youtube.py --resume      # Resume from last completed phase
"""

import argparse
import os
import sys
import json
import re
import subprocess
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed


# === PATHS ===
BASE_DIR = Path(__file__).parent
RECORDING_DIR = BASE_DIR / "TalkingHeadRecording"
BROLL_DIR = BASE_DIR / "B-Roll"
GRAPHICS_DIR = BASE_DIR / "Graphics" / "Static"
OUTPUT_DIR = BASE_DIR / "Final_Product"
WORK_DIR = OUTPUT_DIR / "work"
STATE_FILE = WORK_DIR / "pipeline_state.json"

# === OUTPUT SETTINGS ===
WIDTH = 1920
HEIGHT = 1080
FPS = 30
CRF = 20          # Quality (18-23 is good for YouTube)
PRESET = "medium"  # Encoding speed/quality tradeoff

# === SECTIONS (in assembly order) ===
SECTIONS = [
    {"name": "Hook",         "file": "Hook.mov",             "chapter": "Hook"},
    {"name": "Section1",     "file": "Section1_fixed.mov",   "chapter": "What Are Peptides?"},
    {"name": "Section2",     "file": "Section2.mov",         "chapter": "The 4 Categories"},
    {"name": "Section3",     "file": "Section3.mov",         "chapter": "Science vs Hype"},
    {"name": "Section4",     "file": "Section4.mov",         "chapter": "What I've Learned"},
    {"name": "Section5",     "file": "Section5.mov",         "chapter": "Decision Framework"},
    {"name": "CTA",          "file": "CallToAction.mov",     "chapter": "Subscribe & Comment"},
]

# === B-ROLL INSERTIONS ===
# offset_pct = approximate position within the section where B-roll should appear
# The voice audio continues over B-roll (only video track is replaced)
BROLL_INSERTIONS = [
    {"section": "Section1", "offset_pct": 0.13, "file": "01-gym-training.mp4", "dur": 12},
    {"section": "Section1", "offset_pct": 0.50, "file": "02-amino-acid.mp4",   "dur": 10},
    {"section": "Section3", "offset_pct": 0.20, "file": "03-lab-scene.mp4",    "dur": 12},
    {"section": "Section4", "offset_pct": 0.25, "file": "04-supplements.mp4",  "dur": 10},
    {"section": "Section4", "offset_pct": 0.55, "file": "05-morning-routine.mp4", "dur": 12},
    {"section": "Section5", "offset_pct": 0.35, "file": "06-decision-framework.mp4", "dur": 10},
]


# ============================================================
# UTILITIES
# ============================================================

def run_ffmpeg(args, desc="FFmpeg", timeout=1200):
    """Run FFmpeg command and return success status."""
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning"] + args
    print(f"  $ ffmpeg {' '.join(args[:6])}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            print(f"  ERROR: {result.stderr[:500]}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"  ERROR: {desc} timed out after {timeout}s")
        return False


def get_duration(path):
    """Get video duration in seconds using ffprobe."""
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json",
           "-show_format", str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    return 0


def get_video_info(path):
    """Get video width, height, fps using ffprobe."""
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json",
           "-show_streams", "-select_streams", "v:0", str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        data = json.loads(result.stdout)
        stream = data["streams"][0]
        fps_str = stream.get("r_frame_rate", "30/1")
        num, den = fps_str.split("/")
        fps = round(int(num) / int(den))
        return {
            "width": int(stream["width"]),
            "height": int(stream["height"]),
            "fps": fps,
        }
    return {"width": WIDTH, "height": HEIGHT, "fps": FPS}


def format_time(seconds):
    """Format seconds as MM:SS."""
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def save_state(state):
    """Save pipeline state to JSON."""
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def load_state():
    """Load pipeline state from JSON."""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"completed_phases": [], "section_durations": {}}


# ============================================================
# PHASE 0: COMPRESS RAW MOVs TO H.264 MP4
# ============================================================

def compress_section(section):
    """Compress a single section MOV to MP4. Called in parallel."""
    name = section["name"]
    input_path = RECORDING_DIR / section["file"]
    output_path = WORK_DIR / "00_compressed" / f"{name}.mp4"

    if not input_path.exists():
        return name, False, 0, f"Not found: {input_path}"

    if output_path.exists():
        dur = get_duration(output_path)
        if dur > 0:
            return name, True, dur, "Already compressed (skipped)"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if file is already small enough (like Section1_fixed.mov at 81MB)
    file_size_mb = input_path.stat().st_size / (1024 * 1024)

    args = [
        "-i", str(input_path),
        "-vf", f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
               f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264",
        "-crf", str(CRF),
        "-preset", PRESET if file_size_mb > 200 else "fast",
        "-c:a", "aac", "-b:a", "192k",
        "-r", str(FPS),
        "-movflags", "+faststart",
        str(output_path)
    ]

    success = run_ffmpeg(args, desc=f"Compress {name}")
    dur = get_duration(output_path) if success else 0
    return name, success, dur, f"{file_size_mb:.0f}MB → {output_path.stat().st_size/(1024*1024):.0f}MB" if success else "Failed"


def phase0_compress():
    """Compress all raw MOVs to H.264 MP4 at 1080p."""
    print("\n" + "=" * 70)
    print("PHASE 0: COMPRESS RAW MOVs")
    print("=" * 70)

    (WORK_DIR / "00_compressed").mkdir(parents=True, exist_ok=True)

    results = {}
    # Process sequentially to avoid overwhelming the machine
    for section in SECTIONS:
        name, success, dur, msg = compress_section(section)
        results[name] = {"success": success, "duration": dur, "msg": msg}
        status = "OK" if success else "FAIL"
        print(f"  [{status}] {name}: {msg} ({format_time(dur)})")

    total_dur = sum(r["duration"] for r in results.values())
    successes = sum(1 for r in results.values() if r["success"])
    print(f"\n  Compressed: {successes}/{len(SECTIONS)} sections")
    print(f"  Total duration: {format_time(total_dur)} ({total_dur:.1f}s)")

    return results


# ============================================================
# PHASE 1: JUMP CUT (SILENCE REMOVAL)
# ============================================================

def detect_silence(input_path, noise_db=-35, min_duration=0.4):
    """Detect silent segments in a video using FFmpeg silencedetect."""
    cmd = [
        "ffmpeg", "-i", str(input_path),
        "-af", f"silencedetect=noise={noise_db}dB:d={min_duration}",
        "-f", "null", "-"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    stderr = result.stderr

    # Parse silence_start and silence_end from FFmpeg output
    silences = []
    starts = re.findall(r'silence_start: ([\d.]+)', stderr)
    ends = re.findall(r'silence_end: ([\d.]+)', stderr)

    for i, start in enumerate(starts):
        end = ends[i] if i < len(ends) else None
        if end:
            silences.append((float(start), float(end)))

    return silences


def phase1_jumpcut(noise_db=-30, min_silence=0.3, pad=0.04):
    """
    Aggressive jump cut: remove ALL dead air (Ryan Humiston style).

    Uses trim/concat filter approach for correct container duration.
    The old select/setpts approach left container metadata at the original
    duration, causing downstream concat to produce frozen-frame padding.

    Defaults tuned for tight pacing:
      -30dB threshold (catches quieter pauses)
      0.3s minimum silence (removes even short gaps)
      0.04s pad (minimal breathing room)
    """
    print("\n" + "=" * 70)
    print("PHASE 1: JUMP CUT - Humiston Style (trim/concat)")
    print(f"  Noise threshold: {noise_db}dB, Min silence: {min_silence}s, Pad: {pad}s")
    print("=" * 70)

    input_dir = WORK_DIR / "00_compressed"
    output_dir = WORK_DIR / "01_jumpcut"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    for section in SECTIONS:
        name = section["name"]
        input_path = input_dir / f"{name}.mp4"
        output_path = output_dir / f"{name}.mp4"

        if not input_path.exists():
            print(f"  [{name}] SKIP - compressed file not found")
            continue

        orig_dur = get_duration(input_path)
        print(f"\n  [{name}] Detecting silence in {format_time(orig_dur)} clip...")

        silences = detect_silence(input_path, noise_db, min_silence)
        print(f"    Found {len(silences)} silent segments")

        if not silences:
            print(f"    No silence detected, copying as-is")
            subprocess.run(["cp", str(input_path), str(output_path)])
            results[name] = {"duration": orig_dur, "original": orig_dur}
            continue

        # Build list of non-silent segments (the parts we KEEP)
        segments = []
        prev_end = 0.0
        for s_start, s_end in silences:
            seg_start = prev_end
            seg_end = s_start + pad  # Small pad into silence start
            if seg_end > seg_start + 0.05:  # Skip very tiny segments
                segments.append((seg_start, min(seg_end, orig_dur)))
            prev_end = max(0, s_end - pad)  # Resume slightly before speech

        # Add final segment (after last silence to end)
        if prev_end < orig_dur - 0.05:
            segments.append((prev_end, orig_dur))

        print(f"    Keeping {len(segments)} speech segments")

        # Build trim/concat filter: trim each keep segment, concat them
        # This produces correct container duration (unlike select+setpts)
        filter_parts = []
        concat_v = []
        concat_a = []

        for i, (seg_start, seg_end) in enumerate(segments):
            # Video: trim + reset PTS
            filter_parts.append(
                f"[0:v]trim={seg_start:.3f}:{seg_end:.3f},setpts=PTS-STARTPTS[v{i}]"
            )
            # Audio: atrim + reset PTS
            filter_parts.append(
                f"[0:a]atrim={seg_start:.3f}:{seg_end:.3f},asetpts=PTS-STARTPTS[a{i}]"
            )
            concat_v.append(f"[v{i}]")
            concat_a.append(f"[a{i}]")

        # Interleave [v0][a0][v1][a1]... for concat
        concat_inputs = []
        for v, a in zip(concat_v, concat_a):
            concat_inputs.append(v)
            concat_inputs.append(a)

        n = len(segments)
        filter_parts.append(
            f"{''.join(concat_inputs)}concat=n={n}:v=1:a=1[outv][outa]"
        )

        filter_str = ";\n".join(filter_parts)

        # Write filter to temp file (can be very long with 70+ segments)
        filter_file = WORK_DIR / f"01_filter_{name}.txt"
        with open(filter_file, 'w') as f:
            f.write(filter_str)

        args = [
            "-i", str(input_path),
            "-filter_complex_script", str(filter_file),
            "-map", "[outv]", "-map", "[outa]",
            "-c:v", "libx264", "-crf", str(CRF), "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            str(output_path)
        ]

        success = run_ffmpeg(args, desc=f"JumpCut {name}", timeout=600)

        if success:
            new_dur = get_duration(output_path)
            saved = orig_dur - new_dur
            pct = (saved / orig_dur * 100) if orig_dur > 0 else 0
            print(f"    {format_time(orig_dur)} → {format_time(new_dur)} (saved {saved:.1f}s, {pct:.0f}%)")
            results[name] = {"duration": new_dur, "original": orig_dur}
        else:
            # Fallback: copy original
            print(f"    Jump cut failed, using original")
            subprocess.run(["cp", str(input_path), str(output_path)])
            results[name] = {"duration": orig_dur, "original": orig_dur}

    total_orig = sum(r["original"] for r in results.values())
    total_new = sum(r["duration"] for r in results.values())
    total_saved = total_orig - total_new
    print(f"\n  Total: {format_time(total_orig)} → {format_time(total_new)}")
    print(f"  Saved: {format_time(total_saved)} ({total_saved/total_orig*100:.0f}%)")

    return results


# ============================================================
# PHASE 2: CONCATENATE ALL SECTIONS
# ============================================================

def phase2_concat(use_jumpcut=True):
    """Concatenate all section videos into one base video."""
    print("\n" + "=" * 70)
    print("PHASE 2: CONCATENATE SECTIONS")
    print("=" * 70)

    source_dir = WORK_DIR / ("01_jumpcut" if use_jumpcut else "00_compressed")
    if not source_dir.exists():
        source_dir = WORK_DIR / "00_compressed"
        print(f"  Note: Using compressed files (no jump cuts found)")

    output_path = WORK_DIR / "02_concat.mp4"
    concat_list = WORK_DIR / "concat_list.txt"

    # Build concat list
    files = []
    section_starts = {}
    running_time = 0.0

    for section in SECTIONS:
        name = section["name"]
        path = source_dir / f"{name}.mp4"

        if not path.exists():
            print(f"  WARNING: Missing {name}, skipping")
            continue

        dur = get_duration(path)
        section_starts[name] = running_time
        files.append(str(path))
        print(f"  {name}: {format_time(dur)} (starts at {format_time(running_time)})")
        running_time += dur

    print(f"\n  Total expected duration: {format_time(running_time)}")

    # Write concat list file
    with open(concat_list, 'w') as f:
        for filepath in files:
            f.write(f"file '{filepath}'\n")

    # Concatenate using FFmpeg concat demuxer (fast, no re-encode if formats match)
    args = [
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c:v", "libx264", "-crf", str(CRF), "-preset", PRESET,
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(output_path)
    ]

    print(f"\n  Concatenating {len(files)} sections...")
    success = run_ffmpeg(args, desc="Concat", timeout=900)

    if success:
        actual_dur = get_duration(output_path)
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"\n  Base video: {format_time(actual_dur)} ({size_mb:.0f}MB)")
        print(f"  Output: {output_path}")
    else:
        print(f"\n  ERROR: Concatenation failed")

    # Save section starts for B-roll timing
    return section_starts


# ============================================================
# PHASE 3: B-ROLL HARD CUTS (Ryan Humiston style)
# ============================================================

def phase3_broll(section_starts=None):
    """
    Hard-cut B-roll insertions. Voice audio continues, video switches to B-roll.

    Uses trim/concat approach: splits base video at B-roll timestamps,
    replaces video segments with B-roll, concatenates back together.
    Audio track stays continuous from the base video throughout.

    This is the Ryan Humiston style: hard cuts, no soft crossfades.
    """
    print("\n" + "=" * 70)
    print("PHASE 3: B-ROLL HARD CUTS (Humiston style)")
    print("=" * 70)

    input_path = WORK_DIR / "02_concat.mp4"
    output_path = WORK_DIR / "03_broll.mp4"

    if not input_path.exists():
        print("  ERROR: Concatenated video not found. Run phase 2 first.")
        return False

    total_dur = get_duration(input_path)

    # If no section starts provided, estimate from available files
    if not section_starts:
        section_starts = _estimate_section_starts()

    # Calculate section durations
    section_durations = {}
    names = [s["name"] for s in SECTIONS]
    for i, name in enumerate(names):
        start = section_starts.get(name, 0)
        if i + 1 < len(names):
            end = section_starts.get(names[i + 1], start + 60)
        else:
            end = total_dur
        section_durations[name] = end - start

    # Calculate absolute B-roll timestamps and sort by start time
    insertions = []
    print(f"\n  Base video: {format_time(total_dur)}")
    print(f"  B-roll hard cuts:")

    for i, broll in enumerate(BROLL_INSERTIONS):
        broll_path = BROLL_DIR / broll["file"]
        if not broll_path.exists():
            print(f"    SKIP: {broll['file']} (not found)")
            continue

        section = broll["section"]
        sec_start = section_starts.get(section, 0)
        sec_dur = section_durations.get(section, 60)

        abs_start = sec_start + (sec_dur * broll["offset_pct"])
        broll_clip_dur = get_duration(broll_path)
        use_dur = min(broll["dur"], broll_clip_dur)
        abs_end = abs_start + use_dur

        if abs_end > total_dur:
            abs_end = total_dur
            use_dur = abs_end - abs_start
        if abs_start >= total_dur:
            continue

        insertions.append({
            "idx": i,
            "path": str(broll_path),
            "start": abs_start,
            "end": abs_end,
            "dur": use_dur,
            "file": broll["file"],
        })
        print(f"    #{i+1} {broll['file']}: {format_time(abs_start)} → {format_time(abs_end)} ({use_dur:.1f}s)")

    insertions.sort(key=lambda x: x["start"])

    if not insertions:
        print("  No B-roll clips found, copying base video")
        subprocess.run(["cp", str(input_path), str(output_path)])
        return True

    # Build trim/concat filter: split base video at each B-roll point,
    # replace video with B-roll, keep audio continuous.
    #
    # Video: [base_seg0] [broll0] [base_seg1] [broll1] ... [base_segN]
    # Audio: continuous from base (no cuts)
    #
    input_args = ["-i", str(input_path)]
    for ins in insertions:
        input_args += ["-i", ins["path"]]

    filter_parts = []
    concat_inputs = []
    prev_end = 0.0

    for seg_idx, ins in enumerate(insertions):
        broll_input = seg_idx + 1  # 1-indexed (0 is base video)

        # Base video segment BEFORE this B-roll
        if ins["start"] > prev_end + 0.1:
            seg_label = f"[seg{seg_idx}]"
            filter_parts.append(
                f"[0:v]trim={prev_end:.3f}:{ins['start']:.3f},"
                f"setpts=PTS-STARTPTS{seg_label}"
            )
            concat_inputs.append(seg_label)

        # B-roll clip (scaled to 1080p, trimmed to exact duration)
        broll_label = f"[br{seg_idx}]"
        filter_parts.append(
            f"[{broll_input}:v]scale={WIDTH}:{HEIGHT}:"
            f"force_original_aspect_ratio=decrease,"
            f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2,"
            f"trim=0:{ins['dur']:.3f},"
            f"setpts=PTS-STARTPTS{broll_label}"
        )
        concat_inputs.append(broll_label)

        prev_end = ins["end"]

    # Final base segment after last B-roll
    if prev_end < total_dur - 0.1:
        final_label = "[segfinal]"
        filter_parts.append(
            f"[0:v]trim={prev_end:.3f}:{total_dur:.3f},"
            f"setpts=PTS-STARTPTS{final_label}"
        )
        concat_inputs.append(final_label)

    # Concat all video segments
    n_segments = len(concat_inputs)
    concat_str = "".join(concat_inputs)
    filter_parts.append(
        f"{concat_str}concat=n={n_segments}:v=1:a=0[outv]"
    )

    filter_complex = ";\n".join(filter_parts)

    # Output: concatenated video + original audio (continuous, no cuts)
    args = input_args + [
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "0:a",
        "-c:v", "libx264", "-crf", str(CRF), "-preset", PRESET,
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        "-shortest",
        str(output_path)
    ]

    print(f"\n  Rendering {n_segments} segments ({len(insertions)} B-roll hard cuts)...")
    success = run_ffmpeg(args, desc="B-roll hard cuts", timeout=1200)

    if success:
        dur = get_duration(output_path)
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"\n  B-roll video: {format_time(dur)} ({size_mb:.0f}MB)")
        print(f"  Output: {output_path}")
    else:
        print(f"\n  B-roll rendering failed. Check FFmpeg output above.")

    return success


# ============================================================
# PHASE 4: GRAPHIC OVERLAYS
# ============================================================

def phase4_graphics(section_starts=None):
    """Apply graphic overlays (lower thirds, headers, stat cards)."""
    print("\n" + "=" * 70)
    print("PHASE 4: GRAPHIC OVERLAYS")
    print("=" * 70)

    # Use B-roll version if available, otherwise concat
    input_path = WORK_DIR / "03_broll.mp4"
    if not input_path.exists():
        input_path = WORK_DIR / "02_concat.mp4"
    if not input_path.exists():
        print("  ERROR: No base video found. Run earlier phases first.")
        return False

    output_path = WORK_DIR / "04_graphics.mp4"
    total_dur = get_duration(input_path)

    # Get section timing for overlay positioning
    if not section_starts:
        section_starts = _estimate_section_starts()

    # Define overlay schedule based on section timing
    # Section 2 starts at ~section_starts["Section2"], duration ~section_durations["Section2"]
    s2_start = section_starts.get("Section2", 95)
    s3_start = section_starts.get("Section3", 245)
    s4_start = section_starts.get("Section4", 355)
    s5_start = section_starts.get("Section5", 495)

    # Estimate Section 2 sub-timing for peptide lower thirds
    s2_dur = s3_start - s2_start

    overlays = [
        # === CATEGORY HEADERS (full-screen flash, 2s each) ===
        # Cat 1: GH Secretagogues (~15% into Section 2)
        {"file": "header_category_1.png", "start": s2_start + s2_dur * 0.10, "dur": 2.0},
        # Cat 2: Healing & Recovery (~40% into Section 2)
        {"file": "header_category_2.png", "start": s2_start + s2_dur * 0.40, "dur": 2.0},
        # Cat 3: Performance (~65% into Section 2)
        {"file": "header_category_3.png", "start": s2_start + s2_dur * 0.65, "dur": 2.0},
        # Cat 4: Cognitive (~80% into Section 2)
        {"file": "header_category_4.png", "start": s2_start + s2_dur * 0.80, "dur": 2.0},

        # === PEPTIDE LOWER THIRDS (4s each, lower-left) ===
        # GH Secretagogues group
        {"file": "lower_third_sermorelin.png",  "start": s2_start + s2_dur * 0.13, "dur": 4.0, "pos": "lower_left"},
        {"file": "lower_third_cjc_1295.png",    "start": s2_start + s2_dur * 0.18, "dur": 4.0, "pos": "lower_left"},
        {"file": "lower_third_ipamorelin.png",  "start": s2_start + s2_dur * 0.23, "dur": 4.0, "pos": "lower_left"},
        {"file": "lower_third_tesamorelin.png", "start": s2_start + s2_dur * 0.28, "dur": 4.0, "pos": "lower_left"},
        # Healing group
        {"file": "lower_third_bpc_157.png",     "start": s2_start + s2_dur * 0.43, "dur": 4.0, "pos": "lower_left"},
        {"file": "lower_third_tb_500.png",      "start": s2_start + s2_dur * 0.50, "dur": 4.0, "pos": "lower_left"},
        # Performance group
        {"file": "lower_third_ghrp_6.png",      "start": s2_start + s2_dur * 0.68, "dur": 4.0, "pos": "lower_left"},
        {"file": "lower_third_mk_677.png",      "start": s2_start + s2_dur * 0.73, "dur": 4.0, "pos": "lower_left"},
        {"file": "lower_third_aod_9604.png",    "start": s2_start + s2_dur * 0.78, "dur": 4.0, "pos": "lower_left"},
        # Cognitive group
        {"file": "lower_third_epithalon.png",   "start": s2_start + s2_dur * 0.83, "dur": 4.0, "pos": "lower_left"},
        {"file": "lower_third_semax.png",       "start": s2_start + s2_dur * 0.88, "dur": 4.0, "pos": "lower_left"},
        {"file": "lower_third_selank.png",      "start": s2_start + s2_dur * 0.93, "dur": 4.0, "pos": "lower_left"},

        # === MAIN GRAPHICS (center, longer display) ===
        # Spectrum graphic (Section 3, after discussing proven/promising/hype)
        {"file": "graphic_spectrum.png", "start": s3_start + (s4_start - s3_start) * 0.70, "dur": 8.0},
        # Categories overview (early Section 2)
        {"file": "graphic_categories.png", "start": s2_start + s2_dur * 0.05, "dur": 6.0},
        # Checklist graphic (Section 4, after all 5 key learnings)
        {"file": "graphic_checklist.png", "start": s4_start + (s5_start - s4_start) * 0.75, "dur": 8.0},
        # Framework graphic (Section 5)
        {"file": "graphic_framework.png", "start": s5_start + 20, "dur": 10.0},

        # === STAT CARDS (Section 1/3, brief displays) ===
        {"file": "stat_30_years.png",     "start": s2_start - 15, "dur": 4.0},
        {"file": "stat_fda_years.png",    "start": s3_start + 20, "dur": 4.0},
        {"file": "stat_not_approved.png", "start": s3_start + 35, "dur": 4.0},

        # === DISCLAIMER (end of Section 2) ===
        {"file": "disclaimer.png", "start": s3_start - 8, "dur": 6.0, "pos": "bottom"},
    ]

    # Build FFmpeg filter for all overlays
    input_args = ["-i", str(input_path)]
    filter_parts = []
    overlay_chain = "[0:v]"
    valid_count = 0

    for i, ov in enumerate(overlays):
        png_path = GRAPHICS_DIR / ov["file"]
        if not png_path.exists():
            continue

        start = ov["start"]
        end = start + ov["dur"]
        if start >= total_dur:
            continue

        input_args += ["-i", str(png_path)]
        valid_count += 1
        input_idx = valid_count  # 1-indexed

        pos = ov.get("pos", "center")

        # Scale and position based on overlay type
        if pos == "lower_left":
            # Lower-left: scale to ~30% width, position at bottom-left with padding
            filter_parts.append(
                f"[{input_idx}:v]scale=iw*0.3:-1,"
                f"fade=t=in:st=0:d=0.3:alpha=1,"
                f"fade=t=out:st={ov['dur']-0.3:.2f}:d=0.3:alpha=1"
                f"[ov{i}]"
            )
            x = f"{int(WIDTH * 0.05)}"
            y = f"{int(HEIGHT * 0.82)}"
        elif pos == "bottom":
            # Bottom: full width, at very bottom
            filter_parts.append(
                f"[{input_idx}:v]scale={WIDTH}:-1,"
                f"fade=t=in:st=0:d=0.3:alpha=1,"
                f"fade=t=out:st={ov['dur']-0.3:.2f}:d=0.3:alpha=1"
                f"[ov{i}]"
            )
            x = "0"
            y = f"{int(HEIGHT * 0.88)}"
        else:
            # Center: scale to fit (max 80% of frame)
            filter_parts.append(
                f"[{input_idx}:v]scale='min({int(WIDTH*0.8)},iw)':'min({int(HEIGHT*0.8)},ih)'"
                f":force_original_aspect_ratio=decrease,"
                f"fade=t=in:st=0:d=0.5:alpha=1,"
                f"fade=t=out:st={ov['dur']-0.5:.2f}:d=0.5:alpha=1"
                f"[ov{i}]"
            )
            x = f"(main_w-overlay_w)/2"
            y = f"(main_h-overlay_h)/2"

        out_label = f"[gv{i}]"
        filter_parts.append(
            f"{overlay_chain}[ov{i}]overlay={x}:{y}:"
            f"enable='between(t,{start:.2f},{end:.2f})'"
            f"{out_label}"
        )
        overlay_chain = out_label

    if not filter_parts:
        print("  No graphics found, copying input")
        subprocess.run(["cp", str(input_path), str(output_path)])
        return True

    print(f"  Applying {valid_count} graphic overlays...")

    filter_complex = ";\n".join(filter_parts)

    args = input_args + [
        "-filter_complex", filter_complex,
        "-map", overlay_chain,
        "-map", "0:a",
        "-c:v", "libx264", "-crf", str(CRF), "-preset", PRESET,
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(output_path)
    ]

    success = run_ffmpeg(args, desc="Graphics overlay", timeout=1200)

    if success:
        dur = get_duration(output_path)
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"\n  Graphics video: {format_time(dur)} ({size_mb:.0f}MB)")
        print(f"  Output: {output_path}")

    return success


# ============================================================
# PHASE 5: AUDIO NORMALIZATION + FINAL EXPORT
# ============================================================

def phase5_final():
    """Normalize audio and produce final YouTube-ready export."""
    print("\n" + "=" * 70)
    print("PHASE 5: AUDIO NORMALIZATION + FINAL EXPORT")
    print("=" * 70)

    # Find best available input (latest phase)
    for candidate in ["04_graphics.mp4", "03_broll.mp4", "02_concat.mp4"]:
        input_path = WORK_DIR / candidate
        if input_path.exists():
            break
    else:
        print("  ERROR: No video found. Run earlier phases first.")
        return None

    output_path = OUTPUT_DIR / "peptide-video-FINAL.mp4"
    print(f"\n  Input: {input_path.name}")
    print(f"  Output: {output_path}")

    # Two-pass loudnorm for best quality
    # Pass 1: Measure
    print("\n  Pass 1: Measuring audio levels...")
    measure_cmd = [
        "ffmpeg", "-hide_banner",
        "-i", str(input_path),
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
        "-f", "null", "-"
    ]
    result = subprocess.run(measure_cmd, capture_output=True, text=True, timeout=600)

    # Try to extract loudnorm stats
    loudnorm_params = "loudnorm=I=-16:TP=-1.5:LRA=11"
    try:
        # Find the JSON block in stderr
        json_match = re.search(r'\{[^}]*"input_i"[^}]*\}', result.stderr)
        if json_match:
            stats = json.loads(json_match.group())
            loudnorm_params = (
                f"loudnorm=I=-16:TP=-1.5:LRA=11:"
                f"measured_I={stats['input_i']}:"
                f"measured_TP={stats['input_tp']}:"
                f"measured_LRA={stats['input_lra']}:"
                f"measured_thresh={stats['input_thresh']}:"
                f"offset={stats['target_offset']}:"
                f"linear=true"
            )
            print(f"    Input loudness: {stats['input_i']} LUFS")
    except Exception as e:
        print(f"    Could not parse loudnorm stats, using single-pass: {e}")

    # Pass 2: Apply normalization + also apply highpass/lowpass for clarity
    print("  Pass 2: Normalizing and exporting...")
    args = [
        "-i", str(input_path),
        "-af", f"{loudnorm_params},highpass=f=80,lowpass=f=12000",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(output_path)
    ]

    success = run_ffmpeg(args, desc="Final export", timeout=900)

    if success:
        dur = get_duration(output_path)
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"\n  {'=' * 50}")
        print(f"  FINAL VIDEO READY!")
        print(f"  {'=' * 50}")
        print(f"  File: {output_path}")
        print(f"  Duration: {format_time(dur)} ({dur:.1f}s)")
        print(f"  Size: {size_mb:.0f}MB")
        print(f"  Format: H.264, 1920x1080, {FPS}fps")

        # Generate chapter markers
        _print_chapters(dur)

        return str(output_path)

    return None


def _estimate_section_starts():
    """Estimate section start times from available intermediate files."""
    section_starts = {}
    running = 0.0

    for source_dir in [WORK_DIR / "01_jumpcut", WORK_DIR / "00_compressed"]:
        if source_dir.exists():
            for section in SECTIONS:
                name = section["name"]
                path = source_dir / f"{name}.mp4"
                section_starts[name] = running
                if path.exists():
                    running += get_duration(path)
                else:
                    running += 60
            return section_starts

    # Rough estimates from raw durations (pre-compression)
    raw_durations = {"Hook": 35, "Section1": 65, "Section2": 160,
                     "Section3": 120, "Section4": 150, "Section5": 90, "CTA": 10}
    for section in SECTIONS:
        name = section["name"]
        section_starts[name] = running
        running += raw_durations.get(name, 60)

    return section_starts


def _print_chapters(total_dur):
    """Print YouTube chapter markers."""
    section_starts = _estimate_section_starts()

    print(f"\n  YouTube Chapter Markers (paste in description):")
    print(f"  ───────────────────────────────────────────────")
    for section in SECTIONS:
        name = section["name"]
        start = section_starts.get(name, 0)
        if start < total_dur:
            print(f"  {format_time(start)} - {section['chapter']}")


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='Assemble Peptide YouTube Video from Raw Assets',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python assemble_youtube.py --quick       Fast assembly (compress + concat + B-roll)
  python assemble_youtube.py --full        Full pipeline (all 6 phases)
  python assemble_youtube.py --phase 0     Compress raw MOVs only
  python assemble_youtube.py --phase 3     Add B-roll overlay only
  python assemble_youtube.py --resume      Resume from last completed phase
        """
    )
    parser.add_argument('--phase', type=int, choices=[0, 1, 2, 3, 4, 5],
                        help='Run a specific phase')
    parser.add_argument('--quick', action='store_true',
                        help='Quick assembly: compress + concat + B-roll (no jump cuts/graphics)')
    parser.add_argument('--full', action='store_true',
                        help='Full pipeline: all phases')
    parser.add_argument('--resume', action='store_true',
                        help='Resume from last completed phase')
    parser.add_argument('--noise-db', type=float, default=-30,
                        help='Silence threshold for jump cuts (default: -30, Humiston-aggressive)')
    parser.add_argument('--min-silence', type=float, default=0.3,
                        help='Minimum silence duration to remove (default: 0.3s, Humiston-aggressive)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without processing')

    args = parser.parse_args()

    if not args.phase and not args.quick and not args.full and not args.resume:
        parser.print_help()
        print("\n  Available source files:")
        for section in SECTIONS:
            path = RECORDING_DIR / section["file"]
            exists = "OK" if path.exists() else "MISSING"
            size = f"({path.stat().st_size/(1024*1024):.0f}MB)" if path.exists() else ""
            print(f"    [{exists}] {section['name']}: {section['file']} {size}")
        print(f"\n  B-roll clips:")
        for broll in BROLL_INSERTIONS:
            path = BROLL_DIR / broll["file"]
            exists = "OK" if path.exists() else "MISSING"
            print(f"    [{exists}] {broll['file']}")
        print(f"\n  Graphics: {len(list(GRAPHICS_DIR.glob('*.png')))} PNGs in {GRAPHICS_DIR}")
        return 0

    # Ensure output directory exists
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    state = load_state()
    section_starts = None

    print("\n" + "=" * 70)
    print("PEPTIDE YOUTUBE VIDEO ASSEMBLY")
    print(f"  Mode: {'quick' if args.quick else 'full' if args.full else f'phase {args.phase}'}")
    print("=" * 70)

    try:
        # Phase 0: Compress
        if args.full or args.quick or args.phase == 0 or (args.resume and 0 not in state.get("completed_phases", [])):
            if not args.dry_run:
                results = phase0_compress()
                state["completed_phases"] = list(set(state.get("completed_phases", []) + [0]))
                state["compress_results"] = {k: {"duration": v["duration"]} for k, v in results.items()}
                save_state(state)

        # Phase 1: Jump cut (full only)
        if args.full or args.phase == 1 or (args.resume and 1 not in state.get("completed_phases", [])):
            if not args.dry_run:
                results = phase1_jumpcut(args.noise_db, args.min_silence)
                state["completed_phases"] = list(set(state.get("completed_phases", []) + [1]))
                state["jumpcut_results"] = {k: v for k, v in results.items()}
                save_state(state)

        # Phase 2: Concatenate
        if args.full or args.quick or args.phase == 2 or (args.resume and 2 not in state.get("completed_phases", [])):
            if not args.dry_run:
                use_jumpcut = args.full or args.phase == 2 or (1 in state.get("completed_phases", []))
                section_starts = phase2_concat(use_jumpcut=use_jumpcut)
                state["completed_phases"] = list(set(state.get("completed_phases", []) + [2]))
                state["section_starts"] = section_starts
                save_state(state)

        # Phase 3: B-roll
        if args.full or args.quick or args.phase == 3 or (args.resume and 3 not in state.get("completed_phases", [])):
            if not section_starts:
                section_starts = state.get("section_starts") or _estimate_section_starts()
            if not args.dry_run:
                phase3_broll(section_starts)
                state["completed_phases"] = list(set(state.get("completed_phases", []) + [3]))
                save_state(state)

        # Phase 4: Graphics (full only)
        if args.full or args.phase == 4 or (args.resume and 4 not in state.get("completed_phases", [])):
            if not section_starts:
                section_starts = state.get("section_starts") or _estimate_section_starts()
            if not args.dry_run:
                phase4_graphics(section_starts)
                state["completed_phases"] = list(set(state.get("completed_phases", []) + [4]))
                save_state(state)

        # Phase 5: Final export
        if args.full or args.quick or args.phase == 5 or (args.resume and 5 not in state.get("completed_phases", [])):
            if not args.dry_run:
                result = phase5_final()
                if result:
                    state["completed_phases"] = list(set(state.get("completed_phases", []) + [5]))
                    state["final_output"] = result
                    save_state(state)

    except KeyboardInterrupt:
        print("\n\n  Interrupted! Progress saved. Run with --resume to continue.")
        save_state(state)
        return 1

    elapsed = time.time() - start_time
    print(f"\n  Total time: {elapsed/60:.1f} minutes")
    print(f"  State saved to: {STATE_FILE}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
