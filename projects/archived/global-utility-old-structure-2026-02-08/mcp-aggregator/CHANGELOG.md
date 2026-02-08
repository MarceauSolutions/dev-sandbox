# Changelog

All notable changes to the MCP Aggregator platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Phase 1: Core Platform (Months 1-2)
- MCP Registry system
- Intelligent routing engine
- Billing infrastructure
- Flagship rideshare comparison MCP
- Claude Desktop integration
- Break-even revenue target

## [1.1.0-dev] - 2026-01-13

### Added - Platform Generalization (Shortcoming Discovery & Fix)

**Problem Discovered**: Platform was developed in parallel with rideshare, baking in rideshare-specific assumptions that blocked non-rideshare services.

**Discovery Phase**:
- Systematic analysis of 5 core files found **51 rideshare-specific assumptions**
- Created `SHORTCOMING-DISCOVERY-REPORT.md` with complete findings

**Refactoring Completed** (4 parallel agents):

#### Agent 1: Platform Core Wiring
- **Created** `mcp-server/aggregator_mcp.py` - New MCP that uses platform core
- **Fixed** Platform core (router.py, registry.py, billing.py) was dead code - now actually used
- **Added** Configurable timeout per-MCP (supports hours for async services)

#### Agent 2: Connectivity Abstraction
- **Added** `ConnectivityType` enum with 6 types:
  - `HTTP` (default), `EMAIL`, `OAUTH`, `WEBHOOK`, `GRAPHQL`, `ASYNC`
- **Changed** `endpoint_url` now optional (not required for email-based services)
- **Added** `email_address` and `webhook_path` fields to MCP dataclass
- **Updated** Validation to be connectivity-type-specific

#### Agent 3: Flexible Billing
- **Added** `PricingModel` enum with 5 types:
  - `PER_REQUEST` (default), `SUBSCRIPTION`, `COMMISSION`, `TIERED`, `HYBRID`
- **Added** `TierConfig` dataclass for volume-based pricing
- **Added** Fee calculation methods: `calculate_commission_fees()`, `calculate_subscription_fees()`, `calculate_tiered_fees()`, `calculate_hybrid_fees()`
- **Added** `get_mcp_developer_share()` for per-MCP billing splits
- **Added** `subscriptions` and `pricing_tiers` tables to schema

#### Agent 4: Configurable Scoring
- **Added** `ScoringProfile` dataclass with configurable thresholds
- **Added** 6 scoring profiles: `rideshare`, `travel`, `food_delivery`, `async`, `e_commerce`, `default`
- **Changed** Latency/cost scoring now uses category-specific thresholds
- **Changed** Scoring weights configurable per-category (e.g., async: health 40%, latency 5%)

### Fixed
- Flight search (3s latency) now scores 100/100 instead of 30/100 (uses `travel` profile)
- HVAC services (24hr response) now scores fairly (uses `async` profile)
- Email-based services can now register (endpoint_url not required)
- Commission-based billing now supported (e.g., 10% of booking value)

### Files Modified
- `agent3-platform-core/workspace/router.py` - ScoringProfile, configurable timeout
- `agent3-platform-core/workspace/registry.py` - ConnectivityType enum, optional endpoint_url
- `agent3-platform-core/workspace/billing.py` - PricingModel enum, multiple fee calculations
- `agent3-platform-core/workspace/schema.sql` - New enums, tables, columns

### Files Created
- `mcp-server/aggregator_mcp.py` - New MCP server using platform core
- `SHORTCOMING-DISCOVERY-REPORT.md` - Complete analysis of 51 shortcomings

### Phase 2: Marketplace (Months 3-6)
- Developer portal
- 10+ service categories
- Multi-platform partnerships
- $50K/month revenue target

### Phase 3: Scale (Months 7-12)
- 500+ MCPs
- Series A funding
- $500K/month revenue target

## [1.0.0-dev] - 2026-01-12

### Added
- Initial project structure
- Directive document (Layer 1 of DOE architecture)
- Development roadmap
- Documentation framework

### Development Notes
- Following SOP 1 (New Project Initialization)
- Target: Break-even in Month 2
- Architecture: Tier 2 Aggregation Layer
- Business Model: 10-20% transaction fees + marketplace listings

---

## Version Strategy

**Major (X.0.0)**: Breaking changes, major platform updates
**Minor (x.Y.0)**: New features, new MCP categories, backwards compatible
**Patch (x.y.Z)**: Bug fixes, performance improvements

**Current**: 1.0.0-dev (pre-release development)
**Next**: 1.0.0 (production launch, Month 2)
