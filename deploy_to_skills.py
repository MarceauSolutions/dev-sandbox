#!/usr/bin/env python3
"""
Deploy projects from dev-sandbox to production Skills workspaces or GitHub repos.

Supports versioned deployments for tracking changes across releases.

Usage:
    # List all projects
    python deploy_to_skills.py --list

    # Check deployment status
    python deploy_to_skills.py --status interview-prep

    # Sync scripts from project src to execution/
    python deploy_to_skills.py --sync-execution --project interview-prep

    # Deploy with version tag
    python deploy_to_skills.py --project interview-prep --version 1.1.0

    # Deploy to local Skills workspace
    python deploy_to_skills.py --project interview-prep

    # Deploy to GitHub repository
    python deploy_to_skills.py --project interview-prep --repo MarceauSolutions/interview-prep-assistant

    # List version history
    python deploy_to_skills.py --project interview-prep --versions
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
            "template_manager.py",
            "live_editor.py",
            "grok_image_gen.py",
            "mock_interview.py",
            "pdf_outputs.py",
            "intent_router.py"
        ],
        "description": "Interview Prep AI Assistant",
        "frontend": {
            "dir": DEV_SANDBOX / "interview-prep-pptx",
            "deploy_method": "railway",  # railway, git-push, or manual
            "test_command": "python src/api.py",
            "deploy_command": "railway up"
        }
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
    },
    "personal-assistant": {
        "skill_name": "personal-assistant",
        "src_dir": PROJECTS_DIR / "personal-assistant" / "src",
        "skill_md": SKILLS_DIR / "personal-assistant" / "SKILL.md",
        "directive": None,  # No directive - this is a meta-skill
        "scripts": [],  # Aggregates other project scripts
        "description": "William's Personal AI Assistant (Aggregates all skills)",
        "deployment_target": "local-only"  # No Railway/GitHub deployment
    },
    "website-builder": {
        "skill_name": "website-builder",
        "src_dir": PROJECTS_DIR / "website-builder" / "src",
        "skill_md": SKILLS_DIR / "website-builder" / "SKILL.md",
        "directive": "website_builder.md",
        "scripts": [
            "research_engine.py",
            "content_generator.py",
            "site_builder.py",
            "website_builder_api.py"
        ],
        "description": "AI Website Builder - Research & Generate Websites",
        "frontend": {
            "dir": PROJECTS_DIR / "website-builder",
            "deploy_method": "railway",
            "deploy_command": "railway up"
        }
    }
}


def get_version(project_name: str) -> str:
    """Get current version from VERSION file."""
    config = PROJECTS.get(project_name, {})
    version_file = config.get("src_dir", Path()).parent / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()
    return "0.0.0"


def get_deployed_version(project_name: str) -> str:
    """Get version deployed to .claude/skills/."""
    config = PROJECTS.get(project_name, {})
    skill_name = config.get("skill_name", "")
    version_file = SKILLS_DIR / skill_name / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()
    return "not deployed"


def set_version(project_name: str, version: str):
    """Set version in VERSION file."""
    config = PROJECTS.get(project_name, {})
    version_file = config.get("src_dir", Path()).parent / "VERSION"
    version_file.write_text(version + "\n")


def show_status(project_name: str):
    """Show deployment status for a project."""
    if project_name not in PROJECTS:
        print(f"❌ Unknown project: {project_name}")
        return

    config = PROJECTS[project_name]
    dev_version = get_version(project_name)
    prod_version = get_deployed_version(project_name)

    print(f"\n{'=' * 60}")
    print(f"Deployment Status: {project_name}")
    print(f"{'=' * 60}\n")

    print(f"  📦 Project: {config['description']}")
    print(f"  🏷️  Dev Version: {dev_version}")
    print(f"  🚀 Prod Version: {prod_version}")
    print(f"  📁 Skill: {config['skill_name']}")
    print()

    # Check if update needed
    if dev_version != prod_version and not dev_version.endswith("-dev"):
        print(f"  ⚠️  Dev version differs from prod - consider deploying")
    elif dev_version.endswith("-dev"):
        print(f"  🔧 Development in progress")
    else:
        print(f"  ✅ Prod is up to date")
    print()


def list_projects():
    """List all available projects."""
    print("\n" + "=" * 60)
    print("Available Projects")
    print("=" * 60 + "\n")

    for name, config in PROJECTS.items():
        status = "✓" if config["src_dir"].exists() else "✗"
        dev_ver = get_version(name)
        prod_ver = get_deployed_version(name)
        print(f"  {status} {name}")
        print(f"      Skill: {config['skill_name']}")
        print(f"      Dev: {dev_ver} | Prod: {prod_ver}")
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


def deploy_to_local_workspace(project_name: str, version: str = None):
    """Deploy project to a local Skills workspace (~/{project}-prod/)."""
    if project_name not in PROJECTS:
        print(f"❌ Unknown project: {project_name}")
        return False

    config = PROJECTS[project_name]
    skill_name = config["skill_name"]
    workspace_path = Path.home() / f"{project_name}-prod"

    # Get version
    if version is None:
        version = get_version(project_name)
        if version == "0.0.0":
            version = "1.0.0"
            set_version(project_name, version)

    print(f"\n{'=' * 60}")
    print(f"Deploying: {project_name} v{version} → Local Skills Workspace")
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

    # Create VERSION file
    (skill_dir / "VERSION").write_text(version + "\n")
    print(f"   ✓ Set VERSION to {version}")

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


def deploy_frontend(project_name: str, test_only: bool = False):
    """Deploy frontend for a project (Railway, git push, etc.)."""
    if project_name not in PROJECTS:
        print(f"❌ Unknown project: {project_name}")
        return False

    config = PROJECTS[project_name]
    frontend_config = config.get("frontend")

    if not frontend_config:
        print(f"❌ No frontend configured for {project_name}")
        return False

    frontend_dir = frontend_config["dir"]
    deploy_method = frontend_config.get("deploy_method", "manual")
    test_command = frontend_config.get("test_command")
    deploy_command = frontend_config.get("deploy_command")

    print(f"\n{'=' * 60}")
    print(f"{'Testing' if test_only else 'Deploying'} Frontend: {project_name}")
    print(f"{'=' * 60}\n")

    if not frontend_dir.exists():
        print(f"❌ Frontend directory not found: {frontend_dir}")
        return False

    # Test locally first
    if test_command:
        print(f"🧪 Test command: {test_command}")
        print(f"   Run this in {frontend_dir} to test locally\n")

    if test_only:
        print(f"📋 To test locally:")
        print(f"   cd {frontend_dir}")
        print(f"   {test_command}")
        print(f"\n   Then open http://localhost:8000 in your browser")
        return True

    # Deploy based on method
    if deploy_method == "railway":
        print(f"🚂 Deploying to Railway...")
        print(f"   cd {frontend_dir}")
        print(f"   {deploy_command}")
        print(f"\n   Running deployment...")

        result = subprocess.run(
            deploy_command.split(),
            cwd=frontend_dir,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"\n✅ Frontend deployed successfully!")
            print(result.stdout)
        else:
            print(f"\n⚠️  Railway CLI may not be installed or configured.")
            print(f"   Install: npm install -g @railway/cli")
            print(f"   Login: railway login")
            print(f"\n   Or deploy manually:")
            print(f"   cd {frontend_dir}")
            print(f"   {deploy_command}")
            # Don't return False - let user deploy manually
            return True

    elif deploy_method == "git-push":
        print(f"📤 Deploying via git push...")
        result = subprocess.run(
            ["git", "push"],
            cwd=frontend_dir,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ Pushed to remote - deployment will auto-trigger")
        else:
            print(f"❌ Git push failed: {result.stderr}")
            return False

    else:
        print(f"📋 Manual deployment required:")
        print(f"   cd {frontend_dir}")
        print(f"   {deploy_command or '(see project docs for deployment steps)'}")

    return True


def deploy_full(project_name: str, version: str = None):
    """Deploy both skill and frontend for a project."""
    if project_name not in PROJECTS:
        print(f"❌ Unknown project: {project_name}")
        return False

    config = PROJECTS[project_name]

    print(f"\n{'=' * 60}")
    print(f"FULL DEPLOYMENT: {project_name}")
    print(f"{'=' * 60}\n")

    # Step 1: Sync scripts to execution/
    print("📦 Step 1: Syncing scripts to execution/...")
    sync_to_execution(project_name)

    # Step 2: Deploy skill to .claude/skills/
    print(f"\n🎯 Step 2: Deploying skill...")
    skill_name = config["skill_name"]
    skill_dest = SKILLS_DIR / skill_name

    # Update SKILL.md
    if config["skill_md"].exists():
        skill_dest.mkdir(parents=True, exist_ok=True)
        shutil.copy(config["skill_md"], skill_dest / "SKILL.md")
        print(f"   ✓ Updated SKILL.md")

    # Update VERSION
    if version:
        set_version(project_name, version)
        (skill_dest / "VERSION").write_text(version + "\n")
        print(f"   ✓ Set VERSION to {version}")
    else:
        version = get_version(project_name)
        if version.endswith("-dev"):
            version = version.replace("-dev", "")
            set_version(project_name, version)
        (skill_dest / "VERSION").write_text(version + "\n")
        print(f"   ✓ Using VERSION {version}")

    # Step 3: Deploy frontend (if configured)
    if config.get("frontend"):
        print(f"\n🖥️  Step 3: Deploying frontend...")
        deploy_frontend(project_name)
    else:
        print(f"\n🖥️  Step 3: No frontend configured (skill-only project)")

    # Step 4: Bump to next dev version
    current = version.split(".")
    next_minor = int(current[1]) + 1
    next_version = f"{current[0]}.{next_minor}.0-dev"
    set_version(project_name, next_version)
    print(f"\n🔧 Step 4: Bumped to {next_version} for continued development")

    print(f"\n{'=' * 60}")
    print(f"✅ FULL DEPLOYMENT COMPLETE: {project_name} v{version}")
    print(f"{'=' * 60}")
    print(f"\n📋 Next steps:")
    print(f"   1. Test skill in Claude Code chat")
    if config.get("frontend"):
        print(f"   2. Test frontend in browser")
    print(f"   3. Commit: git add -A && git commit -m 'chore: Deploy {project_name} v{version}'")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Deploy dev-sandbox projects to production",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python deploy_to_skills.py --list
  python deploy_to_skills.py --status interview-prep
  python deploy_to_skills.py --sync-execution --project interview-prep
  python deploy_to_skills.py --sync-all
  python deploy_to_skills.py --project interview-prep --version 1.1.0
  python deploy_to_skills.py --project interview-prep --repo MarceauSolutions/interview-prep-assistant

  # Frontend deployment
  python deploy_to_skills.py --project interview-prep --frontend
  python deploy_to_skills.py --project interview-prep --test-frontend

  # Full deployment (skill + frontend)
  python deploy_to_skills.py --project interview-prep --full --version 1.2.0
        """
    )
    parser.add_argument("--list", action="store_true", help="List all available projects")
    parser.add_argument("--status", metavar="PROJECT", help="Show deployment status for a project")
    parser.add_argument("--project", help="Project name to deploy")
    parser.add_argument("--version", help="Version to deploy (e.g., 1.1.0)")
    parser.add_argument("--repo", help="GitHub repo (org/name) to deploy to")
    parser.add_argument("--sync-execution", action="store_true", help="Sync project scripts to execution/")
    parser.add_argument("--sync-all", action="store_true", help="Sync ALL project scripts to execution/")
    parser.add_argument("--frontend", action="store_true", help="Deploy frontend only")
    parser.add_argument("--test-frontend", action="store_true", help="Show how to test frontend locally")
    parser.add_argument("--full", action="store_true", help="Full deployment: skill + frontend + version bump")

    args = parser.parse_args()

    if args.list:
        list_projects()
        return 0

    if args.status:
        show_status(args.status)
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
        # Full deployment (skill + frontend)
        if args.full:
            deploy_full(args.project, args.version)
            return 0

        # Frontend only
        if args.frontend:
            deploy_frontend(args.project)
            return 0

        # Test frontend locally
        if args.test_frontend:
            deploy_frontend(args.project, test_only=True)
            return 0

        # GitHub deployment
        if args.repo:
            deploy_to_github(args.project, args.repo)
            return 0

        # Default: skill deployment to local workspace
        deploy_to_local_workspace(args.project, args.version)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
