#!/usr/bin/env python3
"""
Project & Tool Inventory — Machine-readable discovery for dev-sandbox.

Replaces the prose rule "check existing tools first" with a searchable index.
Used by Claude Code hooks to warn about duplicate tool creation.

Usage:
    python scripts/inventory.py list              # List all projects
    python scripts/inventory.py search <keyword>  # Search everything
    python scripts/inventory.py scripts           # List execution/ scripts
    python scripts/inventory.py project <name>    # Show project details
"""

import os
import re
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS_DIR = ROOT / "projects"
EXECUTION_DIR = ROOT / "execution"
DIRECTIVES_DIR = ROOT / "directives"


def get_docstring(py_file: Path) -> str:
    """Extract first docstring from a Python file."""
    try:
        content = py_file.read_text(errors="replace")
        match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        if match:
            return match.group(1).strip().split("\n")[0]  # First line only
        match = re.search(r"'''(.*?)'''", content, re.DOTALL)
        if match:
            return match.group(1).strip().split("\n")[0]
        return ""
    except Exception:
        return ""


def get_version(project_dir: Path) -> str:
    """Read VERSION file from project directory."""
    version_file = project_dir / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()
    return ""


def scan_projects() -> list[dict]:
    """Scan all projects under projects/."""
    results = []
    if not PROJECTS_DIR.exists():
        return results

    for company_dir in sorted(PROJECTS_DIR.iterdir()):
        if not company_dir.is_dir() or company_dir.name.startswith("."):
            continue

        # Check if this is a direct project (has src/ or VERSION)
        if (company_dir / "src").exists() or (company_dir / "VERSION").exists():
            results.append({
                "name": company_dir.name,
                "path": str(company_dir.relative_to(ROOT)),
                "company": "(root)",
                "version": get_version(company_dir),
                "has_src": (company_dir / "src").exists(),
                "has_workflows": (company_dir / "workflows").exists(),
            })
            continue

        # Otherwise scan subdirectories as projects
        for proj_dir in sorted(company_dir.iterdir()):
            if not proj_dir.is_dir() or proj_dir.name.startswith("."):
                continue
            results.append({
                "name": proj_dir.name,
                "path": str(proj_dir.relative_to(ROOT)),
                "company": company_dir.name,
                "version": get_version(proj_dir),
                "has_src": (proj_dir / "src").exists(),
                "has_workflows": (proj_dir / "workflows").exists(),
            })
    return results


def scan_scripts() -> list[dict]:
    """Scan all execution/*.py scripts."""
    results = []
    if not EXECUTION_DIR.exists():
        return results

    for py_file in sorted(EXECUTION_DIR.glob("*.py")):
        if py_file.name.startswith("__"):
            continue
        results.append({
            "name": py_file.stem,
            "file": str(py_file.relative_to(ROOT)),
            "docstring": get_docstring(py_file),
        })
    return results


def scan_directives() -> list[dict]:
    """Scan all directives/*.md files."""
    results = []
    if not DIRECTIVES_DIR.exists():
        return results

    for md_file in sorted(DIRECTIVES_DIR.glob("*.md")):
        first_line = ""
        try:
            content = md_file.read_text()
            for line in content.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    first_line = line[:100]
                    break
        except Exception:
            pass
        results.append({
            "name": md_file.stem,
            "file": str(md_file.relative_to(ROOT)),
            "summary": first_line,
        })
    return results


def cmd_list():
    """List all projects with key metadata."""
    projects = scan_projects()
    print(f"{'Project':<35} {'Company':<20} {'Version':<12} {'src/':<5} {'workflows/'}")
    print("-" * 90)
    for p in projects:
        if p["company"] == "archived":
            continue
        print(f"{p['name']:<35} {p['company']:<20} {p['version']:<12} "
              f"{'yes' if p['has_src'] else '-':<5} "
              f"{'yes' if p['has_workflows'] else '-'}")
    print(f"\nTotal: {len([p for p in projects if p['company'] != 'archived'])} active projects")


def cmd_scripts():
    """List all execution/ scripts with docstrings."""
    scripts = scan_scripts()
    print(f"{'Script':<45} {'Description'}")
    print("-" * 90)
    for s in scripts:
        desc = s["docstring"][:50] if s["docstring"] else "(no docstring)"
        print(f"{s['name']:<45} {desc}")
    print(f"\nTotal: {len(scripts)} scripts in execution/")


def cmd_search(keyword: str):
    """Search projects, scripts, and directives for a keyword."""
    keyword_lower = keyword.lower()
    found = False

    # Search projects
    projects = scan_projects()
    matching_projects = [p for p in projects if keyword_lower in p["name"].lower()
                         or keyword_lower in p["path"].lower()]
    if matching_projects:
        found = True
        print("=== Projects ===")
        for p in matching_projects:
            print(f"  {p['path']}  (v{p['version']})" if p['version'] else f"  {p['path']}")

    # Search execution scripts (name + docstring)
    scripts = scan_scripts()
    matching_scripts = [s for s in scripts if keyword_lower in s["name"].lower()
                        or keyword_lower in s["docstring"].lower()]
    if matching_scripts:
        found = True
        print("=== Execution Scripts ===")
        for s in matching_scripts:
            desc = s["docstring"][:60] if s["docstring"] else ""
            print(f"  {s['file']}")
            if desc:
                print(f"    {desc}")

    # Search directives
    directives = scan_directives()
    matching_directives = [d for d in directives if keyword_lower in d["name"].lower()
                           or keyword_lower in d["summary"].lower()]
    if matching_directives:
        found = True
        print("=== Directives ===")
        for d in matching_directives:
            print(f"  {d['file']}")

    if not found:
        print(f"No matches for '{keyword}'")
        return 1
    return 0


def cmd_project(name: str):
    """Show detailed info for a specific project."""
    projects = scan_projects()
    matches = [p for p in projects if name.lower() in p["name"].lower()]
    if not matches:
        print(f"No project matching '{name}'")
        return 1

    for p in matches:
        proj_path = ROOT / p["path"]
        print(f"Project: {p['name']}")
        print(f"Path:    {p['path']}")
        print(f"Company: {p['company']}")
        print(f"Version: {p['version'] or '(none)'}")
        print()

        # List src/ files
        src_dir = proj_path / "src"
        if src_dir.exists():
            py_files = list(src_dir.glob("*.py"))
            if py_files:
                print("Source files:")
                for f in sorted(py_files):
                    doc = get_docstring(f)
                    print(f"  {f.name}: {doc[:60]}" if doc else f"  {f.name}")

        # List workflows
        wf_dir = proj_path / "workflows"
        if wf_dir.exists():
            md_files = list(wf_dir.glob("*.md"))
            if md_files:
                print("Workflows:")
                for f in sorted(md_files):
                    print(f"  {f.name}")

        # Check for CLAUDE.md
        claude_md = proj_path / "CLAUDE.md"
        if claude_md.exists():
            print(f"Has project CLAUDE.md: yes")

        print()
    return 0


def cmd_json():
    """Output full inventory as JSON (for programmatic use)."""
    inventory = {
        "projects": scan_projects(),
        "scripts": scan_scripts(),
        "directives": scan_directives(),
    }
    print(json.dumps(inventory, indent=2))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    cmd = sys.argv[1]

    if cmd == "list":
        cmd_list()
    elif cmd == "scripts":
        cmd_scripts()
    elif cmd == "search" and len(sys.argv) >= 3:
        return cmd_search(" ".join(sys.argv[2:]))
    elif cmd == "project" and len(sys.argv) >= 3:
        return cmd_project(sys.argv[2])
    elif cmd == "json":
        cmd_json()
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
