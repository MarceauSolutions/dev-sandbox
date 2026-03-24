#!/usr/bin/env python3
"""AgentOS Health Check — System status at a glance."""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

def get_repo_root():
    try:
        result = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                              capture_output=True, text=True, timeout=5)
        return Path(result.stdout.strip()) if result.returncode == 0 else Path.cwd()
    except Exception:
        return Path.cwd()

def check_git_status(root):
    """Check for uncommitted changes and unpushed commits."""
    issues = []
    try:
        # Uncommitted changes
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, cwd=root)
        changes = len([l for l in result.stdout.strip().split('\n') if l.strip()])
        if changes > 0:
            issues.append(f"  {changes} uncommitted change(s)")

        # Unpushed commits
        result = subprocess.run(['git', 'log', '--oneline', 'origin/main..HEAD'],
                              capture_output=True, text=True, cwd=root)
        unpushed = len([l for l in result.stdout.strip().split('\n') if l.strip()])
        if unpushed > 0:
            issues.append(f"  {unpushed} unpushed commit(s) — run: git push origin main")
    except Exception as e:
        issues.append(f"  Git check failed: {e}")
    return issues

def check_env_file(root):
    """Check if .env exists and has content."""
    env_path = root / '.env'
    if not env_path.exists():
        return ["  .env file missing — create one with your API keys"]
    lines = [l for l in env_path.read_text().split('\n') if l.strip() and not l.startswith('#')]
    if len(lines) == 0:
        return ["  .env exists but has no configured keys"]
    return []

def check_nested_repos(root):
    """Check for nested git repositories."""
    issues = []
    try:
        result = subprocess.run(
            ['find', str(root), '-name', '.git', '(', '-type', 'd', '-o', '-type', 'f', ')'],
            capture_output=True, text=True, timeout=10
        )
        repos = [l for l in result.stdout.strip().split('\n') if l.strip() and l != str(root / '.git')]
        if repos:
            issues.append(f"  {len(repos)} nested git repo(s) found:")
            for r in repos[:5]:
                issues.append(f"    - {r}")
    except Exception:
        pass
    return issues

def check_agent_os_config(root):
    """Check AgentOS configuration status."""
    config = root / '.agent-os-configured'
    if not config.exists():
        return ["  AgentOS not configured — start a Claude Code session to run onboarding"]
    return []

def check_hooks(root):
    """Check that hooks exist and are executable."""
    hooks_dir = root / '.claude' / 'hooks'
    issues = []
    if not hooks_dir.exists():
        issues.append("  .claude/hooks/ directory missing")
        return issues
    hooks = list(hooks_dir.glob('*.sh'))
    if len(hooks) == 0:
        issues.append("  No hooks found in .claude/hooks/")
    else:
        for hook in hooks:
            if not os.access(hook, os.X_OK):
                issues.append(f"  {hook.name} is not executable — run: chmod +x {hook}")
    return issues

def check_memory(root):
    """Check memory system."""
    memory = root / 'memory' / 'MEMORY.md'
    if not memory.exists():
        return ["  memory/MEMORY.md missing — memory system not initialized"]
    return []

def main():
    root = get_repo_root()
    print(f"\n{'='*50}")
    print(f"  AgentOS Health Check")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Root: {root}")
    print(f"{'='*50}\n")

    checks = {
        "AgentOS Config": check_agent_os_config,
        "Git Status": check_git_status,
        "Environment (.env)": check_env_file,
        "Nested Repos": check_nested_repos,
        "Hooks": check_hooks,
        "Memory System": check_memory,
    }

    total_issues = 0
    for name, check_fn in checks.items():
        issues = check_fn(root)
        status = "PASS" if not issues else "WARN"
        icon = "✓" if not issues else "!"
        print(f"  [{icon}] {name}: {status}")
        for issue in issues:
            print(issue)
            total_issues += 1

    print(f"\n{'='*50}")
    if total_issues == 0:
        print("  All checks passed. System healthy.")
    else:
        print(f"  {total_issues} issue(s) found. Review above.")
    print(f"{'='*50}\n")

if __name__ == '__main__':
    main()
