# Changelog

All notable changes to the Interview Prep AI Assistant will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 1.4.0-dev

### Planned
- Additional mock interview question banks
- Interview performance analytics
- Integration with calendar for interview scheduling

## [1.3.0] - 2026-01-08

### Added
- **Mock Interview Practice** - Interactive behavioral, technical, and case interviews with STAR format coaching
- **PDF Outputs** - Cheat sheets, flashcards, talking points, and preparation checklists
- **Intent Router** - Unified conversational interface that routes requests to appropriate workflows
- Added to website Industries dropdown navigation
- Full deployment pipeline (skill + frontend)
- MCP server configuration with cost-benefit guidelines

### Changed
- Renamed from "Interview Prep PowerPoint" to "Interview Prep AI Assistant"
- Updated solution card with expanded capabilities
- Enhanced deployment checklist with security review section

### Deployment
- Production URL: https://interview-prep-pptx-production.up.railway.app/app
- Skill location: `.claude/skills/interview-prep/`

## [1.2.0] - 2026-01-08

### Added
- User guidance prompts at each workflow stage (USER_PROMPTS.md)
- Download to ~/Downloads functionality (download_pptx.py)
- Inference guidelines for intelligent scope extension
- Live editing session with auto-close previous presentation
- Enhanced experience slides script
- Template mode for continuing existing presentations

### Changed
- Theme color updated to #1A1A2E (dark navy)
- "Relevance:" label now Adobe red (#EC1C24)
- PowerPoint now closes before reopening updated version

### Fixed
- Slides 23-24 now included in theme consistency
- Multiple PowerPoint windows no longer accumulate during editing

## [1.0.0] - 2026-01-07

### Added
- Initial release
- AI-powered company and role research
- PowerPoint generation with professional themes
- Experience slides with AI-generated images
- Interactive slide editing
- Session management for iterative edits
- Template mode for continuing existing presentations
- Railway deployment with web frontend

### Features
- Research company, role, and match to resume
- Generate 20-24 slide professional presentation
- AI image generation for experience highlights (~$0.07/image)
- Edit text, images, and slide content
- Multiple themes: modern, professional, minimal
