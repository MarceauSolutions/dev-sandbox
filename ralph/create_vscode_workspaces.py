#!/usr/bin/env python3
"""
Generate VSCode workspace files for common development scenarios.

Run after migration to create pre-configured workspace files.

Usage:
    python ralph/create_vscode_workspaces.py
"""

import json
from pathlib import Path

# Base directory
DEV_SANDBOX = Path(__file__).parent.parent

def create_workspace(name, folders, settings=None):
    """Create a VSCode workspace file."""
    workspace = {
        "folders": folders,
        "settings": settings or {
            "files.exclude": {
                "**/__pycache__": True,
                "**/.pytest_cache": True,
                "**/node_modules": True,
                "**/.DS_Store": True
            },
            "search.exclude": {
                "**/archived": True
            }
        }
    }

    filepath = DEV_SANDBOX / f"{name}.code-workspace"
    with open(filepath, 'w') as f:
        json.dump(workspace, f, indent=2)

    print(f"✅ Created: {filepath.name}")

def main():
    print("Creating VSCode workspace files...\n")

    # 1. All Companies (Multi-root)
    create_workspace(
        "dev-sandbox-all-companies",
        [
            {"name": "🌐 Shared (Multi-Tenant)", "path": "projects/shared-multi-tenant"},
            {"name": "🎯 Marceau Solutions", "path": "projects/marceau-solutions"},
            {"name": "❄️ SW Florida HVAC", "path": "projects/swflorida-hvac"},
            {"name": "📦 Square Foot Shipping", "path": "projects/square-foot-shipping"},
            {"name": "🔧 Global Utilities", "path": "projects/global-utility"},
            {"name": "💡 Product Ideas", "path": "projects/product-ideas"},
            {"name": "📚 Infrastructure", "path": "."}
        ]
    )

    # 2. Marceau-only
    create_workspace(
        "dev-sandbox-marceau",
        [
            {"name": "Marceau Projects", "path": "projects/marceau-solutions"},
            {"name": "Shared Systems", "path": "projects/shared-multi-tenant"},
            {"name": "Infrastructure", "path": "."}
        ]
    )

    # 3. Shared Systems (lead-scraper, social, voice AI)
    create_workspace(
        "dev-sandbox-shared",
        [
            {"name": "Shared Multi-Tenant", "path": "projects/shared-multi-tenant"},
            {"name": "Infrastructure", "path": "."}
        ]
    )

    # 4. Infrastructure-only (docs, SOPs, deploy)
    create_workspace(
        "dev-sandbox-infrastructure",
        [
            {"name": "Documentation", "path": "docs"},
            {"name": "Directives", "path": "directives"},
            {"name": "Methods", "path": "methods"},
            {"name": "Execution", "path": "execution"},
            {"name": "Root", "path": "."}
        ]
    )

    # 5. Campaign Management (all 3 businesses)
    create_workspace(
        "dev-sandbox-campaigns",
        [
            {"name": "Lead Scraper (Shared)", "path": "projects/shared-multi-tenant/lead-scraper"},
            {"name": "Social Media (Shared)", "path": "projects/shared-multi-tenant/social-media-automation"},
            {"name": "Voice AI (Shared)", "path": "projects/shared-multi-tenant/ai-customer-service"},
            {"name": "Infrastructure", "path": "."}
        ]
    )

    print("\n📁 Workspace files created!")
    print("\nUsage:")
    print("  1. Open VSCode")
    print("  2. File → Open Workspace from File...")
    print("  3. Choose the workspace that matches your task:")
    print("     - dev-sandbox-all-companies.code-workspace → Multi-company work")
    print("     - dev-sandbox-marceau.code-workspace → Marceau-focused")
    print("     - dev-sandbox-shared.code-workspace → Shared systems")
    print("     - dev-sandbox-infrastructure.code-workspace → Docs/SOPs")
    print("     - dev-sandbox-campaigns.code-workspace → Campaign management")
    print("\nOr use command line:")
    print("  code dev-sandbox-marceau.code-workspace")

if __name__ == "__main__":
    main()
