"""Upwork MCP Server - Job discovery and proposal assistance."""

import os
import json
import logging
from typing import Any, Optional
from datetime import datetime

from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import AnyUrl

from .client import (
    UpworkClient,
    UpworkCredentials,
    SEARCH_JOBS_QUERY,
    JOB_DETAILS_QUERY,
    MY_PROFILE_QUERY,
    MY_PROPOSALS_QUERY,
    MY_CONTRACTS_QUERY,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = Server("upwork-mcp")

# Initialize Upwork client (lazy loaded)
_upwork_client: Optional[UpworkClient] = None


def get_client() -> UpworkClient:
    """Get or create Upwork client."""
    global _upwork_client
    if _upwork_client is None:
        _upwork_client = UpworkClient()
    return _upwork_client


@mcp.list_tools()
async def list_tools() -> list[Tool]:
    """List available Upwork tools."""
    return [
        Tool(
            name="upwork_search_jobs",
            description="""Search for jobs on Upwork marketplace.

Filter by keywords, category, budget range, and client quality.
Returns job listings with title, budget, client info, and skills required.

Use this to discover relevant opportunities matching your skills.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keywords (e.g., 'amazon fba analytics python')"
                    },
                    "min_budget": {
                        "type": "number",
                        "description": "Minimum budget filter (USD)"
                    },
                    "max_budget": {
                        "type": "number",
                        "description": "Maximum budget filter (USD)"
                    },
                    "payment_verified": {
                        "type": "boolean",
                        "description": "Only show clients with verified payment",
                        "default": True
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results to return",
                        "default": 20
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="upwork_get_job_details",
            description="""Get detailed information about a specific job posting.

Returns full job description, client history, questions, attachments,
and competition level. Use this before writing a proposal.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "Upwork job ID"
                    }
                },
                "required": ["job_id"]
            }
        ),
        Tool(
            name="upwork_analyze_client",
            description="""Analyze a client's hiring history and reliability.

Returns hire rate, total spend, review history, and red flags.
Use this to evaluate if a client is worth pursuing.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "Job ID to analyze client from"
                    }
                },
                "required": ["job_id"]
            }
        ),
        Tool(
            name="upwork_draft_proposal",
            description="""Generate a customized proposal draft for a job.

Takes job details and your profile to create a tailored cover letter.
Includes relevant experience, answers to screening questions, and CTA.

NOTE: You must manually submit proposals - automated submission is not allowed.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "Job ID to write proposal for"
                    },
                    "highlight_skills": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Skills to emphasize in proposal"
                    },
                    "relevant_experience": {
                        "type": "string",
                        "description": "Relevant experience to mention"
                    },
                    "proposed_rate": {
                        "type": "number",
                        "description": "Your proposed hourly rate or fixed price"
                    }
                },
                "required": ["job_id"]
            }
        ),
        Tool(
            name="upwork_get_my_profile",
            description="""Get your Upwork freelancer profile information.

Returns your title, overview, skills, portfolio, and stats.
Useful for proposal customization.""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="upwork_get_my_proposals",
            description="""Get your submitted proposals and their status.

Returns proposals with status (pending, interviewing, archived),
job details, and submission date. Track your application pipeline.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["PENDING", "INTERVIEWING", "ARCHIVED", "ALL"],
                        "description": "Filter by proposal status",
                        "default": "ALL"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results",
                        "default": 20
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="upwork_get_my_contracts",
            description="""Get your active and past contracts.

Returns contracts with earnings, client info, and feedback.
Track your work history and earnings.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["ACTIVE", "ENDED", "ALL"],
                        "description": "Filter by contract status",
                        "default": "ACTIVE"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results",
                        "default": 20
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="upwork_auth_status",
            description="""Check Upwork API authentication status.

Returns whether you're authenticated and token expiration.
If not authenticated, provides authorization URL.""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="upwork_complete_auth",
            description="""Complete OAuth authorization flow.

After visiting the authorization URL and approving access,
provide the callback URL to complete authentication.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "callback_url": {
                        "type": "string",
                        "description": "The full callback URL after authorization"
                    }
                },
                "required": ["callback_url"]
            }
        ),
    ]


@mcp.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "upwork_search_jobs":
            return await search_jobs(arguments)
        elif name == "upwork_get_job_details":
            return await get_job_details(arguments)
        elif name == "upwork_analyze_client":
            return await analyze_client(arguments)
        elif name == "upwork_draft_proposal":
            return await draft_proposal(arguments)
        elif name == "upwork_get_my_profile":
            return await get_my_profile(arguments)
        elif name == "upwork_get_my_proposals":
            return await get_my_proposals(arguments)
        elif name == "upwork_get_my_contracts":
            return await get_my_contracts(arguments)
        elif name == "upwork_auth_status":
            return await auth_status(arguments)
        elif name == "upwork_complete_auth":
            return await complete_auth(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        logger.error(f"Error in {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def search_jobs(args: dict) -> list[TextContent]:
    """Search for jobs on Upwork."""
    client = get_client()

    query = args["query"]
    limit = args.get("limit", 20)
    min_budget = args.get("min_budget")
    max_budget = args.get("max_budget")
    payment_verified = args.get("payment_verified", True)

    try:
        result = client.graphql(
            SEARCH_JOBS_QUERY,
            {"query": query, "limit": limit, "offset": 0}
        )

        jobs = result.get("data", {}).get("marketplaceJobPostings", {}).get("edges", [])
        total = result.get("data", {}).get("marketplaceJobPostings", {}).get("totalCount", 0)

        # Filter results
        filtered_jobs = []
        for edge in jobs:
            job = edge.get("node", {})

            # Budget filter
            budget = job.get("budget", {}).get("amount") or 0
            hourly_max = job.get("hourlyBudget", {}).get("max") or 0
            effective_budget = budget or hourly_max * 40  # Assume 40 hours

            if min_budget and effective_budget < min_budget:
                continue
            if max_budget and effective_budget > max_budget:
                continue

            # Payment verified filter
            if payment_verified:
                client_info = job.get("client", {})
                if client_info.get("paymentVerificationStatus") != "VERIFIED":
                    continue

            filtered_jobs.append(job)

        # Format output
        output = f"# Upwork Job Search Results\n\n"
        output += f"**Query:** {query}\n"
        output += f"**Total Found:** {total} | **Showing:** {len(filtered_jobs)}\n\n"

        for i, job in enumerate(filtered_jobs, 1):
            client_info = job.get("client", {})
            skills = [s.get("name") for s in job.get("skills", [])]

            output += f"## {i}. {job.get('title', 'Untitled')}\n\n"
            output += f"**Job ID:** `{job.get('id')}`\n"

            # Budget
            if job.get("budget", {}).get("amount"):
                output += f"**Budget:** ${job['budget']['amount']} (Fixed)\n"
            elif job.get("hourlyBudget"):
                hourly = job["hourlyBudget"]
                output += f"**Hourly Rate:** ${hourly.get('min', '?')}-${hourly.get('max', '?')}/hr\n"

            output += f"**Duration:** {job.get('duration', 'Not specified')}\n"
            output += f"**Experience:** {job.get('experienceLevel', 'Not specified')}\n"
            output += f"**Posted:** {job.get('publishedDateTime', 'Unknown')}\n"

            # Client info
            output += f"\n**Client:**\n"
            output += f"- Jobs Posted: {client_info.get('totalPostedJobs', 0)}\n"
            output += f"- Hires: {client_info.get('totalHires', 0)}\n"
            total_spend = client_info.get("totalSpend", {}).get("amount", 0)
            output += f"- Total Spend: ${total_spend:,.0f}\n"
            output += f"- Payment Verified: {client_info.get('paymentVerificationStatus', 'Unknown')}\n"
            output += f"- Location: {client_info.get('location', {}).get('country', 'Unknown')}\n"

            # Skills
            if skills:
                output += f"\n**Skills:** {', '.join(skills[:10])}\n"

            # Description snippet
            desc = job.get("description", "")[:300]
            if desc:
                output += f"\n**Description:**\n{desc}...\n"

            output += "\n---\n\n"

        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(type="text", text=f"Search failed: {str(e)}")]


async def get_job_details(args: dict) -> list[TextContent]:
    """Get detailed job information."""
    client = get_client()
    job_id = args["job_id"]

    try:
        result = client.graphql(JOB_DETAILS_QUERY, {"jobId": job_id})
        job = result.get("data", {}).get("marketplaceJobPosting", {})

        if not job:
            return [TextContent(type="text", text=f"Job not found: {job_id}")]

        client_info = job.get("client", {})
        skills = [s.get("name") for s in job.get("skills", [])]
        questions = job.get("questions", [])

        output = f"# Job Details: {job.get('title')}\n\n"
        output += f"**Job ID:** `{job.get('id')}`\n"

        # Budget
        if job.get("budget", {}).get("amount"):
            output += f"**Budget:** ${job['budget']['amount']} (Fixed Price)\n"
        elif job.get("hourlyBudget"):
            hourly = job["hourlyBudget"]
            output += f"**Hourly Rate:** ${hourly.get('min', '?')}-${hourly.get('max', '?')}/hr\n"

        output += f"**Duration:** {job.get('duration', 'Not specified')}\n"
        output += f"**Experience Level:** {job.get('experienceLevel', 'Not specified')}\n"
        output += f"**Posted:** {job.get('publishedDateTime', 'Unknown')}\n"
        output += f"**Proposals:** {job.get('proposalsTier', 'Unknown')} range\n"
        output += f"**Invite Only:** {job.get('inviteOnly', False)}\n\n"

        # Full description
        output += f"## Description\n\n{job.get('description', 'No description')}\n\n"

        # Skills
        if skills:
            output += f"## Required Skills\n\n{', '.join(skills)}\n\n"

        # Screening questions
        if questions:
            output += f"## Screening Questions\n\n"
            for i, q in enumerate(questions, 1):
                output += f"{i}. {q.get('question', 'Unknown')}\n"
            output += "\n"

        # Client info
        output += f"## Client Information\n\n"
        output += f"- **Company:** {client_info.get('companyName', 'Not specified')}\n"
        output += f"- **Location:** {client_info.get('location', {}).get('country', 'Unknown')}\n"
        output += f"- **Jobs Posted:** {client_info.get('totalPostedJobs', 0)}\n"
        output += f"- **Hires:** {client_info.get('totalHires', 0)}\n"
        total_spend = client_info.get("totalSpend", {}).get("amount", 0)
        output += f"- **Total Spend:** ${total_spend:,.0f}\n"
        output += f"- **Payment Verified:** {client_info.get('paymentVerificationStatus', 'Unknown')}\n"

        if client_info.get("companyDescription"):
            output += f"\n**About Company:**\n{client_info['companyDescription'][:500]}\n"

        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(type="text", text=f"Failed to get job details: {str(e)}")]


async def analyze_client(args: dict) -> list[TextContent]:
    """Analyze client reliability and hiring patterns."""
    client = get_client()
    job_id = args["job_id"]

    try:
        result = client.graphql(JOB_DETAILS_QUERY, {"jobId": job_id})
        job = result.get("data", {}).get("marketplaceJobPosting", {})
        client_info = job.get("client", {})

        if not client_info:
            return [TextContent(type="text", text=f"Client info not found for job: {job_id}")]

        # Calculate metrics
        total_posted = client_info.get("totalPostedJobs", 0)
        total_hires = client_info.get("totalHires", 0)
        total_spend = client_info.get("totalSpend", {}).get("amount", 0)
        payment_verified = client_info.get("paymentVerificationStatus") == "VERIFIED"

        hire_rate = (total_hires / total_posted * 100) if total_posted > 0 else 0
        avg_spend = (total_spend / total_hires) if total_hires > 0 else 0

        # Risk assessment
        red_flags = []
        green_flags = []

        if not payment_verified:
            red_flags.append("Payment NOT verified")
        else:
            green_flags.append("Payment verified")

        if total_posted == 0:
            red_flags.append("No previous jobs posted (new client)")
        elif total_posted < 3:
            red_flags.append(f"Low job history ({total_posted} jobs)")
        else:
            green_flags.append(f"Established client ({total_posted} jobs)")

        if hire_rate < 30 and total_posted > 2:
            red_flags.append(f"Low hire rate ({hire_rate:.0f}%)")
        elif hire_rate > 60:
            green_flags.append(f"Good hire rate ({hire_rate:.0f}%)")

        if total_spend < 1000 and total_posted > 3:
            red_flags.append(f"Low total spend (${total_spend:,.0f})")
        elif total_spend > 10000:
            green_flags.append(f"High spender (${total_spend:,.0f})")

        # Overall rating
        if len(red_flags) > 2:
            rating = "⚠️ HIGH RISK"
        elif len(red_flags) > 0:
            rating = "⚡ MODERATE RISK"
        elif len(green_flags) > 2:
            rating = "✅ LOW RISK"
        else:
            rating = "📊 AVERAGE"

        output = f"# Client Analysis\n\n"
        output += f"**Overall Rating:** {rating}\n\n"

        output += f"## Metrics\n\n"
        output += f"| Metric | Value |\n"
        output += f"|--------|-------|\n"
        output += f"| Jobs Posted | {total_posted} |\n"
        output += f"| Freelancers Hired | {total_hires} |\n"
        output += f"| Hire Rate | {hire_rate:.0f}% |\n"
        output += f"| Total Spend | ${total_spend:,.0f} |\n"
        output += f"| Avg per Hire | ${avg_spend:,.0f} |\n"
        output += f"| Payment Verified | {'Yes' if payment_verified else 'No'} |\n"
        output += f"| Location | {client_info.get('location', {}).get('country', 'Unknown')} |\n\n"

        if green_flags:
            output += f"## ✅ Green Flags\n\n"
            for flag in green_flags:
                output += f"- {flag}\n"
            output += "\n"

        if red_flags:
            output += f"## ⚠️ Red Flags\n\n"
            for flag in red_flags:
                output += f"- {flag}\n"
            output += "\n"

        output += f"## Recommendation\n\n"
        if rating == "⚠️ HIGH RISK":
            output += "Consider passing on this job or requesting milestone payments."
        elif rating == "⚡ MODERATE RISK":
            output += "Proceed with caution. Ensure clear scope and milestones."
        else:
            output += "Client appears reliable. Standard proposal approach recommended."

        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(type="text", text=f"Analysis failed: {str(e)}")]


async def draft_proposal(args: dict) -> list[TextContent]:
    """Generate a proposal draft for a job."""
    client = get_client()
    job_id = args["job_id"]
    highlight_skills = args.get("highlight_skills", [])
    relevant_experience = args.get("relevant_experience", "")
    proposed_rate = args.get("proposed_rate")

    try:
        # Get job details
        result = client.graphql(JOB_DETAILS_QUERY, {"jobId": job_id})
        job = result.get("data", {}).get("marketplaceJobPosting", {})

        if not job:
            return [TextContent(type="text", text=f"Job not found: {job_id}")]

        title = job.get("title", "")
        description = job.get("description", "")
        skills = [s.get("name") for s in job.get("skills", [])]
        questions = job.get("questions", [])
        client_info = job.get("client", {})

        # Build proposal draft
        output = f"# Proposal Draft for: {title}\n\n"
        output += f"**Job ID:** `{job_id}`\n"
        output += f"**Client:** {client_info.get('companyName', 'Unknown')}\n\n"

        output += f"## Cover Letter\n\n"
        output += f"---\n\n"

        # Opening
        output += f"Hi,\n\n"

        # Hook - reference specific job need
        if description:
            # Extract first sentence or key phrase
            first_need = description.split('.')[0][:100]
            output += f"I noticed you're looking for help with {first_need.lower()}. "
            output += "This is exactly what I specialize in.\n\n"

        # Value proposition
        output += f"**For your project, I would:**\n\n"
        output += f"1. [Specific solution based on job requirements]\n"
        output += f"2. [Technical approach using: {', '.join(skills[:3]) if skills else 'relevant technologies'}]\n"
        output += f"3. [Deliverable they'll receive]\n\n"

        # Experience
        if relevant_experience:
            output += f"**Relevant Experience:**\n{relevant_experience}\n\n"
        else:
            output += f"**Relevant Experience:**\n"
            output += f"[Add your relevant experience here - specific results, similar projects]\n\n"

        # Qualifying questions
        output += f"**A few questions to scope accurately:**\n\n"
        output += f"- [Question about their current process/setup]\n"
        output += f"- [Question about timeline/urgency]\n"
        output += f"- [Question about success criteria]\n\n"

        # CTA
        output += f"Happy to share a demo or jump on a quick call to discuss.\n\n"
        output += f"Best,\n[Your Name]\n\n"
        output += f"---\n\n"

        # Screening questions
        if questions:
            output += f"## Screening Question Answers\n\n"
            for i, q in enumerate(questions, 1):
                output += f"**Q{i}: {q.get('question', '')}**\n\n"
                output += f"[Your answer here]\n\n"

        # Rate
        if proposed_rate:
            output += f"## Proposed Rate\n\n"
            output += f"${proposed_rate}"
            if job.get("hourlyBudget"):
                output += "/hr\n"
            else:
                output += " (fixed)\n"
        output += "\n"

        # Skills to highlight
        if highlight_skills:
            output += f"## Skills to Emphasize\n\n"
            output += ", ".join(highlight_skills) + "\n\n"

        output += f"---\n\n"
        output += f"⚠️ **IMPORTANT:** You must submit this proposal manually on Upwork. "
        output += f"Automated submission is not allowed.\n"

        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(type="text", text=f"Failed to draft proposal: {str(e)}")]


async def get_my_profile(args: dict) -> list[TextContent]:
    """Get user's freelancer profile."""
    client = get_client()

    try:
        result = client.graphql(MY_PROFILE_QUERY)
        me = result.get("data", {}).get("me", {})
        profile = me.get("freelancerProfile", {})

        output = f"# My Upwork Profile\n\n"
        output += f"**Name:** {me.get('name', 'Unknown')}\n"
        output += f"**Email:** {me.get('email', 'Unknown')}\n\n"

        output += f"## Professional Info\n\n"
        output += f"**Title:** {profile.get('title', 'Not set')}\n"
        hourly = profile.get("hourlyRate", {})
        output += f"**Hourly Rate:** ${hourly.get('amount', 0)} {hourly.get('currencyCode', 'USD')}\n\n"

        output += f"**Overview:**\n{profile.get('overview', 'Not set')}\n\n"

        skills = [s.get("name") for s in profile.get("skills", [])]
        if skills:
            output += f"**Skills:** {', '.join(skills)}\n\n"

        stats = profile.get("stats", {})
        output += f"## Stats\n\n"
        output += f"- Total Jobs: {stats.get('totalJobs', 0)}\n"
        output += f"- Total Hours: {stats.get('totalHours', 0)}\n"
        earnings = stats.get("totalEarnings", {}).get("amount", 0)
        output += f"- Total Earnings: ${earnings:,.0f}\n\n"

        portfolio = profile.get("portfolioItems", [])
        if portfolio:
            output += f"## Portfolio ({len(portfolio)} items)\n\n"
            for item in portfolio[:5]:
                output += f"- **{item.get('title', 'Untitled')}**\n"
                if item.get("description"):
                    output += f"  {item['description'][:100]}...\n"

        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(type="text", text=f"Failed to get profile: {str(e)}")]


async def get_my_proposals(args: dict) -> list[TextContent]:
    """Get user's proposals."""
    client = get_client()
    status = args.get("status", "ALL")
    limit = args.get("limit", 20)

    try:
        variables = {"limit": limit}
        if status != "ALL":
            variables["status"] = status

        result = client.graphql(MY_PROPOSALS_QUERY, variables)
        proposals = result.get("data", {}).get("proposals", {}).get("edges", [])
        total = result.get("data", {}).get("proposals", {}).get("totalCount", 0)

        output = f"# My Proposals\n\n"
        output += f"**Status Filter:** {status}\n"
        output += f"**Total:** {total}\n\n"

        for edge in proposals:
            prop = edge.get("node", {})
            job = prop.get("job", {})

            output += f"## {job.get('title', 'Unknown Job')}\n\n"
            output += f"- **Proposal ID:** `{prop.get('id')}`\n"
            output += f"- **Status:** {prop.get('status', 'Unknown')}\n"
            output += f"- **Submitted:** {prop.get('createdDateTime', 'Unknown')}\n"
            output += f"- **Client:** {job.get('client', {}).get('companyName', 'Unknown')}\n"

            charged = prop.get("chargedAmount", {}).get("amount")
            if charged:
                output += f"- **Connects Used:** {charged}\n"

            output += "\n---\n\n"

        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(type="text", text=f"Failed to get proposals: {str(e)}")]


async def get_my_contracts(args: dict) -> list[TextContent]:
    """Get user's contracts."""
    client = get_client()
    status = args.get("status", "ACTIVE")
    limit = args.get("limit", 20)

    try:
        variables = {"limit": limit}
        if status != "ALL":
            variables["status"] = status

        result = client.graphql(MY_CONTRACTS_QUERY, variables)
        contracts = result.get("data", {}).get("contracts", {}).get("edges", [])
        total = result.get("data", {}).get("contracts", {}).get("totalCount", 0)

        output = f"# My Contracts\n\n"
        output += f"**Status Filter:** {status}\n"
        output += f"**Total:** {total}\n\n"

        total_earnings = 0
        for edge in contracts:
            contract = edge.get("node", {})
            client_info = contract.get("client", {})
            feedback = contract.get("feedback", {})

            earnings = contract.get("totalEarnings", {}).get("amount", 0)
            total_earnings += earnings

            output += f"## {contract.get('title', 'Unknown Contract')}\n\n"
            output += f"- **Contract ID:** `{contract.get('id')}`\n"
            output += f"- **Status:** {contract.get('status', 'Unknown')}\n"
            output += f"- **Client:** {client_info.get('companyName', 'Unknown')}\n"
            output += f"- **Location:** {client_info.get('location', {}).get('country', 'Unknown')}\n"
            output += f"- **Started:** {contract.get('startDateTime', 'Unknown')}\n"

            if contract.get("endDateTime"):
                output += f"- **Ended:** {contract['endDateTime']}\n"

            output += f"- **Earnings:** ${earnings:,.2f}\n"

            if feedback:
                output += f"- **Feedback Score:** {feedback.get('score', 'N/A')}/5\n"
                if feedback.get("comment"):
                    output += f"- **Comment:** {feedback['comment'][:100]}...\n"

            output += "\n---\n\n"

        output += f"## Summary\n\n"
        output += f"**Total Earnings (shown):** ${total_earnings:,.2f}\n"

        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(type="text", text=f"Failed to get contracts: {str(e)}")]


async def auth_status(args: dict) -> list[TextContent]:
    """Check authentication status."""
    client = get_client()

    if client.is_authenticated():
        output = "# Upwork Authentication Status\n\n"
        output += "✅ **Status:** Authenticated\n\n"
        output += "You can use all Upwork MCP tools.\n"
    else:
        auth_url = client.get_authorization_url()
        output = "# Upwork Authentication Required\n\n"
        output += "❌ **Status:** Not authenticated\n\n"
        output += "## Steps to Authenticate\n\n"
        output += f"1. Visit this URL:\n\n```\n{auth_url}\n```\n\n"
        output += "2. Log in and authorize the application\n"
        output += "3. Copy the callback URL you're redirected to\n"
        output += "4. Use `upwork_complete_auth` with the callback URL\n"

    return [TextContent(type="text", text=output)]


async def complete_auth(args: dict) -> list[TextContent]:
    """Complete OAuth authorization."""
    client = get_client()
    callback_url = args["callback_url"]

    try:
        token = client.complete_authorization(callback_url)
        output = "# Upwork Authentication Complete\n\n"
        output += "✅ **Status:** Successfully authenticated!\n\n"
        output += "Token has been saved. You can now use all Upwork MCP tools.\n"
        return [TextContent(type="text", text=output)]
    except Exception as e:
        return [TextContent(type="text", text=f"Authentication failed: {str(e)}")]


def main():
    """Run the MCP server."""
    import asyncio
    from mcp.server.stdio import stdio_server

    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await mcp.run(
                read_stream,
                write_stream,
                mcp.create_initialization_options()
            )

    asyncio.run(run())


if __name__ == "__main__":
    main()
