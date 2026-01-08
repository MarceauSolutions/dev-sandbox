# Interview Prep AI Assistant - Expanded Scope

## Vision

Transform from "Interview Prep PowerPoint Builder" → **"Interview Prep AI Assistant"**

A conversational AI assistant that helps with ALL aspects of interview preparation, routed through a single chat interface. The user describes what they need, and the assistant interprets and executes the appropriate workflow.

## Architecture: Unified Conversational Interface

```
User Input (natural language)
        │
        ▼
┌─────────────────────────────────────┐
│   INTENT ROUTER (Claude/AI)         │
│   - Interprets user request         │
│   - Transforms to structured prompt │
│   - Routes to appropriate workflow  │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         CAPABILITIES                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  📊 RESEARCH          │  📝 DOCUMENTS         │  🎤 PRACTICE         │
│  ─────────────────    │  ─────────────────    │  ─────────────────   │
│  • Company research   │  • PowerPoint         │  • Mock interview    │
│  • Role analysis      │  • PDF summary        │  • Q&A practice      │
│  • Industry trends    │  • Cheat sheet        │  • Elevator pitch    │
│  • Interviewer lookup │  • Talking points     │  • STAR responses    │
│                       │  • Cover letter       │                      │
│                                                                      │
│  📅 LOGISTICS         │  💡 COACHING          │  📈 TRACKING         │
│  ─────────────────    │  ─────────────────    │  ─────────────────   │
│  • Calendar prep      │  • Feedback on        │  • Interview log     │
│  • Reminder setup     │    responses          │  • Follow-up         │
│  • Day-of checklist   │  • Body language tips │    reminders         │
│  • Travel planning    │  • Salary negotiation │  • Offer comparison  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Core Use Cases

### 1. Research & Preparation (Existing + Enhanced)

| User Says | Assistant Does |
|-----------|----------------|
| "Research Google for a PM interview" | Run interview_research.py → return summary |
| "What does [Company] do?" | Company overview with recent news |
| "What questions might they ask?" | Common questions + STAR-formatted answers |
| "Look up my interviewer Sarah Smith" | LinkedIn research, find common ground |
| "What's the salary range for this role?" | Salary benchmarking (Levels.fyi, Glassdoor) |

### 2. Document Generation (Existing + New Outputs)

| User Says | Assistant Does |
|-----------|----------------|
| "Create a PowerPoint presentation" | Generate full PPTX (existing capability) |
| "Give me a one-page cheat sheet" | Generate PDF summary for quick review |
| "Create talking points I can print" | Bullet-point PDF of key messages |
| "Write a thank-you email template" | Generate post-interview follow-up |
| "Draft a cover letter for this role" | Generate tailored cover letter |
| "Make flashcards of likely questions" | Generate Q&A flashcard PDF |

### 3. Mock Interview Practice (NEW - High Value)

| User Says | Assistant Does |
|-----------|----------------|
| "Practice interview with me" | Start interactive mock interview |
| "Be my interviewer for Google" | Role-play as company interviewer |
| "Ask me behavioral questions" | STAR-format behavioral interview |
| "Quiz me on technical questions" | Technical screen simulation |
| "Practice my elevator pitch" | Listen and provide feedback |
| "How was that answer?" | Evaluate response, suggest improvements |

**Mock Interview Flow:**
```
1. User: "Practice interview for Google PM role"
2. Assistant: Sets context (interviewer persona, company culture)
3. Assistant: "Let's begin. Tell me about yourself..."
4. User: [Responds]
5. Assistant: Evaluates, asks follow-up OR moves to next question
6. [Repeat for 5-10 questions]
7. Assistant: Provides overall feedback and improvement areas
```

### 4. Logistics & Planning (NEW)

| User Says | Assistant Does |
|-----------|----------------|
| "My interview is Tuesday at 2pm" | Create calendar event + prep reminders |
| "Set up reminders for my interview" | Day-before, morning-of, 1-hour-before alerts |
| "Create a day-of checklist" | Printable checklist (outfit, docs, directions) |
| "What should I bring?" | Customized list based on interview type |

### 5. Coaching & Feedback (NEW)

| User Says | Assistant Does |
|-----------|----------------|
| "How do I answer 'why this company?'" | Craft personalized answer with examples |
| "Review my answer to [question]" | Evaluate and suggest improvements |
| "Help me negotiate salary" | Salary negotiation scripts and strategy |
| "What red flags should I watch for?" | Company/role red flag checklist |

### 6. Tracking & Follow-up (NEW)

| User Says | Assistant Does |
|-----------|----------------|
| "Log this interview" | Add to interview tracking spreadsheet |
| "Compare my offers" | Side-by-side offer comparison |
| "Write a follow-up email" | Generate personalized thank-you note |
| "They haven't responded in a week" | Suggest follow-up approach |

---

## Output Formats

| Format | Use Case | Script |
|--------|----------|--------|
| **PowerPoint** | Full presentation for prep/presenting | `pptx_generator.py` (exists) |
| **PDF Summary** | One-page cheat sheet | `pdf_cheat_sheet.py` (NEW) |
| **Talking Points** | Printable bullet points | `talking_points_pdf.py` (NEW) |
| **Flashcards** | Q&A practice cards | `flashcard_generator.py` (NEW) |
| **Email Templates** | Thank-you, follow-up | `email_templates.py` (NEW) |
| **Cover Letter** | Tailored application letter | `cover_letter.py` (NEW) |
| **Checklist PDF** | Day-of preparation list | `interview_checklist.py` (NEW) |

---

## Mock Interview Implementation

### Architecture

```python
# mock_interview.py

class MockInterviewer:
    """Simulates an interviewer from the target company."""

    def __init__(self, company: str, role: str, interview_type: str):
        self.company = company
        self.role = role
        self.interview_type = interview_type  # behavioral, technical, case
        self.questions_asked = []
        self.responses = []
        self.feedback = []

    def get_next_question(self) -> str:
        """Get next question based on interview type and progress."""
        pass

    def evaluate_response(self, response: str) -> dict:
        """Evaluate user's response and provide feedback."""
        return {
            "score": 7,  # 1-10
            "strengths": ["Good use of STAR format", "Specific metrics"],
            "improvements": ["Could elaborate on learnings"],
            "follow_up": "Can you tell me more about the impact?"
        }

    def get_summary(self) -> dict:
        """Get overall interview performance summary."""
        pass
```

### Interview Types

| Type | Focus | Question Style |
|------|-------|----------------|
| **Behavioral** | Past experiences, soft skills | "Tell me about a time when..." |
| **Technical** | Domain knowledge, problem-solving | Coding, system design, analysis |
| **Case** | Business acumen, structured thinking | "How would you approach..." |
| **Cultural** | Values fit, motivation | "Why [Company]?", "Where do you see yourself..." |

### Feedback Criteria

- **STAR Format**: Situation, Task, Action, Result
- **Specificity**: Concrete examples vs. generalities
- **Relevance**: Connection to role requirements
- **Conciseness**: Appropriate length (1-2 minutes)
- **Energy/Enthusiasm**: Engagement level (for coaching)

---

## Implementation Priority

### Phase 1: Core Enhancements (Immediate)
1. **Mock Interview** - Highest user value, differentiator
2. **PDF Cheat Sheet** - Quick output alternative to PPTX
3. **Intent Router** - Unified chat interface

### Phase 2: Additional Outputs (Next)
4. **Flashcard Generator** - Q&A practice
5. **Email Templates** - Follow-up automation
6. **Talking Points PDF** - Print-friendly format

### Phase 3: Advanced Features (Later)
7. **Interviewer Lookup** - LinkedIn integration
8. **Salary Benchmarking** - External API integration
9. **Interview Tracking** - Google Sheets logging
10. **Calendar Integration** - Reminder setup

---

## File Structure (Proposed)

```
interview-prep/                    # Renamed from interview-prep-pptx
├── src/
│   ├── interview_research.py      # Existing - company/role research
│   ├── pptx_generator.py          # Existing - PowerPoint generation
│   ├── pptx_editor.py             # Existing - PowerPoint editing
│   ├── mock_interview.py          # NEW - Interactive mock interviews
│   ├── pdf_outputs.py             # NEW - Cheat sheet, flashcards, etc.
│   ├── email_templates.py         # NEW - Thank-you, follow-up emails
│   ├── intent_router.py           # NEW - Route user requests
│   └── interview_assistant.py     # NEW - Main entry point
├── workflows/
│   ├── generate-presentation.md   # Existing
│   ├── mock-interview.md          # NEW
│   ├── quick-outputs.md           # NEW - PDF, flashcards, etc.
│   └── coaching-session.md        # NEW
├── templates/
│   ├── cheat_sheet.html           # Template for PDF generation
│   ├── flashcard.html             # Template for flashcards
│   └── thank_you_email.txt        # Email template
├── VERSION
├── CHANGELOG.md
├── SKILL.md
└── USER_PROMPTS.md
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| User can complete full prep in one chat session | Yes |
| Mock interview feels realistic | User feedback |
| Output generation < 30 seconds | All formats |
| User knows next steps at every stage | Guidance prompts |

---

## Questions to Resolve

1. **Scope of mock interview**: How many questions? Time limit?
2. **Feedback depth**: Real-time vs. end-of-session summary?
3. **Voice support**: Should mock interview support voice input? (Future)
4. **Persistence**: Save interview history across sessions?
5. **Multi-company**: Track prep for multiple interviews simultaneously?

---

## Next Steps

1. Build `mock_interview.py` with basic behavioral interview flow
2. Create `pdf_outputs.py` for cheat sheet generation
3. Update SKILL.md with expanded capabilities
4. Test mock interview flow end-to-end
5. Create workflow documentation for new capabilities
