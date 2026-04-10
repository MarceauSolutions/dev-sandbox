#!/bin/bash
# Shortcut: convert a Markdown file to a branded PDF
# Usage: ./make-pdf.sh docs/LIVE-OPERATION-GUIDE.md
#        ./make-pdf.sh docs/LIVE-OPERATION-GUIDE.md "Custom Title"
exec "$(dirname "$0")/scripts/md-to-branded-pdf.sh" "$@"
