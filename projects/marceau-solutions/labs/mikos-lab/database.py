#!/usr/bin/env python3
"""
Miko's Lab SQLite Database — Project Pipeline & Implementation Tracker
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "mikoslab.db"


def get_db():
    """Get database connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_db()
    conn.executescript("""
        -- AI Avatar Projects (the main pipeline)
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            niche TEXT NOT NULL DEFAULT '',
            platform TEXT NOT NULL DEFAULT 'instagram',
            description TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'planning'
                CHECK(status IN ('planning','character_design','content_creation','launched','paused','archived')),
            persona_name TEXT NOT NULL DEFAULT '',
            persona_bio TEXT NOT NULL DEFAULT '',
            character_prompt TEXT NOT NULL DEFAULT '',
            voice_style TEXT NOT NULL DEFAULT '',
            posting_schedule TEXT NOT NULL DEFAULT '',
            monetization_plan TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        -- Workflow steps for each project (tracks progress through Miko's pipeline)
        CREATE TABLE IF NOT EXISTS workflow_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            step_key TEXT NOT NULL,
            step_name TEXT NOT NULL,
            step_order INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK(status IN ('pending','in_progress','completed','skipped')),
            notes TEXT NOT NULL DEFAULT '',
            output_files TEXT NOT NULL DEFAULT '[]',
            completed_at TEXT,
            UNIQUE(project_id, step_key)
        );

        -- Generated assets (images, videos, audio) for each project
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            asset_type TEXT NOT NULL CHECK(asset_type IN ('image','video','audio','document')),
            name TEXT NOT NULL,
            file_path TEXT NOT NULL DEFAULT '',
            prompt_used TEXT NOT NULL DEFAULT '',
            tool_used TEXT NOT NULL DEFAULT '',
            rating INTEGER DEFAULT NULL CHECK(rating BETWEEN 1 AND 5),
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        -- Implementation tracker: which Miko methods have you tried?
        CREATE TABLE IF NOT EXISTS method_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            method_name TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL DEFAULT '',
            source TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'not_started'
                CHECK(status IN ('not_started','learning','tried','works','doesnt_work','needs_revisit')),
            difficulty TEXT NOT NULL DEFAULT 'medium'
                CHECK(difficulty IN ('easy','medium','hard')),
            cost_estimate TEXT NOT NULL DEFAULT '',
            tools_needed TEXT NOT NULL DEFAULT '',
            my_notes TEXT NOT NULL DEFAULT '',
            results TEXT NOT NULL DEFAULT '',
            rating INTEGER DEFAULT NULL CHECK(rating BETWEEN 1 AND 5),
            tried_at TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        -- Prompt library: save and reuse prompts that work
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'general'
                CHECK(category IN ('character','video','voice','image','social','general')),
            tool TEXT NOT NULL DEFAULT '',
            prompt_text TEXT NOT NULL,
            result_quality INTEGER DEFAULT NULL CHECK(result_quality BETWEEN 1 AND 5),
            notes TEXT NOT NULL DEFAULT '',
            is_favorite INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()


# ---- Default workflow steps for new projects ----
DEFAULT_WORKFLOW = [
    ("niche_research", "Niche Research & Validation", 1),
    ("persona_design", "Persona Design & Bio", 2),
    ("character_creation", "Character Image Creation", 3),
    ("starting_frames", "Starting Frame Library", 4),
    ("voice_setup", "Voice & Audio Setup", 5),
    ("first_video", "First Video Generation", 6),
    ("content_batch", "Content Batch (5-10 pieces)", 7),
    ("platform_setup", "Platform Account Setup", 8),
    ("first_post", "First Post Published", 9),
    ("posting_rhythm", "Consistent Posting (7 days)", 10),
    ("monetization", "Monetization Activation", 11),
]

# ---- Default methods to seed from Miko's knowledge ----
DEFAULT_METHODS = [
    ("NanoBanana Pro Character Creation", "character-creation", "THE COMPLETE AI INFLUENCER SYSTEM GUIDE", "medium", "NanoBanana subscription", "NanoBanana Pro"),
    ("Sora 2 Character Cameos", "character-creation", "AI Influencer Money Printing Blueprint", "medium", "ChatGPT Pro ($200/mo)", "Sora 2 Pro"),
    ("Ideogram Character Fill", "character-creation", "THE COMPLETE AI INFLUENCER SYSTEM GUIDE", "easy", "Ideogram free tier", "Ideogram"),
    ("Image-to-Video (I2V) Workflow", "video-generation", "MIKO_METHODS_SUMMARY", "medium", "Varies by tool", "Sora 2, VEO 3, Seedance 2"),
    ("Sora 2 Pro Storyboard Mode", "video-generation", "Sora Video Prompt Structure System Guide", "medium", "ChatGPT Pro ($200/mo) or kie.ai", "Sora 2 Pro"),
    ("VEO 3 Video Generation", "video-generation", "VEO 3.1 VS SORA 2", "easy", "Google AI (free tier)", "VEO 3 / 3.1"),
    ("Seedance 2 Realistic Motion", "video-generation", "Telegram posts", "hard", "doubao.com access", "Seedance 2"),
    ("Seedance 2 Face Bypass", "video-generation", "Telegram posts", "hard", "Same as Seedance 2", "Seedance 2 + image gen"),
    ("MiniMax Voice Generation", "voice-audio", "How to Create Realistic AI Voices", "easy", "$5/mo for 120 min", "MiniMax"),
    ("Resemble AI Audio Fix", "voice-audio", "How to Create Realistic AI Voices", "medium", "Per-use pricing", "Resemble AI"),
    ("ElevenLabs Voice Cloning", "voice-audio", "How to Clone Any Creator's Brain", "easy", "ElevenLabs subscription", "ElevenLabs"),
    ("AI UGC for Brands", "monetization", "Full guide on making AI UGC", "medium", "Tool costs only", "Sora 2, MiniMax"),
    ("AI Content Agency Model", "monetization", "THE AI CONTENT AGENCY BLUEPRINT", "hard", "$2K-10K/client", "Full stack"),
    ("AI Slideshow Workflow", "advanced", "Full AI slideshow workflow", "easy", "Minimal", "Image gen + video editor"),
    ("VEO 3 Prompt Framework", "video-generation", "VEO 3 Meta Framework (GitHub)", "medium", "Google AI", "VEO 3"),
    ("Get AI Tools 95% Cheaper", "optimization", "How to Get AI Tools for 95% Cheaper", "easy", "Various API access", "API keys"),
    ("Cut Video Costs 60%", "optimization", "How I Cut AI Video Costs By 60%", "easy", "Same tools, smarter use", "I2V workflow"),
    ("AI Personal Brand Building", "getting-started", "HOW TO BUILD AN AI PERSONAL BRAND", "medium", "Platform dependent", "Full stack"),
]


def seed_methods(conn):
    """Seed default methods if table is empty."""
    count = conn.execute("SELECT COUNT(*) FROM method_tracker").fetchone()[0]
    if count == 0:
        for name, cat, source, diff, cost, tools in DEFAULT_METHODS:
            conn.execute(
                "INSERT INTO method_tracker (method_name, category, source, difficulty, cost_estimate, tools_needed) VALUES (?,?,?,?,?,?)",
                (name, cat, source, diff, cost, tools),
            )
        conn.commit()


def create_project(conn, name, niche="", platform="instagram", description=""):
    """Create a new project with default workflow steps."""
    cur = conn.execute(
        "INSERT INTO projects (name, niche, platform, description) VALUES (?,?,?,?)",
        (name, niche, platform, description),
    )
    project_id = cur.lastrowid

    for step_key, step_name, step_order in DEFAULT_WORKFLOW:
        conn.execute(
            "INSERT INTO workflow_steps (project_id, step_key, step_name, step_order) VALUES (?,?,?,?)",
            (project_id, step_key, step_name, step_order),
        )
    conn.commit()
    return project_id


# Initialize on import
init_db()
conn = get_db()
seed_methods(conn)
conn.close()
