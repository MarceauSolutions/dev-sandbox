#!/usr/bin/env python3
"""
AI Content Generator
Unified pipeline for generating full AI fitness influencer content.

Combines:
- NanoBanana Pro: Character images
- Seedance 2: Full-body video generation  
- MiniMax/ElevenLabs: Voice generation
- Our platform: Captions, overlays, export

Workflow:
1. Generate starting frame (NanoBanana)
2. Animate to video (Seedance 2)
3. Generate voiceover (MiniMax/ElevenLabs)
4. Add captions + overlays (Our platform)
5. Export for platforms
"""

import os
import asyncio
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Import our clients
from backend.nanobanana_client import (
    NanoBananaClient, 
    CharacterProfile, 
    get_nanobanana_client,
    JULIA_PROFILE
)
from backend.seedance_client import (
    SeedanceClient,
    get_seedance_client,
    EXERCISE_PROMPTS,
    CameraMovement
)
from backend.minimax_tts import (
    get_tts_client,
    VoiceStyle
)

# Logging
try:
    from backend.logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class ContentType(Enum):
    WORKOUT_DEMO = "workout_demo"
    TALKING_HEAD = "talking_head"
    PRODUCT_REVIEW = "product_review"
    LIFESTYLE = "lifestyle"
    TRANSFORMATION = "transformation"
    TESTIMONIAL = "testimonial"


@dataclass
class ContentSpec:
    """Specification for generating AI content."""
    content_type: ContentType
    character_name: str
    script: str
    exercise: Optional[str] = None
    setting: str = "gym"
    duration_seconds: int = 10
    voice_style: VoiceStyle = VoiceStyle.INSTRUCTIONAL
    aspect_ratio: str = "9:16"
    output_dir: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content_type": self.content_type.value,
            "character_name": self.character_name,
            "script": self.script,
            "exercise": self.exercise,
            "setting": self.setting,
            "duration_seconds": self.duration_seconds,
            "voice_style": self.voice_style.value,
            "aspect_ratio": self.aspect_ratio
        }


class AIContentGenerator:
    """
    Main pipeline for generating AI fitness content.
    """
    
    def __init__(self, output_base_dir: str = "./generated_content"):
        self.nanobanana = get_nanobanana_client()
        self.seedance = get_seedance_client()
        self.tts = get_tts_client()
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        
    async def close(self):
        """Cleanup all clients."""
        await self.seedance.close()
        await self.tts.close()
        
    def _get_output_dir(self, content_id: str) -> Path:
        """Create and return output directory for this content."""
        output_dir = self.output_base_dir / content_id
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
    
    async def generate_workout_content(
        self,
        character_name: str,
        exercise: str,
        script: str,
        reps: int = 5,
        setting: str = "modern gym"
    ) -> Dict[str, Any]:
        """
        Generate a complete workout demonstration video.
        
        Pipeline:
        1. Generate starting frame image
        2. Generate exercise video
        3. Generate voiceover
        4. Return all assets for final assembly
        """
        content_id = f"workout_{exercise}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir = self._get_output_dir(content_id)
        
        results = {
            "content_id": content_id,
            "content_type": ContentType.WORKOUT_DEMO.value,
            "exercise": exercise,
            "output_dir": str(output_dir),
            "steps": {}
        }
        
        # Step 1: Generate starting frame
        logger.info(f"Generating starting frame for {character_name} - {exercise}")
        
        pose = f"exercise start position for {exercise}, ready stance"
        image_result = await self.nanobanana.generate_character_image(
            character_name=character_name,
            scene_description=f"About to demonstrate {exercise}",
            shot_type="full body",
            setting=setting,
            pose=pose
        )
        results["steps"]["image_generation"] = image_result
        
        # For now, we'll use a placeholder image path if API not configured
        image_path = image_result.get("local_path") or output_dir / "starting_frame.png"
        
        # Step 2: Generate video
        logger.info(f"Generating workout video for {exercise}")
        
        motion_prompt = EXERCISE_PROMPTS.get(
            exercise.lower().replace(" ", "_"),
            self.seedance.build_exercise_prompt(
                character_description="Athletic woman",
                exercise=exercise,
                rep_count=reps
            )
        )
        
        video_path = output_dir / "workout_video.mp4"
        video_result = await self.seedance.generate_video_from_image(
            image_path=str(image_path),
            motion_prompt=motion_prompt,
            duration_seconds=10,
            output_path=str(video_path)
        )
        results["steps"]["video_generation"] = video_result
        
        # Step 3: Generate voiceover
        logger.info("Generating voiceover")
        
        audio_path = output_dir / "voiceover.mp3"
        audio_result = await self.tts.generate_speech(
            text=script,
            output_path=str(audio_path)
        )
        results["steps"]["audio_generation"] = audio_result
        
        # Step 4: Return assembly instructions
        results["assembly"] = {
            "video_path": str(video_path),
            "audio_path": str(audio_path),
            "image_path": str(image_path),
            "next_steps": [
                "Sync audio to video",
                "Add captions using caption_generator",
                "Add workout overlay using workout_overlays",
                "Export using platform_exporter"
            ]
        }
        
        # Save manifest
        manifest_path = output_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
            
        results["manifest_path"] = str(manifest_path)
        
        return results
    
    async def generate_talking_head_content(
        self,
        character_name: str,
        script: str,
        topic: str = "fitness tips",
        setting: str = "home studio"
    ) -> Dict[str, Any]:
        """
        Generate a talking head / UGC style video.
        """
        content_id = f"talking_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir = self._get_output_dir(content_id)
        
        results = {
            "content_id": content_id,
            "content_type": ContentType.TALKING_HEAD.value,
            "topic": topic,
            "output_dir": str(output_dir),
            "steps": {}
        }
        
        # Step 1: Generate image
        image_result = await self.nanobanana.generate_character_image(
            character_name=character_name,
            scene_description=f"Talking to camera about {topic}",
            shot_type="medium shot",
            setting=setting,
            pose="natural, engaging, looking at camera"
        )
        results["steps"]["image_generation"] = image_result
        
        image_path = output_dir / "starting_frame.png"
        
        # Step 2: Generate video with talking motion
        motion_prompt = f"""
Woman talking naturally to camera, 
engaging hand gestures, 
authentic expression, 
natural head movement,
iPhone selfie video aesthetic,
{setting} background
""".strip().replace("\n", " ")
        
        video_path = output_dir / "talking_video.mp4"
        video_result = await self.seedance.generate_video_from_image(
            image_path=str(image_path),
            motion_prompt=motion_prompt,
            duration_seconds=15,
            output_path=str(video_path)
        )
        results["steps"]["video_generation"] = video_result
        
        # Step 3: Generate voiceover
        audio_path = output_dir / "voiceover.mp3"
        audio_result = await self.tts.generate_speech(
            text=script,
            output_path=str(audio_path)
        )
        results["steps"]["audio_generation"] = audio_result
        
        results["assembly"] = {
            "video_path": str(video_path),
            "audio_path": str(audio_path),
            "image_path": str(image_path)
        }
        
        return results
    
    async def generate_product_review(
        self,
        character_name: str,
        product_name: str,
        review_script: str,
        setting: str = "home kitchen"
    ) -> Dict[str, Any]:
        """
        Generate a product review video.
        """
        content_id = f"review_{product_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir = self._get_output_dir(content_id)
        
        results = {
            "content_id": content_id,
            "content_type": ContentType.PRODUCT_REVIEW.value,
            "product": product_name,
            "output_dir": str(output_dir),
            "steps": {}
        }
        
        # Generate image holding product
        image_result = await self.nanobanana.generate_character_image(
            character_name=character_name,
            scene_description=f"Showing off {product_name}",
            shot_type="medium shot",
            setting=setting,
            pose=f"holding {product_name}, excited expression"
        )
        results["steps"]["image_generation"] = image_result
        
        image_path = output_dir / "starting_frame.png"
        
        # Generate video
        motion_prompt = f"""
Woman excitedly showing product to camera,
demonstrating {product_name},
natural gestures,
authentic enthusiasm,
UGC product review style
"""
        
        video_path = output_dir / "review_video.mp4"
        video_result = await self.seedance.generate_video_from_image(
            image_path=str(image_path),
            motion_prompt=motion_prompt,
            duration_seconds=15,
            output_path=str(video_path)
        )
        results["steps"]["video_generation"] = video_result
        
        # Generate voiceover
        audio_path = output_dir / "voiceover.mp3"
        audio_result = await self.tts.generate_speech(
            text=review_script,
            output_path=str(audio_path)
        )
        results["steps"]["audio_generation"] = audio_result
        
        results["assembly"] = {
            "video_path": str(video_path),
            "audio_path": str(audio_path),
            "image_path": str(image_path)
        }
        
        return results
    
    async def batch_generate(
        self,
        specs: List[ContentSpec]
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple pieces of content.
        """
        results = []
        
        for spec in specs:
            try:
                if spec.content_type == ContentType.WORKOUT_DEMO:
                    result = await self.generate_workout_content(
                        character_name=spec.character_name,
                        exercise=spec.exercise or "general workout",
                        script=spec.script,
                        setting=spec.setting
                    )
                elif spec.content_type == ContentType.TALKING_HEAD:
                    result = await self.generate_talking_head_content(
                        character_name=spec.character_name,
                        script=spec.script,
                        setting=spec.setting
                    )
                elif spec.content_type == ContentType.PRODUCT_REVIEW:
                    result = await self.generate_product_review(
                        character_name=spec.character_name,
                        product_name=spec.exercise or "product",  # Reusing exercise field
                        review_script=spec.script,
                        setting=spec.setting
                    )
                else:
                    result = {"error": f"Unknown content type: {spec.content_type}"}
                    
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to generate content: {e}")
                results.append({"error": str(e), "spec": spec.to_dict()})
                
        return results


# Singleton instance
_generator: Optional[AIContentGenerator] = None

def get_content_generator() -> AIContentGenerator:
    global _generator
    if _generator is None:
        _generator = AIContentGenerator()
    return _generator


# Convenience functions
async def generate_julia_workout(
    exercise: str,
    script: str,
    setting: str = "modern home gym"
) -> Dict[str, Any]:
    """Quick function to generate Julia workout content."""
    generator = get_content_generator()
    return await generator.generate_workout_content(
        character_name="julia",
        exercise=exercise,
        script=script,
        setting=setting
    )


async def generate_julia_talking(
    script: str,
    topic: str = "fitness tips"
) -> Dict[str, Any]:
    """Quick function to generate Julia talking head content."""
    generator = get_content_generator()
    return await generator.generate_talking_head_content(
        character_name="julia",
        script=script,
        topic=topic
    )


if __name__ == "__main__":
    async def test():
        generator = get_content_generator()
        
        # Test workout content generation
        result = await generator.generate_workout_content(
            character_name="julia",
            exercise="squat",
            script="""
Let's work on your squat form. 
Keep your chest up, core tight, and push through your heels.
Going down... and up. That's one rep.
Keep going, you've got this!
""",
            setting="modern home gym"
        )
        
        print("Workout content generation result:")
        print(json.dumps(result, indent=2, default=str))
        
    asyncio.run(test())
