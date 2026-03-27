# AI Systems Tower Directive

## Domain
Core AI infrastructure: orchestration, learning, personas, goals, knowledge bases, agent intelligence, monitoring, and self-healing.

## Core Capabilities
- **Cost Tracking**: Token usage per session, budget limits, pricing info
- **Conversation Memory**: Persistent chat history, summarization
- **Agent Templates & Personas**: Pre-configured agent behaviors
- **Multi-Agent Orchestration**: Parallel agent coordination
- **Knowledge Bases / RAG**: Semantic search, file indexing
- **Scheduled Tasks**: Cron-like task scheduling
- **Tool Plugins**: Python, HTTP, MCP plugin registration
- **Learning & Feedback**: Outcome analysis, recommendations
- **Workflow Recording**: Action sequence capture and playback
- **Context Injection**: Rule-based context provision
- **Inter-Agent Communication**: Agent messaging, state sharing
- **Goal Decomposition**: Complex task breakdown
- **Audit Trail**: Action logging
- **Adaptive Behavior**: Dynamic agent behavior adaptation
- **Self-Healing**: Autonomous error detection, rebuild monitoring
- **Security Scanning**: Vulnerability detection

## Entry Point
- Flask app: `src/app.py` (port 5013)
- 7 blueprint modules, 95 routes

## Integration Points
- **pipeline.db**: Reads deal data for AI monitoring dashboards
- **execution/**: Uses shared utilities (mem0_api, secrets_manager)
- **All towers**: Provides AI capabilities consumed by other towers

## Current Version
1.2.0
