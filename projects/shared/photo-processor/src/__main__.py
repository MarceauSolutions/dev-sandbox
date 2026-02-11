#!/usr/bin/env python3
"""
Photo Processor — Export and resize photos from macOS Photos.app.

Usage:
    python -m src --album "Vacation 2025" --output ~/Desktop/resized/
    python -m src --recent 10 --output ~/Desktop/resized/
    python -m src --pick --output ~/Desktop/resized/
"""

import sys
from .cli import build_parser, run


def main():
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run(args))


if __name__ == "__main__":
    main()
