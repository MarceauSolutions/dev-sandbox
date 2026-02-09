# Enterprise Security Framework

**Classification**: INTERNAL - SECURITY SENSITIVE
**Created**: 2026-01-29
**Author**: Security Engineering
**Review Cycle**: Monthly

---

## Executive Summary

This document establishes enterprise-grade security controls across all systems including AWS EC2 infrastructure, MCP servers, credentials management, and operational security. It supersedes and enhances the previous MCP-focused remediation plan.

**Risk Assessment**: HIGH
**Current Security Posture**: 3/10
**Target Security Posture**: 9/10

---

## Attack Surface Analysis

### Critical Assets Identified

| Asset | Type | Risk Level | Data Classification |
|-------|------|------------|---------------------|
| EC2 Instance (44.193.244.59) | Infrastructure | CRITICAL | Contains credentials, SSH access |
| `.env` file | Secrets | CRITICAL | 20+ API keys/tokens |
| AWS Account (005023349538) | Cloud | CRITICAL | IAM, billing, resources |
| 15 MCP Servers | Applications | HIGH | Client PII, financial data |
| Clawdbot | Service | HIGH | Telegram access, code execution |
| Lead Database | Data | MEDIUM | Business contact info |

### Vulnerability Summary

| Category | Count | Severity | Status |
|----------|-------|----------|--------|
| Command Injection | 2 | CRITICAL | OPEN |
| Hardcoded Credentials | 1 | CRITICAL | OPEN |
| Exposed Ports | 5 | HIGH | OPEN |
| Over-Privileged IAM | 1 | HIGH | OPEN |
| No Secrets Encryption | 1 | HIGH | OPEN |
| No Audit Logging | 15 | MEDIUM | OPEN |
| Missing Rate Limiting | 15 | MEDIUM | OPEN |

---

## Security Architecture

### Defense in Depth Layers

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: PERIMETER                                               │
│ - AWS Security Groups (restricted IP allowlists)                │
│ - VPC Network ACLs                                              │
│ - SSH key-only authentication (no passwords)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│ Layer 2: NETWORK                                                 │
│ - TLS 1.3 for all communications                                │
│ - VPN for administrative access                                 │
│ - Internal service mesh (no public exposure)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3: HOST                                                    │
│ - Minimal installed packages                                    │
│ - Automatic security updates (unattended-upgrades)              │
│ - fail2ban for brute-force protection                          │
│ - auditd for system call logging                               │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│ Layer 4: APPLICATION                                             │
│ - Input sanitization (mcp_security.py)                          │
│ - Rate limiting                                                 │
│ - Least-privilege execution                                     │
│ - Audit logging                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│ Layer 5: DATA                                                    │
│ - Encrypted secrets (AWS Secrets Manager or local encryption)   │
│ - Encrypted at rest (EBS encryption)                           │
│ - Encrypted in transit (TLS)                                   │
│ - Data classification and handling                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 0: IMMEDIATE (Within 24 Hours)

#### 0.1 Rotate All Compromised Credentials

**CRITICAL**: The `.env` file contains live credentials that should be rotated immediately.

```bash
# Credentials requiring immediate rotation:
# 1. AWS Access Keys (AMAZON_AWS_ACCESS_KEY, AMAZON_AWS_SECRET_KEY)
# 2. Twilio Auth Token (TWILIO_AUTH_TOKEN)
# 3. SMTP Password (SMTP_PASSWORD)
# 4. ClickUp API Token (CLICKUP_API_TOKEN)
# 5. PyPI Token (PYPI_TOKEN)
# 6. All OAuth secrets
```

**Rotation Process**:
1. Generate new credentials in each service's dashboard
2. Update `.env` with new values
3. Test each service
4. Revoke old credentials
5. Document rotation in security log

#### 0.2 Restrict EC2 Security Group

**Current State** (INSECURE):
```
Port 22 (SSH)  → My IP only (Good)
Port 80        → 0.0.0.0/0 (BAD)
Port 443       → 0.0.0.0/0 (BAD)
Port 3002      → 0.0.0.0/0 (BAD)
Port 8000      → 0.0.0.0/0 (BAD)
```

**Target State** (SECURE):
```
Port 22 (SSH)  → Specific IP allowlist only
Port 80        → CloudFront/ALB only (if public)
Port 443       → CloudFront/ALB only (if public)
Port 3002      → REMOVE or VPN only
Port 8000      → REMOVE or VPN only
```

**AWS CLI Commands**:
```bash
# Get current security group rules
aws ec2 describe-security-groups --group-names marceau-web-server

# Revoke overly permissive rules
aws ec2 revoke-security-group-ingress \
    --group-name marceau-web-server \
    --protocol tcp \
    --port 3002 \
    --cidr 0.0.0.0/0

# Add restricted rule (your IP only)
aws ec2 authorize-security-group-ingress \
    --group-name marceau-web-server \
    --protocol tcp \
    --port 3002 \
    --cidr $(curl -s ifconfig.me)/32
```

---

### Phase 1: CRITICAL (Week 1)

#### 1.1 Fix Command Injection Vulnerabilities

**File**: `projects/marceau-solutions/fitness-influencer-mcp/src/fitness_influencer_mcp/video_jumpcut.py`

See implementation in `execution/mcp_security.py` - `validate_path()` function.

#### 1.2 Implement Encrypted Secrets Management

**Option A**: AWS Secrets Manager (Recommended for production)
**Option B**: Local encryption with Fernet (Implemented below)

```python
# execution/secrets_manager.py
# See full implementation below
```

#### 1.3 Enable EC2 Instance Hardening

Create hardening script: `scripts/ec2-hardening.sh`

---

### Phase 2: HIGH (Weeks 2-3)

#### 2.1 Implement Zero-Trust MCP Architecture

Every MCP call must:
1. Authenticate the caller
2. Validate inputs
3. Check rate limits
4. Audit log the action
5. Validate outputs before returning

#### 2.2 Deploy Intrusion Detection

- Enable AWS GuardDuty
- Configure CloudWatch alarms
- Set up SNS notifications for security events

#### 2.3 Implement Secrets Rotation

Automated rotation schedule:
- API keys: 90 days
- OAuth tokens: 30 days
- AWS credentials: 90 days
- SSH keys: 180 days

---

### Phase 3: MEDIUM (Weeks 4-6)

#### 3.1 Network Segmentation

- Create private subnet for services
- Use NAT Gateway for outbound
- Deploy Application Load Balancer for inbound

#### 3.2 Implement WAF

- AWS WAF with managed rules
- Rate limiting at edge
- Bot protection

#### 3.3 Security Monitoring Dashboard

- CloudWatch dashboards
- Security metrics
- Anomaly detection

---

## EC2 Hardening Checklist

### Operating System

- [ ] Update all packages: `sudo apt update && sudo apt upgrade -y`
- [ ] Enable automatic security updates
- [ ] Remove unnecessary packages
- [ ] Disable root login via SSH
- [ ] Configure SSH key-only authentication
- [ ] Set strong SSH ciphers
- [ ] Install and configure fail2ban
- [ ] Configure firewall (ufw)
- [ ] Enable auditd

### AWS Configuration

- [ ] Enable EBS encryption
- [ ] Enable detailed monitoring
- [ ] Configure IAM instance profile (not access keys)
- [ ] Enable VPC Flow Logs
- [ ] Configure CloudTrail
- [ ] Enable GuardDuty
- [ ] Set up CloudWatch alarms

### Application Security

- [ ] Run services as non-root user
- [ ] Use systemd for service management
- [ ] Configure resource limits
- [ ] Enable application-level logging
- [ ] Implement health checks

---

## Incident Response Plan

### Severity Levels

| Level | Description | Response Time | Example |
|-------|-------------|---------------|---------|
| P0 | Active breach | 15 minutes | Unauthorized access detected |
| P1 | Imminent threat | 1 hour | Credentials leaked |
| P2 | Vulnerability | 24 hours | New CVE affecting system |
| P3 | Weakness | 1 week | Missing security control |

### Response Procedures

#### P0 - Active Breach

1. **CONTAIN** (0-15 min)
   ```bash
   # Isolate EC2 instance
   aws ec2 modify-instance-attribute --instance-id i-xxx \
       --groups sg-isolated-incident

   # Revoke all IAM credentials
   aws iam update-access-key --access-key-id AKIA... --status Inactive --user-name xxx
   ```

2. **PRESERVE** (15-30 min)
   ```bash
   # Snapshot instance for forensics
   aws ec2 create-snapshot --volume-id vol-xxx --description "Incident snapshot"

   # Capture memory dump (if tools available)
   # Preserve all logs
   ```

3. **INVESTIGATE** (30 min - 4 hours)
   - Review CloudTrail logs
   - Analyze audit logs
   - Identify attack vector
   - Determine scope of compromise

4. **ERADICATE** (4-24 hours)
   - Remove malicious access
   - Patch vulnerability
   - Reset all credentials

5. **RECOVER** (24-72 hours)
   - Restore from clean backup
   - Verify integrity
   - Gradually restore access

6. **LEARN** (Post-incident)
   - Write incident report
   - Update security controls
   - Conduct team debrief

---

## Security Metrics

### Key Performance Indicators

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Mean Time to Detect (MTTD) | < 1 hour | Unknown | NOT MEASURED |
| Mean Time to Respond (MTTR) | < 4 hours | Unknown | NOT MEASURED |
| Credential Rotation Compliance | 100% | 0% | FAILING |
| Patch Compliance | 100% | Unknown | NOT MEASURED |
| Security Training Completion | 100% | N/A | N/A |
| MCP Security Coverage | 100% | 0% | FAILING |

### Monitoring Dashboards

1. **Security Events Dashboard**
   - Failed login attempts
   - Unusual API patterns
   - Rate limit violations
   - Audit log anomalies

2. **Infrastructure Dashboard**
   - EC2 CPU/memory/network
   - Security group changes
   - IAM changes
   - S3 access patterns

3. **Application Dashboard**
   - MCP tool call rates
   - Error rates
   - Response times
   - Input validation failures

---

## Compliance Considerations

### Data Protection

- Client PII (Trainerize): Subject to privacy regulations
- Financial data (Amazon Seller): Subject to PCI-DSS
- Contact data (Apollo): Subject to GDPR/CCPA

### Required Controls

- [ ] Data encryption at rest
- [ ] Data encryption in transit
- [ ] Access logging and auditing
- [ ] Data retention policies
- [ ] Right to deletion capability
- [ ] Breach notification procedures

---

## Appendix A: Security Tools Reference

| Tool | Purpose | Location |
|------|---------|----------|
| `mcp_security.py` | Application security utilities | `execution/mcp_security.py` |
| `secrets_manager.py` | Encrypted secrets handling | `execution/secrets_manager.py` |
| `security_scanner.py` | Vulnerability scanning | `execution/security_scanner.py` |
| `ec2-hardening.sh` | Instance hardening | `scripts/ec2-hardening.sh` |
| `rotate-credentials.sh` | Credential rotation | `scripts/rotate-credentials.sh` |

---

## Appendix B: Emergency Contacts

| Role | Contact | Escalation |
|------|---------|------------|
| Security Lead | William Marceau | Primary |
| AWS Support | aws.amazon.com/support | For AWS issues |
| Incident Response | TBD | After hours |

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-29 | Security Engineering | Initial release |
