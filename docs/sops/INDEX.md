# SOP Index

> All Standard Operating Procedures extracted from CLAUDE.md into individual files for on-demand loading.

## Quick Reference

| SOP | Name | When to Use | File |
|-----|------|-------------|------|
| **0** | Project Kickoff & App Type Classification | BEFORE starting any new project | `sop-00-kickoff.md` |
| **1** | New Project Initialization | Starting a new AI assistant or automation project | `sop-01-init.md` |
| **2** | Multi-Agent Testing | After manual testing, complex features with edge cases | `sop-02-testing.md` |
| **3** | Version Control & Deployment (Skills) | Deploying a Skill to production | `sop-03-deployment.md` |
| **4** | Repository Cleanup & Verification | Weekly maintenance, or when adding new projects | `sop-04-repo-cleanup.md` |
| **5** | Session Documentation | End of significant session or major learnings | `sop-05-session-docs.md` |
| **6** | Workflow Creation | Completing a repeatable task for the first time | `sop-06-workflow-creation.md` |
| **7** | DOE Architecture Rollback | Premature deployment detected | `sop-07-doe-rollback.md` |
| **8** | Client Demo & Test Output Management | Testing for clients or preserving test outputs | `sop-08-client-demo.md` |
| **9** | Multi-Agent Architecture Exploration | New project with multiple possible approaches (BEFORE implementation) | `sop-09-architecture-exploration.md` |
| **10** | Multi-Agent Parallel Development | Large system with 3+ independent components | `sop-10-parallel-development.md` |
| **11** | MCP Package Structure | Converting a project to MCP format for distribution | `sop-11-mcp-package.md` |
| **12** | PyPI Publishing | Publishing an MCP package to PyPI | `sop-12-pypi-publishing.md` |
| **13** | MCP Registry Publishing | Publishing to Claude's MCP Registry (after PyPI) | `sop-13-mcp-registry.md` |
| **14** | MCP Update & Version Bump | Updating an already-published MCP | `sop-14-mcp-update.md` |
| **15** | Multi-Channel Deployment | Deploying to multiple distribution channels | `sop-15-multi-channel-deployment.md` |
| **16** | OpenRouter Registration | Registering MCP on OpenRouter and directories | `sop-16-openrouter.md` |
| **17** | Market Viability Analysis (Multi-Agent) | BEFORE investing development time in a new product idea | `sop-17-market-viability.md` |
| **18** | SMS Campaign Execution | Running SMS outreach campaigns via Twilio | `sop-18-sms-campaign.md` |
| **19** | Multi-Touch Follow-Up Sequence | Managing automated follow-up sequences | `sop-19-followup-sequence.md` |
| **20** | Internal Method Development | Creating internal operational frameworks | `sop-20-internal-methods.md` |
| **21** | SOP Creation Method (Meta-Method) | Recurring process needs documentation | `sop-21-sop-creation.md` |
| **22** | Campaign Analytics & Tracking | Tracking campaign performance and response rates | `sop-22-campaign-analytics.md` |
| **23** | Cold Outreach Strategy Development | Developing and testing outreach messaging | `sop-23-cold-outreach.md` |
| **24** | Daily/Weekly Digest System | Reviewing business operations or digest setup | `sop-24-digest-system.md` |
| **25** | Documentation Decision Framework | Documenting large efforts (>30 min) | `../SOP-25-DOCUMENTATION-DECISION-FRAMEWORK.md` |
| **26** | User Statement Validation Protocol | MANDATORY: Never contradict user statements | `sop-26-user-validation.md` |
| **27** | Clawdbot Usage | Quick tasks while mobile / away from computer | `../SOP-27-CLAWDBOT-USAGE.md` |
| **28** | Ralph Usage | Complex multi-story development tasks | `../SOP-28-RALPH-USAGE.md` |
| **29** | Three-Agent Collaboration | Deciding which agent to use | `../SOP-29-THREE-AGENT-COLLABORATION.md` |
| **30** | n8n Workflow Management | Creating, managing, or transitioning automations to n8n | `sop-30-n8n-workflow.md` |
| **31** | AI Assistant Deployment | Deploying standalone AI assistant for fresh Claude or sale | `sop-31-ai-assistant.md` |
| **32** | Project Routing & Classification | FIRST step for ANY new idea (before SOP 0 or SOP 17) | `sop-32-project-routing.md` |
| **33** | Pre-Flight Checklist | MANDATORY before EVERY task — inventory, service status, standards | `sop-33-preflight-checklist.md` |

## By Category

### Getting Started (New Projects)
- **SOP 32** - Project Routing & Classification (always first)
- **SOP 17** - Market Viability Analysis (if uncertain market)
- **SOP 0** - Project Kickoff & App Type Classification
- **SOP 1** - New Project Initialization
- **SOP 9** - Architecture Exploration (if multiple approaches)

### Development
- **SOP 10** - Multi-Agent Parallel Development
- **SOP 6** - Workflow Creation

### Testing
- **SOP 2** - Multi-Agent Testing

### Deployment
- **SOP 3** - Version Control & Deployment (Skills)
- **SOP 31** - AI Assistant Deployment (standalone/sellable)
- **SOP 15** - Multi-Channel Deployment

### MCP Publishing
- **SOP 11** - MCP Package Structure
- **SOP 12** - PyPI Publishing
- **SOP 13** - MCP Registry Publishing
- **SOP 14** - MCP Update & Version Bump
- **SOP 16** - OpenRouter Registration

### Campaigns & Outreach
- **SOP 18** - SMS Campaign Execution
- **SOP 19** - Multi-Touch Follow-Up Sequence
- **SOP 22** - Campaign Analytics & Tracking
- **SOP 23** - Cold Outreach Strategy Development

### Operations & Maintenance
- **SOP 4** - Repository Cleanup & Verification
- **SOP 5** - Session Documentation
- **SOP 7** - DOE Architecture Rollback
- **SOP 8** - Client Demo & Test Output Management
- **SOP 24** - Daily/Weekly Digest System

### Meta / Governance
- **SOP 20** - Internal Method Development
- **SOP 21** - SOP Creation Method (Meta-Method)
- **SOP 25** - Documentation Decision Framework
- **SOP 26** - User Statement Validation Protocol
- **Tool Selection Framework** - `docs/service-standards.md` (integrated, not a separate SOP)

### Agent Routing
- **SOP 27** - Clawdbot Usage
- **SOP 28** - Ralph Usage
- **SOP 29** - Three-Agent Collaboration
- **SOP 30** - n8n Workflow Management

## Development Pipeline Order

```
SOP 32 → SOP 17 (if needed) → SOP 0 → SOP 9 (if needed) → SOP 1 → Develop → SOP 2 → SOP 3/31 → SOPs 11-14 (if MCP)
```

## Notes

- SOPs 25, 27, 28, 29 are stored in `docs/` (not in `docs/sops/`) as they predate this extraction
- All SOPs in this directory were extracted from the original monolithic CLAUDE.md
- The original monolithic version is archived at `docs/archive/CLAUDE-v1-monolithic.md`
