Check memory system health and consolidate if needed.

Run: `python execution/memory_consolidator.py $ARGUMENTS`

Options:
- `--report` (default) — Show analysis without changing anything
- `--fix` — Auto-fix orphans and broken links
- `--compact` — Rewrite MEMORY.md to save space

Run this periodically to keep the memory system clean and under the 200-line limit.
