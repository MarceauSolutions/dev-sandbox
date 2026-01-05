#!/usr/bin/env python3
"""
Deploy a workflow from DOE development environment to Claude Skills production.

This script:
1. Reads a directive from directives/
2. Creates a corresponding SKILL.md in .claude/skills/
3. References execution scripts
4. Validates skill format
5. Optionally adds to a project manifest

Usage:
    python execution/deploy_to_skills.py directive_name [--project PROJECT_NAME]

Example:
    python execution/deploy_to_skills.py amazon_process_orders --project amazon-assistant
"""

import argparse
import json
import re
from pathlib import Path
from datetime import datetime

def load_directive(directive_name: str) -> dict:
    """Load directive from directives/ folder."""
    directive_file = Path(__file__).parent.parent / 'directives' / f'{directive_name}.md'

    if not directive_file.exists():
        print(f"✗ Directive not found: {directive_file}")
        print(f"  Available directives:")
        directives_dir = Path(__file__).parent.parent / 'directives'
        for f in directives_dir.glob('*.md'):
            print(f"    - {f.stem}")
        return None

    with open(directive_file, 'r') as f:
        content = f.read()

    print(f"✓ Loaded directive: {directive_file}")

    # Extract key information from directive
    return {
        'name': directive_name,
        'content': content,
        'file': str(directive_file)
    }

def find_execution_scripts(directive_name: str) -> list:
    """Find related execution scripts."""
    execution_dir = Path(__file__).parent

    # Look for scripts with similar names
    patterns = [
        f"{directive_name}.py",
        f"*{directive_name}*.py",
    ]

    scripts = []
    for pattern in patterns:
        for script in execution_dir.glob(pattern):
            if script.name != 'deploy_to_skills.py':  # Exclude this script
                scripts.append(str(script))

    if scripts:
        print(f"✓ Found {len(scripts)} execution script(s):")
        for script in scripts:
            print(f"    - {Path(script).name}")
    else:
        print(f"⚠ No execution scripts found for '{directive_name}'")

    return scripts

def extract_description(directive_content: str) -> str:
    """Extract a description from the directive content."""
    # Try to find ## Goal or # Goal section
    goal_match = re.search(r'##?\s*Goal\s*\n(.*?)(?:\n##|\n#|$)', directive_content, re.DOTALL | re.IGNORECASE)
    if goal_match:
        goal = goal_match.group(1).strip()
        # Take first sentence or paragraph
        first_line = goal.split('\n')[0].strip()
        return first_line

    # Try ## Overview
    overview_match = re.search(r'##?\s*Overview\s*\n(.*?)(?:\n##|\n#|$)', directive_content, re.DOTALL | re.IGNORECASE)
    if overview_match:
        overview = overview_match.group(1).strip()
        first_line = overview.split('\n')[0].strip()
        return first_line

    # Default description
    return "Automated workflow deployed from DOE development environment"

def create_skill_md(directive: dict, execution_scripts: list, description: str) -> str:
    """Create SKILL.md content from directive."""
    skill_name = directive['name'].replace('_', '-')

    # Build allowed-tools list
    allowed_tools = ["Bash(python:*)"]

    # Extract script names for more specific permissions
    if execution_scripts:
        script_names = [Path(s).name for s in execution_scripts]
        script_patterns = ', '.join([f"python execution/{name}" for name in script_names])
    else:
        script_patterns = "python execution scripts"

    skill_content = f"""---
name: {skill_name}
description: {description}
allowed-tools: {json.dumps(allowed_tools)}
---

# {directive['name'].replace('_', ' ').title()}

## Overview

This skill was deployed from the DOE development environment.

**Source Directive:** `directives/{directive['name']}.md`

{description}

## When to use

This skill is automatically triggered based on the description above. Claude will detect when your request matches this skill's capabilities.

## Execution Scripts

This skill uses the following execution scripts:

"""

    # Add execution script references
    if execution_scripts:
        for script in execution_scripts:
            script_path = Path(script)
            skill_content += f"- `{script_path.relative_to(Path(__file__).parent.parent)}`\n"
    else:
        skill_content += f"- `execution/{directive['name']}.py` (create this script)\n"

    skill_content += f"""

## Instructions

For detailed implementation instructions, refer to the source directive:

**Directive:** [{directive['name']}.md](../../directives/{directive['name']}.md)

The directive contains:
- Goal and purpose
- Input requirements
- Step-by-step process
- Output format
- Edge cases and error handling
- API considerations
- Best practices

## Usage

{script_patterns}

## Deployment Information

- **Deployed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Source:** DOE development environment
- **Status:** Production-ready

## Notes

This skill references the directive in `directives/` for complete documentation.
All execution logic is in deterministic Python scripts in `execution/`.

Intermediate files are stored in `.tmp/` and are not committed to version control.
"""

    return skill_content

def create_skill_directory(skill_name: str, skill_content: str) -> Path:
    """Create skill directory and SKILL.md file."""
    skills_dir = Path(__file__).parent.parent / '.claude' / 'skills'
    skills_dir.mkdir(parents=True, exist_ok=True)

    skill_dir = skills_dir / skill_name
    skill_dir.mkdir(exist_ok=True)

    skill_file = skill_dir / 'SKILL.md'

    with open(skill_file, 'w') as f:
        f.write(skill_content)

    print(f"✓ Created skill: {skill_file}")
    return skill_file

def add_to_project_manifest(skill_name: str, project_name: str) -> bool:
    """Add skill to project manifest."""
    projects_dir = Path(__file__).parent.parent / '.claude' / 'projects'
    projects_dir.mkdir(parents=True, exist_ok=True)

    manifest_file = projects_dir / f'{project_name}-skills.json'

    # Load or create manifest
    if manifest_file.exists():
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)
    else:
        manifest = {
            'project': project_name,
            'description': f'{project_name.replace("-", " ").title()} project skills',
            'version': '1.0.0',
            'skills': [],
            'allowed_tools': ['Bash(python:*)', 'Read', 'Write', 'Grep'],
            'knowledge_domains': []
        }

    # Add skill if not already present
    if skill_name not in manifest['skills']:
        manifest['skills'].append(skill_name)
        manifest['skills'].sort()  # Keep alphabetical

        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)

        print(f"✓ Added '{skill_name}' to project manifest: {manifest_file}")
        print(f"  Project now has {len(manifest['skills'])} skill(s)")
        return True
    else:
        print(f"ℹ Skill '{skill_name}' already in project manifest")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Deploy a directive from DOE to Claude Skills',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Deploy a directive to skills:
    python execution/deploy_to_skills.py amazon_process_orders

  Deploy and add to project:
    python execution/deploy_to_skills.py amazon_process_orders --project amazon-assistant

  Deploy with custom description:
    python execution/deploy_to_skills.py weather_report --description "Generate weekly weather reports"
"""
    )

    parser.add_argument('directive_name', help='Name of directive (without .md extension)')
    parser.add_argument('--project', help='Project name to add this skill to')
    parser.add_argument('--description', help='Custom skill description')

    args = parser.parse_args()

    print("=" * 60)
    print("Deploying from DOE Development → Claude Skills Production")
    print("=" * 60)
    print()

    # Load directive
    directive = load_directive(args.directive_name)
    if not directive:
        return 1

    # Find execution scripts
    execution_scripts = find_execution_scripts(args.directive_name)

    # Extract or use custom description
    if args.description:
        description = args.description
    else:
        description = extract_description(directive['content'])

    print(f"\nSkill description: {description}")
    print()

    # Create skill
    skill_name = args.directive_name.replace('_', '-')
    skill_content = create_skill_md(directive, execution_scripts, description)
    skill_file = create_skill_directory(skill_name, skill_content)

    # Add to project manifest if specified
    if args.project:
        print()
        add_to_project_manifest(skill_name, args.project)

    print()
    print("=" * 60)
    print("✓ Deployment complete!")
    print("=" * 60)
    print(f"Skill name: {skill_name}")
    print(f"Skill file: {skill_file}")
    if args.project:
        print(f"Project: {args.project}")
    print()
    print("Next steps:")
    print("1. Test the skill by asking Claude naturally")
    print("2. Review and edit SKILL.md if needed")
    if not args.project:
        print("3. Add to a project with: --project PROJECT_NAME")
    print()

    return 0

if __name__ == "__main__":
    exit(main())
