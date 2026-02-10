<!-- Original SOP as it appeared in CLAUDE.md (4,402 lines) before 2026-02-09 restructuring -->

### SOP 6: Workflow Creation

**When**: Completing a repeatable task for the first time

**Purpose**: Document repeatable processes as workflows to prevent re-learning and enable consistent execution across sessions and agents.

**Agent**: Any agent. Claude Code for complex workflows. Clawdbot for simple 3-5 step workflows. Ralph: N/A.

**Decision Matrix** - Score each factor 0-3:

| Factor | 0 | 1 | 2 | 3 |
|--------|---|---|---|---|
| **Recurrence** | One-time | Unlikely | Probable | Frequent |
| **Consistency** | Doesn't matter | Nice to have | Important | Critical |
| **Complexity** | Trivial (<3 steps) | Simple | Moderate | Complex (10+ steps) |
| **Onboarding** | Only I'll do this | Might help others | Would help | Essential for handoff |

**Total Score:**
- **0-3**: Skip workflow, note in session-history.md if notable
- **4-6**: Consider workflow, or create after second occurrence
- **7-9**: Create workflow during this session
- **10-12**: Create workflow immediately

**Quick Test**: If you'd feel frustrated repeating the same research/trial-and-error next time, create the workflow now.

**Parallel Workflow Creation** (Optional for complex tasks):
Launch a second Claude instance to document steps as you work:
1. Main instance: Execute the task
2. Workflow instance: Document steps in real-time
3. Benefit: Captures edge cases and troubleshooting without interrupting work

**Steps**:
1. **While working**, note the steps you're taking

2. **After completion**, create workflow file:
   - Location: `[project]/workflows/[workflow-name].md`
   - Structure:
     ```markdown
     # Workflow: [Name]

     ## Overview
     [What this workflow does]

     ## Use Cases
     - [Use case 1]
     - [Use case 2]

     ## Prerequisites
     - [What must exist before starting]

     ## Steps

     ### 1. [Step Name]
     **Objective**: [What this step achieves]
     **Actions**: [What to do]
     **Tools**: [Which tools to use]

     ## Troubleshooting
     [Common issues and solutions]

     ## Success Criteria
     - ✅ [Criterion 1]
     - ✅ [Criterion 2]
     ```

3. **Test the workflow**:
   - Have another agent (or yourself fresh) follow it
   - Note any ambiguities
   - Refine steps

4. **Reference in directive**:
   - Add to `directives/[project].md`
   - Link to workflow for detailed steps

**Example**: `email-analyzer/workflows/analyze-email-from-html.md`

**Success Criteria**:
- [ ] Workflow file created in `[project]/workflows/`
- [ ] Contains: Overview, Use Cases, Prerequisites, Steps, Troubleshooting, Success Criteria
- [ ] Another agent can follow workflow without additional context
- [ ] Referenced in project directive (if applicable)

**References**: `docs/workflow-standard.md`

