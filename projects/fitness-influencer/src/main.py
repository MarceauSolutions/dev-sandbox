#!/usr/bin/env python3
"""
Fitness Assistant API Wrapper
FastAPI server to expose fitness influencer tools as REST endpoints.

This allows your Replit app to interact with the assistant via HTTP requests.

Usage:
    pip install fastapi uvicorn python-multipart
    python execution/fitness_assistant_api.py

    # Or with uvicorn:
    uvicorn execution.fitness_assistant_api:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import subprocess
import os
from pathlib import Path
import tempfile
import shutil
import uuid
import time

# Structured logging (v2.0)
from backend.logging_config import setup_logging, get_logger
from backend.middleware import setup_middleware

# Rate limiting (v2.0)
from backend.rate_limiter import (
    limiter,
    rate_limit_exceeded_handler,
    check_quota,
    get_quota_status,
    require_quota,
    get_rate_limit_headers,
    Tier
)
from slowapi.errors import RateLimitExceeded

# Gamification routes (v2.0)
from backend.gamification_routes import router as gamification_router

# Task management routes (v2.0)
from backend.tasks_routes import router as tasks_router

# SMS routes — hybrid n8n + Python (v2.1)
from backend.sms_routes import router as sms_router

# Collaborator management routes (v2.1)
from backend.collaborators_routes import router as collaborators_router

# Branded PDF generation routes (v2.2)
from backend.pdf_routes import router as pdf_router

# Document serving routes (v2.3)
from backend.docs_routes import router as docs_router

# Client portal routes (v2.4)
from backend.client_routes import router as client_router
from backend.workout_routes import router as workout_router

# Initialize structured JSON logging
setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="Fitness Influencer Assistant API",
    description="AI-powered fitness content creation and automation",
    version="2.0.0"
)

# Add rate limiter to app state and register error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Enable CORS for Replit app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Replit app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add structured logging and performance monitoring middleware (v2.0)
setup_middleware(app)

# Include gamification routes (v2.0)
app.include_router(gamification_router)

# Include task management routes (v2.0)
app.include_router(tasks_router)

# Include SMS routes — hybrid n8n + Python (v2.1)
app.include_router(sms_router)

# Include collaborator management routes (v2.1)
app.include_router(collaborators_router)

# Include branded PDF generation routes (v2.2)
app.include_router(pdf_router)

# Include document serving routes (v2.3)
app.include_router(docs_router)

# Include client portal routes (v2.4)
app.include_router(client_router)
app.include_router(workout_router)

# Base path for execution scripts
SCRIPTS_PATH = Path(__file__).parent
PROJECT_PATH = SCRIPTS_PATH.parent  # fitness-influencer root

# Create static directory for processed videos
STATIC_PATH = SCRIPTS_PATH / "static"
VIDEOS_PATH = STATIC_PATH / "videos"
VIDEOS_PATH.mkdir(parents=True, exist_ok=True)

# Frontend path for HTML files
FRONTEND_PATH = PROJECT_PATH / "frontend"

# Mount static files for video downloads
app.mount("/static", StaticFiles(directory=str(STATIC_PATH)), name="static")

# Mount client portal SPA (v2.4 — must be before /frontend mount)
CLIENT_PATH = PROJECT_PATH / "client"
if CLIENT_PATH.exists():
    app.mount("/client", StaticFiles(directory=str(CLIENT_PATH), html=True), name="client")

# Mount frontend assets (CSS, JS) for dashboard
app.mount("/frontend", StaticFiles(directory=str(FRONTEND_PATH)), name="frontend")


# Route modules extracted from main.py monolith
from routes.video_routes import router as video_router
from routes.analysis_routes import router as analysis_router
from routes.content_routes import router as content_router
from routes.overlay_routes import router as overlay_router
from routes.lead_routes import router as lead_router
from routes.infra_routes import router as infra_router

# Register extracted route modules
app.include_router(video_router)
app.include_router(analysis_router)
app.include_router(content_router)
app.include_router(overlay_router)
app.include_router(lead_router)
app.include_router(infra_router)

# ============================================================================
# Frontend Routes
# ============================================================================

@app.get("/dashboard")
async def dashboard_page():
    """Serve the main dashboard SPA."""
    dashboard_html = FRONTEND_PATH / "index.html"
    if dashboard_html.exists():
        return FileResponse(dashboard_html, media_type="text/html")
    raise HTTPException(status_code=404, detail="Dashboard not found")


@app.get("/portal")
async def client_portal_page():
    """Serve the client portal SPA."""
    client_html = CLIENT_PATH / "index.html"
    if client_html.exists():
        return FileResponse(client_html, media_type="text/html")
    raise HTTPException(status_code=404, detail="Client portal not found")


@app.get("/gamification")
async def gamification_page():
    """Serve the gamification dashboard HTML page."""
    gamification_html = FRONTEND_PATH / "gamification.html"
    if gamification_html.exists():
        return FileResponse(gamification_html, media_type="text/html")
    raise HTTPException(status_code=404, detail="Gamification page not found")



# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """API health check and info."""
    return {
        "name": "Fitness Influencer Assistant API",
        "status": "active",
        "version": "2.0.0",
        "ai_providers": {
            "anthropic": bool(os.getenv('ANTHROPIC_API_KEY')),
            "xai": bool(os.getenv('XAI_API_KEY')),
            "shotstack": bool(os.getenv('SHOTSTACK_API_KEY'))
        },
        "endpoints": {
            "ai_chat": "/api/ai/chat",
            "video_edit": "/api/video/edit",
            "video_generate": "/api/video/generate (hybrid: MoviePy free → Creatomate paid)",
            "video_stats": "/api/video/stats",
            "video_providers": "/api/video/providers",
            "create_graphic": "/api/graphics/create",
            "email_digest": "/api/email/digest",
            "revenue_report": "/api/analytics/revenue",
            "generate_image": "/api/images/generate"
        },
        "v2_endpoints": {
            "job_submit": "/api/jobs/submit",
            "job_status": "/api/jobs/{job_id}/status",
            "job_cancel": "/api/jobs/{job_id}/cancel",
            "job_list": "/api/jobs",
            "video_caption": "/api/video/caption",
            "video_reframe": "/api/video/reframe",
            "video_export": "/api/video/export",
            "video_export_batch": "/api/video/export/batch",
            "video_export_platforms": "/api/video/export/platforms",
            "video_remove_fillers": "/api/video/remove-fillers",
            "video_detect_fillers": "/api/video/detect-fillers",
            "video_analyze": "/api/video/analyze",
            "video_viral_moments": "/api/video/viral-moments",
            "video_analyze_hook": "/api/video/analyze-hook",
            "video_predict_retention": "/api/video/predict-retention",
            "video_workout_overlay": "/api/video/add-workout-overlay",
            "video_form_annotations": "/api/video/add-form-annotations",
            "video_detect_exercise": "/api/video/detect-exercise",
            "content_metadata": "/api/content/metadata",
            "quota_status": "/api/quota/status",
            "quota_tiers": "/api/quota/tiers",
            "transcription": "/api/transcription"
        }
    }




if __name__ == "__main__":
    import uvicorn

    print("="*70)
    print("FITNESS INFLUENCER ASSISTANT API")
    print("="*70)
    print("\nStarting server...")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/api/status")
    print("\nPress CTRL+C to stop")
    print("="*70 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
