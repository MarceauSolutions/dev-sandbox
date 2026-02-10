# SOP 30: n8n Workflow Management

**When**: Creating, managing, or transitioning automations to n8n

**Purpose**: Use n8n for visual workflow automation, webhooks, and scheduled tasks instead of Python scripts where appropriate.

**Agent**: Claude Code (all n8n MCP operations). Clawdbot (status checks only). Ralph (complex automation via PRD).

**Prerequisites**:
- ✅ EC2 n8n running at http://34.193.98.97:5678
- ✅ n8n MCP configured in `~/.claude.json`
- ✅ Python Bridge API running on EC2 (localhost:5010)

**CRITICAL: EC2 INSTANCE ONLY**

| Instance | URL | Usage |
|----------|-----|-------|
| **EC2 (PRODUCTION)** | http://34.193.98.97:5678 | ALL development, testing, production |
| Local | http://localhost:5678 | DEPRECATED - do not use |

- **Never start or use the local n8n instance**
- **All workflow creation/editing happens on EC2**
- **Claude Code MCP is configured to connect to EC2** (`~/.claude.json`)
- **Weekly backup (optional)**: Export workflows from EC2 to `projects/shared/n8n-workflows/`

**When to Use n8n vs Python**:

| Use n8n | Use Python |
|---------|------------|
| Webhook handlers | Complex ML/AI logic |
| Scheduled tasks with visual debugging | Statistical analysis |
| Multi-service integrations | Lead scoring algorithms |
| Follow-up sequences (Wait nodes) | Video/image generation |
| Form → CRM → Email pipelines | Custom API clients |

**Active n8n Workflows** (on EC2):

| Workflow | ID | Webhook Path |
|----------|-----|--------------|
| SMS-Response-Handler-v2 | G14Mb6lpeFZVYGwa | `/webhook/sms-response` |
| Form-Submission-Pipeline | MmXDtZMsY9nR5Wrx | `/webhook/form-submit` |
| Daily-Operations-Digest | Hz05R5SeJGb4VNCl | *Scheduled 8 AM* |
| Follow-Up-Sequence-Engine | w8PYKJyeozM3qJQW | `/webhook/enroll-followup` |
| Hot-Lead-to-ClickUp | SzVXrbi1y433799Y | `/webhook/hot-lead-clickup` |
| Grok-Imagine-B-Roll-Generator | sYvUyTooDcHQQuKN | *Manual trigger* |

**Commands**:
```bash
# Check EC2 n8n status
curl http://34.193.98.97:5678/healthz

# List workflows via MCP
# Use mcp__n8n__list_workflows_minimal tool

# Export workflow to local backup
# Use mcp__n8n__export_workflow_to_file tool
```

**Python Scripts Replaced by n8n**:
- `twilio_webhook.py` → SMS-Response-Handler-v2
- `form_webhook.py` → Form-Submission-Pipeline
- `morning_digest.py` → Daily-Operations-Digest
- `follow_up_sequence.py` → Follow-Up-Sequence-Engine

**Communication Patterns**:
- "Check n8n status" → `curl http://34.193.98.97:5678/healthz`
- "Create n8n workflow for X" → Use n8n MCP tools (connects to EC2)
- "Migrate X to n8n" → Follow transition plan in `docs/N8N-TRANSITION-PLAN.md`
- "Backup n8n workflows" → Export to `projects/shared/n8n-workflows/`

**Success Criteria**:
- [ ] Workflow created/updated on EC2 n8n
- [ ] Workflow activated and responding to triggers
- [ ] Webhook URL documented in table above
- [ ] Backup exported to `projects/shared/n8n-workflows/`

**Troubleshooting**:

| Issue | Cause | Solution |
|-------|-------|----------|
| Can't connect to n8n | EC2 not running | SSH and check `docker ps` or PM2 status |
| MCP tool fails | n8n credential expired | Re-authenticate in n8n MCP settings |
| Webhook not firing | Workflow inactive | Activate workflow in n8n UI |
| Python Bridge error | Port 5010 not listening | SSH and restart `agent_bridge_api.py` |
| Workflow execution fails | Node error | Check n8n execution log, fix node config |

**References**: `docs/N8N-TRANSITION-PLAN.md`, `docs/EC2-N8N-SETUP.md`
