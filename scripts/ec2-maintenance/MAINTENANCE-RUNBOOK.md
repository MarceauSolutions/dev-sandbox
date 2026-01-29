# EC2 Maintenance Runbook

**Created**: 2026-01-29
**Purpose**: Standard procedures for EC2 maintenance tasks requiring downtime

---

## Pre-Maintenance Checklist

### 24 Hours Before
- [ ] Review AWS billing dashboard for any anomalies
- [ ] Check EC2 instance health in console
- [ ] Notify stakeholders of planned downtime (if applicable)
- [ ] Run `./notify-maintenance.sh --schedule` to set reminder

### 1 Hour Before
- [ ] Verify all active Clawdbot/Ralph tasks are complete
- [ ] Check no critical cron jobs running: `ssh ec2-user@$EC2_IP "crontab -l"`
- [ ] Save any in-progress work on EC2
- [ ] Run dry-run of maintenance script to verify prerequisites

### Immediately Before
- [ ] Final check for active connections: `ssh ec2-user@$EC2_IP "who"`
- [ ] Confirm low-traffic period (check Voice AI call logs)
- [ ] Have AWS Console open as backup

---

## Maintenance Window Schedule

**Recommended Windows** (US Eastern Time):
| Window | Time | Duration | Best For |
|--------|------|----------|----------|
| **Late Night** | 2:00 AM - 5:00 AM | 3 hours | Major changes (EBS encryption) |
| **Early Morning** | 5:00 AM - 7:00 AM | 2 hours | Quick maintenance |
| **Weekend** | Saturday 2:00 AM | 4 hours | Extended maintenance |

**Avoid**:
- Business hours (9 AM - 6 PM) - Voice AI may be in use
- Monday mornings - Higher activity
- End of month - Business reporting may need systems

---

## Available Maintenance Scripts

### 1. EBS Encryption (`encrypt-ebs.sh`)
**Purpose**: Encrypt unencrypted root EBS volume
**Downtime**: 10-15 minutes
**Risk**: Medium (volume swap)

```bash
# Dry run first (always!)
./encrypt-ebs.sh --dry-run

# Execute
./encrypt-ebs.sh --instance-id i-01752306f94897d7d --profile marceau-admin
```

### 2. Instance Type Change (future)
**Purpose**: Resize EC2 instance
**Downtime**: 5-10 minutes

### 3. Security Updates (future)
**Purpose**: Apply OS patches requiring reboot
**Downtime**: 5 minutes

---

## Emergency Rollback Procedures

### If Instance Won't Start After EBS Swap

1. **Check CloudWatch Events**:
   ```bash
   aws ec2 describe-instance-status --instance-ids i-01752306f94897d7d \
       --profile marceau-admin
   ```

2. **Reattach Original Volume**:
   ```bash
   # Stop instance
   aws ec2 stop-instances --instance-ids i-01752306f94897d7d --profile marceau-admin
   aws ec2 wait instance-stopped --instance-ids i-01752306f94897d7d

   # Detach new volume
   aws ec2 detach-volume --volume-id vol-NEW --profile marceau-admin

   # Reattach original volume (from log file)
   aws ec2 attach-volume --volume-id vol-ORIGINAL \
       --instance-id i-01752306f94897d7d \
       --device /dev/xvda --profile marceau-admin

   # Start instance
   aws ec2 start-instances --instance-ids i-01752306f94897d7d --profile marceau-admin
   ```

3. **Verify Recovery**:
   ```bash
   ssh ec2-user@$(aws ec2 describe-instances --instance-ids i-01752306f94897d7d \
       --query 'Reservations[0].Instances[0].PublicIpAddress' --output text \
       --profile marceau-admin)
   ```

---

## Post-Maintenance Verification

### Immediate (within 5 minutes)
- [ ] SSH access works: `ssh ec2-user@$NEW_IP`
- [ ] Clawdbot responds: Check Telegram bot
- [ ] Check system logs: `journalctl -n 50`

### Within 1 Hour
- [ ] All cron jobs running: `systemctl status crond`
- [ ] fail2ban active: `systemctl status fail2ban`
- [ ] Voice AI lines working (test call if critical)

### Within 24 Hours
- [ ] Review CloudWatch metrics for anomalies
- [ ] Check Clawdbot error logs
- [ ] Verify git push/pull from EC2 works

---

## Quick Reference

```bash
# EC2 Instance Details
INSTANCE_ID="i-01752306f94897d7d"
AWS_PROFILE="marceau-admin"
REGION="us-east-1"

# Get current IP
aws ec2 describe-instances --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' --output text \
    --profile $AWS_PROFILE

# Check instance state
aws ec2 describe-instance-status --instance-ids $INSTANCE_ID --profile $AWS_PROFILE

# View maintenance logs
ls -la /tmp/ebs-encryption-*.log
```

---

## Contacts

- **AWS Support**: Console → Support Center
- **EC2 Issues**: Check `docs/incidents/` for similar past issues
- **Escalation**: Review TROUBLESHOOTING-METHODOLOGY.md

---

**Document Status**: Living document - update after each maintenance event
