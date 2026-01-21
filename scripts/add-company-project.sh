#!/bin/bash
# Add Project to Company Folder Script
# Adds new projects, tools, or products to an existing company folder

set -e  # Exit on error

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: ./add-company-project.sh \"company-folder-name\" \"project-name\" [type]"
    echo
    echo "Examples:"
    echo "  ./add-company-project.sh naples-dental-group \"lead-automation\" tool"
    echo "  ./add-company-project.sh marceau-solutions \"email-analyzer\" product"
    echo "  ./add-company-project.sh swflorida-hvac \"voice-ai-backend\" service"
    echo
    echo "Types (optional):"
    echo "  - tool       : Automation tool or internal utility"
    echo "  - product    : Customer-facing product/service"
    echo "  - service    : Backend service or API"
    echo "  - workflow   : Documented procedure or process"
    echo "  - mcp        : MCP server integration"
    exit 1
fi

COMPANY_FOLDER="$1"
PROJECT_NAME="$2"
PROJECT_TYPE="${3:-tool}"  # Default to "tool" if not specified

COMPANY_DIR="/Users/williammarceaujr./dev-sandbox/projects/$COMPANY_FOLDER"
PROJECT_DIR="$COMPANY_DIR/$PROJECT_NAME"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Adding Project: $PROJECT_NAME"
echo "║  To Company: $COMPANY_FOLDER"
echo "║  Type: $PROJECT_TYPE"
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

# Create project directory structure based on type
echo "Creating project structure for type: $PROJECT_TYPE"
mkdir -p "$PROJECT_DIR"

case "$PROJECT_TYPE" in
    tool|product|service)
        # Standard project structure
        mkdir -p "$PROJECT_DIR/src"
        mkdir -p "$PROJECT_DIR/workflows"
        mkdir -p "$PROJECT_DIR/tests"
        mkdir -p "$PROJECT_DIR/output"

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
**Type**: $PROJECT_TYPE
**Status**: Development
**Version**: 1.0.0-dev

## Overview

[Brief description of what this $PROJECT_TYPE does]

## Features

- [ ] Feature 1
- [ ] Feature 2
- [ ] Feature 3

## Usage

\`\`\`bash
# How to use this $PROJECT_TYPE
cd projects/$COMPANY_FOLDER/$PROJECT_NAME
python -m src.main
\`\`\`

## Directory Structure

\`\`\`
$PROJECT_NAME/
├── src/                 # Python source code
├── workflows/           # Task procedures (markdown)
├── tests/               # Unit and integration tests
├── output/              # Generated outputs
├── VERSION              # Current version
├── CHANGELOG.md         # Version history
└── README.md            # This file
\`\`\`

## Dependencies

[List any dependencies or requirements]

## Development

[Development notes, how to contribute, etc.]

---

**Documentation**: See [docs/FOLDER-STRUCTURE-GUIDE-UPDATED.md](../../../docs/FOLDER-STRUCTURE-GUIDE-UPDATED.md)
EOF

        # Create placeholder main.py
        cat > "$PROJECT_DIR/src/main.py" <<EOF
#!/usr/bin/env python3
"""
$PROJECT_NAME - Main Entry Point

Company: $COMPANY_FOLDER
Type: $PROJECT_TYPE
"""

def main():
    """Main entry point for $PROJECT_NAME"""
    print("$PROJECT_NAME is running!")
    print("Company: $COMPANY_FOLDER")
    print("Type: $PROJECT_TYPE")

if __name__ == "__main__":
    main()
EOF

        chmod +x "$PROJECT_DIR/src/main.py"

        echo "✅ Created standard project structure"
        ;;

    workflow)
        # Workflow structure (documentation-focused)
        mkdir -p "$PROJECT_DIR"

        cat > "$PROJECT_DIR/README.md" <<EOF
# $PROJECT_NAME Workflows

**Company**: $COMPANY_FOLDER
**Type**: Documented Procedures

## Overview

Collection of documented procedures and workflows for $PROJECT_NAME operations.

## Workflows

- [ ] [workflow-1.md](workflow-1.md) - Description
- [ ] [workflow-2.md](workflow-2.md) - Description

## Workflow Template

See [docs/workflow-standard.md](../../../docs/workflow-standard.md) for standard workflow format.
EOF

        cat > "$PROJECT_DIR/example-workflow.md" <<EOF
# Workflow: [Name]

**Created**: $(date +%Y-%m-%d)
**Company**: $COMPANY_FOLDER
**Project**: $PROJECT_NAME

## Overview
[What this workflow does]

## Prerequisites
- [ ] Prerequisite 1
- [ ] Prerequisite 2

## Steps

### Step 1: [Name]
**Objective**: [What this step achieves]

**Actions**:
1. Action 1
2. Action 2

**Verification**: ✅ You should see...

### Step 2: [Name]
[Repeat structure]

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| [Issue] | [Cause] | [Solution] |

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2
EOF

        echo "✅ Created workflow structure"
        ;;

    mcp)
        # MCP server structure
        mkdir -p "$PROJECT_DIR/src/${PROJECT_NAME//-/_}_mcp"
        mkdir -p "$PROJECT_DIR/workflows"

        echo "1.0.0" > "$PROJECT_DIR/VERSION"

        cat > "$PROJECT_DIR/README.md" <<EOF
# $PROJECT_NAME MCP Server

**Company**: $COMPANY_FOLDER
**Type**: Model Context Protocol Server

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
- \`tool_2\`: Description

## Resources

[Any resources this MCP exposes]

---

**MCP Documentation**: See SOPs 11-14 in CLAUDE.md
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

        echo "✅ Created MCP server structure"
        ;;

    *)
        echo "❌ Unknown project type: $PROJECT_TYPE"
        echo "   Valid types: tool, product, service, workflow, mcp"
        exit 1
        ;;
esac

echo
echo "✅ Project created: $PROJECT_DIR/"
echo

echo "Next steps:"
echo "───────────"
case "$PROJECT_TYPE" in
    tool|product|service)
        echo "1. Implement functionality in src/"
        echo "2. Add workflows in workflows/"
        echo "3. Test your implementation"
        echo "4. Update VERSION and CHANGELOG.md before deploying"
        ;;
    workflow)
        echo "1. Document procedures in workflow markdown files"
        echo "2. Reference from company README or other projects"
        ;;
    mcp)
        echo "1. Implement MCP tools in src/${PROJECT_NAME//-/_}_mcp/server.py"
        echo "2. Test locally with Claude Desktop"
        echo "3. Follow SOPs 11-14 to publish to PyPI and MCP Registry"
        ;;
esac

echo
echo "5. Commit to dev-sandbox:"
echo "    git add projects/$COMPANY_FOLDER/$PROJECT_NAME"
echo "    git commit -m \"feat($COMPANY_FOLDER): Add $PROJECT_NAME ($PROJECT_TYPE)\""
echo "    git push origin main"
echo
echo "✅ Done!"
