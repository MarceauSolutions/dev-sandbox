#!/usr/bin/env python3
"""
NanoBanana Pro API Client
For generating consistent AI character images.

NanoBanana Pro excels at:
- High prompt adherence
- Consistent character generation
- Detailed scene control via JSON prompts
"""

import os
import httpx
import json
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
import hashlib

# Logging
try:
    from backend.logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# Configuration
NANOBANANA_API_URL = os.getenv("NANOBANANA_API_URL", "https://api.nanobanana.pro/v1")
NANOBANANA_API_KEY = os.getenv("NANOBANANA_API_KEY", "")


class CharacterProfile:
    """Stores consistent character attributes for reuse."""
    
    def __init__(
        self,
        name: str,
        description: str,
        hair_color: str = "brown",
        hair_style: str = "long, wavy",
        skin_tone: str = "light",
        body_type: str = "athletic, fit",
        age_range: str = "25-30",
        distinctive_features: List[str] = None,
        default_attire: str = "fitness attire",
        style_keywords: List[str] = None
    ):
        self.name = name
        self.description = description
        self.hair_color = hair_color
        self.hair_style = hair_style
        self.skin_tone = skin_tone
        self.body_type = body_type
        self.age_range = age_range
        self.distinctive_features = distinctive_features or []
        self.default_attire = default_attire
        self.style_keywords = style_keywords or ["fitness influencer", "natural lighting", "iPhone quality"]
        self.created_at = datetime.now().isoformat()
        
    def to_prompt_segment(self) -> str:
        """Convert character profile to prompt segment."""
        features = ", ".join(self.distinctive_features) if self.distinctive_features else ""
        return f"""
{self.body_type} woman, age {self.age_range}, 
{self.hair_color} {self.hair_style} hair, 
{self.skin_tone} skin,
{features}
""".strip().replace("\n", " ")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "hair_color": self.hair_color,
            "hair_style": self.hair_style,
            "skin_tone": self.skin_tone,
            "body_type": self.body_type,
            "age_range": self.age_range,
            "distinctive_features": self.distinctive_features,
            "default_attire": self.default_attire,
            "style_keywords": self.style_keywords,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterProfile":
        profile = cls(
            name=data["name"],
            description=data["description"],
            hair_color=data.get("hair_color", "brown"),
            hair_style=data.get("hair_style", "long"),
            skin_tone=data.get("skin_tone", "light"),
            body_type=data.get("body_type", "athletic"),
            age_range=data.get("age_range", "25-30"),
            distinctive_features=data.get("distinctive_features", []),
            default_attire=data.get("default_attire", "fitness attire"),
            style_keywords=data.get("style_keywords", [])
        )
        profile.created_at = data.get("created_at", datetime.now().isoformat())
        return profile


class NanoBananaClient:
    """Client for NanoBanana Pro API."""
    
    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
        self.api_key = api_key or NANOBANANA_API_KEY
        self.api_url = api_url or NANOBANANA_API_URL
        self.client = httpx.AsyncClient(timeout=120.0)
        self.character_profiles: Dict[str, CharacterProfile] = {}
        
    async def close(self):
        await self.client.aclose()
        
    def add_character_profile(self, profile: CharacterProfile):
        """Store a character profile for reuse."""
        self.character_profiles[profile.name.lower()] = profile
        logger.info(f"Added character profile: {profile.name}")
        
    def get_character_profile(self, name: str) -> Optional[CharacterProfile]:
        """Get stored character profile."""
        return self.character_profiles.get(name.lower())
    
    def build_json_prompt(
        self,
        scene_description: str,
        character: Optional[CharacterProfile] = None,
        aspect_ratio: str = "9:16",
        shot_type: str = "full body",
        lighting: str = "natural, soft",
        setting: str = "modern gym",
        camera_angle: str = "eye level",
        additional_details: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Build a structured JSON prompt for NanoBanana.
        JSON method gives better prompt adherence.
        """
        prompt_data = {
            "scene": {
                "description": scene_description,
                "setting": setting,
                "lighting": lighting,
                "time_of_day": additional_details.get("time_of_day", "day") if additional_details else "day"
            },
            "subject": {
                "type": "person",
                "shot_type": shot_type,
                "camera_angle": camera_angle,
                "pose": additional_details.get("pose", "natural") if additional_details else "natural"
            },
            "technical": {
                "aspect_ratio": aspect_ratio,
                "quality": "high",
                "style": "photorealistic"
            }
        }
        
        if character:
            prompt_data["subject"]["character"] = {
                "description": character.to_prompt_segment(),
                "attire": character.default_attire,
                "expression": additional_details.get("expression", "confident, friendly") if additional_details else "confident, friendly"
            }
            prompt_data["technical"]["style_keywords"] = character.style_keywords
            
        if additional_details:
            prompt_data["additional"] = additional_details
            
        return prompt_data
    
    def json_to_text_prompt(self, json_prompt: Dict[str, Any]) -> str:
        """Convert JSON prompt to text prompt for API."""
        parts = []
        
        # Subject
        subject = json_prompt.get("subject", {})
        if "character" in subject:
            char = subject["character"]
            parts.append(char.get("description", ""))
            parts.append(f"wearing {char.get('attire', 'casual clothes')}")
            parts.append(f"expression: {char.get('expression', 'neutral')}")
        
        parts.append(f"{subject.get('shot_type', 'medium shot')}")
        parts.append(f"{subject.get('camera_angle', 'eye level')} angle")
        
        # Scene
        scene = json_prompt.get("scene", {})
        parts.append(f"in {scene.get('setting', 'studio')}")
        parts.append(f"{scene.get('lighting', 'natural')} lighting")
        parts.append(scene.get("description", ""))
        
        # Technical
        tech = json_prompt.get("technical", {})
        style_keywords = tech.get("style_keywords", [])
        if style_keywords:
            parts.extend(style_keywords)
        parts.append(f"{tech.get('quality', 'high')} quality")
        parts.append(tech.get("style", "photorealistic"))
        
        # Clean up and join
        parts = [p.strip() for p in parts if p and p.strip()]
        return ", ".join(parts)
    
    async def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "9:16",
        num_images: int = 1,
        negative_prompt: str = "blurry, distorted, low quality, text, watermark",
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate image using NanoBanana Pro.
        
        Note: This is a placeholder - actual API integration requires
        NanoBanana Pro API credentials and endpoint documentation.
        """
        if not self.api_key:
            logger.warning("NanoBanana API key not configured, returning mock response")
            return {
                "success": False,
                "error": "API key not configured",
                "mock": True,
                "prompt": prompt,
                "message": "Set NANOBANANA_API_KEY environment variable"
            }
        
        try:
            response = await self.client.post(
                f"{self.api_url}/generate",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "aspect_ratio": aspect_ratio,
                    "num_images": num_images,
                    "seed": seed
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"NanoBanana API error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"NanoBanana request failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_character_image(
        self,
        character_name: str,
        scene_description: str,
        shot_type: str = "full body",
        setting: str = "modern gym",
        pose: str = "standing, confident",
        aspect_ratio: str = "9:16",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate image of a stored character profile.
        """
        character = self.get_character_profile(character_name)
        if not character:
            return {
                "success": False,
                "error": f"Character profile '{character_name}' not found"
            }
        
        json_prompt = self.build_json_prompt(
            scene_description=scene_description,
            character=character,
            shot_type=shot_type,
            setting=setting,
            aspect_ratio=aspect_ratio,
            additional_details={"pose": pose, **kwargs}
        )
        
        text_prompt = self.json_to_text_prompt(json_prompt)
        logger.info(f"Generating image for {character_name}: {text_prompt[:100]}...")
        
        return await self.generate_image(
            prompt=text_prompt,
            aspect_ratio=aspect_ratio
        )
    
    async def generate_starting_frame_library(
        self,
        character_name: str,
        frame_types: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate a library of starting frames for video generation.
        """
        if frame_types is None:
            frame_types = [
                {"shot": "full body", "setting": "gym", "pose": "standing, looking at camera", "desc": "Ready to workout"},
                {"shot": "full body", "setting": "gym", "pose": "exercise start position, squat", "desc": "Squat start"},
                {"shot": "medium shot", "setting": "home", "pose": "talking to camera", "desc": "Talking head"},
                {"shot": "full body", "setting": "kitchen", "pose": "holding protein shake", "desc": "Product shot"},
                {"shot": "full body", "setting": "outdoors, park", "pose": "stretching", "desc": "Outdoor fitness"}
            ]
        
        results = []
        for frame in frame_types:
            result = await self.generate_character_image(
                character_name=character_name,
                scene_description=frame.get("desc", ""),
                shot_type=frame.get("shot", "full body"),
                setting=frame.get("setting", "gym"),
                pose=frame.get("pose", "natural")
            )
            result["frame_type"] = frame
            results.append(result)
            
        return results


# Pre-built character profiles
JULIA_PROFILE = CharacterProfile(
    name="Julia",
    description="Fitness influencer Julia Marceau",
    hair_color="brown",
    hair_style="long, wavy",
    skin_tone="light tan",
    body_type="athletic, fit, toned",
    age_range="24-28",
    distinctive_features=["bright smile", "fit physique", "energetic vibe"],
    default_attire="athletic wear, sports bra and leggings",
    style_keywords=[
        "fitness influencer aesthetic",
        "natural lighting",
        "iPhone quality",
        "Instagram ready",
        "vibrant and energetic"
    ]
)


# Singleton client instance
_client: Optional[NanoBananaClient] = None

def get_nanobanana_client() -> NanoBananaClient:
    """Get or create NanoBanana client instance."""
    global _client
    if _client is None:
        _client = NanoBananaClient()
        _client.add_character_profile(JULIA_PROFILE)
    return _client


# Convenience functions
async def generate_julia_image(
    scene: str,
    shot_type: str = "full body",
    setting: str = "gym",
    pose: str = "confident, ready to workout"
) -> Dict[str, Any]:
    """Quick function to generate Julia images."""
    client = get_nanobanana_client()
    return await client.generate_character_image(
        character_name="julia",
        scene_description=scene,
        shot_type=shot_type,
        setting=setting,
        pose=pose
    )


if __name__ == "__main__":
    # Test the client
    async def test():
        client = get_nanobanana_client()
        
        # Test prompt building
        prompt = client.build_json_prompt(
            scene_description="Demonstrating proper squat form",
            character=JULIA_PROFILE,
            shot_type="full body",
            setting="modern home gym",
            additional_details={"pose": "squat start position", "expression": "focused"}
        )
        
        print("JSON Prompt:")
        print(json.dumps(prompt, indent=2))
        print("\nText Prompt:")
        print(client.json_to_text_prompt(prompt))
        
    asyncio.run(test())
