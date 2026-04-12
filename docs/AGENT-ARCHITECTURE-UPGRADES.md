# Agent Architecture Upgrades — ReAct Pattern Integration

**Date**: 2026-04-10
**Source**: Research from agentic workflow articles (Substack) mapped against current systems
**Priority**: Integrate during active rebuild / tower restructuring
**Status**: Ready for implementation

---

## IMPORTANT: Relationship to Gap Analysis Rebuild

These upgrades are **ADDITIVE behavioral enhancements** to existing agent systems. They do NOT change file locations, tower structure, or the rebuild's structural goals. The gap analysis rebuild (REBUILD-GAP-ANALYSIS.md) is the primary mission — these upgrades ride alongside it, not ahead of it.

**Rule: Complete the structural move/cleanup for a file FIRST, then apply the behavioral upgrade.**

### Phase Dependencies (RESOLVED as of 2026-04-10)

Phases 0.5 through 6 are **COMPLETE**. All structural blockers are cleared. Every upgrade is safe to apply now.

| Upgrade | Status | Notes |
|---------|--------|-------|
| Goal Runner ReAct | UNLOCKED | `execution/goal_runner.py` — no move was ever planned for this file |
| AutoIterator Traces | UNLOCKED | Phase 3 already promoted `auto_iterator.py` to `execution/`. Apply upgrade at `execution/auto_iterator.py` |
| Daily Loop Dynamic | UNLOCKED | Phases 2+5 completed all surrounding file moves. Loop files are stable. |
| Panacea Metrics | UNLOCKED | Phase 0.5 complete. `panacea_relay.py` is stable. |
| Tool Discovery | UNLOCKED | Process only, no files. |

**Remaining rebuild (Phase 7: n8n migration, Phase 8: tower protocols) does NOT block any upgrades.**

---

## Context

Research from multiple articles on goal-oriented agent architecture identified 5 concrete upgrades for our existing agent systems. These align with the active rebuild (REBUILD-GAP-ANALYSIS.md) and should be integrated as files are already being touched.

---

## Upgrade 1: Goal Runner ReAct Loop (HIGH PRIORITY)

**File**: `execution/goal_runner.py`
**Current**: Goal → Strategist → Execute → Strategist → Execute → hard cap at 5
**Problem**: No observation/reflection step. Uses fixed iteration cap as primary stop, not goal-completion detection.

**Change**: Add an `evaluate_goal_completion()` step after each execution that asks:
> "Given the original goal and what just happened, is the goal achieved? If not, what specifically remains?"

**New loop**:
```
Goal → Research Gate → Strategist → Execute → OBSERVE/REFLECT →
  "Is goal met?" →
    YES → DONE (with completion summary)
    NO  → Feed reflection into next Strategist call → Execute → ...
    STUCK → Surface to William with what was tried
```

**Implementation**:
1. After Claude executes a task and returns a result, add a new LLM call (can use Haiku for cost):
   - Input: original goal + execution result + iteration history
   - Output: `{goal_met: bool, confidence: float, remaining_work: str, reflection: str}`
2. If `goal_met == true && confidence > 0.8` → terminate with success summary
3. If `goal_met == false` → inject `reflection` and `remaining_work` into next Strategist prompt
4. Keep max iterations as a SAFETY NET (bump to 10), not the primary stop condition
5. Log the reflection trace to `pipeline.db` for post-run analysis

**Why**: The articles show that agents without explicit reflection between steps make the same mistakes repeatedly. The reflection step catches "I did the wrong thing" before wasting 4 more iterations.

---

## Upgrade 2: AutoIterator Reasoning Traces (MEDIUM PRIORITY)

**DEPENDENCY**: Phase 3 (COMPLETE) promoted `auto_iterator.py` to `execution/`. Apply this upgrade at its current location.

**File**: `execution/auto_iterator.py`
**Current**: Proposes variants → deploys → collects metrics → evaluates (keep/revert)
**Problem**: Evaluation is metric-only. No structured reasoning about WHY a variant won/lost.

**Change**: When evaluating, generate a reasoning trace:
```python
reasoning_prompt = f"""
Variant: {variant_description}
Baseline metrics: {baseline}
Variant metrics: {variant_metrics}

Explain in 2-3 sentences:
1. WHY did this variant perform better/worse?
2. What principle does this teach for future variants?
"""
```

Store the reasoning in the experiment record. When proposing NEW variants, include the last 5 reasoning traces as context so the system learns from its own analysis.

**Files to modify**:
- `auto_iterator.py` — add `generate_reasoning_trace()` after evaluation
- `auto_iterator_evaluators.py` — pass reasoning traces to proposal generation
- Strategy docs under `projects/lead-generation/` — auto-append learnings

---

## Upgrade 3: Daily Loop Dynamic Staging (MEDIUM PRIORITY)

**Files**: 
- `projects/lead-generation/src/daily_loop.py` (8-stage)
- `projects/fitness-influencer/src/fitness_daily_loop.py` (5-stage)

**Current**: Stages run sequentially regardless of observations.
**Problem**: If Stage 5 (MONITOR) finds 3 hot leads, Stage 7 (FOLLOW-UP on cold) still runs at same priority.

**Change**: After each stage, evaluate what the most valuable next stage is:
```python
def select_next_stage(completed_stages, stage_results):
    """ReAct-style: observe results, pick highest-value next stage."""
    # If MONITOR found hot leads → prioritize immediate response over cold follow-up
    # If DISCOVER found 0 new prospects → skip SCORE, go to OUTREACH with existing
    # If OUTREACH hit daily cap → skip to REPORT
    ...
```

**Implementation**: 
- Keep the stage definitions as-is
- Replace the sequential `for stage in stages:` with a priority-selecting loop
- Add a `stage_priority_evaluator()` that takes the last stage's output and returns the next best stage
- Log the decision reasoning for each stage selection

---

## Upgrade 4: Panacea Grok Consultation Optimization (LOW PRIORITY — evaluate first)

**File**: `projects/personal-assistant/src/panacea_relay.py`
**Current**: Grok consulted on EVERY request via `--append-system-prompt`
**Observation**: Articles argue single-model with good tools > two-model consultation for most tasks.

**NOT recommending removal** — William's directive is "Grok always consulted." But worth evaluating:
- Track Grok consultation latency per request
- Track how often Grok's strategic direction materially changes Claude's output
- If >80% of consultations don't change the output direction, consider making Grok consultation conditional on request complexity

**Action for now**: Add timing metrics only. No architectural change without data.

---

## Upgrade 5: Tool Parameter Discovery Protocol (PROCESS UPGRADE)

**Not a code change** — a process improvement for when new tools/MCP servers are added.

**Current**: Tools get integrated, prompts are written, sometimes they work.
**Better**: Before deploying any new tool integration:

1. **Test independently** — Give the model small sub-tasks using only that tool
2. **Ask the model to explain** — "What did you learn about using this tool effectively?"
3. **Standardize** — Write explicit tool-use instructions based on what was learned
4. **Embed in prompt** — Add the standardized instructions to the system prompt

This applies to: new MCP servers, new API integrations, new bridge endpoints, new n8n tool nodes.

---

## Integration Points with Active Rebuild

| Upgrade | Rebuild Phase It Aligns With |
|---------|------------------------------|
| Goal Runner ReAct | Phase 5 (tower purification) — goal_runner.py is in `execution/`, being restructured |
| AutoIterator Traces | Phase 2 (lead-gen tower cleanup) — auto_iterator.py imports already being fixed |
| Daily Loop Dynamic | Phase 2 (lead-gen) + Phase 3 (fitness) — daily loops being audited |
| Panacea Optimization | Phase 0.5 (Panacea) — already touched recently |
| Tool Discovery | Process — apply to all new integrations going forward |

---

## What NOT to Change

- **AutoIterator's core state machine** (proposed → approved → deployed → collecting → evaluated) — already matches the iterate-until-goal pattern
- **Three-Agent Orchestrator routing rules** — role separation is sound
- **Human-in-the-loop gates** — already in the right places
- **Grok-always-consulted directive** — William's rule, data first before changing
