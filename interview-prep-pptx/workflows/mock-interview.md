# Workflow: Mock Interview Practice

## Purpose
Conduct interactive mock interviews to help users practice answering interview questions with real-time feedback.

## When to Use
- User says "practice interview with me"
- User says "ask me interview questions"
- User says "do a mock interview"
- User wants to practice before their interview

## Prerequisites
- Company and role context (ask if not provided)
- Optionally: existing research JSON for more context

## Steps

### 1. Confirm Context
```
User: "Practice interview with me"

You: What company and role would you like to practice for?
- If already discussed: "Would you like to practice for the [Company] [Role] interview we researched?"
```

### 2. Choose Interview Type
```
Available types:
- behavioral (default) - STAR format questions about past experiences
- technical - Domain-specific questions for the role
- case - Business problem-solving scenarios
- cultural - Motivation and fit questions
- mixed - Combination of all types
```

### 3. Start Mock Interview

**With existing research:**
```bash
python interview-prep-pptx/src/mock_interview.py \
  --company "{COMPANY}" \
  --role "{ROLE}" \
  --type behavioral \
  --research .tmp/interview_research_{company_slug}.json
```

**Without research:**
```bash
python interview-prep-pptx/src/mock_interview.py \
  --company "{COMPANY}" \
  --role "{ROLE}" \
  --type behavioral
```

**Quick 5-question practice:**
```bash
python interview-prep-pptx/src/mock_interview.py \
  --company "{COMPANY}" \
  --role "{ROLE}" \
  --questions 5
```

### 4. During the Interview

The mock interview will:
1. Introduce itself as an interviewer from the company
2. Ask questions one at a time
3. Wait for user responses
4. Provide feedback after each response:
   - Score (1-10)
   - STAR format check
   - Strengths identified
   - Areas for improvement
   - Follow-up questions (optional)

### 5. After Completion

Show summary:
```
✅ Mock interview complete!

Overall Rating: [Good/Excellent/Needs Practice] ([X]/10)
STAR Format Usage: S[✓/○] T[✓/○] A[✓/○] R[✓/○]

Top Strengths:
• [Strength 1]
• [Strength 2]

Areas to Improve:
• [Improvement 1]
• [Improvement 2]

Session saved to: .tmp/mock_interview_[session_id].json
```

### 6. Offer Next Steps

```
📋 What you can do next:
• "Practice again" - Another mock interview
• "Focus on behavioral questions only"
• "Try technical questions this time"
• "Create a cheat sheet"
• "Generate presentation slides"
```

## Command Reference

| Command | Description |
|---------|-------------|
| `--company` | Company name (required) |
| `--role` | Role/position (required) |
| `--type` | Interview type: behavioral, technical, case, cultural, mixed |
| `--questions` | Number of questions (default: 7) |
| `--research` | Path to research JSON for context |
| `--api` | API mode (returns JSON for integration) |

## API Mode (For Chat Integration)

For integration with the intent router:

```bash
# Start session
python mock_interview.py --api --action start --company "Google" --role "PM"

# Get next question
python mock_interview.py --api --action ask

# Submit response and get feedback
python mock_interview.py --api --action respond --response "My answer..."

# Get summary
python mock_interview.py --api --action summary
```

## Example Session

```
MOCK INTERVIEW: Google - Product Manager
Type: Behavioral
═══════════════════════════════════════════════════

Hello! I'm excited to meet you today. I'm a hiring manager at Google
and I'll be conducting your interview for the Product Manager position.

This will be a behavioral interview with about 7 questions.
Ready to begin?

──────────────────────────────────────────────────────────────────────
Question 1:

  Tell me about yourself and why you're interested in this role.

──────────────────────────────────────────────────────────────────────

[User responds...]

──────────────────────────────────────────────────────────────────────
FEEDBACK:
  Score: 7/10

  Strengths:
    + Good overview of experience
    + Clear connection to role

  Areas to improve:
    - Could be more concise (aim for 2 minutes)
    - Add specific metrics from past work

  STAR Format: S✓ T○ A✓ R○

──────────────────────────────────────────────────────────────────────
```

## Troubleshooting

**No research context:**
- Mock interview works without research, but questions are more generic
- Consider running research first for personalized questions

**API key error:**
- Ensure ANTHROPIC_API_KEY is set in .env
- Run `source .env` before starting

**Session not saved:**
- Check .tmp/ directory exists
- Verify write permissions

## Related Workflows
- [generate-presentation.md](generate-presentation.md) - Full research and presentation
- [quick-outputs.md](quick-outputs.md) - Cheat sheet and flashcards
