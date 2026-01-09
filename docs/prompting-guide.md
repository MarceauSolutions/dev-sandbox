# Prompting Guide: How to Get Consistent Results

This guide documents the phrases and patterns that reliably trigger specific workflows and behaviors. Use these as templates when you want predictable results.

---

## Core Principle

**You don't need to use exact phrases.** I understand intent. But if you want to be certain a specific workflow runs, these phrases are documented triggers.

The key is: **What you say → What I do** is now documented in CLAUDE.md and this guide.

---

## Interview Prep PowerPoint

### Theme & Styling

| You Say (any of these) | I Do |
|------------------------|------|
| "Make slides consistent" | Apply theme to ALL slides |
| "Same color across all slides" | Apply theme to ALL slides |
| "Match the style of slide X" | Inspect slide X → apply its format to others |
| "Make it look professional" | Apply dark navy theme (#1A1A2E) |
| "Fix the colors" | Apply consistent theme |
| "Apply the theme" | Run `apply_navy_theme.py` |

**All of these trigger the same workflow:** `apply-consistent-theme.md`

### Content Editing

| You Say | I Do |
|---------|------|
| "Change [text] to [new text]" | Edit specific text only |
| "Update the relevance section" | Edit relevance text on specified slides |
| "Add more detail to slide X" | Enhance content on that slide |
| "Make the descriptions richer" | Run `enhance_experience_slides.py` |

### Live Editing

| You Say | I Do |
|---------|------|
| "I have it open" | Start live editing session |
| "I'm looking at the PowerPoint" | Start live editing session |
| "Watch me edit" | Start live editing session |
| "Real-time editing" | Start live editing session |

### Download/Export

| You Say | I Do |
|---------|------|
| "Download it" | Copy to ~/Downloads |
| "Save the final version" | Copy to ~/Downloads |
| "I'm happy with this" | Offer download options |
| "Export as PDF" | Export PDF to ~/Downloads |
| "Send to Downloads" | Copy to ~/Downloads |

---

## Session & Documentation

### Saving Session Progress

| You Say (any of these) | I Do |
|------------------------|------|
| "Save session progress" | Update `docs/session-history.md` |
| "Document what we learned" | Update `docs/session-history.md` |
| "Update the session history" | Update `docs/session-history.md` |
| "Log this session" | Update `docs/session-history.md` |
| "Don't forget this" | Update relevant doc (session-history or CLAUDE.md) |

### Creating/Updating SOPs

| You Say | I Do |
|---------|------|
| "Create a workflow for this" | Create new `[project]/workflows/X.md` |
| "Document this process" | Create/update workflow file |
| "Build the SOP" | Create directive or workflow |
| "Make sure we don't forget how to do this" | Document in appropriate location |
| "Add this to our methods" | Update CLAUDE.md or relevant doc |

### Deployment

| You Say | I Do |
|---------|------|
| "Deploy to skills" | Run `deploy_to_skills.py` with version |
| "Push to production" | Run deployment script |
| "Ship it" | Run deployment script |
| "Don't deploy yet" | Stay in dev-sandbox, iterate locally |
| "Keep iterating" | Don't deploy, continue development |

---

## Fitness Influencer AI

### Content Creation

| You Say | I Do |
|---------|------|
| "Edit my video" | Run video_jumpcut.py (FREE) |
| "Remove silence from video" | Run video_jumpcut.py (FREE) |
| "Create a graphic" | Run educational_graphics.py (FREE) |
| "Make an Instagram post" | Run educational_graphics.py (FREE) |
| "Generate AI images" | Call Grok API ($0.07/image) - confirms if >$0.10 |
| "Create a video ad" | Shotstack + Grok ($0.34) - requires confirmation |

### Business Management

| You Say | I Do |
|---------|------|
| "Summarize my emails" | Run gmail_monitor.py (FREE) |
| "Show revenue analytics" | Run revenue_analytics.py (FREE) |
| "What are my expenses?" | Run revenue_analytics.py (FREE) |

### Fitness Planning

| You Say | I Do |
|---------|------|
| "Create workout plan" | Run workout_plan_generator.py (FREE) |
| "Make nutrition guide" | Run nutrition_guide_generator.py (FREE) |
| "Calculate my macros" | Run nutrition_guide_generator.py (FREE) |

### Cost Confirmations

| Pattern | Interpretation |
|---------|---------------|
| Paid operation requested | Show cost + alternatives, ask to confirm |
| "Yes, proceed" / "Confirm" | Execute paid operation |
| "Use the cheaper option" | Execute budget alternative |
| "Cancel" | Abort operation, no charge |

---

## General Patterns

### Scope Extension (Inference)

| You Say | How I Interpret |
|---------|-----------------|
| "Fix slide 3" | Only slide 3 (literal) |
| "Fix the slides" | All slides (general intent) |
| "Make it consistent" | Apply to everything (consistency = all) |
| "Update the theme" | All slides (theme = global) |
| "Change the text on slide 5" | Only slide 5 (specific reference) |

**Rule:** Styling = apply everywhere. Content = apply only where specified.

### Asking for Changes

| Pattern | Interpretation |
|---------|---------------|
| "Can you..." | Yes, I'll do it |
| "Would you..." | Yes, I'll do it |
| "Please..." | Yes, I'll do it |
| "I want..." | Yes, I'll do it |
| "Make it..." | Yes, I'll do it |

All of these are action requests. I don't need "please" or questions - direct statements work fine.

### Checking Understanding

| You Say | I Do |
|---------|------|
| "Does that make sense?" | I confirm understanding or ask clarifying questions |
| "Am I explaining this right?" | I summarize what I understood |
| "Do you get what I mean?" | I paraphrase your intent back |

---

## Best Practices

### Be Direct
Instead of: "Could you maybe try to make the slides look more consistent?"
Say: "Make the slides consistent"

### Specify When Needed
Instead of: "Fix it"
Say: "Fix the colors on slide 3" or "Fix all the slides"

### Use Keywords That Trigger Workflows

| Keyword | Triggers |
|---------|----------|
| "consistent" | Apply to all, use reference as template |
| "theme" | Global styling change |
| "download" | Export to Downloads folder |
| "deploy" | Run deployment pipeline |
| "session" | Session-related docs |
| "workflow" | Create/read workflow files |
| "SOP" | Create/update procedures |

---

## When You're Unsure

If you're not sure how to phrase something, just describe what you want:

"I want the PowerPoint to look professional with the same dark blue on every slide and the relevance label in red"

I'll interpret this as:
1. Apply dark navy theme (#1A1A2E) to all slides
2. Set "Relevance:" labels to Adobe red (#EC1C24)
3. Ensure consistency across all slides

---

## Feedback Loop

If I do something wrong or not what you expected:
- "That's not what I meant" → I'll ask for clarification
- "Undo that" → I'll revert if possible
- "Do it differently" → I'll ask how you want it done
- "Stop" → I stop current action

---

## Quick Reference Card

```
STYLING:        "make consistent" / "apply theme" / "same style"
CONTENT:        "change X to Y on slide N" / "update the text"
LIVE EDIT:      "I have it open" / "watch the changes"
DOWNLOAD:       "download" / "save final" / "export"
DEPLOY:         "deploy" / "ship it" / "push to production"
DON'T DEPLOY:   "don't deploy" / "keep iterating"
DOCUMENT:       "save session" / "create workflow" / "document this"
```

---

## Adding New Patterns

When we discover new ways you phrase things that should trigger specific actions, I'll add them to:
1. This guide (`docs/prompting-guide.md`)
2. CLAUDE.md (Communication Patterns table)
3. Session history (as new patterns learned)

This way the system gets smarter over time.
