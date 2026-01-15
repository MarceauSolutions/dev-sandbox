# Changelog

All notable changes to the Uber/Lyft Price Comparison MCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0-dev] - 2026-01-13

Initial separation from mcp-aggregator platform.

### Added
- Moved rideshare implementation to standalone project
- Project structure: src/, data/, testing/, workflows/, mcp-server/
- Rate card algorithm (comparison.py)
- Deep linking support (deep_links.py)
- Rate card database (rate_cards.py)
- Accuracy testing framework (testing/accuracy/)

### Architecture
- Connects to MCP Aggregator platform for routing and billing
- Standalone service that can run independently
- Data files stored in data/ directory

### In Progress
- Rate card data collection for Naples, FL region
- Accuracy validation against live Uber/Lyft prices

---

## Version History

| Version | Date | Summary |
|---------|------|---------|
| 1.0.0-dev | 2026-01-13 | Initial separation from mcp-aggregator |
