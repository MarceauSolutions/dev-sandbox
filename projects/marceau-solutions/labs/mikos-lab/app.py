#!/usr/bin/env python3
"""
Miko's Lab Interactive Browser
Standalone web app for learning AI influencer creation from Miko's Lab content.
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request

APP_DIR = Path(__file__).parent
POSTS_DIR = APP_DIR / "posts"
PDFS_DIR = APP_DIR / "pdfs"
KNOWLEDGE_BASE = APP_DIR / "KNOWLEDGE_BASE.md"
METHODS_SUMMARY = APP_DIR / "MIKO_METHODS_SUMMARY.md"
LATEST_POSTS = APP_DIR / "LATEST_POSTS.md"
SYNC_STATE = APP_DIR / "sync_state.json"
SCRAPER = APP_DIR / "scripts" / "scrape_mikoslab.py"

app = Flask(__name__, template_folder=str(APP_DIR / "templates"), static_folder=str(APP_DIR / "static"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_file(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")
    return ""


def get_sync_state() -> dict:
    if SYNC_STATE.exists():
        return json.loads(SYNC_STATE.read_text())
    return {"last_sync": None, "seen_hashes": []}


def get_posts() -> list:
    latest = POSTS_DIR / "latest.json"
    if latest.exists():
        return json.loads(latest.read_text())
    return []


def parse_knowledge_base() -> list:
    """Parse KNOWLEDGE_BASE.md into sections by PDF guide."""
    content = read_file(KNOWLEDGE_BASE)
    if not content:
        return []

    sections = []
    current_section = None

    for line in content.split("\n"):
        if line.startswith("## ") and not line.startswith("## Table of Contents"):
            if current_section:
                sections.append(current_section)
            title = line[3:].strip()
            current_section = {"title": title, "content": "", "source": ""}
        elif current_section is not None:
            if line.startswith("*Source:") and line.endswith("*"):
                current_section["source"] = line.strip("* ")
            else:
                current_section["content"] += line + "\n"

    if current_section:
        sections.append(current_section)

    return sections


def categorize_guides(sections: list) -> dict:
    """Organize guides into logical categories."""
    categories = {
        "getting-started": {
            "name": "Getting Started",
            "icon": "rocket",
            "description": "Foundation guides for AI influencer creation",
            "guides": [],
        },
        "character-creation": {
            "name": "Character & Image Creation",
            "icon": "user",
            "description": "Build consistent AI characters and starting frames",
            "guides": [],
        },
        "video-generation": {
            "name": "Video Generation",
            "icon": "video",
            "description": "Tools and techniques for AI video creation",
            "guides": [],
        },
        "voice-audio": {
            "name": "Voice & Audio",
            "icon": "microphone",
            "description": "Realistic AI voices and audio workflows",
            "guides": [],
        },
        "monetization": {
            "name": "Monetization & Agency",
            "icon": "dollar-sign",
            "description": "Turn AI content into revenue",
            "guides": [],
        },
        "optimization": {
            "name": "Cost & Tool Optimization",
            "icon": "settings",
            "description": "Save money and work smarter",
            "guides": [],
        },
        "advanced": {
            "name": "Advanced Techniques",
            "icon": "zap",
            "description": "Cloning, slideshows, and advanced workflows",
            "guides": [],
        },
    }

    keyword_map = {
        "getting-started": ["complete ai influencer system", "niche selection", "personal brand"],
        "character-creation": ["nanobanana", "nano banana", "character"],
        "video-generation": ["sora", "veo", "seedance", "video", "ugc"],
        "voice-audio": ["voice", "audio"],
        "monetization": ["money", "blueprint", "agency", "client"],
        "optimization": ["cheaper", "cost", "cut"],
        "advanced": ["clone", "slideshow", "mentor"],
    }

    for section in sections:
        title_lower = section["title"].lower()
        placed = False
        for cat_key, keywords in keyword_map.items():
            if any(kw in title_lower for kw in keywords):
                categories[cat_key]["guides"].append(section)
                placed = True
                break
        if not placed:
            categories["advanced"]["guides"].append(section)

    return categories


def get_pdf_list() -> list:
    """List available PDF files."""
    if not PDFS_DIR.exists():
        return []
    pdfs = []
    for f in sorted(PDFS_DIR.iterdir()):
        if f.suffix.lower() == ".pdf":
            pdfs.append({
                "name": f.stem,
                "filename": f.name,
                "size_mb": round(f.stat().st_size / (1024 * 1024), 1),
            })
    return pdfs


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/overview")
def api_overview():
    """Dashboard overview data."""
    state = get_sync_state()
    posts = get_posts()
    sections = parse_knowledge_base()
    pdfs = get_pdf_list()

    return jsonify({
        "last_sync": state.get("last_sync"),
        "total_posts": len(posts),
        "total_guides": len(sections),
        "total_pdfs": len(pdfs),
        "categories": len(categorize_guides(sections)),
    })


@app.route("/api/knowledge")
def api_knowledge():
    """Get categorized knowledge base."""
    sections = parse_knowledge_base()
    categories = categorize_guides(sections)
    return jsonify(categories)


@app.route("/api/methods")
def api_methods():
    """Get methods summary."""
    content = read_file(METHODS_SUMMARY)
    return jsonify({"content": content})


@app.route("/api/posts")
def api_posts():
    """Get Telegram posts."""
    posts = get_posts()
    state = get_sync_state()
    return jsonify({"posts": posts, "last_sync": state.get("last_sync")})


@app.route("/api/pdfs")
def api_pdfs():
    """List available PDFs."""
    return jsonify(get_pdf_list())


@app.route("/api/sync", methods=["POST"])
def api_sync():
    """Trigger a sync of the Telegram channel."""
    try:
        result = subprocess.run(
            [sys.executable, str(SCRAPER)],
            capture_output=True, text=True, timeout=60,
            cwd=str(APP_DIR),
        )
        return jsonify({
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr,
        })
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "Sync timed out"}), 504
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/workshop/tools")
def api_workshop_tools():
    """Get available tools for the workshop."""
    dev_sandbox = APP_DIR.parents[3]  # dev-sandbox root
    execution = dev_sandbox / "execution"

    tools = {
        "image_generation": [],
        "video_generation": [],
        "social_posting": [],
        "content_creation": [],
    }

    # Check for image generation tools
    img_tools = [
        ("grok_image_gen.py", "Grok Image Generator", "xAI Aurora — $0.07/image, photorealistic"),
        ("multi_provider_image_router.py", "Multi-Provider Image Router", "Auto-select best provider — $0.003-$0.07/image"),
    ]
    for filename, name, desc in img_tools:
        path = execution / filename
        tools["image_generation"].append({
            "name": name,
            "description": desc,
            "available": path.exists(),
            "script": str(path),
        })

    # Check for video generation tools
    vid_tools = [
        ("grok_video_gen.py", "Grok Video Generator", "xAI video — $0.12-$0.30/video"),
        ("multi_provider_video_router.py", "Multi-Provider Video Router", "Auto-select — $0-$2/video"),
        ("intelligent_video_router.py", "Intelligent Video Router", "Smart MoviePy↔Creatomate fallback"),
        ("moviepy_video_generator.py", "MoviePy Video Generator", "FREE local video composition"),
    ]
    for filename, name, desc in vid_tools:
        path = execution / filename
        tools["video_generation"].append({
            "name": name,
            "description": desc,
            "available": path.exists(),
            "script": str(path),
        })

    # Social media tools
    social_tools = [
        ("Instagram Creator MCP", "Post images, carousels, Reels, Stories"),
        ("YouTube Creator MCP", "Upload videos, Shorts, schedule releases"),
        ("TikTok Creator MCP", "Post videos, track analytics"),
        ("X/Twitter Automation", "n8n scheduler + social-media-automation"),
    ]
    for name, desc in social_tools:
        tools["social_posting"].append({
            "name": name,
            "description": desc,
            "available": True,
        })

    # Content creation tools
    content_tools = [
        ("video_jumpcut.py", "Video Jump Cut", "Remove silence, create jump cuts"),
        ("video_ads.py", "Video Ads Generator", "Automated ad creative generation"),
        ("branded_pdf_engine.py", "Branded PDF Engine", "Professional branded PDFs"),
    ]
    for filename, name, desc in content_tools:
        path = execution / filename
        tools["content_creation"].append({
            "name": name,
            "description": desc,
            "available": path.exists(),
            "script": str(path),
        })

    return jsonify(tools)


@app.route("/api/generate/image", methods=["POST"])
def api_generate_image():
    """Generate an image using available tools."""
    data = request.json or {}
    prompt = data.get("prompt", "")
    if not prompt:
        return jsonify({"success": False, "error": "Prompt required"}), 400

    dev_sandbox = APP_DIR.parents[3]
    script = dev_sandbox / "execution" / "grok_image_gen.py"
    if not script.exists():
        return jsonify({"success": False, "error": "Image generator not found"}), 404

    try:
        result = subprocess.run(
            [sys.executable, str(script), "--prompt", prompt, "--count", "1"],
            capture_output=True, text=True, timeout=120,
            cwd=str(dev_sandbox),
            env={**os.environ, "PYTHONPATH": str(dev_sandbox)},
        )
        return jsonify({
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("MIKOS_LAB_PORT", 8766))
    print(f"\n  Miko's Lab Interactive Browser")
    print(f"  http://127.0.0.1:{port}\n")
    app.run(host="127.0.0.1", port=port, debug=False)
