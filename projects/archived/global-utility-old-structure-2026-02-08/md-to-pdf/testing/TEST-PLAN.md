# MD-to-PDF Converter: Multi-Agent Testing Plan

## Testing Strategy

Deploy 4 specialized testing agents in parallel to comprehensively test the MD-to-PDF converter across multiple edge cases.

## Test Focus Areas

### Agent 1: Header & TOC Edge Cases
**Focus**: Table of contents generation and header handling
**Scenarios**:
1. **Duplicate headers** - Multiple headers with identical text
2. **Special characters in headers** - Headers containing `?, !, @, #, $, %, &, *, (, ), [, ], {, }`
3. **Very long headers** - Headers exceeding 100 characters
4. **Deep nesting** - All 6 header levels (H1-H6) with proper hierarchy

**Expected Outputs**:
- Unique anchor IDs for duplicate headers
- Sanitized anchors for special characters
- Properly wrapped long headers
- Complete TOC hierarchy with correct indentation

**Workspace**: `projects/md-to-pdf/testing/agent1/`

---

### Agent 2: Content Formatting Edge Cases
**Focus**: Markdown element rendering
**Scenarios**:
1. **Complex tables** - Multi-column tables with merged cells, alignment variations
2. **Nested lists** - Deeply nested ordered/unordered lists (4+ levels)
3. **Code blocks** - Multiple languages (Python, JavaScript, Bash, SQL), very long lines
4. **Mixed content** - Blockquotes containing code, lists, and tables

**Expected Outputs**:
- Tables render without overflow issues
- List indentation maintains clarity
- Code blocks preserve formatting and syntax highlighting
- Mixed content renders cleanly

**Workspace**: `projects/md-to-pdf/testing/agent2/`

---

### Agent 3: Image & Link Handling
**Focus**: External resources and hyperlinks
**Scenarios**:
1. **Missing images** - References to non-existent image files
2. **Various image formats** - PNG, JPG, GIF, SVG
3. **External links** - HTTP/HTTPS URLs
4. **Internal anchors** - Links to headers within document

**Expected Outputs**:
- Graceful handling of missing images (warning, not crash)
- All image formats render correctly
- External links are clickable
- Internal anchor links navigate correctly

**Workspace**: `projects/md-to-pdf/testing/agent3/`

---

### Agent 4: Large Documents & Performance
**Focus**: Scalability and edge case file sizes
**Scenarios**:
1. **Very large document** - 100+ headers, 500+ lines
2. **Empty document** - No headers, minimal content
3. **No headers** - Document with content but no headers (TOC should be empty)
4. **UTF-8 special characters** - Emojis, accented characters, CJK characters

**Expected Outputs**:
- Large documents generate without timeout/memory errors
- Empty documents handle gracefully
- No-header documents skip TOC generation
- UTF-8 characters render correctly

**Workspace**: `projects/md-to-pdf/testing/agent4/`

---

## Agent Isolation

Each agent works in isolated workspace:
- Agent 1: `projects/md-to-pdf/testing/agent1/`
- Agent 2: `projects/md-to-pdf/testing/agent2/`
- Agent 3: `projects/md-to-pdf/testing/agent3/`
- Agent 4: `projects/md-to-pdf/testing/agent4/`

**Critical**: Agents must NOT interfere with each other's workspaces.

## Testing Timeline

**Total estimated time**: 90-120 minutes
- Setup: 10 minutes
- Parallel testing: 60-90 minutes (4 agents running simultaneously)
- Consolidation: 20 minutes

## Deliverables

Each agent produces:
1. **Test markdown files** - In their workspace
2. **Generated PDFs** - Output from converter
3. **FINDINGS.md** - Issues discovered, categorized by severity:
   - **CRITICAL**: Crashes, data loss, broken core functionality
   - **IMPORTANT**: Incorrect rendering, missing features
   - **NICE-TO-HAVE**: Minor improvements, polish

## Success Criteria

- All 4 agents complete testing
- Zero CRITICAL issues (or all resolved)
- Consolidated findings document created
- Priority fixes identified

## Post-Testing

After all agents complete:
1. Consolidate findings into `testing/consolidated-results/CONSOLIDATED-FINDINGS.md`
2. Categorize issues: Critical → Important → Nice-to-Have
3. Prioritize fixes
4. Update `directives/md_to_pdf.md` with new edge cases
5. Update VERSION and CHANGELOG for next release
