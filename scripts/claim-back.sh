#!/bin/bash
# ClaimBack — Medical Billing Dispute Platform
# Launch: ./scripts/claim-back.sh
# URL: http://127.0.0.1:8790

cd "$(dirname "$0")/.." || exit 1

PROJECT="projects/marceau-solutions/labs/claim-back"

# Load environment
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo ""
echo "  ClaimBack — Medical Billing Dispute Platform"
echo "  ─────────────────────────────────────────────"
echo "  Starting on http://127.0.0.1:8790"
echo ""

# Open browser after short delay
(sleep 2 && open "http://127.0.0.1:8790") &

# Run the app
python "$PROJECT/src/app.py"
