#!/usr/bin/env python3
"""
Open PowerPoint File (with proper cleanup)

Closes any existing PowerPoint presentations before opening a new one
to prevent multiple versions from accumulating.

Usage:
    python open_pptx.py .tmp/file.pptx
    python open_pptx.py --file .tmp/file.pptx
"""

import argparse
import subprocess
import time
import sys
from pathlib import Path


def close_all_presentations():
    """Close all open PowerPoint presentations."""
    # Try to close presentations in Microsoft PowerPoint
    script = '''
    tell application "System Events"
        if exists process "Microsoft PowerPoint" then
            tell application "Microsoft PowerPoint"
                close every presentation saving no
            end tell
        end if
    end tell
    '''
    try:
        subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
    except:
        pass

    # Also try quitting PowerPoint entirely for a clean slate
    quit_script = '''
    tell application "System Events"
        if exists process "Microsoft PowerPoint" then
            tell application "Microsoft PowerPoint" to quit saving no
        end if
    end tell
    '''
    try:
        subprocess.run(['osascript', '-e', quit_script], capture_output=True, timeout=5)
    except:
        pass

    # Brief pause to let the app close
    time.sleep(0.5)


def open_file(file_path: str):
    """Open a PowerPoint file."""
    path = Path(file_path)
    if not path.exists():
        print(f"❌ File not found: {file_path}")
        return False

    try:
        subprocess.run(['open', str(path)], check=True)
        print(f"✅ Opened: {path.name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to open: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Open PowerPoint file (closes existing presentations first)"
    )
    parser.add_argument("file", nargs="?", help="PowerPoint file to open")
    parser.add_argument("--file", "-f", dest="file_flag", help="PowerPoint file to open")

    args = parser.parse_args()

    file_path = args.file or args.file_flag
    if not file_path:
        print("Usage: python open_pptx.py <file.pptx>")
        return 1

    print("Closing existing presentations...")
    close_all_presentations()

    print(f"Opening {file_path}...")
    if open_file(file_path):
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
