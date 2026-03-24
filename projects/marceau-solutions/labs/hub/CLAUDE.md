# Marceau Hub — Master App Launcher

**Status**: Active (always running) | **Port**: 8760 | **URL**: http://127.0.0.1:8760

## What It Does
Central hub that lists all web apps, shows which are running, and launches any of them with one click. Auto-starts on login via launchd. William never needs to remember a CLI command.

## Access
- **Bookmark**: http://127.0.0.1:8760
- **Auto-starts on login** via `~/Library/LaunchAgents/com.marceau.hub.plist`
- **Manual start**: `./scripts/hub.sh` (only if launchd isn't working)

## Features
- Shows all 14 web apps with live running/stopped status
- One-click launch (starts the app and opens it in browser)
- One-click stop
- Auto-refreshes status every 10 seconds
- Grouped by category: Business, Build, Productivity, Health, System

## Adding a New App
Edit `app.py` → `APPS` list. Add a dict with: id, name, description, port, script (filename in scripts/), category, icon.

## Architecture
- Flask server, no database, single HTML page
- Port scanning to detect running apps
- Subprocess launch of `scripts/*.sh` files
- launchd KeepAlive ensures it restarts if killed

## Files
| What | Where |
|------|-------|
| App server | `app.py` |
| Frontend | `templates/index.html` |
| Launch script | `scripts/hub.sh` |
| launchd plist | `~/Library/LaunchAgents/com.marceau.hub.plist` |
| Logs | `/tmp/marceau-hub.log`, `/tmp/marceau-hub.err` |
