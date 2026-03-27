#!/usr/bin/env python3
"""
Safe Git Save — Commit and push tracked changes without risk of leaking secrets.

Safety rules:
  1. Only stages files already tracked by git (never `git add .`)
  2. New files must be added manually first (`git add <file>`)
  3. Skips .env, token*.json, credentials.json, *.db, logs/ via .gitignore
  4. Pulls before pushing (avoids force-push)
  5. Logs every action to git_save_log.md (which is gitignored)
  6. Never auto-runs — must be explicitly called

Usage:
    python3 execution/safe_git_save.py "Added daily loop and morning digest"
    python3 execution/safe_git_save.py                    # Default message
    python3 execution/safe_git_save.py --dry-run          # Preview without committing
    python3 execution/safe_git_save.py --include-new      # Also stage untracked .py/.md files

Shortcut:
    bash scripts/save.sh "my changes"
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = REPO_ROOT / "git_save_log.md"

# Files that must NEVER be staged, even if tracked
NEVER_STAGE = {
    ".env", ".env.local", ".env.production",
    "token.json", "token_sheets.json", "token_marceausolutions.json",
    "token_gmail_compose.json", "token.json.bak",
    "credentials.json",
}

# Extensions that must never be staged
NEVER_EXTENSIONS = {".db", ".db-shm", ".db-wal", ".db-journal", ".log"}

# Directories whose contents should never be staged
NEVER_DIRS = {"node_modules", "__pycache__", ".tmp", "logs"}


def run(cmd: list, **kwargs) -> subprocess.CompletedProcess:
    """Run a git command and return result."""
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT), **kwargs)


def get_status() -> dict:
    """Get current git status summary."""
    result = run(["git", "status", "--porcelain"])
    lines = [l for l in result.stdout.strip().split("\n") if l.strip()]

    modified = [l[3:] for l in lines if l.startswith(" M")]
    deleted = [l[3:] for l in lines if l.startswith(" D")]
    untracked = [l[3:] for l in lines if l.startswith("??")]
    staged = [l[3:] for l in lines if l[0] in "MADR"]

    return {
        "modified": modified,
        "deleted": deleted,
        "untracked": untracked,
        "staged": staged,
        "total_changes": len(modified) + len(deleted) + len(staged),
    }


def is_safe_to_stage(filepath: str) -> bool:
    """Check if a file is safe to stage (not a secret or binary)."""
    name = Path(filepath).name
    ext = Path(filepath).suffix

    if name in NEVER_STAGE:
        return False
    if ext in NEVER_EXTENSIONS:
        return False
    if any(d in filepath for d in NEVER_DIRS):
        return False

    return True


def safe_save(message: str = "", dry_run: bool = False, include_new: bool = False) -> dict:
    """Safely commit and push tracked changes.

    Args:
        message: Commit message (auto-generated if empty)
        dry_run: Preview without committing
        include_new: Also stage new .py and .md files (careful)

    Returns:
        dict with result details
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Get current status
    status = get_status()

    if status["total_changes"] == 0 and not status["modified"] and not include_new:
        print("Nothing to save — working tree is clean.")
        return {"saved": False, "reason": "clean"}

    # Stage modified and deleted tracked files (safe — already in git)
    safe_files = []
    skipped_files = []

    for f in status["modified"] + status["deleted"]:
        if is_safe_to_stage(f):
            safe_files.append(f)
        else:
            skipped_files.append(f)

    # Optionally stage new .py/.md files
    if include_new:
        safe_extensions = {".py", ".md", ".txt", ".json", ".plist", ".sh"}
        for f in status["untracked"]:
            ext = Path(f).suffix
            if ext in safe_extensions and is_safe_to_stage(f):
                safe_files.append(f)

    if not safe_files:
        print("No safe files to stage.")
        if skipped_files:
            print(f"Skipped {len(skipped_files)} sensitive/binary files: {skipped_files[:5]}")
        return {"saved": False, "reason": "nothing_safe", "skipped": skipped_files}

    # Generate commit message
    if not message:
        message = f"auto: safe save — {timestamp}"

    if dry_run:
        print(f"\n[DRY RUN] Would commit {len(safe_files)} files:")
        for f in safe_files[:20]:
            print(f"  + {f}")
        if len(safe_files) > 20:
            print(f"  ... and {len(safe_files) - 20} more")
        if skipped_files:
            print(f"\nSkipped {len(skipped_files)} sensitive files:")
            for f in skipped_files[:5]:
                print(f"  - {f}")
        print(f"\nMessage: {message}")
        return {"saved": False, "dry_run": True, "files": len(safe_files)}

    # Stage safe files
    for f in safe_files:
        run(["git", "add", f])

    # Pull first (avoid conflicts)
    pull_result = run(["git", "pull", "--rebase", "origin", "main"])
    if pull_result.returncode != 0:
        # If pull fails, try without rebase
        pull_result = run(["git", "pull", "origin", "main"])

    # Commit
    commit_result = run(["git", "commit", "-m", message])
    if commit_result.returncode != 0:
        print(f"Commit failed: {commit_result.stderr[:200]}")
        return {"saved": False, "error": commit_result.stderr[:200]}

    # Push
    push_result = run(["git", "push", "origin", "main"])
    pushed = push_result.returncode == 0

    if not pushed:
        print(f"Push failed (commit saved locally): {push_result.stderr[:200]}")
        print("Run manually: git push origin main")

    # Log
    log_entry = f"| {timestamp} | {len(safe_files)} files | {'pushed' if pushed else 'local only'} | {message} |\n"
    with open(LOG_FILE, "a") as f:
        if not LOG_FILE.exists() or LOG_FILE.stat().st_size == 0:
            f.write("| Date | Files | Status | Message |\n|------|-------|--------|--------|\n")
        f.write(log_entry)

    print(f"\n✓ Committed {len(safe_files)} files")
    print(f"  Message: {message}")
    print(f"  Pushed: {'yes' if pushed else 'no (saved locally)'}")
    if skipped_files:
        print(f"  Skipped: {len(skipped_files)} sensitive files")

    return {
        "saved": True,
        "files": len(safe_files),
        "pushed": pushed,
        "message": message,
        "skipped": len(skipped_files),
    }


def main():
    parser = argparse.ArgumentParser(description="Safe Git Save")
    parser.add_argument("message", nargs="?", default="", help="Commit message")
    parser.add_argument("--dry-run", action="store_true", help="Preview without committing")
    parser.add_argument("--include-new", action="store_true",
                        help="Also stage new .py/.md files (untracked)")
    args = parser.parse_args()

    safe_save(message=args.message, dry_run=args.dry_run, include_new=args.include_new)


if __name__ == "__main__":
    main()
