#!/bin/bash
# notify-input-needed.sh
# Plays a pleasant church bell sound when Claude needs user input
# Created: 2026-01-27

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOUND_FILE="$SCRIPT_DIR/../assets/sounds/church-bell.mp3"

# Default message
MESSAGE="${1:-Claude needs your input}"

# Play the church bell sound
if [ -f "$SOUND_FILE" ]; then
    afplay "$SOUND_FILE" &
else
    # Fallback to system sound if church bell not found
    afplay /System/Library/Sounds/Glass.aiff &
fi

# Show macOS notification
osascript -e "display notification \"$MESSAGE\" with title \"Claude Code\" sound name \"\""

echo "🔔 Notification sent: $MESSAGE"
