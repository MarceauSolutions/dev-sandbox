"""Configuration management for AI Customer Service."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "AI Customer Service"
    debug: bool = False

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    # LLM
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    default_llm: str = "anthropic"  # anthropic or openai

    # Speech-to-Text
    deepgram_api_key: str = ""

    # Text-to-Speech
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Default: Rachel

    # Database
    database_url: str = "sqlite:///./ai_customer_service.db"

    # Billing
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    base_url: str = "https://cuddly-bryn-fiduciarily.ngrok-free.dev"

    class Config:
        env_file = str(Path(__file__).parent.parent.parent.parent / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
