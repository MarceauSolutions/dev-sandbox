# Changelog

All notable changes to the Upwork MCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-27

### Added

- Initial release of Upwork MCP Server
- **Job Discovery Tools**:
  - `upwork_search_jobs` - Search with filters (budget, payment verified, skills)
  - `upwork_get_job_details` - Full job info with screening questions
- **Client Analysis Tools**:
  - `upwork_analyze_client` - Red/green flag analysis with risk rating
- **Proposal Assistance**:
  - `upwork_draft_proposal` - Template generation with job-specific customization
- **Profile & Tracking**:
  - `upwork_get_my_profile` - Your freelancer profile info
  - `upwork_get_my_proposals` - Track submitted proposals
  - `upwork_get_my_contracts` - View active/past contracts
- **Authentication**:
  - `upwork_auth_status` - Check OAuth status
  - `upwork_complete_auth` - Complete OAuth flow

### Technical

- OAuth 2.0 authentication via `python-upwork-oauth2`
- GraphQL queries for job search and details
- Token persistence in `~/.upwork/token.json`
- MCP 1.0+ compatible server implementation
