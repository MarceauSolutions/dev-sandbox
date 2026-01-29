#!/bin/bash
###############################################################################
# daily-backup.sh - Daily backup of critical data to S3
#
# Backs up:
# - .env file (secrets)
# - data/ directory (Stripe events, form submissions)
# - output/ directory (campaign data, form submissions)
# - config/ directory (service catalog)
#
# USAGE:
#   ./scripts/daily-backup.sh                    # Run backup
#   ./scripts/daily-backup.sh --restore DATE     # Restore from date (YYYY-MM-DD)
#   ./scripts/daily-backup.sh --list             # List available backups
#
# CRON SETUP (on EC2):
#   0 2 * * * /home/clawdbot/dev-sandbox/scripts/daily-backup.sh >> /var/log/backup.log 2>&1
#
# Created: 2026-01-29
###############################################################################

set -e

# Configuration
S3_BUCKET="marceau-company-backups"
BACKUP_PREFIX="daily"
DEV_SANDBOX="/home/clawdbot/dev-sandbox"
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="/tmp/backup-$TIMESTAMP"
LOG_FILE="/var/log/backup.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error() {
    log "${RED}ERROR: $1${NC}"
    exit 1
}

success() {
    log "${GREEN}SUCCESS: $1${NC}"
}

# Check AWS CLI
check_aws() {
    if ! command -v aws &> /dev/null; then
        error "AWS CLI not installed"
    fi

    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials not configured"
    fi
}

# Create backup
do_backup() {
    log "Starting daily backup..."

    # Create temp directory
    mkdir -p "$BACKUP_DIR"

    # Backup .env (encrypted for security)
    if [ -f "$DEV_SANDBOX/.env" ]; then
        cp "$DEV_SANDBOX/.env" "$BACKUP_DIR/env-backup"
        log "Backed up .env"
    fi

    # Backup data directory
    if [ -d "$DEV_SANDBOX/data" ]; then
        cp -r "$DEV_SANDBOX/data" "$BACKUP_DIR/data"
        log "Backed up data/"
    fi

    # Backup output directory
    if [ -d "$DEV_SANDBOX/output" ]; then
        cp -r "$DEV_SANDBOX/output" "$BACKUP_DIR/output"
        log "Backed up output/"
    fi

    # Backup config directory
    if [ -d "$DEV_SANDBOX/config" ]; then
        cp -r "$DEV_SANDBOX/config" "$BACKUP_DIR/config"
        log "Backed up config/"
    fi

    # Create tarball
    TARBALL="/tmp/backup-$TIMESTAMP.tar.gz"
    tar -czf "$TARBALL" -C "$BACKUP_DIR" .

    # Upload to S3
    log "Uploading to S3..."
    aws s3 cp "$TARBALL" "s3://$S3_BUCKET/$BACKUP_PREFIX/$DATE/backup-$TIMESTAMP.tar.gz"

    # Create 'latest' marker
    aws s3 cp "$TARBALL" "s3://$S3_BUCKET/$BACKUP_PREFIX/latest.tar.gz"

    # Cleanup
    rm -rf "$BACKUP_DIR" "$TARBALL"

    # Calculate size
    SIZE=$(aws s3 ls "s3://$S3_BUCKET/$BACKUP_PREFIX/$DATE/backup-$TIMESTAMP.tar.gz" | awk '{print $3}')
    SIZE_KB=$((SIZE / 1024))

    success "Backup completed: $SIZE_KB KB uploaded to s3://$S3_BUCKET/$BACKUP_PREFIX/$DATE/"

    # Retention: Keep last 30 days of backups
    cleanup_old_backups
}

# Cleanup old backups (keep last 30 days)
cleanup_old_backups() {
    log "Checking for old backups to clean up..."

    CUTOFF_DATE=$(date -d "30 days ago" +%Y-%m-%d 2>/dev/null || date -v-30d +%Y-%m-%d)

    aws s3 ls "s3://$S3_BUCKET/$BACKUP_PREFIX/" | while read -r line; do
        FOLDER=$(echo "$line" | awk '{print $2}' | tr -d '/')

        # Skip 'latest' and invalid folder names
        if [[ "$FOLDER" == "latest"* ]] || [[ ! "$FOLDER" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
            continue
        fi

        if [[ "$FOLDER" < "$CUTOFF_DATE" ]]; then
            log "Removing old backup: $FOLDER"
            aws s3 rm "s3://$S3_BUCKET/$BACKUP_PREFIX/$FOLDER/" --recursive
        fi
    done
}

# List available backups
list_backups() {
    log "Available backups:"
    echo ""
    aws s3 ls "s3://$S3_BUCKET/$BACKUP_PREFIX/" | grep PRE | awk '{print $2}' | tr -d '/' | sort -r | head -30
    echo ""

    # Show latest backup size
    LATEST=$(aws s3 ls "s3://$S3_BUCKET/$BACKUP_PREFIX/latest.tar.gz" 2>/dev/null)
    if [ -n "$LATEST" ]; then
        SIZE=$(echo "$LATEST" | awk '{print $3}')
        DATE=$(echo "$LATEST" | awk '{print $1}')
        echo "Latest backup: $DATE ($(($SIZE / 1024)) KB)"
    fi
}

# Restore from backup
restore_backup() {
    RESTORE_DATE=$1

    if [ -z "$RESTORE_DATE" ]; then
        error "Please specify date to restore: --restore YYYY-MM-DD"
    fi

    log "Restoring backup from $RESTORE_DATE..."

    # Find backup file
    BACKUP_FILE=$(aws s3 ls "s3://$S3_BUCKET/$BACKUP_PREFIX/$RESTORE_DATE/" | awk '{print $4}' | head -1)

    if [ -z "$BACKUP_FILE" ]; then
        error "No backup found for date: $RESTORE_DATE"
    fi

    # Download
    RESTORE_DIR="/tmp/restore-$TIMESTAMP"
    mkdir -p "$RESTORE_DIR"

    log "Downloading backup..."
    aws s3 cp "s3://$S3_BUCKET/$BACKUP_PREFIX/$RESTORE_DATE/$BACKUP_FILE" "/tmp/$BACKUP_FILE"

    # Extract
    tar -xzf "/tmp/$BACKUP_FILE" -C "$RESTORE_DIR"

    log "Backup extracted to: $RESTORE_DIR"
    log "Contents:"
    ls -la "$RESTORE_DIR"

    echo ""
    log "${YELLOW}To restore, manually copy files from $RESTORE_DIR to $DEV_SANDBOX${NC}"
    log "Example: cp $RESTORE_DIR/env-backup $DEV_SANDBOX/.env"
}

# Main
check_aws

case "${1:-}" in
    --list)
        list_backups
        ;;
    --restore)
        restore_backup "$2"
        ;;
    *)
        do_backup
        ;;
esac
