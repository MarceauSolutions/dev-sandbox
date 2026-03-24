#!/usr/bin/env python3
"""
Miko's Lab — AI Avatar Workshop & Implementation Tracker
Full production web app for learning AND executing AI influencer creation.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory

from database import get_db, create_project, DEFAULT_WORKFLOW, init_db

APP_DIR = Path(__file__).parent
POSTS_DIR = APP_DIR / "posts"
PDFS_DIR = APP_DIR / "pdfs"
KNOWLEDGE_BASE = APP_DIR / "KNOWLEDGE_BASE.md"
METHODS_SUMMARY = APP_DIR / "MIKO_METHODS_SUMMARY.md"
LATEST_POSTS = APP_DIR / "LATEST_POSTS.md"
SYNC_STATE = APP_DIR / "sync_state.json"
SCRAPER = APP_DIR / "scripts" / "scrape_mikoslab.py"
ASSETS_DIR = APP_DIR / "assets"
ASSETS_DIR.mkdir(exist_ok=True)

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
    categories = {
        "getting-started": {"name": "Getting Started", "icon": "rocket", "description": "Foundation guides for AI influencer creation", "guides": []},
        "character-creation": {"name": "Character & Image Creation", "icon": "user", "description": "Build consistent AI characters and starting frames", "guides": []},
        "video-generation": {"name": "Video Generation", "icon": "video", "description": "Tools and techniques for AI video creation", "guides": []},
        "voice-audio": {"name": "Voice & Audio", "icon": "microphone", "description": "Realistic AI voices and audio workflows", "guides": []},
        "monetization": {"name": "Monetization & Agency", "icon": "dollar-sign", "description": "Turn AI content into revenue", "guides": []},
        "optimization": {"name": "Cost & Tool Optimization", "icon": "settings", "description": "Save money and work smarter", "guides": []},
        "advanced": {"name": "Advanced Techniques", "icon": "zap", "description": "Cloning, slideshows, and advanced workflows", "guides": []},
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
    if not PDFS_DIR.exists():
        return []
    pdfs = []
    for f in sorted(PDFS_DIR.iterdir()):
        if f.suffix.lower() == ".pdf":
            pdfs.append({"name": f.stem, "filename": f.name, "size_mb": round(f.stat().st_size / (1024 * 1024), 1)})
    return pdfs


def row_to_dict(row):
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows):
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Routes — Original (Knowledge, Feed, Tools)
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/overview")
def api_overview():
    state = get_sync_state()
    posts = get_posts()
    sections = parse_knowledge_base()
    pdfs = get_pdf_list()
    conn = get_db()
    project_count = conn.execute("SELECT COUNT(*) FROM projects WHERE status != 'archived'").fetchone()[0]
    active_methods = conn.execute("SELECT COUNT(*) FROM method_tracker WHERE status NOT IN ('not_started')").fetchone()[0]
    total_methods = conn.execute("SELECT COUNT(*) FROM method_tracker").fetchone()[0]
    total_assets = conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
    total_prompts = conn.execute("SELECT COUNT(*) FROM prompts").fetchone()[0]
    conn.close()

    return jsonify({
        "last_sync": state.get("last_sync"),
        "total_posts": len(posts),
        "total_guides": len(sections),
        "total_pdfs": len(pdfs),
        "categories": len(categorize_guides(sections)),
        "project_count": project_count,
        "active_methods": active_methods,
        "total_methods": total_methods,
        "total_assets": total_assets,
        "total_prompts": total_prompts,
    })


@app.route("/api/knowledge")
def api_knowledge():
    sections = parse_knowledge_base()
    categories = categorize_guides(sections)
    return jsonify(categories)


@app.route("/api/methods")
def api_methods():
    content = read_file(METHODS_SUMMARY)
    return jsonify({"content": content})


@app.route("/api/posts")
def api_posts():
    posts = get_posts()
    state = get_sync_state()
    return jsonify({"posts": posts, "last_sync": state.get("last_sync")})


@app.route("/api/pdfs")
def api_pdfs():
    return jsonify(get_pdf_list())


@app.route("/api/pdfs/<path:filename>")
def serve_pdf(filename):
    return send_from_directory(str(PDFS_DIR), filename)


@app.route("/api/sync", methods=["POST"])
def api_sync():
    try:
        result = subprocess.run(
            [sys.executable, str(SCRAPER)],
            capture_output=True, text=True, timeout=60,
            cwd=str(APP_DIR),
        )
        return jsonify({"success": result.returncode == 0, "output": result.stdout, "error": result.stderr})
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "Sync timed out"}), 504
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/workshop/tools")
def api_workshop_tools():
    dev_sandbox = APP_DIR.parents[3]
    execution = dev_sandbox / "execution"
    tools = {"image_generation": [], "video_generation": [], "social_posting": [], "content_creation": []}
    img_tools = [
        ("grok_image_gen.py", "Grok Image Generator", "xAI Aurora — $0.07/image, photorealistic"),
        ("multi_provider_image_router.py", "Multi-Provider Image Router", "Auto-select best provider — $0.003-$0.07/image"),
    ]
    for filename, name, desc in img_tools:
        path = execution / filename
        tools["image_generation"].append({"name": name, "description": desc, "available": path.exists(), "script": str(path)})
    vid_tools = [
        ("grok_video_gen.py", "Grok Video Generator", "xAI video — $0.12-$0.30/video"),
        ("multi_provider_video_router.py", "Multi-Provider Video Router", "Auto-select — $0-$2/video"),
        ("intelligent_video_router.py", "Intelligent Video Router", "Smart MoviePy↔Creatomate fallback"),
        ("moviepy_video_generator_v2.py", "MoviePy Video Generator", "FREE local video composition"),
    ]
    for filename, name, desc in vid_tools:
        path = execution / filename
        tools["video_generation"].append({"name": name, "description": desc, "available": path.exists(), "script": str(path)})
    social_tools = [
        ("Instagram Creator MCP", "Post images, carousels, Reels, Stories"),
        ("YouTube Creator MCP", "Upload videos, Shorts, schedule releases"),
        ("TikTok Creator MCP", "Post videos, track analytics"),
        ("X/Twitter Automation", "n8n scheduler + social-media-automation"),
    ]
    for name, desc in social_tools:
        tools["social_posting"].append({"name": name, "description": desc, "available": True})
    content_tools = [
        ("video_jumpcut.py", "Video Jump Cut", "Remove silence, create jump cuts"),
        ("video_ads.py", "Video Ads Generator", "Automated ad creative generation"),
        ("branded_pdf_engine.py", "Branded PDF Engine", "Professional branded PDFs"),
    ]
    for filename, name, desc in content_tools:
        path = execution / filename
        tools["content_creation"].append({"name": name, "description": desc, "available": path.exists(), "script": str(path)})
    return jsonify(tools)


# ---------------------------------------------------------------------------
# Routes — Projects (CRUD + Workflow)
# ---------------------------------------------------------------------------

@app.route("/api/projects")
def api_projects():
    conn = get_db()
    projects = rows_to_list(conn.execute(
        "SELECT * FROM projects WHERE status != 'archived' ORDER BY updated_at DESC"
    ).fetchall())
    for p in projects:
        steps = rows_to_list(conn.execute(
            "SELECT * FROM workflow_steps WHERE project_id=? ORDER BY step_order", (p["id"],)
        ).fetchall())
        p["steps"] = steps
        total = len(steps)
        done = sum(1 for s in steps if s["status"] == "completed")
        p["progress"] = round(done / total * 100) if total else 0
        p["asset_count"] = conn.execute("SELECT COUNT(*) FROM assets WHERE project_id=?", (p["id"],)).fetchone()[0]
    conn.close()
    return jsonify(projects)


@app.route("/api/projects", methods=["POST"])
def api_create_project():
    data = request.json or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400
    conn = get_db()
    pid = create_project(conn, name, data.get("niche", ""), data.get("platform", "instagram"), data.get("description", ""))
    # Update optional fields
    fields = ["persona_name", "persona_bio", "character_prompt", "voice_style", "posting_schedule", "monetization_plan", "notes"]
    updates = []
    values = []
    for f in fields:
        if f in data and data[f]:
            updates.append(f"{f}=?")
            values.append(data[f])
    if updates:
        values.append(pid)
        conn.execute(f"UPDATE projects SET {','.join(updates)} WHERE id=?", values)
        conn.commit()
    conn.close()
    return jsonify({"id": pid, "success": True})


@app.route("/api/projects/<int:pid>")
def api_get_project(pid):
    conn = get_db()
    project = row_to_dict(conn.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone())
    if not project:
        conn.close()
        return jsonify({"error": "Not found"}), 404
    project["steps"] = rows_to_list(conn.execute(
        "SELECT * FROM workflow_steps WHERE project_id=? ORDER BY step_order", (pid,)
    ).fetchall())
    project["assets"] = rows_to_list(conn.execute(
        "SELECT * FROM assets WHERE project_id=? ORDER BY created_at DESC", (pid,)
    ).fetchall())
    project["prompts"] = rows_to_list(conn.execute(
        "SELECT * FROM prompts WHERE project_id=? ORDER BY created_at DESC", (pid,)
    ).fetchall())
    conn.close()
    return jsonify(project)


@app.route("/api/projects/<int:pid>", methods=["PUT"])
def api_update_project(pid):
    data = request.json or {}
    conn = get_db()
    allowed = ["name", "niche", "platform", "description", "status", "persona_name", "persona_bio",
               "character_prompt", "voice_style", "posting_schedule", "monetization_plan", "notes"]
    updates = []
    values = []
    for f in allowed:
        if f in data:
            updates.append(f"{f}=?")
            values.append(data[f])
    if updates:
        updates.append("updated_at=?")
        values.append(datetime.now().isoformat())
        values.append(pid)
        conn.execute(f"UPDATE projects SET {','.join(updates)} WHERE id=?", values)
        conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/projects/<int:pid>", methods=["DELETE"])
def api_delete_project(pid):
    conn = get_db()
    conn.execute("UPDATE projects SET status='archived', updated_at=? WHERE id=?", (datetime.now().isoformat(), pid))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Routes — Workflow Steps
# ---------------------------------------------------------------------------

@app.route("/api/projects/<int:pid>/steps/<int:sid>", methods=["PUT"])
def api_update_step(pid, sid):
    data = request.json or {}
    conn = get_db()
    updates = []
    values = []
    if "status" in data:
        updates.append("status=?")
        values.append(data["status"])
        if data["status"] == "completed":
            updates.append("completed_at=?")
            values.append(datetime.now().isoformat())
    if "notes" in data:
        updates.append("notes=?")
        values.append(data["notes"])
    if "output_files" in data:
        updates.append("output_files=?")
        values.append(json.dumps(data["output_files"]))
    if updates:
        values.append(sid)
        conn.execute(f"UPDATE workflow_steps SET {','.join(updates)} WHERE id=?", values)
        conn.execute("UPDATE projects SET updated_at=? WHERE id=?", (datetime.now().isoformat(), pid))
        conn.commit()
    conn.close()
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Routes — Method Tracker
# ---------------------------------------------------------------------------

@app.route("/api/methods/tracker")
def api_method_tracker():
    conn = get_db()
    methods = rows_to_list(conn.execute("SELECT * FROM method_tracker ORDER BY category, method_name").fetchall())
    conn.close()
    return jsonify(methods)


@app.route("/api/methods/tracker/<int:mid>", methods=["PUT"])
def api_update_method(mid):
    data = request.json or {}
    conn = get_db()
    allowed = ["status", "my_notes", "results", "rating", "difficulty"]
    updates = ["updated_at=?"]
    values = [datetime.now().isoformat()]
    for f in allowed:
        if f in data:
            updates.append(f"{f}=?")
            values.append(data[f])
    if "status" in data and data["status"] in ("tried", "works", "doesnt_work"):
        updates.append("tried_at=?")
        values.append(datetime.now().isoformat())
    values.append(mid)
    conn.execute(f"UPDATE method_tracker SET {','.join(updates)} WHERE id=?", values)
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/methods/tracker", methods=["POST"])
def api_add_method():
    data = request.json or {}
    name = data.get("method_name", "").strip()
    if not name:
        return jsonify({"error": "Method name required"}), 400
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO method_tracker (method_name, category, source, difficulty, cost_estimate, tools_needed) VALUES (?,?,?,?,?,?)",
            (name, data.get("category", ""), data.get("source", ""), data.get("difficulty", "medium"), data.get("cost_estimate", ""), data.get("tools_needed", "")),
        )
        conn.commit()
    except Exception:
        conn.close()
        return jsonify({"error": "Method already exists"}), 409
    conn.close()
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Routes — Assets
# ---------------------------------------------------------------------------

@app.route("/api/projects/<int:pid>/assets", methods=["POST"])
def api_add_asset(pid):
    data = request.json or {}
    conn = get_db()
    conn.execute(
        "INSERT INTO assets (project_id, asset_type, name, file_path, prompt_used, tool_used, notes) VALUES (?,?,?,?,?,?,?)",
        (pid, data.get("asset_type", "image"), data.get("name", "Untitled"), data.get("file_path", ""),
         data.get("prompt_used", ""), data.get("tool_used", ""), data.get("notes", "")),
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/assets/<int:aid>", methods=["PUT"])
def api_update_asset(aid):
    data = request.json or {}
    conn = get_db()
    allowed = ["name", "rating", "notes", "prompt_used", "tool_used"]
    updates = []
    values = []
    for f in allowed:
        if f in data:
            updates.append(f"{f}=?")
            values.append(data[f])
    if updates:
        values.append(aid)
        conn.execute(f"UPDATE assets SET {','.join(updates)} WHERE id=?", values)
        conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/assets/<int:aid>", methods=["DELETE"])
def api_delete_asset(aid):
    conn = get_db()
    conn.execute("DELETE FROM assets WHERE id=?", (aid,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Routes — Prompt Library
# ---------------------------------------------------------------------------

@app.route("/api/prompts")
def api_prompts_list():
    conn = get_db()
    prompts = rows_to_list(conn.execute("SELECT * FROM prompts ORDER BY is_favorite DESC, created_at DESC").fetchall())
    conn.close()
    return jsonify(prompts)


@app.route("/api/prompts", methods=["POST"])
def api_save_prompt():
    data = request.json or {}
    name = data.get("name", "").strip()
    text = data.get("prompt_text", "").strip()
    if not name or not text:
        return jsonify({"error": "Name and prompt text required"}), 400
    conn = get_db()
    conn.execute(
        "INSERT INTO prompts (project_id, name, category, tool, prompt_text, notes) VALUES (?,?,?,?,?,?)",
        (data.get("project_id"), name, data.get("category", "general"), data.get("tool", ""), text, data.get("notes", "")),
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/prompts/<int:pid>", methods=["PUT"])
def api_update_prompt(pid):
    data = request.json or {}
    conn = get_db()
    allowed = ["name", "category", "tool", "prompt_text", "result_quality", "notes", "is_favorite"]
    updates = []
    values = []
    for f in allowed:
        if f in data:
            updates.append(f"{f}=?")
            values.append(data[f])
    if updates:
        values.append(pid)
        conn.execute(f"UPDATE prompts SET {','.join(updates)} WHERE id=?", values)
        conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/prompts/<int:pid>", methods=["DELETE"])
def api_delete_prompt(pid):
    conn = get_db()
    conn.execute("DELETE FROM prompts WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Routes — Image Generation
# ---------------------------------------------------------------------------

@app.route("/api/generate/image", methods=["POST"])
def api_generate_image():
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
        return jsonify({"success": result.returncode == 0, "output": result.stdout, "error": result.stderr})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("MIKOS_LAB_PORT", 8766))
    print(f"\n  Miko's Lab — AI Avatar Workshop")
    print(f"  http://127.0.0.1:{port}\n")
    app.run(host="127.0.0.1", port=port, debug=False)
