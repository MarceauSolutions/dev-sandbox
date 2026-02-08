# Claude Development Framework - Quick Start Guide

> The systematized approach to AI-assisted development with Claude

## What This Is

This is a battle-tested operating system for working with Claude Code and Claude AI. Instead of trial-and-error prompting, you get documented procedures that work consistently.

## What's Included (Free Tier)

1. **Claude.md Template** - The foundation file that shapes how Claude works with your codebase
2. **3 Core SOPs**:
   - SOP 1: Project Initialization
   - SOP 3: Version Control & Deployment
   - SOP 5: Session Documentation
3. **Quick Reference Card** - One-page cheat sheet

## Quick Start (5 Minutes)

### Step 1: Copy Claude.md to Your Project

```bash
cp CLAUDE.md /path/to/your/project/
```

### Step 2: Customize the Sections

Open CLAUDE.md and update:
- `## Architecture` - Describe your project structure
- `## Communication Patterns` - Add your common phrases
- `## Operating Principles` - Keep or modify as needed

### Step 3: Start a Claude Session

When starting Claude Code:
```bash
cd /path/to/your/project
claude
```

Claude will automatically read CLAUDE.md and follow its guidelines.

## The 3 Core SOPs

### SOP 1: Project Initialization

**When**: Starting any new project

**Steps**:
1. Create project folder
2. Initialize with standard structure:
   ```
   project/
   ├── src/           # Your code
   ├── workflows/     # Documented procedures
   ├── VERSION        # e.g., "1.0.0-dev"
   ├── CHANGELOG.md   # Version history
   └── README.md      # Project docs
   ```
3. Create initial directive (what the project does)
4. Develop iteratively, document as you go

### SOP 3: Version Control & Deployment

**When**: Ready to deploy or release

**Steps**:
1. Update VERSION file (remove "-dev" suffix)
2. Update CHANGELOG.md with all changes
3. Deploy using your deployment script
4. Bump to next dev version
5. Verify deployment worked

**Version Strategy**:
- Major (X.0.0): Breaking changes
- Minor (x.Y.0): New features, backwards compatible
- Patch (x.y.Z): Bug fixes only

### SOP 5: Session Documentation

**When**: End of significant work session

**Steps**:
1. Note what you accomplished
2. Document key learnings
3. Record any new patterns discovered
4. Update relevant docs

## Communication Patterns

Tell Claude what you want using consistent phrases:

| You Say | Claude Does |
|---------|-------------|
| "Follow the SOP" | Reads and follows documented procedure |
| "Update the changelog" | Adds entry to CHANGELOG.md |
| "Document this" | Creates workflow or updates docs |
| "Deploy to production" | Runs deployment procedure |
| "Save session progress" | Updates session history |

## What's in the Pro Version?

The free tier gives you the foundation. The Pro tier ($97) includes:

- **17 Complete SOPs** covering the full development lifecycle
- **Multi-Agent Testing Patterns** - Run parallel agents to find edge cases
- **DOE Architecture Framework** - Directive-Orchestration-Execution model
- **Session Continuity System** - Never lose context between sessions
- **Workflow Templates** - Pre-built procedures for common tasks
- **6 Months of Updates** - As Claude evolves, so does the framework

[Learn more about Pro →](https://marceausolutions.com/claude-framework)

## Next Steps

1. **Try it now**: Copy CLAUDE.md to a project and start a session
2. **Join the list**: Get notified when new SOPs are released
3. **Share feedback**: What would make this more useful?

---

Questions? william@marceausolutions.com
