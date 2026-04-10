# Mac Mini vs EC2: Security & Cost Analysis

**Date:** 2026-01-31
**Purpose:** Reevaluate hosting decision for Clawdbot/AI assistant

---

## Current Setup: EC2

- **Instance:** t4g (ARM) on AWS
- **Cost:** ~$15-30/month depending on instance size
- **Security:** SSH keys, firewall rules, some protocols in place
- **Exposure:** Public internet (port 22 + any exposed services)

---

## The Security Concern

William's concern: **API keys and credentials are stored on an internet-exposed server.**

**What's at risk:**
- Anthropic API key (Claude)
- OpenAI/xAI API keys
- Twilio credentials (SMS)
- Google OAuth tokens
- Stripe API keys (if added)
- Any client data

**Attack vectors on EC2:**
1. SSH brute force (mitigated with key auth, but still probed)
2. Exploits in exposed services (Clawdbot endpoints)
3. AWS account compromise
4. Supply chain attacks (dependencies)
5. AI-specific attacks (prompt injection to leak keys)

**Reality check:** Your EC2 is being probed constantly. Every server on the public internet is. The question is whether your defenses hold.

---

## Option A: Mac Mini at Home

### Pros

| Factor | Benefit |
|--------|---------|
| **Physical security** | In your home, behind your router |
| **No public IP** | Not directly exposed to internet |
| **Network isolation** | Only accessible from your LAN (or via Tailscale/VPN) |
| **One-time cost** | No recurring cloud bills |
| **Apple Silicon** | Fast, power-efficient, great for AI workloads |
| **Local data** | API keys never leave your network |
| **macOS security** | FileVault encryption, Gatekeeper, etc. |

### Cons

| Factor | Drawback |
|--------|----------|
| **Uptime depends on you** | Power outages, internet outages affect it |
| **Physical theft risk** | Someone could steal the device |
| **No redundancy** | Single point of failure |
| **Maintenance** | You handle updates, backups, etc. |
| **Remote access complexity** | Need Tailscale/VPN for mobile access |
| **Initial cost** | $600-2000 upfront |

### Cost Breakdown

| Model | Price | RAM | Storage | Best For |
|-------|-------|-----|---------|----------|
| Mac Mini M4 (base) | $599 | 16GB | 256GB | Light use |
| Mac Mini M4 (upgraded) | $799 | 16GB | 512GB | Recommended |
| Mac Mini M4 Pro | $1,399 | 24GB | 512GB | Heavy AI/ML |
| Mac Mini M4 Pro (max) | $1,999 | 48GB | 1TB | Overkill |

**Recommendation:** M4 with 16GB/512GB ($799) is plenty for Clawdbot.

### Annual Cost Comparison

| Option | Year 1 | Year 2 | Year 3 | 3-Year Total |
|--------|--------|--------|--------|--------------|
| Mac Mini M4 ($799) | $799 | $0* | $0* | $799 |
| EC2 ($25/mo) | $300 | $300 | $300 | $900 |

*Electricity: ~$20-30/year for Mac Mini running 24/7 (15-20W average)

**Mac Mini breaks even in ~32 months** vs EC2.

---

## Option B: Keep EC2 (Hardened)

### What You'd Need to Do

1. **VPN-only access** (Tailscale or WireGuard)
   - No public SSH
   - No public endpoints
   - All access through VPN

2. **Secrets management**
   - Use AWS Secrets Manager ($0.40/secret/month)
   - Or HashiCorp Vault (free, self-hosted)
   - Secrets loaded at runtime, not in .env files

3. **Network isolation**
   - VPC with private subnet
   - No public IP
   - Access via bastion or VPN only

4. **Monitoring**
   - CloudWatch alerts for unusual activity
   - Fail2ban for SSH (if exposed)
   - Log all API key usage

**Cost of hardening:** +$5-20/month for secrets manager, VPN, monitoring

---

## Security Comparison

| Threat | Mac Mini (Home) | EC2 (Current) | EC2 (Hardened) |
|--------|-----------------|---------------|----------------|
| Random internet scans | ✅ Not exposed | ❌ Exposed | ✅ VPN only |
| SSH brute force | ✅ Not exposed | ⚠️ Mitigated | ✅ VPN only |
| API endpoint exploits | ✅ LAN only | ❌ Exposed | ✅ VPN only |
| AWS account compromise | ✅ N/A | ❌ Risk | ❌ Risk |
| Physical theft | ⚠️ Possible | ✅ N/A | ✅ N/A |
| Power/internet outage | ❌ Affected | ✅ AWS uptime | ✅ AWS uptime |
| AI prompt injection | ⚠️ Same | ⚠️ Same | ⚠️ Same |
| Credential leakage | ✅ Local only | ❌ Cloud storage | ⚠️ Better |

### Honest Assessment

**For your use case (personal AI assistant with sensitive API keys):**

**Mac Mini is actually more secure** for most realistic threat models:
- Your biggest risk is internet exposure, which Mac Mini eliminates
- Physical theft is lower probability than remote compromise
- You're not a high-value target for sophisticated attackers
- Local = smaller attack surface

**EC2 is better if:**
- You need 99.9% uptime
- You access from many locations/devices
- You want to avoid hardware maintenance
- You're scaling to multiple users

---

## My Recommendation

### If Security is Top Priority: **Mac Mini**

**Setup:**
1. Buy Mac Mini M4 ($799, 16GB/512GB)
2. Set up at home, connected to your router
3. Enable FileVault (full disk encryption)
4. Install Tailscale for remote access (free, encrypted)
5. Run Clawdbot locally
6. API keys stay on your local machine

**Access pattern:**
- Home network: Direct access
- Mobile/remote: Through Tailscale VPN
- Same functionality, much smaller attack surface

### If Convenience is Top Priority: **Hardened EC2**

**Setup:**
1. Remove public IP
2. Set up Tailscale on EC2
3. Access everything through Tailscale
4. Move secrets to AWS Secrets Manager
5. Enable CloudWatch monitoring

**This gives you EC2 reliability + reduced exposure.**

---

## Hybrid Approach (Best of Both?)

You could also:

1. **Mac Mini at home** = Primary, has all API keys
2. **EC2 as relay/backup** = No keys, just proxies to Mac Mini via Tailscale

This way:
- API keys never leave your home network
- EC2 handles incoming webhooks (Telegram, etc.)
- EC2 forwards to Mac Mini over encrypted tunnel
- If EC2 is compromised, attacker gets nothing valuable

**Complexity:** Medium. Requires Tailscale setup and some routing config.

---

## Decision Framework

| If you... | Then... |
|-----------|---------|
| Value security over convenience | Mac Mini |
| Want lowest ongoing cost | Mac Mini |
| Need 99.9% uptime | EC2 (hardened) |
| Want zero hardware maintenance | EC2 |
| Travel frequently and need access | Either (with Tailscale) |
| Want to eliminate cloud risk entirely | Mac Mini |
| Run multiple AI agents at scale | EC2 |

---

## The "Evolving AI Threats" Factor

William mentioned concern about evolving AI threats. This is valid:

**New threat vectors in AI:**
- Prompt injection to leak credentials
- Model manipulation to exfiltrate data
- AI agents being tricked into running malicious commands

**These threats exist regardless of hosting.** But:
- Local hosting (Mac Mini) means leaked data stays on your network
- Cloud hosting means leaked data could be exfiltrated to the internet more easily
- Both require careful prompt engineering and sandboxing

**Bottom line:** Mac Mini reduces the blast radius. If something goes wrong, the data is at least not already on the internet.

---

## Final Verdict

**For William's specific situation:**

| Factor | Weight | Mac Mini | EC2 |
|--------|--------|----------|-----|
| Security (API keys) | High | ✅ | ⚠️ |
| Cost (3-year) | Medium | ✅ | ❌ |
| Uptime | Medium | ⚠️ | ✅ |
| Convenience | Medium | ⚠️ | ✅ |
| Peace of mind | High | ✅ | ❌ |

**Recommendation: Buy the Mac Mini.**

For ~$800, you get:
- Better security posture
- Lower long-term cost
- API keys stay home
- Less anxiety about cloud exposure

The trade-off (slightly more maintenance, potential downtime during power outages) is worth it for the security and cost benefits.

**Keep EC2 running temporarily** during transition, then decommission it.

---

## Quick Action Plan (If You Decide Mac Mini)

1. **Order:** Mac Mini M4, 16GB RAM, 512GB ($799)
2. **While waiting:**
   - Set up Tailscale account
   - Document current EC2 configuration
   - Export all credentials securely
3. **When it arrives:**
   - Set up macOS, enable FileVault
   - Install Tailscale
   - Install Clawdbot/dependencies
   - Transfer credentials locally
   - Test everything
4. **Cutover:**
   - Point Telegram webhook to new location (via Tailscale)
   - Monitor for 1 week
   - Decommission EC2

---

*Analysis complete. Mac Mini wins for your use case.*
