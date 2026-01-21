"""
LinkedIn Manual OAuth - Get Access Token Without Local Server
Run this if the automated OAuth flow isn't working
"""

import os
import requests
from dotenv import load_dotenv, set_key
from pathlib import Path

load_dotenv()

CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")

print("🔐 LinkedIn Manual OAuth Flow\n")

# Step 1: Generate authorization URL
auth_url = f"https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id={CLIENT_ID}&redirect_uri=http://localhost:8000/callback&scope=r_liteprofile%20w_member_social"

print("Step 1: Open this URL in your browser:")
print(auth_url)
print("\nStep 2: Click 'Allow' to authorize")
print("\nStep 3: After clicking Allow, you'll be redirected to an error page.")
print("        That's OK! Just copy the FULL URL from your address bar.")
print("\nThe URL will look like:")
print("http://localhost:8000/callback?code=AQT...very_long_code...&state=...")
print()

# Step 2: Get the code from user
callback_url = input("Paste the full callback URL here: ").strip()

# Extract code from URL
if "code=" not in callback_url:
    print("❌ Error: No authorization code found in URL")
    print("Make sure you copied the FULL URL after clicking Allow")
    exit(1)

code = callback_url.split("code=")[1].split("&")[0]
print(f"\n✅ Authorization code extracted: {code[:20]}...")

# Step 3: Exchange code for access token
print("\n⏳ Exchanging code for access token...")

token_url = "https://www.linkedin.com/oauth/v2/accessToken"

payload = {
    'grant_type': 'authorization_code',
    'code': code,
    'redirect_uri': 'http://localhost:8000/callback',
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET
}

response = requests.post(token_url, data=payload)

if response.status_code != 200:
    print(f"❌ Token exchange failed: {response.text}")
    exit(1)

tokens = response.json()
access_token = tokens.get('access_token')
expires_in = tokens.get('expires_in')

print(f"✅ Access token received!")
print(f"   Expires in: {expires_in} seconds ({expires_in // 86400} days)")

# Step 4: Save to .env
env_path = Path("/Users/williammarceaujr./dev-sandbox/.env")
set_key(env_path, "LINKEDIN_ACCESS_TOKEN", access_token)

print(f"\n✅ Saved LINKEDIN_ACCESS_TOKEN to .env")
print("\nYou can now test posting:")
print("  python -m src.linkedin_api test")
