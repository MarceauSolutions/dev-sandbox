#!/usr/bin/env python3
"""
MiniMax TTS API Client
For generating realistic AI voices that don't sound robotic.

MiniMax advantages over ElevenLabs:
- More natural cadence
- Better for organic/UGC content
- More realistic flow
- Great for fitness influencer voiceovers

Pricing: $5/month for 120 minutes
"""

import os
import httpx
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


class VoiceStyle(Enum):
    ENERGETIC = "energetic"  # High energy fitness content
    CALM = "calm"  # Meditation, stretching
    CONVERSATIONAL = "conversational"  # Natural talking
    MOTIVATIONAL = "motivational"  # Pump-up content
    INSTRUCTIONAL = "instructional"  # Tutorial style


class MiniMaxClient:
    """
    Client for MiniMax Text-to-Speech API.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY", "")
        self.api_url = api_url or os.getenv("MINIMAX_API_URL", "https://api.minimax.chat/v1")
        self.group_id = os.getenv("MINIMAX_GROUP_ID", "")
        self.client = httpx.AsyncClient(timeout=60.0)
        
        # Voice library - pre-configured voices
        self.voice_library = {
            "sarah_fitness": {
                "voice_id": "female_fitness_01",
                "description": "Energetic female fitness instructor",
                "style": VoiceStyle.ENERGETIC
            },
            "emma_calm": {
                "voice_id": "female_calm_01", 
                "description": "Calm female voice for yoga/meditation",
                "style": VoiceStyle.CALM
            },
            "fitness_coach": {
                "voice_id": "female_coach_01",
                "description": "Professional female fitness coach",
                "style": VoiceStyle.INSTRUCTIONAL
            }
        }
        
    async def close(self):
        await self.client.aclose()
    
    async def list_voices(self) -> Dict[str, Any]:
        """List available voices from MiniMax."""
        if not self.api_key:
            return {
                "success": False,
                "error": "API key not configured",
                "available_presets": list(self.voice_library.keys())
            }
            
        try:
            response = await self.client.get(
                f"{self.api_url}/voices",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            if response.status_code == 200:
                return {"success": True, "voices": response.json()}
            else:
                return {"success": False, "error": response.text}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def generate_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        voice_preset: Optional[str] = None,
        speed: float = 1.0,
        pitch: float = 1.0,
        output_path: Optional[str] = None,
        style: VoiceStyle = VoiceStyle.CONVERSATIONAL
    ) -> Dict[str, Any]:
        """
        Generate speech from text.
        
        Args:
            text: The text to convert to speech
            voice_id: Specific MiniMax voice ID
            voice_preset: Name of preset from voice_library
            speed: Speech speed (0.5-2.0)
            pitch: Voice pitch (0.5-2.0)
            output_path: Where to save the audio file
            style: Voice style for generation
        """
        # Resolve voice
        if voice_preset and voice_preset in self.voice_library:
            voice_config = self.voice_library[voice_preset]
            voice_id = voice_config["voice_id"]
            style = voice_config.get("style", style)
        
        if not self.api_key:
            logger.warning("MiniMax API key not configured")
            return {
                "success": False,
                "mock": True,
                "error": "API key not configured. Set MINIMAX_API_KEY environment variable.",
                "text": text,
                "would_use_voice": voice_id or "default",
                "style": style.value
            }
        
        try:
            # Build request
            payload = {
                "text": text,
                "voice_id": voice_id or "default",
                "speed": speed,
                "pitch": pitch,
                "model": "speech-01"  # MiniMax model
            }
            
            # Add style modifiers
            if style == VoiceStyle.ENERGETIC:
                payload["timber_weights"] = [{"voice_id": "energetic", "weight": 1}]
            elif style == VoiceStyle.CALM:
                payload["timber_weights"] = [{"voice_id": "calm", "weight": 1}]
            
            response = await self.client.post(
                f"{self.api_url}/text_to_speech",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Decode and save audio
                if output_path and "audio" in result:
                    audio_data = base64.b64decode(result["audio"])
                    with open(output_path, "wb") as f:
                        f.write(audio_data)
                    result["local_path"] = output_path
                    
                return {"success": True, **result}
            else:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"MiniMax TTS failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def clone_voice(
        self,
        audio_samples: List[str],
        voice_name: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Clone a voice from audio samples.
        Requires 30-60 seconds of clean audio.
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "API key not configured",
                "instructions": [
                    "1. Get 30-60 seconds of clean audio of the target voice",
                    "2. Upload to MiniMax voice cloning interface",
                    "3. Save the resulting voice_id",
                    "4. Add to voice_library for reuse"
                ]
            }
        
        try:
            # Read audio files
            audio_data = []
            for sample_path in audio_samples:
                with open(sample_path, "rb") as f:
                    audio_data.append(base64.b64encode(f.read()).decode())
            
            response = await self.client.post(
                f"{self.api_url}/voice_clone",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "audio_samples": audio_data,
                    "voice_name": voice_name,
                    "description": description
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Add to local library
                if "voice_id" in result:
                    self.voice_library[voice_name.lower().replace(" ", "_")] = {
                        "voice_id": result["voice_id"],
                        "description": description,
                        "style": VoiceStyle.CONVERSATIONAL,
                        "cloned": True
                    }
                    
                return {"success": True, **result}
            else:
                return {"success": False, "error": response.text}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_fitness_script(
        self,
        exercise: str,
        reps: int = 10,
        sets: int = 3,
        style: VoiceStyle = VoiceStyle.INSTRUCTIONAL
    ) -> str:
        """
        Generate a fitness voiceover script.
        """
        scripts = {
            VoiceStyle.INSTRUCTIONAL: f"""
Alright, let's do {exercise}. We're going for {reps} reps, {sets} sets.
Keep your core tight, and focus on your form.
Here we go - one, two, three... nice and controlled.
Keep breathing. You've got this.
""",
            VoiceStyle.ENERGETIC: f"""
Let's GO! Time for {exercise}! 
{reps} reps, {sets} sets - we're gonna crush this!
Keep that energy UP! One! Two! Three!
Don't stop now, you're doing AMAZING!
""",
            VoiceStyle.MOTIVATIONAL: f"""
You're about to do {exercise}. {reps} reps, {sets} sets.
Remember why you started. Every rep counts.
One rep at a time. You're stronger than you think.
This is where champions are made. Let's go.
"""
        }
        
        return scripts.get(style, scripts[VoiceStyle.INSTRUCTIONAL]).strip()


# Integration with ElevenLabs as fallback
class ElevenLabsClient:
    """Fallback client for ElevenLabs voice cloning."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY", "")
        self.api_url = "https://api.elevenlabs.io/v1"
        self.client = httpx.AsyncClient(timeout=60.0)
        
        # Julia's cloned voice (if available)
        self.julia_voice_id = os.getenv("ELEVENLABS_JULIA_VOICE_ID", "Dfq9xw2lqy9dGc5FIpi5")
        
    async def generate_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate speech using ElevenLabs."""
        if not self.api_key:
            return {"success": False, "error": "ElevenLabs API key not configured"}
            
        voice_id = voice_id or self.julia_voice_id
        
        try:
            response = await self.client.post(
                f"{self.api_url}/text-to-speech/{voice_id}",
                headers={
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "text": text,
                    "model_id": "eleven_monolingual_v1",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75
                    }
                }
            )
            
            if response.status_code == 200:
                if output_path:
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    return {"success": True, "local_path": output_path}
                else:
                    return {"success": True, "audio": base64.b64encode(response.content).decode()}
            else:
                return {"success": False, "error": response.text}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def close(self):
        await self.client.aclose()


# Unified TTS interface
class UnifiedTTSClient:
    """
    Unified interface for TTS with automatic fallback.
    Tries MiniMax first (more natural), falls back to ElevenLabs.
    """
    
    def __init__(self):
        self.minimax = MiniMaxClient()
        self.elevenlabs = ElevenLabsClient()
        
    async def generate_speech(
        self,
        text: str,
        voice_preset: Optional[str] = None,
        output_path: Optional[str] = None,
        prefer_elevenlabs: bool = False
    ) -> Dict[str, Any]:
        """
        Generate speech using the best available service.
        """
        if prefer_elevenlabs and self.elevenlabs.api_key:
            result = await self.elevenlabs.generate_speech(text, output_path=output_path)
            if result.get("success"):
                result["provider"] = "elevenlabs"
                return result
        
        # Try MiniMax first
        if self.minimax.api_key:
            result = await self.minimax.generate_speech(
                text,
                voice_preset=voice_preset,
                output_path=output_path
            )
            if result.get("success"):
                result["provider"] = "minimax"
                return result
        
        # Fallback to ElevenLabs
        if self.elevenlabs.api_key:
            result = await self.elevenlabs.generate_speech(text, output_path=output_path)
            if result.get("success"):
                result["provider"] = "elevenlabs"
                return result
        
        return {
            "success": False,
            "error": "No TTS service configured",
            "text": text
        }
    
    async def close(self):
        await self.minimax.close()
        await self.elevenlabs.close()


# Singleton instances
_minimax_client: Optional[MiniMaxClient] = None
_unified_client: Optional[UnifiedTTSClient] = None

def get_minimax_client() -> MiniMaxClient:
    global _minimax_client
    if _minimax_client is None:
        _minimax_client = MiniMaxClient()
    return _minimax_client

def get_tts_client() -> UnifiedTTSClient:
    global _unified_client
    if _unified_client is None:
        _unified_client = UnifiedTTSClient()
    return _unified_client


# Convenience functions
async def generate_fitness_voiceover(
    script: str,
    output_path: str,
    style: VoiceStyle = VoiceStyle.INSTRUCTIONAL
) -> Dict[str, Any]:
    """Generate a fitness voiceover."""
    client = get_tts_client()
    return await client.generate_speech(
        text=script,
        output_path=output_path
    )


async def generate_julia_voiceover(
    script: str,
    output_path: str
) -> Dict[str, Any]:
    """Generate voiceover using Julia's cloned voice (ElevenLabs)."""
    client = get_tts_client()
    return await client.generate_speech(
        text=script,
        output_path=output_path,
        prefer_elevenlabs=True  # Use ElevenLabs for Julia's cloned voice
    )


if __name__ == "__main__":
    async def test():
        client = get_minimax_client()
        
        # Test script generation
        script = client.create_fitness_script(
            exercise="squats",
            reps=10,
            sets=3,
            style=VoiceStyle.ENERGETIC
        )
        print("Generated script:")
        print(script)
        print()
        
        # Test voice list
        voices = await client.list_voices()
        print("Available voices:")
        print(voices)
        
    asyncio.run(test())
