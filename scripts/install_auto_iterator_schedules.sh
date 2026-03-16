#!/bin/bash
# Install AutoIterator launchd schedules
# Usage: ./scripts/install_auto_iterator_schedules.sh

set -e

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_DIR="$SCRIPTS_DIR/launchd"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"

echo "Installing AutoIterator launchd schedules..."

for plist in "$PLIST_DIR"/com.marceausolutions.auto-iterator-*.plist; do
    name=$(basename "$plist")
    dest="$LAUNCH_AGENTS/$name"

    # Unload if already loaded
    if launchctl list | grep -q "${name%.plist}" 2>/dev/null; then
        echo "  Unloading existing: $name"
        launchctl unload "$dest" 2>/dev/null || true
    fi

    # Copy and load
    cp "$plist" "$dest"
    launchctl load "$dest"
    echo "  Installed: $name"
done

echo ""
echo "Installed schedules:"
echo "  - auto-iterator-cycle:   Daily 7:00 AM  (evaluate + sync + notify)"
echo "  - auto-iterator-batch:   Daily 2:00 AM  (overnight LLM optimization)"
echo "  - auto-iterator-weekly:  Monday 8:00 AM (report + cross-domain learning)"
echo ""
echo "Verify: launchctl list | grep auto-iterator"
