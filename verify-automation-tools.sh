#!/bin/bash

# Automation Tools Verification Script
# Purpose: Verify all critical automation tools work after folder restructure
# Run BEFORE and AFTER any restructure to ensure nothing breaks

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Automation Tools Verification Suite${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

# Function to run test
run_test() {
  local test_name=$1
  local test_command=$2
  local working_dir=$3

  echo -e "${YELLOW}Testing:${NC} $test_name"

  if [ -n "$working_dir" ]; then
    cd "$working_dir" || {
      echo -e "  ${RED}✗ FAILED${NC} - Directory not found: $working_dir"
      TESTS_FAILED=$((TESTS_FAILED + 1))
      FAILED_TESTS+=("$test_name (directory missing)")
      return 1
    }
  fi

  if eval "$test_command" &>/dev/null; then
    echo -e "  ${GREEN}✓ PASSED${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    return 0
  else
    echo -e "  ${RED}✗ FAILED${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    FAILED_TESTS+=("$test_name")
    return 1
  fi
}

# Detect current structure (shared-multi-tenant vs shared)
if [ -d ~/dev-sandbox/projects/shared-multi-tenant ]; then
  SHARED_PATH="shared-multi-tenant"
  echo -e "${BLUE}Detected structure:${NC} shared-multi-tenant/"
elif [ -d ~/dev-sandbox/projects/shared ]; then
  SHARED_PATH="shared"
  echo -e "${BLUE}Detected structure:${NC} shared/"
else
  echo -e "${RED}ERROR:${NC} Cannot find shared tools directory"
  exit 1
fi

echo ""

# ========================================
# LEAD GENERATION & OUTREACH TOOLS
# ========================================

echo -e "${BLUE}=== LEAD GENERATION & OUTREACH ===${NC}"
echo ""

run_test \
  "Lead Scraper - Module Import" \
  "python -c 'from src.scraper import LeadScraper'" \
  ~/dev-sandbox/projects/$SHARED_PATH/lead-scraper

run_test \
  "Lead Scraper - Help Command" \
  "python -m src.scraper --help" \
  ~/dev-sandbox/projects/$SHARED_PATH/lead-scraper

run_test \
  "Apollo Import - Module Access" \
  "python -c 'from src.apollo_import import ApolloImporter'" \
  ~/dev-sandbox/projects/$SHARED_PATH/lead-scraper

run_test \
  "Apollo Import - Help Command" \
  "python -m src.apollo_import --help" \
  ~/dev-sandbox/projects/$SHARED_PATH/lead-scraper

run_test \
  "SMS Outreach - Module Import" \
  "python -c 'from src.sms_outreach import SMSCampaign'" \
  ~/dev-sandbox/projects/$SHARED_PATH/lead-scraper

run_test \
  "SMS Templates - Files Exist" \
  "[ -d templates/sms ] && [ -f templates/sms/no_website_intro.txt ]" \
  ~/dev-sandbox/projects/$SHARED_PATH/lead-scraper

run_test \
  "Follow-up Sequences - Module Import" \
  "python -c 'from src.follow_up_sequence import FollowUpSequence'" \
  ~/dev-sandbox/projects/$SHARED_PATH/lead-scraper

run_test \
  "Campaign Analytics - Module Import" \
  "python -c 'from src.campaign_analytics import CampaignAnalytics'" \
  ~/dev-sandbox/projects/$SHARED_PATH/lead-scraper

run_test \
  "Campaign Analytics - Help Command" \
  "python -m src.campaign_analytics --help" \
  ~/dev-sandbox/projects/$SHARED_PATH/lead-scraper

run_test \
  "Twilio Webhook - Module Import" \
  "python -c 'from src.twilio_webhook import TwilioWebhook'" \
  ~/dev-sandbox/projects/$SHARED_PATH/lead-scraper

# ========================================
# AI CUSTOMER SERVICE (VOICE AI)
# ========================================

echo ""
echo -e "${BLUE}=== AI CUSTOMER SERVICE (VOICE AI) ===${NC}"
echo ""

run_test \
  "AI Customer Service - Main Module" \
  "python -c 'from src.main import app'" \
  ~/dev-sandbox/projects/$SHARED_PATH/ai-customer-service

run_test \
  "Voice Engine - Module Import" \
  "python -c 'from src.voice_engine import VoiceEngine'" \
  ~/dev-sandbox/projects/$SHARED_PATH/ai-customer-service

run_test \
  "Voice Styles - Module Import" \
  "python -c 'from src.voice_styles import VoiceStyle'" \
  ~/dev-sandbox/projects/$SHARED_PATH/ai-customer-service

run_test \
  "Business Voice Engine - Module Import" \
  "python -c 'from src.business_voice_engine import BusinessVoiceEngine'" \
  ~/dev-sandbox/projects/$SHARED_PATH/ai-customer-service

run_test \
  "Twilio Handler - Module Import" \
  "python -c 'from src.twilio_handler import TwilioHandler'" \
  ~/dev-sandbox/projects/$SHARED_PATH/ai-customer-service

run_test \
  "Call Insights - Module Import" \
  "python -c 'from src.call_insights import CallInsights'" \
  ~/dev-sandbox/projects/$SHARED_PATH/ai-customer-service

# ========================================
# SOCIAL MEDIA AUTOMATION
# ========================================

echo ""
echo -e "${BLUE}=== SOCIAL MEDIA AUTOMATION ===${NC}"
echo ""

run_test \
  "Business Scheduler - Module Import" \
  "python -c 'from src.business_scheduler import BusinessScheduler'" \
  ~/dev-sandbox/projects/$SHARED_PATH/social-media-automation

run_test \
  "Business Scheduler - Help Command" \
  "python -m src.business_scheduler --help" \
  ~/dev-sandbox/projects/$SHARED_PATH/social-media-automation

run_test \
  "X Scheduler - Module Import" \
  "python -c 'from src.x_scheduler import XScheduler'" \
  ~/dev-sandbox/projects/$SHARED_PATH/social-media-automation

run_test \
  "Business Content Generator - Module Import" \
  "python -c 'from src.business_content_generator import BusinessContentGenerator'" \
  ~/dev-sandbox/projects/$SHARED_PATH/social-media-automation

run_test \
  "Content Templates - Files Exist" \
  "[ -f templates/business_content.json ]" \
  ~/dev-sandbox/projects/$SHARED_PATH/social-media-automation

# ========================================
# PERSONAL ASSISTANT
# ========================================

echo ""
echo -e "${BLUE}=== PERSONAL ASSISTANT ===${NC}"
echo ""

run_test \
  "Morning Digest - Module Import" \
  "python -c 'from src.morning_digest import MorningDigest'" \
  ~/dev-sandbox/projects/$SHARED_PATH/personal-assistant

run_test \
  "Morning Digest - Help Command" \
  "python -m src.morning_digest --help" \
  ~/dev-sandbox/projects/$SHARED_PATH/personal-assistant

run_test \
  "Digest Aggregator - Module Import" \
  "python -c 'from src.digest_aggregator import DigestAggregator'" \
  ~/dev-sandbox/projects/$SHARED_PATH/personal-assistant

run_test \
  "Routine Scheduler - Module Import" \
  "python -c 'from src.routine_scheduler import RoutineScheduler'" \
  ~/dev-sandbox/projects/$SHARED_PATH/personal-assistant

# ========================================
# ENVIRONMENT & CREDENTIALS
# ========================================

echo ""
echo -e "${BLUE}=== ENVIRONMENT & CREDENTIALS ===${NC}"
echo ""

run_test \
  ".env File Exists" \
  "[ -f .env ]" \
  ~/dev-sandbox

run_test \
  "Twilio Credentials in .env" \
  "grep -q 'TWILIO_ACCOUNT_SID' .env" \
  ~/dev-sandbox

run_test \
  "Google Places API in .env" \
  "grep -q 'GOOGLE_PLACES_API_KEY' .env" \
  ~/dev-sandbox

run_test \
  "Apollo API Key in .env" \
  "grep -q 'APOLLO_API_KEY' .env" \
  ~/dev-sandbox

run_test \
  "X API Credentials in .env" \
  "grep -q 'X_API_KEY' .env" \
  ~/dev-sandbox

# ========================================
# DEPLOYMENT & GIT
# ========================================

echo ""
echo -e "${BLUE}=== DEPLOYMENT & GIT ===${NC}"
echo ""

run_test \
  "deploy_to_skills.py Exists" \
  "[ -f deploy_to_skills.py ]" \
  ~/dev-sandbox

run_test \
  "deploy_to_skills.py - List Projects" \
  "python deploy_to_skills.py --list" \
  ~/dev-sandbox

run_test \
  "No Nested Git Repos in dev-sandbox" \
  "[ \$(find . -name '.git' -type d | wc -l) -eq 1 ]" \
  ~/dev-sandbox

run_test \
  "Git Remote Configured for dev-sandbox" \
  "git remote | grep -q 'origin'" \
  ~/dev-sandbox

# ========================================
# SUMMARY
# ========================================

echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Test Results Summary${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "Total Tests Run:    $((TESTS_PASSED + TESTS_FAILED))"
echo -e "${GREEN}Tests Passed:${NC}      $TESTS_PASSED"
echo -e "${RED}Tests Failed:${NC}       $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
  echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
  echo -e "All automation tools are working correctly."
  exit 0
else
  echo -e "${RED}✗ SOME TESTS FAILED${NC}"
  echo ""
  echo -e "${YELLOW}Failed Tests:${NC}"
  for test in "${FAILED_TESTS[@]}"; do
    echo -e "  - $test"
  done
  echo ""
  echo -e "${RED}DO NOT PROCEED WITH RESTRUCTURE${NC}"
  echo -e "Fix these issues before making any folder changes."
  exit 1
fi
