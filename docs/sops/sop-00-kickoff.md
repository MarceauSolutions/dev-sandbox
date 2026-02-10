# SOP 0: Project Kickoff & App Type Classification

**When**: BEFORE starting any new project (runs before SOP 1 and SOP 9)

**Purpose**: Ensure proper app type selection, cost analysis, and template decisions are made upfront.

**Agent**: Claude Code (primary, interactive). Clawdbot for complexity 0-4 projects only. Ralph: N/A.

**Steps**:
1. **Complete kickoff questionnaire**: Copy `templates/project-kickoff-questionnaire.md` to project folder
   - Answer all 19 questions
   - Part 1: Business/Purpose (Q1-5)
   - Part 2: Technical Requirements (Q6-10)
   - Part 3: App Type Decision (Q11-13)
   - Part 4: Resource Assessment (Q14-16)
   - Part 5: Template Decision (Q17-19)

2. **Determine MCP Aggregator alignment**:
   - Use `docs/app-type-decision-guide.md` decision tree
   - If YES → Select MCP connectivity type (HTTP, EMAIL, OAUTH, WEBHOOK, GRAPHQL, ASYNC)
   - If NO → Select standalone app type (CLI, Skill, Web API, Full-Stack, Desktop, Hybrid)

3. **Complete cost-benefit analysis**:
   - Use templates from `docs/cost-benefit-templates.md`
   - Calculate development cost
   - Calculate monthly operational cost
   - Project revenue/value
   - Determine break-even timeline

4. **Decide template vs clean slate**:
   - Low innovation → Use full template
   - Medium innovation → Adapt template
   - High innovation → Clean slate

5. **Document decision**:
   - Record in `KICKOFF.md` in project folder
   - Include rationale for app type choice
   - Include cost-benefit summary
   - Get approval before proceeding

**Decision Output**:
- App Type selected
- Connectivity type (if MCP)
- Template decision
- Go/No-Go decision
- Next step (SOP 1 or SOP 9)

**Success Criteria**:
- [ ] Kickoff questionnaire completed (19 questions answered)
- [ ] App type selected with rationale documented
- [ ] Cost-benefit analysis shows positive ROI or strategic value
- [ ] KICKOFF.md created in project folder
- [ ] Go/No-Go decision made and documented

**References**: `docs/app-type-decision-guide.md`, `docs/cost-benefit-templates.md`, `templates/project-kickoff-questionnaire.md`
