#!/usr/bin/env python3
"""
Creatomate Video Generation API Wrapper

Professional video creation using Creatomate's template-based API.
Better developer experience and reliability than Shotstack.

Pricing: $0.05 per video (pay-per-use)
API Docs: https://creatomate.com/docs/api/introduction

Usage:
    python creatomate_api.py create-video --images img1.jpg,img2.jpg --headline "Transform" --cta "Start Now"
    python creatomate_api.py check-status RENDER_ID
"""

import os
import sys
import time
import json
import argparse
import requests
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class CreatomateAPI:
    """
    Creatomate Video Generation API wrapper.
    
    Creates professional videos from templates with dynamic content.
    Cost: ~$0.05 per video
    """
    
    def __init__(self, api_key: str = None, template_id: str = None):
        """
        Initialize Creatomate API wrapper.
        
        Args:
            api_key: Creatomate API key (or from CREATOMATE_API_KEY env var)
            template_id: Template ID to use (or from CREATOMATE_TEMPLATE_ID env var)
        """
        self.api_key = api_key or os.getenv('CREATOMATE_API_KEY')
        self.template_id = template_id or os.getenv('CREATOMATE_TEMPLATE_ID')
        self.base_url = "https://api.creatomate.com/v1"
        
        if not self.api_key:
            print("WARNING: CREATOMATE_API_KEY not found in environment")
            print("Video generation will fail until the key is configured")
            print("Get your API key at: https://creatomate.com/docs/api/authentication")
        
        if not self.template_id:
            print("WARNING: CREATOMATE_TEMPLATE_ID not found in environment")
            print("Will use inline template generation (more complex)")
    
    def get_headers(self) -> Dict[str, str]:
        """Get API headers with authentication."""
        if not self.api_key:
            raise ValueError(
                "CREATOMATE_API_KEY not set.\n"
                "Get your API key from: https://creatomate.com/docs/api/authentication"
            )
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def create_fitness_ad(
        self,
        image_urls: List[str],
        headline: str,
        cta_text: str,
        duration: float = 15.0,
        music_style: str = "energetic"
    ) -> Dict[str, Any]:
        """
        Create a fitness ad video from images using a simple JSON template.
        
        Args:
            image_urls: List of image URLs
            headline: Main headline text
            cta_text: Call-to-action text
            duration: Total video duration in seconds
            music_style: Background music style
            
        Returns:
            Dict with render status and video URL
        """
        print(f"\n{'='*70}")
        print("CREATOMATE VIDEO GENERATION")
        print(f"{'='*70}")
        print(f"Images: {len(image_urls)}")
        print(f"Duration: {duration}s")
        print(f"Headline: {headline}")
        print(f"CTA: {cta_text}")
        
        if not self.api_key:
            return {"success": False, "error": "CREATOMATE_API_KEY not configured"}
        
        try:
            print(f"\n-> Submitting render job...")
            
            # If template_id is configured, use template-based rendering
            if self.template_id:
                print(f"  Using template: {self.template_id}")
                
                # Build modifications for template
                modifications = {
                    "headline": headline,
                    "cta": cta_text,
                }
                
                # Add image sources
                for i, url in enumerate(image_urls):
                    modifications[f"image{i+1}"] = url
                
                # Template-based render request
                render_data = {
                    "template_id": self.template_id,
                    "modifications": modifications
                }
            else:
                # Fall back to inline template
                print(f"  Using inline template (no template_id configured)")
                render_data = self._build_fitness_ad_template(
                    image_urls, headline, cta_text, duration, music_style
                )
            
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
            
            print(f"  OK Render job submitted!")
            print(f"  Render ID: {render_id}")
            print(f"  Estimated cost: $0.05")
            
            # Wait for render to complete
            result = self.wait_for_render(render_id, max_wait=120)
            
            return result
        
        except requests.RequestException as e:
            print(f"  X Request failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _build_fitness_ad_template(
        self,
        image_urls: List[str],
        headline: str,
        cta_text: str,
        duration: float,
        music_style: str
    ) -> Dict[str, Any]:
        """
        Build Creatomate template JSON for fitness ad.
        
        This creates a template inline without requiring a pre-saved template ID.
        """
        duration_per_image = duration / len(image_urls)
        
        # Build elements (layers)
        elements = []
        current_time = 0.0
        
        # Add image clips with transitions
        for i, img_url in enumerate(image_urls):
            # Image element
            image_element = {
                "type": "image",
                "source": img_url,
                "time": current_time,
                "duration": duration_per_image,
                "width": "100%",
                "height": "100%",
                "fit": "cover",
                "x": "50%",
                "y": "50%",
                "animations": []
            }
            
            # Add fade in transition (except first)
            if i > 0:
                image_element["animations"].append({
                    "type": "fade",
                    "fade_start": 0,
                    "easing": "linear",
                    "duration": 0.5
                })
            
            # Add fade out transition (except last)
            if i < len(image_urls) - 1:
                image_element["animations"].append({
                    "type": "fade",
                    "start_time": duration_per_image - 0.5,
                    "fade_start": 1,
                    "fade_end": 0,
                    "easing": "linear",
                    "duration": 0.5
                })
            
            elements.append(image_element)
            
            # Add headline text on first image
            if i == 0:
                elements.append({
                    "type": "text",
                    "text": headline,
                    "time": current_time,
                    "duration": duration_per_image,
                    "x": "50%",
                    "y": "50%",
                    "width": "90%",
                    "font_family": "Montserrat",
                    "font_weight": "800",
                    "font_size": "10%",
                    "fill_color": "#ffffff",
                    "stroke_color": "#000000",
                    "stroke_width": "0.3%",
                    "text_align": "center",
                    "animations": [
                        {
                            "type": "fade",
                            "fade_start": 0,
                            "easing": "quadratic-out",
                            "duration": 0.5
                        },
                        {
                            "type": "fade",
                            "start_time": duration_per_image - 0.5,
                            "fade_start": 1,
                            "fade_end": 0,
                            "easing": "quadratic-in",
                            "duration": 0.5
                        }
                    ]
                })
            
            # Add CTA text on last image
            if i == len(image_urls) - 1:
                elements.append({
                    "type": "text",
                    "text": cta_text,
                    "time": current_time,
                    "duration": duration_per_image,
                    "x": "50%",
                    "y": "75%",
                    "width": "90%",
                    "font_family": "Montserrat",
                    "font_weight": "700",
                    "font_size": "8%",
                    "fill_color": "#ffffff",
                    "stroke_color": "#000000",
                    "stroke_width": "0.3%",
                    "text_align": "center",
                    "animations": [
                        {
                            "type": "fade",
                            "fade_start": 0,
                            "easing": "quadratic-out",
                            "duration": 0.5
                        }
                    ]
                })
            
            current_time += duration_per_image
        
        # Stock music URLs (free music from Creatomate library)
        music_urls = {
            "energetic": "https://creatomate-static.s3.amazonaws.com/music/energetic-workout.mp3",
            "motivational": "https://creatomate-static.s3.amazonaws.com/music/motivational-sport.mp3",
            "upbeat": "https://creatomate-static.s3.amazonaws.com/music/upbeat-pop.mp3",
            "calm": "https://creatomate-static.s3.amazonaws.com/music/calm-ambient.mp3"
        }
        
        # Note: Using placeholder URLs - you may need to update with actual Creatomate music library URLs
        # or provide your own music URLs
        
        # Build complete template
        template = {
            "output_format": "mp4",
            "width": 1080,
            "height": 1920,  # 9:16 vertical for social media
            "frame_rate": 30,
            "duration": duration,
            "elements": elements
        }
        
        return template
    
    def check_render_status(self, render_id: str) -> Dict[str, Any]:
        """
        Check the status of a render job.
        
        Args:
            render_id: The render ID from create_fitness_ad
            
        Returns:
            Dict with status and video URL if complete
        """
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
                print(f"  OK Video ready: {result['video_url']}")
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
        max_wait: int = 120,
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
        print(f"\n-> Waiting for render to complete (max {max_wait}s)...")
        
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
    """CLI for Creatomate video generation."""
    if len(sys.argv) < 2:
        print("Usage: python creatomate_api.py <command> [options]")
        print("\nCommands:")
        print("  create-video --images URL1,URL2 --headline 'Your Text' --cta 'Start Now'")
        print("  check-status RENDER_ID")
        print("\nEnvironment: Set CREATOMATE_API_KEY in .env file")
        sys.exit(1)
    
    command = sys.argv[1]
    api = CreatomateAPI()
    
    try:
        if command == "create-video":
            parser = argparse.ArgumentParser()
            parser.add_argument('--images', required=True)
            parser.add_argument('--headline', default='Transform Your Body')
            parser.add_argument('--cta', default='Start Your Journey')
            parser.add_argument('--duration', type=float, default=15.0)
            parser.add_argument('--music', default='energetic')
            
            args = parser.parse_args(sys.argv[2:])
            
            images = [url.strip() for url in args.images.split(',')]
            
            result = api.create_fitness_ad(
                image_urls=images,
                headline=args.headline,
                cta_text=args.cta,
                duration=args.duration,
                music_style=args.music
            )
            
            if result.get("video_url"):
                print(f"\n✓ Video URL: {result['video_url']}")
            else:
                print(f"\n✗ Failed: {result.get('error')}")
        
        elif command == "check-status":
            render_id = sys.argv[2]
            result = api.check_render_status(render_id)
            print(f"\nStatus: {result.get('status')}")
            if result.get("video_url"):
                print(f"Video URL: {result['video_url']}")
        
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()