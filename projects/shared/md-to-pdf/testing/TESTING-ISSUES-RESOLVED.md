# Multi-Agent Testing Issues - Root Cause & Resolution

**Date**: 2026-01-12
**Status**: ✅ RESOLVED

---

## Summary

Agents 1 and 2 got interrupted during multi-agent testing of the MD-to-PDF converter due to **two independent issues**:

1. **Confusing workspace structure** - Nested `testing/projects/md-to-pdf/testing/` directories
2. **Missing library path** - WeasyPrint couldn't find Pango libraries on macOS

Both issues have been **completely resolved**.

---

## Issue #1: Confusing Workspace Structure

### The Problem

**Expected structure** (from successful email-analyzer testing):
```
md-to-pdf/testing/
├── AGENT-PROMPTS.txt
├── TEST-PLAN.md
├── agent1/              ← Agents work HERE
│   ├── FINDINGS.md
│   └── test-*.md
├── agent2/
├── agent3/
├── agent4/
└── consolidated-results/
```

**Actual structure** (what was created):
```
md-to-pdf/testing/
├── AGENT-PROMPTS.txt
├── agent1/              ← Test files created here
│   └── test-*.md
├── projects/            ← PROBLEM: Nested confusion
│   └── md-to-pdf/
│       └── testing/
│           └── agent1/  ← Empty/unused
```

### Root Cause

Agent prompts said:
```
MY WORKSPACE: projects/md-to-pdf/testing/agent1/
```

Agents interpreted this as a **relative path** and created:
- `testing/projects/md-to-pdf/testing/agent1/` (nested structure)

Instead of using the **absolute path**:
- `/Users/williammarceaujr./dev-sandbox/projects/md-to-pdf/testing/agent1/`

### The Fix

✅ **Removed** nested `testing/projects/` directory
✅ **Updated** all agent prompts with **absolute paths**:
```
MY WORKSPACE: /Users/williammarceaujr./dev-sandbox/projects/md-to-pdf/testing/agent1/
```

---

## Issue #2: WeasyPrint Library Path (macOS Specific)

### The Problem

When agents tried to run the conversion:
```bash
python src/md_to_pdf.py test.md output.pdf
```

**Error**:
```
OSError: cannot load library 'libpango-1.0-0': dlopen(libpango-1.0-0, 0x0002): tried:
'libpango-1.0-0' (no such file), '/opt/anaconda3/bin/../lib/libpango-1.0-0' (no such file)
```

### Root Cause

WeasyPrint requires Pango, Cairo, and GDK-Pixbuf libraries. On macOS with Homebrew:
- Libraries are installed to `/opt/homebrew/lib/`
- Python's `cffi` library doesn't check this location by default
- `DYLD_LIBRARY_PATH` must be set to `/opt/homebrew/lib`

Agent prompts **did mention** this:
```bash
Set DYLD_LIBRARY_PATH=/opt/homebrew/lib before running:
export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH
```

But agents either:
- Missed the instruction
- Ran the export in a different shell than the conversion command
- Forgot to set it for subsequent test runs

### The Fix

✅ **Created wrapper script**: `/Users/williammarceaujr./dev-sandbox/projects/md-to-pdf/src/convert.sh`
```bash
#!/bin/bash
export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH
python "$(dirname "$0")/md_to_pdf.py" "$@"
```

✅ **Updated agent prompts** to use wrapper:
```bash
HOW TO RUN CONVERTER:
Use the wrapper script (handles library paths automatically):
/Users/williammarceaujr./dev-sandbox/projects/md-to-pdf/src/convert.sh input.md output.pdf

Example:
cd /Users/williammarceaujr./dev-sandbox/projects/md-to-pdf/testing/agent1/
/Users/williammarceaujr./dev-sandbox/projects/md-to-pdf/src/convert.sh test1.md test1.pdf
```

✅ **Verified it works**:
```bash
$ /Users/williammarceaujr./dev-sandbox/projects/md-to-pdf/src/convert.sh test1.md test1.pdf
✓ Generated: test1.pdf
```

---

## Impact on End Users

### ZERO Impact ✅

The wrapper script is **development/testing only**. End users have multiple options:

**Option 1: Normal installation (most users)**
```bash
pip install markdown2 weasyprint pygments
python src/md_to_pdf.py input.md output.pdf  # Works fine
```

**Option 2: macOS/Homebrew users (if library issues occur)**
```bash
./src/convert.sh input.md output.pdf  # Use wrapper
```

**Option 3: Manual library path (advanced)**
```bash
export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH
python src/md_to_pdf.py input.md output.pdf
```

### Documentation Updated

✅ Added troubleshooting section to [convert-md-to-pdf.md](../workflows/convert-md-to-pdf.md:422-449)

---

## Files Changed

### Created
- `/Users/williammarceaujr./dev-sandbox/projects/md-to-pdf/src/convert.sh` - Wrapper script

### Updated
- `/Users/williammarceaujr./dev-sandbox/projects/md-to-pdf/testing/AGENT-PROMPTS.txt` - All 4 agent prompts
- `/Users/williammarceaujr./dev-sandbox/projects/md-to-pdf/workflows/convert-md-to-pdf.md` - Troubleshooting section
- `/Users/williammarceaujr./dev-sandbox/CLAUDE.md` - SOP 2 with critical prerequisites, absolute paths, reference template

### Removed
- `/Users/williammarceaujr./dev-sandbox/projects/md-to-pdf/testing/projects/` - Nested directory structure

---

## Verification Tests

✅ **Agent 1 test file converts successfully**:
```bash
$ cd /Users/williammarceaujr./dev-sandbox/projects/md-to-pdf/testing/agent1
$ /Users/williammarceaujr./dev-sandbox/projects/md-to-pdf/src/convert.sh test1-duplicate-headers.md test1-output.pdf
✓ Generated: test1-output.pdf (8.6 KB)
```

✅ **Agent 2 test file converts successfully**:
```bash
$ cd /Users/williammarceaujr./dev-sandbox/projects/md-to-pdf/testing/agent2
$ /Users/williammarceaujr./dev-sandbox/projects/md-to-pdf/src/convert.sh test-complex-tables.md test-output.pdf
✓ Generated: test-output.pdf
```

✅ **Workspace structure cleaned**:
```bash
$ ls -la /Users/williammarceaujr./dev-sandbox/projects/md-to-pdf/testing/
AGENT-PROMPTS.txt
START-HERE.md
TEST-PLAN.md
agent1/
agent2/
agent3/
agent4/
consolidated-results/
# No more nested projects/ directory ✅
```

---

## Root Insight: Testing Too Early

**Key Discovery**: The md-to-pdf converter was tested **before** the core implementation was fully stable and manually verified.

**What should have happened**:
1. ✅ Complete core implementation
2. ✅ Test manually with several examples
3. ✅ Resolve all environment issues (library paths, dependencies)
4. ✅ Document basic workflows
5. **THEN** set up multi-agent testing

**What actually happened**:
1. ✅ Implementation created
2. ❌ Jumped straight to multi-agent testing
3. ❌ Environment issues (library paths) not resolved
4. ❌ Agent workspace structure not verified
5. ❌ Result: Agents crashed immediately

**Comparison**: Email-analyzer testing succeeded because:
- Core implementation was solid
- Workflows were tested manually first
- Environment was working
- Simple cases verified before edge case testing

**Takeaway**: Multi-agent testing is for finding **edge cases**, not debugging **basic functionality**.

---

## Lessons Learned

### 1. Verify Prerequisites Before Multi-Agent Testing

**Before creating test plan, verify**:
- [ ] Core scripts work for happy path
- [ ] Environment dependencies resolved
- [ ] At least 1-2 workflows tested manually
- [ ] Basic functionality confirmed

**Reference**: `CLAUDE.md` SOP 2 now includes critical prerequisites checklist

### 2. Always Use Absolute Paths in Agent Prompts
**Before**:
```
MY WORKSPACE: projects/md-to-pdf/testing/agent1/
```

**After**:
```
MY WORKSPACE: /Users/williammarceaujr./dev-sandbox/projects/md-to-pdf/testing/agent1/
```

### 2. Wrapper Scripts > Environment Instructions
**Instead of**:
```
Set DYLD_LIBRARY_PATH=/opt/homebrew/lib before running
```

**Use**:
```bash
# Wrapper script that handles it automatically
./src/convert.sh input.md output.pdf
```

### 3. Reference Successful Patterns
Email-analyzer testing structure worked perfectly. Use it as the template for future multi-agent testing setups.

### 4. Verify Structure Before Launch
Run this check before launching agents:
```bash
# Should only show workspace folders (agent1, agent2, etc.)
ls -la testing/
```

---

## Ready to Resume Testing

All issues resolved. Agents can now be launched with the updated prompts in:
- [AGENT-PROMPTS.txt](AGENT-PROMPTS.txt)

Updated prompts include:
- ✅ Absolute workspace paths
- ✅ Wrapper script usage
- ✅ Clear examples
- ✅ No environment setup required

---

## Related Documentation

- [SOP 2: Multi-Agent Testing](../../../CLAUDE.md#sop-2-multi-agent-testing)
- [Email Analyzer Testing](../../../email-analyzer/testing/TESTING-COMPLETE.md) - Successful reference
- [Convert MD-to-PDF Workflow](../workflows/convert-md-to-pdf.md) - Updated troubleshooting
