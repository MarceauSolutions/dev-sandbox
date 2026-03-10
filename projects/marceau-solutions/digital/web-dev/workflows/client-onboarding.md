# Web Dev Client Onboarding Workflow

## Trigger
New website client signs on (after discovery call + invoice paid).

## Pre-Flight (SOP 33)
- [ ] `python scripts/inventory.py search website` — check existing tools
- [ ] Check `scripts/deploy_website.sh` for existing client config
- [ ] Verify Twilio toll-free is default in `.env`
- [ ] Confirm n8n is healthy: `n8n-Health-Check` workflow

---

## Step 1: Create Project Structure (Claude Code)

```bash
# Replace {client} with slug (lowercase, hyphenated)
mkdir -p projects/{client}/website
```

Create `projects/{client}/CLAUDE.md`:
```markdown
# {Client Name}

Client of Marceau Solutions. {Brief description}.

## Projects in This Namespace

| Project | What | Deploy Repo |
|---------|------|-------------|
| `website/` | Client website (static HTML) | `MarceauSolutions/{client}-website` |

## Deployment

Website: `./scripts/deploy_website.sh {client}` -> pushes to `MarceauSolutions/{client}-website` (GitHub Pages).
```

## Step 2: Create GitHub Pages Repo

```bash
gh repo create MarceauSolutions/{client}-website --public --description "{Client Name} website"
```

## Step 3: Add Client to Deploy Script

Edit `scripts/deploy_website.sh` — add case entry:
```bash
{client})
    LOCAL_PATH="projects/{client}/website"
    DEPLOY_REPO="MarceauSolutions/{client}-website"
    ;;
```

Also update the help text at the bottom.

## Step 4: Create n8n Form Pipeline (if client needs forms)

Clone the `Flames-Form-Pipeline` (`mrfVYqg5H12Z2l5K`) pattern:
- Webhook: `POST /webhook/form-submit` (reuse existing, filter by `source` field)
- Or create dedicated: `POST /webhook/{client}-form`
- Route to Google Sheets + Telegram notification

## Step 5: Build the Website

- Use `projects/marceau-solutions/website-builder/` for AI-generated first draft, OR
- Build manually in `projects/{client}/website/`
- Match client brand (NOT Marceau Solutions dark+gold unless requested)
- Include `CNAME` file if custom domain is known

## Step 6: DNS Setup

Follow `workflows/dns-setup.md` for the full SOP.

Quick version:
1. Determine where client's DNS is managed (registrar, Google, Cloudflare, etc.)
2. Send visual guide via SMS (generate from dns-setup template)
3. Or do it for them if they give access
4. Configure GitHub Pages custom domain:
   ```bash
   gh api repos/MarceauSolutions/{client}-website/pages --method PUT -f cname="{domain}"
   ```
5. Monitor DNS propagation: `dig {domain} +short`
6. Enable HTTPS once propagated:
   ```bash
   gh api repos/MarceauSolutions/{client}-website/pages --method PUT -f https_enforced=true
   ```

## Step 7: Deploy

```bash
./scripts/deploy_website.sh {client}
```

## Step 8: Client Communication

Send welcome SMS:
```
python execution/twilio_sms.py --template webdev_welcome --to {phone}
```

Send site-live notification:
```
python execution/twilio_sms.py --template webdev_site_live --to {phone}
```

---

## Checklist Summary

- [ ] Project directory created with CLAUDE.md
- [ ] GitHub Pages repo created
- [ ] Deploy script updated
- [ ] n8n form pipeline (if needed)
- [ ] Website built and reviewed
- [ ] DNS configured and propagated
- [ ] HTTPS enabled
- [ ] First deploy successful
- [ ] Welcome SMS sent
- [ ] Site-live SMS sent

## SLA

| Milestone | Target |
|-----------|--------|
| Project structure | Day 0 (same day as payment) |
| First draft live | Day 3 |
| DNS configured | Day 5 (depends on client) |
| Final site live | Day 7 |
