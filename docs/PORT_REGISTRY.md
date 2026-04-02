# Port Registry — Marceau Solutions Infrastructure

**Purpose:** Prevent port conflicts by documenting all allocated ports.
**Rule:** Check this file before assigning ANY new port.

---

## Reserved Port Ranges

| Range | Purpose |
|-------|---------|
| 5000-5099 | Core services (pipeline, webhooks) |
| 5678 | n8n (fixed) |
| 8780-8799 | Application services |
| 18789-18799 | Clawdbot internal |

---

## Active Allocations

| Port | Service | Status | Owner |
|------|---------|--------|-------|
| 5002 | Webhook Server | Active | clawdbot |
| 5010 | Pipeline Python Bridge | Active | lead-gen |
| 5015 | Pipeline Alt | Active | lead-gen |
| 5020 | Mem0 Memory API | Dormant | shared |
| 5678 | n8n | Active | automation |
| 8780 | Unknown Python | Active | investigate |
| 8785 | Uvicorn Service | Active | investigate |
| 8786 | PA Service (Personal Assistant) | Active | clawdbot |
| 8788 | Unknown Python | Active | investigate |
| 8790 | **RESERVED: Grok Agent** | Pending | grok-native |
| 8791 | Python Service | Active | investigate |
| 8793 | Python Service | Active | investigate |
| 8795 | Python Service | Active | fitness |
| 8796 | Python Service | Active | unknown |
| 8797 | Python Service | Active | unknown |
| 8798 | Python Service | Active | unknown |
| 18789 | Clawdbot Gateway | Active | clawdbot |
| 18791 | Clawdbot Internal | Active | clawdbot |
| 18792 | Clawdbot Internal | Active | clawdbot |

---

## Dormant Services (disabled but configured)

| Port | Service | Systemd Unit | Notes |
|------|---------|--------------|-------|
| 8790 | ClaimBack | claimback.service | Medical billing - DISABLED |

---

## How to Add a New Service

1. **Check this file** for conflicts
2. **Pick an unused port** in the appropriate range
3. **Update this file** with your allocation
4. **Run the port check script** before starting: `/home/clawdbot/scripts/check-port.sh <port>`
5. **Commit the change** to this file

---

## Port Conflict Prevention Script

Location: `/home/clawdbot/scripts/check-port.sh`

Usage:
```bash
/home/clawdbot/scripts/check-port.sh 8790
# Returns: AVAILABLE or CONFLICT with process info
```

---

*Last updated: 2026-04-02*
*Maintainer: Clawdbot*
