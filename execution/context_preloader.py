#!/usr/bin/env python3
"""
Context Pre-loader for dev-sandbox sessions.

Identifies and surfaces the most relevant context files based on a project name
or keyword, so the AI agent can load exactly what it needs at session start.

Usage:
    python execution/context_preloader.py --project fitness
    python execution/context_preloader.py --project hvac --deep
    python execution/context_preloader.py --auto
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS_DIR = ROOT / "projects"
MEMORY_DIR = None  # Resolved at runtime
DOCS_DIR = ROOT / "docs"
SESSION_HISTORY = DOCS_DIR / "session-history.md"
SYSTEM_STATE = DOCS_DIR / "SYSTEM-STATE.md"

# Resolve the Claude memory directory
_MEMORY_CANDIDATES = [
    Path.home() / ".claude" / "projects" / "-Users-williammarceaujr--dev-sandbox" / "memory",
    ROOT / "memory",
]


def _resolve_memory_dir():
    for candidate in _MEMORY_CANDIDATES:
        if candidate.is_dir():
            return candidate
    return None


def fuzzy_match(keyword: str, text: str) -> bool:
    """Case-insensitive fuzzy match — keyword appears as substring or dash-separated token."""
    kw = keyword.lower().replace("-", "").replace("_", "")
    txt = text.lower().replace("-", "").replace("_", "")
    return kw in txt


def find_project_claudes(keyword: str) -> list[str]:
    """Find CLAUDE.md files in projects/ that match the keyword."""
    matches = []
    if not PROJECTS_DIR.is_dir():
        return matches
    for claude_md in sorted(PROJECTS_DIR.rglob("CLAUDE.md")):
        # Skip archived projects
        rel = str(claude_md.relative_to(ROOT))
        if "archived" in rel:
            continue
        # Match against the path components
        path_str = str(claude_md.relative_to(ROOT))
        if fuzzy_match(keyword, path_str):
            matches.append(path_str)
    return matches


def find_relevant_memory(keyword: str) -> list[str]:
    """Find memory files that mention the keyword in their name or content."""
    memory_dir = _resolve_memory_dir()
    if not memory_dir or not memory_dir.is_dir():
        return []
    matches = []
    for f in sorted(memory_dir.iterdir()):
        if not f.is_file() or f.suffix not in (".md", ".txt"):
            continue
        # Check filename match
        if fuzzy_match(keyword, f.stem):
            matches.append(str(f))
            continue
        # Check content match (first 2000 chars for speed)
        try:
            content = f.read_text(errors="replace")[:2000]
            if re.search(re.escape(keyword), content, re.IGNORECASE):
                matches.append(str(f))
        except (OSError, PermissionError):
            continue
    return matches


def find_session_history(keyword: str) -> list[str]:
    """Find recent session history entries mentioning the keyword."""
    if not SESSION_HISTORY.is_file():
        return []
    try:
        content = SESSION_HISTORY.read_text(errors="replace")
    except (OSError, PermissionError):
        return []

    entries = []
    current_entry = []
    current_header = ""

    for line in content.splitlines():
        if line.startswith("## ") or line.startswith("### "):
            if current_entry and current_header:
                block = "\n".join(current_entry)
                if re.search(re.escape(keyword), block, re.IGNORECASE):
                    entries.append(current_header.strip())
            current_header = line
            current_entry = [line]
        else:
            current_entry.append(line)

    # Check last block
    if current_entry and current_header:
        block = "\n".join(current_entry)
        if re.search(re.escape(keyword), block, re.IGNORECASE):
            entries.append(current_header.strip())

    # Return last 5 matches (most recent)
    return entries[-5:]


def find_system_state(keyword: str) -> list[str]:
    """Find system state entries for the keyword."""
    if not SYSTEM_STATE.is_file():
        return []
    try:
        content = SYSTEM_STATE.read_text(errors="replace")
    except (OSError, PermissionError):
        return []

    matches = []
    for line in content.splitlines():
        if re.search(re.escape(keyword), line, re.IGNORECASE):
            matches.append(line.strip())
    return matches[:10]


def find_project_workflows(keyword: str) -> list[str]:
    """Find workflow files in projects matching the keyword."""
    if not PROJECTS_DIR.is_dir():
        return []
    matches = []
    for workflows_dir in PROJECTS_DIR.rglob("workflows"):
        if not workflows_dir.is_dir():
            continue
        # Check if this workflows dir is under a matching project
        rel = str(workflows_dir.relative_to(ROOT))
        if not fuzzy_match(keyword, rel):
            continue
        for f in sorted(workflows_dir.rglob("*.md")):
            matches.append(str(f.relative_to(ROOT)))
    return matches


def auto_detect_keyword() -> str | None:
    """Detect the project area from recently modified git files."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~5", "HEAD"],
            capture_output=True, text=True, cwd=str(ROOT), timeout=10
        )
        files = result.stdout.strip().splitlines() if result.returncode == 0 else []
    except (subprocess.TimeoutExpired, FileNotFoundError):
        files = []

    if not files:
        # Fall back to git status
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, cwd=str(ROOT), timeout=10
            )
            files = [
                line[3:].strip() for line in result.stdout.strip().splitlines()
                if len(line) > 3
            ]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    # Count project directory occurrences
    project_counts: dict[str, int] = {}
    for f in files:
        parts = Path(f).parts
        if len(parts) >= 2 and parts[0] == "projects":
            # Use the deepest meaningful project name
            # e.g., projects/marceau-solutions/fitness/clients/pt-business -> pt-business
            key = parts[-2] if parts[-1].endswith((".py", ".md", ".json", ".html")) else parts[-1]
            # Skip generic dirs
            generic_dirs = {"src", "workflows", "tools", "clients", "__pycache__", "tests", "docs"}
            if key in generic_dirs:
                # Walk backwards to find a meaningful project name
                for i in range(len(parts) - 1, 0, -1):
                    if parts[i] not in generic_dirs and not parts[i].endswith((".py", ".md", ".json", ".html", ".css", ".js")):
                        key = parts[i]
                        break
                else:
                    key = parts[min(2, len(parts) - 1)]
            project_counts[key] = project_counts.get(key, 0) + 1
        elif len(parts) >= 1 and parts[0] == "execution":
            project_counts["execution"] = project_counts.get("execution", 0) + 1

    if not project_counts:
        return None

    # Return the most-touched project
    return max(project_counts, key=project_counts.get)


def read_file_content(path_str: str) -> str:
    """Read file content, resolving relative to ROOT."""
    p = Path(path_str)
    if not p.is_absolute():
        p = ROOT / p
    try:
        return p.read_text(errors="replace")
    except (OSError, PermissionError):
        return f"[Could not read {path_str}]"


def build_suggested_reads(
    project_claudes: list[str],
    memory_files: list[str],
    has_workflows: bool,
    keyword: str,
) -> list[str]:
    """Build an ordered list of suggested reads."""
    reads = []

    # 1. Project CLAUDE.md (most specific first — longest path)
    for c in sorted(project_claudes, key=len, reverse=True)[:3]:
        reads.append(c)

    # 2. System state
    if SYSTEM_STATE.is_file():
        reads.append(f'docs/SYSTEM-STATE.md (search for "{keyword}")')

    # 3. Session history
    if SESSION_HISTORY.is_file():
        reads.append("docs/session-history.md (recent entries)")

    # 4. Memory files
    for m in memory_files[:3]:
        # Show relative path if possible
        try:
            reads.append(str(Path(m).relative_to(ROOT)))
        except ValueError:
            reads.append(m)

    # 5. Workflows
    if has_workflows:
        reads.append(f"[project]/workflows/ (check for procedures)")

    return reads


def run(keyword: str, deep: bool = False):
    """Main execution — find and print the context brief."""
    project_claudes = find_project_claudes(keyword)
    memory_files = find_relevant_memory(keyword)
    session_entries = find_session_history(keyword)
    system_entries = find_system_state(keyword)
    workflow_files = find_project_workflows(keyword)

    suggested = build_suggested_reads(
        project_claudes, memory_files, bool(workflow_files), keyword
    )

    # Print the brief
    print(f"\n=== Context Pre-load: {keyword} ===\n")

    # Project Config
    print("Project Config:")
    if project_claudes:
        for c in project_claudes:
            print(f"  -> {c}")
    else:
        print(f"  (no CLAUDE.md found matching '{keyword}')")

    # Relevant Memory
    print("\nRelevant Memory:")
    if memory_files:
        for m in memory_files:
            try:
                rel = str(Path(m).relative_to(ROOT))
            except ValueError:
                rel = m
            print(f"  -> {rel}")
    else:
        print(f"  (no memory files matching '{keyword}')")

    # Recent Session Activity
    print("\nRecent Session Activity:")
    if session_entries:
        for e in session_entries:
            print(f"  -> {e}")
    else:
        print(f"  (no recent session entries for '{keyword}')")

    # System State
    print("\nSystem State:")
    if system_entries:
        for s in system_entries:
            print(f"  -> {s}")
    else:
        print(f"  (no system state entries for '{keyword}')")

    # Workflows
    if workflow_files:
        print("\nWorkflow Files:")
        for w in workflow_files:
            print(f"  -> {w}")

    # Suggested Reads
    print("\nSuggested Reads (in order):")
    if suggested:
        for i, s in enumerate(suggested, 1):
            print(f"  {i}. {s}")
    else:
        print("  (no suggestions — keyword may not match any project)")

    print("\n===")

    # Deep mode — print file contents
    if deep:
        print("\n\n" + "=" * 60)
        print("DEEP MODE — File Contents")
        print("=" * 60)

        files_to_read = project_claudes[:3] + memory_files[:3]
        for f in files_to_read:
            print(f"\n--- {f} ---")
            print(read_file_content(f))
            print(f"--- end {f} ---\n")


def main():
    parser = argparse.ArgumentParser(
        description="Context pre-loader for dev-sandbox sessions"
    )
    parser.add_argument(
        "--project", "-p",
        help="Project name or keyword to search for"
    )
    parser.add_argument(
        "--auto", "-a",
        action="store_true",
        help="Auto-detect project from recent git changes"
    )
    parser.add_argument(
        "--deep", "-d",
        action="store_true",
        help="Print file contents, not just paths"
    )

    args = parser.parse_args()

    # Determine keyword
    keyword = None
    if args.project:
        keyword = args.project
    elif args.auto:
        keyword = auto_detect_keyword()
        if not keyword:
            print("Could not auto-detect project from recent git changes.")
            print("Try: python execution/context_preloader.py --project <name>")
            sys.exit(1)
        print(f"Auto-detected project area: {keyword}")
    else:
        # If bare positional args, treat as keyword
        remaining = sys.argv[1:]
        # Filter out flags
        remaining = [a for a in remaining if not a.startswith("-")]
        if remaining:
            keyword = remaining[0]
        else:
            parser.print_help()
            sys.exit(1)

    run(keyword, deep=args.deep)


if __name__ == "__main__":
    main()
