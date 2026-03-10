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
#   1. Auto-stashes any untracked/uncommitted work (safety net)
#   2. Copies website files from projects/{client}/website/ to a temp dir
#   3. Pushes to the client's GitHub Pages deployment repo
#   4. Cleans up

set -euo pipefail

# ============================================================
# SAFETY: Refuse to rm -rf inside dev-sandbox
# ============================================================
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "")"
safety_check() {
    local target_dir="$1"
    local resolved
    resolved="$(cd "$target_dir" 2>/dev/null && pwd -P)"
    if [[ "$resolved" == "$REPO_ROOT" || "$resolved" == "$HOME" || "$resolved" == "/" ]]; then
        echo "FATAL: Refusing to delete contents of $resolved (safety check)"
        exit 99
    fi
}

# ============================================================
# Client config (bash 3.2 compatible — no associative arrays)
# ============================================================
get_client_config() {
    case "$1" in
        marceau)
            LOCAL_PATH="projects/marceau-solutions/digital/website"
            DEPLOY_REPO="MarceauSolutions/marceausolutions.com"
            ;;
        hvac)
            LOCAL_PATH="projects/marceau-solutions/digital/clients/swflorida-hvac/website"
            DEPLOY_REPO="MarceauSolutions/swflorida-comfort-hvac"
            ;;
        boabfit)
            LOCAL_PATH="projects/marceau-solutions/digital/clients/boabfit/website"
            DEPLOY_REPO="MarceauSolutions/boabfit-website"
            ;;
        flames)
            LOCAL_PATH="projects/marceau-solutions/digital/clients/flames-of-passion/website"
            DEPLOY_REPO="MarceauSolutions/flames-of-passion-website"
            ;;
        *)
            return 1
            ;;
    esac
}

# --- Validate args ---
CLIENT="${1:-}"
if [[ -z "$CLIENT" ]]; then
    echo "Usage: $0 <client>"
    echo ""
    echo "Available clients:"
    echo "  marceau  →  MarceauSolutions/marceausolutions.com"
    echo "  hvac     →  MarceauSolutions/swflorida-comfort-hvac"
    echo "  boabfit  →  MarceauSolutions/boabfit-website"
    echo "  flames   →  MarceauSolutions/flames-of-passion-website"
    exit 1
fi

if ! get_client_config "$CLIENT"; then
    echo "Unknown client: $CLIENT"
    echo "Available: marceau, hvac, boabfit, flames"
    exit 1
fi

WEBSITE_DIR="$REPO_ROOT/$LOCAL_PATH"

if [[ ! -d "$WEBSITE_DIR" ]]; then
    echo "Error: $WEBSITE_DIR does not exist"
    exit 1
fi

echo "Deploying $CLIENT website..."
echo "  Source: $LOCAL_PATH"
echo "  Target: $DEPLOY_REPO"
echo ""

# ============================================================
# PRE-DEPLOY: Backup untracked + uncommitted work
# ============================================================
BACKUP_DIR="$REPO_ROOT/.deploy-backups"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="$BACKUP_DIR/pre-deploy-${CLIENT}-${TIMESTAMP}.tar.gz"

# Capture untracked files list
UNTRACKED=$(cd "$REPO_ROOT" && git ls-files --others --exclude-standard 2>/dev/null || true)
MODIFIED=$(cd "$REPO_ROOT" && git diff --name-only 2>/dev/null || true)

if [[ -n "$UNTRACKED" || -n "$MODIFIED" ]]; then
    echo "Backing up uncommitted work to $BACKUP_FILE ..."
    # Create tarball of all untracked + modified files
    (
        cd "$REPO_ROOT"
        {
            echo "$UNTRACKED"
            echo "$MODIFIED"
        } | sort -u | grep -v '^$' | tar czf "$BACKUP_FILE" -T - 2>/dev/null
    )
    echo "  Backup created ($(du -h "$BACKUP_FILE" | cut -f1))"
    echo ""
else
    echo "  No uncommitted work to backup."
    echo ""
fi

# Prune old backups (keep last 10)
ls -t "$BACKUP_DIR"/pre-deploy-*.tar.gz 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true

# ============================================================
# Clone deployment repo, replace contents, push
# ============================================================
DEPLOY_TMPDIR=$(mktemp -d)
trap "rm -rf '$DEPLOY_TMPDIR'" EXIT

git clone --depth 1 "https://github.com/$DEPLOY_REPO.git" "$DEPLOY_TMPDIR/repo" 2>&1

# Safety: verify we're in the temp dir, not dev-sandbox
safety_check "$DEPLOY_TMPDIR/repo"

# Remove old files (except .git)
find "$DEPLOY_TMPDIR/repo" -mindepth 1 -maxdepth 1 -not -name '.git' -exec rm -rf {} +

# Copy new files
cp -R "$WEBSITE_DIR"/* "$DEPLOY_TMPDIR/repo/"

# Check if anything changed
cd "$DEPLOY_TMPDIR/repo"
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
