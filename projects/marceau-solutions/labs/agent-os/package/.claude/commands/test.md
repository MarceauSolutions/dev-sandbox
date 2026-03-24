Run testing for the current project.

Testing checklist (in order):
1. **Syntax check** — `python -c "import ast; ast.parse(open('file.py').read())"` on new .py files
2. **Import check** — Verify all imports resolve
3. **Manual test** — Run main entry points with basic inputs
4. **Integration test** — Verify end-to-end flow works

For the project: $ARGUMENTS

Never commit untested code.
