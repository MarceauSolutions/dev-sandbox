<!-- Original SOP as it appeared in CLAUDE.md (4,402 lines) before 2026-02-09 restructuring -->

### SOP 4: Repository Cleanup & Verification

**When**: Weekly maintenance, or when adding new projects

**Purpose**: Maintain clean repository structure with no nested git repos, ensuring all production code is properly organized.

**Agent**: Any agent (Claude Code for complex fixes, Clawdbot for checks, Ralph: N/A).

**Steps**:
1. **Check for nested repos**:
   ```bash
   cd /Users/williammarceaujr./dev-sandbox
   find . -name ".git" -type d
   # Expected: Only ./.git
   ```

2. **If nested repos found**:
   - Move to appropriate category: `mv dev-sandbox/[nested-repo] ~/[category]/[nested-repo]`
   - Categories: production/, websites/, active-projects/, legacy/, archived/
   - Verify: Re-run find command
   - Commit change: `git add -A && git commit -m "fix: Move nested repo to [category]"`

3. **Verify git status**:
   ```bash
   git status
   # Should show clean working tree or expected changes
   # Should NOT show submodule warnings
   ```

4. **Check deployment targets**:
   ```bash
   python deploy_to_skills.py --list
   # Verify all prod repos are outside dev-sandbox
   ```

**If issues persist**: See `docs/repository-management.md` Section: "Common Mistakes and Fixes"

**Success Criteria**:
- [ ] `find . -name ".git" -type d` shows only `./.git`
- [ ] `git status` shows no submodule warnings
- [ ] All production repos outside dev-sandbox verified

**References**: `docs/repository-management.md`, `docs/REPO-QUICK-REFERENCE.md`

