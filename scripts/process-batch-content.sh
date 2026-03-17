#!/usr/bin/env bash
#
# process-batch-content.sh — Batch Video Processing for Fitness YouTube
#
# WHAT: Takes a directory of raw video files, removes silence via video_jumpcut.py,
#       outputs processed files to output/processed/[date]/
# WHY:  One command to clean up all raw footage before editing/uploading
#
# USAGE:
#   ./scripts/process-batch-content.sh /path/to/raw/videos
#   ./scripts/process-batch-content.sh /path/to/raw/videos --silence-thresh -35
#   ./scripts/process-batch-content.sh /path/to/raw/videos --min-silence 0.5
#
# DEPENDENCIES: ffmpeg, moviepy (pip install moviepy)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
JUMPCUT_SCRIPT="$PROJECT_ROOT/execution/video_jumpcut.py"
DATE_STAMP=$(date +%Y-%m-%d)
OUTPUT_DIR="$PROJECT_ROOT/output/processed/$DATE_STAMP"

# Colors
GOLD='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
DIM='\033[0;90m'
RESET='\033[0m'

# Defaults
SILENCE_THRESH=-40
MIN_SILENCE=0.3
MIN_CLIP=0.5

# ─── Usage ───────────────────────────────────────────────────
usage() {
    echo ""
    echo -e "${GOLD}BATCH VIDEO PROCESSOR${RESET} — Marceau Fitness Content Pipeline"
    echo ""
    echo "Usage: $0 <input-directory> [options]"
    echo ""
    echo "Options:"
    echo "  --silence-thresh <dB>   Silence threshold (default: -40)"
    echo "  --min-silence <sec>     Min silence duration to cut (default: 0.3)"
    echo "  --min-clip <sec>        Min clip duration to keep (default: 0.5)"
    echo "  --output <dir>          Custom output directory"
    echo "  -h, --help              Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 ~/Desktop/raw-footage"
    echo "  $0 ~/Desktop/raw-footage --silence-thresh -35"
    echo ""
    exit 1
}

# ─── Parse Arguments ─────────────────────────────────────────
if [ $# -lt 1 ]; then
    usage
fi

INPUT_DIR="$1"
shift

while [[ $# -gt 0 ]]; do
    case $1 in
        --silence-thresh) SILENCE_THRESH="$2"; shift 2 ;;
        --min-silence)    MIN_SILENCE="$2"; shift 2 ;;
        --min-clip)       MIN_CLIP="$2"; shift 2 ;;
        --output)         OUTPUT_DIR="$2"; shift 2 ;;
        -h|--help)        usage ;;
        *) echo -e "${RED}Unknown option: $1${RESET}"; usage ;;
    esac
done

# ─── Validate ────────────────────────────────────────────────
if [ ! -d "$INPUT_DIR" ]; then
    echo -e "${RED}Error: Input directory not found: $INPUT_DIR${RESET}"
    exit 1
fi

if [ ! -f "$JUMPCUT_SCRIPT" ]; then
    echo -e "${RED}Error: video_jumpcut.py not found at $JUMPCUT_SCRIPT${RESET}"
    exit 1
fi

if ! command -v ffmpeg &>/dev/null; then
    echo -e "${RED}Error: ffmpeg not installed. Install with: brew install ffmpeg${RESET}"
    exit 1
fi

# ─── Find Video Files ────────────────────────────────────────
VIDEO_EXTENSIONS=("mp4" "mov" "avi" "mkv" "webm" "m4v" "MP4" "MOV")
VIDEO_FILES=()

for ext in "${VIDEO_EXTENSIONS[@]}"; do
    while IFS= read -r -d '' file; do
        VIDEO_FILES+=("$file")
    done < <(find "$INPUT_DIR" -maxdepth 1 -name "*.$ext" -print0 2>/dev/null)
done

if [ ${#VIDEO_FILES[@]} -eq 0 ]; then
    echo -e "${RED}No video files found in: $INPUT_DIR${RESET}"
    echo -e "${DIM}Supported formats: ${VIDEO_EXTENSIONS[*]}${RESET}"
    exit 1
fi

# ─── Process ─────────────────────────────────────────────────
mkdir -p "$OUTPUT_DIR"

echo ""
echo -e "${GOLD}======================================================================${RESET}"
echo -e "${GOLD}  BATCH VIDEO PROCESSOR — Marceau Fitness${RESET}"
echo -e "${GOLD}======================================================================${RESET}"
echo -e "  Input:          $INPUT_DIR"
echo -e "  Output:         $OUTPUT_DIR"
echo -e "  Videos found:   ${#VIDEO_FILES[@]}"
echo -e "  Silence thresh: ${SILENCE_THRESH}dB"
echo -e "  Min silence:    ${MIN_SILENCE}s"
echo -e "  Min clip:       ${MIN_CLIP}s"
echo -e "${GOLD}======================================================================${RESET}"
echo ""

PROCESSED=0
FAILED=0
TOTAL_SAVED=0
SUMMARY=()

for video in "${VIDEO_FILES[@]}"; do
    BASENAME=$(basename "$video")
    STEM="${BASENAME%.*}"
    EXT="${BASENAME##*.}"
    OUTPUT_FILE="$OUTPUT_DIR/${STEM}_processed.mp4"

    echo -e "${GOLD}[$((PROCESSED + FAILED + 1))/${#VIDEO_FILES[@]}]${RESET} Processing: $BASENAME"

    # Get original file size
    ORIG_SIZE=$(stat -f%z "$video" 2>/dev/null || stat --format=%s "$video" 2>/dev/null || echo "0")

    if python3 "$JUMPCUT_SCRIPT" \
        --input "$video" \
        --output "$OUTPUT_FILE" \
        --silence-thresh "$SILENCE_THRESH" \
        --min-silence "$MIN_SILENCE" \
        --min-clip "$MIN_CLIP" 2>&1; then

        if [ -f "$OUTPUT_FILE" ]; then
            NEW_SIZE=$(stat -f%z "$OUTPUT_FILE" 2>/dev/null || stat --format=%s "$OUTPUT_FILE" 2>/dev/null || echo "0")
            SAVED=$(( (ORIG_SIZE - NEW_SIZE) / 1024 / 1024 ))
            if [ "$SAVED" -lt 0 ]; then SAVED=0; fi
            TOTAL_SAVED=$((TOTAL_SAVED + SAVED))

            PROCESSED=$((PROCESSED + 1))
            SUMMARY+=("  [OK] $BASENAME -> ${STEM}_processed.mp4 (saved ~${SAVED}MB)")
            echo -e "${GREEN}  Done: $OUTPUT_FILE${RESET}"
        else
            FAILED=$((FAILED + 1))
            SUMMARY+=("  [FAIL] $BASENAME — output file not created")
            echo -e "${RED}  Failed: output not created${RESET}"
        fi
    else
        FAILED=$((FAILED + 1))
        SUMMARY+=("  [FAIL] $BASENAME — processing error")
        echo -e "${RED}  Failed: processing error${RESET}"
    fi

    echo ""
done

# ─── Summary ─────────────────────────────────────────────────
echo -e "${GOLD}======================================================================${RESET}"
echo -e "${GOLD}  BATCH PROCESSING COMPLETE${RESET}"
echo -e "${GOLD}======================================================================${RESET}"
echo -e "  Processed:  ${GREEN}$PROCESSED${RESET} / ${#VIDEO_FILES[@]}"
if [ "$FAILED" -gt 0 ]; then
    echo -e "  Failed:     ${RED}$FAILED${RESET}"
fi
echo -e "  Output dir: $OUTPUT_DIR"
echo -e "  Space saved: ~${TOTAL_SAVED}MB"
echo ""
echo "  Files:"
for line in "${SUMMARY[@]}"; do
    echo "$line"
done
echo -e "${GOLD}======================================================================${RESET}"
echo ""
