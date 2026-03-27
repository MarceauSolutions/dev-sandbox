#!/bin/bash
# Install personal-assistant launchd jobs
# Run: bash projects/personal-assistant/launchd/install.sh

set -e

PLIST_DIR="$(cd "$(dirname "$0")" && pwd)"
LAUNCH_DIR="$HOME/Library/LaunchAgents"

echo "Installing personal-assistant scheduled jobs..."

for plist in "$PLIST_DIR"/com.marceau.pa.*.plist; do
    name=$(basename "$plist")
    launchctl unload "$LAUNCH_DIR/$name" 2>/dev/null || true
    cp "$plist" "$LAUNCH_DIR/$name"
    launchctl load "$LAUNCH_DIR/$name"
    echo "  ✓ Installed: $name"
done

echo ""
echo "Installed jobs:"
echo "  • morning-digest: Runs at 6:30am daily (unified digest to Telegram)"
echo ""
echo "To uninstall: launchctl unload ~/Library/LaunchAgents/com.marceau.pa.*.plist"
echo "Logs: projects/personal-assistant/logs/"
