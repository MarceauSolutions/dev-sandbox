# Changelog

All notable changes to Time Blocks will be documented in this file.

## [1.0.0-dev] - 2026-01-14

### Added
- Initial implementation of Time Blocks
- Core time block data model with start, end, activity, category, priority, notes
- Categories: work, exercise, personal, rest, admin, meal, learning, social
- Priority levels: low, medium, high, critical
- Local storage in `~/.time-blocks/blocks.json`
- Template system for reusable schedules
- Built-in templates: productive_day, weekend
- Visual schedule display with colors and symbols
- Timeline view for day overview
- Google Calendar integration
  - OAuth authentication
  - Event creation with category colors
  - Duplicate detection to avoid re-creating events
  - Support for recurring events
- CLI interface with commands:
  - `add` - Create time blocks
  - `remove` - Remove blocks by index
  - `clear` - Clear all blocks for a day
  - `view` - Display schedule (list or timeline)
  - `apply-template` - Apply saved template
  - `save-template` - Save schedule as template
  - `templates` - List available templates
  - `sync` - Sync to Google Calendar
  - `calendars` - List Google calendars
  - `auth` - Google authentication
- Workflow documentation: create-schedule.md
- Personal assistant skill definition (SKILL.md)
