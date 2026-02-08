# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-02-07

### Added
- Initial release of Ticket Discovery MCP
- Multi-platform search (Ticketmaster, SeatGeek)
- Price comparison across platforms
- Tools: `search_events`, `compare_prices`, `get_event_details`, `get_upcoming_events`, `find_cheap_tickets`, `check_api_status`
- Affiliate link support for monetization
- Market viability analysis documentation

### Technical
- Uses official public APIs only (legal, ToS-compliant)
- Async HTTP requests with httpx
- FastMCP server implementation
