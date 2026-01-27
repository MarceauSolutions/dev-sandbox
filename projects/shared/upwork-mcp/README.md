# Upwork MCP Server

mcp-name: io.github.marceausolutions/upwork

A Model Context Protocol (MCP) server for Upwork job discovery, client analysis, and proposal assistance. Helps freelancers find relevant opportunities and craft winning proposals.

## Features

- **Job Search** - Search Upwork marketplace with keyword, budget, and client quality filters
- **Job Details** - Get full job descriptions, requirements, and screening questions
- **Client Analysis** - Analyze client reliability, hire rate, and spending history
- **Proposal Drafting** - Generate customized proposal drafts based on job requirements
- **Profile Management** - View your profile, stats, and portfolio
- **Proposal Tracking** - Track submitted proposals and their status
- **Contract History** - View active and past contracts with earnings

## Installation

```bash
pip install upwork-mcp
```

## Setup

### 1. Get Upwork API Credentials

1. Go to [Upwork Developer Portal](https://www.upwork.com/developer)
2. Create a new API application
3. Note your `client_id` and `client_secret`

### 2. Configure Environment Variables

```bash
export UPWORK_CLIENT_ID="your_client_id"
export UPWORK_CLIENT_SECRET="your_client_secret"
export UPWORK_REDIRECT_URI="https://localhost"  # or your callback URL
```

### 3. Add to Claude Desktop

Add to your Claude Desktop configuration (`~/.claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "upwork": {
      "command": "upwork-mcp",
      "env": {
        "UPWORK_CLIENT_ID": "your_client_id",
        "UPWORK_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

### 4. Authenticate

On first use, run the `upwork_auth_status` tool to get the authorization URL. Visit the URL, authorize the app, and use `upwork_complete_auth` with the callback URL.

## Available Tools

### Job Discovery

#### `upwork_search_jobs`
Search for jobs matching your skills and preferences.

```
Input:
- query: Search keywords (required)
- min_budget: Minimum budget filter
- max_budget: Maximum budget filter
- payment_verified: Only verified clients (default: true)
- limit: Max results (default: 20)

Output: Job listings with title, budget, client info, skills
```

#### `upwork_get_job_details`
Get full details about a specific job.

```
Input:
- job_id: Upwork job ID (required)

Output: Full description, questions, attachments, client details
```

### Client Intelligence

#### `upwork_analyze_client`
Analyze a client's reliability and hiring patterns.

```
Input:
- job_id: Job ID to analyze client from (required)

Output: Hire rate, spend history, red flags, recommendation
```

### Proposal Assistance

#### `upwork_draft_proposal`
Generate a customized proposal draft.

```
Input:
- job_id: Job ID to write proposal for (required)
- highlight_skills: Skills to emphasize
- relevant_experience: Experience to mention
- proposed_rate: Your rate

Output: Cover letter template, question answers, rate
```

**Note:** Proposals must be submitted manually. Automated submission is not allowed by Upwork.

### Profile & Tracking

#### `upwork_get_my_profile`
View your freelancer profile and stats.

#### `upwork_get_my_proposals`
Track your submitted proposals.

```
Input:
- status: PENDING, INTERVIEWING, ARCHIVED, or ALL
- limit: Max results
```

#### `upwork_get_my_contracts`
View your contracts and earnings.

```
Input:
- status: ACTIVE, ENDED, or ALL
- limit: Max results
```

### Authentication

#### `upwork_auth_status`
Check authentication status and get auth URL if needed.

#### `upwork_complete_auth`
Complete OAuth flow with callback URL.

## Example Usage

### Finding Jobs

```
User: Search for Amazon FBA analytics jobs with budget over $500

Claude: [Uses upwork_search_jobs with query="amazon fba analytics" min_budget=500]
```

### Evaluating Opportunities

```
User: Analyze the client for job 123456

Claude: [Uses upwork_analyze_client]

Result shows:
- Client has posted 45 jobs, hired 38 (84% hire rate)
- Total spend: $125,000
- Payment verified
- Rating: LOW RISK ✅
```

### Drafting Proposals

```
User: Draft a proposal for job 123456, emphasizing my Python and SP-API experience

Claude: [Uses upwork_draft_proposal with highlight_skills and experience]
```

## Rate Limits

- Upwork API: 300 requests/minute per IP
- GraphQL queries are batched where possible

## Privacy & Security

- OAuth tokens are stored locally at `~/.upwork/token.json`
- No data is sent to third parties
- API requests go directly to Upwork

## License

MIT License - see [LICENSE](LICENSE)

## Support

- Issues: [GitHub Issues](https://github.com/MarceauSolutions/upwork-mcp/issues)
- Upwork API Docs: [developer.upwork.com](https://www.upwork.com/developer)
