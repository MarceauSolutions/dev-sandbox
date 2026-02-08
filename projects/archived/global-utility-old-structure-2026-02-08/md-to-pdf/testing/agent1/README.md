# Agent 1 Workspace: Header & TOC Edge Cases

**Focus**: Table of contents generation and header handling

## Test Scenarios

1. **Duplicate headers** - Multiple headers with identical text
2. **Special characters in headers** - Headers containing `?, !, @, #, $, %, &, *, (, ), [, ], {, }`
3. **Very long headers** - Headers exceeding 100 characters
4. **Deep nesting** - All 6 header levels (H1-H6) with proper hierarchy

## Expected Outputs

- Unique anchor IDs for duplicate headers
- Sanitized anchors for special characters
- Properly wrapped long headers
- Complete TOC hierarchy with correct indentation

## Files to Create

- Test markdown files for each scenario
- Generated PDFs
- FINDINGS.md documenting all issues

## Status

⏳ Waiting for agent to begin testing...
