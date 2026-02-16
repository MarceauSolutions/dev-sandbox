#!/bin/bash
# Deploy a client website from monorepo to its GitHub Pages repo.
#
# Usage: ./scripts/deploy_website.sh <client>
#   ./scripts/deploy_website.sh marceau
#   ./scripts/deploy_website.sh hvac
#   ./scripts/deploy_website.sh boabfit
#   ./scripts/deploy_website.sh flames
#
# What it does:
#   1. Copies website files from projects/{client}/website/ to a temp dir
#   2. Pushes to the client's GitHub Pages deployment repo
#   3. Cleans up

set -e

# Client → local path + deployment repo mapping
declare -A PATHS REPOS
PATHS[marceau]="projects/marceau-solutions/website"
REPOS[marceau]="MarceauSolutions/marceausolutions.com"

PATHS[hvac]="projects/swflorida-hvac/website"
REPOS[hvac]="MarceauSolutions/swflorida-comfort-hvac"

PATHS[boabfit]="projects/boabfit/website"
REPOS[boabfit]="MarceauSolutions/boabfit-website"

PATHS[flames]="projects/flames-of-passion/website"
REPOS[flames]="MarceauSolutions/flames-of-passion-website"

# --- Validate args ---
CLIENT="$1"
if [[ -z "$CLIENT" ]]; then
    echo "Usage: $0 <client>"
    echo ""
    echo "Available clients:"
    for key in "${!PATHS[@]}"; do
        echo "  $key  →  ${REPOS[$key]}"
    done
    exit 1
fi

if [[ -z "${PATHS[$CLIENT]}" ]]; then
    echo "Unknown client: $CLIENT"
    echo "Available: ${!PATHS[*]}"
    exit 1
fi

LOCAL_PATH="${PATHS[$CLIENT]}"
DEPLOY_REPO="${REPOS[$CLIENT]}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
WEBSITE_DIR="$REPO_ROOT/$LOCAL_PATH"

if [[ ! -d "$WEBSITE_DIR" ]]; then
    echo "Error: $WEBSITE_DIR does not exist"
    exit 1
fi

echo "Deploying $CLIENT website..."
echo "  Source: $LOCAL_PATH"
echo "  Target: $DEPLOY_REPO"
echo ""

# --- Clone deployment repo, replace contents, push ---
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

git clone --depth 1 "https://github.com/$DEPLOY_REPO.git" "$TMPDIR/repo" 2>&1

# Remove old files (except .git)
find "$TMPDIR/repo" -maxdepth 1 -not -name '.git' -not -name '.' -not -name '..' -exec rm -rf {} +

# Copy new files
cp -R "$WEBSITE_DIR"/* "$TMPDIR/repo/"

# Check if anything changed
cd "$TMPDIR/repo"
if git diff --quiet && [[ -z "$(git ls-files --others --exclude-standard)" ]]; then
    echo "No changes to deploy."
    exit 0
fi

# Commit and push
git add -A
git commit -m "Deploy from dev-sandbox $(date +%Y-%m-%d)"
git push origin main

echo ""
echo "Deployed $CLIENT website to $DEPLOY_REPO"
