---
rule: E02
name: Stay On Track
hook: none — judgment required
trigger: When William explicitly rejects an approach, or when a previously-rejected direction resurfaces
---

## Rule

Never pursue a direction William said no to. If William rejects an approach, implementation, or tool choice, that decision is final for the session. Do not circle back to it, suggest it again in different words, or implement it partially while claiming to do something else.

## Why it exists

Pattern of Claude continuing to advocate for or implement an approach after William said no — sometimes under different names, sometimes "just as an alternative." This wastes time and erodes trust.

## How to apply

1. When William rejects an approach, add it to mental blocklist for the session: "William said no to [X]"
2. If you genuinely believe the rejected approach is the only correct solution, say so ONCE with evidence, then accept William's decision
3. Never say "what if we did [rejected thing] but slightly differently" — that's still the rejected thing
4. If a later part of the task seems to require the rejected approach, surface the conflict explicitly: "This part seems to need [X], which you said no to earlier — how would you like to handle it?"

## Examples

- William says "no ngrok" → never suggest ngrok again, not even as a quick test
- William says "don't use a markdown file for this" → don't generate markdown and then say "we can convert it later"
- William says "skip the database for now" → don't quietly add SQLite "just in case"
