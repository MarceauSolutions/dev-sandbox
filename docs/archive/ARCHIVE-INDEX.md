# Archive Index

*Last Updated: 2026-02-10*

This directory contains documentation that has been archived from active use. Files are preserved for historical reference.

## How to Navigate

- **Looking for old SOPs?** → `original-sops/` directory has each SOP as a separate readable file
- **Looking for the full original CLAUDE.md?** → `CLAUDE-v1-monolithic.md` (4,402 lines, complete)
- **Looking for the original MEMORY.md?** → `MEMORY-v1-endpoints.md` (all n8n endpoint docs)

## Archived Files

### Core System Backups

| File | Archived | Reason | Superseded By |
|------|----------|--------|---------------|
| `CLAUDE-v1-monolithic.md` | 2026-02-09 | Restructured to modular system | Root `CLAUDE.md` (~138 lines) + `docs/sops/` |
| `MEMORY-v1-endpoints.md` | 2026-02-09 | Replaced with actionable learnings | `.claude/projects/*/memory/MEMORY.md` |

### Original SOPs (Pre-Restructuring)

| Directory | Contents | Notes |
|-----------|----------|-------|
| `original-sops/` | All 28+ SOPs extracted as individual files | Exact text from monolithic CLAUDE.md |

### Strategy & Planning Documents

| File | Archived | Reason |
|------|----------|--------|
| `AUTONOMOUS-DEVELOPMENT-ARCHITECTURE.md` | 2026-02-09 | Concepts absorbed into SOPs 9, 10, 29 |
| `COMPANY-ON-COMPUTER-ROADMAP.md` | 2026-02-09 | Superseded by current project structure |
| `UNIFIED-ARCHITECTURE-SOLUTION.md` | 2026-02-09 | Superseded by `docs/architecture-guide.md` |
| `UNIFIED-TOOL-ORCHESTRATION.md` | 2026-02-09 | Superseded by n8n Agent Orchestrator |
| `HYBRID-ARCHITECTURE-SOLUTION.md` | 2026-02-09 | Superseded by `docs/HYBRID-ARCHITECTURE-QUICK-REF.md` |

### Session Files

| File | Date | Context |
|------|------|---------|
| `SESSION-PAUSE-2026-01-19.md` | 2026-01-19 | Session state snapshot |
| `SESSION-SUMMARY-2026-01-18.md` | 2026-01-18 | Session accomplishments |
| `SESSION-SUMMARY-JAN-19-2026.md` | 2026-01-19 | Session accomplishments |
| `session-files/PARALLEL-CAMPAIGNS-STRATEGY-JAN-19-2026.md` | 2026-01-19 | Campaign planning |
| `session-files/PARALLEL-POC-STRATEGY-JAN-19-2026.md` | 2026-01-19 | Proof of concept planning |
| `session-files/UPDATED-STRATEGY-JAN-19-2026.md` | 2026-01-19 | Strategy revision |
| `session-files/X-AUTOMATION-PLAN-JAN-19-2026.md` | 2026-01-19 | X/Twitter automation plan |

### Analysis Documents

| File | Context |
|------|---------|
| `analysis/ARCHITECTURE-CONFLICT-RESOLUTION.md` | Architecture decision analysis |
| `analysis/BILLING-ALERTS-SUMMARY.md` | Google Cloud billing setup |
| `analysis/COMPREHENSIVE-CONFLICT-AUDIT.md` | Codebase conflict audit |
| `analysis/EC2-VS-MAC-MINI-ANALYSIS.md` | Infrastructure comparison |
| `analysis/END-CUSTOMER-DEPLOYMENT-STRATEGY.md` | Deployment strategy research |
| `analysis/ENTERPRISE-SECURITY-FRAMEWORK.md` | Security framework design |
| `analysis/EXECUTION-FOLDER-AUDIT.md` | Execution scripts audit |
| `analysis/GOOGLE-CLOUD-ACTION-PLAN.md` | GCP setup plan |
| `analysis/GOOGLE-CLOUD-BILLING-ALERTS-SETUP.md` | GCP billing configuration |
| `analysis/GOOGLE-CLOUD-COST-ANALYSIS.md` | GCP cost analysis |
| `analysis/MARCEAU-SOLUTIONS-MARKETING-STRATEGY.md` | Marketing strategy |
| `analysis/MARCEAU-SOLUTIONS-SERVICE-POSITIONING-ANALYSIS.md` | Service positioning |
| `analysis/MCP-SECURITY-REMEDIATION-PLAN.md` | Security remediation |
| `analysis/STRIPE-PRODUCTS-ANALYSIS.md` | Stripe product configuration |

### Integration Guides (Completed Setup)

| File | Context |
|------|---------|
| `CREATOMATE_API_SETUP.md` | Creatomate video API setup (completed) |
| `CREATOMATE_VS_HYBRID_COMPARISON.md` | Video provider comparison (decided) |
| `GOOGLE-SHEETS-ORGANIZATION.md` | Sheets structure (implemented) |
| `GOOGLE_API_RECOMMENDATIONS.md` | Google API setup (completed) |
| `MULTI-BUSINESS-FORM-SYSTEM.md` | Form system design (implemented) |
| `MULTI-CAMPAIGN-MANAGEMENT-FUTURE.md` | Future campaign features |
| `NGROK-AI-GATEWAY-SETUP.md` | Ngrok gateway setup (completed) |

### Video/Content System

| File | Context |
|------|---------|
| `HYBRID_VIDEO_IMPLEMENTATION_SUMMARY.md` | Video system implementation summary |
| `HYBRID_VIDEO_SETUP_GUIDE.md` | Video system setup guide |
| `HYBRID_VIDEO_SYSTEM_READY.md` | Video system completion notice |
| `IMPLEMENTATION_STRATEGY_ANALYSIS.md` | Implementation approach analysis |
| `OPTIMIZATION_IMPLEMENTATION_SUMMARY.md` | Optimization results |
| `VIDEO_GENERATION_RESEARCH.md` | Video generation provider research |
| `WEBSITE_INTEGRATION.md` | Website integration plan |

### Stripe Documentation

| File | Context |
|------|---------|
| `STRIPE-PRODUCTS-MASTER-REFERENCE.md` | Stripe product catalog |
| `STRIPE-PRODUCTS-V2-BUNDLED-OFFERINGS.md` | Bundled product definitions |
| `STRIPE-TIER-DEFINITIONS.md` | Pricing tier structure |

### SOP Resolution

| File | Context |
|------|---------|
| `SOP-HYBRID-ARCHITECTURE-FIXES-APPLIED.md` | Architecture fixes applied |
| `SOP-HYBRID-ARCHITECTURE-REVIEW.md` | Architecture review results |
| `SOP-RESOLUTION-COMPLETE.md` | SOP resolution summary |

### Deprecated

| File | Context |
|------|---------|
| `deprecated/FOLDER-STRUCTURE-GUIDE-OLD.md` | Superseded by `docs/FOLDER-STRUCTURE-GUIDE.md` |

---

## Files NOT Archived (Still Active in `docs/`)

These files were evaluated during the 2026-02-09 restructuring and kept active:

- `STRIPE-UPDATE-GUIDE-JAN-19-2026.md` — Still referenced by 3 Marceau Solutions docs
- `COMPANY-LIFECYCLE-MANAGEMENT.md` — Still referenced by FOLDER-STRUCTURE-GUIDE and HYBRID-ARCHITECTURE docs
- `FITNESS_INFLUENCER_OPTIMIZATION_REPORT.md` — Still referenced by DEPLOYMENT-GUIDE and SETUP-GUIDE
- All SOPs 25-29 — Active standalone files in `docs/`
- `architecture-guide.md`, `testing-strategy.md`, etc. — Core operational docs

## When to Archive

Move files here when:
- Analysis is complete and no longer actively referenced
- File has been superseded by a newer version
- Session-specific work that served its purpose
- Documentation for deprecated features/systems

**Before archiving**: Grep for references to the file in active docs. If referenced, do NOT archive.
