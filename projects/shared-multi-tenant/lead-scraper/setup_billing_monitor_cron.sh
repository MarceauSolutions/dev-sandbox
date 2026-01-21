#!/bin/bash
#
# Google Cloud Billing Monitor - Cron Setup Script
#
# This script sets up automated daily billing monitoring via launchd (macOS)
# or cron (Linux/Unix).
#
# Usage:
#   bash setup_billing_monitor_cron.sh
#
# What it does:
#   1. Detects OS (macOS vs Linux)
#   2. Creates appropriate scheduled job configuration
#   3. Sets up daily execution at 9:00 AM
#   4. Creates log files
#   5. Tests the configuration
#

set -e  # Exit on error

# =============================================================================
# Configuration
# =============================================================================

PROJECT_DIR="/Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/lead-scraper"
SCRIPT="google_cloud_cost_monitor.py"
PYTHON_PATH="/usr/local/bin/python3"
LOG_FILE="/tmp/google-billing-monitor.log"
ERROR_LOG="/tmp/google-billing-monitor.error.log"

# Detect OS
OS_TYPE=$(uname -s)

echo "============================================================"
echo "Google Cloud Billing Monitor - Cron Setup"
echo "============================================================"
echo "OS: $OS_TYPE"
echo "Project: $PROJECT_DIR"
echo "Script: $SCRIPT"
echo "Python: $PYTHON_PATH"
echo "============================================================"
echo ""

# =============================================================================
# Helper Functions
# =============================================================================

check_prerequisites() {
    echo "Checking prerequisites..."

    # Check Python
    if [ ! -f "$PYTHON_PATH" ]; then
        echo "❌ Python not found at $PYTHON_PATH"
        echo "   Looking for Python..."
        PYTHON_PATH=$(which python3)
        if [ -z "$PYTHON_PATH" ]; then
            echo "❌ Python 3 not installed. Please install Python 3 first."
            exit 1
        fi
        echo "✅ Found Python at: $PYTHON_PATH"
    else
        echo "✅ Python found: $PYTHON_PATH"
    fi

    # Check project directory
    if [ ! -d "$PROJECT_DIR" ]; then
        echo "❌ Project directory not found: $PROJECT_DIR"
        exit 1
    fi
    echo "✅ Project directory exists"

    # Check script exists
    if [ ! -f "$PROJECT_DIR/src/$SCRIPT" ]; then
        echo "❌ Script not found: $PROJECT_DIR/src/$SCRIPT"
        exit 1
    fi
    echo "✅ Script found"

    # Check .env file
    if [ ! -f "$PROJECT_DIR/../../../.env" ]; then
        echo "⚠️  Warning: .env file not found"
        echo "   SMS alerts may not work without Twilio credentials"
    else
        echo "✅ .env file found"
    fi

    echo ""
}

test_script() {
    echo "Testing script execution..."
    cd "$PROJECT_DIR"

    if $PYTHON_PATH -m src.google_cloud_cost_monitor --once --no-sms; then
        echo "✅ Script executed successfully"
    else
        echo "❌ Script failed to execute"
        echo "   Please check error messages above"
        exit 1
    fi

    echo ""
}

# =============================================================================
# macOS Setup (launchd)
# =============================================================================

setup_macos_launchd() {
    echo "Setting up macOS launchd job..."

    PLIST_FILE="$HOME/Library/LaunchAgents/com.marceausolutions.google-billing-monitor.plist"

    # Create LaunchAgents directory if doesn't exist
    mkdir -p "$HOME/Library/LaunchAgents"

    # Create plist file
    cat > "$PLIST_FILE" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.marceausolutions.google-billing-monitor</string>

    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>-m</string>
        <string>src.google_cloud_cost_monitor</string>
        <string>--once</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>$LOG_FILE</string>

    <key>StandardErrorPath</key>
    <string>$ERROR_LOG</string>

    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF

    echo "✅ Created plist file: $PLIST_FILE"

    # Unload existing job (if exists)
    if launchctl list | grep -q "com.marceausolutions.google-billing-monitor"; then
        echo "Unloading existing job..."
        launchctl unload "$PLIST_FILE" 2>/dev/null || true
    fi

    # Load job
    echo "Loading launchd job..."
    if launchctl load "$PLIST_FILE"; then
        echo "✅ Launchd job loaded successfully"
    else
        echo "❌ Failed to load launchd job"
        exit 1
    fi

    # Verify job is loaded
    if launchctl list | grep -q "com.marceausolutions.google-billing-monitor"; then
        echo "✅ Job is running"
    else
        echo "❌ Job not found in launchctl list"
        exit 1
    fi

    echo ""
    echo "============================================================"
    echo "✅ macOS launchd setup complete!"
    echo "============================================================"
    echo ""
    echo "The billing monitor will run daily at 9:00 AM."
    echo ""
    echo "Useful commands:"
    echo "  # Check job status"
    echo "  launchctl list | grep google-billing-monitor"
    echo ""
    echo "  # Start job manually (for testing)"
    echo "  launchctl start com.marceausolutions.google-billing-monitor"
    echo ""
    echo "  # View logs"
    echo "  tail -f $LOG_FILE"
    echo "  tail -f $ERROR_LOG"
    echo ""
    echo "  # Unload job (disable)"
    echo "  launchctl unload $PLIST_FILE"
    echo ""
    echo "  # Reload job (after changes)"
    echo "  launchctl unload $PLIST_FILE && launchctl load $PLIST_FILE"
    echo "============================================================"
    echo ""
}

# =============================================================================
# Linux Setup (cron)
# =============================================================================

setup_linux_cron() {
    echo "Setting up Linux cron job..."

    CRON_ENTRY="0 9 * * * cd $PROJECT_DIR && $PYTHON_PATH -m src.google_cloud_cost_monitor --once >> $LOG_FILE 2>&1"

    # Check if entry already exists
    if crontab -l 2>/dev/null | grep -q "google_cloud_cost_monitor"; then
        echo "⚠️  Cron entry already exists. Removing old entry..."
        (crontab -l 2>/dev/null | grep -v "google_cloud_cost_monitor") | crontab -
    fi

    # Add new entry
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

    echo "✅ Cron job added"

    # Verify
    echo ""
    echo "Current crontab:"
    crontab -l | grep google_cloud_cost_monitor

    echo ""
    echo "============================================================"
    echo "✅ Linux cron setup complete!"
    echo "============================================================"
    echo ""
    echo "The billing monitor will run daily at 9:00 AM."
    echo ""
    echo "Useful commands:"
    echo "  # View all cron jobs"
    echo "  crontab -l"
    echo ""
    echo "  # Edit cron jobs"
    echo "  crontab -e"
    echo ""
    echo "  # View logs"
    echo "  tail -f $LOG_FILE"
    echo ""
    echo "  # Remove cron job"
    echo "  crontab -e  # Then delete the line"
    echo "============================================================"
    echo ""
}

# =============================================================================
# Main
# =============================================================================

main() {
    check_prerequisites
    test_script

    case "$OS_TYPE" in
        Darwin)
            setup_macos_launchd
            ;;
        Linux)
            setup_linux_cron
            ;;
        *)
            echo "❌ Unsupported OS: $OS_TYPE"
            echo "   This script supports macOS (Darwin) and Linux only"
            exit 1
            ;;
    esac

    echo "✅ Setup complete!"
    echo ""
    echo "To test immediately, run:"
    echo "  cd $PROJECT_DIR"
    echo "  python -m src.google_cloud_cost_monitor"
    echo ""
}

# Run main
main
