#!/bin/bash
# tailor_resume.sh — Generate a tailored resume + cover letter from a job posting.
#
# Personal-use entry point for William's job hunt. The same engine that the
# (still-inactive) Stripe-gated n8n workflow uses, just invoked directly.
#
# Usage:
#   bash scripts/tailor_resume.sh --job posting.txt
#   bash scripts/tailor_resume.sh --job-url https://example.com/jobs/123
#   cat posting.txt | bash scripts/tailor_resume.sh
#
# Output: PDF + Markdown for both the resume and the cover letter, plus the
# parsed job JSON (so you can see what Claude extracted from the posting).
#
# Default output dir: projects/shared/resume/output/applications/<company>/

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RESUME_DIR="$REPO_ROOT/projects/shared/resume"

# Parse args
JOB_FILE=""
JOB_URL=""
OUTPUT_DIR="$RESUME_DIR/output/applications"
MODEL="${SOP_BUILDER_MODEL:-claude-sonnet-4-6}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --job)         JOB_FILE="$2"; shift 2 ;;
        --job-url)     JOB_URL="$2"; shift 2 ;;
        --output-dir)  OUTPUT_DIR="$2"; shift 2 ;;
        --model)       MODEL="$2"; shift 2 ;;
        -h|--help)
            sed -n '2,16p' "$0"
            exit 0 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

# Resolve output dir to absolute path BEFORE we cd, so relative paths from the
# caller's CWD don't get nested when the engine resolves them again post-cd.
case "$OUTPUT_DIR" in
    /*) ;;  # already absolute
    *)  OUTPUT_DIR="$(pwd)/$OUTPUT_DIR" ;;
esac
mkdir -p "$OUTPUT_DIR"

# Same for the job file if it's relative
if [ -n "$JOB_FILE" ]; then
    case "$JOB_FILE" in
        /*) ;;
        *)  JOB_FILE="$(pwd)/$JOB_FILE" ;;
    esac
fi

# If neither flag was passed, read stdin
JOB_TEXT_FILE=""
if [ -z "$JOB_FILE" ] && [ -z "$JOB_URL" ]; then
    JOB_TEXT_FILE="$(mktemp -t job_posting)"
    cat > "$JOB_TEXT_FILE"
    JOB_FILE="$JOB_TEXT_FILE"
fi

# Resolve job text
if [ -n "$JOB_URL" ]; then
    JOB_TEXT_FILE="$(mktemp -t job_posting)"
    curl -sS -L "$JOB_URL" | python3 -c "
import sys, re
html = sys.stdin.read()
# Strip tags crudely; the engine is robust to noisy input
text = re.sub(r'<[^>]+>', ' ', html)
text = re.sub(r'\s+', ' ', text).strip()
print(text)
" > "$JOB_TEXT_FILE"
    JOB_FILE="$JOB_TEXT_FILE"
fi

if [ ! -f "$JOB_FILE" ]; then
    echo "ERROR: job posting file not found: $JOB_FILE"
    exit 1
fi

cd "$RESUME_DIR"

python3 - "$JOB_FILE" "$OUTPUT_DIR" "$MODEL" <<'PY'
import json, sys
from pathlib import Path
sys.path.insert(0, ".")
from src.engine.generate_application import generate_full_application

job_file = sys.argv[1]
output_dir = sys.argv[2]
model = sys.argv[3]

with open("src/resume_data.json") as f:
    profile = json.load(f)
with open(job_file) as f:
    job_text = f.read()

result = generate_full_application(
    profile=profile,
    job_text=job_text,
    output_dir=output_dir,
    model=model,
)

print()
print(f"  Company:      {result.get('company', '?')}")
print(f"  Role:         {result.get('role_title', '?')}")
print(f"  Resume PDF:   {result['files']['resume_pdf']}")
print(f"  Cover PDF:    {result['files']['cover_letter_pdf']}")
print(f"  Duration:     {result.get('duration_seconds', 0):.1f}s")
PY

# Clean up stdin tempfile if we made one
[ -n "$JOB_TEXT_FILE" ] && rm -f "$JOB_TEXT_FILE" 2>/dev/null || true
