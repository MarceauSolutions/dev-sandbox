#!/bin/bash
# Launch the HVAC Appointment Marketplace (interface-first: opens in browser).
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
PORT="${MARKETPLACE_PORT:-8767}"
python3 -c "import flask" 2>/dev/null || pip3 install flask --quiet
python3 seed.py || true
echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║  Marceau Air — Appointment Marketplace      ║"
echo "  ║   http://127.0.0.1:${PORT}                     ║"
echo "  ║   admin: http://127.0.0.1:${PORT}/admin/login  ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""
(sleep 1.5 && open "http://127.0.0.1:${PORT}" 2>/dev/null) &
python3 app.py
