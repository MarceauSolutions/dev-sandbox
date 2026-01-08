# Interview Prep PowerPoint - Workflows

This directory contains documented workflows for common tasks in the Interview Prep PowerPoint Generator project. Each workflow describes the exact steps, scripts, and commands to perform a specific task consistently.

## Workflow Index

| Workflow | Description | When to Use |
|----------|-------------|-------------|
| [generate-presentation.md](generate-presentation.md) | Full workflow from research to final PPTX | User requests new interview prep presentation |
| [template-mode.md](template-mode.md) | Continue editing from existing presentation | User has existing PPTX to modify |
| [live-editing-session.md](live-editing-session.md) | Real-time editing while user views presentation | User has presentation open and wants to watch changes |
| [reformat-experience-slides.md](reformat-experience-slides.md) | Standardize experience slides to match a target layout | User says "make slides X look like slide Y" |
| [apply-consistent-theme.md](apply-consistent-theme.md) | Apply dark navy theme across all slides | User wants consistent colors/styling |
| [add-images-to-slides.md](add-images-to-slides.md) | Add images from previous session to slides | User has exp_img_*.jpeg files to add |

## User Guidance

**IMPORTANT:** At key workflow stages, show the user suggested next steps. See [USER_PROMPTS.md](../USER_PROMPTS.md) for the complete guide.

### Quick Reference - What to Show Users

| After This Action | Show These Options |
|-------------------|-------------------|
| Research completes | "Generate presentation", "Add AI images", "Show summary" |
| Presentation created | "Open it", "List slides", "Apply consistent theme", "Edit slide X" |
| During editing | "Change text", "Apply theme", "Make slide X look like Y" |
| User is satisfied | "Download as PowerPoint", "Download as PDF" |

### Download Commands
```bash
# Download to ~/Downloads as PowerPoint
python execution/download_pptx.py --input .tmp/interview_prep_company.pptx

# Download with custom name
python execution/download_pptx.py --input .tmp/interview_prep_company.pptx --name "Google Interview Prep"

# Download as PDF (requires LibreOffice)
python execution/download_pptx.py --input .tmp/interview_prep_company.pptx --format pdf
```

## How to Use Workflows

1. **Identify the task** - Match user request to a workflow
2. **Read the workflow** - Follow the documented steps exactly
3. **Execute commands** - Run the scripts in order
4. **Verify results** - Check output matches expected results
5. **Update workflow** - If you learn something new, update the workflow

## Creating New Workflows

When performing a new type of task:

1. Document each step as you perform it
2. Note which scripts/commands you use
3. Record any parameters or variations
4. Add error handling discovered during execution
5. Create the workflow file after completing the task

## Workflow File Template

```markdown
# Workflow: [Name]

## Purpose
[What this workflow accomplishes]

## When to Use
[Trigger phrases or conditions]

## Prerequisites
[Required files, sessions, or state]

## Steps

### Step 1: [Name]
```bash
[command]
```
**Expected output:** [what to expect]

### Step 2: [Name]
...

## Verification
[How to confirm success]

## Troubleshooting
[Common issues and fixes]

## Related Workflows
[Links to related workflows]
```
