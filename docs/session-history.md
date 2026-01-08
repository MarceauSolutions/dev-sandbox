# Session History & Learnings

Running log of significant learnings, decisions, and patterns discovered during development sessions.

---

## 2026-01-08 (Late Evening): Interview Prep Expansion & Personal AI Assistant

**Context:** Expanding Interview Prep from PowerPoint-only to comprehensive assistant, setting up Personal AI Assistant project

**Accomplished:**
- Expanded Interview Prep scope from "PowerPoint Builder" to full "AI Assistant"
- Built mock interview capability with STAR format evaluation
- Built PDF output generator (cheat sheets, talking points, flashcards, checklists)
- Built intent router for unified conversational interface
- Created Personal AI Assistant project structure
- Updated all documentation to reflect new organization
- Clarified living vs stable documents

**Key Learnings:**
1. **Mock interviews** - Use behavioral/technical/case types, evaluate with STAR format
2. **Intent routing** - Classify user request → route to appropriate workflow
3. **Personal Assistant** - Aggregates all skills, no frontend, Claude Code chat only
4. **Document types** - Living (session-history, prompting-guide, CLAUDE.md) vs Stable (SOPs, workflows)

**New Communication Patterns:**
- "Practice interview with me" → Start mock_interview.py with company/role context
- "Give me a cheat sheet" → Run pdf_outputs.py --output cheat-sheet
- All requests → Route through personal-assistant skill for consistency

**Files Created:**
- `interview-prep-pptx/src/mock_interview.py` - Interactive mock interviews
- `interview-prep-pptx/src/pdf_outputs.py` - Cheat sheets, flashcards, etc.
- `interview-prep-pptx/src/intent_router.py` - Request routing
- `interview-prep-pptx/EXPANDED_SCOPE.md` - Vision for expanded assistant
- `interview-prep-pptx/workflows/mock-interview.md` - Mock interview workflow
- `interview-prep-pptx/workflows/quick-outputs.md` - PDF outputs workflow
- `projects/personal-assistant/README.md` - Personal assistant overview
- `projects/personal-assistant/VERSION` - 1.0.0-dev
- `projects/personal-assistant/CHANGELOG.md` - Version history
- `.claude/skills/personal-assistant/SKILL.md` - Master skill file

**Files Updated:**
- `.claude/skills/interview-prep/SKILL.md` - Expanded capabilities, v1.2.0-dev
- `interview-prep-pptx/VERSION` - Now 1.2.0-dev
- `deploy_to_skills.py` - Added personal-assistant project
- `docs/deployment.md` - Added personal-assistant to architecture
- `CLAUDE.md` - Clarified living vs stable documents

---

## 2026-01-08 (Evening): Versioned Deployment & User Guidance System

**Context:** Building systems for iterative deployment and better user experience

**Accomplished:**
- Created versioned deployment pipeline (like Anthropic ships Claude versions)
- Built user guidance prompts system for interview prep assistant
- Created inference guidelines for intelligent scope extension
- Fixed PowerPoint close-before-open issue
- Updated Brookhaven presentation with consistent theme and enhanced content

**Key Learnings:**
1. **Versioned deployments** - Use VERSION file + CHANGELOG.md per project
2. **Inference guidelines** - Very Low/Low/Medium/High risk determines action
3. **User guidance** - Show next-step prompts after each workflow stage
4. **Theme colors corrected** - #1A1A2E (dark navy), not #003366
5. **Relevance label** - Adobe red #EC1C24 for visual hierarchy

**New Communication Patterns:**
- "Deploy to skills" → Check version, use `deploy_to_skills.py --version X.X.X`
- After any major action → Show user guidance prompts with next options
- Styling changes → Apply to ALL slides (infer consistency)
- Content changes → Only change specified content (don't override user edits)

**Files Created:**
- `docs/versioned-deployment.md` - Complete versioning guide
- `docs/inference-guidelines.md` - When to extend scope vs ask
- `interview-prep-pptx/USER_PROMPTS.md` - User guidance at each stage
- `interview-prep-pptx/VERSION` - Current: 1.1.0-dev
- `interview-prep-pptx/CHANGELOG.md` - Version history
- `execution/download_pptx.py` - Download to ~/Downloads
- `execution/open_pptx.py` - Close previous before opening new
- `execution/enhance_experience_slides.py` - Rich content for slides 14-18

**Scripts Updated:**
- `deploy_to_skills.py` - Added `--status`, `--version` flags
- `live_editor.py` - Added `close_all_presentations()` function
- `apply_navy_theme.py` - Corrected to #1A1A2E

---

## 2026-01-08 (Morning): Interview Prep Workflows & Documentation Reorg

**Context:** Working on Brookhaven National Laboratory presentation, building live editing capabilities

**Accomplished:**
- Created `live_editor.py` for real-time PowerPoint editing
- Created `template_manager.py` for loading existing presentations
- Created `reformat_experience_slides.py` for standardizing slide layouts
- Created `apply_navy_theme.py` for consistent theming
- Built workflow documentation system in `interview-prep-pptx/workflows/`
- Reorganized dev-sandbox documentation structure

**Key Learnings:**
1. **Build workflows as you work** - Document procedures while completing tasks, not after
2. **Experience slide layout:** Title (0.55", 0.3"), Image (0.75", 1.5"), Description (6.55", 1.5"), Relevance (6.55", 4.5")

**New Communication Patterns:**
- "Make slides look like slide X" → Use inspection + reformatting scripts
- "I have the file open" → Start live editing session
- "Don't deploy yet" → Stay in dev-sandbox, iterate locally

**Files Created:**
- `execution/live_editor.py`
- `execution/template_manager.py`
- `execution/reformat_experience_slides.py`
- `execution/apply_navy_theme.py`
- `interview-prep-pptx/workflows/*.md` (6 workflow files)

---

## 2026-01-07: Interview Prep Initial Build

**Context:** Building interview prep PowerPoint generator

**Accomplished:**
- Fixed Railway 500 error (direct module imports vs importlib)
- Combined Steps 1 & 2 into single workflow
- Added slide preview functionality
- Generated first Brookhaven presentation with AI images

**Key Learnings:**
1. Railway needs direct imports, not dynamic importlib
2. Session management helps track iterative edits
3. Grok API costs ~$0.07/image

---

## Adding New Entries

When completing a session with significant learnings:

```markdown
## YYYY-MM-DD: [Brief Title]

**Context:** [What you were working on]

**Accomplished:**
- Item 1
- Item 2

**Key Learnings:**
1. Learning 1
2. Learning 2

**New Communication Patterns:** (if any)
- "User says X" → Do Y

**Files Created:** (if any)
- path/to/file.py
```
