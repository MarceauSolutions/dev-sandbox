# Launch Guide: Overnight Autonomous Development

**Date**: Tonight (2026-01-12)
**Return**: Tomorrow morning (2026-01-13)
**Expected**: 3 agents complete their work overnight, ready for your 2-hour execution

---

## Step-by-Step Launch (5 minutes)

### 1. Open the Autonomous Prompts File

```bash
open /Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/AGENT-PROMPTS-AUTONOMOUS.txt
```

Or navigate to:
- Finder → dev-sandbox → projects → mcp-aggregator
- Open `AGENT-PROMPTS-AUTONOMOUS.txt` in any text editor

---

### 2. Launch Agent 1 (REST API)

**Open Browser Tab 1**:
- Go to https://claude.ai (or open new Claude Desktop window)
- Scroll to "AGENT 1: REST API DEVELOPMENT (AUTONOMOUS MODE)" in the prompts file
- Copy everything from that section (starts with "I'm Agent 1..." ends before "AGENT 2")
- Paste into Claude
- Hit Enter
- **Label the tab**: "Agent 1 - API"

**Expected**: Agent 1 starts working immediately, building FastAPI server

---

### 3. Launch Agent 2 (Accuracy Testing)

**Open Browser Tab 2**:
- Go to https://claude.ai in a NEW tab (separate conversation)
- Scroll to "AGENT 2: ACCURACY TESTING (AUTONOMOUS MODE)" in the prompts file
- Copy that entire section
- Paste into Claude
- Hit Enter
- **Label the tab**: "Agent 2 - Testing"

**Expected**: Agent 2 starts generating test routes and estimates

---

### 4. Launch Agent 3 (Platform Core)

**Open Browser Tab 3**:
- Go to https://claude.ai in a NEW tab (separate conversation)
- Scroll to "AGENT 3: PLATFORM CORE (AUTONOMOUS MODE)" in the prompts file
- Copy that entire section
- Paste into Claude
- Hit Enter
- **Label the tab**: "Agent 3 - Platform"

**Expected**: Agent 3 starts building registry, router, billing system

---

### 5. Verify All 3 Are Running

**Check each tab**:
- ✅ Agent 1: Should be reading rideshare MCP code and planning API
- ✅ Agent 2: Should be generating test routes
- ✅ Agent 3: Should be designing database schema

**If any agent asks a question**:
- Respond with: "Proceed autonomously, document your decision in FINDINGS.md"
- Or: "Use your best judgment and continue"

---

### 6. Leave Them Overnight

**Before you go**:
- [ ] All 3 tabs open and agents working
- [ ] Browser won't sleep (adjust power settings if needed)
- [ ] Computer won't sleep (or keep it plugged in)

**Optional**: Bookmark all 3 tabs or use browser's "restore tabs" feature

---

## What Happens Overnight (8-12 hours)

### Agent 1 Will Build:
```
agent1-rest-api/
├── workspace/
│   ├── server.py (complete FastAPI app)
│   ├── auth.py (API key authentication)
│   ├── models.py (request/response schemas)
│   ├── config.py (configuration)
│   ├── requirements.txt (dependencies)
│   ├── Dockerfile (production-ready)
│   ├── docker-compose.yml (local dev)
│   └── test_api.py (test suite)
└── output/
    ├── COMPLETION-SUMMARY.md ← Read this first!
    ├── API-DOCS.md
    ├── DEPLOYMENT-GUIDE.md
    └── FINDINGS.md
```

### Agent 2 Will Build:
```
agent2-accuracy-testing/
├── workspace/
│   ├── generate_test_routes.py
│   ├── test-routes.csv (30 routes READY)
│   ├── run_algorithm.py
│   ├── estimated-quotes.csv (our predictions READY)
│   ├── actual-quotes-template.csv (for you to fill)
│   └── calculate_accuracy.py (analysis tool)
└── output/
    ├── COMPLETION-SUMMARY.md ← Read this first!
    ├── QUOTE-COLLECTION-GUIDE.md (your instructions)
    └── FINDINGS.md
```

### Agent 3 Will Build:
```
agent3-platform-core/
├── workspace/
│   ├── schema.sql (PostgreSQL schema)
│   ├── seed_data.sql (initial data)
│   ├── database.py (connection layer)
│   ├── registry.py (MCP registry)
│   ├── router.py (routing engine)
│   ├── billing.py (billing system)
│   └── test_platform.py (test suite)
└── output/
    ├── COMPLETION-SUMMARY.md ← Read this first!
    ├── DATABASE-SETUP.md (your setup guide)
    ├── ARCHITECTURE.md
    └── FINDINGS.md
```

---

## Tomorrow Morning (When You Return)

### Quick Check (2 minutes)

**Open all 3 tabs** and look for completion messages:
- ✅ "Autonomous work complete. See COMPLETION-SUMMARY.md"
- ✅ "All deliverables saved to workspace/ and output/"
- ✅ "Ready for human execution"

**If agent is still working**:
- Let it finish (give it 30 more minutes)
- Or: Say "Please complete current task and summarize progress"

---

### Read Summaries (5 minutes)

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator

# Agent 1 summary
cat agent1-rest-api/output/COMPLETION-SUMMARY.md

# Agent 2 summary
cat agent2-accuracy-testing/output/COMPLETION-SUMMARY.md

# Agent 3 summary
cat agent3-platform-core/output/COMPLETION-SUMMARY.md
```

Each summary tells you:
- ✅ What was built
- ⏰ What you need to do
- 🕐 How long it will take

---

### Execute Their Work (2 hours)

**Follow the guide**: `/Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/AUTONOMOUS-MODE-GUIDE.md`

**Quick version**:
1. Agent 3 first (15 min): Set up PostgreSQL database
2. Agent 1 second (30 min): Deploy API with Docker
3. Agent 2 third (60 min): Collect real Uber/Lyft quotes
4. Integration (15 min): Test everything together
5. Launch! (Day 5)

---

## Troubleshooting

### Browser closed or tabs lost?
**Recovery**:
- Work is saved in `workspace/` and `output/` folders
- Check those folders for completed files
- Launch new agent to continue if needed

### Agent stopped mid-work?
**Recovery**:
- Read `FINDINGS.md` to see progress
- Copy same prompt, add: "Continue from where you left off in workspace/"
- Agent will resume

### Agent produced errors?
**Recovery**:
- Code is in `workspace/`, you can fix bugs manually
- Or: Launch new agent with prompt: "Fix the code in workspace/"
- Usually faster to fix yourself (5-10 minutes)

### Computer went to sleep?
**Recovery**:
- Browser tabs should restore
- If agents stopped, check workspace/ for partial work
- Restart agents if needed

---

## Expected Timeline

**Tonight (10 PM)**:
- Launch 3 agents (5 min)
- Verify they're working (2 min)
- Go to sleep 😴

**Overnight (8-12 hours)**:
- Agents work autonomously
- No permissions needed
- All code written and saved

**Tomorrow Morning (8 AM)**:
- Check completion (2 min)
- Read summaries (5 min)
- Execute instructions (2 hours)
- **Integration and testing (15 min)**
- **READY FOR PRODUCTION LAUNCH!** 🚀

---

## Success Criteria (Tomorrow Morning)

When you return, you should have:

- [ ] Complete REST API (production-ready code)
- [ ] 30 test routes with our estimates (ready for comparison)
- [ ] Complete platform core (registry + router + billing)
- [ ] Clear instructions for what you need to do
- [ ] All code documented and tested (with SQLite)
- [ ] Total human time needed: ~2 hours

---

## Final Checklist Before You Go

- [ ] All 3 Claude tabs open
- [ ] Agents are responding (not stuck)
- [ ] Computer won't sleep (power settings)
- [ ] Browser won't close tabs (save session if needed)
- [ ] You know where to find results tomorrow: `agent*/output/COMPLETION-SUMMARY.md`

---

## Ready? Let's Launch! 🚀

**Right now**:
1. Open `AGENT-PROMPTS-AUTONOMOUS.txt`
2. Launch 3 Claude instances
3. Paste prompts
4. Verify they start working
5. Go to sleep!

**Tomorrow**:
1. Check completion
2. Execute 2-hour checklist
3. Launch to production
4. Start earning revenue!

**Goal**: Break-even ($500/month) by Month 2
**Timeline**: Overnight work + 2 hours execution = DONE!

---

**See you tomorrow morning with 3 complete systems ready to deploy!** 💤➡️🚀
