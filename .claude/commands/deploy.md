Read and follow the deployment SOP at `docs/sops/sop-03-deployment.md`.

Before deploying:
1. Verify all testing is complete (manual + multi-agent if applicable)
2. Update VERSION file (remove -dev suffix)
3. Update CHANGELOG.md

Then run: `python deploy_to_skills.py --project $ARGUMENTS --version <VERSION>`

For AI Assistant deployment (standalone/sellable), also follow `docs/sops/sop-31-ai-assistant.md`.
