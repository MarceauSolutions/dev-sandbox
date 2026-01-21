# Changelog

All notable changes to William's Personal AI Assistant will be documented in this file.

## [Unreleased] - 1.0.0-dev

### Added
- Initial project structure
- Aggregated skill file from all dev-sandbox projects
- Auto-deployment integration with deploy_to_skills.py
- Master SKILL.md as entry point for all capabilities

### Capabilities Aggregated
- **Interview Prep**: Research, presentations, mock interviews, quick outputs
- **Fitness Influencer**: Video editing, email management, analytics
- **Amazon Seller**: Inventory management, fee calculations
- **Naples Weather**: Weather reports, PDF generation

### Architecture
- Follows DOE (Directive-Orchestration-Execution) pattern
- No frontend required - interaction via Claude Code chat
- Skills auto-deploy from project development
