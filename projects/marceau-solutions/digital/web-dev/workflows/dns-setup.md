# DNS Setup SOP — Website Development Clients

## Standard: GitHub Pages

All client websites are hosted on GitHub Pages. DNS must point to GitHub's servers.

### Required DNS Records

| Type | Host | Value |
|------|------|-------|
| A | @ | 185.199.108.153 |
| A | @ | 185.199.109.153 |
| A | @ | 185.199.110.153 |
| A | @ | 185.199.111.153 |
| CNAME | www | marceausolutions.github.io |

### Before Starting

1. **Determine DNS provider**: Ask client or run `whois {domain}` to check nameservers
2. **Check for existing email**: MX records must NOT be deleted
3. **Check for existing services**: TXT records (SPF, DKIM) must NOT be deleted

### Common DNS Providers

| Provider | How to Access DNS |
|----------|-------------------|
| Namecheap | Domain List → Manage → Advanced DNS |
| GoDaddy | My Products → DNS → Manage |
| Google Domains / Workspace | admin.google.com → Domains → Manage → DNS |
| Squarespace | Domains → DNS Settings (if nameservers still point to Squarespace) |
| Cloudflare | DNS → Records |

### Workflow

#### Option A: Client Does It (Preferred for existing domains)

1. Generate visual guide:
   - Use `projects/flames-of-passion/website/dns-guide.html` as template
   - Customize for client's DNS provider
   - Deploy to EC2: `scp guide.html ec2-user@34.193.98.97:/var/www/html/forms/{client}-dns-guide.html`
2. Send via SMS:
   ```
   python execution/twilio_sms.py --template webdev_dns_instructions --to {phone}
   ```
3. Monitor for completion:
   ```bash
   dig {domain} +short  # Should return GitHub Pages IPs
   ```

#### Option B: William Does It (For Namecheap-managed domains)

1. Log into Namecheap → Domain List → Manage → Advanced DNS
2. Delete existing A records (keep MX, TXT)
3. Add 4 A records + 1 CNAME per table above
4. Save

#### Option C: Transfer Domain to Namecheap (For cost savings)

Only if client agrees. Reduces annual cost to ~$10/year.
1. Unlock domain at current registrar
2. Get auth/EPP code
3. Initiate transfer at Namecheap
4. Wait for transfer (5-7 days)
5. Add DNS records per Option B

### After DNS Records Are Added

1. **Wait 15-30 min** for propagation
2. **Verify**: `dig {domain} +short` returns `185.199.108.153` (etc.)
3. **Set custom domain on GitHub Pages**:
   ```bash
   gh api repos/MarceauSolutions/{repo}/pages --method PUT -f cname="{domain}"
   ```
4. **Enable HTTPS** (only after DNS fully propagated):
   ```bash
   gh api repos/MarceauSolutions/{repo}/pages --method PUT -f https_enforced=true
   ```
5. **Test**: Visit `https://{domain}` in incognito

### Troubleshooting

| Problem | Solution |
|---------|----------|
| DNS not propagating | Wait up to 48h. Check for typos in IP addresses |
| "Certificate does not exist" | DNS not fully propagated yet. Wait and retry HTTPS |
| Old site still showing | Clear browser cache, try incognito, check TTL |
| Email stopped working | MX records were deleted. Restore immediately |
| GitHub Pages build failing | Check repo for `.nojekyll` file, check GitHub status |
