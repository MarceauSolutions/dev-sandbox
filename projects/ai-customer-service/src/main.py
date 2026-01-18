"""FastAPI application for AI Customer Service."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .twilio_handler import router as twilio_router

settings = get_settings()

app = FastAPI(
    title="AI Customer Service",
    description="Voice AI ordering system for restaurants",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(twilio_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "AI Customer Service",
        "version": "0.1.0",
        "status": "operational"
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "twilio_configured": bool(settings.twilio_account_sid),
        "anthropic_configured": bool(settings.anthropic_api_key),
        "deepgram_configured": bool(settings.deepgram_api_key),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
