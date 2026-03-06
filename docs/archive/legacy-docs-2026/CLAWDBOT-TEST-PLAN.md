# Clawdbot System Testing Plan

## Prerequisites Check

Before testing, verify:
- ✅ Clawdbot service running: `ssh ec2 "sudo systemctl status clawdbot"`
- ✅ Ralph webhook server running: `ssh ec2 "curl http://localhost:5002/health"`
- ✅ SOUL.md contains ops manual: `ssh ec2 "sudo -u clawdbot head -20 /home/clawdbot/clawd/SOUL.md"`
- ✅ Phase 1 .env configured: `ssh ec2 "sudo -u clawdbot grep HOME /home/clawdbot/dev-sandbox/.env"`

## Test 1: Identity Verification

**Goal**: Verify Clawdbot knows it's a full dev agent, not a relay

**Test via Telegram**:
```
User → Clawdbot: "What are you capable of?"
```

**Expected Response** (should mention):
- "full autonomous AI development agent"
- "build apps directly"
- "commit and push to GitHub"
- "trigger Ralph for complex work"
- "follow SOPs"
- NOT "I'm just a message relay"

**Pass Criteria**: Response shows Clawdbot understands its role as a full dev agent

---

## Test 2: Simple Build (Complexity 0-6)

**Goal**: Verify Clawdbot can build simple code directly without delegating

**Test via Telegram**:
```
User → Clawdbot: "Build a simple Flask app with one route that returns 'Hello World'"
```

**Expected Behavior**:
1. Clawdbot analyzes complexity (should be low: 3-4)
2. Clawdbot builds directly in `/home/clawdbot/dev-sandbox/projects/shared/hello-flask/`
3. Creates `src/app.py` with Flask code
4. Commits to GitHub: `git add . && git commit -m "clawdbot: Add simple Flask hello world" && git push`
5. Response: "Done! Created Flask app at projects/shared/hello-flask/. Committed to GitHub."

**Pass Criteria**:
- ✅ Clawdbot builds code (doesn't delegate to Ralph)
- ✅ Code committed to GitHub
- ✅ No errors in execution
- ✅ Flask app is functional

**Verification Commands**:
```bash
# Check if files were created
ssh ec2 "sudo -u clawdbot ls -la /home/clawdbot/dev-sandbox/projects/shared/hello-flask/src/"

# Check if committed to GitHub
ssh ec2 "sudo -u clawdbot bash -c 'cd /home/clawdbot/dev-sandbox && git log -1 --oneline'"

# Test the Flask app
ssh ec2 "sudo -u clawdbot python3 /home/clawdbot/dev-sandbox/projects/shared/hello-flask/src/app.py"
```

---

## Test 3: Complex Build (Complexity 7-10) - Delegates to Ralph

**Goal**: Verify Clawdbot recognizes complex tasks and delegates to Ralph

**Test via Telegram**:
```
User → Clawdbot: "Ralph: Build an HVAC campaign system with database, SMS integration, and tests"
```

**Expected Behavior**:
1. Clawdbot recognizes "Ralph:" prefix (or high complexity score: 8-9)
2. Creates PRD in `/home/clawdbot/dev-sandbox/ralph/prd.json` with user stories:
   - Story 1: Database schema
   - Story 2: SMS integration
   - Story 3: Campaign management
   - Story 4: Testing suite
   - Story 5: Documentation
   - Story 6: Integration tests
3. Triggers Ralph via webhook: `/home/clawdbot/scripts/clawdbot-trigger-ralph.sh hvac-system 10`
4. Response: "Ralph started with 6 stories. You'll be notified when complete."
5. Ralph executes autonomously (~30-60 minutes)
6. Telegram notification when complete: "Ralph Complete - 6/6 stories passed - Iterations: X/10"

**Pass Criteria**:
- ✅ Clawdbot creates PRD
- ✅ Ralph is triggered via webhook
- ✅ Ralph executes all stories
- ✅ User receives completion notification
- ✅ Code committed to GitHub by Ralph

**Verification Commands**:
```bash
# Check PRD was created
ssh ec2 "sudo -u clawdbot cat /home/clawdbot/dev-sandbox/ralph/prd.json | python3 -m json.tool"

# Check Ralph status
ssh ec2 "curl http://localhost:5002/webhook/status | python3 -m json.tool"

# Check Ralph progress
ssh ec2 "sudo -u clawdbot tail -50 /home/clawdbot/dev-sandbox/ralph/progress.txt"

# After completion, check git commits
ssh ec2 "sudo -u clawdbot bash -c 'cd /home/clawdbot/dev-sandbox && git log --oneline | head -10'"
```

---

## Test 4: Mac-Specific Task

**Goal**: Verify Clawdbot delegates Mac-specific tasks to Claude Code

**Test via Telegram**:
```
User → Clawdbot: "Deploy the fitness-influencer MCP to PyPI"
```

**Expected Response**:
```
This requires Mac-specific tools (PyPI deployment). Please use Claude Code on your Mac for this task.
```

**Pass Criteria**:
- ✅ Clawdbot recognizes PyPI deployment as Mac-specific
- ✅ Responds with delegation message
- ✅ Does NOT attempt to deploy from EC2

---

## Test 5: SOP Access (Memory System)

**Goal**: Verify Clawdbot can search memory for SOP information

**Test via Telegram**:
```
User → Clawdbot: "How do I run an SMS campaign?"
```

**Expected Behavior**:
1. Clawdbot searches Ollama memory for "SMS campaign"
2. Finds SOP 18 in embedded CLAUDE.md
3. Responds with summary of SOP 18 steps:
   - Verify prerequisites (Twilio, templates, leads)
   - Dry run first
   - Small batch test (10 leads)
   - Full campaign (only after success)
   - Monitor via Twilio Console and webhook

**Pass Criteria**:
- ✅ Clawdbot references SOP 18
- ✅ Provides accurate summary
- ✅ Mentions key steps (dry run → small batch → full campaign)

---

## Test 6: Git Workflow

**Goal**: Verify Clawdbot follows proper git workflow

**Test via Telegram**:
```
User → Clawdbot: "Create a simple Python calculator script"
```

**Expected Git Workflow**:
1. `cd /home/clawdbot/dev-sandbox`
2. `git pull origin main`
3. Create `projects/shared/calculator/src/calculator.py`
4. `git add projects/shared/calculator/`
5. `git commit -m "clawdbot: Add calculator script"`
6. `git push origin main`

**Pass Criteria**:
- ✅ Pulls before working
- ✅ Commits with "clawdbot:" prefix
- ✅ Pushes to GitHub
- ✅ Commit appears on GitHub

**Verification**:
```bash
# Check git log
ssh ec2 "sudo -u clawdbot bash -c 'cd /home/clawdbot/dev-sandbox && git log -1 --stat'"

# Verify on Mac (when awake)
cd ~/dev-sandbox
git pull
git log --oneline | grep "clawdbot:" | head -5
```

---

## Test 7: Multi-Agent Collaboration Pattern

**Goal**: Verify Clawdbot can coordinate with Ralph for parallel work

**Test via Telegram** (Advanced):
```
User → Clawdbot: "Build analytics dashboard with data pipeline"
```

**Expected Behavior** (Parallel Work + Merge):
1. Clawdbot analyzes: High complexity (8/10), can be parallelized
2. Clawdbot splits work:
   - Clawdbot handles: UI (dashboard components, Flask routes)
   - Ralph handles: Backend (data pipeline, ETL, tests)
3. Clawdbot creates branch: `clawdbot/ui`
4. Clawdbot triggers Ralph PRD with branch: `ralph/backend`
5. Both work simultaneously
6. Clawdbot waits for Ralph webhook
7. Clawdbot integrates both branches
8. Final merge to main

**Pass Criteria**:
- ✅ Work is parallelized
- ✅ Both agents create branches
- ✅ Both agents complete their work
- ✅ Clawdbot integrates successfully
- ✅ Final code works end-to-end

---

## Success Criteria Summary

For the system to be considered fully operational:

| Test | Status | Critical? |
|------|--------|-----------|
| Test 1: Identity | ⬜ | ✅ YES |
| Test 2: Simple Build | ⬜ | ✅ YES |
| Test 3: Complex Build (Ralph) | ⬜ | ✅ YES |
| Test 4: Mac-Specific | ⬜ | ✅ YES |
| Test 5: SOP Access | ⬜ | ✅ YES |
| Test 6: Git Workflow | ⬜ | ✅ YES |
| Test 7: Multi-Agent Collab | ⬜ | ⚠️ NICE-TO-HAVE |

**Minimum to proceed**: Tests 1-6 passing

---

## Troubleshooting Guide

### Issue: Clawdbot says "I'm just a relay"
- **Cause**: SOUL.md not loaded or reverted
- **Fix**: Verify `/home/clawdbot/clawd/SOUL.md` contains ops manual, restart service

### Issue: Clawdbot can't find SOP information
- **Cause**: Ollama embeddings not populated
- **Fix**: Memory auto-populates on first search, wait 1-2 minutes after first query

### Issue: Ralph doesn't trigger
- **Cause**: Webhook server not running
- **Fix**: `ssh ec2 "sudo systemctl status ralph-webhook"`, restart if needed

### Issue: Git push fails
- **Cause**: SSH key not configured or permissions
- **Fix**: Verify Clawdbot can push: `ssh ec2 "sudo -u clawdbot ssh -T git@github.com"`

### Issue: Telegram messages don't reach Clawdbot
- **Cause**: Service crashed or bot token invalid
- **Fix**: Check logs: `ssh ec2 "sudo journalctl -u clawdbot -n 50"`

---

## Next Steps After Testing

Once all critical tests pass:
1. Document results in session-history.md
2. Update CLAUDE.md with communication patterns
3. Create SOP 29: Three-Agent Collaboration
4. Phase 2: Add read-only API credentials (Week 2-3)
5. Phase 3: Add low-risk write APIs (Week 4)
6. Phase 4: Add SMS/Email with approval (Week 5-6)
7. Phase 5: Full autonomy (Month 2+)
