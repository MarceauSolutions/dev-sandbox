# Execution — Shared Utilities

This directory contains scripts used by **2 or more projects**.

## Rules
- If a script is only used by one project, it belongs in `projects/[name]/src/`
- If a second project needs the same functionality, move it here
- All scripts should work with standard library where possible
- Document any pip dependencies in a comment at the top of the file

## Finding Tools
```bash
python scripts/inventory.py search <keyword>
python scripts/inventory.py scripts
```
