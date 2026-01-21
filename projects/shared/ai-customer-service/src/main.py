"""
FastAPI application for Marceau Solutions API Gateway.

Serves multiple services:
1. Voice AI / Twilio webhooks (/twilio/*)
2. Multi-business form handling (/api/form/*)

All accessible via https://api.marceausolutions.com
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .twilio_handler import router as twilio_router
from .form_router import router as form_router

settings = get_settings()

app = FastAPI(
    title="Marceau Solutions API",
    description="Voice AI + Multi-Business Form Handler",
    version="0.2.0"
)

# CORS middleware - allow all websites to submit forms
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://marceausolutions.com",
        "https://www.marceausolutions.com",
        "https://swfloridacomfort.com",
        "https://www.swfloridacomfort.com",
        "https://squarefootshipping.com",
        "https://www.squarefootshipping.com",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "*",  # Allow all for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(twilio_router)  # Voice AI at /twilio/*
app.include_router(form_router)    # Forms at /api/form/*


@app.get("/")
async def root():
    """API Gateway root."""
    return {
        "service": "Marceau Solutions API",
        "version": "0.2.0",
        "status": "operational",
        "endpoints": {
            "voice_ai": "/twilio/*",
            "forms": "/api/form/*",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Detailed health check for all services."""
    return {
        "status": "healthy",
        "services": {
            "voice_ai": {
                "twilio_configured": bool(settings.twilio_account_sid),
                "anthropic_configured": bool(settings.anthropic_api_key),
                "deepgram_configured": bool(settings.deepgram_api_key),
            },
            "forms": {
                "enabled": True,
                "endpoint": "/api/form/submit"
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
