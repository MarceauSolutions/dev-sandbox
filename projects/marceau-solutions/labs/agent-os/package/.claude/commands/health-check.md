Run system health check.

```bash
python scripts/health_check.py
```

This checks:
- AgentOS configuration status
- Git status (uncommitted/unpushed changes)
- Environment file (.env)
- Nested git repos
- Hook status
- Memory system

For project: $ARGUMENTS
