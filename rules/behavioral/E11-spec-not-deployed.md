---
rule: E11
name: Spec Written != Deployed
hook: none — judgment required
trigger: After writing any specification, design document, JSON template, or architecture doc
---

## Rule

A specification document is NOT a deliverable. A JSON template is NOT a deployed system. A PDF describing a feature is NOT a working feature. Nothing is "done" until it is running on its target platform and William can interact with it without Claude's help.

## Why it exists

The entire accountability system was "built" as markdown files and never deployed to EC2 or n8n. William woke up expecting it to work and it didn't. The lesson: writing about a system is not the same as building it.

## The Deployment Pipeline (every project must complete all steps)

```
Research → Design → Build → Deploy → Test on target → Verify user can interact → THEN mark complete
```

Never tell William something "is set up" when it's only been:
- Designed (spec doc written)
- Generated (PDF created)
- Templated (JSON structure defined)
- Coded locally (script runs on Mac)
- Committed (in git but not deployed)

## How to apply

Before saying a system is "done" or "set up":
1. Is it running on its target platform? (EC2? n8n? Telegram?)
2. Can William interact with it from his phone RIGHT NOW without opening VS Code?
3. Has it processed real data (not test data)?
4. Is it documented in SYSTEM-STATE.md?

If any answer is no → it is NOT done.

## Status vocabulary

| What you can say | What you cannot say |
|------------------|---------------------|
| "The spec is written" | "It's set up" (when only spec'd) |
| "The script runs locally" | "It's deployed" (when not on EC2) |
| "The workflow is built" | "It's live" (when not tested end-to-end) |
| "Ready for deployment" | "Done" (when not verified by William) |

## Examples

- Designed n8n workflow on paper → "spec is written, ready to build in n8n" (not "workflow is set up")
- Python script runs on Mac → "logic is built, needs to be wired to Clawdbot" (not "tool is ready")
- JSON template created → "template is defined, needs to be added to branded_pdf_engine.py" (not "template is done")
