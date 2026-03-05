#!/bin/bash
# backup-n8n-workflows.sh - n8n Workflow Backup
#
# WHAT: Exports all n8n workflows from EC2 to local backup directory
# WHY: Disaster recovery and version control for automation workflows (SOP 30)
# DEPENDENCIES: ssh, curl, jq (optional)
# API_KEYS: N8N_API_KEY (from .env, used for API authentication)
#
# Usage: ./scripts/backup-n8n-workflows.sh

set -euo pipefail

# Load N8N_API_KEY from .env if available
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"
if [ -f "${ENV_FILE}" ]; then
    N8N_API_KEY=$(grep '^N8N_API_KEY=' "${ENV_FILE}" | cut -d'=' -f2- | tr -d '"' || echo "")
fi

N8N_HOST="https://n8n.marceausolutions.com"
BACKUP_DIR="projects/shared/n8n-workflows/backups"
DATE=$(date +%Y-%m-%d)
BACKUP_PATH="${BACKUP_DIR}/${DATE}"

echo "=== n8n Workflow Backup ==="
echo "Date: ${DATE}"
echo "Host: ${N8N_HOST}"
if [ -n "${N8N_API_KEY:-}" ]; then
    echo "Auth: API key loaded from .env"
else
    echo "Auth: No API key (using localhost bypass via SSH)"
fi
echo ""

# Create backup directory
mkdir -p "${BACKUP_PATH}"

# Known workflow IDs (from coaching-ops-runbook.md + client-acquisition-system-guide.md)
declare -A WORKFLOWS=(
    ["aBxCj48nGQVLRRnq"]="Coaching-Monday-Checkin"
    ["1wS9VvXIt95BrR9V"]="Coaching-Payment-Welcome"
    ["uKjqRexDIheaDJJH"]="Coaching-Cancellation-Exit"
    ["89XxmBQMEej15nak"]="Fitness-SMS-Outreach"
    ["VKC5cifm595JNcwG"]="Fitness-SMS-Followup-Sequence"
    ["hgInaJCLffLFBX1G"]="Lead-Magnet-Capture"
    ["szuYee7gtQkzRn3L"]="Nurture-Sequence-7Day"
    ["Y2jfeIlTRDlbCHeS"]="Non-Converter-Followup"
    ["WTZDxLDQuSkIkcqf"]="Challenge-Signup-7Day"
    ["Xza1DB4f4PIHw2lZ"]="Challenge-Day7-Upsell"
    ["j306crRxCmWW3dMo"]="Premium-Waitlist-Capture"
    ["kk7ZjWtjmZgylVzi"]="Digital-Product-Delivery"
    ["BsoplLFe1brLCBof"]="GitHub-Push-Notifications"
    ["G14Mb6lpeFZVYGwa"]="SMS-Response-Handler-v2"
    ["QhDtNagsZFUrKFsG"]="n8n-Health-Check"
    ["M62QBpROE48mEgDC"]="Weekly-Campaign-Analytics"
    ["2QaQbhIUlL7ctfq4"]="Monthly-Workflow-Backup"
)

# Export each workflow via SSH
echo "Connecting to EC2 to export workflows..."
for ID in "${!WORKFLOWS[@]}"; do
    NAME="${WORKFLOWS[$ID]}"
    echo "  Exporting: ${NAME} (${ID})..."

    # Build curl command with optional API key header
    CURL_CMD="curl -s http://localhost:5678/api/v1/workflows/${ID}"
    if [ -n "${N8N_API_KEY:-}" ]; then
        CURL_CMD="curl -s -H 'X-N8N-API-KEY: ${N8N_API_KEY}' http://localhost:5678/api/v1/workflows/${ID}"
    fi

    ssh -i ~/.ssh/marceau-ec2-key.pem ec2-user@34.193.98.97 \
        "${CURL_CMD}" \
        > "${BACKUP_PATH}/${NAME}.json" 2>/dev/null || {
            echo "    WARNING: Failed to export ${NAME}"
            continue
        }

    # Check if file has content
    if [ -s "${BACKUP_PATH}/${NAME}.json" ]; then
        echo "    OK"
    else
        echo "    WARNING: Empty export for ${NAME}"
        rm -f "${BACKUP_PATH}/${NAME}.json"
    fi
done

# Count successful exports
EXPORTED=$(ls -1 "${BACKUP_PATH}"/*.json 2>/dev/null | wc -l | tr -d ' ')
TOTAL=${#WORKFLOWS[@]}

echo ""
echo "=== Backup Complete ==="
echo "Exported: ${EXPORTED}/${TOTAL} workflows"
echo "Location: ${BACKUP_PATH}/"
echo ""

if [ "${EXPORTED}" -eq "0" ]; then
    echo "ERROR: No workflows exported. Check SSH connection and n8n status."
    echo "  SSH: ssh -i ~/.ssh/marceau-ec2-key.pem ec2-user@34.193.98.97"
    echo "  Health: curl http://34.193.98.97:5678/healthz"
    exit 1
fi

echo "To commit: git add ${BACKUP_PATH} && git commit -m 'n8n backup ${DATE}'"
