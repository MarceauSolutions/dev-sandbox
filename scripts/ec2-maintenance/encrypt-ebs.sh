#!/bin/bash
###############################################################################
# encrypt-ebs.sh - Encrypt EC2 EBS Volume with Minimal Downtime
#
# This script encrypts an unencrypted EBS root volume by:
# 1. Creating a snapshot
# 2. Copying snapshot with encryption
# 3. Creating new encrypted volume
# 4. Stopping instance, swapping volumes, starting instance
#
# REQUIREMENTS:
# - AWS CLI configured with appropriate permissions
# - Instance must be stoppable (not spot/scheduled)
# - ~30-60 minutes for 30GB volume
#
# USAGE:
#   ./encrypt-ebs.sh [--dry-run] [--instance-id i-xxx] [--profile aws-profile]
#
# Created: 2026-01-29
###############################################################################

set -e

# Configuration
INSTANCE_ID="${INSTANCE_ID:-i-01752306f94897d7d}"  # Default to Clawdbot EC2
AWS_PROFILE="${AWS_PROFILE:-marceau-admin}"
REGION="${AWS_REGION:-us-east-1}"
DRY_RUN=false
LOG_FILE="/tmp/ebs-encryption-$(date +%Y%m%d-%H%M%S).log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "$msg" | tee -a "$LOG_FILE"
}

error() {
    log "${RED}ERROR: $1${NC}"
    exit 1
}

warn() {
    log "${YELLOW}WARNING: $1${NC}"
}

success() {
    log "${GREEN}✓ $1${NC}"
}

info() {
    log "${BLUE}INFO: $1${NC}"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --instance-id)
            INSTANCE_ID="$2"
            shift 2
            ;;
        --profile)
            AWS_PROFILE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--dry-run] [--instance-id i-xxx] [--profile aws-profile]"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

AWS_CMD="aws --profile $AWS_PROFILE --region $REGION"

log "═══════════════════════════════════════════════════════════════"
log "       EBS ENCRYPTION SCRIPT - $(date)"
log "═══════════════════════════════════════════════════════════════"
log "Instance ID: $INSTANCE_ID"
log "AWS Profile: $AWS_PROFILE"
log "Region: $REGION"
log "Dry Run: $DRY_RUN"
log "Log File: $LOG_FILE"
log "═══════════════════════════════════════════════════════════════"

# Pre-flight checks
info "Running pre-flight checks..."

# Check AWS credentials
if ! $AWS_CMD sts get-caller-identity > /dev/null 2>&1; then
    error "AWS credentials not valid. Run: aws sso login --profile $AWS_PROFILE"
fi
success "AWS credentials valid"

# Get instance details
INSTANCE_INFO=$($AWS_CMD ec2 describe-instances --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].[State.Name,RootDeviceName,BlockDeviceMappings[0].Ebs.VolumeId,AvailabilityZone]' \
    --output text)

INSTANCE_STATE=$(echo "$INSTANCE_INFO" | awk '{print $1}')
ROOT_DEVICE=$(echo "$INSTANCE_INFO" | awk '{print $2}')
VOLUME_ID=$(echo "$INSTANCE_INFO" | awk '{print $3}')
AZ=$(echo "$INSTANCE_INFO" | awk '{print $4}')

info "Instance State: $INSTANCE_STATE"
info "Root Device: $ROOT_DEVICE"
info "Volume ID: $VOLUME_ID"
info "Availability Zone: $AZ"

# Check if already encrypted
IS_ENCRYPTED=$($AWS_CMD ec2 describe-volumes --volume-ids "$VOLUME_ID" \
    --query 'Volumes[0].Encrypted' --output text)

if [ "$IS_ENCRYPTED" == "True" ]; then
    success "Volume is already encrypted. Nothing to do."
    exit 0
fi

warn "Volume $VOLUME_ID is NOT encrypted. Proceeding with encryption..."

# Get volume size
VOLUME_SIZE=$($AWS_CMD ec2 describe-volumes --volume-ids "$VOLUME_ID" \
    --query 'Volumes[0].Size' --output text)
info "Volume Size: ${VOLUME_SIZE}GB"

# Estimate time
ESTIMATED_MINUTES=$((VOLUME_SIZE * 2))
warn "Estimated time: ~${ESTIMATED_MINUTES} minutes (including downtime)"

if [ "$DRY_RUN" == "true" ]; then
    log ""
    log "═══════════════════════════════════════════════════════════════"
    log "                    DRY RUN COMPLETE"
    log "═══════════════════════════════════════════════════════════════"
    log "Would perform the following actions:"
    log "  1. Create snapshot of $VOLUME_ID"
    log "  2. Copy snapshot with encryption"
    log "  3. Create encrypted volume in $AZ"
    log "  4. Stop instance $INSTANCE_ID"
    log "  5. Detach $VOLUME_ID from $ROOT_DEVICE"
    log "  6. Attach new encrypted volume to $ROOT_DEVICE"
    log "  7. Start instance"
    log "  8. Verify instance is running"
    log ""
    log "Run without --dry-run to execute."
    exit 0
fi

# Confirmation
log ""
warn "This will cause DOWNTIME for instance $INSTANCE_ID"
warn "Estimated downtime: 10-15 minutes"
read -p "Are you sure you want to proceed? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    log "Aborted by user."
    exit 1
fi

# Step 1: Create snapshot
log ""
info "Step 1/8: Creating snapshot of $VOLUME_ID..."
SNAPSHOT_ID=$($AWS_CMD ec2 create-snapshot \
    --volume-id "$VOLUME_ID" \
    --description "Pre-encryption snapshot for $INSTANCE_ID" \
    --tag-specifications "ResourceType=snapshot,Tags=[{Key=Name,Value=encryption-migration-$INSTANCE_ID},{Key=Purpose,Value=EBS-Encryption}]" \
    --query 'SnapshotId' --output text)
success "Snapshot created: $SNAPSHOT_ID"

# Wait for snapshot to complete
info "Waiting for snapshot to complete..."
$AWS_CMD ec2 wait snapshot-completed --snapshot-ids "$SNAPSHOT_ID"
success "Snapshot completed"

# Step 2: Copy snapshot with encryption
log ""
info "Step 2/8: Creating encrypted copy of snapshot..."
ENCRYPTED_SNAPSHOT_ID=$($AWS_CMD ec2 copy-snapshot \
    --source-region "$REGION" \
    --source-snapshot-id "$SNAPSHOT_ID" \
    --description "Encrypted copy of $SNAPSHOT_ID" \
    --encrypted \
    --query 'SnapshotId' --output text)
success "Encrypted snapshot copy initiated: $ENCRYPTED_SNAPSHOT_ID"

info "Waiting for encrypted snapshot to complete (this may take a while)..."
$AWS_CMD ec2 wait snapshot-completed --snapshot-ids "$ENCRYPTED_SNAPSHOT_ID"
success "Encrypted snapshot completed"

# Step 3: Create encrypted volume
log ""
info "Step 3/8: Creating encrypted volume from snapshot..."
NEW_VOLUME_ID=$($AWS_CMD ec2 create-volume \
    --availability-zone "$AZ" \
    --snapshot-id "$ENCRYPTED_SNAPSHOT_ID" \
    --volume-type gp3 \
    --tag-specifications "ResourceType=volume,Tags=[{Key=Name,Value=encrypted-root-$INSTANCE_ID},{Key=OriginalVolume,Value=$VOLUME_ID}]" \
    --query 'VolumeId' --output text)
success "Encrypted volume created: $NEW_VOLUME_ID"

info "Waiting for volume to become available..."
$AWS_CMD ec2 wait volume-available --volume-ids "$NEW_VOLUME_ID"
success "Encrypted volume is available"

# Step 4: Stop instance
log ""
info "Step 4/8: Stopping instance $INSTANCE_ID..."
warn ">>> DOWNTIME BEGINS NOW <<<"
$AWS_CMD ec2 stop-instances --instance-ids "$INSTANCE_ID" > /dev/null
$AWS_CMD ec2 wait instance-stopped --instance-ids "$INSTANCE_ID"
success "Instance stopped"

# Step 5: Detach old volume
log ""
info "Step 5/8: Detaching old volume $VOLUME_ID..."
$AWS_CMD ec2 detach-volume --volume-id "$VOLUME_ID" > /dev/null
sleep 10  # Wait for detachment
success "Old volume detached"

# Step 6: Attach new encrypted volume
log ""
info "Step 6/8: Attaching encrypted volume $NEW_VOLUME_ID..."
$AWS_CMD ec2 attach-volume \
    --volume-id "$NEW_VOLUME_ID" \
    --instance-id "$INSTANCE_ID" \
    --device "$ROOT_DEVICE" > /dev/null
sleep 10  # Wait for attachment
success "Encrypted volume attached"

# Step 7: Start instance
log ""
info "Step 7/8: Starting instance..."
$AWS_CMD ec2 start-instances --instance-ids "$INSTANCE_ID" > /dev/null
$AWS_CMD ec2 wait instance-running --instance-ids "$INSTANCE_ID"
success "Instance started"
warn ">>> DOWNTIME ENDED <<<"

# Step 8: Verify
log ""
info "Step 8/8: Verifying encryption..."
sleep 30  # Wait for instance to fully boot

# Get new public IP (may have changed)
NEW_IP=$($AWS_CMD ec2 describe-instances --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
info "New Public IP: $NEW_IP"

# Verify encryption
VERIFY_ENCRYPTED=$($AWS_CMD ec2 describe-volumes --volume-ids "$NEW_VOLUME_ID" \
    --query 'Volumes[0].Encrypted' --output text)

if [ "$VERIFY_ENCRYPTED" == "True" ]; then
    success "EBS encryption verified!"
else
    error "Encryption verification failed!"
fi

# Summary
log ""
log "═══════════════════════════════════════════════════════════════"
log "                    ENCRYPTION COMPLETE"
log "═══════════════════════════════════════════════════════════════"
log "Old Volume (unencrypted): $VOLUME_ID"
log "New Volume (encrypted):   $NEW_VOLUME_ID"
log "Instance IP:              $NEW_IP"
log ""
log "CLEANUP REQUIRED:"
log "  After verifying everything works, delete old resources:"
log "  aws ec2 delete-volume --volume-id $VOLUME_ID --profile $AWS_PROFILE"
log "  aws ec2 delete-snapshot --snapshot-id $SNAPSHOT_ID --profile $AWS_PROFILE"
log "  aws ec2 delete-snapshot --snapshot-id $ENCRYPTED_SNAPSHOT_ID --profile $AWS_PROFILE"
log ""
log "Log saved to: $LOG_FILE"
log "═══════════════════════════════════════════════════════════════"
