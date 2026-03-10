#!/usr/bin/env python3
"""
Seedance 2 API Client
For generating realistic full-body AI videos with natural motion.

Seedance 2 excels at:
- Realistic human motion
- Full body video generation
- Consistent character animation

Access methods:
- jimeng.jianying.com/ai-tool/home/
- doubao.com/chat/ (incognito mode)
- Direct API (if available)

Bypass for realistic faces:
"Make this character as a realistic 3D character in T-pose"
"""

import os
import httpx
import json
import asyncio
import base64
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
from enum import Enum

# Logging
try:
    from backend.logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class VideoQuality(Enum):
    FAST = "fast"  # 10s, lower quality
    STANDARD = "standard"  # 10s, standard quality
    HIGH = "high"  # 5-10s, high quality


class CameraMovement(Enum):
    STATIC = "static"
    PUSH_IN = "push_in"
    PULL_OUT = "pull_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    TRACKING = "tracking"
    HANDHELD = "handheld"


class SeedanceClient:
    """
    Client for Seedance 2 video generation.
    
    Note: Seedance 2 API access varies. This client supports:
    1. Direct API (if you have access)
    2. Proxy services
    3. Manual workflow assistance
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        use_proxy: bool = True
    ):
        self.api_key = api_key or os.getenv("SEEDANCE_API_KEY", "")
        self.api_url = api_url or os.getenv("SEEDANCE_API_URL", "")
        self.use_proxy = use_proxy
        self.client = httpx.AsyncClient(timeout=300.0)  # Long timeout for video gen
        
        # Proxy options
        self.proxy_urls = {
            "jimeng": "https://jimeng.jianying.com/ai-tool/home/",
            "doubao": "https://doubao.com/chat/",
            "kie": "https://kie.ai/"  # If they add Seedance support
        }
        
    async def close(self):
        await self.client.aclose()
    
    @staticmethod
    def apply_face_bypass(prompt: str) -> str:
        """
        Apply the Seedance 2 face bypass trick.
        When faces look too realistic, Seedance blocks it.
        This bypasses that restriction.
        """
        bypass_prefix = "realistic 3D character, "
        if "realistic 3D character" not in prompt.lower():
            return bypass_prefix + prompt
        return prompt
    
    @staticmethod
    def build_motion_prompt(
        subject_description: str,
        action: str,
        setting: str = "gym",
        duration_seconds: int = 10,
        camera_movement: CameraMovement = CameraMovement.STATIC,
        quality: VideoQuality = VideoQuality.STANDARD,
        additional_details: Dict[str, Any] = None
    ) -> str:
        """
        Build an optimized prompt for Seedance 2 video generation.
        """
        parts = []
        
        # Subject and action
        parts.append(subject_description)
        parts.append(action)
        
        # Setting
        parts.append(f"in {setting}")
        
        # Camera
        if camera_movement != CameraMovement.STATIC:
            camera_desc = camera_movement.value.replace("_", " ")
            parts.append(f"{camera_desc} camera movement")
        
        # Quality modifiers
        if quality == VideoQuality.HIGH:
            parts.extend(["high quality", "detailed", "smooth motion"])
        
        # Seedance-specific keywords for better results
        parts.extend([
            "natural human movement",
            "realistic physics",
            "proper body mechanics"
        ])
        
        # Additional details
        if additional_details:
            if "lighting" in additional_details:
                parts.append(f"{additional_details['lighting']} lighting")
            if "mood" in additional_details:
                parts.append(additional_details["mood"])
                
        return ", ".join(parts)
    
    @staticmethod
    def build_exercise_prompt(
        character_description: str,
        exercise: str,
        rep_count: int = 3,
        form_emphasis: bool = True
    ) -> str:
        """
        Build a prompt specifically for exercise demonstrations.
        """
        parts = [
            character_description,
            f"performing {exercise}",
            f"completing {rep_count} repetitions",
            "smooth controlled movement",
            "gym setting",
            "full body visible"
        ]
        
        if form_emphasis:
            parts.extend([
                "proper form",
                "correct posture",
                "controlled tempo"
            ])
            
        parts.extend([
            "natural lighting",
            "front view",
            "fitness video aesthetic"
        ])
        
        return ", ".join(parts)
    
    async def generate_video_from_image(
        self,
        image_path: str,
        motion_prompt: str,
        duration_seconds: int = 10,
        output_path: Optional[str] = None,
        apply_bypass: bool = True
    ) -> Dict[str, Any]:
        """
        Generate video from a starting image (Image-to-Video / I2V).
        This is the recommended workflow - 90% of projects should use I2V.
        """
        if apply_bypass:
            motion_prompt = self.apply_face_bypass(motion_prompt)
            
        if not self.api_key and not self.api_url:
            logger.warning("Seedance API not configured, returning workflow instructions")
            return {
                "success": False,
                "mock": True,
                "workflow": "manual",
                "instructions": self._get_manual_instructions(image_path, motion_prompt),
                "prompt": motion_prompt,
                "image_path": image_path
            }
        
        try:
            # Read image as base64
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
            
            response = await self.client.post(
                f"{self.api_url}/generate",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "image": image_data,
                    "prompt": motion_prompt,
                    "duration": duration_seconds,
                    "quality": "standard"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Save video if output path specified
                if output_path and "video_url" in result:
                    video_response = await self.client.get(result["video_url"])
                    with open(output_path, "wb") as f:
                        f.write(video_response.content)
                    result["local_path"] = output_path
                    
                return {"success": True, **result}
            else:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"Seedance generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_exercise_video(
        self,
        character_image_path: str,
        exercise: str,
        rep_count: int = 3,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate an exercise demonstration video.
        """
        # Build exercise-specific prompt
        prompt = self.build_exercise_prompt(
            character_description="Athletic woman",  # Will be overridden by image
            exercise=exercise,
            rep_count=rep_count,
            form_emphasis=True
        )
        
        return await self.generate_video_from_image(
            image_path=character_image_path,
            motion_prompt=prompt,
            duration_seconds=10,
            output_path=output_path
        )
    
    def _get_manual_instructions(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """
        Return manual instructions for generating video when API is not available.
        """
        return {
            "method": "manual",
            "steps": [
                {
                    "step": 1,
                    "action": "Open Seedance 2 interface",
                    "options": [
                        "https://jimeng.jianying.com/ai-tool/home/",
                        "https://doubao.com/chat/ (incognito mode)"
                    ]
                },
                {
                    "step": 2,
                    "action": "Upload starting image",
                    "image_path": image_path
                },
                {
                    "step": 3,
                    "action": "Enter the following prompt",
                    "prompt": prompt
                },
                {
                    "step": 4,
                    "action": "Set video parameters",
                    "settings": {
                        "duration": "10 seconds",
                        "quality": "fast" if "fast" in prompt.lower() else "standard"
                    }
                },
                {
                    "step": 5,
                    "action": "Generate and download video"
                }
            ],
            "tips": [
                "Use incognito mode to avoid account issues",
                "If face gets blocked, use the T-pose bypass trick",
                "Generate multiple variations and pick the best"
            ]
        }
    
    async def batch_generate(
        self,
        generations: List[Dict[str, Any]],
        parallel: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple videos from a list of specifications.
        
        Each item in generations should have:
        - image_path: str
        - prompt: str
        - output_path: Optional[str]
        """
        results = []
        
        if parallel:
            tasks = [
                self.generate_video_from_image(
                    image_path=gen["image_path"],
                    motion_prompt=gen["prompt"],
                    output_path=gen.get("output_path")
                )
                for gen in generations
            ]
            results = await asyncio.gather(*tasks)
        else:
            for gen in generations:
                result = await self.generate_video_from_image(
                    image_path=gen["image_path"],
                    motion_prompt=gen["prompt"],
                    output_path=gen.get("output_path")
                )
                results.append(result)
                
        return results


# Pre-built exercise prompts
EXERCISE_PROMPTS = {
    "squat": "performing barbell squat, lowering into deep squat position then standing up, smooth controlled movement, proper form, back straight",
    "deadlift": "performing deadlift, hinging at hips, lifting barbell from ground to standing, controlled descent",
    "pushup": "performing push-ups on mat, lowering chest to ground then pushing up, full range of motion",
    "lunge": "performing walking lunges, stepping forward into lunge position, alternating legs",
    "plank": "holding plank position, core engaged, body in straight line from head to heels",
    "bicep_curl": "performing dumbbell bicep curls, controlled movement, full contraction at top",
    "shoulder_press": "performing dumbbell shoulder press, pressing weights overhead, controlled descent",
    "hip_thrust": "performing hip thrusts on bench, driving hips up, squeezing glutes at top"
}


# Singleton client
_client: Optional[SeedanceClient] = None

def get_seedance_client() -> SeedanceClient:
    """Get or create Seedance client instance."""
    global _client
    if _client is None:
        _client = SeedanceClient()
    return _client


async def generate_workout_video(
    character_image: str,
    exercise: str,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Quick function to generate a workout video.
    """
    client = get_seedance_client()
    
    exercise_lower = exercise.lower().replace(" ", "_")
    prompt = EXERCISE_PROMPTS.get(exercise_lower)
    
    if not prompt:
        prompt = client.build_exercise_prompt(
            character_description="Athletic woman",
            exercise=exercise,
            rep_count=3
        )
    
    return await client.generate_video_from_image(
        image_path=character_image,
        motion_prompt=prompt,
        output_path=output_path
    )


if __name__ == "__main__":
    # Test the client
    async def test():
        client = get_seedance_client()
        
        # Test prompt building
        prompt = client.build_exercise_prompt(
            character_description="Athletic woman with brown hair",
            exercise="squat",
            rep_count=5
        )
        print("Exercise prompt:")
        print(prompt)
        
        # Test bypass
        bypassed = client.apply_face_bypass(prompt)
        print("\nWith bypass:")
        print(bypassed)
        
        # Test motion prompt
        motion = client.build_motion_prompt(
            subject_description="Fit woman in athletic wear",
            action="walking confidently towards camera",
            setting="modern gym",
            camera_movement=CameraMovement.TRACKING
        )
        print("\nMotion prompt:")
        print(motion)
        
    asyncio.run(test())
