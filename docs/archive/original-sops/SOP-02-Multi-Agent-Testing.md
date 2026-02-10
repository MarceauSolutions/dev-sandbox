<!-- Original SOP as it appeared in CLAUDE.md (4,402 lines) before 2026-02-09 restructuring -->

### SOP 2: Multi-Agent Testing

**When**: After manual testing complete AND implementing complex features with multiple edge cases

**Agent**: Claude Code (orchestrate agents). Ralph (generate test suites). Clawdbot: N/A.

**Complete Testing Guide**: See `docs/testing-strategy.md` for full pipeline

**This SOP is Scenario 2** in the testing pipeline:
```
Manual Testing → Multi-Agent Testing → Pre-Deployment → Deploy
(Scenario 1)     (Scenario 2 - YOU)    (Scenario 3)
```

**CRITICAL PREREQUISITES** (verify ALL before creating test plan):
1. ✅ **Manual testing complete** - Scenario 1 from testing-strategy.md passed
2. ✅ **Core implementation stable** - All main scripts working in `src/`
3. ✅ **Basic functionality verified** - Tool works for simple happy-path cases
4. ✅ **Environment dependencies resolved** - All libraries installed and accessible
5. ✅ **Workflows documented** - At least 1-2 workflows tested manually

**DO NOT start multi-agent testing if**:
- Manual testing (Scenario 1) hasn't been completed
- Implementation is incomplete
- Scripts haven't been manually tested first
- Environment issues exist (library paths, dependencies, etc.)
- You haven't tested it yourself first

**Steps**:
1. **Reference working example first**: `email-analyzer/testing/`
   - Use as template for directory structure
   - Copy AGENT-PROMPTS.txt format
   - Use **absolute paths** in prompts (not relative)
   - Include clear "HOW TO RUN" sections with exact commands

2. **Create test infrastructure**:
   - `[project]/testing/TEST-PLAN.md` - Define test scenarios (3-4 per agent)
   - `[project]/testing/AGENT-PROMPTS.txt` - Copy-paste ready prompts
   - `[project]/testing/agent1/` through `agent4/` - Empty workspace directories
   - `[project]/testing/consolidated-results/` - Results folder
   - `[project]/testing/START-HERE.md` - Quick launch guide

3. **Set up workspace structure**:
   ```
   projects/[project]/testing/
   ├── TEST-PLAN.md
   ├── AGENT-PROMPTS.txt
   ├── START-HERE.md
   ├── agent1/              ← Absolute paths in prompts
   ├── agent2/
   ├── agent3/
   ├── agent4/
   └── consolidated-results/
   ```

4. **Write agent prompts with**:
   - **Absolute paths**: `/Users/williammarceaujr./dev-sandbox/projects/[project]/testing/agent1/`
   - **Exact commands**: Full paths to wrapper scripts or executables
   - **Clear examples**: Show exact command with expected output
   - **Workspace isolation**: "CRITICAL: I will ONLY work in my workspace"

5. **Launch agents** (in parallel):
   - Open separate Claude instances
   - Paste agent-specific prompts
   - Let agents work independently

6. **Consolidate findings**:
   - Wait for all agents to complete
   - Create `[project]/testing/consolidated-results/CONSOLIDATED-FINDINGS.md`
   - Categorize: Critical, Important, Nice-to-Have
   - Prioritize fixes

7. **Implement fixes**:
   - Address critical issues first
   - Update workflows with solutions
   - Deploy new version
   - Update CHANGELOG

**Troubleshooting Template**: If agents fail, create `TESTING-ISSUES-RESOLVED.md`:
- Document root causes
- List all fixes applied
- Verify with test runs
- Reference: `md-to-pdf/testing/TESTING-ISSUES-RESOLVED.md`

**Successful Example**: `email-analyzer/testing/` - 4 agents found 6 critical + 6 important issues in 225 minutes

**Failed Example (lessons learned)**: `md-to-pdf/testing/TESTING-ISSUES-RESOLVED.md`
- Used relative paths → agents confused about workspace
- Missing library path wrapper → agents crashed on conversion
- Fixed with absolute paths + wrapper script

**References**: `email-analyzer/testing/TEST-PLAN.md`, `md-to-pdf/testing/TESTING-ISSUES-RESOLVED.md`

