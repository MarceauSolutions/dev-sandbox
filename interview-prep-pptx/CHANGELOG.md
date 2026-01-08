# Changelog

All notable changes to the Interview Prep PowerPoint Generator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 1.1.0-dev

### Added
- User guidance prompts at each workflow stage (USER_PROMPTS.md)
- Download to ~/Downloads functionality (download_pptx.py)
- Inference guidelines for intelligent scope extension (docs/inference-guidelines.md)
- Live editing session with auto-close previous presentation (live_editor.py)
- Enhanced experience slides script (enhance_experience_slides.py)
- Open PPTX helper that closes previous versions (open_pptx.py)

### Changed
- Theme color updated to #1A1A2E (dark navy) - matches slides 19-22
- "Relevance:" label now Adobe red (#EC1C24) instead of white
- apply_navy_theme.py updated with correct color code
- PowerPoint now closes before reopening updated version

### Fixed
- Slides 23-24 now included in theme consistency (inference guidelines)
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
