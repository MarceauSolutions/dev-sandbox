#!/usr/bin/env python3
"""
Manage project manifests and agent skill assignments.

This script helps you:
- Create new project manifests
- Add/remove skills from projects
- List projects and their skills
- Configure agent access and permissions

Usage:
    python execution/manage_agent_skills.py create-project --name PROJECT
    python execution/manage_agent_skills.py add --project PROJECT --skill SKILL
    python execution/manage_agent_skills.py remove --project PROJECT --skill SKILL
    python execution/manage_agent_skills.py list [--project PROJECT]
    python execution/manage_agent_skills.py configure --project PROJECT

Examples:
    python execution/manage_agent_skills.py create-project --name amazon-assistant
    python execution/manage_agent_skills.py add --project amazon-assistant --skill amazon-process-orders
    python execution/manage_agent_skills.py list --project amazon-assistant
"""

import argparse
import json
from pathlib import Path
from typing import Optional

def get_projects_dir() -> Path:
    """Get .claude/projects directory."""
    projects_dir = Path(__file__).parent.parent / '.claude' / 'projects'
    projects_dir.mkdir(parents=True, exist_ok=True)
    return projects_dir

def get_agents_dir() -> Path:
    """Get .claude/agents directory."""
    agents_dir = Path(__file__).parent.parent / '.claude' / 'agents'
    agents_dir.mkdir(parents=True, exist_ok=True)
    return agents_dir

def get_skills_dir() -> Path:
    """Get .claude/skills directory."""
    return Path(__file__).parent.parent / '.claude' / 'skills'

def list_available_skills() -> list:
    """List all available skills."""
    skills_dir = get_skills_dir()
    if not skills_dir.exists():
        return []

    skills = []
    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir() and (skill_dir / 'SKILL.md').exists():
            skills.append(skill_dir.name)

    return sorted(skills)

def create_project(name: str, description: Optional[str] = None, domains: Optional[list] = None) -> dict:
    """Create a new project manifest."""
    projects_dir = get_projects_dir()
    manifest_file = projects_dir / f'{name}-skills.json'

    if manifest_file.exists():
        print(f"⚠ Project '{name}' already exists")
        with open(manifest_file, 'r') as f:
            return json.load(f)

    manifest = {
        'project': name,
        'description': description or f'{name.replace("-", " ").title()} project',
        'version': '1.0.0',
        'skills': [],
        'allowed_tools': [
            'Bash(python:*)',
            'Read',
            'Write',
            'Grep'
        ],
        'knowledge_domains': domains or [],
        'restrictions': []
    }

    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"✓ Created project: {name}")
    print(f"  Manifest: {manifest_file}")

    # Also create agent configuration
    create_agent_config(name, manifest)

    return manifest

def create_agent_config(project_name: str, manifest: dict) -> Path:
    """Create agent configuration file."""
    agents_dir = get_agents_dir()
    agent_file = agents_dir / f'{project_name}.json'

    agent_config = {
        'agent_name': project_name,
        'project': project_name,
        'description': manifest.get('description', ''),
        'skills_manifest': f'../.claude/projects/{project_name}-skills.json',
        'allowed_tools': manifest.get('allowed_tools', []),
        'knowledge_domains': manifest.get('knowledge_domains', []),
        'jargon': {
            'enabled': False,
            'domains': []
        },
        'restrictions': manifest.get('restrictions', [])
    }

    with open(agent_file, 'w') as f:
        json.dump(agent_config, f, indent=2)

    print(f"✓ Created agent config: {agent_file}")
    return agent_file

def load_project(name: str) -> Optional[dict]:
    """Load project manifest."""
    projects_dir = get_projects_dir()
    manifest_file = projects_dir / f'{name}-skills.json'

    if not manifest_file.exists():
        print(f"✗ Project '{name}' not found")
        return None

    with open(manifest_file, 'r') as f:
        return json.load(f)

def save_project(name: str, manifest: dict):
    """Save project manifest."""
    projects_dir = get_projects_dir()
    manifest_file = projects_dir / f'{name}-skills.json'

    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"✓ Updated project: {name}")

def add_skill_to_project(project_name: str, skill_name: str) -> bool:
    """Add a skill to a project."""
    manifest = load_project(project_name)
    if not manifest:
        return False

    # Check if skill exists
    available_skills = list_available_skills()
    if skill_name not in available_skills:
        print(f"✗ Skill '{skill_name}' not found")
        print(f"  Available skills:")
        for skill in available_skills:
            print(f"    - {skill}")
        return False

    # Add skill
    if skill_name in manifest['skills']:
        print(f"ℹ Skill '{skill_name}' already in project")
        return True

    manifest['skills'].append(skill_name)
    manifest['skills'].sort()

    save_project(project_name, manifest)
    print(f"✓ Added skill '{skill_name}' to project '{project_name}'")
    print(f"  Project now has {len(manifest['skills'])} skill(s)")

    return True

def remove_skill_from_project(project_name: str, skill_name: str) -> bool:
    """Remove a skill from a project."""
    manifest = load_project(project_name)
    if not manifest:
        return False

    if skill_name not in manifest['skills']:
        print(f"ℹ Skill '{skill_name}' not in project")
        return True

    manifest['skills'].remove(skill_name)

    save_project(project_name, manifest)
    print(f"✓ Removed skill '{skill_name}' from project '{project_name}'")
    print(f"  Project now has {len(manifest['skills'])} skill(s)")

    return True

def list_projects():
    """List all projects."""
    projects_dir = get_projects_dir()

    manifests = list(projects_dir.glob('*-skills.json'))

    if not manifests:
        print("No projects found")
        print()
        print("Create a project with:")
        print("  python execution/manage_agent_skills.py create-project --name PROJECT_NAME")
        return

    print(f"Found {len(manifests)} project(s):")
    print()

    for manifest_file in sorted(manifests):
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)

        project_name = manifest['project']
        description = manifest.get('description', '')
        skill_count = len(manifest.get('skills', []))

        print(f"  • {project_name}")
        print(f"    {description}")
        print(f"    {skill_count} skill(s)")
        print()

def list_project_details(project_name: str):
    """List detailed information about a project."""
    manifest = load_project(project_name)
    if not manifest:
        return

    print()
    print("=" * 60)
    print(f"Project: {manifest['project']}")
    print("=" * 60)
    print(f"Description: {manifest.get('description', '')}")
    print(f"Version: {manifest.get('version', '')}")
    print()

    print("Skills:")
    skills = manifest.get('skills', [])
    if skills:
        for skill in skills:
            print(f"  • {skill}")
    else:
        print("  (no skills assigned)")
    print()

    print("Allowed Tools:")
    for tool in manifest.get('allowed_tools', []):
        print(f"  • {tool}")
    print()

    domains = manifest.get('knowledge_domains', [])
    if domains:
        print("Knowledge Domains:")
        for domain in domains:
            print(f"  • {domain}")
        print()

    restrictions = manifest.get('restrictions', [])
    if restrictions:
        print("Restrictions:")
        for restriction in restrictions:
            print(f"  • {restriction}")
        print()

def configure_project(project_name: str):
    """Interactive configuration of a project."""
    manifest = load_project(project_name)
    if not manifest:
        return

    print()
    print(f"Configuring project: {project_name}")
    print()

    # Description
    print(f"Current description: {manifest.get('description', '')}")
    new_desc = input("New description (press Enter to keep): ").strip()
    if new_desc:
        manifest['description'] = new_desc

    # Knowledge domains
    print()
    print(f"Current domains: {', '.join(manifest.get('knowledge_domains', []))}")
    new_domains = input("New domains (comma-separated, press Enter to keep): ").strip()
    if new_domains:
        manifest['knowledge_domains'] = [d.strip() for d in new_domains.split(',')]

    # Restrictions
    print()
    print("Current restrictions:")
    for r in manifest.get('restrictions', []):
        print(f"  • {r}")
    print("Add restriction (press Enter to skip): ")
    new_restriction = input().strip()
    if new_restriction:
        if 'restrictions' not in manifest:
            manifest['restrictions'] = []
        manifest['restrictions'].append(new_restriction)

    save_project(project_name, manifest)
    print()
    print("✓ Configuration updated")

def main():
    parser = argparse.ArgumentParser(
        description='Manage project manifests and agent skill assignments',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # create-project
    create_parser = subparsers.add_parser('create-project', help='Create a new project')
    create_parser.add_argument('--name', required=True, help='Project name')
    create_parser.add_argument('--description', help='Project description')
    create_parser.add_argument('--domains', help='Comma-separated knowledge domains')

    # add
    add_parser = subparsers.add_parser('add', help='Add a skill to a project')
    add_parser.add_argument('--project', required=True, help='Project name')
    add_parser.add_argument('--skill', required=True, help='Skill name')

    # remove
    remove_parser = subparsers.add_parser('remove', help='Remove a skill from a project')
    remove_parser.add_argument('--project', required=True, help='Project name')
    remove_parser.add_argument('--skill', required=True, help='Skill name')

    # list
    list_parser = subparsers.add_parser('list', help='List projects or project details')
    list_parser.add_argument('--project', help='Show details for specific project')

    # configure
    config_parser = subparsers.add_parser('configure', help='Configure a project')
    config_parser.add_argument('--project', required=True, help='Project name')

    # list-skills
    subparsers.add_parser('list-skills', help='List all available skills')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    if args.command == 'create-project':
        domains = [d.strip() for d in args.domains.split(',')] if args.domains else []
        create_project(args.name, args.description, domains)

    elif args.command == 'add':
        add_skill_to_project(args.project, args.skill)

    elif args.command == 'remove':
        remove_skill_from_project(args.project, args.skill)

    elif args.command == 'list':
        if args.project:
            list_project_details(args.project)
        else:
            list_projects()

    elif args.command == 'configure':
        configure_project(args.project)

    elif args.command == 'list-skills':
        print("Available skills:")
        for skill in list_available_skills():
            print(f"  • {skill}")

    return 0

if __name__ == "__main__":
    exit(main())
