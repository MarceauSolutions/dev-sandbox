---
name: interview-prep
description: Comprehensive Interview Prep AI Assistant - research companies, generate presentations, practice with mock interviews, create cheat sheets, and more. Your complete interview preparation companion.
version: 1.3.0
trigger_phrases:
  - interview prep
  - prepare for interview
  - research company for interview
  - create interview presentation
  - make interview slides
  - interview powerpoint
  - job interview preparation
  - mock interview
  - practice interview
  - interview questions
  - cheat sheet for interview
  - interview talking points
model: opus
allowed_tools:
  - Bash(python:*)
  - Bash(python3:*)
  - Read
  - Write
  - Edit
  - mcp:google-sheets
  - mcp:google-drive
  - mcp:brave-search
mcp_servers:
  - google-sheets    # Store interview prep data, track sessions
  - google-drive     # Save/retrieve documents
  - brave-search     # Enhanced company research
---

# Interview Prep AI Assistant

## Overview

A comprehensive AI assistant for interview preparation. Goes beyond just PowerPoint generation to include mock interviews, quick reference outputs, and coaching.

## Capabilities

| Category | What I Can Do |
|----------|---------------|
| **Research** | Research companies, analyze roles, identify interview questions |
| **Documents** | Generate PowerPoint, cheat sheets, talking points, flashcards |
| **Practice** | Conduct mock interviews (behavioral, technical, case) |
| **Coaching** | Evaluate responses, provide STAR format feedback |
| **Logistics** | Create day-of checklists, preparation materials |

## When to Use

Use this assistant when the user wants to:
- Prepare for a job interview
- Research a company and role
- Create interview preparation materials
- Practice answering interview questions
- Get a quick cheat sheet before an interview
- Generate talking points
- Practice with a mock interview

## Decision Tree

```
User Request → Classify Intent
│
├─ Research/Presentation → Standard Research + PPTX Flow
│   └─ "Research [Company] for [Role]"
│   └─ "Create presentation for interview"
│
├─ Mock Interview → mock_interview.py
│   └─ "Practice interview with me"
│   └─ "Ask me behavioral questions"
│   └─ "Do a mock interview for Google PM"
│
├─ Quick Outputs → pdf_outputs.py
│   └─ "Give me a cheat sheet"
│   └─ "Create talking points"
│   └─ "Generate flashcards"
│   └─ "Day-of checklist"
│
├─ Editing → pptx_editor.py / live_editor.py
│   └─ "Edit slide 3"
│   └─ "Make slides consistent"
│   └─ "Apply theme"
│
└─ Help → Show capabilities
    └─ "What can you help with?"
    └─ "How do I use this?"
```

## MCP Server Integration

**MCP servers are token-intensive.** Use them for the **deployed/shared version** of this assistant, not for personal/development use.

### When to Use MCP (Deployed Version)
For external users where standardization and maintenance savings justify token costs:

| MCP Server | Use Case |
|------------|----------|
| `google-sheets` | Track user sessions, save scores, export data |
| `google-drive` | Save presentations to user's Drive, retrieve resumes |
| `brave-search` | Enhanced company research for users |

### When to Use Python Scripts (Development/Personal)
For local development and personal use, prefer scripts in `execution/`:

```bash
# Use scripts directly - more token-efficient
python execution/interview_research.py --company "Google" --role "PM"
python execution/pptx_generator.py --input .tmp/interview_research_google.json
```

**Decision rule:** If building for yourself → use scripts. If deploying for others → consider MCP.

## Quick Commands

### Research & Presentation
```bash
# Basic research (uses brave-search MCP if available)
source .env && python execution/interview_research.py --company "{COMPANY}" --role "{ROLE}"

# Generate PowerPoint
python execution/pptx_generator.py --input .tmp/interview_research_{company_slug}.json

# Open presentation
open .tmp/interview_prep_{company_slug}.pptx
```

### Mock Interview Practice
```bash
# Behavioral interview
python interview-prep-pptx/src/mock_interview.py --company "{COMPANY}" --role "{ROLE}" --type behavioral

# Technical interview
python interview-prep-pptx/src/mock_interview.py --company "{COMPANY}" --role "{ROLE}" --type technical

# Quick 5-question practice
python interview-prep-pptx/src/mock_interview.py --company "{COMPANY}" --role "{ROLE}" --questions 5
```

### Quick Reference Outputs
```bash
# One-page cheat sheet
python interview-prep-pptx/src/pdf_outputs.py --input .tmp/interview_research_{company_slug}.json --output cheat-sheet

# Talking points document
python interview-prep-pptx/src/pdf_outputs.py --input .tmp/interview_research_{company_slug}.json --output talking-points

# Q&A flashcards
python interview-prep-pptx/src/pdf_outputs.py --input .tmp/interview_research_{company_slug}.json --output flashcards

# Day-of checklist
python interview-prep-pptx/src/pdf_outputs.py --input .tmp/interview_research_{company_slug}.json --output checklist

# All outputs
python interview-prep-pptx/src/pdf_outputs.py --input .tmp/interview_research_{company_slug}.json --output all
```

### Intent Routing (For Complex Requests)
```bash
# Route user request to appropriate workflow
python interview-prep-pptx/src/intent_router.py --input "Help me prepare for my Google PM interview"

# Interactive chat mode
python interview-prep-pptx/src/intent_router.py --interactive
```

## Workflows

| Workflow | File | Use When |
|----------|------|----------|
| Generate Presentation | `workflows/generate-presentation.md` | Creating new presentation |
| Mock Interview | `workflows/mock-interview.md` | Practice interviews |
| Quick Outputs | `workflows/quick-outputs.md` | Cheat sheets, flashcards, etc. |
| Template Mode | `workflows/template-mode.md` | Continue existing PPTX |
| Live Editing | `workflows/live-editing-session.md` | Real-time edits |

## User Guidance

After key actions, show next-step prompts from `USER_PROMPTS.md`:

### After Research
```
✅ Research complete for [Company] - [Role]

📋 What you can do next:
• "Generate the PowerPoint presentation"
• "Give me a one-page cheat sheet"
• "Practice interview with me"
• "Show me likely interview questions"
```

### After Presentation
```
✅ Presentation created: [filename].pptx

📋 What you can do next:
• "Open the presentation"
• "Apply consistent theme"
• "Edit slide [X]"
• "Download the final version"
```

### After Mock Interview
```
✅ Mock interview complete!

📋 What you can do next:
• "Review my scores"
• "Practice again"
• "Focus on behavioral questions"
• "Create a cheat sheet from what I learned"
```

## Output Formats

| Format | Script | Cost |
|--------|--------|------|
| PowerPoint | `pptx_generator.py` | Free |
| Cheat Sheet (MD/PDF) | `pdf_outputs.py` | Free |
| Talking Points (MD/PDF) | `pdf_outputs.py` | Free |
| Flashcards (MD/PDF) | `pdf_outputs.py` | Free |
| Checklist (MD/PDF) | `pdf_outputs.py` | Free |
| Mock Interview Session | `mock_interview.py` | ~$0.05 |

## Cost Summary

| Action | Cost |
|--------|------|
| Company/Role Research | ~$0.02-0.05 |
| PowerPoint Generation | Free |
| Mock Interview (7 questions) | ~$0.05 |
| PDF Outputs | Free |
| Text Edits | Free |
| AI Image Generation | $0.07/image |

## File Structure

```
interview-prep-pptx/
├── src/
│   ├── interview_research.py     # AI research
│   ├── pptx_generator.py         # PowerPoint generation
│   ├── pptx_editor.py            # Slide editing
│   ├── mock_interview.py         # Mock interview practice
│   ├── pdf_outputs.py            # Cheat sheet, flashcards, etc.
│   ├── intent_router.py          # Request routing
│   ├── session_manager.py        # Session tracking
│   └── live_editor.py            # Real-time editing
├── workflows/
│   ├── generate-presentation.md
│   ├── mock-interview.md
│   ├── quick-outputs.md
│   └── live-editing-session.md
├── VERSION                        # 1.2.0-dev
├── CHANGELOG.md
├── USER_PROMPTS.md
├── EXPANDED_SCOPE.md
└── SKILL.md
```

## Example Interactions

**User:** "Help me prepare for my Google PM interview"
**Assistant:**
1. Ask if they have a resume
2. Run research script
3. Generate PowerPoint
4. Offer mock interview or cheat sheet

**User:** "Practice interview with me"
**Assistant:**
1. Confirm company/role context
2. Start mock interview (behavioral by default)
3. Ask questions, evaluate responses
4. Provide STAR format feedback
5. Give overall performance summary

**User:** "Quick cheat sheet for my Apple interview tomorrow"
**Assistant:**
1. Check for existing research
2. Generate one-page cheat sheet
3. Offer to download to Downloads folder

## Deployment

- **Production API**: https://interview-prep-pptx-production.up.railway.app
- **Frontend**: https://interview-prep-pptx-production.up.railway.app/app
- **Skill Version**: 1.2.0-dev

## Related Files

- Directive: `directives/interview_prep.md`
- User prompts: `interview-prep-pptx/USER_PROMPTS.md`
- Expanded scope: `interview-prep-pptx/EXPANDED_SCOPE.md`
- Inference guidelines: `docs/inference-guidelines.md`
