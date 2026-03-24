#!/usr/bin/env python3
"""
Session Summarizer — auto-captures session work to docs/session-history.md.

Reads git log and diff to generate a structured summary of what was done,
what changed, and what's still open. Prepends to session-history.md so
newest entries appear first.

Usage:
    python execution/session_summarizer.py                    # write summary
    python execution/session_summarizer.py --preview          # print only
    python execution/session_summarizer.py --since "2 hours ago"
"""

import argparse
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_HISTORY = os.path.join(REPO_ROOT, "docs", "session-history.md")


def run_git(args, cwd=None):
    """Run a git command and return stdout. Returns empty string on failure."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd or REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def get_commits(since):
    """Get recent commits within the time window."""
    log = run_git([
        "log",
        "--since={}".format(since),
        "--pretty=format:%H|%s",
        "--no-merges",
    ])
    if not log:
        return []
    commits = []
    for line in log.strip().split("\n"):
        if "|" in line:
            sha, msg = line.split("|", 1)
            commits.append({"sha": sha.strip(), "msg": msg.strip()})
    return commits


def get_diff_stat(since):
    """Get diff --stat for commits in the time window."""
    # Find the earliest commit in range to diff against
    earliest = run_git([
        "log",
        "--since={}".format(since),
        "--pretty=format:%H",
        "--no-merges",
        "--reverse",
    ])
    if not earliest:
        return "", 0
    first_sha = earliest.split("\n")[0].strip()
    # Diff from parent of earliest commit to HEAD
    stat = run_git(["diff", "--stat", "{}~1..HEAD".format(first_sha)])
    if not stat:
        # Fallback: diff from the commit itself
        stat = run_git(["diff", "--stat", "{}..HEAD".format(first_sha)])

    # Count files from the summary line (e.g., "15 files changed, 200 insertions...")
    file_count = 0
    match = re.search(r"(\d+) files? changed", stat)
    if match:
        file_count = int(match.group(1))
    return stat, file_count


def get_uncommitted():
    """Get list of uncommitted changes (staged + unstaged + untracked)."""
    status = run_git(["status", "--short", "--porcelain"])
    if not status:
        return []
    changes = []
    for line in status.strip().split("\n"):
        if not line:
            continue
        # Parse git status --porcelain: XY PATH or XY -> PATH (renames)
        # Use regex to robustly extract status and path regardless of spacing
        m = re.match(r'^([MADRCU?! ]{1,2})\s+(.+)$', line)
        if not m:
            continue
        indicator = m.group(1).strip()
        filepath = m.group(2).strip()
        # Handle renames: "old -> new"
        if " -> " in filepath:
            filepath = filepath.split(" -> ")[-1]
        # Skip common noise files
        if any(skip in filepath for skip in ["__pycache__", ".pyc", ".DS_Store"]):
            continue
        if indicator == "??":
            changes.append("Untracked: {}".format(filepath))
        elif "M" in indicator:
            changes.append("Modified: {}".format(filepath))
        elif "A" in indicator:
            changes.append("Staged: {}".format(filepath))
        elif "D" in indicator:
            changes.append("Deleted: {}".format(filepath))
        elif "R" in indicator:
            changes.append("Renamed: {}".format(filepath))
        else:
            changes.append("{}: {}".format(indicator, filepath))
    return changes


def group_changes_by_area(stat_output):
    """Group changed files by top-level project area."""
    areas = defaultdict(list)
    for line in stat_output.split("\n"):
        line = line.strip()
        # Skip the summary line
        if "files changed" in line or "file changed" in line:
            continue
        if not line or "|" not in line:
            continue
        filepath = line.split("|")[0].strip()
        # Determine area from path
        parts = filepath.split("/")
        if len(parts) >= 3 and parts[0] == "projects":
            if parts[1] == "marceau-solutions" and len(parts) >= 4:
                area = "projects/marceau-solutions/{}/".format(parts[2])
            else:
                area = "projects/{}/".format(parts[1])
        elif parts[0] in ("execution", "docs", "scripts", ".claude", "directives"):
            area = "{}/".format(parts[0])
        else:
            area = "root"

        # Truncate long filenames
        display = filepath if len(filepath) < 80 else "...{}".format(filepath[-60:])
        areas[area].append(display)
    return dict(areas)


def extract_focus(commits):
    """Derive session focus from commit messages."""
    if not commits:
        return "No commits in time window"

    # Look for common prefixes
    prefixes = []
    for c in commits:
        msg = c["msg"]
        # Extract prefix like "feat:", "fix:", "refactor:"
        m = re.match(r"^(\w+):\s*(.+)", msg)
        if m:
            prefixes.append(m.group(1))

    # Build focus from commit messages — take the most descriptive parts
    topics = []
    for c in commits:
        msg = c["msg"]
        # Strip conventional commit prefix
        msg = re.sub(r"^\w+:\s*", "", msg)
        # Take first clause (before em-dash or comma list)
        msg = re.split(r"\s*[—,]", msg)[0].strip()
        if msg and msg not in topics:
            topics.append(msg)

    if len(topics) <= 3:
        return "; ".join(topics)
    # Too many — summarize
    return "{}; and {} more changes".format("; ".join(topics[:3]), len(topics) - 3)


def extract_completed(commits):
    """Extract completed items from commit messages."""
    if not commits:
        return ["No commits recorded"]
    items = []
    for c in commits:
        msg = c["msg"]
        # Clean up conventional commit prefix for readability
        msg = re.sub(r"^(\w+):\s*", r"[\1] ", msg)
        items.append(msg)
    return items


def build_summary(since):
    """Build the full session summary."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    commits = get_commits(since)
    stat_output, file_count = get_diff_stat(since)
    uncommitted = get_uncommitted()
    areas = group_changes_by_area(stat_output)
    focus = extract_focus(commits)
    completed = extract_completed(commits)

    lines = []
    lines.append("### Session {}".format(now))
    lines.append("**Focus**: {}".format(focus))

    lines.append("**Completed**:")
    for item in completed:
        lines.append("- {}".format(item))

    lines.append("**Files Changed**: {} files".format(file_count if file_count else "0"))

    if areas:
        lines.append("**Key Changes**:")
        for area in sorted(areas.keys()):
            files = areas[area]
            if len(files) <= 3:
                lines.append("- `{}` — {}".format(area, ", ".join(files)))
            else:
                lines.append("- `{}` — {} files ({}, ...)".format(
                    area, len(files), ", ".join(files[:2])
                ))

    if uncommitted:
        lines.append("**Open Threads**:")
        # Cap at 10 to avoid noise
        for item in uncommitted[:10]:
            lines.append("- {}".format(item))
        if len(uncommitted) > 10:
            lines.append("- ...and {} more uncommitted changes".format(
                len(uncommitted) - 10
            ))
    else:
        lines.append("**Open Threads**: None (clean working tree)")

    # Infer next session from open threads
    lines.append("**Next Session**:")
    if uncommitted:
        lines.append("- Review and commit/discard {} uncommitted changes".format(
            len(uncommitted)
        ))
    if not commits:
        lines.append("- No commits found — check if work was done outside the time window (try --since)")
    else:
        lines.append("- Continue from latest work")

    return "\n".join(lines)


def prepend_to_history(summary_text):
    """Prepend summary to session-history.md, preserving the header."""
    if os.path.exists(SESSION_HISTORY):
        with open(SESSION_HISTORY, "r") as f:
            content = f.read()
    else:
        content = "# Session History & Learnings\n\nRunning log of significant learnings, decisions, and patterns discovered during development sessions.\n\n---\n"

    # Find the first --- separator (after the header)
    separator_pos = content.find("---")
    if separator_pos == -1:
        # No separator — append after header
        header = content.strip() + "\n\n---\n\n"
        rest = ""
    else:
        header = content[: separator_pos + 3]
        rest = content[separator_pos + 3 :]

    new_content = "{}\n\n{}\n\n---{}".format(header.rstrip(), summary_text, rest)

    with open(SESSION_HISTORY, "w") as f:
        f.write(new_content)

    return SESSION_HISTORY


def main():
    parser = argparse.ArgumentParser(
        description="Generate a session summary from recent git activity"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Print summary without writing to session-history.md",
    )
    parser.add_argument(
        "--since",
        default="8 hours ago",
        help='Time window for git log (default: "8 hours ago")',
    )
    args = parser.parse_args()

    summary = build_summary(args.since)

    if args.preview:
        print(summary)
        print("\n(Preview mode — nothing written. Remove --preview to save.)")
    else:
        path = prepend_to_history(summary)
        print(summary)
        print("\nWritten to: {}".format(path))


if __name__ == "__main__":
    main()
