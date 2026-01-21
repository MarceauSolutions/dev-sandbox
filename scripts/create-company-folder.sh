#!/bin/bash
# Create Company Folder Script
# Ensures consistent company-centric folder structure for all new companies

set -e  # Exit on error

if [ -z "$1" ]; then
    echo "Usage: ./create-company-folder.sh \"Company Name\""
    echo "Example: ./create-company-folder.sh \"Naples Dental Group\""
    exit 1
fi

COMPANY_NAME="$1"
# Convert to folder name (lowercase, spaces to hyphens)
FOLDER_NAME=$(echo "$COMPANY_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')

COMPANY_DIR="/Users/williammarceaujr./dev-sandbox/projects/$FOLDER_NAME"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Creating Company Folder: $COMPANY_NAME"
echo "╚════════════════════════════════════════════════════════════════╝"
echo

# Check if folder already exists
if [ -d "$COMPANY_DIR" ]; then
    echo "❌ Error: Company folder already exists at $COMPANY_DIR"
    exit 1
fi

# Create company directory
echo "Creating directory: projects/$FOLDER_NAME/"
mkdir -p "$COMPANY_DIR"

# Create .gitkeep to ensure folder is tracked by git
touch "$COMPANY_DIR/.gitkeep"

# Create company README.md
cat > "$COMPANY_DIR/README.md" <<EOF
# $COMPANY_NAME

**Status**: Active
**Created**: $(date +%Y-%m-%d)

## Overview

[Brief description of company and what we're building for them]

## Company Assets

### Website
\`\`\`
projects/$FOLDER_NAME/website/  ← Git submodule (if needed)
\`\`\`

### Projects
\`\`\`
projects/$FOLDER_NAME/[project-name]/
\`\`\`

## Services We Provide

- [ ] Website
- [ ] Lead Generation
- [ ] AI Voice Customer Service
- [ ] Social Media Automation
- [ ] Other: _______________

## Contact Information

- **Primary Contact**:
- **Email**:
- **Phone**:
- **Location**:

## Key Dates

- **Project Start**: $(date +%Y-%m-%d)
- **Launch Date**: TBD
- **Next Review**: TBD

## Notes

[Any important notes about this client]

---

**For documentation on folder structure**, see: [docs/FOLDER-STRUCTURE-GUIDE-UPDATED.md](../../docs/FOLDER-STRUCTURE-GUIDE-UPDATED.md)
EOF

echo "✅ Created: $COMPANY_DIR/"
echo "✅ Created: $COMPANY_DIR/README.md"
echo "✅ Created: $COMPANY_DIR/.gitkeep"
echo

echo "Next steps:"
echo "───────────"
echo "1. Update $COMPANY_DIR/README.md with company details"
echo
echo "2a. IF they need a website (hosted on GitHub Pages):"
echo "    - Create GitHub repo: gh repo create [Org]/$FOLDER_NAME-website --public"
echo "    - Clone outside dev-sandbox: cd ~ && gh repo clone [Org]/$FOLDER_NAME-website"
echo "    - Add initial files and push"
echo "    - Add as submodule: git submodule add https://github.com/[Org]/$FOLDER_NAME-website projects/$FOLDER_NAME/website"
echo
echo "2b. IF they need projects (automation, backend, tools):"
echo "    - Create project folder: mkdir -p projects/$FOLDER_NAME/[project-name]"
echo "    - Copy template: cp -r .demo-structure-template/project-template/* projects/$FOLDER_NAME/[project-name]/"
echo "    - Build the project!"
echo
echo "3. Commit to dev-sandbox:"
echo "    git add projects/$FOLDER_NAME"
echo "    git commit -m \"feat: Add $COMPANY_NAME to portfolio\""
echo "    git push origin main"
echo
echo "✅ Company folder created successfully!"
