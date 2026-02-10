<!-- Original SOP as it appeared in CLAUDE.md (4,402 lines) before 2026-02-09 restructuring -->

### SOP 3: Version Control & Deployment (Skills)

**When**: Deploying a Skill to production for dev-sandbox Claude usage (AFTER testing complete)

**Agent**: Claude Code (primary, REQUIRED for PyPI/MCP). Clawdbot (git operations only). Ralph: N/A.

**This SOP is for Skills** (used by dev-sandbox Claude). For standalone AI Assistants (fresh Claude or sellable), see **SOP 31**.

| Deployment Type | Target | SOP | Used By |
|-----------------|--------|-----|---------|
| **Skills** | `~/production/[name]-prod/` | SOP 3 (this) | Dev-sandbox Claude |
| **AI Assistants** | `~/ai-assistants/[name]/` | SOP 31 | Fresh Claude / Buyers |
| **Both** | Both locations | SOP 3 + SOP 31 | Both |

**CRITICAL PREREQUISITES** (verify BEFORE deploying):
1. ✅ **Manual testing complete** - Scenario 1 from testing-strategy.md
2. ✅ **Multi-agent testing complete** (if applicable) - Scenario 2
3. ✅ **Pre-deployment verification passed** - Scenario 3 from testing-strategy.md
4. ✅ **All critical issues resolved**
5. ✅ **Documentation updated**

**Complete Testing Guide**: See `docs/testing-strategy.md`

**Steps**:
1. **Develop and test in dev-sandbox** (version X.Y.Z-dev in VERSION file)
   - Make changes
   - Test thoroughly (see testing-strategy.md)
   - Fix all critical issues
   - Update workflows

2. **Update version files**:
   - `VERSION`: Change from `X.Y.Z-dev` to `X.Y.Z`
   - `CHANGELOG.md`: Document all changes under `## [X.Y.Z] - YYYY-MM-DD`
   - Include: Added, Changed, Fixed, Deprecated sections

3. **Deploy with version**:
   ```bash
   python deploy_to_skills.py --project [name] --version X.Y.Z
   ```
   - Creates `~/production/[name]-prod/` with separate git repo
   - Copies necessary files
   - Commits and tags version

4. **Bump to next dev version**:
   - `VERSION`: Update to `X.Y+1.0-dev` (or `X+1.0.0-dev` for major)
   - Commit to dev-sandbox

5. **Verify deployment**:
   ```bash
   python deploy_to_skills.py --status [name]
   # Should show: dev-sandbox (X.Y+1.0-dev) vs prod (X.Y.Z)
   ```

**Version strategy**:
- **Major (X.0.0)**: Breaking changes, major features
- **Minor (x.Y.0)**: New features, backwards compatible
- **Patch (x.y.Z)**: Bug fixes only

**Success Criteria**:
- [ ] Production folder created at `~/production/[name]-prod/`
- [ ] VERSION file updated (no -dev suffix)
- [ ] CHANGELOG.md has entry for this version
- [ ] `deploy_to_skills.py --status` shows matching versions
- [ ] Dev-sandbox bumped to next -dev version
- [ ] Post-deployment verification passed (Scenario 4)

**References**: `docs/versioned-deployment.md`

