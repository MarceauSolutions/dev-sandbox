# Fitness Influencer AI - Testing Guide

**Last Updated:** January 6, 2026  
**Purpose:** Comprehensive testing procedures to verify all AI assistant features

---

## 🧪 Quick Test Suite

Run the automated test suite:
```bash
cd /Users/williammarceaujr./dev-sandbox
python execution/test_fitness_ai.py --all
```

---

## 📋 Manual Testing Checklist

### ✅ Phase 1: Core Script Testing (Local)

#### Test 1: Workout Plan Generator
```bash
python execution/workout_plan_generator.py \
  --goal "muscle gain" \
  --experience intermediate \
  --days 4 \
  --equipment full_gym \
  --output test_workout

# Expected Output:
# ✓ Markdown exported: .tmp/workout_plans/test_workout.md
# ✓ JSON exported: .tmp/workout_plans/test_workout.json
# ✓ Total exercises: 24
```

**Verify:**
- [ ] Markdown file created with proper formatting
- [ ] JSON file contains all workout days
- [ ] Exercises match experience level
- [ ] Equipment matches selection

---

#### Test 2: Nutrition Guide Generator
```bash
python execution/nutrition_guide_generator.py \
  --weight 180 \
  --activity moderate \
  --goal lean_bulk \
  --diet flexible \
  --output test_nutrition

# Expected Output:
# ✓ Markdown exported: .tmp/nutrition_guides/test_nutrition.md
# ✓ JSON exported: .tmp/nutrition_guides/test_nutrition.json
# ✓ Target calories: ~3090 kcal/day
# ✓ Macros: ~231p / 347c / 85f
```

**Verify:**
- [ ] Calories calculated correctly (TDEE + surplus)
- [ ] Macro ratios appropriate for goal
- [ ] Meal timing recommendations included
- [ ] Food lists match dietary preference

---

#### Test 3: Living Documentation System
```bash
# Check current status
python execution/update_skill_docs.py report

# Add a test use case
python execution/update_skill_docs.py add-use-case \
  --request "Test workout generation" \
  --capability "workout_plan_generator.py" \
  --time "15s" \
  --notes "Testing living documentation"

# Verify it was added
python execution/update_skill_docs.py report
```

**Verify:**
- [ ] Report shows all use cases
- [ ] New use case appears in output
- [ ] USE_CASES.json updated
- [ ] Frequency tracking works

---

#### Test 4: Capability Gap Monitoring
```bash
# Check capability gaps
python execution/monitor_capability_gaps.py check

# Generate implementation plan
python execution/monitor_capability_gaps.py plan

# Mark capability as implemented
python execution/monitor_capability_gaps.py mark-implemented --gap "Workout"
```

**Verify:**
- [ ] Monitoring report shows gaps correctly
- [ ] Priority levels assigned based on frequency
- [ ] Implementation plans generated
- [ ] Mark-implemented updates USE_CASES.json

---

### ✅ Phase 2: Integration Testing

#### Test 5: End-to-End Workflow Test
```bash
# Simulate complete user workflow
python execution/test_fitness_ai.py --workflow

# This tests:
# 1. User requests workout plan
# 2. AI matches to workout_plan_generator.py
# 3. Script executes successfully
# 4. Output validated
# 5. USE_CASES.json updated
# 6. Monitoring system tracks success
```

**Verify:**
- [ ] Request routing works (decision tree)
- [ ] Script execution succeeds
- [ ] Output files created
- [ ] Documentation auto-updated
- [ ] No errors in process

---

#### Test 6: Unknown Request Handling
```bash
# Test the Unknown Use Case Handler
python execution/test_fitness_ai.py --unknown-request \
  "Create a meditation guide PDF"

# Should:
# 1. Detect no match in decision tree
# 2. Log to unhandled_requests[]
# 3. Analyze request components
# 4. Suggest potential solutions
```

**Verify:**
- [ ] Request logged to USE_CASES.json
- [ ] Analysis performed (action/object/domain)
- [ ] Capability proximity checked
- [ ] Response generated with options

---

### ✅ Phase 3: Living Documentation Tests

#### Test 7: Pattern Detection
```bash
# Simulate same request 3 times to trigger pattern detection
for i in {1..3}; do
  python execution/update_skill_docs.py add-use-case \
    --request "Create meditation guide" \
    --capability "educational_graphics.py" \
    --notes "Test pattern $i"
done

# Check if it triggers auto-documentation
python execution/monitor_capability_gaps.py check
```

**Verify:**
- [ ] Frequency increments correctly
- [ ] Priority changes at threshold (3)
- [ ] Recommendation to implement appears
- [ ] Learning log updated

---

#### Test 8: Auto-Documentation Update
```bash
# Increment existing use case to frequency > 3
python execution/update_skill_docs.py increment --id video-edit-001

# This should trigger SKILL.md update if configured
python execution/update_skill_docs.py update-skill --id video-edit-001
```

**Verify:**
- [ ] Frequency counter incremented
- [ ] last_used updated
- [ ] SKILL.md example added (if freq > 3)
- [ ] Learning log entry created

---

### ✅ Phase 4: System Health Checks

#### Test 9: File System Validation
```bash
python execution/test_fitness_ai.py --validate-files

# Checks:
# - All required scripts exist
# - USE_CASES.json is valid JSON
# - SKILL.md has proper structure
# - Decision tree is complete
# - All headers present in scripts
```

**Verify:**
- [ ] All execution scripts found
- [ ] JSON files valid
- [ ] Markdown files well-formed
- [ ] No broken references

---

#### Test 10: Token Efficiency Test
```bash
python execution/test_fitness_ai.py --measure-tokens

# Measures:
# - SKILL.md token count
# - Script header token counts
# - Decision tree parsing time
# - Overall efficiency gain
```

**Verify:**
- [ ] SKILL.md < 250 tokens (target: 200)
- [ ] Script headers < 60 tokens each
- [ ] Decision time < 2 seconds
- [ ] 90%+ token reduction vs baseline

---

## 🎯 Automated Test Suite

### Run All Tests
```bash
python execution/test_fitness_ai.py --all
```

### Run Specific Test Categories
```bash
# Core functionality only
python execution/test_fitness_ai.py --core

# Living documentation only
python execution/test_fitness_ai.py --living-docs

# Monitoring system only
python execution/test_fitness_ai.py --monitoring

# Integration tests only
python execution/test_fitness_ai.py --integration
```

---

## 📊 Test Results Interpretation

### Success Criteria

**All tests passing means:**
- ✅ All 10 capabilities working correctly
- ✅ Living documentation system functional
- ✅ Monitoring and auto-implementation operational
- ✅ Token efficiency targets met (95% reduction)
- ✅ No file system or JSON errors
- ✅ Pattern detection working
- ✅ Auto-documentation triggers correctly

### Common Issues & Fixes

#### Issue: "Script not found"
```bash
# Fix: Ensure you're in dev-sandbox directory
cd /Users/williammarceaujr./dev-sandbox
```

#### Issue: "JSON parsing error"
```bash
# Fix: Validate JSON
python -m json.tool .claude/skills/fitness-influencer-operations/USE_CASES.json
```

#### Issue: "Permission denied"
```bash
# Fix: Make scripts executable
chmod +x execution/*.py
```

#### Issue: "Import errors"
```bash
# Fix: Install dependencies
pip install -r requirements.txt
```

---

## 🔍 Testing the Frontend (marceausolutions.com)

### Test 1: Video Upload & Editing
1. Navigate to https://marceausolutions.com/assistant.html
2. Upload test video (5-10 minutes)
3. Click "Edit Video"
4. **Verify:**
   - [ ] Upload completes (100%)
   - [ ] Processing starts
   - [ ] Download link appears
   - [ ] Stats display correctly
   - [ ] Video plays after download

### Test 2: Graphics Generation
1. Type: "Create an Instagram post about protein timing"
2. **Verify:**
   - [ ] AI extracts title and points
   - [ ] Image generates (1080x1080)
   - [ ] Branding appears correctly
   - [ ] Text is readable

### Test 3: Workout Plan Request
1. Type: "Create a 4-day workout plan for muscle gain, intermediate level, full gym"
2. **Verify:**
   - [ ] AI routes to workout_plan_generator.py
   - [ ] Plan generates with 4 days
   - [ ] Exercises appropriate for intermediate
   - [ ] Download links for markdown and JSON

### Test 4: Nutrition Guide Request
1. Type: "Create a nutrition plan for 180 lbs, lean bulk, moderate activity"
2. **Verify:**
   - [ ] AI routes to nutrition_guide_generator.py
   - [ ] Macros calculated correctly
   - [ ] Meal timing included
   - [ ] Food lists appropriate

---

## 📝 Test Log Template

Use this template to record test results:

```
Test Date: ________
Tester: ________
Environment: [ ] Local [ ] Frontend [ ] Both

Phase 1 - Core Scripts:
[ ] Workout Generator: PASS / FAIL - Notes: ________
[ ] Nutrition Guide: PASS / FAIL - Notes: ________
[ ] Living Docs: PASS / FAIL - Notes: ________
[ ] Monitoring: PASS / FAIL - Notes: ________

Phase 2 - Integration:
[ ] End-to-End: PASS / FAIL - Notes: ________
[ ] Unknown Requests: PASS / FAIL - Notes: ________

Phase 3 - Living Documentation:
[ ] Pattern Detection: PASS / FAIL - Notes: ________
[ ] Auto-Documentation: PASS / FAIL - Notes: ________

Phase 4 - System Health:
[ ] File Validation: PASS / FAIL - Notes: ________
[ ] Token Efficiency: PASS / FAIL - Notes: ________

Overall Status: PASS / FAIL
Issues Found: ________
Action Items: ________
```

---

## 🚀 Continuous Testing

### Daily Checks (Automated)
```bash
# Add to crontab for daily testing
0 9 * * * cd /Users/williammarceaujr./dev-sandbox && python execution/test_fitness_ai.py --all >> test_results.log 2>&1
```

### Weekly Reports
```bash
# Generate weekly analytics
python execution/monitor_capability_gaps.py daily >> weekly_report.log
python execution/update_skill_docs.py report >> weekly_report.log
```

---

## 📞 Support

If tests fail:
1. Check error messages in terminal
2. Verify all dependencies installed
3. Ensure .env file configured
4. Review DEPLOYMENT_GUIDE.md
5. Check SESSION_LOG.md for recent changes

**Test Results Directory:** `.tmp/test_results/`  
**Test Logs:** `test_results.log`

---

**Remember:** Test locally first, then deploy to Railway, then test via frontend!