<!-- Original SOP as it appeared in CLAUDE.md (4,402 lines) before 2026-02-09 restructuring -->

### SOP 20: Internal Method Development

**When**: Creating internal operational frameworks, classification systems, or procedural methods

**Purpose**: Develop internal methods (estimation frameworks, qualification criteria, onboarding processes) with the same rigor as projects, but with appropriate differences

**Agent**: Claude Code (primary). Clawdbot (research phases). Ralph (complex method via PRD).

**Prerequisites**:
- ✅ Problem clearly defined (not vague)
- ✅ Used by 2+ people or applied 2+ times
- ✅ Existing ad-hoc approach to formalize

**Key Distinction from Projects**:
- **Projects** → External products/services → Deploy to PyPI/GitHub
- **Internal Methods** → Operational tools → Integrate into CLAUDE.md/SOPs

**Directory Structure**:
```
methods/[method-name]/
├── DEFINITION.md           # Problem statement, scope, success criteria
├── exploration/            # SOP 9 multi-agent research
│   ├── EXPLORATION-PLAN.md
│   ├── agent1-[focus]/
│   ├── agent2-[focus]/
│   ├── agent3-[focus]/
│   ├── agent4-[focus]/
│   └── consolidated/
├── [METHOD-OUTPUT].md      # The actual framework/matrix
├── templates/              # Supporting templates
└── VALIDATION-LOG.md       # Test cases and refinements
```

**Steps**:

1. **DEFINE** - Create `methods/[name]/DEFINITION.md`:
   - What problem does this method solve?
   - Who uses it (William, Claude, both)?
   - What does success look like?
   - What are the inputs and outputs?

2. **EXPLORE** (SOP 9) - Multi-agent research:
   - Launch 3-4 agents to research different aspects
   - Consolidate findings into recommendation

3. **DESIGN** - Create the method:
   - Classification matrix / decision tree
   - Templates / checklists
   - Automation scripts (if applicable)

4. **DOCUMENT** - Make it usable:
   - Create SOP in `workflows/`
   - Add to CLAUDE.md communication patterns
   - Update KNOWLEDGE_BASE.md

5. **VALIDATE** - Test on real scenarios:
   - Apply to 3-5 past or hypothetical cases
   - Document in `VALIDATION-LOG.md`
   - Refine based on results

6. **INTEGRATE** - No deployment, just integration:
   - Reference in relevant SOPs
   - Add communication patterns to CLAUDE.md

**Versioning**: Date-based (2026-01-15) not semantic (1.0.0)

**Examples of Internal Methods**:
- Project scoping & estimation
- Lead qualification criteria
- Client onboarding process
- Pricing strategy framework
- Quality assurance checklists
- SOP creation method (meta-method)

**Success Criteria**:
- [ ] DEFINITION.md exists with problem statement and success definition
- [ ] Method validated on 3-5 real or hypothetical cases
- [ ] VALIDATION-LOG.md documents test results
- [ ] Integrated into CLAUDE.md or relevant SOPs
- [ ] Another agent can apply method without additional context

**References**: SOP 9 (Multi-Agent Exploration), SOP 6 (Workflow Creation)

