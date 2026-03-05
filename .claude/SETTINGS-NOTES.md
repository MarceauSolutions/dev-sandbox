# Settings Notes

Explains the permission patterns in `.claude/settings.local.json`.

## Permission Categories

| Category | Patterns | Why Allowed |
|----------|----------|-------------|
| **Python** | `python:*`, `python3:*`, `pip install:*` | Core development — covers all Python execution |
| **Git** | `git add/commit/push/pull/fetch/clone/branch/rm/rev-parse/init/remote add:*` | Version control operations |
| **GitHub CLI** | `gh repo view/create:*`, `gh auth status:*`, `gh api:*` | GitHub API operations |
| **HTTP** | `curl:*` | API testing, health checks, downloads |
| **File ops** | `tree/ls/test/file/open/xargs/cat/grep/echo/chmod:*` | Basic file operations |
| **Network** | `dig:*` | DNS lookups |
| **Shell** | `source:*` | Loading .env files |
| **macOS** | `osascript:*` | Photos.app export (/photos command) |
| **Packages** | `brew install:*` | System package management |
| **Railway** | `railway *:*` | Deploying hosted services (if still used) |

## Hooks

| Trigger | Hook | Behavior |
|---------|------|----------|
| Write (any file) | `check-existing-tools.sh` | Warns about similar tools (informational, non-blocking) |
| Write (any file) | `duplicate-code-guard.sh` | Blocks creating .py files that duplicate execution/ scripts |
| Bash (any command) | `api-cost-guard.sh` | Warns/blocks expensive API calls based on provider status |

## What's NOT Allowed (by omission)

- `git reset --hard` — destructive, requires explicit user permission
- `rm -rf` — destructive, requires explicit user permission
- `git push --force` — destructive, requires explicit user permission
- `ssh` — requires explicit permission per-session for EC2 access

## Cleanup Log

- 2026-02-28: Removed loop fragments (`for slide...`, `do`, `done`) — one-time command leftovers
- 2026-02-28: Removed redundant specific python patterns covered by `python:*` wildcard
- 2026-02-28: Added duplicate-code-guard.sh hook to Write matcher
