#!/usr/bin/env python3
"""
MoviePy Video Generator - Local Video Creation (Zero Cost)
Compatible with MoviePy v2.x

Creates fitness ad videos locally using MoviePy instead of cloud APIs.
No per-video costs, full control over quality and effects.

Cost: $0 per video (only local processing)
Time: ~30-60 seconds per video (depending on hardware)

Usage:
    python moviepy_video_generator_v2.py --images img1.jpg,img2.jpg --headline "Transform" --cta "Start Now"
"""

import os
import sys
import argparse
import requests
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Import MoviePy v2.x
try:
    from moviepy import (
        ImageClip, CompositeVideoClip, 
        concatenate_videoclips, AudioFileClip, TextClip
    )
    from moviepy import vfx
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

load_dotenv()


class MoviePyVideoGenerator:
    """
    Local video generation using MoviePy v2.x.
    
    Creates professional fitness ads entirely locally:
    - Downloads images from URLs
    - Adds smooth transitions
    - Overlays text (headline + CTA)
    - Includes background music
    - Exports as MP4
    
    Cost: $0 per video
    """
    
    def __init__(self, temp_dir: str = None):
        """Initialize MoviePy generator."""
        if not MOVIEPY_AVAILABLE:
            raise ImportError("MoviePy not installed. Run: pip install moviepy pillow imageio-ffmpeg")
        
        self.temp_dir = Path(temp_dir) if temp_dir else Path(".tmp/moviepy")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Stock music directory
        self.music_dir = Path("execution/assets/music")
        self.music_dir.mkdir(parents=True, exist_ok=True)
    
    def download_image(self, url: str, output_path: Path) -> bool:
        """Download image from URL to local file."""
        try:
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
        except Exception as e:
            print(f"  ✗ Failed to download {url}: {e}")
            return False
    
    def create_fitness_ad(
        self,
        image_urls: List[str],
        headline: str,
        cta_text: str,
        duration: float = 15.0,
        music_style: str = "energetic",
        resolution: tuple = (1080, 1920)  # 9:16 vertical for social media
    ) -> Dict[str, Any]:
        """
        Create fitness ad video from images.
        
        Args:
            image_urls: List of image URLs (4 recommended)
            headline: Main headline text
            cta_text: Call-to-action text
            duration: Total video duration in seconds
            music_style: Background music style
            resolution: Video resolution (width, height)
            
        Returns:
            Dict with success status, video path, and metadata
        """
        print(f"\n{'='*70}")
        print("MOVIEPY LOCAL VIDEO GENERATION (v2.x)")
        print(f"{'='*70}")
        print(f"Images: {len(image_urls)}")
        print(f"Duration: {duration}s")
        print(f"Resolution: {resolution[0]}x{resolution[1]}")
        print(f"Headline: {headline}")
        print(f"CTA: {cta_text}")
        
        try:
            # Step 1: Download images
            print(f"\n-> Downloading {len(image_urls)} images...")
            image_paths = []
            for i, url in enumerate(image_urls):
                img_path = self.temp_dir / f"img_{i}_{os.getpid()}.jpg"
                if self.download_image(url, img_path):
                    image_paths.append(img_path)
                    print(f"  ✓ Image {i+1}/{len(image_urls)} downloaded")
                else:
                    return {
                        'success': False,
                        'error': f'Failed to download image {i+1}',
                        'method': 'moviepy'
                    }
            
            # Step 2: Create video clips
            print(f"\n-> Creating video clips...")
            clips = []
            duration_per_image = duration / len(image_paths)
            
            for i, img_path in enumerate(image_paths):
                # Create image clip
                clip = ImageClip(str(img_path), duration=duration_per_image)
                
                # Resize and crop to fit resolution
                # First resize to match height
                clip = clip.resized(height=resolution[1])
                
                # Then crop width if needed
                if clip.size[0] > resolution[0]:
                    x_center = clip.size[0] / 2
                    clip = clip.cropped(
                        x_center=x_center,
                        width=resolution[0],
                        height=resolution[1]
                    )
                
                # Add fade transitions using vfx
                if i == 0:
                    # First clip: fade in
                    clip = clip.fx(vfx.fadein, duration=0.5)
                elif i == len(image_paths) - 1:
                    # Last clip: fade out
                    clip = clip.fx(vfx.fadeout, duration=0.5)
                else:
                    # Middle clips: fade in and out
                    clip = clip.fx(vfx.fadein, duration=0.3)
                    clip = clip.fx(vfx.fadeout, duration=0.3)
                
                clips.append(clip)
            
            # Step 3: Concatenate clips
            print(f"-> Concatenating clips...")
            final_video = concatenate_videoclips(clips, method="compose")
            
            # Step 4: Add text overlays
            print(f"-> Adding text overlays...")
            final_video = self._add_text_overlays(final_video, headline, cta_text, duration, resolution)
            
            # Step 5: Add background music
            print(f"-> Adding background music ({music_style})...")
            final_video = self._add_background_music(final_video, music_style)
            
            # Step 6: Export video
            output_path = self.temp_dir / f"video_{os.getpid()}.mp4"
            print(f"-> Exporting video to {output_path}...")
            
            final_video.write_videofile(
                str(output_path),
                fps=30,
                codec='libx264',
                audio_codec='aac',
                preset='medium',
                threads=4,
                logger=None  # Suppress MoviePy logs
            )
            
            # Cleanup
            final_video.close()
            for clip in clips:
                clip.close()
            
            # Get file size
            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            
            print(f"  ✓ Video created successfully!")
            print(f"  File size: {file_size_mb:.2f} MB")
            print(f"  Location: {output_path}")
            
            return {
                'success': True,
                'video_path': str(output_path),
                'method': 'moviepy',
                'cost': 0,
                'file_size_mb': file_size_mb,
                'duration': duration
            }
        
        except Exception as e:
            print(f"  ✗ MoviePy generation failed: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'success': False,
                'error': str(e),
                'method': 'moviepy'
            }
    
    def _add_text_overlays(self, video, headline, cta_text, duration, resolution):
        """Add headline and CTA text overlays to video."""
        try:
            text_clips = [video]
            
            # Headline (first 40% of video)
            headline_duration = duration * 0.4
            txt_headline = TextClip(
                text=headline,
                font_size=80,
                color='white',
                stroke_color='black',
                stroke_width=3,
                size=(resolution[0] - 100, None),
                method='caption'
            )
            txt_headline = txt_headline.with_position('center').with_duration(headline_duration).with_start(0)
            txt_headline = txt_headline.fx(vfx.fadein, duration=0.3).fx(vfx.fadeout, duration=0.3)
            text_clips.append(txt_headline)
            
            # CTA (last 40% of video)
            cta_start = duration * 0.6
            cta_duration = duration * 0.4
            txt_cta = TextClip(
                text=cta_text,
                font_size=70,
                color='white',
                stroke_color='black',
                stroke_width=3,
                size=(resolution[0] - 100, None),
                method='caption'
            )
            txt_cta = txt_cta.with_position(('center', 0.75), relative=True).with_duration(cta_duration).with_start(cta_start)
            txt_cta = txt_cta.fx(vfx.fadein, duration=0.3).fx(vfx.fadeout, duration=0.3)
            text_clips.append(txt_cta)
            
            return CompositeVideoClip(text_clips)
        
        except Exception as e:
            print(f"  ! Warning: Failed to add text overlays: {e}")
            print(f"    Continuing without text...")
            return video
    
    def _add_background_music(self, video, music_style):
        """Add background music to video."""
        music_files = {
            'energetic': self.music_dir / 'energetic.mp3',
            'motivational': self.music_dir / 'motivational.mp3',
            'upbeat': self.music_dir / 'upbeat.mp3',
            'calm': self.music_dir / 'calm.mp3'
        }
        
        music_path = music_files.get(music_style)
        
        if not music_path or not music_path.exists():
            print(f"  ! Warning: Music file not found. Skipping music.")
            print(f"    Add music files to: {self.music_dir}")
            return video
        
        try:
            audio = AudioFileClip(str(music_path))
            audio = audio.subclipped(0, min(audio.duration, video.duration))
            audio = audio.fx(vfx.audio_fadein, duration=1.0)
            audio = audio.fx(vfx.audio_fadeout, duration=1.0)
            audio = audio.with_volume_scaled(0.3)
            video = video.with_audio(audio)
            print(f"  ✓ Background music added")
        except Exception as e:
            print(f"  ! Warning: Failed to add music: {e}")
        
        return video


def main():
    """CLI for MoviePy video generation."""
    parser = argparse.ArgumentParser(
        description="Generate fitness videos locally with MoviePy (zero cost)"
    )
    
    parser.add_argument('--images', required=True, help='Comma-separated list of image URLs')
    parser.add_argument('--headline', default='Transform Your Body', help='Headline text for video')
    parser.add_argument('--cta', default='Start Your Journey', help='Call-to-action text')
    parser.add_argument('--duration', type=float, default=15.0, help='Video duration in seconds')
    parser.add_argument('--music', default='energetic', help='Background music style')
    parser.add_argument('--output', help='Output path for video (optional)')
    
    args = parser.parse_args()
    
    # Parse images
    image_urls = [url.strip() for url in args.images.split(',')]
    
    if len(image_urls) < 2:
        print("Error: Need at least 2 images")
        sys.exit(1)
    
    # Create generator
    generator = MoviePyVideoGenerator()
    
    # Generate video
    result = generator.create_fitness_ad(
        image_urls=image_urls,
        headline=args.headline,
        cta_text=args.cta,
        duration=args.duration,
        music_style=args.music
    )
    
    if not result['success']:
        print(f"\n✗ Error: {result['error']}")
        sys.exit(1)
    
    # Copy to output path if specified
    if args.output:
        import shutil
        shutil.copy(result['video_path'], args.output)
        print(f"✓ Video copied to: {args.output}")
    
    print("\n✓ Video generation complete!")
    print(f"  Cost: $0 (local processing)")
    print(f"  Video: {result['video_path']}")


if __name__ == "__main__":
    main()