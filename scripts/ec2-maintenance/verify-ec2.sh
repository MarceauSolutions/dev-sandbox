#!/bin/bash
###############################################################################
# verify-ec2.sh - Post-Maintenance EC2 Verification
#
# Runs automated health checks after maintenance to ensure system is operational
#
# USAGE:
#   ./verify-ec2.sh [--quick|--full]
#
# Created: 2026-01-29
###############################################################################

set -e

# Configuration
AWS_PROFILE="${AWS_PROFILE:-marceau-admin}"
REGION="${AWS_REGION:-us-east-1}"
INSTANCE_ID="${INSTANCE_ID:-i-01752306f94897d7d}"

AWS_CMD="aws --profile $AWS_PROFILE --region $REGION"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

check() {
    local name="$1"
    local status="$2"  # pass, fail, warn
    local detail="$3"

    case $status in
        pass)
            echo -e "${GREEN}✓${NC} $name: $detail"
            ((PASS++))
            ;;
        fail)
            echo -e "${RED}✗${NC} $name: $detail"
            ((FAIL++))
            ;;
        warn)
            echo -e "${YELLOW}⚠${NC} $name: $detail"
            ((WARN++))
            ;;
    esac
}

echo "═══════════════════════════════════════════════════════════════"
echo "       EC2 POST-MAINTENANCE VERIFICATION"
echo "       $(date)"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# 1. AWS Authentication
echo -e "${BLUE}[1/8] AWS Authentication${NC}"
if $AWS_CMD sts get-caller-identity > /dev/null 2>&1; then
    IDENTITY=$($AWS_CMD sts get-caller-identity --query 'Arn' --output text)
    check "AWS Auth" "pass" "$IDENTITY"
else
    check "AWS Auth" "fail" "Cannot authenticate. Run: aws sso login --profile $AWS_PROFILE"
fi

# 2. Instance State
echo -e "\n${BLUE}[2/8] Instance State${NC}"
STATE=$($AWS_CMD ec2 describe-instances --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].State.Name' --output text 2>/dev/null || echo "error")

if [ "$STATE" == "running" ]; then
    check "Instance State" "pass" "$STATE"
else
    check "Instance State" "fail" "$STATE (expected: running)"
fi

# 3. Public IP
echo -e "\n${BLUE}[3/8] Network${NC}"
PUBLIC_IP=$($AWS_CMD ec2 describe-instances --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' --output text 2>/dev/null || echo "None")

if [ "$PUBLIC_IP" != "None" ] && [ -n "$PUBLIC_IP" ]; then
    check "Public IP" "pass" "$PUBLIC_IP"
else
    check "Public IP" "fail" "No public IP assigned"
fi

# 4. SSH Connectivity
echo -e "\n${BLUE}[4/8] SSH Connectivity${NC}"
if [ "$PUBLIC_IP" != "None" ] && [ -n "$PUBLIC_IP" ]; then
    if timeout 10 ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 ec2-user@$PUBLIC_IP "echo 'SSH OK'" 2>/dev/null | grep -q "SSH OK"; then
        check "SSH Access" "pass" "Connected successfully"
    else
        check "SSH Access" "fail" "Cannot connect via SSH"
    fi
else
    check "SSH Access" "warn" "Skipped (no public IP)"
fi

# 5. EBS Volume
echo -e "\n${BLUE}[5/8] EBS Volume${NC}"
VOLUME_INFO=$($AWS_CMD ec2 describe-instances --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].BlockDeviceMappings[0].Ebs.VolumeId' --output text 2>/dev/null)

if [ -n "$VOLUME_INFO" ] && [ "$VOLUME_INFO" != "None" ]; then
    ENCRYPTED=$($AWS_CMD ec2 describe-volumes --volume-ids "$VOLUME_INFO" \
        --query 'Volumes[0].Encrypted' --output text 2>/dev/null)

    if [ "$ENCRYPTED" == "True" ]; then
        check "EBS Encryption" "pass" "$VOLUME_INFO is encrypted"
    else
        check "EBS Encryption" "warn" "$VOLUME_INFO is NOT encrypted"
    fi
else
    check "EBS Volume" "fail" "Cannot determine volume"
fi

# 6. Services (if SSH works)
echo -e "\n${BLUE}[6/8] Services${NC}"
if [ "$PUBLIC_IP" != "None" ] && [ -n "$PUBLIC_IP" ]; then
    # Check fail2ban
    F2B_STATUS=$(timeout 10 ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 ec2-user@$PUBLIC_IP \
        "sudo systemctl is-active fail2ban 2>/dev/null" 2>/dev/null || echo "unknown")
    if [ "$F2B_STATUS" == "active" ]; then
        check "fail2ban" "pass" "active"
    elif [ "$F2B_STATUS" == "unknown" ]; then
        check "fail2ban" "warn" "Could not verify"
    else
        check "fail2ban" "fail" "$F2B_STATUS"
    fi

    # Check Clawdbot (check if process exists)
    CLAWDBOT=$(timeout 10 ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 ec2-user@$PUBLIC_IP \
        "pgrep -f clawdbot || echo 'not running'" 2>/dev/null || echo "unknown")
    if [[ "$CLAWDBOT" =~ ^[0-9]+$ ]]; then
        check "Clawdbot Process" "pass" "PID $CLAWDBOT"
    elif [ "$CLAWDBOT" == "unknown" ]; then
        check "Clawdbot Process" "warn" "Could not verify"
    else
        check "Clawdbot Process" "warn" "Not detected (may need manual start)"
    fi
fi

# 7. Security Group
echo -e "\n${BLUE}[7/8] Security Group${NC}"
SG_ID=$($AWS_CMD ec2 describe-instances --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' --output text 2>/dev/null)

if [ -n "$SG_ID" ] && [ "$SG_ID" != "None" ]; then
    SSH_RULE=$($AWS_CMD ec2 describe-security-groups --group-ids "$SG_ID" \
        --query 'SecurityGroups[0].IpPermissions[?FromPort==`22`].IpRanges[].CidrIp' --output text 2>/dev/null)

    if echo "$SSH_RULE" | grep -q "0.0.0.0/0"; then
        check "SSH Access Rule" "warn" "Open to 0.0.0.0/0 - consider restricting"
    elif [ -n "$SSH_RULE" ]; then
        check "SSH Access Rule" "pass" "Restricted to: $SSH_RULE"
    else
        check "SSH Access Rule" "pass" "SSH port restricted"
    fi
else
    check "Security Group" "warn" "Could not verify"
fi

# 8. CloudWatch Status
echo -e "\n${BLUE}[8/8] Instance Health${NC}"
INSTANCE_STATUS=$($AWS_CMD ec2 describe-instance-status --instance-ids "$INSTANCE_ID" \
    --query 'InstanceStatuses[0].InstanceStatus.Status' --output text 2>/dev/null || echo "unknown")
SYSTEM_STATUS=$($AWS_CMD ec2 describe-instance-status --instance-ids "$INSTANCE_ID" \
    --query 'InstanceStatuses[0].SystemStatus.Status' --output text 2>/dev/null || echo "unknown")

if [ "$INSTANCE_STATUS" == "ok" ] && [ "$SYSTEM_STATUS" == "ok" ]; then
    check "Health Checks" "pass" "Instance: $INSTANCE_STATUS, System: $SYSTEM_STATUS"
elif [ "$INSTANCE_STATUS" == "initializing" ] || [ "$SYSTEM_STATUS" == "initializing" ]; then
    check "Health Checks" "warn" "Still initializing (wait a few minutes)"
else
    check "Health Checks" "fail" "Instance: $INSTANCE_STATUS, System: $SYSTEM_STATUS"
fi

# Summary
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "                    VERIFICATION SUMMARY"
echo "═══════════════════════════════════════════════════════════════"
echo -e "  ${GREEN}Passed:${NC}  $PASS"
echo -e "  ${YELLOW}Warnings:${NC} $WARN"
echo -e "  ${RED}Failed:${NC}  $FAIL"
echo ""

if [ $FAIL -gt 0 ]; then
    echo -e "${RED}⚠ ATTENTION: $FAIL check(s) failed. Review before proceeding.${NC}"
    exit 1
elif [ $WARN -gt 0 ]; then
    echo -e "${YELLOW}Some warnings detected. Review recommended.${NC}"
    exit 0
else
    echo -e "${GREEN}All checks passed! System is operational.${NC}"
    exit 0
fi
