# User Guidance Prompts

This document defines the guidance prompts and next-step suggestions to show users at different stages of the interview prep workflow.

## Stage 1: After Research Completes

**Context:** Research JSON has been generated, presentation not yet created.

**Show user:**
```
✅ Research complete for [Company] - [Role]

📋 What you can do next:
• "Generate the PowerPoint presentation"
• "Generate presentation with AI images" (~$0.35 for 5 images)
• "Show me a summary of the research"
• "Research a different company instead"
```

---

## Stage 2: After Presentation Generated

**Context:** PowerPoint has been created and is ready for review.

**Show user:**
```
✅ Presentation created: [filename].pptx ([X] slides)

📋 What you can do next:
• "Open the presentation" - View in PowerPoint
• "List all slides" - See slide titles and content overview
• "Make the theme consistent across all slides"
• "Edit slide [X]..." - Change text or content on a specific slide
• "Add an image to slide [X]"

💾 When you're happy with the presentation:
• "Download the final version" - Save to your Downloads folder
• "Export as PDF" - Create a PDF version for easy sharing
```

---

## Stage 3: During Editing (Live Session Active)

**Context:** User is actively editing the presentation.

**Show user:**
```
📝 Live editing session active for [filename].pptx

📋 Editing commands you can use:
• "Change [old text] to [new text] on slide [X]"
• "Make slide [X] look like slide [Y]" - Copy styling
• "Apply consistent theme to all slides"
• "Add my image to slide [X]" - Use your own image
• "Generate an AI image for slide [X]" (~$0.07)
• "Remove the image from slide [X]"
• "Change the Relevance text on slide [X] to..."

🔄 Navigation:
• "Show me slide [X]" - Inspect a specific slide
• "List all slides" - See overview
• "Go back to the previous version" - Revert last change

💾 When you're done editing:
• "Download the final version" - Save to Downloads folder
• "I'm happy with this version" - Finalize the presentation
```

---

## Stage 4: After Theme/Style Changes

**Context:** User has made styling changes (colors, formatting).

**Show user:**
```
✅ Theme updated across [X] slides

📋 What you can do next:
• "Show me slide [X]" - Verify the changes look correct
• "The colors look off on slide [X]" - Fix specific slides
• "Change the Relevance label color to [color]"
• "Make the title text larger/smaller"

💾 When you're satisfied:
• "Download the final version" - Save to Downloads folder
```

---

## Stage 5: Final Presentation Ready

**Context:** User indicates they're happy with the presentation.

**Show user:**
```
🎉 Your presentation is ready!

📥 Download options:
• "Download as PowerPoint" - .pptx file to Downloads folder
• "Download as PDF" - PDF version for sharing/printing
• "Email me the presentation" - Send to your email (if configured)

📤 The file is saved at: .tmp/[filename].pptx

💡 Interview tips:
• Review the "Smart Questions to Ask" slide before your interview
• Practice your talking points from the experience slides
• Check the "Preparation Checklist" slide for final reminders

🔄 Need changes?
• "Actually, change [X]..." - Make additional edits
• "Start over with a new company" - Begin fresh research
```

---

## Stage 6: Experience Slides Enhancement

**Context:** User is working on experience/relevance slides.

**Show user:**
```
📝 Working on experience slides

📋 What you can do:
• "Make all experience slides match slide [X]" - Apply consistent format
• "Add more detail to the relevance section on slide [X]"
• "Change the image on slide [X] to show [description]"
• "The description doesn't capture what I did - change it to [new text]"

💡 For best results:
• Each experience slide should explain:
  1. What you did (image + description)
  2. Why it matters for THIS role (relevance section)
• Keep relevance sections specific to [Company]'s needs
```

---

## Stage 7: Download/Export Complete

**Context:** User has downloaded their presentation.

**Show user:**
```
✅ Downloaded to: ~/Downloads/[filename].pptx

📋 What else can I help with?
• "Create a presentation for another company"
• "Help me prepare talking points for the interview"
• "What questions should I expect from [Company]?"
• "Review my resume for this role"

Good luck with your interview at [Company]! 🍀
```

---

## Error Recovery Prompts

### Missing Resume
```
❓ I don't see a resume file. You can:
• "Use my resume at [path]" - Provide resume location
• "Continue without a resume" - Generate general presentation
• "I'll paste my experience here..." - Enter experience manually
```

### Research Failed
```
❌ Research encountered an issue.

📋 You can try:
• "Try again" - Retry the research
• "Use a different company name: [name]"
• "Skip research and create a basic presentation"
```

### Edit Didn't Work
```
⚠️ Couldn't find that text to replace.

📋 Try:
• "Show me slide [X]" - See exact text on the slide
• "List all text on slide [X]" - Get copyable text
• Rephrase your edit request with the exact text shown
```

---

## Inline Prompt Examples

These short prompts can be shown inline after specific actions:

| After Action | Show This |
|-------------|-----------|
| Open presentation | `💡 Try: "List all slides" or "Edit slide 3"` |
| List slides | `💡 Try: "Show me slide [X]" for details` |
| Edit text | `💡 Try: "Download the final version" when ready` |
| Add image | `💡 Try: "Make all slides consistent" to apply same style` |
| Apply theme | `💡 Try: "Download as PDF" for easy sharing` |
| Download | `🎉 Good luck with your interview!` |

---

## Implementation Notes

1. **When to show prompts:** After every major action (research, generation, edit, download)
2. **Formatting:** Use emoji sparingly for visual hierarchy
3. **Personalization:** Include company name and role when available
4. **Context-awareness:** Only show relevant options based on current state
5. **Cost transparency:** Always mention cost for AI image generation

## Color Reference

When user asks about colors:
- Background: Dark Navy #1A1A2E
- Text: White #FFFFFF
- Relevance label: Adobe Red #EC1C24
- Accent: Orange #FF9900
