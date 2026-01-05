# Amazon SP-API Authentication Setup Guide

**Issue:** Getting "Unauthorized - access token revoked/malformed/invalid" errors

**Diagnosis:** The refresh token is valid (can generate new access tokens), but the SP-API application needs re-authorization or IAM role permissions need updating.

---

## Quick Diagnosis

Run this to verify your current setup:

```bash
python execution/refresh_amazon_token.py
```

If you get a new access token ✅, the refresh token works.
If you still get auth errors when calling SP-API ❌, follow steps below.

---

## Solution Path 1: Re-Authorize the Application (Most Common)

### Step 1: Check Current Credentials

```bash
# See what's in your .env (first 15 chars only for security)
grep "^AMAZON_" .env
```

You should have:
- `AMAZON_REFRESH_TOKEN`
- `AMAZON_LWA_APP_ID`
- `AMAZON_LWA_CLIENT_SECRET`
- `AMAZON_AWS_ACCESS_KEY`
- `AMAZON_AWS_SECRET_KEY`
- `AMAZON_ROLE_ARN`
- `AMAZON_MARKETPLACE_ID`

### Step 2: Re-Authorize Your App in Seller Central

The refresh token might need to be re-generated. This happens when:
- App permissions changed
- Token was revoked in Seller Central
- App was re-registered

**To re-authorize:**

1. Go to: https://sellercentral.amazon.com/apps/authorize/consent

2. Or use the authorization URL from your app:
   ```
   https://sellercentral.amazon.com/apps/authorize/consent?application_id=YOUR_LWA_APP_ID&version=beta
   ```

3. You'll be redirected to a URL like:
   ```
   https://localhost?spapi_oauth_code=AUTHORIZATION_CODE
   ```

4. Copy the `spapi_oauth_code` value

5. Run the helper script:
   ```bash
   python execution/amazon_get_refresh_token.py
   ```

   When prompted, paste the authorization code.

6. Update your `.env` file with the new `AMAZON_REFRESH_TOKEN`

---

## Solution Path 2: Check IAM Role Permissions

### Step 1: Verify IAM Role ARN

Check that your IAM role ARN in `.env` is correct:

```bash
grep "AMAZON_ROLE_ARN" .env
```

It should look like:
```
arn:aws:iam::YOUR_ACCOUNT_ID:role/SellingPartnerAPIRole
```

### Step 2: Check IAM Role Trust Policy

1. Go to AWS IAM Console: https://console.aws.amazon.com/iam/

2. Find your role: `SellingPartnerAPIRole` (or whatever yours is named)

3. Check the **Trust relationships** tab

4. It should have this trust policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::437568002678:role/Selling-Partner-API-Role"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

If it's different, update it.

### Step 3: Check IAM Role Permissions

The role needs permission to execute SP-API calls. Ensure it has a policy like:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "execute-api:Invoke"
      ],
      "Resource": "arn:aws:execute-api:*:*:*"
    }
  ]
}
```

Or use the AWS managed policy: `AmazonSPAPIFullAccess` (if it exists)

---

## Solution Path 3: Verify Application Registration

### Check Your SP-API App Settings

1. Go to Amazon Developer Console: https://developer.amazonservices.com

2. Navigate to **Apps & Services** → **Login with Amazon**

3. Find your application

4. Verify:
   - ✅ App is active (not disabled)
   - ✅ IAM ARN matches what's in `.env`
   - ✅ OAuth Redirect URI is set (can be `https://localhost` for testing)
   - ✅ App has proper permissions/scopes

---

## Solution Path 4: Check AWS Credentials

Your AWS access keys might be invalid or lack permissions.

### Test AWS Credentials

```bash
# Install AWS CLI if not already installed
brew install awscli  # macOS
# or
pip install awscli

# Configure and test
aws configure
aws sts get-caller-identity
```

If this fails, your AWS credentials are invalid.

### Verify in .env

```bash
grep "AMAZON_AWS" .env
```

Should show:
- `AMAZON_AWS_ACCESS_KEY` - Starts with `AKIA...`
- `AMAZON_AWS_SECRET_KEY` - Long secret key

These should match an IAM user that has permission to assume the SP-API role.

---

## Testing After Each Fix

After making any changes, test with:

```bash
# Test token refresh
python execution/refresh_amazon_token.py

# Test SP-API connection
python execution/test_amazon_connection.py

# Test inventory optimizer (will use real API)
python execution/amazon_inventory_optimizer.py --asin B08N5WRWNW --days 7
```

---

## Common Issues & Solutions

### Issue: "Invalid grant" when refreshing token
**Solution:** Token is expired or revoked. Re-authorize the app (Path 1).

### Issue: "Access denied" or "Forbidden"
**Solution:** IAM role permissions issue (Path 2).

### Issue: "Invalid signature"
**Solution:** AWS credentials are wrong (Path 4).

### Issue: App not found
**Solution:** Check Developer Console registration (Path 3).

---

## Quick Start Script

I'll create an interactive setup script to diagnose and fix:

```bash
python execution/setup_amazon_auth.py
```

This will:
1. Check all credentials exist
2. Test token refresh
3. Test SP-API connection
4. Provide specific fix instructions

---

## Need Help?

If stuck, check:
1. **Amazon SP-API Docs:** https://developer-docs.amazon.com/sp-api/
2. **Setup guide:** `docs/AMAZON_SETUP.md`
3. **Quick start:** `docs/AMAZON_QUICK_START.md`

The code is working perfectly - this is purely an auth/config issue!
