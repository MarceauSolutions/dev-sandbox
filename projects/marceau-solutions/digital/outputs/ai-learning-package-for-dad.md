# CLAUDE CODE
## Installation, Operation & Maintenance Manual

**For AI-Assisted Software Development Systems**

```
╔══════════════════════════════════════════════════════════════╗
║  MARCEAU TECHNICAL PUBLICATIONS                              ║
║  First Edition — March 2026                                  ║
║  Manual No. MS-2026-CC-001                                   ║
╚══════════════════════════════════════════════════════════════╝
```

**Applicable Models:**
- Claude 4 Opus (Primary)
- Claude 4 Sonnet (Economy)
- VS Code 1.85+

---

# TABLE OF CONTENTS

| Section | Description | Page |
|---------|-------------|------|
| 1 | General Information | 1 |
| 2 | Theory of Operation | 2 |
| 3 | Tools & Equipment Required | 3 |
| 4 | Installation Procedures | 4 |
| 5 | Initial Startup & Break-In | 6 |
| 6 | Operating Procedures | 8 |
| 7 | Troubleshooting | 12 |
| 8 | Specifications | 14 |
| 9 | Maintenance Schedule | 15 |

---

# SECTION 1: GENERAL INFORMATION

## 1.1 Introduction

This manual covers the installation, operation, and maintenance of Claude Code AI development systems. Procedures are applicable to macOS and Windows platforms.

## 1.2 How to Use This Manual

1. Read the entire section before beginning work
2. Gather all required tools before starting
3. Follow procedures in order — do not skip steps
4. Refer to Section 7 (Troubleshooting) if problems occur

## 1.3 Safety Warnings

```
┌─────────────────────────────────────────────────────────────┐
│  ⚠️  CAUTION                                                │
│                                                             │
│  AI systems may generate incorrect information with high    │
│  confidence. Always verify critical outputs before use.     │
│  The operator is responsible for final quality control.     │
└─────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────┐
│  ⚠️  WARNING                                                │
│                                                             │
│  Do not share API keys or authentication tokens publicly.   │
│  Unauthorized access may result in unexpected charges.      │
└─────────────────────────────────────────────────────────────┘
```

## 1.4 Abbreviations Used in This Manual

| Abbrev. | Meaning |
|---------|---------|
| LLM | Large Language Model |
| API | Application Programming Interface |
| IDE | Integrated Development Environment |
| CLI | Command Line Interface |
| GUI | Graphical User Interface |
| Cmd | Command key (Mac) |
| Ctrl | Control key (Windows) |

---

# SECTION 2: THEORY OF OPERATION

## 2.1 System Overview

The Claude Code system consists of three primary components:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   OPERATOR      │────▶│   VS CODE       │────▶│   CLAUDE        │
│   (You)         │◀────│   (Interface)   │◀────│   (AI Engine)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
    Provides              Transmits               Processes
    instructions          requests &              & generates
    & feedback            responses               code/text
```

## 2.2 How the AI Engine Works

The Claude AI operates on a **pattern recognition** principle:

1. Training data (books, code, websites) is processed
2. Statistical relationships between words are learned
3. When prompted, the model predicts likely next words
4. Output is generated token-by-token until complete

**Note:** The AI does not "understand" in the human sense. It recognizes patterns and generates statistically probable responses.

## 2.3 The Context Window

The AI maintains a **context window** — a working memory of approximately 200,000 tokens (≈150,000 words).

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTEXT WINDOW                           │
├─────────────────────────────────────────────────────────────┤
│  System Instructions (CLAUDE.md)     ████░░░░░░░░░░░  10%   │
│  Current Files                       ██████░░░░░░░░░  25%   │
│  Conversation History                ████████░░░░░░░  40%   │
│  Available for New Content           ██████████████░  65%   │
└─────────────────────────────────────────────────────────────┘
```

When the window fills, older content is dropped. Plan accordingly.

---

# SECTION 3: TOOLS & EQUIPMENT REQUIRED

## 3.1 Required Tools

| Item | Specification | Source |
|------|--------------|--------|
| Computer | Mac or Windows, 8GB+ RAM | — |
| Internet Connection | Stable broadband | — |
| VS Code | Version 1.85 or later | code.visualstudio.com |
| Claude Code Extension | Latest version | VS Code Marketplace |
| Anthropic Account | Pro ($20/mo) or API credits | anthropic.com |

## 3.2 Optional but Recommended

| Item | Purpose |
|------|---------|
| Git | Version control |
| Node.js | Running JavaScript projects |
| Python 3.9+ | Running Python projects |
| Second Monitor | Viewing output while editing |

## 3.3 Workspace Preparation

Before beginning installation:

1. Clear at least 2GB disk space
2. Close unnecessary applications
3. Ensure stable internet connection
4. Have Anthropic account credentials ready

---

# SECTION 4: INSTALLATION PROCEDURES

## 4.1 Installing VS Code

**Procedure:**

1. Open web browser
2. Navigate to `https://code.visualstudio.com`
3. Click "Download for [Your OS]"
4. Locate downloaded file in Downloads folder
5. **Mac:** Drag to Applications folder
   **Windows:** Run installer, accept defaults
6. Launch VS Code
7. Verify installation by confirming main window appears

```
┌─────────────────────────────────────────────────────────────┐
│  ✓ CHECKPOINT                                               │
│                                                             │
│  VS Code window should display:                             │
│  • Welcome tab                                              │
│  • Sidebar on left                                          │
│  • Activity bar (icons) on far left                         │
└─────────────────────────────────────────────────────────────┘
```

## 4.2 Installing Claude Code Extension

**Procedure:**

1. In VS Code, locate Activity Bar (left edge)
2. Click Extensions icon (four squares)
3. In search box, type: `Claude`
4. Locate "Claude" by Anthropic
5. Click "Install"
6. Wait for installation to complete (10-30 seconds)
7. Claude icon appears in Activity Bar

**Fig. 4-1: Extension Installation**
```
    ┌──────────────────────────────────────┐
    │  🔍 Claude                           │
    ├──────────────────────────────────────┤
    │  Claude                              │
    │  Anthropic               [Install]   │
    │  ★★★★★ (4.8) | 500K+ installs        │
    └──────────────────────────────────────┘
```

## 4.3 Authentication

**Procedure:**

1. Click Claude icon in Activity Bar
2. Click "Sign In" button
3. Browser opens to Anthropic login page
4. Enter credentials or create account
5. Authorize VS Code access
6. Return to VS Code
7. Verify "Signed in" status appears

```
┌─────────────────────────────────────────────────────────────┐
│  ⚠️  NOTE                                                   │
│                                                             │
│  Subscription required:                                     │
│  • Claude Pro: $20/month (recommended for learning)         │
│  • API credits: Pay-per-use (for production)                │
└─────────────────────────────────────────────────────────────┘
```

## 4.4 Creating Your First Project

**Procedure:**

1. Create folder on desktop: `my-first-project`
2. In VS Code: File → Open Folder
3. Navigate to and select `my-first-project`
4. Click "Open"
5. If prompted "Trust authors?", click "Yes"

**Result:** Empty project workspace ready for use.

---

# SECTION 5: INITIAL STARTUP & BREAK-IN

## 5.1 Opening the Claude Interface

**Procedure:**

1. Press keyboard shortcut:
   - **Mac:** `Cmd + Shift + P`
   - **Windows:** `Ctrl + Shift + P`
2. Type: `Claude`
3. Select: "Claude: Open Chat"
4. Chat panel appears on right side of window

**Fig. 5-1: Chat Panel Location**
```
┌────────────────────────────────────────────────────────────────┐
│  VS CODE WINDOW                                                │
├──────────┬──────────────────────────────┬─────────────────────┤
│          │                              │                     │
│  FILE    │      EDITOR AREA             │    CLAUDE CHAT      │
│  TREE    │                              │                     │
│          │                              │    ┌─────────────┐  │
│          │                              │    │ Your msg... │  │
│          │                              │    └─────────────┘  │
│          │                              │                     │
└──────────┴──────────────────────────────┴─────────────────────┘
```

## 5.2 First Test — "Hello World"

This procedure verifies proper system operation.

**Procedure:**

1. In Claude chat panel, type exactly:
```
Create an HTML file called index.html that displays 
"Hello World" in large blue text on a white background.
```

2. Press Enter or click Send
3. Wait for response (5-15 seconds)
4. Observe:
   - Claude creates `index.html` in your project
   - File appears in left sidebar
   - Code is displayed in response

**Expected Result:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Hello World</title>
</head>
<body>
    <h1 style="color: blue;">Hello World</h1>
</body>
</html>
```

## 5.3 Verifying Output

**Procedure:**

1. Locate `index.html` in left sidebar
2. Right-click the file
3. Select "Open with Live Server" 
   - If not available, select "Reveal in Finder/Explorer"
   - Double-click file to open in browser
4. Verify "Hello World" displays in blue

```
┌─────────────────────────────────────────────────────────────┐
│  ✓ SYSTEM CHECK COMPLETE                                    │
│                                                             │
│  If text displays correctly, proceed to Section 6.          │
│  If errors occur, refer to Section 7 (Troubleshooting).     │
└─────────────────────────────────────────────────────────────┘
```

---

# SECTION 6: OPERATING PROCEDURES

## 6.1 The Operating Cycle

All Claude Code operations follow this cycle:

```
    ┌──────────────┐
    │  1. PROMPT   │ ◀─────────────────────────┐
    │  (You type)  │                           │
    └──────┬───────┘                           │
           │                                   │
           ▼                                   │
    ┌──────────────┐                           │
    │  2. PROCESS  │                           │
    │  (Claude     │                           │
    │   works)     │                           │
    └──────┬───────┘                           │
           │                                   │
           ▼                                   │
    ┌──────────────┐                           │
    │  3. OUTPUT   │                           │
    │  (Code/text  │                           │
    │   generated) │                           │
    └──────┬───────┘                           │
           │                                   │
           ▼                                   │
    ┌──────────────┐      ┌──────────────┐     │
    │  4. REVIEW   │─────▶│  5. REFINE   │─────┘
    │  (You check) │  No  │  (Request    │
    │              │ Good │   changes)   │
    └──────┬───────┘      └──────────────┘
           │ Good
           ▼
    ┌──────────────┐
    │  6. ACCEPT   │
    │  (Move on)   │
    └──────────────┘
```

## 6.2 Proper Prompting Technique

### 6.2.1 Prompt Structure

A complete prompt contains:

| Element | Description | Example |
|---------|-------------|---------|
| **Context** | What exists now | "I have a contact form..." |
| **Task** | What to do | "Add email validation..." |
| **Constraints** | Limitations | "Keep it under 50 lines..." |
| **Format** | How to deliver | "Comment each section..." |

### 6.2.2 Example — Good Prompt

```
CONTEXT: I have a basic HTML contact form with name, 
email, and message fields.

TASK: Add JavaScript validation that:
- Checks all fields are filled
- Validates email format
- Shows error messages below each field

CONSTRAINTS: 
- No external libraries
- Must work in all modern browsers

FORMAT: Add the JavaScript in a <script> tag at the 
bottom of the HTML file. Comment each validation function.
```

### 6.2.3 Example — Poor Prompt (Avoid)

```
make it work better
```

**Problem:** No context, vague task, no constraints.

## 6.3 Iterative Refinement

When output requires adjustment:

**Procedure:**

1. Identify specific issue
2. Describe what's wrong
3. Describe what you want instead
4. Request specific change

**Example:**
```
The submit button is blue, but I need it to be green 
(#28a745) to match my brand colors. Change only the 
button color, leave everything else unchanged.
```

## 6.4 Reading Files Before Editing

Before modifying existing code:

**Procedure:**

1. Ask Claude to read the file first:
```
Read the file src/utils.js and explain what each 
function does.
```

2. Review Claude's explanation
3. Then request specific changes

```
┌─────────────────────────────────────────────────────────────┐
│  ⚠️  CAUTION                                                │
│                                                             │
│  Modifying code without understanding it may cause          │
│  cascading failures. Always read before editing.            │
└─────────────────────────────────────────────────────────────┘
```

## 6.5 Common Operations Quick Reference

| Task | Command |
|------|---------|
| Create new file | "Create a file called X.js that does Y" |
| Edit existing file | "In file X.js, change the function Y to do Z" |
| Explain code | "Explain what this file does" |
| Fix error | "I'm getting this error: [paste]. Fix it." |
| Add feature | "Add a feature that does X" |
| Remove feature | "Remove the Y functionality from this file" |
| Refactor | "Refactor this code to be more readable" |

---

# SECTION 7: TROUBLESHOOTING

## 7.1 Diagnostic Procedure

When problems occur:

1. **Identify** — What exactly went wrong?
2. **Isolate** — When did it last work?
3. **Document** — Copy exact error messages
4. **Research** — Check table below
5. **Resolve** — Apply fix
6. **Verify** — Confirm problem is solved

## 7.2 Common Problems & Solutions

### Problem: Claude not responding

| Check | Action |
|-------|--------|
| Internet connection | Open browser, load any website |
| Authentication | Click Claude icon, verify signed in |
| Service status | Check status.anthropic.com |
| Extension | Disable and re-enable extension |

### Problem: "Context window exceeded"

| Cause | Solution |
|-------|----------|
| Conversation too long | Start new chat session |
| Files too large | Work with smaller sections |
| Too many files open | Close unnecessary files |

### Problem: Generated code has errors

**Procedure:**

1. Copy the exact error message
2. Send to Claude:
```
When I run this code, I get the following error:

[PASTE ERROR MESSAGE HERE]

The relevant code is in [FILENAME]. Please fix.
```

3. Apply Claude's fix
4. Test again
5. Repeat if necessary

### Problem: Output not what expected

**Procedure:**

1. Be more specific in prompt
2. Provide example of desired output
3. Break request into smaller steps
4. Review and iterate

## 7.3 Error Message Reference

| Error | Meaning | Solution |
|-------|---------|----------|
| `401 Unauthorized` | Authentication failed | Re-sign in |
| `429 Rate Limited` | Too many requests | Wait 60 seconds |
| `500 Server Error` | Anthropic issue | Wait and retry |
| `Context length exceeded` | Window full | Start new session |

---

# SECTION 8: SPECIFICATIONS

## 8.1 Claude Model Specifications

| Specification | Claude 4 Opus | Claude 4 Sonnet |
|---------------|---------------|-----------------|
| Context Window | 200K tokens | 200K tokens |
| Max Output | 4,096 tokens | 4,096 tokens |
| Speed | Standard | Fast |
| Capability | Highest | High |
| Cost | Higher | Lower |
| Recommended For | Complex tasks | Simple tasks |

## 8.2 Token Estimation

| Content Type | Tokens per 1,000 chars |
|--------------|------------------------|
| English text | ~250 |
| Code | ~300 |
| JSON/Data | ~350 |

**Rule of thumb:** 1 token ≈ 4 characters or ¾ of a word

## 8.3 Keyboard Shortcuts

| Action | Mac | Windows |
|--------|-----|---------|
| Open command palette | Cmd+Shift+P | Ctrl+Shift+P |
| Open file quickly | Cmd+P | Ctrl+P |
| Save file | Cmd+S | Ctrl+S |
| Undo | Cmd+Z | Ctrl+Z |
| Redo | Cmd+Shift+Z | Ctrl+Y |
| Find in file | Cmd+F | Ctrl+F |
| Find in project | Cmd+Shift+F | Ctrl+Shift+F |
| Toggle sidebar | Cmd+B | Ctrl+B |

---

# SECTION 9: MAINTENANCE SCHEDULE

## 9.1 Daily Checks

| Item | Procedure |
|------|-----------|
| Save work | Cmd+S / Ctrl+S before closing |
| Commit changes | If using Git, commit daily |

## 9.2 Weekly Maintenance

| Item | Procedure |
|------|-----------|
| Update VS Code | Help → Check for Updates |
| Update extensions | Extensions panel → Update All |
| Clean workspace | Delete unused files |
| Review context | Start fresh chat if sluggish |

## 9.3 Monthly Maintenance

| Item | Procedure |
|------|-----------|
| Review subscription | Check Anthropic billing |
| Backup projects | Copy to external drive or cloud |
| Update documentation | Keep CLAUDE.md current |

---

# APPENDIX A: VIDEO TRAINING RESOURCES

## Fundamentals (Complete in Order)

| # | Topic | Duration | URL |
|---|-------|----------|-----|
| 1 | How LLMs Work | 10 min | youtube.com/watch?v=wjZofJX0v4M |
| 2 | VS Code Basics | 15 min | youtube.com/watch?v=VqCgcpAypFQ |
| 3 | Git Basics | 30 min | youtube.com/watch?v=8JJ101D3knE |

## Supplementary Reading

- Anthropic Prompting Guide: docs.anthropic.com/claude/docs/prompt-engineering

---

# APPENDIX B: QUICK START CARD

```
╔═══════════════════════════════════════════════════════════════╗
║  CLAUDE CODE — QUICK START CARD                               ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  OPEN CHAT:     Cmd+Shift+P → "Claude: Open Chat"             ║
║                                                               ║
║  GOOD PROMPT:   Context + Task + Constraints + Format         ║
║                                                               ║
║  BAD PROMPT:    "make it work" (too vague)                    ║
║                                                               ║
║  FIX ERRORS:    Copy exact error → Paste to Claude → Apply    ║
║                                                               ║
║  STUCK?         1) Be more specific  2) Break into steps      ║
║                 3) Ask Claude to explain first                ║
║                                                               ║
║  REMEMBER:      You = Architect    Claude = Builder           ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

---

**END OF MANUAL**

*Marceau Technical Publications — Manual No. MS-2026-CC-001*
*First Edition — March 2026*
