# Ralph ↔ Clawdbot Pipeline Optimization

**Goal:** 10%+ quality improvement in outputs through tighter coordination.

## Problems Identified

1. **No PRD validation** — Ralph can start with vague acceptance criteria, wasting iterations
2. **No context injection** — Ralph gets a generic prompt, missing project-specific architecture decisions
3. **No post-completion review** — Ralph's output goes straight to user notification without quality check
4. **One-way feedback** — Ralph's learnings (progress.txt patterns) don't improve future Clawdbot PRDs
5. **No mid-execution health checks** — Ralph loops without intermediate quality validation
6. **Loose handoff protocol** — No structured context transfer between agents

## Solutions Implemented

### 1. PRD Quality Gate (pre_flight.py)
- Validates all stories have specific, testable acceptance criteria
- Ensures architecture notes are included
- Checks for dependency ordering between stories
- Blocks Ralph start if PRD scores below quality threshold

### 2. Context-Enriched Prompt (prompt_builder.py)
- Dynamically builds Ralph's prompt with project-specific context
- Includes: tech stack, coding standards, existing patterns, file structure
- Appends learnings from previous Ralph runs

### 3. Post-Completion Review (post_review.py)
- After Ralph completes, Clawdbot reviews changed files
- Runs quality checks: syntax, consistency, test coverage
- Generates quality score before notifying user
- Blocks notification if quality < threshold

### 4. Feedback Loop (feedback_loop.py)
- Extracts patterns from Ralph's progress.txt
- Updates a shared knowledge base (ralph/knowledge_base.json)
- Future PRDs auto-include relevant patterns

### 5. Enhanced Webhook (webhook improvements)
- Mid-execution progress reporting
- Per-iteration health checks
- Estimated completion time
