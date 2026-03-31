#!/usr/bin/env python3.11
"""
Re-authenticate token.json with Calendar + Gmail scopes.
Run this locally (with browser access) to update the token.
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
]

CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), '..', 'credentials.json')
TOKEN_FILE = os.path.join(os.path.dirname(__file__), '..', 'token.json')

def main():
    print("Re-authenticating with Calendar + Gmail scopes...")
    print(f"Credentials: {CREDENTIALS_FILE}")
    print(f"Token output: {TOKEN_FILE}")
    print(f"Scopes: {SCOPES}\n")
    
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server(port=8090)
    
    with open(TOKEN_FILE, 'w') as f:
        f.write(creds.to_json())
    
    print(f"\n✅ Token saved to {TOKEN_FILE}")
    print("You can now use Calendar API with this token.")

if __name__ == '__main__':
    main()
