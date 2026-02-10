<!-- Original SOP as it appeared in CLAUDE.md (4,402 lines) before 2026-02-09 restructuring -->

### SOP 8: Client Demo & Test Output Management

**When**: Testing workflows for clients or need to preserve test outputs for review/demonstration

**Purpose**: Systematically save valuable test outputs while maintaining workspace cleanliness

**Agent**: Claude Code (primary for file management). Clawdbot can copy/move files. Ralph: N/A.

**Directory Structure**:

For **company-specific** projects:
```
projects/[company-name]/[project-name]/
├── demos/
│   ├── client-[name]/           # Client-specific demo outputs
│   │   ├── YYYY-MM-DD/          # Date-stamped test sessions
│   │   │   ├── output.pdf
│   │   │   ├── screenshot.png
│   │   │   └── notes.md         # Context about this demo
│   │   └── latest/              # Symlink to most recent
│   └── internal/                # Internal testing outputs
└── samples/                     # Reference examples for documentation
```

For **shared/multi-tenant** projects:
```
projects/shared/[project-name]/
├── demos/
│   ├── client-[name]/           # Client-specific demo outputs
│   │   ├── YYYY-MM-DD/          # Date-stamped test sessions
│   │   │   ├── output.pdf
│   │   │   ├── screenshot.png
│   │   │   └── notes.md         # Context about this demo
│   │   └── latest/              # Symlink to most recent
│   └── internal/                # Internal testing outputs
└── samples/                     # Reference examples for documentation
```

**Steps**:

1. **During Testing (in .tmp/)**:
   - Run workflow tests in `.tmp/` as normal
   - Outputs are created temporarily
   - Review outputs immediately

2. **Identify Keeper Outputs**:
   Ask yourself:
   - Does this demonstrate client capability?
   - Would I show this to a client?
   - Is this a reference example for docs?
   - Does this show an edge case or important result?

   **If YES** → Save to appropriate location
   **If NO** → Delete from `.tmp/`

3. **Save Demo Outputs**:
   ```bash
   # Create client demo directory (if doesn't exist)
   mkdir -p projects/[project]/demos/client-[name]/$(date +%Y-%m-%d)

   # Copy valuable outputs from .tmp/
   cp .tmp/output.pdf projects/[project]/demos/client-[name]/$(date +%Y-%m-%d)/

   # Add context notes
   echo "Demo showing [feature] - client requested [capability]" > \
     projects/[project]/demos/client-[name]/$(date +%Y-%m-%d)/notes.md

   # Update 'latest' symlink
   cd projects/[project]/demos/client-[name]/
   ln -sf $(date +%Y-%m-%d) latest
   ```

4. **Save Reference Examples**:
   ```bash
   # For documentation examples or edge cases
   mkdir -p projects/[project]/samples/
   cp .tmp/example.pdf projects/[project]/samples/example-complex-table.pdf
   ```

5. **Clean Up .tmp/**:
   ```bash
   # After saving what you need, clean temporary files
   rm .tmp/output.pdf .tmp/test-*.pdf

   # Or clean entire .tmp/ directory
   rm -rf .tmp/*
   ```

6. **Review Before Client Meeting**:
   ```bash
   # Check latest demo outputs
   ls -la projects/[project]/demos/client-[name]/latest/

   # Open for review
   open projects/[project]/demos/client-[name]/latest/output.pdf
   ```

7. **Commit Demo Outputs** (optional, based on sensitivity):
   ```bash
   # Commit if outputs don't contain sensitive data
   git add projects/[project]/demos/
   git commit -m "demo: Add [client-name] demo outputs for [date]"

   # OR add to .gitignore if sensitive
   echo "projects/[project]/demos/" >> .gitignore
   ```

**Best Practices**:

- **Date-stamp sessions**: Use `YYYY-MM-DD` format for chronological sorting
- **Add context notes**: Brief `notes.md` explaining what the output demonstrates
- **Use 'latest' symlink**: Easy access to most recent demo without remembering dates
- **Client folders**: Separate outputs by client for easy organization
- **Sensitive data**: Add `demos/` to `.gitignore` if outputs contain client data
- **Regular cleanup**: Archive or delete old demo sessions (keep latest 2-3)

**File Naming Conventions**:
```
demos/client-acme/2026-01-12/
├── notes.md                    # "Demonstrates PowerPoint generation with custom theme"
├── output-v1.pdf               # First iteration
├── output-v2-revised.pdf       # After feedback
└── screenshot-theme.png        # Visual reference
```

**Communication Pattern**:
- "Save this for the client" → Move to `demos/client-[name]/$(date)/`
- "This is a good example" → Move to `samples/`
- "Clean up test files" → Delete everything in `.tmp/`

**Example Workflow**:
```bash
# 1. Test in .tmp/
python projects/interview-prep/src/generate_pptx.py --company "Acme Corp" --output .tmp/acme-demo.pptx

# 2. Review output
open .tmp/acme-demo.pptx

# 3. Client likes it! Save for demo
mkdir -p projects/interview-prep/demos/client-acme/2026-01-12
cp .tmp/acme-demo.pptx projects/interview-prep/demos/client-acme/2026-01-12/
echo "Acme Corp interview prep demo - custom navy theme" > \
  projects/interview-prep/demos/client-acme/2026-01-12/notes.md

# 4. Update latest symlink
cd projects/interview-prep/demos/client-acme/
ln -sf 2026-01-12 latest

# 5. Clean .tmp/
rm .tmp/acme-demo.pptx

# 6. Before client meeting
open projects/interview-prep/demos/client-acme/latest/acme-demo.pptx
```

**Success Criteria**:
- [ ] Valuable outputs saved to `demos/` or `samples/`
- [ ] Each demo has `notes.md` with context
- [ ] `latest` symlink updated for easy access
- [ ] `.tmp/` cleaned after session
- [ ] Sensitive outputs added to `.gitignore` (if applicable)

**References**: See `docs/workflow-standard.md` for documentation examples, `docs/repository-management.md` for .gitignore best practices

