#!/bin/bash
# Claude Code PreToolUse Hook: Tool Reuse Checker
# BLOCKING for known shortcut patterns. Informational for everything else.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null)

if [[ ! "$FILE_PATH" =~ \.py$ ]]; then
    exit 0
fi

BASENAME=$(basename "$FILE_PATH" .py | tr '[:upper:]' '[:lower:]')

# ============================================================
# HARD BLOCKS — exit 2 stops the tool call entirely
# ============================================================

if [[ "$BASENAME" =~ pdf|branded.*doc|report.*gen|doc.*gen ]]; then
    echo "BLOCKED: Do NOT write a custom PDF script." >&2
    echo "USE: execution/branded_pdf_engine.py" >&2
    echo "  --list-templates                        (see what's available)" >&2
    echo "  --template generic_document             (for markdown content)" >&2
    echo "  Data key = 'content_markdown' NOT 'content' or 'sections'" >&2
    echo "If branded_pdf_engine genuinely cannot handle this, state why explicitly." >&2
    exit 2
fi

if [[ "$BASENAME" =~ send.*email|email.*send|smtp|mailer ]]; then
    echo "BLOCKED: Do NOT write a custom email sender." >&2
    echo "USE: execution/send_onboarding_email.py SMTP pattern (SMTP_USERNAME/SMTP_PASSWORD in .env)" >&2
    exit 2
fi

if [[ "$BASENAME" =~ send.*sms|sms.*send|twilio_send ]]; then
    echo "BLOCKED: Do NOT write a custom SMS sender." >&2
    echo "USE: execution/twilio_sms.py" >&2
    exit 2
fi

# ============================================================
# INFORMATIONAL — warn but allow (exit 0)
# ============================================================

KEYWORDS=$(echo "$BASENAME" | tr '_-' '\n' | grep -v '^$')
INVENTORY_SCRIPT="/Users/williammarceaujr./dev-sandbox/scripts/inventory.py"
if [[ ! -f "$INVENTORY_SCRIPT" ]]; then
    exit 0
fi

MATCHES=""
for KEYWORD in $KEYWORDS; do
    if [[ ${#KEYWORD} -lt 4 ]]; then continue; fi
    RESULT=$(python3 "$INVENTORY_SCRIPT" search "$KEYWORD" 2>/dev/null)
    if [[ -n "$RESULT" && "$RESULT" != *"No matches"* ]]; then
        MATCHES="$MATCHES\n--- '$KEYWORD' ---\n$RESULT"
    fi
done

if [[ -n "$MATCHES" ]]; then
    echo "WARNING: Similar tools already exist — verify you cannot reuse before creating:" >&2
    echo -e "$MATCHES" >&2
fi

exit 0
