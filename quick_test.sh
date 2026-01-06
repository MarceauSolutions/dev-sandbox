#!/bin/bash
###############################################################################
# quick_test.sh - Quick Testing Script for Fitness Influencer AI
#
# PURPOSE: Rapidly test all new capabilities we implemented
# USAGE: ./quick_test.sh
###############################################################################

echo "=========================================="
echo "Fitness Influencer AI - Quick Test Suite"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS_COUNT=0
FAIL_COUNT=0

# Test 1: Workout Plan Generator
echo "📋 Test 1: Workout Plan Generator"
if python execution/workout_plan_generator.py --goal "strength" --experience beginner --days 3 --equipment minimal --output quick_test_workout > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC} - Workout plan generated successfully"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗ FAIL${NC} - Workout plan generation failed"
    ((FAIL_COUNT++))
fi
echo ""

# Test 2: Nutrition Guide Generator
echo "🥗 Test 2: Nutrition Guide Generator"
if python execution/nutrition_guide_generator.py --weight 160 --activity light --goal cut --diet flexible --output quick_test_nutrition > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC} - Nutrition guide generated successfully"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗ FAIL${NC} - Nutrition guide generation failed"
    ((FAIL_COUNT++))
fi
echo ""

# Test 3: Living Documentation System
echo "📊 Test 3: Living Documentation System"
if python execution/update_skill_docs.py report > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC} - Documentation system working"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗ FAIL${NC} - Documentation system failed"
    ((FAIL_COUNT++))
fi
echo ""

# Test 4: Capability Gap Monitoring
echo "🔍 Test 4: Capability Gap Monitoring"
if python execution/monitor_capability_gaps.py check > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC} - Monitoring system working"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗ FAIL${NC} - Monitoring system failed"
    ((FAIL_COUNT++))
fi
echo ""

# Test 5: File Structure Validation
echo "📁 Test 5: File Structure Validation"
FILES_OK=true
for file in "execution/workout_plan_generator.py" "execution/nutrition_guide_generator.py" "execution/monitor_capability_gaps.py" "execution/update_skill_docs.py" ".claude/skills/fitness-influencer-operations/SKILL.md" ".claude/skills/fitness-influencer-operations/USE_CASES.json"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}  Missing: $file${NC}"
        FILES_OK=false
    fi
done

if $FILES_OK; then
    echo -e "${GREEN}✓ PASS${NC} - All required files present"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗ FAIL${NC} - Some files missing"
    ((FAIL_COUNT++))
fi
echo ""

# Test 6: JSON Validation
echo "🔧 Test 6: JSON Validation"
if python -m json.tool .claude/skills/fitness-influencer-operations/USE_CASES.json > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC} - USE_CASES.json is valid"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗ FAIL${NC} - USE_CASES.json is invalid"
    ((FAIL_COUNT++))
fi
echo ""

# Test 7: Output Files Check
echo "📄 Test 7: Output Files Check"
if [ -f ".tmp/workout_plans/quick_test_workout.md" ] && [ -f ".tmp/nutrition_guides/quick_test_nutrition.md" ]; then
    echo -e "${GREEN}✓ PASS${NC} - Output files created successfully"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗ FAIL${NC} - Output files not created"
    ((FAIL_COUNT++))
fi
echo ""

# Summary
echo "=========================================="
echo "Test Results Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $PASS_COUNT${NC}"
echo -e "${RED}Failed: $FAIL_COUNT${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED!${NC}"
    echo ""
    echo "🎉 Your Fitness Influencer AI is working perfectly!"
    echo ""
    echo "Next steps:"
    echo "1. Deploy to Railway: See DEPLOYMENT_GUIDE.md"
    echo "2. Test via frontend: https://marceausolutions.com/assistant.html"
    echo "3. Monitor usage: python execution/monitor_capability_gaps.py daily"
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    echo ""
    echo "Please check:"
    echo "1. Are you in the dev-sandbox directory?"
    echo "2. Have you installed dependencies? (pip install -r requirements.txt)"
    echo "3. Review error messages above"
    echo ""
    echo "See TESTING_GUIDE.md for detailed troubleshooting"
    exit 1
fi