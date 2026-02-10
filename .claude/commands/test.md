Run testing for the current project. Read `docs/testing-strategy.md` for the full pipeline.

Testing scenarios (in order):
1. **Manual Testing** (ALWAYS required) — Run scripts, verify output
2. **Multi-Agent Testing** (complex features) — See `docs/sops/sop-02-testing.md`
3. **Pre-Deployment Verification** — Check before deploying
4. **Post-Deployment Verification** — Check after deploying

For the project: $ARGUMENTS

Start with Scenario 1. At minimum:
- Run `python -c "import ast; ast.parse(open('file.py').read())"` on new .py files
- Test main entry points with basic inputs
- Verify imports work

Never commit untested code (Operating Principle #9a).
