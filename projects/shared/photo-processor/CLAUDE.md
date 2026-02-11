# Photo Processor

## What This Does
Export photos from macOS Photos.app by album, recency, or interactive picker,
then resize/compress to a configurable max file size (default 5MB).
Handles HEIC-to-JPEG conversion automatically via macOS `sips`.

## Interactive Use
Just say **"download photos"** or type **`/photos`** — Claude will walk you through
selecting photos, choosing an output folder, and setting max file size with clickable options.
No bash commands needed.

## Quick Commands
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared/photo-processor

# Export album, compress to 5MB
python -m src --album "Vacation 2025" --output ~/Desktop/resized/

# Export 10 most recent photos
python -m src --recent 10 --output ~/Desktop/resized/

# Interactive album picker
python -m src --pick --output ~/Desktop/resized/

# Dry run (preview without exporting)
python -m src --album "Gym" --output ~/Desktop/resized/ --dry-run

# Custom max size (2MB)
python -m src --album "Gym" --output ~/Desktop/resized/ --max-size 2.0

# Export originals without compression
python -m src --album "Gym" --output ~/Desktop/resized/ --no-resize
```

## Architecture
- `src/cli.py` — argparse CLI interface and main orchestration
- `src/photo_exporter.py` — Photos.app integration (osxphotos + AppleScript)
- `src/image_compressor.py` — Resize/compress to target file size
- `src/__main__.py` — Entry point (`python -m src`)

## Project-Specific Rules
- macOS only (uses Photos.app, sips)
- osxphotos requires Full Disk Access for Terminal in System Settings
- HEIC files converted to JPEG via macOS sips (zero extra deps)
- Binary search on JPEG quality, then dimension reduction if needed
- Never fails the whole batch for a single photo error
