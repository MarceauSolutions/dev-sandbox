# Inference Guidelines: When to Extend Scope

When the user requests a change, Claude should consider what related changes would logically follow. This document defines when to act, when to ask, and when to stay strictly within scope.

## The Inference Spectrum

| Risk Level | Examples | Action |
|------------|----------|--------|
| **Very Low** | Completing obvious consistency (e.g., theme on remaining slides) | Just do it |
| **Low** | Extending pattern to similar elements | Do it, mention in summary |
| **Medium** | Changes that could override previous user edits | Ask first |
| **High** | Structural changes (delete, reorder, add slides) | Always ask |

## Decision Framework

### 1. JUST DO IT (No confirmation needed)

**Criteria:** Change is additive, non-destructive, and obviously implied

Examples:
- User asks for "consistent theme across slides 1-18" → Also apply to slides 23-24 (closing slides)
- User asks to "fix the background color" → Apply to all slides, not just one
- User asks to "add images to experience slides" → Include all experience slides, not just ones mentioned

**Why safe:** These changes complete the user's intent. Leaving them undone creates inconsistency that the user would immediately notice and request.

### 2. DO IT + MENTION (Inform user of inference)

**Criteria:** Change extends the pattern but affects content the user might have customized

Examples:
- User asks to "update the relevance section format" → Apply to all experience slides, but list which ones were changed
- User asks to "fix text color" → Apply everywhere, but note "Updated text color on 24 slides"

**Format:**
```
✅ Completed requested changes to slides 14-18
📋 Also updated for consistency:
   - Slide 23 (Preparation Checklist): Applied dark navy theme
   - Slide 24 (Closing): Applied dark navy theme
```

### 3. ASK FIRST (Confirmation required)

**Criteria:** Change could override user's intentional customizations

Examples:
- User asks to "change the wording on slide 5" → DON'T automatically apply to other slides
- User asks to "update the company description" → ASK if they want it updated everywhere
- User references specific text → Only change that specific text

**Question format:**
```
I've updated slide 5 as requested. I noticed slides 8 and 12 have similar
content that could also be updated. Would you like me to:
1. Update those slides as well
2. Leave them as-is
```

### 4. NEVER DO (Always requires explicit request)

**Criteria:** Destructive, structural, or irreversible changes

Examples:
- Deleting slides
- Reordering slides
- Removing images
- Changing slide layouts fundamentally
- Overwriting content with AI-generated alternatives

## Specific Rules for PowerPoint Editing

### Theme/Styling Changes
- **Background color** → Apply to ALL slides (very low risk)
- **Text color** → Apply to ALL slides (very low risk)
- **Font changes** → Apply to ALL slides (low risk)
- **Accent removal** → Apply to ALL slides (low risk)

### Content Changes
- **Specific text edit** → ONLY the specified location (user may have customized elsewhere)
- **Format change** (e.g., add "Relevance:" label) → Ask if should apply everywhere
- **Content enhancement** → Only where specified, mention what was changed

### Structural Changes
- **Add slide** → Only if explicitly requested
- **Delete slide** → Only if explicitly requested
- **Reorder slides** → Only if explicitly requested
- **Change layout** → Ask first unless obviously broken

## Implementation Pattern

Before executing any PowerPoint edit, Claude should:

1. **Parse the request** - What was literally asked?
2. **Identify scope** - What slides/elements are explicitly mentioned?
3. **Check for implied scope** - Would leaving other elements unchanged create obvious inconsistency?
4. **Assess risk** - Could extending scope override user's intentional work?
5. **Decide action** - Just do, do + mention, ask, or refuse

## Examples

### Example 1: Theme Consistency
**User:** "Make slides 1-18 match the color of slides 19-22"
**Implied:** Slides 23-24 should also match (obvious consistency)
**Action:** Apply to all slides including 23-24
**Communication:** "Updated all 24 slides to use dark navy theme (#1A1A2E)"

### Example 2: Text Edit
**User:** "Change 'Company Overview' to 'About the Company' on slide 3"
**NOT Implied:** Change similar titles on other slides
**Action:** Only change slide 3
**Communication:** "Updated slide 3 title"

### Example 3: Format Enhancement
**User:** "Add detailed descriptions to the experience slides like slide 19 has"
**Implied:** All experience slides (14-22) should be enhanced
**Action:** Enhance all experience slides, list which ones
**Communication:** "Enhanced experience slides 14-18 to match format of 19-22"

### Example 4: Ambiguous Request
**User:** "Fix the text on the experience slides"
**Unclear:** Which slides? What's wrong with text?
**Action:** Ask for clarification
**Communication:** "Which experience slides would you like me to update? And what specifically should I fix - the wording, formatting, or something else?"

## Self-Check Questions

Before extending scope beyond what was literally requested, ask:

1. **Would NOT doing this create obvious inconsistency?** → If yes, just do it
2. **Could this override the user's intentional customizations?** → If yes, ask first
3. **Is this a styling change or a content change?** → Styling is safer to extend
4. **Would the user be surprised or upset if I did this?** → If maybe, ask first
5. **Can this be easily undone?** → If not, ask first
