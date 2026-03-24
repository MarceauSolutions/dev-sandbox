#!/usr/bin/env bash
# AgentOS Hook: API Cost Guard
# Prevents accidental spending on paid APIs without verification.
# Add your paid API providers to PROVIDER_MAP below.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"

# --- CONFIGURE YOUR PAID PROVIDERS ---
# Format: "keyword:provider_name"
# Example entries:
#   "openai:OpenAI"
#   "anthropic:Anthropic"
#   "twilio:Twilio"
#   "sendgrid:SendGrid"
#   "stripe:Stripe"
PROVIDER_MAP=(
    # Add your paid providers here
)

if [ ${#PROVIDER_MAP[@]} -eq 0 ]; then
    exit 0
fi

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null || true)
TOOL_INPUT=$(echo "$INPUT" | jq -r '.tool_input // empty' 2>/dev/null || true)

if [ -z "$TOOL_NAME" ] || [ -z "$TOOL_INPUT" ]; then
    exit 0
fi

COMBINED="$TOOL_NAME $TOOL_INPUT"
COMBINED_LOWER=$(echo "$COMBINED" | tr '[:upper:]' '[:lower:]')

for entry in "${PROVIDER_MAP[@]}"; do
    KEYWORD="${entry%%:*}"
    PROVIDER="${entry##*:}"

    if echo "$COMBINED_LOWER" | grep -qi "$KEYWORD"; then
        # Check if there's a status file for this provider
        STATUS_FILE="$REPO_ROOT/.agent-os-api-status/${KEYWORD}.json"
        if [ -f "$STATUS_FILE" ]; then
            VERIFIED=$(jq -r '.verified // false' "$STATUS_FILE" 2>/dev/null || echo "false")
            if [ "$VERIFIED" = "true" ]; then
                exit 0
            fi
        fi

        echo "WARN: This operation may incur costs with $PROVIDER."
        echo "Verify the API key is active and billing is expected."
        echo "To suppress this warning, create: $STATUS_FILE"
        echo '{"verified": true, "verified_at": "YYYY-MM-DD"}'
        exit 0
    fi
done

exit 0
