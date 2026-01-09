#!/usr/bin/env python3
"""
chat_api.py - AI Chat Interface for Fitness Influencer Assistant

Dual-AI architecture combining Claude + XAI/Grok for intelligent,
cost-effective decision making.

Architecture:
    User Message → Dual-AI Router
                 → Claude (intent understanding, tool selection)
                 → Grok (cost optimization, image generation)
                 → Execute tool
                 → Return result to user

Cost Guardrails:
    - Operations >$0.10 require user confirmation
    - Suggests cheaper alternatives when available
    - Tracks session costs

API Keys Required:
    - ANTHROPIC_API_KEY: For Claude conversation
    - XAI_API_KEY: For Grok image generation
    - SHOTSTACK_API_KEY: For video ad creation
    - Google credentials: For email/sheets

Usage:
    uvicorn chat_api:app --reload --host 0.0.0.0 --port 8000
"""

import os
import sys
import json
import tempfile
import shutil
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import dual-AI router
try:
    # When running as module (src.chat_api)
    from src.dual_ai_router import get_router, DualAIRouter, ToolDecision, CostTier
except ImportError:
    # When running directly (python chat_api.py)
    from dual_ai_router import get_router, DualAIRouter, ToolDecision, CostTier

load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="Fitness Influencer AI Chat",
    description="Conversational AI assistant for fitness content creators",
    version="1.0.0"
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
FRONTEND_PATH = SCRIPTS_PATH.parent / "frontend"

# Initialize dual-AI router
try:
    ai_router = get_router()
except Exception as e:
    print(f"Warning: AI router not initialized: {e}")
    ai_router = None


# ==============================================================================
# Models
# ==============================================================================

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []
    file_info: Optional[Dict[str, Any]] = None  # {name, type, size}
    confirmed: Optional[bool] = False  # User confirmed expensive operation

class ChatResponse(BaseModel):
    message: str
    result: Optional[Dict[str, Any]] = None
    tool_used: Optional[str] = None
    requires_confirmation: Optional[bool] = False
    cost_info: Optional[Dict[str, Any]] = None  # Cost details for confirmation
    session_total: Optional[float] = 0.0


# ==============================================================================
# Tool definitions are now in dual_ai_router.py
# ==============================================================================


# ==============================================================================
# Tool Execution Functions
# ==============================================================================

def execute_tool(tool_name: str, tool_input: Dict[str, Any], uploaded_file_path: Optional[str] = None) -> Dict[str, Any]:
    """Execute the specified tool and return results."""

    import subprocess

    try:
        if tool_name == "edit_video":
            if not uploaded_file_path:
                return {
                    "success": False,
                    "error": "Please upload a video file first"
                }

            # Output path
            output_path = Path(tempfile.gettempdir()) / f"edited_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

            cmd = [
                "python",
                str(SCRIPTS_PATH / "video_jumpcut.py"),
                "--input", uploaded_file_path,
                "--output", str(output_path),
                "--silence-thresh", str(tool_input.get("silence_threshold", -40))
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode == 0 and output_path.exists():
                return {
                    "success": True,
                    "title": "Video Edited Successfully",
                    "icon": "video",
                    "message": "Removed silent parts and created jump cuts",
                    "file_path": str(output_path),
                    "download_text": "Download Edited Video"
                }
            else:
                return {"success": False, "error": result.stderr or "Video processing failed"}

        elif tool_name == "create_graphic":
            output_path = Path(tempfile.gettempdir()) / f"graphic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

            cmd = [
                "python",
                str(SCRIPTS_PATH / "educational_graphics.py"),
                "--title", tool_input.get("title", "Fitness Tips"),
                "--points", ",".join(tool_input.get("points", ["Stay hydrated", "Get enough sleep"])),
                "--platform", tool_input.get("platform", "instagram_post"),
                "--output", str(output_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0 and output_path.exists():
                return {
                    "success": True,
                    "title": "Graphic Created",
                    "icon": "graphic",
                    "message": f"Created {tool_input.get('platform', 'Instagram')} graphic",
                    "file_path": str(output_path),
                    "download_text": "Download Graphic"
                }
            else:
                return {"success": False, "error": result.stderr or "Graphic generation failed"}

        elif tool_name == "generate_ai_image":
            output_dir = Path(tempfile.gettempdir()) / f"ai_images_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            output_dir.mkdir(exist_ok=True)

            count = min(tool_input.get("count", 1), 4)
            cost = count * 0.07

            cmd = [
                "python",
                str(SCRIPTS_PATH / "grok_image_gen.py"),
                "--prompt", tool_input.get("prompt", "Fitness athlete"),
                "--count", str(count),
                "--output", str(output_dir / "image.png")
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                # Find generated images
                images = list(output_dir.glob("*.png"))
                return {
                    "success": True,
                    "title": f"{count} AI Image{'s' if count > 1 else ''} Generated",
                    "icon": "ai",
                    "message": f"Generated using Grok AI. Cost: ${cost:.2f}",
                    "images": [str(img) for img in images],
                    "cost": cost
                }
            else:
                return {"success": False, "error": result.stderr or "Image generation failed"}

        elif tool_name == "create_video_ad":
            output_path = Path(tempfile.gettempdir()) / f"video_ad_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

            cmd = [
                "python",
                str(SCRIPTS_PATH / "video_ads.py"),
                "--theme", tool_input.get("theme", "fitness"),
                "--cta", tool_input.get("cta", "Start your journey today!"),
                "--handle", tool_input.get("handle", "@fitness"),
                "--output", str(output_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

            if result.returncode == 0 and output_path.exists():
                return {
                    "success": True,
                    "title": "Video Ad Created",
                    "icon": "ads",
                    "message": "Created video ad with AI images and transitions. Cost: $0.34",
                    "file_path": str(output_path),
                    "download_text": "Download Video Ad",
                    "cost": 0.34
                }
            else:
                return {"success": False, "error": result.stderr or "Video ad creation failed"}

        elif tool_name == "summarize_emails":
            hours = tool_input.get("hours_back", 24)

            # For demo/testing, return simulated data
            # In production, this would call gmail_monitor.py
            return {
                "success": True,
                "title": f"Email Summary (Last {hours} hours)",
                "icon": "email",
                "html": """
                    <div style="margin-bottom: 16px;">
                        <strong style="color: #ef4444;">URGENT (2)</strong>
                        <ul style="margin: 8px 0 0 20px;">
                            <li>Sponsorship offer from FitGear Pro - $2,500/month</li>
                            <li>Brand collaboration deadline tomorrow</li>
                        </ul>
                    </div>
                    <div style="margin-bottom: 16px;">
                        <strong style="color: #f59e0b;">BUSINESS (5)</strong>
                        <ul style="margin: 8px 0 0 20px;">
                            <li>Payment received: $450 from coaching client</li>
                            <li>3 new affiliate program invitations</li>
                        </ul>
                    </div>
                    <div>
                        <strong style="color: #4ade80;">CUSTOMER (12)</strong>
                        <ul style="margin: 8px 0 0 20px;">
                            <li>8 questions about workout programs</li>
                            <li>4 testimonials/thank you messages</li>
                        </ul>
                    </div>
                """
            }

        elif tool_name == "revenue_report":
            # For demo/testing, return simulated data
            return {
                "success": True,
                "title": "Revenue Analytics",
                "icon": "analytics",
                "html": """
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
                        <div style="background: rgba(74, 222, 128, 0.1); padding: 12px; border-radius: 8px;">
                            <div style="color: #6b7280; font-size: 12px;">Total Revenue</div>
                            <div style="color: #4ade80; font-size: 24px; font-weight: 700;">$8,450</div>
                        </div>
                        <div style="background: rgba(239, 68, 68, 0.1); padding: 12px; border-radius: 8px;">
                            <div style="color: #6b7280; font-size: 12px;">Expenses</div>
                            <div style="color: #ef4444; font-size: 24px; font-weight: 700;">$2,100</div>
                        </div>
                    </div>
                    <div style="background: rgba(96, 165, 250, 0.1); padding: 12px; border-radius: 8px; margin-bottom: 16px;">
                        <div style="color: #6b7280; font-size: 12px;">Net Profit</div>
                        <div style="color: #60a5fa; font-size: 28px; font-weight: 700;">$6,350</div>
                        <div style="color: #4ade80; font-size: 12px;">+23% vs last month</div>
                    </div>
                """
            }

        elif tool_name == "create_workout_plan":
            goal = tool_input.get("goal", "muscle_building")
            days = tool_input.get("days_per_week", 4)

            return {
                "success": True,
                "title": f"{days}-Day {goal.replace('_', ' ').title()} Plan",
                "icon": "workout",
                "html": f"""
                    <p><strong>Day 1: Push (Chest, Shoulders, Triceps)</strong></p>
                    <ul style="margin: 8px 0 16px 20px;">
                        <li>Bench Press: 4x8-10</li>
                        <li>Overhead Press: 3x10</li>
                        <li>Dips: 3x12</li>
                    </ul>
                    <p><strong>Day 2: Pull (Back, Biceps)</strong></p>
                    <ul style="margin: 8px 0 16px 20px;">
                        <li>Deadlift: 4x6</li>
                        <li>Pull-ups: 3x10</li>
                        <li>Barbell Rows: 3x12</li>
                    </ul>
                    <p><em>...plus {days - 2} more days</em></p>
                """,
                "download_text": "Download Full Plan (PDF)"
            }

        elif tool_name == "create_nutrition_guide":
            weight = tool_input.get("weight_lbs", 170)
            goal = tool_input.get("goal", "maintenance")

            # Simple TDEE calculation
            base_calories = weight * 14
            if goal == "fat_loss":
                calories = int(base_calories * 0.8)
                protein = int(weight * 1.0)
            elif goal == "muscle_gain":
                calories = int(base_calories * 1.15)
                protein = int(weight * 1.2)
            else:
                calories = int(base_calories)
                protein = int(weight * 0.9)

            return {
                "success": True,
                "title": f"Nutrition Guide - {goal.replace('_', ' ').title()}",
                "icon": "nutrition",
                "html": f"""
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 16px;">
                        <div style="background: rgba(251, 191, 36, 0.1); padding: 12px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 12px; color: #6b7280;">Daily Calories</div>
                            <div style="font-size: 24px; font-weight: 700; color: #fbbf24;">{calories}</div>
                        </div>
                        <div style="background: rgba(239, 68, 68, 0.1); padding: 12px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 12px; color: #6b7280;">Protein</div>
                            <div style="font-size: 24px; font-weight: 700; color: #ef4444;">{protein}g</div>
                        </div>
                    </div>
                    <p><strong>Recommended Foods:</strong></p>
                    <ul style="margin: 8px 0 0 20px;">
                        <li>Lean proteins: chicken, fish, eggs</li>
                        <li>Complex carbs: rice, oats, sweet potato</li>
                        <li>Healthy fats: avocado, nuts, olive oil</li>
                    </ul>
                """,
                "download_text": "Download Full Guide (PDF)"
            }

        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

    except Exception as e:
        return {"success": False, "error": str(e)}


# ==============================================================================
# Chat Endpoint (Dual-AI Flow)
# ==============================================================================

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat message using dual-AI system (Claude + Grok).

    Flow:
    1. Claude understands intent and selects tool
    2. Grok validates and optimizes cost (for paid operations)
    3. If cost > $0.10, require user confirmation
    4. Execute tool and return result
    """
    if not ai_router:
        raise HTTPException(status_code=500, detail="AI router not configured")

    # Build message history for router
    history = []
    for msg in request.history:
        history.append({"role": msg.role, "content": msg.content})

    # Add file info to message if present
    user_message = request.message
    if request.file_info:
        user_message += f"\n\n[User attached file: {request.file_info.get('name', 'file')}]"

    try:
        # Process through dual-AI router
        router_result = ai_router.process_request(
            message=user_message,
            history=history,
            skip_confirmation=request.confirmed  # Skip if already confirmed
        )

        # Check for errors
        if "error" in router_result:
            raise HTTPException(status_code=500, detail=router_result["error"])

        decision = router_result.get("decision")
        response_text = router_result.get("response", "")
        session_total = router_result.get("session_total", 0.0)

        # If no tool was selected, just return the conversation response
        if not decision:
            return ChatResponse(
                message=response_text,
                result=None,
                tool_used=None,
                requires_confirmation=False,
                session_total=session_total
            )

        # If confirmation is required (cost > $0.10), return confirmation request
        if decision.requires_confirmation and not request.confirmed:
            cost_info = {
                "estimated_cost": decision.estimated_cost,
                "cost_tier": decision.cost_tier.value,
                "tool_name": decision.tool_name,
                "tool_input": decision.tool_input,
                "alternatives": decision.alternatives,
                "explanation": decision.explanation
            }

            confirmation_message = f"{response_text}\n\n"
            confirmation_message += f"This will cost ${decision.estimated_cost:.2f}. "

            if decision.alternatives:
                confirmation_message += "Options available:\n"
                for alt in decision.alternatives:
                    confirmation_message += f"  - {alt['name']}: ${alt['cost']:.2f}\n"

            confirmation_message += "\nConfirm to proceed?"

            return ChatResponse(
                message=confirmation_message,
                result=None,
                tool_used=decision.tool_name,
                requires_confirmation=True,
                cost_info=cost_info,
                session_total=session_total
            )

        # Execute the tool
        tool_result = execute_tool(decision.tool_name, decision.tool_input)

        # Track cost in router
        if decision.estimated_cost > 0:
            ai_router.confirm_and_execute(decision)

        result = None
        if tool_result.get("success"):
            result = {
                "icon": tool_result.get("icon", "check"),
                "title": tool_result.get("title", "Complete"),
            }

            if "html" in tool_result:
                result["html"] = tool_result["html"]
            if "file_path" in tool_result:
                result["download"] = f"/api/download?path={tool_result['file_path']}"
                result["downloadText"] = tool_result.get("download_text", "Download")
            if "images" in tool_result:
                result["images"] = [f"/api/download?path={img}" for img in tool_result["images"]]
            if "cost" in tool_result:
                result["cost"] = tool_result["cost"]

            if not response_text:
                response_text = tool_result.get("message", "Done!")
        else:
            response_text = f"I encountered an issue: {tool_result.get('error', 'Unknown error')}. Please try again."

        return ChatResponse(
            message=response_text,
            result=result,
            tool_used=decision.tool_name,
            requires_confirmation=False,
            session_total=ai_router.session_costs
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download")
async def download_file(path: str):
    """Serve generated files for download."""
    file_path = Path(path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        file_path,
        filename=file_path.name,
        media_type="application/octet-stream"
    )


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file for processing."""
    # Save to temp directory
    temp_dir = Path(tempfile.gettempdir()) / "fitness_uploads"
    temp_dir.mkdir(exist_ok=True)

    file_path = temp_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {"path": str(file_path), "name": file.filename, "size": file_path.stat().st_size}


# ==============================================================================
# Health & Static Files
# ==============================================================================

@app.get("/")
async def root():
    """Redirect to chat interface."""
    return FileResponse(FRONTEND_PATH / "chat.html")


@app.get("/dashboard")
async def dashboard():
    """Serve dashboard interface."""
    return FileResponse(FRONTEND_PATH / "dashboard.html")


@app.get("/api/costs")
async def get_costs():
    """Get session cost summary."""
    if not ai_router:
        return {"total_cost": 0, "operation_count": 0, "operations": []}

    return ai_router.get_session_summary()


@app.post("/api/costs/reset")
async def reset_costs():
    """Reset session costs."""
    global ai_router
    if ai_router:
        ai_router.session_costs = 0.0
        ai_router.operation_history = []
    return {"status": "reset", "total_cost": 0}


@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "claude": ai_router.claude is not None if ai_router else False,
        "xai": os.getenv("XAI_API_KEY") is not None,
        "dual_ai_router": ai_router is not None,
        "session_costs": ai_router.session_costs if ai_router else 0,
        "timestamp": datetime.now().isoformat()
    }


# Serve static files
if FRONTEND_PATH.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_PATH), name="static")


if __name__ == "__main__":
    import uvicorn

    print("=" * 70)
    print("FITNESS INFLUENCER AI - DUAL-AI CHAT API")
    print("=" * 70)
    print(f"\nFrontend: http://localhost:8000")
    print(f"Dashboard: http://localhost:8000/dashboard")
    print(f"Health: http://localhost:8000/health")
    print(f"Costs: http://localhost:8000/api/costs")
    print(f"\nDual-AI Router: {'Active' if ai_router else 'Not configured'}")
    if ai_router:
        print(f"  - Claude: {'Connected' if ai_router.claude else 'Not configured'}")
        print(f"  - Grok/XAI: {'Configured' if ai_router.grok_api_key else 'Not configured'}")
    print(f"\nCost Guardrails: Operations >$0.10 require confirmation")
    print("=" * 70 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
