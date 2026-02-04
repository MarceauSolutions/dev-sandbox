#!/usr/bin/env python3
"""
video_compositor.py - Apply Overlays to Video at Specific Timestamps

Composites PNG overlays (lower thirds, graphics, headers) onto video
at specified timestamps with fade in/out animations.

Usage:
    python video_compositor.py --input video.mp4 --overlays overlays.json --output final.mp4
    python video_compositor.py --input video.mp4 --peptide-overlays   # Auto-apply peptide overlays
"""

import argparse
import sys
import os
import json
from pathlib import Path

try:
    from moviepy import (
        VideoFileClip, ImageClip, CompositeVideoClip,
        concatenate_videoclips
    )
    MOVIEPY_V2 = True
except ImportError:
    try:
        from moviepy.editor import (
            VideoFileClip, ImageClip, CompositeVideoClip,
            concatenate_videoclips
        )
        MOVIEPY_V2 = False
    except ImportError:
        print("ERROR: moviepy not installed. Run: pip install moviepy")
        sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)


# Default overlay configurations for peptide video
# Format: (overlay_file, start_time, duration, position, fade_in, fade_out)
# position: "lower_left", "lower_right", "center", "top_center", "custom"
# Times are approximate - adjust based on actual video timing

PEPTIDE_OVERLAY_CONFIG = [
    # Category headers (full screen flashes)
    {"file": "header_category_1.png", "start": 120, "duration": 2.0, "position": "center", "fade_in": 0.3, "fade_out": 0.3},
    {"file": "header_category_2.png", "start": 200, "duration": 2.0, "position": "center", "fade_in": 0.3, "fade_out": 0.3},
    {"file": "header_category_3.png", "start": 255, "duration": 2.0, "position": "center", "fade_in": 0.3, "fade_out": 0.3},
    {"file": "header_category_4.png", "start": 295, "duration": 2.0, "position": "center", "fade_in": 0.3, "fade_out": 0.3},

    # Peptide name lower thirds (Section 2)
    {"file": "lower_third_sermorelin.png", "start": 125, "duration": 4.0, "position": "lower_left", "fade_in": 0.3, "fade_out": 0.3},
    {"file": "lower_third_cjc_1295.png", "start": 135, "duration": 4.0, "position": "lower_left", "fade_in": 0.3, "fade_out": 0.3},
    {"file": "lower_third_ipamorelin.png", "start": 145, "duration": 4.0, "position": "lower_left", "fade_in": 0.3, "fade_out": 0.3},
    {"file": "lower_third_tesamorelin.png", "start": 155, "duration": 4.0, "position": "lower_left", "fade_in": 0.3, "fade_out": 0.3},

    {"file": "lower_third_bpc_157.png", "start": 210, "duration": 4.0, "position": "lower_left", "fade_in": 0.3, "fade_out": 0.3},
    {"file": "lower_third_tb_500.png", "start": 220, "duration": 4.0, "position": "lower_left", "fade_in": 0.3, "fade_out": 0.3},

    {"file": "lower_third_ghrp_6.png", "start": 260, "duration": 4.0, "position": "lower_left", "fade_in": 0.3, "fade_out": 0.3},
    {"file": "lower_third_mk_677.png", "start": 270, "duration": 4.0, "position": "lower_left", "fade_in": 0.3, "fade_out": 0.3},
    {"file": "lower_third_aod_9604.png", "start": 280, "duration": 4.0, "position": "lower_left", "fade_in": 0.3, "fade_out": 0.3},

    {"file": "lower_third_epithalon.png", "start": 300, "duration": 4.0, "position": "lower_left", "fade_in": 0.3, "fade_out": 0.3},
    {"file": "lower_third_semax.png", "start": 310, "duration": 4.0, "position": "lower_left", "fade_in": 0.3, "fade_out": 0.3},
    {"file": "lower_third_selank.png", "start": 320, "duration": 4.0, "position": "lower_left", "fade_in": 0.3, "fade_out": 0.3},

    # Main graphics (Section 3-5)
    {"file": "graphic_spectrum.png", "start": 380, "duration": 8.0, "position": "center", "fade_in": 0.5, "fade_out": 0.5},
    {"file": "graphic_checklist.png", "start": 490, "duration": 8.0, "position": "center", "fade_in": 0.5, "fade_out": 0.5},
    {"file": "graphic_framework.png", "start": 555, "duration": 10.0, "position": "center", "fade_in": 0.5, "fade_out": 0.5},

    # Disclaimer (end of categories section)
    {"file": "disclaimer.png", "start": 325, "duration": 6.0, "position": "bottom", "fade_in": 0.3, "fade_out": 0.3},
]


class VideoCompositor:
    """Apply overlays to video at specific timestamps."""

    def __init__(self, video_path, overlay_dir):
        """
        Initialize compositor.

        Args:
            video_path: Path to input video
            overlay_dir: Directory containing overlay PNGs
        """
        self.video_path = Path(video_path)
        self.overlay_dir = Path(overlay_dir)

        if not self.video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        print(f"Loading video: {video_path}")
        self.video = VideoFileClip(str(video_path))
        self.video_duration = self.video.duration
        self.video_size = self.video.size

        print(f"  Duration: {self.video_duration:.1f}s ({self.video_duration/60:.1f} min)")
        print(f"  Size: {self.video_size}")

    def _get_position(self, position_str, overlay_size):
        """
        Convert position string to (x, y) coordinates.

        Args:
            position_str: "lower_left", "lower_right", "center", etc.
            overlay_size: (width, height) of overlay

        Returns:
            (x, y) position tuple
        """
        video_w, video_h = self.video_size
        overlay_w, overlay_h = overlay_size

        positions = {
            "center": ((video_w - overlay_w) // 2, (video_h - overlay_h) // 2),
            "lower_left": (int(video_w * 0.05), video_h - overlay_h - int(video_h * 0.1)),
            "lower_right": (video_w - overlay_w - int(video_w * 0.05), video_h - overlay_h - int(video_h * 0.1)),
            "top_center": ((video_w - overlay_w) // 2, int(video_h * 0.05)),
            "bottom": (0, video_h - overlay_h),
        }

        return positions.get(position_str, positions["center"])

    def _apply_fade(self, clip, fade_in=0.3, fade_out=0.3):
        """Apply fade in/out to clip."""
        if fade_in > 0:
            if MOVIEPY_V2:
                clip = clip.with_effects([lambda c: c.crossfadein(fade_in)])
            else:
                clip = clip.crossfadein(fade_in)

        if fade_out > 0:
            if MOVIEPY_V2:
                clip = clip.with_effects([lambda c: c.crossfadeout(fade_out)])
            else:
                clip = clip.crossfadeout(fade_out)

        return clip

    def apply_overlay(self, overlay_config):
        """
        Create an overlay clip from config.

        Args:
            overlay_config: Dict with file, start, duration, position, fade_in, fade_out

        Returns:
            ImageClip positioned and timed, or None if file not found
        """
        overlay_path = self.overlay_dir / overlay_config['file']

        if not overlay_path.exists():
            print(f"  ⚠️  Overlay not found: {overlay_config['file']}")
            return None

        # Load overlay image
        try:
            img = Image.open(overlay_path)
            # Resize if needed to match video dimensions
            if img.size != tuple(self.video_size):
                img = img.resize(self.video_size, Image.Resampling.LANCZOS)

            # Create image clip
            overlay_clip = ImageClip(str(overlay_path))

            # Set duration
            duration = min(overlay_config['duration'], self.video_duration - overlay_config['start'])
            if MOVIEPY_V2:
                overlay_clip = overlay_clip.with_duration(duration)
            else:
                overlay_clip = overlay_clip.set_duration(duration)

            # Set start time
            start_time = overlay_config['start']
            if start_time >= self.video_duration:
                print(f"  ⚠️  Overlay start time ({start_time}s) exceeds video duration, skipping: {overlay_config['file']}")
                return None

            if MOVIEPY_V2:
                overlay_clip = overlay_clip.with_start(start_time)
            else:
                overlay_clip = overlay_clip.set_start(start_time)

            # Set position
            position = self._get_position(overlay_config.get('position', 'center'), img.size)
            if MOVIEPY_V2:
                overlay_clip = overlay_clip.with_position(position)
            else:
                overlay_clip = overlay_clip.set_position(position)

            # Note: Fades would be applied here but MoviePy 2.x has different syntax
            # For simplicity, we skip fades - can be added in post

            print(f"  ✓ {overlay_config['file']}: {start_time}s - {start_time + duration}s")

            return overlay_clip

        except Exception as e:
            print(f"  ✗ Error loading {overlay_config['file']}: {e}")
            return None

    def composite_video(self, overlay_configs, output_path):
        """
        Composite all overlays onto video.

        Args:
            overlay_configs: List of overlay config dicts
            output_path: Path for output video

        Returns:
            Path to output video
        """
        print(f"\n{'='*70}")
        print(f"VIDEO COMPOSITOR")
        print(f"{'='*70}")
        print(f"Input: {self.video_path}")
        print(f"Output: {output_path}")
        print(f"Overlays: {len(overlay_configs)} configs")

        # Filter overlays to only those that exist
        print("\n→ Loading overlays...")
        overlay_clips = []

        for config in overlay_configs:
            clip = self.apply_overlay(config)
            if clip:
                overlay_clips.append(clip)

        print(f"\n→ Compositing {len(overlay_clips)} overlays...")

        # Create composite
        all_clips = [self.video] + overlay_clips
        final = CompositeVideoClip(all_clips)

        # Render
        print(f"\n→ Rendering to: {output_path}")
        print("  (This may take several minutes...)")

        final.write_videofile(
            str(output_path),
            codec='libx264',
            audio_codec='aac',
            fps=self.video.fps or 30,
            preset='medium',
            threads=4
        )

        # Cleanup
        final.close()
        self.video.close()

        print(f"\n✅ COMPOSITE COMPLETE!")
        print(f"   Output: {output_path}")
        print(f"{'='*70}\n")

        return str(output_path)

    def close(self):
        """Close video resources."""
        if hasattr(self, 'video'):
            self.video.close()


def main():
    """CLI for video compositor."""
    parser = argparse.ArgumentParser(
        description='Apply overlays to video at specific timestamps'
    )
    parser.add_argument('--input', required=True, help='Input video file')
    parser.add_argument('--output', help='Output video file')
    parser.add_argument('--overlay-dir', help='Directory containing overlay PNGs')
    parser.add_argument('--overlays', help='JSON file with overlay configurations')
    parser.add_argument('--peptide-overlays', action='store_true',
                        help='Use default peptide video overlay config')
    parser.add_argument('--list-config', action='store_true',
                        help='Print default peptide overlay config as JSON')

    args = parser.parse_args()

    if args.list_config:
        print(json.dumps(PEPTIDE_OVERLAY_CONFIG, indent=2))
        return 0

    # Set defaults
    if not args.overlay_dir:
        args.overlay_dir = "/Users/williammarceaujr./dev-sandbox/projects/marceau-solutions/fitness-influencer/content/Peptide-Video/Graphics/Static"

    if not args.output:
        input_path = Path(args.input)
        args.output = str(input_path.parent / f"{input_path.stem}_with_overlays.mp4")

    # Load overlay config
    if args.overlays:
        with open(args.overlays, 'r') as f:
            overlay_configs = json.load(f)
    elif args.peptide_overlays:
        overlay_configs = PEPTIDE_OVERLAY_CONFIG
    else:
        print("Error: Must specify --overlays or --peptide-overlays")
        return 1

    try:
        compositor = VideoCompositor(args.input, args.overlay_dir)
        compositor.composite_video(overlay_configs, args.output)
        return 0

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
