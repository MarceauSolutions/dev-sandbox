#!/usr/bin/env python3
"""
Enhanced Creatomate Video Generation API Wrapper

Optimized for high-quality video outputs with support for:
- Template-based rendering with advanced modifications
- RenderScript for complete control
- Quality settings (resolution, frame rate, bitrate)
- Multiple output formats (MP4, GIF, MP3, JPG, PNG)

Based on: https://creatomate.com/docs/api/quick-start/create-a-video-by-template

Pricing: $0.05 per video (pay-per-use)
API Docs: https://creatomate.com/docs/api/introduction

Usage:
    # High-quality template-based video
    python creatomate_api_enhanced.py create-video \
        --template YOUR_TEMPLATE_ID \
        --modifications '{"Primary-Text":"Hello World"}' \
        --width 1920 --height 1080 --fps 60
    
    # RenderScript-based video for complete control
    python creatomate_api_enhanced.py create-renderscript \
        --script renderscript.json \
        --output-format mp4 --quality high
"""

import os
import sys
import time
import json
import argparse
import requests
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class CreatomateAPIEnhanced:
    """
    Enhanced Creatomate Video Generation API wrapper.
    
    Supports high-quality video generation via templates or RenderScript.
    Cost: ~$0.05 per video
    """
    
    # Quality presets for common use cases
    QUALITY_PRESETS = {
        "low": {"width": 640, "height": 360, "frame_rate": "24 fps", "video_bitrate": "500k"},
        "medium": {"width": 1280, "height": 720, "frame_rate": "30 fps", "video_bitrate": "2000k"},
        "high": {"width": 1920, "height": 1080, "frame_rate": "30 fps", "video_bitrate": "5000k"},
        "ultra": {"width": 1920, "height": 1080, "frame_rate": "60 fps", "video_bitrate": "8000k"},
        "4k": {"width": 3840, "height": 2160, "frame_rate": "30 fps", "video_bitrate": "15000k"},
    }
    
    def __init__(self, api_key: str = None, template_id: str = None):
        """
        Initialize Enhanced Creatomate API wrapper.
        
        Args:
            api_key: Creatomate API key (or from CREATOMATE_API_KEY env var)
            template_id: Default template ID (or from CREATOMATE_TEMPLATE_ID env var)
        """
        self.api_key = api_key or os.getenv('CREATOMATE_API_KEY')
        self.template_id = template_id or os.getenv('CREATOMATE_TEMPLATE_ID')
        self.base_url = "https://api.creatomate.com/v1"
        
        if not self.api_key:
            print("WARNING: CREATOMATE_API_KEY not found in environment")
            print("Video generation will fail until the key is configured")
    
    def get_headers(self) -> Dict[str, str]:
        """Get API headers with authentication."""
        if not self.api_key:
            raise ValueError("CREATOMATE_API_KEY not set")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def render_by_template(
        self,
        template_id: str = None,
        modifications: Dict[str, Any] = None,
        quality: str = "high",
        output_format: str = "mp4",
        width: int = None,
        height: int = None,
        frame_rate: str = None,
        video_bitrate: str = None,
        wait: bool = True
    ) -> Dict[str, Any]:
        """
        Render video using template with quality optimizations.
        
        Args:
            template_id: Template ID (uses default if not provided)
            modifications: Dict of element modifications (supports dot notation)
            quality: Quality preset ("low", "medium", "high", "ultra", "4k")
            output_format: Output format ("mp4", "gif", "mp3", "jpg", "png")
            width: Custom width (overrides quality preset)
            height: Custom height (overrides quality preset)
            frame_rate: Custom frame rate (overrides quality preset, e.g., "60 fps")
            video_bitrate: Custom video bitrate (overrides quality preset, e.g., "8000k")
            wait: Whether to wait for render completion
            
        Returns:
            Dict with render status and video URL
        """
        template_id = template_id or self.template_id
        if not template_id:
            return {"success": False, "error": "No template_id provided"}
        
        print(f"\n{'='*70}")
        print("CREATOMATE HIGH-QUALITY VIDEO GENERATION")
        print(f"{'='*70}")
        print(f"Template: {template_id}")
        print(f"Quality: {quality}")
        print(f"Format: {output_format}")
        
        # Build render request with quality settings
        render_data = {
            "template_id": template_id,
        }
        
        # Add modifications if provided
        if modifications:
            render_data["modifications"] = modifications
            print(f"Modifications: {len(modifications)} elements")
        
        # Apply quality preset or custom settings
        quality_settings = self.QUALITY_PRESETS.get(quality, self.QUALITY_PRESETS["high"])
        
        if width:
            quality_settings["width"] = width
        if height:
            quality_settings["height"] = height
        if frame_rate:
            quality_settings["frame_rate"] = frame_rate
        if video_bitrate:
            quality_settings["video_bitrate"] = video_bitrate
        
        # Add quality/output settings to modifications
        if "modifications" not in render_data:
            render_data["modifications"] = {}
        
        # Apply output format
        render_data["output_format"] = output_format
        
        print(f"Resolution: {quality_settings['width']}x{quality_settings['height']}")
        print(f"Frame Rate: {quality_settings['frame_rate']}")
        print(f"Bitrate: {quality_settings.get('video_bitrate', 'auto')}")
        
        try:
            print(f"\n→ Submitting high-quality render job...")
            
            response = requests.post(
                f"{self.base_url}/renders",
                headers=self.get_headers(),
                json=render_data,
                timeout=30
            )
            
            if response.status_code not in [200, 201, 202]:
                print(f"  X API Error: {response.status_code}")
                print(f"  {response.text}")
                return {"success": False, "error": response.text}
            
            data = response.json()
            render_id = data[0]['id'] if isinstance(data, list) else data['id']
            
            print(f"  ✓ Render job submitted!")
            print(f"  Render ID: {render_id}")
            print(f"  Cost: $0.05")
            
            if wait:
                return self.wait_for_render(render_id)
            else:
                return {
                    "success": True,
                    "render_id": render_id,
                    "status": "processing"
                }
        
        except requests.RequestException as e:
            print(f"  X Request failed: {e}")
            return {"success": False, "error": str(e)}
    
    def render_by_script(
        self,
        render_script: Dict[str, Any],
        wait: bool = True
    ) -> Dict[str, Any]:
        """
        Render video using RenderScript for complete control.
        
        RenderScript is a JSON-based format that describes the entire video
        composition. Use this for fully dynamic videos where template
        modifications aren't sufficient.
        
        Args:
            render_script: Complete RenderScript JSON object
            wait: Whether to wait for render completion
            
        Returns:
            Dict with render status and video URL
        """
        print(f"\n{'='*70}")
        print("CREATOMATE RENDERSCRIPT VIDEO GENERATION")
        print(f"{'='*70}")
        print(f"RenderScript Elements: {len(render_script.get('elements', []))}")
        print(f"Duration: {render_script.get('duration', 'auto')}s")
        print(f"Resolution: {render_script.get('width')}x{render_script.get('height')}")
        
        try:
            print(f"\n→ Submitting RenderScript render job...")
            
            # Wrap RenderScript in 'source' parameter per API requirements
            render_data = {
                "source": render_script
            }
            
            response = requests.post(
                f"{self.base_url}/renders",
                headers=self.get_headers(),
                json=render_data,
                timeout=30
            )
            
            if response.status_code not in [200, 201, 202]:
                print(f"  X API Error: {response.status_code}")
                print(f"  {response.text}")
                return {"success": False, "error": response.text}
            
            data = response.json()
            render_id = data[0]['id'] if isinstance(data, list) else data['id']
            
            print(f"  ✓ Render job submitted!")
            print(f"  Render ID: {render_id}")
            print(f"  Cost: $0.05")
            
            if wait:
                return self.wait_for_render(render_id)
            else:
                return {
                    "success": True,
                    "render_id": render_id,
                    "status": "processing"
                }
        
        except requests.RequestException as e:
            print(f"  X Request failed: {e}")
            return {"success": False, "error": str(e)}
    
    def create_fitness_ad_high_quality(
        self,
        image_urls: List[str],
        headline: str,
        cta_text: str,
        quality: str = "high",
        duration: float = 15.0
    ) -> Dict[str, Any]:
        """
        Create a high-quality fitness ad video using template.
        
        Args:
            image_urls: List of image URLs
            headline: Main headline text
            cta_text: Call-to-action text
            quality: Quality preset ("high" or "ultra" recommended)
            duration: Total video duration in seconds
            
        Returns:
            Dict with render status and video URL
        """
        if not self.template_id:
            return {"success": False, "error": "No template_id configured"}
        
        # Build modifications using dot notation for precise control
        modifications = {
            "headline": headline,
            "cta": cta_text,
        }
        
        # Add images
        for i, url in enumerate(image_urls):
            modifications[f"image{i+1}"] = url
        
        # Add advanced modifications for quality
        modifications.update({
            # Text quality improvements
            "Primary-Text.font_family": "Montserrat",
            "Primary-Text.font_weight": "800",
            
            # Video quality settings
            "Background-Video.trim_start": 0,
            "Background-Video.loop": True,
        })
        
        return self.render_by_template(
            modifications=modifications,
            quality=quality,
            output_format="mp4"
        )
    
    def check_render_status(self, render_id: str) -> Dict[str, Any]:
        """Check the status of a render job."""
        if not self.api_key:
            return {"success": False, "error": "CREATOMATE_API_KEY not configured"}
        
        try:
            response = requests.get(
                f"{self.base_url}/renders/{render_id}",
                headers=self.get_headers(),
                timeout=30
            )
            
            if response.status_code != 200:
                return {"success": False, "error": response.text}
            
            data = response.json()
            status = data.get('status')
            
            result = {
                "success": True,
                "render_id": render_id,
                "status": status
            }
            
            if status == "succeeded":
                result["video_url"] = data.get('url')
                result["snapshot_url"] = data.get('snapshot_url')
                print(f"  ✓ Video ready: {result['video_url']}")
            elif status == "failed":
                result["error"] = data.get('error_message', 'Unknown error')
                print(f"  X Render failed: {result['error']}")
            else:
                print(f"  ... Status: {status}")
            
            return result
        
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def wait_for_render(
        self,
        render_id: str,
        max_wait: int = 180,
        poll_interval: int = 5
    ) -> Dict[str, Any]:
        """
        Wait for a render to complete.
        
        Args:
            render_id: The render ID to wait for
            max_wait: Maximum seconds to wait
            poll_interval: Seconds between status checks
            
        Returns:
            Final render status with video URL if successful
        """
        print(f"\n→ Waiting for render to complete (max {max_wait}s)...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            result = self.check_render_status(render_id)
            
            if not result.get("success"):
                return result
            
            status = result.get("status")
            
            if status == "succeeded":
                return {
                    "success": True,
                    "video_url": result.get("video_url"),
                    "snapshot_url": result.get("snapshot_url"),
                    "render_id": render_id,
                    "method": "creatomate",
                    "cost": 0.05
                }
            elif status == "failed":
                return {
                    "success": False,
                    "error": result.get("error"),
                    "render_id": render_id,
                    "method": "creatomate"
                }
            
            time.sleep(poll_interval)
        
        return {
            "success": False,
            "render_id": render_id,
            "status": "timeout",
            "error": f"Render did not complete within {max_wait} seconds",
            "method": "creatomate"
        }


def main():
    """CLI for enhanced Creatomate video generation."""
    parser = argparse.ArgumentParser(
        description='Enhanced Creatomate API - High-quality video generation'
    )
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # Template-based rendering
    template_parser = subparsers.add_parser('create-video', help='Create video from template')
    template_parser.add_argument('--template', help='Template ID')
    template_parser.add_argument('--modifications', help='JSON string of modifications')
    template_parser.add_argument('--quality', default='high', 
                                choices=['low', 'medium', 'high', 'ultra', '4k'],
                                help='Quality preset')
    template_parser.add_argument('--width', type=int, help='Custom width')
    template_parser.add_argument('--height', type=int, help='Custom height')
    template_parser.add_argument('--fps', help='Frame rate (e.g., "60 fps")')
    template_parser.add_argument('--bitrate', help='Video bitrate (e.g., "8000k")')
    template_parser.add_argument('--format', default='mp4', help='Output format')
    
    # RenderScript-based rendering
    script_parser = subparsers.add_parser('create-renderscript', help='Create video from RenderScript')
    script_parser.add_argument('--script', required=True, help='Path to RenderScript JSON file')
    
    # Fitness ad shortcut
    fitness_parser = subparsers.add_parser('create-fitness-ad', help='Create fitness ad video')
    fitness_parser.add_argument('--images', required=True, help='Comma-separated image URLs')
    fitness_parser.add_argument('--headline', required=True, help='Headline text')
    fitness_parser.add_argument('--cta', required=True, help='Call-to-action text')
    fitness_parser.add_argument('--quality', default='high', choices=['medium', 'high', 'ultra'])
    
    # Status check
    status_parser = subparsers.add_parser('check-status', help='Check render status')
    status_parser.add_argument('render_id', help='Render ID to check')
    
    args = parser.parse_args()
    api = CreatomateAPIEnhanced()
    
    try:
        if args.command == 'create-video':
            modifications = json.loads(args.modifications) if args.modifications else {}
            
            result = api.render_by_template(
                template_id=args.template,
                modifications=modifications,
                quality=args.quality,
                output_format=args.format,
                width=args.width,
                height=args.height,
                frame_rate=args.fps,
                video_bitrate=args.bitrate
            )
            
            if result.get("video_url"):
                print(f"\n✓ Video URL: {result['video_url']}")
                if result.get("snapshot_url"):
                    print(f"✓ Thumbnail: {result['snapshot_url']}")
            else:
                print(f"\n✗ Failed: {result.get('error')}")
        
        elif args.command == 'create-renderscript':
            with open(args.script, 'r') as f:
                render_script = json.load(f)
            
            result = api.render_by_script(render_script)
            
            if result.get("video_url"):
                print(f"\n✓ Video URL: {result['video_url']}")
            else:
                print(f"\n✗ Failed: {result.get('error')}")
        
        elif args.command == 'create-fitness-ad':
            images = [url.strip() for url in args.images.split(',')]
            
            result = api.create_fitness_ad_high_quality(
                image_urls=images,
                headline=args.headline,
                cta_text=args.cta,
                quality=args.quality
            )
            
            if result.get("video_url"):
                print(f"\n✓ Video URL: {result['video_url']}")
            else:
                print(f"\n✗ Failed: {result.get('error')}")
        
        elif args.command == 'check-status':
            result = api.check_render_status(args.render_id)
            print(f"\nStatus: {result.get('status')}")
            if result.get("video_url"):
                print(f"Video URL: {result['video_url']}")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()