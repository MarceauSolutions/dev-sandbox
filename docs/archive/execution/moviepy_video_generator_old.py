#!/usr/bin/env python3
"""
MoviePy Video Generator - Local Video Creation (Zero Cost)

Creates fitness ad videos locally using MoviePy instead of cloud APIs.
No per-video costs, full control over quality and effects.

Cost: $0 per video (only local processing)
Time: ~30-60 seconds per video (depending on hardware)

Usage:
    python moviepy_video_generator.py --images img1.jpg,img2.jpg --headline "Transform" --cta "Start Now"
"""

import os
import sys
import argparse
import requests
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from dotenv import load_dotenv

# Import MoviePy (v2.x has different import structure)
try:
    from moviepy import (
        ImageClip, VideoClip, CompositeVideoClip, 
        concatenate_videoclips, AudioFileClip, TextClip
    )
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    # Define dummy classes for type checking
    if TYPE_CHECKING:
        VideoClip = Any
        CompositeVideoClip = Any
    else:
        VideoClip = object
        CompositeVideoClip = object

load_dotenv()


class MoviePyVideoGenerator:
    """
    Local video generation using MoviePy.
    
    Creates professional fitness ads entirely locally:
    - Downloads images from URLs
    - Adds smooth transitions
    - Overlays text (headline + CTA)
    - Includes background music
    - Exports as MP4
    
    Cost: $0 per video
    """
    
    def __init__(self, temp_dir: str = None):
        """
        Initialize MoviePy generator.
        
        Args:
            temp_dir: Directory for temporary files (default: .tmp/moviepy)
        """
        if not MOVIEPY_AVAILABLE:
            raise ImportError("MoviePy not installed. Run: pip install moviepy pillow imageio-ffmpeg")
        
        self.temp_dir = Path(temp_dir) if temp_dir else Path(".tmp/moviepy")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Stock music directory
        self.music_dir = Path("execution/assets/music")
        self.music_dir.mkdir(parents=True, exist_ok=True)
    
    def download_image(self, url: str, output_path: Path) -> bool:
        """
        Download image from URL to local file.
        
        Args:
            url: Image URL
            output_path: Local path to save image
            
        Returns:
            True if successful
        """
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
            music_style: Background music style (energetic, motivational, upbeat)
            resolution: Video resolution (width, height)
            
        Returns:
            Dict with success status, video path, and metadata
        """
        print(f"\n{'='*70}")
        print("MOVIEPY LOCAL VIDEO GENERATION")
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
            print(f"\n-> Creating video clips with transitions...")
            clips = self._create_clips_with_transitions(
                image_paths, headline, cta_text, duration, resolution
            )
            
            # Step 3: Concatenate clips
            print(f"-> Concatenating clips...")
            final_video = concatenate_videoclips(clips, method="compose")
            
            # Step 4: Add background music
            print(f"-> Adding background music ({music_style})...")
            final_video = self._add_background_music(final_video, music_style)
            
            # Step 5: Export video
            output_path = self.temp_dir / f"video_{os.getpid()}.mp4"
            print(f"-> Exporting video to {output_path}...")
            
            final_video.write_videofile(
                str(output_path),
                fps=30,
                codec='libx264',
                audio_codec='aac',
                preset='medium',  # Balance between speed and quality
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
    
    def _create_clips_with_transitions(
        self,
        image_paths: List[Path],
        headline: str,
        cta_text: str,
        duration: float,
        resolution: tuple
    ) -> List[VideoClip]:
        """
        Create video clips from images with text overlays and transitions.
        
        Args:
            image_paths: List of local image paths
            headline: Headline text for first image
            cta_text: CTA text for last image
            duration: Total video duration
            resolution: Video resolution (width, height)
            
        Returns:
            List of video clips ready to concatenate
        """
        clips = []
        duration_per_image = duration / len(image_paths)
        transition_duration = 0.5  # 0.5 second crossfade
        
        for i, img_path in enumerate(image_paths):
            # Create image clip
            clip = ImageClip(str(img_path), duration=duration_per_image)
            
            # Resize to fit resolution (maintain aspect ratio, crop to fit)
            clip = clip.resized(height=resolution[1])
            
            # Center crop to exact resolution
            if clip.w > resolution[0]:
                clip = clip.cropped(
                    x_center=clip.w/2,
                    width=resolution[0],
                    height=resolution[1]
                )
            
            # Add transitions (crossfade)
            if i > 0:  # Fade in on all except first
                clip = clip.with_effects([lambda c: c.crossfadein(transition_duration)])
            if i < len(image_paths) - 1:  # Fade out on all except last
                clip = clip.with_effects([lambda c: c.crossfadeout(transition_duration)])
            
            # Add text overlays
            if i == 0:  # First image gets headline
                clip = self._add_headline_text(clip, headline, resolution)
            
            if i == len(image_paths) - 1:  # Last image gets CTA
                clip = self._add_cta_text(clip, cta_text, resolution)
            
            clips.append(clip)
        
        return clips
    
    def _add_headline_text(
        self,
        clip: VideoClip,
        headline: str,
        resolution: tuple
    ) -> CompositeVideoClip:
        """
        Add headline text overlay to clip.
        
        Args:
            clip: Video clip
            headline: Headline text
            resolution: Video resolution
            
        Returns:
            Composite clip with text overlay
        """
        try:
            # Create text clip
            txt = TextClip(
                headline,
                fontsize=80,
                color='white',
                font='Arial-Bold',
                stroke_color='black',
                stroke_width=3,
                method='caption',
                size=(resolution[0] - 100, None),  # Leave margin
                align='center'
            )
            
            # Position text in center
            txt = txt.set_position('center').set_duration(clip.duration)
            
            # Add fade in/out effects
            txt = txt.crossfadein(0.3).crossfadeout(0.3)
            
            # Composite
            return CompositeVideoClip([clip, txt])
        
        except Exception as e:
            print(f"  ! Warning: Failed to add headline text: {e}")
            return clip  # Return clip without text if text fails
    
    def _add_cta_text(
        self,
        clip: VideoClip,
        cta_text: str,
        resolution: tuple
    ) -> CompositeVideoClip:
        """
        Add CTA text overlay to clip.
        
        Args:
            clip: Video clip
            cta_text: CTA text
            resolution: Video resolution
            
        Returns:
            Composite clip with text overlay
        """
        try:
            # Create text clip
            txt = TextClip(
                cta_text,
                fontsize=70,
                color='white',
                font='Arial-Bold',
                stroke_color='black',
                stroke_width=3,
                method='caption',
                size=(resolution[0] - 100, None),
                align='center'
            )
            
            # Position text at bottom (80% down)
            txt = txt.set_position(('center', 0.75), relative=True)
            txt = txt.set_duration(clip.duration)
            
            # Add fade in/out effects
            txt = txt.crossfadein(0.3).crossfadeout(0.3)
            
            # Composite
            return CompositeVideoClip([clip, txt])
        
        except Exception as e:
            print(f"  ! Warning: Failed to add CTA text: {e}")
            return clip  # Return clip without text if text fails
    
    def _add_background_music(
        self,
        video: VideoClip,
        music_style: str
    ) -> VideoClip:
        """
        Add background music to video.
        
        Args:
            video: Video clip
            music_style: Music style (energetic, motivational, upbeat)
            
        Returns:
            Video with background music
        """
        # Stock music files (you'll need to add these)
        music_files = {
            'energetic': self.music_dir / 'energetic.mp3',
            'motivational': self.music_dir / 'motivational.mp3',
            'upbeat': self.music_dir / 'upbeat.mp3',
            'calm': self.music_dir / 'calm.mp3'
        }
        
        music_path = music_files.get(music_style)
        
        # Check if music file exists
        if not music_path or not music_path.exists():
            print(f"  ! Warning: Music file not found for '{music_style}'. Skipping music.")
            print(f"    Add music files to: {self.music_dir}")
            return video
        
        try:
            # Load audio
            audio = AudioFileClip(str(music_path))
            
            # Trim audio to match video duration
            audio = audio.subclip(0, min(audio.duration, video.duration))
            
            # Lower volume (30% of original)
            audio = audio.volumex(0.3)
            
            # Add fade out at the end
            audio = audio.audio_fadeout(1.0)
            
            # Set audio to video
            video = video.set_audio(audio)
            
            print(f"  ✓ Background music added")
            
        except Exception as e:
            print(f"  ! Warning: Failed to add music: {e}")
        
        return video
    
    def cleanup_temp_files(self):
        """Remove temporary files."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            print(f"✓ Cleaned up temporary files in {self.temp_dir}")


def main():
    """CLI for MoviePy video generation."""
    parser = argparse.ArgumentParser(
        description="Generate fitness videos locally with MoviePy (zero cost)"
    )
    
    parser.add_argument(
        '--images',
        required=True,
        help='Comma-separated list of image URLs'
    )
    
    parser.add_argument(
        '--headline',
        default='Transform Your Body',
        help='Headline text for video'
    )
    
    parser.add_argument(
        '--cta',
        default='Start Your Journey',
        help='Call-to-action text'
    )
    
    parser.add_argument(
        '--duration',
        type=float,
        default=15.0,
        help='Video duration in seconds'
    )
    
    parser.add_argument(
        '--music',
        default='energetic',
        choices=['energetic', 'motivational', 'upbeat', 'calm'],
        help='Background music style'
    )
    
    parser.add_argument(
        '--output',
        help='Output path for video (optional)'
    )
    
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