# Rules System — Master Registry

## How to use this system

- **Hooks enforce mechanically** — stack-guard.sh, check-existing-tools.sh, api-cost-guard.sh, interface-first-guard.sh block or warn at tool-call time. You cannot skip them.
- **`rules/routing/ROUTING.md`** — the single file to load for ANY routing, interface, agent, output, or code placement decision. Start here.
- **`rules/behavioral/`** — explains the judgment rules (E01–E12). Load a specific file when you need the reasoning behind a rule or its exact application steps.
- **`rules/tools/`** — exact commands and required data formats for shared tools. Load when using branded_pdf_engine, SMTP email, Twilio SMS, api-key-manager, or inventory.

## Rule Registry

| Rule ID | Name | Category | Hook Enforced? | File | When to Load |
|---------|------|----------|---------------|------|--------------|
| C01 | Check existing tools first | Critical | `check-existing-tools.sh` (BLOCKING for PDF/email/SMS) | `rules/INDEX.md` | Before writing any .py file |
| C02 | Never nest git repos | Critical | none — manual check | `rules/INDEX.md` | Before `git init` or cloning |
| C03 | Test before committing | Critical | pre-commit hook | `rules/INDEX.md` | Before every commit |
| C04 | DOE discipline | Critical | none — judgment | `rules/INDEX.md` | Before deploying anything |
| C05 | Never contradict user | Critical | none — judgment | `rules/INDEX.md` | Always |
| C06 | Document >30min efforts | Critical | none — judgment | `rules/INDEX.md` | After long sessions |
| C07 | Rule of Three | Critical | none — judgment | `rules/INDEX.md` | When same approach fails 3x |
| C08 | Push after commit | Critical | `post-push-ec2-sync.sh` | `rules/INDEX.md` | After every git commit |
| C09 | Verify sync on session start | Critical | none — checklist | `rules/INDEX.md` | Session start |
| E01 | Just do it | Behavioral | `no-asking-guard.sh` | `rules/behavioral/E01-just-do-it.md` | When tempted to ask permission |
| E02 | Stay on track | Behavioral | none — judgment | `rules/behavioral/E02-stay-on-track.md` | When William says no to an approach |
| E04 | Verify before spending | Behavioral | `api-cost-guard.sh` (warning/block) | `rules/behavioral/E04-verify-before-spending.md` | Before any paid API call |
| E05 | Use APIs, never delegate | Behavioral | `no-delegation-guard.sh` (BLOCKING) | `rules/behavioral/E05-use-apis-never-delegate.md` | Before telling William to do anything manually |
| E06 | Build foundations | Behavioral | none — judgment | `rules/behavioral/E06-build-foundations.md` | When scoping any new tool |
| E07 | Complete the loop | Behavioral | `complete-the-loop-guard.sh` | `rules/behavioral/E07-complete-the-loop.md` | After sending SMS or email |
| E08 | Stay in the stack | Behavioral | `stack-guard.sh` (BLOCKING) | `rules/behavioral/E08-stay-in-stack.md` | Before using any external service |
| E09 | Pre-flight mandatory | Behavioral | none — checklist | `rules/behavioral/E09-preflight.md` | Before every task |
| E10 | Best-path evaluation | Behavioral | `interface-first-guard.sh` (warning) | `rules/behavioral/E10-best-path.md` | Before building anything |
| E11 | Spec written != deployed | Behavioral | none — judgment | `rules/behavioral/E11-spec-not-deployed.md` | After writing any spec or design doc |
| E12 | Code to production pipeline | Behavioral | `interface-first-guard.sh` (warning) | `rules/behavioral/E12-code-to-production.md` | After any script is working locally |
| R01 | Interface selection | Routing | `interface-first-guard.sh` | `rules/routing/ROUTING.md` | Before building any user-facing tool |
| R02 | Output format | Routing | `check-existing-tools.sh` | `rules/routing/ROUTING.md` | When deciding what to produce |
| R03 | Agent routing | Routing | none — judgment | `rules/routing/ROUTING.md` | When assigning tasks across agents |
| R04 | Code placement | Routing | `project-structure-guard.sh` | `rules/routing/ROUTING.md` | Before creating any new file |
| R05 | PDF template selection | Routing | `check-existing-tools.sh` | `rules/routing/ROUTING.md` | Before calling branded_pdf_engine.py |
