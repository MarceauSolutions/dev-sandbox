#!/usr/bin/env python3
"""
Rollback Multi-Company Folder Structure Migration

This script reverses the multi-company folder structure migration,
restoring all files to their original locations.

USAGE:
    python ralph/rollback_migration.py --dry-run    # Preview rollback
    python ralph/rollback_migration.py --execute     # Execute rollback

SAFETY:
- Uses git mv to preserve file history
- Creates atomic commit
- Only use if migration needs to be undone
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

# Base directory (dev-sandbox root)
BASE_DIR = Path("/Users/williammarceaujr./dev-sandbox")

# Reverse mapping: new_path -> old_path
# (This is the inverse of migrate_to_company_structure.py)
PROJECT_ROLLBACKS = {
    # SHARED MULTI-TENANT (4 projects)
    "projects/shared-multi-tenant/lead-scraper": "projects/lead-scraper",
    "projects/shared-multi-tenant/social-media-automation": "projects/social-media-automation",
    "projects/shared-multi-tenant/ai-customer-service": "projects/ai-customer-service",
    "projects/shared-multi-tenant/personal-assistant": "projects/personal-assistant",

    # MARCEAU SOLUTIONS (8 projects)
    "projects/marceau-solutions/fitness-influencer": "projects/fitness-influencer",
    "projects/marceau-solutions/website-builder": "projects/website-builder",
    "projects/marceau-solutions/instagram-creator": "projects/instagram-creator",
    "projects/marceau-solutions/tiktok-creator": "projects/tiktok-creator",
    "projects/marceau-solutions/youtube-creator": "projects/youtube-creator",
    "projects/marceau-solutions/interview-prep": "projects/interview-prep",
    "projects/marceau-solutions/amazon-seller": "projects/amazon-seller",

    # SW FLORIDA HVAC (1 project)
    "projects/swflorida-hvac/hvac-distributors": "projects/hvac-distributors",

    # GLOBAL UTILITY (9 projects)
    "projects/global-utility/md-to-pdf": "projects/md-to-pdf",
    "projects/global-utility/twilio-mcp": "projects/twilio-mcp",
    "projects/global-utility/claude-framework": "projects/claude-framework",
    "projects/global-utility/registry": "projects/registry",
    "projects/global-utility/mcp-aggregator": "projects/mcp-aggregator",
    "projects/global-utility/naples-weather": "projects/naples-weather",
    "projects/global-utility/time-blocks": "projects/time-blocks",
    "projects/global-utility/resume": "projects/resume",
    "projects/global-utility/shared": "projects/shared",

    # PRODUCT IDEAS (5 projects)
    "projects/product-ideas/crave-smart": "projects/crave-smart",
    "projects/product-ideas/decide-for-her": "projects/decide-for-her",
    "projects/product-ideas/elder-tech-concierge": "projects/elder-tech-concierge",
    "projects/product-ideas/amazon-buyer": "projects/amazon-buyer",
    "projects/product-ideas/uber-lyft-comparison": "projects/uber-lyft-comparison",

    # ARCHIVED (1 project)
    "projects/archived/automated-social-media-campaign": "projects/Automated_SocialMedia_Campaign",
}

DOCS_ROLLBACKS = {
    # MARCEAU SOLUTIONS DOCS
    "docs/companies/marceau-solutions/AI-VOICE-SERVICE-ECONOMICS.md": "docs/AI-VOICE-SERVICE-ECONOMICS.md",
    "docs/companies/marceau-solutions/MARCEAU-SOLUTIONS-COMPLETE-SERVICE-OFFERING.md": "docs/MARCEAU-SOLUTIONS-COMPLETE-SERVICE-OFFERING.md",
    "docs/companies/marceau-solutions/COLD-OUTREACH-STRATEGY-JAN-19-2026.md": "docs/COLD-OUTREACH-STRATEGY-JAN-19-2026.md",
    "docs/companies/marceau-solutions/CUSTOMER-ACQUISITION-STRATEGY-JAN-19-2026.md": "docs/CUSTOMER-ACQUISITION-STRATEGY-JAN-19-2026.md",
    "docs/companies/marceau-solutions/API-USAGE-COST-CHECKER.md": "docs/API-USAGE-COST-CHECKER.md",
    "docs/companies/marceau-solutions/APOLLO-IO-MAXIMIZATION-PLAN.md": "docs/APOLLO-IO-MAXIMIZATION-PLAN.md",
    "docs/companies/marceau-solutions/BUSINESS-MODEL-OPTIONS-ANALYSIS.md": "docs/BUSINESS-MODEL-OPTIONS-ANALYSIS.md",
    "docs/companies/marceau-solutions/COST-BUDGET-TRACKING-JAN-19-2026.md": "docs/COST-BUDGET-TRACKING-JAN-19-2026.md",
    "docs/companies/marceau-solutions/EXECUTION-PLAN-WEEK-JAN-19-2026.md": "docs/EXECUTION-PLAN-WEEK-JAN-19-2026.md",
    "docs/companies/marceau-solutions/LEAD-TRACKING-FOLLOWUP-SYSTEM.md": "docs/LEAD-TRACKING-FOLLOWUP-SYSTEM.md",
    "docs/companies/marceau-solutions/MAKE-MONEY-FIRST-STRATEGY-JAN-19-2026.md": "docs/MAKE-MONEY-FIRST-STRATEGY-JAN-19-2026.md",
    "docs/companies/marceau-solutions/ACTUAL-COSTS-AND-LEADS-STATUS-JAN-19-2026.md": "docs/ACTUAL-COSTS-AND-LEADS-STATUS-JAN-19-2026.md",
    "docs/companies/marceau-solutions/ACTION-ITEMS-JAN-20-2026.md": "docs/ACTION-ITEMS-JAN-20-2026.md",
    "docs/companies/marceau-solutions/EXECUTION-SUMMARY-JAN-19-2026.md": "docs/EXECUTION-SUMMARY-JAN-19-2026.md",
    "docs/companies/marceau-solutions/GROK-IMAGE-COLD-OUTREACH-JAN-19-2026.md": "docs/GROK-IMAGE-COLD-OUTREACH-JAN-19-2026.md",

    # SW FLORIDA HVAC DOCS
    "docs/companies/swflorida-hvac/3-PHASE-HVAC-PLAN-JAN-19-2026.md": "docs/3-PHASE-HVAC-PLAN-JAN-19-2026.md",
}

OUTPUT_ROLLBACKS = {
    # MARCEAU SOLUTIONS OUTPUTS
    "output/companies/marceau-solutions/market-analysis/AI-ASSISTANT-MCP-MARKET-ANALYSIS-2026.md": "output/AI-ASSISTANT-MCP-MARKET-ANALYSIS-2026.md",
    "output/companies/marceau-solutions/market-analysis/ai-automation-agency-market-research-2026.md": "output/ai-automation-agency-market-research-2026.md",
}

# Empty directories to remove after rollback
DIRECTORIES_TO_REMOVE = [
    "projects/shared-multi-tenant",
    "projects/marceau-solutions",
    "projects/swflorida-hvac",
    "projects/square-foot-shipping",
    "projects/global-utility",
    "projects/product-ideas",
    "projects/archived",
    "docs/companies/marceau-solutions/market-analysis",
    "docs/companies/marceau-solutions/strategy",
    "docs/companies/marceau-solutions",
    "docs/companies/swflorida-hvac",
    "docs/companies/square-foot-shipping",
    "docs/companies",
    "output/companies/marceau-solutions/market-analysis",
    "output/companies/marceau-solutions/campaigns",
    "output/companies/marceau-solutions",
    "output/companies/swflorida-hvac/campaigns",
    "output/companies/swflorida-hvac",
    "output/companies/square-foot-shipping/campaigns",
    "output/companies/square-foot-shipping",
    "output/companies",
    "templates/companies/marceau-solutions/sms",
    "templates/companies/marceau-solutions/email",
    "templates/companies/marceau-solutions/forms",
    "templates/companies/marceau-solutions",
    "templates/companies/swflorida-hvac/sms",
    "templates/companies/swflorida-hvac/email",
    "templates/companies/swflorida-hvac/forms",
    "templates/companies/swflorida-hvac",
    "templates/companies/square-foot-shipping/sms",
    "templates/companies/square-foot-shipping/email",
    "templates/companies/square-foot-shipping/forms",
    "templates/companies/square-foot-shipping",
    "templates/companies",
]

# README files to remove
README_FILES_TO_REMOVE = [
    "projects/marceau-solutions/README.md",
    "projects/swflorida-hvac/README.md",
    "projects/square-foot-shipping/README.md",
    "projects/shared-multi-tenant/README.md",
    "projects/global-utility/README.md",
    "projects/product-ideas/README.md",
]


def run_command(cmd: List[str], dry_run: bool = False) -> Tuple[bool, str]:
    """Run a shell command and return (success, output)"""
    if dry_run:
        return True, f"DRY-RUN: {' '.join(cmd)}"

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, f"ERROR: {e.stderr}"


def git_mv(old_path: Path, new_path: Path, dry_run: bool = False) -> bool:
    """Move a file/directory using git mv"""
    if not old_path.exists():
        print(f"  ⚠ SKIP: {old_path} does not exist")
        return False

    if dry_run:
        print(f"  [DRY-RUN] git mv {old_path} → {new_path}")
        return True

    # Use git mv
    success, output = run_command(["git", "mv", str(old_path), str(new_path)])
    if success:
        print(f"  ✓ Moved: {old_path} → {new_path}")
    else:
        print(f"  ✗ Failed: {old_path} - {output}")

    return success


def remove_file(path: Path, dry_run: bool = False) -> bool:
    """Remove a file using git rm"""
    if not path.exists():
        print(f"  ⚠ SKIP: {path} does not exist")
        return False

    if dry_run:
        print(f"  [DRY-RUN] git rm {path}")
        return True

    success, output = run_command(["git", "rm", str(path)])
    if success:
        print(f"  ✓ Removed: {path}")
    else:
        print(f"  ✗ Failed: {path} - {output}")

    return success


def remove_directory(path: Path, dry_run: bool = False) -> bool:
    """Remove an empty directory"""
    if not path.exists():
        return False

    if dry_run:
        print(f"  [DRY-RUN] Would remove directory: {path}")
        return True

    try:
        path.rmdir()
        print(f"  ✓ Removed directory: {path}")
        return True
    except OSError as e:
        print(f"  ⚠ Could not remove {path}: {e}")
        return False


def main(dry_run: bool = True):
    """Execute rollback"""
    print("="*80)
    print("ROLLBACK MULTI-COMPANY FOLDER STRUCTURE MIGRATION")
    print("="*80)
    print()

    if dry_run:
        print("MODE: DRY-RUN (no changes will be made)")
    else:
        print("MODE: EXECUTION (files will be moved back)")

    print()
    print(f"Base directory: {BASE_DIR}")
    print()

    os.chdir(BASE_DIR)

    # PHASE 1: Rollback projects
    print("-" * 80)
    print("PHASE 1: Rolling back projects")
    print("-" * 80)
    print()

    moved_projects = 0
    skipped_projects = 0

    for new_path, old_path in PROJECT_ROLLBACKS.items():
        new_full = BASE_DIR / new_path
        old_full = BASE_DIR / old_path

        if git_mv(new_full, old_full, dry_run):
            moved_projects += 1
        else:
            skipped_projects += 1

    print()
    print(f"Projects: {moved_projects} rolled back, {skipped_projects} skipped")
    print()

    # PHASE 2: Rollback documentation
    print("-" * 80)
    print("PHASE 2: Rolling back documentation")
    print("-" * 80)
    print()

    moved_docs = 0
    skipped_docs = 0

    for new_path, old_path in DOCS_ROLLBACKS.items():
        new_full = BASE_DIR / new_path
        old_full = BASE_DIR / old_path

        if git_mv(new_full, old_full, dry_run):
            moved_docs += 1
        else:
            skipped_docs += 1

    print()
    print(f"Docs: {moved_docs} rolled back, {skipped_docs} skipped")
    print()

    # PHASE 3: Rollback output files
    print("-" * 80)
    print("PHASE 3: Rolling back output files")
    print("-" * 80)
    print()

    moved_outputs = 0
    skipped_outputs = 0

    for new_path, old_path in OUTPUT_ROLLBACKS.items():
        new_full = BASE_DIR / new_path
        old_full = BASE_DIR / old_path

        if git_mv(new_full, old_full, dry_run):
            moved_outputs += 1
        else:
            skipped_outputs += 1

    print()
    print(f"Outputs: {moved_outputs} rolled back, {skipped_outputs} skipped")
    print()

    # PHASE 4: Remove README files
    print("-" * 80)
    print("PHASE 4: Removing company README files")
    print("-" * 80)
    print()

    removed_readmes = 0

    for readme_path in README_FILES_TO_REMOVE:
        readme_full = BASE_DIR / readme_path
        if remove_file(readme_full, dry_run):
            removed_readmes += 1

    print()
    print(f"READMEs removed: {removed_readmes}")
    print()

    # PHASE 5: Remove empty directories
    print("-" * 80)
    print("PHASE 5: Removing empty directories")
    print("-" * 80)
    print()

    removed_dirs = 0

    for dir_path in DIRECTORIES_TO_REMOVE:
        dir_full = BASE_DIR / dir_path
        if remove_directory(dir_full, dry_run):
            removed_dirs += 1

    print()
    print(f"Directories removed: {removed_dirs}")
    print()

    # SUMMARY
    print("=" * 80)
    print("ROLLBACK SUMMARY")
    print("=" * 80)
    print()
    print(f"Projects rolled back: {moved_projects} / {len(PROJECT_ROLLBACKS)}")
    print(f"Docs rolled back: {moved_docs} / {len(DOCS_ROLLBACKS)}")
    print(f"Outputs rolled back: {moved_outputs} / {len(OUTPUT_ROLLBACKS)}")
    print(f"READMEs removed: {removed_readmes}")
    print(f"Directories removed: {removed_dirs}")
    print()

    if dry_run:
        print("✓ DRY-RUN COMPLETE - No changes made")
        print()
        print("To execute rollback:")
        print("  python ralph/rollback_migration.py --execute")
    else:
        print("✓ ROLLBACK COMPLETE")
        print()
        print("Structure has been restored to original state.")
        print()
        print("Next steps:")
        print("  1. Review git status: git status")
        print("  2. Commit rollback: git add -A && git commit -m 'rollback: Revert multi-company structure'")

    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Rollback multi-company folder structure migration")
    parser.add_argument("--dry-run", action="store_true", help="Preview rollback without executing")
    parser.add_argument("--execute", action="store_true", help="Execute rollback")

    args = parser.parse_args()

    if args.execute:
        confirm = input("⚠️  Execute rollback? This will restore original structure. Type 'yes' to confirm: ")
        if confirm.lower() != "yes":
            print("Rollback cancelled.")
            sys.exit(0)
        main(dry_run=False)
    else:
        # Default to dry-run
        main(dry_run=True)
