#!/usr/bin/env python3
"""
Interview Prep PowerPoint API
FastAPI REST API for interview preparation PowerPoint generation.

Endpoints:
    POST /api/research          - Research company and role
    POST /api/generate          - Generate PowerPoint from research
    POST /api/edit/text         - Edit text on a slide
    POST /api/edit/add-slide    - Add new slide with image
    POST /api/edit/regenerate   - Regenerate slide image
    GET  /api/slides            - List all slides
    GET  /api/download/{file}   - Download generated file
    GET  /api/status            - Check API status
    GET  /api/session           - Get current session info
    POST /api/session/close     - Close current session
    GET  /api/session/history   - List recent sessions

Session-based editing allows users to make iterative changes to their
presentation without specifying the file path each time.
"""

import os
import sys
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import session manager
try:
    from session_manager import (
        create_session, get_active_session, get_current_pptx,
        get_current_pptx_name, log_edit, update_slide_count,
        close_session, get_session_summary, list_recent_sessions,
        load_session
    )
    SESSION_ENABLED = True
except ImportError:
    SESSION_ENABLED = False

app = FastAPI(
    title="Interview Prep PowerPoint API",
    description="AI-powered interview preparation and PowerPoint generation",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = Path(__file__).parent.parent
SRC_DIR = Path(__file__).parent
TMP_DIR = BASE_DIR / ".tmp"
TMP_DIR.mkdir(exist_ok=True)


# Request/Response Models
class ResearchRequest(BaseModel):
    company: str
    role: str
    generate_images: Optional[bool] = False


class GenerateRequest(BaseModel):
    research_file: str
    theme: Optional[str] = "modern"


class EditTextRequest(BaseModel):
    pptx_file: str
    slide_number: int
    find_text: str
    replace_text: str
    match_all: Optional[bool] = False


class AddSlideRequest(BaseModel):
    pptx_file: str
    title: str
    description: str
    relevance: str
    after_slide: Optional[int] = None
    image_prompt: Optional[str] = None  # For AI generation


class RegenerateImageRequest(BaseModel):
    pptx_file: str
    slide_number: int
    prompt: str
    image_index: Optional[int] = 0


class StatusResponse(BaseModel):
    status: str
    version: str
    anthropic_key: bool
    xai_key: bool
    tmp_dir_writable: bool


# Health check
@app.get("/")
async def root():
    """API health check and endpoint listing."""
    return {
        "name": "Interview Prep PowerPoint API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "POST /api/research": "Research company and role",
            "POST /api/research/upload": "Research with resume upload",
            "POST /api/generate": "Generate PowerPoint from research",
            "POST /api/edit/text": "Edit text on a slide",
            "POST /api/edit/add-slide": "Add new slide",
            "POST /api/edit/add-slide/upload": "Add slide with image upload",
            "POST /api/edit/regenerate": "Regenerate slide image",
            "GET /api/slides": "List all slides",
            "GET /api/download/{filename}": "Download generated file",
            "GET /api/status": "Check API status"
        }
    }


@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Check API status and dependencies."""
    return StatusResponse(
        status="running",
        version="1.0.0",
        anthropic_key=bool(os.getenv("ANTHROPIC_API_KEY")),
        xai_key=bool(os.getenv("XAI_API_KEY")),
        tmp_dir_writable=os.access(TMP_DIR, os.W_OK)
    )


@app.post("/api/research")
async def research_company(request: ResearchRequest):
    """
    Research a company and role using AI.

    Returns research JSON with company overview, culture, role analysis,
    interview questions, and talking points.
    """
    try:
        cmd = [
            "python", str(SRC_DIR / "interview_research.py"),
            "--company", request.company,
            "--role", request.role,
        ]

        if request.generate_images:
            cmd.append("--generate-images")

        # Run research script
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=str(BASE_DIR),
            env={**os.environ, "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", "")}
        )

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Research failed: {result.stderr}")

        # Find output file
        safe_name = request.company.lower().replace(" ", "_").replace("/", "_")
        output_file = TMP_DIR / f"interview_research_{safe_name}.json"

        if not output_file.exists():
            raise HTTPException(status_code=500, detail="Research output not found")

        with open(output_file) as f:
            research_data = json.load(f)

        return {
            "success": True,
            "message": "Research completed",
            "output_file": str(output_file.name),
            "data": research_data
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Research timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/research/upload")
async def research_with_resume(
    company: str = Form(...),
    role: str = Form(...),
    generate_images: bool = Form(False),
    resume: UploadFile = File(...)
):
    """
    Research a company and role with resume upload.

    Parses resume to extract relevant experience for personalized insights.
    """
    try:
        # Save uploaded resume
        resume_path = TMP_DIR / f"uploaded_resume_{resume.filename}"
        with open(resume_path, "wb") as f:
            shutil.copyfileobj(resume.file, f)

        cmd = [
            "python", str(SRC_DIR / "interview_research.py"),
            "--company", company,
            "--role", role,
            "--resume", str(resume_path),
        ]

        if generate_images:
            cmd.append("--generate-images")

        # Run research script
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(BASE_DIR),
            env={**os.environ, "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", "")}
        )

        # Clean up uploaded file
        resume_path.unlink(missing_ok=True)

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Research failed: {result.stderr}")

        # Find output file
        safe_name = company.lower().replace(" ", "_").replace("/", "_")
        output_file = TMP_DIR / f"interview_research_{safe_name}.json"

        if not output_file.exists():
            raise HTTPException(status_code=500, detail="Research output not found")

        with open(output_file) as f:
            research_data = json.load(f)

        return {
            "success": True,
            "message": "Research completed with resume",
            "output_file": str(output_file.name),
            "data": research_data
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Research timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate")
async def generate_presentation(request: GenerateRequest):
    """
    Generate PowerPoint presentation from research data.

    Returns path to generated PPTX file.
    """
    try:
        research_path = TMP_DIR / request.research_file
        if not research_path.exists():
            raise HTTPException(status_code=404, detail="Research file not found")

        cmd = [
            "python", str(SRC_DIR / "pptx_generator.py"),
            "--input", str(research_path),
            "--theme", request.theme,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(BASE_DIR)
        )

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Generation failed: {result.stderr}")

        # Find output file
        with open(research_path) as f:
            research_data = json.load(f)
        company = research_data.get("company_overview", {}).get("name", "presentation")
        safe_name = company.lower().replace(" ", "_").replace("/", "_")
        output_file = TMP_DIR / f"interview_prep_{safe_name}.pptx"

        if not output_file.exists():
            raise HTTPException(status_code=500, detail="PowerPoint output not found")

        # Create session for this presentation
        role = research_data.get("role_analysis", {}).get("title", "Unknown Role")
        if SESSION_ENABLED:
            session = create_session(
                company=company,
                role=role,
                research_file=request.research_file,
                pptx_file=output_file.name,
                theme=request.theme
            )
            session_id = session.get("session_id")
        else:
            session_id = None

        return {
            "success": True,
            "message": "Presentation generated",
            "output_file": str(output_file.name),
            "download_url": f"/api/download/{output_file.name}",
            "session_id": session_id,
            "session_active": SESSION_ENABLED
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Generation timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/slides")
async def list_slides(pptx_file: str):
    """List all slides in a presentation."""
    try:
        pptx_path = TMP_DIR / pptx_file
        if not pptx_path.exists():
            raise HTTPException(status_code=404, detail="PowerPoint file not found")

        cmd = [
            "python", str(SRC_DIR / "pptx_editor.py"),
            "--input", str(pptx_path),
            "--action", "list",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(BASE_DIR)
        )

        return {
            "success": True,
            "output": result.stdout
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/edit/text")
async def edit_slide_text(request: EditTextRequest):
    """Edit text on a specific slide."""
    try:
        pptx_path = TMP_DIR / request.pptx_file
        if not pptx_path.exists():
            raise HTTPException(status_code=404, detail="PowerPoint file not found")

        cmd = [
            "python", str(SRC_DIR / "pptx_editor.py"),
            "--input", str(pptx_path),
            "--action", "edit-text",
            "--slide", str(request.slide_number),
            "--find", request.find_text,
            "--replace", request.replace_text,
        ]

        if request.match_all:
            cmd.append("--match-all")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(BASE_DIR)
        )

        return {
            "success": result.returncode == 0,
            "message": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/edit/add-slide")
async def add_slide(request: AddSlideRequest):
    """Add a new slide with optional AI-generated image."""
    try:
        pptx_path = TMP_DIR / request.pptx_file
        if not pptx_path.exists():
            raise HTTPException(status_code=404, detail="PowerPoint file not found")

        cmd = [
            "python", str(SRC_DIR / "pptx_editor.py"),
            "--input", str(pptx_path),
            "--action", "add-slide",
            "--title", request.title,
            "--description", request.description,
            "--relevance", request.relevance,
        ]

        if request.after_slide:
            cmd.extend(["--after-slide", str(request.after_slide)])

        if request.image_prompt:
            cmd.extend(["--prompt", request.image_prompt])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(BASE_DIR),
            env={**os.environ, "XAI_API_KEY": os.getenv("XAI_API_KEY", "")}
        )

        return {
            "success": result.returncode == 0,
            "message": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Operation timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/edit/add-slide/upload")
async def add_slide_with_image(
    pptx_file: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    relevance: str = Form(...),
    after_slide: Optional[int] = Form(None),
    image: UploadFile = File(...)
):
    """Add a new slide with uploaded image (FREE - no AI cost)."""
    try:
        pptx_path = TMP_DIR / pptx_file
        if not pptx_path.exists():
            raise HTTPException(status_code=404, detail="PowerPoint file not found")

        # Save uploaded image
        image_path = TMP_DIR / f"uploaded_image_{image.filename}"
        with open(image_path, "wb") as f:
            shutil.copyfileobj(image.file, f)

        cmd = [
            "python", str(SRC_DIR / "pptx_editor.py"),
            "--input", str(pptx_path),
            "--action", "add-slide",
            "--title", title,
            "--description", description,
            "--relevance", relevance,
            "--new-image", str(image_path),
        ]

        if after_slide:
            cmd.extend(["--after-slide", str(after_slide)])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(BASE_DIR)
        )

        # Clean up uploaded image
        image_path.unlink(missing_ok=True)

        return {
            "success": result.returncode == 0,
            "message": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/edit/regenerate")
async def regenerate_image(request: RegenerateImageRequest):
    """Regenerate an image on a slide using AI ($0.07)."""
    try:
        pptx_path = TMP_DIR / request.pptx_file
        if not pptx_path.exists():
            raise HTTPException(status_code=404, detail="PowerPoint file not found")

        cmd = [
            "python", str(SRC_DIR / "pptx_editor.py"),
            "--input", str(pptx_path),
            "--action", "regenerate-image",
            "--slide", str(request.slide_number),
            "--prompt", request.prompt,
            "--image-index", str(request.image_index),
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(BASE_DIR),
            env={**os.environ, "XAI_API_KEY": os.getenv("XAI_API_KEY", "")}
        )

        return {
            "success": result.returncode == 0,
            "message": result.stdout,
            "cost": "$0.07" if result.returncode == 0 else None,
            "error": result.stderr if result.returncode != 0 else None
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Image generation timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """Download a generated file (PPTX or JSON)."""
    file_path = TMP_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # Determine media type
    if filename.endswith(".pptx"):
        media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    elif filename.endswith(".json"):
        media_type = "application/json"
    else:
        media_type = "application/octet-stream"

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type
    )


@app.get("/api/files")
async def list_files():
    """List all generated files in the temp directory."""
    files = []
    for f in TMP_DIR.iterdir():
        if f.is_file() and (f.suffix in [".pptx", ".json", ".jpeg", ".jpg", ".png"]):
            files.append({
                "name": f.name,
                "size": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                "type": f.suffix
            })

    return {"files": sorted(files, key=lambda x: x["modified"], reverse=True)}


# Session Management Endpoints
@app.get("/api/session")
async def get_session():
    """Get current active session information."""
    if not SESSION_ENABLED:
        return {"error": "Session management not available"}

    session = get_active_session()
    if not session:
        return {
            "active": False,
            "message": "No active session. Create a presentation first.",
            "hint": "Use POST /api/research to start a new interview prep session"
        }

    return {
        "active": True,
        "session_id": session.get("session_id"),
        "company": session.get("company"),
        "role": session.get("role"),
        "pptx_file": session.get("pptx_file"),
        "research_file": session.get("research_file"),
        "resume_included": bool(session.get("resume_file")),
        "theme": session.get("theme"),
        "slide_count": session.get("slide_count"),
        "edits_made": len(session.get("edit_history", [])),
        "created_at": session.get("created_at"),
        "download_url": f"/api/download/{session.get('pptx_file')}" if session.get("pptx_file") else None
    }


@app.post("/api/session/close")
async def close_current_session():
    """Close the current session and finalize the presentation."""
    if not SESSION_ENABLED:
        return {"error": "Session management not available"}

    session = get_active_session()
    if not session:
        return {"success": False, "message": "No active session to close"}

    pptx_file = session.get("pptx_file")
    close_session()

    return {
        "success": True,
        "message": "Session closed successfully",
        "final_presentation": pptx_file,
        "download_url": f"/api/download/{pptx_file}" if pptx_file else None
    }


@app.get("/api/session/history")
async def get_session_history():
    """List recent interview prep sessions."""
    if not SESSION_ENABLED:
        return {"error": "Session management not available"}

    # Get recent research files
    research_files = list(TMP_DIR.glob("interview_research_*.json"))
    research_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    sessions = []
    for f in research_files[:10]:  # Last 10 sessions
        try:
            with open(f) as file:
                data = json.load(file)
            company = data.get("company_overview", {}).get("name", "Unknown")
            role = data.get("role_analysis", {}).get("title", "Unknown")
            pptx_name = f.name.replace("interview_research_", "interview_prep_").replace(".json", ".pptx")
            pptx_exists = (TMP_DIR / pptx_name).exists()

            sessions.append({
                "company": company,
                "role": role,
                "research_file": f.name,
                "pptx_file": pptx_name if pptx_exists else None,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                "has_presentation": pptx_exists
            })
        except:
            continue

    return {"sessions": sessions}


@app.post("/api/session/resume")
async def resume_session(research_file: str = Form(...)):
    """Resume editing a previous session's presentation."""
    if not SESSION_ENABLED:
        return {"error": "Session management not available"}

    research_path = TMP_DIR / research_file
    if not research_path.exists():
        raise HTTPException(status_code=404, detail="Research file not found")

    # Load research data
    with open(research_path) as f:
        data = json.load(f)

    company = data.get("company_overview", {}).get("name", "Unknown")
    role = data.get("role_analysis", {}).get("title", "Unknown")
    pptx_name = research_file.replace("interview_research_", "interview_prep_").replace(".json", ".pptx")

    if not (TMP_DIR / pptx_name).exists():
        raise HTTPException(status_code=404, detail="Presentation file not found. Generate it first.")

    # Create new session for this presentation
    session = create_session(
        company=company,
        role=role,
        research_file=research_file,
        pptx_file=pptx_name
    )

    return {
        "success": True,
        "message": f"Resumed session for {company} - {role}",
        "session": session
    }


# Serve frontend
FRONTEND_DIR = BASE_DIR / "frontend"

@app.get("/app", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the frontend application."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(), status_code=200)
    raise HTTPException(status_code=404, detail="Frontend not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
