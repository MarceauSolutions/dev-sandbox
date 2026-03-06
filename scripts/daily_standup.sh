#!/bin/bash
# daily_standup.sh — Start the day: health + revenue + digest + api status + links
# Usage: ./scripts/daily_standup.sh

set -uo pipefail
cd "$(dirname "$0")/.."

BOLD="\033[1m"
GOLD="\033[33m"
RESET="\033[0m"
GREEN="\033[32m"

echo -e "\n${BOLD}${GOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${BOLD}${GOLD}  MARCEAU SOLUTIONS — DAILY STANDUP${RESET}"
echo -e "${BOLD}${GOLD}  $(date '+%A, %B %d %Y — %I:%M %p')${RESET}"
echo -e "${BOLD}${GOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"

# 1. System health
echo -e "${BOLD}[1/5] SYSTEM HEALTH${RESET}"
python scripts/health_check.py 2>&1 || true

echo ""
echo -e "${BOLD}${GOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${BOLD}[2/5] REVENUE SNAPSHOT (last 7 days)${RESET}"
python scripts/revenue-report.py 2>&1 || echo "  (revenue data unavailable)"

echo ""
echo -e "${BOLD}${GOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${BOLD}[3/5] MORNING DIGEST (preview — no email sent)${RESET}"
python -m projects.shared.personal-assistant.src.morning_digest --preview 2>&1 || echo "  (digest unavailable)"

echo ""
echo -e "${BOLD}${GOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${BOLD}[4/5] API BALANCES${RESET}"
python scripts/check_api_balances.py 2>&1 || echo "  (api balance check unavailable)"

echo ""
echo -e "${BOLD}${GOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${BOLD}[5/5] QUICK LINKS${RESET}"
echo "  Stripe:        https://dashboard.stripe.com/customers"
echo "  PT Tracker:    https://docs.google.com/spreadsheets/d/1ZkzOY9SxMcDrDtq69rDcQ0ZMd9Ss8YaE-qeJmS7FuBA"
echo "  WebDev Tracker:https://docs.google.com/spreadsheets/d/1gWobdkQsa8XCr7xEOXTFJ3t45e2K54bfxQpYLkCqN7Q"
echo "  n8n Dashboard: https://n8n.marceausolutions.com"
echo "  System State:  docs/SYSTEM-STATE.md"

echo ""
echo -e "${BOLD}${GOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${GREEN}  Standup complete. Have a productive day.${RESET}"
echo -e "${BOLD}${GOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
