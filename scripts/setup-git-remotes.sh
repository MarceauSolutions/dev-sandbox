#!/bin/bash

# Git Remote Configuration Setup Script
# Created: 2026-01-21
# Purpose: Configure GitHub remotes for repos that lack them

set -e  # Exit on error

echo "🔍 Git Remote Configuration Setup"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check and setup remote
setup_remote() {
  local repo_path=$1
  local repo_name=$2
  local org=$3
  local github_url="https://github.com/$org/$repo_name.git"

  echo -e "\n📁 ${YELLOW}$repo_name${NC}"

  if [ ! -d "$repo_path/.git" ]; then
    echo -e "  ${RED}✗${NC} Not a git repository"
    return 1
  fi

  cd "$repo_path"

  # Check if remote exists
  if git remote | grep -q "origin"; then
    local current_remote=$(git remote get-url origin)
    echo -e "  ${GREEN}✓${NC} Remote already configured: $current_remote"
    return 0
  fi

  # No remote - prompt user
  echo -e "  ${RED}✗${NC} No remote configured"
  echo -e "  ${YELLOW}?${NC} Configure remote: $github_url"
  read -p "  Add this remote? (y/n/skip-all): " choice

  case "$choice" in
    y|Y)
      # Check if GitHub repo exists
      if gh repo view "$org/$repo_name" &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} GitHub repo exists"
      else
        echo -e "  ${YELLOW}!${NC} GitHub repo doesn't exist - creating..."
        gh repo create "$org/$repo_name" --public --description "$(basename $repo_path) - production deployment"
        echo -e "  ${GREEN}✓${NC} GitHub repo created"
      fi

      # Add remote
      git remote add origin "$github_url"
      echo -e "  ${GREEN}✓${NC} Remote added"

      # Ensure on main branch
      current_branch=$(git branch --show-current)
      if [ "$current_branch" != "main" ]; then
        git branch -M main
        echo -e "  ${GREEN}✓${NC} Renamed branch to 'main'"
      fi

      # Push
      echo -e "  ${YELLOW}→${NC} Pushing to GitHub..."
      if git push -u origin main; then
        echo -e "  ${GREEN}✓${NC} Pushed successfully"
      else
        echo -e "  ${RED}✗${NC} Push failed"
        return 1
      fi
      ;;
    skip-all)
      echo -e "  ${YELLOW}⊘${NC} Skipping all remaining repos"
      return 2
      ;;
    *)
      echo -e "  ${YELLOW}⊘${NC} Skipped"
      ;;
  esac
}

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
  echo -e "${RED}ERROR:${NC} GitHub CLI (gh) not installed"
  echo "Install with: brew install gh"
  echo "Then authenticate: gh auth login"
  exit 1
fi

# Check if authenticated
if ! gh auth status &>/dev/null; then
  echo -e "${RED}ERROR:${NC} Not authenticated with GitHub CLI"
  echo "Run: gh auth login"
  exit 1
fi

echo -e "${GREEN}✓${NC} GitHub CLI authenticated"
echo ""

# Setup production repos
echo "=== PRODUCTION REPOS ==="

PROD_REPOS=(
  "email-analyzer-prod"
  "hvac-distributors-prod"
  "interview-prep-prod"
  "lead-scraper-prod"
  "time-blocks-prod"
)

skip_all=false
for repo in "${PROD_REPOS[@]}"; do
  if [ "$skip_all" = true ]; then
    echo -e "\n📁 ${YELLOW}$repo${NC}"
    echo -e "  ${YELLOW}⊘${NC} Skipped (skip-all)"
    continue
  fi

  setup_remote ~/production/$repo $repo "MarceauSolutions"
  if [ $? -eq 2 ]; then
    skip_all=true
  fi
done

# Setup active-projects
echo -e "\n\n=== ACTIVE PROJECTS ==="

setup_remote ~/active-projects/square-foot-shipping "square-foot-shipping" "MarceauSolutions"

# Summary
echo -e "\n\n=================================="
echo "📊 Summary"
echo "=================================="

echo -e "\n${GREEN}Configured repos:${NC}"
for repo in ~/production/*-prod ~/active-projects/*; do
  if [ -d "$repo/.git" ]; then
    cd "$repo"
    if git remote | grep -q "origin"; then
      echo "  ✓ $(basename $repo): $(git remote get-url origin)"
    fi
  fi
done

echo -e "\n${RED}Repos without remotes:${NC}"
for repo in ~/production/*-prod ~/active-projects/*; do
  if [ -d "$repo/.git" ]; then
    cd "$repo"
    if ! git remote | grep -q "origin"; then
      echo "  ✗ $(basename $repo)"
    fi
  fi
done

echo -e "\n${GREEN}✓${NC} Setup complete!"
echo ""
echo "To verify all remotes:"
echo "  bash verify-git-remotes.sh"
