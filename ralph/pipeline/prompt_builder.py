#!/usr/bin/env python3
"""
Context-Enriched Prompt Builder — Generates Ralph's prompt with project-specific context.

Instead of Ralph getting a generic prompt, this builds a prompt that includes:
1. Project architecture and tech stack from the PRD
2. Coding standards and patterns from the codebase
3. Learnings from previous Ralph runs (knowledge_base.json)
4. File structure overview
5. Clawdbot's architectural decisions and analysis
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

RALPH_DIR = Path("/home/clawdbot/dev-sandbox/ralph")
BASE_PROMPT = RALPH_DIR / "prompt.md"
KNOWLEDGE_BASE = RALPH_DIR / "pipeline" / "knowledge_base.json"
SANDBOX_DIR = Path("/home/clawdbot/dev-sandbox")


def load_knowledge_base() -> Dict:
    """Load accumulated learnings from previous runs."""
    if KNOWLEDGE_BASE.exists():
        with open(KNOWLEDGE_BASE) as f:
            return json.load(f)
    return {"patterns": [], "gotchas": [], "conventions": []}


def get_file_structure(project_dir: str, max_depth: int = 3) -> str:
    """Get project file structure for context."""
    try:
        result = subprocess.run(
            ["find", project_dir, "-maxdepth", str(max_depth),
             "-type", "f", "-not", "-path", "*/.git/*",
             "-not", "-path", "*/node_modules/*",
             "-not", "-path", "*/__pycache__/*",
             "-not", "-path", "*/venv/*"],
            capture_output=True, text=True, timeout=10
        )
        files = result.stdout.strip().split("\n")
        # Limit output
        if len(files) > 50:
            return "\n".join(files[:50]) + f"\n... and {len(files) - 50} more files"
        return "\n".join(files)
    except Exception:
        return "(Could not read file structure)"


def get_recent_git_context(project_dir: str, limit: int = 5) -> str:
    """Get recent git history for context."""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", f"-{limit}"],
            cwd=project_dir,
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def extract_codebase_patterns(project_dir: str) -> List[str]:
    """Detect coding patterns from existing code."""
    patterns = []
    project_path = Path(project_dir)
    
    # Check for common patterns
    if (project_path / "requirements.txt").exists():
        patterns.append("Python project — use pip/venv for dependencies")
    if (project_path / "package.json").exists():
        patterns.append("Node.js project — use npm/yarn for dependencies")
    if (project_path / "pyproject.toml").exists():
        patterns.append("Modern Python packaging — use pyproject.toml")
    if (project_path / "Makefile").exists():
        patterns.append("Makefile present — check for build/test commands")
    if (project_path / ".env.example").exists():
        patterns.append("Uses .env for configuration — don't commit secrets")
    if (project_path / "tests").exists() or (project_path / "test").exists():
        patterns.append("Has test directory — run tests after changes")
    
    # Check for Python patterns
    py_files = list(project_path.rglob("*.py"))
    if py_files:
        sample = py_files[0].read_text(errors="ignore")[:2000] if py_files else ""
        if "from typing import" in sample:
            patterns.append("Uses typing module for type hints")
        if "async def" in sample:
            patterns.append("Uses async/await patterns")
        if "from fastapi" in sample:
            patterns.append("FastAPI framework — use Depends for DI, Pydantic for schemas")
        if "from sqlalchemy" in sample:
            patterns.append("SQLAlchemy ORM — follow existing model patterns")
    
    return patterns


def build_enhanced_prompt(
    prd_path: str,
    project_dir: Optional[str] = None,
    clawdbot_context: Optional[str] = None,
) -> str:
    """
    Build an enhanced prompt for Ralph that includes project-specific context.
    
    Args:
        prd_path: Path to the PRD JSON
        project_dir: Path to the project code (for codebase analysis)
        clawdbot_context: Additional context from Clawdbot's analysis
    
    Returns:
        Enhanced prompt string
    """
    # Load base prompt
    base_prompt = BASE_PROMPT.read_text()
    
    # Load PRD
    with open(prd_path) as f:
        prd = json.load(f)
    
    # Build context sections
    sections = []
    
    # --- Section 1: Project Context ---
    sections.append("## Project Context (from Clawdbot)")
    sections.append(f"**Project:** {prd.get('projectName', 'Unknown')}")
    sections.append(f"**Description:** {prd.get('description', 'N/A')}")
    
    if "techStack" in prd:
        tech = prd["techStack"]
        if isinstance(tech, dict):
            sections.append(f"**Tech Stack:** {json.dumps(tech, indent=2)}")
        else:
            sections.append(f"**Tech Stack:** {tech}")
    
    if "codingStandards" in prd:
        standards = prd["codingStandards"]
        if isinstance(standards, dict):
            sections.append("**Coding Standards:**")
            for key, value in standards.items():
                if key != "note":
                    sections.append(f"  - {key}: {value}")
        else:
            sections.append(f"**Coding Standards:** {standards}")
    
    # --- Section 2: Quality Requirements ---
    if "qualityChecks" in prd:
        sections.append("\n## Required Quality Checks")
        sections.append("Run ALL of these before committing:")
        for check in prd["qualityChecks"]:
            sections.append(f"  - {check}")
    
    # --- Section 3: Codebase Analysis ---
    if project_dir and Path(project_dir).exists():
        sections.append("\n## Codebase Analysis")
        
        # File structure
        structure = get_file_structure(project_dir)
        if structure:
            sections.append(f"**File Structure:**\n```\n{structure}\n```")
        
        # Detected patterns
        patterns = extract_codebase_patterns(project_dir)
        if patterns:
            sections.append("**Detected Patterns:**")
            for pattern in patterns:
                sections.append(f"  - {pattern}")
        
        # Recent git context
        git_context = get_recent_git_context(project_dir)
        if git_context:
            sections.append(f"**Recent Commits:**\n```\n{git_context}\n```")
    
    # --- Section 4: Knowledge Base (from previous runs) ---
    kb = load_knowledge_base()
    if kb.get("patterns") or kb.get("gotchas"):
        sections.append("\n## Learnings from Previous Runs")
        if kb.get("patterns"):
            sections.append("**Known Patterns:**")
            for pattern in kb["patterns"][-10:]:  # Last 10
                sections.append(f"  - {pattern}")
        if kb.get("gotchas"):
            sections.append("**Known Gotchas:**")
            for gotcha in kb["gotchas"][-10:]:
                sections.append(f"  - ⚠️ {gotcha}")
        if kb.get("conventions"):
            sections.append("**Conventions:**")
            for convention in kb["conventions"][-10:]:
                sections.append(f"  - {convention}")
    
    # --- Section 5: Clawdbot's Analysis ---
    if clawdbot_context:
        sections.append(f"\n## Clawdbot's Analysis\n{clawdbot_context}")
    
    # --- Section 6: Quality Emphasis ---
    sections.append("""
## Quality Standards (Clawdbot Enforced)

Clawdbot will review your output after completion. To pass review:
1. **Every function has a docstring** explaining what it does
2. **Error handling** — no bare except, always log errors
3. **Consistent style** — match existing codebase patterns
4. **No hardcoded values** — use config/constants
5. **Meaningful variable names** — no single letters except loop counters
6. **Tests or testable code** — business logic must be unit-testable
7. **Security basics** — no secrets in code, validate inputs
""")
    
    # Combine: base prompt + context
    enhanced = base_prompt + "\n\n---\n\n" + "\n".join(sections)
    
    return enhanced


def save_enhanced_prompt(
    prd_path: str,
    output_path: Optional[str] = None,
    project_dir: Optional[str] = None,
    clawdbot_context: Optional[str] = None,
) -> str:
    """Build and save the enhanced prompt. Returns the output path."""
    prompt = build_enhanced_prompt(prd_path, project_dir, clawdbot_context)
    
    if output_path is None:
        output_path = str(RALPH_DIR / "prompt_enhanced.md")
    
    with open(output_path, "w") as f:
        f.write(prompt)
    
    return output_path


if __name__ == "__main__":
    import sys
    prd_file = sys.argv[1] if len(sys.argv) > 1 else str(RALPH_DIR / "prd.json")
    project = sys.argv[2] if len(sys.argv) > 2 else None
    
    output = save_enhanced_prompt(prd_file, project_dir=project)
    print(f"Enhanced prompt saved to: {output}")
