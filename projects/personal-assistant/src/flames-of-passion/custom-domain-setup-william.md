# Custom Domain Setup — William's Steps

Once the client confirms DNS records are pointing to GitHub Pages, do this:

## 1. Add CNAME file to the website repo

```bash
echo "flamesofpassionentertainment.com" > projects/flames-of-passion/website/CNAME
./scripts/deploy_website.sh flames
```

## 2. Enable HTTPS in GitHub repo settings

```bash
# Or do it via CLI:
gh api repos/MarceauSolutions/flames-of-passion-website/pages \
  --method PUT \
  --field cname="flamesofpassionentertainment.com" \
  --field https_enforced=true
```

If the `gh api` command doesn't work, do it manually:
1. Go to github.com/MarceauSolutions/flames-of-passion-website/settings/pages
2. Under "Custom domain", enter the domain
3. Check "Enforce HTTPS"

## 3. Verify

- Visit `http://flamesofpassionentertainment.com` — should redirect to HTTPS
- Visit `https://www.flamesofpassionentertainment.com` — should also work
- Check that the padlock icon appears

**Note:** HTTPS certificate provisioning can take up to 24 hours after setting the custom domain, but usually happens within minutes.
