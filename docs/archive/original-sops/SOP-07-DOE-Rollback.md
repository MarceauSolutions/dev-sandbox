<!-- Original SOP as it appeared in CLAUDE.md (4,402 lines) before 2026-02-09 restructuring -->

### SOP 7: DOE Architecture Rollback

**When**: Premature deployment detected (deployed before all DOE layers complete)

**Purpose**: Safely roll back deployments that violated DOE discipline (Directive → Orchestration → Execution order), preventing broken features from reaching users while capturing learnings.

**Agent**: Claude Code (primary for code rollback and git operations). Clawdbot can identify violations. Ralph: N/A.

**Prerequisites**:
- ✅ Premature deployment identified (feature deployed without directive)
- ✅ Git access to affected repository
- ✅ Understanding of which DOE layer is missing

**DOE Violation Patterns**:

| Violation | Example | Impact |
|-----------|---------|--------|
| **No Directive** | Scripts deployed without SOPs | Users don't know how to use feature |
| **No Orchestration** | Standalone scripts, no integration | Feature works in isolation only |
| **No Execution** | Frontend with no backend | Broken UI, failed API calls |
| **Skip Testing** | Deployed without Scenario 1-3 | Bugs reach production |

**Steps**:

1. **Identify the violation**:
   ```bash
   # Check what's deployed
   ls ~/production/[project]-prod/

   # Check if directive exists
   ls directives/[project].md

   # Check if tested
   grep -r "testing" projects/[project]/
   ```

2. **Assess rollback scope**:
   - **Minor**: Missing docs only → Add docs, no code rollback
   - **Moderate**: Missing tests → Add tests, keep code
   - **Major**: Missing execution → Roll back frontend/UI
   - **Critical**: Broken production → Immediate rollback + incident doc

3. **Execute rollback** (for Major/Critical):
   ```bash
   # Option A: Remove specific files
   cd ~/production/[project]-prod
   git rm [premature-file]
   git commit -m "rollback: Remove premature [feature] - missing [layer]"
   git push

   # Option B: Revert to last good version
   git revert HEAD
   git push
   ```

4. **Create placeholder** (if user-facing):
   - Replace removed feature with "Coming Soon" page
   - Add email capture form for notifications
   - Link to existing working features

5. **Document the violation**:
   ```bash
   # Create incident doc
   cat > docs/incidents/$(date +%Y-%m-%d)-[feature]-rollback.md << 'EOF'
   # Incident: [Feature] Premature Deployment

   **Date**: $(date +%Y-%m-%d)
   **Severity**: [Minor/Moderate/Major/Critical]
   **DOE Violation**: [Missing layer]

   ## What Happened
   [Description]

   ## Impact
   [User impact]

   ## Resolution
   [Rollback steps taken]

   ## Prevention
   [What we'll do differently]
   EOF
   ```

6. **Complete the missing layer**:
   - If missing Directive → Create `directives/[project].md`
   - If missing Orchestration → Integrate with Claude/n8n
   - If missing Execution → Build and test `src/` scripts
   - If missing Testing → Complete Scenarios 1-3

7. **Re-deploy properly** (after all layers complete):
   ```bash
   python deploy_to_skills.py --project [name] --version X.Y.Z
   ```

**Troubleshooting**:

| Issue | Cause | Solution |
|-------|-------|----------|
| Can't identify what's premature | Unclear deployment history | Check `git log`, CHANGELOG.md |
| Rollback breaks other features | Tight coupling | Isolate change, test dependencies |
| Users already using feature | Deployed too long ago | Gradual deprecation instead |

**Success Criteria**:
- [ ] Premature deployment removed from production
- [ ] Incident documented in `docs/incidents/`
- [ ] Missing DOE layer identified and planned
- [ ] No broken features visible to users
- [ ] Lesson added to session-history.md

**References**: `docs/architecture-guide.md`, `docs/testing-strategy.md`

