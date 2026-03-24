#!/bin/bash
# Live Call Coach Overlay — always-on-top floating window
# Put call on speakerphone → MacBook mic hears both sides
# Transcribes via Whisper → Claude suggests next best response

set -e

OVERLAY_DIR="$(cd "$(dirname "$0")/.." && pwd)/projects/marceau-solutions/labs/call-coach-overlay"

echo "🎙  Call Coach Overlay"
echo "─────────────────────────────────"

# Install deps if needed
echo "Checking dependencies..."
pip3 install --quiet sounddevice numpy openai anthropic python-dotenv 2>/dev/null || true

# Check if sounddevice installed correctly
python3 -c "import sounddevice" 2>/dev/null || {
    echo "⚠  sounddevice not available — will run in simulation/paste mode"
    echo "   To enable mic capture: pip3 install sounddevice"
}

echo "Launching overlay..."
echo ""
echo "  HOW TO USE:"
echo "  1. Put your call on speakerphone"
echo "  2. Click ▶ START in the overlay window"
echo "  3. Coach updates every 4 seconds"
echo "  4. Click ⏹ STOP when call ends"
echo ""

cd "$OVERLAY_DIR"
python3 overlay.py
