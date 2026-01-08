# Dev-Sandbox Development Process

This document establishes the standard development process for all projects in the dev-sandbox repository. The core principle is: **build workflows as you work**.

## Core Principle

When an AI assistant performs tasks on a project, it should:
1. Complete the requested task
2. Document the workflow used to complete it
3. Store the workflow in the project's `workflows/` directory

This creates a library of reusable procedures that ensure consistency across sessions and between different AI assistants.

## Project Structure

Every project in dev-sandbox should have:

```
project-name/
├── src/                    # Source code
├── workflows/              # Documented workflows (NEW)
│   ├── README.md           # Index of available workflows
│   └── [workflow-name].md  # Individual workflow files
├── SKILL.md                # Skill definition for Claude Code
└── ...
```

## Workflow Documentation Standard

### When to Create a Workflow

Create a new workflow document when:
- Performing a multi-step task for the first time
- A task requires specific scripts or commands in sequence
- The task might be repeated in future sessions
- The task involves project-specific knowledge or patterns

### Workflow File Template

Each workflow should follow this structure:

```markdown
# Workflow: [Name]

## Purpose
[What this workflow accomplishes - 1-2 sentences]

## When to Use
[Trigger phrases or conditions that indicate this workflow applies]
- "User says X..."
- "When condition Y..."

## Prerequisites
[Required files, sessions, state, or dependencies]

## Steps

### Step 1: [Action Name]
```bash
[exact command to run]
```
**Expected output:** [what to expect]
**Notes:** [any important details]

### Step 2: [Action Name]
...

## Verification
[How to confirm the workflow completed successfully]
- [ ] Checklist item 1
- [ ] Checklist item 2

## Troubleshooting
[Common issues and how to fix them]

### Issue: [Problem]
**Solution:** [How to fix]

## Scripts Used
[List of scripts this workflow uses]

## Related Workflows
[Links to related workflow documents]
```

## Development Loop

For each user request:

```
1. USER REQUEST
      ↓
2. IDENTIFY TASK
   - Match to existing workflow? → Follow workflow
   - New task type? → Continue to step 3
      ↓
3. PERFORM TASK
   - Execute required steps
   - Note commands and scripts used
   - Track any issues encountered
      ↓
4. VERIFY RESULTS
   - Confirm task completed successfully
   - Check output matches expectations
      ↓
5. DOCUMENT WORKFLOW (if new)
   - Create workflow file in project/workflows/
   - Follow template structure
   - Include troubleshooting from any issues hit
      ↓
6. UPDATE TODO LIST
   - Mark completed tasks
   - Add any follow-up items discovered
```

## Directory-Specific Workflows

Some workflows apply at the dev-sandbox level rather than project level:

```
dev-sandbox/
├── workflows/                    # Dev-sandbox level workflows
│   ├── deploy-to-skills.md       # Deploying any project to skills
│   ├── sync-to-execution.md      # Syncing project scripts
│   └── new-project-setup.md      # Creating new projects
├── projects/
│   └── [project]/workflows/      # Project-specific workflows
```

## Integration with DOE Architecture

Workflows complement the Directive-Orchestration-Execution architecture:

| Layer | Role | Workflows |
|-------|------|-----------|
| **Directive** | SOPs in `directives/` | Reference workflows for implementation details |
| **Orchestration** | AI decision-making | Use workflows as step-by-step guides |
| **Execution** | Python scripts in `execution/` | Workflows document which scripts to call and in what order |

## Example: Interview Prep Project

The interview-prep project demonstrates this process:

```
interview-prep-pptx/
├── workflows/
│   ├── README.md
│   ├── reformat-experience-slides.md   # Created after reformatting task
│   ├── live-editing-session.md         # Created after live edit task
│   ├── generate-presentation.md        # Full generation workflow
│   └── template-mode.md                # Continue from existing PPTX
├── src/
│   ├── pptx_generator.py
│   ├── live_editor.py
│   └── ...
└── SKILL.md
```

## Benefits

1. **Consistency** - Same task produces same results every time
2. **Learning** - Troubleshooting captured for future reference
3. **Handoff** - New sessions or assistants can continue work
4. **Debugging** - Known-good procedures to reference
5. **Iteration** - Workflows improve over time with learnings

## Maintaining Workflows

- **Update** workflows when you discover better approaches
- **Add troubleshooting** when you encounter new issues
- **Deprecate** workflows that are superseded by new scripts
- **Reference** related workflows to build a connected knowledge base
