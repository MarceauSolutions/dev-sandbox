#!/usr/bin/env python3
"""
Session Manager for Interview Prep PowerPoint

Manages active editing sessions so users can continue editing their presentations
without specifying file paths repeatedly.

Session data is stored in .tmp/session.json and tracks:
- Current presentation file
- Original research data
- Uploaded resume (if any)
- Edit history
- Creation timestamp
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Paths
BASE_DIR = Path(__file__).parent.parent
TMP_DIR = BASE_DIR / ".tmp"
SESSION_FILE = TMP_DIR / "session.json"

TMP_DIR.mkdir(exist_ok=True)


def load_session() -> Dict[str, Any]:
    """Load current session data."""
    if SESSION_FILE.exists():
        try:
            with open(SESSION_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_session(session: Dict[str, Any]) -> None:
    """Save session data."""
    session["last_updated"] = datetime.now().isoformat()
    with open(SESSION_FILE, "w") as f:
        json.dump(session, f, indent=2)


def create_session(
    company: str,
    role: str,
    research_file: str,
    pptx_file: str,
    resume_file: Optional[str] = None,
    theme: str = "modern"
) -> Dict[str, Any]:
    """Create a new editing session."""
    session = {
        "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "company": company,
        "role": role,
        "research_file": research_file,
        "pptx_file": pptx_file,
        "resume_file": resume_file,
        "theme": theme,
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "edit_history": [],
        "slide_count": 0,
        "status": "active"
    }
    save_session(session)
    return session


def get_active_session() -> Optional[Dict[str, Any]]:
    """Get the current active session, if any."""
    session = load_session()
    if session and session.get("status") == "active":
        return session
    return None


def get_current_pptx() -> Optional[str]:
    """Get the current PowerPoint file path."""
    session = get_active_session()
    if session:
        pptx_path = TMP_DIR / session["pptx_file"]
        if pptx_path.exists():
            return str(pptx_path)
    return None


def get_current_pptx_name() -> Optional[str]:
    """Get just the filename of the current PowerPoint."""
    session = get_active_session()
    if session:
        return session.get("pptx_file")
    return None


def log_edit(action: str, details: Dict[str, Any]) -> None:
    """Log an edit action to the session history."""
    session = load_session()
    if session:
        if "edit_history" not in session:
            session["edit_history"] = []
        session["edit_history"].append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details
        })
        save_session(session)


def update_slide_count(count: int) -> None:
    """Update the slide count in the session."""
    session = load_session()
    if session:
        session["slide_count"] = count
        save_session(session)


def close_session() -> None:
    """Mark the current session as complete."""
    session = load_session()
    if session:
        session["status"] = "completed"
        session["completed_at"] = datetime.now().isoformat()
        save_session(session)


def get_session_summary() -> str:
    """Get a human-readable summary of the current session."""
    session = get_active_session()
    if not session:
        return "No active session. Create a new presentation first."

    summary = f"""
=== Active Interview Prep Session ===
Company: {session.get('company', 'Unknown')}
Role: {session.get('role', 'Unknown')}
Theme: {session.get('theme', 'modern')}
PowerPoint: {session.get('pptx_file', 'None')}
Slides: {session.get('slide_count', 'Unknown')}
Resume: {'Yes' if session.get('resume_file') else 'No'}
Edits Made: {len(session.get('edit_history', []))}
Created: {session.get('created_at', 'Unknown')[:19]}
=====================================
"""
    return summary.strip()


def list_recent_sessions(limit: int = 5) -> str:
    """List recent session files for reference."""
    # Look for research JSON files
    research_files = list(TMP_DIR.glob("interview_research_*.json"))
    research_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    if not research_files:
        return "No previous sessions found."

    lines = ["Recent Interview Prep Sessions:", ""]
    for f in research_files[:limit]:
        try:
            with open(f) as file:
                data = json.load(file)
            company = data.get("company_overview", {}).get("name", "Unknown")
            role = data.get("role_analysis", {}).get("title", "Unknown")
            mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            lines.append(f"  - {company} | {role} | {mtime}")
            lines.append(f"    Research: {f.name}")
            pptx = f.name.replace("interview_research_", "interview_prep_").replace(".json", ".pptx")
            if (TMP_DIR / pptx).exists():
                lines.append(f"    PowerPoint: {pptx}")
            lines.append("")
        except:
            continue

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Interview Prep Session Manager")
    parser.add_argument("--status", action="store_true", help="Show current session status")
    parser.add_argument("--list", action="store_true", help="List recent sessions")
    parser.add_argument("--current", action="store_true", help="Get current PPTX file")
    parser.add_argument("--close", action="store_true", help="Close current session")

    args = parser.parse_args()

    if args.status:
        print(get_session_summary())
    elif args.list:
        print(list_recent_sessions())
    elif args.current:
        pptx = get_current_pptx_name()
        if pptx:
            print(pptx)
        else:
            print("No active session")
    elif args.close:
        close_session()
        print("Session closed")
    else:
        print(get_session_summary())
