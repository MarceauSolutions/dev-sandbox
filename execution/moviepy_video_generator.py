#!/usr/bin/env python3
"""
Simple MoviePy Video Generator - Compatible with MoviePy v2.x
Creates basic video slideshows from images.
"""

import os
import sys
import argparse
import requests
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

try:
    from moviepy import ImageClip, concatenate_videoclips
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

load_dotenv()


class MoviePyVideoGenerator:
    """Simple local video generation using MoviePy v2.x."""
    
    def __init__(self, temp_dir: str = None):
        """Initialize generator."""
        if not MOVIEPY_AVAILABLE:
            raise ImportError("MoviePy not installed")
        
        self.temp_dir = Path(temp_dir) if temp_dir else Path(".tmp/moviepy")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def download_image(self, url: str, output_path: Path) -> bool:
        """Download image from URL."""
        try:
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            print(f"  ✗ Failed to download: {e}")
            return False
    
    def create_fitness_ad(
        self,
        image_urls: List[str],
        headline: str,
        cta_text: str,
        duration: float = 15.0,
        music_style: str = "energetic",
        resolution: tuple = (1080, 1920)
    ) -> Dict[str, Any]:
        """Create video from images (simplified version)."""
        print(f"\n{'='*70}")
        print("MOVIEPY SIMPLE VIDEO GENERATION")
        print(f"{'='*70}")
        print(f"Images: {len(image_urls)} | Duration: {duration}s")
        
        try:
            # Download images
            print(f"\n-> Downloading images...")
            image_paths = []
            for i, url in enumerate(image_urls):
                img_path = self.temp_dir / f"img_{i}_{os.getpid()}.jpg"
                if self.download_image(url, img_path):
                    image_paths.append(img_path)
                    print(f"  ✓ Image {i+1}/{len(image_urls)}")
                else:
                    return {'success': False, 'error': f'Download failed', 'method': 'moviepy'}
            
            # Create clips
            print(f"-> Creating video clips...")
            clips = []
            duration_per_image = duration / len(image_paths)
            
            for img_path in image_paths:
                clip = ImageClip(str(img_path), duration=duration_per_image)
                # Resize to target resolution
                clip = clip.resized(height=resolution[1])
                # Crop to exact width if needed
                if clip.size[0] > resolution[0]:
                    x_center = clip.size[0] / 2
                    clip = clip.cropped(
                        x_center=x_center,
                        width=resolution[0],
                        height=resolution[1]
                    )
                clips.append(clip)
            
            # Concatenate
            print(f"-> Concatenating...")
            final_video = concatenate_videoclips(clips, method="compose")
            
            # Export
            output_path = self.temp_dir / f"video_{os.getpid()}.mp4"
            print(f"-> Exporting to {output_path}...")
            
            final_video.write_videofile(
                str(output_path),
                fps=30,
                codec='libx264',
                audio_codec='aac',
                preset='medium',
                threads=4,
                logger=None
            )
            
            # Cleanup
            final_video.close()
            for clip in clips:
                clip.close()
            
            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            
            print(f"\n✓ Video created! Size: {file_size_mb:.2f} MB")
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
            print(f"\n✗ Failed: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e), 'method': 'moviepy'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--images', required=True)
    parser.add_argument('--headline', default='Transform')
    parser.add_argument('--cta', default='Start Now')
    parser.add_argument('--duration', type=float, default=15.0)
    parser.add_argument('--music', default='energetic')
    args = parser.parse_args()
    
    image_urls = [url.strip() for url in args.images.split(',')]
    generator = MoviePyVideoGenerator()
    result = generator.create_fitness_ad(
        image_urls=image_urls,
        headline=args.headline,
        cta_text=args.cta,
        duration=args.duration,
        music_style=args.music
    )
    
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()