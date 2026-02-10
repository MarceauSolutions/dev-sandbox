<!-- Original SOP as it appeared in CLAUDE.md (4,402 lines) before 2026-02-09 restructuring -->

### SOP 5: Session Documentation

**When**: At end of each significant session or when major learnings occur

**Purpose**: Capture session learnings, patterns, and progress to enable continuity across sessions and self-annealing system improvement.

**Agent**: All agents document their own work. Claude Code updates CLAUDE.md. Clawdbot/Ralph update session-history.md.

**Intermittent Save Points**:

Save progress mid-session when:
- Completing a major milestone (e.g., all repos created, PR submitted)
- Before starting a risky operation (destructive commands, major refactors)
- At natural breakpoints in multi-step tasks
- Every 30-60 minutes of intensive work
- After discovering something that took effort to figure out

**Quick Save Actions:**
1. Update relevant checklist/tracking doc (mark items complete)
2. Commit changes to dev-sandbox if files were modified
3. Note critical learnings in session-history.md (brief bullet points)

**Full Save** (end of session): Follow Steps 1-4 below.

**Steps**:
1. **Update session-history.md**:
   ```markdown
   ## YYYY-MM-DD: [Session Title]

   **Context:** [What you were working on]

   **Accomplished:**
   - [Key achievement 1]
   - [Key achievement 2]

   **Key Learnings:**
   1. [Learning with explanation]
   2. [Pattern discovered]

   **New Communication Patterns:**
   - "[User phrase]" → [What Claude does]

   **Files Created/Updated:**
   - `path/to/file.ext` - [What changed]
   ```

2. **Update prompting-guide.md** (if new phrases discovered):
   - Add to appropriate category
   - Include context and expected action

3. **Update CLAUDE.md Communication Patterns** (if recurring pattern):
   - Add row to table
   - Keep concise (3-5 words in each column)

4. **Commit documentation**:
   ```bash
   git add docs/session-history.md docs/prompting-guide.md CLAUDE.md
   git commit -m "docs: Session learnings from YYYY-MM-DD"
   ```

**Success Criteria**:
- [ ] session-history.md updated with accomplishments and learnings
- [ ] New communication patterns added to CLAUDE.md (if discovered)
- [ ] Documentation committed to git
- [ ] Future sessions can continue without re-learning

**References**: `docs/session-history.md`, `docs/prompting-guide.md`

