#!/usr/bin/env python3
"""
video_polish.py - Final video polish tools

WHAT: Color grading, background music mixing, thumbnail generation, YouTube export
WHY: Final production polish for YouTube-ready video
INPUT: Final video with overlays, music track (optional)
OUTPUT: Polished video ready for YouTube upload

CAPABILITIES:
  - Color grading (match B-roll to talking head)
  - Background music mixing (-15dB to -20dB)
  - Thumbnail generation (1920x1080)
  - YouTube export optimization (H.264, optimal bitrate)
"""

import argparse
import subprocess
import sys
from pathlib import Path

try:
    from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip
    MOVIEPY_V2 = True
except ImportError:
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
        MOVIEPY_V2 = False
    except ImportError:
        print("ERROR: moviepy not installed. Run: pip install moviepy")
        sys.exit(1)

from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Base directory for peptide video
BASE_DIR = Path(__file__).parent.parent / "content" / "Peptide-Video"
OUTPUT_DIR = BASE_DIR / "Output"


class VideoPolisher:
    """Final polish tools for production-ready video."""

    def __init__(self, video_path: str):
        """
        Initialize polisher.

        Args:
            video_path: Path to input video
        """
        self.video_path = Path(video_path)
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

    def add_background_music(
        self,
        music_path: str,
        output_path: str,
        music_volume: float = 0.1,  # -20dB roughly
        fade_in: float = 2.0,
        fade_out: float = 3.0
    ) -> str:
        """
        Add background music to video.

        Args:
            music_path: Path to music file (MP3, WAV, etc.)
            output_path: Output video path
            music_volume: Music volume (0.0-1.0), 0.1 = -20dB, 0.15 = -16dB
            fade_in: Fade in duration (seconds)
            fade_out: Fade out duration (seconds)

        Returns:
            Path to output video
        """
        print(f"\n{'='*70}")
        print("ADDING BACKGROUND MUSIC")
        print(f"{'='*70}")
        print(f"Input: {self.video_path}")
        print(f"Music: {music_path}")
        print(f"Volume: {music_volume} ({20 * __import__('math').log10(music_volume):.1f} dB)")

        music_file = Path(music_path)
        if not music_file.exists():
            print(f"Music file not found: {music_path}")
            return None

        # Load video
        print("\n-> Loading video...")
        video = VideoFileClip(str(self.video_path))
        video_duration = video.duration

        # Load music
        print("-> Loading music...")
        music = AudioFileClip(str(music_path))

        # Loop music if shorter than video
        if music.duration < video_duration:
            print(f"-> Looping music ({music.duration:.1f}s) to match video ({video_duration:.1f}s)...")
            # Create looped audio
            loops_needed = int(video_duration / music.duration) + 1
            music_clips = [music] * loops_needed
            from moviepy import concatenate_audioclips
            music = concatenate_audioclips(music_clips)

        # Trim music to video duration
        if hasattr(music, 'subclipped'):
            music = music.subclipped(0, video_duration)
        else:
            music = music.subclip(0, video_duration)

        # Apply volume and fades
        print(f"-> Applying volume ({music_volume}) and fades...")
        music = music.with_volume_scaled(music_volume)

        # Apply fades using audio_fadein/fadeout
        if fade_in > 0:
            music = music.audio_fadein(fade_in)
        if fade_out > 0:
            music = music.audio_fadeout(fade_out)

        # Mix with original audio
        print("-> Mixing audio tracks...")
        original_audio = video.audio
        if original_audio:
            final_audio = CompositeAudioClip([original_audio, music])
        else:
            final_audio = music

        # Create final video
        final_video = video.with_audio(final_audio)

        # Export
        print(f"\n-> Exporting to: {output_path}")
        print("  (This may take several minutes...)")

        final_video.write_videofile(
            str(output_path),
            codec='libx264',
            audio_codec='aac',
            fps=video.fps or 30,
            preset='medium',
            threads=4
        )

        # Cleanup
        final_video.close()
        video.close()
        music.close()

        print(f"\n-> Background music added: {output_path}")
        return output_path

    def color_grade_broll(self, output_path: str) -> str:
        """
        Apply subtle color grading to match B-roll with talking head.
        Uses FFmpeg for precise color correction.

        Args:
            output_path: Output video path

        Returns:
            Path to output video
        """
        print(f"\n{'='*70}")
        print("COLOR GRADING (B-ROLL MATCHING)")
        print(f"{'='*70}")

        # FFmpeg color grading filter for B-roll matching
        # Slightly warmer, subtle contrast boost
        color_filter = (
            "eq=contrast=1.05:brightness=0.02:saturation=1.1,"
            "colorbalance=rs=0.05:gs=0.02:bs=-0.02"
        )

        cmd = [
            'ffmpeg', '-y',
            '-i', str(self.video_path),
            '-vf', color_filter,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '18',
            '-c:a', 'copy',
            str(output_path)
        ]

        print(f"-> Applying color grade...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Color grading failed: {result.stderr}")
            return None

        print(f"-> Color graded: {output_path}")
        return output_path

    def generate_thumbnail(
        self,
        output_path: str,
        frame_time: float = None,
        title_text: str = "PEPTIDES",
        subtitle_text: str = "The Truth About What Works",
        style: str = "bold"
    ) -> str:
        """
        Generate YouTube thumbnail from video frame.

        Args:
            output_path: Output image path (PNG/JPG)
            frame_time: Time in video to extract frame (None = 30% in)
            title_text: Main title text
            subtitle_text: Subtitle text
            style: "bold", "minimal", or "split"

        Returns:
            Path to thumbnail
        """
        print(f"\n{'='*70}")
        print("GENERATING THUMBNAIL")
        print(f"{'='*70}")

        # Load video and extract frame
        video = VideoFileClip(str(self.video_path))

        if frame_time is None:
            frame_time = video.duration * 0.3

        print(f"-> Extracting frame at {frame_time:.1f}s...")
        frame = video.get_frame(frame_time)
        video.close()

        # Convert to PIL Image
        img = Image.fromarray(frame)

        # Resize to YouTube thumbnail size (1920x1080 or 1280x720)
        target_size = (1920, 1080)
        img = img.resize(target_size, Image.Resampling.LANCZOS)

        # Apply style
        if style == "bold":
            img = self._apply_bold_style(img, title_text, subtitle_text)
        elif style == "minimal":
            img = self._apply_minimal_style(img, title_text)
        elif style == "split":
            img = self._apply_split_style(img, title_text, subtitle_text)

        # Save
        img.save(output_path, quality=95)
        print(f"-> Thumbnail saved: {output_path}")

        return output_path

    def _apply_bold_style(self, img: Image.Image, title: str, subtitle: str) -> Image.Image:
        """Apply bold thumbnail style with large text overlay."""
        draw = ImageDraw.Draw(img)
        width, height = img.size

        # Add dark gradient overlay on left side
        gradient = Image.new('RGBA', img.size, (0, 0, 0, 0))
        gradient_draw = ImageDraw.Draw(gradient)
        for x in range(width // 2):
            alpha = int(180 * (1 - x / (width // 2)))
            gradient_draw.line([(x, 0), (x, height)], fill=(15, 23, 42, alpha))

        img = img.convert('RGBA')
        img = Image.alpha_composite(img, gradient)
        img = img.convert('RGB')
        draw = ImageDraw.Draw(img)

        # Try to load Inter font, fallback to default
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 140)
            subtitle_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()

        # Draw title with shadow
        title_x, title_y = 80, height // 2 - 100

        # Shadow
        draw.text((title_x + 4, title_y + 4), title, font=title_font, fill=(0, 0, 0))
        # Main text
        draw.text((title_x, title_y), title, font=title_font, fill=(255, 255, 255))

        # Subtitle
        draw.text((title_x, title_y + 160), subtitle, font=subtitle_font, fill=(34, 197, 94))

        return img

    def _apply_minimal_style(self, img: Image.Image, title: str) -> Image.Image:
        """Apply minimal thumbnail style with centered text."""
        # Add slight blur and darken
        img = img.filter(ImageFilter.GaussianBlur(radius=2))

        # Darken
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(0.7)

        draw = ImageDraw.Draw(img)
        width, height = img.size

        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 160)
        except:
            title_font = ImageFont.load_default()

        # Center text
        bbox = draw.textbbox((0, 0), title, font=title_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (width - text_width) // 2
        y = (height - text_height) // 2

        # Draw with shadow
        draw.text((x + 4, y + 4), title, font=title_font, fill=(0, 0, 0))
        draw.text((x, y), title, font=title_font, fill=(255, 255, 255))

        return img

    def _apply_split_style(self, img: Image.Image, title: str, subtitle: str) -> Image.Image:
        """Apply split style with face on one side, text on other."""
        width, height = img.size

        # Create new image with dark left side
        new_img = Image.new('RGB', (width, height), (15, 23, 42))

        # Paste right half of original (face) to right side
        right_half = img.crop((width // 2, 0, width, height))
        new_img.paste(right_half, (width // 2, 0))

        draw = ImageDraw.Draw(new_img)

        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 100)
            subtitle_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()

        # Draw title on left
        draw.text((60, height // 2 - 80), title, font=title_font, fill=(255, 255, 255))
        draw.text((60, height // 2 + 40), subtitle, font=subtitle_font, fill=(34, 197, 94))

        return new_img

    def youtube_export(self, output_path: str, resolution: str = "4k") -> str:
        """
        Export optimized for YouTube upload.

        Args:
            output_path: Output video path
            resolution: "4k" (3840x2160), "1080p" (1920x1080), or "720p" (1280x720)

        Returns:
            Path to exported video
        """
        print(f"\n{'='*70}")
        print(f"YOUTUBE EXPORT ({resolution.upper()})")
        print(f"{'='*70}")

        # Resolution settings
        res_settings = {
            "4k": {"scale": "3840:2160", "bitrate": "35M", "maxrate": "40M"},
            "1080p": {"scale": "1920:1080", "bitrate": "12M", "maxrate": "15M"},
            "720p": {"scale": "1280:720", "bitrate": "6M", "maxrate": "8M"}
        }

        settings = res_settings.get(resolution, res_settings["1080p"])

        # FFmpeg YouTube-optimized export
        cmd = [
            'ffmpeg', '-y',
            '-i', str(self.video_path),
            '-vf', f"scale={settings['scale']}:force_original_aspect_ratio=decrease,pad={settings['scale']}:(ow-iw)/2:(oh-ih)/2",
            '-c:v', 'libx264',
            '-preset', 'slow',  # Better compression
            '-profile:v', 'high',
            '-level', '4.2',
            '-b:v', settings['bitrate'],
            '-maxrate', settings['maxrate'],
            '-bufsize', settings['maxrate'],
            '-pix_fmt', 'yuv420p',
            '-c:a', 'aac',
            '-b:a', '320k',
            '-ar', '48000',
            '-movflags', '+faststart',  # Web optimization
            str(output_path)
        ]

        print(f"-> Exporting at {resolution}...")
        print(f"   Bitrate: {settings['bitrate']}")
        print("   (This may take several minutes...)")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Export failed: {result.stderr}")
            return None

        # Get file size
        size_mb = Path(output_path).stat().st_size / (1024 * 1024)
        print(f"\n-> YouTube export complete: {output_path}")
        print(f"   Size: {size_mb:.1f} MB")

        return output_path


def main():
    parser = argparse.ArgumentParser(description='Video Polish Tools')
    parser.add_argument('--input', required=True, help='Input video file')
    parser.add_argument('--output', help='Output path (default: input_polished.mp4)')

    # Operations
    parser.add_argument('--music', help='Add background music (path to audio file)')
    parser.add_argument('--music-volume', type=float, default=0.1, help='Music volume 0.0-1.0 (default: 0.1 = -20dB)')
    parser.add_argument('--color-grade', action='store_true', help='Apply color grading')
    parser.add_argument('--thumbnail', action='store_true', help='Generate thumbnail')
    parser.add_argument('--thumbnail-style', choices=['bold', 'minimal', 'split'], default='bold')
    parser.add_argument('--thumbnail-title', default='PEPTIDES')
    parser.add_argument('--thumbnail-subtitle', default='The Truth About What Works')
    parser.add_argument('--youtube-export', action='store_true', help='YouTube-optimized export')
    parser.add_argument('--resolution', choices=['4k', '1080p', '720p'], default='1080p')

    args = parser.parse_args()

    # Set default output
    if not args.output:
        input_path = Path(args.input)
        args.output = str(input_path.parent / f"{input_path.stem}_polished{input_path.suffix}")

    try:
        polisher = VideoPolisher(args.input)
        current_video = args.input

        # Apply operations in order
        if args.color_grade:
            color_output = Path(args.output).parent / f"{Path(args.output).stem}_graded.mp4"
            result = polisher.color_grade_broll(str(color_output))
            if result:
                current_video = result
                polisher = VideoPolisher(current_video)

        if args.music:
            music_output = Path(args.output).parent / f"{Path(args.output).stem}_music.mp4"
            result = polisher.add_background_music(
                args.music,
                str(music_output),
                music_volume=args.music_volume
            )
            if result:
                current_video = result
                polisher = VideoPolisher(current_video)

        if args.thumbnail:
            thumb_output = Path(args.output).parent / f"{Path(args.output).stem}_thumbnail.jpg"
            polisher.generate_thumbnail(
                str(thumb_output),
                title_text=args.thumbnail_title,
                subtitle_text=args.thumbnail_subtitle,
                style=args.thumbnail_style
            )

        if args.youtube_export:
            polisher.youtube_export(args.output, resolution=args.resolution)

        print("\nPolish complete!")
        return 0

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
