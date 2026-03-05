# Web Dev Operations Runbook

## Daily

- Check Twilio inbox for client replies: `python execution/twilio_inbox_monitor.py check --hours 24`
- Check n8n health: Verify `n8n-Health-Check` workflow ran successfully

## Weekly

- Review all client sites for uptime (visit each domain)
- Check GitHub Pages build status for each repo
- Review any pending DNS setups

## On Demand

### Deploy a Client Website
```bash
./scripts/deploy_website.sh {client}
# Clients: marceau, hvac, boabfit, flames
```

### Check DNS Propagation
```bash
dig {domain} +short
# Expected: 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153
```

### Enable HTTPS on GitHub Pages
```bash
gh api repos/MarceauSolutions/{repo}/pages --method PUT -f https_enforced=true
```

### Host Static File on EC2 (Fallback)
```bash
scp file.html ec2-user@34.193.98.97:/var/www/html/forms/
# Accessible at: https://api.marceausolutions.com/forms/file.html
```

### Send Client SMS
```bash
python execution/twilio_sms.py --template webdev_{template} --to {phone}
```

### Generate PDF for Client
```bash
python execution/branded_pdf_engine.py --input {markdown_file} --output {output.pdf}
```

### Create New Client (Full Flow)
See `workflows/client-onboarding.md`

## Incident Response

| Scenario | Action |
|----------|--------|
| GitHub Pages down | Use EC2 fallback (see `docs/decision-frameworks/service-fallback-matrix.md`) |
| Client site broken | Check deploy repo, redeploy, check DNS |
| SMS not delivering | Verify using toll-free number, check Twilio logs |
| n8n form not working | Check workflow status, test webhook manually |
| Client lost domain access | Help via screen share (Zoom/FaceTime) or do it for them |
