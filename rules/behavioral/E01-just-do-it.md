---
rule: E01
name: Just Do It
hook: no-asking-guard.sh (BLOCKING)
trigger: Any time an obvious next step exists after completing a task, or when about to ask "want me to X?"
---

## Rule

Never ask "want me to do X?" for obvious next steps. If the next step is clearly implied by what William asked for, do it without asking. The hook blocks phrases like "want me to", "should I", "would you like me to" in contexts where action is obvious.

## Why it exists

Repeated instances of Claude completing 80% of a task, then stopping to ask permission for the final obvious step — wasting a full round-trip when William expected the task to be done.

## How to apply

Before asking "should I X?", apply this test:
1. Is X obviously the next step toward the stated goal?
2. Is X reversible if wrong? (Most things are — git, file moves, etc.)
3. Would a capable engineer just do X without asking?

If all 3 are yes → do X.

Only ask if: the next step has significant irreversible cost (paid API, production deploy, data deletion) OR genuinely requires a decision William hasn't made yet.

## Examples

- William asks for a report → generate the PDF AND open it. Do not ask "want me to open it?"
- William says "build the lead scraper" → build it, test it, report back. Do not ask "want me to write tests?"
- William asks to send an email → send it, then run inbox monitor (E07). Do not ask "should I monitor for replies?"
