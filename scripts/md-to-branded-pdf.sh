#!/bin/bash
# Convert a Markdown file to a branded PDF using branded_pdf_engine
#
# Usage:
#   ./scripts/md-to-branded-pdf.sh docs/LIVE-OPERATION-GUIDE.md
#   ./scripts/md-to-branded-pdf.sh docs/LIVE-OPERATION-GUIDE.md "Live Operation Guide"
#
# Output: projects/fitness-influencer/outputs/branded-pdfs/<filename>_<date>.pdf

set -e

INPUT="$1"
TITLE="${2:-}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENGINE="$REPO_ROOT/projects/fitness-influencer/src/branded_pdf_engine.py"
OUTPUT_DIR="$REPO_ROOT/projects/fitness-influencer/outputs/branded-pdfs"

if [ -z "$INPUT" ]; then
  echo "Usage: ./scripts/md-to-branded-pdf.sh <markdown-file> [title]"
  exit 1
fi

# Resolve input path
if [ ! -f "$INPUT" ] && [ -f "$REPO_ROOT/$INPUT" ]; then
  INPUT="$REPO_ROOT/$INPUT"
fi

if [ ! -f "$INPUT" ]; then
  echo "Error: File not found: $INPUT"
  exit 1
fi

# Auto-detect title from first H1 if not provided
if [ -z "$TITLE" ]; then
  TITLE=$(head -20 "$INPUT" | grep "^# " | head -1 | sed 's/^# //')
  [ -z "$TITLE" ] && TITLE=$(basename "$INPUT" .md | tr '-' ' ')
fi

# Build output path
mkdir -p "$OUTPUT_DIR"
STEM=$(basename "$INPUT" .md)
DATE=$(date +%Y%m%d)
OUTPUT="$OUTPUT_DIR/${STEM}_${DATE}.pdf"

# Build temp JSON data file
CONTENT=$(cat "$INPUT")
SUBTITLE="Generated $(date '+%B %d, %Y')"
TMP_DATA=$(mktemp /tmp/pdf_data_XXXXXX.json)

python3 -c "
import json, sys
data = {
    'title': sys.argv[1],
    'subtitle': sys.argv[2],
    'content_markdown': open(sys.argv[3]).read()
}
json.dump(data, open(sys.argv[4], 'w'))
" "$TITLE" "$SUBTITLE" "$INPUT" "$TMP_DATA"

# Run branded_pdf_engine
cd "$REPO_ROOT/projects/fitness-influencer/src"
python3 "$ENGINE" --template generic_document --input "$TMP_DATA" --output "$OUTPUT"

# Cleanup
rm -f "$TMP_DATA"

echo ""
echo "✓ Branded PDF: $OUTPUT"
