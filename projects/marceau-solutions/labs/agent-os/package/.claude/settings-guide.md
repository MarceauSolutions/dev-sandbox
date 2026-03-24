# Settings Guide

The `.claude/settings.local.json` file controls permissions and hooks.

## Permissions
The `allow` array lists commands Claude Code can run without asking:
- `Bash(git:*)` — All git commands
- `Bash(python:*)` — Python execution
- `Bash(npm:*)` — NPM commands
- etc.

Add patterns as needed. Format: `Bash(command-prefix:*)`

## Hooks
Hooks run automatically before/after tool use:

### PreToolUse hooks
- **Write matcher**: Runs before creating files
  - `check-existing-tools.sh` — warns about duplicate tools
  - `project-structure-guard.sh` — warns about wrong file locations
- **Bash matcher**: Runs before shell commands
  - `api-cost-guard.sh` — warns/blocks paid API calls
  - `destructive-guard.sh` — backs up before destructive ops
  - `stack-guard.sh` — blocks unapproved services
  - `complete-the-loop-guard.sh` — reminds to check replies after sending

### Adding new hooks
Add entries to the `hooks` section in settings.local.json following the existing pattern.
