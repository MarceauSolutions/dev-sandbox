#!/usr/bin/env python3
"""
process_peptide_video.py - Full Peptide Video Processing Pipeline

Processes talking head clips with jump cuts and compiles with B-roll.

Usage:
    python process_peptide_video.py --phase 1  # Jump cut all talking heads
    python process_peptide_video.py --phase 2  # Compile with B-roll
    python process_peptide_video.py --all      # Run full pipeline
"""

import argparse
import os
import sys
from pathlib import Path
import subprocess
import json

# Add execution directory to path for video_jumpcut
sys.path.insert(0, '/Users/williammarceaujr./dev-sandbox/execution')

try:
    # MoviePy 2.x import syntax
    from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips
except ImportError:
    try:
        # MoviePy 1.x fallback
        from moviepy.editor import (
            VideoFileClip, AudioFileClip, concatenate_videoclips,
            CompositeVideoClip, CompositeAudioClip
        )
    except ImportError:
        print("ERROR: moviepy not installed. Run: pip install moviepy")
        sys.exit(1)

# Paths
BASE_DIR = Path("/Users/williammarceaujr./dev-sandbox/projects/marceau-solutions/fitness-influencer/content/Peptide-Video")
OUTPUT_DIR = BASE_DIR / "Output"
JUMPCUT_DIR = OUTPUT_DIR / "JumpCut"
BROLL_DIR = BASE_DIR / "B-Roll"

# Video sections in order
SECTIONS = [
    ("Hook", ["part1.mov", "Part2.mov", "Part3.mov"]),
    ("Section1-What-are-Peptides", ["Part1.mov", "Part2.mov", "Part3.mov", "Part4.mov", "Part5.mov"]),
    ("Section2-Categories-of-peptides", ["Part1.mov", "Part2.mov", "Part3.mov", "Part4.mov", "Part5.mov", "Part6.mov", "Part7.mov", "Part8.mov"]),
    ("Section3-The-science-versus-the-hype", ["Part1.mov", "Part2.mov", "Part3.mov", "Part4.mov"]),
    ("Section4-My-Personal-Take", ["Part1.mov", "Part2.mov", "Part3.mov", "Part4.mov", "Part5.mov"]),
    ("Call-To-Action", ["Part1.mov", "Part2.mov", "Part3.mov"]),
]

# B-roll insertion points (section_name, after_part_index, broll_file)
# Based on PEPTIDE-VIDEO-PRODUCTION.md timestamps
BROLL_INSERTIONS = [
    # B-Roll #1: After Hook, before Section 1 starts (gym training)
    ("Section1-What-are-Peptides", 0, "01-gym-training.mp4"),  # After Section1/Part1
    # B-Roll #2: After "peptide is a chain of amino acids" explanation
    ("Section1-What-are-Peptides", 2, "02-amino-acid.mp4"),    # After Section1/Part3
    # B-Roll #3: Science vs Hype section
    ("Section3-The-science-versus-the-hype", 0, "03-lab-scene.mp4"),  # After Section3/Part1
    # B-Roll #4: After "Quality matters" in personal take
    ("Section4-My-Personal-Take", 1, "04-supplements.mp4"),    # After Section4/Part2
    # B-Roll #5: After "Track everything" advice
    ("Section4-My-Personal-Take", 2, "05-morning-routine.mp4"),  # After Section4/Part3
    # B-Roll #6: Decision framework (before CTA)
    ("Section4-My-Personal-Take", 4, "06-decision-framework.mp4"),  # After Section4/Part5
]


def ensure_dirs():
    """Create output directories."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    JUMPCUT_DIR.mkdir(exist_ok=True)
    print(f"✓ Output directories ready: {OUTPUT_DIR}")


def phase1_jumpcut_clips(silence_thresh=-35, min_silence=0.4):
    """
    Phase 1: Apply jump cuts to all talking head clips.

    Args:
        silence_thresh: dB threshold for silence detection
        min_silence: Minimum silence duration to remove
    """
    print("\n" + "="*70)
    print("PHASE 1: JUMP CUT PROCESSING")
    print("="*70)

    ensure_dirs()

    stats = {
        "processed": 0,
        "failed": 0,
        "total_original": 0,
        "total_edited": 0,
    }

    for section_name, parts in SECTIONS:
        section_dir = BASE_DIR / section_name
        jumpcut_section_dir = JUMPCUT_DIR / section_name
        jumpcut_section_dir.mkdir(exist_ok=True)

        print(f"\n→ Processing {section_name}...")

        for part in parts:
            input_path = section_dir / part
            output_path = jumpcut_section_dir / part.replace('.mov', '_jc.mp4')

            if not input_path.exists():
                print(f"  ⚠️  Not found: {input_path}")
                continue

            # Get original duration
            video = VideoFileClip(str(input_path))
            original_duration = video.duration
            video.close()

            print(f"\n  Processing: {part} ({original_duration:.1f}s)")

            # Run video_jumpcut.py
            cmd = [
                sys.executable,
                '/Users/williammarceaujr./dev-sandbox/execution/video_jumpcut.py',
                '--input', str(input_path),
                '--output', str(output_path),
                '--silence-thresh', str(silence_thresh),
                '--min-silence', str(min_silence),
            ]

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

                if result.returncode == 0 and output_path.exists():
                    # Get new duration
                    edited = VideoFileClip(str(output_path))
                    edited_duration = edited.duration
                    edited.close()

                    saved = original_duration - edited_duration
                    print(f"    ✓ Done: {edited_duration:.1f}s (saved {saved:.1f}s)")

                    stats["processed"] += 1
                    stats["total_original"] += original_duration
                    stats["total_edited"] += edited_duration
                else:
                    print(f"    ✗ Failed: {result.stderr[:200]}")
                    stats["failed"] += 1

            except subprocess.TimeoutExpired:
                print(f"    ✗ Timeout processing {part}")
                stats["failed"] += 1
            except Exception as e:
                print(f"    ✗ Error: {e}")
                stats["failed"] += 1

    # Print summary
    print("\n" + "="*70)
    print("PHASE 1 SUMMARY")
    print("="*70)
    print(f"  Clips processed:     {stats['processed']}")
    print(f"  Clips failed:        {stats['failed']}")
    print(f"  Original duration:   {stats['total_original']:.1f}s ({stats['total_original']/60:.1f} min)")
    print(f"  After jump cuts:     {stats['total_edited']:.1f}s ({stats['total_edited']/60:.1f} min)")
    print(f"  Time saved:          {stats['total_original'] - stats['total_edited']:.1f}s")
    print(f"  Reduction:           {((stats['total_original'] - stats['total_edited']) / stats['total_original'] * 100):.1f}%")

    return stats


def phase2_compile_with_broll():
    """
    Phase 2: Compile all jump-cut clips with B-roll insertions.
    """
    print("\n" + "="*70)
    print("PHASE 2: COMPILE WITH B-ROLL")
    print("="*70)

    all_clips = []
    current_time = 0

    # Build insertion lookup
    insertion_map = {}
    for section, after_part_idx, broll_file in BROLL_INSERTIONS:
        key = (section, after_part_idx)
        insertion_map[key] = broll_file

    print("\n→ Loading clips in sequence order...")

    for section_name, parts in SECTIONS:
        print(f"\n  Section: {section_name}")

        for i, part in enumerate(parts):
            # Load jump-cut version
            jc_path = JUMPCUT_DIR / section_name / part.replace('.mov', '_jc.mp4')

            # Fall back to original if jump-cut doesn't exist
            if not jc_path.exists():
                jc_path = BASE_DIR / section_name / part

            if not jc_path.exists():
                print(f"    ⚠️  Missing: {part}")
                continue

            clip = VideoFileClip(str(jc_path))
            # Ensure consistent fps for concatenation
            if not hasattr(clip, 'fps') or clip.fps is None:
                clip = clip.with_fps(30)
            all_clips.append(("talking_head", clip, part))
            print(f"    + {part}: {clip.duration:.1f}s (at {current_time:.1f}s)")
            current_time += clip.duration

            # Check for B-roll insertion after this part
            key = (section_name, i)
            if key in insertion_map:
                broll_file = insertion_map[key]
                broll_path = BROLL_DIR / broll_file

                if broll_path.exists():
                    broll_clip = VideoFileClip(str(broll_path))
                    all_clips.append(("broll", broll_clip, broll_file))
                    print(f"    + [B-ROLL] {broll_file}: {broll_clip.duration:.1f}s (at {current_time:.1f}s)")
                    current_time += broll_clip.duration
                else:
                    print(f"    ⚠️  B-roll not found: {broll_file}")

    # Calculate totals
    total_talking = sum(c[1].duration for c in all_clips if c[0] == "talking_head")
    total_broll = sum(c[1].duration for c in all_clips if c[0] == "broll")

    print(f"\n→ Compilation summary:")
    print(f"    Talking head:  {total_talking:.1f}s ({total_talking/60:.1f} min)")
    print(f"    B-roll:        {total_broll:.1f}s ({total_broll/60:.1f} min)")
    print(f"    Total:         {current_time:.1f}s ({current_time/60:.1f} min)")

    # Concatenate all clips
    print(f"\n→ Concatenating {len(all_clips)} clips...")

    video_clips = [c[1] for c in all_clips]
    final_video = concatenate_videoclips(video_clips, method="compose")

    # Export
    output_path = OUTPUT_DIR / "peptide_video_compiled.mp4"
    print(f"\n→ Rendering final video to: {output_path}")
    print("  (This may take several minutes...)")

    final_video.write_videofile(
        str(output_path),
        codec='libx264',
        audio_codec='aac',
        fps=30,
        preset='medium',
        threads=4
    )

    # Cleanup
    final_video.close()
    for _, clip, _ in all_clips:
        clip.close()

    print(f"\n✅ COMPILATION COMPLETE!")
    print(f"   Output: {output_path}")
    print(f"   Duration: {current_time/60:.1f} minutes")

    return str(output_path)


def phase3_audio_enhance(video_path):
    """
    Phase 3: Enhance audio (normalize levels, reduce noise).
    Uses FFmpeg for audio processing.
    """
    print("\n" + "="*70)
    print("PHASE 3: AUDIO ENHANCEMENT")
    print("="*70)

    input_path = Path(video_path)
    output_path = input_path.parent / f"{input_path.stem}_enhanced.mp4"

    print(f"\n→ Enhancing audio...")
    print(f"  Input:  {input_path}")
    print(f"  Output: {output_path}")

    # FFmpeg command for audio normalization and light noise reduction
    cmd = [
        'ffmpeg', '-y',
        '-i', str(input_path),
        '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11,highpass=f=80,lowpass=f=12000',
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '192k',
        str(output_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode == 0:
            print(f"\n✅ Audio enhanced: {output_path}")
            return str(output_path)
        else:
            print(f"\n⚠️  Audio enhancement failed, using original")
            return video_path

    except Exception as e:
        print(f"\n⚠️  Audio enhancement error: {e}")
        return video_path


def phase4_generate_overlays():
    """
    Phase 4: Generate all text overlays and graphics.
    """
    print("\n" + "="*70)
    print("PHASE 4: GENERATE OVERLAYS & GRAPHICS")
    print("="*70)

    graphics_dir = BASE_DIR / "Graphics" / "Static"
    graphics_dir.mkdir(parents=True, exist_ok=True)

    # Import overlay generators
    from text_overlay_generator import TextOverlayGenerator
    from peptide_graphics_generator import PeptideGraphicsGenerator

    # Generate text overlays
    print("\n→ Generating text overlays...")
    text_gen = TextOverlayGenerator(str(graphics_dir))
    text_gen.generate_all()

    # Generate main graphics
    print("\n→ Generating main graphics...")
    graphics_gen = PeptideGraphicsGenerator(str(graphics_dir))
    graphics_gen.generate_all()

    print(f"\n✅ All overlays generated in: {graphics_dir}")
    return str(graphics_dir)


def phase5_apply_overlays(video_path=None):
    """
    Phase 5: Apply overlays to compiled video.
    """
    print("\n" + "="*70)
    print("PHASE 5: APPLY OVERLAYS TO VIDEO")
    print("="*70)

    if not video_path:
        # Try to find the enhanced video first, then compiled
        enhanced_path = OUTPUT_DIR / "peptide_video_compiled_enhanced.mp4"
        compiled_path = OUTPUT_DIR / "peptide_video_compiled.mp4"

        if enhanced_path.exists():
            video_path = str(enhanced_path)
        elif compiled_path.exists():
            video_path = str(compiled_path)
        else:
            print("✗ No compiled video found. Run --phase 2 first.")
            return None

    from video_compositor import VideoCompositor, PEPTIDE_OVERLAY_CONFIG

    graphics_dir = BASE_DIR / "Graphics" / "Static"
    output_path = OUTPUT_DIR / "peptide_video_final.mp4"

    try:
        compositor = VideoCompositor(video_path, str(graphics_dir))
        result = compositor.composite_video(PEPTIDE_OVERLAY_CONFIG, str(output_path))
        return result
    except Exception as e:
        print(f"✗ Overlay application failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser(description='Peptide Video Processing Pipeline')
    parser.add_argument('--phase', type=int, choices=[1, 2, 3, 4, 5], help='Run specific phase')
    parser.add_argument('--all', action='store_true', help='Run full pipeline (phases 1-3)')
    parser.add_argument('--full', action='store_true', help='Run complete pipeline (phases 1-5)')
    parser.add_argument('--silence-thresh', type=float, default=-35, help='Silence threshold in dB')
    parser.add_argument('--min-silence', type=float, default=0.4, help='Min silence duration (seconds)')

    args = parser.parse_args()

    if not args.phase and not args.all and not args.full:
        parser.print_help()
        print("\nPipeline Phases:")
        print("  Phase 1: Jump cut processing (remove silence)")
        print("  Phase 2: Compile with B-roll")
        print("  Phase 3: Audio enhancement")
        print("  Phase 4: Generate overlays & graphics")
        print("  Phase 5: Apply overlays to video")
        print("\nExamples:")
        print("  python process_peptide_video.py --phase 1   # Jump cuts only")
        print("  python process_peptide_video.py --phase 2   # Compile with B-roll")
        print("  python process_peptide_video.py --all       # Phases 1-3")
        print("  python process_peptide_video.py --full      # Phases 1-5 (complete)")
        print("  python process_peptide_video.py --phase 4   # Generate overlays")
        print("  python process_peptide_video.py --phase 5   # Apply overlays")
        return 1

    try:
        compiled_path = None

        if args.full or args.all or args.phase == 1:
            phase1_jumpcut_clips(args.silence_thresh, args.min_silence)

        if args.full or args.all or args.phase == 2:
            compiled_path = phase2_compile_with_broll()

        if args.full or args.all or args.phase == 3:
            if not compiled_path:
                compiled_path = OUTPUT_DIR / "peptide_video_compiled.mp4"
            if Path(compiled_path).exists():
                enhanced_path = phase3_audio_enhance(str(compiled_path))
            else:
                print(f"✗ Compiled video not found. Run --phase 2 first.")
                return 1

        if args.full or args.phase == 4:
            phase4_generate_overlays()

        if args.full or args.phase == 5:
            final_path = phase5_apply_overlays()
            if final_path:
                print(f"\n🎬 FINAL VIDEO: {final_path}")

        print("\n" + "="*70)
        print("PROCESSING COMPLETE")
        print("="*70)
        print(f"\nOutput files in: {OUTPUT_DIR}")

        return 0

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
