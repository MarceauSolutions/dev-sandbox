#!/bin/bash
# Claude Code PreToolUse Hook: Stay In The Stack Guard
#
# HARD RULE #8: Stay in the stack.
#
# Blocks attempts to use unapproved tools/services. Catches:
# - pip install of unapproved packages (ngrok, cloudflared, netlify, vercel, etc.)
# - curl/wget to unapproved services
# - References to tools we've explicitly decided against
#
# Approved stack: Twilio, Stripe, n8n, GitHub Pages, EC2, Google Workspace,
#                 Namecheap, Gmail, Telegram, Mem0

INPUT=$(cat)

COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

if [[ -z "$COMMAND" ]]; then
    exit 0
fi

COMMAND_LOWER=$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]')

# Unapproved tools/services — things we've explicitly decided against
BLOCKED_TOOLS=(
    "ngrok"
    "cloudflared"
    "netlify"
    "vercel"
    "heroku"
    "formsubmit"
    "formspree"
    "typeform"
    "jotform"
    "mailchimp"
    "sendgrid"
    "postmark"
    "railway"
)

for tool in "${BLOCKED_TOOLS[@]}"; do
    if [[ "$COMMAND_LOWER" == *"$tool"* ]]; then
        echo "" >&2
        echo "=== STACK GUARD: BLOCKED ===" >&2
        echo "HARD RULE #8: Stay in the stack." >&2
        echo "" >&2
        echo "Attempted to use: $tool" >&2
        echo "This is NOT in the approved stack." >&2
        echo "" >&2
        echo "Approved alternatives:" >&2
        echo "  Hosting:  GitHub Pages (primary), EC2 (fallback)" >&2
        echo "  Forms:    n8n webhooks" >&2
        echo "  SMS:      Twilio" >&2
        echo "  Email:    Gmail API" >&2
        echo "  Tunnels:  Not needed — use EC2 or GitHub Pages" >&2
        echo "" >&2
        echo "Check docs/service-standards.md before proposing new tools." >&2
        echo "" >&2
        exit 1
    fi
done

exit 0
