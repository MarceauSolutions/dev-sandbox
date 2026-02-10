<!-- Original SOP as it appeared in CLAUDE.md (4,402 lines) before 2026-02-09 restructuring -->

### SOP 10: Multi-Agent Parallel Development

**When**: Building a complex system with 3+ independent components that can be developed simultaneously

**Purpose**: Accelerate development by having multiple agents BUILD different components in parallel, then consolidate outputs into a unified codebase

**Agent**: Claude Code (orchestrate consolidation). Clawdbot (build components 0-6). Ralph (build components 7-10).

**Key Distinction from Other Multi-Agent SOPs**:
- **SOP 2 (Testing)**: Agents find bugs in EXISTING code (after implementation)
- **SOP 9 (Exploration)**: Agents research different APPROACHES (before implementation)
- **SOP 10 (Development)**: Agents BUILD different COMPONENTS simultaneously (during implementation)

**When to Use**:

✅ **Use SOP 10 when**:
- Large refactoring with 3+ independent files
- System has clear component boundaries
- Components don't have circular dependencies
- Each agent can work in isolation without conflicting edits
- Time savings justify the consolidation overhead

❌ **Skip SOP 10 when**:
- Components are tightly coupled (agents would edit same files)
- Less than 3 components
- Single file changes
- Unclear how to divide work

**Directory Structure**:
```
projects/[project]/
├── agent1-[component-name]/
│   ├── workspace/          ← Agent 1 builds code here
│   └── output/
│       ├── FINDINGS.md     ← What agent discovered
│       └── COMPLETION-SUMMARY.md
├── agent2-[component-name]/
│   ├── workspace/
│   └── output/
├── agent3-[component-name]/
│   ├── workspace/
│   └── output/
├── agent4-[component-name]/
│   ├── workspace/
│   └── output/
├── consolidated/           ← Final consolidated findings
└── src/                    ← Final integrated code lives here
```

**Steps**:

**Phase 1: Component Decomposition**

1. **Identify independent components** that can be built in parallel:
   - Each component should have clear boundaries
   - Minimal dependencies between components
   - Each agent can work without knowing what others are doing

   Example (MCP Aggregator):
   - Agent 1: REST API Server (`server.py`, `auth.py`, `models.py`)
   - Agent 2: Accuracy Testing (`test scripts`, `data generators`)
   - Agent 3: Platform Core (`router.py`, `registry.py`, `billing.py`, `schema.sql`)
   - Agent 4: MCP Server (`aggregator_mcp.py`, Claude Desktop integration)

2. **Define integration points** - how components will connect:
   - What imports/interfaces each component exposes
   - What other components depend on
   - Shared data structures or schemas

**Phase 2: Agent Prompt Creation**

Create `AGENT-PROMPTS.txt` with clear prompts for each agent:

```markdown
==================================================
AGENT 1: [COMPONENT NAME]
==================================================

I'm Agent 1 in a PARALLEL DEVELOPMENT effort for [Project Name].

MY WORKSPACE: /absolute/path/to/agent1-[component]/workspace/
MY OUTPUT: /absolute/path/to/agent1-[component]/output/

MY MISSION: Build [Component Name]

COMPONENTS TO BUILD:
1. [File 1] - [Description]
2. [File 2] - [Description]
3. [File 3] - [Description]

INTERFACE CONTRACT:
- I will expose: [class/function names with signatures]
- I will expect from other agents: [dependencies - may not exist yet]
- Shared schema: [if applicable]

DELIVERABLES:
1. All code files in workspace/
2. output/FINDINGS.md - Technical decisions made
3. output/COMPLETION-SUMMARY.md - What was built, what human needs to do

CRITICAL: Work independently. Do not assume other agents exist.
Build to the interface contract. Test your component in isolation.
```

**Phase 3: Launch and Monitor**

1. **Launch all agents** simultaneously:
   - Open 4 separate Claude instances
   - Copy-paste each agent's prompt
   - Let agents work independently

2. **Do not interrupt** - let agents complete autonomously

3. **Collect completion summaries** from each agent's `output/` folder

**Phase 4: Consolidation (CRITICAL)**

This is where outputs are merged into a working system:

1. **Create consolidation plan**:
   ```markdown
   # Consolidation Plan

   ## Agent Outputs to Integrate
   - Agent 1: workspace/server.py → src/api/server.py
   - Agent 2: workspace/test_*.py → testing/
   - Agent 3: workspace/*.py → src/core/
   - Agent 4: workspace/aggregator_mcp.py → mcp-server/

   ## Integration Order
   1. Foundation: Agent 3 (core) first - everything depends on it
   2. API Layer: Agent 1 (uses core)
   3. MCP Server: Agent 4 (uses core)
   4. Testing: Agent 2 (tests everything)

   ## Import Updates Required
   - Agent 4's code imports from agent3/workspace → change to src.core
   - Agent 1's code may need core imports
   ```

2. **Copy files to final locations**:
   ```bash
   # Foundation first
   cp agent3-platform-core/workspace/*.py src/core/

   # Then dependent layers
   cp agent1-rest-api/workspace/*.py src/api/
   cp mcp-server/*.py mcp-server/
   ```

3. **Update imports** in all files:
   - Change `from agent3...` to `from src.core...`
   - Fix relative imports
   - Create `__init__.py` files for modules

4. **Create module `__init__.py`** that exposes all classes:
   ```python
   from .router import Router, RoutingRequest
   from .registry import Registry, MCP, MCPCategory
   from .billing import BillingSystem, PricingModel
   ```

5. **Test integration**:
   ```bash
   python -c "from src.core import Router, Registry, BillingSystem"
   ```

6. **Document in CHANGELOG.md**:
   ```markdown
   ## [X.Y.Z-dev] - YYYY-MM-DD

   ### Added - Multi-Agent Development

   **Agent 1**: [What they built]
   **Agent 2**: [What they built]
   **Agent 3**: [What they built]
   **Agent 4**: [What they built]

   ### Integration Notes
   - Agent outputs consolidated into src/
   - Imports updated from agentN-workspace to src.module
   ```

**Phase 5: Verification**

1. **Run all tests** (if any exist)
2. **Verify imports work** from multiple entry points
3. **Test end-to-end flow** that uses all components
4. **Commit integrated result**

**Example: MCP Aggregator (2026-01-13)**

**Problem**: Platform had 51 rideshare-specific assumptions blocking non-rideshare services

**Agent Assignments**:
| Agent | Component | Output |
|-------|-----------|--------|
| Agent 1 | REST API | `server.py`, `auth.py`, `models.py`, `config.py` |
| Agent 2 | Accuracy Testing | Test scripts, data generators |
| Agent 3 | Platform Core | `router.py`, `registry.py`, `billing.py`, `schema.sql` (+ enums, scoring profiles) |
| Agent 4 | MCP Server | `aggregator_mcp.py` |

**Consolidation**:
1. Copied Agent 3 outputs to `src/core/`
2. Copied Agent 1 outputs to `src/api/`
3. Updated `aggregator_mcp.py` imports from `agent3-workspace` to `src.core`
4. Created `__init__.py` exposing all classes
5. Verified imports: `from src.core import Router, Registry, BillingSystem`

**Result**: 4 agents completed in ~2 hours what would take 8+ hours sequentially

**Common Consolidation Mistakes**:

| Mistake | Fix |
|---------|-----|
| Left agent workspace imports | Search-replace `agent[N]-workspace` → `src.module` |
| Missing `__init__.py` | Create module inits exposing key classes |
| Circular dependencies | Order consolidation by dependency graph |
| Duplicate implementations | Compare, choose best, delete other |
| Conflicting schemas | Merge manually, choosing superset |

**Success Criteria**:

- ✅ All agent code consolidated into `src/`
- ✅ No imports reference `agent[N]-workspace`
- ✅ All modules have `__init__.py`
- ✅ Integration test passes
- ✅ CHANGELOG documents all agent contributions

**References**:
- `projects/mcp-aggregator/` - Working example of SOP 10
- `projects/mcp-aggregator/CHANGELOG.md` - How to document agent contributions

