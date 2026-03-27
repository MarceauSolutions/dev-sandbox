# DNS Records Backup — flamesofpassionentertainment.com

Captured: 2026-03-05 (before Namecheap transfer)
Nameservers: ns-cloud-c1-c4.googledomains.com (Google Cloud DNS)

## MX Records (Google Workspace email — MUST recreate on Namecheap)

| Priority | Server |
|----------|--------|
| 1 | aspmx.l.google.com |
| 5 | alt1.aspmx.l.google.com |
| 5 | alt2.aspmx.l.google.com |
| 10 | alt3.aspmx.l.google.com |
| 10 | alt4.aspmx.l.google.com |

## TXT Records

None found via public DNS. Check Squarespace DNS page for any SPF/DKIM records.
Standard Google Workspace SPF would be: `v=spf1 include:_spf.google.com ~all`

## A Records

None configured (domain not pointed to any website yet).

## CNAME Records

None (www subdomain not configured).

## Records to ADD on Namecheap (GitHub Pages)

| Type | Host | Value |
|------|------|-------|
| A | @ | 185.199.108.153 |
| A | @ | 185.199.109.153 |
| A | @ | 185.199.110.153 |
| A | @ | 185.199.111.153 |
| CNAME | www | marceausolutions.github.io |
