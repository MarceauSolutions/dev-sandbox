# SOP 01 — Project Initialization

> Creates the standard directory structure for a new project.

## Prerequisites
- SOP 00 (Kickoff) completed
- Project name decided
- Location decided: `projects/[name]/`

## Steps

### 1. Create directory structure
```
projects/[name]/
├── src/           # Source code
├── docs/          # Project-specific docs
├── tests/         # Test files
└── CLAUDE.md      # Project configuration
```

### 2. Create project CLAUDE.md
Include:
- Project name and description
- Status (exploration, development, production)
- Key files and their purpose
- Build/run commands
- Generated files list (update as you create outputs)

### 3. Verify structure
- [ ] No nested .git directory
- [ ] CLAUDE.md exists with correct info
- [ ] Project appears in `python scripts/inventory.py list`

### 4. Update parent references
- If inside a company folder, update the company's CLAUDE.md
- Update memory/MEMORY.md if this is a significant project
