#!/usr/bin/env python3
"""
website_builder_api.py - FastAPI Backend for Website Builder

Provides REST API for the website builder workflow:

Basic Workflow:
1. POST /api/research - Research company and owner
2. POST /api/generate - Generate content from research
3. POST /api/build - Build static site
4. POST /api/workflow - Full end-to-end workflow

Enhanced Social Research Workflow:
1. POST /api/research/social - Research with social media profiles
2. POST /api/generate/personality - Generate personality-driven content
3. POST /api/build/personality - Build personality-styled site
4. POST /api/workflow/social - Full social research workflow

Usage:
    uvicorn website_builder_api:app --reload --host 0.0.0.0 --port 8001
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Import our modules
from research_engine import ResearchEngine
from content_generator import ContentGenerator
from site_builder import SiteBuilder

load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="Website Builder AI",
    description="AI-powered website generation from company research",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
SCRIPTS_PATH = Path(__file__).parent
OUTPUT_PATH = Path(tempfile.gettempdir()) / "website_builder"
OUTPUT_PATH.mkdir(exist_ok=True)

# Initialize engines
research_engine = ResearchEngine()
content_generator = ContentGenerator()
site_builder = SiteBuilder()

# Session storage (in production, use Redis or database)
sessions: Dict[str, Dict[str, Any]] = {}


# ==============================================================================
# Models
# ==============================================================================

class ResearchRequest(BaseModel):
    company_name: str
    owner_name: str
    location: Optional[str] = None


class GenerateRequest(BaseModel):
    session_id: str


class BuildRequest(BaseModel):
    session_id: str


class WorkflowRequest(BaseModel):
    company_name: str
    owner_name: str
    location: Optional[str] = None


class SocialResearchRequest(BaseModel):
    """Request for social media enhanced research."""
    company_name: str
    owner_name: str
    location: Optional[str] = None
    social_profiles: Dict[str, str] = Field(
        default={},
        description="Social profile URLs: {'x': 'url', 'linkedin': 'url', 'instagram': 'url'}"
    )
    enable_web_search: bool = Field(
        default=True,
        description="Enable web search for additional context"
    )
    user_preferences: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional brand preferences to override AI suggestions"
    )


class SocialWorkflowRequest(BaseModel):
    """Request for full social research workflow."""
    company_name: str
    owner_name: str
    location: Optional[str] = None
    social_profiles: Dict[str, str] = Field(
        default={},
        description="Social profile URLs"
    )
    enable_web_search: bool = True
    user_preferences: Optional[Dict[str, Any]] = None


# ==============================================================================
# API Endpoints - Basic
# ==============================================================================

@app.post("/api/research")
async def research_company(request: ResearchRequest):
    """
    Research a company and owner.

    Returns session_id to use for subsequent steps.
    """
    try:
        # Perform research
        research = research_engine.research_company(
            request.company_name,
            request.owner_name,
            request.location
        )

        # Create session
        session_id = f"wb_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        sessions[session_id] = {
            "research": research_engine.to_dict(research),
            "content": None,
            "files": None,
            "created_at": datetime.now().isoformat()
        }

        return {
            "session_id": session_id,
            "research": sessions[session_id]["research"],
            "next_step": "POST /api/generate with session_id"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate")
async def generate_content(request: GenerateRequest):
    """
    Generate website content from research.

    Requires session_id from /api/research.
    """
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[request.session_id]
    if not session.get("research"):
        raise HTTPException(status_code=400, detail="Research not completed")

    try:
        # Generate content
        content = content_generator.generate_content(session["research"])

        # Update session
        session["content"] = content_generator.to_dict(content)

        return {
            "session_id": request.session_id,
            "content": session["content"],
            "next_step": "POST /api/build with session_id"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/build")
async def build_site(request: BuildRequest):
    """
    Build static website from research and content.

    Requires session_id with completed research and content.
    """
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[request.session_id]
    if not session.get("research"):
        raise HTTPException(status_code=400, detail="Research not completed")
    if not session.get("content"):
        raise HTTPException(status_code=400, detail="Content not generated")

    try:
        # Build site
        output_dir = OUTPUT_PATH / request.session_id
        files = site_builder.build_site(
            session["research"],
            session["content"],
            str(output_dir)
        )

        # Update session
        session["files"] = files

        return {
            "session_id": request.session_id,
            "files": list(files.keys()),
            "preview_url": f"/preview/{request.session_id}/index.html",
            "download_url": f"/api/download/{request.session_id}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/workflow")
async def full_workflow(request: WorkflowRequest):
    """
    Complete end-to-end workflow.

    Research → Generate → Build in one call.
    """
    try:
        # 1. Research
        research = research_engine.research_company(
            request.company_name,
            request.owner_name,
            request.location
        )
        research_dict = research_engine.to_dict(research)

        # 2. Generate content
        content = content_generator.generate_content(research_dict)
        content_dict = content_generator.to_dict(content)

        # 3. Build site
        session_id = f"wb_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir = OUTPUT_PATH / session_id
        files = site_builder.build_site(
            research_dict,
            content_dict,
            str(output_dir)
        )

        # Store session
        sessions[session_id] = {
            "research": research_dict,
            "content": content_dict,
            "files": files,
            "created_at": datetime.now().isoformat()
        }

        return {
            "session_id": session_id,
            "company": request.company_name,
            "owner": request.owner_name,
            "template": research_dict.get("recommended_template", "business"),
            "sections": research_dict.get("suggested_sections", []),
            "files": list(files.keys()),
            "preview_url": f"/preview/{session_id}/index.html",
            "download_url": f"/api/download/{session_id}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get session data."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    return sessions[session_id]


@app.get("/api/download/{session_id}")
async def download_site(session_id: str):
    """Download generated site as ZIP."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    if not session.get("files"):
        raise HTTPException(status_code=400, detail="Site not built")

    try:
        # Create ZIP
        output_dir = OUTPUT_PATH / session_id
        zip_path = OUTPUT_PATH / f"{session_id}.zip"
        shutil.make_archive(str(zip_path.with_suffix("")), "zip", output_dir)

        return FileResponse(
            str(zip_path),
            filename=f"website_{session_id}.zip",
            media_type="application/zip"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/preview/{session_id}/{filename}")
async def preview_file(session_id: str, filename: str):
    """Preview generated file."""
    file_path = OUTPUT_PATH / session_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(str(file_path))


# ==============================================================================
# API Endpoints - Enhanced Social Research
# ==============================================================================

@app.post("/api/research/social")
async def research_with_social(request: SocialResearchRequest):
    """
    Research a company using social media profiles.

    Enhanced research that analyzes social profiles to understand:
    - Communication style and tone
    - Brand personality
    - Visual identity preferences
    - Content strategy recommendations

    Returns session_id with enriched research data.
    """
    if not request.social_profiles:
        raise HTTPException(
            status_code=400,
            detail="At least one social profile URL is required"
        )

    try:
        # Perform enhanced research
        research = research_engine.research_with_social(
            company_name=request.company_name,
            owner_name=request.owner_name,
            social_profiles=request.social_profiles,
            location=request.location,
            enable_web_search=request.enable_web_search,
            user_preferences=request.user_preferences
        )

        # Create session
        session_id = f"wb_social_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        research_dict = research_engine.to_dict(research)

        sessions[session_id] = {
            "research": research_dict,
            "content": None,
            "files": None,
            "workflow_type": "social",
            "created_at": datetime.now().isoformat()
        }

        return {
            "session_id": session_id,
            "workflow_type": "social",
            "research": research_dict,
            "brand_personality": research_dict.get("brand_personality"),
            "research_sources": research_dict.get("research_sources", []),
            "confidence_score": research_dict.get("confidence_score", 0.5),
            "next_step": "POST /api/generate/personality with session_id"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate/personality")
async def generate_personality_content(request: GenerateRequest):
    """
    Generate personality-driven website content.

    Uses brand personality data to create content that matches:
    - Brand voice and tone
    - Communication style
    - Content strategy guidelines
    - Audience pain points and desires
    """
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[request.session_id]
    if not session.get("research"):
        raise HTTPException(status_code=400, detail="Research not completed")

    try:
        # Generate personality-driven content
        content = content_generator.generate_personality_content(session["research"])

        # Update session
        session["content"] = content_generator.to_dict(content)

        return {
            "session_id": request.session_id,
            "content": session["content"],
            "next_step": "POST /api/build/personality with session_id"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/build/personality")
async def build_personality_site(request: BuildRequest):
    """
    Build website with personality-driven styling.

    Uses visual identity from brand personality to customize:
    - Typography and fonts
    - Border radius and shapes
    - Shadow intensity
    - Animation levels
    - Color scheme
    """
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[request.session_id]
    if not session.get("research"):
        raise HTTPException(status_code=400, detail="Research not completed")
    if not session.get("content"):
        raise HTTPException(status_code=400, detail="Content not generated")

    try:
        # Build personality-styled site
        output_dir = OUTPUT_PATH / request.session_id
        files = site_builder.build_personality_site(
            session["research"],
            session["content"],
            str(output_dir)
        )

        # Update session
        session["files"] = files

        return {
            "session_id": request.session_id,
            "files": list(files.keys()),
            "preview_url": f"/preview/{request.session_id}/index.html",
            "download_url": f"/api/download/{request.session_id}",
            "visual_identity": session["research"].get("brand_personality", {}).get("visual_identity", {})
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/workflow/social")
async def social_workflow(request: SocialWorkflowRequest):
    """
    Complete social research workflow.

    Full pipeline:
    1. Analyze social media profiles
    2. Gather web context (reviews, news, competitors)
    3. Synthesize brand personality
    4. Generate personality-driven content
    5. Build personality-styled website

    Returns complete website matching owner's social presence.
    """
    if not request.social_profiles:
        raise HTTPException(
            status_code=400,
            detail="At least one social profile URL is required"
        )

    try:
        # 1. Enhanced research with social profiles
        research = research_engine.research_with_social(
            company_name=request.company_name,
            owner_name=request.owner_name,
            social_profiles=request.social_profiles,
            location=request.location,
            enable_web_search=request.enable_web_search,
            user_preferences=request.user_preferences
        )
        research_dict = research_engine.to_dict(research)

        # 2. Generate personality-driven content
        content = content_generator.generate_personality_content(research_dict)
        content_dict = content_generator.to_dict(content)

        # 3. Build personality-styled site
        session_id = f"wb_social_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir = OUTPUT_PATH / session_id
        files = site_builder.build_personality_site(
            research_dict,
            content_dict,
            str(output_dir)
        )

        # Store session
        sessions[session_id] = {
            "research": research_dict,
            "content": content_dict,
            "files": files,
            "workflow_type": "social",
            "created_at": datetime.now().isoformat()
        }

        # Extract key personality info for response
        personality = research_dict.get("brand_personality", {})

        return {
            "session_id": session_id,
            "workflow_type": "social",
            "company": request.company_name,
            "owner": request.owner_name,

            # Personality summary
            "brand_name": personality.get("brand_name", request.company_name),
            "tagline": personality.get("tagline", ""),
            "tone": personality.get("voice", {}).get("tone", "professional"),
            "confidence_score": research_dict.get("confidence_score", 0.5),
            "research_sources": research_dict.get("research_sources", []),

            # Visual identity
            "visual_identity": personality.get("visual_identity", {}),

            # Files
            "files": list(files.keys()),
            "preview_url": f"/preview/{session_id}/index.html",
            "download_url": f"/api/download/{session_id}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# Health & Info
# ==============================================================================

@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "anthropic": os.getenv("ANTHROPIC_API_KEY") is not None,
        "active_sessions": len(sessions),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """API info."""
    return {
        "name": "Website Builder AI",
        "version": "0.2.0",
        "description": "AI-powered website generation with social media personality matching",
        "workflows": {
            "basic": {
                "description": "Basic AI research and generation",
                "endpoints": {
                    "research": "POST /api/research",
                    "generate": "POST /api/generate",
                    "build": "POST /api/build",
                    "workflow": "POST /api/workflow"
                }
            },
            "social": {
                "description": "Enhanced social media research with personality matching",
                "endpoints": {
                    "research": "POST /api/research/social",
                    "generate": "POST /api/generate/personality",
                    "build": "POST /api/build/personality",
                    "workflow": "POST /api/workflow/social"
                }
            }
        },
        "utility_endpoints": {
            "session": "GET /api/session/{id}",
            "download": "GET /api/download/{id}",
            "preview": "GET /preview/{id}/index.html",
            "health": "GET /health"
        },
        "example_social_workflow": {
            "endpoint": "POST /api/workflow/social",
            "body": {
                "company_name": "Project Evolve",
                "owner_name": "Jake Raleigh",
                "location": "Naples, FL",
                "social_profiles": {
                    "x": "https://x.com/projectevolve",
                    "instagram": "https://instagram.com/projectevolve"
                }
            }
        }
    }


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("WEBSITE BUILDER AI - API")
    print("=" * 60)
    print(f"\nAPI: http://localhost:8001")
    print(f"Docs: http://localhost:8001/docs")
    print(f"\nAnthropic API: {'Connected' if os.getenv('ANTHROPIC_API_KEY') else 'Not configured'}")
    print("=" * 60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8001)
