#!/usr/bin/env python3
"""
Deploy projects from dev-sandbox to production Skills workspaces or GitHub repos.

Usage:
    # Sync scripts from project src to execution/
    python deploy_to_skills.py --sync-execution --project interview-prep

    # Deploy to local Skills workspace
    python deploy_to_skills.py --project interview-prep

    # Deploy to GitHub repository
    python deploy_to_skills.py --project interview-prep --repo MarceauSolutions/interview-prep-assistant

    # List all projects
    python deploy_to_skills.py --list
"""

import os
import sys
import argparse
import shutil
import subprocess
import json
from pathlib import Path
from datetime import datetime

# Base paths
DEV_SANDBOX = Path(__file__).parent
EXECUTION_DIR = DEV_SANDBOX / "execution"
DIRECTIVES_DIR = DEV_SANDBOX / "directives"
SKILLS_DIR = DEV_SANDBOX / ".claude" / "skills"
PROJECTS_DIR = DEV_SANDBOX / "projects"

# Project configurations
PROJECTS = {
    "interview-prep": {
        "skill_name": "interview-prep",
        "src_dir": DEV_SANDBOX / "interview-prep-pptx" / "src",
        "skill_md": DEV_SANDBOX / "interview-prep-pptx" / "SKILL.md",
        "directive": "interview_prep.md",
        "scripts": [
            "interview_research.py",
            "interview_prep_api.py",
            "pptx_generator.py",
            "pptx_editor.py",
            "session_manager.py",
            "grok_image_gen.py"
        ],
        "description": "Interview Prep PowerPoint Generator"
    },
    "fitness-influencer": {
        "skill_name": "fitness-influencer-operations",
        "src_dir": PROJECTS_DIR / "fitness-influencer" / "src",
        "skill_md": SKILLS_DIR / "fitness-influencer-operations" / "SKILL.md",
        "directive": "fitness_influencer_operations.md",
        "scripts": [
            "video_jumpcut.py",
            "educational_graphics.py",
            "gmail_monitor.py",
            "revenue_analytics.py",
            "grok_image_gen.py",
            "twilio_sms.py",
            "workout_plan_generator.py",
            "nutrition_guide_generator.py"
        ],
        "description": "Fitness Influencer AI Operations"
    },
    "amazon-seller": {
        "skill_name": "amazon-seller-operations",
        "src_dir": PROJECTS_DIR / "amazon-seller" / "src",
        "skill_md": SKILLS_DIR / "amazon-seller-operations" / "SKILL.md",
        "directive": "amazon_seller_operations.md",
        "scripts": [
            "amazon_sp_api.py",
            "amazon_fee_calculator.py",
            "amazon_inventory_optimizer.py",
            "gmail_monitor.py",
            "revenue_analytics.py",
            "twilio_sms.py"
        ],
        "description": "Amazon Seller AI Operations"
    },
    "naples-weather": {
        "skill_name": "naples-weather-report",
        "src_dir": PROJECTS_DIR / "naples-weather" / "src",
        "skill_md": SKILLS_DIR / "naples-weather-report" / "SKILL.md",
        "directive": "generate_naples_weather_report.md",
        "scripts": [
            "fetch_naples_weather.py",
            "generate_weather_report.py",
            "markdown_to_pdf.py"
        ],
        "description": "Naples Weather Report Generator"
    }
}


def list_projects():
    """List all available projects."""
    print("\n" + "=" * 60)
    print("Available Projects")
    print("=" * 60 + "\n")

    for name, config in PROJECTS.items():
        status = "✓" if config["src_dir"].exists() else "✗"
        print(f"  {status} {name}")
        print(f"      Skill: {config['skill_name']}")
        print(f"      Src: {config['src_dir']}")
        print()


def sync_to_execution(project_name: str):
    """Sync project scripts from src/ to execution/ directory."""
    if project_name not in PROJECTS:
        print(f"❌ Unknown project: {project_name}")
        print(f"   Available: {', '.join(PROJECTS.keys())}")
        return False

    config = PROJECTS[project_name]
    src_dir = config["src_dir"]

    if not src_dir.exists():
        print(f"❌ Source directory not found: {src_dir}")
        return False

    print(f"\n{'=' * 60}")
    print(f"Syncing {project_name} to execution/")
    print(f"{'=' * 60}\n")

    synced = 0
    for script in config["scripts"]:
        src_file = src_dir / script
        if src_file.exists():
            dest_file = EXECUTION_DIR / script
            shutil.copy(src_file, dest_file)
            print(f"   ✓ {script}")
            synced += 1
        else:
            # Try to find in execution/ already (shared scripts)
            exec_file = EXECUTION_DIR / script
            if exec_file.exists():
                print(f"   ○ {script} (already in execution/)")
            else:
                print(f"   ✗ {script} (not found)")

    print(f"\n✅ Synced {synced} scripts to execution/")
    return True


def sync_all_execution():
    """Sync all project scripts to execution/."""
    print("\n" + "=" * 60)
    print("Syncing ALL projects to execution/")
    print("=" * 60 + "\n")

    for project_name in PROJECTS:
        sync_to_execution(project_name)
        print()


def deploy_to_local_workspace(project_name: str):
    """Deploy project to a local Skills workspace (~/{project}-prod/)."""
    if project_name not in PROJECTS:
        print(f"❌ Unknown project: {project_name}")
        return False

    config = PROJECTS[project_name]
    skill_name = config["skill_name"]
    workspace_path = Path.home() / f"{project_name}-prod"

    print(f"\n{'=' * 60}")
    print(f"Deploying: {project_name} → Local Skills Workspace")
    print(f"{'=' * 60}\n")

    # Check if workspace exists
    if workspace_path.exists():
        response = input(f"⚠️  Workspace exists at {workspace_path}. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("❌ Deployment cancelled")
            return False
        shutil.rmtree(workspace_path)

    # Create directory structure
    print("📁 Creating directory structure...")
    skill_dir = workspace_path / ".claude" / "skills" / skill_name
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (workspace_path / ".tmp").mkdir(exist_ok=True)

    # Copy .env.example
    env_example = DEV_SANDBOX / ".env.example"
    if env_example.exists():
        shutil.copy(env_example, workspace_path / ".env.example")
        shutil.copy(env_example, workspace_path / ".env")
        print("   ✓ Created .env (UPDATE WITH PRODUCTION CREDENTIALS)")

    # Copy SKILL.md
    if config["skill_md"].exists():
        shutil.copy(config["skill_md"], skill_dir / "SKILL.md")
        print(f"   ✓ Copied SKILL.md")
    else:
        # Try from .claude/skills
        alt_skill = SKILLS_DIR / skill_name / "SKILL.md"
        if alt_skill.exists():
            shutil.copy(alt_skill, skill_dir / "SKILL.md")
            print(f"   ✓ Copied SKILL.md (from .claude/skills)")

    # Copy USE_CASES.json if exists
    use_cases = SKILLS_DIR / skill_name / "USE_CASES.json"
    if use_cases.exists():
        shutil.copy(use_cases, skill_dir / "USE_CASES.json")
        print(f"   ✓ Copied USE_CASES.json")

    # Copy scripts
    print(f"\n📋 Copying scripts...")
    for script in config["scripts"]:
        src = EXECUTION_DIR / script
        if src.exists():
            shutil.copy(src, scripts_dir / script)
            print(f"   ✓ {script}")
        else:
            print(f"   ✗ {script} (not found in execution/)")

    # Copy directive
    directive = DIRECTIVES_DIR / config["directive"]
    if directive.exists():
        shutil.copy(directive, skill_dir / "DIRECTIVE.md")
        print(f"   ✓ Copied directive")

    # Create README
    readme = f"""# {config['description']} - Production Workspace

**Deployed from:** dev-sandbox
**Skill:** {skill_name}
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Setup

1. Update `.env` with production credentials
2. Test the skill with natural language commands

## Documentation

See `.claude/skills/{skill_name}/SKILL.md` for usage.

## Development

DO NOT edit directly here. Make changes in dev-sandbox first, then redeploy:

```bash
cd ~/dev-sandbox
python deploy_to_skills.py --project {project_name}
```
"""
    (workspace_path / "README.md").write_text(readme)

    # Initialize git
    os.system(f'cd "{workspace_path}" && git init -q')

    print(f"\n{'=' * 60}")
    print(f"✅ Deployment Complete!")
    print(f"{'=' * 60}")
    print(f"\n📍 Location: {workspace_path}")
    print(f"🎯 Skill: {skill_name}")
    print(f"\n📋 Next Steps:")
    print(f"   1. cd {workspace_path}")
    print(f"   2. Edit .env with production credentials")
    print(f"   3. Test with natural language commands\n")

    return True


def deploy_to_github(project_name: str, repo: str):
    """Deploy project skills to a GitHub repository."""
    if project_name not in PROJECTS:
        print(f"❌ Unknown project: {project_name}")
        return False

    config = PROJECTS[project_name]
    skill_name = config["skill_name"]

    print(f"\n{'=' * 60}")
    print(f"Deploying: {project_name} → GitHub: {repo}")
    print(f"{'=' * 60}\n")

    # Clone or update the repo
    repo_dir = Path.home() / ".deploy-temp" / repo.split("/")[1]
    repo_dir.parent.mkdir(parents=True, exist_ok=True)

    if repo_dir.exists():
        print(f"📥 Updating existing clone...")
        result = subprocess.run(
            ["git", "pull"],
            cwd=repo_dir,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"⚠️  Pull failed, re-cloning...")
            shutil.rmtree(repo_dir)
            subprocess.run(["gh", "repo", "clone", repo, str(repo_dir)], check=True)
    else:
        print(f"📥 Cloning {repo}...")
        try:
            subprocess.run(["gh", "repo", "clone", repo, str(repo_dir)], check=True)
        except subprocess.CalledProcessError:
            print(f"❌ Failed to clone {repo}. Make sure it exists and you have access.")
            return False

    # Create .claude/skills directory
    skill_dir = repo_dir / ".claude" / "skills" / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)

    # Copy SKILL.md
    print(f"\n📋 Copying skill files...")
    if config["skill_md"].exists():
        shutil.copy(config["skill_md"], skill_dir / "SKILL.md")
        print(f"   ✓ SKILL.md")
    else:
        alt_skill = SKILLS_DIR / skill_name / "SKILL.md"
        if alt_skill.exists():
            shutil.copy(alt_skill, skill_dir / "SKILL.md")
            print(f"   ✓ SKILL.md")

    # Copy USE_CASES.json
    use_cases = SKILLS_DIR / skill_name / "USE_CASES.json"
    if use_cases.exists():
        shutil.copy(use_cases, skill_dir / "USE_CASES.json")
        print(f"   ✓ USE_CASES.json")

    # Copy directive
    directive = DIRECTIVES_DIR / config["directive"]
    if directive.exists():
        shutil.copy(directive, skill_dir / "DIRECTIVE.md")
        print(f"   ✓ DIRECTIVE.md")

    # Create scripts directory and copy scripts
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir(exist_ok=True)

    print(f"\n📋 Copying scripts...")
    for script in config["scripts"]:
        src = EXECUTION_DIR / script
        if src.exists():
            shutil.copy(src, scripts_dir / script)
            print(f"   ✓ {script}")

    # Commit and push
    print(f"\n📤 Committing and pushing...")
    os.chdir(repo_dir)
    subprocess.run(["git", "add", "-A"], check=True)

    commit_msg = f"chore: Update {skill_name} skill from dev-sandbox\n\nDeployed: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    result = subprocess.run(
        ["git", "commit", "-m", commit_msg],
        capture_output=True,
        text=True
    )

    if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
        print("   ○ No changes to commit")
    else:
        subprocess.run(["git", "push"], check=True)
        print("   ✓ Pushed to GitHub")

    print(f"\n{'=' * 60}")
    print(f"✅ Deployment Complete!")
    print(f"{'=' * 60}")
    print(f"\n📍 Repository: https://github.com/{repo}")
    print(f"🎯 Skill: .claude/skills/{skill_name}/")

    # Cleanup
    os.chdir(DEV_SANDBOX)

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Deploy dev-sandbox projects to production",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python deploy_to_skills.py --list
  python deploy_to_skills.py --sync-execution --project interview-prep
  python deploy_to_skills.py --sync-all
  python deploy_to_skills.py --project interview-prep
  python deploy_to_skills.py --project interview-prep --repo MarceauSolutions/interview-prep-assistant
        """
    )
    parser.add_argument("--list", action="store_true", help="List all available projects")
    parser.add_argument("--project", help="Project name to deploy")
    parser.add_argument("--repo", help="GitHub repo (org/name) to deploy to")
    parser.add_argument("--sync-execution", action="store_true", help="Sync project scripts to execution/")
    parser.add_argument("--sync-all", action="store_true", help="Sync ALL project scripts to execution/")

    args = parser.parse_args()

    if args.list:
        list_projects()
        return 0

    if args.sync_all:
        sync_all_execution()
        return 0

    if args.sync_execution:
        if not args.project:
            print("❌ --project required with --sync-execution")
            return 1
        sync_to_execution(args.project)
        return 0

    if args.project:
        if args.repo:
            deploy_to_github(args.project, args.repo)
        else:
            deploy_to_local_workspace(args.project)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
