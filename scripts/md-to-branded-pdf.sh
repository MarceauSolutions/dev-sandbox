#!/bin/bash
# Convert a Markdown file to a branded PDF using branded_pdf_engine
#
# Auto-detects the best template from filename/content keywords:
#   proposal, workout, nutrition, onboarding, progress, agreement → matched template
#   Everything else → generic_document
#
# Usage:
#   ./scripts/md-to-branded-pdf.sh docs/LIVE-OPERATION-GUIDE.md
#   ./scripts/md-to-branded-pdf.sh docs/LIVE-OPERATION-GUIDE.md "Custom Title"
#   ./scripts/md-to-branded-pdf.sh client-proposal.md                  # auto: proposal
#   ./scripts/md-to-branded-pdf.sh julia-workout-week5.md              # auto: workout_program
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
  echo ""
  echo "Auto-detects template from filename keywords:"
  echo "  proposal      → proposal template"
  echo "  workout/program → workout_program template"
  echo "  nutrition/meal → nutrition_guide template"
  echo "  onboarding    → onboarding_packet template"
  echo "  progress/report → progress_report template"
  echo "  agreement/contract → agreement template"
  echo "  (other)       → generic_document template"
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

# Auto-detect template from filename and first 5 lines
FILENAME=$(basename "$INPUT" | tr '[:upper:]' '[:lower:]')
FIRST_LINES=$(head -5 "$INPUT" | tr '[:upper:]' '[:lower:]')
DETECT_TEXT="$FILENAME $FIRST_LINES"

TEMPLATE="generic_document"
if echo "$DETECT_TEXT" | grep -qiE "proposal|quote|pitch"; then
  TEMPLATE="proposal"
elif echo "$DETECT_TEXT" | grep -qiE "workout|program|training|exercise"; then
  TEMPLATE="workout_program"
elif echo "$DETECT_TEXT" | grep -qiE "nutrition|meal|diet|macro"; then
  TEMPLATE="nutrition_guide"
elif echo "$DETECT_TEXT" | grep -qiE "onboarding|welcome|getting.started"; then
  TEMPLATE="onboarding_packet"
elif echo "$DETECT_TEXT" | grep -qiE "progress|review|check.in"; then
  TEMPLATE="progress_report"
elif echo "$DETECT_TEXT" | grep -qiE "agreement|contract|terms"; then
  TEMPLATE="agreement"
fi

echo "Template: $TEMPLATE (auto-detected from filename/content)"

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
python3 "$ENGINE" --template "$TEMPLATE" --input "$TMP_DATA" --output "$OUTPUT"

# Cleanup
rm -f "$TMP_DATA"

echo ""
echo "✓ Branded PDF: $OUTPUT"
