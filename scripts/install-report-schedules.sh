#!/bin/bash
# Install launchd schedules for weekly business report and monthly review
# Run: bash scripts/install-report-schedules.sh

set -e

SANDBOX="/Users/williammarceaujr./dev-sandbox"
LAUNCH_DIR="$HOME/Library/LaunchAgents"

mkdir -p "$SANDBOX/logs"

# Weekly report — Monday 9am ET
cat > "$LAUNCH_DIR/com.marceausolutions.weekly-report.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.marceausolutions.weekly-report</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/williammarceaujr./dev-sandbox/scripts/weekly-business-report.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/williammarceaujr./dev-sandbox</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>1</integer>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/williammarceaujr./dev-sandbox/logs/weekly-report.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/williammarceaujr./dev-sandbox/logs/weekly-report-error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
        <key>HOME</key>
        <string>/Users/williammarceaujr.</string>
    </dict>
</dict>
</plist>
EOF

# Monthly review — 1st of month 9am ET
cat > "$LAUNCH_DIR/com.marceausolutions.monthly-review.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.marceausolutions.monthly-review</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/williammarceaujr./dev-sandbox/scripts/monthly-business-review.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/williammarceaujr./dev-sandbox</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Day</key>
        <integer>1</integer>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/williammarceaujr./dev-sandbox/logs/monthly-review.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/williammarceaujr./dev-sandbox/logs/monthly-review-error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
        <key>HOME</key>
        <string>/Users/williammarceaujr.</string>
    </dict>
</dict>
</plist>
EOF

echo "Loading launchd agents..."
launchctl load "$LAUNCH_DIR/com.marceausolutions.weekly-report.plist" 2>/dev/null || true
launchctl load "$LAUNCH_DIR/com.marceausolutions.monthly-review.plist" 2>/dev/null || true

echo ""
echo "Installed and loaded:"
echo "  - com.marceausolutions.weekly-report (Monday 9am)"
echo "  - com.marceausolutions.monthly-review (1st of month 9am)"
echo ""
echo "Verify: launchctl list | grep marceausolutions"
