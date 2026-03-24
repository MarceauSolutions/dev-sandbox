Generate a session summary and append it to docs/session-history.md.

Run: `python execution/session_summarizer.py $ARGUMENTS`

Use `--preview` to see the summary without writing it.
Use `--since "2 hours ago"` to narrow the time window.

This captures what was done this session for cross-session continuity.
Run this at the end of every working session.
