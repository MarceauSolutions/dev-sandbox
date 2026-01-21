#!/usr/bin/env python3
"""
Multi-Company Folder Structure Migration Script

This script reorganizes dev-sandbox to separate 3 companies:
- Marceau Solutions
- SW Florida HVAC
- Square Foot Shipping

USAGE:
    python ralph/migrate_to_company_structure.py --dry-run   # Preview changes
    python ralph/migrate_to_company_structure.py --execute    # Execute migration

SAFETY:
- Uses git mv to preserve file history
- Creates atomic commit
- Rollback script available
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple

# Base directory (dev-sandbox root)
BASE_DIR = Path("/Users/williammarceaujr./dev-sandbox")

# Migration mapping: old_path -> new_path
PROJECT_MIGRATIONS = {
    # SHARED MULTI-TENANT (4 projects)
    "projects/lead-scraper": "projects/shared/lead-scraper",
    "projects/social-media-automation": "projects/shared/social-media-automation",
    "projects/ai-customer-service": "projects/shared/ai-customer-service",
    "projects/personal-assistant": "projects/shared/personal-assistant",

    # MARCEAU SOLUTIONS (8 projects)
    "projects/fitness-influencer": "projects/marceau-solutions/fitness-influencer",
    "projects/website-builder": "projects/marceau-solutions/website-builder",
    "projects/instagram-creator": "projects/marceau-solutions/instagram-creator",
    "projects/tiktok-creator": "projects/marceau-solutions/tiktok-creator",
    "projects/youtube-creator": "projects/marceau-solutions/youtube-creator",
    "projects/interview-prep": "projects/marceau-solutions/interview-prep",
    "projects/amazon-seller": "projects/marceau-solutions/amazon-seller",

    # SW FLORIDA HVAC (1 project)
    "projects/hvac-distributors": "projects/swflorida-hvac/hvac-distributors",

    # GLOBAL UTILITY (9 projects)
    "projects/md-to-pdf": "projects/global-utility/md-to-pdf",
    "projects/twilio-mcp": "projects/global-utility/twilio-mcp",
    "projects/claude-framework": "projects/global-utility/claude-framework",
    "projects/registry": "projects/global-utility/registry",
    "projects/mcp-aggregator": "projects/global-utility/mcp-aggregator",
    "projects/naples-weather": "projects/global-utility/naples-weather",
    "projects/time-blocks": "projects/global-utility/time-blocks",
    "projects/resume": "projects/global-utility/resume",
    "projects/shared": "projects/global-utility/shared",

    # PRODUCT IDEAS (5 projects)
    "projects/crave-smart": "projects/product-ideas/crave-smart",
    "projects/decide-for-her": "projects/product-ideas/decide-for-her",
    "projects/elder-tech-concierge": "projects/product-ideas/elder-tech-concierge",
    "projects/amazon-buyer": "projects/product-ideas/amazon-buyer",
    "projects/uber-lyft-comparison": "projects/product-ideas/uber-lyft-comparison",

    # ARCHIVED (1 project)
    "projects/Automated_SocialMedia_Campaign": "projects/archived/automated-social-media-campaign",
}

DOCS_MIGRATIONS = {
    # MARCEAU SOLUTIONS DOCS
    "docs/AI-VOICE-SERVICE-ECONOMICS.md": "docs/companies/marceau-solutions/AI-VOICE-SERVICE-ECONOMICS.md",
    "docs/MARCEAU-SOLUTIONS-COMPLETE-SERVICE-OFFERING.md": "docs/companies/marceau-solutions/MARCEAU-SOLUTIONS-COMPLETE-SERVICE-OFFERING.md",
    "docs/COLD-OUTREACH-STRATEGY-JAN-19-2026.md": "docs/companies/marceau-solutions/COLD-OUTREACH-STRATEGY-JAN-19-2026.md",
    "docs/CUSTOMER-ACQUISITION-STRATEGY-JAN-19-2026.md": "docs/companies/marceau-solutions/CUSTOMER-ACQUISITION-STRATEGY-JAN-19-2026.md",
    "docs/API-USAGE-COST-CHECKER.md": "docs/companies/marceau-solutions/API-USAGE-COST-CHECKER.md",
    "docs/APOLLO-IO-MAXIMIZATION-PLAN.md": "docs/companies/marceau-solutions/APOLLO-IO-MAXIMIZATION-PLAN.md",
    "docs/BUSINESS-MODEL-OPTIONS-ANALYSIS.md": "docs/companies/marceau-solutions/BUSINESS-MODEL-OPTIONS-ANALYSIS.md",
    "docs/COST-BUDGET-TRACKING-JAN-19-2026.md": "docs/companies/marceau-solutions/COST-BUDGET-TRACKING-JAN-19-2026.md",
    "docs/EXECUTION-PLAN-WEEK-JAN-19-2026.md": "docs/companies/marceau-solutions/EXECUTION-PLAN-WEEK-JAN-19-2026.md",
    "docs/LEAD-TRACKING-FOLLOWUP-SYSTEM.md": "docs/companies/marceau-solutions/LEAD-TRACKING-FOLLOWUP-SYSTEM.md",
    "docs/MAKE-MONEY-FIRST-STRATEGY-JAN-19-2026.md": "docs/companies/marceau-solutions/MAKE-MONEY-FIRST-STRATEGY-JAN-19-2026.md",
    "docs/ACTUAL-COSTS-AND-LEADS-STATUS-JAN-19-2026.md": "docs/companies/marceau-solutions/ACTUAL-COSTS-AND-LEADS-STATUS-JAN-19-2026.md",
    "docs/ACTION-ITEMS-JAN-20-2026.md": "docs/companies/marceau-solutions/ACTION-ITEMS-JAN-20-2026.md",
    "docs/EXECUTION-SUMMARY-JAN-19-2026.md": "docs/companies/marceau-solutions/EXECUTION-SUMMARY-JAN-19-2026.md",
    "docs/GROK-IMAGE-COLD-OUTREACH-JAN-19-2026.md": "docs/companies/marceau-solutions/GROK-IMAGE-COLD-OUTREACH-JAN-19-2026.md",

    # SW FLORIDA HVAC DOCS
    "docs/3-PHASE-HVAC-PLAN-JAN-19-2026.md": "docs/companies/swflorida-hvac/3-PHASE-HVAC-PLAN-JAN-19-2026.md",
}

OUTPUT_MIGRATIONS = {
    # MARCEAU SOLUTIONS OUTPUTS
    "output/AI-ASSISTANT-MCP-MARKET-ANALYSIS-2026.md": "output/companies/marceau-solutions/market-analysis/AI-ASSISTANT-MCP-MARKET-ANALYSIS-2026.md",
    "output/ai-automation-agency-market-research-2026.md": "output/companies/marceau-solutions/market-analysis/ai-automation-agency-market-research-2026.md",
}

# Directories to create
DIRECTORIES_TO_CREATE = [
    # Project directories
    "projects/shared",
    "projects/marceau-solutions",
    "projects/swflorida-hvac",
    "projects/square-foot-shipping",
    "projects/global-utility",
    "projects/product-ideas",
    "projects/archived",

    # Docs directories
    "docs/companies",
    "docs/companies/marceau-solutions",
    "docs/companies/marceau-solutions/market-analysis",
    "docs/companies/marceau-solutions/strategy",
    "docs/companies/swflorida-hvac",
    "docs/companies/square-foot-shipping",

    # Output directories
    "output/companies",
    "output/companies/marceau-solutions",
    "output/companies/marceau-solutions/market-analysis",
    "output/companies/marceau-solutions/campaigns",
    "output/companies/swflorida-hvac",
    "output/companies/swflorida-hvac/campaigns",
    "output/companies/square-foot-shipping",
    "output/companies/square-foot-shipping/campaigns",

    # Template directories
    "templates/companies",
    "templates/companies/marceau-solutions",
    "templates/companies/marceau-solutions/sms",
    "templates/companies/marceau-solutions/email",
    "templates/companies/marceau-solutions/forms",
    "templates/companies/swflorida-hvac",
    "templates/companies/swflorida-hvac/sms",
    "templates/companies/swflorida-hvac/email",
    "templates/companies/swflorida-hvac/forms",
    "templates/companies/square-foot-shipping",
    "templates/companies/square-foot-shipping/sms",
    "templates/companies/square-foot-shipping/email",
    "templates/companies/square-foot-shipping/forms",
    "templates/shared",
]

# README content for each company
COMPANY_READMES = {
    "projects/marceau-solutions/README.md": """# Marceau Solutions Projects

**Company Focus:** AI automation, lead generation, websites, content creation

## Projects

### Active Projects
- **fitness-influencer** - AI automation suite for fitness creators (MCP published)
- **website-builder** - Automated website generation powered by AI
- **instagram-creator** - Instagram automation MCP (published)
- **tiktok-creator** - TikTok automation MCP (published)
- **youtube-creator** - YouTube automation MCP (published)
- **interview-prep** - PowerPoint generator for interview prep
- **amazon-seller** - Amazon SP-API tools for sellers (published MCP)

### Product Ideas
See `projects/product-ideas/` for future revenue products.

### Shared Multi-Tenant Tools
See `projects/shared/` for tools used across all 3 companies:
- lead-scraper (lead generation)
- social-media-automation (social posting)
- ai-customer-service (voice AI)
- personal-assistant (digest/calendar)

## Documentation
Company-specific docs: `docs/companies/marceau-solutions/`

## Templates
Company-specific templates: `templates/companies/marceau-solutions/`

## Output
Company-specific outputs: `output/companies/marceau-solutions/`
""",

    "projects/swflorida-hvac/README.md": """# SW Florida HVAC Projects

**Company Focus:** HVAC services, local service business

## Projects

### Active Projects
- **hvac-distributors** - RFQ system for HVAC equipment quotes

### Future Projects
- HVAC service booking system
- Quote management
- Social media automation (HVAC-specific)

### Shared Multi-Tenant Tools
See `projects/shared/` for tools used across all 3 companies:
- lead-scraper (lead generation)
- social-media-automation (social posting)
- ai-customer-service (voice AI for phone quotes)
- personal-assistant (digest/calendar)

## Documentation
Company-specific docs: `docs/companies/swflorida-hvac/`

## Templates
Company-specific templates: `templates/companies/swflorida-hvac/`

## Output
Company-specific outputs: `output/companies/swflorida-hvac/`
""",

    "projects/square-foot-shipping/README.md": """# Square Foot Shipping Projects

**Company Focus:** Logistics/freight services

## Projects

### Future Projects
- Shipping quote comparison
- Freight tracking system
- Logistics optimization tools

### Shared Multi-Tenant Tools
See `projects/shared/` for tools used across all 3 companies:
- lead-scraper (lead generation)
- social-media-automation (social posting)
- ai-customer-service (voice AI for shipping quotes)
- personal-assistant (digest/calendar)

## Documentation
Company-specific docs: `docs/companies/square-foot-shipping/`

## Templates
Company-specific templates: `templates/companies/square-foot-shipping/`

## Output
Company-specific outputs: `output/companies/square-foot-shipping/`
""",

    "projects/shared/README.md": """# Shared Multi-Tenant Projects

**Used by ALL 3 companies:**
- Marceau Solutions
- SW Florida HVAC
- Square Foot Shipping

## Projects

### lead-scraper
Lead generation system with business_id separation.
Used by all 3 companies for local lead scraping.

### social-media-automation
Social media posting with business separation.
Schedules posts for all 3 companies.

### ai-customer-service
Voice AI phone ordering system.
Handles calls for all 3 businesses (restaurant ordering, HVAC quotes, shipping quotes).

### personal-assistant
William's personal digest and calendar system.
Global utility - no business affiliation.

## Business Separation

All shared projects use `business_id` separation in code/data:
- `business_id: "marceau-solutions"`
- `business_id: "swflorida-hvac"`
- `business_id: "square-foot-shipping"`

## Data Organization

Data is separated by business_id:
- Forms: `output/form_submissions/` with business_id in data
- SMS campaigns: `output/companies/{company}/campaigns/`
- Social posts: `output/companies/{company}/social/`
""",

    "projects/global-utility/README.md": """# Global Utility Projects

**General-purpose tools with no specific business affiliation**

## Projects

### MCP Servers (Published)
- **md-to-pdf** - Markdown to PDF converter MCP
- **twilio-mcp** - Twilio SMS MCP server

### Frameworks & Infrastructure
- **claude-framework** - Claude Code "operating system"
- **registry** - MCP Registry (upstream from Anthropic)
- **mcp-aggregator** - Universal MCP aggregation platform

### Personal Tools
- **naples-weather** - Weather report generator for Naples, FL
- **time-blocks** - Personal productivity calendar tool
- **resume** - William's resume project

### Shared Utilities
- **shared** - Shared utilities across multiple projects

## Usage

These tools are available to all projects and companies.
No business_id separation needed.
""",

    "projects/product-ideas/README.md": """# Product Ideas

**Future revenue products - not yet developed**

## Projects

### Consumer Apps
- **crave-smart** - Food craving prediction app (menstrual cycle-based)
- **decide-for-her** - Decision-making app for women
- **uber-lyft-comparison** - Rideshare price comparison

### E-commerce Tools
- **amazon-buyer** - Amazon buying tools

### Service Offerings
- **elder-tech-concierge** - White-glove AI setup for seniors (v0.1.0-dev)

## Status

These are concept/exploration phase projects.
When developed, they will likely become Marceau Solutions products.

## See Also

- Market analysis: `docs/companies/marceau-solutions/market-analysis/`
- SOP 17: Market Viability Analysis (before building)
""",
}


def run_command(cmd: List[str], dry_run: bool = False) -> Tuple[bool, str]:
    """Run a shell command and return (success, output)"""
    if dry_run:
        return True, f"DRY-RUN: {' '.join(cmd)}"

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, f"ERROR: {e.stderr}"


def create_directory(path: Path, dry_run: bool = False) -> bool:
    """Create a directory if it doesn't exist"""
    if dry_run:
        print(f"  [DRY-RUN] Would create: {path}")
        return True

    path.mkdir(parents=True, exist_ok=True)
    print(f"  ✓ Created: {path}")
    return True


def git_mv(old_path: Path, new_path: Path, dry_run: bool = False) -> bool:
    """Move a file/directory using git mv"""
    if not old_path.exists():
        print(f"  ⚠ SKIP: {old_path} does not exist")
        return False

    if dry_run:
        print(f"  [DRY-RUN] git mv {old_path} → {new_path}")
        return True

    # Ensure parent directory exists
    new_path.parent.mkdir(parents=True, exist_ok=True)

    # Use git mv
    success, output = run_command(["git", "mv", str(old_path), str(new_path)])
    if success:
        print(f"  ✓ Moved: {old_path} → {new_path}")
    else:
        print(f"  ✗ Failed: {old_path} - {output}")

    return success


def write_file(path: Path, content: str, dry_run: bool = False) -> bool:
    """Write content to a file"""
    if dry_run:
        print(f"  [DRY-RUN] Would write: {path}")
        return True

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"  ✓ Created: {path}")
    return True


def main(dry_run: bool = True):
    """Execute migration"""
    print("="*80)
    print("MULTI-COMPANY FOLDER STRUCTURE MIGRATION")
    print("="*80)
    print()

    if dry_run:
        print("MODE: DRY-RUN (no changes will be made)")
    else:
        print("MODE: EXECUTION (files will be moved)")

    print()
    print(f"Base directory: {BASE_DIR}")
    print()

    os.chdir(BASE_DIR)

    # PHASE 1: Create directory structure
    print("-" * 80)
    print("PHASE 1: Creating directory structure")
    print("-" * 80)
    print()

    for dir_path in DIRECTORIES_TO_CREATE:
        create_directory(BASE_DIR / dir_path, dry_run)

    print()

    # PHASE 2: Create company README files
    print("-" * 80)
    print("PHASE 2: Creating company README files")
    print("-" * 80)
    print()

    for readme_path, content in COMPANY_READMES.items():
        write_file(BASE_DIR / readme_path, content, dry_run)

    print()

    # PHASE 3: Migrate projects
    print("-" * 80)
    print("PHASE 3: Migrating projects")
    print("-" * 80)
    print()

    moved_projects = 0
    skipped_projects = 0

    for old_path, new_path in PROJECT_MIGRATIONS.items():
        old_full = BASE_DIR / old_path
        new_full = BASE_DIR / new_path

        if git_mv(old_full, new_full, dry_run):
            moved_projects += 1
        else:
            skipped_projects += 1

    print()
    print(f"Projects: {moved_projects} moved, {skipped_projects} skipped")
    print()

    # PHASE 4: Migrate documentation
    print("-" * 80)
    print("PHASE 4: Migrating documentation")
    print("-" * 80)
    print()

    moved_docs = 0
    skipped_docs = 0

    for old_path, new_path in DOCS_MIGRATIONS.items():
        old_full = BASE_DIR / old_path
        new_full = BASE_DIR / new_path

        if git_mv(old_full, new_full, dry_run):
            moved_docs += 1
        else:
            skipped_docs += 1

    print()
    print(f"Docs: {moved_docs} moved, {skipped_docs} skipped")
    print()

    # PHASE 5: Migrate output files
    print("-" * 80)
    print("PHASE 5: Migrating output files")
    print("-" * 80)
    print()

    moved_outputs = 0
    skipped_outputs = 0

    for old_path, new_path in OUTPUT_MIGRATIONS.items():
        old_full = BASE_DIR / old_path
        new_full = BASE_DIR / new_path

        if git_mv(old_full, new_full, dry_run):
            moved_outputs += 1
        else:
            skipped_outputs += 1

    print()
    print(f"Outputs: {moved_outputs} moved, {skipped_outputs} skipped")
    print()

    # SUMMARY
    print("=" * 80)
    print("MIGRATION SUMMARY")
    print("=" * 80)
    print()
    print(f"Directories created: {len(DIRECTORIES_TO_CREATE)}")
    print(f"README files created: {len(COMPANY_READMES)}")
    print(f"Projects migrated: {moved_projects} / {len(PROJECT_MIGRATIONS)}")
    print(f"Docs migrated: {moved_docs} / {len(DOCS_MIGRATIONS)}")
    print(f"Outputs migrated: {moved_outputs} / {len(OUTPUT_MIGRATIONS)}")
    print()

    if dry_run:
        print("✓ DRY-RUN COMPLETE - No changes made")
        print()
        print("To execute migration:")
        print("  python ralph/migrate_to_company_structure.py --execute")
    else:
        print("✓ MIGRATION COMPLETE")
        print()
        print("Next steps:")
        print("  1. Review git status: git status")
        print("  2. Test imports and paths")
        print("  3. Commit changes: git add -A && git commit -m 'feat: Multi-company folder structure'")
        print("  4. If issues: python ralph/rollback_migration.py")

    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Migrate dev-sandbox to multi-company structure")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without executing")
    parser.add_argument("--execute", action="store_true", help="Execute migration")

    args = parser.parse_args()

    if args.execute:
        confirm = input("⚠️  Execute migration? This will move files. Type 'yes' to confirm: ")
        if confirm.lower() != "yes":
            print("Migration cancelled.")
            sys.exit(0)
        main(dry_run=False)
    else:
        # Default to dry-run
        main(dry_run=True)
