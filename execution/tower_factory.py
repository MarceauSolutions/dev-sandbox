#!/usr/bin/env python3
"""
Tower Factory — Create new towers and project scaffolds per CLAUDE.md.

Creates fully compliant tower structures with:
  - src/ with __init__.py and app.py (Flask /health endpoint)
  - workflows/ with __init__.py
  - directives/[name].md
  - VERSION (1.0.0-dev)
  - README.md
  - requirements.txt

Also scaffolds sub-project folders inside existing towers.

Usage:
    # Create a new tower
    python execution/tower_factory.py create-tower real-estate \
        --domain "Real estate lead generation and property management" \
        --capabilities "Property scraping,CRM integration,Showing scheduler" \
        --port 5016

    # Create a sub-project inside an existing tower
    python execution/tower_factory.py create-project lead-generation drip-campaign \
        --description "Automated email drip campaign for cold leads"

    # Dry-run (preview without creating)
    python execution/tower_factory.py create-tower real-estate --dry-run

    # Programmatic use
    from execution.tower_factory import create_tower, create_project
    result = create_tower("real-estate", domain="Real estate ops", port=5016)
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent

# Port registry — avoids collisions with existing towers
USED_PORTS = {
    5010: "monolith (agent_bridge_api)",
    5011: "personal-assistant",
    5012: "lead-generation",
    5013: "ai-systems",
    5014: "amazon-seller",
    5015: "mcp-services",
    8000: "fitness-influencer (FastAPI)",
}


def create_tower(
    name: str,
    domain: str = "",
    capabilities: Optional[List[str]] = None,
    port: int = 0,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Create a new tower with full CLAUDE.md-compliant structure.

    Args:
        name: Tower name (kebab-case, e.g. "real-estate")
        domain: One-line domain description
        capabilities: List of capability strings
        port: Flask port (0 = auto-assign next available)
        dry_run: Preview without creating files

    Returns:
        Dict with created paths and metadata
    """
    capabilities = capabilities or []
    tower_dir = REPO_ROOT / "projects" / name
    directive_path = REPO_ROOT / "directives" / f"{name}.md"

    if tower_dir.exists() and not dry_run:
        return {"success": False, "error": f"Tower already exists: {tower_dir}"}

    # Auto-assign port
    if port == 0:
        port = _next_available_port()

    files = {}

    # src/__init__.py
    files[tower_dir / "src" / "__init__.py"] = f"# {name} tower\n"

    # src/app.py
    files[tower_dir / "src" / "app.py"] = _generate_app_py(name, domain, port)

    # workflows/__init__.py
    files[tower_dir / "workflows" / "__init__.py"] = ""

    # VERSION
    files[tower_dir / "VERSION"] = "1.0.0-dev\n"

    # README.md
    files[tower_dir / "README.md"] = _generate_readme(name, domain, capabilities, port)

    # requirements.txt
    files[tower_dir / "requirements.txt"] = "Flask==2.3.3\npython-dotenv==1.0.0\n"

    # directives/[name].md
    files[directive_path] = _generate_directive(name, domain, capabilities, port)

    if dry_run:
        print(f"\n[DRY RUN] Would create tower: {name}")
        print(f"  Directory: {tower_dir}")
        print(f"  Port: {port}")
        print(f"  Files:")
        for path in sorted(files.keys()):
            print(f"    {path.relative_to(REPO_ROOT)}")
        return {"success": True, "dry_run": True, "files": len(files), "port": port}

    # Create all files
    created = []
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        created.append(str(path.relative_to(REPO_ROOT)))

    print(f"✓ Tower '{name}' created at {tower_dir.relative_to(REPO_ROOT)}")
    print(f"  Port: {port}")
    print(f"  Files: {len(created)}")
    print(f"  Directive: directives/{name}.md")
    print(f"  Start: cd projects/{name} && python -m src.app")

    return {
        "success": True,
        "name": name,
        "port": port,
        "directory": str(tower_dir),
        "files_created": created,
    }


def create_project(
    tower: str,
    project_name: str,
    description: str = "",
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Scaffold a sub-project folder inside an existing tower.

    Args:
        tower: Existing tower name (e.g. "lead-generation")
        project_name: Sub-project name (e.g. "drip-campaign")
        description: What this project does
        dry_run: Preview without creating

    Returns:
        Dict with created paths
    """
    tower_dir = REPO_ROOT / "projects" / tower
    if not tower_dir.exists():
        return {"success": False, "error": f"Tower not found: {tower}"}

    project_dir = tower_dir / project_name

    if project_dir.exists() and not dry_run:
        return {"success": False, "error": f"Project already exists: {project_dir}"}

    files = {}

    # README.md
    files[project_dir / "README.md"] = (
        f"# {project_name.replace('-', ' ').title()}\n\n"
        f"{description or 'Sub-project of ' + tower + ' tower.'}\n\n"
        f"## Structure\n```\n{project_name}/\n"
        f"├── src/          # Python modules\n"
        f"├── templates/    # Configuration templates\n"
        f"├── config/       # Runtime config files\n"
        f"└── README.md\n```\n"
    )

    # src/__init__.py
    files[project_dir / "src" / "__init__.py"] = ""

    # templates/ (empty, ready for content)
    files[project_dir / "templates" / ".gitkeep"] = ""

    # config/ (empty, ready for content)
    files[project_dir / "config" / ".gitkeep"] = ""

    if dry_run:
        print(f"\n[DRY RUN] Would create project: {tower}/{project_name}")
        for path in sorted(files.keys()):
            print(f"    {path.relative_to(REPO_ROOT)}")
        return {"success": True, "dry_run": True, "files": len(files)}

    created = []
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        created.append(str(path.relative_to(REPO_ROOT)))

    print(f"✓ Project '{project_name}' created in {tower}")
    print(f"  Path: projects/{tower}/{project_name}/")
    print(f"  Files: {len(created)}")

    return {
        "success": True,
        "tower": tower,
        "project": project_name,
        "directory": str(project_dir),
        "files_created": created,
    }


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------

def _next_available_port() -> int:
    """Find the next available port not in USED_PORTS."""
    for p in range(5016, 5100):
        if p not in USED_PORTS:
            return p
    return 5099


def _generate_app_py(name: str, domain: str, port: int) -> str:
    mod_name = name.replace("-", "_")
    return f'''#!/usr/bin/env python3
"""
{name.replace("-", " ").title()} Tower - Flask API Server

{domain or "Tower entry point."}

Port: {port}
"""

import os
import logging
from flask import Flask, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({{
            "tower": "{name}",
            "status": "healthy",
            "version": "1.0.0-dev",
        }})

    return app


if __name__ == "__main__":
    port = int(os.getenv("{mod_name.upper()}_PORT", {port}))
    logger.info(f"{name.replace('-', ' ').title()} Tower starting on port {{port}}")
    create_app().run(host="0.0.0.0", port=port, debug=False)
'''


def _generate_readme(name: str, domain: str, capabilities: List[str], port: int) -> str:
    title = name.replace("-", " ").title()
    caps = ""
    if capabilities:
        caps = "\n## Capabilities\n" + "\n".join(f"- {c}" for c in capabilities) + "\n"
    return f"""# {title} Tower

{domain or "Tower for " + title.lower() + " operations."}
{caps}
## Entry Point
- Flask app: `src/app.py` (port {port})
- Start: `cd projects/{name} && python -m src.app`

## Version
1.0.0-dev
"""


def _generate_directive(name: str, domain: str, capabilities: List[str], port: int) -> str:
    title = name.replace("-", " ").title()
    caps = ""
    if capabilities:
        caps = "\n## Core Capabilities\n" + "\n".join(f"- **{c}**" for c in capabilities) + "\n"
    return f"""# {title} Tower Directive

## Domain
{domain or title + " operations."}
{caps}
## Entry Point
- Flask app: `src/app.py` (port {port})

## Integration Points
- **pipeline.db**: Shared coordination layer (if applicable)
- **execution/tower_protocol.py**: Inter-tower messaging

## Current Version
1.0.0-dev
"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Tower Factory — Create towers and projects")
    sub = parser.add_subparsers(dest="command")

    # create-tower
    ct = sub.add_parser("create-tower", help="Create a new tower")
    ct.add_argument("name", help="Tower name (kebab-case)")
    ct.add_argument("--domain", default="", help="Domain description")
    ct.add_argument("--capabilities", default="", help="Comma-separated capabilities")
    ct.add_argument("--port", type=int, default=0, help="Flask port (0=auto)")
    ct.add_argument("--dry-run", action="store_true", help="Preview only")

    # create-project
    cp = sub.add_parser("create-project", help="Create a sub-project inside a tower")
    cp.add_argument("tower", help="Existing tower name")
    cp.add_argument("project", help="Project name")
    cp.add_argument("--description", default="", help="Project description")
    cp.add_argument("--dry-run", action="store_true", help="Preview only")

    args = parser.parse_args()

    if args.command == "create-tower":
        caps = [c.strip() for c in args.capabilities.split(",") if c.strip()] if args.capabilities else []
        create_tower(args.name, domain=args.domain, capabilities=caps,
                     port=args.port, dry_run=args.dry_run)
    elif args.command == "create-project":
        create_project(args.tower, args.project, description=args.description,
                       dry_run=args.dry_run)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
