#!/bin/bash
# Install lead-generation launchd jobs
# Run: bash projects/lead-generation/launchd/install.sh

set -e

PLIST_DIR="$(cd "$(dirname "$0")" && pwd)"
LAUNCH_DIR="$HOME/Library/LaunchAgents"

echo "Installing lead-generation scheduled jobs..."

for plist in "$PLIST_DIR"/com.marceau.leadgen.*.plist; do
    name=$(basename "$plist")

    # Unload if already loaded
    launchctl unload "$LAUNCH_DIR/$name" 2>/dev/null || true

    # Copy to LaunchAgents
    cp "$plist" "$LAUNCH_DIR/$name"

    # Load
    launchctl load "$LAUNCH_DIR/$name"

    echo "  ✓ Installed: $name"
done

echo ""
echo "Installed 3 jobs:"
echo "  • daily-loop:       Runs at 9:00am daily (full acquisition loop)"
echo "  • check-responses:  Runs every 15 minutes (response monitoring)"
echo "  • digest:           Runs at 5:30pm daily (pipeline digest to Telegram)"
echo ""
echo "To uninstall:"
echo "  launchctl unload ~/Library/LaunchAgents/com.marceau.leadgen.*.plist"
echo ""
echo "To check status:"
echo "  launchctl list | grep marceau.leadgen"
echo ""
echo "Logs: projects/lead-generation/logs/"
