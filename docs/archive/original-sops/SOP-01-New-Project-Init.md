<!-- Original SOP as it appeared in CLAUDE.md (4,402 lines) before 2026-02-09 restructuring -->

### SOP 1: New Project Initialization

**When**: Starting a new AI assistant or automation project (AFTER completing SOP 0)

**Purpose**: Create standardized project structure with proper folder placement, version control, and documentation scaffolding.

**Agent**: Claude Code (primary). Clawdbot for complexity 0-6. Ralph for complexity 7-10 via PRD.

**Prerequisites**:
- ✅ SOP 0 complete (KICKOFF.md exists with Go decision)
- ✅ App type determined (MCP, CLI, Web, etc.)
- ✅ Company/shared placement decided

**Steps**:
1. **Determine location** using folder structure decision tree:
   - **Company-specific** → `projects/[company-name]/[project-name]/`
   - **Multi-tenant (2+ companies)** → `projects/shared/[project-name]/`
   - See: `docs/FOLDER-STRUCTURE-GUIDE.md` for decision tree

2. **Use automated scripts**:
   ```bash
   # For company-specific project
   ./scripts/add-company-project.sh company-name "project-name" [type]

   # For shared/multi-tenant project
   ./scripts/add-company-project.sh shared "project-name" [type]
   ```

   **Project subtypes** (3rd argument — see Build Taxonomy for definitions):
   - `project` (default) - Company Project or general-purpose codebase
   - `automation` - Scheduled/triggered process (n8n, cron, webhook handler)
   - `ops` - Business Ops (primarily workflows/documentation, minimal code)
   - `mcp` - MCP Server (for eventual PyPI/MCP Registry publishing via SOPs 11-14)

3. **Create directive (if needed)**: `directives/[project-name].md`
   - Define capabilities and SOPs
   - Document edge cases and error handling
   - Include tool usage patterns

4. **Create project structure**:
   - **DO NOT** run `git init` inside folder
   - Structure (same for company-specific or shared):
     ```
     projects/[location]/[project-name]/
     ├── src/              # Python scripts
     ├── workflows/        # Task procedures (markdown)
     ├── VERSION           # e.g., "1.0.0-dev"
     ├── CHANGELOG.md      # Version history
     ├── SKILL.md          # Skill definition (if deploying)
     └── README.md         # Project documentation
     ```

5. **Develop iteratively**:
   - Write code in `src/`
   - Use shared utilities from `execution/` (if needed)
   - Extract to `execution/` only when 3+ projects use same code
   - Document workflows as you complete tasks
   - Update directive with learnings

6. **Commit to dev-sandbox**:
   ```bash
   cd /Users/williammarceaujr./dev-sandbox
   git add projects/[location]/[project-name]/
   git commit -m "feat([company]): Initial [project-name] structure"
   git push origin main
   ```

7. **Deploy when ready**:
   ```bash
   python deploy_to_skills.py --project [project-name] --version 1.0.0
   ```

**Success Criteria**:
- [ ] Project folder created in correct location (company-specific or shared)
- [ ] Standard structure present: src/, workflows/, VERSION, CHANGELOG.md, README.md
- [ ] No nested git repository (`find . -name ".git"` shows only parent)
- [ ] Initial commit pushed to dev-sandbox
- [ ] Directive created (if project has SOPs)

**References**:
- `docs/FOLDER-STRUCTURE-GUIDE.md` - Where to put new code
- `docs/HYBRID-ARCHITECTURE-QUICK-REF.md` - Quick reference
- `scripts/add-company-project.sh` - Automated project creation
- `docs/deployment.md` - Deployment pipeline

