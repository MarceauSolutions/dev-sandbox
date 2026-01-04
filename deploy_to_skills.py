#!/usr/bin/env python3
"""
Deploy a tested DOE project to a new Skills workspace.

Usage:
    python deploy_to_skills.py --project project-name
    python deploy_to_skills.py --project client-crm --skill-name crm-management
"""

import os
import sys
import argparse
import shutil
from pathlib import Path

# Base paths
DOE_WORKSPACE = Path(__file__).parent
SKILLS_BASE = Path.home() / "youtubeworkspace-skills"


def create_skill_workspace(project_name, skill_name=None):
    """Create a new Skills workspace for a deployed project."""

    if not skill_name:
        skill_name = project_name

    workspace_path = Path.home() / f"{project_name}-prod"

    print(f"\n{'='*70}")
    print(f"Deploying: {project_name} → Production Skills Workspace")
    print(f"{'='*70}\n")

    # Check if workspace already exists
    if workspace_path.exists():
        response = input(f"⚠️  Workspace already exists at {workspace_path}\nOverwrite? (y/n): ")
        if response.lower() != 'y':
            print("❌ Deployment cancelled")
            return
        shutil.rmtree(workspace_path)

    # Create directory structure
    print("📁 Creating directory structure...")
    skill_dir = workspace_path / ".claude" / "skills" / skill_name / "scripts"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (workspace_path / ".tmp").mkdir(exist_ok=True)

    # Copy configuration files
    print("⚙️  Copying configuration files...")
    files_to_copy = [".env.example", "requirements.txt", ".gitignore"]
    for file in files_to_copy:
        src = DOE_WORKSPACE / file
        if src.exists():
            shutil.copy(src, workspace_path / file)

    # Create .env from .env.example
    env_example = workspace_path / ".env.example"
    env_file = workspace_path / ".env"
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print(f"   ✓ Created .env (REMEMBER TO UPDATE WITH PRODUCTION CREDENTIALS)")

    # Find and copy directive
    print(f"📋 Looking for directive: directives/{project_name}.md")
    directive_path = DOE_WORKSPACE / "directives" / f"{project_name}.md"

    if not directive_path.exists():
        print(f"   ⚠️  Directive not found at {directive_path}")
        print(f"   You'll need to create SKILL.md manually")
        directive_content = None
    else:
        with open(directive_path, 'r') as f:
            directive_content = f.read()
        print(f"   ✓ Found directive")

    # Find and copy scripts
    print(f"🔍 Looking for scripts: execution/{project_name}*.py")
    execution_dir = DOE_WORKSPACE / "execution"
    scripts = list(execution_dir.glob(f"{project_name}*.py"))

    if not scripts:
        scripts = list(execution_dir.glob("*.py"))
        print(f"   ⚠️  No project-specific scripts found")
        print(f"   Found {len(scripts)} general scripts")
        response = input(f"   Copy all scripts? (y/n): ")
        if response.lower() != 'y':
            scripts = []

    for script in scripts:
        dest = skill_dir / script.name
        shutil.copy(script, dest)
        print(f"   ✓ Copied {script.name}")

    # Copy any JSON config files
    json_files = list(execution_dir.glob("*.json"))
    for json_file in json_files:
        if not json_file.name.startswith('.'):
            dest = skill_dir / json_file.name
            shutil.copy(json_file, dest)
            print(f"   ✓ Copied {json_file.name}")

    # Create SKILL.md
    print(f"📝 Creating SKILL.md...")
    skill_md = create_skill_md(skill_name, project_name, directive_content, scripts)
    skill_md_path = workspace_path / ".claude" / "skills" / skill_name / "SKILL.md"
    with open(skill_md_path, 'w') as f:
        f.write(skill_md)
    print(f"   ✓ Created SKILL.md")

    # Create README
    print(f"📖 Creating README...")
    readme = create_readme(project_name, skill_name)
    with open(workspace_path / "README.md", 'w') as f:
        f.write(readme)

    # Initialize git
    print(f"🔧 Initializing git repository...")
    os.system(f'cd "{workspace_path}" && git init')

    # Summary
    print(f"\n{'='*70}")
    print(f"✅ Deployment Complete!")
    print(f"{'='*70}\n")
    print(f"📍 Location: {workspace_path}")
    print(f"🎯 Skill: {skill_name}")
    print(f"\n📋 Next Steps:")
    print(f"   1. cd {workspace_path}")
    print(f"   2. Edit .env with production credentials")
    print(f"   3. Review SKILL.md and add trigger phrases")
    print(f"   4. Test with natural language commands")
    print(f"   5. Use in production!\n")

    return workspace_path


def create_skill_md(skill_name, project_name, directive_content, scripts):
    """Generate SKILL.md from directive."""

    script_names = [s.name for s in scripts] if scripts else ["your-script.py"]

    skill_md = f"""---
name: {skill_name}
description: [ADD DESCRIPTION - this triggers auto-activation]
allowed-tools: [Bash, Read, Write, Edit]
model: opus
trigger-phrases:
  - "[ADD TRIGGER PHRASE 1]"
  - "[ADD TRIGGER PHRASE 2]"
---

# {skill_name.replace('-', ' ').title()} Skill

**Deployed from DOE project:** {project_name}

## When to Activate

[ADD: When should this skill activate? What problems does it solve?]

## Quick Usage

```bash
# Example command
python .claude/skills/{skill_name}/scripts/{script_names[0]} --help
```

## What This Does

[ADD: Step-by-step description of what this skill does]

## Configuration

Required environment variables in `.env`:

```env
# [ADD: List required environment variables]
EXAMPLE_VAR=value
```

## Examples

**Example 1:**
```
User: "[ADD EXAMPLE USER REQUEST]"
→ [What happens]
```

## Technical Details

### Scripts
"""

    for script_name in script_names:
        skill_md += f"- `scripts/{script_name}`\n"

    if directive_content:
        skill_md += f"\n\n## Original Directive\n\n{directive_content}\n"
    else:
        skill_md += "\n\n## TODO\n\n- Add trigger phrases in YAML frontmatter\n"
        skill_md += "- Document usage examples\n"
        skill_md += "- Add configuration requirements\n"
        skill_md += "- Test with natural language\n"

    return skill_md


def create_readme(project_name, skill_name):
    """Create README for Skills workspace."""

    return f"""# {project_name.replace('-', ' ').title()} - Production Skills Workspace

**Deployed from:** DOE Development Workspace
**Skill:** {skill_name}

## Purpose

This is a **production Skills workspace** for the {project_name} project.

Use natural language to interact with this skill.

## Setup

1. Update `.env` with production credentials:
   ```bash
   nano .env
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Test the skill:
   ```
   [ADD: Natural language test command]
   ```

## Documentation

See [.claude/skills/{skill_name}/SKILL.md](.claude/skills/{skill_name}/SKILL.md) for complete documentation.

## Configuration

All configuration is in `.env` (not committed to git).

## Development

To make changes:
1. Go back to DOE workspace: `/Users/williammarceaujr./youtubeworkspaceDOE/`
2. Update directive and scripts there
3. Test thoroughly
4. Re-deploy with: `python deploy_to_skills.py --project {project_name}`

**DO NOT edit scripts directly in this workspace.** Always develop in DOE, then deploy.

## Related Workspaces

- **DOE Development:** `/Users/williammarceaujr./youtubeworkspaceDOE/` (for development/testing)
- **This workspace:** Production deployment (for actual use)
"""


def main():
    parser = argparse.ArgumentParser(description="Deploy DOE project to Skills workspace")
    parser.add_argument("--project", required=True, help="Project name (matches directive filename)")
    parser.add_argument("--skill-name", help="Custom skill name (defaults to project name)")

    args = parser.parse_args()

    workspace_path = create_skill_workspace(args.project, args.skill_name)

    if workspace_path:
        print(f"🎉 Ready to use! Open Claude Code in the new workspace:")
        print(f"   cd {workspace_path}")


if __name__ == "__main__":
    main()
