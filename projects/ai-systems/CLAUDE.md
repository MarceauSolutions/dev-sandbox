# CLAUDE.md - Modular Multi-Tower Architecture

**Version**: 1.0.0
**Architecture**: Modular Multi-Tower
**Last Updated**: 2026-03-26

## Architecture Overview

This system uses a **modular multi-tower architecture** where specialized towers handle different domains:

### Tower Structure

```
projects/
├── ai-systems/           # Core AI orchestration & automation
├── amazon-seller/        # Amazon marketplace operations
├── fitness-influencer/   # Fitness content creation & management
├── lead-generation/      # Prospect discovery & enrichment
├── mcp-services/         # Model Context Protocol servers
└── personal-assistant/   # Personal productivity & scheduling
```

### Tower Responsibilities

| Tower | Domain | Key Functions |
|-------|--------|----------------|
| **ai-systems** | AI Orchestration | Claude integration, multi-agent coordination, automation workflows |
| **amazon-seller** | E-commerce | Inventory management, pricing optimization, seller operations |
| **fitness-influencer** | Content Creation | Video editing, social media automation, fitness content pipeline |
| **lead-generation** | Prospecting | Apollo.io integration, lead enrichment, cold outreach campaigns |
| **mcp-services** | AI Tools | MCP server development, tool distribution, registry publishing |
| **personal-assistant** | Productivity | Email management, calendar automation, daily digests |

## Operating Principles

### 1. Tower Autonomy
- Each tower operates independently within its domain
- Towers can call other towers via APIs or shared utilities
- No tight coupling between towers

### 2. Shared Utilities
- Common functionality lives in `execution/` (gmail, twilio, etc.)
- Towers import from shared utilities, not duplicate code
- Changes to shared utilities affect all dependent towers

### 3. Interface-First Design
- Towers expose clean APIs for inter-tower communication
- Documentation-first approach for all tower interfaces
- Versioned APIs with backward compatibility

### 4. Self-Contained Towers
- Each tower has its own `src/`, `workflows/`, `VERSION`, `CHANGELOG.md`
- Towers can be developed, tested, and deployed independently
- Tower-specific CLAUDE.md files for domain-specific guidance

## Development Workflow

### 1. Tower Selection
Choose the appropriate tower based on the task domain:
- AI automation → ai-systems
- Amazon selling → amazon-seller
- Fitness content → fitness-influencer
- Lead generation → lead-generation
- MCP development → mcp-services
- Personal tools → personal-assistant

### 2. Tower Development
```bash
# Work within the appropriate tower
cd projects/[tower-name]/

# Develop using tower-specific patterns
# Each tower has its own CLAUDE.md with domain guidance
```

### 3. Cross-Tower Integration
When towers need to work together:
- Use shared utilities from `execution/`
- Call tower APIs via HTTP or direct imports
- Document inter-tower dependencies

### 4. Deployment
- Towers deploy independently to separate repos
- Shared utilities deploy once, update all towers
- Version compatibility maintained across towers

## Tower Communication Patterns

| Pattern | Example | Implementation |
|---------|---------|----------------|
| **Tower API Call** | "Use lead-generation tower to enrich contacts" | HTTP API or direct import |
| **Shared Utility** | "Use gmail utility for email sending" | Import from `execution/` |
| **Tower Coordination** | "ai-systems orchestrates fitness-influencer content" | Workflow calls between towers |
| **Data Sharing** | "lead-generation shares enriched data with amazon-seller" | Shared database or file exchange |

## Tower-Specific Guidance

Each tower has its own CLAUDE.md with domain-specific:
- Development patterns
- Key workflows
- Integration points
- Success metrics

### Quick Tower Reference

| Tower | Entry Point | Key Workflows |
|-------|-------------|----------------|
| ai-systems | `src/orchestrator.py` | Multi-agent coordination, automation pipelines |
| amazon-seller | `src/inventory_manager.py` | Product listing, pricing optimization |
| fitness-influencer | `src/content_pipeline.py` | Video processing, social posting |
| lead-generation | `src/apollo_bridge.py` | Lead discovery, enrichment workflows |
| mcp-services | `src/server.py` | MCP tool development, registry publishing |
| personal-assistant | `src/digest_aggregator.py` | Email processing, calendar management |

## Quality Standards

### Code Quality
- All towers follow PEP 8
- Type hints required for public APIs
- Comprehensive error handling
- Unit tests for core functionality

### Documentation
- Each tower has README.md and CLAUDE.md
- API documentation for inter-tower interfaces
- Workflow documentation in `workflows/`
- Change logs in CHANGELOG.md

### Testing
- Manual testing before commits
- Multi-agent testing for complex features
- Integration testing for cross-tower functionality

## Maintenance

### Weekly Tasks
- Review tower health and dependencies
- Update shared utilities if needed
- Check for cross-tower integration issues

### Monthly Tasks
- Audit tower performance metrics
- Review and update tower documentation
- Plan tower enhancements and new features

## Emergency Procedures

### Tower Failure
1. Isolate the failing tower
2. Check shared utility dependencies
3. Roll back to last working version
4. Document root cause and fix

### Cross-Tower Issues
1. Identify which towers are affected
2. Check shared utilities and APIs
3. Coordinate fixes across tower maintainers
4. Test integration after fixes

## Future Evolution

### Tower Expansion
- New towers can be added for new domains
- Existing towers can be split if they grow too large
- Tower APIs remain stable during evolution

### Architecture Improvements
- Enhanced inter-tower communication protocols
- Improved shared utility management
- Better monitoring and observability

---

**Principle**: Modular towers enable focused expertise while maintaining system coherence.