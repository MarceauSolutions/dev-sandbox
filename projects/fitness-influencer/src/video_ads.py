#!/usr/bin/env python3
"""
video_ads.py - Fitness Video Advertisement Generator

WHAT: Creates complete video ads by generating AI images + stitching into video
WHY: Automate fitness ad creation for social media (Instagram, TikTok, YouTube)
INPUT: Ad concept, headline, CTA text, number of images
OUTPUT: Rendered video ad (MP4) ready to post
COST: $0.34 per 15-second ad (4 images @ $0.07 + video render @ $0.06)
TIME: ~90 seconds (60s image generation + 30s video rendering)

QUICK USAGE:
  python execution/video_ads.py --account "@boabfit" --headline "Your Fitness Journey Starts Here"
  python execution/video_ads.py --concept "muscle building transformation" --duration 15

CAPABILITIES:
  • Generates 4 AI images using Grok based on fitness concept
  • Creates video from images using Shotstack with transitions
  • Adds text overlays (headline + CTA)
  • Includes background music
  • Optimized for Instagram Reels, TikTok, YouTube Shorts
  • 9:16 vertical format for mobile

EXAMPLE PROMPTS:
  "Build a video ad for @boabfit showing transformation journey"
  "Create a 15-second ad about muscle building with motivational vibes"
  "Make a fitness ad highlighting workout variety and inclusivity"
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Import our API wrappers
from grok_image_gen import GrokImageGenerator
from intelligent_video_router import IntelligentVideoRouter

load_dotenv()


class VideoAdGenerator:
    """
    Complete fitness video ad generator combining AI images + video rendering.
    
    Workflow:
    1. Generate 4 AI images based on fitness concept (Grok)
    2. Create video from images using intelligent router (MoviePy or Creatomate)
    3. Add text overlays (headline + CTA)
    4. Add background music
    5. Export as MP4
    
    Cost: ~$0.28-$0.33 per 15-second video ad (down from $0.34)
    - Images: $0.28 (4 images × $0.07)
    - Video: $0-$0.05 (70% free MoviePy, 30% Creatomate)
    Time: ~60-90 seconds total
    """
    
    def __init__(self):
        self.grok = GrokImageGenerator()
        self.video_router = IntelligentVideoRouter()
        
    def generate_image_prompts(
        self,
        concept: str,
        account_name: str = None,
        num_images: int = 4
    ) -> List[str]:
        """
        Generate optimized image prompts for fitness ads.
        
        Args:
            concept: Ad concept/theme (e.g., "transformation", "workout variety")
            account_name: Instagram/social media account name
            num_images: Number of images to generate (default 4 for 15s video)
            
        Returns:
            List of detailed image prompts
        """
        # Base style for all images
        base_style = (
            "professional fitness photography, high contrast lighting, "
            "vibrant colors, modern aesthetic, instagram-worthy, "
            "sharp focus, dynamic composition"
        )
        
        # Common fitness ad scenes
        prompts = [
            # Image 1: Hero/Opener
            f"Dynamic fitness hero shot, {concept}, athletic person in action pose, "
            f"{base_style}, motivational energy, empowering vibe",
            
            # Image 2: Process/Workout
            f"Fitness workout in progress, {concept}, showing proper form and technique, "
            f"{base_style}, focused expression, gym environment",
            
            # Image 3: Results/Transformation
            f"Fitness transformation result, {concept}, confident pose, "
            f"{base_style}, achievement vibe, inspiring moment",
            
            # Image 4: Call-to-Action
            f"Fitness motivation closeup, {concept}, determined expression, "
            f"{base_style}, ready to start journey, aspirational feeling"
        ]
        
        return prompts[:num_images]
    
    def create_video_ad(
        self,
        concept: str = "fitness transformation",
        headline: str = "Transform Your Body",
        cta_text: str = "Start Your Journey",
        account_name: str = None,
        duration: float = 15.0,
        num_images: int = 4,
        music_style: str = "energetic",
        output_path: str = None
    ) -> Dict[str, Any]:
        """
        Create complete video ad from concept to final video.
        
        Args:
            concept: Ad concept/theme
            headline: Main headline text for ad
            cta_text: Call-to-action text
            account_name: Social media account (for branding)
            duration: Video duration in seconds
            num_images: Number of AI images to generate
            music_style: Background music style
            output_path: Optional local path to save video
            
        Returns:
            Dict with video_url, render_id, cost, and status
        """
        print("\n" + "="*70)
        print("FITNESS VIDEO AD GENERATOR")
        print("="*70)
        print(f"Concept: {concept}")
        print(f"Headline: {headline}")
        print(f"CTA: {cta_text}")
        print(f"Duration: {duration}s")
        print(f"Images: {num_images}")
        print(f"Music: {music_style}")
        if account_name:
            print(f"Account: {account_name}")
        
        # Step 1: Generate image prompts
        print(f"\n{'='*70}")
        print("STEP 1: GENERATING IMAGE PROMPTS")
        print("="*70)
        prompts = self.generate_image_prompts(concept, account_name, num_images)
        
        for i, prompt in enumerate(prompts, 1):
            print(f"\nImage {i} prompt:")
            print(f"  {prompt[:80]}...")
        
        # Step 2: Generate AI images with Grok
        print(f"\n{'='*70}")
        print("STEP 2: GENERATING AI IMAGES WITH GROK")
        print("="*70)
        print(f"Generating {num_images} images...")
        print(f"Cost: ${0.07 * num_images:.2f} ({num_images} images × $0.07)")
        print(f"Time: ~{num_images * 15} seconds")
        
        image_urls = []
        total_image_cost = 0.0
        
        for i, prompt in enumerate(prompts, 1):
            print(f"\n-> Generating image {i}/{num_images}...")
            result = self.grok.generate_image(prompt, count=1)
            
            if result and isinstance(result, list) and len(result) > 0:
                image_url = result[0]
                image_urls.append(image_url)
                total_image_cost += 0.07
                print(f"  ✓ Image {i} generated: {image_url[:60]}...")
            else:
                print(f"  ✗ Image {i} failed")
                return {
                    "success": False,
                    "error": f"Image generation failed for image {i}",
                    "step": "grok_image_generation"
                }
        
        print(f"\n✓ All {num_images} images generated successfully!")
        print(f"  Total image cost: ${total_image_cost:.2f}")
        
        # Step 3: Create video from images with Intelligent Router
        print(f"\n{'='*70}")
        print("STEP 3: CREATING VIDEO WITH INTELLIGENT ROUTER")
        print("="*70)
        print(f"Stitching {num_images} images into {duration}s video...")
        print(f"Resolution: HD (1080p)")
        print(f"Format: Vertical (9:16 for Instagram/TikTok)")
        print(f"Transitions: Smooth slides")
        print(f"Music: {music_style}")
        print(f"Router will intelligently choose: MoviePy (free) or Creatomate ($0.05)")
        
        # Create vertical video for social media using intelligent router
        result = self.video_router.create_video(
            image_urls=image_urls,
            headline=headline,
            cta_text=cta_text,
            duration=duration,
            music_style=music_style
        )
        
        if not result.get("success"):
            error = result.get("error", "Unknown error")
            print(f"\n✗ Video creation failed: {error}")
            return {
                "success": False,
                "error": f"Video creation failed: {error}",
                "step": "video_router_creation",
                "images_generated": len(image_urls),
                "image_urls": image_urls,
                "image_cost": total_image_cost
            }
        
        video_url = result.get("video_url") or result.get("video_path")
        render_id = result.get("render_id", "local")
        video_cost = result.get("cost", 0)
        video_method = result.get("method", "unknown")
        
        total_cost = total_image_cost + video_cost
        
        print(f"\n✓ Video created successfully!")
        print(f"  Render ID: {render_id}")
        print(f"  Video URL: {video_url}")
        print(f"  Video cost: ${video_cost:.2f}")
        print(f"  Total cost: ${total_cost:.2f}")
        
        # Step 4: Copy video if output path specified and video is local
        if output_path and result.get('video_path'):
            print(f"\n{'='*70}")
            print("STEP 4: SAVING VIDEO")
            print("="*70)
            import shutil
            try:
                shutil.copy(result['video_path'], output_path)
                print(f"✓ Video saved to: {output_path}")
            except Exception as e:
                print(f"✗ Failed to save video: {e}")
        
        # Final summary
        print(f"\n{'='*70}")
        print("VIDEO AD CREATION COMPLETE!")
        print("="*70)
        print(f"✓ Images generated: {num_images}")
        print(f"✓ Video duration: {duration}s")
        print(f"✓ Total cost: ${total_cost:.2f}")
        print(f"✓ Video URL: {video_url}")
        print(f"\n📱 Ready to post on:")
        print(f"  • Instagram Reels")
        print(f"  • TikTok")
        print(f"  • YouTube Shorts")
        print(f"  • Facebook Stories")
        
        return {
            "success": True,
            "video_url": video_url,
            "render_id": render_id,
            "image_urls": image_urls,
            "num_images": num_images,
            "duration": duration,
            "costs": {
                "images": total_image_cost,
                "video": video_cost,
                "total": total_cost
            },
            "headline": headline,
            "cta": cta_text,
            "concept": concept
        }


def main():
    """CLI for video ad generation."""
    parser = argparse.ArgumentParser(
        description="Generate fitness video ads with AI images + video rendering"
    )
    
    parser.add_argument(
        "--concept",
        default="fitness transformation",
        help="Ad concept/theme (default: 'fitness transformation')"
    )
    
    parser.add_argument(
        "--headline",
        default="Transform Your Body",
        help="Main headline text for ad"
    )
    
    parser.add_argument(
        "--cta",
        default="Start Your Journey",
        help="Call-to-action text"
    )
    
    parser.add_argument(
        "--account",
        help="Social media account name (e.g., @boabfit)"
    )
    
    parser.add_argument(
        "--duration",
        type=float,
        default=15.0,
        help="Video duration in seconds (default: 15)"
    )
    
    parser.add_argument(
        "--images",
        type=int,
        default=4,
        help="Number of images to generate (default: 4)"
    )
    
    parser.add_argument(
        "--music",
        default="energetic",
        choices=["energetic", "motivational", "upbeat", "calm"],
        help="Background music style"
    )
    
    parser.add_argument(
        "--output",
        help="Local path to save video (e.g., ad_video.mp4)"
    )
    
    args = parser.parse_args()
    
    # Create generator
    generator = VideoAdGenerator()
    
    # Generate video ad
    result = generator.create_video_ad(
        concept=args.concept,
        headline=args.headline,
        cta_text=args.cta,
        account_name=args.account,
        duration=args.duration,
        num_images=args.images,
        music_style=args.music,
        output_path=args.output
    )
    
    if not result.get("success"):
        print(f"\n✗ Error: {result.get('error')}")
        sys.exit(1)
    
    print("\n✓ Success! Video ad is ready.")
    sys.exit(0)


if __name__ == "__main__":
    main()