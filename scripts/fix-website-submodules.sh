#!/bin/bash

# Fix Website Submodules
# Converts website folders from git submodules to regular directories

echo "=== Fixing Website Submodules ==="
echo

# Array of website paths
websites=(
    "projects/marceau-solutions/website"
    "projects/swflorida-hvac/website"
    "projects/square-foot-shipping/website"
)

for website in "${websites[@]}"; do
    echo "Processing: $website"

    # Check if it's a submodule
    if git ls-tree HEAD "$website" | grep -q "^160000"; then
        echo "  → Is a submodule, converting..."

        # Remove submodule entry from git
        git rm --cached "$website"

        # Remove .git directory from website folder (makes it a regular directory)
        if [ -d "$website/.git" ]; then
            rm -rf "$website/.git"
        fi

        # Add website contents to parent repo
        git add "$website"

        echo "  ✓ Converted to regular directory"
    else
        echo "  → Not a submodule, skipping"
    fi
    echo
done

# Check .gitmodules file
if [ -f .gitmodules ]; then
    echo "Found .gitmodules file"
    cat .gitmodules
    echo
    echo "Removing .gitmodules..."
    git rm .gitmodules
    echo "✓ Removed"
    echo
fi

echo "=== Commit Changes ==="
git status

echo
echo "Ready to commit. Run:"
echo "git commit -m \"fix: Convert website submodules to regular directories\""
