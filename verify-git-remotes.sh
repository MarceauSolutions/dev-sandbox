#!/bin/bash

# Git Remote Verification Script
# Created: 2026-01-21
# Purpose: Verify all repositories have correct GitHub remotes

echo "🔍 Git Remote Verification Report"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

total_repos=0
configured_repos=0
missing_repos=0

# Function to check repo remote
check_remote() {
  local category=$1
  local repo_path=$2

  if [ ! -d "$repo_path/.git" ]; then
    return
  fi

  total_repos=$((total_repos + 1))
  local repo_name=$(basename "$repo_path")

  cd "$repo_path"

  if git remote | grep -q "origin"; then
    configured_repos=$((configured_repos + 1))
    local remote_url=$(git remote get-url origin)
    echo -e "  ${GREEN}✓${NC} $repo_name → $remote_url"
  else
    missing_repos=$((missing_repos + 1))
    echo -e "  ${RED}✗${NC} $repo_name ${YELLOW}(no remote configured)${NC}"
  fi
}

# Check dev-sandbox
echo -e "${BLUE}=== DEV-SANDBOX ===${NC}"
check_remote "dev-sandbox" ~/dev-sandbox

# Check production repos
echo -e "\n${BLUE}=== PRODUCTION (~/production/) ===${NC}"
if [ -d ~/production ]; then
  for repo in ~/production/*-prod; do
    if [ -d "$repo" ]; then
      check_remote "production" "$repo"
    fi
  done
else
  echo -e "  ${YELLOW}!${NC} Production directory doesn't exist"
fi

# Check website repos
echo -e "\n${BLUE}=== WEBSITES (~/websites/) ===${NC}"
if [ -d ~/websites ]; then
  for repo in ~/websites/*; do
    if [ -d "$repo" ]; then
      check_remote "websites" "$repo"
    fi
  done
else
  echo -e "  ${YELLOW}!${NC} Websites directory doesn't exist"
fi

# Check active-projects
echo -e "\n${BLUE}=== ACTIVE PROJECTS (~/active-projects/) ===${NC}"
if [ -d ~/active-projects ]; then
  for repo in ~/active-projects/*; do
    if [ -d "$repo" ]; then
      check_remote "active-projects" "$repo"
    fi
  done
else
  echo -e "  ${YELLOW}!${NC} Active-projects directory doesn't exist"
fi

# Summary
echo -e "\n=================================="
echo -e "${BLUE}📊 Summary${NC}"
echo "=================================="
echo -e "Total repositories:     $total_repos"
echo -e "${GREEN}Configured:${NC}             $configured_repos"
echo -e "${RED}Missing remotes:${NC}        $missing_repos"

if [ $missing_repos -eq 0 ]; then
  echo -e "\n${GREEN}✓ All repositories have GitHub remotes configured!${NC}"
  exit 0
else
  echo -e "\n${YELLOW}⚠️  Some repositories need remote configuration${NC}"
  echo ""
  echo "To setup missing remotes:"
  echo "  bash setup-git-remotes.sh"
  exit 1
fi
