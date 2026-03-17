#!/bin/bash
# Add Project to Company Folder Script
# Adds new projects to an existing company folder
# See Build Taxonomy in CLAUDE.md for definitions of each subtype

set -e  # Exit on error

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: ./add-company-project.sh \"company-folder-name\" \"project-name\" [subtype]"
    echo
    echo "Examples:"
    echo "  ./add-company-project.sh marceau-solutions \"email-analyzer\" project"
    echo "  ./add-company-project.sh marceau-solutions \"daily-digest\" automation"
    echo "  ./add-company-project.sh marceau-solutions \"onboarding\" ops"
    echo "  ./add-company-project.sh marceau-solutions \"price-compare\" mcp"
    echo
    echo "Subtypes (see Build Taxonomy in CLAUDE.md):"
    echo "  - project    : (default) Company Project — multi-file codebase"
    echo "  - automation : Scheduled/triggered process (n8n, cron, webhook)"
    echo "  - ops        : Business Ops — primarily workflows/documentation"
    echo "  - mcp        : MCP Server — Model Context Protocol server"
    exit 1
fi

COMPANY_FOLDER="$1"
PROJECT_NAME="$2"
PROJECT_TYPE="${3:-project}"  # Default to "project" if not specified

COMPANY_DIR="/Users/williammarceaujr./dev-sandbox/projects/$COMPANY_FOLDER"
PROJECT_DIR="$COMPANY_DIR/$PROJECT_NAME"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Adding Project: $PROJECT_NAME"
echo "║  To Company: $COMPANY_FOLDER"
echo "║  Subtype: $PROJECT_TYPE"
echo "╚════════════════════════════════════════════════════════════════╝"
echo

# Check if company folder exists
if [ ! -d "$COMPANY_DIR" ]; then
    echo "❌ Error: Company folder does not exist: $COMPANY_DIR"
    echo "   Create it first with: ./create-company-folder.sh"
    exit 1
fi

# Check if project already exists
if [ -d "$PROJECT_DIR" ]; then
    echo "❌ Error: Project already exists: $PROJECT_DIR"
    exit 1
fi

# Create project directory structure based on subtype
echo "Creating project structure for subtype: $PROJECT_TYPE"
mkdir -p "$PROJECT_DIR"

case "$PROJECT_TYPE" in
    project|automation)
        # Standard project structure (Company Project or Automation)
        mkdir -p "$PROJECT_DIR/src"
        mkdir -p "$PROJECT_DIR/workflows"

        # Create VERSION file
        echo "1.0.0-dev" > "$PROJECT_DIR/VERSION"

        # Create CHANGELOG
        cat > "$PROJECT_DIR/CHANGELOG.md" <<EOF
# Changelog

All notable changes to $PROJECT_NAME will be documented here.

## [Unreleased]

### Added
- Initial project structure

---

Format based on [Keep a Changelog](https://keepachangelog.com/)
EOF

        # Create README
        cat > "$PROJECT_DIR/README.md" <<EOF
# $PROJECT_NAME

**Company**: $COMPANY_FOLDER
**Subtype**: $PROJECT_TYPE (see Build Taxonomy in CLAUDE.md)
**Status**: Development
**Version**: 1.0.0-dev

## Overview

[Brief description of what this project does]

## Usage

\`\`\`bash
cd projects/$COMPANY_FOLDER/$PROJECT_NAME
python -m src.main
\`\`\`

## Directory Structure

\`\`\`
$PROJECT_NAME/
├── src/                 # Python source code
├── workflows/           # Task procedures (markdown)
├── VERSION              # Current version
├── CHANGELOG.md         # Version history
└── README.md            # This file
\`\`\`

---

**Documentation**: See [docs/FOLDER-STRUCTURE-GUIDE.md](../../../docs/FOLDER-STRUCTURE-GUIDE.md)
EOF

        # Create placeholder main.py
        cat > "$PROJECT_DIR/src/main.py" <<EOF
#!/usr/bin/env python3
"""
$PROJECT_NAME - Main Entry Point

Company: $COMPANY_FOLDER
Subtype: $PROJECT_TYPE
"""

def main():
    """Main entry point for $PROJECT_NAME"""
    print("$PROJECT_NAME is running!")
    print("Company: $COMPANY_FOLDER")
    print("Subtype: $PROJECT_TYPE")

if __name__ == "__main__":
    main()
EOF

        chmod +x "$PROJECT_DIR/src/main.py"

        echo "✅ Created $PROJECT_TYPE structure"
        ;;

    ops)
        # Business Ops structure (documentation-focused, minimal code)
        mkdir -p "$PROJECT_DIR/workflows"

        cat > "$PROJECT_DIR/README.md" <<EOF
# $PROJECT_NAME

**Company**: $COMPANY_FOLDER
**Subtype**: ops (Business Ops — see Build Taxonomy in CLAUDE.md)

## Overview

Collection of documented procedures and workflows for $PROJECT_NAME operations.

## Workflows

- [ ] [workflow-1.md](workflows/workflow-1.md) - Description

## Workflow Template

See [docs/workflow-standard.md](../../../docs/workflow-standard.md) for standard workflow format.
EOF

        cat > "$PROJECT_DIR/workflows/example-workflow.md" <<EOF
# Workflow: [Name]

**Created**: $(date +%Y-%m-%d)
**Company**: $COMPANY_FOLDER
**Project**: $PROJECT_NAME

## Overview
[What this workflow does]

## Prerequisites
- [ ] Prerequisite 1

## Steps

### Step 1: [Name]
**Objective**: [What this step achieves]

**Actions**:
1. Action 1
2. Action 2

**Verification**: You should see...

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| [Issue] | [Cause] | [Solution] |

## Success Criteria
- [ ] Criterion 1
EOF

        echo "✅ Created ops (Business Ops) structure"
        ;;

    mcp)
        # MCP Server structure
        mkdir -p "$PROJECT_DIR/src/${PROJECT_NAME//-/_}_mcp"
        mkdir -p "$PROJECT_DIR/workflows"

        echo "1.0.0" > "$PROJECT_DIR/VERSION"

        cat > "$PROJECT_DIR/README.md" <<EOF
# $PROJECT_NAME MCP Server

**Company**: $COMPANY_FOLDER
**Subtype**: mcp (MCP Server — see Build Taxonomy in CLAUDE.md)

## Overview

[Description of what this MCP server provides]

## Installation

\`\`\`bash
pip install ${PROJECT_NAME}-mcp
\`\`\`

## Usage

Add to Claude Desktop config:

\`\`\`json
{
  "mcpServers": {
    "$PROJECT_NAME": {
      "command": "python",
      "args": ["-m", "${PROJECT_NAME//-/_}_mcp.server"]
    }
  }
}
\`\`\`

## Tools Provided

- \`tool_1\`: Description

---

**Publishing**: Follow SOPs 11-14 in CLAUDE.md to publish as MCP Package
EOF

        # Create minimal MCP server
        cat > "$PROJECT_DIR/src/${PROJECT_NAME//-/_}_mcp/__init__.py" <<EOF
__version__ = "1.0.0"

from .server import mcp
EOF

        cat > "$PROJECT_DIR/src/${PROJECT_NAME//-/_}_mcp/server.py" <<EOF
#!/usr/bin/env python3
"""
$PROJECT_NAME MCP Server

Company: $COMPANY_FOLDER
"""

from mcp.server.stdio import stdio_server
from mcp.types import Tool

mcp = stdio_server(__name__)

@mcp.tool()
def example_tool(text: str) -> str:
    """Example MCP tool"""
    return f"Processed: {text}"

if __name__ == "__main__":
    import asyncio
    asyncio.run(mcp.run())
EOF

        chmod +x "$PROJECT_DIR/src/${PROJECT_NAME//-/_}_mcp/server.py"

        echo "✅ Created MCP Server structure"
        ;;

    *)
        echo "❌ Unknown subtype: $PROJECT_TYPE"
        echo "   Valid subtypes: project, automation, ops, mcp"
        echo "   See Build Taxonomy in CLAUDE.md for definitions"
        exit 1
        ;;
esac

echo
echo "✅ Project created: $PROJECT_DIR/"
echo

echo "Next steps:"
echo "───────────"
case "$PROJECT_TYPE" in
    project|automation)
        echo "1. Implement functionality in src/"
        echo "2. Add workflows in workflows/"
        echo "3. Test your implementation"
        echo "4. Update VERSION and CHANGELOG.md before deploying"
        ;;
    ops)
        echo "1. Document procedures in workflows/"
        echo "2. Reference from company README or other projects"
        ;;
    mcp)
        echo "1. Implement MCP tools in src/${PROJECT_NAME//-/_}_mcp/server.py"
        echo "2. Test locally with Claude Desktop"
        echo "3. Follow SOPs 11-14 to publish as MCP Package"
        ;;
esac

echo
echo "Commit to dev-sandbox:"
echo "    git add projects/$COMPANY_FOLDER/$PROJECT_NAME"
echo "    git commit -m \"feat($COMPANY_FOLDER): Add $PROJECT_NAME ($PROJECT_TYPE)\""
echo "    git push origin main"
echo
echo "✅ Done!"
