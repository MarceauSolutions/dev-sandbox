Start a new project by following these SOPs in order:

1. First read `docs/sops/sop-00-kickoff.md` — Complete project kickoff questionnaire
2. Then read `docs/sops/sop-01-init.md` — Initialize project structure

Before creating anything:
- Run `python scripts/inventory.py search $ARGUMENTS` to check for existing similar tools
- Determine location: company-specific (`projects/[company]/`) or shared (`projects/shared/`)
- Use `./scripts/add-company-project.sh` for automated setup

Do NOT create a new git repo inside the project. dev-sandbox is the parent repo.
