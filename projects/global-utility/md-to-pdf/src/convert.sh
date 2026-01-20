#!/bin/bash
# Wrapper script for md_to_pdf.py that sets required library path
# Usage: ./convert.sh input.md output.pdf

# Set library path for WeasyPrint dependencies (Pango, Cairo, etc.)
export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH

# Get the directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Run the Python converter with all arguments
python "$SCRIPT_DIR/md_to_pdf.py" "$@"
