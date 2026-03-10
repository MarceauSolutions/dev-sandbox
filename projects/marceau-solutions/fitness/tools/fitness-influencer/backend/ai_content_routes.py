#!/usr/bin/env python3
"""
AI Content Generation API Routes
FastAPI routes for the AI content generation pipeline.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

from backend.ai_content_generator import (
    get_content_generator,
    ContentType,
    ContentSpec,
    generate_julia_workout,
    generate_julia_talking
)
from backend.nanobanana_client import (
    get_nanobanana_client,
    CharacterProfile
)
from backend.seedance_client import (
    get_seedance_client,
    EXERCISE_PROMPTS
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


router = APIRouter(prefix="/api/ai-content", tags=["AI Content Generation"])


# Request/Response Models

class ContentTypeEnum(str, Enum):
    workout_demo = "workout_demo"
    talking_head = "talking_head"
    product_review = "product_review"
    lifestyle = "lifestyle"
    transformation = "transformation"
    testimonial = "testimonial"


class VoiceStyleEnum(str, Enum):
    energetic = "energetic"
    calm = "calm"
    conversational = "conversational"
    motivational = "motivational"
    instructional = "instructional"


class CharacterProfileCreate(BaseModel):
    """Request to create a character profile."""
    name: str = Field(..., description="Character name (e.g., 'julia')")
    description: str = Field(..., description="Character description")
    hair_color: str = Field(default="brown")
    hair_style: str = Field(default="long, wavy")
    skin_tone: str = Field(default="light")
    body_type: str = Field(default="athletic, fit")
    age_range: str = Field(default="25-30")
    distinctive_features: List[str] = Field(default=[])
    default_attire: str = Field(default="fitness attire")
    style_keywords: List[str] = Field(default=["fitness influencer", "natural lighting"])


class GenerateImageRequest(BaseModel):
    """Request to generate a character image."""
    character_name: str = Field(..., description="Name of stored character profile")
    scene_description: str = Field(..., description="What's happening in the scene")
    shot_type: str = Field(default="full body", description="full body, medium shot, close-up")
    setting: str = Field(default="gym", description="Location/environment")
    pose: str = Field(default="natural", description="Character pose")
    aspect_ratio: str = Field(default="9:16", description="9:16 for vertical, 16:9 for horizontal")


class GenerateVideoRequest(BaseModel):
    """Request to generate a video from image."""
    image_path: str = Field(..., description="Path to starting frame image")
    motion_prompt: str = Field(..., description="Description of motion/action")
    duration_seconds: int = Field(default=10, ge=5, le=25)
    apply_face_bypass: bool = Field(default=True, description="Apply Seedance face bypass trick")


class GenerateVoiceRequest(BaseModel):
    """Request to generate voiceover."""
    text: str = Field(..., description="Script to convert to speech")
    voice_preset: Optional[str] = Field(default=None, description="Voice preset name")
    voice_style: VoiceStyleEnum = Field(default=VoiceStyleEnum.conversational)
    speed: float = Field(default=1.0, ge=0.5, le=2.0)


class GenerateWorkoutRequest(BaseModel):
    """Request to generate complete workout content."""
    character_name: str = Field(default="julia")
    exercise: str = Field(..., description="Exercise name (e.g., 'squat', 'deadlift')")
    script: str = Field(..., description="Voiceover script")
    reps: int = Field(default=5, ge=1, le=20)
    setting: str = Field(default="modern gym")


class GenerateTalkingHeadRequest(BaseModel):
    """Request to generate talking head content."""
    character_name: str = Field(default="julia")
    script: str = Field(..., description="What the character says")
    topic: str = Field(default="fitness tips")
    setting: str = Field(default="home studio")


class GenerateProductReviewRequest(BaseModel):
    """Request to generate product review content."""
    character_name: str = Field(default="julia")
    product_name: str = Field(..., description="Name of product being reviewed")
    review_script: str = Field(..., description="Review voiceover script")
    setting: str = Field(default="home kitchen")


class BatchGenerateRequest(BaseModel):
    """Request to generate multiple pieces of content."""
    specs: List[Dict[str, Any]]


# Routes

@router.get("/status")
async def get_status():
    """Check status of AI content generation services."""
    nanobanana = get_nanobanana_client()
    seedance = get_seedance_client()
    tts = get_tts_client()
    
    return {
        "nanobanana": {
            "configured": bool(nanobanana.api_key),
            "characters_loaded": list(nanobanana.character_profiles.keys())
        },
        "seedance": {
            "configured": bool(seedance.api_key or seedance.api_url),
            "exercises_available": list(EXERCISE_PROMPTS.keys())
        },
        "tts": {
            "minimax_configured": bool(tts.minimax.api_key),
            "elevenlabs_configured": bool(tts.elevenlabs.api_key)
        }
    }


@router.get("/characters")
async def list_characters():
    """List available character profiles."""
    client = get_nanobanana_client()
    return {
        "characters": {
            name: profile.to_dict()
            for name, profile in client.character_profiles.items()
        }
    }


@router.post("/characters")
async def create_character(request: CharacterProfileCreate):
    """Create a new character profile."""
    client = get_nanobanana_client()
    
    profile = CharacterProfile(
        name=request.name,
        description=request.description,
        hair_color=request.hair_color,
        hair_style=request.hair_style,
        skin_tone=request.skin_tone,
        body_type=request.body_type,
        age_range=request.age_range,
        distinctive_features=request.distinctive_features,
        default_attire=request.default_attire,
        style_keywords=request.style_keywords
    )
    
    client.add_character_profile(profile)
    
    return {
        "success": True,
        "message": f"Character '{request.name}' created",
        "profile": profile.to_dict()
    }


@router.post("/generate/image")
async def generate_image(request: GenerateImageRequest):
    """Generate a character image for use as video starting frame."""
    client = get_nanobanana_client()
    
    result = await client.generate_character_image(
        character_name=request.character_name,
        scene_description=request.scene_description,
        shot_type=request.shot_type,
        setting=request.setting,
        pose=request.pose,
        aspect_ratio=request.aspect_ratio
    )
    
    return result


@router.post("/generate/video")
async def generate_video(request: GenerateVideoRequest):
    """Generate video from starting frame image."""
    client = get_seedance_client()
    
    result = await client.generate_video_from_image(
        image_path=request.image_path,
        motion_prompt=request.motion_prompt,
        duration_seconds=request.duration_seconds,
        apply_bypass=request.apply_face_bypass
    )
    
    return result


@router.post("/generate/voice")
async def generate_voice(request: GenerateVoiceRequest):
    """Generate voiceover from text."""
    client = get_tts_client()
    
    result = await client.generate_speech(
        text=request.text,
        voice_preset=request.voice_preset
    )
    
    return result


@router.post("/generate/workout")
async def generate_workout(
    request: GenerateWorkoutRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate complete workout demonstration content.
    Returns immediately with job ID, content generated in background.
    """
    generator = get_content_generator()
    
    # For now, run synchronously (can be moved to background task queue)
    result = await generator.generate_workout_content(
        character_name=request.character_name,
        exercise=request.exercise,
        script=request.script,
        reps=request.reps,
        setting=request.setting
    )
    
    return result


@router.post("/generate/talking-head")
async def generate_talking_head(request: GenerateTalkingHeadRequest):
    """Generate talking head / UGC style content."""
    generator = get_content_generator()
    
    result = await generator.generate_talking_head_content(
        character_name=request.character_name,
        script=request.script,
        topic=request.topic,
        setting=request.setting
    )
    
    return result


@router.post("/generate/product-review")
async def generate_product_review(request: GenerateProductReviewRequest):
    """Generate product review content."""
    generator = get_content_generator()
    
    result = await generator.generate_product_review(
        character_name=request.character_name,
        product_name=request.product_name,
        review_script=request.review_script,
        setting=request.setting
    )
    
    return result


@router.get("/exercises")
async def list_exercises():
    """List pre-configured exercise prompts."""
    return {
        "exercises": list(EXERCISE_PROMPTS.keys()),
        "prompts": EXERCISE_PROMPTS
    }


@router.get("/voice-styles")
async def list_voice_styles():
    """List available voice styles."""
    return {
        "styles": [style.value for style in VoiceStyle],
        "presets": {
            "energetic": "High energy fitness content",
            "calm": "Meditation, stretching, yoga",
            "conversational": "Natural talking, UGC style",
            "motivational": "Pump-up, inspirational",
            "instructional": "Tutorial, educational"
        }
    }


# Quick generation endpoints for Julia

@router.post("/julia/workout")
async def julia_workout(
    exercise: str,
    script: str,
    setting: str = "modern home gym"
):
    """Quick endpoint to generate Julia workout content."""
    result = await generate_julia_workout(
        exercise=exercise,
        script=script,
        setting=setting
    )
    return result


@router.post("/julia/talking")
async def julia_talking(
    script: str,
    topic: str = "fitness tips"
):
    """Quick endpoint to generate Julia talking head content."""
    result = await generate_julia_talking(
        script=script,
        topic=topic
    )
    return result
