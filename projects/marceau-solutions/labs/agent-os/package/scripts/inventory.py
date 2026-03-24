#!/usr/bin/env python3
"""AgentOS Inventory — Find existing tools before building new ones."""

import os
import sys
from pathlib import Path

def get_repo_root():
    import subprocess
    try:
        result = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                              capture_output=True, text=True, timeout=5)
        return Path(result.stdout.strip()) if result.returncode == 0 else Path.cwd()
    except Exception:
        return Path.cwd()

def search(keyword, root):
    """Search for tools matching a keyword."""
    keyword_lower = keyword.lower()
    matches = []

    # Search execution/
    exec_dir = root / 'execution'
    if exec_dir.exists():
        for f in exec_dir.glob('*.py'):
            if keyword_lower in f.stem.lower():
                matches.append(f"  execution/{f.name}")

    # Search scripts/
    scripts_dir = root / 'scripts'
    if scripts_dir.exists():
        for f in scripts_dir.iterdir():
            if f.is_file() and keyword_lower in f.stem.lower():
                matches.append(f"  scripts/{f.name}")

    # Search projects/
    projects_dir = root / 'projects'
    if projects_dir.exists():
        for f in projects_dir.rglob('*.py'):
            if keyword_lower in f.stem.lower():
                rel = f.relative_to(root)
                matches.append(f"  {rel}")

    if matches:
        print(f"Matches for '{keyword}':")
        for m in matches:
            print(m)
    else:
        print(f"No matches for '{keyword}'")
    return matches

def list_projects(root):
    """List all projects."""
    projects_dir = root / 'projects'
    if not projects_dir.exists():
        print("No projects/ directory found.")
        return

    print("Projects:")
    for d in sorted(projects_dir.iterdir()):
        if d.is_dir() and not d.name.startswith('.'):
            has_claude = (d / 'CLAUDE.md').exists()
            marker = " (has CLAUDE.md)" if has_claude else ""
            print(f"  {d.name}/{marker}")
            # Show subdirectories
            for sub in sorted(d.iterdir()):
                if sub.is_dir() and not sub.name.startswith('.'):
                    print(f"    {sub.name}/")

def list_scripts(root):
    """List utility scripts."""
    for dirname in ['execution', 'scripts']:
        target = root / dirname
        if not target.exists():
            continue
        files = sorted(target.glob('*'))
        scripts = [f for f in files if f.is_file() and not f.name.startswith('.')]
        print(f"\n{dirname}/ ({len(scripts)} files):")
        for f in scripts:
            print(f"  {f.name}")

def main():
    root = get_repo_root()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  inventory.py search <keyword>  — Find tools by keyword")
        print("  inventory.py list              — List all projects")
        print("  inventory.py scripts           — List utility scripts")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'search' and len(sys.argv) >= 3:
        search(sys.argv[2], root)
    elif cmd == 'list':
        list_projects(root)
    elif cmd == 'scripts':
        list_scripts(root)
    else:
        print(f"Unknown command: {cmd}")
        print("Use: search <keyword>, list, or scripts")

if __name__ == '__main__':
    main()
