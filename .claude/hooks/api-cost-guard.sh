#!/bin/bash
# Claude Code PreToolUse Hook: API Cost Guard
#
# Receives JSON on stdin from Claude Code with tool_input.command.
# Checks if the Bash command invokes a paid API provider.
# If provider is temporarily blocked in provider-status.json → exit 1 (block).
# If provider is active → exit 0 (allow) + print cost warning to stderr.
#
# No provider is permanently blocked. Status is either "active" or "blocked"
# with a clear "action" field explaining how to unblock it.

INPUT=$(cat)

# Extract the command from tool input
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

if [[ -z "$COMMAND" ]]; then
    exit 0
fi

# Map of keywords → provider names (as they appear in provider-status.json)
declare -A PROVIDER_MAP
PROVIDER_MAP=(
    ["fal.ai"]="fal.ai"
    ["fal-ai"]="fal.ai"
    ["fal_ai"]="fal.ai"
    ["fal.run"]="fal.ai"
    ["queue.fal.run"]="fal.ai"
    ["replicate"]="replicate"
    ["elevenlabs"]="elevenlabs"
    ["eleven_labs"]="elevenlabs"
    ["xi-api"]="elevenlabs"
    ["openai"]="openai-tts"
    ["grok"]="xai"
    ["xai"]="xai"
    ["x.ai"]="xai"
    ["ideogram"]="ideogram"
    ["kie.ai"]="kie.ai"
    ["kie_ai"]="kie.ai"
    ["api.apollo.io"]="apollo"
    ["apollo_api_key"]="apollo"
    ["api.hunter.io"]="hunter"
    ["hunter_api_key"]="hunter"
)

STATUS_FILE="$(dirname "$0")/provider-status.json"

if [[ ! -f "$STATUS_FILE" ]]; then
    exit 0
fi

# Check if command references any known provider
COMMAND_LOWER=$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]')
MATCHED_PROVIDER=""

for keyword in "${!PROVIDER_MAP[@]}"; do
    if [[ "$COMMAND_LOWER" == *"$keyword"* ]]; then
        MATCHED_PROVIDER="${PROVIDER_MAP[$keyword]}"
        break
    fi
done

# Also check for Python imports and API calls that reference providers
if [[ -z "$MATCHED_PROVIDER" ]]; then
    # Check for environment variable usage patterns
    if [[ "$COMMAND_LOWER" == *"fal_api_key"* || "$COMMAND_LOWER" == *"fal_key"* ]]; then
        MATCHED_PROVIDER="fal.ai"
    elif [[ "$COMMAND_LOWER" == *"replicate_api_token"* ]]; then
        MATCHED_PROVIDER="replicate"
    elif [[ "$COMMAND_LOWER" == *"elevenlabs_api_key"* || "$COMMAND_LOWER" == *"eleven_api_key"* ]]; then
        MATCHED_PROVIDER="elevenlabs"
    elif [[ "$COMMAND_LOWER" == *"openai_api_key"* && "$COMMAND_LOWER" == *"tts"* ]]; then
        MATCHED_PROVIDER="openai-tts"
    elif [[ "$COMMAND_LOWER" == *"xai_api_key"* ]]; then
        MATCHED_PROVIDER="xai"
    elif [[ "$COMMAND_LOWER" == *"ideogram_api_key"* ]]; then
        MATCHED_PROVIDER="ideogram"
    elif [[ "$COMMAND_LOWER" == *"kie_api_key"* ]]; then
        MATCHED_PROVIDER="kie.ai"
    fi
fi

# Special case: Apollo — skip auth/health checks (those are free)
if [[ "$MATCHED_PROVIDER" == "apollo" ]]; then
    if [[ "$COMMAND_LOWER" == *"auth/health"* || "$COMMAND_LOWER" == *"auth_health"* ]]; then
        exit 0
    fi
    echo "" >&2
    echo "--- API Cost Guard: apollo (credit warning) ---" >&2
    echo "  Apollo credits are limited. Check balance first:" >&2
    echo "  ./scripts/api-key-manager.sh → http://127.0.0.1:8793" >&2
    echo "  Use auth/health endpoint to test connectivity without spending credits." >&2
    echo "" >&2
    exit 0
fi

# Special case: Hunter.io — warn about low value for Naples FL leads
if [[ "$MATCHED_PROVIDER" == "hunter" ]]; then
    echo "" >&2
    echo "--- API Cost Guard: hunter.io (effectiveness warning) ---" >&2
    echo "  Hunter.io found 0 Naples FL leads in prior run — low value for local B2B." >&2
    echo "  Consider: Apollo (better B2B data) or manual LinkedIn outreach." >&2
    echo "  Check balance first: ./scripts/api-key-manager.sh" >&2
    echo "  Proceeding, but confirm this is the right tool for this use case." >&2
    echo "" >&2
    exit 0
fi

if [[ -z "$MATCHED_PROVIDER" ]]; then
    exit 0
fi

# Read provider status
STATUS=$(python3 -c "
import json, sys
with open('$STATUS_FILE') as f:
    data = json.load(f)
provider = data.get('$MATCHED_PROVIDER', {})
print(provider.get('status', 'unknown'))
print(provider.get('reason', ''))
print(provider.get('action', ''))
print(provider.get('note', ''))
print(provider.get('renewal', ''))
" 2>/dev/null)

PROVIDER_STATUS=$(echo "$STATUS" | sed -n '1p')
REASON=$(echo "$STATUS" | sed -n '2p')
ACTION=$(echo "$STATUS" | sed -n '3p')
NOTE=$(echo "$STATUS" | sed -n '4p')
RENEWAL=$(echo "$STATUS" | sed -n '5p')

if [[ "$PROVIDER_STATUS" == "blocked" ]]; then
    echo "" >&2
    echo "=== API COST GUARD: BLOCKED ===" >&2
    echo "Provider: $MATCHED_PROVIDER" >&2
    echo "Reason: $REASON" >&2
    echo "To unblock: $ACTION" >&2
    if [[ -n "$RENEWAL" ]]; then
        echo "Renewal: $RENEWAL" >&2
    fi
    echo "" >&2
    echo "This provider is temporarily blocked. Fix the issue above or use an alternative." >&2
    echo "Edit $STATUS_FILE to update provider status." >&2
    echo "" >&2
    exit 1
fi

if [[ "$PROVIDER_STATUS" == "active" ]]; then
    echo "" >&2
    echo "--- API Cost Guard: $MATCHED_PROVIDER (active) ---" >&2
    if [[ -n "$NOTE" ]]; then
        echo "  Note: $NOTE" >&2
    fi
    echo "  This command will incur API costs. Proceeding." >&2
    echo "" >&2
    exit 0
fi

# Unknown status — allow but warn
echo "API Cost Guard: Unknown status for $MATCHED_PROVIDER — allowing." >&2
exit 0
